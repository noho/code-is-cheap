# Endpoint runtime rename implementation

Implemented the accepted `plan.md` on the existing work branch
`fix/endpoint-runtime-rename-disable`.

## Changes

- `scripts/agent-endpoint.py`: the existing `validate_document` schema owner
  selects private override runtimes by exact names in the supplied factory,
  before inspecting runtime values. Its returned active view contains only
  recognized runtimes. Recognized provider containers must still be objects;
  empty or entirely filtered private override maps contribute no overrides.
  Default/factory validation remains strict. No suffix rules, input mutation,
  merge/snapshot changes, security policy changes or credential fallback were
  introduced.
- `tests/test_install_endpoints.py`: updated old Hy schema expectations and
  moved empty/all-unknown provider maps out of malformed-active expectations.
  Added both-runtime arbitrary rename/restoration, whole private-default and
  factory fallback, active sibling/provider preservation, stable snapshots,
  unchanged input/private bytes/mode, malformed ignored/restored values,
  active tuple-field rename rejection, strict default/factory/container/JSON
  boundaries and local/cloud key boundaries. Extended the existing staged
  helper/fake Claude launch test with all-renamed runtime entries; unrelated
  `mimo_claude` launches while disabled cloud connections reject missing
  selected keys despite saved/inherited keys.
- `README.md` and `README.zh.md`: documented arbitrary runtime names, exact
  restoration, inert empty/all-disabled maps, fallback and unchanged strict
  boundaries. Updated both Hy deployment notes to distinguish filtering
  helpers from historical rejecting helpers.

## Actual verification

From `/Users/leo/workspace/code-is-cheap`, ran the changed/focused endpoint
tests first:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests python3 -m unittest -v test_install_endpoints.EndpointTests.test_hy_factory_override_mapping_and_old_schema_ordering test_install_endpoints.EndpointTests.test_rename_disable_restore_uses_whole_defaults_without_writes test_install_endpoints.EndpointTests.test_runtime_rename_restore_preserves_siblings_snapshots_and_private_file test_install_endpoints.EndpointTests.test_empty_and_all_disabled_runtime_maps_contribute_no_overrides test_install_endpoints.EndpointTests.test_unknown_runtime_values_are_inert_until_exact_name_restoration test_install_endpoints.EndpointTests.test_malformed_backups_are_inert_until_exact_name_restoration test_install_endpoints.EndpointTests.test_backup_selection_keeps_default_factory_and_json_validation_strict test_install_endpoints.EndpointTests.test_mimo_native_launch_with_disabled_overrides_and_no_backup_key_fallback
```

Exit 0: **8 tests passed in 7.281 seconds**.

Then ran the full requested suite:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_install_endpoints.py'
```

Exit 0: **37 tests passed in 35.340 seconds**.

```bash
git diff --check
```

Exit 0, no output. Also inspected `git diff --numstat`, `git diff` and
`git status --short`: tracked edits are limited to the four authorized product
files above; this implementation artifact is the only newly written file.
The pre-existing plan/review artifacts were retained. The three pre-existing
untracked `docs/reviews/runner-handle-loss-20261023-*` files were untouched.

No verification failures occurred, so there were no test-failure corrections
or retries to report.

## Limits and handoff

All connection/launch coverage uses synthetic data, temporary homes, staged
helpers, fake native executables and the existing suite's local fixtures.
No live endpoints, private configurations or credential files were accessed.
No model capability or vendor inference work was performed. No delegation,
commits, push, PR creation or live sync was performed, per the implementer
task scope. Independent review, adjudication and final closeout remain the
controller's responsibility. No known implementation issues remain from the
requested checks.

After controller review and final closeout, remind the user to sync the
approved changes from the checkout containing them. Applicable commands
(recorded only; live deployment requires user authorization):

```bash
./scripts/sync-agent-tools.sh
./scripts/sync-codex-agent.sh
```

Both installed endpoint helpers/factories need the update. No skill files
changed, so `sync-skills.sh` is not needed for this work unit. If interactive
launcher functions are deployed, reload with `source ~/.zshrc` or a new shell;
runner callers already using an installed runner on `PATH` need no shell
reload.
