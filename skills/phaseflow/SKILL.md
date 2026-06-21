---
name: phaseflow
description: "项目分步总控。基于 design_doc 和 control_doc 推进 phase/work unit；phase = work unit，每个 phase 可是 feature、issue 或 bug fix；总控读取 Gateflow 的 Gate Order 和 Gate State Machine，自己完成 preflight 和 goal confirmation，然后按固定 gate 顺序派发 Agent 完成具体 plan/implementation/review/fix，裁决结果、更新 control_doc、追踪 residual risk。"
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
- 复述当前目标、非目标、约束、风险和下一步；
- 生成交给 Agent 的任务说明；
- 派发 Agent、等待结果、读取结果；
- 裁决 accepted / rejected / deferred / needs-more-evidence findings；
- 更新 `control_doc` 的状态、artifact、commit hash、PR 信息、finding 裁决、residual risk、next entry point；
- 做 branch/status 检查、创建 accepted local commit、记录验证结果等 gate bookkeeping。

必须交给 Agent 的具体任务：

- code-generation-ready plan；
- implementation；
- fix；
- review / re-review；
- aggregate deepreview；
- PR review / re-review；
- source code、tests、migration、schema、配置、运行时行为或产品功能文档修改。

如果具体任务没有可用 Agent 或职责不清，先停下来报告，不要自己补做。

## Startup

启动后先读取 `control_doc`，再按需要读取 `design_doc`，并读取 Gateflow 的 `Gate Order` 和 `Gate State Machine`。首次回复必须包含：

- 当前 phase/work unit；
- 它属于 feature、issue、bug fix 还是其它可交付单元；
- 当前 gate / next entry point；
- Gateflow `Gate Order` 中下一步对应的 gate；
- 将派发给哪个 Agent 做下一步具体任务；
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
- 目标、非目标、scope boundary；
- 从 `control_doc` 提炼出的当前 gate 约束和风险；
- 从 `control_doc` 提炼出的 Slice 切分原则（如有）；
- allowed files/modules；
- expected artifact path；
- required validation；
- stop condition；
- completion report format；
- 禁止 commit、push、PR、merge、进入其它 gate，除非当前任务明确要求。

如果用户指定 Agent，就按用户指定。若用户要求使用 `$init-agents` / `/init-agents`，按其通信规则确认 pane、clear、send、wait、capture。

总控派发 Agent 后，若有证据表明 Agent 在工作、或 Agent 所在的 pane 的显示在变化，不得擅自停止该 gate。

并行派发前必须确认 file ownership 不重叠。

## Slice Principle Handoff

如果 `control_doc` 中有 Slice 切分原则，phaseflow 必须在进入 `plan` gate 前读取并提炼它。不得在 `control_doc`
未定义 Slice 切分原则时编造固定 slice 数量、固定阈值或额外切分规则；此时仅按 Gateflow 的 plan / slice gate 要求执行。

当 `control_doc` 中存在 Slice 切分原则时：

- 派发 `plan` gate 时，必须把 Slice 切分原则作为 planning constraints 写入 Agent 任务说明；
- plan artifact 必须说明 implementation slice 数量、切分依据，以及是否符合该 Slice 切分原则；
- 如果 plan 的 implementation slices 超过 `control_doc` 中定义的建议上限或阈值（例如 3 个），plan artifact 必须说明为什么不能合并或减少；
- 派发 `plan review` gate 时，必须要求 reviewer 审查是否存在按模块 / 文件 / owner 机械拆分、slice 过多、gate 成本超过实现风险、或违反 `control_doc` Slice 切分原则的问题；
- 如果 `control_doc` 定义了具体阈值（例如超过 3 个 slices），plan review handoff 必须把该阈值列为 checklist 项。

## Gate Order Dispatch

phaseflow 必须读取 Gateflow 中 `Gate Order` 和 `Gate State Machine` 定义，并按其中固定顺序总控当前 phase/work unit。
不要把整个 work unit 交给其它 Agent 启动完整 Gateflow；phaseflow 自己维护 current gate，并逐 gate 派发具体任务。

以读取到的 Gateflow `Gate Order` 为准；当前定义为：

```text
goal confirmation
-> plan
-> plan review
-> fix
-> re-review
-> accepted plan commit
-> implementation
-> code review
-> fix
-> re-review
-> accepted slice commit
-> aggregate deepreview
-> fix
-> re-review
-> accepted deepreview commit
-> ready-to-open-draft-PR
-> push
-> create draft PR
-> PR review
-> fix
-> re-review
-> accepted PR review commit
-> push
-> draft-PR-pass
-> final closeout
```

`plan review` gate 必须使用 `planreview` skill；`code review`、`aggregate deepreview` 和 `PR review` gates 必须使用 `deepreview` skill。

`final closeout` gate 在下方 `## Gate: final closeout` 定义。不得把 `draft-PR-pass` 当作 phase/work unit 完成；必须继续执行
`final closeout` gate。

多 slice 时重复：

```text
implementation -> code review -> fix -> re-review -> accepted slice commit
```

每次派发 Agent 的任务说明只包含该 gate 所需的信息：

- work unit 名称和类型；
- `design_doc` 路径；
- 目标、非目标、success signal、约束和风险；`plan` / `plan review` gate 还必须包含从 `control_doc` 提炼出的 Slice 切分原则（如有）；
- current gate；
- allowed files/modules；
- accepted findings（fix / re-review gate）；
- expected artifact path；
- required validation；
- stop condition；
- completion report format；
- 禁止 commit、push、PR、merge、进入其它 gate，除非当前 gate 明确要求。

每个 Agent 返回后，phaseflow 读取 artifact，裁决结果，更新 `control_doc`，再进入下一个 gate。

## Gateflow State Machine Execution

Gateflow 定义通用 gate state machine；phaseflow 负责执行它，并把状态写回 `control_doc`。

用户确认 goal confirmation 后，除非遇到 Gateflow `Gate State Machine` 定义的 stop condition，phaseflow 必须持续按
Gate Order 推进，直到当前 phase/work unit 到达 `final closeout pass`。

每个 gate 完成后，phaseflow 必须立即：

1. 读取 gate artifact / validation / decision；
2. 裁决 findings 和 residual risks；
3. 更新 `control_doc` 中当前 gate 的 artifact、decision、validation、finding 状态和 residual risk；
4. 将 `control_doc` 的 current gate / next entry point 写成 Gate Order 中下一个未完成 gate；
5. 继续执行总控 gate，或派发下一个具体 gate 给 Agent。

`control_doc` 的 current gate / next entry point 必须表示下一个未完成 gate，而不是刚完成的 gate。不得 invent、skip、
collapse 或 reorder gates。PR gate chain 必须遵守 Gateflow `Gate State Machine` 的状态不变量；`create draft PR`
成功后，`control_doc` 必须进入 `PR review`，不得写成 `draft-PR-pass`。

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

- plan/re-review 通过后：plan artifact、plan review artifacts、accepted plan commit hash；
- 每个 slice commit 后：slice 状态、artifact、review 结论、commit hash、未覆盖项；
- aggregate deepreview/re-review 通过后：aggregate review artifact、accepted deepreview commit hash；
- ready-to-open-draft-PR 前：draft PR readiness、剩余风险、owner、后续 phase/work unit destination；
- final closeout gate：按 `## Gate: final closeout` 写入 draft PR、review、commit、risk、issue、final closeout summary、
  final closeout pass、completion 和 next entry point 状态。

如果 `control_doc` 没有合适位置记录这些内容，先提出具体写入位置或结构。

## Gate: final closeout

`draft-PR-pass` 后，phaseflow 不得直接结束。必须先执行 `final closeout` gate。

`final closeout` 是总控任务，由 phaseflow 自己完成，不派发给 Agent。缺少必须 artifact、issue 状态需要外部授权，或
`control_doc` 没有合适位置记录结果时，停止并询问用户。

`final closeout` gate 必须按顺序完成：

1. 重新读取 `control_doc`，确认当前 phase/work unit、当前 gate、draft PR URL、PR review artifacts、accepted PR review
   commit hash、follow-up push 状态和 next entry point。
2. 读取 review artifacts、fix artifacts 和 finding 裁决记录；如 final closeout summary 尚不存在，由 phaseflow 创建。
3. 汇总 what changed、what was verified、docs updates、finding status、draft PR URL。
4. 执行 residual risk reconciliation：收集所有 remaining risks，确认每项都有 owner 和 destination。
5. 更新 `control_doc`：draft PR URL、PR review artifacts、accepted PR review commit hash、follow-up push 状态、remaining
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

- 收集 final closeout、review artifacts、fix artifacts 和裁决记录中的 residual risks；
- 为仍存在的 residual risk 写入 owner、destination、后续 phase/work unit、issue 或 user decision；
- 删除已 close 的 residual risk；
- 对已解决但尚未 close 的 residual risk，关闭或标记已解决；
- 如果当前 work unit 是 issue，确认 issue 已关联 draft PR、已有 closeout comment，并记录 merge 后关闭预期；只有项目流程明确要求手动关闭且用户授权时，才手动 close issue；
- 确认 next entry point 指向用户 merge 当前 PR 后可以直接进入的下一个 phase/work unit。

存在没有 owner/destination 的 residual risk 时，不得关闭 phase/work unit。

## Resume

每次 resume、上下文压缩后继续、Agent 返回、review loop 结束、进入新 gate 或准备修改文件前，先恢复状态：

- 重新读取或确认 `control_doc` 中的当前 phase/work unit；
- 确认 current gate 和 next entry point 指向 Gate Order 中下一个未完成 gate，而不是刚完成的 gate；
- 判断下一步是总控任务还是具体任务；
- 总控任务自己做并写回 `control_doc`；
- 具体任务派发给 Agent。
