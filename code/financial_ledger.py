"""Exact-money cash-flow simulator and contract-ranked payment candidates."""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN

D = Decimal
CENT = D('0.01')
HORIZON_DAYS = 90

def money(value):
    result = D(str(value))
    if not result.is_finite():
        raise ValueError('Money must be finite')
    return result.quantize(CENT)

def amount_text(value):
    return format(value, '.2f').rstrip('0').rstrip('.')

@dataclass(frozen=True)
class CashFlow:
    day: str
    amount: Decimal
    evidence_id: str
    category: str = ''
    recurring_id: str = ''

class Ledger:
    def __init__(self, start, opening, minimum, flows):
        self.start = date.fromisoformat(start)
        self.end = self.start + timedelta(days=HORIZON_DAYS)
        self.opening, self.minimum = money(opening), money(minimum)
        self.flows = sorted([f for f in flows if self.start <= date.fromisoformat(f.day) <= self.end],
                            key=lambda f: (f.day, f.amount >= 0, f.evidence_id))

    def trajectory(self, payments=()):
        grouped = {}
        for f in self.flows:
            grouped.setdefault(f.day, []).append((f.amount, f.evidence_id))
        for day, amount in payments:
            if amount < 0 or not self.start <= date.fromisoformat(day) <= self.end:
                raise ValueError('Payment must be nonnegative and inside forecast')
            grouped.setdefault(day, []).append((-money(amount), 'request_payment'))
        balance = self.opening
        points = [(self.start.isoformat(), balance, 'opening')]
        for day in sorted(grouped):
            # Essential debits before income; request payment after bank-posted salary.
            entries = sorted(grouped[day], key=lambda v: (v[1] == 'request_payment', v[0] >= 0, v[1]))
            for delta, evidence in entries:
                balance += delta
                points.append((day, balance, evidence))
        return points

    def verify(self, payments):
        points = self.trajectory(payments)
        trough = min(points, key=lambda v: v[1])
        return dict(safe=trough[1] >= self.minimum, minimum_projected=str(trough[1]),
                    minimum_required=str(self.minimum), binding_date=trough[0], binding_evidence=trough[2])

    def capacity(self, day):
        # All pre-payment points must also be solvent; a later credit cannot repair insolvency.
        points = self.trajectory()
        if min(p[1] for p in points) < self.minimum:
            return D('0.00')
        balance = self.opening
        future = []
        for pday, value, evidence in points[1:]:
            if pday <= day:
                balance = value
            if pday > day:
                future.append(value)
        return max(D('0'), min([balance] + future) - self.minimum).quantize(CENT, rounding=ROUND_DOWN)

    def earliest(self, amount):
        for offset in range(HORIZON_DAYS + 1):
            day = (self.start + timedelta(days=offset)).isoformat()
            if self.capacity(day) >= amount:
                return day
        return ''

def choose_plan(ledger, request, profile, options, changes=()):
    today, deadline = request['request_date'], request['desired_completion_date']
    requested = money(request['requested_amount'])
    allowed = set(profile['payment_methods_user_will_consider'].split('|'))
    safe_today = min(requested, ledger.capacity(today))
    earliest = ledger.earliest(requested)
    candidates = []

    def add(method, payments, option_id='', total=None):
        if not payments or payments[-1][0] > deadline or not ledger.verify(payments)['safe']:
            return
        candidates.append(dict(method=method, payments=payments, option_id=option_id,
                               total=total or sum(v for _, v in payments), changes=list(changes)))

    if 'full_payment' in allowed and safe_today >= requested:
        add('full_payment', [(today, requested)])
    if ('partial_payment' in allowed and request['allows_partial_payment'].lower() == 'true'
            and D('0') < safe_today < requested and earliest and earliest <= deadline):
        add('partial_payment', [(today, safe_today), (earliest, requested - safe_today)])
    if 'full_payment' in allowed and earliest and earliest > today:
        add('wait', [(earliest, requested)])
    for option in options:
        if option['payment_method'] != 'installments' or 'installments' not in allowed:
            continue
        count = int(option['number_of_payments'])
        cap = profile.get('max_installment_months', '')
        if not cap or count > int(cap) or count < 2:
            continue
        first = date.fromisoformat(option['first_payment_date'])
        frequency = int(option['payment_frequency_days'])
        if first < ledger.start or frequency < 1:
            continue
        payments = [((first + timedelta(days=i * frequency)).isoformat(), money(option['payment_amount']))
                    for i in range(count)]
        total = money(option['total_payable_amount'])
        if abs(sum(v for _, v in payments) - total) > CENT:
            continue
        if abs(total - requested - money(option['financing_fee'])) > CENT:
            continue
        if payments[-1][0] <= ledger.end.isoformat():
            add('installments', payments, option['payment_option_id'], total)
    if not candidates:
        return None
    return min(candidates, key=lambda p: (bool(p['changes']), p['total'], p['payments'][0][0],
                                           len(p['payments']), p['option_id']))
