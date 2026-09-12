import sys
import unittest
import tempfile
import csv
import hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from batch_execution import execute_batch
from financial_tools import OUTPUT_COLUMNS

def row(req):
    return dict(zip(OUTPUT_COLUMNS,[req['request_id'],'0','not_affordable','not_recommended','none','','none','Insufficient evidence.']))

class BatchTests(unittest.TestCase):
    def test_resume_every_row_and_failure_isolation(self):
        requests=[dict(request_id=str(i),requested_amount='1',request_date='2026-01-01',desired_completion_date='2026-01-02') for i in range(3)]
        calls=[]
        def solve(req):
            calls.append(req['request_id'])
            if req['request_id']=='1':raise ValueError('bad row')
            return dict(row=row(req),usage=dict(input_tokens=0,output_tokens=0,model_calls=0),trace=[])
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'output.csv';checkpoint=Path(tmp)/'checkpoint.jsonl'
            execute_batch(requests,solve,lambda r,why:row(r),output,checkpoint,'abc')
            self.assertEqual(len(checkpoint.read_text().splitlines()),3)
            before=hashlib.sha256(output.read_bytes()).hexdigest()
            execute_batch(requests,solve,lambda r,why:row(r),output,checkpoint,'abc')
            self.assertEqual(calls,['0','1','2'])
            self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(),before)
            with self.assertRaises(ValueError):execute_batch(requests,solve,lambda r,why:row(r),output,checkpoint,'changed')

    def test_duplicate_request_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                execute_batch([{'request_id':'x'},{'request_id':'x'}],None,None,Path(tmp)/'out',Path(tmp)/'cp','a')
if __name__=='__main__':unittest.main()
