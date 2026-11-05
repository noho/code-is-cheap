# Endpoint rename disable plan

Branch: `fix/endpoint-rename-disable` · inspected base: `f2ba5abe8b123a6581632860e59e9bf797b76133`.

## Goal and boundaries

Temporarily disable overrides by renaming `override.ds-flash` to an unknown provider name such as `ds-flash-bak` or `overrideds-flash-bak`, or by renaming root `override` to `overridexxx`. Restore the exact recognized name to reactivate. Preserve ignored data in the private JSON unchanged. Matching connections fall back to the user's `default`, then program defaults for omitted connections; unrelated `mimo_claude` must launch normally when its effective key is present.

This is a selection/validation fix only. No model/provider/capability changes, suffix heuristics, migration, private-file rewriting, framework, or broad refactor. Controller owns implementation dispatch, reviews, delivery, and any separately authorized live sync. This planning pass creates only this artifact; it does not read private endpoints or credentials.

## Evidence and root cause

- `scripts/agent-endpoint.py:50–87`: `validate_document` rejects unknown root fields, then validates every provider subtree. With the factory schema supplied, an unknown override provider fails provider/runtime validation; malformed backup values fail even earlier. Thus renaming either scope rejects the entire document.
- `scripts/agent-endpoint.py:108–151`: every connection query loads/validates the entire private document. Simply relaxing validation is insufficient: the merge currently iterates raw override providers and calls `result[provider].update(...)`, so an ignored unknown provider would cause a `KeyError` unless selection and merge agree.
- `scripts/agent-tools.zsh:89–145,257`: Claude launch and Codex setup use this helper. `codex-agent/bin/codex-auto-review-shim:91–105,236–242,321–328` imports the same helper and resolves snapshots. Fix schema ownership here rather than adding launcher/shim filtering or a second provider registry.
- `config/endpoints.example.json` is the existing authority for recognized provider/runtime pairs. `factory_document()` validates the deployed factory or repository fallback before passing `factory["default"]` to private validation. The Hy regression at `tests/test_install_endpoints.py:98` deliberately rejects a runtime absent from the supplied factory; retain that behavior.
- Read-only in-memory probes against the inspected helper: a valid active `override.ds-flash.codex` is accepted; the same tuple under `ds-flash-bak` fails `unknown provider/runtime`; root `overridexxx` fails the root schema check. Unknown default providers and active unknown runtimes also fail and must continue to do so.
- `README.md:150–175` and `README.zh.md:141–166` currently promise rejection of all unknown fields and describe deletion as the way to revert. Both need the narrower active/inert contract below.

## Selection, validation, and merge contract

1. Keep JSON parsing and file checks before semantic selection: valid JSON, duplicate-field rejection throughout the entire document (including inert subtrees), owned regular non-symlink file, exact mode `600`, and sanitized errors. Inert data may be malformed **as connection settings**, not malformed JSON.
2. Existing private documents remain objects with mandatory object-valued `default`. Validate `default` exactly as today, including unknown providers, unsupported runtimes, empty provider maps, tuple shape and values—even if an override shadows that default tuple. There is no demonstrated contradiction requiring default relaxation. Missing private files still use program defaults without creation.
3. Only exact root `override` is active; it is optional, but must be an object when present. Other private root fields are inert regardless of their value/shape. Under active `override`, only provider names present in the validated factory defaults are active. Skip unknown providers **before** inspecting their value, runtime names, tuple fields, URLs, models, or keys. No suffix recognition or backup-name normalization.
4. For recognized override providers, preserve existing strict validation: nonempty provider object; only `codex`/`claude` runtimes supported for that provider by the factory; exact complete `base_url`/`upstream_model`/`api_key` tuples; existing URL/model/key rules; own nonblank cloud override key; empty direct-local Codex key. Unknown runtime names under a recognized provider still fail. Validate all recognized active entries, not merely the requested connection; an active malformed ds-flash entry still blocks a mimo query. Unknown fields inside active tuples still fail.
5. Implementation detail: keep the schema owner in `agent-endpoint.py`. Have `validate_document(doc, known=...)` produce and return a validated active view containing strict `default` and only recognized override providers; let `load_endpoints()` merge that returned view instead of raw private data. Do not mutate the input. Existing callers that only check validation may ignore the return. Keep the `known is None` factory-validation path strict as today; private-field leniency must not weaken project-default validation or credential prohibition. A small local selection block is sufficient; do not add another schema or provider list.
6. Merge a deep copy of factory defaults, then private defaults, then selected overrides. Replace each runtime's entire tuple, never individual fields. Ignored names must neither appear in effective connections nor trigger lookup errors. Preserve snapshot behavior and existing Codex URL normalization.
7. Fallback does not borrow backup credentials or inherited environment keys. A cloud fallback with an empty effective default key still fails `require_key=True`/launch, as today. Load/check without a selected-key requirement may succeed. Restoring an exact active name revalidates its contents before use; it may fail if the stored tuple is invalid.

## Minimal implementation and behavioral regressions

Change only `scripts/agent-endpoint.py`, focused cases in `tests/test_install_endpoints.py`, and the private-connection sections of both READMEs. Reuse `private_doc`, `conn`, temporary HOME, `stage_helper`, and existing fake-native-launch patterns; use synthetic keys and no network.

| Regression | Required observable behavior |
| --- | --- |
| Single provider rename / restore | Parameterize `ds-flash-bak` and `overrideds-flash-bak`. With distinct default/override tuples for both runtimes, active → renamed → restored selects complete override → complete private default → original override. Other active overrides remain effective; ignored provider names never enter the result. Retain a selected snapshot and verify later loads do not change it. |
| Root rename / restore | Rename `override` to `overridexxx`; both overridden providers/runtimes fall back, then exact-name restoration reactivates them. Keep mandatory `default`; cover absent runtime using the factory fallback. |
| Inert malformed data | Unknown root values and unknown override-provider values may be null/scalars, empty maps, or incomplete/invalid connection-shaped objects. Load and `--check` succeed without validating their contents; malformed JSON and duplicate keys inside these same backups still fail. |
| Active malformed data | Restore the malformed backup to an active name and assert rejection. Retain/add compact cases for partial/extra tuple fields, blank cloud override key, invalid URL/model/key, unsupported runtime and malformed recognized provider/override containers. A malformed recognized ds-flash entry still rejects a mimo query. |
| Unrelated actual launcher | Stage the shared helper and a fake `claude`; invoke `mimo_claude` with a synthetic valid default key while ds-flash backups/root backups are present. Assert native stub execution receives the intended mimo URL/model/token, no backup credentials, and no key in argv/settings. |
| Fallback key boundary and no writes | Renamed ds-flash uses its default key; an empty effective default key fails selected cloud launch/check despite a key in the backup or environment. Compare private bytes and mode before/after load/check and existing-file `--initialize`; backup data remains unchanged. |

Keep current default-rejection, whole-tuple, missing-file, factory-credential, permissions/symlink, inherited-key scrubbing, selected-key, local-Codex, shim mapping/snapshot and install-preservation regressions. Controller scope amendment approved before implementation (see controller.md, Plan check passed): the unchanged ownership-mismatch branch does not require an additional mock in this work unit; retain its existing guard and security tests. No ownership check may be relaxed to make fixtures pass. Preserve the Hy old-factory runtime rejection.

Update both READMEs together: document exact-name activation, provider/root rename and restoration examples, inert unknown private root/override-provider data, strict active tuple/runtime/default validation, global duplicate rejection, whole-tuple fallback, and the need for a valid default key. Clarify that runtime/tuple-field renaming is not supported as disablement. Correct the current blanket “unknown fields fail” statement without implying arbitrary unknown default providers are allowed.

## Verification and handoff

Run focused new endpoint cases first, then `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_install_endpoints.py'` with the existing synthetic-home/stub conventions; run `git diff --check`. Verify only intended files changed and preserve the three preexisting untracked runner-handle-loss artifacts. No live endpoint probes are required. Controller conducts the independent review/fix loop and PR delivery.

No blocking questions. Future closeout should record `./scripts/sync-agent-tools.sh` and `./scripts/sync-codex-agent.sh`, since both install copies of this helper; execution requires live-deployment authorization. No skill sync is needed for this scope. Private renames become effective on subsequent loads/requests once the corrected helper is installed.
