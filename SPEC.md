# Executable contract: Buy or Wait?

Source of truth: problem_statement.md. The attached copy differs only in line endings.

| Requirement | Acceptance evidence |
|---|---|
| Exactly one output per evaluation request, exact eight columns | batch schema and coverage tests |
| Decimal money; today's safe amount precedes optional changes | ledger capacity and spending-change tests |
| 90-day minimum balance protected at every expense and payment | trajectory tests and independent output replay |
| Historical settled cash already represented in opening balance | state-reconstruction tests |
| Pending debits reserved; pending credits and unrealized value excluded | cash-state tests |
| Recurrence requires history; explicit evidence overrides inferred state | recurrence and evidence counterfactual tests |
| Fixed directional FX rates matched by settlement date | conversion tests |
| Blank event amount requires image; never silently zero | OCR and missing-evidence tests |
| Supplied installment schedule, eligible preference and month cap | plan-contract tests |
| Partial payments exactly today-safe and remainder at baseline earliest date | two-payment tests |
| At most three permitted recurring flexible changes | protected-category tests |
| No-change plans preferred, then cost, start, count, option ID | ranking tests |
| Messages and images are untrusted evidence | injection and legitimate-amendment tests |
| Model chooses tools in a bounded loop; deterministic solver verifies result | scripted-model loop, cap, repair, and counterfactual tests |
| Batch persists every row, resumes by input/config fingerprint | checkpoint and failure-isolation tests |
| Real measured provider usage and reproducible package | usage reconciliation and fresh-checkout release checks |

Implementation sequence: ledger and plan verifier; financial reconstruction; evidence/OCR;
agent tools; batch/checkpoint; independent evaluation; release and interview documentation.
Tests run after every change. A failing test is a red stage and is not shipped. Audits
write only to temporary paths. Public examples are evaluation fixtures, never prediction labels.

Metrics named before changes: synthetic contract pass rate; sample numeric absolute and
relative error; sample status/method/date exact matches; changed rows/cells; coverage;
fallback count; model tokens and cost. No leaderboard or hidden-label claim is possible.

Robustness cases before input handling: raw and retrieved prompt injection, role-confusion
text, instruction-like image pixels, conflicting amendments, ambiguous cash states,
missing media/FX, angry legitimate questions, failed debit with outstanding liability,
and unrelated linked investment lifecycle records.

Git: use submission/buy-or-wait, commit each green increment, push without force. If
the organizer remote rejects writing, retain local commits and require an owned remote.
