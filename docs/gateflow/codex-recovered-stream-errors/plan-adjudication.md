# Plan review adjudication: codex-recovered-stream-errors

- Gate: plan review -> fix -> re-review (pending).
- Valid independent reviews: docs/reviews/plan-review-20261011-033016.md (DS-Flash/Claude); docs/reviews/plan-review-20261011-034538.md (MiMo/Codex retry 1). Both actual native/runner exit 0, successful terminal and complete artifacts.
- Original MiMo report docs/reviews/plan-review-20261011-033015.md is retained UNACCEPTED: execution was interrupted by explicit authorization, managed exit 130, no native terminal. It is not review-pass evidence or an input to the independent retry. First attempt + exactly one repair retry recorded; no further automatic repair retry.
- First-call stop authorization: user delegation message; evidence/plan-review-mimo-attempt-1.json. Supplied caller decision path is an authorization reference, not read business evidence.

## Decisions

| ID/source | Adjudication | Current fix status | Required fix / validation |
| --- | --- | --- | --- |
| DS-1: partial existing regression coverage | accepted | 已修复 | Add full tests/test_agent_run_results.py offline run, beyond focused new-case execution; share-path regression risk justifies coverage. |
| MiMo-01: exact frame proof assumption | accepted as clarification (option a) | 已修复 | Explicitly choose intentionally conservative supported-shape proof, not universal protocol invariants; unknown extra/preamble shapes remain refused recovery only, unchanged ordinary streams. Tests for each frame fence and classified false negatives; no generic validator redesign. |
| MiMo-02: notice -> final -> notice -> terminal | accepted | 已修复 | Add mixed-order negative asserting late notice line retained in errors, rejected/exit1; last candidate drives proof. |
| MiMo-03: report contract | accepted | 已修复 | Freeze existing full key set and schema/source/result_status/tool_evidence_scope values on recovery/proof failure/Claude controls; no proof/model/route fields. |
| Controller-01: recovered diagnostic hidden by existing full warning list | accepted | 已修复 | Independently reproduced in evidence/controller-diagnostic-cap-check.json: 20 old warnings +25 notices => count45/display20/no notice. Reserve one display slot for first candidate when category already full, without subtracting counts; same bounded guarantee for failed candidates. Add saturation tests. |

Strict shape decision follows confirmed goal: only known notice and reliable success evidence supported; unobserved protocol frames cannot be assumed harmless. This does not turn the observed shapes into a universal protocol contract or change baseline acceptance of streams without a candidate. Bounded ASCII attempts 1..5 are an explicit supported grammar; only 1/5 was observed, 2..5 synthetic. No recovery follows from the digit itself. Raw event JSON remains in original logs; parsed original message and physical line suffice for bounded diagnostics. Full-key tests constrain the existing report rather than adding fields.

## Scope / risk / next gate

Only plan.md and plan-fix-01.md may be edited by GPT-6 Sol for this gate. No product code until independent re-review accepts the revised plan. Original optional checks remain unrerun and task correctness remains not_assessed.
- Current classification/proof/visibility/test gaps: fixed in current slice, pending implementation and reviews; controller/S1 owner.
- Unobserved wording, added metadata/preambles, resume stream variants and final-before-notice evidence: assigned to later evidence-backed protocol work unit; runner maintainer; conservative rejection now.
- Original business correctness/optional checks: outside confirmed scope; caller retains original workflow ownership.
- Merge/live deployment: requiring explicit user decision; user/caller after draft PR final closeout.
No new blocking scope question. All accepted findings must be fixed and re-reviewed; gate not yet passed.

## Re-review clarification / DS new candidate decision

DS re-review docs/reviews/plan-review-20261011-040833.md independently verifies all five document fixes. New-1 is `rejected-with-reason` as a required behavioral change: D2's named proof-frame table and D3's exhaustive predicates are the recovery contract; the context explicitly says this is not a generic schema validator. The broad phrase “unobserved envelopes” refers to shapes of those named proof-bearing frames. It does not require a whitelist for every unrelated valid event kind. Adding such a whitelist would broaden validation beyond the confirmed minimum. This controller clarification resolves the report's permitted “明确裁决” path and is binding in implementation handoff.

Concrete boundary: shapes of thread/turn start, selected final and success terminal must meet the exact supported proof predicates; notice envelope must meet D1. Post-start non-proof event kinds retain baseline handling and are not additional recovery fences. Existing arbitrary top-level error, parse/terminal/process/selected-check failures remain authoritative. This does not assert unknown event semantics are safe; generic validation of such events is assigned to a separately confirmed runner/protocol work unit, owner runner maintainer. No future event kind is newly recognized by this task, and no existing error is downgraded by that clarification. Current defects in the known retry classification remain required S1 work.

DS O1 is resolved explicitly without a new design: increment start counters on EVERY thread.started/turn.started event, including invalid-shape/duplicate events; only validity proof is conditional. A valid followed by malformed duplicate cannot prove single execution. This follows D2's whole-stream counters/D3's duplicate-start condition. The implementation prompt will state it directly; no valid-only counting interpretation is authorized.

Re-review remains open pending actual MiMo completion. A same-family retry notice has appeared in that owned review log with subsequent tool activity; do not classify the review solely from this intermediate event. Collect the true terminal and native exit before any acceptance decision.

## Final plan-loop acceptance

Both independent re-reviews verify all five accepted findings 已修复 at plan-document level: plan-review-20261011-040832.md and plan-review-20261011-040833.md. DS New-1/O1 adjudicated above, with no accepted unresolved finding. Root directly read both reports, revised exact predicates, saturated arithmetic evidence and contract fixtures; no blocking scope question or unclassified risk remains.

MiMo actual native0/completed/turn.completed but old live collector returned1/rejected solely for exact supported reconnect at line69. Later final line81, terminal82, full valid unique starts, native/precollection0, no other hard errors prove recovery; evidence/plan-rereview-mimo-recovery.json records the actual report plus private proof simulation. Root accepts the review on direct evidence, preserving actual runner rejection and all statistics. This is the defect being fixed, not a new failed review or retry. Unavailable MCP channel and recovered wc typo did not affect local evidence or complete report; neither is the sole error or required external source. No current-peer conclusions were read in recorded tool outputs.

Decision: plan review/fix/re-review PASS; proceed immediately to accepted plan commit, then S1 implementation. Production behavior not yet implemented/validated. Existing residual classifications apply.
