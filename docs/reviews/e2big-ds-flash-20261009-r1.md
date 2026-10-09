RUNTIME/PROVIDER/MODEL: codex/ds-flash/deepseek-flash
CANARY=ds-flash-1340c966

# Code Review

## Scope

- Mode: current changes
- Branch: `fix/agent-sandbox-large-policy-launch`
- Base: `f818dde2d361dea5313aefb7d7383399f947e0c9`
- Frozen HEAD: `690ec69116f95b79bcb1d1d60c9044ac36eff6d1`
- Output file: `docs/reviews/e2big-ds-flash-20261009-r1.md`
- Included scope: the complete `base...HEAD` diff, all changed implementation/test/documentation files, the `agent-sandbox` startup path through `sub-agent-preflight`, the pinned `srt` 0.0.79 CLI/macOS policy/quote sources, and the supplied validation artifact.
- Excluded scope: business data, original business commands, portfolio-manager-v2, endpoint/auth/key material, user sessions, tmux/user workflows, other reviewer reports, live sync/deployment, network access, and source edits.
- Parallel review coverage: none. The task explicitly prohibited child Agent dispatch.
- Native kernel status: the opt-in macOS/Seatbelt tests were not rerun because they require leaving the controller sandbox. Their evidence remains supplied input, not an independent result in this report.

## Findings

### 1-未修复-低-`agent-sandbox --check` can report `setup_status=ok` for a runtime the launcher refuses before the runner starts

- **入口/函数**: `agent-sandbox --check` and `agent-sandbox-launch.mjs` package validation.
- **文件(行号)**: `scripts/agent-sandbox:358-395`; `scripts/agent-sandbox-launch.mjs:128-142`.
- **输入场景**: `srt` on `PATH` is a standalone or otherwise non-package executable that reports `0.0.79`, or an installed package has a different layout/missing `package.json`.
- **实际分支**: `agent-sandbox --check` runs the `srt --version` check at lines 367-369, checks that `node` and the adjacent launcher file merely exist at lines 361-366, and returns `setup_status=ok` at lines 387-395 without invoking the launcher's package/layout validation. The package check at `scripts/agent-sandbox-launch.mjs:135-140` is reached only when the real spawn is attempted.
- **预期行为**: A preflight that reports `setup_status=ok` should either validate the exact launcher/package contract that will be used or explicitly mark that contract as unvalidated. At minimum, the eventual error should be the intended actionable “Node package CLI required” message.
- **实际行为**: Preflight returns success, then the actual launch exits before the runner with a raw error such as `agent-sandbox-launch: ENOENT: no such file or directory, open '.../package.json'`.
- **直接证据**: A disposable `/private/tmp` fixture with a fake standalone `srt` produced `check_rc=0` / `setup_status=ok`; the same invocation without `--check` returned `launch_rc=1` and the launcher ENOENT error. This is direct code-path evidence, not an inference from a nearby symptom.
- **影响**: False-positive preflight; an operator may dispatch a job that cannot start. The failure is closed and no runner/provider work starts, so this is operational usability/observability risk rather than a sandbox-boundary breach.
- **建议改法和验证点**: Add a non-spawning `--validate` mode to `agent-sandbox-launch.mjs` (or a small shared validator) that performs the `realpathSync`/package-name/version/bin-path and required-module checks. Call it from `agent-sandbox --check` before returning `setup_status=ok`, and add tests for a standalone `srt`, a mismatched package root, and a missing `shell-quote.js`.
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 低

除了上述 operational gap，未发现实质性的 correctness、stability 或 security defect。

## Adversarial Pass

- **Compaction equivalence**: `compactDenyRules` only rewrites top-level `subpath`/`literal` conditions in the four deny-rule operation shapes emitted by pinned `srt`, groups by operation kind and exact parent, escapes regex metacharacters, distinguishes exact `literal` from descendant `subpath`, caps each emitted regex below the pinned 900-byte string bound, skips root/trailing-slash cases, and preserves unmatched filters and rule position. Static inspection and ad-hoc randomized decode/compaction checks found no widening or truncation path.
- **Quote decoder**: `decodeArgv` handles srt's canonical single-quote plus `'"'"'` encoding, rejects operators/noncanonical separators, and is re-encoded with the same installed `quote` before acceptance. Ad-hoc checks covered empty, newline, Unicode, metacharacter, backslash, and repeated-quote arguments.
- **Failure closure**: Launcher layout, package, profile-write, and profile-compile failures all occur before the runner is executed; no unsandboxed fallback exists. The adapter intentionally refuses unsupported shell-spawn layouts rather than passing them through.
- **Rule ordering and operations**: Neither rule order nor operation sets are merged; replacement occurs inside one deny rule and retains the original rule's message. Multiple filters within a rule are a union, so moving a union to the first sibling's position is semantically equivalent.
- **Original write boundaries**: The existing `write_boundary` logic is unchanged. The new state files are added only to write-deny coverage; the new adapter does not add user-visible writable roots. The supplied native validation claims profile writes/renames are denied.
- **Proxy, signals, exit status, cleanup**: The launcher imports the pinned CLI and leaves its proxy setup, control channel, signal handlers, child `exit`/`error` handling, and cleanup callbacks in place. The only changed child operation is the final shell-string spawn, which is converted to a direct spawn with the same child object and stdio/options.
- **Parameter/effectiveness chain**: `node`/launcher path -> realpath/package check -> `srt` argv -> expected inner command -> single shell-spawn interception -> `sandbox-exec -f profile` was traced. No value was silently defaulted or dropped on the intended path.
- **Protected policy files**: `seatbelt.sb` and `seatbelt.source.sb` are created in the fresh private state and named in the generated write-deny set. They are not read-denied; the sandboxed Agent can read policy metadata, but this does not alter the loaded policy and the same state already contains `srt.json`/`boundary.json` metadata. No content-isolation claim is made.

## Agent-Facing Review

- `README.md:154-162` and `README.zh.md:150-156` accurately state the Node-package-CLI requirement, adjacent adapter deployment, source/effective profile retention, `sandbox-exec -f` transport, fail-closed behavior, and remaining native compiler limits.
- `skills/sub-agents/SKILL.md:162-166` correctly distinguishes wrapper startup failure from provider execution, tells the controller to retain/report original errors, forbids deny-list truncation, verification skipping, and ordinary unsandboxed fallback, and points to the stderr-visible state/profile evidence.
- Permissions and deployment are consistent: `install.sh:55` calls `sync-agent-tools.sh`, and `sync-agent-tools.sh:14-16` installs both `agent-sandbox` and the adjacent launcher. The install test checks that the launcher bytes are deployed.
- Failure evidence is adequate for a normal run: `scripts/agent-sandbox:460` prints `state=...`, and `scripts/agent-sandbox-launch.mjs:154` prints `seatbelt_profile=...`, effective/source byte counts, and `file-backed`. The low finding above is the remaining preflight/real-launch mismatch.

## Verification

- `python3 -m unittest discover -s tests -p 'test_agent_sandbox*.py' -v`: 23 run, OK, 8 kernel tests skipped.
- `python3 -m unittest discover -s tests -p 'test_install_endpoints.py' -v`: 18 run, OK.
- `python3 -m unittest discover -s tests -p 'test_sub_agent_preflight.py' -v`: 8 run, OK.
- `python3 -m unittest discover -s tests`: 90 run, OK, 8 skipped.
- `node --check scripts/agent-sandbox-launch.mjs`: pass.
- `bash -n scripts/sync-agent-tools.sh`: pass.
- `git diff --check f818dde2d361dea5313aefb7d7383399f947e0c9...HEAD`: pass.
- Ad-hoc disposable checks for canonical quote decode and large regex-union membership: pass. The initial exploratory harness attempts had test-code parse mistakes; after correction they were not product failures and are not counted as evidence against the change.
- Native macOS policy/kernel tests: not independently rerun here; the supplied validation artifact reports 23 native/runtime tests passing plus 4108-item kernel verification. That claim is treated as input evidence, not independently reproduced.

## Read-File Coverage

- Fully read: `scripts/agent-sandbox-launch.mjs`, `scripts/sync-agent-tools.sh`, `tests/test_agent_sandbox_launch.py`, and `docs/reviews/agent-sandbox-e2big-validation-20261009.md`.
- Fully read through line-chunked reads: `scripts/agent-sandbox` (lines 1-474) and `tests/test_agent_sandbox.py` (lines 1-331).
- Changed/relevant sections read: `README.md:139-201`, `README.zh.md:135-186`, `skills/sub-agents/SKILL.md:140-166`, `tests/test_install_endpoints.py:900-972`, and the complete `base...HEAD` diff.
- Dependency inspection: pinned `dist/cli.js` startup/spawn path (including lines 394-480), pinned macOS policy generation and write-rule/move-blocking logic (including lines 397-760 and 760-1143), full `dist/utils/shell-quote.js`, and full `package.json`.
- Not read: unrelated repository production modules, unrelated tests, other review artifacts, business data, credentials/endpoint files, user sessions, and live deployment state.

## Open Questions

- 无。

## Residual Risk

- The native macOS/Seatbelt behavior was not independently rerun because it requires escaping the controller sandbox; kernel-specific case-normalization, firmlink, signal, and policy-compiler behavior therefore remains supplied evidence rather than a locally reproduced result.
- Node 22.12 compatibility was not independently exercised in this run; the focused tests ran on Node 25.9.0. The adapter uses Node APIs available since before 22.12, but exact-version execution remains untested.
- Native compiler limits for large numbers of unrelated parents, very long names, or insufficient sibling grouping remain. The implementation and documentation explicitly do not claim universal removal of those limits.
- Signal/exit cleanup was inspected and remains delegated to pinned `srt`, but no independent SIGINT/SIGTERM/orphan-process stress test was run.
- Policy metadata is write-denied but not read-denied. This is consistent with pre-existing state metadata and does not change policy enforcement, but callers that treat deny-list path names as sensitive should account for it.
- No CI/check information or PR metadata was consulted because this review was restricted to the frozen local revision and no network use.

