# Code Re-review: accepted-fix affected surface

实际复审身份：`ds-flash` / Claude runtime。仅审查最终 accepted-fix 及其实际影响面；未读取另一并行复审结论。

## Scope

- Mode: PR Review Mode 的 affected-surface re-review（非完整复审），仓库 `/Users/leo/workspace/code-is-cheap`，PR #70，分支 `fix/shim-subagent-message-delivery`。
- Base: `09337967910277785b82874326d7f49156c9395b`（freeze v2 `base_ref`）；集成点 `head_before_source_commit` = `901cea16928ef2db01ce774c99652f62fb3dca68`。
- Output file: `docs/reviews/code-rereview-20261108-021422-ds-flash-all-shim-providers.md`
- Review point: workspace 最终组合版本，逐字节对上 [review-freeze-v2.json](../gateflow/shim-subagent-all-providers/review-freeze-v2.json) 的 9 个 source/test 文件（helper `55a5bd5b5e120cac648d9ad86c366430a9a535bf79d796cf58a79b44ffbb9b9a`）。
- Included scope:
  - DS-1/MiMo-1：README 中英 `additional_tools` 契约修正及 route-level flag 边界。
  - DS-2：probe observer 对 GET/空 body/非 JSON/非对象 JSON 的透明性、独立最小 metadata、thread-local 隔离、生产 transforms 保留、正常 native/guardian 对照、HEAD 501。
  - MiMo-2：active-map 成功路径标准 status/model/rewrite 日志恢复、`_summary` 非数组 tools 防护、helper 增量仅诊断及 a6246 有界适用。
  - Accepted 回归改进：真实 MiMo A/4 pass、A/3 incomplete fail 及 v2 fresh-FINAL/wait 严格性。
- Reused scope（原完整审核已确认、允许有界复用）：未改动的生产 native 协议/mapping/restore、guardian/retry/auth、auditor 规则、九路 captures、catalog/policy/private endpoint、Lite/CodeMode 默认面。未重读数十 MB 历史 captures，未重跑九路 vendor/API/native inference。
- Parallel review coverage: 无（本轮为单方复审，未委派）。

## Findings

未发现实质性问题。

三个逻辑 accepted findings 均已在最终冻结版本中实际修复，且未发现由修复引入的新 material defect：

1. **README additional_tools 漂移 — fixed。** 英文与中文均改为：Kimi request flatten/mapping 仅使用顶层 `tools` 原生描述符；MiMo Flash response-only map 读取当前请求顶层 `tools` 与直接位于 `input[type=additional_tools].tools` 的描述符，完整请求字节保持不变。实现核对：`native_agent_request` 在 `flatten=True` 时 `candidates = tools`，仅在 `flatten=False` 时读取上述两个容器，且无 selected/mapping 时原字节返回。新 flag `agent_message_fix`、`native_agent_request_flatten`、`native_agent_response_restore` 在 loader 中均为 `r.get(..., False)` route 级判定，无文件顶层继承；legacy flags 保持原 doc-level 默认。`shim-routes.json` 为 9 条 managed route 显式设置，Kimi 两项 native flag 均 true、MiMo Flash 仅 response restore，未新增 route/endpoint。
2. **probe observer 自造 502/400 — fixed。** `observe_fix` 先执行原生产 `fix_agent_messages`，仅在 ingress/egress 均为 JSON dict、存在非空字符串 `thread_id` 且路径（去 query）以 `/responses` 结尾时才建立 native record；其余请求不进入 wire。`observe_open` 无 record 时调用原 `original_open`，仅独立记录 method、去 query path、`body_bytes`、`body_sha256`、`model=None`、`http_status`、`error_class` 七字段，不记录 headers/query/完整 body/凭据；异常原样重抛，HTTPError 语义与无 observer 对照一致。独立 `passthrough-requests.json` 与 `wire.json` 分离；record/attempt 在 `_handle` 入口、`observe_fix`、`observe_open` 处重置，串行同 worker 测试证明旧 record 不被后续 GET/非 JSON 请求修改。`observe_fix` 的 JSON 防护只在无有效 record 时旁路记录，生产 transforms 照常执行（guardian model swap/id fix/json format/drop tools 测试通过）。HEAD 未新增 handler：`do_HEAD` 不存在，实测 HEAD `/v1/responses` 与 `/` 均为 501。
3. **active-map 成功路径缺标准日志 — fixed。** 原标准行按原语句 AST 前移至 active-map early return 之前，active 成功路径重新记录原 status/model/encoding/rewrite/顶层工具摘要；实际日志捕获未见 prompt、arguments、header、auth key、私有 URL、thread/session 标记。`_summary` 对 absent/null/object/number/boolean/string/敏感 object 等非数组 `tools` 均安全返回 `tools=none`，不产生新失败，且每请求仅一条标准行。helper 相对 a6246 的差异仅为该日志块位置与 `_summary` 非数组防护；排除该诊断块与 `_summary` owner 后 Handler 及 Handler 外模块 AST 完全一致，mapping、request/response bytes、headers、auth/model rewrite、guardian/retry 与流式 first-event 契约均保持。
4. **A/4、A/3 回归 — implemented。** 离线测试直接以当前 auditor 重审真实不可变目录：MiMo A/4 strict PASS、coverage a=true/b=false、11 requests/3 receipts/6 项 collaboration map/0 namespace additions；A/3 仍 incomplete FAIL、coverage a=false；原 captures、旧 verdict 与源 snapshot 均未改写。v2 fresh parent FINAL 的 independent child turn/author/recipient/order/token/provenance、wait-error/dispatch-error 仍被拒绝；删除全部 wait 后仅凭已收 FINAL 仍通过，未重新要求额外邮箱更新。

相关 owner 已由 accepted adjudication 记录：未来版本/backend 或新协议反例归 shim/protocol 及 provider maintainers；live sync/部署与业务父线程回报由用户/controller 在授权后执行。

## Verification Actually Executed

- 9 个 freeze v2 source/test 文件实际 SHA-256 与字节数逐一比对一致；测试执行后再次比对未变。
- `helper-v-a6246.diff` 核对为 2 处诊断性差异；`test_a4_baseline_all_nonlogging_source_semantics_unchanged` 通过。
- `unchanged-path-90-reuse.json` 的 4 个复用测试源与 4 个归档通过日志 hash 逐一核对一致（38+11+11+30=90）。
- 实跑 affected 套件：namespace 37、native evidence 36、subagent delivery 13，合计 **86 tests，全部 OK**（首轮因沙箱拒绝本地 loopback bind 报 `PermissionError`，关闭该限制后重跑通过；无真实 API/native inference）。
- 实测生产 helper HEAD 请求返回 501。
- A/4、A/3 五类输入文件 hash 与 `actual-a4-a3-current-audits.json` 一致；auditor hash `5d46cf…` 与 freeze 一致。
- 176 项适用 = 86 实际执行 + 90 有界复用；未重新开启不受改动影响的设计/未来能力议题。

## Open Questions

无。

## Residual Risk

- 最终 helper 未重新生成九路 native captures；九路适用性仍是原 accepted captures（原始 launch/helper hashes）加本轮观察到的诊断-only source/byte 等价链，不代表最终 helper 已重新验证外部 provider 可用性。
- 新增 `passthrough-requests.json` 为附加产物；当前 auditor/测试按固定文件名读取，未受影响；若未来有工具假定 attempt 目录 JSON 集合固定，需由 probe 维护方适配。
- source、routes 与 README 尚未 live sync/restart；部署需用户显式授权，原业务父线程回报在 live sync 前继续禁止。
