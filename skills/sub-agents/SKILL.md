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

先看实际外层退出码、`agent_status` 和 `final_answer`：结论、未完成事项、影响结果的问题以及文件路径。
最终答复超过 12000 字符会标记截断，完整内容可从日志取得。runner 不提供中途注入指令、唤醒或自动完成通知；
仍使用总控环境的托管句柄等待。

汇总还包含：

- `runtime_exit_code` / `runner_exit_code` / `terminal`：进程与结构化终态。
- `session_id`：原生事件中的会话 ID（Codex thread_id / Claude session_id）；缺失或冲突为 null。
  只有显式持久化的会话才可续接；ID 不证明默认一次性会话已保存。
- `validation_status`：`passed` 是机械检查通过；`needs_review` 提醒存在工具异常或可见性缺项；
  `rejected` 是结构损坏、终态/最终答复缺失、进程失败或显式检查未满足。runtime 非零保留原码，否则机械拒收返回 1。
- `errors` / `anomalies` / `warnings`：最多每类 20 条、每条 2000 字符，附计数、截断和日志位置。
  普通工具失败列入 anomalies，成功 runtime 仍返回 0；并不自动判 Agent 或任务失败。
- `wall_clock_seconds`：runner 启动至调用结果收集器的实测秒数，含 setup/runtime/最终消息处理，
  不含收集器序列化、调用方预检和等待开销。`usage` 是单一终态的原始用量对象，不累计流式片段。
  `runtime_metrics` 保留 Claude 报告的时长、费用和 modelUsage；缺失数据为 null/空对象，不估算。
  重复或缺失终态不提供可信用量；失败终态有真实用量时仍保留。完整原始统计也在日志中。
- `artifacts` / `canary_status`：只在调用方显式声明对应检查时有检查结果。
  `result_status=not_assessed` 表示 runner 不替调用方判定任务正确性。

传错参数、探索无匹配、权限错误等工具失败在 Agent 执行中常见。默认不要求逐事件裁决报告或固定 YAML。
结合最终答复和任务目的判断结果是否可用；有未解决且影响结论的缺项时，核对相关日志/文件或要求补足。
具体任务要求测试、独立来源或审核证据时，按这些要求核对；多个 Agent 一致或最终答复声称完成，不能替代所需证据。
文件是否存在和内容是否符合任务也按交付需要核对，无需给所有任务设置统一 canary 或附加产物。
最终答复中的工具调用语法且无记录的工具结果，只能提示可能的示例或未执行声明；runner 不据此断言伪造。
按任务目的判断，要求实际执行的任务仍需核对执行结果。
`needs_review` 本身不要求用户追加授权、暂停 workflow 或重派；也不能只凭退出 0 推断业务正确。

需要原始输出时加 `--detail`：恢复原始 stdout/stderr 行为，不自动汇总，也不执行可选 canary/产物收尾检查。
`--output-format text` 和 Claude `json` 仅用于此模式。它是输出选择，不额外要求调用方审计所有工具事件。
子 Agent 的答复和 runner 的汇总都不构成用户授权。

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
已运行的实际失败先区分配置/环境故障、模型故障、任务问题；普通工具失败已经恢复且不影响结果时，无需重派。
确需重派时最多一次有明确理由的同 provider 修复性重试，使用新的独立调用/日志并保留原尝试。
再次失败后，遵守任务或项目的替补路由/授权；无额外限制时才可切换 provider。原因未知时先查清，不无限重试。
测量任务一旦启动，失败计入原批次，不能用重试结果替换或重试到成功；固定并发度。

需要后续会话时首次使用 `--persist`，后续用返回的 session ID 配合 `--resume`（Codex 也有 `--resume-last`）。
一次性任务无需持久化。外层禁读隔离不支持 resume 或中途追加输入。
