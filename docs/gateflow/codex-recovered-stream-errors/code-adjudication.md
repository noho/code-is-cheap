# Code adjudication: codex-recovered-stream-errors / S1

## Decisions

- MiMo 001: accepted, 未修复 (contract/evidence and negative test gap). Parser-rejected malformed start rows are already fatal before proof dispatch; they cannot be recovered. Counter multiplicity concerns parser-accepted start events, including invalid proof shapes. Do not move counting ahead of strict parsing or add a generic validator. GPT-6 Sol shall clarify this distinction in task evidence and cover malformed raw duplicate starts; no new protocol acceptance or behavior is required.
- DS nonblocking unreachable outside-turn reason: rejected-with-reason. Earlier start ordinal fence rejects this case conservatively; retaining planned reason priority has no acceptance effect. No refactor needed.
- Both reviewers completed native/runner0. Intermediate corrected command/probe failures do not impair their direct source/test evidence. Logs and real statistics retained.

## Next gate

S1 fix -> independent dual re-review. No accepted slice yet.

## Residual classifications

- Counter wording/test mismatch: fixed in current slice after independent re-review.
- Strict supported-frame false negatives and general collector protocol validation: assigned to later work unit; runner maintainer, separately confirmed protocol work.
- Original optional/business checks: requiring explicit caller decision; caller owns original workflow, outside this structural fix.
- Live deployment/merge/restoration: requiring explicit user decision; no current permission. User merges draft; controller deploys only when separately authorized; caller restores task.

## Final S1 loop acceptance

Independent re-reviews code-review-20261011-050623.md (MiMo) and code-review-20261011-050624.md (DS Flash) both confirm MiMo001 accepted / 已修复, with no new material findings. Root read both complete artifacts, fixed test/assertions, append-only adjudication, actual fix full49 stderr, protected source snapshots and unchanged final product hashes. Production parsing/counting did not change; four raw malformed duplicate-start negatives prove fatal parser errors and unrecovered notices. Both native/runner0; recovered ordinary tool issues do not invalidate completed evidence. No accepted unresolved finding remains.

DS optional malformed sole/first start test gap: assigned to later work unit, runner/test maintainer / separately confirmed optional protocol test coverage. Nonblocking: existing parser-before-dispatch fatal path plus the four direct duplicate controls already prove no recovery when parsing fails; missing/invalid start fence also tested. No additional S1 expansion needed.

Current live-runner limitation: requiring explicit user decision, user/controller / later authorized rollout; no live test or deployment in this task. General variants/validation and original optional/business checks retain earlier owner/destination classifications.

Decision: S1 code review/fix/re-review PASS; proceed to accepted slice checkpoint then aggregate deepreview. Final task closeout not yet passed.
