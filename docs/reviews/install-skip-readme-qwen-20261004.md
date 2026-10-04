# Code Review

RUNTIME/PROVIDER/MODEL: codex/qwen/gpt-5
CANARY=qwen-683160f5
Task label: install-skip-qwen-20261004-01

## Scope

- Mode: current changes (`$deepreview --base 61f19e42b439aa034d4f5738cc916af2b7e5fdd4`)
- Branch or PR: `feat/local-endpoints-installer`（open PR #45, noho/code-is-cheap 的后续 doc-only 增量；本轮未访问 GitHub，PR 号仅作为 controller 提供的上下文记录）
- Base: `61f19e42b439aa034d4f5738cc916af2b7e5fdd4`（同时是本地 HEAD；`git diff <base>...HEAD` 为空，新增内容全部是未提交的 workspace changes）
- Output file: `docs/reviews/install-skip-readme-qwen-20261004.md`（文件名由本轮任务显式指定，覆盖 skill 默认的 `code-review-${ts}.md` 命名；review 时钟时间取自本机 `date`：local `20261004-204936` / UTC `2026-10-04T12:49:36Z`）
- Included scope（仅这两段新增文字）:
  - `README.md:127` — `## Prepare Agent Environment`（`README.md:125`）下新增的英文段落
  - `README.zh.md:123` — `## 准备 Agent 环境`（`README.zh.md:121`）下新增的中文段落
  - 对照真源：`install.sh`、`scripts/sync-agent-tools.sh`、`scripts/sync-codex-agent.sh`，以及两份 README 中与该段落直接相关的既有小节（Install / Local API keys / Prerequisites / Codex Agent Profiles / Maintenance）
- Excluded scope:
  - PR #45 既有实现（installer、endpoint 解析、provider registry、sync 脚本本体）不做广泛审计；本轮只把它们当作段落声明的对照证据来读
  - 未读取另一 reviewer 的报告、任何凭据、live 配置、会话或已安装二进制（任务禁止）
  - 未执行 `install.sh`、任何 sync 脚本、测试或网络/API 探测；**本文不包含任何 runtime 安装结论**，所有判断均来自静态源码阅读
- Parallel review coverage: 无。按任务要求未派发 sub-agent，全部证据由主 reviewer 直接读取。

### 身份与哈希校验（写入前）

| 项目 | 期望值 | 实测值 | 结果 |
| --- | --- | --- | --- |
| `git rev-parse HEAD` | `61f19e42b439aa034d4f5738cc916af2b7e5fdd4` | `61f19e42b439aa034d4f5738cc916af2b7e5fdd4` | 一致 |
| `git branch --show-current` | `feat/local-endpoints-installer` | `feat/local-endpoints-installer` | 一致 |
| `git status --short` | 仅两份 README 被修改 | ` M README.md` / ` M README.zh.md` | 一致 |
| `shasum -a 256 README.md` | `184c4122…b2b8be` | `184c412263f9245d4621e7f2ebc13b11176e7753904141648fd3083566b2b8be` | 一致 |
| `shasum -a 256 README.zh.md` | `291c395c…d0e2f` | `291c395c07a1f68cb2c582e6cf8d2124a6825294dbf01d5bb00b5272552d0e2f` | 一致 |
| `shasum -a 256 install.sh` | `9305fa6e…6a96f94` | `9305fa6e4a6df3aa5c22325831bb3a38f10b494936cf79df95da97c336a96f94` | 一致 |
| workspace diff vs 冻结 diff | 逐字节相同 | `git diff -- README.md README.zh.md` 与 `/private/tmp/code-is-cheap-readme-install-skip/diff.patch` 同为 `4fc2313efadb0219010066a714415882ef350269fa3770dca30c931102ef8c73`，`diff` 无输出 | 一致 |

期望哈希取自 `/private/tmp/code-is-cheap-readme-install-skip/manifest.json`。写入后复核见文末「身份与哈希校验（写入后）」。

### 段落声明逐条对照 install.sh

| 段落声明 | 直接证据 | 判定 |
| --- | --- | --- |
| 「已部署 launcher/runner」 | `install.sh:71` 调 `scripts/sync-agent-tools.sh`；该脚本 `:10` 装 `~/.config/zsh/agent-tools.zsh`(600)，`:11-16` 装 `claude-agent-run`/`codex-agent-run`/`sub-agent-preflight`/`compose-codex-app-config.py`/`repair-codex-reasoning-history.py`/`agent-endpoint.py`(755)，`:17-18` 装默认 URL 资源 | 成立 |
| 「已部署模型卡」 | `install.sh:72` 调 `scripts/sync-codex-agent.sh`；`:47-58` 暂存 `codex-agent/profiles/*/config.toml` 并替换 `@HOME@`，`:62-73` 生成并安装 catalog，`:74-81` 整文件写入 `~/.codex/<profile>.config.toml`。`codex-agent/profiles/` 实测 12 个目录（ds-flash、glm、glm-flash、gpt-6-astra、gpt-6-luna、gpt-6-sol、kimi、local、mimo、mimo-fast、mimo-flash、qwen），正好覆盖 `README.md:171` 的 Codex profile 列表去掉 `business`；`hy` 按 `README.md:175-176` 是 Claude-only，不需要卡 | 成立 |
| 「已配置 shell 加载入口」 | `install.sh:75-84` 向 `~/.zshrc` 追加 `# code-is-cheap launchers` 块，`:82` 导出 `PATH="$HOME/.local/bin:$PATH"`（对应 `README.md:138` 前置要求），`:83` 写入的 source 行与手动步骤 `README.md:157` 逐字相同 | 成立 |
| 上述部署是无条件的（因此「成功即已部署」成立） | `install.sh:3` `set -euo pipefail`、`:6` `die` 使任何失败都以非零退出；`:70-72`、`:75-84` 不带条件；唯一开关是 `:7`/`:9` 的 `--no-service`，只影响 `:85-87` 的 launchd shim 服务 | 成立 |
| 「仍需填写 API key」——安装器不提供凭据 | `install.sh:51-67` 以 `O_CREAT\|O_EXCL`(`:62`) 仅在缺失时创建用户文件；`:58` 写入的 key 文件内容是注释占位（`# Provider keys; this file is never synchronized.` / `# export DEEPSEEK_API_KEY="your-key"`），不含任何真实凭据；`:88` 仍提示 `Set provider keys in ~/.config/zsh/agent-tools.local.zsh.`；`README.md:110-117`、`README.md:139-140` 同义 | 成立 |
| 「仍需填写自定义 URL」 | `install.sh:57` 只把 `config/endpoints.example.json` 原样种入 `~/.config/agent-tools/endpoints.json`（同样 exclusive-create），`:89` 提示自行定制；`README.md:117` 说明本地值优先且 sync 永不补写 | 成立 |
| 「然后 `source ~/.zshrc`（或打开新 shell）」 | `install.sh:90` `Run: source ~/.zshrc; …`；安装器无法影响父 shell，本小节唯一无法被安装器代劳的部署步骤正是 `README.md:160-164`，段落正确保留了它 | 成立（但见 Finding 1：同句被截断） |
| 「`business` 需自行准备账号 home」 | `install.sh` 全文无 `~/.codex-agent/business` 创建动作；`scripts/sync-codex-agent.sh:20-21` 说明 business 使用独立 CODEX_HOME 且只同步 model 差量，`:108-115` 仅在 `business/config.toml` 已存在时才写，缺失时 `:114` 打印 `note: business config not found; skipped model defaults`；`README.md:104` 明示安装器不创建该 home、不登录；`README.md:141`、`README.md:263` 同义 | 成立 |
| 「本地模型需自行准备本地服务」 | `install.sh` 无启动本地模型服务的动作（`README.md:104` 明示 "or start a local model server"）；`local` 的模型卡确实由 `:72` 部署（profiles 目录含 `local`），但服务本体不在其中；`README.md:142` / `README.zh.md:137` 说明 `local` 服务地址默认 `http://127.0.0.1:8080` 并走 `/health` 健康检查 | 成立（卡与服务被正确区分） |
| 前置要求不会因跳过而失效 | `install.sh:17` macOS 硬门禁、`:19-21` 逐个 `command -v` 检查 git/codex/claude/python3/jq/uv/tmux/rsync/zsh/curl、`:22` Python 3.11+、`:68` `agent-endpoint.py --check`，与 `README.md:136-137` 前置项一一对应；`:82` 满足 `README.md:138`；`sync-agent-tools.sh:16` 满足「`agent-endpoint.py` 必须在 PATH 上」。即「成功」蕴含前置项在安装时已满足，而段落把安装器唯一不满足的两项（凭据、本地服务）显式保留 | 成立 |
| 中英双语一致 | `README.md:127` 与 `README.zh.md:123` 句数、语义、代码引用逐句对应（skip 判断 / 已部署三项 / 仍需 key+URL+shell reload / business+本地服务例外 / 下面步骤用于手动安装或后续更新），且都位于各自小节首段 | 成立（两版共享同一处遗漏，见 Finding 1） |

### Agent-facing 检查（任务显式要求）

- **A1 是否会导致重复安装**：不会。段落把跳过条件绑定在「`install.sh` 已成功」这一可观测事实（`install.sh:3`/`:6` 使失败必然非零退出，`:88-90` 是成功输出），并要求跳过本小节的手动部署命令（`README.md:148-152` 的 `sync-agent-tools.sh`、`README.md:154-158` 的 zshrc 追加、`README.md:160-164` 的 shell reload 中前两项已被 `install.sh:71`/`:75-84` 覆盖）。末句「下面的步骤用于手动安装或后续更新」保留了手动路径，不诱导再次运行安装器。
- **A2 是否暗示安装器提供凭据**：不暗示。段落用「仍需…填写 API key 和可选的自定义 URL」明确把凭据/URL 归回用户，与 `install.sh:58` 的注释占位、`:88-89` 的收尾提示一致。
- **A3 是否暗示安装器提供可选服务**：不暗示。段落明确 `business` 账号 home 与本地模型服务需另行准备，与 `install.sh` 无相关动作、`sync-codex-agent.sh:113-114` 的缺失跳过提示一致。唯一需要 controller 注意的是段落对「launchd shim 服务」保持沉默：默认安装会装它（`install.sh:85-87`），`--no-service` 则不装，而该服务的手动步骤写在本小节之外（`README.md:265-273`）。见 Open Questions 2 与 Residual Risk。
- **A4 跳过是否安全（反向检查）**：安全。本小节中安装器无法代劳的只有 `source ~/.zshrc`，段落保留了它；其余步骤均由 `install.sh:71-72`、`:75-84` 实际执行。段落也没有让读者跳过编辑真源后的重新同步：同一小节 `README.md:129-131`（zh `:125-126`）与 `README.md:591-655` 的 Maintenance 流程仍然要求「改仓库真源并重跑 sync」，末句的「后续更新」也覆盖该路径。

## Findings

### 1-未修复-低-新段落漏掉「重新打开 Agent 会话以加载 skills」这项仍需执行的义务（中英同缺）

- **入口/函数**: 文档入口 —— `## Prepare Agent Environment` / `## 准备 Agent 环境` 的新增首段；读者与 Agent 据此判断「安装器成功后还剩什么必须做」
- **文件(行号)**: `README.md:127`；`README.zh.md:123`
- **输入场景**: 在一个已经运行的 Codex / Claude 会话内成功执行 `install.sh`（即原地更新既有安装，而不是全新机器首装），随后只读本段决定后续动作
- **实际分支**: 段落列出的剩余义务只有三项：填 API key、填可选自定义 URL、`source ~/.zshrc`（或打开新 shell）；完全没有提到需要重新打开 Agent 会话才能加载新同步的 skills
- **预期行为**: 与本仓库既有真源保持一致 —— shell reload 与 skills reload 是两件不同的事，必须同时说明。`install.sh:90` 的收尾输出把两者写在同一句：`Run: source ~/.zshrc; open new Agent sessions to reload skills.`；`README.md:106` 写作 "Reopen Agent sessions to reload skills, and run `source ~/.zshrc` to load launchers in the current shell."；`README.zh.md:102` 同义
- **实际行为**: 段落只保留 `install.sh:90` 的前半句，并把「打开新 shell」呈现为 `source ~/.zshrc` 的等价替代。对新 shell 而言这只解决 launcher 加载；已在运行的 Agent 会话仍然持有旧 skills —— `install.sh:69-70` 通过 `sync-skills.sh` 把 skills 写入 `~/.codex/skills` 与 `~/.claude/skills`，而运行中的会话不会自动重读。失败是静默的：没有任何报错提示环境未完全刷新
- **直接证据**: `install.sh:90`（成功输出把 source 与会话重载并列）；`install.sh:69-70`（skills 同步的实际来源）；`README.md:106` 与 `README.zh.md:102`（既有文档已明确区分两件事）；对照 `README.md:127` 与 `README.zh.md:123` 的「仍需…」句只含 key / URL / `source ~/.zshrc`（或打开新 shell）
- **影响**: 静默失效（局部）。原地更新后 Agent 继续使用旧版 skill 定义，行为与仓库真源不一致且无告警；不产生错误状态、数据损坏或不可恢复后果。属于本轮变更的核心风险面：该段落的全部作用就是给出「可以跳过什么、仍须做什么」的清单，清单不完整即偏离意图
- **建议改法和验证点**: 在两版「仍需」句末补回会话重载，例如 EN 追加 `, and reopen Agent sessions to reload skills`，zh 追加 `，并重新打开 Agent 会话以加载 skills`；如需保留「或打开新 shell」，应把它明确限定为 launcher 加载的替代而非会话重载的替代。验证点：改后段落与 `install.sh:88-90` 的三行收尾输出逐项对应，与 `README.md:104-106` / `README.zh.md:100-102` 不再互相矛盾，且中英两版句数与语义仍保持一致
- **修复风险（低/中/高）**: 低。纯文档追加，不改变 skip 判断、凭据归属或可选服务归属的任何表述
- **严重程度（低/中/高/严重）**: 低

## Open Questions

1. 段落以「`install.sh` 已成功」作为跳过闸门，但没有给出 Agent 可核验的成功信号。是否需要在段落中点名可观测判据（退出码 0，或 `install.sh:88-90` 的三行 `Installed. …` 输出）？现状下判据在 `install.sh:3`/`:6`/`:88-90` 中是明确的，因此这只是精度问题，不构成 defect。
2. 「下面的手动部署步骤 / the manual deployment steps below」是否有意只限定在本小节内？按文档顺序，`README.md:265-273`（zh 对应小节）的 `sync-codex-agent.sh` 与 launchd shim 服务安装也位于「下面」。对默认安装而言两者都已被 `install.sh:72`/`:85-87` 覆盖，跳过是正确的；但对显式选择 `--no-service` 的用户，「成功」同样成立而 shim 服务并未安装，其手动步骤只存在于本小节之外。请 controller 确认是否需要把范围写明（例如「本小节以下的手动部署步骤」）。

## Residual Risk

- 纯文档变更，且仓库内没有任何测试断言 README 与安装器行为一致：`grep -rn "README" tests/*.py` 无命中。因此 Finding 1 与上述 Open Questions 只能靠人工评审拦截，未来 `install.sh` 行为变化时这两段文字不会被任何自动检查提醒。
- 安装器行为的散文描述现在存在于三处（`install.sh:88-90` 的收尾输出、Install 小节 `README.md:104-106` / `README.zh.md:100-102`、本次新增的 Prepare 小节段落），且各有中英两份，构成后续漂移面。本轮未发现三处之间存在事实冲突（除 Finding 1 的遗漏外）。
- 本轮所有结论均来自静态阅读，未执行安装器、sync 脚本或测试，未做网络/API 探测，因此**不对任何真实安装结果作出断言**；「安装器会部署 X」类判定一律以脚本源码行为证据。
- 按任务边界未读取另一 reviewer 报告、凭据、live 配置、会话与已安装二进制；PR #45 既有实现未做广泛审计，若其中存在与本次段落相关的未审问题，本轮无法发现。
- 为核验「模型卡已部署」这一句，除允许清单中的文件外还做了一次只读目录列举 `ls codex-agent/profiles/`（12 个 profile 目录，无 `business`）。该操作只读取仓库结构、未读取文件内容，特此披露以便 controller 判断是否越界。
- `install.sh:79-80` 的 `# code-is-cheap launchers` marker 只在缺失时追加 zshrc 块：若用户此前手工加过同样的 source 行（无 marker），成功后 zshrc 会出现重复加载块。这属于既有安装器实现（PR #45 已审范围），且不影响本段任何声明的正确性，故不作为本轮 finding，仅记录为已知边界。

### 身份与哈希校验（写入后）

写入本文件后重新执行同一组身份/哈希检查（本机时钟 `20261004-205905`），结果与写入前完全一致，说明本轮评审没有触碰被审对象：

| 项目 | 实测值（写入后） | 结果 |
| --- | --- | --- |
| `git rev-parse HEAD` | `61f19e42b439aa034d4f5738cc916af2b7e5fdd4` | 与冻结 base 一致 |
| `git branch --show-current` | `feat/local-endpoints-installer` | 一致 |
| `shasum -a 256 README.md` | `184c412263f9245d4621e7f2ebc13b11176e7753904141648fd3083566b2b8be` | 与 manifest 一致，未被修改 |
| `shasum -a 256 README.zh.md` | `291c395c07a1f68cb2c582e6cf8d2124a6825294dbf01d5bb00b5272552d0e2f` | 与 manifest 一致，未被修改 |
| `shasum -a 256 install.sh` | `9305fa6e4a6df3aa5c22325831bb3a38f10b494936cf79df95da97c336a96f94` | 与 manifest 一致，未被修改 |
| workspace diff vs 冻结 diff | `/tmp/ws2.diff` 与 `/private/tmp/code-is-cheap-readme-install-skip/diff.patch` 同为 `4fc2313efadb0219010066a714415882ef350269fa3770dca30c931102ef8c73`，`diff` 无输出 | 一致 |
| `git status --short` | ` M README.md`、` M README.zh.md`、`?? docs/reviews/install-skip-readme-qwen-20261004.md`、`?? docs/reviews/install-skip-readme-mimo-20261004.md` | 唯一由本轮产生的写入是本 artifact |

补充披露：`docs/reviews/install-skip-readme-mimo-20261004.md` 在本轮执行期间出现（写入前的 `git status` 中尚不存在），是并行评审路径的产物。按任务边界**未读取该文件**，本文结论不依赖其内容。本轮未做任何 stage / commit / push / PR / 评论 / merge 操作，未修改源码或测试，未推进任何 gate 状态。
