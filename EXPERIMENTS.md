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

## OR-LIVE-02 — user-requested free-model retry (2026-09-12)

Starting commit fde9098. The user's local OPENROUTER_MODEL setting now selects
`nvidia/nemotron-3-ultra-550b-a55b:free`; no agent-initiated model/configuration edit.
Both required settings were loaded locally without exposing credentials. Public catalog
prices are 0 input/0 output and architecture is text-only. Prompt and financial logic
remain unchanged. New ignored retry01 artifacts preserve OR-LIVE-01 rather than resuming
or overwriting its failed checkpoints.

The first request_01 inference failed: sanitized ProviderError "OpenRouter connection
failed", three bounded HTTP attempts, 183.735 seconds. No usable response, tool call,
structured financial row, returned model identity or token/cost usage was received.
This connection failure is distinct from the prior HTTP 402 and does NOT establish that
billing/image issues are resolved. Catalog price zero does not substitute for measured
usage: actual input/output tokens and charges are UNKNOWN, not reported as zero.

Stopped before completing smoke or starting another 25-row public run. No prompt tuning,
financial correction, golden re-pin, paid full 250-row run or final release was attempted.
Public comparative result remains OR-LIVE-01's explicitly degraded 7/25 artifact, not a
new free-model accuracy measurement. All 75 local tests pass; production source and
tracked golden artifacts are unchanged. Exact-key/secret-format and report consistency
checks pass; local .env, transcript and retry evidence remain ignored.

Decision remains TUNE OPENROUTER, gated on a responsive endpoint and an explicitly chosen
image-capable model. This failed retry provides no accuracy evidence for a different verdict.

## OR-LIVE-03 — configured vision-model preflight (2026-09-13)

Starting commit 3c689d2. Required key/model settings detected without exposing the key.
User-configured model: `qwen/qwen2.5-vl-32b-instruct:free`. Configuration was not changed
by the agent. Financial logic, prompts and finish-tool schema remain unchanged.

Before inference, reviewed the existing adapter and experiment driver. The configured
base matches https://openrouter.ai/api/v1; completions use /chat/completions, POST JSON,
Bearer authorization, native function parameters/tool_calls/tool_call_id and preserved
reasoning continuation. Contract/integration checks pass (15 provider, eight flow tests).
Effective urllib proxy configuration is absent. The previous 183.735-second failure is
consistent with three 60-second timeout attempts plus 1/2-second backoff; its redacted
historical error does not distinguish timeout from every other connectivity failure.
No clear payload/transport implementation defect was established, so no speculative fix.

VERIFIED: current public model catalog returned HTTP 200. Neither the exact configured
identifier nor its non-free base identifier is listed. The existing first-call driver
correctly refused it before sending inference. A second public read-only catalog query
confirmed absence and recorded model capabilities in ignored live-retry02-preflight.json.
Failure category: invalid model / unavailable catalog identifier. This is not a new
connection timeout, authentication test or evidence that hosted billing is resolved.

Inference HTTP attempts: zero. No smoke response, tool calls, structured decision,
returned model identity or model token/cost measurement exists for this configuration.
No 25-row run, finish-tool change, model substitution or full 250-row hosted run occurred.
The catalog currently lists free image-and-tool candidates including
google/gemma-4-31b-it:free and google/gemma-4-26b-a4b-it:free. Advertised capability is
not live acceptance, responsiveness or financial accuracy evidence. User selection is
required before a new fixed-model smoke. Source: https://openrouter.ai/api/v1/models;
tool format reference: https://openrouter.ai/docs/guides/features/tool-calling;
image format reference: https://openrouter.ai/docs/guides/overview/multimodal/image-understanding.

Decision: SMOKE_FAILED — DIAGNOSE PROVIDER. The blocker is specifically the unavailable
configured identifier; no blind inference retry is warranted. Financial logic, finish
ambiguity and previous results remain untouched. Final local regression: 75 tests,
all 14 isolated files, unchanged 250-row golden and 100 independent plan replays pass;
secret/report checks pass, offline release still correctly refused. No submission-ready
claim is made and the required final hosted usage artifact remains pending.

## OR-LIVE-04 — guarded Gemma smoke, rate limited (2026-09-13)

Starting commit 079dcfa. User explicitly selected google/gemma-4-31b-it:free. Initial
preflight detected the key but the saved .env still selected the unavailable Qwen model;
process/user/machine model settings also did not match Gemma. Changed ONLY the local
ignored OPENROUTER_MODEL line to the exact user-selected Gemma identifier, preserving
the key. No financial logic, prompt, temperature, tools, finish interface or ranking edit.

VERIFIED: current public catalog lists Gemma, advertises image/text/video input and tools,
tool_choice, temperature, max_tokens, reasoning and response_format. Catalog input/output
prices are zero. Advertised capability is not live image acceptance or responsiveness.
The actual request_01 production-format inference used the unchanged system prompt,
dataset request, FinancialTools definitions and OpenRouter adapter. It failed with
HTTP 429 after three existing bounded HTTP attempts in 5.75 seconds. Failure category:
rate limit. The sanitized HTTP status does not establish whether the limit is per-model,
per-provider, per-account or free daily quota; raw provider bodies were not exposed.

No usable model response, returned model identity, tool call, finish arguments or
structured financial decision was received. Response parsing and deterministic final
validation were not reached. Actual input/output tokens and charge are UNKNOWN, not
fabricated as zero. Catalog-zero pricing does not replace missing measured usage.
Ignored live-gemma01-meta.json and live-gemma01-first-failure.json preserve evidence.

Stopped before further inference, smoke continuation or a new 25-example run. No
financial accuracy, blast-radius or finish-interface before/after result can be claimed
for this model. request_01 has no image evidence; existing real-adapter/real-tools mocked
image integration verifies PNG base64 handoff through an untrusted user image_url block,
image result incorporation and removal of private model-image content from traces.
That verifies application transport in the fixture, not Gemma's live image acceptance.

Final local regression: all 75 tests and 14 isolated files pass, including existing
seven adversarial safety scenarios and evaluator/adapter negative controls. Offline
250-row golden unchanged, 100 independent forecast-plan replays pass, public offline
ablation hash unchanged. Secret/report checks pass; offline release still correctly
refused. Credentials/log/scratch remain ignored. No final hosted usage report, ZIP,
paid full-dataset run or submission-ready claim.

Decision: SMOKE_FAILED — DIAGNOSE PROVIDER (HTTP 429 rate limit). Do not immediately
retry or substitute another model; obtain a provider-permitted retry time or restore
available quota before a new guarded smoke. Historical Qwen and previous failures remain
unchanged, and the finish-tool ambiguity is not tuned without a successful live baseline.

## OR-LIVE-05 — exactly one inference attempt, still HTTP 429 (2026-09-13)

Starting commit aecb3c9. Local .env has two OPENROUTER_API_KEY assignments and three
OPENROUTER_MODEL assignments, not separately named rotation/pairing settings. Existing
loader uses last assignment for each variable. No secrets were exposed; no local
configuration edit or key rotation performed. Effective model google/gemma-4-31b-it:free.
Current catalog: nvidia/nemotron-3-ultra-550b-a55b:free is listed with tools but text-only;
google/gemma-4-26b-a4b:free is absent; effective Gemma31 is listed with tools and images.
No direct Anthropic dependency/configuration is used by code/tests/requirements/env example.

Exactly ONE inference HTTP attempt sent for request_01 through the actual OpenRouter
adapter with production prompt, dataset request and FinancialTools definitions. An ignored
caller-side egress cap stops failures before the adapter retries: no source retry-policy
edit, model/prompt/interface/financial/validator/dataset/golden change. No second key or
alternate model was tried. MEASURED: HTTP 429, 0.906 seconds, one attempt, no usable model
response. Classification RATE_LIMIT. Tool calls did not occur; response parsing/final
deterministic validation were not reached. request_01 requires no image, so image acceptance
was not exercised. No financial model-quality or comparative-accuracy evidence obtained.

UNKNOWN: token usage, returned model identity, actual billed charge, estimated inference
cost from tokens and exact limiter scope/reset time. Current catalog prices are zero,
but absent usage is not fabricated as measured zero tokens/cost. Key presence and model
catalog compatibility do not prove authentication/quota status. Provider raw bodies/headers
and credential values were not printed or retained. Ignored live-single01-result.json
preserves the status/latency/attempt and capability evidence.

The local one-attempt negative control initially encountered Windows SSL initialization
under a cleared test environment; injected a mock opener rather than constructing TLS
in that fixture. Corrected harness control proves a mocked 429 causes exactly one opener
call and no sleep. This fixture error was not a production compatibility defect and did
not cause the live HTTP429. No application architecture or retry implementation change.

Stopped hosted work immediately. Offline full golden reproduction remains unchanged;
no new public25/full250 hosted evaluation, tuning, re-pin, ZIP or final hosted report.
Credentials/transcript/scratch remain ignored. Previous successful/failed measurements
are preserved as history. Decision: RATE_LIMIT — provider-side live inference remains
blocked; obtain available quota/provider-permitted retry timing before further smoke.
