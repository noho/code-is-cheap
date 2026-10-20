# GPT-6 Astra xhigh implementation

Implemented the approved slice on `feat/gpt-6-astra-xhigh`. Ready for controller-owned independent reviews; no implementation blocker remains. No commits, pushes, delegation, live sync, App instance, or remote model request were performed.

## Changes

- Added the two-key `gpt-6-astra-xhigh` card: upstream `gpt-6-astra`, effort `xhigh`. Existing Astra/high, Sol, Luna, aliases, business defaults and policy remain intact.
- Connected the distinct title, CLI and both App forms, runner help/catalog/dispatch, and both sandbox subscription-provider decisions. Reused generic shared-home selection, App composition, sync/install and preflight; no catalog, gateway or registry changes.
- Extended existing fixtures for real runner → launcher → terminal helper → fake native selection, old Astra/`astra` high controls, shared homes, interactive/resume forwarding, absent-card rejection and zero gateway queries. Both public App forms were intercepted successfully on this macOS host without opening ChatGPT; composition, synthetic auth, workspace URL and profile-specific environments were checked.
- Verified real preflight discovery, temporary-HOME install/reinstall/manual sync, repeated private card installation, unchanged nine catalog targets / 18 native parses across two syncs, and both sandbox check/launch branches with real cards, synthetic auth and CA. Sandbox tests preserve the existing read/write and network boundaries and reject a denied selected card.

## Validation

Full command/output history, UTC timestamps and exit codes: [validation.log](validation.log). All Python test commands ran with `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests` from the repository root.

| Check | Actual result |
| --- | --- |
| `python3 -m unittest -v test_codex_model_defaults test_install_endpoints test_provider_registry test_sub_agent_preflight test_model_catalog_generation test_agent_sandbox` | 167 tests in 52.378s: **157 passed, 10 skipped**, exit 0. All new selection, App, install/sync, preflight and sandbox tests ran. |
| `zsh -n scripts/agent-tools.zsh`; `zsh -n scripts/codex-agent-run`; Python AST parse of `scripts/agent-sandbox` | All exit 0. |
| `./scripts/codex-agent-run --list-providers`; `--help` | Both exit 0; catalog includes each Astra ID once and help includes the new canonical ID. |
| `./scripts/validate-skills.sh` | All six skills valid, exit 0. |
| `git diff --check` | Exit 0. |

Initial focused runs in the log contain fixture setup failures, subsequently corrected: the retained App destination needed its existing policy/state; staged composer/helper files needed installed executable modes; the real helper needed Python 3.11 on fixture PATH. The final six-suite run passed after these fixture corrections. Catalog rejection warnings in that run are expected output from existing synthetic negative cases.

## Documentation decision

Updated both READMEs together: launcher inventory, CLI/runner/both App examples, high versus xhigh selection, profile table, four shared-login profiles across three upstream models, and profile tree. Updated only the Codex provider table in `skills/sub-agents/SKILL.md`. No separate design or skill-version change is needed. The plan's existing `../../../AGENTS.md` link resolves correctly to the repository AGENTS.md and was retained; controller gate artifacts were left unchanged.

## Residual risks and uncovered areas

| Classification / item | Owner | Destination |
| --- | --- | --- |
| Accepted uncovered live behavior: subscription entitlement, remote Astra xhigh acceptance, cost/latency and native desktop UI behavior are not established by fake-native or intercepted-App tests. | User; controller records limits | Final closeout; separately authorized post-merge live smoke test if desired. |
| Accepted uncovered kernel behavior: 10 existing Seatbelt/srt tests require explicit outer-sandbox opt-in and were skipped. Mocked launch verifies staging/classification, not a new kernel proof. No isolation policy changed. | Controller | Record skips in final closeout; existing opt-in isolation validation workflow. |
| Outside-scope pre-existing diagnostic observation: when the real preflight helper was not executable during fixture setup, the contract failure reached an unbraced variable adjacent to Chinese punctuation at `scripts/sub-agent-preflight:136`; Bash emitted a malformed/unbound-variable diagnostic (the focused test saw a Unicode decode error). It failed before dispatch. Proper installed helper setup passes. This production file is unchanged; no generic error-path expansion was added. | Controller | Triage for a separate preflight diagnostic fix; proposed nonblocking deferral for this additive-profile slice. |
| Assigned later deployment: installed live cards/tools/skill remain unchanged until authorized sync. | User; controller supplies closeout commands | Post-merge sync from the approved checkout: `./scripts/sync-skills.sh`, `./scripts/sync-agent-tools.sh`, `./scripts/sync-codex-agent.sh`; reload interactive functions with `source ~/.zshrc` or a new shell, and reopen Agent sessions for skills. Installed runner callers need no shell reload. |

No new generic resume/auth/CA matrix was added, per the controller's scope decision; existing affected suites cover those shared mechanisms. Independent review, adjudication, accepted fixes, GitHub delivery and final closeout remain with the controller.
