# OpenRouter migration inventory and acceptance plan

Audited at `b1b3acc` before implementation: tracked source, tests, hidden CI/config,
documentation, requirements, and generated-artifact references. Historical ignored transcripts
and manifests are retained, not rewritten as new runs. No provider SDK is installed by requirements.

| File | Previous dependency / purpose | Replacement |
|---|---|---|
| code/model_provider.py | Direct Messages HTTP endpoint, key header/env, payload/response/errors | OpenRouter chat completions adapter; Bearer OPENROUTER_API_KEY; normalized internal response |
| code/main.py | AnthropicModel import, provider choice, hosted construction/model flags | OpenRouter hosted default; env model; injectable provider; explicit offline remains key-free |
| code/financial_agent.py | Block tool-call/result messages, input/output token fields | Retain provider-neutral internal block contract; adapter translates wire messages; carry routing/reasoning/usage metadata |
| code/financial_tools.py | input_schema definitions and base64 image blocks | No financial edits; adapter converts schemas to function parameters and PNG blocks to image_url |
| code/model_usage.py | Normalized token accounting and configured-price cost | Map actual prompt/completion tokens; retain measured API charge separately from configured-price estimate |
| tests/test_agent.py | Scripted block responses bypass HTTP boundary | Retain component tests; add integration through real OpenRouter adapter with only HTTP mocked |
| tests/test_usage.py, tests/test_release.py | Previous provider labels in usage/package fixtures | OpenRouter fixtures and measured-cost tests |
| SOLUTION_README.md | Key, commands, direct-provider/tool-use documentation | OpenRouter setup, model capabilities, controlled smoke run, no direct-provider credentials |
| EXPERIMENTS.md, INTERVIEW.md | Claude references and untested-hosted limitations | Preserve historical facts, identify new OpenRouter measurements and limitations |
| SPEC.md, CONSTANTS.md | General model contract, timeouts/budget assumptions | Explicit adapter/security contract and OpenRouter budget boundaries |
| code/evaluation/usage_report.md | Pending hosted report | Pending OpenRouter full run; never substitute mocked or offline usage |
| README.md, .gitignore, CI, requirements.txt | General setup/secret/contract policies, no direct API dependency | Inspect and clarify hosted entry point; retain env ignores and SDK-free implementation |
| AGENTS.md | Lists coding harnesses including Claude Code; references CLAUDE.md | Organizer instructions, not a runtime dependency; preserve unchanged |
| code/forecast_experiments.py | Implicit offline run default | Explicit offline arm so hosted-default migration cannot incur charges |
| code/release_submission.py | Generic hosted manifest gate | Require supported hosted provider and current matching artifacts |

The internal `complete(system, messages, tools)` interface returns text/tool-call blocks plus
normalized measured usage. Its block names are a project protocol, not HTTP payload fields.
Only the adapter constructs HTTP. It converts native tool calls and JSON arguments, sends
all tool schemas on every turn, preserves assistant reasoning details across turns, and moves
image evidence into a paired untrusted user image message when returning textual tool results.
No changes to recurrence, financial constraints, ranking, amendment rules, or output schema.

Baseline: 47 tests pass; 250 rows SHA-256
`66d188bbd0c7a36769632197d3d68d5a34865f6dd57db36d2c1c0e8584e4789c`;
100 independent payment replays pass. Public methods/plans 14/25, statuses 13/25,
earliest dates 13/25, spending actions 21/25; no invalid rows. Keys/models absent in environment.

TDD acceptance: configuration/missing key; actual HTTP construction and response normalization;
multi-tool turns and PNG handoff; JSON argument repair; missing/malformed usage and responses;
transient retries/timeouts; permanent and embedded errors; redaction in outputs/exceptions;
provider-boundary negative control; complete real-tool batch/report/replay/package tests with
only transport mocked. Re-run full offline/sample artifacts and measure zero financial blast
radius before considering accuracy optimization. A live small sample runs only if env key/model
and explicit prices are configured; no full paid batch is authorized by the smoke-test step.

Official contracts: [tool calling](https://openrouter.ai/docs/guides/features/tool-calling),
[image inputs](https://openrouter.ai/docs/guides/overview/multimodal/image-understanding),
[usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting).
