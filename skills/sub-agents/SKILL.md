---
name: sub-agents
description: "通过 claude-agent-run 或 codex-agent-run 子进程启动外部子 Agent。用于隔离或并发派发调查、实现和 review 任务，并检查进程与结构化输出。"
---

# Sub Agents

使用下述 runner 子进程派发子 Agent。此 skill 激活时，所有子 Agent 调用都必须遵循本协议。

## Runners

| Runtime | Command | Providers | Default structured output |
| --- | --- | --- | --- |
| Claude Code | `$HOME/.local/bin/claude-agent-run` | `ds mimo qwen kimi glm local` | one JSON result |
| Codex | `$HOME/.local/bin/codex-agent-run` | `ds mimo qwen kimi glm local gpt business` | JSONL event stream |

调用前确认 runner 可执行，并用 `pwd -P` 得到当前任务 workspace 的绝对路径。每次调用必须显式传入
`--cwd "<absolute-workspace>"`，不得依赖总控当前目录。

## Dispatch Contract

每个子 Agent 的 prompt 必须明确：

- 目标、非目标和 stop condition；
- 可读取、可修改以及禁止修改的文件；
- 是否允许调用工具和允许的副作用；
- 相关代码、文档和约束的路径；
- 预期输出格式、artifact 路径和 validation；
- 禁止 commit、push、PR、merge 或进入其它 gate，除非任务明确授权。

一次性任务默认使用 `--no-persist`。Claude 调用必须使用唯一 `--instance`。Codex runner 没有
`--instance` 参数，应使用唯一 task label、输出文件名，并把该 label 写入 prompt。

写任务需要显式选择适当权限：Claude 使用 `--permission-mode`，Codex 使用 `--sandbox`。不得通过宽权限扩张
用户授权或任务 scope。

## Execution And Isolation

为每轮派发创建独立目录：

```bash
run_dir="$(mktemp -d "${TMPDIR:-/tmp}/sub-agents.XXXXXX")"
workspace="$(pwd -P)"
```

默认调用：

```bash
"$HOME/.local/bin/claude-agent-run" \
  --provider ds \
  --cwd "$workspace" \
  --instance "review-ds-01" \
  --no-persist \
  --output-format json \
  --output "$run_dir/review-ds-01.json" \
  --stderr "$run_dir/review-ds-01.stderr" \
  --prompt "<bounded task>"

"$HOME/.local/bin/codex-agent-run" \
  --provider gpt \
  --cwd "$workspace" \
  --no-persist \
  --output-format json \
  --output "$run_dir/review-gpt-01.jsonl" \
  --stderr "$run_dir/review-gpt-01.stderr" \
  --last-message "$run_dir/review-gpt-01.last.md" \
  --prompt "<bounded task>"
```

相互独立的子任务应后台并发启动，分别记录 PID，完成后逐个 `wait "$pid"` 并保存各自退出码。存在数据依赖、
写入顺序依赖或 file ownership 重叠时必须串行。不得让多个子 Agent 并发修改同一文件，除非已划分互不重叠的写入范围。

不要仅因运行时间长而 kill、重派或切换 provider。进程仍存活且有输出或文件变化时，默认仍为 in-flight。只有明确失败、
阻塞、用户停止或进程退出证据才能结束该次派发。

## Result Validation

每个进程结束后必须检查 exit code、stderr 和输出文件，不得只读取最终自然语言。

Claude JSON：

- 文件必须是有效 JSON；
- 检查外层 `subtype`、`is_error` 和 `result`；
- 非成功 subtype、`is_error=true`、缺少 result 或非零退出码均不得判定成功；
- `result` 可能包含 Markdown code fence。解析其中的 JSON 时先去除 fence，再进行结构化解析。

Codex JSONL：

- 每个非空行都必须是有效 JSON event；
- 检查 error / failed events，并要求存在明确的 turn completion；
- 非零退出码、失败 event 或缺少 completion evidence 均不得判定成功；
- 优先使用 `--last-message` 保存最终消息，但仍必须同时审查完整 event stream 和 stderr。

空 stderr 不证明成功，非空 stderr 也不自动证明失败；结合退出码和结构化状态裁决。

## Retry And Sessions

失败后先根据 stderr 和结构化输出区分配置错误、超时、模型错误或任务错误。只允许一次有明确理由的同 provider 重试；
再次失败后可切换 provider，并记录两次失败和切换原因。不得无上限重试。

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
