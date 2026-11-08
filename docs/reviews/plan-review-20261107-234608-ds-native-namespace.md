# Plan Review — Native namespace compatibility（Kimi / MiMoFlash bounded plan）re-review

- **Reviewed target**: `docs/gateflow/shim-subagent-all-providers/native-namespace-plan.md`（SHA-256 `e6d474dd431c2ccf8e43bd31ee78c0dab043b62e8dad1d57ef94d961b0500188`；branch `fix/shim-subagent-message-delivery`，PR #70，HEAD `901cea16928ef2db01ce774c99652f62fb3dca68`）
- **Review type**: independent adversarial PLAN re-review only；不 review 已写代码、不做 implementation/native probes、不编辑 plan/生产文件、不 commit/push/deploy、不发送消息。
- **Reviewer provider/model**: `deepseek/deepseek-flash[1m]`，Claude runtime。该值来自本次 invocation 的 runtime model 报告。
- **Timestamp**: 2026-11-07T23:46:08+0800
- **Independence / boundaries**: 只读取了 target plan、`control.md`、`controller-native-diagnostics.md`、`scenario-validation.md`、原始 all-provider `plan.md`、被引用证据的必要子集（`routing-verdict.json`、`response-native-calls.json`、`namespace-transform.json`、MiMoFlash A/B rollout/wire/audit）、`codex-agent/shim-routes.json`、`codex-auto-review-shim` 的相关 handler 逻辑及 probe 的 descriptor 采集代码；未读取另一 concurrent reviewer 的结论、private endpoints/credentials、业务 session 或旧 business run；未执行 vendor/native 探测或 broad suite；除本 artifact 外未写文件。

## 1. Goal、scope 与 review question

用户已确认的 goal：九条既有 managed cloud shim routes 全部完成 native 验证；每条要求实际 native A initial、同一 child 的真实 continuation、在 descriptor 实际提供时完成独立 MESSAGE delivery，以及 B child 实际读取未知无害 fixture；不得 catalog/provider fallback、不得削弱 policy；live sync/restart 与向原业务 parent thread 发技术 callback 均需另行授权。

目标 plan 的范围：只对实际出现在 top-level `tools` 的 `multi_agent_v1` / `collaboration` native collaboration namespace 做 bounded 适配；Kimi 使用 request flatten + response restore，MiMoFlash 使用 response-only restore，其余七条保持原 response path；request-local map、bounded per-event SSE、namespace-only restore、identity response encoding、fresh observer、affected-provider fresh A/B，以及七条既有 positive 的 bounded reuse equivalence。

本 re-review 的核心问题：**上一轮 DS review 的两个 accepted findings 是否已关闭，修订后的 plan 是否足以指导已确认 goal 内的实现。** 本次不是对已写代码的 review；函数拆分、局部解析算法和 handler 实现细节留给 implementation/code review。

## 2. Assumptions tested

| # | Assumption | 结果 | 直接证据 |
| --- | --- | --- | --- |
| 1 | Kimi request-only flattening 会产生裸 `spawn_agent`，但缺少 native namespace 时 Codex 不能路由，因此 response restoration 是必要方向 | **成立** | `routing-verdict.json`：`bare_function_call.name="spawn_agent"`、`routing_result="FAIL: unsupported call: spawn_agent"`、`child_created=false`、`request_only_flattening_sufficient=false`；`response-native-calls.json` 的 added/done function_call 无 namespace |
| 2 | MiMoFlash 的 bare `wait_agent` 是 namespace 丢失，而成功的 `spawn_agent` 可以带显式 `collaboration` | **成立** | A rollout 第 16 行 `spawn_agent` 带 `namespace="collaboration"`；第 32 行 `wait_agent` 无 namespace；第 34 行 `unsupported call: wait_agent`；advertised descriptor 为 `collaboration.wait_agent` |
| 3 | 旧 `native_descriptors` 不能证明 descriptor 的实际请求位置，因为该字段聚合了 top-level tools 与 input `additional_tools` | **成立** | `native-probe.py:151-156` 明确从 `doc["tools"]` 和 `input[type=additional_tools].tools` 聚合；MiMoFlash request 4 的 `native_descriptors` 出现 top-level `functions`、top-level `collaboration` 与 additional-tools 中的 `functions` 三个条目 |
| 4 | 收窄到 exact top-level `multi_agent_v1` / `collaboration` 即可关闭上一轮“无关 MCP 被展开/全局唯一性拒绝”的 finding | **成立** | target plan §Route contract 与 §Exact request-local namespace map 1/3/4/5/6；旧 `namespace-transform.json` 显示 prototype 确实额外展开了 `mcp__github`、`mcp__node_repl`，新 plan 明确不再展开 |
| 5 | 只检查 mapped native bare name 的歧义，不会把无关 MCP 重名升级为整请求 400 | **成立** | target plan 第 44-45 行明确“Duplicate unrelated MCP names … do not block a request”“only mapped native bare names require uniqueness” |
| 6 | Guardian 可由现有 original-model check 识别，并可显式绕过两个新 stage | **成立** | `codex-auto-review-shim:389-405` 在原请求上判定 `request_model == route["from"]`；`:450-482` guardian 走 buffered/retry，普通请求走 streaming；新 plan 第 34 行明确 bypass |
| 7 | Active map 只接受 identity/absent response encoding，非 identity 在 downstream headers 之前 502，是当前 handler 可实现的边界 | **方向成立；实际 encoding 仍需 fresh evidence** | 当前 handler 在 `:501-507` 先转发 status/headers 再读 body；plan 第 58 行把 identity 设为 active-map 前置条件并要求 fresh observer 记录实际 encoding。实现需在发送 headers 前完成该检查（见 local obligations） |
| 8 | MiMoFlash response-only 不改 request；Kimi 只 flatten `multi_agent_v1`；fresh A/B 才能证明 native 修复 | **设计成立；尚未执行** | plan 第 34、42、76-85 行；A audit `passed=false`，B audit `passed=true` 但均为旧 source；plan 明确不给 native pass、不把旧 B 拼入新 source |
| 9 | 不引入 aliases、跨请求 orchestration state、catalog/model/policy/v2 强制 | **成立** | plan 第 5、34、40、46、102 行 |
| 10 | 旧 plan 中“用户禁止 request-local stream rewrite”的归因错误已纠正 | **成立** | target plan 第 5 行：“Necessary request-local SSE compatibility was **not prohibited by the user**”；旧 `kimi-namespace-plan.md` 保持 immutable，作为 diagnostic history |

## 3. Findings

**0 material findings.** 未发现仍会阻止在已确认 goal 内正确实现的 scope、contract、architecture 或 acceptance blocker。

### 3.1 上一轮 findings 关闭核对

| 上轮 finding | 状态 | 关闭依据 |
| --- | --- | --- |
| **1-高**：把所有 function-only namespace（含 `mcp__github`/`mcp__node_repl`）展开/恢复，扩大 Kimi tool surface，并以全局唯一性把无关 MCP 重名升级为 400 | **已关闭** | target plan §Route contract 与 §Exact map 1/3/4/5/6：只选 exact top-level `multi_agent_v1` / `collaboration`；无关 namespace 保留；仅 mapped native bare name 做歧义检查；unrelated MCP duplicates / repeated unrelated `functions.exec` / opaque schema duplicates 不阻塞；unknown descriptor 只在其显式 declaration-level name 与 mapped native name 相同时按 scoped ambiguity 处理。该收窄直接对应上轮建议 1-4。 |
| **2-中**：错误归因“用户明确要求本轮不实现 stateful stream rewrite” | **已关闭** | target plan 第 5 行明确 request-local SSE compatibility 未被用户禁止；第 102 行把 plan-only/no live sync/no callback 边界与实现授权分开。上轮建议的精确表述已落实。 |

上轮 DS review 的 Open Questions 在本 plan 中的处理：

- namespaced history acceptance：列为 A2/B 的 fresh native gate，明确“先保留、真实测试；若 gateway 拒绝，保留失败并仅按证据修订，不预先删除 history namespace”。
- guardian 路径：明确 bypass 两个新 stage，保留当前 buffered/retry。
- ordinary streaming immediacy/concurrency：明确 first-event flush 与两个并发请求使用独立 map 的 handler-level tests。
- response compression/header：明确 identity/absent only、非 identity 502 before headers、fresh evidence 记录实际 encoding，不新增 compression engine。
- structured `tool_choice`：明确 flattened native 目标 400、unrelated structured choice 保持不变、absent/auto/none/required 原样。
- mid-stream 冲突/abort：明确整 event 验证、begin 后 close、不得发 HTTP 400、不得 synthetic terminal，并明确不能对已转发调用声称 transactionality。
- `additional_tools`/compaction：保持 defer，作为 future work，不阻塞当前 goal。
- 当前矩阵表述：明确 7 strict / MiMoFlash partial / Kimi blocked，且 plan 不新增 native pass。
- production observability：限定 route identity、flags/stage、counts、fixed error class，不记录 prompts/arguments/bodies/credentials/private URL/session IDs。

## 4. Open questions

**无 material open question 阻塞 implementation。** 以下均是 implementation / code review 的本地验证义务，不是新的 plan finding，也不是对已明确意愿的重复质疑：

1. **Stage ordering / map derivation**：map 必须从实际 decoded request 的 top-level `tools`、在 native flatten 之前建立；MiMoFlash 的 native request stage 必须相对既有 stage byte-identical（plan 第 34、40、42、89 行）。现有 `native-probe.py:151-156` 的聚合字段不足以证明位置，fresh observer 必须记录。Owner: implementation/code review；destination: request tests + fresh observer。
2. **Downstream header timing**：要满足“非 identity encoding 或首个 affected event 解析失败时在 downstream headers 前 502”，实现不能先无条件发送 response headers；同时仍须通过 first-event-before-EOF test。Owner: implementation/code review；destination: response/header tests。
3. **Activation path gating**：只对 normal Responses requests 生效；flags off / no map / guardian / 非目标 path 必须保持原行为（plan 第 34、43、58、60 行）。Owner: implementation/code review；destination: handler tests。
4. **Structured `tool_choice` 与错误分类**：native-targeted choice 400、unrelated choice 原样、malformed/oversize/conflict 的 fixed error class 与 no-retry 语义需在代码层面对齐 plan 第 46、62 行。Owner: implementation/code review；destination: request/response tests。
5. **Fresh evidence 的实际边界**：必须记录 descriptors 的 exact top-level 位置、实际 response encoding、source/stage hashes、before/after response leaves；旧的 aggregated `native_descriptors` 与旧 SSE 不足以证明新 boundary（plan 第 48、87-94 行）。Owner: controller/implementation；destination: fresh observer + native A/B。
6. **Native acceptance gates**：Kimi A1/A2/A3（仅 descriptor 确认无独立 `send_message` 时 N/A）/B；MiMoFlash A1/A2/A3/B；七条既有 positive 只有在 controller 记录 flags-off/path equivalence 后才可 bounded reuse（plan 第 76-94 行）。Owner: controller；destination: A/B evidence + reuse record。

## 5. Residual risks and suggested tracking destination

- **Kimi 窄化 flattening 是否足够**：旧 prototype 展开过 MCP groups；新 plan 只展开 exact native namespace，fresh native A/B 才能证明足够。Destination: plan 第 100 行 residual acceptance question；owner: controller。
- **实际 response encoding 可能不是 identity**：若 upstream 返回 gzip/deflate，按 plan 该 attempt 成为 blocked evidence，需要 bounded contract decision，而不是自动改 header/重试。Destination: fresh observer；owner: controller。
- **Kimi gateway 可能拒绝 namespaced history**：这是 A2/B 的真实未知；失败时保留证据，不预删 namespace。Destination: fresh A2/B；owner: controller。
- **MiMoFlash `collaboration` descriptor 的 exact top-level 位置**：旧观测字段是聚合结果；fresh observer 必须证明。Destination: fresh observer；owner: controller/implementation。
- **Mid-stream 冲突不能撤回已转发调用**：plan 已明确承认，不允许 review/closeout 声称整段 response 的 transactionality。Destination: response error-path tests + code review；owner: implementation。
- **七条既有 positive 的复用等价性**：若 helper/flags/response path 不再等价，必须重跑；DS historical conditional reuse 与 Hy attempt 2 的限制仍需 controller 记录。Destination: controller closeout；owner: controller。
- **本 plan 不新增任何 native pass**：当前仍是 7 strict / MiMoFlash partial / Kimi blocked；MiMoFlash B 旧 positive 不能拼入新 source 的 A+B。Destination: controller closeout；owner: controller。

## 6. Final conclusion

**pass-with-risks**。

上一轮两个 DS findings 均已关闭：适配已收窄到实际 top-level `multi_agent_v1` / `collaboration`，无关 MCP 保持 passthrough，唯一性只针对 mapped native names；错误归因已修正。修订后的 plan 对 contract、scope、state semantics、guardian bypass、identity encoding、SSE boundedness、mid-stream failure、fresh observer 和 A/B acceptance 给出了足够可执行的边界，未发现新的 material scope/contract/architecture/acceptance blocker。

风险来自 plan 自己明确保留的 fresh primary evidence gates（实际 encoding、descriptors 位置、namespaced history、MiMoFlash A2/A3、七路等价复用），不是 plan 缺陷或未收敛的 wording。Controller 仍须先裁决另一份 concurrent plan review，再授权 implementation；本 review 不代替 code review，也不宣称任何 native pass。
