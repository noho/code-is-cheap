# Runner dispatch ledger

All calls use explicit cwd `/Users/leo/workspace/code-is-cheap`, separate escalated managed exec calls, and installed runner subprocesses. Prompts/logs are under `/private/tmp/subagent-native-exit-contract/`; durable receipts in this directory retain actual completed results. Handles below are host-managed execution sessions, not native session IDs or OS PIDs.

| Role / target | Route | Prompt / raw log stem | Managed handle | Result / artifact |
| --- | --- | --- | --- | --- |
| Initial plan | gpt-6-sol / codex-agent-run | plan-prompt.md / plan | 39687 | Actual 0; plan-receipt.json; plan.md preserved in 25120e6; superseded by user clarification |
| Old plan review A | mimo / claude-agent-run | plan-review-mimo-prompt.md / plan-review-mimo | 84324 | Actual 0; plan-review-mimo-receipt.json; docs/reviews/plan-review-20261018-085246.md; old-target pass-with-risks, superseded |
| Old plan review B | ds-flash / claude-agent-run | plan-review-ds-flash-prompt.md / plan-review-ds-flash | 70435 | Actual 0; plan-review-ds-flash-receipt.json; docs/reviews/plan-review-20261018-085247.md; old-target pass-with-risks, superseded |
| Revised plan | gpt-6-sol / codex-agent-run | plan-v2-prompt.md / plan-v2 | 56993 | Actual 0; plan-v2-receipt.json; plan-v2.md preserved in 9599bf7 |
| Revised plan review A | mimo / claude-agent-run | plan-v2-review-mimo-prompt.md / plan-v2-review-mimo | 84455 | Actual 0; plan-v2-review-mimo-receipt.json; docs/reviews/plan-review-20261018-091226.md; pass-with-risks adjudicated in decisions.md |
| Revised plan review B | ds-flash / claude-agent-run | plan-v2-review-ds-flash-prompt.md / plan-v2-review-ds-flash | 59854 | Actual 0; plan-v2-review-ds-flash-receipt.json; docs/reviews/plan-review-20261018-091227.md; pass-with-risks adjudicated in decisions.md |
| Implementation / validation | gpt-6-sol / codex-agent-run | implementation-prompt.md / implementation | 97310 | Actual 0; implementation.md, implementation-receipt.json, source-freeze.json and retained validation evidence; complete code review pending |
| Complete code review A | mimo / claude-agent-run | code-review-mimo-prompt.md / code-review-mimo | 38045 | Actual outer1/native0; code-review-mimo-receipt.json; native content_filter final, no report; no code approval |
| Complete code review B | ds-flash / claude-agent-run | code-review-ds-flash-prompt.md / code-review-ds-flash | 3629 | Actual 0; code-review-ds-flash-receipt.json; docs/reviews/code-review-20261018-100303.md; accepted findings pending combined fix |
| Accepted fixes / validation | gpt-6-sol / codex-agent-run | fix1-prompt-draft.md (authorized final section) / fix1 | 44460 | Actual0; fix1-receipt.json, fix1.md, fix1-source-freeze.json;236 tests/24 conditional skips/exit0; independent reviews pending |

No invocation is accepted as task completion merely because it exits 0. Here the controller reads the delivered artifact and adjudicates it under Gateflow; the thin runner itself must not own that decision. No original task replay, kill, resume, provider fallback or live sync was performed.

Latest binding clarification: thin CLI wrapper, full untruncated final, no multi-status verdicts or warning-text judgment. Known SSE/catalog/unknown text must be exposed without semantic classification. All future implementation/review handoffs must include scope-amendment.md and decisions.md; old review endorsements of rejected status machinery are not current authorization.
