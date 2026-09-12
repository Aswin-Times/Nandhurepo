# Measured decisions and rejected variants

Metrics were named in SPEC.md before implementation. Sample IDs are disjoint from the 250
evaluation requests. Public samples are evaluation fixtures; runtime predictions never copy labels.

| Experiment | Measurement | Decision |
|---|---|---|
| Initial offline scaffold | 13/25 statuses, 14/25 methods; mean request-relative amount error 0.21527 | Rejected as submission-ready; batch coverage is not accuracy |
| Explicit next/final payroll supersedes inference | Methods 14→15/25; relative error 0.21527→0.13334; 4 sample rows / 23 cells and 35 full rows / 146 cells changed | Accepted diagnosed cash-source correction |
| Synthetic OCR assumptions | Four added real-format regressions all failed before parser correction, all passed afterward | Rejected initial comma/label parsing; repaired Indian grouping and label priority |
| 1.20 variable buffer vs 1.10 | Relative error 0.16002 vs 0.13334; methods 11 vs 14/25; 25 sample rows / 52 cells changed | Rejected larger buffer |
| 1.30 variable buffer vs 1.10 | Relative error 0.19260 vs 0.13334; methods 11 vs 14/25; 25 sample rows / 52 cells changed | Rejected larger buffer |
| Future settlement-date FX | Two variable-rate synthetic regressions failed, then passed; full 250-row output hash unchanged, zero changed rows/cells | Accepted nominal-currency recurrence fix; missing future dated rates fail explicitly |

The two larger buffers are variants of one idea, not two independent feature discoveries.
The current offline method count returned to 14/25 when spending-change-derived wait plans
were excluded to preserve the unchanged-baseline earliest-date contract. This is a contract
correction with a sample-score cost. Further forecast/evidence work is still required.

Run `python code/forecast_experiments.py` to reproduce buffer comparisons; every arm writes
inside a temporary directory. Run `evaluate_submission.py --before ...` or
`summarize_experiment.py BEFORE.csv AFTER.csv` to measure changes. Earlier generated runs
remain local under gitignored `runs/`; they must not be treated as current submission artifacts.

Historical pre-OpenRouter counterfactual tests: removing evidence retrieval removes its financial effect in scripted-agent
tests; removing pixel text prevents extraction; deliberately unsafe payments fail both the
production verifier and independent replay. These are component tests, not a claim that hosted
Claude is accurate. Hosted sample/full runs have not occurred because no API key is configured.

A new checkout and isolated Python environment installed README dependencies, passed the suite,
and regenerated all 250 offline rows with cold pixel OCR. Its SHA-256 matched the pinned baseline;
independent Decimal replay verified 100 recommended payment plans with zero failures. One
handwritten-image row remained an explicit insufficient-evidence fallback. These checks establish
reproducibility and conditional arithmetic safety, not prediction correctness.

## OpenRouter migration — transport only

Baseline `b1b3acc`: 47 tests, public methods/plans 14/25, statuses 13/25, earliest dates 13/25,
actions 21/25, normalized amount error 0.13333768. After the adapter/wiring change: 67 tests;
both sample and full offline CSV hashes unchanged. Zero request IDs, output cells, methods,
statuses or plans changed; zero public accuracy regressions. All 250 rows reproduce and all
100 recommended plans independently replay safely. Financial decision modules are unchanged.

Negative control: deliberately replacing the actual adapter's message builder with an empty
builder makes the positive HTTP-boundary contract test fail with an assertion; the control
checks this failure. Invalid wire responses separately force a schema-valid insufficient-evidence
row. Integration uses the real adapter/agent/tools/batch/report code and only mocks HTTP.
All token/cost values in those fixtures are synthetic, not live OpenRouter measurements.
Environment OpenRouter key/model are absent, so no live smoke, 25-example hosted accuracy,
paid cost measurement or accuracy optimization has occurred. Baseline remains 14/25.

Follow-up boundary hardening: malformed routing/continuation metadata and nonstandard/duplicate
JSON arguments failed new regressions before correction. The suite now has 73 tests, including
real PNG/media handling with OCR inference mocked, an adapter-backed salary-amendment ablation,
and a synthetic 250-request run through evaluation, independent replay, usage reporting and ZIP
packaging. That synthetic run makes 1,000 mocked HTTP responses, not paid requests; its 250
safe plans and fixture charges are not participant-dataset accuracy or cost evidence. Direct
financial modules remain unchanged; the participant offline CSVs remain the comparison target.

## First live verification pre-flight — blocked before network

At 1161e5e, all 73 existing tests passed. Boolean-only checks of process, Windows user and
machine environments found neither OPENROUTER_API_KEY nor OPENROUTER_MODEL configured.
No credential value was printed. Model comes from OPENROUTER_MODEL or --model; pricing
comes separately from --input-price/--output-price, with no key embedded in price configuration.
The selected smoke candidate is simple public request_01, but it has NOT been executed live.
Actual live OpenRouter calls: zero; live model, tokens, charges and accuracy are unmeasured.
The 25-example hosted experiment and prompt/model tuning remain gated; no fake comparison
or final hosted-usage report is created to fill the missing measurement.

Added checks exercise seven adversarial scenarios through the real adapter/agent/tools with
HTTP mocked: below-minimum payment, ignored pending debit, unavailable option, invented
income, after-deadline payment, unaccepted method and malformed installment terms. None can
authorize an unsafe payment. A positive control still pays a valid 350, not the model's attempted
700. Unsupported proposed row fields are never authoritative; source-free income amendments
are rejected and invalid offers are excluded. These are finite component checks, not a proof
of all possible semantic attacks. A one-method evaluator mutation loses exactly one method
match and changes exactly one output cell. Test-draft failures were fixture/type mistakes,
not production financial defects; they were corrected without changing the financial engine.

Decision: KEEP OPENROUTER provisionally as the tested transport. No live comparative evidence
supports model tuning, rejection or an accuracy-improvement claim. Configure key/model locally
and supply current prices before the one-request live gate can proceed.

Final local regression: 75 tests pass and all 14 test files pass independently. Running the
whole suite with unmocked HTTP forbidden reports zero unmocked HTTP attempts. The credential-
free full run reproduces all 250 rows and the pinned hash; 100 forecast-plan replays pass.
Public methods/statuses remain 14/25 and 13/25; sample hash unchanged, zero invalid rows,
changed request IDs or changed cells. Current artifact freshness passes, and release correctly
refuses this offline artifact. Secret-format scan found no credential/private-key candidates;
transcript stays ignored. No production code, constants, prices or golden hashes were changed.

## OR-LIVE-01 — first real OpenRouter measurement (2026-09-12)

Starting commit: 6cfa322. Financial logic and prompt unchanged. Local ignored .env settings
were exported into the experiment process; the runtime provider reads its key only from
environment variables. Provider: OpenRouter. Configured and returned model:
`nvidia/nemotron-3-ultra-550b-a55b`. Temperature 0, maximum response tokens 2400,
12-step tool loop. Current public model catalog supplied USD/million prices 0.625 input,
3.125 output (https://openrouter.ai/api/v1/models); configured-price costs are ESTIMATED.
The catalog advertises text-only input and tool/reasoning support, not image input.

First inference call succeeded: retrieve_evidence, 1686 input/109 output tokens,
USD 0.0010828 provider-reported cost, 3.969 seconds, reasoning/reasoning_details returned.
The complete request_01 smoke reused that exact response rather than billing it again:
four real calls, 49344 input + 1502 output = 50846 tokens, USD 0.018146 reported charge,
USD 0.03553375 ESTIMATED cost, 26.157 seconds summed API time. Tool sequence:
retrieve_evidence, reconstruct_finances, evaluate_payment_plans, finish_decision.
Structured full_payment/affordable_now row accepted; independent minimum 21912.32
exceeds required 18000. No smoke fallback and no missing usage.

Before public evaluation: 75 tests and all 14 test files passed; offline 250-row golden
hash unchanged, 100 independent forecast-plan replays passed, offline release refused.
Network-denied suite counted zero unmocked HTTP attempts. Model-disabled ablation uses
the actual offline pipeline with the hosted constructor patched to fail if invoked:
zero constructor attempts, zero model calls, unchanged public baseline hash and 14/25
methods, 13/25 statuses. It is a verified bypass, not merely an ineffective toggle.

Unchanged public run attempted all 25 rows with USD 5 conservative local budget:
37 real HTTP attempts, 14 returned measured responses, one HTTP 404 following
inspect_image on request_03 and 22 HTTP 402 failures starting during request_04.
The 404 is consistent with the text-only model's unsupported image input; its raw
provider body was deliberately not retained, so that cause is an inference. OpenRouter
documents 402 as insufficient account/key credits. A read-only key diagnostic returned
is_free_tier=true and no configured key credit limit; it does not prove account balance.
No further hosted inference, model switch, funding action or 250-row paid run occurred.

Observed artifact score: methods 7/25 (delta -7), statuses 7/25 (delta -6), plans/dates
7/25, actions 22/25, normalized amount error 0.49317553, zero schema-invalid rows.
All 25 rows are no-payment fallbacks: two model-supplied uncertainty arguments and 23
provider failures. The seven label matches are therefore not successful model decisions.
This is a degraded end-to-end result, NOT a completed model-quality accuracy baseline.
Decision fields changed on 17 requests; 25 rows/76 raw cells changed including explanations.
Regressions versus previously correct method/status fields: requests 01,03,04,16,18,21,22.
Detailed all-row comparison and mechanisms: evaluation/live_public_20260912.md.

Public measured usage: 160436 input + 4166 output = 164602 tokens (6584.08/request).
Reported charge USD 0.0631688 covers only 14/37 attempts; token usage missing on 23.
USD 0.11329125 total / 0.00453165 per request is the configured-price ESTIMATE for
measured tokens, not a complete billing reconciliation. Summed API time 94.921 seconds.
Combined smoke/public reported charges: USD 0.0813148, with the same missing-call caveat.
Ignored checkpoints, latency records, comparison JSON and usage reports preserve evidence;
the required final full-dataset hosted usage report remains pending, not overwritten.

Causality is proven locally for specific mechanisms, not all 25 model decisions.
request_01's model explanation recommended the verified full payment but supplied
uncertainty="None - confirmed salary ..."; any nonempty uncertainty causes fallback.
request_02 correctly applied quoted message_01 salary increase (42750000 effective
2025-08-15), producing a safe installment candidate, then ordinary forecast caveats in
uncertainty forced fallback. No-network replay changing ONLY omission of that finish
argument changes request_01 to full_payment and request_02 to installments, both with
independent safe replays. This diagnostic is NOT a tuned hosted score or justification
to ignore genuine missing evidence. Model amendments change reconstruction/candidates;
the deterministic validator still selects and validates payment plans, never model rows.

Decision: TUNE OPENROUTER. Measured finish-argument ambiguity and image compatibility
justify a controlled integration/prompt experiment once billing is restored. Do not tune
financial ranking or claim accuracy gains from this failed public run. First obtain funded
access and an explicitly selected image-capable OpenRouter model; then change one variable
at a time with fresh checkpoints. A valid complete 25-row measurement is still required.
Production logic, constants, prompts and golden hashes remain unchanged; no submission-ready
claim or final release certification is warranted.
