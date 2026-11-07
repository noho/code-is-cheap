# Kimi namespace compatibility：诊断与最小生产方案

2026-11-07；PLAN/diagnosis delegate；沿用 `fix/shim-subagent-message-delivery` / PR #70。**本轮结论：仅展开请求 namespace、保持返回裸函数名不变，在实际 Codex 0.167.0 上不能完成原生路由。** 已取得本机 `unsupported call: spawn_agent`，不是依据模型最后的解释作结论。下面的生产方案尚未实现，交 controller 检查；没有部署或重启。

## 事实、假设与范围

1. 原 Kimi [attempt-1](evidence/kimi/attempt-1/summary.json) 使用用户选择的 TokenHub 连接，8 次模型 HTTP 请求均200，但没有 spawn。其 ingress 确有 `multi_agent_v1` descriptors。仅凭这个样本，不能说 gateway 内部删了工具，也不能把问题归结为单纯的模型拒绝。
2. controller 的[真实 vendor 非执行诊断](kimi-tool-namespace-diagnostic.json)：同一个 harmless `probe_echo`，namespace 包装版本 completed、只有 reasoning；相同平铺 function 返回正确 `function_call` / token。未执行 callback。这是 namespace 兼容性调查依据，不是原生验收。
3. 本轮只做一次新的隔离 targeted prototype，结果见 [routing-verdict.json](evidence/kimi-namespace-diagnostic/routing-verdict.json)。它把请求里的已知 function-only namespace 展开到 `tools`，保留原有裸函数名、schema 和 namespace 描述语义；**完全没有响应/SSE 改写**。真实 Kimi 返回裸 `spawn_agent`，本机 Codex 拒绝路由，未创建 child。
4. 当前有效 destination 仍由 installed Kimi route `127.0.0.1:8790/coding/v1` 持有；resolver 检查其 URL/key 与对应 ds-flash 用户覆盖一致，wire model 为 `kimi-k3`。没有输出 URL/key、读写 private connections、换 provider/model，或回滚[用户覆盖](local-endpoint-override.json)。candidate 只转发到该 installed route，不观测私有 gateway 内部代码。

**已证实的边界**：此连接接受平铺 function 并产出实际调用；本版本 Codex 对这个没有 namespace 的 namespaced-tool 调用不能按唯一裸名自动匹配。**仍是待验证方案**：将 namespace 从原请求的唯一名称表恢复到返回项后，能否完成 fresh native parent/child 及后续历史重放。未实现这种恢复，也未把它写成已通过。

## 一次 targeted 原生 prototype 的实际记录

执行的是临时副本 `/private/tmp/shim-kimi-namespace-work/native-probe.py`，不是被另一个 delegate 修改的通用 probe；`ROOT` 明确指向本 repo。副本来自 `/private/tmp/shim-kimi-namespace-baseline/` 的不可变 probe/auditor，未覆盖原文件。实际 argv、app-server argv、完整安全设置和 source hashes 保存在 [launch.json](evidence/kimi-namespace-diagnostic/attempt-1/launch.json)。

```bash
python3 /private/tmp/shim-kimi-namespace-work/native-probe.py \
  --profile kimi \
  --evidence-dir /Users/leo/workspace/code-is-cheap/docs/gateflow/shim-subagent-all-providers/evidence/kimi-namespace-diagnostic/attempt-1 \
  --attempt namespace-prototype-1
```

只占一个 profile slot。一个全新 parent `01a1b688-143c-7771-a243-6d553ea9e735`，任务要求只 spawn 一名 fresh child，`fork_context=false`，child 只回随机 marker；parent 只可原生 spawn/wait。没有完整 A/B、file-read 或新的九路矩阵。由于第一次 spawn 被拒绝，没有 child ID，因此没有伪造或补做 wait，也没有成功重试。

| 实测项目 | 证据 / 结果 |
| --- | --- |
| runtime | `codex-cli 0.167.0`；实际 rollout `cli_version=0.167.0`；安装 binary hash 另记在 routing source evidence |
| 模型 / catalog | `k3` / provider `kimi` / max；原 installed catalog hash `61f9af1da02dc3c96666c0468f4be7abaebfb18b2de89f4a44712e39b38aed21`；未强制 v2、Lite、Code Mode 或 catalog version |
| 策略 | 保持原 Kimi probe 的 read-only、approval `never`；原生 `thread_settings_applied.approvals_reviewer=auto_review`，不是关闭 node review |
| HTTP | 2 次 `/coding/v1/responses`，均200 / completed；15.33秒；app-server exit0，仅代表程序完成 |
| 请求1 | 展开 `multi_agent_v1`、`mcp__github`、`mcp__node_repl` 三个实际 namespaces；没有变更非 `tools` 字段 |
| 请求2 | runtime 原生加入其他 MCP descriptors，共6个 namespaces；没有变更非 `tools` 字段；包含实际 rejected call/result 历史 |
| tool choice | 两次均实际存在 `tool_choice="auto"`，`parallel_tool_calls=true`，逐值保持；未强制 required/function choice |
| 原始调用 | SSE `response.output_item.added` 和 `.done` 中 `name="spawn_agent"`，`call_id="spawn_agent:0"`，两项都**缺少 namespace**；done arguments 是完整原始诊断任务与 `fork_context=false` |
| 本机结果 | rollout 第12行实际 `function_call`；第14行同一 call_id 的 `function_call_output.output="unsupported call: spawn_agent"`；stderr 也有该 router error |
| 原生协作 | 只有这个 parent 的 rollout；零 collaboration/tool-execution events，零 child；没有 executed callback |

关键调用原文：

```json
{"type":"function_call","id":"fc_spawn_agent:0","status":"completed","name":"spawn_agent","call_id":"spawn_agent:0","arguments":"{\"message\": \"KIMI_NAMESPACE_ROUTING_DIAGNOSTIC. Reply exactly one line LIVE_INITIAL_cbda008fdb10. Do not use tools, read/write files, or delegate.\", \"fork_context\": false}"}
```

独立证据索引：

- [response-native-calls.json](evidence/kimi-namespace-diagnostic/attempt-1/response-native-calls.json)：安装 route 返回的原始 function-call SSE `data:` 行；保留 added/done、原 call_id / arguments，以及完整响应流的 hash/字节数。没有保存 hidden reasoning。
- [rollouts-sanitized.json](evidence/kimi-namespace-diagnostic/attempt-1/rollouts-sanitized.json)、[native-events.json](evidence/kimi-namespace-diagnostic/attempt-1/native-events.json)、[native-rollout-supplement.json](evidence/kimi-namespace-diagnostic/attempt-1/native-rollout-supplement.json)：仅本轮明确新 test ID 的原生 call/result、事件和设置、源 rollout hash。未读业务/调度/watchlist/旧用户会话，未执行 captured JS。
- [namespace-transform.json](evidence/kimi-namespace-diagnostic/attempt-1/namespace-transform.json)：真实 post-observer 请求变换、pre/post hash、完整 native namespace 前后 descriptors、其他 namespaces 的函数名与 schema hashes。原 function 的 name/parameters/strict 等字段保持，description 为 `Namespace <原名>: <原描述>\n\n<原函数描述>`，没有 alias。
- [wire.json](evidence/kimi-namespace-diagnostic/attempt-1/wire.json)：原 helper observer 和实际发送点的不同边界。`expected_outbound_sha256` 仍指 **prototype 之前**；`pre_prototype_body_verified=true`、旧 `actual_upstream_body_verified=false` 是预期事实。实际 prototype body hash 独立记录，不能拿原 observer hash 冒称覆盖了后加变换。
- [source-snapshots](evidence/kimi-namespace-diagnostic/attempt-1/source-snapshots/) 保存实际启动 harness 的精确 gzip 源码；该 hash 是 `launch.source_hashes_at_launch` 中临时 probe 的值。没有运行通用 all-provider auditor，也没有伪造 audit pass。
- [privacy-processing.json](evidence/kimi-namespace-diagnostic/privacy-processing.json)：无关 global tool descriptors 作 hash omission 的前后文件 hash；原生 descriptors、全部实际 native calls/results 未删。全部尝试均保留，只有这一次 native prototype。

## Codex namespace 字段与实际路由检查

[codex-routing-source.json](evidence/kimi-namespace-diagnostic/codex-routing-source.json) 保存公开 tag `rust-v0.167.0`（commit `086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a`）的精确路径、文件 hash、有关行号/摘录，以及本机 binary hash。公开同版本源码仅佐证原生观察；不声称已复现安装 binary 的构建，更不是 gateway 内部源码。

- `protocol/src/models.rs` 的 `ResponseItem::FunctionCall` 明确有 `namespace: Option<String>`，缺省序列化省略。**协议字段可选，不等于任意 namespace 下的工具都可以省略它。**
- `core/src/tools/router.rs::build_tool_call` 使用 `ToolName::new(namespace, name).with_default_namespace()`；没有按裸名扫描唯一匹配的逻辑。
- `protocol/src/tool_name.rs` 把缺省/空 namespace 归为 `functions`。
- `handlers/multi_agents/spawn.rs::tool_name` 注册的是 `ToolName::namespaced(MULTI_AGENT_V1_NAMESPACE, "spawn_agent")`，constant 是 `multi_agent_v1`。
- `registry.rs::registered_tool` 按完整 ToolName 查表；找不到时原生返回 `unsupported call: {tool_name}`。这与本机第14行的实际结果一致。

因此本次返回的键相当于 `functions / spawn_agent`，而 native handler 的键是 `multi_agent_v1 / spawn_agent`。namespace 在这里参与执行契约，不能称为 display-only。把描述符名称改成点号/下划线拼接也不会自动得到这个字段；源码没有这样的 split 路由。没有理由为了这次诊断引入 alias、改 catalog/multi-agent version，或换 model/policy。

## 建议的最小生产方案——待 controller plan check

**拒绝上线 request-only flattening。建议对 Kimi 增加默认关闭的、显式逐 route 启用的 namespace function compatibility：请求展开 + 仅从该请求名称表恢复返回 function_call.namespace。** 这比原 `agent_message_fix` 多出响应契约，必须由 controller 判定适用 plan review 后再派实现；本 delegate 没有实现它。

### 边界和请求不变量

1. 新 flag 可命名 `namespace_function_compat`，loader 默认 false，global/env-only/未列 route 不继承。只在 Kimi 那条 existing route 显式 true；另外八路、原全部 `agent_message_fix=true`、guardian/model/ID/JSON/drop flags 均不变。不改 catalog、profiles、registry、private connections、端口/prefix、tool policy。
2. 适配只针对 `/responses` 的顶层 `tools` 中已知 function-only namespace wrapper，保留原 list 顺序，wrapper 的 children 在原位置依次展开。沿用原函数名，无 alias；保留 child 的所有字段/schema，唯一允许的语义补充为把原 namespace name/description 无损并入 description。建立**本 HTTP 请求内只读映射** `bare_name -> original_namespace`；平铺函数保持原义，不入恢复表。
3. 全部 callable 名称必须可证明全局唯一，包括原平铺 function/custom 与 namespace 内 function；跨 namespace 重名、与平铺工具冲突、非法 name，启用 route 在发 upstream 前 sanitized400，零发送，不能挑第一个、加 alias 或误路由。prototype 检查的是实际 function 名称唯一；生产需补齐 custom/未知 callable 形状的保守 collision 防线。
4. namespace metadata 限定现有 `type/name/description/tools`；children 只接受 function。遇到未来 namespace metadata、nested namespace、custom/mixed child、非对象/非数组等无法无损映射形状，明确 sanitized400，不能丢字段继续。其他已知非目标工具保持原样；无法确认是否 callable/是否会破坏唯一性的未来 tool shape 同样拒绝适配请求，不猜类型前缀。flag off 时不引入这些拒绝行为。
5. `input`（包括已有 namespaced call/output history、additional_tools）、instructions、reasoning/context、metadata、include、format、tool_choice、parallel_tool_calls 和所有其他字段保持深度相等。当前实测只覆盖 `tool_choice=auto`；第一版支持 absent / auto / none / required 原值，不擅自改为 required。结构化指定 namespaced function 的 tool_choice 没有兼容证据，应在适配确有 namespace 时 sanitized400，而非偷偷抹 namespace。以后若有实际需求再单独验证/扩展。
6. additional_tools 中的 namespace 不在本次实际 Kimi样本；不预先改写它。不能因为它存在就 drop。若后续实际 native 路径依赖这类动态 descriptor，先保留原始失败证据，再界定同一 request 内完整映射所需的扩展，不能声称本方案已覆盖。

### 响应的最小恢复设计

1. 从真实证据看，至少 `response.output_item.added.item`、`.done.item`，以及 `response.completed.response.output[]` 的 function_call 表示应一致恢复；普通非 stream JSON 的 `output[]` 也用同一变换。只在 `type=function_call`、原 name 属于本次恢复表、namespace absent/null 时添加原 namespace。已有相同 namespace 保持；显式冲突 namespace 不覆盖/猜测，按明确协议错误失败。
2. **不改 name、arguments、call_id、id、status 或其他字段，不改函数输出，不执行工具。** 原平铺 exec_command 等调用仍由 Codex 的默认 namespace 处理；非目标/未知工具名原样交给原生 runtime，不能据此扩充可执行工具集。不是建立另一个 collaboration API。
3. 只需每 HTTP 请求的一份 immutable map 和有界 SSE event framing buffer；不需要 session/child registry、跨请求 map、call_id alias 状态或 agent 生命周期状态。实际 added/done 都带 name，本轮没有证明需要积攒 argument delta 或跨调用关联才能恢复 namespace。不要预先加这些机制。
4. SSE 需按完整 event/data framing 解析 JSON，不用正则替换，不执行 captured 代码；兼容任意 network chunk / UTF-8 / CRLF 边界、多 data 行、并行交错调用。非目标 events 原 bytes 转发；被改 event 除上述 namespace 叶子外 JSON 全值相等。arguments delta 不需要重写，不能改变调用顺序、terminal/lifecycle、空成功工具结果或 reasoning 内容。
5. 继续真正流式发送，不能等整个回答结束；event buffer 设明确界限（建议8MiB，超过时显式终止并记录 sanitized 协议错误，不截断后当成功）。第一次相关 event 验证/恢复后再发该 event；malformed/truncated JSON/stream 保持失败，不能造 completed。变长响应须处理 Content-Length/Transfer-Encoding/Content-Encoding；支持的 response compression 要按真实 bytes 边界解码/重新编码，未知编码不能透传后冒称已修复。保留现有 guardian buffering/retry 和普通 streaming 的差异，禁止由 adapter 新增推理重试。
6. 原生 response 恢复后，下一请求会带 namespaced function_call 历史；**先原样保留并真实验证 gateway 是否接受**。本轮只有 bare-call rejected history，未证明要删历史 namespace。若后续实测失败，不用预设历史/输出改写解决，保留证据再调整最小契约。

这仍需 SSE/JSON response compatibility 的实现与验证，不能称为“stateless request-only adapter”。允许的状态仅是一次 HTTP 的名称表/分帧缓冲；没有证据支持更重的 bridge。用户明确要求本轮不实现 stateful stream rewrite，故这里仅给设计，代码仍未改。

## 实现后需要的回归与原生证据

- helper/route 离线回归：新 flag 默认关闭和只有 Kimi启用；无 namespace / flag off bytes no-op；unique names、schema、strict、description语义、extra child fields、非目标工具/字段的精确保留；duplicates/未知 wrapper shapes/unknown callable/unsupported structured tool_choice sanitized400 且零 upstream send。
- response 离线回归：added/done/completed/JSON 一致恢复、既有 namespace 保留/冲突失败、未知/默认函数不改、并行 interleave、单字节和 UTF-8/CRLF chunk、multi-data、malformed/truncated/oversize、gzip/deflate/未知编码、Content-Length变化，以及 guardian vs ordinary streaming；实际回放已保留的 raw spawn 行，证明 name/arguments/call_id 都不变。测试 parser，不模拟模型成功；不执行 captures 中的 JS。
- 原 `agent_message_fix`、ID/JSON/model swap、auth snapshot/replacement、prefix、redirect、Lite/custom/非目标 items、其他八路和 env-only 的既有 focused checks 必须继续通过。原114离线通过是旧版本基线，不自动成为未来 helper 版本通过记录。
- 先声明一次 targeted Kimi fresh parent/child 路由复验：原 catalog/card/policy/0.167.0，真实 vendor；保留 namespace 前后请求/响应哈希、原始 calls、native spawn/wait 事件、child-owned独立 completed turn，不能用 parent final 或 exit0替代 child evidence。源版本必须精确关联，新 observer 须实际覆盖新增 response stage。失败不得覆盖这次 prototype。
- 路由复验成功后，再由 controller 安排完整 Kimi A1/A2/B（实际 v1 无独立 send_message 时 A3 N/A），验证 namespaced历史重放、同 child 新 turn、不同 child 实际文件执行/call-result/exit0。保持父代 native-only、fixtures unknown、无额外工具、固定并发总数<=2；不能只把任务 marker 对了当验收。
- 任何生产 helper 改动需由 controller 派 `gpt-6-sol` 实现、验证，再走仓库独立 mimo-flash / ds-flash review、裁决修复与受影响面复审。本轮没有派发其他 Agent。controller 决定此响应契约变化的 planreview applicability。

## 当前交付和阻塞

当前 ownership 内仅新增本计划及 `evidence/kimi-namespace-diagnostic/*`；临时 Python 在 `/private/tmp/shim-kimi-namespace-work/`。14项诊断 harness 不变量检查通过，见 [prototype-invariants.json](evidence/kimi-namespace-diagnostic/prototype-invariants.json)；它们不代表生产测试或 all-provider acceptance。生产 helper 保持 `cd8e9f218c5a65d65bceff6ffac8b723c075913dad7ca08d999941ee34544dda`，generic probe/auditor、catalog、routes 和 private connections 均未由本轮修改。

**阻塞**：request-only方案已被实际路由错误否定；响应 namespace恢复的设计等待 controller plan check/适用审核、另行派实现和真实验收。Kimi尚未产生 native child；本轮不更新全局6/9结论，Hy/MiMo Flash由另一 delegate负责。本轮不 commit/push/deploy/restart，也不向原业务 parent/thread 发技术 callback。

未来 approved changes final closeout 后，controller 应提醒用户在批准 checkout 中、取得 live授权后运行 `./scripts/sync-codex-agent.sh`；本轮没有执行该命令。不需要为本诊断改 skills/launcher，因此无其他同步命令。
