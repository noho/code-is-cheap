# Provider registry review adjudication

- Branch: `fix/shared-provider-resume`
- Base: `main` at `4aa780f`
- Initial reviews: [Kimi](code-review-20260925-083810.md), [MiMo](code-review-20260925-084205.md)
- Re-reviews: [MiMo](code-review-20260925-090337.md), [Kimi](code-review-20260925-090353.md)

## Decisions

| Finding | Decision | Evidence and disposition |
| --- | --- | --- |
| Fresh home with no base config stops sync | Accepted, fixed | Sync now creates a private `0600` base; fresh-home subprocess test and both re-reviews pass. |
| New composer crashes on installed old-format cards | Accepted, fixed | Legacy card route is retained with a warning until card sync; real old `mimo-fast` card and test pass. |
| Old `glm` / `mimo` IDs cannot identify a gateway variant | Deferred, project maintainer owns compatibility | Historical IDs are ambiguous. Ordinary IDs retain their old ordinary routes; new variant sessions use unique IDs. Reviewer impact claim depended on an unobserved bootstrap request. The ambiguity is documented; no silent historical migration is attempted. |
| Comment marker could be lost by an external config rewrite | Deferred, project maintainer owns observation | No rewrite that strips the marker was observed. Current sync fails closed if ownership cannot be established. Check after a desktop app config rewrite before changing the ownership strategy. |
| Symlink base replacement and concurrent write gap | Symlink accepted and fixed; concurrency deferred | Symlink is rejected and tested. A content/existence recheck narrows the write race; external writers do not participate in a shared lock. |
| Removed providers remain in composed app homes | Deferred, project maintainer owns future removal | No provider was removed from the shared registry in this change. Automatic deletion could erase an app-local provider without ownership metadata. |
| Missing failure-path and cross-file contract tests | Accepted, fixed in scope | Nine tests cover fresh sync, malformed and empty tables, conflicts, broken markers, symlinks, desktop migration, and registry/card/shim/launcher port and key agreement. CI and an injected concurrent-write test remain follow-up risks. |
| Malformed registry and lost direct fallback URLs | Accepted, fixed | Invalid provider values are rejected without writing; all shim-backed direct URLs are retained in registry comments. |
| Re-review: empty provider table, scalar base key, missing desktop base, inverted marker error | Accepted, fixed | Added strict validation and actionable errors; all four negative paths are covered by the nine-test suite. |

## Live validation

- A copied Kimi-origin session failed to resume with `Model provider kimi not found` before registry sync and entered the GPT-6-Sol TUI after sync.
- The installed shared home resumed the same Kimi-origin session and selected GPT-6-Sol without sending a new prompt.
- The installed `mimo-fast` launcher entered the TUI with `mimo-v2.6-pro-ultraspeed`; its empty smoke-test session was deleted.
- The live base retained every non-provider configuration value, kept mode `0600`, and a second registry sync reported `already current`.
- `python3 -m unittest discover -s tests -v`: 9 passed. `bash -n`, `py_compile`, and `git diff --check` passed.

## Residual risk

- Actual response routing after a continued prompt was not exercised; bootstrap and selected-model display were verified.
- Old variant sessions recorded under shared `glm` / `mimo` IDs cannot be mapped to their original gateway variant from the recorded ID alone.
- A future desktop config serializer might remove comment ownership markers; sync then stops on an ownership conflict.
- Concurrent writers can still race between the final content check and atomic replacement; no shared lock exists.
- Composed app homes retain provider sections removed from the shared base; no provider removal occurs in this change.
