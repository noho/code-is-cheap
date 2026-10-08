# Agent sandbox validation

## Scope

Branch `feat/agent-deny-list-sandbox`, base `6bc30cd`. macOS, Codex 0.161.0, Claude Code 2.1.294,
Anthropic sandbox-runtime 0.0.79. Only synthetic temporary fixtures and local mock model endpoints were used.
No portfolio project files, running workflows or live deployment files were modified.

## Observed checks

- `python3 -m unittest discover -s tests`: 84 tests, OK, 6 opt-in kernel/runtime tests skipped.
- `AGENT_SANDBOX_KERNEL_TESTS=1 SRT_TEST_BIN=/private/tmp/code-is-cheap-srt-test/node_modules/.bin/srt python3 -m unittest discover -s tests -p 'test_agent_sandbox*.py'`:
  17 tests, OK; kernel tests run outside the controller sandbox with managed escalation.
- Existing endpoint regression: 18 tests OK; preflight: 8 tests OK.
- `git diff --check`, Python compilation, zsh/bash syntax checks passed; skill-creator quick_validate passed.

| Check | Actual observation |
| --- | --- |
| Allowed input and output | Allowed text read; cwd output written under workspace-write; selected output file written outside cwd |
| Forbidden reads | Direct path, symlink file/directory, case-only APFS aliases, `..`, `/tmp` and `/System/Volumes/Data` aliases all returned PermissionError |
| Recursive search | `rg` stdout contained no forbidden marker; stderr reported Operation not permitted |
| Python/script access | Python file opens failed on every denied alias; subprocesses inherited the policy |
| Write preservation | read-only did not gain cwd writes; workspace-write protected `.git`; outside file and output-sink neighbor writes failed; Claude's original denyWrite defeated the cwd allow; conflicting output failed at setup |
| Escape attempts | Creating a hardlink to a forbidden file failed; a nested sandbox-exec with allow-default did not restore access |
| Fail closed | Unsupported original permission profile stopped before the runner/output file; bad/empty/missing/special-file deny entries rejected; direct internal verification with ordinary Unix mode denial did not start a runner |
| Native Codex | Explicit require_escalated request rejected by approval=never; ordinary cat/rg denied; forbidden view_image failed with EPERM; allowed view_image succeeded |
| Native Claude | Read of forbidden report/image denied; Bash alias/recursive access denied; allowed image and text succeeded |
| Model-facing payload | Codex made six requests and Claude five to local mocks; captured requests contained allowed canary/image, no forbidden text/image |
| Default behavior | Fake native binary tests observed no bypass flag/sandbox setting without opt-in, and the proper Full Access flags/settings with opt-in |
| Original Codex rules | Copied user .rules actually rejected a touch command with the original justification; the forbidden output did not exist |
| Fixed task | Missing/dual/stdin prompts rejected; prepared prompt snapshotted; attempted snapshot write returned PermissionError |

Raw synthetic native-tool evidence retained at `/private/tmp/code-is-cheap-agent-sandbox-evidence-v3/{codex,claude}-probe.json`
includes actual request bodies, structured output, stderr and exit codes. Reproduce via
`AGENT_SANDBOX_EVIDENCE_DIR=/absolute/temp/evidence` with the opt-in tests. This is diagnostic evidence, not installed configuration.
Codex tool inventory was exec_command/write_stdin/request_user_input/view_image; Claude inventory was Bash/Edit/Glob/Grep/Read/Write.
Both outer exits were 0; Codex had turn.completed, Claude had result success/is_error=false/num_turns=5.
Expected diagnostics: synthetic Codex model metadata fallback; under-development skip_host_skill_discovery warning;
Claude synthetic unrecognized_model warning. Permission failures are expected adversarial evidence, not failed task execution.

Additional synthetic kernel checks retained under `/private/tmp/code-is-cheap-agent-sandbox-evidence/`:
`literal-path-probe.json` proves filenames containing brackets are literal (denied file blocked, neighbor readable;
selected sink writable, neighbor unwritable). `app-launch-probe.json` uses a valid temporary background-only Mach-O app:
the unsandboxed control read its synthetic marker; LaunchServices inside the envelope failed and produced no copy.
No GUI or user application was launched. These checks do not assert coverage of future IPC channels.

## Limits

- The caller supplies existing literal forbidden paths and every known forbidden copy. Unlisted semantic copies remain readable.
- Existing hardlinks are rejected. Concurrent replacement/copying by another unsandboxed process is outside this boundary.
- Writes retain a conservative subset, not all additional writable roots. Per-run state and caller-selected output files are runner necessities.
- Custom permission profiles/project-layer Codex configs, Claude custom read/glob write/tool deny rules and managed policies are unsupported and fail explicitly.
- Required runtime configuration/credentials are readable dependencies; denying them stops setup. This feature does not isolate credentials from Agent tools.
- Isolation uses fresh state and a reduced tool/integration surface. No resume, native passthrough, staged inputs or dynamic prompts.
- Runtime upgrades and additional enabled channels require boundary tests before asserting coverage.
- A symlink inside a denied directory targeting a FIFO/special file is rejected before opening it, so setup cannot block on that input.
