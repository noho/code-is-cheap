# Code Review

## Scope

- Mode: current changes（PR #70 最终组合版本；含当前未提交/未跟踪改动）。不是仅 `git diff main` 的单 commit 版本，而是 `review-freeze-v1.json` 冻结的完整 workspace。
- Branch / PR: `fix/shim-subagent-message-delivery` / draft PR #70（base `main`）；本地 HEAD `901cea16928ef2db01ce774c99652f62fb3dca68`，base `09337967910277785b82874326d7f49156c9395b`。
- Output file: `docs/reviews/code-review-20261108-012340-ds-flash-all-shim-providers.md`
- Included scope:
  - `codex-agent/bin/codex-auto-review-shim`（生产 shim，最终 helper `a6246a4bc810125437992791aedcc8f2aa4c072f55e2bcf3691562feecd8e1e6`）
  - `codex-agent/shim-routes.json`（九条 managed cloud routes，最终 `0dd8e0fdbf4c360470b2102005075a981b1a09393894997faeb18468e59af5c6`）
  - `docs/gateflow/shim-subagent-delivery/native-probe.py`（`6fde7ff90f47035520f500b618daf993149450c10b38ac515420e32888dd452f`）
  - `docs/gateflow/shim-subagent-delivery/audit-native-evidence.py`（`5d46cf1c43553c0536454a3877b9e6aa20d3fb00a88a2c24910d77b2ea3014d6`）
  - `tests/test_shim_native_namespace.py`、`tests/test_shim_native_evidence.py`、`tests/test_shim_subagent_delivery.py` 及 README/README.zh
  - `docs/gateflow/shim-subagent-all-providers/`（control、两份最终契约、controller 裁决、location validation、全部 evidence 与冻结清单）以及 `docs/gateflow/shim-subagent-delivery/` 中本 PR 相关 probe/audit 变更
- Excluded scope: 三个无关 `docs/reviews/runner-handle-loss-20261023-*` 未跟踪文件（未读取/未修改）；私有 `endpoints.json`、凭据、Kimi 私有 TokenHub URL/key；原业务/调度/自选股会话；live 部署与 live shim；另一位并行 reviewer 的结论/artifact；历史业务 captures 未纳入本轮重读范围，仅按冻结 hash 核对完整性。
- Parallel review coverage: 无。本 reviewer 按要求独立审查，未委派 subagent，未读取另一位并行 reviewer 的结论。
- Evidence freeze: `docs/gateflow/shim-subagent-all-providers/review-freeze-v1.json`。我用系统时钟核对：该清单 `source_files` + `evidence_files` 共 481 项，当前工作区全部存在，SHA-256 与字节数 **481/481 完全一致**；冻结 base_ref 为 `0933796`，`head_before_source_commit` 为 `901cea1`。

### 实际执行的离线验证（未运行 vendor/native 模型）

本机沙箱默认禁止 loopback bind（`PermissionError: [Errno 1] Operation not permitted`）；受影响的 loopback 测试已在单条命令上按沙箱失败证据解除限制后重跑，未访问外部网络、未调用模型：

- 本 slice 直接测试：namespace **27 passed**，native evidence **33 passed**，delivery **13 passed**（合计 73）。
- 复用 mandatory checks 在当前树上重跑：`test_install_endpoints.py` **38 passed**、`test_provider_registry.py` **11 passed**、`test_shim_service.py` **11 passed**、`test_model_catalog_generation.py` **30 passed**（合计 90）。163 项 applicable unique tests 全部通过。
- `python3 -m py_compile`（shim / probe / auditor）通过；`git diff --check` 通过；默认历史 DS legacy audit exit 0。
- 冻结 auditor 重跑：MiMo A/4 `--scenario a` pass，MiMo B/2 `--scenario b` pass，MiMo A/4+B/2 aggregate pass（coverage a=true b=true）；Kimi A/2+B/2 aggregate pass；MiMo A/1 在最终 auditor（legacy helper 5d47 分支）pass；A/2 setup failure 与 A/3 incomplete failure 仍为 fail；默认 legacy DS audit pass。
- 历史七条 provider 的既有 attempt 在最终 auditor 下重审：GLM/2、GLM Flash/1、MiMo/2、MiMo Fast/1、Qwen/1、Hy/2 均 pass，observed mode 分别为 v1/v1/v2/v2/v1/v1；DS 走历史条件复用。

## Findings

### 1-未修复-低-README 仍把 input additional_tools 描述为 adapter 契约之外

- **入口/函数**: 用户面向文档 vs 生产 `native_agent_request(body, flatten=False)` 的 response-only map 采集路径。
- **文件(行号)**:
  - `README.md:526`：`Only top-level native descriptors seed the map; advertisement only through input additional_tools (as observed for MiMo Flash Lite) remains outside this adapter contract.`
  - `README.zh.md:484`：`映射仅来自顶层 tools 中的原生描述符；仅通过 input additional_tools 广告的格式（实际 MiMo Flash Lite 所用）尚不在本适配契约内。`
  - 生产实现：`codex-agent/bin/codex-auto-review-shim:293-298`（response-only 时 `containers` 同时收集顶层 `tools` 与 immediate `input[i].type == "additional_tools"` 的 `tools`）。
- **输入场景**: 运维/维护者阅读 README 后部署或诊断九路 route；或未来对 MiMo Flash Lite 路径做兼容性判断。
- **实际分支**: `flatten=False`（MiMo Flash）→ `containers` 含 additional_tools → 选中 `collaboration` group → 构造 six-entry map → `_relay_native_response` 实际激活。
- **预期行为**: 最终契约（`native-descriptor-location-plan.md` 第 13-16 行）已明确 response-only 可从顶层 `tools` 或 immediate `input[i].type="additional_tools"` 的 `tools[]` 取 map；README 应与最终实现/契约一致，并保留“request flatten 仅顶层”这一区别。
- **实际行为**: 中英文 README 均声称 additional_tools 广告“尚不在契约内”，与最终实现、A/4+B/2 的实际激活路径以及 location validation 文档直接矛盾。
- **直接证据**:
  - README 原文行号如上；working tree/freeze 中 README hash 分别为 `88381c2d…`、`448c4b3a…`，确认属于最终组合版本。
  - `native_agent_request` 的 `containers` 代码行；`location-implementation-validation.md:9` 明确写出两种来源；`evidence/mimo-flash/namespace-scenario-a-attempt-4/wire.json` 全部 11 个请求的 `descriptor_locations` 为 `input[0].tools[2]`、`containing_item_type=additional_tools`、非空 six-entry map。
- **影响**: 不是运行时缺陷；是用户可见的契约/文档漂移，会误导部署与后续兼容性判断，且与本 PR 的最终验收声明冲突。
- **建议改法和验证点**: 更新中英文 README 该段：说明 response-only route（MiMo Flash）从顶层 `tools` 和 immediate `additional_tools` 两种来源构建 map；request flatten（Kimi）仍仅顶层。验证：README 文本与 `native-descriptor-location-plan.md`、A4/B2 wire 的 descriptor location 一致；无需改生产代码。
- **修复风险（低/中/高）**: 低。
- **严重程度（低/中/高/严重）**: 低。

### 2-未修复-低-native-probe 的 observer 假定请求体非空且为 JSON，非 Responses/空 body 请求会在 probe 侧变成 502/400

- **入口/函数**: `install_observers().observe_open(req, timeout)`（并连带 `observe_fix(body)`）。
- **文件(行号)**:
  - `docs/gateflow/shim-subagent-delivery/native-probe.py:181-186`：`body = req.data`；`sha(body)` / `json.loads(body).get('model')`，无空值/非 JSON 防护。
  - `docs/gateflow/shim-subagent-delivery/native-probe.py:110-119`：`observe_fix` 对输入/输出 `json.loads` 无 try。
  - `codex-agent/bin/codex-auto-review-shim:823`：`do_GET = do_POST = ... = _handle`；`:702-745`：observer 异常会被 `_handle` 的 `except Exception` 捕获，`resp=None` 后返回 502；agent_message 路径的 `ValueError` 会返回 400。
- **输入场景**: Codex app-server 或任何调用方向 candidate 端口发出 GET/HEAD、无 body 请求或非 JSON body（例如模型列表/健康检查/未来端点）。
- **实际分支**: `req.data is None` → `sha(None)` 抛 `TypeError: object supporting the buffer API required`（已离线复现，未发网络请求）；`_handle` 捕获后走 `resp is None` → 502。非 JSON 的 POST 在 agent_message_fix 路由上会被 observer 的 `json.loads` 转为 400。
- **预期行为**: 诊断 observer 对非 Responses/非 JSON 流量应透明；至少记录一个最小 attempt（如 `body_sha256=None`、`model=None`）并直接调用 `original_open`，不应阻断/改写这类请求。
- **实际行为**: observer 在转发前抛异常，由生产 handler 转成 502/400，probe 不再是透明代理；这类请求也不会出现在 `wire`（`observe_fix` 只记录非空 body），因此可能被静默漏记。
- **直接证据**: 离线调用 `shim.upstream_open(Request(..., data=None, method='GET'))` 得到 `TypeError object supporting the buffer API required`；该调用在 `original_open` 之前失败。当前已验收 captures 的 `wire.json`/`candidate-transport.log` 只显示实际 `POST .../responses`（A4 11 个、B2 5 个、Kimi A2 7 个），未显示 GET/空 body，因此**不推翻本次 A/B 证据**。
- **影响**: 仅 validation harness；未来 probe run 若 app-server 发出非 Responses 请求，会产生 probe 侧 502/400、可能改变 app-server 行为或让证据审计漏记，不影响生产 shim 的用户路径。
- **建议改法和验证点**: 在 `observe_open` 开头判断 `req.data in (None, b"")` 或 `json.loads` 失败：记录最小 attempt 后直接 `original_open`，不进入 stage hash 链；`observe_fix` 同样跳过非 JSON body。增加一个 offline 单测：GET/空 body/非 JSON POST 均原样转发。
- **修复风险（低/中/高）**: 低。
- **严重程度（低/中/高/严重）**: 低。

## Open Questions

无。两个 finding 均有直接代码路径和可执行修复；其余疑点按既有 controller/plan owner 的明确限制归类为 Residual Risk，不作为未决 defect。

## Verification Evidence（按最终组合版本核对）

### 生产 shim 契约

- `agent_message_fix`：九条 routes 显式 `true`；loader 默认 false；env-only/新 route 默认 false；`fix_agent_messages` 只处理精确 `type="agent_message"`，校验 author/recipient 非空字符串、content 非空列表、每个 part 精确 `{type,input_text,text}` 或 `{type,encrypted_content,encrypted_content}`；正文顺序/空白/Unicode 逐 part 转为 input_text，metadata（含 id/author/recipient/internal metadata）以文本 envelope 保留；非法已知内容在 `upstream_open` 前 400；reasoning/工具参数/其它顶层 item 值不变；不解密真实密文。对应 delivery 13 项测试通过。
- 新 flags：`native_agent_request_flatten` 仅在 Kimi true，`native_agent_response_restore` 在 Kimi + MiMo Flash true；其余七条显式 false；loader 拒绝 flatten=true 且 restore=false；env-only 无该两 flag（默认 false）。
- Kimi `flatten=True`：只选顶层 `tools` 中 exact `type="namespace"` 且 name ∈ {`multi_agent_v1`,`collaboration`} 的 wrapper；只 flatten 其 function children，保留 schema/strict/扩展字段/顺序，description 确定性拼接；additional_tools 只参与 collision 检查，不 flatten、不进 map；`tool_choice` 若指向被 flatten 的原生 function 或原生 group → 400；unrelated/未知命名冲突按声明级 scoped 规则拒绝。`7cdaf30d…` → `a6246a4b…` 的 AST 对比与 actual Kimi A2/B2 输入 replay 证明 flatten=True 路径等价。
- MiMo Flash `flatten=False`：从顶层 `tools[]` 与每个 immediate `input[i].type="additional_tools"` 的 `tools[]` 选 native group；请求字节原样返回（native stage before==after）；selected wrapper 从 collision 扫描中排除自身；重复 selected callable、跨容器同名、native/non-native 声明冲突 → sanitized 400、零 upstream；disjoint group 合并。
- 响应恢复：仅对 mapped bare-name 的 `function_call`，仅当 `namespace` 缺失或 `null` 时补 group name；`namespace` 已匹配不改；显式不同（含 `""`、`functions`）→ NativeProtocolError。覆盖 SSE `response.output_item.added/done`、`response.completed.response.output[]` 与 nonstream JSON `output[]`；name/arguments/call_id/id/status/扩展 leaves 保持。SSE 逐 event 帧化，支持 arbitrary chunk、UTF-8、CRLF/LF/CR、multi-data、comment、`[DONE]`；非目标 event 原始字节透传；单 event 8 MiB 上限（nonstream JSON 同）；首事件在 headers 后立即 flush；中途冲突/截断/超限关闭连接，不伪造 terminal、不重试。active map 仅接受 absent/identity response encoding 与 SSE/JSON media；否则在 downstream headers 前 502。Guardian 在 `not guardian` 条件下 bypass 两阶段，保持原有 buffered/retry。
- 既有契约保持：model/auth 单请求 snapshot、Authorization/X-Api-Key/Api-Key 替换、NoRedirect、request_prefix、id_fix、json_fmt_fix、drop_tools_item、Lite/custom/additional_tools、streaming/guardian 均由旧路径测试和 `SevenRouteEquivalence` 覆盖。

### 九条 route 的 A/B 与来源版本

| Profile | 采用的证据 | 实际模型 / provider / effort | 实际 native 模式 | 来源版本与适用性 |
| --- | --- | --- | --- | --- |
| ds-flash | 历史 candidate-run-1/2 + `ds-reuse-check.json` | `deepseek-flash` → wire `deepseek/deepseek-flash` / deepseek / max | v2 direct | helper `cd8e9f21…`、route 旧对象；历史条件复用；最终 helper flags-off 等价测试覆盖 |
| glm | `glm/attempt-2` | `glm-5.3` / glm / max | v1 direct | helper `cd8e9f21…`、routes `28fabd…`；profile/registry/catalog 与当前一致；当前 auditor pass |
| glm-flash | `glm-flash/attempt-1` | `glm-5.3-flash` / glm_flash / max | v1 direct | 同上 |
| mimo | `mimo/attempt-2` | `mimo-v2.6-pro` / mimo / max | v2 Code Mode + Lite | helper `cd8e9f21…`；catalog `multi_agent_version=v2`、`tool_mode=code_mode_only`、Lite true；当前 auditor pass |
| mimo-fast | `mimo-fast/attempt-1` | `mimo-v2.6-pro-ultraspeed` / mimo_fast / max | v2 Code Mode + Lite | 同上 |
| qwen | `qwen/attempt-1` | `qwen3.8-max` / qwen / max | v1 direct | 同上 |
| hy | `hy/attempt-2` | `hy4` / hy / high | v1 direct | 同上 |
| kimi | `kimi/namespace-scenario-a-attempt-2` + B/2 | `k3` → wire `kimi-k3` / kimi / max | v1 direct（multi_agent_v1） | helper `7cdaf30d…`、routes `0dd8e0fd…`；flatten 路径与最终 `a6246a4b…` 等价；final auditor aggregate pass；用户授权 TokenHub override 未被改动/输出 |
| mimo-flash | `mimo-flash/namespace-scenario-a-attempt-4` + B/2 | `mimo-v2.6-flash` / mimo_flash / max | v2 Code Mode + Lite | helper `a6246a4b…`、routes `0dd8e0fd…`；A4+B2 aggregate pass |

- **MiMo A4/B2**：A4 11 个请求（8 parent + 3 child），B2 5 个（3 parent + 2 child）；全部 16 个 accepted 请求的 native stage `map` 为六项 `followup_task/interrupt_agent/list_agents/send_message/spawn_agent/wait_agent → collaboration`，`descriptor_locations` 为 `input[0].tools[2]`、`containing_item_type=additional_tools`，`before_sha256==after_sha256`，实际 outbound hash 与 stage 链一致；全部 200 `text/event-stream`，Content-Encoding absent/identity，实际 parser invocation 与 SSE event 处理计数 >0；`namespace_added_count=0`（上游已带正确 namespace），但 nonempty map + actual parser/active path + offline bare-wait replay 构成 activation 证据，未用空 map 充数。
- **MiMo A4 receipts**：exact child `01a1b6f0-b854-…` 的三个 distinct completed turns `…b85e…`、`…dd90…`、`…f6651…`；parent native receipt 行 29/42/62 分别精确为 `LIVE_PROBE_OK`、`LIVE_FOLLOWUP_b83399960ae0`、`LIVE_MESSAGE_OK_7c31d20ac519`；MESSAGE 单次、consume task 不含 token；无 parent file/JS/Code Mode call。A4 的 parent 没有执行 wait；上游 response 中出现过模型提议的 wait_agent（app-server 在收到 fresh FINAL 后没有执行；未进入 rollout function_call），实际 wait 集合为空，符合 “fresh FINAL 已在 context 即完成” 的修正语义。
- **MiMo B2**：独立 fresh child `01a1b6dd-60a5-…` 以 Code Mode `exec` 执行真实 `cat <fixture>`；supplement 有同 child/turn 的 `CommandExecution exec-c8292e5d-…`、exit 0、aggregated_output 与 fixture 完全一致；child final 精确等于 fixture；fixture 内容不在 parent prompt/dispatch；parent 未读文件。
- **Kimi A2/B2**：A/2 使用 v1 boolean `fork_context=false`、同 child `send_input`、两次 distinct completed turns 与 exact finals；A3 为 descriptor-backed N/A（实际 v1 只有 `send_input`，没有独立 `send_message`）；B/2 独立 child 以 `exec_command` 读取真实 fixture，CommandExecution/call-result span/exit 0/exact final 齐全；当前 auditor aggregate pass。
- **A2/A3 失败保留**：A/2 为零 HTTP、无 parent 的 `Operation not permitted` setup failure（exit 1）；A/3 为 11 请求、parent `…f188`、child `…9626` 的 incomplete/aborted（exit -2，808.86s），MESSAGE/consume 未完成；两者 audit 仍 fail，未被 A/4 覆盖或改写。controller fixture cleanup 记录与 delegate 的 no-target race 记录同时保留。
- **七条有界复用**：routes `28fabd9d…` → `0dd8e0fd…` 的差异仅为九条 route 新增 `native_agent_request_flatten/native_agent_response_restore` 字段（七条 false、Kimi true/true、MiMo Flash false/true）；七条 profile/registry/installed catalog 的 launch hash 与当前文件一致（shim/routes/harness 差异为预期）。`SevenRouteEquivalence` 对七条 route 的 200 SSE 与 429 gzip、identity/gzip 请求、完整 request/response/headers 与 `cd8e9f21…` baseline 一致，测试通过。该复用不是最终 helper 上一次 fresh inference，文档已明确。
- **DS 条件复用**：历史两次真实 v2 run、helper `cd8e9f21…`、DS route 对象/catalog/wire model 不变；legacy audit AST 未变；最终 helper flags-off 等价测试覆盖 DS route；未把新 generic 断言追溯冒充旧 capture。
- **v2 receipt 修正**：`controller-wait-receipt-decision.md` 的语义由 auditor 实现——v2 不强制额外 wait，但要求 exact parent-received native FINAL（作者/接收者/text/turn/provenance/line/time interval/唯一）关联 child 独立 completed turn；每个实际 wait 仍校验 namespace/result/target/error；timeout 单独、child-local final、prose、wrong-author/recipient/token/turn/provenance、duplicate、stale/out-of-interval、failed dispatch/wait、wrong namespace 均被 mutation tests 拒绝；v1 仍要求 persistent wait status/result。A/3 的旧 prompt 失败保留；新 `short_v2_completion_prompt` 只用于 declared short v2，v1/default all 不变。
- **失败记录/证据完整性**：冻结清单 481 项 hash/size 全部匹配；A1 初始 fail audit 与 receipt-aware audit 并存；A2/A3 失败目录、GLM/MiMo attempt-1、Kimi A1、Hy A1、MiMo Flash attempt-1/2 等未改写；`preservation-check.json` 记录 1380 个既有文件除 5 个授权文件 + controller-owned `control.md` 外 hash 不变；三个 runner-handle-loss 文件未被触碰。

## Adversarial Failure Pass

- 请求契约：重复 selected callable、跨容器同名、selected 与 unrelated/native 声明冲突、未知 descriptor 显式映射名、structured native `tool_choice`、unsupported wrapper metadata/child type、absent/非数组 tools、additional_tools 非数组、非目标 duplicate/unknown/schema-property name 均已由测试覆盖；失败路径零 upstream。
- 响应契约：absent/null/matching/conflicting namespace、JSON/SSE 四种 output 位置、name/arguments/call_id/id/status/extension 保持、single-byte/UTF-8/CRLF/multi-data/interleaved delta、非目标原始字节、malformed/truncated/oversize/conflict、first-event 时序、concurrent per-request map、gzip/deflate/unknown/stacked encoding、Content-Type、Content-Length/Transfer-Encoding/Connection-nominated/Trailer headers、guardian 原 buffering/retry 均有测试；未发现可实际触发的生产失败路径。
- A/B 反例：wrong child、stale turn、token leak、duplicate MESSAGE/completion、parent read/JS、wrong call association、missing execution、wait namespace/error/timeout、wrong scenario/argv/launch、missing B、A/B aggregate mismatch 均被 auditor mutation tests 拒绝；A4/B2 是 final reader 下的实际 pass。
- 未发现新 production blocker；两个 finding 分别是文档漂移与 probe harness 健壮性，均非产品运行时缺陷。

## Project Instructions / Coupling / Semantic Ownership

- **项目指令**: 分支复用 `fix/shim-subagent-message-delivery`；实现由 gpt-6-sol/Codex 完成；本次 review 由 ds-flash/Claude runtime 执行；未委派、未修改实现、未 commit/push/deploy/restart、未发送消息、未读取私有配置/业务会话；未读取另一位 reviewer 结论；未触碰三个无关 runner 文件。与 `AGENTS.md` 及用户本次边界一致。
- **耦合**: 两个新 flag 是显式 per-route opt-in，无全局默认/新 route；生产 shim 只在两个 helper + handler 两个分支内扩展，未改变 catalog/policy/Lite/Code Mode/runner/skill；probe/auditor 参数化复用而非复制九套脚本；auditor 独立重算 map/location/receipt，不 import 生产 helper 的 allowlist。未发现反向 import、跨层穿透或共享可变状态。
- **Semantic ownership**: native namespace 的最终语义 owner 是 Codex/gateway 协议；shim 仅在已证明的 `multi_agent_v1`/`collaboration` 兼容边界做 request flatten / response restore，map 来自当前请求的实际 advertised function children，无 alias、历史激活、MCP 泛化或跨请求状态。`agent_message_fix` 的 plaintext 假设、identity-only response encoding、top-level-only flatten 和 future descriptor 限制均由 plan/controller 明确归属，不属于“下游 fallback 补齐上游 contract”的无 owner 漂移。未发现新的 ownership drift；相反，README 的 additional_tools 陈述是本轮唯一 contract/doc 漂移（finding 1）。

## Residual Risk

- **future/dynamic descriptor location、additional_tools 新容器/新 index、压缩 active response**：明确在最终契约之外；当前实现只在已证明的两类位置工作，上游若改为压缩或新位置，active map 会 502/不激活，需 bounded contract revision。
- **selected callable 重复激活**：同/跨容器重复或同名跨 native group 仍保守 400；未来若真实协议要求重复声明，需要 controller 新决策。
- **真实 ciphertext / 新 Codex schema**：`agent_message` plaintext 假设继承 prior work unit 的已知限制；真密文可能无法可靠检测或产生 task-invisible 行为，只保证结构性非法已知内容 400。
- **A/B 覆盖范围**：MiMo/Kimi 和七条的 A/B 证据、Kimi A2/B2 的 helper 等价、七条的 helper/route/catalog 有界复用，均不是最终 helper 上的一次 fresh inference；不声称当前外部 service availability 或所有 future provider 通用。
- **Kimi A3 N/A**：仅因实际 v1 descriptors 没有独立 `send_message`；若未来 v1 广告该能力，auditor 会拒绝 N/A。
- **v1/default all prompt**：本轮只修正 declared short v2 prompt；default `all` 与 v1 prompt 保持旧文本，未来 `all` v2 运行仍可能触发旧 wait 语义。
- **probe 证据最小化**：`before_tools`/`after_tools` 仍保留完整顶层/附加工具描述（含 MCP schema/description），`descriptor_sources` 仅投影 type/name；本次 captures 按用户判断为无害，但这种证据保留粒度不是严格 hash-only。
- **auditor receipt provenance**：v2 receipt 的 `content_item_metadata` 期望 `namespace: collaboration` 是从实际 Codex 0.167.0 v2 形状硬编码；未来 provenance 形状变化会使 audit fail（不会被误判为 pass）。
- **live 状态**：helper/routes 未 sync/restart，installed shim 仍为旧版本；PR #70 仍为 draft，由用户手工 merge；live 部署需用户单独授权 `./scripts/sync-codex-agent.sh`，不得向原业务 parent 发送 callback。
- **环境**：本机沙箱禁止 loopback bind，相关测试在解除单条命令限制后通过；这是 review 环境限制，不是产品失败。

## Findings Summary

- Finding 数量：**2**（均为低严重度：1 个 README/README.zh 文档漂移，1 个 native-probe observer 对空/非 JSON 请求的 harness 健壮性）。
- Blocker：**0**。两个 finding 不推翻 A/B 证据，也不涉及已 sync live 的代码。
- 结论：**PASS（no blocker；2 low findings）**。生产 shim、九条 routes、最终 source/tests/probe/auditor 和九条 A/B 证据在冻结版本上自洽；README 需随 accepted finding 修正，probe observer 可择机加固。
- Artifact: `docs/reviews/code-review-20261108-012340-ds-flash-all-shim-providers.md`
