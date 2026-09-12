"""Local pixel OCR, content-addressed caching, and conservative amount extraction."""
import hashlib
import json
import re
from pathlib import Path
from financial_ledger import money, amount_text

NUMBER = re.compile(r'(?<![\w/])(?:\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)(?![\w/])')

def extract_amount(lines, category=''):
    ranked = []
    for i, line in enumerate(lines):
        lower = line.lower()
        score = 0
        if category == 'salary' and any(label in lower for label in ('net pay','net salary','take home','gaji bersih')):
            score = 100
        elif any(label in lower for label in ('grand total','amount due','balance due','total payable','total amount','total paid','net amount')):
            score = 90
        elif 'total' in lower and not any(label in lower for label in ('subtotal','sub total','earnings','deduction','tax')):
            score = 70
        elif 'amount' in lower or 'paid' in lower:
            score = 50
        if not score:
            continue
        matches = NUMBER.findall(line)
        if not matches and i+1 < len(lines):
            matches = NUMBER.findall(lines[i+1])
        if matches:
            ranked.append((score, i, matches[-1].replace(',','')))
    if not ranked:
        raise ValueError('No explicit final payable/net amount found in image text')
    ranked.sort(reverse=True)
    highest = ranked[0][0]
    amounts = {money(value) for score, _, value in ranked if score == highest}
    if len(amounts) != 1:
        raise ValueError('Conflicting equally authoritative image amounts')
    return amount_text(amounts.pop())

class ImageEvidence:
    def __init__(self, dataset, cache=None):
        self.dataset = Path(dataset)
        self.cache = Path(cache) if cache else None
        self._engine = None

    def read(self, image_id, category=''):
        path = self.dataset / 'media' / 'images' / (image_id + '.png')
        if not path.is_file():
            raise ValueError('Image file absent: ' + image_id)
        data = path.read_bytes()
        if not data.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('Image does not contain PNG data')
        digest = hashlib.sha256(data).hexdigest()
        cache_path = self.cache / (digest + '.json') if self.cache else None
        if cache_path and cache_path.is_file():
            result = json.loads(cache_path.read_text(encoding='utf-8'))
        else:
            if self._engine is None:
                try:
                    from rapidocr_onnxruntime import RapidOCR
                except ImportError as exc:
                    raise ValueError('Install requirements.txt for pixel OCR') from exc
                self._engine = RapidOCR(intra_op_num_threads=1, inter_op_num_threads=1)
            blocks, _ = self._engine(str(path))
            # Join text at similar y to keep labels paired with amounts in tables.
            rows = []
            for box, text, confidence in sorted(blocks or [], key=lambda b: (b[0][0][1], b[0][0][0])):
                y = sum(p[1] for p in box) / 4
                height = max(p[1] for p in box)-min(p[1] for p in box)
                row = next((r for r in rows if abs(r['y']-y) < max(8,height*.6)), None)
                item = (min(p[0] for p in box),text,float(confidence))
                if row is None:
                    rows.append(dict(y=y, items=[item]))
                else:
                    row['items'].append(item)
            lines = [' | '.join(i[1] for i in sorted(r['items'])) for r in sorted(rows,key=lambda r:r['y'])]
            result = dict(image_id=image_id, sha256=digest, lines=lines, trust='untrusted_evidence')
            if cache_path:
                self.cache.mkdir(parents=True,exist_ok=True)
                cache_path.write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
        try:
            result['suggested_amount'] = extract_amount(result['lines'], category)
        except ValueError as exc:
            result['extraction_error'] = str(exc)
        return result

if __name__ == '__main__':
    import csv
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--dataset',default='dataset')
    args=parser.parse_args()
    media=ImageEvidence(args.dataset,'.cache/ocr')
    with (Path(args.dataset)/'images.csv').open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            result=media.read(row['image_id'],'salary' if row['image_id']=='' else '')
            print(json.dumps(result,ensure_ascii=True))
