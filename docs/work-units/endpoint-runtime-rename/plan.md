# Private override runtime rename plan

Branch: `fix/endpoint-runtime-rename-disable`. Inspected HEAD/base: `f5e16766a94b7f19680296b0aee1c7a16a1402a3` (`main`, PR67 merged).

## Goal and evidence

Extend the existing private override name-selection contract to runtime names: renaming `override.ds-flash.codex` to any unrecognized name disables that override while preserving its saved contents. Exact-name restoration revalidates/reactivates it. No suffix matching, normalization, or connection-field rename support.

- `scripts/agent-endpoint.py:50–95` filters unknown private override providers before inspecting their values, but requires every recognized provider map to be nonempty and rejects every unknown runtime. This explains the reported `codex-bak` failure.
- `scripts/agent-endpoint.py:134–138` already merges the returned active view over factory then private defaults, replacing whole runtime tuples. Runtime filtering must affect that returned view, not merely skip validation while retaining raw entries.
- `tests/test_install_endpoints.py:98–106` expects an override runtime missing from an older Hy schema to reject. That expectation intentionally changes. At `:236–268`, the malformed-backup table also wrongly treats an empty provider map and a map containing only `codex-bak` as invalid after provider restoration under the new contract.
- `README.md:158–160` and `README.zh.md:149–151` explicitly deny runtime rename disablement. Their Hy paragraphs (`README.md:337`, `README.zh.md:313`) also need to distinguish historical rejecting helpers from the updated helper's filtering behavior.

## Minimal implementation

Change only four product files: `scripts/agent-endpoint.py`, `tests/test_install_endpoints.py`, `README.md`, and `README.zh.md`. This planning pass writes only this artifact; implementation, review/PR delivery, and authorized live sync belong to the controller. Do not access private configs/credentials or alter the unrelated runner-handle-loss artifacts.

1. In `validate_document`, limit runtime selection to `section == "override" and known is not None`. Retain exact provider selection from the validated factory schema. For each recognized provider, first require an object-valued runtime container; null/scalar/list containers remain errors. Then build a new runtime map containing only exact runtime names recognized for that provider by the supplied schema, before inspecting any runtime values. Store this filtered map in the returned active view without mutating the input. Reuse the existing schema; add no registry or suffix rules.
2. Permit an empty runtime map in this private-override path, including an originally empty map or one emptied by filtering. It contributes no overrides. Keep nonempty-provider requirements for private `default` and factory validation (`known is None`). Keep all existing active runtime tuple/field, URL/model/key, blank cloud key, and direct-local Codex key checks. Invalid active entries still reject unrelated queries; an unknown sibling does not shelter an invalid known runtime.
3. Leave whole-tuple merge/deep-copy and snapshot behavior unchanged. A disabled runtime uses its complete private default tuple, or the complete factory tuple when omitted privately. Valid sibling runtimes and other providers remain active; all-renamed runtime maps fall back completely. Ignored values never enter effective connections. Restoring a valid tuple under an exact recognized runtime activates it; restoring malformed data rejects it.
4. Keep default/factory schema and credential checks strict. Keep JSON parsing and global duplicate rejection ahead of selection, including ignored runtime subtrees. Preserve file mode/ownership/regular-file/symlink checks, sanitized errors, selected-key requirements, and the prohibition on borrowing backup/environment credentials. No security or ownership-test expansion is needed.

## Focused regression changes

Reuse synthetic `conn`/`private_doc`, temporary HOME, and existing staged-helper/fake-native fixtures; no network or live probes.

- Extend rename/restore coverage to both `codex` and `claude`, using `codex-bak` plus arbitrary names without a backup suffix. Verify active → renamed → restored whole tuples, a valid sibling override, another active provider, and all-renamed/empty override maps. Exercise private-default and omitted-private-default factory fallback. Assert unknown names are absent from the active/effective result, input remains unchanged, retained snapshots remain stable, and load/`--check`/existing-file `--initialize` preserve private bytes and mode.
- Add runtime-value cases for null/scalar/list/empty object, incomplete/extra fields, invalid URL/model/key, and blank cloud key under unknown runtime names: ignore them before value validation while valid siblings still work. Restore the exact known runtime and assert rejection for malformed values, including an unrelated query; valid saved values reactivate. Preserve rejection for wrong recognized-provider container types and renamed fields inside active tuples.
- Update `test_hy_factory_override_mapping_and_old_schema_ordering`: under the old schema lacking `hy.codex`, assert the override runtime is absent from the active view; under the current schema it is active. Preserve old-schema rejection with `default.hy.codex` unknown to that supplied schema instead. Retain current mapping/staged-factory checks.
- In `test_malformed_backups_are_inert_until_exact_name_restoration`, move the provider `{}` and `{"codex-bak": ...}` cases to successful no-active-runtime coverage. Keep the genuinely malformed active cases. Extend strict-selection tests with runtime-level malformed/duplicate JSON, strict default/factory unknown-runtime and empty-provider rejection, and malformed known runtimes alongside ignored names. Do not preserve contradictory unknown-override-runtime rejection.
- Extend the existing fake-launch/key-fallback case with all-renamed runtime entries under recognized `ds-flash`: unrelated `mimo_claude` still launches, and disabled cloud connections with empty factory keys fail selected-key checks despite saved backup keys. Reuse current assertions; avoid new launcher machinery.

## Documentation and verification

Update both private-connection sections together with a single-runtime rename example, arbitrary-name/exact-name selection, unknown runtime values ignored before validation, valid siblings retained, empty/all-renamed override maps, whole-tuple fallback, restoration, and unchanged strict default/factory/active-field/JSON/file/key boundaries. Remove the runtime-renaming prohibition while retaining the connection-field prohibition. Align both Hy deployment notes: helpers with this fix ignore runtime overrides absent from their installed factory, so install both updated factories to activate `hy.codex`; historical helpers may reject them. Do not imply unknown default runtimes are accepted or change unrelated Hy claims.

Run the changed `EndpointTests` first, then `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_install_endpoints.py'`, followed by `git diff --check`. Check the final product diff is limited to the four files above and existing unrelated artifacts remain untouched. Controller owns independent review/adjudication and any fixes, commits, PR, and live sync.

Blocking questions: none.
