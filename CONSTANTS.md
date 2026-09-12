# Constant provenance

| Constant | Value | Provenance | Reason / guarantee boundary |
|---|---|---|---|
| Forecast horizon | 90 days | SPEC | Fixed challenge safety interval |
| Partial payments | Exactly 2 | SPEC | Today-safe amount, remainder at unchanged earliest full date |
| Optional changes | At most 3 | SPEC | Distinct permitted recurring flexible events |
| Decimal quantization | 0.01, half-even | JUDGEMENT / STANDARD implementation | Data uses hundredths; FX rates preserve their own precision |
| Monthly observations | 3 distinct months | JUDGEMENT | Avoid recurrence from single unusual purchase |
| Monthly median gap | 25–35 days | JUDGEMENT | Calendar-month detector; not proof for arbitrary recurrence |
| Posting-day range | At most 3 days | JUDGEMENT | Allows small posting drift |
| Recent monthly observations | 3 | JUDGEMENT | Debit envelope is max recent; salary is authoritative/latest |
| Variable amount observations | 6 | JUDGEMENT | Recent median limits one-off outlier influence |
| Variable buffer | 1.10 | JUDGEMENT, compared experimentally | 1.20 and 1.30 worsened sample relative error; not globally optimal |
| Agent cap | 12 model steps | BOUND | Explicit insufficient-evidence fallback at cap |
| Output repair | 1 retry | BOUND | Second rejected finish falls back |
| Model temperature | 0 | JUDGEMENT | Reduces hosted variation; does not establish bit stability |
| Maximum model response | 2400 tokens | BOUND | Limits each response, not entire batch |
| HTTP attempts | 3 | BOUND | Retry transient status/network failure |
| HTTP retry sleep | 1 then 2 seconds | JUDGEMENT | Deterministic exponential backoff |
| HTTP timeout | 60 seconds | BOUND | Avoid indefinite model call |
| Budget framing allowance | 2000 raw token units | JUDGEMENT | Conservative reservation alongside UTF-8 payload-byte bound |
| Budget default | USD 10 | JUDGEMENT | Configurable; requires actual selected model prices |
| Installment cap convention | payment count <= max months | JUDGEMENT | Monthly offers in this dataset; arbitrary nonmonthly terms need review |

No sampling/randomness is used by the offline runtime. Test fixtures do not contact providers.
