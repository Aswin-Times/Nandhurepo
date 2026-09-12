# Architecture and honest limitations

The agent chooses which evidence to read and how to amend uncertain financial state. A Decimal
solver owns arithmetic and financial constraints. One context per user retains cross-evidence
relationships. Tools return useful errors so the model can repair arguments; work is bounded.

Historical settled transactions are already in the available balance. Future debits and pending
debits reduce headroom; pending credits and unrealized investment gains are unavailable. A
linked-event ID is a lifecycle relationship, not permission to delete unrelated cash. Explicit
confirmed payroll prevents duplicate inferred payroll and supersedes stale salary amounts.

Safety is conditional: the recommended payments preserve the supplied minimum across the
reconstructed 90-day forecast. The independent replay checks the solver's arithmetic from
recorded flows. It does not prove the forecast is the true future or the model read evidence
correctly. Public-sample accuracy is currently insufficient for a winning claim.

Real limitations: conservative recurrence/variable-expense estimation is approximate; absent
intraday timing makes same-day debit-first ordering a judgement; the handwritten image is not
resolved by OCR alone; hosted tool behavior and output quality are unmeasured until credentials
are available. Numeric quotes constrain amendments, but semantic interpretation still belongs to
the model. Month-cap interpretation for nonmonthly offers needs specification clarification.

Offline core operations use no network models or randomness. Hosted temperature zero is not
a determinism guarantee. Completed rows are checkpointed; partial/corrupt checkpoint records
are detected, not automatically repaired. Model HTTP failures with no usage response are an
accounting boundary. Do not claim leaderboard rank, hidden-label accuracy or live-agent results.

## Historical Gate 7 manual self-score at b1b3acc — not an organizer score

The requested orchestrate skill repository and CLI were unavailable in the local workspace;
`orchestrate evaluate`, `mentor`, `release`, and `certify` were not run. This readiness assessment
uses inspected source, measured tests and public examples rather than a simulated certification.

| Artifact | Readiness / 5 | Evidence and remaining gap |
|---|---|---|
| Code | 4 | 47 passing tests, each file isolated; scripted model-directed tool loop and guarded release; hosted behavior untested |
| Output | 2 | 250 offline rows reproducible; 100 plans pass independent arithmetic replay; only 14/25 sample methods match and one image fallback |
| Transcript | 3 | Decisions, counterfactuals and rejections documented; missed per-turn file entries were appended late, not reconstructed as contemporaneous logs |
| Interview | 3 | Constants, rejected variants and limitations documented; no hosted-run evidence or judge interview yet |

Using the supplied 30/30/10/30 artifact weights, this subjective readiness estimate is 3/5.
It is neither a leaderboard prediction nor a claim of submission correctness. The weakest gate
is financial interpretation/output quality. Next action: obtain locally configured model access,
run public samples, diagnose mismatches, then run the complete hosted batch and recheck release.

## OpenRouter migration readiness

Direct API transport was removed, not retained as an alternate provider. OpenRouter owns all
hosted HTTP behind an injectable adapter; the financial engine still owns the same constraints.
Provider-normalized blocks preserve the existing agent loop without leaking wire HTTP into
financial decisions. Tool JSON, multiple calls, image handoff and opaque reasoning continuation
are covered by boundary tests. Invalid responses never become arbitrary CSV decisions.

73 tests pass, including a deliberately broken real adapter detected by its positive contract
test, an evidence-disabled counterfactual, real-tool batch/report/replay, and synthetic full-run
ZIP packaging. Offline participant artifacts remain byte-identical and public methods stay
14/25. No actual OpenRouter model/call/usage/accuracy has been measured: key/model are absent.
Code is ready for a configured small smoke experiment, not claimed live-certified or submission
ready. Output interpretation remains the weakest gate; provider replacement is not an accuracy
improvement. Numeric quote validation does not prove the model's semantic reading is correct.
