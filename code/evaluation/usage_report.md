# Model usage report

Provider: openrouter. Model: google/gemma-4-31b-it:free. Requests: 250.

| Calls | Input tokens | Output tokens | Total tokens | Average tokens/request |
|---|---|---|---|---|
| 259 | 13275 | 90 | 13365 | 53.46 |

Estimated total cost: USD 0.000000. Average per request: USD 0.000000.
Configured USD/million input tokens: 0; output: 0.

Provider-reported charge: USD 0.000000; available for 9/259 calls. This is not the configured-price estimate.
Usage completeness: INCOMPLETE; calls missing token usage: 250. Token totals cover only measured responses.
HTTP attempts: 1025. Returned models (calls): {"google/gemma-4-31b-it:free": 9}.

Input/config fingerprint: `7d1613c89aa1bb04e79a72a7ea54b28faa2b46f64cd952d3d46cfc8509cb02da`. Output SHA-256: `cd11a5169a9c78af6c23556fc78d2c256f38a3ced8394519309d30fcb0175d4f`.

Usage is summed from the row checkpoints of this run, including resumed rows. Hosted calls are measured from provider usage, not guessed from text length. Failed HTTP requests without returned usage cannot be reconciled from the API response. Retry attempts without returned usage may incur unmeasured charges; configured-price estimates exclude such charges. Development-chat tokens are not the submitted runtime's model usage.

## Per-attempt reconciliation

HTTP/network attempts observed: 1025; statuses: {"200": 9, "429": 1015, "NETWORK/NO_HTTP": 1}.
Key phases: {"fallback": 765, "primary": 260}; fallback activations: 259; recoveries: 9.
Attempts without token usage: 1016; attempts with reported cost: 9.
HTTP usage completeness: INCOMPLETE. Tokens and provider charges above are measured-response subtotals; total cost UNKNOWN when any attempt has no returned cost.

## Final 250-row outcome and retry audit

Measurement source: `runs/final-submission-250.jsonl`. This is the actual final production
run against all 250 evaluation requests, not development smoke totals. All output IDs are
unique and match `dataset/requests.csv`. Schema, checkpoint correspondence, current-source
fingerprint and independent artifact validation passed.

**Accepted model decisions: 0/250. Terminal RATE_LIMIT outcomes: 250/250.**
All outputs are the existing explicit insufficient-evidence no-payment fallback rows.
The nine successful model responses retrieved evidence but did not complete a decision.
These are infrastructure failures, not demonstrated model reasoning errors. No predictions
or image-derived facts were manually patched. There are no positive plans to replay in this
hosted output; the separate offline regression validates 100 plans, not 100 hosted decisions.
Valid evaluation ground truth is unavailable; payment-method, affordability and exact
financial-decision accuracy are UNKNOWN.

| Additional final-run metric | Measured value |
|---|---:|
| HTTP 200 / 400 / 429 | 9 / 0 / 1015 |
| Network attempt without HTTP response | 1 |
| Successful / unsuccessful attempts | 9 / 1016 |
| Explicit terminal key-quota 429 classifications | 259 |
| UNKNOWN-scope provider 429 classifications | 756 |
| Explicit transient-rate-limit classifications | 0 |
| Fallback 429 attempts beyond the first attempt in their phase | 503 |
| Whole requests recovered to accepted decisions | 0 |
| Full-run wall-clock seconds / average per request | 1672.543 / 6.690 |
| Sum measured HTTP-attempt seconds | 909.460 |
| Total provider-reported cost | UNKNOWN |

Reported USD 0 covers only nine responses with returned charges. The configured free-model
prices yield an estimated USD 0 total/per-request; that is not a provider billing report.
Missing usage is not zero usage: 13365 tokens is only the measured-response subtotal.
1016 attempts have unavailable usage/cost and 250 logical calls lack usage.

The unchanged policy stopped explicit primary daily quotas and used the existing fallback.
UNKNOWN-scope fallback limits retained normal bounded retries, including 503 repeated 429
attempts. Nine fallback recoveries were logical responses, not completed requests.
No third key, model routing, prompt optimization or policy change occurred during this run.
Native-image acceptance remains unverified; rate limits prevented completion of image tools.

The strict release certification helper still rejects incomplete usage and unresolved
fallbacks. A physical upload ZIP does not override that gate or certify hosted success.
This artifact set preserves the user's explicitly requested actual full run and its supported
safe error-handling output, with failure measurements disclosed rather than concealed.
