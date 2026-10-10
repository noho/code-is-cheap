# S1 code fix 01: agent-sandbox-workspace-routing

- Gate: S1 code review → fix; root owns adjudication and subsequent gates.
- Branch/worktree: `fix/agent-sandbox-workspace-routing`, `/private/tmp/code-is-cheap-workspace-routing`.
- Scope authority: confirmed `goal.md`, accepted `plan.md`, root `code-adjudication.md`; `kernel-validation-initial.md` read solely as K1 failure definition, never successful proof.
- Artifact: `docs/gateflow/agent-sandbox-workspace-routing/code-fix-01.md`.
- Dispatch changes: one assertion in `tests/test_agent_sandbox.py`, plus this artifact. Existing source/docs changes and root lifecycle/state/statistics/evidence/goal/plan/adjudication/peer reports are unchanged by this dispatch. No peer report was read.

## Accepted finding and fix

| Finding | Change/evidence | Fix status |
| --- | --- | --- |
| K1: real runner `--detail --output` writes native stdout to the selected fresh sink, leaving captured stdout empty | Read `(p/'sinks'/('ca-'+name)).read_text()` and compare exactly with `'NATIVE_CA_PATH='+str(expected)+'\n'` inside each default/SSL subtest, before fixture cleanup. Native stub still checks the selected canonical path and nonempty bytes/SHA-256. `--output`, stub assertions, kernel opt-in, profile/source hashes, adapter-before-verification order and all policy/boundary assertions remain intact. | 部分修复: assertion implemented; actual fresh kernel evidence and independent re-review pending with root. No review/gate pass claimed. |

K1 is the only accepted code finding. Root rejected the DS errno substring note as a required change; no extra cleanup was made. No runner/launcher/collector/policy/source change or invented terminal event was introduced.

Exact test-file change verification: pre-fix SHA-256 `62a0a53d10670773643d5f617ea15a51b507ca8f871e4d59333edae03ae8d6a9`; post-fix `105ae162f05daa17dd7e79773a1947f651982c05ac8e1682b1dd12f35b24bac6`. Reversing only the assertion reproduces the pre-fix hash.

## Validation

Executed in a fresh synthetic HOME/TMPDIR with a clean child environment; no caller CA overrides, kernel opt-in, config/auth variables or user HOME material inherited:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_agent_sandbox.py
```

Actual exit **0**; **Ran 77 tests in 1.576s, OK (skipped=10)**: 67 executed, 10 explicit opt-in kernel skips (9 baseline, 1 new CA kernel test). The changed kernel method was skipped, so offline success does not establish its native/sandbox behavior.

Pending, unexecuted here (root-owned):

- Fresh opt-in kernel run of `test_codex_ca_reaches_native_cli` (both default/SSL subcases), `test_kernel_boundary_and_write_preservation`, `test_read_only_does_not_gain_cwd_writes`, and `test_claude_original_deny_write_wins_over_cwd`; actual exits and selected-sink/path/hash/policy/order evidence required.
- Fresh managed-auth synthetic startup validation and inspection/adjudication of actual exits, terminal/final answer, collector diagnostics and first-record policy hashes.
- Dual independent code re-review and root finding adjudication. Original initial-failure evidence remains a failure record.

Docs decision: no product documentation update needed for this test-only correction; the three existing CA documentation surfaces were left unchanged.

## Remaining risks and owners

| Area | Classification | Owner / destination |
| --- | --- | --- |
| K1 assertion defect | fixed in current slice at implementation level; validation pending | Root: fresh kernel validation and independent S1 re-review before final finding status/gate acceptance. |
| Keychain-only/custom roots and endpoint trust | assigned to later work unit | Deployment caller: explicit bundle configuration and post-deployment verification. |
| Native/OpenSSL parser, AUX/algorithm/version differences; input/path replacement stability | assigned to later work unit | Runtime-upgrade owner and caller controlling input stability: documented boundary revalidation / separately scoped follow-up. |
| Exact blocked macOS service remains unmeasured | assigned to later work unit | Root/maintainer: optional separately scoped system-trust diagnosis. |
| Original business task and large caller deny graph | assigned to later work unit | Original caller/controller: separately authorized post-deployment restoration/verification. |

Completion: authorized fix implementation and offline suite complete; required validations above remain **pending**. Next root entry: fresh kernel/live revalidation, then independent S1 re-review and adjudication. Root retains all gate transitions/checkpoints. No Git writes, delegation, publishing, merge, installation/live sync or business restoration occurred.
