RUNTIME/PROVIDER/MODEL: codex/ds-flash/deepseek-flash
CANARY=ds-flash-5eac2c1a

# Code Review (focused closure review)

## Scope

- Mode: current changes, focused independent verification of the accepted first-round preflight finding (task label `e2big-ds-flash-20261009-r2`).
- Branch: `fix/agent-sandbox-large-policy-launch`
- Base: `690ec69116f95b79bcb1d1d60c9044ac36eff6d1`
- Frozen HEAD: `6672741e6a58939aba3a65c57c03843d2c92aa10` (verified before review; re-verified unchanged after all read-only work)
- Diff under review: `690ec69...6672741`, 7 files, +83/-11: `scripts/agent-sandbox-launch.mjs`, `scripts/agent-sandbox`, `tests/test_agent_sandbox.py`, `tests/test_agent_sandbox_launch.py`, `README.md`, `README.zh.md`, `docs/reviews/agent-sandbox-e2big-validation-20261009.md`
- Output file: `docs/reviews/e2big-ds-flash-20261009-r2.md`
- Included scope: `validateRuntime` and `--validate` mode; the `agent-sandbox --check` integration and its ordering relative to `setup_status=ok`, state creation and launch; the pinned `@anthropic-ai/sandbox-runtime` 0.0.79 package/module layout; the two changed test files; Agent-facing README/validation-doc changes.
- Excluded scope: MiMo reports, portfolio-manager-v2, business inputs/history, original dispatch commands, endpoint/auth/key files, user sessions/workflows, network access, live sync, kernel-test reruns, source edits, git writes. No other repository modules were re-read beyond what this fix touches.
- Parallel review coverage: none. The task explicitly prohibited subagent dispatch.
- Kernel evidence: the controller-reported 25 native Seatbelt/Codex/Claude local-mock tests and 92 ordinary tests (9 kernel opt-in skips) are treated as supplied input evidence, not independently reproduced here. No native/kernel test was rerun.

## Finding Status

### r1 finding `1-未修复-低` (`agent-sandbox --check` can report `setup_status=ok` for standalone srt 0.0.79) — RESOLVED

- **Fix ownership**: `scripts/agent-sandbox-launch.mjs:128-144` adds `validateRuntime(srt)`: `realpathSync` -> package root -> `package.json` name/version/`bin.srt` mapping -> existence/readability of `dist/cli.js`, `dist/utils/shell-quote.js`, `dist/sandbox/macos-sandbox-utils.js`. Single error wrapper at `:142` always carries the actionable `reinstall with install-agent-sandbox.sh` instruction plus the underlying cause.
- **Shared use is real**: `--validate` mode at `:148-151` calls the same function, and the real launch path at `:157` now calls it too (the previous inline check was replaced, not duplicated). `scripts/agent-sandbox:370-372` invokes `node <launcher> --validate <srt>` and raises `ValueError` on nonzero exit before the `args.check` branch at `:390-398` can print `setup_status=ok`, and before state creation at `:399+`.
- **Old repro now rejected (reproduced end-to-end this round)**: synthetic HOME/PATH fixture with a standalone `/bin/sh` shim printing `0.0.79` -> `agent-sandbox --check ...` returned rc=1, stdout contained no `setup_status=ok`, stderr contained `agent-sandbox: agent-sandbox-launch: srt 0.0.79 Node package CLI and required modules must be readable; reinstall with install-agent-sandbox.sh (ENOENT: ... package.json)`. The r1 false-accept path is closed, and the raw `ENOENT package.json` is now wrapped in the intended operator guidance.
- **Non-spawning / no-CLI-import proof (marker experiment)**: a fake standalone `srt` that appends to a marker when executed left the marker absent under `node agent-sandbox-launch.mjs --validate <fake>` (rc=1) — the validation itself never spawns the candidate. A fixture package whose `dist/cli.js` writes a marker on import validated rc=0 with the marker absent — the CLI is never imported/executed by validation. The good fixture used valid `package.json`/`bin`/modules, so rc=0 also proves the pass path does not depend on executing the package.
- **No compaction/permission drift**: the launcher diff touches only the `node:fs` import list, the new `validateRuntime`, the `--validate` branch, and the launch-path call. `decodeArgv`, `compactDenyRules`, `fileBackedArgv` and the profile write modes (`wx`/`0o400`, `0o600` then `chmod 0o400`, `seatbelt.source.sb` at `0o400`) are byte-identical to base; `scripts/agent-sandbox` gained exactly the 3 validation lines. The compaction regression test (`test_compaction_preserves_exact_path_regions_and_other_rules`) and the large-profile test pass unchanged.
- **Supported install unaffected**: real deployed install (`/Users/leo/.local/bin/srt` -> `/Users/leo/.local/share/agent-sandbox/node_modules/@anthropic-ai/sandbox-runtime/dist/cli.js`) returned rc=0 with `setup_status=ok`; `--validate` returned rc=0 both through the symlink and directly against `dist/cli.js`.

## Findings

未发现实质性问题。

这轮 diff 只包含 accepted finding 的修复、对应测试和文档更新；未发现新的 correctness、stability、security 或 architecture defect。

## Verification

Ordinary (non-kernel) focused suites, run on Node v25.9.0 / Python 3.11.15:

- `python3 -m unittest discover -s tests -p 'test_agent_sandbox_launch.py' -v`: 6 run, OK, 1 native-Seatbelt skip. Includes the new `test_runtime_validation_is_nonspawning_and_rejects_incomplete_installations` (`tests/test_agent_sandbox_launch.py:36-58`).
- `python3 -m unittest discover -s tests -p 'test_agent_sandbox.py' -v`: 17 run, OK, 6 kernel-gated skips. The new `test_preflight_rejects_standalone_srt_before_reporting_success` (`tests/test_agent_sandbox.py:210-219`) sits in the `KernelTests` opt-in class, so it was skipped here by design; I reproduced its exact scenario manually end-to-end (scenario B below) in an ordinary synthetic environment.
- `node --check scripts/agent-sandbox-launch.mjs`: pass. `git diff --check 690ec69...HEAD`: pass.
- Synthetic driver: `/private/tmp/e2big-r2/driver.py`; results JSON: `/private/tmp/e2big-r2.zhnl_tap/results.json` (disposable scratch; synthetic HOME, synthetic `api_key` value, fake runner that was never executed in `--check`).

Scenario matrix (rc / evidence):

| # | Scenario | Result |
|---|---|---|
| A | `--check`, real symlinked install (codex/mimo, synthetic env) | rc=0, `setup_status=ok`, runner marker absent |
| B | `--check`, standalone shim printing 0.0.79 | rc=1, no `setup_status=ok`, stderr has reinstall instruction + ENOENT cause |
| C | `--validate`, deployed symlink | rc=0, no output |
| D | `--validate`, real `dist/cli.js` directly | rc=0 |
| E | `--validate`, standalone 0.0.79 shim | rc=1, reinstall message, shim marker absent (no spawn) |
| F | `--validate`, valid synthetic package (cli.js has import side-effect) | rc=0, cli marker absent (no import) |
| G | package `version=0.0.80` | rc=1, reinstall message (`package/layout mismatch`) |
| H | `bin.srt=dist/other.js` | rc=1, reinstall message |
| I | `name=other-package` | rc=1, reinstall message |
| J | `bin` as a string (not `{srt: ...}`) | rc=1, fail-closed |
| K | malformed `package.json` | rc=1, reinstall message + JSON parse detail |
| L | missing `dist/utils/shell-quote.js` | rc=1, reinstall message + exact missing path |
| M | missing `dist/sandbox/macos-sandbox-utils.js` | rc=1, reinstall message + exact missing path |
| N | nonexistent `srt` target | rc=1, reinstall message + `lstat` path |
| O | `--validate` with wrong argv count (`... extra`) | rc=1 `invalid internal srt launch` (fail-closed, no fallthrough into launch) |

## Exact Version Coverage

- Pinned dependency inspected at `/Users/leo/.local/share/agent-sandbox/node_modules/@anthropic-ai/sandbox-runtime`: `package.json` -> name `@anthropic-ai/sandbox-runtime`, version `0.0.79`, `bin.srt=dist/cli.js`; `dist/cli.js` (23,584 B), `dist/utils/shell-quote.js` (2,333 B), `dist/sandbox/macos-sandbox-utils.js` (57,260 B) all present as readable regular files.
- Required-module set is a genuine dependency slice, not arbitrary: `dist/cli.js:3` imports `./utils/shell-quote.js` directly; `dist/sandbox/macos-sandbox-utils.js` is imported by `dist/sandbox/sandbox-manager.js` and `dist/sandbox/credential-mask-files.js` (macOS policy/credential path).
- `scripts/agent-sandbox:19` `SRT_VERSION="0.0.79"` matches the literals in the validator (`:133`, `:142`).
- Deployed `srt` entry: `/Users/leo/.local/bin/srt` is a symlink resolving to the package `dist/cli.js`; both symlink and canonical-path forms pass.
- Version-skew behavior: package version `0.0.80` rejected; an actually installed 0.0.80 would first be rejected by the pre-existing `srt --version` probe (`scripts/agent-sandbox:367-369`, unchanged by this diff).
- Not covered this round: any srt version other than 0.0.79 (pinned by design), Node 22.12 execution (checks ran on v25.9.0), non-macOS platforms (script refuses non-Darwin), and content-hash integrity of package files.

## Adversarial Pass (focused on this fix)

- **Can a standalone/non-package `srt` still reach `setup_status=ok`?** Only a candidate that supplies a parseable `package.json` with exact name/version and `bin.srt` resolving to itself plus both required modules; such a candidate is structurally the pinned package layout. Any other candidate fails closed at `:133-139` before the check branch at `scripts/agent-sandbox:390`. No silent acceptance path found.
- **Can validation be bypassed on real launch?** No: preflight validates at `scripts/agent-sandbox:370-372`, and the launcher re-validates at `:157` in the same process immediately before importing the CLI; failure raises before any state dir, profile or runner work (`:399+`). Double validation is cheap and fail-closed.
- **Are diagnostics actionable?** Every rejection path emits `reinstall with install-agent-sandbox.sh`; filesystem failures include the exact failing path (`stat`/`open`/`lstat`), logical mismatches say `package/layout mismatch`, invalid JSON carries the parser detail. No swallowed error and no success-shaped fallback found.
- **Does validation have side effects?** No writes, no process spawn, no CLI import (marker-proved for both). Only `realpathSync`/`readFileSync`/`statSync`/`accessSync`.
- **Ordering/regression checks**: `args.check` returns only after validation; the ordinary compaction, quoting, and large-profile tests still pass; the diff introduces no shared mutable state or new global behavior.

## Agent-Facing Review

- `README.md:160` ("Preflight and launch share a non-spawning package/module-layout check. Unsupported CLI layouts fail closed.") and `README.zh.md:154` (对应中文) match the implementation: the check itself spawns no `srt` and never imports the CLI; unsupported layouts fail before `setup_status=ok`. The wording "non-spawning" describes the check's semantics (it is itself executed as a `node --validate` child from preflight); this is consistent with the accepted first-round recommendation and is not misleading.
- `docs/reviews/agent-sandbox-e2big-validation-20261009.md:85-97` new section accurately describes the shared validator, the three rejection classes, the reinstall instruction, the 25-test native rerun, and it correctly limits the historical-policy claim (365/4476 entries were ENOENT, "not claimed as complete open verification"). Those kernel numbers remain controller-supplied evidence, not reproduced here.
- No Agent-facing doc promises hash/integrity verification or universal compiler-limit removal; the residual limits remain explicitly documented.

## Read-File Coverage

- Fully read: `scripts/agent-sandbox-launch.mjs` (all 187 lines), `scripts/agent-sandbox` (lines 232-256, 300-332, 330-477; previously reviewed 1-474 in r1; this round also 1-60/context as needed), the complete `690ec69...HEAD` diff, `tests/test_agent_sandbox.py` (setup/fixture plus the new test), `tests/test_agent_sandbox_launch.py` (harness plus the new test), `README.md`/`README.zh.md` changed paragraphs and the validation-doc diff section.
- Dependency inspection: pinned `package.json`, module presence, `dist/cli.js` import line, `macos-sandbox-utils.js` importers.
- Not read this round: MiMo reports, portfolio-manager-v2, business inputs, dispatch commands, endpoint/auth/key files, user sessions/workflows, unrelated repository modules and unrelated tests; no network or deployment state.

## Open Questions

- 无。

## Residual Risk

- The check is structural (name/version/bin mapping + module existence/readability), not an integrity pin: a package satisfying the exact layout would be accepted and imported, and transitive imports beyond the two checked modules are not statically verified. This matches the accepted design (package CLI + pinned version) and any residue fails closed at launch with a Node module error rather than the reinstall message.
- The end-to-end `--check` rejection assertion (`tests/test_agent_sandbox.py:210-219`) only runs with `AGENT_SANDBOX_KERNEL_TESTS=1`; the ordinary suite covers validator-level rejection via `tests/test_agent_sandbox_launch.py:36-58`. If CI never sets the kernel opt-in, consider adding a non-gated fixture for the 3-line glue path. I reproduced the rejected-standalone scenario manually this round, so this is a CI-coverage note, not an unresolved defect.
- The pre-existing `srt --version` probe at `scripts/agent-sandbox:367` still executes whatever binary named `srt` is first on `PATH` before validation (my standalone shim was executed once by that probe, then rejected). This predates and is orthogonal to the accepted finding; the fix ensures the run cannot reach `setup_status=ok` afterwards.
- The `0.0.79` pin is duplicated between `scripts/agent-sandbox:19` and `scripts/agent-sandbox-launch.mjs:133,142`; a future bump must move them together, otherwise failure is loud and fail-closed rather than silent.
- Native Seatbelt/kernel behavior, Node 22.12 compatibility, and other macOS versions were not exercised here; those remain supplied evidence.
- No relevant tool failures occurred during this review; all commands used completed successfully.
