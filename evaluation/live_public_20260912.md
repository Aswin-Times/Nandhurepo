# OR-LIVE-01: degraded public evaluation

Model: nvidia/nemotron-3-ultra-550b-a55b, OpenRouter only. Starting commit 6cfa322;
no production code or prompt change. Baseline is the verified, zero-hosted-call offline
ablation. This run is NOT a valid completed model-quality evaluation: 23 provider failures
and two model uncertainty fallbacks yield 25 no-payment rows. Correct no-payment labels
matched by failed calls do not establish correct model reasoning.

For every OpenRouter row below: safe amount **0**, earliest full-payment date **empty**,
selected payment plan **none**, spending changes **none**, validator output method
**not_recommended**, status **not_affordable**, schema **valid**. These are conservative
failure outputs, not measured safe capacity. Requested amounts are in each user's currency;
amounts across currencies are not directly comparable.

| request_id | expected_method | baseline_method | openrouter_method | expected_status | baseline_status | openrouter_status | requested amount | mechanism |
|---|---|---|---|---|---|---|---:|---|
| request_01 | full_payment | full_payment | not_recommended | affordable_now | affordable_now | not_affordable | 25256 | U1 |
| request_02 | installments | not_recommended | not_recommended | affordable_with_plan | not_affordable | not_affordable | 46018000 | U2 |
| request_03 | wait | wait | not_recommended | affordable_later | affordable_later | not_affordable | 5491000 | I |
| request_04 | wait | wait | not_recommended | affordable_later | affordable_later | not_affordable | 12693000 | C1 |
| request_05 | not_recommended | not_recommended | not_recommended | not_affordable | not_affordable | not_affordable | 15488 | C0 |
| request_06 | full_payment | not_recommended | not_recommended | affordable_with_plan | not_affordable | not_affordable | 620.4 | C0 |
| request_07 | installments | not_recommended | not_recommended | affordable_with_plan | not_affordable | not_affordable | 197400 | C0 |
| request_08 | wait | not_recommended | not_recommended | affordable_later | not_affordable | not_affordable | 996.6 | C0 |
| request_09 | full_payment | not_recommended | not_recommended | affordable_now | not_affordable | not_affordable | 166.61 | C0 |
| request_10 | not_recommended | not_recommended | not_recommended | not_affordable | not_affordable | not_affordable | 266700 | C0 |
| request_11 | full_payment | not_recommended | not_recommended | affordable_with_plan | not_affordable | not_affordable | 13110000 | C0 |
| request_12 | installments | not_recommended | not_recommended | affordable_with_plan | not_affordable | not_affordable | 65164 | C0 |
| request_13 | wait | not_recommended | not_recommended | affordable_later | not_affordable | not_affordable | 941.6 | C0 |
| request_14 | not_recommended | not_recommended | not_recommended | not_affordable | not_affordable | not_affordable | 5414.2 | C0 |
| request_15 | not_recommended | not_recommended | not_recommended | not_affordable | not_affordable | not_affordable | 3685 | C0 |
| request_16 | full_payment | full_payment | not_recommended | affordable_now | affordable_now | not_affordable | 122500 | C0 |
| request_17 | installments | not_recommended | not_recommended | affordable_with_plan | not_affordable | not_affordable | 274600 | C0 |
| request_18 | wait | wait | not_recommended | affordable_later | affordable_later | not_affordable | 3246.1 | C0 |
| request_19 | partial_payment | not_recommended | not_recommended | affordable_with_plan | not_affordable | not_affordable | 39660 | C0 |
| request_20 | not_recommended | not_recommended | not_recommended | not_affordable | not_affordable | not_affordable | 303700 | C0 |
| request_21 | full_payment | full_payment | not_recommended | affordable_with_plan | affordable_now | not_affordable | 1574.4 | C0 |
| request_22 | installments | installments | not_recommended | affordable_with_plan | affordable_with_plan | not_affordable | 731.5 | C0 |
| request_23 | wait | not_recommended | not_recommended | affordable_later | not_affordable | not_affordable | 38016 | C0 |
| request_24 | not_recommended | not_recommended | not_recommended | not_affordable | not_affordable | not_affordable | 109600 | C0 |
| request_25 | not_recommended | not_recommended | not_recommended | not_affordable | not_affordable | not_affordable | 60496000 | C0 |

## Tool-level diagnosis and model versus validator decisions

- U1: Model explicitly recommended full payment in its explanation, matching the
  deterministic candidate, but passed nonempty uncertainty beginning "None - confirmed
  salary". The finish tool interprets this as insufficient evidence and emits no payment.
  Candidate safe amount 25256, full date 2024-03-03, plan 2024-03-03:25256; independent
  projected minimum 21912.32 versus minimum 18000. The separate smoke succeeded on the
  same request; a successful smoke therefore does not guarantee stable finish arguments.
- U2: Model applied the exact quoted message_01 increase to recurring salary event_136:
  IDR 42750000 effective 2025-08-15. Deterministic candidate: installments, safe amount
  16038765.69, earliest full date 2025-09-15, plan
  2025-08-08:15952906.67|2025-09-07:15952906.67|2025-10-07:15952906.67.
  Model explanation agreed, but financing-fee/forecast caveats in uncertainty forced
  no payment. Independent projected minimum 29244259.02 versus required 29158400.
- I: No finish/model decision accepted. inspect_image was followed by HTTP 404. Public
  catalog advertises this model as text-only; unsupported image routing is a plausible
  cause, not verified from a retained raw error body. Financial eligibility/ranking cannot
  be diagnosed from this failed model run.
- C1: No finish/model decision accepted. HTTP 402 occurred after reconstruct_finances.
  Insufficient-credit failure prevented candidate evaluation and final reasoning.
- C0: HTTP 402 before any tools; no model financial decision or candidate exists for this
  run. Each row's mismatch mechanism is provider availability/billing, not established
  faulty financial reasoning. Accidental correct no-payment labels remain failure rows.

OpenRouter defines HTTP 402 as insufficient account/API-key credits in its
[official error documentation](https://openrouter.ai/docs/api_reference/errors-and-debugging).
Raw provider bodies/headers and credentials are not included in artifacts.

## Causality, score and limits

Model-disabled ablation really bypasses the hosted constructor (fail-on-invocation guard,
zero invocations) and records zero calls. Its public CSV SHA-256 remains
3f66b1b53005b6dda16a84c4a50513bd0f454418a53d714ebc36f89224d3df68.
Normal live output is not identical: 17 rows differ in decision fields, 25 in raw fields.
Changed decision IDs: 01,02,03,04,06,11,12,13,16,17,18,19,20,21,22,23,24.
Blast radius: 76 raw cells; method/status regression IDs: 01,03,04,16,18,21,22.
Method score 14/25 -> 7/25; status 13/25 -> 7/25; amount normalized error
0.13333768 -> 0.49317553. Zero invalid output rows; no live payment plans to replay.

No-network replay of U1/U2, changing only omission of finish uncertainty, produces the
independently safe full_payment/installments candidates above. This proves finish-argument
influence on these rows, not a tuned hosted improvement or permission to ignore genuine
uncertainty. U2 also demonstrates model evidence interpretation changing reconstruction.
No financial ranking, eligibility, forecast or evaluator change was accepted.

Public usage: 37 HTTP attempts; measured responses 14; missing token usage 23.
Measured input 160436, output 4166, total 164602, average 6584.08/request.
Provider-reported cost USD 0.0631688 covers measured responses only. Configured-price
ESTIMATED cost USD 0.11329125, average USD 0.00453165/request, excludes unmeasured calls.
API time sum 94.921 seconds. Full checkpoint/comparison/latency records live in ignored
runs/live-public* files; the final submission usage report is not replaced by this run.

Decision: TUNE OPENROUTER, gated on restored billing and explicit image-capable model
selection. Change one variable per measured experiment. No further paid calls, full hosted
250-row run, golden re-pin, final ZIP or submission-ready claim was made.
