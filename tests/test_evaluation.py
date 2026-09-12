import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from evaluate_submission import compare_rows,blast_radius

class EvaluationTests(unittest.TestCase):
    def test_negative_control_corrupt_amount_enum_and_missing_row(self):
        expected=[dict(request_id='x',amount_safe_to_pay='100',affordability_status='affordable_now',
                       recommended_payment_method='full_payment',payment_plan='2026-01-01:100',
                       earliest_date_for_full_payment='2026-01-01',spending_changes_needed='none')]
        self.assertEqual(compare_rows(expected,expected)['amount_mae'],0)
        bad=[dict(expected[0],amount_safe_to_pay='50',affordability_status='not_affordable')]
        result=compare_rows(expected,bad)
        self.assertEqual(result['amount_mae'],50)
        self.assertEqual(result['exact_matches']['affordability_status'],0)
        self.assertEqual(compare_rows(expected,[])['missing'],['x'])
        self.assertEqual(blast_radius(expected,bad)['changed_cells'],2)
if __name__=='__main__':unittest.main()
