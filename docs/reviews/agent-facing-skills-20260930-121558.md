RUNTIME/PROVIDER/MODEL: codex/gpt-6-astra/gpt-6-astra
CANARY=gpt-6-astra-0fe055db

# 六份技能入口 Agent-facing 独立审查

## 身份、版本与结论

- 审查日期：2026-09-30T12:25:08+08:00。
- Runtime 是本次 Codex CLI 子任务；provider 名来自明确派发协议。模型名按本次指定 profile 与读取到的本机模型卡 `model = "gpt-6-astra"` 报告。当前 JSONL 的 `thread.started` / `turn.started` 没有 model 字段，因此未取得独立服务端模型身份证明；不把模型自报当作该证明。
- 本次 thread：`01a0f087-945f-70d2-8915-4dce596aa125`；其 JSONL thread ID 与环境 `CODEX_THREAD_ID` 一致。CANARY 来自工具实际读取，不是 prompt 推断。
- 仓库：`/Users/leo/workspace/code-is-cheap`。
- 实际分支：`codex/sub-agents-result-validation`；实际 HEAD：`d65a4ae741ef89d278f5bb6195b763d6bf75c6b5`。
- 开始和写报告前 `git status --short` 均为空。六份 SKILL 及三个 runner/preflight 文件逐字节等于当前 HEAD；文末记录 SHA-256。
- PR 42 未 merge 是派发背景；本次未查询 GitHub，不作为独立确认的当前远端状态。
- 六份 SKILL 均完整阅读。发现 **2 项高、6 项中** 的实质性问题；Planreview 未发现实质性问题。这里的严重度表示在所列触发场景下的风险，不表示本次已经发生错误派发或代码修改。
- 本次是指定六文件及直接依赖审查，不是全仓 `deepreview --all`，没有执行 Gateflow、Phaseflow 或技能中的派发/发布动作；唯一新增文件是本报告。

Agent-facing 判据：新 Agent 只能使用自己的系统/开发者指令、当前派发 prompt、明确加载的技能和可定位的文件；目录相同不意味着继承总控对话、裁决、授权或 accepted artifacts。文本契约缺口、脚本实现事实和具体派发者责任分别列出。

## Findings 索引（严重度顺序）

| ID | 严重度 | 所属技能 | 问题 |
| --- | --- | --- | --- |
| S1 | 高 | sub-agents | 未建立独立上下文交接契约，预检通过也不证明任务信息完整 |
| P1 | 高 | phaseflow | implementation / review 派发清单没有绑定上一 gate 的实际输入 artifact |
| G1 | 中 | gateflow | 通用 review pass 条件只要求 finding 有状态，未要求阻塞项已收敛 |
| T1 | 中 | tmux-agents | `tmux-cli status` 在 tmux 外有创建 session 的副作用，入口未声明环境前提 |
| P2 | 中 | phaseflow | Agent 自报返回即可退出 in-flight，与 runner 终态规则冲突 |
| S2 | 中 | sub-agents | `--prompt-file` 路径没有注入或校验本轮 CANARY 读取协议 |
| S3 | 中 | sub-agents | 手工预检使用过时的 Codex profile 路径 |
| D1 | 中 | deepreview | PR 模式没有绑定不可变 head/base 身份及深挖代码版本 |

## 逐份覆盖与 findings

### 1. skills/gateflow/SKILL.md（1–340，完整）

首次调用能识别单 work unit、可选 design_doc/base_ref、preflight、目标确认、gate 顺序、输出和发布授权边界。直接交叉阅读 Planreview、Deepreview 与 Phaseflow；它本身不直接调用专属执行脚本。

#### G1 — 中：review loop 的机械通过条件不足以阻止未修复 accepted finding 进入 checkpoint

- **位置**：`skills/gateflow/SKILL.md:224–237`、`269–278`；对照 `282–287`、`310–316`。
- **触发场景**：新总控只得到 plan review artifact 与当前技能；某 accepted finding 的 re-review 状态为“部分修复”，尚有已确认的必要修复，但没有新的 open question，风险已分类。当前 gate 是 accepted plan commit 或 accepted slice commit。
- **实际规则**：状态枚举明确包含“未修复/部分修复”；通用通过条件要求 accepted findings “都有 fix/re-review 状态”、最终状态列出、无 blocking open question、risk 已分类，没有要求阻塞 finding 已修复或明确裁决为非阻塞。`269` 在 loop 通过后自动 commit。后面的 aggregate/PR entry criteria 才明确要求 accepted findings 已修复或 required fixes 已通过，不能倒替前面 plan/slice 的放行条件。
- **影响**：新 Agent 若按列出的充分条件判定，会先接受不完整计划或 slice；若凭工程常识拒绝，则必须自行补出未写明的 gate 判据。问题是 pass contract 欠规格，不是声称所有 Agent 一定误放行。
- **技能文本应修**：在通用通过条件中增加“所有本 gate 的 blocking accepted findings 已修复且 re-review 验证；未修复、部分修复、证据失效不得仅凭有状态放行”。允许延期时必须引用既有授权下的非阻塞裁决、owner/destination；scope 或验收改变仍按目标重新确认规则。
- **派发者必须提供**：本 gate 的 finding 裁决、哪些是阻塞项、修复证据和允许延期的具体决定。通用技能不应硬编码项目 severity 阈值。
- **验证点/修复风险**：用“accepted + 部分修复 + 已分类 risk + 无 open question”反例，确认仍留在 fix/re-review；文本修复风险低。

### 2. skills/tmux-agents/SKILL.md（1–90，完整）

已核对 pane discovery/full ID、CLI 类型、clear 边界、send/wait/capture 和 completion 规则；进一步读取实际安装的 tmux-cli 入口与对应方法，未向任何 pane 发送消息。技能只负责通信，不分配角色；缺少项目任务内容本身属于调用者责任。

#### T1 — 中：在 tmux 外，所谓 socket 预检会先创建额外 session

- **位置**：`skills/tmux-agents/SKILL.md:14`、`34–46`、`64–69`。
- **直接执行证据**：实际 PATH 的 tmux-cli 入口导入 `claude_code_tools.tmux_cli_controller.main`。该模块 `695–712` 根据 `TMUX` 是否存在选择 controller；在 tmux 外构造 `RemoteTmuxController(session_name="remote-cli-session")`。`tmux_remote_controller.py:20–27,40–50` 在构造时执行 `_ensure_session()`，不存在就调用 `new-session -d`；`tmux_cli_controller.py:714–720` 的 status 本身仅报告 remote 模式，并非返回所有 pane 的只读 socket 检查。
- **触发场景**：Codex 桌面/独立 exec 环境中无 `TMUX`，用户只授权对已经运行的 Agent 做 discovery。新 Agent 按技能首先运行 `tmux-cli status`。
- **影响**：尚未识别目标 pane 就尝试创建新 shell session；新 Agent 无法从技能获知这项副作用，也不能仅凭 status “能返回”判断 socket 工作。后续 `tmux list-panes -a` 不会撤销已发生的创建。
- **验证**：把已读取的 `RemoteTmuxController.__init__`、`_ensure_session` 原 AST 在内存执行，用假 `_run_tmux` 记录调用；缺少 session 时得到 `has-session` 后接 `new-session -d -s remote-cli-session`。没有启动实际 tmux 或修改其状态。
- **技能文本应修**：明确 local/remote 模式前提和远程构造副作用；只读 discovery 先用原生 `tmux list-panes -a` 检查目标/socket。对于要求使用既有 pane 的路径，给出经验证的不会隐式创建 session 的调用方式，或明确环境不满足时停止；不能把猜设 `TMUX` 当作修复。
- **派发者必须提供**：目标 Agent/pane 的角色分配，以及是否允许新建 session；无须传完整历史。
- **限定/修复风险**：这是本机所安装依赖的可确认行为，不声称所有 tmux-cli 版本相同；建议记录依赖版本。修复风险低至中，需要验证两种模式。

### 3. skills/phaseflow/SKILL.md（1–339，完整）

design_doc/control_doc 真源、preflight、目标确认、逐 gate 派发、默认 sub-agents 路由、禁止静默回退、裁决和状态回写均有明确文本。已完整交叉阅读 Gateflow 及两个派发技能。

#### P1 — 高：派发清单没有要求传入本 gate 消费的 accepted plan / reviewed target

- **位置**：`skills/phaseflow/SKILL.md:100–113`、`211–224`；对照 `168`、`275–277`，及 `skills/gateflow/SKILL.md:196–213`。
- **触发场景**：plan 已在另一个 Agent 中完成、review 并提交；总控给新 implementation Agent 写了 work unit、design_doc、目标、allowed files、输出路径、验证和 stop condition，逐项满足清单。仓库有两个 plan 草稿，最终 accepted plan 只由 control_doc 中的路径/commit 标识。
- **缺口**：两份派发清单均未明确要求 accepted plan 路径/版本、当前 slice ID 及其完整约束、已完成 prerequisite 的证据；甚至没有要求给子 Agent control_doc 路径。对于 plan review，也没有把 target plan artifact 列成必传项；fix/re-review 仅列 accepted findings，未要求来源 review/修复输入身份。总控记录 plan artifact 并不等于子 Agent 已收到它。
- **影响**：新 implementation Agent 可能重新设计、选错草稿或做 future-slice work，违反 Gateflow “只能做当前 approved slice”；保守的 plan reviewer 会按 Planreview 规则回问 target，造成可避免的 gate 阻塞。仅传 design_doc 不能替代 accepted implementation plan。
- **技能文本应修**：增加按 gate 区分的输入依赖表：plan review→target plan；implementation→accepted plan、slice ID/节、批准版本、prerequisite evidence；code review→冻结代码范围；fix/re-review→裁决 artifact、finding IDs、待修/已修版本；PR review→repo/PR/head/base。每项包含可定位路径/标识；子 Agent 校验缺失或版本不符则停止。
- **派发者必须提供**：具体路径、slice、版本及相关决定摘要。不要把项目 plan 内容固化进 Phaseflow，也不要求传无关 gate 的全部材料。
- **验证点/修复风险**：在两个 plan 草稿并存、子上下文清空的场景下，仅凭 handoff 应能唯一确定已批准 slice。修复风险低。

#### P2 — 中：自报完成/blocked 就算 gate 返回，与 sub-agents 生命周期判据冲突

- **位置**：`skills/phaseflow/SKILL.md:133–149`、`226`、`240–246`；对照 `skills/sub-agents/SKILL.md:118–122,139–144,242–245`。
- **触发场景**：默认 runner 路由中 Agent 最终文字已进入 JSONL，或报告 blocked，但外层托管 session 尚未返回退出码，runner 还在收尾/保存 last-message。
- **直接证据**：Phaseflow `137–143` 使用“以下情况之一”把明确自报完成、artifact+自报、blocked 报告与进程结束并列为 gate 返回证据。Sub-agents 则明确规定 blocked 不等于进程已退出，任一仍在途不得最终验收。`scripts/codex-agent-run:438–460` 在子程序返回后仍需保存 last-message，且保存失败可以把最终退出码改为非零。
- **影响**：新总控得到两套不等价的返回定义；按 Phaseflow 的 OR 条件推进可能提前更新 gate、启动下一任务，或遗漏 runner 收尾失败。
- **技能文本应修**：分开 task-reported status、process lifecycle、result acceptance。runner 路由以 sub-agents 终态+验收为准；自报完成/blocked 只作候选任务状态。tmux 长驻 CLI 则按 pane completion 协议判定，不要求 CLI 进程退出。
- **派发者必须提供**：本次协议类型、调用句柄、输出路径及实际终态证据，不需要把进程终态语义交给每个项目决定。
- **验证点/修复风险**：先出现 final message、后出现非零 runner 退出，不能推进；blocked 但句柄存活不能覆盖原任务。修复风险低。

### 4. skills/sub-agents/SKILL.md（1–282，完整）

完整读取 `scripts/sub-agent-preflight`（1–268）、`scripts/codex-agent-run`（1–460）、`scripts/claude-agent-run`（1–382），并追踪 launcher 中的 profile/cwd/prompt/参数消费链。Result Validation 已明确区分任务结论与派发生命周期、工具非零退出的影响裁决、CANARY 和总控独立复核；这些是有效防线，但不能自动补齐任务输入。

#### S1 — 高：没有明确独立上下文边界，且把有限结构预检描述为全部检查

- **位置**：`skills/sub-agents/SKILL.md:17–18,24–25,41–59,64–66`；执行证据 `scripts/sub-agent-preflight:190–215,232–237`，`scripts/codex-agent-run:330–342,359,412–435`，`scripts/claude-agent-run:304–316,338,360–381`。
- **触发场景**：父上下文中已裁决仅修某个 slice、禁止改公共契约、审查必须用某份冻结 diff；新子任务正文写“按已确认方案修复当前 slice”，并附 allowed paths、artifact 路径及三个小节。父 Agent 误以为同 cwd 或 auto 权限把这些决定带过去。
- **实际执行**：Codex runner 读取 `prompt_text`，`cd` 后把该文本送给新的 `codex exec`；Claude runner 同样 `cd` 后把该文本作为 print prompt。二者没有收集父对话/裁决/用户授权的参数或逻辑。项目指令可能由运行时另行加载，但不能据此推定父会话语义已传递。
- **文本缺口**：Dispatch Contract 已要求目标、路径、权限、输出与 validation；却未明确要求列出任务需要的既有决定/用户授权、冻结输入身份、依赖和成功信号，也未声明“子 Agent 不继承父对话；缺项不得猜”。`64` 的“权限默认继承 auto”没有区分工具策略与用户任务授权。
- **机器校验范围**：预检只用三个行首 regex 找节名，不解析正文或其它合同项。拼接器只补 runtime/provider/model、CANARY、完成后停止/不再派发；未注入项目背景、label 或授权。脚本 `207` 已承认“内容质量仍由总控负责”，而技能 `24` 写“它执行全部检查”，容易使首次调用者过度依赖 setup_status。
- **反例验证**：对脚本原样 regex 用 `grep -qiE` 检查 `目标\n非目标\n停止条件\n` 及“按刚才确认的方案”样例，三个退出码均为 `[0,0,0]`。这是**小节校验通过**，不是声称完整 preflight 或派发已执行/通过。
- **影响**：新 Agent 或停下来反问不可见背景，或自行猜测 accepted 输入和权限并产出偏离任务的结果。事后验收可发现一部分问题，但不能使派发时任务变得自包含。
- **技能文本应修**：明确独立上下文模型；要求本任务需要的 context capsule，缺失项必须说明“不适用”或阻塞，不依赖“刚才/照旧/已确认”等无可定位引用。将“全部检查”改为“机械 setup/结构检查；总控仍须逐项确认 Dispatch Contract、语义完整性和并发写边界”。不要求用 regex 判定任意自然语言授权是否真实。
- **脚本最小方向**：可校验非空必填节、标识/路径字段存在，并明确输出哪些项未做语义验证；若有结构化 handoff schema 可进一步验证。脚本不能推导用户决定，也不应读取和传输完整父历史。
- **派发者必须提供**：本任务适用的目标/非目标/成功信号、范围和冻结身份、约束来源、相关决定及授权边界、输入依赖、可读写路径、工具/副作用、输出和停止规则。详见下方专项表。
- **修复风险**：低至中；必须保持普通小任务可用，允许明确 N/A，避免把所有项目决定硬编码到通用技能。

#### S2 — 中：预先提供完整 prompt 时，本轮 CANARY 不会传给子 Agent

- **位置**：`skills/sub-agents/SKILL.md:41–43,153–159`；`scripts/sub-agent-preflight:154–175,190–215,232–236,263`。
- **触发场景**：调用者使用被技能支持的 `--prompt-file complete.md`；文件有三个节、runtime 声明和完整任务内容，但未含本轮尚未生成的随机 run_dir/canary 路径，或仍指向上一轮 canary。
- **实际分支**：预检先生成本轮随机 run_dir/token；provided 分支只把 `prompt_used` 指向原文件。只有 `prompt_used` 为空的 task 分支才追加本轮 canary 读取要求。随后只检查新 token 不在 prompt 和三个节名；未检查正确 canary 路径/读取要求。输出命令继续指向未修改的文件，收尾说明却要求比对新 `canary.expected`。
- **影响**：在其它 setup 项通过的条件下，会得到可派发命令，但新 Agent 无法从给定 prompt 知道本轮 canary；验证类结果最终必须拒收。照抄上一轮完整 prompt 也不能解决。
- **技能/脚本应修**：最小方案是把 `--prompt-file` 同样复制到本轮 run_dir 并追加本轮固定报告协议；或者提供显式可绑定的 run_dir/canary 输入并校验一致。若保留 verbatim，必须明确调用者如何在派发前补入本轮路径并重新验证，不能称现状“完整命令可直接执行”。
- **派发者必须提供**：任务内容和允许读取 CANARY 文件的权限；不需要提前猜 token 或随机目录。
- **验证点/修复风险**：provided 模式生成的最终 prompt 必须含本轮 canary 路径，不含 token，且 stale canary 路径不能被误作本轮证明。风险低。

#### S3 — 中：手工 fallback 预检要求不存在的旧 profile 布局

- **位置**：`skills/sub-agents/SKILL.md:34–40`。
- **直接证据**：手工清单要求 `~/.codex-agent/<provider>/config.toml`；实际 `scripts/sub-agent-preflight:137–144` 和 `scripts/agent-tools.zsh:245–250,319–337,514–531` 对 business 以外 provider 使用 `~/.codex/<provider>.config.toml`、共享 home 和 `-p`。README `136` 也与当前脚本一致。
- **触发场景**：预检脚本不可用，Codex provider 是 gpt-6-astra/kimi 等非 business，新 Agent 按允许的手工路径逐项检查正常部署环境。
- **影响**：把正常部署判作 setup failure；或者旧目录恰好残留时检查到并非 runner 将消费的配置，错误认为部署已验证。
- **技能文本应修**：business 与非 business 分支使用与 runner 相同的真源路径，最好明确引用当前 launcher 的解析规则而不是复制过时布局。
- **派发者必须提供**：所选 provider/运行环境，不应要求调用者记住迁移历史。
- **验证点/修复风险**：同一安装布局下手工与机器预检应读同一 profile；风险低。

### 5. skills/planreview/SKILL.md（1–198，完整）

**未发现实质性问题。**

- 有明确适用对象；target plan 不清时询问（40–41），不要求 Agent 凭空猜计划。
- 对 Gateflow/Phaseflow 明确要求 Goal Confirmation 或等价 handoff；缺失要记录 open question/finding（76–78）。
- 直接证据、反例与未证实问题分层清楚，提供 finding 格式、artifact 位置和结论枚举（114–193）；只审查，不擅自修 plan/提交/外发（195–198）。
- 与 Gateflow 的“最小设计/goal drift/切片”要求一致；没有必须追踪的专属 runner。
- 可选改进：给 artifact 加 target plan hash/revision 与证据缺失对 `pass` 的影响说明，便于交接复查；现有 scope、evidence 和 open-question 规则已允许诚实报告，未据此另立 defect。具体 plan、目标确认和 design_doc 应由调用者提供。

### 6. skills/deepreview/SKILL.md（1–400，完整）

模式、base 默认、指令冲突处理、真实调用链、证据规则、全仓逐文件覆盖、输出格式和只审查权限边界均有规定。读完 Current/PR/All 三种模式的直接命令协议；本次没有借审查技能之名对 PR 发起动作。

#### D1 — 中：PR review 的本地深挖版本没有与 PR diff 固定绑定

- **位置**：`skills/deepreview/SKILL.md:125–126,276–302,358–366`。
- **触发场景**：Agent 在本地 feature-A 上收到 `--pr 42`，该 PR 是 feature-B；它按示例拿到远端 diff，随后按 Review Method 打开 cwd 下同名实现/测试追调用链。或者审查期间 PR head 被更新。
- **直接证据**：PR facts 只列 repo、number、branch 名等；示例 `gh pr view` 未取 headRefOid/baseRefOid，`gh pr diff` 未记录固定输入身份。没有要求验证本地代码是否等于 PR head、在只读快照中打开该版本、或在结束时检查 PR 已否移动。branch 名是可变引用，不能独立证明代码身份。
- **影响**：新 Agent 可能把旧本地依赖与新 PR diff 拼成不成立的证据链，或把一个版本的结论用于另一个 head。技能“沿真实路径”要求本身不能决定应沿哪个版本读取。
- **技能文本应修**：PR 入口记录 repository、head/base OID 与所读 diff 身份；深挖内容必须来自该 head 的可定位快照，核对本地版本不符时使用只读读取或明确获准的隔离 checkout，不自动改当前工作树。收尾记录审查版本，PR 变动时将旧结论标为旧版本范围。
- **派发者必须提供**：repo/PR 和任何冻结输入要求；OID 可由 reviewer 只读获取，不要求用户手填全部 Git 元数据。
- **验证点/修复风险**：本地与 PR 分支不同、以及审查中 head 变化这两个场景，不能把本地旧代码当 PR 代码。风险低至中。

## sub-agents 独立上下文专项

### 实际传递边界

`--cwd` 解析/`cd` 只改变工作目录。`--prompt-file` 只提供文本；`--no-persist` 选择新的一次性运行；`--persist`/`--resume` 只能恢复明确的子会话，不能自动恢复总控历史。Codex `--thread-source` 是分类参数，也没有收集父对话的逻辑。runner 的 `--sandbox` / `--permission-mode` / passthrough 参数控制执行机制，不生成用户授权或 accepted scope。

派发任务所需的项目指令可以由“明确要求读取的文件路径+版本”提供，不必全部内联；但仅说“遵守既定约束”不足以定位。应避免转发与任务无关的完整历史、凭据或敏感信息。

| 必需信息 | 当前文本/实现 | 判断与归属 |
| --- | --- | --- |
| 目标、非目标、停止条件 | Dispatch Contract 明确；预检只查行首节名 | 形式强制，正文语义由总控确认；空三节也能过结构检查 |
| 任务范围 | 可读/改/禁改文件已要求 | 具体边界由派发者填；不能仅写“当前任务” |
| 冻结输入身份 | Result Validation 180–186 要求失败时拒收，但 Dispatch Contract 无必传身份项 | 通用技能应要求适用时传 base/head/diff hash/manifest/数据版本；实际值由总控提供 |
| 项目约束 | 要求代码、文档、约束路径 | 已有基本义务；路径须唯一且可读，并携带未落盘的相关决定 |
| 既有决定、用户授权 | commit 等默认禁止；其它相关已决事实未显式要求交接 | 技能需声明独立上下文及授权不继承；总控按任务提供必要摘要/证据 |
| 可读写路径 | 文本要求明确 | 预检不验证列表；runner cwd 不是读写白名单 |
| 工具权限、副作用 | 文本要求明确，runner 可传执行权限 | 预检生成命令未设置任务专属 sandbox/tools 白名单；这是文本约束与机制能力的区别，不声称未设置就越权 |
| 预期 artifact/输出格式/validation | 文本要求明确 | 预检不校验 artifact 项；run_dir 中 stdout 文件不等于任务 artifact |
| 成功信号 | 目标和 validation 可以承载，但无显式 completion assertions 项 | 由总控提供可验证断言；通用技能补“成功判据及必要证据” |
| 关键依赖 | 没有显式必填交接项 | 技能要求适用依赖/prerequisite 或 N/A；由总控提供具体输入与状态 |
| task label | 61–62 要求写入 prompt | 拼接器未自动写入；总控须填，或拼接器自动补（可选一致性改进） |
| runtime/provider/model、CANARY | task 模式追加；provided 模式不追加 | S2；模型自报仍需尽可能对照运行证据，不能把静态模型卡当独立服务端证明 |
| 禁止再派发及跨 gate 副作用 | task 拼接追加禁止再派发；Dispatch Contract 禁止提交等 | 总控仍须把适用限制放进完整 prompt；provided 分支不替你补齐 |

### 最小可执行交接模板建议（仅建议，未修改技能）

```text
目标
<具体任务及成功信号；当前角色/gate；唯一 task label>
非目标
<范围外事项；默认禁止 commit/push/PR/merge/跨 gate；是否禁止再派发>
输入与真源
<仓库；输入 artifact 路径；适用的 HEAD/base/hash/manifest；需加载的技能路径>
<当前 slice/finding IDs；必需依赖和 prerequisite 状态；不适用明确写 N/A>
项目约束与已有决定
<必须读取的指令/设计路径；本任务需要的已决事项及依据>
授权与访问边界
<可读、可写、禁止改路径；工具及副作用；必要用户授权摘要；未知授权不得猜>
输出与验收
<唯一 artifact 路径；格式；验证命令/断言；要求的证据；完成信号>
停止条件
<缺失/歧义/版本不一致/不可访问/超范围时返回 blocked 及缺项；完成即停止>
```

通用技能只规定字段意义和缺失时行为；总控填任务事实。机器预检可以保证字段存在、正文非空及可机械比对的身份；不能证明自然语言内容正确或用户真实授权。

### 两个反例 prompt

反例 A（直接复现了节名检查通过，但任务不可执行）：

```text
目标
按刚才确认的方案完成当前 slice。
非目标
不要超范围。
停止条件
完成后停止。
```

反例 B（即便补齐原 Dispatch Contract 的显式项，仍缺关键父上下文）：

```text
目标
按已确认的决定修复 src/api.py 中的当前 slice。
非目标
不得再派发；不提交、不 push、不做 PR、不 merge、不进入其它 gate。
范围与权限
只读 src/、tests/、docs/design.md；可改 src/api.py 与 tests/test_api.py；其它文件禁改。
允许本地读文件、编辑上述文件、运行测试，无外部写操作。
输出
写 docs/reviews/slice-result.md，报告 runtime/provider/model、改动、测试结果和风险。
validation 为项目指定单元测试命令。
停止条件
上述工作完成或必要输入缺失时停止。
```

若父对话的“已确认决定”是不得改 public response schema、使用 plan-v2 slice S2，反例 B 没有传这两项，也没有 plan-v2 身份。它可满足原清单表面结构，但不能唯一确定实施目标。正确修订应加入该 plan/slice/决定证据，而非把整段父历史传给子 Agent。

## 可选改进与不应误报为缺陷的事项

- Gateflow 的 gate 状态写入位置可更明确：首次创建 work-unit 状态 artifact，resume 优先读它。当前已有 durable artifact 要求；目录命名可由项目决定，不必统一硬编码。
- Tmux 清空后应提醒“正式任务重新携带必要背景”；通信技能不承担替用户决定角色/目标。会话清空也不等于共享目录文件被重置。
- Planreview/Deepreview 的固定时间戳命名与调用方指定 artifact 路径可加优先级说明；明确用户路径优先，本次严格写指定文件，不额外生成默认命名文件。
- Phaseflow final closeout 的 next entry point 可以明确允许最后一个 phase 的“项目完成/等待新目标”终态；本次没有具体 control_doc 实例，因此只列可选改进，不声称现有项目一定卡死。
- Gateflow issue closeout comment 的强制产物与额外授权规则需要一起读；未授权必须停，不构成技能已授权任意发评论。本次未发送评论。
- Runner help 中 shell `&` 示例与 Sub-agents 的 harness 独立调用规则应更清楚标明环境边界；直接加载当前 SKILL 时已有明确覆盖规则，本次不另立实质性 finding。

## 实际读取范围

| 对象 | 实际范围/用途 |
| --- | --- |
| 六份指定 SKILL | gateflow 1–340；tmux-agents 1–90；phaseflow 1–339；sub-agents 1–282；planreview 1–198；deepreview 1–400；全部完整阅读 |
| scripts/sub-agent-preflight | 1–268 全文，参数、来源分支、prompt 拼接、校验和命令生成 |
| scripts/codex-agent-run | 1–460 全文，prompt/cwd/sandbox/resume/事件输出与收尾 |
| scripts/claude-agent-run | 1–382 全文，prompt/cwd/permission/输出与 CLI 参数 |
| scripts/agent-tools.zsh | 1–561 全文，重点追踪两个 CLI launcher；app/resume helper 未递归做全功能审查 |
| README.md | 1–210 连续正文；其余技能/runner 相关检索命中只用于定位，未算全文覆盖 |
| 适用 AGENTS | 完整读取 `/Users/leo/workspace/AGENTS.md`；检查根到仓库祖先路径与仓库目录，未找到其它适用 AGENTS.md/CLAUDE.md |
| 本次 canary | 用户指定 run_dir 的 canary.txt 实际读取；20 字节，无尾换行 |
| 本次运行证据 | prompt 文件仅检索报告要求；JSONL 仅提取 thread.started/turn.started；未将本次在途流当终态 |
| 模型卡 | 仓库 codex-agent/profiles/gpt-6-astra/config.toml 全文；本机对应模型卡只提取 model/effort 字段 |
| tmux-cli | 解析 PATH 入口；已读入口全文；tmux_cli_controller.py 1–240、352–523、623–750、782–849、912–940；tmux_remote_controller.py 1–230 |
| memory | 仅快速检索定位以往 runner/审查约定；未读取历史 review，未用历史结论证明当前文件正确性 |

外部 tmux 依赖目录为 `/Users/leo/.local/share/uv/tools/claude-code-tools/lib/python3.11/site-packages/claude_code_tools/`。T1 的具体行号均对应该安装版本；仓库不 vendoring 此依赖，故另记 hash。

## 验证命令与结果

1. `pwd`、`git rev-parse HEAD`、`git branch --show-current`、`git status --short`：确认仓库/HEAD/分支，初始及写前 clean。
2. `nl -ba skills/<name>/SKILL.md` 和分段 `sed -n`：完整阅读六份；对输出截断处重新定向读取补齐。`wc -l` 总计 1649 行。
3. `nl -ba scripts/sub-agent-preflight`、两个 runner 及 launcher：完整源码阅读；未执行任何真实派发。
4. 两个仓库 runner 的 `--help`、`--list-providers`：退出 0；接口/provider 集合与技能表一致。这些路径在加载 launcher 之前退出，不启动模型。
5. `bash -n scripts/sub-agent-preflight`；`zsh -n scripts/codex-agent-run scripts/claude-agent-run scripts/agent-tools.zsh`：退出 0，只做语法检查。未把语法检查当作协议正确性证明。
6. 内存样例调用实际 `grep -qiE` 的三条小节正则：空标题、隐性背景两例均 `[0,0,0]`。没有写测试文件，没有运行会创建 run_dir 的完整 preflight。
7. 内存 AST + 假 `_run_tmux`：验证 remote controller 构造时会走 new-session 分支；未调用 live tmux。
8. Python `git show HEAD:<path>` 与磁盘 bytes 比较：六份技能、三个 runner/preflight 全部一致；SHA-256 见下。
9. `git diff --quiet`、`git diff --cached --quiet`：写报告前均为 0；写后再检查只出现本报告。

探索失败及影响：一次 `ps` 被沙箱拒绝（exit 127），它只用于尝试识别当前运行时，不参与仓库证据/任务判活；改用 thread ID、当前 JSONL 起始事件和模型卡核对。寻找 ephemeral 会话落盘记录未找到，当前线程数据库查询也没有输出，因此未独立证明服务端 model。一次目录检索使用不存在的 `zsh`/`codex` 路径，之后从 README 明确定位 `scripts/agent-tools.zsh` 与 `codex-agent/`；所需关键来源均已读取，未用失败检索冒充覆盖。

## 未覆盖面与剩余风险

- 未启动任何子 Agent、未重跑真实 preflight/runner、未做真实 tmux send/clear、未请求外部模型或 GitHub；因此不声明跨 provider live 行为和服务可用性通过。
- tmux 依赖只走读相关方法，未全文审计整个第三方包；未实测具体 Codex/Claude CLI 版本对 `/clear` 的行为。技能要求清空后确认可输入，报告未据未验证的命令兼容性立 finding。
- 未递归审计 launcher 的 app 配置生成、历史修复脚本、shim 或模型服务；它们不负责本次发现中的新子任务上下文交接。
- 当前本机 Astra 模型卡 effort 为 `high`，仓库模型卡为 `medium`；这是已观察到的安装与仓库差异，仅作 provenance 记录，未修改/同步。当前事件没有足够信息证明最终生效 effort，亦不以本机安装状态代替仓库审查对象。
- S1/P1/G1/P2/D1 是文本契约及真实代码路径推导的失败场景，未故意触发源文件修改或错误 gate；建议由总控裁决后用受控 fixture 验证修订。
- 所有建议均未实施。若未来版本改变，应按文末输入身份重审；本报告不为后来 HEAD 或 live 安装内容背书。

## 输入 SHA-256

| 文件 | SHA-256 |
| --- | --- |
| skills/gateflow/SKILL.md | `05b41c97a4e5c5664d2b4c36b69afa3eda5558884dc5854d760d0293e562335a` |
| skills/tmux-agents/SKILL.md | `af8c065349297b55c6bf161d45e75a7b3b754fd49212066b8780e1bb07dd5551` |
| skills/phaseflow/SKILL.md | `3a347b35db80c0e03446dc4d68097a42170a709c240859ef20dd35bea472f8fd` |
| skills/sub-agents/SKILL.md | `fa50104cec9728f93a07d7f06112dd7ed191323f65853a6160021f8c5deecee7` |
| skills/planreview/SKILL.md | `aa5878d7e84023516882dbb9ec200bbec9cc0034296ea2e811fa1e8d71535402` |
| skills/deepreview/SKILL.md | `cd76556e5ef4d60243bdc15cd565b22df77472038a687fb92b210c94bbe1997b` |
| scripts/sub-agent-preflight | `787cd48099a090052d3da998361295a4c46c5aa935fb59b15cd436559a5c26ba` |
| scripts/codex-agent-run | `2fa002e9b712690a64eb0daf09637c1e1f685120a2a8900455e027f60f142725` |
| scripts/claude-agent-run | `fc32442cdf5349d7d10a03a5d473786aa82736ca407069ee92347e2d82619f4e` |
| scripts/agent-tools.zsh | `4e8b6d63093f4fdea1b719a47ad7282e7c97ac23cbdf2ba17eb90450470caac7` |

外部 tmux_cli_controller.py：`191260af809831736670499586028e66d55035b1f48eb6f96315d92a26abd79b`；tmux_remote_controller.py：`b8cdf7b7a8a080dea2bc15dbea2a11e7da7462c0d7870f97b2f40a330d958ba3`。

## 收尾

六份入口覆盖完整，直接执行依赖的关键断言已按上述范围核对。报告可作为总控裁决输入；本审查不代表任何 gate 放行、PR 批准或修复授权。
