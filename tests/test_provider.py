import io
import json
import os
import sys
import traceback
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from model_provider import OpenRouterModel, ProviderError

SENTINEL='dummy-test-credential-not-a-real-key'
ENV={'OPENROUTER_API_KEY':SENTINEL,'OPENROUTER_MODEL':'fixture/tool-vision'}
TOOL=dict(name='read',description='Read evidence',input_schema={'type':'object','properties':{}})

def completion(name=None,args='{}',cost=0.003):
    message=dict(role='assistant',content='result' if name is None else None)
    if name:message['tool_calls']=[dict(id='call1',type='function',function=dict(name=name,arguments=args))]
    usage=dict(prompt_tokens=100,completion_tokens=20,total_tokens=120)
    if cost is not None:usage['cost']=cost
    return dict(id='generation1',model='fixture/tool-vision',choices=[dict(message=message,finish_reason='tool_calls' if name else 'stop')],usage=usage)

def wire_response(data):
    return io.BytesIO(json.dumps(data).encode())

class ProviderTests(unittest.TestCase):
    def make_model(self,opener,**kw):
        with patch.dict(os.environ,ENV,clear=True):return OpenRouterModel(opener=opener,sleeper=kw.pop('sleeper',Mock()),**kw)

    def test_missing_key_and_model_configuration(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'OPENROUTER_API_KEY'):OpenRouterModel('fixture/model')
        with patch.dict(os.environ,{'OPENROUTER_API_KEY':SENTINEL},clear=True):
            with self.assertRaisesRegex(ValueError,'OPENROUTER_MODEL'):OpenRouterModel()

    def test_real_boundary_request_and_usage_extraction(self):
        opener=Mock(return_value=wire_response(completion()))
        model=self.make_model(opener)
        result=model.complete('system',[dict(role='user',content='evidence')],[TOOL])
        request=opener.call_args.args[0];payload=json.loads(request.data)
        self.assertEqual(request.full_url,'https://openrouter.ai/api/v1/chat/completions')
        self.assertEqual(request.get_header('Authorization'),'Bearer '+SENTINEL)
        self.assertEqual(payload['model'],ENV['OPENROUTER_MODEL'])
        self.assertEqual(payload['messages'],[dict(role='system',content='system'),dict(role='user',content='evidence')])
        self.assertEqual(payload['tools'][0]['function']['parameters'],TOOL['input_schema'])
        self.assertTrue(payload['provider']['require_parameters'])
        self.assertFalse(payload['stream'])
        self.assertEqual(result['content'],[dict(type='text',text='result')])
        self.assertEqual(result['usage']['input_tokens'],100)
        self.assertEqual(result['usage']['output_tokens'],20)
        self.assertEqual(result['usage']['reported_cost_usd'],0.003)
        self.assertEqual(opener.call_args.kwargs['timeout'],60)

    def test_model_override_and_safe_base_url(self):
        opener=Mock(return_value=wire_response(completion()))
        model=self.make_model(opener,model='fixture/override',base_url='https://proxy.example/api/v1/')
        model.complete('system',[],[])
        self.assertEqual(json.loads(opener.call_args.args[0].data)['model'],'fixture/override')
        self.assertEqual(opener.call_args.args[0].full_url,'https://proxy.example/api/v1/chat/completions')
        for url in ('http://proxy.example','https://user:secret@proxy.example','https://proxy.example?secret=1'):
            with self.assertRaises(ValueError):self.make_model(opener,base_url=url)

    def test_multiple_tool_calls_results_reasoning_and_image_handoff(self):
        data=completion('read','{"id": 3}')
        data['choices'][0]['message']['reasoning_details']=[dict(type='reasoning.encrypted',data='opaque-state',signature='sig')]
        data['choices'][0]['message']['tool_calls'].append(dict(id='call2',type='function',function=dict(name='read',arguments='{}')))
        opener=Mock(side_effect=[wire_response(data),wire_response(completion())])
        model=self.make_model(opener)
        first=model.complete('system',[],[TOOL])
        self.assertEqual(first['content'][0]['input'],{'id':3})
        image=dict(type='image',source=dict(type='base64',media_type='image/png',data='aW1hZ2U='))
        messages=[dict(role='assistant',content=first['content'],continuation=first['continuation']),
                  dict(role='user',content=[dict(type='tool_result',tool_use_id='call1',content=[dict(type='text',text='pixels'),image]),
                                            dict(type='tool_result',tool_use_id='call2',content='{"error":"repair"}',is_error=True)])]
        model.complete('system',messages,[TOOL])
        wire=json.loads(opener.call_args.args[0].data)['messages']
        self.assertEqual(wire[1]['reasoning_details'],data['choices'][0]['message']['reasoning_details'])
        self.assertEqual([m['role'] for m in wire],['system','assistant','tool','tool','user'])
        self.assertEqual(wire[2]['tool_call_id'],'call1')
        self.assertEqual(wire[-1]['content'][-1]['image_url']['url'],'data:image/png;base64,aW1hZ2U=')
        self.assertIn('untrusted',wire[-1]['content'][0]['text'])

    def test_invalid_tool_json_is_repairable_and_usage_retained(self):
        opener=Mock(return_value=wire_response(completion('read','{broken')))
        result=self.make_model(opener).complete('system',[],[TOOL])
        self.assertIn('argument_error',result['content'][0])
        self.assertEqual(result['usage']['input_tokens'],100)

    def test_malformed_response_negative_control(self):
        for data in ({},dict(choices=[]),dict(choices=[dict(message='bad')]),dict(error={'message':SENTINEL}),
                     dict(completion(),usage=dict(prompt_tokens=-1,completion_tokens=20)),
                     dict(completion(),usage=dict(prompt_tokens=1,completion_tokens=1,total_tokens=99))):
            with self.subTest(data=data):
                with self.assertRaises(ProviderError):
                    self.make_model(Mock(return_value=wire_response(data))).complete('system',[],[])

    def test_missing_usage_is_not_fabricated(self):
        data=completion();del data['usage']
        result=self.make_model(Mock(return_value=wire_response(data))).complete('system',[],[])
        self.assertEqual(result['usage']['usage_missing_calls'],1)
        self.assertNotIn('input_tokens',result['usage'])
        self.assertNotIn('output_tokens',result['usage'])

    def test_mutated_request_negative_control_makes_contract_test_fail(self):
        # Run the real positive contract test against a broken real adapter. Detect its
        # assertion failure explicitly; a green fake transport alone is not evidence.
        result=unittest.TestResult()
        with patch.object(OpenRouterModel,'_messages',return_value=[]):
            ProviderTests('test_real_boundary_request_and_usage_extraction').run(result)
        self.assertEqual(len(result.failures),1)
        self.assertEqual(len(result.errors),0)

    def test_malformed_routing_and_continuation_metadata_rejected(self):
        variants=[dict(completion(),model={'not':'a model'}),dict(completion(),id=[])]
        for field,value in [('reasoning_details','not-an-array'),('reasoning',{}),('tool_calls',{})]:
            data=completion();data['choices'][0]['message'][field]=value;variants.append(data)
        for data in variants:
            with self.subTest(data=data),self.assertRaises(ProviderError):
                self.make_model(Mock(return_value=wire_response(data))).complete('system',[],[])

    def test_nonstandard_json_tool_arguments_repairable(self):
        for args in ('{"amount":NaN}','{"amount":1,"amount":2}','[]'):
            result=self.make_model(Mock(return_value=wire_response(completion('read',args)))).complete('system',[],[TOOL])
            self.assertIn('argument_error',result['content'][0])

    def test_invalid_json_and_long_retry_after_fail_without_secret_leak(self):
        opener=Mock(return_value=io.BytesIO((SENTINEL+' not-json').encode()))
        with self.assertRaises(ProviderError) as caught:self.make_model(opener).complete('system',[],[])
        self.assertNotIn(SENTINEL,str(caught.exception))
        sleeper=Mock();opener=Mock(side_effect=urllib.error.HTTPError('redacted',429,SENTINEL,{'Retry-After':'120'},None))
        with self.assertRaises(ProviderError):self.make_model(opener,sleeper=sleeper).complete('system',[],[])
        self.assertEqual(opener.call_count,1);sleeper.assert_not_called()

    def test_retry_timeout_rate_limit_and_permanent_error(self):
        sleeper=Mock()
        rate_limit=urllib.error.HTTPError('https://redacted',429,SENTINEL,{'Retry-After':'3'},None)
        opener=Mock(side_effect=[rate_limit,TimeoutError(SENTINEL),wire_response(completion())])
        result=self.make_model(opener,sleeper=sleeper).complete('system',[],[])
        self.assertEqual(opener.call_count,3)
        self.assertEqual([c.args[0] for c in sleeper.call_args_list],[3,2])
        self.assertEqual(result['usage']['http_attempts'],3)
        for error in (urllib.error.HTTPError('https://redacted',401,SENTINEL,{},None),RuntimeError(SENTINEL)):
            opener=Mock(side_effect=error)
            with self.assertRaises(ProviderError) as caught:self.make_model(opener).complete('system',[],[])
            self.assertEqual(opener.call_count,1)
            self.assertNotIn(SENTINEL,str(caught.exception))

    def test_exhausted_retries_sanitized_exception(self):
        opener=Mock(side_effect=urllib.error.URLError(SENTINEL))
        try:self.make_model(opener).complete('system',[],[])
        except ProviderError as error:
            self.assertNotIn(SENTINEL,traceback.format_exc()+repr(error)+json.dumps(error.usage))
            self.assertEqual(error.usage['http_attempts'],3)
        else:self.fail('Broken transport unexpectedly accepted')

    def test_redaction_in_responses_and_object_snapshot(self):
        data=completion();data['choices'][0]['message']['content']=SENTINEL
        model=self.make_model(Mock(return_value=wire_response(data)))
        result=model.complete('system',[],[])
        self.assertNotIn(SENTINEL,json.dumps(result)+repr(model))

    def test_no_redirect_authorization_forwarding(self):
        from model_provider import NoRedirect
        request=__import__('urllib.request',fromlist=['Request']).Request('https://openrouter.ai',headers={'Authorization':'Bearer '+SENTINEL})
        self.assertIsNone(NoRedirect().redirect_request(request,None,302,'redirect',{},'https://other.example'))

class KeyFallbackTests(unittest.TestCase):
    secondary='dummy-secondary-credential-not-a-real-key'

    def make_model(self,opener,secondary=None,**kwargs):
        env=dict(ENV,OPENROUTER_API_KEY_FALLBACK=self.secondary if secondary is None else secondary)
        with patch.dict(os.environ,env,clear=True):
            return OpenRouterModel(opener=opener,sleeper=kwargs.pop('sleeper',Mock()),**kwargs)

    def error(self,status):
        return urllib.error.HTTPError('https://redacted',status,'sanitized fixture',{},None)

    def assert_phases(self,opener,primary,secondary):
        calls=opener.call_args_list
        self.assertEqual(len(calls),primary+secondary)
        for index,call in enumerate(calls):
            self.assertEqual(call.args[0].get_header('Authorization'),'Bearer '+(SENTINEL if index<primary else self.secondary))
            self.assertEqual(json.loads(call.args[0].data)['model'],ENV['OPENROUTER_MODEL'])
            self.assertEqual(call.args[0].data,calls[0].args[0].data)

    def test_primary_success_never_uses_secondary_and_next_call_starts_primary(self):
        opener=Mock(side_effect=[wire_response(completion()),wire_response(completion())])
        model=self.make_model(opener)
        for _ in range(2):model.complete('system',[],[])
        self.assert_phases(opener,2,0)
        self.assertEqual(model.max_http_attempts,6)

    def test_429_exhausts_primary_then_returns_secondary_response(self):
        data=completion();data['choices'][0]['message']['content']='secondary response'
        opener=Mock(side_effect=[self.error(429) for _ in range(3)]+[wire_response(data),wire_response(completion())])
        model=self.make_model(opener)
        result=model.complete('system',[],[])
        self.assert_phases(opener,3,1)
        self.assertEqual(result['content'][0]['text'],'secondary response')
        self.assertEqual(result['usage']['http_attempts'],4)
        model.complete('system',[],[])
        self.assertEqual(opener.call_args.args[0].get_header('Authorization'),'Bearer '+SENTINEL)

    def test_provider_unavailable_uses_secondary_once(self):
        for status in (408,500,502,503,504):
            with self.subTest(status=status):
                opener=Mock(side_effect=[self.error(status) for _ in range(3)]+[wire_response(completion())])
                self.make_model(opener).complete('system',[],[])
                self.assert_phases(opener,3,1)

    def test_quota_402_uses_secondary_without_retrying_primary(self):
        opener=Mock(side_effect=[self.error(402),wire_response(completion())])
        result=self.make_model(opener).complete('system',[],[])
        self.assert_phases(opener,1,1)
        self.assertEqual(result['usage']['http_attempts'],2)

    def test_permanent_request_auth_and_ambiguous_404_never_fallback(self):
        for status in (400,401,403,404):
            with self.subTest(status=status):
                opener=Mock(side_effect=self.error(status))
                with self.assertRaises(ProviderError):self.make_model(opener).complete('system',[],[])
                self.assert_phases(opener,1,0)

    def test_valid_but_incorrect_answer_never_triggers_fallback(self):
        data=completion();data['choices'][0]['message']['content']='incorrect illustrative decision'
        opener=Mock(return_value=wire_response(data))
        result=self.make_model(opener).complete('system',[],[])
        self.assertNotEqual(result['content'][0]['text'],'expected correct illustrative decision')
        self.assert_phases(opener,1,0)

    def test_both_keys_fail_with_original_sanitized_failure_contract(self):
        opener=Mock(side_effect=[self.error(429) for _ in range(6)])
        with self.assertRaises(ProviderError) as caught:self.make_model(opener).complete('system',[],[])
        self.assert_phases(opener,3,3)
        self.assertEqual(str(caught.exception),'OpenRouter request failed with HTTP 429')
        self.assertEqual(caught.exception.usage['http_attempts'],6)
        self.assertEqual(caught.exception.usage['usage_missing_calls'],1)

    def test_secondary_permanent_failure_does_not_recurse(self):
        opener=Mock(side_effect=[self.error(429) for _ in range(3)]+[self.error(400)])
        with self.assertRaises(ProviderError) as caught:self.make_model(opener).complete('system',[],[])
        self.assert_phases(opener,3,1)
        self.assertIn('HTTP 400',str(caught.exception))
        self.assertEqual(caught.exception.usage['http_attempts'],4)

    def test_secondary_application_error_keeps_total_attempt_count_and_does_not_recurse(self):
        opener=Mock(side_effect=[self.error(429) for _ in range(3)]+[RuntimeError('fixture application error')])
        with self.assertRaises(ProviderError) as caught:self.make_model(opener).complete('system',[],[])
        self.assert_phases(opener,3,1)
        self.assertEqual(caught.exception.usage['http_attempts'],4)

    def test_timeout_and_connection_failure_are_availability_failures(self):
        for error in (TimeoutError('fixture'),urllib.error.URLError('fixture'),OSError('fixture')):
            with self.subTest(error_type=type(error).__name__):
                opener=Mock(side_effect=[error]*3+[wire_response(completion())])
                self.make_model(opener).complete('system',[],[])
                self.assert_phases(opener,3,1)

    def test_malformed_output_invalid_tool_arguments_and_application_errors_do_not_fallback(self):
        for response in (io.BytesIO(b'not JSON'),wire_response({}),wire_response(completion('read','{broken'))):
            opener=Mock(return_value=response)
            try:self.make_model(opener).complete('system',[],[TOOL])
            except ProviderError:pass
            self.assert_phases(opener,1,0)
        opener=Mock(side_effect=RuntimeError('fixture application error'))
        with self.assertRaises(ProviderError):self.make_model(opener).complete('system',[],[])
        self.assert_phases(opener,1,0)
        opener=Mock()
        with self.assertRaises(ProviderError):self.make_model(opener).complete('system',[],[{}])
        opener.assert_not_called()
        opener=Mock()
        with patch('model_provider.urllib.request.Request',side_effect=ValueError(self.secondary)):
            with self.assertRaises(ProviderError) as caught:self.make_model(opener).complete('system',[],[])
        self.assertNotIn(self.secondary,str(caught.exception));opener.assert_not_called()

    def test_secondary_malformed_response_fails_without_another_key_phase(self):
        opener=Mock(side_effect=[self.error(429) for _ in range(3)]+[wire_response({})])
        with self.assertRaises(ProviderError) as caught:self.make_model(opener).complete('system',[],[])
        self.assert_phases(opener,3,1)
        self.assertEqual(caught.exception.usage['http_attempts'],4)

    def test_both_credentials_redacted_from_payload_response_and_diagnostics(self):
        data=completion();data['choices'][0]['message']['content']=SENTINEL+' '+self.secondary
        opener=Mock(return_value=wire_response(data));model=self.make_model(opener)
        result=model.complete(SENTINEL+' '+self.secondary,[],[])
        diagnostics=json.dumps(result)+repr(model)+opener.call_args.args[0].data.decode()+json.dumps(model._redact({self.secondary:SENTINEL}))
        for credential in (SENTINEL,self.secondary):self.assertNotIn(credential,diagnostics)
        for credential in (SENTINEL,self.secondary):
            opener=Mock(side_effect=urllib.error.URLError(credential))
            try:self.make_model(opener).complete('system',[],[])
            except ProviderError as error:
                self.assertNotIn(credential,traceback.format_exc()+repr(error)+json.dumps(error.usage))
            else:self.fail('Failure unexpectedly accepted')

    def test_secondary_credentials_cannot_be_embedded_in_model_or_base_url(self):
        for kwargs in ({'model':self.secondary},{'base_url':'https://proxy.example/'+self.secondary}):
            with self.assertRaises(ValueError):self.make_model(Mock(),**kwargs)

    def test_duplicate_secondary_is_disabled_and_long_retry_after_remains_bounded(self):
        opener=Mock(side_effect=self.error(429));model=self.make_model(opener,secondary=SENTINEL)
        with self.assertRaises(ProviderError):model.complete('system',[],[])
        self.assert_phases(opener,3,0)
        self.assertEqual(model.max_http_attempts,3)
        error=urllib.error.HTTPError('https://redacted',429,'fixture',{'Retry-After':'120'},None)
        opener=Mock(side_effect=[error,wire_response(completion())]);sleeper=Mock()
        self.make_model(opener,sleeper=sleeper).complete('system',[],[])
        self.assert_phases(opener,1,1);sleeper.assert_not_called()

class TerminalRateLimitTests(unittest.TestCase):
    secondary=KeyFallbackTests.secondary
    make_model=KeyFallbackTests.make_model
    assert_phases=KeyFallbackTests.assert_phases
    daily='Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day'

    def quota_error(self,message=None,status=429,raw=None,headers=None):
        body=raw if raw is not None else json.dumps({'error':{'code':status,'message':message or self.daily}}).encode()
        return urllib.error.HTTPError('https://redacted',status,'fixture',headers or {},io.BytesIO(body))

    def test_terminal_single_key_stops_after_one_attempt(self):
        opener=Mock(side_effect=self.quota_error());sleeper=Mock()
        with self.assertRaises(ProviderError) as caught:
            self.make_model(opener,secondary='',sleeper=sleeper).complete('system',[],[])
        self.assert_phases(opener,1,0);sleeper.assert_not_called()
        self.assertTrue(caught.exception.availability_failure)
        self.assertEqual(caught.exception.usage['http_attempts'],1)

    def test_terminal_primary_returns_fallback_response_same_payload(self):
        opener=Mock(side_effect=[self.quota_error(),wire_response(completion())]);sleeper=Mock()
        result=self.make_model(opener,sleeper=sleeper).complete('system',[dict(role='user',content='evidence')],[TOOL])
        self.assert_phases(opener,1,1);sleeper.assert_not_called()
        self.assertEqual(result['usage']['http_attempts'],2)
        self.assertEqual(result['content'][0]['text'],'result')

    def test_both_terminal_stops_each_key_once_with_existing_failure(self):
        opener=Mock(side_effect=[self.quota_error(),self.quota_error()]);sleeper=Mock()
        with self.assertRaises(ProviderError) as caught:
            self.make_model(opener,sleeper=sleeper).complete('system',[],[])
        self.assert_phases(opener,1,1);sleeper.assert_not_called()
        self.assertEqual(str(caught.exception),'OpenRouter request failed with HTTP 429')
        self.assertEqual(caught.exception.usage,dict(http_attempts=2,usage_missing_calls=1))

    def test_terminal_primary_preserves_transient_fallback_retries(self):
        opener=Mock(side_effect=[self.quota_error(),self.quota_error('Too many requests'),wire_response(completion())]);sleeper=Mock()
        result=self.make_model(opener,sleeper=sleeper).complete('system',[],[])
        self.assert_phases(opener,1,2)
        self.assertEqual(result['usage']['http_attempts'],3)
        self.assertEqual([c.args[0] for c in sleeper.call_args_list],[1])

    def test_transient_primary_then_terminal_fallback(self):
        opener=Mock(side_effect=[self.quota_error('Too many requests') for _ in range(3)]+[self.quota_error()]);sleeper=Mock()
        with self.assertRaises(ProviderError):self.make_model(opener,sleeper=sleeper).complete('system',[],[])
        self.assert_phases(opener,3,1)
        self.assertEqual([c.args[0] for c in sleeper.call_args_list],[1,2])

    def test_transient_primary_retry_after_then_success_no_fallback(self):
        opener=Mock(side_effect=[self.quota_error('Rate limit exceeded',headers={'Retry-After':'3'}),wire_response(completion())]);sleeper=Mock()
        result=self.make_model(opener,sleeper=sleeper).complete('system',[],[])
        self.assert_phases(opener,2,0)
        self.assertEqual([c.args[0] for c in sleeper.call_args_list],[3])
        self.assertEqual(result['usage']['http_attempts'],2)

    def test_ambiguous_malformed_and_unrelated_bodies_preserve_retries(self):
        bodies=[b'not JSON',b'{"error":',b'[]',b'{"error":{"message":null}}',
                b'{"message":"Daily quota exhausted"}']
        bodies.extend(json.dumps({'error':{'message':m}}).encode() for m in
                      ('Quota exceeded','Daily quota not exhausted','The output token limit is 2400'))
        for body in bodies:
            with self.subTest(body=body):
                opener=Mock(side_effect=[self.quota_error(raw=body) for _ in range(3)]+[wire_response(completion())])
                self.make_model(opener).complete('system',[],[])
                self.assert_phases(opener,3,1)

    def test_primary_success_never_fallback_and_next_call_starts_primary(self):
        opener=Mock(side_effect=[self.quota_error(),wire_response(completion()),wire_response(completion())])
        model=self.make_model(opener);model.complete('system',[],[]);model.complete('system',[],[])
        keys=[c.args[0].get_header('Authorization') for c in opener.call_args_list]
        self.assertEqual(keys,['Bearer '+SENTINEL,'Bearer '+self.secondary,'Bearer '+SENTINEL])

    def test_non429_statuses_ignore_terminal_body(self):
        for status in (400,401,403,404,402,408,500,502,503,504):
            with self.subTest(status=status):
                errors=[self.quota_error(status=status) for _ in range(3 if status in (408,500,502,503,504) else 1)]
                for e in errors:e.fp.read=Mock(wraps=e.fp.read)
                if status in (400,401,403,404):
                    opener=Mock(side_effect=errors)
                    with self.assertRaises(ProviderError):self.make_model(opener).complete('system',[],[])
                    self.assert_phases(opener,1,0)
                else:
                    opener=Mock(side_effect=errors+[wire_response(completion())])
                    self.make_model(opener).complete('system',[],[])
                    self.assert_phases(opener,len(errors),1)
                for e in errors:e.fp.read.assert_called_once_with(16385)

    def test_tool_and_application_failures_never_trigger_fallback(self):
        opener=Mock(return_value=wire_response(completion('read','{broken')))
        result=self.make_model(opener).complete('system',[],[TOOL])
        self.assertIn('argument_error',result['content'][0]);self.assert_phases(opener,1,0)
        for data in ({'error':{'message':self.daily}},{}):
            opener=Mock(return_value=wire_response(data))
            with self.assertRaises(ProviderError) as caught:self.make_model(opener).complete('system',[],[])
            self.assertFalse(caught.exception.availability_failure);self.assert_phases(opener,1,0)

    def test_financial_validation_and_tool_errors_do_not_switch_keys(self):
        from financial_agent import run_agent_loop
        from financial_tools import FinancialTools
        from test_tools import FakeRepository,REQ
        steps=[('retrieve_evidence',{}),('apply_evidence_amendments',{'amendments':[{}]}),
               ('reconstruct_finances',{}),('evaluate_payment_plans',{}),('finish_decision',{})]
        opener=Mock(side_effect=[wire_response(completion(n,json.dumps(a))) for n,a in steps])
        model=self.make_model(opener);request=dict(REQ,requested_amount='700')
        tools=FinancialTools(FakeRepository(),request,None)
        result=run_agent_loop(model,tools,request,tools.fallback)
        self.assertEqual(result['trace'][1]['result']['error']['code'],'invalid_tool_arguments')
        self.assertEqual(result['row']['recommended_payment_method'],'not_recommended')
        self.assertEqual(opener.call_count,5)
        self.assertTrue(all(c.args[0].get_header('Authorization')=='Bearer '+SENTINEL for c in opener.call_args_list))

    def test_primary_200_never_activates_fallback(self):
        opener=Mock(return_value=wire_response(completion()))
        self.make_model(opener).complete('system',[],[]);self.assert_phases(opener,1,0)

    def test_oversized_error_body_does_not_establish_terminal_quota(self):
        from model_provider import MAX_RATE_LIMIT_BODY_BYTES
        body=json.dumps({'error':{'message':self.daily},'padding':'x'*(MAX_RATE_LIMIT_BODY_BYTES+1)}).encode()
        errors=[self.quota_error(raw=body) for _ in range(3)]
        for e in errors:e.fp.read=Mock(wraps=e.fp.read)
        opener=Mock(side_effect=errors+[wire_response(completion())])
        self.make_model(opener).complete('system',[],[]);self.assert_phases(opener,3,1)
        for e in errors:e.fp.read.assert_called_once_with(MAX_RATE_LIMIT_BODY_BYTES+1)

    def test_deeply_nested_error_json_is_unknown_and_preserves_retries(self):
        from model_provider import classify_rate_limit
        raw=b'['*2000+b'0'+b']'*2000
        with patch('model_provider.json.loads',side_effect=RecursionError('nested error response')):
            self.assertEqual(classify_rate_limit(raw),'UNKNOWN')
        self.assertEqual(classify_rate_limit(raw),'UNKNOWN')
        opener=Mock(side_effect=[self.quota_error(raw=raw) for _ in range(3)]+[wire_response(completion())])
        self.make_model(opener).complete('system',[],[]);self.assert_phases(opener,3,1)

    def test_classifier_explicit_terminal_patterns_case_insensitive(self):
        from model_provider import classify_rate_limit
        for message in (self.daily,'DAILY LIMIT REACHED','Daily quota exhausted',
                        'API key quota exceeded','Insufficient quota','Limit reached for the API key',
                        'Usage limit reached for this API key'):
            with self.subTest(message=message):
                self.assertEqual(classify_rate_limit(json.dumps({'error':{'message':message}}).encode()),'TERMINAL_KEY_QUOTA')

    def test_classifier_does_not_guess_from_generic_or_unrelated_words(self):
        from model_provider import classify_rate_limit
        for message in ('Quota exceeded','Usage limit reached','Daily quota not exhausted',
                        'The output token limit is 2400; quota remains available',
                        'Daily limit reached? No, retry after a second',
                        'Documentation mentions daily quota exhausted as an example'):
            with self.subTest(message=message):
                self.assertNotEqual(classify_rate_limit(json.dumps({'error':{'message':message}})),'TERMINAL_KEY_QUOTA')
        self.assertEqual(classify_rate_limit(b'{"error":{"message":"Too many requests"}}'),'TRANSIENT_RATE_LIMIT')
        self.assertEqual(classify_rate_limit(b'not JSON'),'UNKNOWN')

    def test_body_read_failure_preserves_unknown_retry_contract(self):
        errors=[self.quota_error() for _ in range(3)]
        for e in errors:e.fp.read=Mock(side_effect=OSError(SENTINEL))
        opener=Mock(side_effect=errors+[wire_response(completion())])
        self.make_model(opener).complete('system',[],[]);self.assert_phases(opener,3,1)

    def test_terminal_error_body_secrets_never_reach_diagnostics(self):
        message=self.daily+' '+SENTINEL+' '+self.secondary
        opener=Mock(side_effect=[self.quota_error(message),self.quota_error(message)])
        try:self.make_model(opener).complete('system',[],[])
        except ProviderError as error:
            rendered=traceback.format_exc()+repr(error)+json.dumps(error.usage)
            for key in (SENTINEL,self.secondary):self.assertNotIn(key,rendered)
        else:self.fail('Terminal quota unexpectedly succeeded')
        self.assert_phases(opener,1,1)

class ReleaseDiagnosticsTests(unittest.TestCase):
    secondary=KeyFallbackTests.secondary
    make_model=KeyFallbackTests.make_model
    assert_phases=KeyFallbackTests.assert_phases
    quota_error=TerminalRateLimitTests.quota_error
    daily=TerminalRateLimitTests.daily

    def test_primary_success_has_measured_attempt_usage_without_credentials(self):
        result=self.make_model(Mock(return_value=wire_response(completion()))).complete('system',[],[])
        events=result['http_events'];self.assertEqual(len(events),1)
        e=events[0]
        self.assertEqual((e['key_phase'],e['status'],e['attempt'],e['modality']),('primary',200,1,'text_only'))
        self.assertEqual((e['input_tokens'],e['output_tokens'],e['total_tokens']),(100,20,120))
        self.assertEqual(e['reported_cost_usd'],0.003)
        self.assertGreaterEqual(e['elapsed_seconds'],0)
        self.assertNotIn(SENTINEL,json.dumps(events))

    def test_terminal_primary_then_fallback_events_and_bytes(self):
        opener=Mock(side_effect=[self.quota_error(),wire_response(completion())])
        result=self.make_model(opener).complete('system',[],[]);self.assert_phases(opener,1,1)
        events=result['http_events']
        self.assertEqual([e['status'] for e in events],[429,200])
        self.assertEqual([e['key_phase'] for e in events],['primary','fallback'])
        self.assertEqual(events[0]['failure_category'],'TERMINAL_KEY_QUOTA')
        self.assertIsNone(events[0]['input_tokens'])

    def test_image_400_safe_nested_error_is_available_no_fallback(self):
        data={'error':{'code':400,'message':'Provider returned error',
              'metadata':{'raw':json.dumps({'error':{'type':'invalid_request_error',
                   'message':'Image content is unsupported '+SENTINEL+' '+self.secondary+' person@example.com'}})}}}
        opener=Mock(side_effect=self.quota_error(status=400,raw=json.dumps(data).encode()))
        image=dict(type='image',source=dict(type='base64',media_type='image/png',data='opaque-pixels'))
        with self.assertRaises(ProviderError) as caught:
            self.make_model(opener).complete('system',[dict(role='user',content=[image])],[])
        self.assert_phases(opener,1,0)
        e=caught.exception.http_events[0]
        self.assertEqual((e['status'],e['modality']),(400,'image'))
        self.assertIn('unsupported',e['provider_message'])
        rendered=json.dumps(e)
        for value in (SENTINEL,self.secondary,'person@example.com','opaque-pixels'):
            self.assertNotIn(value,rendered)
        self.assertNotIn('Authorization',rendered)

    def test_transient_retry_diagnostics_preserve_policy(self):
        opener=Mock(side_effect=[self.quota_error('Too many requests'),wire_response(completion())]);sleeper=Mock()
        result=self.make_model(opener,sleeper=sleeper).complete('system',[],[])
        self.assert_phases(opener,2,0);sleeper.assert_called_once_with(1)
        self.assertEqual([e['status'] for e in result['http_events']],[429,200])

    def test_network_failure_diagnostics_have_no_exception_text(self):
        opener=Mock(side_effect=urllib.error.URLError(SENTINEL+' person@example.com'))
        with self.assertRaises(ProviderError) as caught:self.make_model(opener).complete('system',[],[])
        self.assert_phases(opener,3,3)
        events=caught.exception.http_events
        self.assertEqual(len(events),6)
        self.assertTrue(all(e['failure_category']=='NETWORK' for e in events))
        self.assertNotIn(SENTINEL,json.dumps(events))
        self.assertNotIn('person@example.com',json.dumps(events))

    def test_invalid_200_response_keeps_status_and_available_usage(self):
        data=completion();data['choices']=[]
        with self.assertRaises(ProviderError) as caught:
            self.make_model(Mock(return_value=wire_response(data))).complete('system',[],[])
        e=caught.exception.http_events[0]
        self.assertEqual(e['status'],200)
        self.assertEqual(e['input_tokens'],100)
        self.assertEqual(e['failure_category'],'APPLICATION')

    def test_agent_preserves_events_on_success_and_failure(self):
        from financial_agent import run_agent_loop
        from financial_tools import FinancialTools
        from test_tools import FakeRepository,REQ
        steps=['retrieve_evidence','reconstruct_finances','evaluate_payment_plans','finish_decision']
        opener=Mock(side_effect=[wire_response(completion(name)) for name in steps])
        tools=FinancialTools(FakeRepository(),REQ,None)
        result=run_agent_loop(self.make_model(opener),tools,REQ,tools.fallback)
        self.assertEqual(len(result['http_events']),4)
        self.assertTrue(all(e['request_id']==REQ['request_id'] for e in result['http_events']))
        opener=Mock(side_effect=[self.quota_error(),self.quota_error()])
        tools=FinancialTools(FakeRepository(),REQ,None)
        result=run_agent_loop(self.make_model(opener),tools,REQ,tools.fallback)
        self.assertEqual([e['status'] for e in result['http_events']],[429,429])
        self.assertEqual(result['usage']['http_attempts'],2)

if __name__=='__main__':unittest.main()
