"""Temporary-output forecast ablations; never overwrite submission artifacts."""
import contextlib
import io
import json
import tempfile
from decimal import Decimal as D
from pathlib import Path
import financial_reconstruction as reconstruction
from main import run,ROOT
from evaluate_submission import read,compare_rows,blast_radius

if __name__=='__main__':
    original=reconstruction.VARIABLE_SAFETY_FACTOR
    expected=read(ROOT/'dataset'/'sample_requests.csv')
    results=[];base=None
    try:
        for factor in ('1.10','1.20','1.30'):
            reconstruction.VARIABLE_SAFETY_FACTOR=D(factor)
            with tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp)/'sample.csv'
                with contextlib.redirect_stdout(io.StringIO()):
                    run(ROOT/'dataset',out,Path(tmp)/'checkpoint.jsonl',provider='offline',samples=True)
                actual=read(out);metrics=compare_rows(expected,actual)
                if base is None:base=actual
                change=blast_radius(base,actual)
                results.append(dict(factor=factor,relative_error=metrics['mean_request_relative_error'],
                                    exact_matches=metrics['exact_matches'],changed_rows=change['changed_rows'],
                                    changed_cells=change['changed_cells']))
    finally:reconstruction.VARIABLE_SAFETY_FACTOR=original
    print(json.dumps(results,indent=2))
