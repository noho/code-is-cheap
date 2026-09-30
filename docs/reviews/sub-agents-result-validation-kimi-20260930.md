# Code Review

RUNTIME/PROVIDER/MODEL: claude/kimi/kimi-k3[1m]
CANARY=kimi-b60fb7f5

## Scope

- Mode: current changes
- Branch: codex/sub-agents-result-validation（HEAD = a827aff，与 main 的 merge-base 相同，分支上无已提交改动）
- Base: main
- Review time: 2026-09-30 11:40 CST（本机系统时钟）
- Output file: docs/reviews/sub-agents-result-validation-kimi-20260930.md
- Included scope: 工作区未提交的 `skills/sub-agents/SKILL.md` 改动（+35/-16，`git diff` 全文）；为核对契约一致性，对照阅读 `scripts/sub-agent-preflight`（268 行全读）、`scripts/codex-agent-run`（460 行全读）、`skills/deepreview/SKILL.md`、`skills/phaseflow/SKILL.md` 与 `skills/gateflow/SKILL.md` 中路由/派发相关段、README.md / README.zh.md 的 sub-agents 段，以及 docs/reviews 下既有裁决文档中对 codex event 名称的实证记录。
- Excluded scope: 上述对照文件的全量 review；仓库其余代码；MiMo 同轮审核产物（任务明确禁止读取）。
- Parallel review coverage: 无（任务明确禁止派发子 Agent）。

改动意图（从 diff 归纳）：把结果验收从"失败 event 一律判负"改为"派发生命周期与结果可信度两轴分离 + 总控逐条裁决失败 event"，并在裁决块新增 `result_status` 键；同时收紧沙箱内派发完成判定（禁止以文件静止推断进程退出）与 provider 切换授权。

## Findings

### 01-未修复-[高]-挂死的派发没有任何合规结束路径，`blocked` 状态成为孤儿枚举
- **入口/函数**: 总控按 `## Execution And Isolation` 的判活规则（skills/sub-agents/SKILL.md:118-120）裁决一次在途派发是否结束。
- **文件(行号)**: skills/sub-agents/SKILL.md:118-120（改动后）；对照 :232（`agent_status` 枚举含 `blocked`）。
- **输入场景**: provider 网关停滞或子进程僵死——托管句柄（Claude 后台任务通知 / Codex `write_stdin` 会话）始终不返回，event stream 无 error/failed 事件，输出文件 mtime 数小时不变，用户不在场（phaseflow 自动推进）。
- **实际分支**: 改动后 :119-120 枚举的结束证据只有"托管调用句柄返回、进程退出、明确失败或用户停止"。挂死场景四者均不满足；"文件暂时没有变化不等于进程已退出"（:120）进一步封死以输出静止为据的结束路径；:118 又禁止仅因运行时间长而 kill。旧文本中该场景的出口"阻塞"（改动前原文："只有明确失败、阻塞、用户停止或进程退出证据才能结束该次派发"）被本次 diff 删除。
- **预期行为**: 协议应为可观测的 stalled 状态给出客观判据与合规结束路径（结束为 `blocked`），使状态机对常见 provider 停滞可终止；裁决块的 `blocked` 枚举应有对应的进入条件。
- **实际行为**: 挂死派发在协议内永不终止。总控只剩两个选择：(a) 无限等待，gate 停摆；(b) 违反成文协议自行 kill 并标记失败——而这正是本 skill 要消除的"总控临场发挥"。同时 :232 的 `agent_status: ... | blocked | ...` 在全文不再有任何进入该状态的规则，成为孤儿枚举；"用户停止"映射到哪个枚举值也未定义。
- **直接证据**: :119-120 新文本的枚举清单（diff 显示旧清单含"阻塞"，新清单删除）；:118 的 kill 禁令；:120 的静止≠退出条款；:232 枚举仍含 `blocked`（diff 中该行未改，属上下文行）。
- **影响**: 自动编排（phaseflow/gateflow）在 provider 停滞时停摆或被迫违约操作；`blocked` 报告值失去判定依据，下游无法信任该键。
- **建议改法和验证点**: 不要删除"阻塞"，而是把它客观化：例如"托管句柄仍打开 + 输出文件超过 N 分钟（N 由任务声明）无变化 + 无在途工具事件"可判 `blocked`，判 `blocked` 允许结束派发并按失败类计入重试规则；同时在裁决块定义"用户停止"对应的 `agent_status`（建议新增 `stopped` 或显式映射为 `blocked`）。验证点：构造一个只输出一半就静默的 mock runner，确认总控按新条款能在有限步骤内合规结束派发并写出一致的裁决块。
- **修复风险（低/中/高）**: 低——纯协议文本补全，不涉及 runner 代码。
- **严重程度（低/中/高/严重）**: 高

### 02-未修复-[中]-provider 切换的前置条件引用了仓库中不存在的"上层路由规则"
- **入口/函数**: 总控在第二次失败后按 `## Retry And Sessions` 决定是否切换 provider（skills/sub-agents/SKILL.md:206-209）。
- **文件(行号)**: skills/sub-agents/SKILL.md:208。
- **输入场景**: 同 provider 两次失败（如 mimo 超时后再败），总控考虑切换到 ds-flash；使用场景为 gateflow、phaseflow 或直接 `$sub-agents` 派发。
- **实际分支**: :208 新文本"再次失败后可在任务的上层路由规则允许时切换 provider……本 skill 不扩大替补路由授权"。切换动作被挂到"任务的上层路由规则"这个外部授权源上。
- **预期行为**: 恢复动作的授权条件必须可在本协议或其明确命名的契约内解析；旧文本是自包含的（"再次失败后可切换 provider，并记录两次失败和切换原因"）。
- **实际行为**: 全仓检索"上层路由 / 路由规则"（`grep -rn`，覆盖 skills/、scripts/、docs/plans、docs/closeouts、README）唯一命中就是 :208 本身。gateflow 与 phaseflow 均无任何 provider 路由/替补规则（phaseflow 只有派发协议选择：sub-agents vs tmux-agents，见 skills/phaseflow/SKILL.md:121-124）。对当前全部使用模式，该前置条件的指称不存在：保守解读（无规则即不允许）使切换路径事实失效——这是对旧自包含规则的行为回退；宽松解读（总控自判）则使"不扩大替补路由授权"的护栏落空。两种解读并存且协议不裁决。
- **直接证据**: skills/sub-agents/SKILL.md:208；`grep -rn "上层路由\|路由规则"` 全仓仅命中该行；skills/gateflow/SKILL.md 与 skills/phaseflow/SKILL.md 中 `路由|provider 切换` 检索零命中。
- **影响**: 恢复动作授权不确定；不同总控/不同轮次对同一情形做出不一致决策；审计时无法判定某次 provider 切换是否合规。
- **建议改法和验证点**: 二选一并写明：(a) 若意图是禁止 skill 层自行切换，直接写"再次失败后停在当前 gate 并上报，由任务发起方决定是否切换 provider"；(b) 若允许切换，恢复旧文本的自包含规则，并保留"不扩大替补路由授权"作为对任务 scope 的限制说明。验证点：以 phaseflow 场景走查第二次失败后的决策树，确认每一步授权来源可指到具名条款。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 中

### 03-未修复-[中]-新增两轴裁决块缺少跨键一致性约束，逻辑矛盾的组合不被成文契约禁止
- **入口/函数**: 总控按 `## Controller Adjudication` 填写固定键裁决块（skills/sub-agents/SKILL.md:230-243）。
- **文件(行号)**: skills/sub-agents/SKILL.md:230-243；相关判据 :154（canary 不等即判失败）、:176-178（派发硬失败 / 结果验收失败清单）。
- **输入场景**: 派发出现硬失败（如 canary_status=mismatch 或 agent_status=failed），但总控（LLM）在压力下或疏忽下填写裁决块。
- **实际分支**: 契约只对 `setup_status=fail` 规定跨键约束（:242-243：`agent_status=not_started`、`canary_status=not_run`、`result_status=not_assessed`、`retry_class=setup`）。`result_status` 被声明"独立于 agent_status"（:235），但对反向矛盾组合没有任何禁止条款。
- **预期行为**: 裁决块是下游 gate 唯一机器可校验的信任锚点；逻辑上不可能的组合应被成文禁止，例如：`agent_status=failed` 时 `result_status` 不得为 `accepted`（:176-178 已规定硬失败的结果不得采纳）；`canary_status=mismatch` 时 `agent_status` 不得为 `completed` 且 `result_status` 不得为 `accepted`（:154"不等即判失败——即使其它检查全部通过"）。
- **实际行为**: `agent_status=failed + result_status=accepted`、`canary_status=mismatch + agent_status=completed`、`canary_status=mismatch + result_status=accepted` 均不违反任何成文条款。值"取自实际检查"的元规则（:228）约束单键取值，不约束键间一致性；prose（:176-178）的禁止性条款没有映射到裁决块字段上。
- **直接证据**: :230-238 键定义与 :242-243 唯一一致性条款；对比 :154、:176-178 的失败判据无任何键级回写要求。
- **影响**: 自相矛盾的裁决块无法被读者或机器检查发现；两轴模型的可信度恰恰依赖这组键的连贯性，缺口直接削弱本次改动的核心交付物。
- **建议改法和验证点**: 在裁决块后补一张最小一致性表：`canary_status=mismatch ⇒ agent_status=failed ∧ result_status∈{rejected,not_assessed}`；`agent_status=failed ⇒ result_status∈{rejected,not_assessed}`；`agent_status∈{blocked,not_started} ⇒ result_status≠accepted`。验证点：用三个矛盾组合样例逐条对照新表，确认均被成文禁止。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 中

### 04-未修复-[低]-`turn.failed` 的字面归属在 §167 与 §191 之间冲突
- **入口/函数**: 总控按 `## Result Validation` 裁决 Codex event stream 中的失败事件（skills/sub-agents/SKILL.md:167-174 与 :190-191）。
- **文件(行号)**: skills/sub-agents/SKILL.md:167 与 :190-191。
- **输入场景**: Codex JSONL 中出现 `turn.failed` event（turn 级终态失败）。
- **实际分支**: :167 规定"其它 `error` / `failed` 事件不得忽略，也**不自动判整次派发失败**"，要求逐条查看后续恢复；豁免表（:161-165）不含 `turn.failed`，故它属于"其它 error / failed 事件"。:191 同时规定"`turn.failed` 或缺少 completion evidence 属派发失败"。
- **预期行为**: 同一事件类别在通用条款与 JSONL 专条之间不应字面冲突；应显式说明 turn 级终态事件（`turn.completed` / `turn.failed`）不适用 :167 的逐条可恢复裁决，只有 item 级事件适用。
- **实际行为**: 按 :167 字面，总控应对 `turn.failed`"查看后续恢复和最终结论"并可记为已解释 warning；按 :191 字面，它直接是派发失败。虽然 :191 后半句（"普通工具失败按上述影响判定"）隐含了 item 级 vs turn 级的分界，解决了实际歧义，但契约文本没有把这个分界写出来，依赖读者用"特别法优于普通法"自行调和。
- **直接证据**: :167"其它 error / failed 事件……不自动判整次派发失败"；:190-191"`turn.failed` 或缺少 completion evidence 属派发失败，普通工具失败按上述影响判定"；豁免表 :161-165 无 `turn.failed` 条目。
- **影响**: 低——意图可从 :191 后半句恢复，但逐字执行协议的总控会在"是否把 turn.failed 写入逐条恢复裁决清单"上产生分叉行为。
- **建议改法和验证点**: 在 :167 开头加限定："本节'其它 error / failed 事件'指 item 级事件；turn 级终态事件按 Codex JSONL 专条（`turn.completed` / `turn.failed`）判定"。验证点：以含 `turn.failed` 的样例 JSONL 走查两条规则，确认结论唯一。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 低

### 05-未修复-[低]-Result Validation 开头"本节上述"是悬空引用
- **入口/函数**: 读者按 `## Result Validation` 定位托管调用句柄的描述（skills/sub-agents/SKILL.md:138）。
- **文件(行号)**: skills/sub-agents/SKILL.md:138；被引用内容实际位于 :122-134。
- **输入场景**: 任何按节查阅协议的总控/读者。
- **实际分支**: :138"沙箱内以本节上述托管调用句柄收集退出状态"。托管句柄机制的完整描述在 `### Sandbox Process Management`（:122-134），该小节隶属 `## Execution And Isolation`（:68），不在 `## Result Validation`（:136 起）之内。
- **预期行为**: 节内引用（"本节上述"）应指向同一节内的前文；跨节引用应写节名。
- **实际行为**: `## Result Validation` 节内 :138 之前没有任何关于托管句柄的文字，引用悬空。所幸同句自举列举了三种句柄（Claude 后台任务完成通知、Codex `exec_command` / `write_stdin` 退出码、前台直接返回），实际影响被稀释。
- **直接证据**: :136 节标题、:138 引用语、:122-134 实际描述位置。
- **影响**: 低——文档准确性缺陷；在后续编辑中若删除同句的自举列举，悬空引用会变成实质信息丢失。
- **建议改法和验证点**: 改为"沙箱内以 Sandbox Process Management 一节所述托管调用句柄收集退出状态"。验证点：grep 确认节名与引用一致。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 低

### 06-未修复-[低]-影响未定的失败事件同时命中"停在 gate"与"可重试"两条规则，优先级靠意图区分
- **入口/函数**: 总控裁决失败事件后的下一步动作选择（skills/sub-agents/SKILL.md:174 vs :206-208）。
- **文件(行号)**: skills/sub-agents/SKILL.md:174 与 :206-208。
- **输入场景**: 某失败事件的影响无法确定（:174 的前提），同时该状态也属于 :206 的"派发或结果验收失败后"（:177 把"未恢复的关键工具失败"定义为结果验收失败）。
- **实际分支**: :174 要求"标记未解决并停在当前 gate；不得为了凑齐通过结果而换路由或重试"；:206-208 允许"确需重派时……一次有明确理由的同 provider 重试"。同一触发状态命中两条规则，文本未声明优先级；唯一的区分是重试意图（"凑通过结果" vs "确需"），而意图恰是 LLM 总控最难自证、最易自我合理化的判据。
- **预期行为**: 应给出客观次序：例如"影响未定的失败事件必须先标记未解决并停 gate；只有在总控能把影响判定为'与必要证据无关'或'可经重派重取'之后，才进入 :206 的重试分类"。
- **实际行为**: 总控可把 :174 的未解决状态直接包装成 :207 的"有明确理由的重试"，绕开停 gate 义务；协议无法事后区分这是合规重派还是违规凑结果。
- **直接证据**: :174 与 :206-208 的触发条件重叠（:177 的结果验收失败定义覆盖"未恢复的关键工具失败"），两条规则均无条件优先级语句。
- **影响**: 低——两条规则各自的意图都清楚，重叠区的滥用需要总控主动合理化；但协议的价值恰在于不给这种合理化留空间。
- **建议改法和验证点**: 在 :174 末尾补"重试仅在对事件影响作出肯定判定后允许；影响未定时禁止以重试替代裁决"。验证点：构造影响未定样例，确认按新条款唯一合法动作是停 gate。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 低

## Open Questions

- :249 要求报告列出"每条非豁免失败事件的编号"——"编号"的来源未定义：JSONL 行号、event 序号还是总控自赋序号？不同选择影响报告间的可比对性。
- "用户停止"一次派发后，`agent_status` 应写 `blocked` 还是 `failed`？枚举无 `stopped`，契约未给映射（与 finding 01 相关但独立：即使修复 stalled 判据，用户停止的落键仍无规定）。
- 非验证类派发（canary_status=not_run）被判 `result_status=accepted` 时，验收完全落在总控独立复核上（:177-178、:225-226），但报告契约未要求记录复核范围（实际打开了哪些文件、重跑了哪些命令）。下游无法区分"复核过的采纳"与"形式采纳"。

## Residual Risk

- 本 review 的静态事实（diff 全文、行号、跨文件检索）已核实，但未实际运行 preflight / runner 复现 event 名称；`turn.completed` / `turn.failed` 与既有裁决文档对真实运行的记录一致（docs/reviews/reasoning-history-adjudication-20260925.md:20），未见反证。
- `tool_evidence` 的 Codex 判据（:145、:233）只要求"存在"一条 `exit_code=0` 的 `command_execution`——一条无关的成功命令即可满足，不证明任务要求的工具成功。该弱点先于本 diff 存在，diff 的 `result_status` 轴（:235）与 :194 的 Claude 汇总告诫只做了部分缓解，未在键级收紧。
- :170-171"已成功改用其它证据的失败"的谓词宽于其示例（探索性无匹配、预期反例）：替代证据是否足以支撑任务要求的证明，靠总控说明理由（:171）兜底，无客观判据。属已知软化，未单列为 finding。
- 未读取 MiMo 同轮审核产物（任务禁止），两路结论是否冲突未知，需总控在汇合时核对。
- 对照文件（runner、preflight、README、phaseflow/gateflow）只为契约一致性而读，未做全量 review；其中可能存在的独立缺陷不在本报告范围。

## 结论与验证

结论：改动方向（生命周期与结果可信度两轴分离、逐条裁决失败事件、收紧退出证据与重试授权）整体成立，豁免表、canary、preflight 报告协议与安全边界（权限继承、禁 `bypassPermissions`、sandbox 条款）未被削弱，部分条款（:174、:208 末句）是实质性收紧。但改动引入 1 个高严重度缺陷（finding 01：挂死派发无合规结束路径、`blocked` 枚举孤儿化——这是对旧文本"阻塞"出口的回退）、2 个中严重度契约缺口（finding 02：provider 切换授权引用不存在的"上层路由规则"；finding 03：新裁决块缺跨键一致性约束）与 3 个低严重度文本缺陷。**在 finding 01-03 修复前不建议合入。**

验证（本报告已执行的检查）：

- `git status` / `git diff main...HEAD` / `git merge-base main HEAD`：确认审查输入为工作区未提交改动（HEAD=a827aff=merge-base，分支无已提交内容），diff +35/-16 已全文读取。
- `scripts/sub-agent-preflight` 全读：确认其拼入的固定报告协议（RUNTIME/PROVIDER/MODEL 行、CANARY 逐字回读、停止条件，:196-198）与 SKILL.md Dispatch Contract（:58）一致；canary token 不进 prompt、无尾换行（:156-161）与 :150-154 一致；预检八项与手工预检清单对应。
- `scripts/codex-agent-run` 全读：确认 `--output-format json` 透传 `codex exec --json` 事件流（:419），runner 退出码经 last-message 保存逻辑透传（:442-460），与 :139-141 的"外层退出码 + 结构化终态双核对"兼容。
- 全仓 `grep`：`上层路由|路由规则` 仅命中 :208（finding 02）；`turn.completed|turn.failed` 在 docs 实证记录中存在、tests 无覆盖；其它 skill 不消费裁决块键（`result_status` 等），无跨 skill 键级漂移。
- canary 文件 `/private/var/folders/.../sub-agents.AlFrdN/canary.txt` 已用工具读取，内容逐字为 `kimi-b60fb7f5`（无尾换行），见本报告头部 CANARY 行。
- 安全边界逐段核对：diff 未触碰权限/沙箱/canary/preflight 条款；:208"本 skill 不扩大替补路由授权"与 :66"不得通过宽权限扩张用户授权或任务 scope"一致。
- 任务边界遵守：未派发子 Agent；除本 artifact 外未修改任何文件；未 stage/commit/push/PR；未读取 MiMo 同轮产物。
