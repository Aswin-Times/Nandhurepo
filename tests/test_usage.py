import sys
import unittest
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from model_usage import BudgetedModel,write_usage_report

class MockProvider:
    calls=0
    def complete(self,*args):
        self.calls+=1
        return dict(content=[],usage=dict(input_tokens=100,output_tokens=50))

class UsageTests(unittest.TestCase):
    def test_budget_uses_reported_charge_and_persists_failed_reservation(self):
        from model_provider import ProviderError
        from model_usage import aggregate_usage,reconciled_cost
        provider=MockProvider()
        provider.complete=lambda *args:dict(content=[],usage=dict(input_tokens=100,output_tokens=50,reported_cost_usd=0.5,cost_reported_calls=1))
        budget=BudgetedModel(provider,1,1,2)
        result=budget.complete('test',[],[])
        self.assertEqual(float(budget.used),0.5)
        usage=dict(result['usage'],model_calls=1)
        self.assertEqual(float(reconciled_cost(usage,1,2)),0.5)
        def fail(*args):raise ProviderError('sanitized',dict(http_attempts=1,usage_missing_calls=1))
        provider.complete=fail
        with self.assertRaises(ProviderError) as caught:budget.complete('test',[],[])
        charge=caught.exception.usage['budget_cost_usd']
        combined=aggregate_usage([dict(usage=usage),dict(usage=dict(caught.exception.usage,model_calls=1))])
        self.assertAlmostEqual(combined['budget_cost_usd'],0.5+charge)
    def test_report_separates_measured_charge_estimated_cost_and_missing_usage(self):
        records=[dict(usage=dict(input_tokens=100,output_tokens=20,model_calls=1,
                     reported_cost_usd=0.003,cost_reported_calls=1,usage_missing_calls=0,http_attempts=1)),
                 dict(usage=dict(model_calls=1,usage_missing_calls=1,http_attempts=1))]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'usage.md'
            result=write_usage_report(path,records,'openrouter','fixture/model',1,2,'fp','hash')
            self.assertEqual(result['reported_cost_usd'],0.003)
            self.assertAlmostEqual(result['estimated_cost_usd'],0.00014)
            self.assertFalse(result['usage_complete'])
            self.assertIn('INCOMPLETE',path.read_text())
            self.assertIn('1/2',path.read_text())
    def test_budget_checked_before_network(self):
        provider=MockProvider();budget=BudgetedModel(provider,0.001,10,20)
        with self.assertRaises(RuntimeError):budget.complete('test',[],[])
        self.assertEqual(provider.calls,0)
    def test_usage_totals_correspond_to_rows(self):
        records=[dict(usage=dict(input_tokens=100,output_tokens=50,model_calls=2))]*2
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'usage_report.md'
            result=write_usage_report(path,records,'openrouter','fixture',10,20,'abc','def')
            self.assertEqual(result['total_tokens'],300)
            self.assertEqual(result['average_tokens_per_request'],150)
            self.assertEqual(result['estimated_cost_usd'],0.004)
            self.assertIn('abc',path.read_text())
if __name__=='__main__':unittest.main()
