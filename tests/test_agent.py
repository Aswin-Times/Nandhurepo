import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from financial_agent import run_agent_loop

class ScriptedModel:
    def __init__(self,names): self.names=iter(names); self.calls=0
    def complete(self,system,messages,tools):
        self.calls+=1
        name,args=next(self.names)
        return dict(content=[dict(type='tool_use',id=str(self.calls),name=name,input=args)],
                    usage=dict(input_tokens=10,output_tokens=5), stop_reason='tool_use')

class FakeTools:
    definitions=[]
    def __init__(self): self.amount=0; self.calls=[]
    def dispatch(self,name,args):
        self.calls.append(name)
        if name=='evidence': self.amount=100; return {'evidence':'salary confirmed'}
        if name=='finish': return {'row':{'amount_safe_to_pay':self.amount}}
        raise ValueError('unsupported test tool')

class AgentTests(unittest.TestCase):
    def test_model_decides_repeated_tool_calls(self):
        tools=FakeTools()
        model=ScriptedModel([('evidence',{}),('evidence',{}),('finish',{})])
        result=run_agent_loop(model,tools,{},lambda why:{'fallback':why})
        self.assertEqual(result['row']['amount_safe_to_pay'],100)
        self.assertEqual(tools.calls,['evidence','evidence','finish'])
        self.assertEqual(result['usage']['input_tokens'],30)

    def test_evidence_counterfactual(self):
        result=run_agent_loop(ScriptedModel([('finish',{})]),FakeTools(),{},lambda why:{'fallback':why})
        self.assertEqual(result['row']['amount_safe_to_pay'],0)

    def test_cap_explicit_fallback(self):
        result=run_agent_loop(ScriptedModel([('evidence',{})]*3),FakeTools(),{},lambda why:{'fallback':why},max_steps=2)
        self.assertIn('step cap',result['row']['fallback'])

    def test_tool_error_is_structured_then_model_recovers(self):
        tools=FakeTools()
        result=run_agent_loop(ScriptedModel([('invalid',{}),('finish',{})]),tools,{},lambda why:{'fallback':why})
        self.assertEqual(result['trace'][0]['result']['error']['code'],'invalid_tool_arguments')
        self.assertIn('row',result)
    def test_unexpected_tool_failure_preserves_usage(self):
        class BrokenTools(FakeTools):
            def dispatch(self,name,args):raise RuntimeError('implementation defect')
        result=run_agent_loop(ScriptedModel([('evidence',{})]),BrokenTools(),{},lambda why:{'fallback':why},max_steps=1)
        self.assertEqual(result['usage']['input_tokens'],10)
        self.assertEqual(result['trace'][0]['result']['error']['code'],'internal_tool_error')

if __name__=='__main__': unittest.main()
