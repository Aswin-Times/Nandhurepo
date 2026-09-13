# Buy or Wait? — submission runtime

Python 3.12+ is required. Keep the supplied participant `dataset/` alongside `code/`.
Run these commands from that parent directory:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Export credentials into the process environment using a trusted local credential manager:
`OPENROUTER_API_KEY`, optional `OPENROUTER_API_KEY_FALLBACK`, and
`OPENROUTER_MODEL=google/gemma-4-31b-it:free`. The runtime does not automatically load `.env`.
Never include actual keys in the ZIP, predictions or transcript.

Production evaluation, with zero configured token pricing for the fixed free model:

```sh
python code/main.py --provider openrouter --budget-usd 10 --input-price 0 --output-price 0 --output output.csv --checkpoint runs/final.jsonl --usage-report code/evaluation/usage_report.md
python code/independent_validation.py --output output.csv --checkpoint runs/final.jsonl
```

The agent uses native tools to retrieve evidence, apply supported financial amendments,
read actual image pixels through local OCR and native image handoff where unresolved,
and evaluate conservative 90-day plans. Expected public answers are evaluator-only.
Deterministic financial rules and output validation remain authoritative. Unresolved facts
and provider failures produce explicit no-payment fallback rows, not invented financial facts.
The existing bounded primary/secondary policy uses the same fixed model and request body.

Checkpoint rows and the CSV are persisted after each request. Resume only with unchanged
code, dataset and configuration; otherwise choose a fresh checkpoint. Do not manually edit
predictions. An output with 250 rows establishes coverage, not 250 accepted model decisions.

The final-run usage report is supplied at `evaluation/usage_report.md` in the ZIP and also
under `code/evaluation/`. Failed calls may return no usage: measured subtotals do not establish
total cost. Zero configured prices are an estimate, not a provider billing report.
Read that report for final-run acceptance, failures, usage and limitations.

Offline regression is a separate engineering check, not the hosted model's accuracy:

```sh
python code/offline_regression.py
python code/main.py --provider offline --output runs/baseline.csv --checkpoint runs/baseline.jsonl
python code/independent_validation.py --output runs/baseline.csv --checkpoint runs/baseline.jsonl
```

The strict `release_submission.py` certification helper rejects incomplete usage and
unresolved fallback rows. A physical upload ZIP containing transparent failure measurements
does not override that policy or certify a successful hosted benchmark. The separately
uploaded `output.csv` and project-root `log.txt` are not included in this source ZIP.
