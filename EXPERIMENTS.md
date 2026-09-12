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

Counterfactual tests: removing evidence retrieval removes its financial effect in scripted-agent
tests; removing pixel text prevents extraction; deliberately unsafe payments fail both the
production verifier and independent replay. These are component tests, not a claim that hosted
Claude is accurate. Hosted sample/full runs have not occurred because no API key is configured.

A new checkout and isolated Python environment installed README dependencies, passed the suite,
and regenerated all 250 offline rows with cold pixel OCR. Its SHA-256 matched the pinned baseline;
independent Decimal replay verified 100 recommended payment plans with zero failures. One
handwritten-image row remained an explicit insufficient-evidence fallback. These checks establish
reproducibility and conditional arithmetic safety, not prediction correctness.
