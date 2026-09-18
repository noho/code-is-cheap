---
name: tmux-agents
description: "通过 tmux pane 与已运行的 CLI Agent 通信。用于 pane discovery、session clear、CLI skill 语法选择，以及 tmux-cli send/wait_idle/capture。"
---

# Tmux Agents

Tmux Agents 只定义与已运行 CLI Agent 的通信协议。目标 Agent 必须已经在 pane 中运行；本 skill 不分配角色。

## Agent CLI Types

根据 pane title 和 `pane_current_command` 确认 CLI 类型：

| Pane title pattern | CLI type | Skill trigger |
| --- | --- | --- |
| `ClaudeAgent-*` | Claude Code Agent | slash command，例如 `/planreview` |
| `CodexAgent-*` | Codex Agent | dollar skill，例如 `$planreview` |

不得仅凭任务角色猜 CLI 类型。

## Pane Discovery

每次发送前都重新确认目标 full pane id：

```bash
tmux-cli status
tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index} #{window_name} #{pane_current_command} #{pane_title}'
```

后续 `send`、`wait_idle`、`capture` 都使用跨 window 的 full pane id，例如 `ai-2:1.3`。目标 Agent
不在线、pane id 不明确、名称冲突或命令不可用时，先报告，不得盲发。

## Session Clear

新 assigned task 或新的 gate/slice，先单独发送 `/clear`，确认目标完成 clear 并回到可输入状态后，再发送正式任务。

如果目标 Agent 仍在完成同一任务、等待补充信息、返回 artifact、修正输出或回答 follow-up，不要 clear，直接发送补充指令。
Agent 仍在工作时不得因耗时长而 clear、覆盖任务或擅自中断。

## Send Safety

通过 `tmux-cli send` 发送文本时避免裸 `#数字`，使用 `PR 45`、`PR-45`、`issue 123` 或完整 URL。
若内容被截断，不要 clear；重新 discovery 后发送不含裸 `#数字` 的完整文本。

## Chat Workflow

新任务：

```bash
tmux-cli status
tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index} #{window_name} #{pane_current_command} #{pane_title}'
tmux-cli send "/clear" --pane=<full-pane-id>
tmux-cli wait_idle --pane=<full-pane-id> --idle-time=3 --timeout=60
tmux-cli capture --pane=<full-pane-id>
tmux-cli send "<task text>" --pane=<full-pane-id>
tmux-cli wait_idle --pane=<full-pane-id> --idle-time=3 --timeout=<task-timeout-seconds>
tmux-cli capture --pane=<full-pane-id>
```

同一任务的 follow-up 省略 clear，重新 discovery 后执行 `send -> wait_idle -> capture`。

`tmux-cli execute` 只用于需要 exit code 的 shell command，不用于 Agent chat。相互独立且 file ownership 不重叠的
任务可以并行发送；有依赖或写入范围重叠时必须串行。

## Completion Check

只有明确的完成、阻塞或失败证据才表示 Agent 返回。单次 `wait_idle`、暂时无输出或主观耗时判断都不构成结束证据。
capture 后检查：

- completion / blocked / failed 状态；
- expected artifact 是否存在；
- validation 和 finding 结论；
- 是否仍请求工具执行或补充输入。

总控必须 review Agent 输出并自行裁决，不能直接照搬。
