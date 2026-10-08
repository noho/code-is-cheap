---
name: sub-agents
description: "通过 claude-agent-run 或 codex-agent-run 子进程启动外部子 Agent。用于隔离或并发派发调查、实现和 review 任务，并检查进程与结构化输出。"
---

# Sub Agents

使用下述 runner 子进程派发子 Agent。此 skill 激活时，所有子 Agent 调用都必须遵循本协议。

## Runners

| Runtime | Command | Providers | Default structured output |
| --- | --- | --- | --- |
| Claude Code | `claude-agent-run` | `ds-flash mimo mimo-fast mimo-flash qwen kimi glm glm-flash local hy` | one JSON result |
| Codex | `codex-agent-run` | `ds-flash mimo mimo-fast mimo-flash qwen kimi glm glm-flash local gpt-6-astra gpt-6-sol gpt-6-luna business` | JSONL event stream |

两个 runner 已在 PATH，直接以命令名调用。调用前先跑 `<runner> --help` 确认可用与接口，并用 `pwd -P` 得到当前任务
workspace 的绝对路径。每次调用必须显式传入 `--cwd "<absolute-workspace>"`，不得依赖总控当前目录。

codex 的 runner 按 `--cwd` 自动判定并追加 `--skip-git-repo-check`（非 git 仓库时），无需手工传；claude-agent-run 无此参数。

## Preflight Checklist

每次派发前逐项过。`sub-agent-preflight` 只完成可机械验证的 setup / 结构检查，生成 run_dir / canary /
最终 prompt（任务正文 + 本轮固定报告协议），并打印命令。它只能拒绝可识别的字面值、路径、
provider 形式 token 和固定协议标记，不能靠正则证明任意自然语言同义旧报告指令不存在。总控仍须逐项核对
下方 Dispatch Contract、prompt 的语义完整性、实际授权和并发写边界；尤其要按语义拒绝任何与本轮报告协议
冲突的旧报告动作。`setup_status=ok` 不证明这些内容正确：

```bash
sub-agent-preflight --runtime <claude|codex> --provider <name> --cwd "<absolute-workspace>" --label "<unique-label>" --task-file <path>
```

`setup_status=ok` 才可派发；任何 `failure=` 都是 **controller setup error**（见失败分类），修好后重跑，不得带着
setup 错误派发。

只有 `sub-agent-preflight` 不可用（未安装或执行失败）时才允许手工预检：必须逐项完成同样八项，把每项结果写进
报告（`setup_status` + 逐条 `failure`），不得跳过检查直接派发：

- [ ] workspace 用 `pwd -P` 解析为绝对路径，`--cwd` 显式传入，不依赖总控当前目录；
- [ ] Git 条件已判定（`git -C "$workspace" rev-parse --is-inside-work-tree`）；codex 的非仓库情形由 runner 自动处理；
- [ ] 两个 runner 均在 PATH，且各自的 `--list-providers` 成功并包含完整基线；`<provider>` 出现在所选 runner 的
      catalog（预检用另一 runtime 的 catalog 识别跨 runtime 旧 token）；
- [ ] launcher 函数与 profile 已部署（codex `business`：`~/.codex-agent/business/config.toml`；其它 Codex
      provider：`~/.codex/<provider>.config.toml`；与 `scripts/agent-tools.zsh` 的 home / `-p` 解析一致）；
- [ ] prompt 是完整任务正文（`--task` / `--task-file`，或 `--prompt-file` 给完整正文；预检均生成本轮最终副本并追加报告协议），
      含 `目标` / `非目标` / `停止条件` 三节（每节单独一行、行首写节名，英文 `Goal` / `Non-goals` / `Stop condition`
      等价；预检会校验）。三种来源均不得含旧 `CANARY=` / `CANARY:` 值、`canary.txt` / `canary.expected`
      文件名（包括裸文件名或路径）、provider 形式的裸旧 token、或固定报告指令；普通讨论 CANARY 概念可以保留。
      预检会在追加本轮协议前检查机械特征；总控还须语义检查其它旧报告动作，确保追加的本轮协议为准；
- [ ] 输出路径（`--output` / `--stderr` / `--last-message`）全新，label / `--instance` 唯一；
- [ ] 一次性任务用 `--no-persist`；默认权限不变；显式隔离派发见下节；
- [ ] 并发无写冲突：写入范围重叠或有依赖时必须串行。

## Dispatch Contract

runner 收到的 `--prompt` / `--prompt-file` 在新的独立 Agent 上下文执行；它不继承总控对话、裁决或用户授权。
相同 `--cwd` 只确定工作目录，同一文件系统或相同 provider 也不传递这些上下文。总控须在任务 prompt 中交接
本任务必要的背景、已决事项及其依据、用户授权范围、冻结输入版本、依赖和验收信号；也可给出明确可定位的
文件路径及版本供子 Agent 读取。只交接本任务必要信息，不转发无关的对话全历史或敏感信息。
不得使用只有父上下文知道意义的“刚才”“照旧”“已确认”等引用。必要信息缺失、不可访问或版本不符时，
子 Agent 应报告 `blocked` 和缺项，不得猜测。

每个子 Agent 的 prompt 必须明确：

- 目标、非目标和 stop condition；
- 本任务所需的既有决定、授权边界、输入 artifact 与冻结身份（适用的 HEAD/base/hash/版本）以及关键依赖；
  不适用项明确写 `N/A`，不得把 `--cwd` 或工具权限当作用户授权；
- 探针 / 验证类任务的非目标必须包含"不得再派发子 Agent"（任务本身是编排时除外）；
- 可读取、可修改以及禁止修改的文件；
- 是否允许调用工具和允许的副作用；
- 相关代码、文档和约束的路径；
- 预期输出格式、artifact 路径、validation、可验证的成功判据与必要证据；
- 报告开头必须声明自身的 runtime、provider 和 model；自报与 event stream 不符时以 event stream 为准；
- 禁止 commit、push、PR、merge 或进入其它 gate，除非任务明确授权。

一次性任务默认使用 `--no-persist`。Claude 调用必须使用唯一 `--instance`。Codex runner 没有
`--instance` 参数，应使用唯一 task label、输出文件名，并把该 label 写入 prompt。

子 Agent 权限默认继承 auto 模式，无需显式传 `--permission-mode`；需要收紧时显式指定。Codex 用 `--sandbox`
选择内层沙箱级别。单独的 `--full-access` 关闭内层沙箱与工具审批，不提供输入隔离；只在调用方明确选择
这种权限时使用。不得通过宽权限扩张用户授权或任务 scope。

## Execution And Isolation

为每轮派发创建独立目录：

```bash
run_dir="$(mktemp -d "${TMPDIR:-/tmp}/sub-agents.XXXXXX")"
workspace="$(pwd -P)"
```

默认调用：

```bash
claude-agent-run \
  --provider ds-flash \
  --cwd "$workspace" \
  --instance "review-dsflash-01" \
  --no-persist \
  --output-format json \
  --output "$run_dir/review-dsflash-01.json" \
  --stderr "$run_dir/review-dsflash-01.stderr" \
  --prompt "<bounded task>"

codex-agent-run \
  --provider gpt-6-astra \
  --cwd "$workspace" \
  --no-persist \
  --output-format json \
  --output "$run_dir/review-astra-01.jsonl" \
  --stderr "$run_dir/review-astra-01.stderr" \
  --last-message "$run_dir/review-astra-01.last.md" \
  --prompt "<bounded task>"
```

派发必须在沙箱外运行，方式取决于总控环境：

- Claude 总控：以独立的一次 Bash 调用发出——裸命令、无引号、无 `$HOME` 前缀、不管道、不复合，run_dir 等准备
  工作在之前的调用完成，使命令命中 `excludedCommands`；
- Codex 总控：每个子 Agent 使用一次独立的 `exec_command` 调用，显式设置 `sandbox_permissions:
  "require_escalated"`（附 justification）；若返回 session_id，通过对应的 `write_stdin` 收集。

沙箱内派发的典型症状：codex 子 Agent 初始化失败（`failed to initialize in-process app-server client`）；
claude 子 Agent 能启动但自身 Bash 不可用（`EPERM ... srt-mux`）。出现这些症状时优先检查派发是否仍在沙箱内；
若派发已显式提权，则检查子进程自身的沙箱配置——该报错不唯一指向父级派发未出沙箱。

并发派发 = 多次**独立**调用（Claude 总控：多次 `run_in_background: true`；Codex 总控：每个子 Agent 一次独立的
`exec_command`，若返回 session_id 则用对应的 `write_stdin` 收集）。Claude 环境中复合命令（`&`、`&&`、管道）
可能无法命中 `excludedCommands`，导致子 Agent 的 Bash 失效。
收集时逐个核对各自退出码与 artifact。存在数据依赖、
写入顺序依赖或 file ownership 重叠时必须串行。不得让多个子 Agent 并发修改同一文件，除非已划分互不重叠的写入范围。

不要仅因运行时间长而 kill、重派或切换 provider。后台任务仍在运行、或输出文件仍有变化时，默认仍为 in-flight；
判活不得依赖 ps / pgrep / kill -0 等进程查询。只有托管调用句柄返回、进程退出或用户停止等证据，
才能认定该进程已结束；文件暂时没有变化不等于进程已退出。Agent 报告无法继续、托管工具明确报告阻塞，
或预先约定的超时条件触发时，可标记任务 `blocked`；仍在运行的进程须继续收集或经用户授权停止，
不得把 `blocked` 冒充进程已退出。用户明确停止并完成中止后，记录为 `blocked` 与停止原因。

### 可选的任务禁读边界（macOS）

默认调用没有任务级读取隔离。调用方需要禁止读取指定材料时，先备齐本次输入，创建 JSON 数组文件，
其中每项为禁止读取的文件或目录的绝对路径；目录递归禁止。路径必须为已存在的普通文件或目录，按字面值处理，不是 glob。
调用方决定范围：业务报告、历史日志及已知副本分别列出；封装不推断角色、业务规则或内容相同的未知副本。

```bash
sub-agent-preflight --runtime codex --provider mimo --cwd /absolute/workspace \
  --label unique-review --task-file /absolute/task.md --deny-list /absolute/denied.json
```

预检生成 `agent-sandbox ... -- codex-agent-run ... --full-access ...` 命令；Claude 同样通过对应 runner。
也可显式用 `agent-sandbox --cwd /absolute/workspace --deny-list /absolute/denied.json -- <runner> ...`。
封装隐含 `--full-access --no-persist`，固定本次文件系统策略。它不支持 resume、native 参数透传、stdin prompt、动态投递或追加 prompt。必须恰好一个非空 `--prompt` 或普通
`--prompt-file`，启动前复制到受写保护的状态；随后关闭 stdin。
`--cwd` 只决定工作目录；获准来源、Python 依赖和 canary 仍可按原路径读取，禁读名单之外没有读取白名单。
启动后在外层 Seatbelt 内验证禁读路径确实被拒绝，再启动 Agent；setup 通过本身不是隔离证据。

封装必须从总控沙箱外启动：Codex 总控仍使用独立 `exec_command(require_escalated)`；Claude 总控须将
`agent-sandbox` 加入自己的 `sandbox.excludedCommands`，并以独立裸命令派发。内层 Full Access 无法解除
外层 Seatbelt。保留原有生命周期、canary 和结果验收协议；权限错误应报告具体缺项，不自动移除禁读项或放宽权限。

首次使用前，由用户按仓库 README 安装可选 srt 依赖。封装只支持经测试的 macOS/srt 版本，检查失败立即停止。
它保留原 runtime 写范围的保守子集及指定输出文件，复制并保护 Codex 用户 `.rules`；不能推导的自定义权限配置会拒绝启动。隔离调用不加载
宿主 MCP、hooks、plugins 或浏览器工具；Claude 仅启用 Bash/Read/Write/Edit/Glob/Grep，Codex 使用本地原生工具。
禁读路径在运行期间不得由其它未隔离进程替换或复制；已有硬链接会拒绝启动。需要的工具/网络缺项须报给调用方裁定。必需的凭据/配置文件列入禁读时 setup 会停止；不提供凭据与 Agent 工具之间的隔离。

### Sandbox Process Management

沙箱（`sandbox.enabled`）下进程管理一律使用下列配套方法，不要在协议里使用 `ps` / `pgrep` 或其它进程列表工具。

- **派发与收集（Claude 总控）**：用 Bash 工具的 `run_in_background: true` 独立发出；harness 托管的后台任务跨调用
  存活，通过后台任务句柄收集完成状态与退出码，输出由 harness 落盘。不要用 shell `&`——其子进程在沙箱下会随
  Bash 调用结束被回收；
- **派发与收集（Codex 总控）**：每个子 Agent 一次独立的 `exec_command`；可能直接返回退出码，也可能返回 session_id，
  后者用 `write_stdin` 持续收集，直到取得退出码；
- **进度判据**：run_dir 内输出文件（或后台任务的 harness 输出文件）的大小 / mtime 变化，不要用进程列表；
- **退出码**：Claude 后台取托管任务完成通知，Codex 取 `exec_command` / `write_stdin` 返回的退出码；
  前台直接调用取其返回码。仅在对应 harness 明确提供时使用完成通知中的退出标记，不假设 runner 输出文件自带该标记；
- **输出流**：后台模式会把 stdout/stderr 合并进同一文件，因此结构化输出与日志必须继续通过 `--output` /
  `--stderr` 落到 run_dir。

## Result Validation

分开裁定**派发生命周期**和**结果可信度**。沙箱内以 Sandbox Process Management 一节所述句柄收集退出状态：Claude 后台任务的完成通知，
Codex `exec_command` 的退出码或 `session_id` 后续 `write_stdin` 的退出码；前台调用则取其直接返回的退出码。
不得以 `ps` / `pgrep`、文件大小或最终消息代替退出证据。进程结束后检查 exit code、stderr、取得的全部结构化输出、
最终消息及要求的 artifact；结构化终态与外层退出码都要核对。任一仍在途时不作最终验收。

任务要求工具调用时，"完成"不证明实际执行过工具；需有可核对的工具执行记录。它只证明调用发生，
不证明每项必需取证都成功，后者还须按任务要求核对：

- Codex：event stream 中有实际 `command_execution` 或 `mcp_tool_call` 的结果；命令非零退出也可能是有效反例，
  但必须按下文检查影响；
- Claude：`num_turns >= 2` 只表明多轮交互；canary 匹配只证明指定文件读取成功，不能证明其它工具调用成功。

验证类派发（探针、验收、产出会被下游信任）必须使用 canary：

1. `TOKEN="<prefix>-$(openssl rand -hex 4)"`，用 `printf '%s' "$TOKEN" > canary.txt` 写入 run_dir 内文件
   （**不带尾换行**，消除"逐字比较"在结尾空白上的歧义）；总控侧另存一份字节相同的 `canary.expected` 作为比对基准；
2. prompt 只给文件路径，不得包含 TOKEN 本身（`sub-agent-preflight` 会自检并拒绝含 token 的 prompt）；
3. 比对规则：子 Agent 报告的 token 字符串与基准**逐字一致**（仅边缘空白不计）；需要字节级证据时，直接比对子 Agent
   `cat canary.txt` 的原始输出与文件字节。不等即判失败——即使其它检查全部通过。

伪造型静默失败是硬失败，不重试，记录并上报：最终消息含字面工具调用语法（`<tool_call>`、`<tool_result>`、
裸 JSON 工具对象）而 event stream 无对应执行事件——provider 级缺陷特征。

已确认的非致命诊断记录为 warning。下表只给这些诊断的精确识别方式，不做近似匹配；检查位置按表，不看其它流：

| predicate（精确判据） | 检查位置 | 处理 |
| --- | --- | --- |
| stderr 某行以 `[claude-code:unrecognized_model]` 开头（其后 JSON payload 不参与匹配） | Claude 侧 stderr | 记录 warning，不判失败 |
| `item.type == "error"` 且其 message 匹配 `^Model metadata for \S+ not found` | Codex event stream（stderr 不作为豁免依据） | 记录 warning，不判失败 |
| `item.type == "error"` 且其 message 含子串 `unrecognized_model` | Codex event stream（stderr 不作为豁免依据） | 记录 warning，不判失败 |

除 turn 级终态外，其它 `error` / `failed` 事件及 `command_execution` 的每个非零 `exit_code` 都不得忽略，
也**不自动判整次派发失败**。即使 item 外层状态为 `completed`，也要检查命令退出码。总控逐条查看事件对应的命令、错误、任务目的、
后续恢复和最终结论：

- 探索性无匹配、预期的反例或已成功改用其它证据的失败，可以记录为已解释的 warning；例如 `rg` 无匹配本身
  不证明审核失败。必须说明该失败为何不影响结论，不能只凭 Agent 最终消息未提失败就认定无影响。
- 测试失败、冻结 diff 比对不一致、读取关键来源失败或工具内核崩溃，先判断该步骤对任务的作用。若它揭示了
  被审核对象的问题，可保留为有效 finding；若关键取证未恢复，相关结论不得采纳，也不得把缺口写成通过。
- 审核输入身份校验失败（如冻结 diff 比对不一致）时，先查明并恢复输入身份；未恢复前，针对该冻结输入的
  审核不能记为 `accepted`。若无法确定失败是否影响必要证据，标记未解决并停在当前 gate；
  先裁定影响与失败类别，再按 Retry And Sessions 决定是否可重派，不得用重派抹去可评分的错误结论。

runner / 托管调用的**外层进程**退出非零、缺少可信终态、结构化输出损坏、canary 不匹配、伪造型静默失败
仍是硬性拒收条件；`command_execution.exit_code` 非零按上文逐项裁决，不等于外层进程失败。关键 artifact 缺失、
无法证明审核了指定输入、未恢复的关键工具失败是结果验收失败。即使派发生命周期正常结束，也须由总控独立核对
关键代码、来源、测试或其它任务证据，再决定采纳、部分采纳或驳回；子 Agent 的 final answer 不单独构成验收。

Claude JSON：

- 文件必须是有效 JSON；
- 检查外层 `subtype`、`is_error` 和 `result`；
- 非成功 subtype、`is_error=true`、缺少 result 或非零退出码均不得判定成功；
- `result` 可能包含 Markdown code fence。解析其中的 JSON 时先去除 fence，再进行结构化解析。

Codex JSONL：

- 每个非空行都必须是有效 JSON event；
- 检查每个 error / failed event、每条 `command_execution` 的非零 `exit_code` 及其后续处理；
  要求存在明确的 `turn.completed`。`turn.failed` 或缺少 completion evidence 属派发失败，item 级工具失败按上述影响判定；
- 优先使用 `--last-message` 保存最终消息，但仍必须同时审查完整 event stream 和 stderr。

Claude 默认 JSON 只有汇总结果，无法逐条观察中间工具失败。记录此可见性限制；不能凭 JSON 成功或 canary 匹配
断言中间调用均成功。总控须独立复核关键输入、产物及任务所要求的测试或取证；无法复核时，相关结论不能记为
`accepted`。只有实际取得逐调用轨迹时，才要求逐条列出 Claude 的中间失败事件。
空 stderr 不证明成功，非空 stderr 也不自动证明失败；结合退出码、结构化状态及任务证据裁决。

## Retry And Sessions

失败先归类，再决定动作：

- **controller setup error**（派发前失败，子 Agent 根本没跑起来）：prompt 文件缺失或为空、`--cwd` 不存在、git 条件
  处理错、输出路径已存在、runner / launcher / profile 未部署、prompt 含 canary token。**不计入 provider 重试额度，
  也不计入任何测量批次**；修好后用**新 label** 重派（同修复性重试规则），并在报告里单列为 setup 失败。
- **provider / 测量失败**（子 Agent 真的运行过）：按下方规则处理。

派发或结果验收失败后，先根据 stderr、结构化输出和任务证据区分配置错误、超时、模型错误或任务错误。
裁决块中 `retry_class=provider` 用于 provider / 运行环境故障，`task` 用于 Agent 的命令、取证或任务执行错误；
尚未查清原因写 `unknown` 并停在当前 gate，不据此切换 provider。
普通工具失败已恢复且不影响结论时，不消耗重试额度。确需重派时只允许一次有明确理由的同 provider 重试；
再次失败后，若任务或项目另有替补路由限制，先遵从该限制；否则可切换 provider。记录两次失败和切换原因；
不得用本 skill 绕过任务或项目的路由授权。
不得无上限重试。

区分派发错误与测量数据：基础设施失败（起不来、超时、配置错）可按上一条重试；测量 provider/环境行为的派发，
一旦启动，失败必须计入原批次，禁止用重派结果替换或重试到成功，且必须固定并发度；本条优先于通用重试规则。

修复性重试必须使用新的 task label，并同步用于 prompt、输出文件名和 Claude `--instance`，同时记录与原尝试的关联
标识；修复性重试不得并入原测量批次的通过率，如需重新测量，另建固定并发度、预定样本数的新批次。

需要多轮延续时，第一次使用 `--persist`：

- Claude 后续使用返回的 session ID 配合 `--resume`；
- Codex 后续使用 `--resume <id>` 或在明确需要时使用 `--resume-last`；
- 一次性任务不得持久化 session。

## Controller Adjudication

子 Agent 输出只是输入证据。总控必须读取相关 artifact、review 关键代码或数据、交叉核对冲突，逐条处理可能
影响结论的工具失败，并自行采纳、部分采纳或驳回。不得因多个 Agent 表述一致或 final answer 没提失败就跳过证据检查。

已派发任务只有取得进程终态并完成检查后，才填写完成报告的固定裁决块；预检失败可在确认子 Agent 未启动后
填写 `setup_status=fail` 的裁决块。在途时只作进度更新，记录托管句柄状态、
最近输出变化与尚未取得的退出码，不填写完成裁决块。值取自实际检查，不得凭印象；确实未检查的写 `unknown`，
不得把 `unknown` 当作通过：

```yaml
setup_status: ok | fail | unknown # sub-agent-preflight 或手工预检的结果
agent_status: completed | blocked | failed | not_started
tool_evidence: yes | no | unknown # 至少一次可核对的工具执行；不代表全部必需取证已成功
tool_trace: complete | partial | summary_only | missing | not_required | unknown # 可见轨迹范围
required_evidence: complete | partial | missing | not_required | not_assessed # 任务必需证据经总控复核后的状态
canary_status: match | mismatch | not_run | unknown
result_status: accepted | partial | rejected | not_assessed # 总控对任务结论的裁定，独立于 agent_status
warnings: []                     # 已解释且不影响结论的诊断 / 工具失败逐条列出
evidence_gaps: []                # 未解决的关键取证缺口；无则空列表
retry_class: none | setup | provider | task | unknown
```

`result_status=accepted` 只表示该子任务的证据与报告可采纳；code review 报告含 blocking finding 时，代码仍不得放行。
`tool_trace=complete` 表示逐调用轨迹可核查，`partial` 表示有缺段，`summary_only` 表示只有 Claude 等汇总结果，
`missing` 表示应有轨迹却没有；这组值不替代 `required_evidence` 的逐项复核。`partial` 或 `summary_only`
只有在全部必需证据经总控独立复核、且无其它硬性拒收条件时，才可支持 `result_status=accepted`。
`agent_status` 记录进程 / 任务终态，`result_status` 记录报告可采纳性：进程退出 0、结构化终态成功但 canary 不匹配时，
`agent_status=completed`、`result_status=rejected`，不能伪称进程失败。`agent_status=failed`、`canary_status=mismatch`
或 `setup_status=fail` 时，`result_status` 只能为 `rejected` 或 `not_assessed`；`agent_status=blocked` 或
`not_started` 时不能为 `accepted`。任务要求工具调用而 `tool_evidence=no`，或任务有必需证据但
`required_evidence` 不是 `complete` 时，受影响结论不能记为 `accepted`。验证类任务若 `canary_status`
不是 `match`，也不能记为 `accepted`。`tool_trace=summary_only`（Claude 默认 JSON）并不自动拒收；
须逐项独立复核必需证据并说明范围。`evidence_gaps` 非空时不能把受影响结论记为 `accepted`。

`setup_status=fail` 时子 Agent 未启动：`agent_status` 必须写 `not_started`、`canary_status` 必须写 `not_run`、
`result_status` 必须写 `not_assessed`、`retry_class` 写 `setup`。每次派发的裁决块后接人读叙述，逐个列出：

- runtime、provider 和唯一 task label；
- 子任务；
- 退出状态的来源与数值；
- stdout、stderr、last-message 或 artifact 路径；
- 每条可观测的非豁免失败事件（Codex 优先用 `item.id`，否则用 JSONL 行号）、步骤、恢复证据及对结论的影响；
  Claude 汇总 JSON 无逐调用事件时明确说明；列出未解决的关键证据缺口；
- 总控实际独立复核的关键文件、命令或数据范围，以及采纳、部分采纳或驳回的结论与理由；
- retry、provider switch 和未解决风险。
