# Goal confirmation: agent-sandbox dangling symlinks

- Gate: goal confirmation; status: confirmed by user delegation.
- Work unit: agent-sandbox-dangling-symlinks.
- Base: main at d51765b (PR #50 already merged); clean worktree checked before branch creation.
- Branch: fix/agent-sandbox-dangling-symlinks. New draft PR required; do not reuse PR #50.
- Controller adjudicates. After confirmation, gpt-6-sol through runner subprocesses owns plan/implementation/fixes; independent parallel reviews use mimo/Codex and ds-flash/Claude. Plan reviews use planreview; code/aggregate/PR reviews use deepreview.

## Goal / motivation

An otherwise valid declared denied directory containing a dangling symlink must not stop isolation setup with an unlocated FileNotFoundError. Define and verify conservative handling without removing declared denials, widening reads/writes or falling back to an ordinary runner.

## Confirmed success signals

- A synthetic denied/old-python link with a missing target no longer causes the reproduced unexplained startup failure; the isolated invocation reaches effective kernel boundary verification and a controlled fixture runner.
- Preserve recursive denial of the declared directory and expansion to existing symlink targets. Missing targets are not a reason to grant access: prefer retaining the safely resolved missing target as a deny path; plan/review must establish its policy and verification semantics using actual macOS behavior.
- ENOENT alone is not evidence of sandbox denial. Effective Seatbelt checks and allowed/existing-denied probes remain mandatory. Unsupported or indeterminate resolution/verification fails closed with the declared entry, offending link and target/error context where available.
- Allowed fixture reads and writes still succeed; direct/alias/recursive forbidden reads and existing write restrictions remain enforced. No requirement to install an obsolete Python or edit a business directory.
- Preserve valid symlink handling, hardlink/special-file rejection and lifecycle/provider/result collection behavior.

## Direct code evidence / reproduction

- scripts/agent-sandbox:38-85 load_denies validates existing declared paths, walks directories, expands symlink targets and rejects hardlinked files. Line 78 calls entry.resolve(strict=True) without link/declared-entry diagnostic context.
- scripts/agent-sandbox:339 verify_and_exec checks effective Seatbelt policy then attempts real reads; missing-path handling must not bypass these checks.
- scripts/agent-sandbox:383 calls load_denies before runner or srt launch. Top-level exception formatting prints the raw exception only.
- Source/live agent-sandbox byte equality verified. Independent fixture: /private/tmp/dangling-deny-repro-vgicca3h/reproduction.json. Actual exception: FileNotFoundError for the missing-framework ancestor, omitting denied/old-python.
- tests/test_agent_sandbox.py covers valid aliases, hardlinks, FIFO targets and actual kernel boundaries, but not this dangling descendant case.

## Scope / non-goals

Expected source scope is load_denies and only the verification changes necessary for its safe missing-target semantics, focused regression/kernel fixtures, and concise documentation of the resulting contract. Gateflow/review artifacts are included. No sandbox redesign, new workflow, provider/config/key changes, compatibility/migration layer, old Python installation, business-file edits or original task execution. Do not read/run the retained caller task copies in /private/tmp/paradigm-mimo-review-vn24sy1t. No merge or live deployment is authorized by this goal; report the installed live entry's version/state at closeout so the caller can arrange deployment and revalidation.

## Risks / decision

Missing-path policy matching and verification must be demonstrated, not assumed. Concurrent unsandboxed path mutation remains subject to the existing documented boundary; no new promise of filesystem snapshot isolation. Loop/permission/other non-absence errors must not be silently treated as missing paths. These are necessary correctness conditions for this fix, not a general path-resolution redesign.

No blocking information request at this gate. Goal accepted: user explicitly confirmed goal/non-goals/scope/success signals and authorized automatic Gateflow progression. Missing-target handling is the minimum verifiable safe implementation, not a requirement to accept ENOENT as proof. Next gate: plan.
