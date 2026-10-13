# Gateflow / Planreview 简化计划

依据：本目录 `control.md` 的已确认目标、完整讨论源 `/Users/leo/workspace/portfolio-manager-v2/orch/workpapers/run-monitor-tencent-20261010/gateflow-optimization-pending-20261013.md`，以及当前仓库文本。分支 `feat/gateflow-planreview-simplification`，基线 `501599da155c77d456d661b2e0f941b86ddecec7`。

目标是减少重复审核和记录开销，使计划足以指导已确认目标的正确实现，同时保留缺陷及已证实结构性问题的根因解决、重要决策审核、完整组合版本审核与目标确认后的自动推进。本任务按 control 中已授权的例外执行；待修改规则不是本任务提前生效的依据，不重复目标确认。

## 根因与边界

- Gateflow 的 Gate Order、状态不变量、Artifacts、Commits 和 draft PR entry 同时强制 plan review、slice / aggregate / PR 三层审核及逐 gate 提交（`skills/gateflow/SKILL.md:62` 起）。只改流程图会留下相互冲突的执行条件。
- plan / slice 的长必填清单、按一次 review pass 定义 slice 成本和默认不超过三个的表述（同文件 `:155` 起），削弱了已有“局部实现由实现者决定”的要求，容易诱导提前写完实现与过细切片。
- Planreview 的“假设至少有一个重要问题”、全部 lenses 必须显式应用和缺规格导向（`skills/planreview/SKILL.md:43` 起），与“不制造 blocker”“无 findings 可通过”形成张力；slice 审查偏向过粗，最优方案审查也缺少搜索边界。
- Phaseflow 复制旧 gates、提交条件和 Agent 职责，Deepreview 的 Gateflow 特例按三层分工，双语 README 再传播旧流程。这些直接链接必须同步对齐。

修改范围是 Gateflow、Planreview 的 SKILL 文本及其必要 metadata 表述，并仅对 Deepreview、Phaseflow 和双语 README 做直接规则/角色对齐。无 runner、collector、runtime、业务流程、live probe 或新流程工具改造；不新增固定记录 schema。现有 `agents/openai.yaml` 未编码旧审核链，核对兼容性即可，无需为了改动而修改。

## 规则、角色与状态

### 计划与实现自主权

计划达到足以指导已确认目标的正确实现即可：说明目标行为和正确职责 owner、实现方向、必要架构边界、重要契约/状态语义、影响范围及验证依据；缺陷类任务还须明确根因，未变目标等事实引用已有记录。功能开发关注新增能力/行为与合适架构，迁移/重构关注目标状态、不变量与必要兼容性。收敛 plan / slice 必填要求，不逐项填无关内容，也不预定函数、局部数据结构、分支或算法。

“最小必要”指减少不必要设计和机制。依据当前目标和直接证据选择实现方案，优先复用适用机制；对缺陷或已证实的结构性问题解决根因，必要时做范围明确的内部重构或替换错误模型/职责边界，避免靠特例、旁路、重复判断或兜底保留结构性问题。最佳实践和替代方案必须有当前需求、具体风险和收益依据，不引入假设未来需要的框架或通用化。

已确认目标内、保持对外承诺的必要实现选择和内部重构由总控继续处理，包括可修复的验证失败。改变目标、公共契约、兼容性承诺、验收标准或未授权的重大架构边界才重新确认；goal confirmation 已授权的变化不重复请示。统一收紧状态机与 Stop Conditions，普通实现选择不能仅因涉及 architecture / strategy 就成为用户停点。

简单计划由总控核对；重要契约、架构、迁移或状态机决策使用 Planreview，显式要求的审核仍执行。Planreview 保留证据驱动的反例审查，按当前风险应用已有 lenses，允许无 material finding 直接通过。审查目标实现方案与过度设计两面；必要重构不因改动较大被否定，非必要机制优先删除或简化。建议本身不得扩大范围、机制或验收要求，也不得靠架构偏好或无界替代方案搜索阻塞实施。需要实际代码判断的问题进入完整代码审核。

### Slice 与统一代码审核

默认一个 slice。只有必须先验证才能决定后续工作的依赖，或无法一次安全完成的迁移步骤，才拆分；每个 slice 有可独立验证的行为结果。多文件、多模块、多角色和代码量不是拆分依据，代码/测试/文档不能机械拆开。通常至多两个；三个及以上解释不可合并的具体依赖，由适用计划核对/Planreview 验证，不仅因数量重新请求用户批准。项目或用户明确的切分约束继续交接。

Slice 是实现与验证单元，不自动产生独立审核或提交。所有 slices 完成后，对最终组合版本执行一轮完整 Deepreview，包含 correctness、整体目标覆盖与遗漏、契约/状态、边界/失败路径、验证有效性及多 slice 接口/共享假设交互；适用独立审核数量及双路并行保留。取消独立 aggregate 轮次和强制 slice 审核。仅当中间决策影响后续大量工作且有明确返工风险时提前审核该决策，最终审核复用仍适用的结论。

保留 controller 裁决、accepted finding 必须实际修复并复审、真实 blocker/证据缺口不得放行、defer 的授权和 owner/destination 要求。Fix / re-review 仅在实际需要时执行，聚焦已裁 findings 与实际影响；有影响扩大或新反例证据才扩大范围。现有验证来源/版本核对、受影响断言重验与 mandatory checks 保留，无需机械重复整套验证。

### 推进与交付

统一各处流程和 entry 条件为：

```text
goal confirmation
-> plan（总控核对；重要决策执行 Planreview，必要修复及复审）
-> implementation / validation（按必要 slices）
-> 一轮完整 code review（含原 aggregate 职责）
-> [fix -> 受影响面 re-review]
-> ready-to-open-draft-PR
-> 必要提交 / push / create draft PR
-> 总控交付核对
-> draft-PR-pass
-> final closeout
```

目标确认后继续自动推进至 final closeout pass；current gate / next entry point 始终指向下一个未完成的适用步骤。计划审核不适用时由总控核对后进入实施，不等待不存在的 review artifact。无实际修复时记录审核通过并继续，不制造空 fix/re-review 或 per-gate accepted commit。

创建 draft PR 后进入总控交付核对，不直接完成：核对实际 repository / PR 身份、head/base 与完整 diff 对应已审版本、title/body 准确性、必要 CI 和 push 状态。相同内容不再派完整双审；内容或 base/diff 实际变化时，先判断旧证据适用性，对受影响面补审核/验证，再提交、push 并重新核对。仅记录变化按其实际影响处理，不能因省去 PR 审核而让未经审核的实质变更交付。

保留计划、实现/验证、审核/裁决、实际修复/复审、交付核对和 final closeout 的可追踪事实，允许同一文件维护及引用已有证据，不要求每个 gate 独立文件、完整字段表或 commit。按实际工作需要提交，并在交付前确保所需成果已提交/push；更新 draft-PR-pass 的前置条件及 final closeout 引用，移除旧层级的 artifact/commit 硬依赖。现有剩余风险归属、issue 关联/结案及外部动作授权边界继续适用。

## 一个实施 slice 与直接链接

一次完成上述文本调整与验证，无必须先验证才能决定后续修改的依赖。

- `skills/gateflow/SKILL.md`：同时对齐 frontmatter description、原则、plan/slice、Gate Order 与 section 绑定、状态机/停点、review/fix、Artifacts/Commits、PR entry 和 closeout，避免旧要求残留。
- `skills/planreview/SKILL.md`：对齐定位/使用条件、posture、readiness、sequencing/lenses、finding 与建议规则；兼顾切片过多/过细和必要依赖，保留 material findings、真实 blocker 和审核产物，不增加同义清单。
- `skills/deepreview/SKILL.md`：仅调整 Gateflow Review Method / artifact 的职责链接，完整审核承担 aggregate 职责；Gateflow 的交付核对由总控承担。独立调用 current changes / PR / all repository 的范围、严格方法和精确 PR 版本证据要求保留。
- `skills/phaseflow/SKILL.md`：总控亲自做简单计划核对、适用性判断和 PR 交付核对；plan / implementation / fix / 适用独立 review 仍交 Agent。同步 Controller Scope、handoff 输入、Slice Principle Handoff、Gate Order、state transitions、Control Doc Updates 与 closeout，消除旧三层角色和提交引用；不改路由或 Agent 生命周期协议。
- `README.md`、`README.zh.md`：同步工程流程介绍、职责表、Core Workflow 和相关用法文字；保留独立 Planreview / Deepreview 调用，避免示例把一次双路审核写成多个强制轮次。

## 验证与完成依据

实施后运行 `git diff --check` 和现有 `./scripts/validate-skills.sh`，预期无格式错误且 SKILL frontmatter/name/description 合法。核对四个 skill 的 `agents/openai.yaml` 名称、默认调用及描述仍与新文本兼容；现有 validator 不验证其角色语义，不能以 metadata pass 代替文本审核。

用 `rg -n 'aggregate|accepted.*commit|PR review|plan review|code-generation-ready|review pass|三层' skills/{gateflow,planreview,deepreview,phaseflow}/SKILL.md README.md README.zh.md` 定位并逐项读上下文，再通读最终组合文本。预期 gate/section、适用条件、通过条件、角色/handoff、记录、PR entry/closeout 和中英文描述一致；独立 PR review 等合理引用可保留，旧强制三层链和逐 gate 提交不能残留。检查实际 diff 只包含授权文本/工作记录，无安装目标或其它组件改动。

以文本走读验证以下场景，不新增测试框架或 runtime probe：

| 场景 | 必须得到的执行结果 |
| --- | --- |
| 简单任务、一个 slice、无 findings | 总控核对计划后实施/验证，一轮完整审核，通过后创建 PR 并核对交付；不等待 planreview、slice/aggregate/PR 双审或空提交。 |
| 重要契约/状态决策 | 实施前 Planreview；必要信息齐备且无 material finding 可通过，不要求穷举局部实现。 |
| 多文件任务与必要两步迁移 | 前者仍默认一个 slice；后者以验证依赖拆分，最终组合审核覆盖交互。三个以上须有具体依赖依据，不仅因数量请示。 |
| 已证实 owner 错误，或新增无依据抽象 | 前者允许范围内根因重构；后者建议删除/简化，不以少改行数或最佳实践保留错误机制。 |
| 审核 finding 修复 / PR 内容变化 | 受影响断言和路径复审，证据有效的未变范围可复用；版本/CI 缺项不能当交付通过，影响扩大才扩大审核。 |
| Resume、验证失败、真正越界 | 从下一个适用步骤继续；范围内可修复失败继续修复；未授权契约/目标变化、必要用户决策或缺失授权才停止。 |

控制器核对本计划后派发实施；最终组合文本由 mimo-flash / ds-flash 经独立 Claude runner 并行做一轮完整 Deepreview，控制器裁决，accepted fixes 经 gpt-6-sol 修复并做受影响面复审。其后控制器负责提交/push、创建并核对 draft PR 和结案。本 planner 只交付本文件。

无 blocking open question。剩余限制：文本只能指导 Agent，不能声称 runtime 强制执行或已测量效率提升；由控制器在 closeout 记录。按 control 的既有授权，后续由控制器在审核通过后执行 `./scripts/sync-skills.sh`，比较仓库与已安装 skills 文本一致，记录同步证据并提醒重开 Agent 会话加载新 skill。
