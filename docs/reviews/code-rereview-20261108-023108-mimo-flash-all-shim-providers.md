# Code Review — Accepted-fix 受影响面复审

## Scope

- Mode: affected-surface re-review（Gateflow 修复闭环的必要 re-review；不重复完整审核，不重开未受影响的设计/未来能力议题）
- 实际 provider/runtime: **mimo-flash / Claude runtime**（本提示指定；未委派任何子 Agent）
- Branch or PR: `fix/shim-subagent-message-delivery`，draft PR #70（用户手工 merge）
- Base: `main` @ `09337967910277785b82874326d7f49156c9395b`
- Output file: `docs/reviews/code-rereview-20261108-023108-mimo-flash-all-shim-providers.md`
- 冻结点: `docs/gateflow/shim-subagent-all-providers/review-freeze-v2.json`（9 source + 527 evidence = 536 文件）；本次逐文件核对全部 536 项 SHA-256 与 bytes，**0 mismatch、0 missing**；mutable controller 记录（`control.md`、`review-adjudication.md`、`closeout.md`、`delivery-verification.json`）按清单排除。最终 helper `55a5bd5b5e120cac648d9ad86c366430a9a535bf79d796cf58a79b44ffbb9b9a` 与 freeze 一致。
- 复用的既有结论: 本人完整审核 [code-review-20261108-014400-mimo-flash-all-shim-providers.md](code-review-20261108-014400-mimo-flash-all-shim-providers.md)（v1 冻结点，2 findings + 1 open question + residual 清单）对未变生产协议、九路 A/B、evidence 的明确结论；**未读取**并行 ds-flash 复审产物（`code-rereview-20261108-021422-...` 出现于目录后未打开）。
- 本次实际增量（v1 → v2，逐字节独立复核）:
  | 文件 | v1 | v2 | 性质 |
  | --- | --- | --- | --- |
  | `README.md` | `88381c2d…` | `bf644dc0…` | DS-1/MiMo-1 文档修正 + route-only 边界说明 |
  | `README.zh.md` | `448c4b3a…` | `afed9549…` | 同上中文 |
  | `codex-agent/bin/codex-auto-review-shim` | `a6246a4b…` | `55a5bd5b…` | MiMo-2 日志修复（`_summary` 防御 + 标准日志块前移） |
  | `docs/gateflow/shim-subagent-delivery/native-probe.py` | `6fde7ff9…` | `8fc7a3e8…` | DS-2 observer 透明化 + 独立 passthrough metadata |
  | `tests/test_shim_native_namespace.py` | `a78f54c4…` | `381ffc9b…` | 5 项 observer + 5 项日志/等价/时序回归 |
  | `tests/test_shim_native_evidence.py` | `278d57fc…` | `914d80e5…` | A/4、A/3 与 v2 wait 回归 |
  | routes / auditor / delivery tests | — | 与 v1 相同 | 未变（`0dd8e0fd` / `5d46cf1c` / `dda2f537`） |
- 本 reviewer 独立执行的验证:
  - **焦点测试全绿**: namespace **37** + evidence **36** + delivery **13** = **86 tests，全部通过**（loopback 套件首次在 sandbox 内因本地 bind EPERM 失败，按沙箱限制关闭 sandbox 后重跑通过，非代码失败）。
  - **helper AST 等价独立复核**: v1 gzip（`before-codex-auto-review-shim.gz`）SHA == `a6246a4b…`，且解压字节 == MiMo A/4 launch 的 `<a6246….source.gz>` 快照；相对当前 helper：Handler 外模块 AST 相同，Handler 方法中仅 `_summary`、`_handle` 变化，排除标准诊断块（warn/model+tools/`_log` 三条语句）后 `_handle` AST 相同，诊断块本身 AST 相同。独立 diff 全部内容仅 42 行，与 `helper-v-a6246.diff` 一致。
  - **freeze 全量 hash 核验**、**90-reuse 记录核验**: `unchanged-path-90-reuse.json` 四项测试源（38+11+11+30=90）与归档通过日志的 SHA-256 均与当前文件匹配、archived exit 全 0；日志本身在 freeze 内。
  - **证据脚本复跑**: `before-counterexamples.py`（4/4 修复前反例，`original_open` 调用 0）与 `normal-observer-equivalence.py`（4/4 正常 native/guardian 对照，wire 除 monotonic 外逐字节、请求/响应 bytes 相等，`native_inference_runs=0`）复跑输出与冻结文件**逐字节一致**。
  - `git diff --check` exit 0；六个相关文件 `py_compile` 通过；复审运行未改动任何被跟踪文件。
  - 两份步骤化 `verify-scope.py` 因其 entry manifest 属于更早时点而在第一条入口断言处退出（预期内：其 after 哈希全部等于 v2 freeze 当前值；`control.md`/`review-adjudication.md` 属清单排除的 controller 记录），其核心 AST/A4/A3 主张已由上述独立核验覆盖。
- Excluded scope: 私有 endpoints/凭据、业务会话、并行 reviewer 结论、真实 API/native probe、九路新 inference、commit/push/deploy/restart、任何消息/callback；captured JS 未执行。
- Parallel review coverage: 无 subagent（用户指示不委派）。

## Findings

未发现实质性问题

三项逻辑 accepted findings 的修复状态（逐条按本次四项检查核对）：

1. **DS-1 + MiMo-1 README additional_tools 修正 —— 已修复**。中英 README 均改为：Kimi flatten/map 仅顶层 `tools`（与 `native_agent_request` `candidates = tools if flatten` 一致）；MiMo response-only map 读当前请求顶层 `tools` 与 immediate `input[type=additional_tools].tools`，原请求字节保持（非 flatten 路径 `return body, mapping` 原样返回，测试断言 upstream 收到 `enc(doc)` 原字节）；旧的“仅顶层 / 尚不在本适配契约内”措辞 grep 无残留；三个兼容 flag 仅 route 级、无文件顶层继承（`load_routes` 三键只读 `r.get(…, False)`，legacy 三键保留 `doc.get` 历史继承；loader 测试显式固化文件顶层 true 被忽略），未新增全局兜底，符合已接受的 opt-in 契约。
2. **DS-2 probe observer 透明化 —— 已修复**。`observe_fix`/stage/native 包装全部经 `json_object` 安全解析，生产 `original_fix`/`original_native`/stage 函数始终先执行，非 dict/无线程 ID/非 Responses 路径仅跳过记录；`observe_open` 在无 record 时完全不解析 body，直接透传原 response（不预读、不缓冲），独立 `passthrough-requests` 列表仅含 method、去 query 的 path、outbound 原始字节的 length/sha256、`model=None`、http_status、error_class——无 query/header/body 内容/凭据，且不进入 wire 链（auditor 不读取该文件，旧 capture 目录无此文件不受影响）；`observe_handle`/`observe_fix`/`observe_open` 每请求清空 thread-local record/attempt/responses_request，同 worker 串行测试证明无串联；13 个子情形（GET/空/非 JSON/数组/null/数字/字符串/无 thread ID/非 UTF-8/gzip/deflate/无法解压/未知编码）全部原样到达 upstream 并回放原响应；429 错误语义与原 handler 对照一致；无 thread ID 的压缩 guardian JSON 仍执行 model swap/id fix/format downgrade/drop_tools_item；四例正常 native/guardian 对照与离线 loopback/首块流式测试实质通过；HEAD 无任何 `do_HEAD` 实现，保持原 handler 501，未新增协议。
3. **MiMo-2 active-map 成功路径标准日志 —— 已修复**。同一标准日志块（AST 完全一致）前移到 active-map relay 与错误 dump 之前，active 成功路径恢复 `POST path -> status model=… enc=… rewrite=… tools=…` 行且每请求恰一条；`_summary` 仅迭代数组 tools，非数组（含 42/True/string/dict）安全显示 `none` 不再抛错；测试逐条断言日志不含 prompt/args/header/auth key/私有 URL/session 标记；独立 diff 与 AST 证明生产 helper 增量仅诊断——mapping、request/response bytes、headers、guardian/retry/auth、first-event 门控均未变，a6246 基线 vs 最终 helper 的 SSE/JSON × identity/gzip/deflate、auth/model rewrite、首块-before-EOF 字节/头等价测试全绿；与旧 a6246 native source 的有界适用关系成立（gzip == a6246 == A/4 launch 快照 + 诊断限定 AST 证明 + loopback 等价），未要求为日志改动重跑九路模型。

4. **A/4 与 A/3 offline audit 回归 —— 已落地**。真实 `mimo-flash/namespace-scenario-a-attempt-4` 由当前 auditor 判 PASS（coverage a=true）、真实 A/3 判 incomplete FAIL（coverage 全 false，具体失败 checks 断言），A/4 内存反例（缺 receipts/错 author/错 child turn/空 map）全部被拒；投影 `actual-a4-a3-current-audits.json` 另存 auditor/输入/capture-helper 哈希，未改写原始 verdict（原始文件在 freeze 内字节不变）；v2 fresh parent 收 FINAL 后去 wait 仍 PASS 且 8 项回执 mutation 全拒；13 项 wait 回执 mutation（含 author/order/token/stale/wait-error）与“回执正确时实际 wait 错误/错 target/错 namespace 仍拒绝”均在回归内；prompt 断言保留 “Do NOT wait for another mailbox update…”，不重新要求已收 FINAL 后再等新邮箱更新。

## Open Questions

- 无

## Residual Risk

- 步骤化 `verify-scope.py`（observer 与 logging 两份）的入口保持断言绑定各自修复步骤的 entry manifest，后续步骤完成后不可原样复跑；当前一致性证据是 v2 freeze 的 536 文件全量 hash 核验（本次通过），后续 controller 应以 freeze 为权威。
- `unchanged-path-90-reuse.json` 引用的四个测试源文件本身不在 freeze 的 source/evidence 列表中，由 reuse 记录内 hash 钉住；本次已核对当前文件匹配，若未来源文件漂移需重跑该 90 项而非沿用。
- 有界适用边界沿用 v1 结论：九路 native captures 归属各自原始 launch/helper hash，最终 helper 无新 inference；外部上游可用性未重新探测；live sync 未执行，原业务回报在 live sync 前继续禁止，source 尚未部署（owner: 用户/controller）。
- 契约明示边界不变（非缺陷）：空 `data:` 心跳、重复 selected callable 显式 400、压缩 active 响应 502、未来 descriptor 容器——owner shim/protocol maintainers，需新观测证据另立工作单元。
- loopback 测试需关闭 sandbox（本地 bind EPERM），与代码无关。
- 未运行任何真实 API/模型调用；未 commit/push/deploy/restart；未发送消息或 callback；未读取私有配置、业务资料或并行复审结论。
