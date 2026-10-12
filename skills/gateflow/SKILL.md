---
name: gateflow
description: "单个 work unit 的 gated 开发流程。用于 feature、issue、bug fix、migration、refactor、schema/public contract change 或 architecture-sensitive task；可选接收 design document；先读代码并从第一性原理确认目标/非目标，经用户确认后按 plan、review、implementation、review、deepreview、draft PR 和 final closeout gate 自动推进到 final closeout pass。"
---

# Gateflow

Gateflow 只定义单个 `work unit` 的流程和 gate。work unit 可以是 feature、issue、bug fix、migration、refactor、
schema/public contract change 或 architecture-sensitive task。

## Core Principles

- 先看代码和事实，再判断 work unit 是否成立。
- 进入 plan 前，先用通俗语言向用户确认目标、非目标、边界和成功信号。
- Goal confirmation 是 binding scope contract；后续 gate 不得扩大目标、非目标、success signal 或验收标准，除非先停下来让用户重新确认。
- 只做当前 work unit 需要的设计；不得引入无当前需求、真实风险或明确扩展压力支撑的过度设计。
- 每个 gate 都必须有 artifact、decision、validation 或明确说明；conversation-only 结果不足以通过 gate。
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

固定必需 gates 的顺序如下；方括号内的 fix/re-review 仅在有实际修复时执行：

```text
goal confirmation
-> plan
-> plan review
-> [fix -> re-review]
-> accepted plan commit
-> implementation
-> code review
-> [fix -> re-review]
-> accepted slice commit
-> aggregate deepreview
-> [fix -> re-review]
-> accepted deepreview commit
-> ready-to-open-draft-PR
-> push
-> create draft PR
-> PR review
-> [fix -> re-review]
-> accepted PR review commit
-> push
-> draft-PR-pass
-> final closeout
```

`plan review` gate 必须使用 `planreview` skill；`code review`、`aggregate deepreview` 和 `PR review` gates 必须使用 `deepreview` skill。

Gate Order entry 与下方 section 的绑定是执行约束。必须按对应的 `## Gate: ...` 或 `## Gate Group: ...` section 执行：

- `goal confirmation` -> `## Gate: goal confirmation`
- `plan` -> `## Gate: plan`
- `implementation -> code review -> [fix -> re-review] -> accepted slice commit` -> `## Gate Group: implementation slice`
- `plan review`、`code review`、`aggregate deepreview`、`PR review` 及其 `fix` / `re-review` -> `## Gate Group: review / fix / re-review`
- `ready-to-open-draft-PR -> ... -> draft-PR-pass` -> `## Gate Group: draft PR`
- `final closeout` -> `## Gate: final closeout`

不得把 `draft-PR-pass` 当作 work unit 完成；必须继续执行 `final closeout` gate。

多 slice 时重复：

```text
implementation -> code review -> [fix -> re-review] -> accepted slice commit
```

直到所有 approved slices 完成。

## Gate State Machine

Gateflow 是确定性的 gate state machine。用户确认 goal confirmation 后，除非遇到明确 stop condition，必须持续按
Gate Order 推进，直到当前 work unit 到达 `final closeout pass`。

普通 gate 完成不是停止条件，而是转移条件。每个 gate 完成后必须立即：

1. 读取 gate artifact / validation / decision；
2. 裁决 findings 和 residual risks；
3. 记录当前 gate 的 artifact、decision、validation、finding 状态和 residual risk；
4. 将 current gate / next entry point 写成 Gate Order 中下一个未完成的适用 gate；
5. 继续执行下一个 gate。

不得因为某个 gate 刚完成就停止、总结或等待用户，除非出现以下情况之一：

- blocking open question 影响 scope、architecture、contract、schema、file ownership、state transition、implementation strategy、
  test expectation 或 user-visible behavior；
- required artifact、code state、external state 或 validation 缺失，且当前允许的 gate 不能产生它；
- review/fix gate 返回 blocking failure，且 required fixing path 不可用或被阻塞；
- branch、dirty changes、file ownership、commit scope 不清，无法安全创建 checkpoint；
- 需要 merge、approve、mark ready for review、request reviewers、delete branch、对外 comment 或创建/修改外部 issue；
- 用户明确要求 pause、stop 或 redirect。

current gate / next entry point 必须表示下一个未完成的适用 gate，而不是刚完成的 gate。不得 invent、skip、collapse 或
reorder 必需或适用 gates；不执行条件不成立的 fix/re-review 不属于 skip。放行条件未满足时保持当前 review/fix/re-review。

PR gate chain 的状态不变量：

- `create draft PR` 成功后，current gate / next entry point 必须变为 `PR review`，不得写成 `draft-PR-pass`；
- `draft-PR-pass` 只有满足下方 `Gate Group: draft PR` 的 entry criteria 后才能进入；
- 缺少 PR review artifacts、accepted PR review commit hash / no-commit pass 记录、或 final push 状态时，不得进入
  `draft-PR-pass` 或 `final closeout`；
- `final closeout` 不得补做、假设或跳过 PR review gate。

## Stop Conditions

除以下情况外，用户确认目标后自动推进：

- blocking open question 影响 scope、architecture、contract、schema、file ownership、state transition、implementation strategy、
  test expectation 或 user-visible behavior；
- branch、dirty changes、file ownership、commit scope 不清，无法安全创建 checkpoint；
- validation failure、unclassified residual risk、deferred finding 或 missing artifact 需要用户决策；
- 需要 merge、approve、mark ready for review、request reviewers、delete branch、对外 comment 或创建/修改外部 issue。

## Gate: plan

plan 必须 code-generation-ready：实现无需重新决定已确认目标与对外行为、必要契约与 identity 语义、architecture/ownership
边界、state transitions/invariants 或验收依据。不要求穷举代码、局部表达式或实现细节；实现者在 approved scope 内决定
局部实现，实际代码问题由 code review 检查。

plan 必须是最小化 plan/design：只规划 Goal Confirmation 已确认目标所必需的设计、实现和验证。每个 design decision、
验收标准和 implementation slice 都必须能映射到已确认的 goal、success signal 或必要 correctness/safety 条件。不得把实现层
发现的潜在风险升级成新的目标、验收标准、架构强化或 future-slice work。

plan 必须包含：

- goal / motivation / success signal；
- non-goals / scope boundary；
- goal alignment：每个 slice / design decision / validation 对应的已确认 goal 或 success signal；
- design document alignment（如有）；
- first-principles judgment and direct code evidence；
- affected files/modules；
- contract/schema/state-machine/public-interface changes；
- 必要的 implementation decisions；
- small implementation slices；
- tests/validation commands and expected assertions；
- docs decision；
- risks/open questions；
- completion report format。

plan 必须显式说明为什么当前方案没有过度设计、没有 goal drift。若代码阅读发现 confirmed goal 之外的风险或改进机会，
plan 只能把它记录为 residual risk / deferred follow-up / open question，或停止并要求重新做 goal confirmation；不得直接纳入
当前 work unit。

implementation slices 必须以可验证行为增量为边界，而不是按模块、文件、owner 或技术层机械拆分。slice 数量应尽量少；
每个 slice 都必须值得一次 implementation pass 和一次 review pass 的 gate 成本。默认避免超过 3 个 implementation
slices；若超过，plan 必须说明为什么不能合并或减少。若 design_doc、用户输入或上游 handoff 定义了不同 Slice 切分原则
或阈值，以其为准。

`plan review` gate 必须审查 slices 是否过多、是否按模块 / 文件 / owner 机械拆分、是否能合并、是否 gate 成本超过实现风险，
以及是否容易让 implementation agent 提前做 future-slice work。

## Gate Group: implementation slice

每个 slice 必须足够小，适合一次 implementation pass 和一次 review pass；同时必须代表一个可验证行为增量，不能只是
机械文件拆分、模块拆分或 owner 拆分。每个 slice 必须写清：

- id/name、objective、expected outcome；
- allowed files/modules；
- prerequisites/dependencies；
- 明确的 allowed change scope；
- 必要 interfaces、data flow、identity 语义、state transitions、error handling、invariants；
- non-goals；
- tests/validation commands and expected assertions；
- completion signal and stop condition。

implementation 只能做当前 approved slice，除非 approved plan 明确允许一次做多个 slice。

implementation 不得实现 approved slice 之外的修复、重构、硬化、兼容、验收标准或设计扩展。若实现过程中发现当前 slice
之外的风险，必须记录为 residual risk / deferred follow-up，或停止请求重新确认 goal；不得顺手扩大实现范围。

## Gate Group: review / fix / re-review

三层代码审核都须完成适用的独立审核数量，由 reviewer 审查证据并形成当前 gate 的实质判断：

- slice code review：沿当前 approved slice 的受影响路径检查 correctness、契约/状态、边界/失败路径及 tests/validation。
- aggregate deepreview：检查 slices 的接口/状态/共享假设交互、整体目标覆盖与遗漏、既有证据对整体版本的适用性。
  单个未变 slice 仍须独立判断整体目标与遗漏，可引用 slice 证据，无需重做同范围全面 correctness review。
- PR review：核对实际 PR 身份/版本、完整 diff 与 accepted 工作的一致性、title/body、CI/checks 及新增变化的影响。
  精确 OID、diff 快照/hash、同版深挖与收尾核对按 Deepreview 执行；新变化、交互风险或证据反例须追踪受影响路径。

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
仅因实际变更影响或新的有证据反例扩大范围，不对未受影响部分全面重设计或重扫。独立 review、gate 顺序与批准要求不变。

所有 review loops（plan、slice、aggregate、PR）统一：有实际需要的修复才执行 fix -> re-review；无待修 finding 且全部
通过条件满足时，记录 review/裁决/pass，直接进入对应 accepted commit，不制造空 fix/re-review。记录 pass 不是新 gate。
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

存在 unclassified residual risk 时，不得关闭 slice、review loop、aggregate deepreview loop、PR gate 或 final closeout。

## Artifacts

必要 artifacts：

- plan artifact；
- plan review artifact；
- implementation artifact for each slice；
- code review artifact for each slice；
- fix / re-review artifacts when fixes occur；
- aggregate deepreview artifact；
- PR review artifact；
- final closeout summary。

artifact 必须记录 gate、work unit、scope、changed files 或 reviewed target/版本、decisions/findings、validation、docs decision、
residual risks/uncovered areas、completion status、artifact path 和 next entry point。
未变且已确认的 goal/scope/plan/实现/验证事实可引用 artifact 路径、可取回版本（commit 或 hash 对应的保存快照）及相关事实/章节，
无需复制全文。hash 不替代保存版本；来源缺失、错版或不适用须先补足，不能标作完成。当前变化、检查、裁决与验证适用性仍须记录。

## Commits

review loop 满足上述全部通过条件且 artifact 完整后，自动创建 protected local commit：

```text
gateflow: accept plan for <work-unit>
gateflow: accept <work-unit> <slice-id>
gateflow: accept deepreview for <work-unit>
gateflow: accept PR review for <work-unit>
```

commit 前必须确认 branch 不是 protected trunk，检查 `git status`，只 stage 当前 gate 相关文件，避免 unrelated dirty changes。

## Gate Group: draft PR

`ready-to-open-draft-PR` 前确认：

- branch 只包含当前 work unit intended commits；
- all approved slices 完成并有 accepted slice commits；
- aggregate deepreview 已满足全部通过条件；实际 accepted 修复已 re-reviewed，无需修复时已记录 pass；
- accepted deepreview commit 已创建；
- tests/type checks 有实际运行或适用复用的结果，失败已说明且不妨碍放行；mandatory checks 已满足；
- docs decision 已完成；
- deferred findings/residual risks 有 owner/destination；
- 如果当前 work unit 是 issue，创建 draft PR 时 PR body 必须关联 issue：完整解决时使用 GitHub closing keyword（如 `Closes #123`），部分解决或仅关联时使用非关闭引用（如 `Related to #123`）并说明剩余 owner/destination；
- draft PR summary 匹配真实代码，不把 future work 写成已完成。

到达 `ready-to-open-draft-PR` 后自动：

```text
push
-> create draft PR
-> PR review
-> [fix -> re-review]
-> accepted PR review commit
-> push
-> draft-PR-pass
```

PR review 按上述统一通过条件执行：accepted findings 的实际修复必须 re-review；无需 fix 时记录 pass。
PR review artifact / pass evidence 仍须提交并 push，沿用下方既有 no-commit pass 规则。

进入 `draft-PR-pass` 前必须满足：

- PR review artifacts 已存在；
- 所有 PR review findings 已裁决；
- 上述 review gate 的全部通过条件已满足；
- required fixes / re-review 已通过，或 PR review artifact 明确记录 pass 且无需 fix；
- accepted PR review commit 已创建，或已明确记录 PR review pass 且无需 commit；
- PR review / fix 后的 final push 已完成。

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

若 draft PR 未关联 issue、issue closeout comment 未添加、缺少权限、issue number 不明确，或 closing keyword 会错误关闭未完成 issue，不得输出 final closeout pass，必须停止并询问用户。
