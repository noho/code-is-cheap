# Final combined review adjudication

Current gate: fix / affected re-review. No release closeout or deployment pass is claimed yet.

Both independent full reviews actually exited 0 on the same `review-freeze-v1.json` point (9 source + 472 evidence files). [DS Flash / Claude](../../reviews/code-review-20261108-012340-ds-flash-all-shim-providers.md), session `2f36e768-7099-48f0-b1fb-9eea7a2b0936`, found two low items and no blocker. [MiMo Flash / Claude](../../reviews/code-review-20261108-014400-mimo-flash-all-shim-providers.md), session `be25719c-fee7-4216-a442-44a1c15c604d`, found the same README drift plus a low logging gap and no blocker. Each independently verified all 163 checks, current native aggregates, bounded reuse, old failures and the freeze. Neither read the other's conclusion; no runtime fallback was needed.

| Finding | Decision / state | Evidence and destination |
| --- | --- | --- |
| DS-1 + MiMo-1: stale bilingual README says additional_tools is unsupported | accepted; candidate integrated, pending affected re-review | Actual response-only implementation and 16 accepted MiMo requests use immediate additional_tools. Correct both languages while retaining Kimi top-only flatten. Severity disagreement does not alter the required fix. |
| DS-2: probe observer blocks GET/empty/non-JSON/non-object requests | accepted; candidate integrated, pending affected re-review | Reproduced pre-fix before original_open; only validation harness, no accepted native sample triggered it. Safely bypass observer parsing, retain production transforms and record separate minimal metadata. HEAD is not implemented by the production handler and remains its existing 501; this fix does not introduce a new HTTP capability. |
| MiMo-2: active-map success bypasses the standard status/model/rewrite request log | accepted; gpt-6-sol logging-only fix pending | Restore existing safe request diagnostic fields for active paths without changing request/response routing, model arguments, framing or retry behavior. Preserve no prompt/args/credentials logging. |

DS-1/2 candidate preparation ran in an isolated worktree while MiMo was still reviewing the original frozen point; the original nine source hashes remained unchanged throughout that review. Gpt-6-sol session `01a1b718-c2e3-7860-80c6-1023f68afd77` exited 0 with [candidate validation](review-fix-validation.md): 78 affected tests pass, four before-fix failures reproduced, four normal observer equivalence cases match. After **both** full reviewers exited, controller copied exactly the four authored files plus new validation artifacts; [integration receipt](controller-candidate-integration.json). No production/helper/routes/auditor change occurred in this first fix step. Original captures, verdicts, reports and v1 freeze stay immutable.

MiMo open question about file-level defaults is resolved: the three new compatibility flags are intentionally **route-level only**, with no file-wide/environment inheritance. This is the accepted opt-in boundary, explicitly tested by loader tests. Existing legacy flags retain their historical inheritance. Clarify this distinction in README; do not add a global fallback that changes the accepted scope.

MiMo's A4/A3 regression-pinning residual is accepted as a focused validation improvement: pin the real accepted A4 and incomplete A3 verdicts in the offline suite, alongside existing mutation tests. It does not require more vendor inference. The logging fix delegate owns this small addition.

Remaining review residuals are classified, not waived current defects:

- Unchanged-path/native-source reuse remains bounded to the exact hashes/flags/catalogs/settings in the applicability records; DS retains its conditional legacy assertions. Owner controller for current closeout, provider maintainers for future version/backend changes.
- Real ciphertext, repeated selected callable declarations, future descriptor containers and compressed active responses require new observed protocol evidence and a bounded compatibility work unit. Existing immediate indices are already supported; a review's shorthand about a new index being outside scope does not apply to arbitrary indices within the two accepted containers. Owner shim/protocol maintainers.
- Empty `data:` heartbeats are outside the current Responses-JSON event contract; comment heartbeats work. No such empty data event exists in accepted captures. Per-event non-target byte preservation is established by the same parser's tests, not a claim that every hidden-reasoning byte was saved. Owner protocol maintainers on a concrete future counterexample.
- Default compound `all` and v1 prompts retain historical behavior; current user-required regression commands use explicit short A/B scenarios. A future compound-v2 diagnostic update belongs to probe maintenance; current native task delivery is verified without inventing an extra mailbox edge after completion.
- Full top-level tool descriptors in older captures are retained for verification, with no private connection/credential or hidden reasoning copied. New source projections minimize unrelated content. The controller's JSON secret-field screen found no direct private credential values; this is not an exhaustive secret-attestation claim.
- Live source/routes remain unsynchronized. User owns manual merge and subsequent explicit deployment authorization; the original business-thread callback stays withheld until live sync. Business recovery remains a separate deliberate action.

Next entry: required gpt-6-sol logging/docs/regression fix, then two independent **affected-surface** re-reviews of the final combined point. Reuse the completed full reviews for unchanged production/protocol/evidence scope; do not repeat all-nine vendor calls or a full review solely for diagnostic/doc changes. Commit/push/update draft PR and delivery/final closeout follow only after this loop passes.

## Fix handoff — implemented, affected re-review pending

Gpt-6-sol logging/docs/regression session `01a1b727-b32d-7a93-977c-eb1cceb9bd83` actually exited 0. [review-logging-fix-validation.md](review-logging-fix-validation.md) records final helper `55a5bd5b5e120cac648d9ad86c366430a9a535bf79d796cf58a79b44ffbb9b9a`, 86 current affected tests and 90 bounded unchanged-path checks (176 applicable). The standard diagnostic block is moved intact before active-map relay; `_summary` safely handles non-array tools. Excluding only that diagnostic block and its summary owner, the Handler AST is identical to a6246; all other module AST and globals are unchanged. Real active Kimi/MiMo loopback requests, bytes/headers, auth/model transforms and gated first-event timing match the a6246 baseline; new logs omit synthetic prompt/args/header/auth/private URL/session markers.

README now also explains the intentional route-only defaults. Real A4/A3 verdicts and A4 receipt/map counterexamples are pinned without modifying captures. Observer-fix and logging-fix reports retain their own staged source hashes; neither claims fresh inference on final helper 55a5. Nine-route applicability is the original accepted native data plus the explicitly proved observer/diagnostic-only equivalence chain. There were no new vendor calls, policy/catalog/routing changes or live actions.

All three logical findings are now **implemented / pending independent affected re-review**, not yet closed by controller assumption. Freeze v2 and ask both repository review routes to examine only actual fixes/interactions and reuse their completed full review for unchanged scope. Current next entry: affected re-review.

## Affected re-review pass / loop closed

Both independent affected reviewers actually exited 0 and confirm all three logical findings **已修复**, with no new material finding:

- [DS Flash / Claude re-review](../../reviews/code-rereview-20261108-021422-ds-flash-all-shim-providers.md), session `53b81b71-65cb-4060-b775-4937204e9c3a`, PASS.
- [MiMo Flash / Claude re-review](../../reviews/code-rereview-20261108-023108-mimo-flash-all-shim-providers.md), session `742979e7-e041-46d2-8914-3e553f0b1498`, PASS.

They independently verified v2 hashes, the diagnostics-only delta, observer transparency, no sensitive logs, normal native-record equivalence and real A4/A3 protections. Each ran the final 86 tests and verified bounded 90-check reuse; controller separately ran 86, [record](controller-final-offline-validation.json). MiMo checked all 536 frozen source/evidence files; DS checked the nine source/test hashes and relevant archived inputs. No new inference was needed for diagnostic/doc/harness fixes. Intentional route-only flag behavior is documented; HEAD retains the original 501. Historical stage scope scripts are checkpoint-specific, and their stored results are not relabeled as fresh checks on later workflow-record edits.

Controller accepts both verdicts, confirms source remains at helper `55a5bd5b…` / freeze v2, and closes the review loop. Shared README, observer and standard-log findings are **已修复**; validation pinning is implemented; no unresolved accepted blocker or unclassified residual remains. Remaining owners/boundaries above are unchanged. Next entry: ready-to-update-draft-PR, commit/push, then controller delivery verification and final closeout. This does not authorize merge, live sync/restart or the withheld business-thread callback.
