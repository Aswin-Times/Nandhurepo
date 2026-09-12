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
