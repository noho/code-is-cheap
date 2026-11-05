# Hy4 Codex runtime and Token Plan integration

User authorized on 2026-11-05:
1. Reinvestigate current hy4 Codex runtime viability.
2. If viable, restore hy.codex support in this repository.
3. Add live override.hy.claude for Token Plan (https://tokenhub.tencentmaas.com/plan/anthropic), model hy4.
4. If viable, add live override.hy.codex for Token Plan (https://tokenhub.tencentmaas.com/plan/v3), model hy4.

The user authorized targeted live private endpoint edits. Repository deployment/sync is a separate final step; prepare and review code, create draft PR, then remind the user of applicable sync commands. No merge authorization.

Branch: feat/hy4-codex-token-plan. Preserve three pre-existing untracked docs/reviews/runner-handle-loss-20261023-* files; exclude them from this work unit.

Success means current native Codex completes streamed conversation, tool-call/result continuation and automatic safety-review structured verdicts under unchanged approval policy. No bypassing safety review to declare availability. Scope conditional restoration on evidence. Measure endpoint/effort/capability compatibility, do not blindly inherit another provider's catalog or claim untested 1M/image capabilities.

Existing private configuration: ~/.config/agent-tools/endpoints.json, mode 0600. Existing default.hy.claude is model hy4 at https://tokenhub.tencentmaas.com with its existing key. override.ds-flash.claude and .codex now carry the Tencent Token Plan key; selected URL/model/key must remain together. Never print or commit key values. Preserve all unrelated settings; backups stay outside Git with mode 0600.

Historical commits (all 2026-09-24): 1f927a8 changed unsupported max reasoning to high and explicitly confirmed Responses usable; 52169de added guardian buffering/retries but all 3 attempts failed under old TokenHub /v1/responses outage; 5e42b41 removed hy Codex because SSE cut mid-generation and chat-completions fallback spent its reasoning budget without a verdict. Squash ee7aa3c preserves descriptions. Current Tencent docs explicitly support Hy Token Plan in Codex at /plan/v3, and model list includes hy4.

Required workflow: gpt-6-sol via codex-agent-run for plan/implementation/fixes; independent parallel deepreview via Claude mimo-flash and Claude ds-flash (documented Codex ds-flash backup only if Claude unavailable); controller adjudicates. Commit/push/draft PR; user merges. No unrelated refactor or new framework.

Current gate: plan.

## User clarification (2026-11-05)
Live files are not part of the repository. Finish code changes and pass testing before sync to live. This explicitly authorizes the final component sync after validation; no live sync or override mutation before code/test/review pass. Store only sanitized deployment facts in Git, never private endpoints, keys or backups. Then update the authorized live Hy overrides.

## User clarification: runtime integration only
The project does not concern itself with model capabilities. Continue the task. Do not expand into model quality, benchmark, vision, or long-context capability research/certification. Runtime viability means completed native Codex requests, real tool continuation and automatic approval verdicts. Catalog/effort settings are only necessary client configuration, not a separate capability acceptance gate.
