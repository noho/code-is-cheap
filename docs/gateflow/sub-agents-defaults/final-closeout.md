# Final closeout: sub-agents-defaults

Gate: final closeout. Status: pass; work unit completed. Goal/plan confirmed by user; current branch feat/sub-agent-result-collection and existing PR #50 reused throughout. Feature continuation, not a numbered issue; issue association and issue comment N/A.

## What changed

- Original PR: both runners wait for actual runtime exit and return one compact JSON report directly; --detail preserves raw output. Native streams/stderr retained in private logs; final/task semantics remain caller-owned, result_status=not_assessed.
- Continuation: ordinary task needs only selected runner/provider, explicit absolute cwd and sufficient independent-context task. No mandatory preflight, label/instance/log path, fixed prompt headings/N/A, child runtime/provider/model self-report, universal canary/extra artifact or per-event adjudication YAML. Local runtime instructions may still load; no parent conversation inheritance promised.
- Optional preflight checks only selected runtime/provider/launcher/profile, accepts natural language, generates fresh private identity, appends brief conclusion/unfinished/items/paths guidance. Optional canary/artifact/isolation reference retained with exact configured enforcement and known-copy/macOS constraints.
- Ordinary tool failures and ambiguous tool-like text yield anomalies/needs_review, not mechanical whole-Agent rejection or automatic permission/retry gate. Necessary task evidence and unresolved problems are judged by caller; invalid native structures/process/terminal or unmet configured proof remain explicit rejection.
- Report preserves measured wall_clock_seconds, verbatim single-terminal usage, available native runtime timing/cost/modelUsage and native session_id. Missing/conflicting metadata unavailable, not estimated; ID alone does not imply persistence. Persist/resume/provider/permissions unchanged.
- Final review fixes: reject invalid canary setup before native launch; reject explicit artifact hard links/log aliases after exit; reject dash log destinations unless --detail; correct raw kernel fixtures without assertion weakening; return native session IDs.
- Existing source edits need no separate report; file deliverables normally use final-answer paths, --artifact only if caller chooses mechanical new-file checks. No new result-collection command/channel/scheduler or business rule in runner.

## Gates, findings and publication

- Accepted plan 1e20493; accepted S1 b7ac57d; accepted aggregate deepreview7101707. Original PR evidence in docs/reviews/result-collection-closeout-20261010.md.
- Published full-PR dual review: MiMo/Codex and DS Flash/Claude, exact bff4b3f/ebd547f immutable compare. Five accepted source/test/doc findings (four external + native session ID omission), all applied in959ef73.
- Independent focused published re-review of959ef73: both routes actually exit0, all five final status 已修复, no new material finding/open question/unfinished issue. Evidence and controller dispositions in pr-review.md and pr-rereview.md; original reports preserved unchanged. Recovered tool errors/no-CI exit1 were evaluated by impact, not used as whole-Agent failure.
- Accepted PR review commit eaefaf896640fd376212d747217058c713e040ab was pushed successfully; GitHub head verified equal, PR OPEN/draft. draft-PR-pass entry criteria satisfied before this final closeout.
- Production scripts/skills/tests/READMEs/config remain identical to independently reviewed959ef73 (git diff exit0); follow-up commits contain evidence only. This closeout/state checkpoint is to be committed and pushed as final documentation, then remote identity reverified.
- PR: https://github.com/noho/code-is-cheap/pull/50. User retains manual ready/merge; no live sync, merge, approval, reviewer request, branch deletion, external issue/comment or other-project operation.

## Verified

- Final focused result/preflight51 pass (25.888s).
- Final full unittest with explicit macOS kernel/native opt-in140 pass, zero skips (60.178s). Actual denial across direct paths/aliases/recursive search/nested sandbox, read-only and workspace write restrictions, protected paths, trusted profile hash handling and4108-entry policy executed. Both actual native CLI collected-mode tests used local synthetic endpoints/keys, no extra real provider probe.
- Final native evidence /private/tmp/defaults-pr-fixed-native-20261010/{codex,claude}-probe.json. Temporary raw review evidence paths and immutable snapshot hashes recorded in review artifacts. Native usage/cost metrics and measured review durations retained in review-statistics.json without normalization or estimates.
- MiMo final re-review independently ran11 focused cases and source/syntax checks; DS independently ran affected suites including actual kernel22 and native2. Explicit limits recorded; no claim both independently ran all140.
- Six skills, shell/Python syntax and full diff whitespace checked. Repository reports no GitHub checks; local validation is not labeled CI pass.

## Documentation

README.md / README.zh.md ordinary-call/result sections, skills/sub-agents/SKILL.md and references/advanced.md updated. Main skill stays compact; advanced proof/isolation detail loads when selected. Installation retains co-located adapter; no compatibility/migration promised. All user-visible claims match the final source.

## Residual risk register

No accepted finding is deferred or partially fixed; no unclassified risk. These are confirmed boundaries, not unfinished scope:

| Boundary | Classification / owner | Destination |
| --- | --- | --- |
| Task truth, required execution/source proof, file content and inode provenance | Assigned to caller project task-contract work unit if stronger proof is requested; caller owns semantic acceptance | SKILL result consumption and advanced artifact/proof contract; no new creation protocol in this WU |
| Native schema evolution/tool visibility and interrupted runs lacking summary | Assigned to later maintainer result-collection work unit on concrete runtime change | Maintainer upgrade/regression work; retain managed exit handles/raw logs |
| Kernel isolation platform/tool dependence | Assigned to future maintainer platform work unit only if requested; macOS/srt limit preserved | README/advanced supported platform contract and native tests |
| No hosted CI checks | Assigned to later maintainer validation automation work unit only if requested | Current documented local140-test evidence; rerun on runtime upgrades |

## Next entry point

User may mark PR ready and merge manually. Live remains unchanged until explicitly authorized sync to live. After merge, follow user's next instruction; no automatic development or deployment.
