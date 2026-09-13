# Buy or Wait? — evidence investigation with verified financial plans

## Current release status

Current local model: `google/gemma-4-31b-it:free` on OpenRouter, using one primary key
and one optional fallback key. The final 250-row hosted run is **pending**.
The native-image smoke sent actual request_03 pixels, but received one primary daily-quota
HTTP 429 and three fallback HTTP 429 responses. No model response or tool call occurred;
native-image acceptance, tokens and cost remain unknown. Final root `output.csv` and
`code.zip` have not been generated or verified.

The local working-tree safety gate passed 147 tests, 250 pinned golden rows and 100 fresh
independent plan checks, with 275 offline outputs unchanged. These are not hosted accuracy
measurements. Pending engineering changes are separate from this documentation-only commit.
Earlier label-exposed public-example scores are not a valid clean model benchmark.

## Setup

Python 3.12 or newer is required. Place the supplied participant `dataset/` directory
beside `code/`; leave those inputs unchanged. No live banking, exchange rates, market data,
or organizer files are read. Install pixel OCR and run the contract tests:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

The default hosted path is OpenRouter. Explicit offline mode is an initial engineering baseline. It runs exact-money forecasting
and OCR but does not interpret message amendments; it is not our final AI-agent submission.
Generate baseline artifacts in a separate location:

```sh
python code/main.py --provider offline --samples --output runs/samples.csv --checkpoint runs/samples.jsonl
python code/evaluate_submission.py --actual runs/samples.csv
python code/main.py --provider offline --output runs/baseline.csv --checkpoint runs/baseline.jsonl
python code/independent_validation.py --output runs/baseline.csv --checkpoint runs/baseline.jsonl
```

For the real agent, configure `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` in the process
environment. Choose an OpenRouter model supporting native function tools and image input;
not every routed model supports both. `--model` overrides the environment model. Never put
a key in code or chat. `.env.example` lists configuration names; `.env` files are ignored and
are not automatically loaded. Use a trusted local environment/credential manager.
Optionally export `OPENROUTER_API_KEY_FALLBACK` for one bounded secondary-key phase.
Every completion starts with the primary key and keeps the exact same model/body.
Only HTTP 402/408/429/500/502/503/504 or exhausted connection/timeout retries qualify.
Each key uses the existing three-attempt policy (at most six HTTP attempts total).
No fallback occurs for request/auth errors, ambiguous 404s, malformed responses,
application/tool errors or financial/finish validation. Empty/identical secondary keys
disable fallback. Both keys are redacted; do not put either value in code or chat.
`OPENROUTER_BASE_URL` optionally overrides the HTTPS API base (default
`https://openrouter.ai/api/v1`); use only a trusted proxy because it receives the credential.
No direct-provider credentials or SDK are required. Supply the model's current prices
in USD per million tokens; the placeholders below must be replaced by numeric prices.

```sh
python code/main.py --provider openrouter --samples --limit 1 --budget-usd 1 --input-price INPUT_USD_PER_MILLION --output-price OUTPUT_USD_PER_MILLION --output runs/smoke.csv --checkpoint runs/smoke.jsonl
```

Inspect the smoke checkpoint's tool trace, usage, validation and fallback count before a larger
experiment. Missing key/model produces a clear hosted configuration error; offline needs neither.
Run the public-example comparison only after the smoke succeeds:

```sh
python code/main.py --provider openrouter --budget-usd 10 --input-price INPUT_USD_PER_MILLION --output-price OUTPUT_USD_PER_MILLION --samples --output runs/agent-samples.csv --checkpoint runs/agent-samples.jsonl
python code/evaluate_submission.py --actual runs/agent-samples.csv --before runs/samples.csv
```

The expensive full run is a separate step after reviewing the public-example experiment:

```sh
python code/main.py --provider openrouter --budget-usd 10 --input-price INPUT_USD_PER_MILLION --output-price OUTPUT_USD_PER_MILLION --output output.csv --checkpoint runs/final.jsonl --usage-report code/evaluation/usage_report.md
python code/independent_validation.py --output output.csv --checkpoint runs/final.jsonl
python code/release_submission.py --checkpoint runs/final.jsonl
```

Resume with the same command. Every completed row is flushed and fsynced to the checkpoint,
and the CSV is atomically replaced after each row. Changed data, code or configuration requires
a new checkpoint. API failures and exhausted agent work emit an explicit insufficient-evidence
explanation with no payment; release requires review of these fallbacks. A torn checkpoint
record fails loudly; preserve it and choose a new checkpoint rather than silently skipping data.

`run_agent_loop` is the model-directed core. The configured model chooses evidence retrieval, image reads,
fact amendments, simulation, and completion. It can repeat tools and react to structured errors.
The financial investigator keeps one user's evidence in one context. The internal block protocol
is normalized by `OpenRouterModel.complete`; only the adapter constructs HTTP requests. Native
function calls/JSON arguments and textual tool results follow the [OpenRouter tool-use contract](https://openrouter.ai/docs/guides/features/tool-calling).
Image evidence uses a paired untrusted user message with base64 PNG `image_url` content;
assistant reasoning details are preserved opaquely on later turns. Tools are sent on every turn,
with required-parameter routing enabled. Final rows still come from verified `finish_decision`,
not free-form text or unverified model-proposed payments.

The adapter is standard-library HTTP, injectable for tests. It retries transient HTTP/network
failures at most three times, uses a 60-second per-attempt timeout, honors numeric Retry-After
up to 60 seconds, and refuses longer waits for a later resume. Malformed/embedded-error responses
are not automatically retried because they may already be billed. Error bodies/headers are never
logged; exceptions are sanitized and returned content redacts both configured keys. Redirects are
disabled so authorization cannot be forwarded. Tests mock HTTP, never a fake provider replacement.

Tokens are actual OpenRouter prompt/completion usage normalized to input/output fields.
Provider-reported charge is recorded separately from the configured-price estimate; missing
usage is flagged rather than fabricated, and blocks release. Reports reconcile all checkpointed
turns and resumed rows, including model identifiers returned by routing. Budget reservation
includes three possible attempts; unknown charges reserve the envelope estimate. This is not
a billing hard cap: routing/image/cache prices and unreported retry charges can differ from
configured rates. Set an account-side key spending limit for a hard financial cap.

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
checks manifest/output/report correspondence and rejects unsupported providers, incomplete
usage and the offline baseline. The final OpenRouter run remains pending because hosted
provider availability is blocked; local credentials are configured. A pre-migration fresh checkout with a newly created
Python environment passed the contract suite and reproduced both the 25-row sample and 250-row
full offline output hashes with cold OCR, with dependencies installed using this README.

Run `python code/offline_regression.py` to regenerate the full pinned baseline in temporary
paths. This copies existing OCR transcriptions into the temporary cache; `--cold-ocr` additionally
checks pixel extraction. Any hash change requires a measured cause recorded in EXPERIMENTS.md.

Migration inventory, baseline and verification scope are in MIGRATION.md. The post-migration
suite includes end-to-end synthetic ZIP packaging, provider mutation negative controls and
model-disabled evidence ablation. Mocked token/cost fixtures are not real provider usage;
final 250-row hosted accuracy remains unmeasured. A successful earlier-model text smoke
does not establish native-image compatibility or availability for the currently configured model.
