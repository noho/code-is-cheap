---
name: gateflow
description: "单个 work unit 的 gated 开发流程。用于 feature、issue、bug fix、migration、refactor、schema/public contract change 或 architecture-sensitive task；可选接收 design document；确认目标后，以最小必要计划、适用计划审核、实现与验证、一轮完整代码审核、必要修复及受影响面复审、draft PR 交付核对和 final closeout 自动推进。"
---

# Gateflow

Gateflow 只定义单个 `work unit` 的流程和 gate。work unit 可以是 feature、issue、bug fix、migration、refactor、
schema/public contract change 或 architecture-sensitive task。

## Core Principles

- 先看代码和事实，再判断 work unit 是否成立。
- 进入 plan 前，先用通俗语言向用户确认目标、非目标、边界和成功信号。
- Goal confirmation 是 binding scope contract。改变目标、公共契约、兼容性承诺、验收标准或未获授权的重大架构边界，
  先让用户重新确认；已确认目标内、保持对外承诺的必要实现选择和内部重构由总控继续处理，不重复请示已授权的变化。
- 最小必要设计是减少不必要的机制，不是减少修改行数。基于代码与事实明确目标行为和正确职责 owner，优先复用适用机制；
  对已证实的缺陷或结构性问题解决根因，允许范围明确的内部重构或旧机制替换，不靠特例、旁路、重复判断或兜底保留错误模型。
  最佳实践须有当前需求、具体风险和收益依据，不为假设未来需求引入框架、抽象或基础设施。
- 保留可追踪的计划、实现/验证、审核/裁决和交付事实；可同文件维护或引用已有记录，不要求每个 gate 独立文件或 commit。
  conversation-only 结果不足以通过 gate。
- draft PR gate 自动推进到 `draft-PR-pass`；merge、approve、mark ready for review、request reviewers、delete branch、
  对外 comment、创建/修改外部 issue 仍需用户额外授权。

## Invocation

典型调用：

```text
使用 $gateflow 开发 <work-unit>。
```

可选参数：

```text
使用 $gateflow design_doc=<path> base_ref=<ref> 开发 <work-unit>。
```

如果传入 `design_doc`，它是当前 work unit 的设计依据之一。若未传入，则以用户需求和代码事实为准。

## Preflight

任何 discussion、plan 或文件修改前，先检查：

```text
git branch --show-current
git status --short
```

如果当前 branch 是 `main`、`master`、`develop`、`release/*` 或项目定义的 protected trunk branch，先停下来让用户确认创建
工作分支。若 branch、dirty changes 或 scope ownership 不清，也先停下来问用户。

## Gate: goal confirmation

进入 plan 前必须完成 goal confirmation：

- 读取需求、design document（如有）和相关代码；
- 从第一性原理判断 work unit 是否成立；
- 复述目标、动机、成功信号、非目标、scope boundary；
- 说明直接代码证据；
- 说明本轮不会做的过度设计；
- 列出 blocking open questions（如有）。

用户确认后才能进入 `plan`。如果目标不成立、范围过大、动机不足或关键约束缺失，先 discussion，不进入 implementation。

## Gate Order

按以下顺序执行适用步骤；fix/re-review 仅在有实际修复时执行：

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

简单计划由总控核对；重要契约、架构、迁移或状态机决策执行 `planreview`，用户或项目显式要求的计划审核仍执行。
最终组合版本的 `code review` 使用 `deepreview`，包含原 aggregate 职责，不再另设 aggregate 轮次或强制逐 slice 审核。
PR 交付核对由总控完成，相同内容不重复派完整代码审核。

Gate Order entry 与下方 section 的绑定是执行约束。必须按对应的 `## Gate: ...` 或 `## Gate Group: ...` section 执行：

- `goal confirmation` -> `## Gate: goal confirmation`
- `plan`（含适用 plan review） -> `## Gate: plan`，审核/修复按 `## Gate Group: review / fix / re-review`
- `implementation / validation` -> `## Gate Group: implementation slice`
- `code review` 及必要 `fix` / `re-review` -> `## Gate Group: review / fix / re-review`
- `ready-to-open-draft-PR -> ... -> draft-PR-pass` -> `## Gate Group: draft PR`
- `final closeout` -> `## Gate: final closeout`

不得把 `draft-PR-pass` 当作 work unit 完成；必须继续执行 `final closeout` gate。

多 slice 时按依赖完成各 slice 的 implementation / validation，所有 slices 完成后审核最终组合版本。

## Gate State Machine

Gateflow 是确定性的 gate state machine。用户确认 goal confirmation 后，除非遇到明确 stop condition，必须持续按
Gate Order 推进，直到当前 work unit 到达 `final closeout pass`。

普通 gate 完成不是停止条件，而是转移条件。每个 gate 完成后必须立即：

1. 读取 gate artifact / validation / decision；
2. 裁决 findings 和 residual risks；
3. 记录当前 gate 的 artifact、decision、validation、finding 状态和 residual risk；
4. 将 current gate / next entry point 写成 Gate Order 中下一个未完成的适用 gate；
5. 继续执行下一个 gate。

不得因为某个 gate 刚完成就停止、总结或等待用户；只按下方 Stop Conditions 停止。范围内可修复的验证失败继续修复。

current gate / next entry point 必须表示下一个未完成的适用 gate，而不是刚完成的 gate。不得 invent、skip、collapse 或
reorder 必需或适用 gates；总控核对简单计划后不等待不存在的 plan review artifact，不执行条件不成立的审核或
fix/re-review 不属于 skip。放行条件未满足时保持当前步骤。

PR gate chain 的状态不变量：

- `create draft PR` 成功后，current gate / next entry point 必须变为 `总控交付核对`，不得写成 `draft-PR-pass`；
- `draft-PR-pass` 只有满足下方 `Gate Group: draft PR` 的 entry criteria 后才能进入；
- 缺少完整代码审核/必要复审证据、交付核对结果、必要 CI 或最终 push 状态时，不得进入 `draft-PR-pass` 或 `final closeout`；
- `final closeout` 不得补做、假设或跳过交付核对。

## Stop Conditions

除以下情况外，用户确认目标后自动推进：

- 必要用户取舍尚未明确，或变化超出 Goal Confirmation 授权的目标、契约、兼容性、验收或重大架构边界；
- branch、dirty changes、file ownership 或 commit scope 不清，无法安全继续；
- 必需输入、外部状态、验证或修复路径在允许范围内无法取得，或 residual risk / defer 确实需要用户决策；
- 需要尚未授权的 merge、approve、mark ready for review、request reviewers、delete branch、对外 comment 或创建/修改外部 issue；
- 用户明确要求 pause、stop 或 redirect。

## Gate: plan

plan 达到足以指导已确认目标的正确实现即可：基于直接证据说明目标行为、解决方向、必要职责/架构边界、重要契约与状态语义、
影响范围及验证依据（实际命令和预期断言）。功能开发说明新增能力与架构适配；迁移/重构说明目标状态、必须保持的不变量与
必要兼容性；缺陷类任务还须说明根因。已确认目标、非目标等事实引用已有记录，不逐项填写无关内容。

实现者在 approved scope 内决定函数拆分、局部数据结构、表达式、分支和算法；其中影响公共契约、关键正确性或架构取舍的
决策才须提前明确。需要实际代码才能判断的问题交完整代码审核，不以穷举局部实现阻塞 plan。

只规划已确认目标所需的设计、实现和验证。目标外风险或改进机会记录为 residual risk / deferred follow-up / open question；
确需改变 scope 时重新确认，不直接纳入当前 work unit。

默认一个 implementation slice。只在必须先验证才能决定后续工作的依赖，或无法一次安全完成的迁移步骤下拆分；每个 slice
须有可独立验证的行为结果。多文件、多模块、多角色或代码量本身不是拆分理由，代码/测试/文档不能机械拆开。
通常至多两个；三个及以上在 plan 解释不可合并的具体依赖，由总控核对或适用 Planreview 验证，不仅因数量重新请示。
design_doc、用户或上游 handoff 的显式切分约束继续适用。

总控核对计划是否足以指导已确认目标的正确实现、范围和切分是否合理，并记录 plan check 结论与计划审核适用性。重要契约、架构、迁移或
状态机决策使用 Planreview，显式要求的审核仍执行；必要修复及受影响面复审按下方统一规则。
简单计划核对中的修正由总控复核，不因此增加独立 Planreview；通过后进入 implementation。

## Gate Group: implementation slice

slice 是实现与验证单元，不自动产生独立审核或提交。按 accepted plan 的行为结果、范围、必要依赖和验证依据实施；
同一计划中已有的约束直接引用，不另填整套 slice 清单。多 slice 按验证依赖推进，未满足 prerequisite 时不得提前实现后续工作。

范围内必要实现选择、内部重构和可修复验证失败继续处理并记录；不得新增目标或承诺。目标外风险按 plan 的 scope 规则处理。
完成后记录实际改动、验证结果和未覆盖项。

仅当中间决策影响后续大量工作且有明确返工风险时提前审核该决策；最终完整审核复用仍适用的结论。

## Gate Group: review / fix / re-review

所有 slices 完成后，对最终组合版本执行一轮完整 Deepreview：检查 correctness、整体目标覆盖与遗漏、契约/状态、
边界/失败路径、验证有效性，以及多 slice 接口/状态/共享假设交互。完成适用的独立审核数量，保留要求的双路并行；
每位 reviewer 独立审查证据并形成实质判断，旧 pass 不能替代当前判断。适用计划审核也须满足其独立审核要求。

review / re-review 必须 evidence-based，并产出 durable artifact。finding 必须能被裁决为：

- `accepted`
- `rejected-with-reason`
- `deferred-with-owner`
- `needs-more-evidence`

fix/re-review 最终状态只用：

- `未修复`
- `已修复`
- `部分修复`
- `证据失效`

plan review 与裁决先判断问题是否实际阻止正确实现已确认目标。措辞重复、明确约束已覆盖的局部表达式，或只能通过
已实现代码判断的问题，不得反复阻塞 plan；按上述裁决与 fix 状态处理，说明 implementation / code review 等 destination
及非阻塞依据。未解决的真实 scope/contract/architecture/state/acceptance blocker 仍阻塞，不得为通过 gate 改名、延期或豁免。

跨 gate 复用真实验证前，核对可取回的来源、实际命令/结果、被验证版本/范围及当前代码、依赖、配置和相关环境；
在当前 artifact 说明证据仍支持哪些所需断言。裸 pass、错版、不可取回或覆盖不足的证据不能放行，也不能替代独立判断。
fix 或其它变化后重验受影响断言与交互，重新判断其余证据的适用性；全量重跑只因实际影响、证据反例或项目 mandatory checks
要求而执行。mandatory checks 仍须满足；reviewer 可独立调查具体疑点，无需每个 gate/reviewer 重跑同一整套命令。

re-review 聚焦已裁决 findings 与实际变更影响，按上述规则复用适用证据。artifact 变更即新版本，受影响的旧证据须重新验证；
仅因实际变更影响或新的有证据反例扩大范围，不对未受影响部分全面重设计或重扫。独立审核数量和授权要求继续适用。

所有适用 review loops 统一：有实际需要的修复才执行 fix -> re-review；无待修 finding 且全部
通过条件满足时，记录 review/裁决/pass，进入下一个适用步骤，不制造空 fix/re-review 或 commit。记录 pass 不是新 gate。
缺失证据在当前 review 内补足；需要实际修复才进入 fix/re-review，证据不足不能推进。

review gate 通过条件：

- 必要独立 review 已完成，review artifact 已记录 artifact path 和裁决；
- 所需验证对当前目标有效且充分，mandatory checks 已满足；
- 每个仍裁决为 `accepted` 的 finding 均为 `已修复`，且修复证据已由 re-review 验证并回写最终状态；
  `未修复`、`部分修复`、`证据失效` 不得仅因有状态、风险已分类或没有 open question 而放行；
- 未完成的 finding 只有正式改裁决为 `deferred-with-owner` 才能退出本 gate 的修复要求；artifact 必须记录
  既有授权依据、明确的非阻塞理由、owner 和 destination。缺任一项不得通过；延期改变 goal、scope 或验收标准时，
  先按 Goal Confirmation 规则重新确认；
- 没有真实 blocker、blocking open question 或未解决的 `needs-more-evidence`；accepted 列表为空不等于 pass；
- residual risks 已分类。

## Residual Risks

每个 implementation/fix/review artifact 必须列出 residual risks 和 uncovered areas。每个 residual risk 必须分类为：

- fixed in current slice；
- covered by later approved slice；
- assigned to later work unit；
- tracked by existing issue；
- requiring new issue or explicit user decision。

存在 unclassified residual risk 时，不得完成 implementation、review loop、PR gate 或 final closeout；
仍存在的风险须有 owner/destination，范围内可分类处理的风险不自动成为用户停点。

## Artifacts

保留 plan 与总控核对、适用 plan review、各 slice 实现/验证、完整代码审核/裁决、实际 fix/re-review、PR 交付核对与
final closeout 的可追踪事实。允许同一文件维护或链接既有 artifact，不要求每个 gate 独立文件或固定字段表。
记录须足以定位 work unit、范围/版本、实际变化、检查/裁决与结果、docs decision、风险/未覆盖项、完成状态及下一步。
未变且已确认的 goal/scope/plan/实现/验证事实可引用 artifact 路径、可取回版本（commit 或 hash 对应的保存快照）及相关事实/章节，
无需复制全文。hash 不替代保存版本；来源缺失、错版或不适用须先补足，不能标作完成。当前变化、检查、裁决与验证适用性仍须记录。

## Commits

按实际工作需要提交，不要求 per-gate accepted commit，不为无实际变化的 pass 制造空提交。交付前确保所需成果已提交并 push。
commit 前必须确认 branch 不是 protected trunk，检查 `git status`，只 stage 当前 work unit 的相关文件，避免 unrelated dirty changes。

## Gate Group: draft PR

`ready-to-open-draft-PR` 前确认：

- branch 只包含当前 work unit intended commits；
- all approved slices 完成；完整代码审核已满足全部通过条件，实际 accepted 修复已 re-reviewed，无需修复时已记录 pass；
- tests/type checks 有实际运行或适用复用的结果，失败已说明且不妨碍放行；mandatory checks 已满足；
- docs decision 已完成；
- deferred findings/residual risks 有 owner/destination；
- 如果当前 work unit 是 issue，创建 draft PR 时 PR body 必须关联 issue：完整解决时使用 GitHub closing keyword（如 `Closes #123`），部分解决或仅关联时使用非关闭引用（如 `Related to #123`）并说明剩余 owner/destination；
- draft PR summary 匹配真实代码，不把 future work 写成已完成。

到达 `ready-to-open-draft-PR` 后自动：

```text
必要提交 / push
-> create draft PR
-> 总控交付核对
-> draft-PR-pass
```

总控交付核对实际 repository / head repository、PR number/URL 和 head/base OID，以该 OID 对定位完整 diff，核对其与已审版本的
对应关系、title/body 准确性、必要 CI 和最终 push 状态，并保存可取回的版本/diff 与核对结果。收尾再次确认 head/base 未变；
身份、完整 diff、版本无法确认，或必要 CI 未满足放行条件时不得通过。此核对不替代完整代码审核，也不对相同内容重新派双路完整审核。

内容或 base/diff 实际变化时，先判断旧证据适用性，对受影响面补审核/验证；accepted findings 实际修复须受影响面复审。
有影响扩大或新反例证据才扩大审核；仅记录变化按其实际影响处理，不能交付未经审核的实质变更。所需变更提交/push 后
重新核对交付；核对记录可与 closeout 同文件维护，不因本地核对记录更新机械重启完整审核或提交循环。

进入 `draft-PR-pass` 前必须满足：

- 完整代码审核及必要受影响面补审/验证已满足上述全部通过条件，所有 findings 已裁决；
- 总控交付核对记录存在，身份/版本/完整 diff、title/body 和最终 push 均已确认，必要 CI 已满足放行条件；
- 所需交付成果已提交/push，无未交付的实质变更。

## Gate: final closeout

`draft-PR-pass` 后必须输出 final closeout：

- what changed；
- what was verified；
- docs updates；
- finding status；
- remaining risks / owners；
- draft PR URL；
- issue link status（如果当前 work unit 是 issue，确认 draft PR body 已用 closing keyword 或非关闭引用关联 issue）；
- issue closeout comment status（如果当前 work unit 是 issue，给 issue 添加 closeout comment，包含 draft PR URL、finding status、remaining risks / owners 和 merge 后关闭预期）；
- next entry point。

如 final closeout summary 尚不存在，`final closeout` gate 必须创建它。`final closeout pass` 后必须记录 work unit completed
status，以及用户 merge 当前 PR 后可继续的 next entry point。
closeout 必须实质总结以上实际结果；可链接明细，不能只是历史 artifact 链接列表。

如果当前 work unit 是 issue，`final closeout` gate 必须确认：

- PR body 已关联 issue；完整解决时使用 closing keyword，部分解决时不得使用会错误关闭 issue 的 closing keyword；
- issue 已添加 closeout comment，指向 draft PR，并说明 remaining risks / owners 和 merge 后 issue 是否会自动关闭。

issue 关联、closeout comment 或关闭预期未满足时，不得输出 final closeout pass；先在既有授权内补足或纠正。
必要 issue 身份不明确、权限/授权缺失，或关闭预期确需用户取舍时，按 Stop Conditions 停止并询问用户。
