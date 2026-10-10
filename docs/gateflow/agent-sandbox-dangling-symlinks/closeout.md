# Final closeout: agent-sandbox dangling symlinks

- Gate: final closeout; status: PASS / work unit completed.
- Artifact: docs/gateflow/agent-sandbox-dangling-symlinks/closeout.md.
- Draft PR: https://github.com/noho/code-is-cheap/pull/51 (new PR, independent of #50).
- Branch: fix/agent-sandbox-dangling-symlinks; base main d51765b.
- Checkpoints: accepted plan 44d652ac8459ae4fa74c977b931fbe905bc6da57; accepted S1 a6124c1e52280c94f8221cd0c030492b2954398f; accepted deepreview 708ed47; accepted PR review 89cc7aba8b1d221220cc9a2dbf13368d410ab23f.
- Push after accepted PR review: actual exit=0; GitHub head matches 89cc7aba8b1d221220cc9a2dbf13368d410ab23f; PR OPEN/draft=true. Final closeout metadata is an additional docs-only record, not a new product revision.

## What changed

Scanning a denied directory containing a dangling symlink now retains a safely canonicalized missing target plus its nearest existing non-root directory ancestor in both read/write denials. Valid strict symlink resolution is unchanged; only exact ENOENT uses stdlib ALLOW_MISSING. Every expansion/unsupported error has declared/link/raw target/actual entry context; ancestors enter the existing expansion graph, and conflicts fail closed rather than deleting denials or granting access.

Before the fixed runner starts, every existing boundary must pass an effective Seatbelt query and actual refusal. Registered missing ENOENT is tolerated only after its exact ancestor has been proved denied; missing/query-only results are never proof. Allowed actual reads/writes remain required. Original write restrictions, lifecycle/result collection and provider routing are unchanged. No new CLI option or migration layer.

## Verified evidence

- Actual macOS Seatbelt/srt suite: 52/52 passed, zero skips, nine kernel cases; original 4108-entry large policy and hash assertions retained.
- Direct/alias/recursive reads, valid external targets and original write restrictions denied; allowed fixture input/output/heredoc succeeded.
- Independent materialization controls: allow-default missing query/ENOENT becomes readable after creation; ancestor-deny policy continues to refuse created targets with actual PermissionError.
- Focused launcher 5 passed / one opt-in skip; preflight 13/13 passed. Independent DS code and aggregate kernel reruns 52/52; aggregate base/head 14-case differential probe; MiMo PR exact-head 30 focused tests exit=0 (native tool output independently checked by controller).
- git diff --check passed. Initial kernel fixture failures and ordinary recovered tool errors retained, not treated as whole-Agent failure or passing test evidence.
- Plan, S1 code, aggregate and PR gates received independent MiMo/Codex + DS Flash/Claude review; controller adjudicated every finding. Prior accepted plan findings 已修复 and independently re-reviewed; subsequent gates found no material defect, corrective fix/re-review no-op.
- Thirteen actual managed runner calls retain native wall-clock/usage/metrics in review-statistics.json and raw logs in /private/tmp/dangling-gateflow-t4xhxmkt/. No stream-summing/estimation.
- PR snapshot: base d51765b...head 2328453, exact compare 29 files / 306384 bytes, SHA256 15a04db5d5a9f0d7ca3b6d84f5a74ee22f33409aeafa8fcfaaf84c0c99f5c4d5; both reviewers and controller rechecked OIDs before acceptance. Later changes only record reviewed evidence.
- GitHub has no CI checks; no CI pass is claimed. Detailed commands, profiles/hashes/raw outputs, reviewer artifacts and controller decisions are linked from implementation.md, code-review.md, aggregate-deepreview.md, pr-review.md and evidence/.

## Docs / compatibility / remaining limits

README English/Chinese and sub-agents advanced reference describe dangling handling, conservative ancestor/cascade breadth, located failure, capability requirements and actual proof. Agent-facing instructions retain caller-owned deny-list/known-copy responsibility.

| Residual / limit | Classification | Owner / destination |
| --- | --- | --- |
| Ancestor/cascade can deny siblings, expand scan or conflict with required tools/inputs; arbitrary business-directory startup is not promised | fixed in current slice as explicit contract | Caller applies deny-list and checks located conflicts; actual business ancestry belongs to caller revalidation |
| ALLOW_MISSING needed only for confirmed missing branch; unsupported capability fails clearly; new missing tests need that capability | assigned to later work unit for other stacks | Maintainer environment validation; verified stack macOS 26.6.2 arm64, Python 3.11.15, srt 0.0.79. No old Python installation or fallback |
| Existing /tmp versus /private/tmp spelling sensitivity in original profile-hardlink fixture | assigned to later work unit | Maintainer harness/platform analysis; failures retained, original assertions pass under documented /tmp spelling; not attributed to this fix |
| Unknown copies, unsandboxed external replacement and snapshot/identity guarantees | assigned to later work unit | Caller/maintainer, separately confirmed goal; existing exclusions unchanged |
| Optional diagnostic origin naming / extra metadata root test / CI | assigned to later work unit | Maintainer diagnostics/hardening/CI; no current reachable-path blocking defect |
| Merge, live deployment and original caller revalidation/restoration | requiring explicit user decision | User/controller/caller; no merge/sync/task launch authorized here |

No unclassified residual, blocking open question or accepted unfixed finding.

## Live entry and next entry point

At final closeout, installed `/Users/leo/.local/bin/agent-sandbox` remains the pre-fix version SHA256 `10bc6c27ee8686b200c60ab07789a089189c3632f6a40e3b2f38726ce7320f31`; source SHA256 is `18d54243b1302aa8ebb4097821c47c44e38776f241185047f771e5c30f1b3eb5`. The live entry is **not updated**. No real provider task or caller job was launched. No business repository/retained caller task was read, modified, cleared or interrupted.

After user merge and separately authorized live synchronization, caller revalidates using the unchanged standard `agent-sandbox --cwd ... --deny-list ... -- codex-agent-run|claude-agent-run ...` entry. The caller alone owns restoration of its original task. This work unit does not claim the original task has resumed.

Issue link/comment: no issue number was supplied, no external issue created or commented; not applicable. Next entry point: user manual merge decision, then authorized deployment/caller revalidation.
