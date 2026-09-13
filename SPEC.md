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

## OpenRouter migration contract

Hosted defaults to OpenRouter using OPENROUTER_API_KEY and OPENROUTER_MODEL, with optional
trusted HTTPS OPENROUTER_BASE_URL. Explicit offline never constructs a provider or requires
credentials. No direct Anthropic HTTP or credential dependency is allowed in runtime source.
Keep financial modules unchanged during transport migration. The injectable HTTP adapter
translates the existing internal block protocol into native function-call/chat/image messages;
the agent does not perform HTTP. Preserve multi-tool turns, reasoning continuation, one repair,
safe fallback and all deterministic plan verification. Actual usage missing from a response
must be marked incomplete, never inferred from text; charges and estimates stay distinct.

Acceptance evidence: provider payload/response tests, malformed-data and key-redaction controls,
an intentionally broken adapter detected by the positive contract test, actual adapter-backed
real-tool batch/report/replay and synthetic full ZIP packaging, key-free offline execution,
unchanged 250-row and 25-row hashes, and 100 independent participant-plan validations.
Live smoke and public hosted accuracy require environment configuration; mocks cannot establish
live compatibility or improved financial correctness. Only optimize accuracy after those gates.

## Bounded secondary-key availability fallback

Optional OPENROUTER_API_KEY_FALLBACK is read once by the existing adapter. Each model
completion starts with the primary key; the same serialized request and model may use
the secondary key only after a classified availability failure. Each key gets the existing
three-attempt HTTP policy, with at most one secondary phase (six total HTTP attempts).
Missing/empty or identical secondary values preserve single-key behavior; no rotation.

Eligible failures: HTTP 402 quota, 408, 429, 500, 502, 503, 504, and exhausted existing
connection/timeout retries. HTTP 400/401/403/404, invalid input/tools, malformed model
responses, application bugs and financial/finish validation failures never trigger fallback.
An ambiguous 404 is deliberately not assumed to mean temporary provider unavailability.
Long Retry-After still ends that key's phase rather than sleeping beyond the existing bound.
Both credentials are redacted from request bodies, responses, errors and diagnostics;
only the selected Authorization header carries a key. HTTP usage counts both phases;
missing response usage is never fabricated. Budget reservation covers the adapter's
three- or six-attempt bound; failed/retried charges can remain unreported by the provider.

Acceptance: real adapter with mocked HTTP, primary-first/no-extra-key success, bounded
availability fallback, forbidden-error controls, identical model/body, next-call primary
reset, six-attempt failure safety, dual-key redaction and pre-network budget reservation.
Financial modules, prompt/tools/finish, label-free input projection and golden files stay unchanged.
