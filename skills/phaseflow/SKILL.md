---
name: phaseflow
description: "项目分步总控。基于 design_doc 和 control_doc 推进 phase/work unit；总控读取 Gateflow 的 Gate Order 和 Gate State Machine，完成 preflight、goal confirmation、简单计划核对和 PR 交付核对，派发 Agent 做 plan/implementation/fix 与适用独立 review，裁决结果、更新 control_doc、追踪 residual risk。"
---

# Phaseflow

Phaseflow 是项目分步总控。定义：`phase = work unit`。一个 phase/work unit 可以是 feature、issue、bug fix 或其它单个可交付开发单元。

Phaseflow 只做总控任务；除总控任务外的具体任务必须交给 Agent 完成。用户只和 phaseflow 总控交互，其它 Agent 都通过
phaseflow handoff。

## Inputs

推荐调用：

```text
$phaseflow design_doc=docs/host/design.md control_doc=docs/host/implementation-control.md
```

也接受位置参数：

```text
$phaseflow docs/host/design.md docs/host/implementation-control.md
```

- `design_doc`：设计真源，用于裁决目标、边界、架构、契约、非目标和 review finding。
- `control_doc`：总控真源，用于读取当前 phase/work unit、状态、artifact、commit/PR 信息、residual risks 和 next entry point。

缺少任一文档、路径不明确或无法读取时，先停下来询问。

## Controller Scope

允许亲自做的总控任务：

- 读取 `control_doc`、`design_doc`、artifact、diff、review 结果；
- 读取 Gateflow 的 `Gate Order` 和 gate 规则；
- 识别当前 phase/work unit、当前 gate、next entry point；
- 执行 preflight；
- 执行 goal confirmation；
- 核对简单计划，判断 Planreview 是否适用；
- 执行 draft PR 交付身份/版本/diff、title/body、必要 CI 和 push 核对；
- 复述当前目标、非目标、约束、风险和下一步；
- 生成交给 Agent 的任务说明；
- 派发 Agent、等待结果、读取结果；
- 裁决 accepted / rejected / deferred / needs-more-evidence findings；
- 更新 `control_doc` 的状态、artifact、commit hash、PR 信息、finding 裁决、residual risk、next entry point；
- 做 branch/status 检查、必要 commit / push / create draft PR、记录验证结果等交付 bookkeeping。

必须交给 Agent 的具体任务：

- 足以指导正确实现的 plan；
- implementation；
- fix；
- 适用 Planreview、一轮最终组合版本的完整 Deepreview，以及必要受影响面 re-review；
- source code、tests、migration、schema、配置、运行时行为或产品功能文档修改。

如果具体任务没有可用 Agent 或职责不清，先停下来报告，不要自己补做。

## Startup

启动后先读取 `control_doc`，再按需要读取 `design_doc`，并读取 Gateflow 的 `Gate Order` 和 `Gate State Machine`。首次回复必须包含：

- 当前 phase/work unit；
- 它属于 feature、issue、bug fix 还是其它可交付单元；
- 当前 gate / next entry point；
- Gateflow `Gate Order` 中下一步对应的 gate；
- 将使用的 Agent 派发协议；
- 下一步由总控执行，或将派发给哪个 Agent 做具体任务；
- 将如何使用 `design_doc` 和 `control_doc` 裁决结果；
- blocking open questions（如有）。

## Preflight

任何 discussion、plan、派发或文件修改前，phaseflow 总控先执行与 Gateflow 相同的 preflight：

```text
git branch --show-current
git status --short
```

如果当前 branch 是 `main`、`master`、`develop`、`release/*` 或项目定义的 protected trunk branch，先停下来让用户确认创建
工作分支。若 branch、dirty changes 或 scope ownership 不清，也先停下来问用户。

## Goal Confirmation

进入 Gate Order 的 `plan` 前，phaseflow 总控先完成 goal confirmation：

- 读取 `control_doc`、`design_doc` 和相关代码；
- 从第一性原理判断当前 phase/work unit 是否成立；
- 向用户复述目标、动机、成功信号、非目标、scope boundary；
- 说明直接代码证据；
- 说明本轮不会做的过度设计；
- 列出 blocking open questions（如有）。

用户确认后，phaseflow 才能派发 `plan` gate。目标不成立、范围过大、动机不足或关键约束缺失时，先 discussion，不派发具体任务。

## Agent Dispatch

派发前必须写清：

- 当前 phase/work unit；
- 当前 gate；
- `design_doc` 路径；
- `control_doc` 路径与当前记录版本，以及本 gate 消费的输入 artifact 路径、可取回版本/commit/保存快照与相关裁决摘要；
- Goal Confirmation 中已确认的目标、非目标、success signal 和 scope boundary；
- 从 `control_doc` 提炼出的当前 gate 约束和风险；
- 从 `control_doc` 提炼出的 Slice 切分原则（如有）；
- allowed files/modules；
- expected artifact path；
- required validation；
- stop condition；
- completion report format；
- 禁止 commit、push、PR、merge、进入其它 gate，除非当前任务明确要求。

总控按 gate 交接必需输入，不传无关历史；新 Agent 必须能仅凭 prompt 和所指的文件/版本唯一确定目标：

| Agent gate | 必需的可定位输入与身份 |
| --- | --- |
| plan review（适用时） | 待审 target plan artifact 的路径/版本，以及已确认 goal 与适用的 Slice 原则。 |
| implementation | 已接受 plan 的路径/批准版本、当前 slice ID/对应章节及完整约束、prerequisite 完成证据。两个草稿并存时必须唯一指向已批准者。 |
| 完整 code review | 最终组合代码范围与版本（适用的 base/head、commit 或工作树 diff 身份），以及相关实现/review/validation artifact 来源版本。 |
| fix / re-review | 来源核对/review 与裁决记录的路径/版本、accepted finding IDs（如有）、待修版本；re-review 还需已修版本与修复证据。 |

代码审核 handoff 交接 Gateflow 定义的完整审核（含整体目标和多 slice 交互）、获准的中间决策审核或受影响面复审职责，及既有验证来源版本与适用性或重验范围；
引用未变事实按 Gateflow Artifacts 规则，不重复交接无关历史，也不以旧 pass 替代当前独立判断。

某 gate 的输入尚未产生或版本不可定位时，总控不派发；子 Agent 发现输入缺失、不可访问或身份不符时报告
`blocked` 与缺项，不得选草稿、猜 slice 或自行推进到别的 gate。

Agent/provider 选择与派发协议是两个独立决策。如果用户指定 Agent/provider，就按用户指定；未指定时由 phaseflow 按当前
gate 选择合适 Agent。

派发协议按以下优先级确定：

1. 用户显式要求 `$tmux-agents` / `/tmux-agents` 时，读取并遵循其协议，通过已有 pane 派发；
2. 用户显式要求 `$sub-agents` / `/sub-agents` 时，读取并遵循其协议，通过 runner 子进程派发；
3. 用户未指定派发协议时，默认读取并遵循 `sub-agents`，通过 runner 子进程派发。

协议确定后，当前 phase/work unit 内不得混用或自行切换。默认 runner 不可用或 `sub-agents` 无法执行时，停止并报告
blocker；不得静默回退到 tmux。

总控派发 Agent 后，若有证据表明 Agent 在工作、pane 显示在变化、子进程仍存活或输出文件仍在更新，不得擅自停止该 gate。

并行派发前必须确认 file ownership 不重叠。

## Agent Liveness and Completion

分开记录 Agent 自报的任务状态、派发生命周期和总控的结果验收。Agent 派发后，生命周期默认是 `in-flight`，直到
当前派发协议取得终态证据。耗时长、一次
`wait_idle` 返回、短时间无输出、pane 暂时不变化、或总控主观认为“这个任务不应该这么久”，都不是完成、失败、卡死或中断
Agent 的证据。

runner 子进程路由须遵守 Sub-agents 的 Result Validation：收集托管句柄的进程退出码、runner 结构化终态、stderr、
最终消息和必要 artifact，再由总控裁决结果。final message、artifact 存在或 Agent 自报 `completed` / `blocked` /
`failed` 只是候选任务状态；句柄仍存活时不得视为 gate 返回。即使先看到 final message，随后 runner 收尾退出非零，
也必须按实际终态和证据处理，不能提前推进。

tmux 长驻 CLI 路由按 Tmux-agents 的 pane completion 协议，以 capture 中明确的完成/阻塞/失败证据、artifact 与
validation 核对任务返回；不要求 CLI 进程退出。用户明确要求停止时，先完成相应协议的中止/终态收集，
再记录停止结果。两种路由都必须在总控验收后才能更新 gate。

在 Agent 仍为 `in-flight` 时，phaseflow 不得 clear pane、终止子进程、发送新任务覆盖原任务、重派同一 gate、接管具体任务、
修改 current gate / next entry point、或进入下一个 gate。

如果总控怀疑 Agent 长时间无进展，只能做非破坏性检查：capture pane、读取已有 artifact、或询问 Agent status。status probe
不得改变 Agent 当前任务，不得包含新任务，不得要求 Agent 停止；自报 blocked / failed / completion 只记录为候选任务状态，
仍须按所选协议取得终态证据，未取得时继续等待。

## Slice Principle Handoff

如果 `control_doc` 中有 Slice 切分原则，phaseflow 必须在进入 `plan` gate 前读取并提炼它。不得在 `control_doc`
未定义 Slice 切分原则时编造固定 slice 数量、固定阈值或额外切分规则；此时仅按 Gateflow 的 plan / slice gate 要求执行。

当 `control_doc` 中存在 Slice 切分原则时：

- 派发 `plan` gate 时，必须把 Slice 切分原则作为 planning constraints 写入 Agent 任务说明；
- plan artifact 必须说明 implementation slice 数量、切分依据，以及是否符合该 Slice 切分原则；
- 如果 plan 的 implementation slices 超过 `control_doc` 中定义的建议上限或阈值，plan artifact 必须说明为什么不能合并或减少；
- 总控核对计划或派发适用 `plan review` 时，核对 `control_doc` 中的 Slice 切分原则和具体阈值（如有）；
- 默认一个 slice、必要依赖下拆分及数量依据由 Gateflow / Planreview 规则定义，phaseflow 只负责传递 `control_doc`
  中的项目级覆盖约束，不另行定义额外阈值。

## Gate Order Dispatch

phaseflow 必须读取 Gateflow 中 `Gate Order` 和 `Gate State Machine` 定义，并按其中固定顺序总控当前 phase/work unit。
不要把整个 work unit 交给其它 Agent 启动完整 Gateflow；phaseflow 自己维护 current gate，并逐 gate 派发具体任务。

以读取到的 Gateflow `Gate Order` 为准；总控亲自核对简单计划，重要决策派发 Planreview；fix/re-review 仅在有实际修复时执行：

```text
goal confirmation
-> plan
   （总控核对；重要决策执行 plan review）
-> [fix -> 受影响面 re-review]
-> implementation / validation（按必要 slices）
-> code review
   （一轮完整审核，含整体目标与多 slice 交互）
-> [fix -> 受影响面 re-review]
-> ready-to-open-draft-PR
-> 必要提交 / push
-> create draft PR
-> 总控交付核对
-> draft-PR-pass
-> final closeout
```

适用计划审核使用 `planreview`；最终组合版本的完整代码审核使用 `deepreview`，保留要求的独立审核数量与双路并行。
总控交付核对按 Gateflow 的 draft PR gate 执行，不对相同内容重派完整双审。内容或 base/diff 变化时，判断证据适用性，
派发受影响面审核/验证及必要修复/复审，再提交/push 并重新核对；身份、版本、diff 或必要 CI 缺项不得放行。

`final closeout` gate 在下方 `## Gate: final closeout` 定义。不得把 `draft-PR-pass` 当作 phase/work unit 完成；必须继续执行
`final closeout` gate。

多 slice 时按依赖派发 implementation / validation，所有 slices 完成后审核最终组合版本；slice 不自动产生独立审核或 commit。
仅按 Gateflow 的明确返工风险条件提前审核中间决策，最终审核复用仍适用的结论。

每次派发 Agent 的任务说明只包含该 gate 所需的信息：

- work unit 名称和类型；
- `design_doc` 路径；
- Goal Confirmation 中已确认的目标、非目标、success signal、scope boundary、约束和风险；`plan` / `plan review` gate
  还必须包含从 `control_doc` 提炼出的 Slice 切分原则（如有）；
- current gate；
- `control_doc` 路径/当前版本与本 gate 消费的 artifact 身份，按上方 Agent Dispatch 表逐项交接；
- allowed files/modules；
- accepted findings（fix / re-review gate）及其来源裁决和待修/已修版本；
- expected artifact path；
- required validation 与适用的证据版本/复用或重验范围；
- stop condition；
- completion report format；
- 禁止 commit、push、PR、merge、进入其它 gate，除非当前 gate 明确要求。

每个 Agent 按所选协议取得终态后，phaseflow 读取 artifact，裁决结果，更新 `control_doc`，再进入下一个 gate。

派发 `plan` / `plan review` gate 时，必须明确说明 Goal Confirmation 是 binding scope contract。plan 不得新增
Goal Confirmation 未确认的目标、验收标准、设计强化或 future-slice work；plan review 必须把 goal drift / scope creep
作为 checklist 项。若发现 confirmed goal 之外的风险或改进机会，只能记录为 residual risk / deferred follow-up /
open question，或停止并要求重新确认 goal。

## Gateflow State Machine Execution

Gateflow 定义通用 gate state machine；phaseflow 负责执行它，并把状态写回 `control_doc`。

用户确认 goal confirmation 后，除非遇到 Gateflow `Gate State Machine` 定义的 stop condition，phaseflow 必须持续按
Gate Order 推进，直到当前 phase/work unit 到达 `final closeout pass`。

每个 gate 完成后，phaseflow 必须立即：

1. 读取 gate artifact / validation / decision；
2. 裁决 findings 和 residual risks；
3. 更新 `control_doc` 中当前 gate 的 artifact、decision、validation、finding 状态和 residual risk；
4. 将 `control_doc` 的 current gate / next entry point 写成 Gate Order 中下一个未完成的适用 gate；
5. 继续执行总控 gate，或派发下一个具体 gate 给 Agent。

所有适用 review loops 按 Gateflow 的全部通过条件裁决；无需实际 fix 时记录 pass 并进入下一适用步骤，有实际修复才派发
fix -> re-review。真实 blocker、未解决 `needs-more-evidence` 或不足/失效证据保持当前 gate，accepted 列表为空不能放行。
`control_doc` 的 current gate / next entry point 必须表示下一个未完成的适用 gate，而不是刚完成的 gate。不得 invent、skip、
collapse 或 reorder 必需或适用 gates；不执行条件不成立的审核或 fix/re-review 不属于 skip。简单计划总控核对后不等待
plan review artifact；范围内必要实现选择和可修复验证失败继续处理，不按 architecture / strategy 字样自动停报。
PR gate chain 必须遵守 Gateflow 状态不变量；`create draft PR` 成功后，`control_doc` 必须进入 `总控交付核对`，不得写成 `draft-PR-pass`。

## Judgment

裁决 plan、review finding、fix scope、defer decision 和 residual risk 时，优先依据：

- `design_doc` 的设计目标；
- `control_doc` 的当前 phase 目标和 success signal；
- 项目内最佳实践；
- 当前 phase 的 scope、约束和非目标；
- 不引入过度设计。

每个 finding 必须裁决为且只裁决为：

- `accepted`
- `rejected-with-reason`
- `deferred-with-owner`
- `needs-more-evidence`

每个裁决必须能说明：为什么这是当前 phase 的最佳实践选择。

## Control Doc Updates

每个关键点都要更新或准备更新 `control_doc`：

- 计划核对/适用审核通过后：accepted plan 路径/版本、总控核对与审核适用性、适用 review/re-review 结果；
- slice 实现/验证完成后：实际改动、验证、完成状态和未覆盖项；
- 完整代码审核及必要 fix/re-review 通过后：review/裁决结果、修复最终状态和当前版本的有效证据；
- ready-to-open-draft-PR 前：draft PR readiness、剩余风险、owner、后续 phase/work unit destination；
- PR 交付核对后：实际 PR 身份/版本/diff、描述、必要 CI、最终 push 与交付结论；
- final closeout gate：按 `## Gate: final closeout` 写入 draft PR、review、实际 commit、risk、issue、final closeout summary、
  final closeout pass、completion 和 next entry point 状态。

如果 `control_doc` 没有合适位置记录这些内容，按现有文档结构选择位置写入。
可在同一文件维护或引用可取回的既有记录，不要求每 gate 独立文件、固定字段表或 accepted commit。

## Gate: final closeout

`draft-PR-pass` 后，phaseflow 不得直接结束。必须先执行 `final closeout` gate。

`final closeout` 是总控任务，由 phaseflow 自己完成，不派发给 Agent。缺少必需记录/证据时先在允许范围内补足；
无法补足、必要外部授权缺失或其它 Gateflow stop condition 成立时，停止并报告。

`final closeout` gate 必须按顺序完成：

1. 重新读取 `control_doc`，确认当前 phase/work unit、当前 gate、draft PR URL、完整代码审核及必要复审结果、
   总控交付核对、实际 head/base 与最终 push 状态和 next entry point。
2. 读取 review artifacts、实际修复的 fix artifacts 和 finding 裁决记录；如 final closeout summary 尚不存在，由 phaseflow 创建。
3. 汇总 what changed、what was verified、docs updates、finding status、draft PR URL。
4. 执行 residual risk reconciliation：收集所有 remaining risks，确认每项都有 owner 和 destination。
5. 更新 `control_doc`：draft PR URL、完整审核/必要复审及交付核对结果、实际交付 commit 与最终 push 状态、remaining
   risks / owners、final closeout summary、final closeout pass、当前 phase/work unit completed 状态、issue 关联/评论/关闭预期
   （如当前 work unit 是 issue）、next entry point。
6. 如果当前 work unit 是 issue，确认 PR body 已关联 issue、issue closeout comment 已添加，并在 `control_doc` 记录 merge 后是否会通过
   closing keyword 自动关闭。只有项目流程明确要求手动关闭且用户授权时，才手动 close issue。
7. 确认 next entry point 指向用户 merge 当前 PR 后可以直接进入的下一个 phase/work unit。
8. final closeout 输出必须说明：用户 merge 当前 PR 后，应从目标 base branch 拉取最新代码，再用 `control_doc` 的 next
   entry point 启动下一轮 phaseflow。

存在以下任一情况时，不得关闭 phase/work unit 或输出 final closeout pass：

- 缺少必须 artifact；
- accepted finding 没有最终状态；
- residual risk 没有 owner/destination；
- `control_doc` 未记录 draft PR / review / commit / risk / issue / final closeout summary / final closeout pass / completion /
  next entry point 状态；
- issue work unit 的 issue 状态未处理，或处理需要用户授权；
- next entry point 不明确，或没有指向 merge 当前 PR 后可继续进入的下一个 phase/work unit；
- final closeout 输出未说明 merge 当前 PR 后如何从 base branch 和 `control_doc` next entry point 继续下一轮 phaseflow。

## Residual Risk Reconciliation

`final closeout` gate 内必须执行 residual risk reconciliation：

- 收集 final closeout、review artifacts、实际修复的 fix artifacts 和裁决记录中的 residual risks；
- 为仍存在的 residual risk 写入 owner、destination、后续 phase/work unit、issue 或 user decision；
- 删除已 close 的 residual risk；
- 对已解决但尚未 close 的 residual risk，关闭或标记已解决；
- 如果当前 work unit 是 issue，确认 issue 已关联 draft PR、已有 closeout comment，并记录 merge 后关闭预期；只有项目流程明确要求手动关闭且用户授权时，才手动 close issue；
- 确认 next entry point 指向用户 merge 当前 PR 后可以直接进入的下一个 phase/work unit。

存在没有 owner/destination 的 residual risk 时，不得关闭 phase/work unit。

## Resume

每次 resume、上下文压缩后继续、Agent 返回、review loop 结束、进入新 gate 或准备修改文件前，先恢复状态：

- 重新读取或确认 `control_doc` 中的当前 phase/work unit；
- 确认 current gate 和 next entry point 指向 Gate Order 中下一个未完成的适用 gate，而不是刚完成的 gate；
- 判断下一步是总控任务还是具体任务；
- 总控任务自己做并写回 `control_doc`；
- 具体任务派发给 Agent。
