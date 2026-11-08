# Code Review

## Scope

- Mode: current changes（`$deepreview --base main`；PR #70 最终组合版本，含已提交与当前未提交改动）
- Branch or PR: `fix/shim-subagent-message-delivery`，draft PR #70（用户手工 merge）
- Base: `main` @ `09337967910277785b82874326d7f49156c9395b`（merge-base 同值）；分支 HEAD `901cea16928ef2db01ce774c99652f62fb3dca68`
- Reviewer identity: **mimo-flash / Claude runtime**（本提示指定）；未读取并行 ds-flash reviewer 的任何结论（其产物出现于 `docs/reviews/` 后未打开）
- Output file: `docs/reviews/code-review-20261108-014400-mimo-flash-all-shim-providers.md`
- 版本冻结核验: `docs/gateflow/shim-subagent-all-providers/review-freeze-v1.json` —— 9 个 source 文件 + 472 个 evidence 文件逐 SHA-256 与当前工作树**全部一致（0 mismatch）**；`control.md` 等 4 个 mutable controller 记录按清单排除。本次审查对象即该冻结版本。
- Included scope:
  - 生产 shim `codex-agent/bin/codex-auto-review-shim`（883 行全文走读，含 committed+unstaged 合并 diff）、`codex-agent/shim-routes.json`（九路由标志）、双语 README。
  - 测试 `tests/test_shim_native_namespace.py`、`tests/test_shim_native_evidence.py`、`tests/test_shim_subagent_delivery.py`（全文走读）。
  - 参数化 probe `docs/gateflow/shim-subagent-delivery/native-probe.py` 与 auditor `docs/gateflow/shim-subagent-delivery/audit-native-evidence.py`（全文走读）。
  - 审查入口与契约：`control.md`、`location-implementation-validation.md`、`location-current-matrix.json`、`implementation-native-namespace.md`、最终契约 `native-namespace-plan.md` + `native-descriptor-location-plan.md`、`controller-wait-receipt-decision.md`。
  - 关键最终证据实质检查（非抽样替代）：MiMo Flash A/4 与 B/2、Kimi A/2 与 B/2 的 wire/rollout/supplement/audit/aggregate/launch/source-snapshots；A/2 setup-failure、A/3 aborted 等失败保留；七路由 bounded reuse 记录；`attempt-matrix`/`namespace-current-matrix`/`location-current-matrix` 的历史保留。
- Excluded scope: 三个无关 runner-handle-loss untracked 文件（未触碰）；私有 `endpoints.json`、凭据、原业务/调度/自选股会话（未读取；仅使用 probe 的仓库内无害捕获与 `privacy-check.json` 结论）；并行 reviewer 产物；captured JS 未执行；未运行任何 vendor/native 模型调用。
- Parallel review coverage: 无 subagent（用户指示不委派）。全部上述区域由主 reviewer 直接走读与复核。
- 验证记录（本 reviewer 独立执行）:
  - 焦点测试全绿：namespace 27 + evidence 33 + delivery 13 = **73 current**；install_endpoints 38 + registry 11 + service 11 + catalog 30 = **90 unchanged-path reused**；合计 163，与 `location-offline/offline-validation.json` 声明一致。loopback 测试需关闭 sandbox 重跑（sandbox 拦截本地 bind，非代码失败）。
  - `py_compile` 三文件、`git diff --check`、默认 legacy DS audit（exit 0，candidate-run-1/2 全过）均通过。
  - 离线 auditor 复跑：mimo-flash A/4、B/2、kimi A/2、B/2 单目录全部 `passed=True`；`mimo-location-a4-b2-aggregate` 与 `kimi-a2-b2-final-receipt-reader-aggregate` 均 `passed=True, coverage={a:true,b:true}, errors=[]`；历史 verdict 保持（mimo A/1 pass-under-receipt-reader、A/2、A/3 fail、kimi A/1 fail、kimi B/1、mimo B/1 均与既有 audit 一致）。
  - AST 等价独立复核：最终 helper `a6246a4b…` vs Kimi A/2 启动基线 `7cdaf30d…`，20 个 function/class 中**仅 `native_agent_request` 变更**，19 个不变，模块级常量无差异；与 `final-source-bounded-reuse.json` 声明一致。
  - 启动 hash 独立复核：A/4 十项 launch hash（helper/routes/card/registry/catalog/probe/auditor/三测试）与当前文件全等；B/2 与 Kimi A/2+B/2 的 launch-time harness 差异项均在各自 attempt 目录以 `<hash>.source.gz` 可取回且解压校验通过；A/4+B/2 aggregate 的 production 比较（helper/routes/card/registry/catalog）全等。
  - A/4 交付事实独立复核：11 请求全部 `flatten=False`、六 entry map、唯一 descriptor 位置 `input[0].tools[2]`/`additional_tools`、stage 前后 hash 相等、11×200、identity 编码、parser 实际调用；四次原生派发（spawn 中文字面 `只回复一行 LIVE_PROBE_OK` / followup / 恰好一次 send_message / 无 token 的 consume）；子代三个独立 completed turn（`LIVE_PROBE_OK`、`LIVE_FOLLOWUP_b83399960ae0`、`LIVE_MESSAGE_OK_7c31d20ac519`）；父代 FINAL 回执 line 29/42/62 payload 逐字匹配、顺序正确；子代历史仅 4 个 envelope（含恰好一个 MESSAGE）。
  - B/2 交付事实独立复核：5 请求同 active map；子代唯一 Code Mode `exec` call `ctc_7690…` → CommandExecution line 18（call line16 < execution < output line19）、`cat <fixture>`、exit 0、`aggregated_output` 与 child final 精确等于随机 fixture；父代 prompt 不含 fixture 内容、父代无文件/JS 调用。
  - Kimi A/2+B/2：v1 持久 wait（completed 状态含精确 finals）、顶层 `tools[7]` flatten（stage_changed=True）、A3 descriptor-backed N/A、B 子代 `exec_command cat` exit 0 精确 final；A/2、B/2 启动 helper 为 `7cdaf…`，经上述 AST+replay 等价证明适用最终源。

## Findings

### 1-未修复-[中]-README（中英双语）仍声明 additional_tools 不在适配契约内，与最终已实现行为直接矛盾

- **入口/函数**: 生产 `native_agent_request`（response-only 路径）的 map 来源选择；文档入口为 README 两段路由说明。
- **文件(行号)**: `README.md:526`（“Only top-level native descriptors seed the map; advertisement only through input `additional_tools` (as observed for MiMo Flash Lite) remains outside this adapter contract.”）、`README.zh.md:484`（“映射仅来自顶层 tools 中的原生描述符；仅通过 input additional_tools 广告的格式（实际 MiMo Flash Lite 所用）尚不在本适配契约内。”）；对照实现 `codex-agent/bin/codex-auto-review-shim:293-298`（containers 合入 `input[i].tools`）与 `:298`（response-only `candidates` 取两容器全部条目）、`:335-336`（response-only 返回原字节+map）。
- **输入场景**: 任何读 README 判断 MiMo Flash Lite（native group 仅出现在 `input[0].tools[2]` 的 `additional_tools`）是否被覆盖的维护者/操作者；以及未来按文档“修正”代码的改动。
- **实际分支**: response-only（`flatten=False`，mimo-flash 路由）下 `containers` 同时含顶层 `tools` 与 immediate `additional_tools`，`selected` 从中选取原生 namespace → additional_tools **确实** seed map。
- **预期行为**: 最终契约（`native-descriptor-location-plan.md` 规则 2，controller 已裁决接受）为 response-only 路径允许且仅允许两个声明容器；README 应描述该已交付行为。
- **实际行为**: 双语 README 仍写“仅顶层”“additional_tools 尚不在本适配契约内”——这是**位置补丁之前的旧契约文本**，与最终代码、与本 PR 的核心修复（MiMo Flash active-path 激活）直接矛盾。
- **直接证据**: 本 reviewer 直接调用 `native_agent_request(json.dumps({'input':[{'type':'additional_tools','tools':[collaboration.wait_agent]}]}), False)` 返回 `{'wait_agent':'collaboration'}`（非空 map，原字节不变）；A/4+B/2 全部 16 个请求的六 entry map 正是来自 `input[0].tools[2]`（wire 证据）；`native-descriptor-location-plan.md` 明确 “Response-only path: two known sources”。
- **影响**: PR 自身的用户可见契约文档错误——低估已交付覆盖范围，误导运维/维护者（例如误以为 mimo-flash 的 additional_tools 路径仍未覆盖，或反过来按旧文档回退实现）；文档与实现漂移会在下一次改动时被“按文档修代码”放大。
- **建议改法和验证点**: 将两段末句改为与 `native-descriptor-location-plan.md` 一致的描述：map 来源为当前请求顶层 `tools` 与 immediate `type="additional_tools"` 项两处（response-only）；Kimi flatten 仍仅顶层；重复/冲突声明与其余边界不变。验证点：改后 grep 双语 README 无“仅顶层/尚不在”残留，并与 `native_agent_request` 行为对照。
- **修复风险（低）**: 纯文档改动，无运行时影响。
- **严重程度（中）**:

### 2-未修复-[低]-active-map 成功响应跳过既有标准每请求日志行，两条启用路由的生产可观测性弱于其余七条

- **入口/函数**: `Handler._handle` → `Handler._relay_native_response`。
- **文件(行号)**: `codex-agent/bin/codex-auto-review-shim:747-749`（2xx+native_map 直接 `return`，早于 `:754-759` 的标准日志行）；native 路径自身日志仅 `:610`（`native response: restored=N relayed=XB`）与 `:613`（固定错误类）。
- **输入场景**: kimi 或 mimo-flash 路由上任一 2xx 且 map 非空的 Responses 成功请求（生产常态路径）。
- **实际分支**: `if native_map and 200 <= resp.status < 300: self._relay_native_response(...); return` —— 在 `POST {path} -> {status} model=… enc=… rewrite=… tools=…` 行之前返回。
- **预期行为**: 既有每请求诊断行（含状态码、model、rewrite how、工具摘要）对九条路由保持可用；新增日志按契约只增加 route/flags/stage/counts/fixed-class，而非删除既有行。
- **实际行为**: 两条启用路由的成功请求只剩 `native response: restored=… relayed=…B`（无 path/status/model/rewrite）；七条 flags-off 路由仍打标准行——同一故障排查面上两套路由日志粒度不一致。
- **直接证据**: 代码控制流 `:747-749` 与 `:754-759` 的先后关系；`:610` 日志内容字段清单；`test_shim_native_namespace` 中成功 relay 用例不断言标准行（仅 `_log` 存在性）。
- **影响**: 生产上无法从日志确认 kimi/mimo-flash 成功请求的 status/model/rewrite（例如模型映射失败的静默 passthrough `how=none` 不再可见）；仅影响诊断效率，不影响正确性。
- **建议改法和验证点**: 在 `_relay_native_response` 进入前（或其内）补打包含 status/path/model/how 的标准行，或把标准行字段并入 `:610`；补一条断言成功 relay 仍输出含 status/model 的日志测试。
- **修复风险（低）**: 日志字段增加，无协议影响；注意不引入 prompt/args 泄漏（仅既有字段）。
- **严重程度（低）**:

## Open Questions

- 两个新 flag（`agent_message_fix`、`native_agent_*`）仅读取 route 级键（`load_routes` `:503-505`），忽略文件顶层默认；而同文件既有 flag（`id_fix`/`json_fmt_fix`/`drop_tools_item` `:500-502`）支持 `doc.get(...)` 文件级默认。`test_route_flag_explicit_default_off_all_managed` 明确把“文件顶层 `agent_message_fix: true` 被忽略、结果 `[False, True]`”固化为预期。这可能是“九路由显式 opt-in、默认全关”的有意收紧（README 也写 “explicitly enable”），但与同文件 sibling flag 的配置惯例不一致：按惯例把键放文件顶层的用户会被静默忽略。本 reviewer 未将其计为确定 defect——请 controller 裁决是有意契约还是应补 `doc.get` 兜底/在 README 注明“仅 route 级生效”。

## Residual Risk

- **测试固化面**: mimo-flash `namespace-scenario-a-attempt-4`（当前 A 验收捕获）与 a-attempt-3（aborted 保留）没有被任何单元测试钉住其 audit verdict（`namespace_case` 硬编码 attempt-1；kimi attempt-2 与 mimo attempt-1 有钉）。本 reviewer 已手动复跑 A/4 audit 通过、A/3 失败保持，且“零 wait + 精确回执”的 A/4 形态已由 `test_v2_fresh_parent_receipts_need_no_extra_mailbox_wait`（对 attempt-1 的去 wait 变体）覆盖契约逻辑；但未来 auditor 回归不会被 A/4 快照自动拦截。
- **有界复用而非最终源新推断**: 七条路由为 flags-off 等价复用（DS 保持 conditional historical）；Kimi A/2+B/2 以 `7cdaf…` 启动、经 AST+字节 replay 等价适用 `a6246a4b…`。最终 helper 上七路由与 Kimi 没有新推断；外部上游可用性未重新探测（契约明示）。
- **契约明示的边界（非缺陷）**: 重复 selected native callable 激活不支持（显式 400）；未来其它 descriptor 位置/动态 only 广告不在覆盖内；active map 压缩响应按契约 502；Kimi flatten 路径 additional_tools 中的原生组不参与 map（有测试钉住，属接受的 top-only 契约）。
- **SSE 空 `data:` 心跳**: active-map 下 `data:`（空值）事件会因 JSON 解析失败触发 502/断流，而 flags-off 路由原样透传；这符合“malformed JSON 即停”的已接受契约，且现有捕获中无此形态，但若未来上游改用 `data:` 心跳（SSE 规范允许），两条启用路由会先于其它路由失败。注释型心跳（`: …`）已验证透传。
- **per-capture 审计不逐事件字节核对非目标 SSE**: auditor 仅对含 mapped call 的事件做 hash/字段核对；非目标事件的字节保持由同一生产函数的单元测试（raw passthrough 全字节等价）保证，而非每份捕获重证。
- **验证环境**: loopback 服务测试在默认 sandbox 下因本地 bind 被拒（EPERM），本 reviewer 在关闭 sandbox 后重跑通过；与代码缺陷无关。
- 未运行任何真实 API/模型调用；未执行 captured JS；未读取并行 reviewer 结论、私有 endpoints/凭据或业务会话；未 commit/push/deploy/restart/发送任何消息。
