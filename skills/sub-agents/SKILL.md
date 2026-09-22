---
name: sub-agents
description: "通过 claude-agent-run 或 codex-agent-run 子进程启动外部子 Agent。用于隔离或并发派发调查、实现和 review 任务，并检查进程与结构化输出。"
---

# Sub Agents

使用下述 runner 子进程派发子 Agent。此 skill 激活时，所有子 Agent 调用都必须遵循本协议。

## Runners

| Runtime | Command | Providers | Default structured output |
| --- | --- | --- | --- |
| Claude Code | `claude-agent-run` | `ds mimo qwen kimi glm local` | one JSON result |
| Codex | `codex-agent-run` | `ds mimo qwen kimi glm local gpt gpt-5.6 business` | JSONL event stream |

`gpt` 是昂贵的低频模型（gpt-6-astra），`gpt-5.6` 是便宜的高频模型（gpt-5.6-sol，medium effort）：工具密集、
量大的派发优先用 `gpt-5.6`。

两个 runner 已在 PATH，直接以命令名调用。调用前先跑 `<runner> --help` 确认可用与接口，并用 `pwd -P` 得到当前任务
workspace 的绝对路径。每次调用必须显式传入 `--cwd "<absolute-workspace>"`，不得依赖总控当前目录。

codex 的 `--cwd` 不在 git 仓库内时（如临时目录），必须显式加 `--skip-git-repo-check`；claude-agent-run 无此限制。

## Dispatch Contract

每个子 Agent 的 prompt 必须明确：

- 目标、非目标和 stop condition；
- 可读取、可修改以及禁止修改的文件；
- 是否允许调用工具和允许的副作用；
- 相关代码、文档和约束的路径；
- 预期输出格式、artifact 路径和 validation；
- 报告开头必须声明自身的 runtime、provider 和 model；自报与 event stream 不符时以 event stream 为准；
- 禁止 commit、push、PR、merge 或进入其它 gate，除非任务明确授权。

一次性任务默认使用 `--no-persist`。Claude 调用必须使用唯一 `--instance`。Codex runner 没有
`--instance` 参数，应使用唯一 task label、输出文件名，并把该 label 写入 prompt。

子 Agent 权限默认继承 auto 模式，无需显式传 `--permission-mode`；需要收紧时显式指定。不得传
`bypassPermissions`（父会话 auto 分类器会拒绝该派发）。Codex 用 `--sandbox` 选择沙箱级别。
不得通过宽权限扩张用户授权或任务 scope。

## Execution And Isolation

为每轮派发创建独立目录：

```bash
run_dir="$(mktemp -d "${TMPDIR:-/tmp}/sub-agents.XXXXXX")"
workspace="$(pwd -P)"
```

默认调用：

```bash
claude-agent-run \
  --provider ds \
  --cwd "$workspace" \
  --instance "review-ds-01" \
  --no-persist \
  --output-format json \
  --output "$run_dir/review-ds-01.json" \
  --stderr "$run_dir/review-ds-01.stderr" \
  --prompt "<bounded task>"

codex-agent-run \
  --provider gpt \
  --cwd "$workspace" \
  --no-persist \
  --output-format json \
  --output "$run_dir/review-gpt-01.jsonl" \
  --stderr "$run_dir/review-gpt-01.stderr" \
  --last-message "$run_dir/review-gpt-01.last.md" \
  --prompt "<bounded task>"
```

派发必须在沙箱外运行，方式取决于总控环境：

- Claude 总控：以独立的一次 Bash 调用发出——裸命令、无引号、无 `$HOME` 前缀、不管道、不复合，run_dir 等准备
  工作在之前的调用完成，使命令命中 `excludedCommands`；
- Codex 总控：每个子 Agent 使用一次独立的 `exec_command` 调用，显式设置 `sandbox_permissions:
  "require_escalated"`（附 justification）；若返回 session_id，通过对应的 `write_stdin` 收集；
  本协议不依赖 Codex 环境提供命令豁免。

沙箱内派发的典型症状：codex 子 Agent 初始化失败（`failed to initialize in-process app-server client`）；
claude 子 Agent 能启动但自身 Bash 不可用（`EPERM ... srt-mux`）。出现这些症状时优先检查派发是否仍在沙箱内；
若派发已显式提权，则检查子进程自身的沙箱配置——该报错不唯一指向父级派发未出沙箱。

并发派发 = 多次**独立**调用（Claude 总控：多次 `run_in_background: true`；Codex 总控：每个子 Agent 一次独立的
`exec_command`，若返回 session_id 则用对应的 `write_stdin` 收集），统一使用独立调用便于权限判定与结果追踪；
Claude 环境中复合命令（`&`、`&&`、管道）还可能无法命中 `excludedCommands`，导致子 Agent 的 Bash 失效。
收集时逐个核对各自退出码与 artifact。存在数据依赖、
写入顺序依赖或 file ownership 重叠时必须串行。不得让多个子 Agent 并发修改同一文件，除非已划分互不重叠的写入范围。

不要仅因运行时间长而 kill、重派或切换 provider。后台任务仍在运行、或输出文件仍有变化时，默认仍为 in-flight；
判活不得依赖 ps / pgrep / kill -0 等进程查询。只有明确失败、阻塞、用户停止或进程退出证据才能结束该次派发。

### Sandbox Process Management

沙箱（`sandbox.enabled`）下进程管理一律使用下列配套方法，不要在协议里使用 `ps` / `pgrep` 或其它进程列表工具。

- **派发与收集（Claude 总控）**：用 Bash 工具的 `run_in_background: true` 独立发出；harness 托管的后台任务跨调用
  存活，通过后台任务句柄收集完成状态与退出码，输出由 harness 落盘。不要用 shell `&`——其子进程在沙箱下会随
  Bash 调用结束被回收；
- **派发与收集（Codex 总控）**：每个子 Agent 一次独立的 `exec_command`；可能直接返回退出码，也可能返回 session_id，
  后者用 `write_stdin` 持续收集，直到取得退出码；
- **进度判据**：run_dir 内输出文件（或后台任务的 harness 输出文件）的大小 / mtime 变化，不要用进程列表；
- **退出码**：前台取 `wait "$pid"` 的返回值；后台取完成通知（其输出文件末尾留有 `[exited with code N]` 标记）；
- **输出流**：后台模式会把 stdout/stderr 合并进同一文件，因此结构化输出与日志必须继续通过 `--output` /
  `--stderr` 落到 run_dir。

## Result Validation

每个进程结束后必须检查 exit code、stderr 和输出文件，不得只读取最终自然语言。退出码来源：前台 `wait "$pid"`
的返回值，或后台任务完成通知（输出文件末尾同样留有 `[exited with code N]` 标记）。

任务要求工具调用时，"完成"不算成功，必须有工具执行成功的证据：

- Codex：event stream 存在 `item.completed` 且 `item.type == "command_execution"`、`exit_code == 0`；
- Claude：`num_turns >= 2` 只证明调用过工具，不证明调用成功（实测：Bash 报错的运行该值仍为 2）——以 canary 为准。

验证类派发（探针、验收、产出会被下游信任）必须使用 canary：

1. `TOKEN="<prefix>-$(openssl rand -hex 4)"`，写入 run_dir 内文件；
2. prompt 只给文件路径，不得包含 TOKEN 本身；
3. 最终消息中的 token 与文件内容逐字比对，不等即判失败——即使其它检查全部通过。

伪造型静默失败是硬失败，不重试，记录并上报：最终消息含字面工具调用语法（`<tool_call>`、`<tool_result>`、
裸 JSON 工具对象）而 event stream 无对应执行事件——provider 级缺陷特征。

已确认的非致命诊断不构成失败，但必须记录：`Model metadata for … not found`、`unrecognized_model`——即使被封装
为 event stream 中的 `item.type == "error"` 也按此例外处理。仅豁免与上述完整诊断模式逐字匹配的事件，其他
error / failed 事件仍按失败处理；仅在退出码、turn completion、工具执行证据与 canary 均满足、且无其它失败证据时
判为通过，并附警告。

Claude JSON：

- 文件必须是有效 JSON；
- 检查外层 `subtype`、`is_error` 和 `result`；
- 非成功 subtype、`is_error=true`、缺少 result 或非零退出码均不得判定成功；
- `result` 可能包含 Markdown code fence。解析其中的 JSON 时先去除 fence，再进行结构化解析。

Codex JSONL：

- 每个非空行都必须是有效 JSON event；
- 检查 error / failed events，并要求存在明确的 turn completion；上段列出的已确认非致命诊断不按失败计；
- 非零退出码、失败 event 或缺少 completion evidence 均不得判定成功（已确认非致命诊断除外）；
- 优先使用 `--last-message` 保存最终消息，但仍必须同时审查完整 event stream 和 stderr。

空 stderr 不证明成功，非空 stderr 也不自动证明失败；结合退出码和结构化状态裁决。

## Retry And Sessions

失败后先根据 stderr 和结构化输出区分配置错误、超时、模型错误或任务错误。只允许一次有明确理由的同 provider 重试；
再次失败后可切换 provider，并记录两次失败和切换原因。不得无上限重试。

区分派发错误与测量数据：基础设施失败（起不来、超时、配置错）可按上一条重试；测量 provider/环境行为的派发，
失败必须计数，禁止重试到成功，且必须固定并发度——否则测到的是并发与 provider 的混合效应。

修复性重试必须使用新的 task label，并同步用于 prompt、输出文件名和 Claude `--instance`，同时记录与原尝试的关联
标识；修复性重试不得并入原测量批次的通过率，如需重新测量，另建固定并发度、预定样本数的新批次。

需要多轮延续时，第一次使用 `--persist`：

- Claude 后续使用返回的 session ID 配合 `--resume`；
- Codex 后续使用 `--resume <id>` 或在明确需要时使用 `--resume-last`；
- 一次性任务不得持久化 session。

## Controller Adjudication

子 Agent 输出只是输入证据。总控必须读取相关 artifact、review 关键代码或数据、交叉核对冲突，并自行采纳或驳回。
不得因多个 Agent 表述一致就跳过证据检查。

完成报告必须逐个列出：

- runtime、provider 和唯一 task label；
- 子任务；
- exit status；
- stdout、stderr、last-message 或 artifact 路径；
- 总控采纳、部分采纳或驳回的结论及理由；
- retry、provider switch 和未解决风险。

首次让某 provider 承担工具密集任务前，先用 canary 探针实测通过率；显著低于 1 时不得用于工具任务并告知用户
（k 次工具调用的任务成功率约 p^k）。
