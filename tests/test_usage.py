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
    def test_budget_checked_before_network(self):
        provider=MockProvider();budget=BudgetedModel(provider,0.001,10,20)
        with self.assertRaises(RuntimeError):budget.complete('test',[],[])
        self.assertEqual(provider.calls,0)
    def test_usage_totals_correspond_to_rows(self):
        records=[dict(usage=dict(input_tokens=100,output_tokens=50,model_calls=2))]*2
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'usage_report.md'
            result=write_usage_report(path,records,'anthropic','fixture',10,20,'abc','def')
            self.assertEqual(result['total_tokens'],300)
            self.assertEqual(result['average_tokens_per_request'],150)
            self.assertEqual(result['estimated_cost_usd'],0.004)
            self.assertIn('abc',path.read_text())
if __name__=='__main__':unittest.main()
