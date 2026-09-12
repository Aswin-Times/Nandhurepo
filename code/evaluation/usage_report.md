# Final OpenRouter hosted-run usage is pending

No live OpenRouter model run has occurred yet; key/model are not configured. Offline baseline reports are generated beside their
outputs and explicitly report zero runtime model calls. They are not final submission usage.

The final command in SOLUTION_README.md writes this report from real row-checkpoint usage,
including provider/model, calls, input/output tokens, per-request averages, configured prices,
estimated cost separately from provider-reported charge, missing-usage flags, input/config
fingerprint and output hash. Mocked provider test fixtures are not real usage and are not included
as final-run measurements. Packaging maps it to the required
`evaluation/usage_report.md` path in code.zip and rejects mismatched or offline artifacts.
