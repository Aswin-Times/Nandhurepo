"""Per-row durable checkpointing and atomic CSV publication."""
import csv
import json
import os
from pathlib import Path
from financial_tools import OUTPUT_COLUMNS,validate_row

def write_output(output,requests,records):
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_suffix(output.suffix+'.tmp')
    with temporary.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=OUTPUT_COLUMNS,lineterminator='\n')
        writer.writeheader()
        for request in requests:
            if request['request_id'] in records:writer.writerow(records[request['request_id']]['row'])
        f.flush();os.fsync(f.fileno())
    os.replace(temporary,output)

def execute_batch(requests,solve,fallback,output,checkpoint,fingerprint):
    ids=[r['request_id'] for r in requests]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate request identifiers')
    checkpoint=Path(checkpoint);checkpoint.parent.mkdir(parents=True,exist_ok=True)
    records={};by_id={r['request_id']:r for r in requests}
    if checkpoint.exists():
        for line in checkpoint.read_text(encoding='utf-8').splitlines():
            record=json.loads(line)
            if record['fingerprint']!=fingerprint:raise ValueError('Checkpoint input/config fingerprint changed; use a new checkpoint')
            rid=record['row']['request_id']
            if rid not in by_id or rid in records:raise ValueError('Checkpoint contains unknown/duplicate request')
            validate_row(record['row'],by_id[rid]);records[rid]=record
    for request in requests:
        rid=request['request_id']
        if rid in records:continue
        try:
            record=solve(request)
            validate_row(record['row'],request)
        except Exception:
            record=dict(row=fallback(request,'row processing failed; insufficient evidence'),
                        usage=dict(input_tokens=0,output_tokens=0,model_calls=0),trace=[])
            validate_row(record['row'],request)
        record['fingerprint']=fingerprint
        with checkpoint.open('a',encoding='utf-8',newline='\n') as f:
            f.write(json.dumps(record,ensure_ascii=False,default=str)+'\n');f.flush();os.fsync(f.fileno())
        records[rid]=record
        write_output(output,requests,records)
    write_output(output,requests,records)
    return [records[rid] for rid in ids]
