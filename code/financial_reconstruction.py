"""Reconstruct dated obligations with explicit provenance and conservative estimates."""
import calendar
import collections
import statistics
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal as D
from financial_ledger import CashFlow, Ledger, money

MIN_MONTHLY_OBSERVATIONS = 3
RECENT_OBSERVATIONS = 3
VARIABLE_SAFETY_FACTOR = D('1.10')

@dataclass
class FinancialState:
    ledger: Ledger
    recurring: list
    excluded: list
    assumptions: list

def month_date(year, month, day):
    return date(year, month, min(day, calendar.monthrange(year, month)[1]))

def monthly_dates(start, end, day):
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        candidate = month_date(year, month, day)
        if start <= candidate <= end:
            yield candidate
        month += 1
        if month == 13:
            year, month = year + 1, 1

def reconstruct(start, profile, events, messages, rates, resolved_amounts=None, amendments=None):
    today = date.fromisoformat(start)
    end = today + timedelta(days=90)
    resolved_amounts = resolved_amounts or {}
    amendments = amendments or []
    rows, excluded = [], []
    seen = set()
    by_id = {e['event_id']: e for e in events}
    for original in sorted(events, key=lambda e: (e['settlement_date'], e['event_id'])):
        e = dict(original)
        status = e['status']
        if status in {'cancelled','failed','unrealized'} or (e['direction'] == 'credit' and status == 'pending'):
            excluded.append(dict(event_id=e['event_id'], reason=status + ' not available cash'))
            continue
        if status not in {'settled','scheduled','pending'}:
            raise ValueError('Unsupported cash state: ' + status)
        linked = by_id.get(e['linked_event_id'])
        duplicate = (e['settlement_date'], e['direction'], e['amount'], e['currency'], e['description'])
        if duplicate in seen or (linked and all(e[k] == linked[k] for k in
                         ('settlement_date','direction','amount','currency','status'))):
            excluded.append(dict(event_id=e['event_id'], reason='duplicate cash representation'))
            continue
        seen.add(duplicate)
        raw = e['amount'] or resolved_amounts.get(e['event_id'])
        if raw is None or raw == '':
            raise ValueError('Missing image-derived amount for ' + e['event_id'])
        amount = money(raw)
        if amount < 0:
            raise ValueError('Negative amount in ' + e['event_id'])
        if e['currency'] != profile['home_currency']:
            pair = (e['settlement_date'], e['currency'], profile['home_currency'])
            if pair not in rates:
                # Historic foreign data without rates cannot support cash inference.
                if date.fromisoformat(e['settlement_date']) < today:
                    excluded.append(dict(event_id=e['event_id'], reason='historic FX rate absent'))
                    continue
                raise ValueError('Missing settlement-date FX rate for ' + e['event_id'])
            amount = money(amount * rates[pair])
        e['_amount'] = amount
        rows.append(e)

    groups = collections.defaultdict(list)
    for e in rows:
        if date.fromisoformat(e['settlement_date']) < today and e['status'] == 'settled':
            groups[(e['description'],e['direction'],e['category'])].append(e)
    flows, recurring, used = [], [], set()
    assumptions = []
    for (description, direction, category), history in sorted(groups.items()):
        dates = [date.fromisoformat(e['settlement_date']) for e in history]
        months = {(d.year,d.month) for d in dates}
        gaps = [(b-a).days for a,b in zip(dates,dates[1:])]
        recent = history[-RECENT_OBSERVATIONS:]
        # Monthly recurrence needs distinct months and calendar-consistent posting days.
        monthly = (len(months) >= MIN_MONTHLY_OBSERVATIONS and len(months) == len(history)
                   and gaps and 25 <= statistics.median(gaps) <= 35
                   and max(d.day for d in dates) - min(d.day for d in dates) <= 3)
        if not monthly:
            continue
        if direction == 'credit' and (category != 'salary' or any(term in description.lower() for term in
                       ('bonus','commission','arrears','prize','refund','one-time','gig','invoice','seasonal'))):
            continue
        amount = recent[-1]['_amount'] if direction == 'credit' else max(e['_amount'] for e in recent)
        anchor = recent[-1]
        day = dates[-1].day
        record = dict(event_id=anchor['event_id'], description=description, category=category,
                      direction=direction, amount=str(amount), day=day, interval='monthly',
                      flexibility=anchor['flexibility'], minimum_allowed_amount=anchor['minimum_allowed_amount'],
                      supporting_event_ids=[e['event_id'] for e in history])
        recurring.append(record)
        used.update(e['event_id'] for e in history)
        for d in monthly_dates(today, end, day):
            # A posted settled event on request day is already reflected in opening balance.
            supplied = [e for e in rows if e['description'] == description and e['direction'] == direction
                        and e['settlement_date'] == d.isoformat()]
            if supplied:
                continue
            flows.append(CashFlow(d.isoformat(), amount if direction == 'credit' else -amount,
                                  anchor['event_id'], category, anchor['event_id']))

    # Aggregate irregular essentials by category, not merchant: changing merchant is not cancellation.
    variable = collections.defaultdict(list)
    for e in rows:
        d = date.fromisoformat(e['settlement_date'])
        if e['event_id'] not in used and e['direction'] == 'debit' and e['status'] == 'settled' and d < today:
            if e['category'] in {'groceries','transport','dining'}:
                variable[e['category']].append(e)
    for category, history in sorted(variable.items()):
        history.sort(key=lambda e: (e['settlement_date'],e['event_id']))
        dates = sorted({date.fromisoformat(e['settlement_date']) for e in history})
        if len(dates) < MIN_MONTHLY_OBSERVATIONS:
            continue
        gaps = [(b-a).days for a,b in zip(dates,dates[1:])]
        interval = max(1, round(statistics.median(gaps)))
        amounts = [e['_amount'] for e in history[-6:]]
        budget = money(D(str(statistics.median(amounts))) * VARIABLE_SAFETY_FACTOR)
        anchor = history[-1]
        d = dates[-1] + timedelta(days=interval)
        while d < today:
            d += timedelta(days=interval)
        while d <= end:
            flows.append(CashFlow(d.isoformat(), -budget, anchor['event_id'], category))
            d += timedelta(days=interval)
        assumptions.append(dict(category=category, amount=str(budget), interval_days=interval,
                                rule='recent median x 1.10; historical median category cadence',
                                evidence_ids=[e['event_id'] for e in history[-6:]]))

    for e in rows:
        d = date.fromisoformat(e['settlement_date'])
        if e['status'] in {'pending','scheduled'} or (e['status'] == 'settled' and d > today):
            if d < today and e['direction'] == 'debit':
                d = today
            if today <= d <= end:
                flows.append(CashFlow(d.isoformat(), e['_amount'] if e['direction'] == 'credit' else -e['_amount'],
                                      e['event_id'], e['category']))

    # Typed, evidence-anchored amendments produced by an evidence tool/model.
    for amendment in amendments:
        source = amendment['evidence_id']
        op = amendment['operation']
        target = amendment.get('target_event_id','')
        if op == 'remove':
            flows = [f for f in flows if f.evidence_id != target and f.recurring_id != target]
        elif op == 'replace_recurring':
            flows = [f for f in flows if f.recurring_id != target]
            record = next((r for r in recurring if r['event_id'] == target), None)
            if record is None:
                raise ValueError('Unknown recurring amendment target')
            for d in monthly_dates(today, end, int(amendment['day'])):
                if d.isoformat() >= amendment.get('effective_date',start):
                    amount = money(amendment['amount'])
                    flows.append(CashFlow(d.isoformat(), amount if record['direction']=='credit' else -amount,
                                          source,record['category'],target))
        elif op == 'add':
            amount = money(amendment['amount'])
            if amendment['direction']=='debit': amount = -amount
            flows.append(CashFlow(amendment['date'],amount,source,amendment.get('category','')))
        else:
            raise ValueError('Unsupported evidence amendment operation')
    return FinancialState(Ledger(start, profile['current_available_balance'],
                                 profile['minimum_balance_to_keep'], flows), recurring,excluded,assumptions)
