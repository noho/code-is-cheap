# code-is-cheap

[English](README.md) | 中文

一套面向自动化 AI Coding 的工程控制框架。它的核心前提是：先把架构设计、phase/work unit 边界、进入 / 退出条件和
implementation control plan 做扎实；之后让 Agent 在明确 gate 内执行，留下 durable artifact、review decision、
residual-risk tracking 和 accepted checkpoint。

它不是一组零散 prompt，而是一套把 AI Coding 纳入工程闭环的工作流：确认目标和非目标，plan、review、按 slice 实施、
code review、fix、re-review、aggregate deepreview、residual risk tracking、本地 accepted commits、创建 draft PR、执行
PR review，并持续推进到 final closeout。merge、approve、mark ready for review、request reviewers、delete branch、
对外 comment、创建/修改外部 issue 仍然需要用户额外授权。

本仓库包含用于 Codex / Claude Code 的本地 skills 和配套脚本，覆盖 phase-driven development、gated feature
development、plan review、deep code review 和多 Agent handoff。

本仓库是 `skills/` 下所有 skill、`scripts/agent-tools.zsh` 中 Agent 启动函数，以及 `scripts/*-agent-run` 子 Agent
调用入口的真源。本地运行时文件只是安装目标，不应作为编辑源；应先修改并验证仓库真源，再同步到本地运行环境。

## 包含的 Skills

| Skill | 职责 |
| --- | --- |
| `gateflow` | 定义单个 work unit 的 gated workflow：preflight、goal confirmation、固定 gate order、artifacts、residual risks、accepted commits、draft PR gate 和 final closeout。它不定义项目级总控文档，也不定义多 Agent 路由。 |
| `phaseflow` | 项目分步总控。读取 `design_doc` 和 `control_doc`，识别当前 `phase = work unit`，和用户完成 preflight / goal confirmation，读取 Gateflow 的 `Gate Order`，逐 gate 派发 Agent，裁决结果，更新 `control_doc`，并 reconcile residual risks。 |
| `planreview` | 需要 adversarial review 一个 plan、implementation plan、migration phase plan、feature slice plan 或 Gateflow plan。 |
| `deepreview` | 需要严格 review 当前 workspace 改动、GitHub PR 或整个仓库。 |
| `tmux-agents` | 只定义 tmux 通信：Agent CLI 类型、`/skill` vs `$skill`、pane discovery、clear/session 规则、`tmux-cli send/wait_idle/capture` 和发送安全规则。它不分配角色。 |
| `sub-agents` | 通过 runner 子进程启动外部 Claude Code 或 Codex 子 Agent，校验结构化结果，并支持隔离的并行派发；它不分配角色。 |

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
8. final closeout 随后记录变更内容、验证结果、文档更新、finding 状态、剩余风险和 owner、draft PR URL，以及 next entry point。
9. 如果 work unit 是 issue，draft PR body 应关联 issue；final closeout 应确认 issue closeout comment 和 merge 后关闭预期。
10. final closeout 通过后，用户手工 merge PR，拉取最新目标 base branch，按需 `/clear`，再从 `control_doc` 的 next entry point 恢复 `phaseflow`。

这个流程的目标不是让 Agent 自行发明架构，而是让 Agent 在已经明确的设计边界和总控计划内稳定执行，并把每一步的证据、
review 结论、修复状态和 residual risks 留在可追踪 artifact 中。

## 环境要求

- Codex CLI、Claude Code，或其它支持本地 skill-style instruction files 的 Agent runtime。
- 如果要运行本仓库自带的 skill 校验脚本，需要 Python 3.11+。
- 如果使用 `tmux-agents` 做多 Agent handoff，需要安装 `tmux` 和 `tmux-cli`。

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
~/.claude/skills
```

同步后，重新打开一个 Codex / Claude session，让运行时重新加载 skill 列表。

## 准备 Agent 环境

受版本控制的真源是 `scripts/agent-tools.zsh`、`scripts/claude-agent-run` 和 `scripts/codex-agent-run`，安装副本位于
`~/.config/zsh` 和 `~/.local/bin`。应修改仓库真源并重新同步，不要直接编辑安装副本。

前置要求：

- `zsh`、`claude`、`codex`、`jq` 和 `curl` 已在 `PATH` 中。
- `~/.local/bin` 已在 `PATH` 中，可以直接调用子 Agent runner。
- 启动对应 Agent 前已导出 provider 凭据：
  `DEEPSEEK_API_KEY`、`MIMO_PLAN_API_KEY`、`QWEN_API_KEY`、`KIMI_API_KEY` 和 `GLM_API_KEY`。
- 每个 Codex profile 都有可读的 `~/.codex-agent/<agent-id>/config.toml`。
- `local` 启动函数需要 `http://127.0.0.1:8080` 上存在健康的 OpenAI-compatible 服务。

凭据应保存在环境变量或不受版本控制的本机文件
`~/.config/zsh/agent-tools.local.zsh` 中。安装后的启动脚本会自动加载该文件。不要把凭据写入
`scripts/agent-tools.zsh`。

安装或更新启动函数和子 Agent runner：

```bash
./scripts/sync-agent-tools.sh
```

在 `~/.zshrc` 中加载：

```zsh
[[ -r "$HOME/.config/zsh/agent-tools.zsh" ]] && source "$HOME/.config/zsh/agent-tools.zsh"
```

同步后重新加载当前 shell：

```bash
source ~/.zshrc
```

可用启动命令：

| Runtime | Agent IDs | 命令 |
| --- | --- | --- |
| Claude Code | `ds`、`mimo`、`mimo-fast`、`mimo-flash`、`qwen`、`kimi`、`glm`、`glm-flash`、`local` | `<agent-id>_claude [args...]` |
| Codex CLI | `ds`、`mimo`、`mimo-fast`、`mimo-flash`、`qwen`、`kimi`、`glm`、`glm-flash`、`local`、`gpt-6-astra`、`gpt-6-sol`、`gpt-6-luna`、`business` | `<agent-id>_codex [args...]` |
| Codex app | 与 Codex CLI 相同 | `<agent-id>_codex_app [workspace]` |

CLI 启动命令可传入 `--title`，设置 `ClaudeAgent-DS`、`CodexAgent-GPT-6-Astra` 这类稳定的 tmux pane title。
app 启动命令会使用所选 profile 和可选 workspace 打开一个新的 Codex app 实例。

```bash
mimo_claude --title
gpt-6-astra_codex --title
business_codex_app /path/to/workspace
```

`tmux-agents` 会发现这些 pane title，但不会分配角色。请在当前用户 prompt 中写清期望分工。

总控非交互调用子 Agent 时，使用已安装的 runner 命令：

```bash
claude-agent-run --provider mimo --cwd /path/to/workspace --prompt-file task.md
codex-agent-run --provider gpt-6-astra --cwd /path/to/workspace --prompt-file task.md
```

runner 可通过 `--prompt`、`--prompt-file`、位置参数或 stdin 接收 prompt，并支持输出文件、临时或持久 session，
以及 provider-specific passthrough arguments。完整接口使用 `--help` 查看。总控必须显式传入 `--cwd`，避免子 Agent
意外继承总控的 workspace。

派发前用 `sub-agent-preflight` 执行 `$sub-agents` 的预检（workspace、git 条件、provider 与 launcher 部署状态、
输出路径是否全新），并生成 run dir、canary 文件与**完整 prompt**（任务正文 + 固定报告协议）：

```bash
sub-agent-preflight --runtime codex --provider gpt-6-sol --cwd /path/to/workspace --label review-sol-01 --task-file task.md
```

它输出 `key=value` 报告和可直接执行的完整命令（`setup_status=ok` 才可派发）。派发必须有真实任务：给 `--task` /
`--task-file` 由脚本拼出 prompt，或给 `--prompt-file` 提供完整 prompt；三者必须且只能给一个，否则预检失败且不输出
命令。prompt 还必须带 Dispatch Contract 的三节 —— `目标` / `非目标` / `停止条件`（每节单独一行、行首写节名，
英文 `Goal` / `Non-goals` / `Stop condition` 等价），预检会校验。canary token 不会打印、也不会进入 prompt ——
子 Agent 自己从生成的文件读取。

## Codex Agent 配置（xx_codex）

每个 `xx_codex` launcher 读取 `~/.codex-agent/<agent-id>/config.toml`。九个第三方 profile（`ds`、`glm`、`glm-flash`、`kimi`、
`mimo`、`mimo-fast`、`mimo-flash`、`qwen`、`local`）与三个订阅制 OpenAI profile（`gpt-6-astra`、`gpt-6-sol`、`gpt-6-luna`）已在仓库
`codex-agent/profiles/` 下维护；`business`、`codex` 不在管理范围内。

`gpt-6-astra` 留给重要、低频的任务；`gpt-6-sol` 用于日常消耗量大的任务，`gpt-6-luna` 负责低成本的批量任务。
三个都是 medium reasoning effort。

| Profile | 模型 | 网关 | shim 端口 | 网关修复 |
| --- | --- | --- | --- | --- |
| `ds` | `deepseek-flash` | api.deepseek.com | 8788 | 仅改模型名 |
| `glm` | `glm-5.3` | open.bigmodel.cn | 8789 | 仅改模型名 |
| `glm-flash` | `glm-5.3-flash` | open.bigmodel.cn | 8795 | 仅改模型名 |
| `kimi` | `kimi-k3` | api.kimi.com | 8790 | + 目录补丁 |
| `mimo` | `mimo-v2.6-pro` | token-plan-cn.xiaomimimo.com | 8791 | + 目录补丁 + `json_object` 降级 |
| `mimo-fast` | `mimo-v2.6-pro-ultraspeed` | api.xiaomimimo.com | 8794 | + 目录补丁 + `json_object` 降级 |
| `mimo-flash` | `mimo-v2.6-flash` | token-plan-cn.xiaomimimo.com | 8793 | + 目录补丁 + `json_object` 降级 |
| `qwen` | `qwen3.8-max` | dashscope.aliyuncs.com | 8792 | + 目录补丁 + message-id 前缀修正 |
| `local` | `qwen3.8-27b-local` | 127.0.0.1:8080（llama.cpp） | 无 | 不走沙箱、不走 shim |
| `gpt-6-astra` | `gpt-6-astra` | OpenAI（ChatGPT 登录） | 无 | 不走 shim，订阅制 |
| `gpt-6-sol` | `gpt-6-sol` | OpenAI（ChatGPT 登录） | 无 | 不走 shim，订阅制 |
| `gpt-6-luna` | `gpt-6-luna` | OpenAI（ChatGPT 登录） | 无 | 不走 shim，订阅制 |

凭据保持在环境变量里（`DEEPSEEK_API_KEY`、`GLM_API_KEY`、`KIMI_API_KEY`、`MIMO_PLAN_API_KEY`、`MIMO_API_KEY`、`QWEN_API_KEY`）；
`local` 不需要 key；三个 OpenAI profile 用 ChatGPT 账号登录，各自的 profile home 里保存自己的 `auth.json`，
不入仓库。

安装或更新：

```bash
# 安装 profiles、shim 脚本、路由表，并重新生成 model catalog
./scripts/sync-codex-agent.sh

# 可选但推荐：把 shim 交给 launchd 常驻
~/.codex-agent/bin/codex-auto-review-shim-service install
```

仓库模板中的本机路径写作 `@HOME@`，由同步脚本在安装时替换为实际 home（Codex 只接受绝对路径）。

模板只承载仓库拥有的设置（model、reasoning effort、沙箱、审批、`web_search`、`service_tier`、env 策略）。
Codex 本体和 ChatGPT 桌面端还会往同一个文件写本机状态——`[projects.*]` trust、`[hooks.state]`、
`[mcp_servers.*]`、`[plugins.*]`、`[marketplaces.*]`、`[tui.*]`、`[desktop]` 以及 `notify` 这类根键。同步脚本
会把这些内容从 live 文件合并进来（`scripts/codex-config-merge.py`）而不是丢掉；合并失败时脚本中止，
live 文件保持原样。

`model-catalog.json`（kimi / mimo / qwen）是**生成型产物，不入仓库**。同步脚本会用 Codex 内置目录
（`codex debug models`，在全新 `CODEX_HOME` 下取）重新生成；若 Codex 改了目录结构，生成脚本会 WARNING 且
非零退出，已有的 catalog 保持不动。

### 切换 sandbox 模式

每个 profile 只用一行决定沙箱。改 `codex-agent/profiles/<agent-id>/config.toml` 里的 `sandbox_mode`，重跑
`./scripts/sync-codex-agent.sh` 即可：

| 取值 | 效果 | 谁在用 |
| --- | --- | --- |
| `"workspace-write"` | 写入限制在 workspace；`[sandbox_workspace_write] network_access = true` 保持网络放开。需要 shim 处于运行状态 | 五个第三方子 Agent profile |
| `"danger-full-access"` | 无沙箱 | `local`——只在终端交互使用，不作为子 Agent 派发 |

`local` 的 `base_url` 直连 llama.cpp（`http://127.0.0.1:8080/v1`），上方被注释的那行是已停用的 shim 路由，留作参考。

## 使用方式

### Gateflow

`gateflow` 用于单个 work unit：feature、issue、bug fix、migration、refactor、schema/public contract change 或
architecture-sensitive task。Gateflow 只定义 gates：preflight、goal confirmation、plan、review、implementation slices、
fixes、aggregate deepreview、accepted commits、draft PR gate 和 final closeout。

单独使用 Gateflow 示例：

```text
按照 $gateflow 开发 <work-unit>。
可选设计依据：docs/host/design.md。
先做 preflight 和 goal confirmation；用户确认目标、非目标和边界后，按 Gate Order 推进到 final closeout。
严格遵循 AGENTS.md 的约束。
```

Gateflow + `tmux-agents` 示例：

```text
按照 $gateflow 开发 <work-unit>。
$tmux-agents 路由 Agents，CodexAgent-GPT-6-Astra 负责 plan / implement / fix，ClaudeAgent-MiMo / ClaudeAgent-DS 负责两路同时 review / re-review。
每次发送前重新 discovery pane，clear 新任务 session，避免裸 #数字。
严格遵循 AGENTS.md 的约束。
```

Gateflow + `sub-agents` 示例：

```text
按照 $gateflow 开发 <work-unit>。
$sub-agents 通过 runner 子进程派发：Codex gpt-6-astra 负责 plan / implement / fix，Claude mimo / ds 负责两路 review / re-review。
所有调用显式传入 workspace 绝对路径，并使用独立 output / stderr 文件；总控检查结构化结果后自行裁决。
严格遵循 AGENTS.md 的约束。
```

### Phaseflow

当项目有设计真源文档和实施总控文档时，使用 `phaseflow`。Phaseflow 是项目分步总控：读取当前 `phase = work unit`，
和用户完成 preflight / goal confirmation，读取 Gateflow 的 `Gate Order`，逐 gate 派发 Agent，裁决结果，更新
`control_doc`，并 reconcile residual risks。

单独使用 Phaseflow 示例：

未指定派发协议时，Phaseflow 默认使用 `sub-agents`。只有显式指定 `$tmux-agents` 时才通过已有 tmux pane 派发。

```text
按照 $phaseflow 推进，设计真源在 docs/host/design.md，总控文档是 docs/host/issues-implementation-control.md。
先读取 control_doc 识别当前 phase/work unit，再读取 design_doc。
总控 Agent 先完成 preflight 和 goal confirmation；用户确认后，按 Gateflow 的 Gate Order 逐 gate 派发 Agent 完成具体任务。
每个 gate 返回后更新 control_doc、记录 artifact / finding 裁决 / residual risk。
final closeout 后说明用户 merge PR、拉取目标 base branch，并从 control_doc 的 next entry point 继续下一轮。
严格遵循 AGENTS.md 的约束。
```

Phaseflow + `tmux-agents` 示例：

```text
按照 $phaseflow 推进，设计真源在 docs/host/design.md，总控文档是 docs/host/issues-implementation-control.md。
$tmux-agents 路由 Agents，ClaudeAgent-MiMo / ClaudeAgent-DS 负责两路同时 review，CodexAgent-GPT-6-Astra 负责 plan / implement / fix。
总控 Agent 先做 preflight 和 goal confirmation；确认后按 Gateflow 的 Gate Order 逐 gate 派发。
每个 Agent 返回后，总控读取 artifact、裁决 finding、更新 control_doc、收集 residual risk、关闭已解决 risk。
final closeout 后说明用户 merge PR、拉取目标 base branch，并从 control_doc 的 next entry point 继续下一轮。
严格遵循 AGENTS.md 的约束。
```

Phaseflow + `sub-agents` 示例：

```text
按照 $phaseflow 推进，设计真源在 docs/host/design.md，总控文档是 docs/host/issues-implementation-control.md。
$sub-agents 通过 runner 子进程派发，Claude mimo / ds 负责两路 review，Codex gpt-6-astra 负责 plan / implement / fix。
总控按 Gateflow 的 Gate Order 推进，检查每个子进程的退出状态和结构化输出，并更新 control_doc。
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

### Tmux Agents

当需要通过 tmux pane 向已经启动的 CLI Agent 发送任务时，使用 `tmux-agents`。它只定义通信：CLI 类型、`/skill` vs `$skill`、
pane discovery、clear/session 规则、`tmux-cli send/wait_idle/capture` 和发送安全规则。它不分配角色。

Codex:

```text
使用 $tmux-agents 初始化多 Agent 通信约定。
```

Claude Code:

```text
使用 /tmux-agents 初始化多 Agent 通信约定。
```

`tmux-agents` 使用以下基本命令：

```bash
tmux-cli status
tmux-cli send "<prompt>" --pane=<full-pane-id>
tmux-cli wait_idle --pane=<full-pane-id> --idle-time=3 --timeout=<seconds>
tmux-cli capture --pane=<full-pane-id>
```

Agent-to-agent chat 使用 `tmux-cli send` + `wait_idle` + `capture`。`tmux-cli execute` 只用于需要 exit code 的 shell command。

### Sub Agents

总控需要通过已安装的 runner 启动外部 Claude Code 或 Codex 子进程时，使用 `sub-agents`。该 skill 定义 workspace
隔离、边界明确的 prompt、并行执行、输出校验、重试上限、session 延续和总控裁决。

Codex:

```text
使用 $sub-agents 通过 runner 子进程派发并裁决当前子任务。
```

Claude Code:

```text
使用 /sub-agents 通过 runner 子进程派发并裁决当前子任务。
```

底层命令为：

```bash
claude-agent-run --provider <provider> --cwd <absolute-workspace> ...
codex-agent-run --provider <provider> --cwd <absolute-workspace> ...
```

写入范围不重叠的独立任务可以并发。总控采纳任何结果前，必须检查 exit code、stderr 和结构化输出。

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
  tmux-agents/
    SKILL.md
    agents/openai.yaml
  sub-agents/
    SKILL.md
    agents/openai.yaml
codex-agent/
  profiles/
    ds/config.toml
    glm/config.toml
    glm-flash/config.toml
    kimi/config.toml
    mimo/config.toml
    mimo-fast/config.toml
    mimo-flash/config.toml
    qwen/config.toml
    local/config.toml
    gpt-6-astra/config.toml
    gpt-6-sol/config.toml
    gpt-6-luna/config.toml
  bin/
    codex-auto-review-shim
    codex-auto-review-shim-service
  shim-routes.json
scripts/
  agent-tools.zsh
  claude-agent-run
  codex-agent-run
  codex-config-merge.py
  sub-agent-preflight
  patch-codex-model-catalog.py
  sync-agent-tools.sh
  sync-codex-agent.sh
  validate-skills.sh
  sync-skills.sh
```

## 维护流程

只编辑本仓库中的真源文件：

```text
skills/<skill-name>/SKILL.md
skills/<skill-name>/agents/openai.yaml
scripts/agent-tools.zsh
scripts/claude-agent-run
scripts/codex-agent-run
codex-agent/profiles/<agent-id>/config.toml
codex-agent/bin/
codex-agent/shim-routes.json
scripts/patch-codex-model-catalog.py
```

校验全部 skills：

```bash
./scripts/validate-skills.sh
```

同步到本地 Codex / Claude homes：

```bash
./scripts/sync-skills.sh
```

同步 Agent 启动函数和子 Agent runner：

```bash
./scripts/sync-agent-tools.sh
```

同步 Codex Agent profiles、shim 脚本与路由表：

```bash
./scripts/sync-codex-agent.sh
```

skill 同步脚本会先 validate，再把每个 skill 复制到已存在的本地目标目录。agent-tools 同步脚本以 `600` 权限把
启动函数安装到 `~/.config/zsh/agent-tools.zsh`，并以 `755` 权限把 runner 安装到 `~/.local/bin`。codex-agent
同步脚本覆盖 `config.toml` 前先写时间戳备份，安装 shim 脚本与路由表，并重新生成不入仓库的
`model-catalog.json`。这些脚本都不会 push、publish、create PR，也不会修改远程仓库。

## 说明

- `gateflow` 定义单个 work unit 的 gates。
- `phaseflow` 是项目分步总控；具体 plan / implementation / review / fix 任务交给 Agent 完成。
- `planreview` 和 `deepreview` 是 review skills。它们应该输出 durable artifacts，而不是只在聊天里给结论。
- 只有在通过 tmux 路由多个 CLI Agent 时才需要 `tmux-agents`。
- 总控通过 runner 子进程启动外部子 Agent 时使用 `sub-agents`。
