# Aggregate deepreview adjudication

Gate: aggregate deepreview. Work unit: codex-recovered-stream-errors.
Reviewed baseline `20fc6c37751836329143567c166990bdffa9de3c`, head `8947d3e2949d9ae2b31a37457f93ec4a77f2d1e2`. Five frozen product hashes remain identical. Reports: `docs/reviews/code-review-20261011-051845.md` (MiMo), `docs/reviews/code-review-20261011-051846.md` (DS Flash).

## Controller decision

PASS. Both independent reports found no material product finding. No fix is required at this gate; no accepted unresolved finding remains. Direct source/runner-chain checks and actual full 49-test executions corroborate the analysis. This accepts the review analyses, not an assertion that both installed-runner mechanical checks passed.

MiMo actual native exit 0, runner exit 1, rejected, final present and terminal completed; 149 strict events, unique starts 1/2, sole top-level error at line 69 (`idle timeout waiting for SSE`), selected final 148, terminal 149, subsequent commands and full49 test exit0 at event90. The controller independently accepts the completed review artifact on these actual evidence and source checks. That transport wording remains UNSUPPORTED by the product rule and remains rejected; no normalization, recovery-pass claim or production matcher expansion is made. Actual flags/logs/1392.307801-second wall time and usage remain in statistics. No retry or interruption was performed. Evidence: `evidence/aggregate-mimo-controls.json`.

DS Flash actual native/runner0, completed, needs_review (one tool anomaly and one visibility warning), full49 independently passed. Root read the recorded outputs. A private probe printing mistake was corrected; the direct collector CLI exited1 while its report preserved native runner code7. This is not a claim that this direct CLI observed the outer shell runner exit7. Existing real wrapper propagation and full tests cover the latter. Evidence: `evidence/aggregate-ds-flash-controls.json`.

DS report's blanket claim of no prior report reads is qualified: an rg command incidentally returned snippets from four completed S1 reports. No current aggregate peer/unaccepted conclusions appeared in the inspected output; conclusions are independently supported by direct code/tests. The shared prompt's Codex tool terminology for Claude was a controller wording error; native Bash/Read/Write remained within scope, and future PR-review prompt wording is corrected. Raw report remains immutable.

## Validation and scope

Both current independent full49 runs passed; source/diff/hashes and strongest proof/count/boundary failure cases were checked. Original structural replay remains the narrowly scoped earlier evidence only; original optional/business checks are not claimed. No product files changed during aggregate review. Diagnostic workspace-routing work has its own independent baseline/worktree and no files in this diff.

## Remaining risk classification

| Risk / excluded area | Classification | Owner / destination |
| --- | --- | --- |
| Unsupported wording including idle-SSE; changed budgets/proof frames/resume variants | Assigned to later work unit | Runner maintainer, separately confirmed evidence-backed protocol support |
| Generic event validation beyond supported recovery proof | Assigned to later work unit | Runner maintainer, separate validator work |
| Optional protocol test gaps outside current proof | Assigned to later work unit | Test maintainer, optional protocol coverage |
| Original optional/canary/artifact/business checks | Requiring explicit caller decision | Original caller workflow |
| Merge/live deployment/task restoration | Requiring explicit later authorization | User/caller rollout and restoration |

Docs decision: the accepted README/skill classification wording is unchanged. Next gate: accepted deepreview commit, then ready-to-open-draft-PR. PR review is still required after creation.
