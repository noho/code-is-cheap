---
name: gateflow
description: "单个 work unit 的 gated 开发流程。用于 feature、issue、bug fix、migration、refactor、schema/public contract change 或 architecture-sensitive task；可选接收 design document；先读代码并从第一性原理确认目标/非目标，经用户确认后按 plan、review、implementation、review、deepreview、draft PR gate 自动推进到 draft-PR-pass。"
---

# Gateflow

Gateflow 只定义单个 `work unit` 的流程和 gate。work unit 可以是 feature、issue、bug fix、migration、refactor、
schema/public contract change 或 architecture-sensitive task。

## Core Principles

- 先看代码和事实，再判断 work unit 是否成立。
- 进入 plan 前，先用通俗语言向用户确认目标、非目标、边界和成功信号。
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

固定顺序：

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

Gate Order entry 与下方 section 的绑定是执行约束。必须按对应的 `## Gate: ...` 或 `## Gate Group: ...` section 执行：

- `goal confirmation` -> `## Gate: goal confirmation`
- `plan` -> `## Gate: plan`
- `implementation -> code review -> fix -> re-review -> accepted slice commit` -> `## Gate Group: implementation slice`
- `plan review`、`code review`、`aggregate deepreview`、`PR review` 及其 `fix` / `re-review` -> `## Gate Group: review / fix / re-review`
- `ready-to-open-draft-PR -> ... -> draft-PR-pass` -> `## Gate Group: draft PR`
- `final closeout` -> `## Gate: final closeout`

不得把 `draft-PR-pass` 当作 work unit 完成；必须继续执行 `final closeout` gate。

多 slice 时重复：

```text
implementation -> code review -> fix -> re-review -> accepted slice commit
```

直到所有 approved slices 完成。

## Stop Conditions

除以下情况外，用户确认目标后自动推进：

- blocking open question 影响 scope、architecture、contract、schema、file ownership、state transition、implementation strategy、
  test expectation 或 user-visible behavior；
- branch、dirty changes、file ownership、commit scope 不清，无法安全创建 checkpoint；
- validation failure、unclassified residual risk、deferred finding 或 missing artifact 需要用户决策；
- 需要 merge、approve、mark ready for review、request reviewers、delete branch、对外 comment 或创建/修改外部 issue。

## Gate: plan

plan 必须 code-generation-ready，即可以直接指导实现，不需要重新设计方案、发明契约、猜 file ownership、猜 state transition
或决定 test scope。

plan 必须包含：

- goal / motivation / success signal；
- non-goals / scope boundary；
- design document alignment（如有）；
- first-principles judgment and direct code evidence；
- affected files/modules；
- contract/schema/state-machine/public-interface changes；
- implementation decisions；
- small implementation slices；
- tests/validation commands and expected assertions；
- docs decision；
- risks/open questions；
- completion report format。

plan 必须显式说明为什么当前方案没有过度设计。

## Gate Group: implementation slice

每个 slice 必须足够小，适合一次 implementation pass 和一次 review pass。每个 slice 必须写清：

- id/name、objective、expected outcome；
- allowed files/modules；
- prerequisites/dependencies；
- exact allowed changes；
- functions/classes/types、call paths、data flow、state transitions、error handling、invariants；
- non-goals；
- tests/validation commands and expected assertions；
- completion signal and stop condition。

implementation 只能做当前 approved slice，除非 approved plan 明确允许一次做多个 slice。

## Gate Group: review / fix / re-review

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

review gate 通过条件：

- review artifact 已记录 artifact path；
- accepted findings 都有 fix/re-review 状态；
- re-review 已回写或列出最终 finding 状态；
- 没有 blocking open question；
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
- plan review / re-review artifact；
- implementation artifact for each slice；
- code review / re-review artifact for each slice；
- fix artifact when fixes occur；
- aggregate deepreview / re-review artifact；
- PR review / re-review artifact；
- final closeout summary。

artifact 必须记录 gate、work unit、scope、changed files 或 reviewed target、decisions/findings、validation、docs decision、
residual risks、completion status 和 artifact path。

## Commits

review loop 通过、artifact 完整且没有 blocking open question 后，自动创建 protected local commit：

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
- aggregate deepreview 已执行，accepted findings 已修复并 re-reviewed；
- accepted deepreview commit 已创建；
- tests/type checks 已运行或失败已说明；
- docs decision 已完成；
- deferred findings/residual risks 有 owner/destination；
- 如果当前 work unit 是 issue，创建 draft PR 时 PR body 必须关联 issue：完整解决时使用 GitHub closing keyword（如 `Closes #123`），部分解决或仅关联时使用非关闭引用（如 `Related to #123`）并说明剩余 owner/destination；
- draft PR summary 匹配真实代码，不把 future work 写成已完成。

到达 `ready-to-open-draft-PR` 后自动：

```text
push
-> create draft PR
-> PR review
-> fix
-> re-review
-> accepted PR review commit
-> push
-> draft-PR-pass
```

PR review 有 accepted findings 时，必须自动修复并 re-review。PR review 若无 accepted findings，也必须提交 PR review artifact /
pass evidence 并 push。

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

如果当前 work unit 是 issue，`final closeout` gate 必须确认：

- PR body 已关联 issue；完整解决时使用 closing keyword，部分解决时不得使用会错误关闭 issue 的 closing keyword；
- issue 已添加 closeout comment，指向 draft PR，并说明 remaining risks / owners 和 merge 后 issue 是否会自动关闭。

若 draft PR 未关联 issue、issue closeout comment 未添加、缺少权限、issue number 不明确，或 closing keyword 会错误关闭未完成 issue，不得输出 final closeout pass，必须停止并询问用户。
