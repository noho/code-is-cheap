# Fix 1 — accepted DS obligations

2026-10-18. Authorized fix author on existing branch `fix/subagent-native-exit-contract`; HEAD remained `381fe24b50eae00661e6c60677efdee3f178c752`. Changes remain unstaged and uncommitted. This is implementation/validation evidence for controller adjudication and independent review, not a code-gate pass or final closeout.

## Scope and completed changes

Read AGENTS.md and the binding goal, scope amendment, plan-v2, decisions, delivery amendment, implementation report, state, original source freeze and DS report `docs/reviews/code-review-20261018-100303.md`. Latest FIX AUTHORIZED dispatch permits only the accepted DS obligations. Mimo's exploratory FD work was not treated as an accepted finding; no launcher/FD change was made.

- **DS-C1:** `scripts/agent-run-result.py` now uses `ensure_ascii=True` at the final report serialization boundary. A duplicate-key exception may contain a lone surrogate before `validate_event_text` runs; JSON escaping makes this report valid UTF-8 without replacing, sanitizing or rewriting any decoded diagnostic string. Full final, free warning text, schema and native exit ownership remain unchanged. No new states, filters, truncation, retries, persistence or compatibility mechanism.
- **DS-C1 regression:** added one synthetic test in `tests/test_agent_run_results.py`, with 16 subcases: Codex/Claude × lone high `\ud800`/low `\udcff` duplicate keys × native 0/7 × collector/public runner. Each has a valid final and terminal, a Unicode/CRLF/whitespace final exceeding 12000 characters, an opaque structured warning and verbatim stderr. It captures bytes, strictly decodes UTF-8, parses JSON, checks exact outer/native agreement (collector itself 0), complete final, terminal, exact decoded duplicate-key diagnostic including the original surrogate, warning/stderr values and path/line provenance. Raw damaged source and stderr bytes are also checked. Test helpers gained optional byte capture and collector fixture environment forwarding only to support this regression. Its PATH contains only fail-closed fake `codex`/`claude` and explicitly selected `python3`, `jq`, `git`, `mktemp` utilities; custom launchers execute the synthetic Python runtime. No inherited host CLI fallback is reachable.
- **DS-C2:** replaced the two README Sub Agents overview claims about bounded retries / 重试上限 with caller-owned continuations/retries under existing user/project authorization and routes; runners do not automatically retry or switch providers. Inspected active READMEs, skills, backup README and catalog-source README for equivalent stale claims. The final ceiling-pattern scan finds only the correct skill sentence denying a fixed same-provider retry count. Historical audits/reviews were preserved. No prose-mirroring test was added.
- **DS question 2:** removed unused `clean=True` and `clean=False` from `tests/test_official_catalog_runtime.py`. No legacy verdict or assumed warning assertion was recreated. Official/native integration and kernel opt-ins remained disabled.

Only the five authorized existing product/test/docs files above changed, plus this required report. No additional equivalent serialization counterexample required source expansion. Controller-owned state/decisions/runs/reviews/receipts and all original evidence were not edited by this author. Existing controller worktree changes were left in place. No delegation, branch switch, staging, commit, push, PR, deployment, live probe, real model request or external network call was performed. Full-suite localhost fixtures and offline native catalog parsing are not live model coverage.

## Verification and actual outcomes

Python 3.11.15. All commands ran from `/Users/leo/workspace/code-is-cheap`. Fresh logs/manifests are under `/tmp/subagent-native-exit-fix1.vyO8eRyB/`; test stdout and stderr were combined using these exact redirections:

```bash
OFFICIAL_CATALOG_RUNTIME_TESTS=0 AGENT_SANDBOX_KERNEL_TESTS=0 PYTHONPATH=tests python3 -m unittest test_agent_run_results.RunnerResults.test_surrogate_duplicate_keys_preserve_utf8_json_native_exit_and_text > /tmp/subagent-native-exit-fix1.vyO8eRyB/surrogate-before.log 2>&1
OFFICIAL_CATALOG_RUNTIME_TESTS=0 AGENT_SANDBOX_KERNEL_TESTS=0 PYTHONPATH=tests python3 -m unittest test_agent_run_results.RunnerResults.test_surrogate_duplicate_keys_preserve_utf8_json_native_exit_and_text > /tmp/subagent-native-exit-fix1.vyO8eRyB/surrogate-after.log 2>&1
OFFICIAL_CATALOG_RUNTIME_TESTS=0 AGENT_SANDBOX_KERNEL_TESTS=0 python3 -m unittest discover -s tests -p 'test_agent_run_results.py' > /tmp/subagent-native-exit-fix1.vyO8eRyB/result-suite.log 2>&1
OFFICIAL_CATALOG_RUNTIME_TESTS=0 AGENT_SANDBOX_KERNEL_TESTS=0 python3 -m unittest discover -s tests > /tmp/subagent-native-exit-fix1.vyO8eRyB/full-offline-suite.log 2>&1
```

| Check | Actual exit / result |
| --- | --- |
| New regression before production fix | **1**, expected counterexample: 1 test, all 16 subcases fail (6 failures, 10 errors), 1.094s. High surrogate: collector crash / empty report, native 0 becomes outer 1. Low surrogate: raw 0xff causes strict UTF-8 decode failure. Native 7 high-surrogate runner retains 7 but loses its report. |
| Same regression after serialization fix | **0**, 1 test / all 16 subcases pass, 1.073s. |
| Focused result suite | **0**, 26 tests pass, 36.676s. |
| Required full offline suite | **0**, 236 tests, 24 conditional skips, 119.312s. No failures/errors. |
| Python AST syntax, three affected Python files | **0**, all parse. |
| Each shell syntax command below | **0**. |
| Skill validation | **0**, all six skills valid. |
| `git diff --check` | **0**, tracked diff has no whitespace errors. |
| New report diff check | **1**, expected `--no-index` new-file difference, empty diagnostic output; no whitespace errors. |

Exact syntax and skill validation commands (individual logs and argv retained in `checks.json` / `validation.json`):

```bash
python3 -B -c "import ast; from pathlib import Path; [ast.parse(Path(p).read_text(), filename=p) for p in ('scripts/agent-run-result.py','tests/test_agent_run_results.py','tests/test_official_catalog_runtime.py')]; print('3 Python files parse successfully')"
zsh -n scripts/codex-agent-run
zsh -n scripts/claude-agent-run
zsh -n scripts/agent-tools.zsh
bash -n scripts/sub-agent-preflight
./scripts/validate-skills.sh
git diff --check
git diff --no-index --check -- /dev/null docs/gateflow/subagent-native-exit-contract/fix1.md
```

Final active-document inspection command (exit 0; only `skills/sub-agents/SKILL.md:118`, the correct no-fixed-count policy, matches; output `active-docs-scan.log`):

```bash
rg -n -i 'bounded.{0,30}retr|retr.{0,30}(bound|limit|ceil|once|one|single)|重试.{0,30}(上限|最多|一次|限制)|同.{0,16}provider.{0,16}(重试|retry)' README.md README.zh.md skills scripts/backup/README.md codex-agent/catalog-sources/README.md --glob '*.md'
```

The full suite was run once on the final product bytes after focused validation; no unchanged passing full suite was repeated. Its log contains expected synthetic catalog-parser rejection/warnings and the actual `OK (skipped=24)` result, not a test failure. The pre-fix regression failure above is retained as evidence, not waived validation.

## Final source and log hashes

`source-after.json` contains all 15 original product-bundle file hashes, the unchanged HEAD, the original freeze-file hash and the exact five changed paths. All 15 files were checked against it again after the full suite. `validation.json` records test commands, observed return codes/results, syntax/skill argv and log hashes. The original `source-freeze.json` was neither replaced nor edited.

Final 15-file bundle SHA-256: `b580c570bdd9e43bfc79861440f4ff48f2cb8bc2b1b22bb7cddd4b8cef512502`. Same computation as original: SHA-256 of sorted UTF-8 lines `<relative path> <file SHA-256>\n`. This report is excluded to avoid a self-hash.

Original `source-freeze.json` SHA-256 (unchanged): `606fb685bc5227f09fb65298d82b5e92aa4c80f30e09be48096c79023521e0c7`.

Full-suite log SHA-256: `ff6ce7ad1b116ac20f1bcf5a42a02980b7758c4c7b804988b4f3ac371f50bec5`.

| File | Final SHA-256 |
| --- | --- |
| `README.md` | `50aa8a4c9cce53b191db1d1375da5877b1d467da883d252691b88d74559644a5` |
| `README.zh.md` | `04781f1d15443c71030170b82162a9b07b414e4a4744719d47ae84eeb323af09` |
| `scripts/agent-endpoint.py` | `ae9e34b45a749c057a3c1074c0d450c7350903bb657af0f54baa68fb27644a59` |
| `scripts/agent-run-result.py` | `0f473f12d70b9c2c3bc29e83250f97bbf2c6aceeb9539ec35fa3a0d64494ae74` |
| `scripts/agent-tools.zsh` | `f9b736191b83d89cb1dd64b9433c444afd836cb234ed57646c79c87f2f40aa1b` |
| `scripts/claude-agent-run` | `d2e47517a36dadbc72f125b63a57e0c1bf6dbfe64ede24c461c5a8205554c52d` |
| `scripts/codex-agent-run` | `bb4f61e0d07fe74b74f9023abb95ba3194fd2a5d4ec75705635001223a0884d1` |
| `scripts/sub-agent-preflight` | `b547a2a85a67fd812d71b5c45763d25184603cf3d5c90e256530fed2cc20480e` |
| `skills/sub-agents/SKILL.md` | `a40660709e3c9d3fa5e6bbebbacb8895e1ad47797c75a7d135508ce0e1518796` |
| `skills/sub-agents/references/advanced.md` | `8b359a88fc36909f9846c510cff5db20b802fad1335a5db663c90e8c549ec307` |
| `tests/test_agent_run_results.py` | `8b2e240a535c26c16137424abe41ee8f7ab282a1156bf3e30ee4d11ce80d8660` |
| `tests/test_agent_sandbox_runtimes.py` | `245d960312dd9c9ebf4d93c521675b1d4f813f9894b271d7ffdb7ea4b47072aa` |
| `tests/test_install_endpoints.py` | `eca12585e202f0d1ebce03e6d29c24576d0db9579464af4707f9cbe15dd42405` |
| `tests/test_official_catalog_runtime.py` | `75bf6f0a3cff1656f2a99aff151d8046ccc57c9481c5eba3c65a2722acf7fa32` |
| `tests/test_sub_agent_preflight.py` | `b7025dd9947f02a43e3d2943bc3fdf2399044d26e9930fbe89f260eb518b97e3` |

## Remaining work, risks and uncovered coverage

- No known implementation/validation blocker remains for the three accepted DS obligations. Controller must adjudicate these fixes and obtain Mimo's still-required complete combined review plus DS affected re-review on this actual fixed source. This author claims neither review approval nor gate closure.
- `OFFICIAL_CATALOG_RUNTIME_TESTS=0` and `AGENT_SANDBOX_KERNEL_TESTS=0` throughout: real native/model/host integration and kernel isolation opt-ins were not executed. Existing 24 conditional skips are not claimed coverage. No live sync, installed-byte comparison or real-runtime probe was performed.
- Caller-owned acceptance/retry decisions, external schema-v1/custom-launcher migration, unrepresented native/OS variants and abrupt wrapper/host loss remain as classified in the existing controller artifacts. No supervisor/result-store/recovery system was added. Warning/stderr volume remains verbatim and uncapped as resolved by the controller; caller/runtime maintainers own any resulting output-volume cost.
- The suggested missing-capability preflight fixture remains explicitly deferred, not a required fix. Mimo FD explorations supply no accepted finding and prompted no change. Controller retains gate, commit/PR, authorized deployment and probe responsibilities under the original delivery amendment; merge remains user-owned.
