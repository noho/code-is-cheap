---
name: init-agents
description: "初始化多 Agent 通信约定。用于总控流程在通过 tmux pane 派发任务前确认 AgentMiMo、AgentDS、AgentGLM、AgentOpus、AgentCodex 的 CLI 类型、推荐任务类型、/skill 或 $skill prompt 写法、pane 发现方式、清 session 方式和 tmux-cli send/wait_idle/capture 流程。"
---

# Init Agents

## Purpose

`init-agents` 负责加载多 Agent 通信约定：每个 Agent 属于哪类 CLI、推荐处理什么任务、发送 prompt 时用什么技能触发格式、
发送前如何确认 pane、何时清 session。具体项目或流程里的最终职责由用户当前任务、`$gateflow`、`$phaseflow`
或其它上层 skill 决定。

## Agent Map

| Agent | CLI type | Recommended task type |
| --- | --- | --- |
| `AgentMiMo` | Claude Code Agent | review / re-review |
| `AgentDS` | Claude Code Agent | review / re-review |
| `AgentGLM` | Claude Code Agent | review / re-review |
| `AgentOpus` | Claude Code Agent | implementation / fix |
| `AgentCodex` | Codex Agent | implementation / fix |

Routing priority:

1. 用户或上层 skill 的明确分工优先。
2. 没有明确分工时，按上表选择适合任务类型的 Agent。
3. Agent 是否在线只影响可用性，不应让 review-only Agent 接 implementation / fix，也不应让 implementation/fix
   Agent 接 review / re-review，除非用户或上层 skill 明确授权。

## Prompt Syntax

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

派发 role-scoped worker handoff 时，不要让 worker 重新启动完整 workflow。也就是说，implementation / fix /
review worker prompt 里应写清 current gate、assigned scope、allowed files/modules、artifact path、stop condition，
而不是只写“使用 `$gateflow`”或“启动 `/gateflow`”。

如果目标 Agent 环境不支持对应 skill/slash command，controller 应把关键 criteria 内联进 handoff prompt，
不要只写 skill 名称。

## Tmux Pane Discovery

每次实际通信前，必须先确认目标 Agent 的当前 pane id：

```bash
tmux-cli status
```

查找到目标 Agent 后，记录 full pane id，例如：

```text
ai-2:1.3
```

后续 `tmux-cli send`、`tmux-cli wait_idle`、`tmux-cli capture` 都使用这个 full pane id。

要求：

- 每次发送前都重新确认目标 full pane id，即使刚刚确认过。
- 应优先使用 full pane id，避免发错目标。
- 如果目标 Agent 不在线、pane id 不明确、名称冲突、命令不可用，先停下来向用户报告，不要盲发 prompt。

## Session Clear

确认目标 full pane id 后，如果这是新的 assigned task 或新的 gate/slice，先向目标 pane 发送清 session 命令，再发送正式
handoff prompt。

Claude Code Agent 使用：

```text
/clear
```

Codex Agent 使用：

```text
/clear
```

要求：

- 等目标 Agent 完成 clear 并回到可输入状态后，再发送正式 handoff prompt；
- 不要把 clear 命令和正式任务 prompt 合并发送；
- 如果 clear 失败、目标 Agent 没有回到可输入状态，先停下来报告。

例外：如果判断该目标 Agent 当前 assigned task 尚未全部完成，正在等待补充信息、继续执行、返回 artifact、
修正同一轮输出或回答同一任务 follow-up，则不能 clear。此时保留现有 session，直接发送与当前未完成任务相关的补充指令。

## Tmux Send Text Safety

通过 `tmux-cli send` 发送 handoff prompt 时，避免正文中使用裸 `#数字`，某些环境会把 `PR #45` 这类文本截断。

写法要求：

- 不写 `PR #45`、`issue #123`；
- 改写为 `PR 45`、`PR-45`、`Pull Request 45`、`issue 123` 或 `issue-123`；
- 如果需要保留 GitHub URL，优先写完整 URL，而不是依赖 `#数字`；
- 如果发现目标 Agent 只收到截断内容，这属于同一未完成 assigned task 的补充场景，不要 clear；刷新
  `tmux-cli status` 后重新发送去掉 `#数字` 的完整 handoff。

## Agent Chat Workflow

与其它 CLI Agent 通信时，使用 `tmux-cli send` + `tmux-cli wait_idle` + `tmux-cli capture`。

新 assigned task 的标准流程：

```bash
tmux-cli status
tmux-cli send "/clear" --pane=<full-pane-id>
tmux-cli wait_idle --pane=<full-pane-id> --idle-time=3 --timeout=60
tmux-cli capture --pane=<full-pane-id>
tmux-cli send "<handoff prompt>" --pane=<full-pane-id>
tmux-cli wait_idle --pane=<full-pane-id> --idle-time=3 --timeout=<task-timeout-seconds>
tmux-cli capture --pane=<full-pane-id>
```

未完成 assigned task 的补充流程：

```bash
tmux-cli status
tmux-cli send "<follow-up prompt>" --pane=<full-pane-id>
tmux-cli wait_idle --pane=<full-pane-id> --idle-time=3 --timeout=<task-timeout-seconds>
tmux-cli capture --pane=<full-pane-id>
```

`tmux-cli execute` 只用于 shell command 且需要 exit code 的场景，例如测试、构建或脚本执行；不要用
`tmux-cli execute` 做 agent-to-agent chat。

## Handoff Checklist

每次向任何 Agent 发送 prompt 前，必须：

1. 运行 `tmux-cli status` 确认目标 full pane id；
2. 判断这是新任务还是未完成任务 follow-up；新任务先 clear，未完成任务不 clear；
3. 检查 prompt 文本，避免裸 `#数字`；
4. 确认目标 Agent 的 recommended task type 与当前任务匹配，或确认用户/上层 skill 明确授权了该分工；
5. 按目标 Agent 类型选择 `/skill` 或 `$skill`；
6. 写清 role-scoped handoff：current gate、assigned scope、allowed files/modules、artifact path、stop condition；
7. 明确 worker 不 commit、不 push、不 PR、不进入其它 gate，除非用户或上层流程明确授权。

如果目标 Agent 不可用，不要假装已经派发；报告不可用证据，并只在职责匹配或已获授权的 Agent 中选择替补，否则询问用户。
