# GPT-6 Astra xhigh: implementation plan

Status: proposed for controller acceptance; plan only. One implementation slice.
Branch: `feat/gpt-6-astra-xhigh`; inspected base: `f300ca395dbdd8204ff009487f1d295235965852`.
Authority: confirmed scope and routes in [control.md](control.md), plus repository [AGENTS.md](../../../AGENTS.md).

## Outcome and boundaries

Add the independent canonical profile ID `gpt-6-astra-xhigh`. Its card selects upstream
`model = "gpt-6-astra"` and `model_reasoning_effort = "xhigh"`. Existing
`gpt-6-astra` continues selecting that same upstream model at `high`.

The new ID must work through interactive CLI, both App launcher forms, the Codex runner,
optional preflight, optional `agent-sandbox`, and installed discovery. It shares the normal
subscription login and CLI session home. App state follows the existing per-profile composed-home mechanism.
Use existing switches and card discovery; add no registry abstraction, gateway, shim route,
catalog mapping, new short alias, or model-ID suffix. Sol, Luna, `gpt_codex`, business defaults,
Claude providers, sandbox policy, and unrelated workflow examples retain their existing behavior.

## Evidence and affected runtime paths

Line references below identify the inspected base; names remain the durable anchors after edits.

| Path / evidence | Required treatment |
| --- | --- |
| `codex-agent/profiles/gpt-6-astra/config.toml:5` contains only Astra / high model deltas. | Add `codex-agent/profiles/gpt-6-astra-xhigh/config.toml` with the same card format and Astra / xhigh. Retain the old card. No provider, credentials, policy, or catalog keys belong in the new card. |
| `scripts/agent-tools.zsh:171` (`_codex_agent_title`), `:246` (`_codex_agent_require_home`), `:498` and `:513` (wrappers). | Add stable title `CodexAgent-GPT-6-Astra-Xhigh`, CLI wrapper `gpt-6-astra-xhigh_codex`, App wrapper `gpt-6-astra-xhigh_codex_app`, and the credential-check exemption alongside existing subscription profiles. |
| Same file: `_codex_agent_home`, `_codex_agent_shim_port`, `_codex_agent_launch`, `_codex_agent_app`. | Reuse shared `~/.codex`, native `-p <id>` placement, resume handling, empty shim-port fallback, and App composition. `gpt-6-astra-xhigh_codex app [workspace]` must dispatch to the same App path as the direct wrapper. App data/home resolve under `~/.codex-agent/app-data/gpt-6-astra-xhigh/`, distinct from old Astra. No generic helper changes expected. |
| `scripts/codex-agent-run:18`, `:24`, `:241`, `:298`. | Extend usage/help, `--list-providers`, and provider-to-launcher dispatch with the canonical new ID. Preserve the existing `astra` alias's high route. Do not add a second upstream model name. |
| `scripts/sub-agent-preflight:95–153`. | Production code already reads the selected runner's catalog, checks `<provider>_codex`, and requires `~/.codex/<provider>.config.toml`. Verify with the real updated runner/launcher; no new production special case is needed. |
| `scripts/agent-sandbox:651` and `:689`. | Add the new ID to **both** subscription-provider sets: skip `helper.connection(..., require_key=True)` and include the existing OpenAI login/API network domains. These are separate launch/check branches and must both be covered. |
| Same file: `codex_documents` / `prepare_codex` (`:285`, `:346`). | Existing generic code overlays the selected shared-home card, retains model/effort, stages the selected card name, and copies subscription `auth.json`. Reuse it; verify selected config, auth and route with synthetic inputs. |
| `scripts/sync-codex-agent.sh:75–86`, `:117–140`; `scripts/sync-agent-tools.sh:10–20`; `install.sh:54–56`. | Card globbing and whole-tool installation already discover/install the new artifacts. Extend tests instead of introducing ID-specific install code. Sync still installs the card privately and preserves base local settings. |
| `scripts/patch-codex-model-catalog.py:28` / `DEFAULT_PROFILES`; `codex-agent/model-providers.toml`; `codex-agent/shim-routes.json`; private endpoint defaults. | New subscription card has no custom catalog or gateway. Leave these mappings unchanged; verify no Astra-xhigh catalog is generated. Backup relocation already globs `*.config.toml` (`scripts/backup/agents-backup-restore.sh:373`). |

Runner use still invokes `agent-endpoint.py` for `--runner-error-contract` and terminal
`--exec-native` (`scripts/agent-endpoint.py:251–301`). “No credential lookup” means no
third-party connection/key query, not removal of these required runner operations.
The sandbox also retains its existing endpoint-file readability checks; this slice changes
provider classification, not that general setup behavior.

## Single implementation slice

1. Add the model card and the narrow launcher, runner and sandbox entries above together.
   Preserve exact profile/upstream identity separation and old Astra behavior.
2. Add focused behavioral coverage using the existing isolated fixtures below. Prefer extending
   those fixtures over adding a parallel framework. Assert selected configuration and failure
   boundaries; merely checking that an ID appears in source text is insufficient.
3. Update the two READMEs and the sub-agents provider table, then run the listed validation.
   Deliver implementation evidence and skipped/uncovered checks to the controller for review.

The implementer/fixer is the controller-dispatched `gpt-6-sol` Codex agent. The controller owns
plan acceptance, two independent full Deepreviews through Claude providers **`mimo` and
`ds-flash`**, adjudication, accepted fixes and affected re-review, draft PR delivery, and final
closeout. These explicit review routes override AGENTS.md's `mimo-flash` default.
This planning task performs none of those gates and authorizes no deployment.

## Meaningful coverage and assertions

| Existing fixture / test file | Required new or extended assertions |
| --- | --- |
| `tests/test_codex_model_defaults.py` / existing GPT effort test | Parse all four subscription cards. New ID is exactly Astra / xhigh; old ID remains Astra / high; Sol and Luna remain unchanged. New card contains only the two model-delta keys. Rename the existing “three cards” test to match its scope. |
| `tests/test_install_endpoints.py` / `RunnerNativeBoundaryTests` and launcher fixtures | Exercise the real repository runner → real launcher → existing terminal helper → fake native Codex with the new canonical provider. Fake native records argv, `CODEX_HOME`, `CODEX_SQLITE_HOME`, and the parsed selected card; assert one `-p gpt-6-astra-xhigh` after `exec`, shared home, actual upstream Astra / xhigh, and collected report provider identity. Run old Astra as a high control. Exercise direct interactive and `resume --help` forwarding to cover native profile placement without modifying session history. |
| Same launcher/helper fixtures | Assert `_codex_agent_shim_port` is empty for the new ID, the title is distinct, and ordinary launch succeeds without an endpoint/key configuration or shim listener. Instrument third-party helper queries to fail/record access while permitting contract and native-exec helper modes; assert zero connection/key queries. A missing new card must fail before native entry even when the old Astra card exists. Do not satisfy these tests with an empty fake new card. |
| `tests/test_provider_registry.py` / App composer, plus launcher fixtures | Compose from a base with different model/effort using the real new card; assert upstream Astra / xhigh, preserved local policy/state/provider tables, and repeat composition idempotence. Verify both public App entry points select the new ID. On macOS with ChatGPT installed, run the actual App launcher with a zsh function intercepting `/usr/bin/open` and temporary HOME: assert composed config, copied synthetic auth, workspace URL and profile-specific home/user-data envs. Never open a real App instance. The path-named open stub is supported on this host. If the App prerequisite is absent, retain unconditional wrapper-dispatch + composer coverage and report the full-launch skip. |
| `tests/test_sub_agent_preflight.py` / `PreflightTests` | Add the new ID to the fixture catalog and a case using the real repository runner's `--list-providers`, real launcher and staged helper/card. Assert setup success, canonical provider, launcher, shared `profile_home`, and generated command selecting the new ID. Removing only the new card must yield failure and an empty command despite old Astra being present. Mock-catalog-only success does not verify discovery. Production preflight code should remain unchanged. |
| `tests/test_model_catalog_generation.py` / `ConversionSyncTests` | After isolated real sync, both cards exist at shared-home `<id>.config.toml`, contain the respective model/effort and mode `0600`, and survive repeat sync byte-for-byte. No `model-catalogs/gpt-6-astra-xhigh.json` is created; existing nine generated catalog targets and native-parse count stay unchanged. Preserve existing local-base and rollback assertions rather than weakening them for the added card. |
| `tests/test_install_endpoints.py` / downloaded bootstrap reinstall test | Extend the existing temporary-HOME install/reinstall/manual-sync fixture to assert new card contents and old Astra high, installed runner catalog, and installed CLI/App launcher discovery; existing endpoint overrides, local state and skill installation assertions remain. Use only fake services and bundled native catalog reads, as the fixture already does. This proves install discovery without adding install branches. |
| `tests/test_agent_sandbox.py` / mocked `main()` check-and-launch setup (existing `CodexCATests.run_main` pattern) | Add focused new-profile coverage for **both** `--check` and launch, with a synthetic shared base, real new card, synthetic `auth.json`, valid fixture CA, and `helper.connection` set to raise if called. Check succeeds without exec; launch stages Astra / xhigh, selected-card marker and synthetic auth privately, retains canonical provider in manifest, and includes route plus `auth.openai.com:443`, `api.openai.com:443`, `chatgpt.com:443` in the existing strict allowlist. Capture `os.execvpe`; never run a real model. Assert existing write/read boundaries are preserved. Include old Astra high as the subscription control. A missing/denied required auth or card still fails before execution. |

Tests must keep all homes, auth, endpoint documents, generated outputs and service stubs in
temporary directories and use synthetic values. Sync/install tests may read the installed
Codex bundled catalog in a fresh home; they must not invoke a remote model or change live services.

## Validation commands and acceptance

Run from `/Users/leo/workspace/code-is-cheap`, using Python 3.11+ and installed zsh/jq/Codex.
These prerequisites, Node, rsync, uv, PyYAML and `/Applications/ChatGPT.app` were present when inspected.

```bash
zsh -n scripts/agent-tools.zsh
zsh -n scripts/codex-agent-run
python3 -c 'import ast,pathlib; ast.parse(pathlib.Path("scripts/agent-sandbox").read_text())'
./scripts/codex-agent-run --list-providers
./scripts/codex-agent-run --help
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests python3 -m unittest -v test_codex_model_defaults test_install_endpoints test_provider_registry test_sub_agent_preflight test_model_catalog_generation test_agent_sandbox
./scripts/validate-skills.sh
git diff --check
```

Expected: syntax/skill/diff checks exit 0; runner catalog contains both Astra IDs once, and help
advertises the new canonical ID. The six affected suites pass with the selection, installed
discovery, no-connection-query, App composition and sandbox assertions above. Inspect the test
summary: opt-in kernel tests are expected to skip; an absent prerequisite for a newly required
selection/sync test is an uncovered check to report, not evidence of a pass. Do not run sync scripts
against the real HOME as validation. Existing targeted suites cover the unchanged generic resume,
provider registry, rollback and native-exit machinery; no new live invocation is required.

Planning baseline already executed (before any implementation):

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests python3 -m unittest -v test_codex_model_defaults test_provider_registry test_sub_agent_preflight
```

Result: **28 tests passed** in 8.230 seconds. Runner catalog currently lacks the new ID; its
launcher does not yet exist. These are expected pre-implementation observations, not failures
of an implementation. No production code, live files or deployment were changed by planning.

## Documentation decision

Update `README.md` and `README.zh.md` together: launcher/provider inventory, explicit high versus
xhigh choice, profile table, shared-login profile count (four profiles across three upstream models),
and repository profile tree. Add a concise new-ID CLI/runner/App usage example. Explain that
`gpt-6-astra-xhigh` is a profile selection for upstream Astra at xhigh; keep old examples and
workflow-role assignments unless a local edit is needed to explain this choice.
Update only the Codex provider table in `skills/sub-agents/SKILL.md`; the skill's workflow stays intact.
No separate design document, catalog-source update, installer refactor or skill-version change is needed.

## Residual risks, uncovered areas and destinations

| Item | Disposition / owner / destination |
| --- | --- |
| Live subscription entitlement, native App UI behavior, remote acceptance of Astra xhigh, latency and billing are not proved by local fake-native tests. | Accepted uncovered live behavior for this configuration slice; controller records it in final closeout. User owns any separately authorized post-merge live smoke test. No provider call is a local acceptance gate. |
| Mocked sandbox selection checks do not establish a new macOS kernel isolation proof. | Existing Seatbelt/srt boundaries are reused without policy changes. Controller records opt-in kernel skips in validation/closeout; any newly observed boundary regression is blocking and belongs to this work unit's fixes. |
| App full-launch interception may require macOS plus installed ChatGPT. | Implementer runs it on the current capable host; if unavailable elsewhere, controller records the exact skip and the unconditional wrapper/composer coverage in implementation evidence and closeout. |
| Added IDs can drift across existing explicit lists. | Blocking until launcher, runner, preflight and both sandbox branches pass behavioral coverage; implementer owns tests and fixes in this slice. No broad registry refactor is justified. |
| Repository changes do not update installed launchers/cards/skills until sync. | User owns authorized live sync after manual merge; controller must record the commands below and reload instructions in final closeout and remind the user. No deployment is authorized by this plan. |

Applicable future live commands, from the checkout containing the approved changes:

```bash
./scripts/sync-skills.sh
./scripts/sync-agent-tools.sh
./scripts/sync-codex-agent.sh
source ~/.zshrc
```

Opening a new shell also reloads interactive launchers. Reopen Agent sessions to load updated
skills. Installed runner callers need no shell reload when the installed runner is already on PATH.

Planning blockers: **none**. Next entry point: controller plan acceptance and implementation dispatch.
