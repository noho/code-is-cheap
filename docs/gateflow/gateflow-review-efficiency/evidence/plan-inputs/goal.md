# Goal confirmation — Gateflow review efficiency

Status: confirmed by the authorized controller on 2026-10-12T20:05:30.032009+08:00; plan authorized.

## Work unit and baseline

- Work unit: `gateflow-review-efficiency`, workflow skill text optimization.
- Baseline: `83e534f71adfdd4d8a0c353642a37dd364045504` (`main` / fetched `origin/main`), includes merged PR55.
- Work branch: `feat/gateflow-review-efficiency`; original worktree clean.
- Preflight facts: [preflight.json](preflight.json).

## Goal and motivation

Implement the user's four approved efficiency improvements as concise Agent-facing instructions:

1. Separate slice correctness/contract/test review, aggregate interaction/whole-goal review, and actual PR delivery/version/CI/change review. Require substantive independent checks at each gate, while citing applicable earlier evidence; a single unchanged slice must not automatically receive two more comprehensive reviews of the same scope.
2. Reuse actual validation across gates after checking code, dependencies, configuration and relevant environment. Revalidate affected parts after a fix; full reruns require actual impact or mandatory project checks. Reviewers may independently investigate concrete doubts, but cannot substitute an unsupported earlier "pass" for their own judgment.
3. At every review loop, record pass and advance to the corresponding accepted commit when no accepted finding requires a fix and all other release conditions hold. Execute fix/re-review only for an actual fix; unresolved blockers, needs-more-evidence and insufficient release evidence continue to block. Keep Gate Order and state expressions consistent.
4. Permit traceable references to unchanged confirmed scope, plan and validation facts. The current artifact records current changes, decisions, evidence and next entry; final closeout summarizes actual results. Required information must remain accessible and auditable without repeated copying.

The direct text evidence below supports the work unit. This task reduces prescribed duplicate effort; it does not claim measured wall-clock or token improvement without measurements.

## Direct source evidence

All locations refer to the baseline above:

- `skills/gateflow/SKILL.md:64-112`: Gate Order and the repeated slice sequence list fix/re-review unconditionally; `:319-328` explicitly recognizes no-fix pass only for PR review.
- `skills/gateflow/SKILL.md:94,236-238`: all three code-related gates use Deepreview; reuse is described specifically for re-review, without clear distinct responsibilities or cross-gate validation reuse.
- `skills/gateflow/SKILL.md:264-277`: generic artifact requirements can be interpreted as repeating all facts in each artifact.
- `skills/deepreview/SKILL.md:88-126` and `## PR Review Mode`: PR review uses the same comprehensive method and complete PR diff scope; it needs a scoped Gateflow interpretation without weakening standalone Deepreview or PR OID/snapshot verification.
- `skills/phaseflow/SKILL.md:182-227`: duplicated Gate Order and slice sequence must agree with Gateflow's conditional fix/re-review semantics; handoff and state execution must retain substantive independent gates.
- `skills/planreview/SKILL.md` (`Special Review Lenses`, `Artifact Guidance`): focused re-review exists, but artifact guidance must not conflict with reusable, traceable unchanged facts. Modify it only if necessary.
- The four `agents/openai.yaml` files contain entry prompts/labels, not conflicting detailed gate rules. No change is currently justified there.

## Scope and non-goals

- Primary source: `skills/gateflow/SKILL.md`.
- Modify `skills/deepreview/SKILL.md`, `skills/phaseflow/SKILL.md` and `skills/planreview/SKILL.md` only where their text conflicts with or duplicates the confirmed rules. Reading a file does not imply it must change.
- Gate artifacts, review/decision evidence and necessary text validation belong to this work unit.
- No runner, preflight implementation, model catalog, provider/default, install/sync implementation, business repository or in-flight business task changes.
- No new tools, fields, severity tiers, exemptions, alternative flow, authorization scope or framework.
- Keep existing gate order, independent review requirements, binding goal scope, accepted-finding repair verification, residual risk obligations and user permission boundaries.
- Do not turn ordinary consultation into an additional gate or alter standalone exhaustive/strict review by default.
- No merge, PR approval/readiness changes, reviewer requests or external comments.

## Success signals

1. Agent-facing text assigns the three review layers distinct substantive checks, reuses still-valid evidence and requires affected-scope investigation for new changes, counterexamples or invalid evidence. Single-slice/unchanged code does not mandate duplicate comprehensive reviews.
2. Validation reuse explicitly checks applicability to current code/dependencies/configuration/relevant environment; changed or unsupported evidence cannot release a gate. Mandatory project checks and independent concrete investigations remain available.
3. Every review loop clearly supports pass without empty fix/re-review while retaining its review artifact, decision and corresponding accepted commit. Real unresolved blocking/needs-more-evidence/insufficient evidence cannot pass on the basis of an empty accepted-finding list.
4. Artifact references identify a retrievable artifact/version and preserve mandatory information, current decisions and next entry; final closeout remains a substantive summary.
5. Gateflow, affected referenced SKILLs and duplicated sequences agree. Representative checks cover unchanged single slice, interacting multiple slices, a real fix, new PR changes, stale validation/environment, no-findings pass, unresolved evidence/blocker and traceable versus missing references. Existing skill validators and relevant whitespace checks pass; no unrelated business test suite is run.
6. Full applicable Gateflow artifacts, independent parallel reviews/adjudications and a new draft PR are delivered. After completed review is reported, authorized skill sync and one MiMo Flash probe per Codex/Claude runtime verify actual tools and reading/application of updated SKILLs. Report actual failures, limitations and logs; do not expand to all providers.

## Execution and authorization

- Controller owns evidence/adjudication/state/accepted commits and PR bookkeeping.
- `gpt-6-sol` via `codex-agent-run` owns plan/implementation/accepted fixes.
- `mimo-flash` and `ds-flash` via `claude-agent-run` review independently in parallel: Planreview for plan, Deepreview for subsequent applicable gates.
- Goal confirmation is required before plan. Ordinary gates then proceed automatically under Gateflow, subject to actual stop conditions.
- New branch and new draft PR are authorized. Live sync and the two scoped probes are authorized after successful reviews and a report before execution. Merge is not authorized; no business resume is authorized.

## Open questions and remaining limits

- No blocking technical question identified; awaiting goal confirmation is the current entry condition.
- Prompt-based SKILLs guide Agents, not a runtime gate engine. This work does not promise mechanical enforcement or quantified speed gains. Controller owns truthful validation/closeout reporting; future runtime enforcement or broader measurement is outside this work unit.

Next entry: record confirmation, then dispatch plan.
