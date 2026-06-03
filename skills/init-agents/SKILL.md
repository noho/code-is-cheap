---
name: init-agents
description: "初始化多 Agent tmux 通信约定。用于确认 Agent CLI 类型、/skill 或 $skill 写法、pane discovery、clear/session 规则，以及 tmux-cli send/wait_idle/capture 流程。"
---

# Init Agents

Init Agents 只定义多 Agent 通信步骤和安全规则。

## Agent CLI Types

| Agent | CLI type | Skill trigger |
| --- | --- | --- |
| `AgentMiMo` | Claude Code Agent | slash command |
| `AgentDS` | Claude Code Agent | slash command |
| `AgentGLM` | Claude Code Agent | slash command |
| `AgentOpus` | Claude Code Agent | slash command |
| `AgentCodex` | Codex Agent | dollar skill |

Claude Code Agent 使用 slash command：

```text
/planreview
/deepreview
/gateflow
```

Codex Agent 使用 dollar skill：

```text
$planreview
$deepreview
$gateflow
```

## Pane Discovery

每次发送前都重新确认目标 full pane id：

```bash
tmux-cli status
tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index} #{window_name} #{pane_current_command} #{pane_title}'
```

使用跨 window 的 full pane id，例如：

```text
ai-2:1.3
```

后续 `tmux-cli send`、`tmux-cli wait_idle`、`tmux-cli capture` 都使用 full pane id。若目标 Agent 不在线、pane id 不明确、
名称冲突或命令不可用，先报告，不要盲发。

## Session Clear

新 assigned task 或新的 gate/slice，先发送 clear，再发送正式任务：

```text
/clear
```

要求：

- clear 和正式任务分开发送；
- 等目标 Agent 完成 clear 并回到可输入状态后，再发送正式任务；
- clear 失败或目标未回到可输入状态时，先报告。

如果目标 Agent 当前任务尚未完成，正在等待补充信息、继续执行、返回 artifact、修正同一轮输出或回答同一任务 follow-up，
不要 clear，直接发送补充指令。

## Send Safety

通过 `tmux-cli send` 发送文本时，避免裸 `#数字`，某些环境会截断 `PR #45` 这类文本。

写法：

- 用 `PR 45`、`PR-45`、`Pull Request 45`；
- 用 `issue 123`、`issue-123`；
- 需要链接时写完整 URL。

如果发现内容被截断，不要 clear；重新 discovery 后发送去掉裸 `#数字` 的完整文本。

## Chat Workflow

新 assigned task：

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

未完成 task 的 follow-up：

```bash
tmux-cli status
tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index} #{window_name} #{pane_current_command} #{pane_title}'
tmux-cli send "<follow-up text>" --pane=<full-pane-id>
tmux-cli wait_idle --pane=<full-pane-id> --idle-time=3 --timeout=<task-timeout-seconds>
tmux-cli capture --pane=<full-pane-id>
```

`tmux-cli execute` 只用于需要 exit code 的 shell command；不要用于 agent-to-agent chat。

## Checklist

发送前确认：

- 已运行 `tmux-cli status`；
- 已运行 `tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index} #{window_name} #{pane_current_command} #{pane_title}'`；
- 已确认目标 full pane id；
- 已判断是否需要 clear；
- 已避免裸 `#数字`；
- 已按目标 CLI 类型选择 `/skill` 或 `$skill`；
- 发送后使用 `wait_idle` 和 `capture` 读取结果。
