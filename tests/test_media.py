import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code'))
from evidence_media import extract_amount

class MediaTests(unittest.TestCase):
    def test_net_salary_over_gross(self):
        self.assertEqual(extract_amount(['Salary IDR 4,500,000','Total Earnings IDR 4,780,800',
                                        'Net Pay IDR 4,365,000'], 'salary'), '4365000')
    def test_final_total_over_tax(self):
        self.assertEqual(extract_amount(['Subtotal 1,000.00','Tax 100.00','Grand Total INR 1,100.00']), '1100')
    def test_missing_or_ambiguous_not_zero(self):
        with self.assertRaises(ValueError): extract_amount(['Thanks for visiting'])
    def test_pixels_counterfactual(self):
        self.assertEqual(extract_amount(['Amount Due INR 1200']), '1200')
        with self.assertRaises(ValueError): extract_amount([])
if __name__ == '__main__': unittest.main()
