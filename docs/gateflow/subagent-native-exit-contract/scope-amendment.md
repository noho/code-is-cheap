# Binding scope clarification — simplify the interaction wrapper

User steering during plan review, 2026-10-18:

> 我要求的是简化，对齐内置子Agent的行为，对齐cli行为，“还保留了多套状态，甚至提议新增 wrapper 状态”都是错的。另外，final_answer_chars、final_answer_truncated；汇总最多展示 12000 字符，12000限制是什么原因？

This explicitly rejects the first plan's multi-status migration/new wrapper status. It refines the existing thin-CLI goal, not permission for a new system. This clarification supersedes conflicting parts of plan.md, and the old Planreviews cannot approve the new version.

## Required target

- One interaction, one actual CLI outcome. The native code belongs to the launched CLI; forward it honestly with the native final and retained logs. Caller decides task acceptance, continuation/retry count and routing.
- Remove `agent_status`, `validation_status`, `result_status` as runner-produced success/acceptance state machines. Do not replace them with `incomplete`, `wrapper_exit_code`, another rollup or a new task classifier. Facts about missing/partial final, damaged source data, optional checks and auxiliary-copy problems can be reported plainly, not as competing interaction verdicts.
- Return the full native final. Remove the custom 12000-character display cap and the associated `final_answer_chars`/`final_answer_truncated` interface. Do not move the cap into another default summary layer or make callers read a second file to obtain their normal final response.
- Simplify diagnostics as well: avoid retaining three parallel diagnostic verdict classes/count/truncation state merely for compatibility. A small factual diagnostic representation plus retained raw log paths is sufficient; do not duplicate entire tool transcripts into summary diagnostics. Preserve meaningful errors and optional-check observations with source locations where available, not business acceptance.
- Keep useful runtime identity/session, actual timing/usage, source logs and existing optional capabilities when directly useful. Update the public schema version and all direct consumers/documentation as needed rather than preserving misleading status APIs. Do not redesign unrelated configuration, storage, routing or isolation.
- Additional explicit user requirement: “薄封装中不得有对warning文本进行判定的行为”. Warning/diagnostic free text is opaque content, preserved with its source; no text recognizer, regex/keyword/known-message whitelist, recovery inference, benign/severe categorization, filtering or acceptance decision. Structured event type/exit fields may locate and report actual protocol facts, but the warning wording cannot drive behavior. Unknown and known warning texts receive identical handling. Preserve original warning text, not a semantic rewrite. Add offline regressions varying only SSE/catalog/unknown warning wording and asserting unchanged exit/final treatment and retained text.
- A returned explanation of missing input/environment/inability is a normal final answer. No fixed same-provider retry cap; no automatic retry/resume/provider switch. Measurement sample retention and caller/project authorization remain intact.
- Auxiliary artifact/canary or extra last-message-copy failures do not override native exit. If no primary response can be delivered because the wrapper itself cannot run/serialize/write, expose that genuine execution/delivery failure plainly, with known native facts when available; do not introduce a public wrapper-status taxonomy. Prelaunch setup failures remain distinct from an actually executed native CLI's return; do not fabricate known exit values.
- Keep implementation minimal. Re-evaluate whether initial plan's launch channel/status proof machinery is actually necessary; do not carry it forward just because it appears in the old plan. No persistence, supervisor, result storage, model probes or changes to the portfolio project.

## Provenance / gates

Initial goal and plan are preserved in `25120e6`; this file and controller decisions capture the user's explicit subsequent clarification. gpt-6-sol must produce revised **plan-v2.md** without editing the old plan being reviewed. Old mimo review may finish against its old target; preserve its actual result as historical/superseded evidence, without canceling, relaunching or treating elapsed time as failure. Independent parallel reviews of the revised contract remain required before implementation.

The 12000 cap originated in the collected-result change merged as PR #50 (`d51765b`, `scripts/agent-run-result.py:11`). Repository history describes a compact result but provides no specific technical basis for that number. It is wrapper policy, not a native model/runtime requirement. Removing it follows the user's explicit thin-interaction and simplification requirement.

Current gate / next entry point: plan, revise to the clarified minimal contract, then independent Planreview of revised target. Implementation remains not started. Risks: public caller migration and tooling deployment remain assigned to later caller/deployment work after merge; current interface/code/test/docs correction is fixed in this slice. No unclassified risk or new blocking user question.
