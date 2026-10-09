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

`tmux-cli` 属于 `claude-code-tools` 包。安装或更新到固定的官方发行版：

```bash
uv tool install --force 'claude-code-tools==1.29.1'
```

此命令会更新整个 `claude-code-tools` 包，不只更新 `tmux-cli`。[v1.29.1](https://github.com/pchalasani/claude-code-tools/releases/tag/v1.29.1) 已通过合入上游的 [PR #213](https://github.com/pchalasani/claude-code-tools/pull/213) 包含我们的 [PR #212](https://github.com/pchalasani/claude-code-tools/pull/212)：remote status/preflight 不再创建托管 session，缓存的 window target 会在复用前重新验证。无需再依赖 fork。本项目的 skills 另用已有的 `./scripts/sync-skills.sh` 同步。

官方文档：

- `tmux-cli`: https://pchalasani.github.io/claude-code-tools/tools/tmux-cli/
- `claude-code-tools` 安装说明: https://pchalasani.github.io/claude-code-tools/getting-started/

## 安装

macOS 上需已有 Git、Codex CLI、Claude Code、Python 3.11+、jq、uv、tmux、rsync、zsh 和 curl。下载并运行安装入口：

```bash
curl -fsSL https://raw.githubusercontent.com/noho/code-is-cheap/main/install.sh -o install-code-is-cheap.sh
bash install-code-is-cheap.sh
```

下载成功后再执行第二条命令。已有 checkout 可直接运行 `bash ./install.sh`。
下载的安装脚本将仓库克隆到 `~/.local/share/code-is-cheap`；重复运行时对干净的 `main` checkout 执行 fast-forward 更新。可通过 `AGENT_INSTALL_DIR` 指定其它目录。

脚本创建含 PyYAML 的独立校验环境（以后手动 sync 也会自动复用），安装 `claude-code-tools==1.29.1`，将 skills 同步到 `~/.codex/skills` 和 `~/.claude/skills`，部署启动函数、runner、模型卡，向 `~/.zshrc` 添加 PATH 和 launcher 加载入口，并安装 launchd shim 服务。`bash install.sh --no-service` 可跳过服务安装。脚本不安装 Codex/Claude CLI、不登录账号、不创建可选 business 账号 home，也不启动本地模型服务。

已有私有连接 JSON、Codex 登录和其它本机 Codex 设置会保留。安装后重新打开 Agent 会话以加载 skills，并运行 `source ~/.zshrc` 在当前 shell 加载启动函数。

### 私有连接配置：default 和 override

`~/.config/agent-tools/endpoints.json` 统一保存每个 provider/runtime 的上游 URL、模型 ID 和 API key，权限必须为 `600`。安装器仅在文件不存在时创建；sync 不创建或修改用户文件。`config/endpoints.example.json` 是单独部署的程序默认资源，不含云端凭据。初始 URL 和模型选择保持当前值；以下示例不会自动选择新云商。

- `default`：你的基线连接，每个 runtime 包含 `base_url`、`upstream_model`、`api_key`。
- `override`：可选的覆盖连接，沿用 provider/runtime 层级。覆盖必须**同时填写这三个字段**，避免新云商沿用旧云商的 key。其他 runtime/provider 保持默认连接；删除该 runtime 的 override 即可恢复。
- 缺少文件或某个 runtime 连接时使用程序默认资源；云端启动仍需要有效连接中的非空 key。已有文件必须包含 `default`；未知字段、不完整覆盖、空 URL/模型、重复 JSON 字段和不安全权限会明确报错。空字符串不表示继承。

例如在 `override` 中添加以下连接，仅切换 `ds-flash_codex`（填入网关实际 URL/模型/key）：

```json
{
  "default": {},
  "override": {
    "ds-flash": {
      "codex": {
        "base_url": "https://gateway.example/custom/v1",
        "upstream_model": "gateway/model-id",
        "api_key": "YOUR_GATEWAY_KEY"
      }
    }
  }
}
```

编辑初始化文件时保留已有的 `default`，只添加 override；上面的空块仅为缩短示例。Codex 的 `base_url` 是完整 Responses API base URL，不含 `/responses`；Claude 使用 Anthropic API base URL，不含 `/v1/messages`，准确传递 `upstream_model`，不额外追加 `[1m]`。两者沿用现有 Bearer 鉴权方式。不转换 API 协议，网关必须支持对应 API/模型以及流式响应、工具调用。保留现有 profile 的上下文限制和 catalog 元数据，切换前需确认网关支持这些能力。

Claude 启动时读取一份连接快照，只将选定 token 交给 Claude 进程，不放进 argv/settings JSON。Codex 云端保留逻辑模型卡/catalog 和 loopback provider ID；shim 每次请求读取一致的 URL/模型/key 快照，将普通逻辑模型和 `codex-auto-review` 映射到配置的上游模型，并自行添加选定 Bearer token。普通流式请求不会被缓冲，guardian 的重试行为单独保留。拒绝上游重定向，避免向其他地址转发 key。云端连接修改后下一次请求直接生效，无需 sync 或重启服务，App 会话也适用。

`local.codex` 仍直接连接且不鉴权，`api_key` 必须为空；修改 URL 后需运行 `sync-codex-agent.sh`，模型在 CLI/App 启动时应用。`local.claude` 和其它 Claude 连接一样使用配置中的 URL/模型/token，初始 token 为 `local`。GPT/business 继续使用原有账号登录和模型卡。网关 API key 不写入 provider registry、catalog、App 配置或服务 plist；账号登录仍使用 Codex 的 auth 文件。仍清理继承的凭据环境变量；`600` 权限不隔离同用户运行的其他进程对文件的访问。

## 可选任务禁读边界（macOS）

**平台限制：`agent-sandbox --deny-list` 当前仅支持 macOS**，通过 srt 使用 Seatbelt。
本项目尚未实现和验证 Linux 封装，Windows 不支持。非 macOS 系统会明确报错，不会退回无沙箱运行。
`--full-access` 使用 runtime 原生参数，不依赖 Seatbelt。

默认 runner/launcher 行为不变。显式 `--full-access`：Codex 关闭内层沙箱和审批；Claude 使用
`bypassPermissions` 并关闭内层沙箱。单独使用该参数没有读取隔离。

普通安装之后，需要禁读边界时再安装可选依赖（Node >=22.12、npm）：

```bash
install-agent-sandbox.sh
```

安装固定版本 Anthropic 的 Apache-2.0 `@anthropic-ai/sandbox-runtime` 0.0.79。普通安装/sync 不要求或安装 srt。
封装要求安装的 **Node 包 CLI**，不接受独立编译版 srt；sync 同时部署相邻的 `agent-sandbox-launch.mjs`。
适配器将同一禁令中同父目录的字面路径/子树条件合并为有长度上限的精确正则并集，避免 Seatbelt 字面量数据表超限；
保留所有路径、子树范围、规则顺序和操作。压缩时原策略保存在受写保护的 `seatbelt.source.sb`，实际策略保存为
`seatbelt.sb` 并通过 `sandbox-exec -f` 加载，避免大策略嵌入启动参数导致 `spawn E2BIG`。预检和启动共用不派生子进程的安装结构/模块检查；不支持的 CLI 启动结构明确失败。macOS 原生策略编译器
仍有容量限制；编译失败时在验证及 runner 启动前停止，不删减禁读项或扩大权限。
两个封装命令由 `scripts/sync-agent-tools.sh` 部署。已测试 macOS、Codex 0.161.0、Claude Code 2.1.294。

`denied.json` 为非空 JSON 数组，每项是**绝对且已存在**的禁读文件/目录，字面路径，不是 glob；目录递归禁止。
调用方自行列出业务报告、历史日志及已知副本；未列出的副本仍可读。

```bash
agent-sandbox --cwd /path/to/workspace --deny-list /path/to/denied.json -- \
  codex-agent-run --provider mimo --prompt-file /path/to/task.md \
  --output /path/to/new-events.jsonl --stderr /path/to/new-stderr
# claude-agent-run 使用相同封装。
```

封装隐含 `--full-access --no-persist`，启动前固定策略，在 Seatbelt 内确认禁读路径确实被拒绝，再启动 runner。
不支持的参数、缺失路径、版本不匹配、已有硬链接、无法保留原写边界的配置均明确失败，不退回无隔离运行。
写入保留原 runtime 的保守子集：Codex read-only 不开放 cwd 写入；workspace-write 保留 cwd 并保护
`.git/.codex/.agents/.aws`，不携带额外 writable roots。Claude 保留 cwd 和各设置层中绝对路径或 `~/` 开头的字面 sandbox `denyWrite`。
仅另加调用方指定的输出**文件**与独立运行状态目录，不开放输出文件的整个父目录。Codex permission profiles、
项目层配置，以及 Claude 自定义读、glob/相对写路径或工具 deny 规则暂不支持。原 Codex `.rules` 复制到独立 home 并禁止修改。禁读路径同时不可写。
运行时必需的凭据/配置文件（包括 endpoints JSON、所选 Codex auth）必须可读；列入禁读时 setup 停止。封装不隔离 Agent 与工具对凭据的访问。

隔离运行使用全新 runtime 状态，关闭宿主 MCP/hooks/plugins/浏览器集成，禁止 Apple Events/Unix sockets，
网络限于所选模型路由；Claude 只启用 Bash/Read/Write/Edit/Glob/Grep，Codex 保留本地原生工具。
可用 `--allow-domain host[:port]` 额外开放调用方授权的网络目的地。权限不足应报告缺项，不自动放宽。
每次策略/状态路径打印在 stderr 并保留在临时目录。运行期间不能由未隔离进程替换禁读路径或另造可读副本。
路径禁令不识别其它位置的相同内容，也不隔离 prompt 已提供的信息；runtime 升级后应重测读取通道。

preflight 可加 `--deny-list /absolute/denied.json` 生成完整封装命令；`--check` 仅预检，不证明内核隔离。
封装必须从**总控**沙箱外派发：Codex 用 `exec_command(require_escalated)`；Claude 在自己的
`sandbox.excludedCommands` 加入 `agent-sandbox`，以独立裸命令调用。生命周期、canary、结果验收仍按现有协议。
一次隔离调用不支持 resume、动态投递或原生参数透传。必须恰好一个非空 `--prompt` 或普通 `--prompt-file`；
关闭 stdin，并将准备好的 prompt 复制到受写保护的运行状态。验证同时查询 Seatbelt 权限和实际文件读取；普通 Unix 权限错误不足以证明隔离。

## 准备 Agent 环境

如果已成功运行 `install.sh`，可跳过本节的手动部署步骤：安装器已部署 launcher/runner、模型卡并配置 shell 加载入口。仍需按上一节填写 API key 和可选的自定义 URL，并执行 `source ~/.zshrc`（或打开新 shell）以加载启动函数；另需重新打开 Agent 会话以加载 skills。使用可选的 `business` 或本地模型时，仍需自行准备对应账号 home 或本地服务。下面的步骤用于手动安装或后续更新。

受版本控制的真源是 `scripts/agent-tools.zsh`、`scripts/claude-agent-run` 和 `scripts/codex-agent-run`，安装副本位于
`~/.config/zsh` 和 `~/.local/bin`。应修改仓库真源并重新同步，不要直接编辑安装副本。
`sync-agent-tools.sh` 还会把 URL helper、默认 URL 资源和 `repair-codex-reasoning-history.py` 安装到 `~/.local/bin`。

前置要求：

- `zsh`、`claude`、`codex`、`jq` 和 `curl` 已在 `PATH` 中。
- URL 读取和 `--resume` 修复需要 `python3` 3.11 或更新版本；`agent-endpoint.py` 应与其它 runner 一起在 `PATH` 中。
- `~/.local/bin` 已在 `PATH` 中，可以直接调用子 Agent runner。
- 私有连接 JSON 中选定云端 runtime 的 `api_key` 已填入非空值。
- 每个 Codex profile 的模型卡已部署为可读的 `~/.codex/<agent-id>.config.toml`（`business` 例外：`~/.codex-agent/business/config.toml`）。
- `local` 服务地址由 `~/.config/agent-tools/endpoints.json` 中 `default` 或 `override` 下的 `local.claude.base_url`、`local.codex.base_url` 决定，默认 `http://127.0.0.1:8080`；健康检查使用对应 runtime 的 URL 加 `/health`（Codex 先去掉末尾 `/v1`），因此 Claude/Codex 可配置不同端口。

凭据只保存在私有连接 JSON 中，不入仓库。

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
| Claude Code | `ds-flash`、`mimo`、`mimo-fast`、`mimo-flash`、`qwen`、`kimi`、`glm`、`glm-flash`、`local`、`hy` | `<agent-id>_claude [args...]` |
| Codex CLI | `ds-flash`、`mimo`、`mimo-fast`、`mimo-flash`、`qwen`、`kimi`、`glm`、`glm-flash`、`local`、`gpt-6-astra`、`gpt-6-sol`、`gpt-6-luna`、`business` | `<agent-id>_codex [args...]` |
| Codex app | 与 Codex CLI 相同 | `<agent-id>_codex_app [workspace]` |

CLI 启动命令可传入 `--title`，设置 `ClaudeAgent-DS-Flash`、`CodexAgent-GPT-6-Astra` 这类稳定的 tmux pane title。
`hy`（tokenhub.tencentmaas.com 上的 hy4-preview，key 来自连接 JSON）**仅提供 Claude runtime**：该网关的 `/v1/responses` SSE
上游对 Codex 自动安全审核的 escalation 过于不稳（2026-09-24 实测），Codex 侧 profile 已移除。
app 启动命令会使用所选 profile 和可选 workspace 打开一个新的 Codex app 实例。桌面 app 只读 `$CODEX_HOME/config.toml`
全文（没有 `-p` 叠加），所以每个受管 app 实例在自己的 user-data 目录里拿一份**合成 home**（共享 base ＋ 所选模型卡，
`compose-codex-app-config.py` 每次启动幂等合成）——启动即所选模型；各 app home 的会话记录彼此隔离。
CLI 会话若要跨模型续接，请在共享 home 中显式指定目标 profile（
`gpt-6-sol_codex resume <session-id>` 或 `codex resume -p gpt-6-sol <session-id>`）。

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

所有受管 profile 共享一个 Codex home（`~/.codex`，Codex 默认 home，**必须是真目录**——桌面 app 沙箱拒绝路径中的 symlink 成分）：base `config.toml` 承载政策与
机器本地运行时状态，每个 profile 是一张模型卡 `~/.codex/<agent-id>.config.toml`，launcher 用
`codex -p <agent-id>` 叠加加载——启动选卡即切模型，会话池共享。换模型续同一段对话时，用目标模型的
launcher（如 `gpt-6-sol_codex resume <session-id>`），或显式传入 profile（如
`codex resume -p gpt-6-sol <session-id>`）。单独执行 `codex resume <session-id>` 可能恢复会话上次选中的模型，
不能保证使用 base config 的默认模型。九个第三方 profile（`ds-flash`、`glm`、`glm-flash`、`kimi`、
`mimo`、`mimo-fast`、`mimo-flash`、`qwen`、`local`）与三个订阅制 OpenAI profile（`gpt-6-astra`、`gpt-6-sol`、`gpt-6-luna`）已在仓库
`codex-agent/profiles/` 下维护；`business` 保留独立的 CODEX_HOME（`~/.codex-agent/business`，另一账号）。
共享 base 配置仍归本机管理，只有带标记的 provider 注册块由本仓库管理。

要一条命令修复并恢复跨模型会话，先退出其他正在使用它的 Codex 窗口，再运行
`gpt-6-sol_codex resume <session-id> [prompt]` 或 `gpt-6-sol_codex --resume <session-id> [prompt]`
（将 launcher 换成目标模型；也支持 `--resume=<session-id>`）。两种写法都会在其 Codex home 中定位会话，
需要修复时保存私有备份、删除来源模型与目标模型不同的 reasoning 记录，然后以目标模型执行
`codex resume`。对话和工具历史保留；其他模型的推理及摘要在修复后的会话中不可用，但仍在备份里。
若没有待删记录，原会话保持不变，也不会生成备份。
使用前运行 `./scripts/sync-agent-tools.sh` 并打开新 shell。不带 ID 的 `resume`，以及 `--help`、`--last` 等
Codex 原生选项仍直接交给 Codex，因为尚未选定要修复的会话。
`gpt_codex` 是 `gpt-6-sol_codex` 的快捷入口，包括相同的 resume 修复和参数转发。

`gpt-6-astra` 留给重要、低频的任务；`gpt-6-sol` 用于日常消耗量大的任务，`gpt-6-luna` 负责低成本的批量任务。
Astra 和 Sol 默认使用 high reasoning effort，Luna 默认使用 xhigh（extra high）。
`gpt-6-sol` profile 选择 GPT-6.1 Sol；独立 CODEX_HOME 的 `business` 使用同一模型 / high；`sync-codex-agent.sh` 只更新它的
模型和推理等级两个顶层键，保留账号及其他本机设置。

| Profile | 模型 | 网关 | shim 端口 | 网关修复 |
| --- | --- | --- | --- | --- |
| `ds-flash` | `deepseek-flash` | api.deepseek.com | 8788 | 改模型名 + 目录补丁 |
| `glm` | `glm-5.3` | open.bigmodel.cn | 8789 | 改模型名 + 目录补丁 |
| `glm-flash` | `glm-5.3-flash` | open.bigmodel.cn | 8795 | 改模型名 + 目录补丁 |
| `kimi` | `kimi-k3` | api.kimi.com | 8790 | + 目录补丁 |
| `mimo` | `mimo-v2.6-pro` | token-plan-cn.xiaomimimo.com | 8791 | + 目录补丁 + `json_object` 降级 |
| `mimo-fast` | `mimo-v2.6-pro-ultraspeed` | api.xiaomimimo.com | 8794 | + 目录补丁 + `json_object` 降级 |
| `mimo-flash` | `mimo-v2.6-flash` | token-plan-cn.xiaomimimo.com | 8793 | + 目录补丁 + `json_object` 降级 |
| `qwen` | `qwen3.8-max` | dashscope.aliyuncs.com | 8792 | + 目录补丁 + message-id 前缀修正 |
| `local` | `qwen3.8-27b-local` | 用户可配置（默认 127.0.0.1:8080） | 无 | 目录补丁、不走沙箱或 shim |
| `gpt-6-astra` | `gpt-6-astra` | OpenAI（ChatGPT 登录） | 无 | 不走 shim，订阅制 |
| `gpt-6-sol` | `gpt-6.1-sol` | OpenAI（ChatGPT 登录） | 无 | 不走 shim，订阅制 |
| `gpt-6-luna` | `gpt-6-luna` | OpenAI（ChatGPT 登录） | 无 | 不走 shim，订阅制 |

云端凭据来自私有连接 JSON，由 shim 添加；`local` 不需要 key。三个 OpenAI profile 共享 home 的 `auth.json`，`business` 保留 `~/.codex-agent/business/` 下的独立登录。

安装或更新：

```bash
# 安装 profiles、shim 脚本、路由表，并重新生成 model catalog
./scripts/sync-codex-agent.sh

# 可选但推荐：把 shim 交给 launchd 常驻
~/.codex-agent/bin/codex-auto-review-shim-service install
```

把 Agent 环境恢复到另一台 Mac 后，再运行一次 `install`。它会查找目标机器上的 Python 3.11+，重写
launchd plist，并重新加载已有服务。`restart` 只重启现有 plist，不会更新 Python 路径。
从更新后的仓库执行 `./scripts/sync-codex-agent.sh`，部署服务、连接 helper 和默认资源。缺少连接文件时使用不含云端凭据的项目默认值，启动前需初始化并填写云端 key。已有自定义文件保持原样。

仓库模板中的本机路径写作 `@HOME@`，由同步脚本在安装时替换为实际 home（Codex 只接受绝对路径）。

模型卡只承载模型差量（model、`model_provider`、reasoning effort、上下文/compact 窗口、`web_search`、
`model_catalog_json`）。九个第三方网关定义集中在 `codex-agent/model-providers.toml`，同步时作为带标记的块
写入共享 base，使恢复会话时可以解析历史 provider。`glm-flash`、`mimo-fast`、`mimo-flash` 因网关端口不同，
现在各有独立 provider ID。旧会话使用的共用 `glm` 或 `mimo` ID 无法识别其创建时的具体变体；
这两个旧 ID 保留普通 `glm` 和 `mimo` 路由。退役的 provider ID 也要在注册表中保留最后可用的路由；
删除 ID 会让记录该 ID 的历史会话无法恢复。政策（沙箱、审批、env 策略、`service_tier` 等）与 Codex 本体和
ChatGPT 桌面端写入的机器本地状态（`[projects.*]` trust、`[hooks.state]`、`[mcp_servers.*]`、`[plugins.*]`、
`[marketplaces.*]`、`[tui.*]`、`[desktop]` 以及 `notify` 等根键）都留在共享 home 的 base `config.toml` 里。
同步脚本只更新带标记的 provider 块；若相同 ID 已在块外定义，则报错而不覆盖。模型卡是纯产物，
同步时整文件覆盖。要给单个模型改设置，改仓库里那张卡再同步即可
（layering 让卡上的键压过 base）。

`model-catalogs/<id>.json`（全部九个第三方 profile）是**生成型产物，不入仓库**。同步脚本会用 Codex 内置目录
（`codex debug models`，在全新 `CODEX_HOME` 下取）重新生成：修正 guardian 的工具模式，并给各模型补入
模型卡配置的窗口和 direct 工具模式。否则 Codex 会将未知模型限制在 272K 的后备上限。
会话模板按当前 catalog 顺序选择第一个工具能力兼容的 direct 模型，不绑定固定模型 ID；
code-mode 模型和 guardian 不作为模板。若没有兼容模板或 Codex 改了必要的目录结构，生成脚本会 WARNING 且非零退出；同步时先暂存全部模型卡和 catalog，
失败不会替换已安装的模型卡或 catalog。

### 修复跨 provider 恢复时的 reasoning 历史

第三方 Responses 网关可能在 reasoning 记录的 `content` 数组里保存 `reasoning_text`。切换到 OpenAI 官方端点
恢复会话时，可能收到 `Invalid 'input[n].content': array too long`（见 [Codex 上游问题 #36551](https://github.com/openai/codex/issues/36551)）。
先退出所有正在使用该会话的 Codex 窗口，在 `~/.codex/sessions/` 中找到对应的 rollout 文件，再执行：

```bash
python3 scripts/repair-codex-reasoning-history.py /path/to/rollout-<session-id>.jsonl
python3 scripts/repair-codex-reasoning-history.py /path/to/rollout-<session-id>.jsonl --apply
# 若随后出现 invalid_encrypted_content 或 reasoning item ID 不存在：
python3 scripts/repair-codex-reasoning-history.py /path/to/rollout-<session-id>.jsonl --drop-reasoning-model kimi-k3 --drop-reasoning-model mimo-v2.6-pro
python3 scripts/repair-codex-reasoning-history.py /path/to/rollout-<session-id>.jsonl --drop-reasoning-model kimi-k3 --drop-reasoning-model mimo-v2.6-pro --apply
```

第一条命令只统计命中数。`--apply` 只将非空且全为 `reasoning_text` 的 reasoning `content` 改为 `null`，
替换前在原目录保存带时间戳的私有备份。第三方加密推理内容仍可能校验失败，其 item ID 也可能在 OpenAI
端点不存在。此时按来源模型使用 `--drop-reasoning-model`：只删除这些模型的 reasoning 记录，保留对话和工具历史。
被删记录中的内部推理及推理摘要不再出现在修复后的会话中，但仍保留在带时间戳的备份里。
参数要使用 `turn_context` 记录的模型名，而非 profile 别名；没有匹配项时工具会警告。
修复后的 rollout 和备份均收紧为仅所有者可访问（原文件允许所有者写入时为 `0600`）。
再次运行相同修复命令应显示零条命中，然后用目标模型的 profile 恢复会话。
若工具报告不支持的 reasoning 内容或 JSONL 损坏，会保持原文件不变；需单独检查报错行。需要回滚时，
先再次退出会话，再把命令输出的 `rollout-*.jsonl.backup-<timestamp>` 文件复制覆盖原 rollout。
确认恢复后的对话可用前保留备份。

### 切换 sandbox 模式

共享 home 的 base `config.toml` 定义默认沙箱：`"workspace-write"`——写入限制在 workspace，
`[sandbox_workspace_write] network_access = true` 保持网络放开（需要 shim 处于运行状态）。单个模型要例外，
在它的模型卡里写 `sandbox_mode` 覆盖 base——`local` 就是这样拿到 `"danger-full-access"`（无沙箱，
只在终端交互使用，不作为子 Agent 派发）。改卡后重跑 `./scripts/sync-codex-agent.sh`。

`local` 在共享 provider 注册表中直连 `local.codex` 指定的服务（默认 `http://127.0.0.1:8080/v1`）。

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
$tmux-agents 路由 Agents，CodexAgent-GPT-6-Astra 负责 plan / implement / fix，ClaudeAgent-MiMo / ClaudeAgent-DS-Flash 负责两路同时 review / re-review。
每次发送前重新 discovery pane，clear 新任务 session，避免裸 #数字。
严格遵循 AGENTS.md 的约束。
```

Gateflow + `sub-agents` 示例：

```text
按照 $gateflow 开发 <work-unit>。
$sub-agents 通过 runner 子进程派发：Codex gpt-6-astra 负责 plan / implement / fix，Claude mimo / ds-flash 负责两路 review / re-review。
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
$tmux-agents 路由 Agents，ClaudeAgent-MiMo / ClaudeAgent-DS-Flash 负责两路同时 review，CodexAgent-GPT-6-Astra 负责 plan / implement / fix。
总控 Agent 先做 preflight 和 goal confirmation；确认后按 Gateflow 的 Gate Order 逐 gate 派发。
每个 Agent 返回后，总控读取 artifact、裁决 finding、更新 control_doc、收集 residual risk、关闭已解决 risk。
final closeout 后说明用户 merge PR、拉取目标 base branch，并从 control_doc 的 next entry point 继续下一轮。
严格遵循 AGENTS.md 的约束。
```

Phaseflow + `sub-agents` 示例：

```text
按照 $phaseflow 推进，设计真源在 docs/host/design.md，总控文档是 docs/host/issues-implementation-control.md。
$sub-agents 通过 runner 子进程派发，Claude mimo / ds-flash 负责两路 review，Codex gpt-6-astra 负责 plan / implement / fix。
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
  model-providers.toml
  profiles/
    ds-flash/config.toml
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
install.sh
config/
  endpoints.example.json
scripts/
  agent-endpoint.py
  validate-skill.py
  agent-tools.zsh
  claude-agent-run
  codex-agent-run
  compose-codex-app-config.py
  sub-agent-preflight
  sync-codex-providers.py
  patch-codex-model-catalog.py
  repair-codex-reasoning-history.py
  sync-codex-model-defaults.py
  sync-agent-tools.sh
  sync-codex-agent.sh
  validate-skills.sh
  sync-skills.sh
tests/
  test_install_endpoints.py
  test_codex_model_defaults.py
  test_provider_registry.py
  test_repair_codex_reasoning_history.py
```

## 维护流程

只编辑本仓库中的真源文件：

```text
skills/<skill-name>/SKILL.md
skills/<skill-name>/agents/openai.yaml
install.sh
config/endpoints.example.json
scripts/agent-endpoint.py
scripts/validate-skill.py
scripts/agent-tools.zsh
scripts/claude-agent-run
scripts/codex-agent-run
scripts/compose-codex-app-config.py
codex-agent/model-providers.toml
codex-agent/profiles/<agent-id>/config.toml
codex-agent/bin/
codex-agent/shim-routes.json
scripts/patch-codex-model-catalog.py
scripts/repair-codex-reasoning-history.py
scripts/sync-codex-model-defaults.py
scripts/sync-codex-providers.py
tests/test_codex_model_defaults.py
tests/test_provider_registry.py
tests/test_install_endpoints.py
tests/test_repair_codex_reasoning_history.py
```

校验全部 skills：

```bash
./scripts/validate-skills.sh
```

检查 provider 注册同步与桌面端迁移路径：

```bash
python3 -m unittest discover -s tests
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
同步脚本只更新共享 base `config.toml` 中带标记的 provider 块，把模型卡整文件写入共享 home
（`~/.codex/<agent-id>.config.toml`），安装 shim 脚本与路由表，并重新生成不入仓库的 `model-catalogs/`。
这些脚本都不会 push、
publish、create PR，也不会修改远程仓库。

## 说明

- `gateflow` 定义单个 work unit 的 gates。
- `phaseflow` 是项目分步总控；具体 plan / implementation / review / fix 任务交给 Agent 完成。
- `planreview` 和 `deepreview` 是 review skills。它们应该输出 durable artifacts，而不是只在聊天里给结论。
- 只有在通过 tmux 路由多个 CLI Agent 时才需要 `tmux-agents`。
- 总控通过 runner 子进程启动外部子 Agent 时使用 `sub-agents`。
