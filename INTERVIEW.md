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
