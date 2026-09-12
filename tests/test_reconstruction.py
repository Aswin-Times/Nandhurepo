import sys
import unittest
from pathlib import Path
from decimal import Decimal as D
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code'))
from financial_reconstruction import reconstruct
from dataset_repository import DatasetRepository

def event(eid, day, amount, direction='debit', status='settled', category='rent', **kw):
    return dict(event_id=eid, settlement_date=day, event_date=day, amount=amount,
                direction=direction, status=status, category=category, description=category,
                currency='USD', linked_event_id='', event_type='expense', flexibility='fixed',
                minimum_allowed_amount='', **kw)

PROFILE = dict(home_currency='USD', current_available_balance='1000', minimum_balance_to_keep='200',
               expense_categories_to_protect='rent', expense_categories_user_is_willing_to_stop='',
               expense_categories_user_is_willing_to_reduce='')

class ReconstructionTests(unittest.TestCase):
    def test_history_not_replayed_pending_debit_reserved(self):
        rows = [event('old', '2025-12-01', '100'), event('pending', '2026-01-03', '100', status='pending'),
                event('refund', '2026-01-03', '999', 'credit', 'pending', 'refund'),
                event('valuation', '2026-01-03', '999', 'credit', 'unrealized', 'investment')]
        state = reconstruct('2026-01-01', PROFILE, rows, [], {})
        self.assertEqual(state.ledger.capacity('2026-01-01'), D('700'))
        self.assertEqual(len(state.ledger.flows), 1)

    def test_recurrence_and_duplicate_representations(self):
        rows = [event('a', '2025-10-02', '100'), event('b', '2025-11-02', '100'),
                event('c', '2025-12-02', '100'),
                event('d', '2025-12-02', '100')]
        rows[-1]['linked_event_id'] = 'c'
        state = reconstruct('2026-01-01', PROFILE, rows, [], {})
        self.assertEqual([f.day for f in state.ledger.flows], ['2026-01-02','2026-02-02','2026-03-02'])
        self.assertEqual(state.ledger.capacity('2026-01-01'), D('500'))

    def test_one_off_income_does_not_recur(self):
        row = event('windfall', '2025-12-15', '900', 'credit', 'settled', 'windfall')
        row['description'] = 'Prize proceeds'
        state = reconstruct('2026-01-01', PROFILE, [row], [], {})
        self.assertEqual(state.ledger.capacity('2026-01-01'), D('800'))

    def test_foreign_settlement_direction(self):
        row = event('fx', '2026-01-04', '100', status='pending')
        row['currency'] = 'EUR'
        state = reconstruct('2026-01-01', PROFILE, [row], [], {('2026-01-04','EUR','USD'):D('1.2')})
        self.assertEqual(state.ledger.capacity('2026-01-01'), D('680'))
        with self.assertRaises(ValueError):
            reconstruct('2026-01-01', PROFILE, [row], [], {})

    def test_blank_amount_fails_closed(self):
        with self.assertRaises(ValueError):
            reconstruct('2026-01-01', PROFILE, [event('missing','2026-01-02','')], [], {})

    def test_confirmed_foreign_salary_uses_each_settlement_rate(self):
        row=event('confirmed','2026-01-15','100','credit','scheduled','salary')
        row.update(currency='EUR',description='Next confirmed salary')
        rates={(day,'EUR','USD'):D(rate) for day,rate in
               [('2026-01-15','1.1'),('2026-02-15','1.2'),('2026-03-15','1.3')]}
        state=reconstruct('2026-01-01',PROFILE,[row],[],rates)
        self.assertEqual([f.amount for f in state.ledger.flows],[D('110'),D('120'),D('130')])
        del rates[('2026-02-15','EUR','USD')]
        with self.assertRaisesRegex(ValueError,'Missing settlement-date FX rate'):
            reconstruct('2026-01-01',PROFILE,[row],[],rates)

    def test_inferred_foreign_expense_uses_nominal_amount_and_future_rates(self):
        rows=[event('rent'+str(i),day,'100') for i,day in enumerate(
            ['2025-10-02','2025-11-02','2025-12-02'])]
        for row in rows: row['currency']='EUR'
        rates={(row['settlement_date'],'EUR','USD'):D('1.9') for row in rows}
        rates.update({(day,'EUR','USD'):D(rate) for day,rate in
                      [('2026-01-02','1.1'),('2026-02-02','1.2'),('2026-03-02','1.3')]})
        state=reconstruct('2026-01-01',PROFILE,rows,[],rates)
        self.assertEqual([f.amount for f in state.ledger.flows],[D('-110'),D('-120'),D('-130')])

    def test_fx_rate_precision_is_not_currency_precision(self):
        repository=DatasetRepository(Path(__file__).resolve().parents[1]/'dataset')
        import csv
        with (repository.dataset/'exchange_rates.csv').open(encoding='utf-8-sig') as f:
            for rate in csv.DictReader(f):
                key=(rate['rate_date'],rate['from_currency'],rate['to_currency'])
                self.assertEqual(repository.rates[key],D(rate['rate']))

    def test_next_confirmed_salary_supersedes_inferred_payroll(self):
        rows=[event('pay'+str(i),day,'100','credit','settled','salary') for i,day in enumerate(
            ['2025-10-15','2025-11-15','2025-12-15'])]
        rows.append(event('confirmed','2026-01-15','200','credit','scheduled','salary'))
        rows[-1]['description']='Next confirmed salary'
        state=reconstruct('2026-01-01',PROFILE,rows,[],{})
        credits=[f for f in state.ledger.flows if f.amount>0]
        self.assertEqual(len(credits),3)
        self.assertEqual(sum(f.amount for f in credits),D('600'))

    def test_final_payroll_ends_historic_salary(self):
        rows=[event('pay'+str(i),day,'100','credit','settled','salary') for i,day in enumerate(
            ['2025-09-15','2025-10-15','2025-11-15'])]
        rows.append(event('final','2025-12-15','100','credit','settled','salary'))
        rows[-1]['description']='Final employer payroll'
        state=reconstruct('2026-01-01',PROFILE,rows,[],{})
        self.assertFalse(any(f.amount>0 for f in state.ledger.flows))

    def test_amendment_preserves_unaffected_pay_cycles(self):
        rows=[event('pay'+str(i),day,'100','credit','settled','salary') for i,day in enumerate(
            ['2025-10-15','2025-11-15','2025-12-15'])]
        amendment=dict(evidence_id='employer',operation='replace_recurring',target_event_id='pay2',
                       amount='200',day=15,effective_date='2026-02-15')
        state=reconstruct('2026-01-01',PROFILE,rows,[],{},amendments=[amendment])
        self.assertEqual([(f.day,f.amount) for f in state.ledger.flows],
                         [('2026-01-15',D('100')),('2026-02-15',D('200')),('2026-03-15',D('200'))])

    def test_context_order_and_id_shape_do_not_change_cash(self):
        rows=[event('opaque/'+str(i),day,'100') for i,day in enumerate(
            ['2025-10-02','2025-11-02','2025-12-02'])]
        a=reconstruct('2026-01-01',PROFILE,rows,[],{})
        b=reconstruct('2026-01-01',PROFILE,list(reversed(rows)),[],{})
        self.assertEqual(a.ledger.capacity('2026-01-01'),b.ledger.capacity('2026-01-01'))

if __name__ == '__main__': unittest.main()
