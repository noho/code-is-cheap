---
name: gateflow
description: "开发流程编排。开发复杂 feature、migration、refactor、schema change、public contract change 或 architecture-sensitive task 时使用；流程包含可选需求讨论、code-generation-ready plan、自动 plan/code/deepreview 闭环、本地 accepted commits，并推进到 ready-to-create-PR；只有遇到 blocking open question、scope 不清或对外可见动作时才停下来问用户。"
---

# Gateflow

Gateflow 是复杂 work unit 的 controller-agent 工作流。它把 feature、migration、refactor、schema/public contract
change 或 architecture-sensitive task，从讨论、计划、实施、review、fix、commit 推进到 `ready-to-create-PR`。

## Role

controller agent 只做总控：维护状态、派发 handoff、收集 artifact、裁决 finding、保护 scope boundary、推进 gate。
controller 不得亲自写 plan、review、implementation、fix 或 re-review，除非用户明确要求。

specialist roles：

- planning agent：写 handoff-ready、code-generation-ready plan。
- implementation agent：只实现 approved plan 的 assigned slice。
- fix agent：只修 controller-accepted findings。
- review / re-review agent：只输出 evidence-based findings 或复核结果。
- user：回答 blocking open questions，并授权 create PR、push、merge、approve、对外 comment、创建/修改外部 issue 等对外可见动作。

总控裁决原则：所有 plan、review finding、fix scope、defer decision 和 residual risk 裁决，都必须追求项目内最佳实践，
同时不得引入无当前需求、风险或明确扩展压力支撑的过度设计。

## When To Use

用于复杂 feature、migration、大型 refactor、schema/storage/public API/state-machine change、架构敏感任务、多 Agent
implementation/review/fix 流程。不用于 typo、小型本地 bugfix 或无须 gated orchestration 的轻量改动。

## Stop Conditions

从 `plan` 到 `ready-to-create-PR` 默认自动推进。controller 只在以下情况停下来问用户：

- blocking open question 影响 scope、architecture、contract、schema、file ownership、state transition、
  implementation strategy、test expectation 或 user-visible behavior；
- branch、dirty changes、file ownership、commit scope 不清，无法安全创建本地 checkpoint；
- validation failure、residual risk、deferred finding、missing artifact 需要用户决策；
- 需要 create PR、push、merge、approve、delete branch、对外 comment 或创建/修改外部 issue。

controller judgment、implementation-agent confidence 或 reviewer approval 只能推进本地 gate，不能替代用户对
blocking open questions 或对外可见动作的授权。

## Preflight Branch Check

workflow 最开始、任何 discussion/plan/文件修改之前，必须检查：

```text
git branch --show-current
git status --short
```

如果当前 branch 是 `main`、`master`、`develop`、`release/*` 或项目定义的 protected trunk branch，停下来提示用户创建工作分支，
包含当前 branch、dirty 状态、建议 branch name、确认后命令。

建议 branch 使用 conventional prefix：`feat/`、`fix/`、`docs/`、`refactor/`、`chore/`。确认后才执行：

```text
git switch -c <suggested-branch-name>
```

如果当前已在非 protected work branch，记录 branch 和 baseline 后继续。若 branch、dirty changes 或 worktree 状态让 scope ownership
不清，先问用户。

## Invocation

用户说：

```text
使用 $gateflow 开发 <feature>。
如果需求不够清楚，先讨论。
```

controller 先判断需求是否足够写 plan。需求清楚则进入 `plan`；需求不清、动机不足、范围过大、风险高或缺少关键约束，则先
feature discussion，收敛 goal、success signal、motivation、alternatives、tradeoffs、likely slicing、non-goals、
stop conditions、user preferences。不要让 discussion 变成 implementation。

## Gate Order

固定顺序：

```text
plan
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
-> ready-to-create-PR
-> PR
-> PR review
-> final closeout
```

多 slice 时自动重复：

```text
implementation -> code review -> fix -> re-review -> accepted slice commit
```

直到所有 approved slices 完成。除非用户明确改变 scope，不要提前进入 aggregate deepreview、ready-to-create-PR、PR 或 closeout。

所有 slices commit 后，必须自动执行 aggregate deepreview：对当前 branch 相对 `main` 的完整 diff 运行
`$deepreview --base main` / `/deepreview --base main` 等价 review。若 work unit 明确指定其它 base ref，记录原因并使用对应 base。
aggregate deepreview 有 accepted findings 时自动 `fix -> re-review`。只有 aggregate re-review 通过并创建
accepted deepreview commit 后，才能进入 `ready-to-create-PR`。

`ready-to-create-PR` 是本地自动流程终点。到达后报告 branch、commits、review artifacts、validation results、
residual risks 和 PR readiness；不要自动 create PR、push、merge、approve 或对外 comment，除非用户已明确授权。

## Controller State

持续维护：

- work-unit name / goal / explicit non-goals；
- current baseline and branch；
- current gate；
- target files/modules；
- plan、review、implementation、fix artifact paths；
- accepted / rejected / deferred / unresolved findings；
- implementation slices and current slice status；
- validation commands/results and documentation decision；
- accepted plan commit hash、accepted slice commit hashes、accepted deepreview commit hash、PR status；
- residual risks、owners、tracking destinations、next entry point。

## Protected Local Commits

Gateflow commit 是本地 accepted checkpoint，不是 push/PR/merge 授权。review loop 通过、artifact 完整且没有
blocking open question 后，controller 自动创建：

- accepted plan commit：`plan -> plan review -> fix -> re-review` 后；
- accepted slice commit：每个 `implementation -> code review -> fix -> re-review` 后；
- accepted deepreview commit：`aggregate deepreview -> fix -> re-review` 后；即使没有 accepted findings，也提交
  aggregate review artifact 和 readiness evidence。

commit 前必须确认 branch 不是 protected trunk，检查 `git status`，只 stage 当前 gate/slice/deepreview 相关文件，
包含相关 artifacts、validation、tests、docs，避免 unrelated dirty changes。scope 不清则停下来问用户。

commit message：

```text
gateflow: accept plan for <work-unit>
gateflow: accept <work-unit> <slice-id>
gateflow: accept deepreview for <work-unit>
```

每次 automatic local commit 后，把 hash 记录进 controller state。automatic local commit 禁止 push、create PR、
merge、approve 或 delete branch。

## Plan Rules

plan 必须 handoff-ready 且 code-generation-ready；implementation agent 应能直接按 plan 生成代码，不需要重新设计方案、
发明契约、选择 file ownership、猜 state transition 或决定 test scope。

plan 必须包含：goal/motivation、non-goals/scope、直接证据、affected files/modules、contract/schema/state-machine/public-interface
changes、具体 implementation decisions、small implementation slices、tests/validation commands/expected assertions/failure paths、
docs decision、review gates、stop conditions、risks/open questions、completion report format。

blocking open questions 必须在 plan re-review 通过前解决，并作为 decision 写回 plan。planning agent 如果发现 blocking
question，应停下来问用户或输出 `Blocking Questions For Controller`，不要把 plan 标为 handoff-ready。non-blocking questions
必须写明 working assumption、为什么低风险、什么信号会触发回看。不要让 implementation agent 在 material options 未收敛时自行选择。

## Slice Rules

每个 slice 必须足够小，适合一个 implementation pass 和一个 review pass。每个 slice 写清：

- id/name、objective、expected outcome；
- allowed files/modules；
- prerequisites/dependencies；
- exact allowed changes；
- functions/classes/types、call paths、data flow、state transitions、error handling、invariants；
- non-goals；
- tests/validation commands and expected assertions；
- completion signal and stop condition。

plan review 必须要求修复 slice 太粗、file ownership 不清、implementation instructions 不够具体、tests 只在最后定义、
sequencing 诱导 implementation agent 提前做 future-slice work 等问题。

implementation 时只能分派当前 assigned slice，除非 approved plan 明确授权一次做多个 slice。

## Residual Risk Tracking

每个 implementation/fix report 必须列出 residual risks 和 uncovered areas。controller 必须分类为：

- fixed in current slice before review；
- covered by later slice in approved plan；
- assigned to later phase/work unit；
- tracked by existing issue；
- requiring new issue or explicit user decision。

存在 unclassified residual risk 时，不得关闭 slice、code review loop、aggregate deepreview loop、PR gate 或 final closeout。
deferred risk 必须有 owner/destination：later slice、later phase/work unit、issue number 或 user decision。

## Artifact Rules

除非用户明确豁免，conversation-only artifact 不足以通过 gate。

work artifacts：

- implementation artifact：每个 assigned slice 完成后、进入 code review 前；
- fix artifact：每次 fix pass 完成后、进入 re-review 前；
- aggregate fix artifact：aggregate deepreview 后如发生 fix；
- PR fix artifact：PR review 后如发生 fix。

implementation artifact 记录 gate、work-unit、slice、approved plan、scope/non-goals/allowed files、changed files、
implemented plan items、validation、docs decision、plan gaps、residual risk classification、completion/stop status、artifact path。

fix artifact 记录 gate、source review artifact、accepted finding ids、per-finding fix status、changed files、validation、
new risks/open questions、residual risk classification、finding 标题状态更新结果、artifact path。

review artifacts：

- plan review / plan re-review；
- code review / code re-review；
- aggregate deepreview / aggregate re-review；
- user-requested additional review/re-review；
- PR review / PR re-review or fix review。

review artifact 记录 gate、reviewed target、conclusion、findings、open questions/residual risk、controller decision status、
artifact path。除非 artifact path 已进 controller state，accepted findings 都有 fix/re-review 状态，且 re-review 已在可编辑
source review artifact 或 work log 中回写最终标题状态，否则不得标记 review gate passed。

## Finding And Status Rules

Plan finding：

```markdown
### 编号-未修复-[严重程度（低/中/高/严重）]-finding简述
- **Plan位置**:
- **问题类型**: 动机不成立 / 范围漂移 / 架构边界 / 契约缺失 / 切片过粗 / 不可直接实施 / 测试缺口 / open question 未收敛 / 其它
- **计划当前写法**:
- **为什么有问题**:
- **直接证据**:
- **影响**:
- **建议改法和验证点**:
- **修复风险（低/中/高）**:
- **严重程度（低/中/高/严重）**:
```

Code/PR finding：

```markdown
### 编号-未修复-[严重程度（低/中/高/严重）]-finding简述
- **入口/函数**:
- **文件(行号)**:
- **输入场景**:
- **实际分支**:
- **预期行为**:
- **实际行为**:
- **直接证据**:
- **影响**:
- **建议改法和验证点**:
- **修复风险（低/中/高）**:
- **严重程度（低/中/高/严重）**:
```

controller 必须把每个 finding 裁决为且只裁决为：`accepted`、`rejected-with-reason`、`deferred-with-owner`、
`needs-more-evidence`。

fix/re-review 标题状态词只用：`未修复`、`已修复`、`部分修复`、`证据失效`。fix agent 可先更新状态；re-review
agent 是最终状态权威。如与 fix 自报不一致，以 re-review 为准。source artifact/work log 可编辑时，re-review
必须回写最终标题状态；不能编辑时，re-review artifact 必须说明原因并列出最终标题状态映射。

## Review Engines

plan review / re-review 默认使用 `$planreview` / `/planreview`。如果目标 agent 不支持，controller 不得亲自 review；
必须把 inline criteria 放进 handoff 派给 review agent：motivation、assumptions、scope、non-goals、success signal、
handoff/code-generation readiness、architecture boundaries、best practices、optimal solution、overengineering、
state machines/lifecycle/concurrency/recovery/partial failure、slice size/sequencing、tests/validation/residual tracking、
blocking questions 是否收敛。

aggregate deepreview 默认使用 `$deepreview --base main` / `/deepreview --base main`，且在 `phaseflow` 等上层 skill 覆盖时遵守其
额外 reviewer 要求。

## Worker Handoff

`$gateflow` 是 controller-only workflow。worker prompt 禁止写：

```text
请遵守 $gateflow
请使用 $gateflow
请启动 /gateflow
follow gateflow from the beginning
```

worker prompt 必须说明：这是 Gateflow-governed handoff；你不是 controller；不要启动 `$gateflow` / `/gateflow`；
不要从 plan 重新开始；不要重排 gate；current gate；assigned scope；allowed files/modules；required validation；
stop condition；completion report format；不得自行进入其它 gate、commit、PR、merge、push 或 closeout。

worker 如果发现当前 assigned gate 信息不足，应停止并报告缺口，把控制权交回 controller。

## Prompt Skeletons

prompt skeletons 只是 minimum contract，controller 必须按 actual feature、repo facts、approved plan、current gate、findings
和项目指令动态构造。

- Plan：只写 plan，不改代码，不进入 implementation；输出 handoff-ready/code-generation-ready plan；blocking questions
  走 user/ASK 或 `Blocking Questions For Controller`。
- Plan review：只 review plan，不改代码，不进入 implementation；用 `$planreview` / `/planreview` 或 inline criteria；
  输出 durable review artifact。
- Implementation：只实现 assigned slice；按 approved plan、scope、allowed files、tests、docs、stop condition；输出 durable
  implementation artifact。
- Code review：只 review assigned slice/diff target；找 bugs、architecture violations、contract drift、missing tests、
  type-safety、undocumented behavior changes；输出 durable review artifact。
- Fix：只修 controller-accepted findings；不处理 rejected/deferred；不扩大 scope；报告 per-finding status，更新标题状态；
  输出 durable fix artifact。
- Re-review：只复核 accepted findings 及 fixes；回写最终标题状态；记录是否引入 blocker；输出 durable re-review artifact；
  不裁决最终 gate pass。
- Accepted commit：review loop 通过、artifact 完整、无 blocking question 后创建 protected local commit；只 stage 当前 gate/slice/deepreview
  文件；记录 hash；不 push/PR/merge/approve/delete branch。

## PR Gate And Closeout

`ready-to-create-PR` 前确认：

- branch 只包含当前 work unit intended commits；
- all approved slices 完成并有 accepted slice commits；
- aggregate deepreview 已执行，accepted findings 已修复并 re-reviewed；
- accepted deepreview commit 已创建并记录 hash；
- tests/type checks 已运行或失败已说明；
- docs decision 已完成；
- deferred findings/residual risks 有 owner/destination；
- PR summary 匹配真实代码，不把 future work 写成已完成。

到达 `ready-to-create-PR` 后停止并报告 readiness。用户要求创建 PR 后，再进入 `PR -> PR review -> final closeout`。

final closeout 说明 what changed、what was verified、docs updates、finding status、remaining risks/owners、next entry point。
