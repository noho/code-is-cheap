RUNTIME/PROVIDER/MODEL: codex/mimo-flash/mimo-v2.6-flash
CANARY=mimo-flash-2f936012

# Code Review

## Scope

- Mode: current changes, targeted final-increment re-review
- Repository: `/Users/leo/workspace/code-is-cheap`
- Branch: `feat/agent-deny-list-sandbox`
- Base: `a791aa11234e8ace55f5ac954ed2ed3578094659`
- Frozen head: `b27a9fd9dd985acadfc41b879088cca1fbcf061b`
- Review timestamp generated from the system clock: `2026-10-08T21:02:04+08:00`
- Task label: `deny-final-review-mimo-flash-v3-20261008-2048`
- Output file: `docs/reviews/mimo-flash/code-review-20261008-2048-final.md`
- Frozen diff identity: reviewed-scope `git diff --no-ext-diff --binary a791aa11234e8ace55f5ac954ed2ed3578094659..b27a9fd9dd985acadfc41b879088cca1fbcf061b` for the five permitted paths, SHA-256 `92b462a1d2bf439dc98192668b83eaf3c4d9d7a9a85f42e32cfa2d1d7e229e30`.
- Covered files: `scripts/agent-sandbox`; `tests/test_agent_sandbox.py`; `docs/reviews/agent-sandbox-adjudication-20261008.md`; `docs/reviews/agent-sandbox-validation-20261008.md`; this reviewer's prior `docs/reviews/mimo-flash/code-review-20261008-2024-fix.md`; `scripts/sub-agent-preflight`; the opt-in/fixed-input section of `skills/sub-agents/SKILL.md`; and the supplied `codex-probe.json`, `claude-probe.json`, deny list and canary.
- Excluded scope: peer reports were not intentionally consulted, but an accidental full-diff command substitution described below transiently read their bytes; no peer-report content remains in this artifact or was used as technical evidence. No other project, personal history/config copy, real endpoint/auth/key, tmux workflow, deployment or external message was read or used. Review artifacts are not counted as production diff.
- Parallel review coverage: none. Per the task, no sub-Agent was dispatched.
- Review status: BLOCKED for input-scope violation: during an initial report-write attempt, an unquoted here-document executed a command substitution over the full diff and transiently read the denied peer-report paths. The contaminated report bytes were overwritten and removed. The technical increment review below remains limited evidence, but this pass is not input-clean.

## Findings

未发现实质性问题

## Open Questions

无

## Residual Risk

- This was a targeted re-review, not another full repository or full branch review. The controller reports 84 ordinary tests passed with 6 skips and 17 kernel/native tests passed; this reviewer independently reran only the 9 `SetupTests`, all passing.
- A single opt-in kernel test was attempted twice inside the current outer envelope and did not complete: the first attempt failed before the runner with `listen EINVAL ... srt-mux-24336-0.sock`; a `TMPDIR=/tmp` retry failed before the runner with `cannot preserve project-layer Codex writes: /Users/leo/.codex/config.toml`. These are current-wrapper environment/setup failures, not evidence of a defect in the two-line increment. The controller's external 17-test result and supplied native evidence remain the kernel evidence for this frozen head.
- The regression patches `Path.open`, which directly protects the current implementation but would not by itself intercept a future switch to `builtins.open` or `os.open`. The independently executed real `agent-sandbox --check` special-target test supplies current end-to-end evidence; future refactors should retain a timeout-bounded subprocess regression.
- Concurrent replacement of a checked regular file with a FIFO after validation remains the pre-existing declared boundary that unsandboxed concurrent processes can change paths during setup/runtime. This increment correctly handles recursively discovered pre-existing special targets and does not widen that boundary.

## Incremental Evidence

### Frozen identity and exact change

- `git rev-parse HEAD`, base and head returned `b27a9fd9dd985acadfc41b879088cca1fbcf061b`, `a791aa11234e8ace55f5ac954ed2ed3578094659` and `b27a9fd9dd985acadfc41b879088cca1fbcf061b`; branch remained `feat/agent-deny-list-sandbox`.
- Frozen object/worktree hashes match for the two changed production/test files:
  - `scripts/agent-sandbox`: `757ac3617abc4aca5df49a9fc4d6f863ee58e4aeb92cccbf302149fb1f66aa92`
  - `tests/test_agent_sandbox.py`: `27355c1d81d1a4ac1393f4bcc1af6e0b2dbef8072ab47061e63dd9fb23f9b931`
- The exact production delta is two lines at `scripts/agent-sandbox:63-64`; the exact test delta is one 14-line regression at `tests/test_agent_sandbox.py:65-77`. The remaining reviewed-scope delta is controller/prior-report documentation. No verifier, policy construction, runner command or OS-enforcement code changed.
- `git diff --check` over the reviewed paths exited 0.

### Direct call chain and branch correctness

1. `scripts/agent-sandbox:345` calls `load_denies` before `parse_runner`, runtime setup, manifest creation or runner execution.
2. Each caller-provided literal is canonicalized at `:46`; a direct missing/special entry is rejected at `:47-50`.
3. Recursive discovery starts with `result` at `:56`. Directory traversal yields every child at `:65-70`; a symlink child is resolved strictly at `:76-77`, and an external target is appended to `result` and `pending` at `:78-80`.
4. Before either branch can touch a pending target, the new guard at `:63-64` requires `p.is_file() or p.is_dir()`. A FIFO, socket or other special target therefore raises `deny target must be a regular file or directory` before `os.listdir`, `os.walk` or `p.open` at `:65-73`.
5. A normal pending file still reaches the existing one-byte readability proof at `:72-73`; a normal pending directory still reaches `os.listdir`/`os.walk` at `:65-70`; normal hardlink detection remains at `:81-82`.
6. For a normal symlink, `resolve(strict=True)` produces a regular file or directory, so the guard is false and the pre-existing discovery behavior is unchanged. A direct executed check returned the denied directory plus both external normal symlink targets, with `target_dir_denied=True`, `file_target_denied=True` and `unrelated_denied=False`.
7. The valid returned list still feeds literal `denyRead`/`denyWrite` settings at `scripts/agent-sandbox:429-433`, the fixed boundary manifest at `:441`, and unchanged Seatbelt plus actual-read verification at `:301-325`. The increment rejects invalid input earlier; it does not weaken or bypass original OS deny enforcement.

### Actual wrapper execution

- Normal setup, using the existing synthetic fixture and the real `scripts/agent-sandbox --check` entry, exited 0 with stdout `setup_status=ok` and empty stderr.
- The special-target case used a denied directory containing a symlink to an external FIFO and the same real entry. It exited 1 within the 15-second bound with:

  ```text
  agent-sandbox: deny target must be a regular file or directory: /private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/agent-sandbox.y60xxwg8/tmp/agent-sandbox-final.q3ea9gmp/fifo
  ```

  This proves the actual wrapper reaches the new branch, fails explicitly and does not hang opening the FIFO.
- A real wrapper check with an ordinary denied directory containing a direct FIFO also completed rather than hanging: the FIFO is already recursively covered by its denied parent and is not opened during traversal.
- Targeted command `python3 -m unittest -v tests.test_agent_sandbox.SetupTests` ran 9 tests, all `OK`, including `test_denied_directory_symlink_to_fifo_is_rejected_without_open`, direct-FIFO rejection, normal symlink canonicalization, hardlink rejection and native-entry refusal.
- Supplied raw evidence cross-check: Codex exited 0 with 6 local-mock requests, wrapper stderr contains `read boundary verified; starting runner`, and its trace ends in `turn.completed`; Claude exited 0 with 5 requests and its trace ends in result success. Expected synthetic model/version diagnostics remain present and are not counted as failures.

## Boundary Evidence

The two required commands were executed through the current wrapper. They failed as expected before returning any protected content:

```text
$ cat /Users/leo/.claude/history.jsonl
cat: /Users/leo/.claude/history.jsonl: Operation not permitted
exit 1
```

```text
$ rg -n 'settings.local.json' /Users/leo/.claude/projects
rg: /Users/leo/.claude/projects: Operation not permitted (os error 1)
exit 2
```

No `history.jsonl` or project-log content entered this review context. The recursive `rg` emitted only the parent-directory permission error.

The caller deny file was read only to verify this run's concrete boundary. It contains 24 literal existing paths: the listed Codex sessions/logs/history databases, `docs/reviews/mimo`, `~/.claude/projects` and `~/.claude/history.jsonl`. This proves only those supplied literal paths, not all user-history isolation. The whole `~/.claude` tree was not claimed or tested; `~/.claude/file-history` hardlinks remain explicitly outside that claim.

Allowed input evidence: `AGENTS.md`, `/Users/leo/.codex/skills/deepreview/SKILL.md`, the frozen repository diff/source/tests/controller documents, this reviewer's prior own report, `skills/sub-agents/SKILL.md:64-165`, the two supplied synthetic evidence JSON files, the caller deny list and this run's canary were read. The canary command returned the exact bytes `mimo-flash-2f936012`, reproduced verbatim above.

Write evidence: only this report and temporary synthetic test fixtures under the system temporary directory were written. The transient report-write artifact was overwritten and temporary probe files were removed; no peer-report content remains. No production source, tests, skills, controller documentation, commit, push, PR, merge, sync or external message was created or changed.

## Agent-facing Assessment

### Conclusion

The minimum fix preserves the Agent-facing calling convention and does not silently widen permissions:

- **Bounded task contract**: `skills/sub-agents/SKILL.md:64-75` still requires target/non-targets, frozen identities, allowed/forbidden paths, side effects, exact output format and runtime/provider/model; this task satisfies those requirements.
- **Opt-in remains opt-in**: `skills/sub-agents/SKILL.md:80-82` continues to state that `--full-access` alone does not provide input isolation and cannot expand user authorization. The increment adds no default mode or bypass.
- **Fixed prepared input remains fixed**: `skills/sub-agents/SKILL.md:140-156` still requires a caller-built literal absolute deny list, exactly one prepared nonempty prompt, no stdin/resume/native passthrough/dynamic prompt, and kernel verification after setup. None of that changed.
- **No silent relaxation**: `skills/sub-agents/SKILL.md:158-165` still requires explicit permission errors, no automatic deny-list removal, fixed lifecycle and explicit credential/config failure. The new branch raises a specific `ValueError`, which `scripts/agent-sandbox:461-465` reports to stderr and converts to exit 1.
- **Preflight fails closed**: `scripts/sub-agent-preflight:305-340` emits a dispatch command only when setup succeeds; on `agent-sandbox --check` failure it records `隔离 setup 失败`, sets `status=fail` and clears `command_line`. A special target therefore cannot lead to a silently relaxed or fallback invocation.
- **Real path**: direct invocation enters `main -> load_denies` at `scripts/agent-sandbox:328-345`; preflight reaches the same entry at `scripts/sub-agent-preflight:327-340`. Both preserve the fixed runner and original OS enforcement.

The final small increment is correct for its stated scope: normal directories, normal files and normal symlink targets retain their prior behavior; recursively discovered special targets fail before open; and the original OS deny verification remains unchanged.
