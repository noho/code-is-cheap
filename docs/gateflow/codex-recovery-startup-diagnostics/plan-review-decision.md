# Plan review controller adjudication

Gate: plan review → fix → re-review. Scope: confirmed goal and one S1, product unchanged.

Independent reports: `docs/reviews/plan-review-20261012-015140.md` (MiMo/Codex) and `docs/reviews/plan-review-20261012-015142.md` (DS Flash/Claude). Both actual native/runner exits 0, valid final and terminal. Frozen input hashes checked unchanged. Full call statistics are in evidence/dispatch-statistics.json; original logs retained at listed private paths.

## Findings and decisions

- MiMo F1: **accepted / 未修复** at initial review. Add the concrete supported-gap + expected failed command + recovered notice case (counts 0/2/1, completed/needs_review/runner0). This protects existing ordinary-tool-failure behavior, not a new goal. GPT-6 Sol assigned to plan-only fix, followed by independent dual re-review.
- MiMo F2: **rejected-with-reason**. Restricting the diagnostic to individually observed directory families or a particular temporary root conflates variable config location with event identity. Confirmed goal permits supported path variations, and the reviewed contract anchors the complete exact warning and envelope while accepting only lexical absolute config.toml paths without traversal. The actual ephemeral /private/var/folders path and actual id `item_0` match. A grammar-valid unobserved location does not turn a different message/event into an allowed diagnostic. No general compatibility or event exemption is added. Future text/envelope and unsupported path grammar remain outside this exception.
- DS Q1 and MiMo identity/native path questions: **resolved** before implementation by root's original line-2 envelope/text/path comparison, recorded in `evidence/pre-implementation-check.json`. No caller business text exported or external access granted.
- DS Q2 README decision: **resolved** by direct root spot-check of English 389–419 and Chinese 363–387. Existing same-run completion/selected checks, needs_review and diagnostics language remains correct; no README change needed.

## Runtime/tool adjudication

MiMo needs_review contains three failed exploratory Python -c commands due to quoting and one deliberately rejected baseline collector replay. Corrected commands/baseline tests and direct lifecycle probes completed; these failures neither invalidate the structural review nor prove product defects. The report does not depend on the failed quoting probes alone; unchanged source and successful fixture replay establish the material claims. Raw anomalies and statistics remain retained. DS result passed with only known model-metadata stderr warning.

## Risks and gate decision

F1 fix/re-review pending, so plan gate not yet passed. F2 does not require scope expansion or another user confirmation. Supported startup grammar/future formats: collector maintenance later work unit. Original business/check acceptance: caller owner, outside scope. Live deployment/network forced interruption: user/deployment owner, later authorization. No unclassified residual risk or blocking open question. Next entry: plan fix by GPT-6 Sol, then two-route planreview.

## Final plan loop disposition

GPT-6 Sol plan fix completed (plan-fix.md; native/runner0/passed). Fresh independent re-reviews: `docs/reviews/plan-review-20261012-021355.md` (MiMo, pass) and `docs/reviews/plan-review-20261012-021356.md` (DS, pass-with-risks). F1 **accepted / 已修复**, verified by both; no new material finding. Input hashes unchanged after both closures. MiMo's two preliminary offline harness failures omitted existing proof conditions and were corrected before the final 30-recognizer/9-lifecycle assertions; ordinary tool anomalies do not invalidate the result. DS result passed; no unresolved execution failure.

DS's nonblocking saved-final question is resolved for the implementation handoff: pass an explicit fresh --last-message file when checking saved final, rather than relying on inert fake FINAL without the option. This realizes the existing intent; it does not alter the contract or acceptance criteria. The ≤1 gap bound is intentionally conservative and future multi-warning formats remain later maintenance work. Risks retain the owner/destination above. **Plan loop pass**, no further fix or re-review needed. Next entry: accepted plan commit, then S1 implementation.
