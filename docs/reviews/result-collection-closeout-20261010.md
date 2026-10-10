# Runner 结果汇总：总控裁决与闭环

## 交付范围

工作分支：`feat/sub-agent-result-collection`；base：`ebd547fab97a5af3f3bcffae7ebb187b71563dcf`。

两个现有 runner 默认在真实子进程结束后向 stdout 返回一条 JSON 汇总：终态、最终答复、异常、canary、必需产物和完整日志路径。
`--output` / `--stderr` 仍保存原始记录；`--detail` 恢复原始输出/重定向行为，由调用方自行检查。
不新增结果收集命令、中途指令通道或完成通知机制。预检和 SKILL 使用同一结果协议，安装时部署内部适配器。

普通工具失败进入 `anomalies`，`validation_status=needs_review`，成功 runtime 的 runner 返回 0。
总控检查恢复和必要证据；不会仅因工具失败要求用户裁决、停止 workflow 或消耗重试额度。
runtime 失败、损坏记录、冲突终态、错误 canary、缺产物等机械拒收仍单独报告。
`result_status=not_assessed` 始终留给总控进行语义验收；机械通过不证明业务结论正确。

## 两轮独立审核与修复

两轮均遵循 `$sub-agents`，并行使用 MiMo/Codex 与 DS Flash/Claude。完整任务书、预检、独立 canary 和日志保留在各轮 run_dir。
初审冻结 head `173b56523503f893c954bcc72fef26fd222cffea`；修复复审冻结 head `04e170e16d56fe7c7c62a82924ef30501ba9c046`。
各 Agent 只写自己的报告，未执行 commit、push、部署或再派发。

| 报告 | 总控裁决与最终验证 |
| --- | --- |
| [MiMo 初审](code-review-20261010-132916.md) 1 / [DS Flash 复审](code-review-20261010-135512.md) 1 | 采纳：无工具执行的字面工具对象检测覆盖裸 JSON、包装对象、说明句内嵌及围栏变体；普通 JSON 数据不崩溃。真实 runner 合成回归覆盖两 runtime。 |
| MiMo 初审 2 | 采纳：last-message 收尾诊断进入完整 stderr；保留 runtime 原始退出码；保存失败时仅读取可信临时 final，不读取被拒绝的目标。 |
| MiMo 初审 3 | 采纳：单条诊断和整体均显式标记截断，提供原长度和事件/日志行号。 |
| MiMo 初审 4 / DS Flash 复审 2 | 采纳：封装预检检查适配器、canary、必需产物与既有读写边界；先拒绝 artifact 叶节点符号链接，再解析父目录。没有扩大 allowWrite。 |
| MiMo 初审 5 / [DS Flash 初审](code-review-20261010-132918.md) 3 | 采纳：移除同名不同义的 `tool_trace` 汇总字段，改为 `tool_evidence_scope=recorded_events_only`；总控独立裁定轨迹范围。 |
| MiMo 初审 6 | 采纳：多终态固定为 conflicting，不允许最后一条成功覆盖失败。 |
| DS Flash 初审 1 / [MiMo 复审](code-review-20261010-135511.md) 1、3 | 采纳：canary 使用独立证明行；围栏、缩进及 HTML pre/code 示例不参与证明；冲突精确定位到 final 事件或 artifact 文件、行号。 |
| DS Flash 初审 2 | 采纳：必需 artifact 是本轮新普通文件；拒绝预存文件、目录、符号链接和日志重叠；运行后再次核对。 |
| DS Flash 初审 4 | 采纳：预检把每个声明 artifact 的绝对路径写入独立任务 prompt，同时保留命令参数。 |
| MiMo 复审 2 | 采纳：started/updated 中显式失败与 completed 失败一样进入待裁决异常，不静默丢弃。 |
| 总控补充 | 未知失败、未完成工具调用保留为待裁决；按解析后的参数辨别 `--detail`，不把参数值当开关；修复普通 JSON 的非字符串 type 和深层嵌套导致的解析异常；围栏中的 HTML 文本不改变围栏外证明扫描。 |

初审指出的问题在 `04e170e` 修复；复审残余问题及上述总控补充在最终提交修复。最终这组小范围改动由总控实际复现、检查代码并运行回归闭环，未宣称两份复审报告本身为“零 finding”。

## 派发生命周期与证据裁决

退出证据来自每一路独立 `exec_command` / `write_stdin` 托管句柄，不依据文件不增长或 Agent 自报认定退出。
以下 `tool_trace=partial` 保守记录 runtime 原生读取通道未保证全轨迹的限制；本次审核必要的冻结 diff、源码和合成反例由总控独立复核。
canary 的真实读取已逐路核对命令/工具参数及返回字节，未只采用 `canary_read_candidate`。

### MiMo/Codex 初审：result-review-codex-20261010-132916

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: partial
required_evidence: complete
canary_status: match
result_status: accepted
warnings:
  - item_46 的环境模型查询 rg 无匹配；不属于源码审核必需取证，模型自报不采信。
  - item_49 的 node_repl 模型元数据查询内核重置；不影响已取得的源码与反例。
  - item_50 再次查询同一模型元数据仍失败；模型身份未验证，未用该自报证明路由。
evidence_gaps: []
retry_class: none
```

句柄 9002 返回外层 0、runtime 0，终态 turn.completed；148 events / 68 tool results。
run_dir：`/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.Oa7bZR`。
原始日志 `result-review-codex-20261010-132916.jsonl`、同名前缀 `.stderr`、`.last.md`；产物为初审报告。
canary 读取：JSONL 第 9 行 item_3 的实际 cat。三项失败为第 93、99、101 行，非必要元数据查询，无未恢复的源码取证缺项。
实际 provider/runtime 以 runner 路由为准，报告中的 gpt-5.6-sol 模型自报不作为证明。
报告可采纳不表示带 blocking finding 的实现可以放行；其 finding 已按上表修复。

### DS Flash/Claude 初审：result-review-claude-20261010-132918

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: partial
required_evidence: complete
canary_status: match
result_status: rejected
warnings:
  - unrecognized_model stderr 属既定精确豁免，未发现普通失败工具结果。
  - 本轮实际 runner 外层返回 1：旧适配器把报告中的 canary 排版示例误判冲突；此事实保留，不记作通过。
evidence_gaps: []
retry_class: none
```

句柄 24122 外层 1、runtime 0、原生 result success；60611 events / 42 tool results。
run_dir：`/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.Qk0PM9`。
日志 `result-review-claude-20261010-132918.jsonl` / `.stderr`；产物为初审报告。
真实 canary 读取：第 287 行 tool_result，与对应 Bash cat 配对，返回与 expected 文件逐字一致。
拒收原因属于被审核适配器自身缺陷；保留机械交付拒收结果，报告中的可复现 finding 另作修复证据。
最终适配器回读该留存日志/报告为 passed、canary match，只是修复验证，不能改写当时的外层退出事实。
第二轮是修改冻结实现后的独立复审，不是把 provider 失败重试到成功。

### MiMo/Codex 复审：result-closure-codex-20261010-135511

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: partial
required_evidence: complete
canary_status: match
result_status: accepted
warnings:
  - item_49 探针重复传入 prompt，随后误解析空 stdout；属于探针命令错误。
  - item_50 使用不存在的临时 runner 路径；属于探针路径错误。
  - item_51 改正命令后取得参数值探针结果；总控还独立运行了对应回归。
evidence_gaps: []
retry_class: none
```

句柄 91165 外层 0、runtime 0、turn.completed；135 events / 63 tool results；汇总 needs_review。
run_dir：`/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.VEadiw`。
日志 `result-closure-codex-20261010-135511.jsonl` / `.stderr` / `.last.md`；产物为 MiMo 复审报告。
真实 canary cat 为第 9 行 item_3；失败为第 99、101 行，修正结果在第 103 行 item_51。
两个工具失败没有造成最终必要证据缺口，不消耗重试额度、不另派发以抹去失败。

### DS Flash/Claude 复审：result-closure-claude-20261010-135512

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: partial
required_evidence: complete
canary_status: match
result_status: accepted
warnings:
  - 第 26193 行工具结果 exit 1，复合检查包含不存在的 managed settings 路径；已取得的公共源码正常返回。
  - 第 26245 行工具结果 exit 1，同类路径不存在；随后合成 HOME/settings 和真实 --check 探针完成入口验证。
  - unrecognized_model stderr 属既定精确豁免。
evidence_gaps: []
retry_class: none
```

句柄 27457 外层 0、runtime 0、result success；55570 events / 46 tool results；汇总 needs_review。
run_dir：`/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.ZquPjq`。
日志 `result-closure-claude-20261010-135512.jsonl` / `.stderr`；产物为 DS Flash 复审报告。
真实 canary 为第 1851 行 Read 的配对结果。总控回读两条完整失败结果，核对是 `/etc/codex` 与 Claude 托管配置不存在；未读取私有 endpoints/key。
第一条展示诊断超过 2000 字符，截断标记有效；上述裁决依据完整原始记录而非截断摘要。

## 最终验证

- 完整 unittest：123 项，114 通过、9 项按环境门控跳过。
- 在最后的嵌套 JSON / 围栏内 HTML 修复后，结果汇总 24 项回归再次全部通过；封装 22 项此前已通过（6 项门控跳过）。
- 另行启用真实 Codex 0.162.1 / Claude Code 2.1.294 / srt 0.0.79：两项 Seatbelt/runtime 测试通过。
  使用临时来源、合成凭据和本机确定性接口；禁止文本及图片内容未进入请求，允许文本及图片正常返回；Codex 用户写入 rules 仍有效，Claude 运行于 bypassPermissions 且不加载 MCP。
  compact report 实际为 completed / needs_review / not_assessed，故预期拒绝的工具调用不会使整次 Agent 失败。
- 原始内核证据：`/private/tmp/collected-result-final-native-proof/{codex,claude}-probe.json`。
  Codex SHA256 `3f89b5fb3c0db09eb254d3ece353e004b0018cf8444b5155c732166bd21ceda7`；
  Claude SHA256 `665e1d8ecc5a00a1208a3d2801f82ef69fc4255416773eec1964dd930d0fcb99`。
- 全部六个 SKILL 校验、zsh/bash/Python 语法和 diff whitespace 检查通过。
- 安装曾在隔离临时目录验证两个 runner 能找到内部适配器；本轮未 sync to live。

## 边界与调用

```bash
sub-agent-preflight --runtime codex --provider mimo --cwd /absolute/workspace \
  --label unique-task --task-file /absolute/task.md --artifact /absolute/workspace/new-report.md
# 按预检生成的命令派发；真实进程结束后读取 stdout JSON。
codex-agent-run --provider mimo --cwd /absolute/workspace --prompt-file task.md --detail
```

无需兼容旧消费者或迁移已有日志。默认 Claude 改为 stream-json；需要其旧 JSON/text/raw 行为必须显式 `--detail`。
canary 候选只定位可能的读取证据；未保证所有 runtime 原生工具通道都完整记录，最终结论仍由总控复核。
必需产物的新普通文件检查不证明内容正确或作者真实性。被中断的进程可能没有 compact report，退出句柄和留存日志仍为生命周期证据。
完整日志保留至调用方清理；汇总有截断或缺口时须回读。任务禁读封装仍为可选 macOS 功能，未因汇总功能扩大读写权限。
结论：已采纳的 findings 已修复并验证，可提交 PR，由用户手工合并；没有部署 live 或改动其它项目。
