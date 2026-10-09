RUNTIME/PROVIDER/MODEL: codex/ds-flash/gpt-5
CANARY=ds-flash-024de331

# Code Review

## Scope

- Mode: focused current-changes closure review. This is not a repeat of the prior full E2BIG review.
- Repository: `/Users/leo/workspace/code-is-cheap`
- Branch: `fix/agent-sandbox-large-policy-launch`
- Frozen HEAD: `ac5b244637e926b8658f5b336e4247b106fd96b8`
- Selected base: `6672741e6a58939aba3a65c57c03843d2c92aa10`
- Commit: `fix: validate runtime before execution and fingerprint loaded policies`
- Identity check: the base is an ancestor of the frozen HEAD. `git diff --name-status 6672741...ac5b244` reports exactly 8 changed files and `git diff --stat` reports 106 insertions and 24 deletions.
- Included scope: `README.md`, `README.zh.md`, `docs/reviews/agent-sandbox-e2big-validation-20261009.md`, `scripts/agent-sandbox`, `scripts/agent-sandbox-launch.mjs`, `skills/sub-agents/SKILL.md`, `tests/test_agent_sandbox.py`, and `tests/test_agent_sandbox_launch.py`.
- Additional context read: only the call paths surrounding the changed code in `scripts/agent-sandbox`, the adapter, and the changed tests/docs.
- Excluded scope: unchanged dependency internals, the prior full E2BIG review, other reviewers' reports, business data, dispatch commands, endpoints, credentials, environment variables, sessions, tmux, workflows, native/kernel test execution, and live sync.
- Parallel review coverage: none. Child Agents were explicitly prohibited for this run.
- Review time: `2026-10-09T02:18:32Z`.
- Write scope: this report is the only repository artifact created. No source files were edited.

## Findings

未发现实质性问题。

The two accepted findings are closed by the new diff for the bounded claims made by this task. The evidence and the remaining limits are recorded below so the provenance fix is not overstated as prevention or immutability.

## Accepted Finding Closure

### 1. Unsupported standalone srt was executed by `--version` before structural validation

**Closure status: closed.**

The preflight order is now:

1. `scripts/agent-sandbox:358-360` resolves `srt` from `PATH` but does not execute it there.
2. `scripts/agent-sandbox:367-369` invokes the adjacent adapter in non-spawning validation mode first.
3. `scripts/agent-sandbox-launch.mjs:152-155` takes the validation-only branch and calls `validateRuntime`; it does not import or execute the candidate CLI.
4. `scripts/agent-sandbox-launch.mjs:132-147` validates the real CLI path, package name/version/bin layout, required module types, and readability using only filesystem APIs.
5. Only after that succeeds does `scripts/agent-sandbox:370-372` execute `srt --version` and compare the version.

The moved regression at `tests/test_agent_sandbox.py:113-129` is in ordinary `SetupTests`, not the kernel-gated suite. Its candidate standalone `srt` would create a marker if executed. It asserts a nonzero result, no `setup_status=ok`, the reinstall error text, and that the marker does not exist. This directly proves the changed ordering for that fixture.

This closes the accepted finding for a deterministic unsupported standalone layout. It is not a code-signing or package-authenticity guarantee: a lookalike package with the checked layout could still pass structural validation. Broad supply-chain hardening was explicitly outside this task.

### 2. Retained policy files could be changed through hard-link aliases

**Closure status: closed as minimal evidence provenance, not as write prevention or inode immutability.**

The adapter now performs this sequence in `scripts/agent-sandbox-launch.mjs:115-129`:

- Take the exact original policy string supplied in srt's canonical shell command.
- Compute the effective policy string with `compactDenyRules`.
- Write `seatbelt.source.sb` when compaction changes the source, write `seatbelt.sb`, and chmod the effective file to `0400`.
- Compute SHA-256 over each exact string using the same UTF-8 representation used by `writeFileSync`.
- Return both hashes to the spawn interceptor.

`scripts/agent-sandbox-launch.mjs:172-175` calls `fileBackedArgv`, logs both digests to the adapter's stderr, sets `launched = true`, and only then calls the original spawn. The digest fields also carry sizes, the effective profile path, and the literal `file-backed` marker.

The precise hash trust boundary is:

1. Trust starts at a parent process that owns and captures the envelope's stderr through a pipe or equivalent controlled channel. The parent must retain the pre-spawn adapter record outside Agent-writable storage.
2. The recorded digest covers the exact source and effective strings that the adapter wrote before spawning srt. For the normal compaction case, the effective digest covers the bytes passed to `sandbox-exec -f` through the file path, not bytes reconstructed later from an Agent-authored report.
3. After the run, the trusted parent compares the retained file bytes with the recorded digests. A mismatch proves that at least one retained file no longer equals the pre-spawn bytes. A final-state match proves only that the bytes compared at that time equal the recorded values; it does not prove that no transient write occurred or that the file was never altered and restored.
4. The hash record does not prevent a hard-link alias from changing the retained file, does not make the inode immutable, does not authenticate the Node runtime or pinned srt package, and does not remove same-UID or pre-existing trusted-package execution races between hashing, package loading, and kernel policy loading.
5. The record is evidence provenance, not an isolation control. A caller must not audit from an Agent-writable log, an unverified retained file, or a digest echoed by the Agent.

The native regression supplied with the change, `tests/test_agent_sandbox.py:229-255`, mutates both retained files through cwd hard-link aliases after the child starts, verifies both recorded digests no longer match the retained bytes, and verifies that the already-loaded read denial still rejects `direct`. The large-list regression at `tests/test_agent_sandbox.py:267-292` checks that pre-spawn hashes equal the unmodified retained files. I did not run either native test.

## Agent-Facing Wording

The changed wording now matches the trust boundary:

- `README.md:160-164` says hard-link aliases can alter retained files after loading, explicitly says this does not change the loaded kernel policy, and says the caller must collect the stderr stream through a trusted parent pipe and compare retained files. It states that Agent-writable logs or retained files alone do not prove integrity.
- `README.zh.md:155-157` carries the same three qualifications in Chinese.
- `skills/sub-agents/SKILL.md:164-166` directs the controller to capture pre-spawn `profile_sha256` and `source_sha256` through a trusted parent pipe and compare before using retained policy as evidence.
- `docs/reviews/agent-sandbox-e2big-validation-20261009.md:124-133` records the hard-link evidence limitation, calls the remedy explicit provenance, and does not claim inode-level immutability.

The wording does not call the files immutable or claim that hashing prevents alias writes. It also does not require removal of the existing trusted-package execution path.

## Verification

### Controller-supplied evidence, not independently executed here

- Ordinary suite: 93 tests, OK, 9 explicit opt-in skips, 35.883 seconds.
- Native Seatbelt plus actual Codex/Claude local-mock suite: 26 tests, all passed, 15.844 seconds.
- Native synthetic alias probe: link, chmod, and write through aliases succeeded for both retained files; the loaded kernel policy continued to deny the original read boundary.

These claims are recorded as supplied evidence only.

### My own focused ordinary tests

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_agent_sandbox.SetupTests.test_preflight_rejects_standalone_srt_without_executing_it`: 1 test run, OK, 0.106 seconds.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_agent_sandbox_launch.LaunchTests.test_runtime_validation_is_nonspawning_and_rejects_incomplete_installations test_agent_sandbox_launch.LaunchTests.test_large_profile_is_byte_preserved_and_no_long_spawn_argument_remains`: 2 tests run, OK, 0.406 seconds.
- `git diff --check 6672741...ac5b244`: no output; no whitespace errors found.

No native/kernel test, permission expansion, network call, or live synchronization was performed.

## Tool Failures And Recovery

- Initial large-context `git diff` commands were truncated by tool output limits. The impact was limited to presentation, not evidence: I recovered by reading each changed file with smaller unified contexts and then reading the relevant line-numbered call paths and tests directly. All 8 changed files were visible in the recovered reads.
- No source or test command failed. No blocked input or frozen-identity mismatch was found.

## Open Questions

无。

## Residual Risk

- This review did not independently execute native Seatbelt tests. The native alias behavior and 26-test result remain controller-supplied evidence.
- Hash comparison is a final-state tamper check. It does not prevent alias writes and cannot detect an overwrite followed by restoration to the exact recorded bytes if only the final hashes are compared.
- The adapter's stderr is a shared descendant stream, not an authenticated framing protocol. The documented trusted-parent rule requires the caller to retain the adapter's pre-spawn record and not let later child-emitted text replace or shadow it. No in-repository caller consumer was in scope, and no exploit of that consumer protocol was demonstrated.
- Structural validation can reject unsupported layouts but cannot prove package authenticity. The remaining exposure from a malicious or concurrently replaced trusted package is outside this closure task and the explicit non-goals.
- Unchanged modules, dependency internals, live deployment state, and other reviewers' artifacts were not reviewed.

End-of-review frozen identity: after this report was written, `git rev-parse HEAD` returned `ac5b244637e926b8658f5b336e4247b106fd96b8`. The reviewed base remains `6672741e6a58939aba3a65c57c03843d2c92aa10`; no frozen-identity mismatch occurred.
