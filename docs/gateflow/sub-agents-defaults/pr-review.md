# Published PR review and fix checkpoint

Gate: PR review. Work unit sub-agents-defaults. PR #50 https://github.com/noho/code-is-cheap/pull/50, draft. Existing branch pushed; no ready-for-review or merge transition.

## Frozen published evidence

- Head bff4b3fcd499adf8175c65a83da8910bb699fc6f; base ebd547fab97a5af3f3bcffae7ebb187b71563dcf; both base/head repositories noho/code-is-cheap.
- Immutable compare URL https://api.github.com/repos/noho/code-is-cheap/compare/ebd547fab97a5af3f3bcffae7ebb187b71563dcf...bff4b3fcd499adf8175c65a83da8910bb699fc6f, Accept application/vnd.github.v3.diff.
- Controller snapshot /private/tmp/defaults-pr-5vjhj2kv/controller-pr.diff, SHA256 88a653565284a4bdc84990ff771ccfc2239b117363c7fef12d4079e5973b6bb0. Facts saved alongside; exact local object and unchanged source worktree used for deep reads. No GitHub CI checks reported.
- Review routes launched independently in parallel: MiMo/Codex managed session 17651; DS Flash/Claude managed session 52456. Private prompt/log metadata /private/tmp/defaults-pr-5vjhj2kv/metadata.json. No model identity self-report requested.

## Completed routes and controller findings

DS process actually exited outer0/runtime0/native success, wall_clock_seconds 721.200442, errors0/anomalies2/warnings1. Report docs/reviews/pr-50-review-20261010-155516.md. Original native token/cost metrics remain in its JSONL; not estimated by controller.

- DS1 accepted at initial review: five opt-in kernel tests abort before runner because raw-output stub fixtures omit adapter yet request collected mode. Controller reproduces 22-test agent_sandbox module with five failures; DS combined agent_sandbox plus launch modules totals28, base combined25 pass. Correct fix: explicit --detail for raw stub invocations; preserve every kernel assertion. Real collected-mode CLI coverage remains in test_agent_sandbox_runtimes, not replaced with stubs.
- DS2 accepted at initial review: explicit dash log destinations silently default to files. Default stdout belongs to the JSON report, so reject dash with clear requires --detail before runtime launch; raw detail behavior retained.
- Controller1 accepted at initial review: persistent runs omit native session ID from compact stdout although raw events include it. Both runtime entries reproduce outer0/ID present only in logs. Return available native identity without child self-report or synthetic inference; missing/conflicting identity unavailable. Existing --persist/resume argv/policy remains.
- Prepared patch remains outside repo source while MiMo reviews frozen head. Its three new deterministic regression tests already pass on private patched runner files; no final fix claim until source applied and full gates complete.

## Ordinary tool failures / evidence

DS GitHub TLS failure was recovered with successful exact-OID facts/compare retrieval; initial /var temporary output denial recovered by using actual TMPDIR. Port binding blocked inside runtime sandbox was re-run outside; fixture containing a forbidden artifact correctly failed and was corrected. Findings and all required source/version evidence obtained. These failures do not invalidate the completed independent review.

## MiMo route and final fix checkpoint

MiMo process actually exited outer0/runtime0/turn.completed, wall_clock_seconds 1683.287715, errors0/anomalies2. Report docs/reviews/pr-50-review-20261010-155515.md. The gh checks exit1 means no checks reported (required CI state obtained); startup MCP403 is outside the required git/gh/local review path. Full immutable diff and exact source facts were acquired. No necessary evidence gap remains and no re-dispatch solely for tool errors.

- MiMo1 accepted: canary input setup only checked after expensive runtime execution. Shared adapter internal validation mode now checks readable nonempty regular inputs and a nonempty whitespace-free expected token before runtime/log opening. Both wrappers stop with setup exit2 when invalid; token never printed. Existing post-run proof comparison remains.
- MiMo2 accepted: post-run hard-link/log aliases could satisfy optional artifact contract. Reject st_nlink !=1 and samefile against retained logs; preserve ordinary files and post-run proof checks. No fresh-directory protocol or file-content judgment introduced. Document mechanical new-path check and inode-provenance limit. Caller requiring hard links may omit optional --artifact and inspect task output.
- DS1 fixed: three raw-stub invocation sites select --detail; kernel assertions unchanged. Actual native collected-mode coverage remains, including adapter. DS2 fixed: explicit dash destinations require --detail, including Codex last-message; detail's prior raw behavior retained.
- Controller1 fixed: collect original Codex thread.started/thread_id and Claude init/result session_id; expose a single available session_id without child self-report, estimate or persistence claim. Missing/invalid/conflicting metadata yields null (conflict diagnostic only); existing persist/resume argv unaffected.

Final source hashes: adapter a160bf00fa0b17721d171c3e1e8180564805679b9e9a821f15a6e51432933764; Codex runner 45baef1f77019a09c2c7d92567de8e9447eea5f8708cea838f2cf89daf954f01; Claude runner 4cdd1700708b0cdeeed82af13fd5215df6c40888d7c83f711503b95a6338dda9.

Validation after applying all five fixes:
- Focused results/preflight: 51 pass (25.888s), including capture proving no runtime invocation for invalid canary/dash setup; runtime-created output/stderr/arbitrary hard links reject; persist/resume ID and missing/conflict cases; original usage/Unicode/tool-error/explicit-proof regressions remain.
- Full unittest with AGENT_SANDBOX_KERNEL_TESTS=1, SRT_TEST_BIN=/Users/leo/.local/bin/srt and private evidence output: 140 pass, zero skips (60.178s). Real Seatbelt aliases/recursive read/dynamic hardlinks/write protections/4108-entry policy and Codex/Claude native CLI collection tests executed. Synthetic local endpoints/keys only, no new provider/model request.
- Native evidence /private/tmp/defaults-pr-fixed-native-20261010/{codex,claude}-probe.json. Six skill validators, shell/Python syntax and diff check pass.

All five fixes applied with regression evidence; independent focused published re-review remains next. Gate remains in progress; no accepted PR-review commit/final push/pass yet.

No live sync, config/key changes, other-project operations or merge. Risks: runtime future schema/visibility/interruption tracked in final closeout by maintainer; task truth/execution/artifact semantics owned by caller. Kernel gap is accepted blocking fix, not a deferred risk. No unclassified risk or scope question.
