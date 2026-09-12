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

if __name__=='__main__':unittest.main()
