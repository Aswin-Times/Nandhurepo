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

if __name__=='__main__':unittest.main()
