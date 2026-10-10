# S1 code review: controller decision

- Gate: code review / fix / re-review; work unit: agent-sandbox-dangling-symlinks.
- Scope: all branch/workspace changes relative to main d51765b; five frozen product files, accepted plan and S1 evidence.
- Artifact: docs/gateflow/agent-sandbox-dangling-symlinks/code-review.md.
- Independent reviews: [MiMo/Codex](../../reviews/code-review-20261010-184718.md) and [DS Flash/Claude](../../reviews/code-review-20261010-184719.md). Both actual runner/runtime exits=0; MiMo 757.407743s, DS 533.020363s. Native usage/log locations in review-statistics.json.
- Result: both found no material findings. Source hashes rechecked by controller unchanged. PASS; no accepted unfixed finding, blocking question or unclassified risk.
- Fix/re-review: no product fix required; no separate corrective re-review required. Prior accepted plan findings remain 已修复 and independently verified.

## Adjudication and validation

Controller inspected actual kernel-final stderr (52/52, zero skips), per-fixture raw argv/exit/stdout/stderr for dangling boundary, both materialization controls and original 4108-entry case; checked first-adapter hash matches via retained evidence. Durable extracted evidence: evidence/controller-s1-kernel-checks.json. DS independently reran 52/52 kernel tests in own scratch and focused/launcher/preflight tests. MiMo traced the complete call chain and all nine retained kernel cases. Neither verdict relies only on Agent self-report.

DS question 1: rejected-with-reason as a current change requirement. Added-ancestor hardlink failures retain original dangling link/raw target, actual offender entry and discovery directory; this is the accepted plan's origin context and locates the failure. Optional origin-field naming cleanup is assigned to later work unit (maintainer, diagnostics work), not a blocker or new S1 requirement.

DS question 2: assigned to later work unit (maintainer, synthetic harness/platform analysis). Original profile-hardlink fixture is unchanged and contains no missing metadata; /tmp spelling passes original assertions, /private/tmp spelling produces EPERM. Initial failure remains retained and documented. No uniform spelling behavior claim is made.

DS ordinary shell errors were recovered, actual runtime exit=0 and required evidence/report complete; needs_review is not mechanical Agent rejection. No lost/failed kernel result was used as passing evidence.

## Classified residuals and docs

- fixed in current slice: missing ENOENT proof ambiguity, non-absence/capability errors, missing ancestor/cascade/conflict handling and their documented support limits.
- assigned to later work unit: other Python/macOS stack validation (maintainer, environment validation); external unsandboxed mutation, unknown copies or snapshot support (caller/maintainer, separate confirmed goal); TMPDIR harness sensitivity and optional origin naming as above.
- requiring explicit user decision: merge/live deployment and caller's live revalidation. No real provider task or caller job was run; unchanged runtime/provider paths plus focused and synthetic lifecycle tests suffice for S1.
- Docs: README EN/ZH and Agent-facing advanced reference match implemented conservative semantics. Plan pointer-only correction does not alter accepted contract.
- Next gate: accepted slice commit, then aggregate deepreview.
