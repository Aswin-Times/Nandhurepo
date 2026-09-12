"""Read-only public sample metrics, output coverage, and change blast radius."""
import argparse
import csv
import json
from decimal import Decimal as D
from pathlib import Path
from financial_tools import OUTPUT_COLUMNS,validate_row

SCORED=('affordability_status','recommended_payment_method','payment_plan',
        'earliest_date_for_full_payment','spending_changes_needed')

def canonical(key,value):
    if key in {'amount_safe_to_pay'}:return D(value)
    if key=='payment_plan' and value!='none':
        return [(entry.split(':')[0],D(entry.split(':')[1])) for entry in value.split('|')]
    if key=='spending_changes_needed' and value!='none':return sorted(value.split('|'))
    return value

def compare_rows(expected,actual):
    exp={r['request_id']:r for r in expected};act={r['request_id']:r for r in actual}
    missing=sorted(set(exp)-set(act));extra=sorted(set(act)-set(exp))
    shared=sorted(set(exp)&set(act));errors=[];relative=[];exact={k:0 for k in SCORED};details=[]
    for rid in shared:
        e,a=exp[rid],act[rid]
        error=abs(D(e['amount_safe_to_pay'])-D(a['amount_safe_to_pay']))
        errors.append(error);relative.append(error/max(D('1'),D(e.get('requested_amount','1'))))
        changed=[k for k in SCORED if canonical(k,e[k])!=canonical(k,a[k])]
        for k in SCORED:exact[k]+=int(k not in changed)
        if changed or error:
            details.append(dict(request_id=rid,amount_error=float(error),changed_fields=changed,
                                expected={k:e[k] for k in ('amount_safe_to_pay',)+SCORED},
                                actual={k:a[k] for k in ('amount_safe_to_pay',)+SCORED}))
    return dict(compared=len(shared),missing=missing,extra=extra,duplicate_actual=len(actual)-len(act),
                amount_mae=float(sum(errors)/len(errors)) if errors else None,
                mean_request_relative_error=float(sum(relative)/len(relative)) if relative else None,
                amount_exact_matches=sum(error<=D('0.01') for error in errors),exact_matches=exact,mismatches=details)

def blast_radius(before,after):
    old={r['request_id']:r for r in before};new={r['request_id']:r for r in after}
    cells=0;changed=[]
    for rid in sorted(set(old)|set(new)):
        fields=[k for k in set(old.get(rid,{}))|set(new.get(rid,{})) if old.get(rid,{}).get(k)!=new.get(rid,{}).get(k)]
        if fields:changed.append(dict(request_id=rid,fields=sorted(fields)));cells+=len(fields)
    return dict(changed_rows=len(changed),changed_cells=cells,details=changed)

def read(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected',type=Path,default=Path('dataset/sample_requests.csv'))
    parser.add_argument('--actual',type=Path,required=True)
    parser.add_argument('--before',type=Path)
    args=parser.parse_args()
    expected,actual=read(args.expected),read(args.actual)
    result=compare_rows(expected,actual)
    requests={r['request_id']:r for r in expected}
    invalid=[]
    for row in actual:
        if row['request_id'] in requests:
            try:validate_row(row,requests[row['request_id']])
            except ValueError as exc:invalid.append(dict(request_id=row['request_id'],error=str(exc)))
    result['invalid_rows']=invalid
    if args.before:result['blast_radius']=blast_radius(read(args.before),actual)
    print(json.dumps(result,indent=2))
