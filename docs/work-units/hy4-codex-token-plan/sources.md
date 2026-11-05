# Current sources and controller observations

Retrieved 2026-11-05:
- https://cloud.tencent.com/document/product/1823/130070 — Claude Token Plan base https://tokenhub.tencentmaas.com/plan/anthropic; set main and subagent model to selected supported model.
- https://cloud.tencent.com/document/product/1823/130071 — Codex supports both general and Hy Token Plan; Responses base https://tokenhub.tencentmaas.com/plan/v3, wire_api=responses.
- https://cloud.tencent.com/document/product/1823/130060 — model IDs include hy4; Hy Token Plan currently documents text-only availability. Full Responses URL /plan/v3/responses. General and Hy plans share Token Plan key.
- https://cloud.tencent.com/document/product/1823/132252 — Hy4 direct API guide (updated 2026-11-04): supports Chat Completions, Responses and Anthropic Messages; direct base https://tokenhub.tencentmaas.com/v1; context 1024k, input 960k, output 64k. Direct guide describes image capability, but Token Plan endpoint availability is narrower; do not infer image support on plan.

Controller checked codex-cli 0.166.0. Existing default.hy.claude key and override.ds-flash.claude Token Plan key are different (values never emitted). Thus direct and plan probes must select different credentials from the appropriate private connection.

Historical facts are commit descriptions/diffs, not fresh measurements: 1f927a8 reports max rejected; 52169de reports guardian SSE unexpected EOF; 5e42b41 removes Hy Codex. New probes must establish current results.

- https://cloud.tencent.com/document/product/1823/131208 (updated 2026-11-04), reasoning depth supported model table explicitly lists hy4 default high and supported high/no_think. Codex should use high; max must not be inherited from other cloud profiles.
