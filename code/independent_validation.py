"""Read-only replay independent of the production Ledger implementation."""
import argparse
import csv
import json
from decimal import Decimal as D
from pathlib import Path
from financial_tools import validate_row

def replay_safe(opening,minimum,flows,payments):
    # Deliberately does not call Ledger.verify or Ledger.trajectory.
    items=[(f['date'],1 if D(f['amount'])>=0 else 0,D(f['amount']),f['evidence_id']) for f in flows]
    items.extend((day,2,-D(str(amount)),'request_payment') for day,amount in payments)
    balance=D(opening);trough=balance;binding='opening'
    for day,order,delta,evidence in sorted(items,key=lambda v:(v[0],v[1],v[3])):
        balance+=delta
        if balance<trough:trough=balance;binding=evidence
    return dict(safe=trough>=D(minimum),minimum_projected=str(trough),binding_evidence=binding)

def validate_artifacts(dataset,output,checkpoint):
    def read(path):
        with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
    requests=read(Path(dataset)/'requests.csv');actual=read(output)
    records=[json.loads(line) for line in Path(checkpoint).read_text(encoding='utf-8').splitlines()]
    by_id={r['request_id']:r for r in requests};rows={r['request_id']:r for r in actual}
    failures=[];verified=0
    if len(actual)!=len(requests) or set(rows)!=set(by_id):failures.append('Output coverage/duplicates differ from requests')
    for record in records:
        row=record['row'];rid=row['request_id']
        if rid not in by_id:failures.append(rid+': unknown request');continue
        if rows.get(rid)!=row:failures.append(rid+': output does not match checkpoint')
        try:payments=validate_row(row,by_id[rid])
        except ValueError as exc:failures.append(rid+': '+str(exc));continue
        if payments:
            proof=record.get('proof')
            if not proof:failures.append(rid+': payment recommendation lacks replay evidence');continue
            safety=replay_safe(proof['opening'],proof['minimum'],proof['plan_flows'],payments)
            if not safety['safe']:failures.append(rid+': independently replayed unsafe plan')
            else:verified+=1
    return dict(rows=len(actual),verified_payment_plans=verified,failures=failures)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,default=Path('dataset'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--checkpoint',type=Path,required=True)
    args=parser.parse_args()
    result=validate_artifacts(args.dataset,args.output,args.checkpoint)
    print(json.dumps(result,indent=2))
    raise SystemExit(bool(result['failures']))
