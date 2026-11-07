# Runtime rename-disable controller

## Scope and preflight

User reports override.ds-flash.codex renamed to codex-bak still fails. Extend the previously confirmed arbitrary-name disablement to private override runtime names: recognized exact names activate; unknown names and their contents are inert; complete defaults/factory provide fallback; valid sibling overrides remain active; exact-name restore validates and reactivates. No suffix matching or connection-field rename support. Preserve private default/factory strictness, active tuple/key validation, file permissions/ownership/type and duplicate JSON checks. A private override provider with no active runtimes means no overrides; invalid container types still fail.

Main is f5e1676 (PR67 merged). Created fix/endpoint-runtime-rename-disable before edits. Three original untracked runner-handle-loss files remain excluded. Baseline fake-home probes with codex-bak and arbitrary-runtime both returned1 before any key requirement. Source root cause: validate_document filters private roots/providers but still rejects unknown runtime names and merges runtime maps without a runtime-selection step. Existing tests/README explicitly retain that prior limitation and must be updated with the new contract, not merely appended around it.

AGENTS.md requires Sol plan/implementation/fixes and independent MiMo Claude plus DS Claude reviews (allowed DS Codex fallback). Continue that workflow. No significant architecture decision or migration requires a separate plan review: this is the same schema owner and user-requested selection rule applied one level deeper. No model capability work or vendor inference tests. No unrelated owner-UID coverage expansion. Private file content will remain unchanged through authorized post-test/review sync of both installed helpers.

Current gate: plan. Sol native task launched with explicit cwd; receipt /private/tmp/endpoint-runtime-rename/plan.jsonl. Controller owns plan check, review adjudication, PR and authorized live sync. Do not deploy while validation/review remain pending.

## Plan check passed

Sol plan native/outer0, 82.879s; controller read plan.md and accepts the narrow four-file extension. Empty private override provider maps (including all-filtered maps) mean no active overrides; default/factory empty-map rejection stays strict. Update the old unknown-Hy-override-runtime test to expect filtering while retaining unknown-default-runtime rejection. This is the intended contract change, not a test waiver. No blocking question or separate architecture review applies. Baseline two fake-home probes returned1 for codex-bak/arbitrary-runtime as expected before implementation.

Current gate: implementation/validation. Sol will implement and test using fake settings only. Reviewer setup may need a staged source helper on PATH because the old live helper rejects the user's codex-bak before any provider launch; staging is read-only with respect to the actual private file and does not deploy the fix. No live code or config writes until validation/reviews pass.

## Implementation validation passed / full review

Sol native/outer0, 244.234s; controller read the complete four-file source/test/doc diff and implementation.md. Eight focused tests0 (7.281s), all37 endpoint/install tests0 (35.340s), diff check0; actual results in test-results.json. No failures or known implementation issues. Existing conflicting unknown-runtime expectations were deliberately aligned with the accepted contract; active/default/factory/security assertions remain strict. All four product files frozen in review-input.json with retrievable source archive and complete private diff.

Actual private inspection revealed mode0600 and ds-flash runtime names claude/codex-bak; no values printed or file writes. Old installed parsing blocks reviewer launch before provider selection, so staged source helper/factory under /private/tmp/endpoint-runtime-rename/review-bin are first on each Claude review PATH. Staged global --check0 confirms the desired parsing with existing data, without deployment or inference. Both installed/live helper copies remain untouched pending review.

Current gate: independent full code review. Dispatch MiMo Claude and DS Claude in parallel against the frozen four-file change and relevant existing consumers, no peer reports/controller verdicts supplied. DS Codex backup only after actual primary unavailability. No live sync before review/fix loop passes.

## Full review adjudication passed

Both required primary Claude reviewers completed native/outer0 with actual durable reports: MiMo docs/reviews/code-review-20261107-104533.md (684.944s), DS docs/reviews/code-review-20261107-104313.md (584.824s). No backup route was required. Controller read both reports, the full four-file diff/new cases and actual validation; all four source hashes match the frozen snapshot. Both reports find no substantive issue, no open question or accepted finding remains. No empty fix/re-review loop is needed.

Both reviewers independently passed8 focused cases and all37 endpoint tests; their initial localhost socket-bind sandbox failures and correction to an authorized non-sandbox local-fixture run are retained and not counted as passing runs. DS also retained a probe expectation/harness correction; no product failure was concealed. Source remained frozen throughout. The required assertion is no mutation during validation/load plus stable effective snapshots; loader deep-copy semantics are unchanged. No extra public mutation-isolation contract is introduced for internal returned views.

Residuals are classified: installed-copy/service integration is covered by the next authorized sync/verification (controller/operator); old-factory filtering is explicit contract with synthetic old-schema coverage and both factories updated together; full-repository/vendor inference coverage remains existing testing policy/operator scope; generic empty-name probing is supporting reviewer evidence, not a mandatory separate test. Existing owner-UID policy expansion remains outside scope. No code blocker, required user decision or unclassified risk remains.

Current gate: ready-to-open-draft-PR; next commit/push/create draft PR, immutable delivery check, then final closeout including authorized sync. No associated issue; user merges manually. Product version stays exactly the reviewed four files.
