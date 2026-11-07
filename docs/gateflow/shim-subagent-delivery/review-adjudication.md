# Controller review adjudication

Branch `fix/shim-subagent-message-delivery`, base `09337967910277785b82874326d7f49156c9395b`. Production shim SHA-256 `cd8e9f218c5a65d65bceff6ffac8b723c075913dad7ca08d999941ee34544dda`; source/routes/tests/probe hashes match controller-validation.json. No production code changed during the review loop.

## Independent routes and evidence

- Full review: Claude runtime `mimo-flash`, [artifact](../../reviews/code-review-20261107-215538-mimo-flash.md). Launched in parallel with the next full reviewer. Native session `4a28d2d2-e5fa-43db-ab9a-b51e38b4b15c`, exit 0. No runtime substitution, forced interruption or cancellation was used despite a long pause in streamed output.
- Full review: Claude runtime `ds-flash`, [artifact](../../reviews/code-review-20261107-213702-ds-flash.md), native session `031aec02-8ddf-4daf-ae22-daef101d878d`, exit 0. The configured Claude runtime was available, so no Codex backup route was used.
- Fix: Codex runtime `gpt-6-sol`, session `01a1b63b-a653-7aa2-925e-136b79769633`, exit 0; [redaction handoff](redaction-fix.md).
- Parallel affected-surface re-review: Claude `mimo-flash`, native session `4baec289-b3ec-46f6-bb64-c4f29e6e0003`, exit 0, [artifact](../../reviews/code-review-20261107-214551-mimo-flash-redaction-rereview.md); Claude `ds-flash`, native session `a7ebe526-0464-4103-868f-230924d1d4a1`, exit 0, [artifact](../../reviews/code-review-20261107-214607-ds-flash-redaction-rereview.md). Both independently verify the accepted finding fixed with delivery evidence intact. The former's filename/self-label was corrected by controller from ds-flash to the actual mimo-flash runner identity; judgment and check results were not changed.

## Findings and decisions

| Finding | Decision | Final state | Evidence / reason |
| --- | --- | --- | --- |
| ds-flash F1, low: unnecessary private project path/context in historical assistant excerpts | accepted | 已修复 | Two excerpts and the review's quotation explicitly redacted; original decoded-text hashes, source-file identity/hash, source lines, exact harmless task messages and failure semantics retained. gpt-6-sol performed fix. Both independent affected-surface reviewers passed; 7 protected code/driver hashes and all 23 manifest entries verified unchanged/matching. |
| mimo-flash F1, low: invented future top-level `agent_message_v2` should fail by a prefix check | rejected-with-reason | 未修复（已拒绝，无修复要求） | Installed 0.167.0 schema defines exact `agent_message`, not an `agent_message*` namespace. Reviewer explicitly confirms no such variant in the schema or actual wire and no current-version error. The approved plan targets exact `agent_message`; preserving non-target top-level items is an explicit invariant. A startswith heuristic would assign undocumented semantics to unrelated/future types and violate that invariant. README's “unknown agent content” is within its explicitly scoped Codex 0.167.0 adapter, not a promise to classify arbitrary future type names. Known-item unknown content already fails before upstream; tests prove it. No change or empty fix/re-review is warranted for the hypothetical top-level type. |

Mimo's doc-level flag inheritance question is nonblocking: this new switch intentionally has only a per-route opt-in, default false everywhere else. The plan, README and test state this behavior; no global flag contract is introduced. Prefix detection and global default inheritance are not added.

## Validation applicability and artifact integrity

- The 71 focused/related test results and both real-model native candidate runs apply to the unchanged production code. Controller independently audited native call order, three distinct A child turns, no parent shell, unknown-to-prompts fixture contents, B's sole child-owned cat call/output, and ingress/egress preservation. Both final-code and first successful candidate attempts, original failure baseline and setup failure are retained.
- Reviewers independently audited stored native evidence; their sandbox EPERM socket failures are environment/setup observations, not contrary functional results. Mimo records passing offline suites after allowing local binding. No additional inference is needed for evidence-only redaction.
- Controller changed gate-state documentation after the initial manifest was generated. Fix delegate disclosed the existing closeout checksum mismatch rather than overwriting it. Controller reconciled that documentation checksum, then both re-reviewers independently verified 23/23 entries from the correct cwd: `cd docs/gateflow/shim-subagent-delivery && shasum -a 256 -c evidence/sha256sums.txt`. Further final-closeout updates will refresh documentation checksums; native evidence hashes are unchanged.
- Redacted original text hashes were computed by the fixer from the existing evidence before replacement. Reviewers did not reopen user source sessions to recompute them; this is an explicit evidence-minimization limit. New native regression captures remain unredacted harmless fixtures and independently prove the fix.

## Residual risk classification

| Item | Classification | Owner / destination |
| --- | --- | --- |
| Current observed plaintext agent_message tasks and initial/followup/MESSAGE delivery | fixed in current slice | This adapter and native A/B evidence. |
| Genuine ciphertext in the same future string slot; new Codex schema types/fields; other providers or single-route env mode | assigned to later work unit | Maintainer compatibility work if those concrete environments are requested. No decryption, prefix-family or universal provider support is promised. True ciphertext cannot reliably be detected and might still yield task-invisible behavior; only structurally invalid known items are guaranteed sanitized 400. |
| Gateway internal exact drop function is unavailable | assigned to later work unit | Endpoint owner if finer internal attribution is needed. Present evidence locates the gateway compatibility boundary and proves the selected adapter restores tasks. |
| Existing failed/unloaded news task recovery | assigned to later work unit | Original parent thread after authorized deployment, using deliberate native followup/new task. This unit neither modifies the ledger nor recovers that business run. |
| Live deployment and service restart | requiring explicit user decision | User, after manual merge/approval, via sync-codex-agent.sh from approved checkout. Not a missing repository implementation gate. |
| Concurrent parent stream client-gone observation | assigned to later work unit | Runtime/transport diagnosis if it recurs; no retry/buffering changes added, all child finals and parent completion verified. |

No unresolved accepted production finding or new material blocker remains in the produced artifacts. Both full-review processes have now exited 0 and their complete artifacts were read and adjudicated. Review gate passes: all accepted findings are independently verified fixed, rejected suggestions have direct reasons, validation remains applicable, and residuals are classified. Current gate / next entry: ready-to-open-draft-PR, then necessary commit/push, draft PR creation, controller delivery verification, draft-PR-pass and final closeout.
