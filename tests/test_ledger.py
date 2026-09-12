import sys
import unittest
from pathlib import Path
from decimal import Decimal as D

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code'))
from financial_ledger import Ledger, CashFlow, choose_plan

class LedgerTests(unittest.TestCase):
    def test_capacity_accounts_for_future_trough(self):
        ledger = Ledger('2026-01-01', D('1000'), D('200'), [
            CashFlow('2026-01-03', D('-300'), 'rent'),
            CashFlow('2026-01-05', D('600'), 'salary')])
        self.assertEqual(ledger.capacity('2026-01-01'), D('500'))
        self.assertEqual(ledger.earliest(D('700')), '2026-01-05')
        self.assertFalse(ledger.verify([('2026-01-01', D('501'))])['safe'])
        self.assertTrue(ledger.verify([('2026-01-01', D('500'))])['safe'])

    def test_same_day_debits_precede_salary(self):
        ledger = Ledger('2026-01-01', D('500'), D('200'), [
            CashFlow('2026-01-02', D('500'), 'salary'),
            CashFlow('2026-01-02', D('-400'), 'rent')])
        self.assertFalse(ledger.verify([])['safe'])

    def test_partial_exact_shape_and_preferences(self):
        ledger = Ledger('2026-01-01', D('1000'), D('200'), [
            CashFlow('2026-01-03', D('-300'), 'rent'),
            CashFlow('2026-01-05', D('600'), 'salary')])
        request = dict(request_id='arbitrary-id', request_date='2026-01-01',
                       requested_amount='700', desired_completion_date='2026-01-10',
                       allows_partial_payment='true')
        profile = dict(payment_methods_user_will_consider='full_payment|partial_payment',
                       max_installment_months='')
        plan = choose_plan(ledger, request, profile, [])
        self.assertEqual(plan['method'], 'partial_payment')
        self.assertEqual(plan['payments'], [('2026-01-01', D('500')), ('2026-01-05', D('200'))])
        profile['payment_methods_user_will_consider'] = 'installments'
        self.assertIsNone(choose_plan(ledger, request, profile, []))

    def test_installment_fee_schedule_cap_and_deadline(self):
        ledger = Ledger('2026-01-01', D('1000'), D('200'), [])
        req = dict(request_date='2026-01-01', requested_amount='700',
                   desired_completion_date='2026-03-15', allows_partial_payment='false')
        profile = dict(payment_methods_user_will_consider='installments', max_installment_months='3')
        option = dict(payment_option_id='offer-A', payment_method='installments',
                      payment_amount='250', number_of_payments='3', first_payment_date='2026-01-02',
                      payment_frequency_days='30', financing_fee='50', total_payable_amount='750')
        plan = choose_plan(ledger, req, profile, [option])
        self.assertEqual(plan['payments'][-1], ('2026-03-03', D('250')))
        profile['max_installment_months'] = '2'
        self.assertIsNone(choose_plan(ledger, req, profile, [option]))

    def test_audit_negative_control(self):
        ledger = Ledger('2026-01-01', D('100'), D('50'), [])
        self.assertFalse(ledger.verify([('2026-01-01', D('51'))])['safe'])

if __name__ == '__main__':
    unittest.main()
