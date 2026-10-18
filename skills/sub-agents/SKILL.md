---
name: sub-agents
description: "通过 claude-agent-run 或 codex-agent-run 启动外部子 Agent，派发独立或并行任务，等待退出并取得最终答复。需要时可选用 canary、产物检查及 macOS 禁读隔离。"
---

# Sub Agents

通过 runner 子进程调用外部 Claude Code / Codex 子 Agent。普通任务直接派发，等待实际退出，读取汇总里的
最终答复，并按任务需要使用或核对成果。项目明确要求的审核、取证和工作流规则仍然适用。

## 直接调用

| Runtime | Runner | Providers |
| --- | --- | --- |
| Claude Code | `claude-agent-run` | `ds-flash mimo mimo-fast mimo-flash qwen kimi glm glm-flash local hy` |
| Codex | `codex-agent-run` | `ds-flash mimo mimo-fast mimo-flash qwen kimi glm glm-flash local gpt-6-astra gpt-6-sol gpt-6-luna business` |

每次显式传 `--cwd` 的 workspace 绝对路径，避免依赖总控当前目录。接口不熟悉时查看所选 runner 的 `--help` / `--list-providers`。

```bash
codex-agent-run --provider mimo --cwd /absolute/workspace --prompt-file /absolute/task.md
claude-agent-run --provider ds-flash --cwd /absolute/workspace --prompt "检查 src/parser.py 对空输入的处理，只报告发现，不修改文件。"
```

runner 自动检查所选 provider、workspace、任务输入、launcher 及输出路径；非 Git workspace 的 Codex 自动追加
`--skip-git-repo-check`。默认一次性运行，不持久化 session。默认自动分配私有日志目录和 Claude instance；
调用方无需提供 label、instance、日志路径或单独运行预检。需要指定日志位置时使用 `--output` / `--stderr` /
Codex `--last-message`，这些必须是新文件；显式 `-` 仅用于 `--detail`，汇总模式明确拒绝。

## 独立上下文交接

`--prompt` / `--prompt-file` 的任务在新的独立 Agent 上下文执行，不继承总控的对话、裁决或用户授权。
相同 cwd 或 provider 也不传递上下文；runtime 自身可能加载 workspace 的 AGENTS.md 等本地指令和配置。

用自然语言提供这项任务需要的背景、已决事项、授权、输入/版本、依赖、可写范围和交付要求，或给出可定位的文件路径。
复杂任务明确范围和完成信号；简单任务无需固定标题或填写 N/A。不要使用只有父上下文知道含义的“刚才”“照旧”。
不要求子 Agent 自报 runtime/provider/model。只交接必要信息，不转发无关的历史或敏感信息。
缺少必要输入、授权或工具时应报告具体缺项，不能猜测或自动扩大权限。

要求交付文件时，把目的及文件路径告诉子 Agent，并要求在最终答复给出产物路径和未完成事项。
修改既有源码无需另写一份报告描述修改；调用方可直接查看源码和任务要求的验证。

## 托管执行与等待

派发从总控沙箱外运行，避免父级沙箱妨碍 runtime 初始化或子 Agent 的工具：

- Codex 总控：每个任务用一次独立的 `exec_command`，设置 `sandbox_permissions: "require_escalated"` 并说明任务。
  返回 session_id 时，用对应 `write_stdin` 收集，直到取得退出码。
- Claude 总控：以独立裸 runner 命令调用 Bash，使其命中 `sandbox.excludedCommands`；准备工作在之前完成。
  后台运行用 `run_in_background: true`，用托管任务句柄/完成通知收集。不要用 shell `&`、管道或复合命令派发。

并行任务各有独立托管调用和日志。可读输入可以共享；写范围重叠或有数据依赖时串行，或先明确互不重叠的 ownership。

不要仅因耗时长就 kill、重派或换 provider。使用托管句柄判断完成；日志大小/mtime 可用于观察进度，
不能代替退出码；不依赖 `ps` / `pgrep` 等进程查询。在途时继续收集，停止在途 Agent 必须取得用户授权。
任务 blocked 不等于进程已经退出；用户授权中止后保留停止原因。最终消息已出现也不能提前认定进程完成。

沙箱内启动的常见症状是 Codex 初始化失败或 Claude Bash 的 EPERM；先核查父级派发环境，
已提权仍失败时核查 runtime 自身配置，不按单一报错猜根因。

## 取得和使用结果

默认在实际 runtime 退出后，runner stdout 返回一个 JSON 汇总；即使指定日志文件也会返回汇总。
Claude 原始 stream-json、Codex JSONL 和 stderr 保留，路径在 `logs` 中。Codex 最终答复也在 JSONL 中；
只有显式 `--last-message` 才另存最终消息文件并返回 `logs.last_message`，默认该字段为 null。

读取实际外层退出码、`runtime_exit_code` 和完整 `final_answer`，再按任务需要使用产物。
runner 等待真实 CLI 退出并原样返回原生退出码；说明缺少输入、环境阻碍或未能完成的 final 是正常答复。
任务是否验收、是否继续交互及次数由调用方按用户/项目授权与路由决定。runner 不自动重试、换 provider、注入指令或唤醒；
使用总控托管句柄等待。退出 0、最终答复和汇总都不证明业务正确或构成用户授权。

schema version **2** 只包含：

- `schema_version=2`、`source=subagent_report`、`runtime`、`provider`：所选交互身份。
- `runtime_exit_code`、`final_answer`：实际原生退出和完整原生 final，无长度限制或截断元数据，保留 Unicode/空白。
  Codex 最后一条 completed agent message 提供 final；Claude 唯一根 result 字符串提供 final。
  缺失/非文本/歧义时为 null，观测到空字符串仍为空；中间/嵌套 assistant 或 result 不回填。部分文本保留在日志。
- `session_id`、`terminal`：实测原生身份、终态 type/subtype，缺失/冲突为 null；ID 不代表临时会话已保存。
- `wall_clock_seconds`：启动到调用收集器的实测时间，含 setup/runtime/附加 final 处理，不含序列化和调用方等待。
  `usage` 仅保留单一终态原始用量；`runtime_metrics` 保留 Claude 实测时长/费用/modelUsage，不累加流式片段。
  缺失为 null/空对象，真实零值保留；原生失败终态有真实统计也保留。
- `logs`：`output`、`stderr` 和可选 `last_message` 的绝对路径。
- `diagnostics`：单一 `{message, path, line}` 事实列表。warning 文本不判断、不分类、不过滤、不改写，原文带来源保留。
  工具错误、协议缺项/负面元数据及损坏日志是观察，不改写原生退出或可归属 final。
- `checks`：`artifacts` 为 `{path, exists, regular_file}` 列表；`canary` 未启用时为 null，启用后为
  `{proof_observed, proof_matches_expected, read_candidate_observed}`，无可比较证明时匹配为 null。
  缺失报告、不匹配证明、候选轨迹都由调用方判断，不构成 runner 任务判决。

v1 的 `agent_status`、`validation_status`、`result_status`、`runner_exit_code`、`final_answer_chars`、
`final_answer_truncated`、三类诊断/计数/截断及工具/事件汇总字段已删除，无替代 wrapper 状态。
外部调用方应迁移到原生退出、完整 final 与观察字段，不再依赖检查缺项产生非零退出。
收集器成功序列化观察时退出 0，即使源日志缺失/损坏；这是收集器进程结果，不是任务验收。

exec 前 setup 错误返回 2，不伪造原生退出或 report；stderr 记录原因及已分配日志路径。
原生退出后若无法运行收集器/序列化/写出主结果，stderr 报告实际交付错误、已知原生码与保留路径：
原生 0 时外层返回 1，原生非零保持原码。附加 `--last-message` 缺失/复制/竞争/清理失败保持原生退出，
不覆盖既有目标，保留可用临时源并报告位置。已有路径/符号链接等启动前检查仍适用。

按任务要求核对测试、独立证据和产物；多个 Agent 一致或自称完成不能替代所需证据。
需要原始输出时加 `--detail`，保留原生退出并跳过收集及 canary/产物收尾；text 和 Claude json 仅在此模式使用。
自定义 `AGENT_TOOLS_FILE` 必须支持 pre-exec-error-v1；过时 launcher/helper 会在启动前失败，详见高级参考。

## 可选能力

只有任务选择相应能力时才读取 [高级调用参考](references/advanced.md)：

- `sub-agent-preflight`：可选的提前 setup 检查及命令生成，默认自动 label，接受普通任务。
- `--canary`（preflight）或成对 runner canary 参数：验证指定文件读取，不证明整项任务正确。
- runner `--artifact`：显式检查本轮新建普通文件；通常直接用最终答复中的产物路径即可。
- `agent-sandbox --deny-list`：macOS/srt 的外层禁读边界，由调用方列出禁止路径和已知副本。
- `--full-access`：显式关闭内层沙箱及审批，本身没有任务级读取隔离。

默认工具权限与 provider 配置保持原样；工具权限不能扩张用户授权或任务 scope。

## 失败、重试和会话

启动前 setup 错误没有运行子 Agent：修正具体缺项后重新调用，不算 provider 重试或测量样本。
已运行交互的后续输入、继续、修复或再次派发由调用方按任务目的、现有授权与指定路由决定，没有固定同 provider 重试次数。
每次使用独立调用/日志，保留原尝试；解释性 final、普通工具错误或任务未完成不自动构成 provider 故障。
原因不明时检查证据，不自动扩大权限或更换 provider。
测量任务一旦启动，失败计入原批次，不能用重试结果替换或重试到成功；固定并发度。

需要后续会话时首次使用 `--persist`，后续用返回的 session ID 配合 `--resume`（Codex 也有 `--resume-last`）。
一次性任务无需持久化。外层禁读隔离不支持 resume 或中途追加输入。
