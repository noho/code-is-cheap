# code-is-cheap

[English](README.md) | 中文

一套面向自动化 AI Coding 的工程控制框架。它的核心前提是：先把架构设计、phase/work unit 边界、进入 / 退出条件和
implementation control plan 做扎实；之后让 Agent 在明确 gate 内执行，留下 durable artifact、review decision、
residual-risk tracking 和 accepted checkpoint。

它不是一组零散 prompt，而是一套把 AI Coding 纳入工程闭环的工作流：确认目标和非目标，plan、review、按 slice 实施、
code review、fix、re-review、aggregate deepreview、residual risk tracking、本地 accepted commits、创建 draft PR、执行
PR review，并持续推进到 `draft-PR-pass`。merge、approve、mark ready for review、request reviewers、delete branch、
对外 comment、创建/修改外部 issue 仍然需要用户额外授权。

本仓库包含用于 Codex / Claude Code 的本地 skills 和配套脚本，覆盖 phase-driven development、gated feature
development、plan review、deep code review 和多 Agent handoff。

本仓库是 `skills/` 目录下所有 skill 的真源。Codex / Claude 的本地 skill 目录只是安装目标，不应作为编辑源。修改 skill 时先改本仓库，验证通过后再同步到本地运行环境。

## 运行截图

![code-is-cheap 在 tmux 中运行多个 Agent](working.png)
![code-is-cheap 在 tmux 中运行多个 Agent](working-2.png)

## 包含的 Skills

| Skill | 职责 |
| --- | --- |
| `gateflow` | 定义单个 work unit 的 gated workflow：preflight、goal confirmation、固定 gate order、artifacts、residual risks、accepted commits、draft PR gate 和 final closeout。它不定义项目级总控文档，也不定义多 Agent 路由。 |
| `phaseflow` | 项目分步总控。读取 `design_doc` 和 `control_doc`，识别当前 `phase = work unit`，和用户完成 preflight / goal confirmation，读取 Gateflow 的 `Gate Order`，逐 gate 派发 Agent，裁决结果，更新 `control_doc`，并 reconcile residual risks。 |
| `planreview` | 需要 adversarial review 一个 plan、implementation plan、migration phase plan、feature slice plan 或 Gateflow plan。 |
| `deepreview` | 需要严格 review 当前 workspace 改动、GitHub PR 或整个仓库。 |
| `init-agents` | 只定义 tmux 通信：Agent CLI 类型、`/skill` vs `$skill`、pane discovery、clear/session 规则、`tmux-cli send/wait_idle/capture` 和发送安全规则。它不分配角色。 |

## 使用演示

```text
按照 $phaseflow 推进，设计真源在 docs/host/design.md，总控文档是 docs/host/issues-implementation-control.md。
严格遵循 AGENTS.md 的约束。
```

等价的显式参数写法：

```text
$phaseflow design_doc=docs/host/design.md control_doc=docs/host/issues-implementation-control.md
```

## 核心工作流

典型使用方式是：

1. 先写好设计真源文档，例如 `docs/design.md` 或 `docs/host/design.md`。
2. 再写好实施总控文档，例如 `docs/implementation-control.md`，记录 phases/work units、状态、验证要求、artifacts、residual risks 和 next entry point。
3. 使用 `phaseflow` 读取这两个文档，识别当前 `phase = work unit`，并和用户完成 preflight 与 goal confirmation。
4. `phaseflow` 读取 Gateflow 的 `Gate Order`，逐 gate 把 plan / implementation / review / fix 等具体任务派发给 Agent。
5. 每个 Agent 返回后，`phaseflow` 读取 artifact、裁决 findings、更新 `control_doc`，再进入下一个 gate。
6. 所有 slices 完成后执行 aggregate deepreview；修复并复核通过后，记录 draft PR readiness 和 residual-risk owner。
7. draft PR gate 自动 push、创建 draft PR、执行 PR review；若有 accepted findings，则自动 fix、re-review、提交 accepted PR review commit 并再次 push，直到 `draft-PR-pass`。
8. 每个 phase/work unit 完成后，`phaseflow` reconcile residual risks、关闭已解决风险、标记当前 phase 完成，并写入 next entry point，方便用户 merge PR 后继续下一个 phase。

这个流程的目标不是让 Agent 自行发明架构，而是让 Agent 在已经明确的设计边界和总控计划内稳定执行，并把每一步的证据、
review 结论、修复状态和 residual risks 留在可追踪 artifact 中。

## 环境要求

- Codex CLI、Claude Code，或其它支持本地 skill-style instruction files 的 Agent runtime。
- 如果要运行本仓库自带的 skill 校验脚本，需要 Python 3.11+。
- 如果使用 `init-agents` 做多 Agent handoff，需要安装 `tmux` 和 `tmux-cli`。

如果要使用后文几个启动 Agent 的 zsh 函数中的 `tmux select-pane -T` 自动设置 pane title，需要先在 `~/.tmux.conf` 中固定 pane 标题，避免运行中的程序覆盖：

```tmux
# 固定 pane 标题，不让运行的程序覆盖
set -gw allow-set-title off
```

`tmux-cli` 属于 `claude-code-tools` 包，安装命令：

```bash
uv tool install claude-code-tools
```

官方文档：

- `tmux-cli`: https://pchalasani.github.io/claude-code-tools/tools/tmux-cli/
- `claude-code-tools` 安装说明: https://pchalasani.github.io/claude-code-tools/getting-started/

## 安装

克隆仓库：

```bash
git clone <repo-url> code-is-cheap
cd code-is-cheap
```

同步 skills 到已存在的本地 Codex / Claude skill 目录：

```bash
./scripts/sync-skills.sh
```

同步脚本会安装到以下已存在的目录：

```text
~/.codex/skills
~/.codex-pro/skills
~/.codex-business/skills
~/.claude/skills
```

同步后，重新打开一个 Codex / Claude session，让运行时重新加载 skill 列表。

## 准备 Agent 环境

`init-agents` 最适合配合多个 tmux pane 使用：每个 CLI Agent 独占一个 pane，并设置稳定的 pane title。下面是一套基于 `~/.zshrc` 函数的实用配置。

前置要求：

- `claude`、`codex`、`tmux`、`jq`、`curl`、`tmux-cli` 已在 `PATH` 中。
- 启动对应 Claude Code wrapper 前，先导出 provider API key：
  - `DEEPSEEK_API_KEY`
  - `MIMO_PLAN_API_KEY`
  - `GLM_API_KEY`
  - `KIMI_API_KEY`
- `opus_claude` 使用本机 Claude proxy：`http://localhost:4141`。
- Codex Pro 使用 `CODEX_HOME="$HOME/.codex-pro"`，这样可以和默认 controller Codex 使用不同身份 / 配置。

把下面函数加入 `~/.zshrc`：

```zsh
opus_claude() {
  curl -fsS --max-time 2 "http://localhost:4141" >/dev/null 2>&1 || {
    echo "localhost:4141 代理未启动或不可访问"
    return 1
  }

  local set_title=false
  local -a claude_args=()
  local arg
  for arg in "$@"; do
    case "$arg" in
      --title)
        set_title=true
        ;;
      *)
        claude_args+=("$arg")
        ;;
    esac
  done

  if [[ "$set_title" == true && -n "${TMUX:-}" ]] && command -v tmux >/dev/null 2>&1; then
    tmux select-pane -T "AgentOpus" >/dev/null 2>&1 || true
  fi

  local settings_json
  settings_json="$(jq -nc \
    --arg base_url "http://localhost:4141" \
    --arg auth_token "dummy" \
    --arg model "claude-opus-4.7" \
    '{
      env: {
        ANTHROPIC_BASE_URL: $base_url,
        ANTHROPIC_AUTH_TOKEN: $auth_token,
        ANTHROPIC_MODEL: $model,
        CLAUDE_CODE_EFFORT_LEVEL: "high"
      }
    }')"

  claude --settings "$settings_json" "${claude_args[@]}"
}

ds_claude() {
  [[ -z "$DEEPSEEK_API_KEY" ]] && echo "DEEPSEEK_API_KEY 未设置" && return 1

  local set_title=false
  local -a claude_args=("${(@)argv:#--title}")
  if (( ${argv[(Ie)--title]} )); then
    set_title=true
  fi

  if [[ "$set_title" == true && -n "${TMUX:-}" ]] && command -v tmux >/dev/null 2>&1; then
    tmux select-pane -T "AgentDS" >/dev/null 2>&1 || true
  fi

  local settings_json
  settings_json="$(jq -nc \
    --arg base_url "https://api.deepseek.com/anthropic" \
    --arg auth_token "$DEEPSEEK_API_KEY" \
    --arg model "deepseek-v4-pro[1m]" \
    '{
      env: {
        ANTHROPIC_BASE_URL: $base_url,
        ANTHROPIC_AUTH_TOKEN: $auth_token,
        ANTHROPIC_MODEL: $model,
        ANTHROPIC_DEFAULT_SONNET_MODEL: $model,
        ANTHROPIC_DEFAULT_OPUS_MODEL: $model,
        ANTHROPIC_DEFAULT_HAIKU_MODEL: $model,
        CLAUDE_CODE_SUBAGENT_MODEL: $model,
        CLAUDE_CODE_DISABLE_AUTO_TITLE: "1",
        CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1",
        CLAUDE_CODE_DISABLE_SESSIONMETADATA: "1",
        CLAUDE_CODE_DISABLE_QUOTA_CHECK: "1",
        DISABLE_NON_ESSENTIAL_MODEL_CALLS: "1",
        CLAUDE_CODE_EFFORT_LEVEL: "max"
      }
    }')"

  claude --settings "$settings_json" "${claude_args[@]}"
}

mimo_claude() {
  [[ -z "$MIMO_PLAN_API_KEY" ]] && echo "MIMO_PLAN_API_KEY 未设置" && return 1

  local set_title=false
  local -a claude_args=("${(@)argv:#--title}")
  if (( ${argv[(Ie)--title]} )); then
    set_title=true
  fi

  if [[ "$set_title" == true && -n "${TMUX:-}" ]] && command -v tmux >/dev/null 2>&1; then
    tmux select-pane -T "AgentMiMo" >/dev/null 2>&1 || true
  fi

  local settings_json
  settings_json="$(jq -nc \
    --arg base_url "https://token-plan-cn.xiaomimimo.com/anthropic" \
    --arg auth_token "$MIMO_PLAN_API_KEY" \
    --arg model "mimo-v2.5-pro[1m]" \
    '{
      env: {
        ANTHROPIC_BASE_URL: $base_url,
        ANTHROPIC_AUTH_TOKEN: $auth_token,
        ANTHROPIC_MODEL: $model,
        ANTHROPIC_DEFAULT_SONNET_MODEL: $model,
        ANTHROPIC_DEFAULT_OPUS_MODEL: $model,
        ANTHROPIC_DEFAULT_HAIKU_MODEL: $model,
        CLAUDE_CODE_SUBAGENT_MODEL: $model,
        CLAUDE_CODE_DISABLE_AUTO_TITLE: "1",
        CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1",
        CLAUDE_CODE_DISABLE_SESSIONMETADATA: "1",
        CLAUDE_CODE_DISABLE_QUOTA_CHECK: "1",
        DISABLE_NON_ESSENTIAL_MODEL_CALLS: "1",
        CLAUDE_CODE_EFFORT_LEVEL: "max"
      }
    }')"

  claude --settings "$settings_json" "${claude_args[@]}"
}

glm_claude() {
  [[ -z "$GLM_API_KEY" ]] && echo "GLM_API_KEY 未设置" && return 1

  local set_title=false
  local -a claude_args=("${(@)argv:#--title}")
  if (( ${argv[(Ie)--title]} )); then
    set_title=true
  fi

  if [[ "$set_title" == true && -n "${TMUX:-}" ]] && command -v tmux >/dev/null 2>&1; then
    tmux select-pane -T "AgentGLM" >/dev/null 2>&1 || true
  fi

  local settings_json
  settings_json="$(jq -nc \
    --arg base_url "https://open.bigmodel.cn/api/anthropic" \
    --arg auth_token "$GLM_API_KEY" \
    --arg model "GLM-5.1" \
    '{
      env: {
        ANTHROPIC_BASE_URL: $base_url,
        ANTHROPIC_AUTH_TOKEN: $auth_token,
        ANTHROPIC_MODEL: $model,
        ANTHROPIC_DEFAULT_SONNET_MODEL: $model,
        ANTHROPIC_DEFAULT_OPUS_MODEL: $model,
        ANTHROPIC_DEFAULT_HAIKU_MODEL: $model,
        CLAUDE_CODE_SUBAGENT_MODEL: $model,
        CLAUDE_CODE_DISABLE_AUTO_TITLE: "1",
        CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1",
        CLAUDE_CODE_DISABLE_SESSIONMETADATA: "1",
        CLAUDE_CODE_DISABLE_QUOTA_CHECK: "1",
        DISABLE_NON_ESSENTIAL_MODEL_CALLS: "1",
        CLAUDE_CODE_EFFORT_LEVEL: "max"
      }
    }')"

  claude --settings "$settings_json" "${claude_args[@]}"
}

kimi_claude() {
  [[ -z "$KIMI_API_KEY" ]] && echo "KIMI_API_KEY 未设置" && return 1

  local set_title=false
  local -a claude_args=("${(@)argv:#--title}")
  if (( ${argv[(Ie)--title]} )); then
    set_title=true
  fi

  if [[ "$set_title" == true && -n "${TMUX:-}" ]] && command -v tmux >/dev/null 2>&1; then
    tmux select-pane -T "AgentKIMI" >/dev/null 2>&1 || true
  fi

  local settings_json
  settings_json="$(jq -nc \
    --arg base_url "https://api.kimi.com/coding/" \
    --arg auth_token "$KIMI_API_KEY" \
    --arg model "kimi-for-coding" \
    '{
      env: {
        ANTHROPIC_BASE_URL: $base_url,
        ANTHROPIC_AUTH_TOKEN: $auth_token,
        ANTHROPIC_MODEL: $model,
        ANTHROPIC_DEFAULT_SONNET_MODEL: $model,
        ANTHROPIC_DEFAULT_OPUS_MODEL: $model,
        ANTHROPIC_DEFAULT_HAIKU_MODEL: $model,
        CLAUDE_CODE_SUBAGENT_MODEL: $model,
        CLAUDE_CODE_DISABLE_AUTO_TITLE: "1",
        CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1",
        CLAUDE_CODE_DISABLE_SESSIONMETADATA: "1",
        CLAUDE_CODE_DISABLE_QUOTA_CHECK: "1",
        DISABLE_NON_ESSENTIAL_MODEL_CALLS: "1",
        CLAUDE_CODE_EFFORT_LEVEL: "max"
      }
    }')"

  claude --settings "$settings_json" "${claude_args[@]}"
}

controller_codex() {
  local set_title=false
  local -a codex_args=("${(@)argv:#--title}")
  if (( ${argv[(Ie)--title]} )); then
    set_title=true
  fi

  if [[ "$set_title" == true && -n "${TMUX:-}" ]] && command -v tmux >/dev/null 2>&1; then
    tmux select-pane -T "AgentController" >/dev/null 2>&1 || true
  fi

  codex -s danger-full-access -a on-request -c shell_environment_policy.inherit=all "${codex_args[@]}"
}

pro_codex() {
  local set_title=false
  local -a codex_args=("${(@)argv:#--title}")
  if (( ${argv[(Ie)--title]} )); then
    set_title=true
  fi

  if [[ "$set_title" == true && -n "${TMUX:-}" ]] && command -v tmux >/dev/null 2>&1; then
    tmux select-pane -T "AgentCodex" >/dev/null 2>&1 || true
  fi

  mkdir -p "$HOME/.codex-pro"
  CODEX_HOME="$HOME/.codex-pro" codex -s danger-full-access -a on-request -c shell_environment_policy.inherit=all "${codex_args[@]}"
}

```

在不同 tmux pane 中启动 Agent，并传入 `--title`，让 `init-agents` 能识别它们：

```bash
controller_codex --title
pro_codex --title
opus_claude --title
ds_claude --title
mimo_claude --title
glm_claude --title
kimi_claude --title
```

预期 pane title 和一种可能的分工：

| Function | Pane title | 示例分工 |
| --- | --- | --- |
| `controller_codex --title` | `AgentController` | Phaseflow 总控 |
| `pro_codex --title` | `AgentCodex` | Plan / implementation / fix |
| `opus_claude --title` | `AgentOpus` | Review / re-review |
| `ds_claude --title` | `AgentDS` | Review / re-review |
| `mimo_claude --title` | `AgentMiMo` | Review / re-review |
| `glm_claude --title` | `AgentGLM` | Review / re-review |
| `kimi_claude --title` | `AgentKIMI` | Review / re-review |

`init-agents` 不分配这些角色。请在当前用户 prompt 中写清期望分工。

## 使用方式

### Gateflow

`gateflow` 用于单个 work unit：feature、issue、bug fix、migration、refactor、schema/public contract change 或
architecture-sensitive task。Gateflow 只定义 gates：preflight、goal confirmation、plan、review、implementation slices、
fixes、aggregate deepreview、accepted commits、draft PR gate 和 final closeout。

单独使用 Gateflow 示例：

```text
按照 $gateflow 开发 <work-unit>。
可选设计依据：docs/host/design.md。
先做 preflight 和 goal confirmation；用户确认目标、非目标和边界后，按 Gate Order 推进到 draft-PR-pass。
严格遵循 AGENTS.md 的约束。
```

Gateflow + `init-agents` 示例：

```text
按照 $gateflow 开发 <work-unit>。
$init-agents 路由 Agents，AgentCodex 负责 plan / implement / fix，AgentMiMo / AgentDS 负责两路同时 review / re-review。
每次发送前重新 discovery pane，clear 新任务 session，避免裸 #数字。
严格遵循 AGENTS.md 的约束。
```

### Phaseflow

当项目有设计真源文档和实施总控文档时，使用 `phaseflow`。Phaseflow 是项目分步总控：读取当前 `phase = work unit`，
和用户完成 preflight / goal confirmation，读取 Gateflow 的 `Gate Order`，逐 gate 派发 Agent，裁决结果，更新
`control_doc`，并 reconcile residual risks。

单独使用 Phaseflow 示例：

```text
按照 $phaseflow 推进，设计真源在 docs/host/design.md，总控文档是 docs/host/issues-implementation-control.md。
先读取 control_doc 识别当前 phase/work unit，再读取 design_doc。
总控 Agent 先完成 preflight 和 goal confirmation；用户确认后，按 Gateflow 的 Gate Order 逐 gate 派发 Agent 完成具体任务。
每个 gate 返回后更新 control_doc、记录 artifact / finding 裁决 / residual risk。
严格遵循 AGENTS.md 的约束。
```

Phaseflow + `init-agents` 示例：

```text
按照 $phaseflow 推进，设计真源在 docs/host/design.md，总控文档是 docs/host/issues-implementation-control.md。
$init-agents 路由 Agents，AgentMiMo / AgentDS 负责两路同时 review，AgentCodex 负责 plan / implement / fix。
总控 Agent 先做 preflight 和 goal confirmation；确认后按 Gateflow 的 Gate Order 逐 gate 派发。
每个 Agent 返回后，总控读取 artifact、裁决 finding、更新 control_doc、收集 residual risk、关闭已解决 risk。
严格遵循 AGENTS.md 的约束。
```

### Planreview

使用 `planreview` 检查 plan 是否具体、可直接实施、切片合理、架构边界清晰，并且没有过度设计。

Codex:

```text
$planreview docs/path/to/plan.md
```

Claude Code:

```text
/planreview docs/path/to/plan.md
```

预期输出是 durable review artifact，通常写到 `docs/reviews/` 或项目指定的 review 目录。

### Deepreview

使用 `deepreview` 做严格 code review。

review 当前分支相对 `main` 的改动：

```text
$deepreview
```

等价显式写法：

```text
$deepreview --base main
```

review 指定 PR：

```text
$deepreview --pr 123
```

review 整个仓库：

```text
$deepreview --all
```

Claude Code 使用 `/deepreview`，参数相同。

预期输出是 durable review artifact，包含基于证据的 findings、状态追踪和 residual risk 说明。

### Init Agents

当需要通过 tmux pane 向已经启动的 CLI Agent 发送任务时，使用 `init-agents`。它只定义通信：CLI 类型、`/skill` vs `$skill`、
pane discovery、clear/session 规则、`tmux-cli send/wait_idle/capture` 和发送安全规则。它不分配角色。

Codex:

```text
使用 $init-agents 初始化多 Agent 通信约定。
```

Claude Code:

```text
使用 /init-agents 初始化多 Agent 通信约定。
```

`init-agents` 使用以下基本命令：

```bash
tmux-cli status
tmux-cli send "<prompt>" --pane=<full-pane-id>
tmux-cli wait_idle --pane=<full-pane-id> --idle-time=3 --timeout=<seconds>
tmux-cli capture --pane=<full-pane-id>
```

Agent-to-agent chat 使用 `tmux-cli send` + `wait_idle` + `capture`。`tmux-cli execute` 只用于需要 exit code 的 shell command。

## 仓库结构

```text
skills/
  gateflow/
    SKILL.md
    agents/openai.yaml
  phaseflow/
    SKILL.md
    agents/openai.yaml
  planreview/
    SKILL.md
    agents/openai.yaml
  deepreview/
    SKILL.md
    agents/openai.yaml
  init-agents/
    SKILL.md
    agents/openai.yaml
scripts/
  validate-skills.sh
  sync-skills.sh
```

## 维护流程

只编辑本仓库中的真源文件：

```text
skills/<skill-name>/SKILL.md
skills/<skill-name>/agents/openai.yaml
```

校验全部 skills：

```bash
./scripts/validate-skills.sh
```

同步到本地 Codex / Claude homes：

```bash
./scripts/sync-skills.sh
```

同步脚本会先 validate，再把每个 skill 复制到已存在的本地目标目录。脚本不会 push、publish、create PR，也不会修改远程仓库。

## 说明

- `gateflow` 定义单个 work unit 的 gates。
- `phaseflow` 是项目分步总控；具体 plan / implementation / review / fix 任务交给 Agent 完成。
- `planreview` 和 `deepreview` 是 review skills。它们应该输出 durable artifacts，而不是只在聊天里给结论。
- 只有在通过 tmux 路由多个 CLI Agent 时才需要 `init-agents`。
