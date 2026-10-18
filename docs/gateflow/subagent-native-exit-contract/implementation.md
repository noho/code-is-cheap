# S1 implementation evidence — native CLI exit / full final

2026-10-18. Work branch reused: `fix/subagent-native-exit-contract`; checkout HEAD throughout implementation: `92757b8dbb1291bfe3d1b2c9f56f90c0218d2571`. Changes are uncommitted. This is implementation/verification evidence for controller review, not independent code review or runner task acceptance.

## Changed scope and contract

- `scripts/{codex,claude}-agent-run`: exact native wait status, Codex pipeline component status, complete prompt bytes, raw detail mode, and primary-delivery exceptions only. Auxiliary final missing/copy/race/mismatch/cleanup observations preserve native exit and retained source; no-clobber remains. Wrapper duplicate descriptors are closed before launch.
- `scripts/agent-run-result.py`: schema 2, full original final, one source-linked diagnostics list and optional `checks`. Removed competing verdicts, exit rollup, length/cap metadata, three diagnostic classes/counts and success-proof/text-suspicion logic. Opaque warning strings retain original whitespace/text; no known-warning exception, recovery inference or wording-dependent behavior. Parser/check observations serialize with collector exit 0.
- `scripts/agent-tools.zsh`, `scripts/agent-endpoint.py`: invocation-local error-only pre-exec pipe, CLOEXEC, original exec failure causes and no native descriptor/environment leakage. Ordinary interactive calls retain their behavior. Only terminal helper invocations own the handoff; setup connection queries return normally. Executable resolution is fixed to one PATH target, without fallback to a different executable after a missing interpreter.
- `scripts/sub-agent-preflight` and its tests: explicit launcher capability prerequisite; optional checks described as caller-owned observations. Unsupported/stale `AGENT_TOOLS_FILE`/helper combinations fail before entry; supported custom success and setup-error paths are exercised. No provider setup duplication, lifecycle/store/supervisor, routing/config/permission change, or agent-sandbox implementation change.
- `tests/test_agent_run_results.py`, `tests/test_install_endpoints.py`, opt-in consumers `tests/test_{official_catalog_runtime,agent_sandbox_runtimes}.py`: migrate v1 assertions; assert actual outer/native agreement rather than business inability implying nonzero. M-v2-1 includes root intermediate assistant text plus missing/empty/nontext, nested-only and ambiguous root result cases; none substitutes assistant/nested text for final. Raw partial material remains in logs.
- `README.md`, `README.zh.md`, `skills/sub-agents/{SKILL.md,references/advanced.md}`: complete v2 migration, native/setup/delivery ownership, custom-launcher skew/activation, full final and informational checks. Removed fixed same-provider retry ceiling; caller owns subsequent interactions under existing authorization/routing. Measurement samples/history/concurrency policies remain.

Controller goal/state/decisions, reviewer reports and historical investigations were not edited. Concurrent controller-owned delivery-amendment/baseline changes are outside this agent's edits. No delegation, branch/staging/commit/push/PR, installed-tool sync or deployment was performed by this implementation turn. The unintended fixture invocation described below is not an authorized delivery probe.

## Verification

Python `3.11.15` (`/opt/homebrew/bin/python3`); existing PyYAML `6.0.3` environment (`/opt/homebrew/opt/python@3.11/bin/python3.11`). No dependency installation or network/security configuration change. Local HTTP/shell fixtures executed; no sandbox restriction blocked the required offline checks.

| Exact command | Actual exit / result | Retained log |
| --- | --- | --- |
| `python3 -m unittest discover -s tests -p 'test_agent_run_results.py'` | 0; 25 tests | `/tmp/native-exit-result-tests-final-v2.log` |
| `python3 -m unittest discover -s tests -p 'test_sub_agent_preflight.py'` | 0; 13 tests | `/tmp/native-exit-preflight-tests-final.log` |
| `python3 -m unittest discover -s tests -p 'test_install_endpoints.py'` | 0; 24 tests | `/tmp/native-exit-endpoint-tests-final-v2.log` |
| `python3 -m unittest discover -s tests -p 'test_agent_sandbox.py'` | 0; 80 tests, 10 skipped | `/tmp/native-exit-sandbox-tests-v2.log` |
| `PYTHONPATH=tests python3 -m unittest test_install_endpoints.RunnerNativeBoundaryTests` | 0; 5 tests | `/tmp/native-exit-boundary-tests-final.log` |
| `PYTHONPATH=tests python3 -m unittest test_agent_run_results.RunnerResults.test_full_final_unicode_and_whitespace_round_trips_every_entry` | 0; 1 test | `/tmp/native-exit-long-final-check.log` |
| `zsh -n scripts/codex-agent-run`; `zsh -n scripts/claude-agent-run`; `zsh -n scripts/agent-tools.zsh`; `bash -n scripts/sub-agent-preflight` | each 0 | tool transcript |
| `./scripts/validate-skills.sh` | 0; all 6 skills valid | tool transcript |
| `OFFICIAL_CATALOG_RUNTIME_TESTS=0 AGENT_SANDBOX_KERNEL_TESTS=0 python3 -m unittest discover -s tests` | 0; 235 tests, 24 skipped; 106.651s | `/tmp/native-exit-all-tests-final-v2.log` |
| `git diff --check` | 0, including final report | tool transcript |

Meaningful assertions cover actual native 0/1/2/7/126/127, no native protocol events, genuine setup/exec failure versus equal numeric native returns, custom/stale launchers, normal interactive calls and all internal FDs closed. They also cover explanatory finals with absent reports, damaged/missing/unreadable logs, root final ownership, exact Unicode/CRLF/leading/trailing whitespace beyond 12000 characters through collector and both runners, same-envelope SSE/catalog/arbitrary warning variations with exact preserved text, tool errors, negative native metadata, check provenance/secondary proof offsets, hard-link/log aliases, detail behavior, private staged installation, auxiliary copy/cleanup failures, collector crash/missing/serialization/OS stdout-write failures, and large prompt SIGPIPE/consuming byte equality.

Intermediate failures were fixed rather than waived: inherited zsh EXIT traps, raw-detail stdout accidentally entering the error pipe, duplicate FD inheritance, setup-query handoff ownership, canonical fixture paths, and a newly extended auxiliary-final fixture still seeding `FINAL=done`. The first runner suite was exit 1 (25 tests, 5 failures); initial endpoint suite exit 1 (23 tests, 2 failures); initial sandbox suite exit 1 (80 tests, 1 failure, 10 skipped). An intermediate full suite passed 234 tests/24 skips; a later intermediate full run exited 1 (234 tests, 1 fixture failure, 24 skipped). Those are not final frozen-source claims. Final results above supersede them; focused checks were repeated only after affected changes/failures, plus the mandatory full check.

**Unintended network invocation during fixture development:** the missing-interpreter case initially used `execvpe` with the inherited PATH. It fell through from the fake executable to the host Codex. The retained failure output shows seven HTTP 401 responses and no captured model final; the intermediate wrapper reported outer 2 and no trustworthy native report, so no native exit/model success is asserted. The process had exited when its test result was collected. This violated the intended offline fixture boundary; fixed by hermetic fixture PATH and single-target `execve` resolution, with deterministic regression coverage. Evidence: `/tmp/native-exit-endpoint-tests.log`, SHA-256 `0b44f9a134a47720470446f6494252e9f764e330ae8fe01ed81a241401c29628`. It does not satisfy or substitute for either authorized future mimo-flash probe.

Final full-suite log SHA-256: `f070fda6b7fd3206409e76481a133f507a33cdc72fcd2d546953ae8910f43846`. All 15 frozen files matched the manifest after the final suite. Live/kernel opt-ins stayed disabled.

## Frozen source evidence

Bundle SHA-256: `e73c2046f0da4f9a580906fadb5cc0ba8046790b9a96bb07f4101df31ebc86d5`. Computation: SHA-256 of sorted UTF-8 lines `<relative path> <file SHA-256>\n` for exactly the following 15 implementation files. This report is excluded to avoid a self-hash. Manifest also retained at `/tmp/subagent-native-exit-final-source-sha256.json`; frozen files were rechecked unchanged during validation.

| File | SHA-256 |
| --- | --- |
| `README.md` | `60b21fe7e0d92eb14916bbbb5b29cc2a14d590f168d234550f7bbcc8a7940a4f` |
| `README.zh.md` | `7bffc6f9ca7d52afd65ff8dd6f2d6b94c81a8f67abb45713ece195b726a362e8` |
| `scripts/agent-endpoint.py` | `ae9e34b45a749c057a3c1074c0d450c7350903bb657af0f54baa68fb27644a59` |
| `scripts/agent-run-result.py` | `8345f1267f2e2d4e0b68af1397dcdb607b49f973cf11280cb291720e314d3c27` |
| `scripts/agent-tools.zsh` | `f9b736191b83d89cb1dd64b9433c444afd836cb234ed57646c79c87f2f40aa1b` |
| `scripts/claude-agent-run` | `d2e47517a36dadbc72f125b63a57e0c1bf6dbfe64ede24c461c5a8205554c52d` |
| `scripts/codex-agent-run` | `bb4f61e0d07fe74b74f9023abb95ba3194fd2a5d4ec75705635001223a0884d1` |
| `scripts/sub-agent-preflight` | `b547a2a85a67fd812d71b5c45763d25184603cf3d5c90e256530fed2cc20480e` |
| `skills/sub-agents/SKILL.md` | `a40660709e3c9d3fa5e6bbebbacb8895e1ad47797c75a7d135508ce0e1518796` |
| `skills/sub-agents/references/advanced.md` | `8b359a88fc36909f9846c510cff5db20b802fad1335a5db663c90e8c549ec307` |
| `tests/test_agent_run_results.py` | `04b16a86469e3c58d3f79f82ef80e838aa8894f91d675e288389a89d8b4f8f57` |
| `tests/test_agent_sandbox_runtimes.py` | `245d960312dd9c9ebf4d93c521675b1d4f813f9894b271d7ffdb7ea4b47072aa` |
| `tests/test_install_endpoints.py` | `eca12585e202f0d1ebce03e6d29c24576d0db9579464af4707f9cbe15dd42405` |
| `tests/test_official_catalog_runtime.py` | `ca3064a6255d84870784abc19e7efc7fdb5bc0c16ede8d834b26599e9dcc832b` |
| `tests/test_sub_agent_preflight.py` | `b7025dd9947f02a43e3d2943bc3fdf2399044d26e9930fbe89f260eb518b97e3` |

## Residual risks / next owner

- Current-slice exit/final/diagnostic/launcher migration is implemented and exercised offline; independent reviews/adjudication remain controller-owned. No implementation blocker is known; the final frozen-source full suite exited 0.
- External v1/custom-launcher callers must adopt v2 and honestly implement pre-exec-error-v1. Owner: caller/launcher maintainers; destination: caller integration. A declaration alone cannot verify an arbitrary custom implementation's honesty; unsupported/skewed implementations are rejected before launch.
- Official model/native integration and kernel opt-in suites remain disabled and unexecuted. Existing offline catalog-parser tests are not model integration evidence. Unrepresented protocol/OS variants: runtime maintainers/controller own follow-up when needed.
- Abrupt wrapper/host loss before observing wait or primary delivery remains uncovered; no exit/final is fabricated. Owner: maintainer; destination: separate explicitly authorized lifecycle/recovery work, not this slice.
- Reviewed-vs-installed skew and required probes are **fixed in current slice (required, pending authorized delivery)**, owner controller. Per `delivery-amendment.md`, controller is authorized and required, **after independent code review and PR delivery checks**, to sync approved work-branch source and run the two real mimo-flash three-step math probes (Codex and Claude). This implementation does not perform those steps or claim deployment/probe success. Next entry: controller code review, accepted fixes if any, draft PR checks, then authorized sync/probe evidence and closeout. Merge remains user-owned.

Applicable future sync commands, from the checkout containing the reviewed changes:

```bash
./scripts/sync-agent-tools.sh
./scripts/sync-skills.sh
```

`sync-codex-agent.sh` is not applicable (no profiles/catalogs/routes/shim change). Controller must check installed/source drift before sync and retain hashes/byte comparisons. Interactive launcher users reload with `source ~/.zshrc` or open a new shell; reopen Agent sessions for skills. Installed runner callers already on PATH need no shell reload. Preserve the existing work-unit directory as the caller patrol/handoff entry point.
