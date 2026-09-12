# Buy or Wait? — evidence investigation with verified financial plans

Python 3.12 or newer is required. Place the supplied participant `dataset/` directory
beside `code/`; leave those inputs unchanged. No live banking, exchange rates, market data,
or organizer files are read. Install pixel OCR and run the contract tests:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

The default offline mode is an initial engineering baseline. It runs exact-money forecasting
and OCR but does not interpret message amendments; it is not our final AI-agent submission.
Generate baseline artifacts in a separate location:

```sh
python code/main.py --samples --output runs/samples.csv --checkpoint runs/samples.jsonl
python code/evaluate_submission.py --actual runs/samples.csv
python code/main.py --output runs/baseline.csv --checkpoint runs/baseline.jsonl
python code/independent_validation.py --output runs/baseline.csv --checkpoint runs/baseline.jsonl
```

For the real agent, configure `ANTHROPIC_API_KEY` in the process environment and select
an available model ID. Never put a key in code or chat. Supply the model's current prices
in USD per million tokens; the placeholders below must be replaced by numeric prices.

```sh
python code/main.py --provider anthropic --model YOUR_MODEL_ID --budget-usd 10 --input-price INPUT_USD_PER_MILLION --output-price OUTPUT_USD_PER_MILLION --samples --output runs/agent-samples.csv --checkpoint runs/agent-samples.jsonl
python code/evaluate_submission.py --actual runs/agent-samples.csv --before runs/samples.csv
python code/main.py --provider anthropic --model YOUR_MODEL_ID --budget-usd 10 --input-price INPUT_USD_PER_MILLION --output-price OUTPUT_USD_PER_MILLION --output output.csv --checkpoint runs/final.jsonl --usage-report code/evaluation/usage_report.md
python code/independent_validation.py --output output.csv --checkpoint runs/final.jsonl
python code/release_submission.py --checkpoint runs/final.jsonl
```

Resume with the same command. Every completed row is flushed and fsynced to the checkpoint,
and the CSV is atomically replaced after each row. Changed data, code or configuration requires
a new checkpoint. API failures and exhausted agent work emit an explicit insufficient-evidence
explanation with no payment; release requires review of these fallbacks. A torn checkpoint
record fails loudly; preserve it and choose a new checkpoint rather than silently skipping data.

`run_agent_loop` is the model-directed core. Claude chooses evidence retrieval, image reads,
fact amendments, simulation, and completion. It can repeat tools and react to structured errors.
The financial investigator keeps one user's evidence in one context. The Messages API uses
client tool calls and returned tool results as described in the [Anthropic tool-use contract](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls).

Deterministic scaffolding loads/join records, computes Decimal cash flows, caps work, enumerates
plans, ranks eligible safe plans, validates output and persists rows. The model resolves financial
meaning and ambiguity; it cannot override the minimum balance, payment eligibility or schema.
Retrieved text and image pixels are explicitly untrusted. Final arithmetic is performed by tools.

Today's safe capacity is the minimum remaining baseline headroom after paying on the request
date, capped at the requested amount. The earliest date is searched without optional changes.
Debits precede credits on the same date unless a request payment occurs after posted income;
this is a conservative assumption because no intraday timing is supplied. Explicit next regular
salary supersedes inferred payroll. Investment value and pending credits never fund a plan.

Monthly expense recurrence requires three calendar-consistent observations. Variable groceries,
transport and dining use recent median amounts with a 10% buffer and median category cadence.
These are documented estimates, not hidden truths. The 90-day safety proof is conditional on
that reconstructed forecast. The independent verifier replays supplied proof cash flows without
calling the production Ledger, which checks arithmetic but cannot prove source interpretation.

`code.zip` contains `evaluation/usage_report.md` at the required root path, runnable code,
tests and documentation. Dataset inputs and the transcript are separate artifacts. Packaging
checks manifest/output/report correspondence and rejects the offline baseline. The final
hosted run and a clean-install release simulation remain pending while credentials are absent.
