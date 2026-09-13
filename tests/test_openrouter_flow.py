import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'code'))
from main import run
from financial_agent import run_agent_loop
from financial_tools import FinancialTools, validate_row
from model_provider import OpenRouterModel
from independent_validation import replay_safe
from test_provider import ENV,SENTINEL,completion,wire_response

class OpenRouterFlowTests(unittest.TestCase):
    def test_public_labels_never_reach_production_wire_or_financial_tools(self):
        from dataset_repository import DatasetRepository
        input_fields=('request_id','user_id','request_date','request_type','requested_amount',
                      'desired_completion_date','allows_partial_payment','request_text')
        labels=('amount_safe_to_pay','affordability_status','recommended_payment_method',
                'payment_plan','earliest_date_for_full_payment','spending_changes_needed','decision_explanation')
        repository=DatasetRepository(ROOT/'dataset')
        source=repository.tables['sample_requests'][0]
        source.update({key:'EVALUATOR_ONLY_CANARY_'+key for key in labels})
        source['affordability_status']='affordable_now'  # Known expected-label negative control.
        source['expected_answer_blob']={'renamed_label':'EVALUATOR_ONLY_CANARY_renamed'}
        saved=dict(source)
        opener=Mock(side_effect=[wire_response(completion(name)) for name in
                                ('retrieve_evidence','reconstruct_finances','evaluate_payment_plans','finish_decision')])
        with patch.dict(os.environ,ENV,clear=True):model=OpenRouterModel(opener=opener,sleeper=Mock())
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()),\
             patch('main.DatasetRepository',return_value=repository),patch('main.FinancialTools',wraps=FinancialTools) as factory:
            run(ROOT/'dataset',Path(tmp)/'output.csv',Path(tmp)/'checkpoint.jsonl',samples=True,
                model=ENV['OPENROUTER_MODEL'],limit=1,provider_instance=model,cache_dir=Path(tmp)/'ocr')
        self.assertEqual(opener.call_count,4)
        for call in opener.call_args_list:
            wire=json.loads(call.args[0].data)
            initial=wire['messages'][1]['content']
            payload=json.loads(initial.removeprefix('<input trust="untrusted">').removesuffix('</input>'))
            self.assertEqual(set(payload),set(input_fields))
            self.assertTrue(set(labels).isdisjoint(payload))
            self.assertEqual(payload,{key:saved[key] for key in input_fields})
            self.assertNotIn('EVALUATOR_ONLY_CANARY_',json.dumps(wire))
        self.assertEqual(set(factory.call_args.args[1]),set(input_fields))
        self.assertEqual(source,saved)  # Evaluator labels remain available and unmodified.

    def test_all_25_public_initial_wire_payloads_are_label_free(self):
        from dataset_repository import DatasetRepository
        input_fields=('request_id','user_id','request_date','request_type','requested_amount',
                      'desired_completion_date','allows_partial_payment','request_text')
        repository=DatasetRepository(ROOT/'dataset')
        self.assertEqual(len(repository.tables['sample_requests']),25)
        for source in repository.tables['sample_requests']:
            with self.subTest(request_id=source['request_id']):
                saved=dict(source)
                request=dict(source,expected_answer_blob={'answer':'EVALUATOR_ONLY_CANARY_renamed'})
                opener=Mock(return_value=wire_response(completion('retrieve_evidence')))
                with patch.dict(os.environ,ENV,clear=True):model=OpenRouterModel(opener=opener,sleeper=Mock())
                tools=FinancialTools(repository,request,None)
                run_agent_loop(model,tools,request,tools.fallback,max_steps=1)
                wire=json.loads(opener.call_args.args[0].data)
                payload=json.loads(wire['messages'][1]['content'].removeprefix('<input trust="untrusted">').removesuffix('</input>'))
                self.assertEqual(payload,{key:source[key] for key in input_fields})
                self.assertNotIn('EVALUATOR_ONLY_CANARY_',json.dumps(wire))
                self.assertEqual(opener.call_count,1)
                self.assertEqual(source,saved)

    def test_default_hosted_configuration_and_old_provider_rejected(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'OPENROUTER_API_KEY'):
                run(ROOT/'dataset',Path(tmp)/'o.csv',Path(tmp)/'c.jsonl',samples=True,limit=1)
            with self.assertRaisesRegex(ValueError,'Unsupported provider'):
                run(ROOT/'dataset',Path(tmp)/'o.csv',Path(tmp)/'c.jsonl',provider='obsolete',limit=1)

    def test_offline_no_key_and_no_network(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{},clear=True),patch('main.OpenRouterModel',side_effect=AssertionError('Offline invoked hosted provider')):
            with contextlib.redirect_stdout(io.StringIO()):
                report=run(ROOT/'dataset',Path(tmp)/'o.csv',Path(tmp)/'c.jsonl',provider='offline',samples=True,limit=1,cache_dir=Path(tmp)/'ocr')
            self.assertEqual(report['request_count'],1)
            self.assertEqual(report['usage']['model_calls'],0)

    def test_full_real_tool_batch_via_actual_adapter_with_only_http_mocked(self):
        steps=['retrieve_evidence','reconstruct_finances','evaluate_payment_plans','finish_decision']
        responses=[]
        for i,name in enumerate(steps):
            data=completion(name);data['choices'][0]['message']['tool_calls'][0]['id']='call'+str(i)
            responses.append(wire_response(data))
        opener=Mock(side_effect=responses)
        with patch.dict(os.environ,ENV,clear=True):model=OpenRouterModel(opener=opener,sleeper=Mock())
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            out=Path(tmp)/'output.csv';checkpoint=Path(tmp)/'checkpoint.jsonl';usage=Path(tmp)/'usage.md'
            report=run(ROOT/'dataset',out,checkpoint,samples=True,model=ENV['OPENROUTER_MODEL'],limit=1,
                       provider_instance=model,input_price=1,output_price=2,usage_report=usage,cache_dir=Path(tmp)/'ocr')
            record=json.loads(checkpoint.read_text())
            self.assertEqual(opener.call_count,4)
            self.assertEqual([t['tool'] for t in record['trace']],steps)
            self.assertEqual(report['usage']['input_tokens'],400)
            self.assertEqual(report['usage']['output_tokens'],80)
            self.assertAlmostEqual(report['usage_report']['reported_cost_usd'],0.012)
            self.assertEqual(report['fallback_rows'],0)
            self.assertIn('proof',record)
            from dataset_repository import DatasetRepository
            request=DatasetRepository(ROOT/'dataset').tables['sample_requests'][0]
            validate_row(record['row'],request)
            proof=record['proof']
            self.assertTrue(replay_safe(proof['opening'],proof['minimum'],proof['plan_flows'],validate_row(record['row'],request))['safe'])
            self.assertNotIn(SENTINEL,checkpoint.read_text()+out.read_text()+usage.read_text()+json.dumps(report))
            # Resume exercises checkpoint accounting, not the mocked transport again.
            resumed=run(ROOT/'dataset',out,checkpoint,samples=True,model=ENV['OPENROUTER_MODEL'],limit=1,
                        provider_instance=model,input_price=1,output_price=2,usage_report=usage,cache_dir=Path(tmp)/'ocr')
            self.assertEqual(opener.call_count,4)
            self.assertEqual(resumed['usage_report'],report['usage_report'])
        final=json.loads(opener.call_args.args[0].data)
        self.assertEqual([m['role'] for m in final['messages']],['system','user','assistant','tool','assistant','tool','assistant','tool'])

    def test_invalid_finish_json_repaired_not_dispatched_and_usage_preserved(self):
        from test_tools import FakeRepository,REQ
        steps=[completion('finish_decision','{broken'),completion('retrieve_evidence'),
               completion('reconstruct_finances'),completion('evaluate_payment_plans'),completion('finish_decision')]
        steps[0]['choices'][0]['message']['reasoning_details']=[dict(type='reasoning.encrypted',data='opaque')]
        opener=Mock(side_effect=[wire_response(data) for data in steps])
        with patch.dict(os.environ,ENV,clear=True):model=OpenRouterModel(opener=opener,sleeper=Mock())
        tools=FinancialTools(FakeRepository(),REQ,None)
        result=run_agent_loop(model,tools,REQ,tools.fallback)
        self.assertEqual(result['trace'][0]['result']['error']['code'],'invalid_tool_arguments')
        self.assertEqual(result['usage']['input_tokens'],500)
        self.assertEqual(result['usage']['reported_cost_usd'],0.015)
        second=json.loads(opener.call_args_list[1].args[0].data)
        self.assertEqual(second['messages'][2]['reasoning_details'],steps[0]['choices'][0]['message']['reasoning_details'])
        self.assertEqual(second['messages'][2]['tool_calls'][0]['function']['arguments'],'{broken')
        validate_row(result['row'],REQ)

    def test_broken_provider_boundary_negative_control(self):
        from test_tools import FakeRepository,REQ
        opener=Mock(return_value=wire_response({'choices':[]}))
        with patch.dict(os.environ,ENV,clear=True):model=OpenRouterModel(opener=opener,sleeper=Mock())
        tools=FinancialTools(FakeRepository(),REQ,None)
        result=run_agent_loop(model,tools,REQ,tools.fallback)
        self.assertEqual(result['row']['recommended_payment_method'],'not_recommended')
        self.assertIn('insufficient',result['row']['decision_explanation'])
        self.assertEqual(result['usage']['model_calls'],1)
        self.assertEqual(result['usage']['usage_missing_calls'],1)
        self.assertEqual(opener.call_count,1)

    def test_pixel_tool_handoff_uses_media_reader_and_never_persists_binary(self):
        from test_tools import FakeRepository,REQ
        from test_reconstruction import event
        from evidence_media import ImageEvidence
        class Repository(FakeRepository):
            dataset=ROOT/'dataset'
            def context(self,request):
                context=super().context(request)
                context['events']=[event('bill','2026-01-02','',status='pending')]
                context['images']=[dict(image_id='image_01',related_event_id='bill')]
                return context
        media=ImageEvidence(ROOT/'dataset')
        # Mock OCR inference only; real PNG reading/hash/media/tool/adaptor code runs.
        media._engine=Mock(return_value=([([[0,0],[100,0],[100,20],[0,20]],'Amount due 100',1.0)],None))
        steps=[('retrieve_evidence',{}),('inspect_image',{'image_id':'image_01'}),
               ('resolve_image_amount',{'image_id':'image_01','amount':'100','quote':'Amount due 100'}),
               ('reconstruct_finances',{}),('evaluate_payment_plans',{}),('finish_decision',{})]
        opener=Mock(side_effect=[wire_response(completion(name,json.dumps(args))) for name,args in steps])
        with patch.dict(os.environ,ENV,clear=True):model=OpenRouterModel(opener=opener,sleeper=Mock())
        tools=FinancialTools(Repository(),REQ,media)
        result=run_agent_loop(model,tools,REQ,tools.fallback)
        self.assertEqual(result['row']['amount_safe_to_pay'],'300')
        validate_row(result['row'],REQ)
        wire=json.loads(opener.call_args_list[2].args[0].data)
        self.assertEqual(wire['messages'][-1]['role'],'user')
        self.assertTrue(wire['messages'][-1]['content'][-1]['image_url']['url'].startswith('data:image/png;base64,'))
        self.assertNotIn('_model_image',json.dumps(result['trace']))
        media._engine.assert_called_once()

    def test_model_disabled_ablation_changes_anchored_financial_effect(self):
        from test_tools import FakeRepository,REQ
        class Repository(FakeRepository):
            def context(self,request):
                context=super().context(request)
                context['messages']=[dict(message_id='employer',sent_at='2025-12-30T00:00:00Z',source_type='employer',
                    message_text='Salary USD 500 confirmed for 2026-01-05.')]
                return context
        request=dict(REQ,requested_amount='700')
        amendment=dict(evidence_id='employer',quote='Salary USD 500 confirmed for 2026-01-05.',operation='add',
                       amount='500',date='2026-01-05',direction='credit',category='salary')
        baseline=FinancialTools(Repository(),request,None)
        for name in ('retrieve_evidence','reconstruct_finances','evaluate_payment_plans'):baseline.dispatch(name,{})
        offline=baseline.dispatch('finish_decision',{})['row']
        steps=[('retrieve_evidence',{}),('reconstruct_finances',{}),
               ('apply_evidence_amendments',{'amendments':[amendment]}),('reconstruct_finances',{}),
               ('evaluate_payment_plans',{}),('finish_decision',{})]
        opener=Mock(side_effect=[wire_response(completion(name,json.dumps(args))) for name,args in steps])
        with patch.dict(os.environ,ENV,clear=True):model=OpenRouterModel(opener=opener,sleeper=Mock())
        tools=FinancialTools(Repository(),request,None)
        result=run_agent_loop(model,tools,request,tools.fallback)
        self.assertEqual(offline['recommended_payment_method'],'not_recommended')
        self.assertEqual(result['row']['recommended_payment_method'],'wait')
        validate_row(result['row'],request)
        self.assertEqual(opener.call_count,6)
        unsafe=dict(result['row'],payment_plan='2026-01-05:9999')
        with self.assertRaises(ValueError):validate_row(unsafe,request)

    def test_synthetic_full_batch_evaluation_report_and_zip_through_provider(self):
        import csv
        import shutil
        import zipfile
        from dataset_repository import FILES
        from independent_validation import validate_artifacts
        from release_submission import package_submission,validate_manifest_freshness
        from evaluate_submission import compare_rows,read
        from test_tools import FakeRepository,REQ
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp);dataset=root/'dataset';dataset.mkdir();(root/'code').mkdir()
            for source in (ROOT/'code').glob('*.py'):shutil.copyfile(source,root/'code'/source.name)
            for name in ('SOLUTION_README.md','requirements.txt'):shutil.copyfile(ROOT/name,root/name)
            requests=[dict(REQ,request_id='fixture-'+str(i)) for i in range(250)]
            profile=dict(FakeRepository().context(REQ)['profile'],user_id=REQ['user_id'])
            for name in FILES:
                rows=requests if name=='requests' else [profile] if name=='financial_profiles' else []
                with (dataset/(name+'.csv')).open('w',encoding='utf-8',newline='') as file:
                    writer=csv.DictWriter(file,fieldnames=list(rows[0]) if rows else ['fixture_empty'])
                    writer.writeheader();writer.writerows(rows)
            turn=0
            def transport(request,timeout):
                nonlocal turn
                payload=json.loads(request.data)
                self.assertEqual(payload['model'],ENV['OPENROUTER_MODEL'])
                name=('retrieve_evidence','reconstruct_finances','evaluate_payment_plans','finish_decision')[turn%4]
                turn+=1
                args=json.dumps({'explanation':SENTINEL}) if name=='finish_decision' else '{}'
                return wire_response(completion(name,args))
            opener=Mock(side_effect=transport)
            with patch.dict(os.environ,ENV,clear=True):model=OpenRouterModel(opener=opener,sleeper=Mock())
            out=root/'output.csv';checkpoint=root/'checkpoint.jsonl';report_path=root/'usage.md'
            report=run(dataset,out,checkpoint,model=ENV['OPENROUTER_MODEL'],provider_instance=model,input_price=1,output_price=2,
                       usage_report=report_path,cache_dir=root/'ocr')
            self.assertEqual(opener.call_count,1000)
            self.assertEqual(report['usage']['model_calls'],1000)
            self.assertEqual(report['usage']['input_tokens'],100000)
            self.assertAlmostEqual(report['usage_report']['reported_cost_usd'],3.0)
            validation=validate_artifacts(dataset,out,checkpoint)
            self.assertEqual(validation,dict(rows=250,verified_payment_plans=250,failures=[]))
            validate_manifest_freshness(root,report)
            expected=[dict(request,amount_safe_to_pay='350',affordability_status='affordable_now',
                           recommended_payment_method='full_payment',payment_plan='2026-01-01:350',
                           earliest_date_for_full_payment='2026-01-01',spending_changes_needed='none') for request in requests]
            self.assertEqual(compare_rows(expected,read(out))['exact_matches']['recommended_payment_method'],250)
            (root/'.env').write_text('OPENROUTER_API_KEY='+SENTINEL)
            (root/'log.txt').write_text('fixture-only '+SENTINEL)
            destination=root/'code.zip'
            package_submission(root,out,report_path,report,destination)
            with zipfile.ZipFile(destination) as archive:
                self.assertIn('evaluation/usage_report.md',archive.namelist())
                self.assertIn('code/model_provider.py',archive.namelist())
                self.assertNotIn('.env',archive.namelist());self.assertNotIn('log.txt',archive.namelist())
                self.assertTrue(all(SENTINEL.encode() not in archive.read(name) for name in archive.namelist()))
            self.assertNotIn(SENTINEL,out.read_text()+checkpoint.read_text()+report_path.read_text()+json.dumps(report))

if __name__=='__main__':unittest.main()
