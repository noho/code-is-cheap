# GPT-6.2 upstream model IDs

## Goal and boundary

On the existing `chore/gpt-6-2-model-ids` branch, keep public provider/profile/launcher identities and change only their upstream model selections. Preserve reasoning efforts, account-login routing, policy, and unrelated settings. The controller owns implementation dispatch, independent reviews, adjudication, commits, push, and PR. This planning task changes only this document.

| Provider/profile ID (unchanged) | Current upstream model | Required upstream model | Effort (unchanged) |
| --- | --- | --- | --- |
| `gpt-6-sol` | `gpt-6.1-sol` | `gpt-6.2-sol` | `high` |
| `gpt-6-sol-x` | `gpt-6.1-sol` | `gpt-6.2-sol` | `xhigh` |
| `gpt-6-sol-max` | `gpt-6.1-sol` | `gpt-6.2-sol` | `max` |
| `gpt-6-astra` | `gpt-6-astra` | `gpt-6.2-astra` | `high` |
| `gpt-6-astra-x` | `gpt-6-astra` | `gpt-6.2-astra` | `xhigh` |
| `gpt-6-astra-max` | `gpt-6-astra` | `gpt-6.2-astra` | `max` |
| `business` (derived from base Sol card) | `gpt-6.1-sol` | `gpt-6.2-sol` | `high` |

Do not rename profile directories, installed card filenames, `-p` arguments, runner provider IDs, `sol`/`astra` aliases, launcher functions (including `gpt_codex`), app-data directories, or window titles. `gpt-6-luna` remains unchanged. `gpt-6.2-*` strings are upstream model IDs, not new aliases. Do not globally replace `gpt-6-astra`, since it serves both roles today.

## Inspected ownership and exact edit scope

### Production sources of truth

1. Change only `model` in these six two-key model cards; retain `model_reasoning_effort` and alias-oriented comments:
   - `codex-agent/profiles/gpt-6-sol/config.toml`
   - `codex-agent/profiles/gpt-6-sol-x/config.toml`
   - `codex-agent/profiles/gpt-6-sol-max/config.toml`
   - `codex-agent/profiles/gpt-6-astra/config.toml`
   - `codex-agent/profiles/gpt-6-astra-x/config.toml`
   - `codex-agent/profiles/gpt-6-astra-max/config.toml`
2. In `scripts/sync-codex-model-defaults.py:compose`, change the existing exact-model guard from `gpt-6.1-sol` to `gpt-6.2-sol`. Preserve the guard, two-key update boundary, idempotence, permissions, atomic replacement, and rejection behavior. The error's `gpt-6-sol` names the card alias and stays unchanged. No generalization or new model registry is needed.

### Derived paths inspected; no production edits needed

- `scripts/sync-codex-agent.sh` copies all tracked cards into the shared home and passes `codex-agent/profiles/gpt-6-sol/config.toml` to the business-default helper. It already derives the desired selections from those cards.
- `scripts/agent-tools.zsh` selects cards by alias for CLI/resume and passes cards to `scripts/compose-codex-app-config.py` for composed app homes. The composer overlays card keys. `gpt_codex` selects the base Sol alias.
- `scripts/codex-agent-run` normalizes `sol`/`astra` to existing provider IDs; `scripts/sub-agent-preflight` discovers those IDs. `scripts/agent-sandbox` layers the selected card over the shared base and stages subscription login. Keep these alias lists and routes intact.
- The shared home's root `config.toml` is machine-local policy/runtime state, not a tracked Sol default. `scripts/sync-codex-providers.py` owns only its marked provider-table block. Do not add a root-model migration or overwrite personal defaults. Shared-home managed Sol cards and card-derived app/sandbox selections receive the new ID automatically.
- `codex-agent/model-providers.toml`, `codex-agent/shim-routes.json`, `config/endpoints.example.json`, catalog source snapshots, and catalog generation logic do not define these subscription upstream IDs. GPT cards continue using native OpenAI account login without a custom catalog or shim.

### Current documentation and skill

- `README.md`: update the subscription-model prose around lines 488–493, including the human-readable business default (`GPT-6.2 Sol / high`), and the six upstream-model cells around lines 516–521. Provider cells and command examples stay unchanged.
- `README.zh.md`: make the corresponding prose/business-default updates around lines 448–453 and six upstream-model cells around lines 474–479.
- `skills/sub-agents/SKILL.md`: update the current Sol upstream statement and explicitly state Astra's `gpt-6.2-astra` upstream alongside it. Keep provider inventory, effort mapping, examples, and workflow unchanged.

### Existing tests to synchronize

Update only the model element of the existing `GPT_PROFILES` tuples in all five files below; keep provider and effort elements unchanged:

- `tests/test_codex_model_defaults.py`: also update business expected models in the replacement and insertion tests.
- `tests/test_model_catalog_generation.py`: also update `ConversionSyncTests.test_success_repeat_bytes_modes_and_no_service_actions`'s expected business model. Preserve the deliberately old `gpt-6-astra-xhigh` card fixture and assertions that sync retains it.
- `tests/test_provider_registry.py`: update the current Sol shared-base model in the subscription-composition fixture and its paired string replacement together. Retain the deliberate `medium` base effort so the test proves the selected card wins.
- `tests/test_install_endpoints.py`: update the explicit `astra`/`sol` runner-alias expected upstream models and the current shared-base Sol fixture in `stage_subscription_profiles`. Preserve provider/title/home assertions and deliberately retained old-provider data.
- `tests/test_agent_sandbox.py`: update the subscription shared-base Sol fixture in `CodexCATests.run_main`; keep its `medium` effort to prove the staged card overrides it.

In `tests/test_repair_codex_reasoning_history.py`, update the managed Sol card fixture in `test_launcher_resume_forwards_without_repair` to `gpt-6.2-sol`. Its existing old-model rollout may remain to exercise byte-for-byte preservation across a model update; it is historical input, not a current-model assertion. Likewise, old-model rollout input in `test_interactive_resume_keeps_third_party_and_business_home_selection` can remain unchanged. Generic legacy-repair and provider-registry preservation fixtures using `model = "gpt-6-sol"` need no mechanical rename.

`tests/test_sub_agent_preflight.py` checks alias discovery and missing cards, so run it without changing its supported-provider expectations. Do not consolidate duplicated test matrices or introduce new architecture in this work unit.

## Implementation order

1. Update the six cards and the business helper's exact-model guard together.
2. Synchronize the current documentation, skill, and existing test expectations/fixtures listed above.
3. Run the focused checks below, inspect failures, and fix only regressions caused by this change. Supply the diff and actual validation results to the controller for its independent review loop.

## Validation commands and expected assertions

Run from the repository root. These tests use temporary homes/stubbed launchers; do not invoke unredirected installer or sync scripts against real HOME. Python 3.11+ is required for `tomllib`; the endpoint suite also needs the existing `codex`, `zsh`, and `jq` prerequisites, and skill validation needs PyYAML. The installed Codex is used for bundled model metadata, not a vendor request. Clear inherited opt-in live/kernel-test flags if running a broader suite.

```bash
python3 -m unittest discover -s tests -p 'test_codex_model_defaults.py'
python3 -m unittest discover -s tests -p 'test_model_catalog_generation.py'
python3 -m unittest discover -s tests -p 'test_provider_registry.py'
python3 -m unittest discover -s tests -p 'test_install_endpoints.py'
python3 -m unittest discover -s tests -p 'test_agent_sandbox.py'
python3 -m unittest discover -s tests -p 'test_sub_agent_preflight.py'
python3 -m unittest discover -s tests -p 'test_repair_codex_reasoning_history.py'
./scripts/validate-skills.sh
git diff --check
git diff --stat
git status --short
```

Expected evidence from the existing cases:

- All six alias/model/effort tuples match the table; cards still contain only `model` and `model_reasoning_effort`. Luna remains `gpt-6-luna` / `max`.
- Temporary-home sync installs cards under unchanged filenames; business receives `gpt-6.2-sol` / `high` while auth, unrelated settings, mode bits, and retained obsolete cards stay unchanged. A second sync is byte-idempotent; malformed/symlink business config remains rejected without interrupting the earlier shared deployment.
- Runner aliases, interactive launchers, resume, and `gpt_codex` select unchanged profiles with the new upstream IDs, forward arguments, and leave saved rollout bytes intact. Subscription launch paths do not query gateway credentials.
- App composition and sandbox staging apply the selected model/effort over shared defaults while preserving policy, registry, auth, and app state. App launch tests mock `open`; report platform/prerequisite skips explicitly.
- Preflight still lists the original provider IDs; the deprecated `gpt-6-astra-xhigh` remains unsupported. GPT profiles still receive no generated custom catalog. Existing catalog snapshot hashes remain unchanged.

Audit current sources without including historical artifacts:

```bash
rg -n 'gpt-6\.1-sol|GPT-6\.1' codex-agent scripts skills README.md README.zh.md tests
rg -n 'gpt-6-astra|gpt-6\.2-(sol|astra)' codex-agent/profiles scripts/sync-codex-model-defaults.py skills/sub-agents/SKILL.md README.md README.zh.md tests
```

The first search may retain only intentional legacy test inputs described above, with each remaining occurrence explained. In the second, inspect model values versus aliases by context; old Astra alias occurrences are required, not failures. Review the final diff for unchanged effort settings, alias names, catalogs/routes, and pricing.

## Risks, exclusions, and handoff

- Updating the Sol card without updating the helper guard would break business sync; update and validate them together.
- Broad replacement would break alias compatibility or erase valuable legacy fixtures. Only upstream model values/current prose change.
- Offline checks prove repository selection and propagation, not upstream account entitlement, server acceptance of the new IDs, or actual `max` support. No real model request, app launch, live service change, API pricing change, or real HOME mutation is authorized here.
- There is no tracked business configuration or shared root-model default to edit. Existing user root defaults and explicit CLI model overrides remain user-owned. Retained obsolete cards/saved sessions are not migrated.
- Leave historical `docs/reviews`, existing `docs/work-units`, `docs/gateflow`, maintenance evidence, and other evidence artifacts untouched. In particular, do not stage, edit, or delete the existing untracked `docs/reviews/runner-handle-loss-20261023-{evidence.json,investigation.md,notification.json}` files. This new plan is the sole planning artifact.
- No planning blocker was found. Missing local validation prerequisites should be reported to the controller rather than installed into real HOME or bypassed silently.
- The controller's eventual closeout should record `./scripts/sync-skills.sh` and `./scripts/sync-codex-agent.sh` as applicable later deployment commands. Launcher/runner code is unchanged, so `sync-agent-tools.sh` is not required by this model-ID change. Deployment requires separate user authorization and is not executed in this task. Reopen Agent sessions after syncing skills; shell reload is needed only if launcher functions are separately deployed.
