"""Regenerate the pinned baseline in temporary paths and reject unrecorded changes."""
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from main import run,ROOT

def check_hash(path,expected):
    actual=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if actual!=expected:raise ValueError('Offline output changed: '+expected+' -> '+actual+'; measure and record cause before re-pinning')
    return actual

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cold-ocr',action='store_true',help='Also recompute image OCR, instead of using copied cached transcriptions')
    args=parser.parse_args()
    expected=(ROOT/'evaluation'/'offline_golden.sha256').read_text(encoding='utf-8').strip().split()[0]
    with tempfile.TemporaryDirectory() as tmp:
        scratch=Path(tmp);cache=scratch/'ocr'
        if not args.cold_ocr and (ROOT/'.cache'/'ocr').is_dir():
            shutil.copytree(ROOT/'.cache'/'ocr',cache)
        output=scratch/'output.csv'
        run(ROOT/'dataset',output,scratch/'checkpoint.jsonl',provider='offline',cache_dir=cache)
        print('VERIFIED offline baseline SHA-256:',check_hash(output,expected))
