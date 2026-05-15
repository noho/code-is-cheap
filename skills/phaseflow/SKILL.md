---
name: phaseflow
description: "基于两个参数文档驱动 phase 开发总控：design_doc 作为设计真源，control_doc 作为实施总控文档；遵循 $gateflow / /gateflow 和 $init-agents / /init-agents 的多 Agent 约定，推进 phase design、plan、implementation、review、risk tracking 和 ready-to-open-draft-PR；用户授权后继续推进 draft PR gate 到 draft-PR-pass。用户说按总控文档开发 phase、继续下一阶段、使用 phaseflow 或给出设计文档和总控文档时使用。"
---

# Phaseflow

## Purpose

`phaseflow` 是 `$gateflow` / `/gateflow` 的项目 phase 总控 wrapper。它不替代 `$gateflow`，而是在给定
`design_doc` 和 `control_doc` 后，规定 controller 如何读取设计真源、维护总控状态、派发多 Agent、裁决 review
结果，并把遗留问题和潜在风险追踪到总控文档或后续 phase。

## Invocation

推荐调用：

```text
$phaseflow design_doc=docs/host/design.md control_doc=docs/host/implementation-control.md
```

也接受位置参数：

```text
$phaseflow docs/host/design.md docs/host/implementation-control.md
```

参数含义：

- `design_doc`：设计真源。所有 phase design、plan 裁决和 review 裁决必须以它为核心依据之一。
- `control_doc`：总控文档。用于读取当前 phase 状态、目标、追踪项、遗留问题、潜在风险和下一步入口；phase
  结束时必须及时更新。

如果两个文档缺失、路径不明确或无法读取，先停下来询问，不要进入 `$gateflow`。

## Startup Contract

启动后第一步必须先读取 `control_doc`，再按需要读取 `design_doc`。读完后先回复用户，不能直接开始实现。

首次回复必须包含：

- 当前从 `control_doc` 识别出的 phase / work unit；
- 接下来应进入哪一步：discussion、plan、implementation、aggregate deepreview、ready-to-open-draft-PR、draft PR gate、draft-PR-pass 或其它；
- 将如何使用 `design_doc` 和 `control_doc`；
- 将如何派发 Agent；
- 将如何做 review 裁决、风险追踪和总控状态更新；
- 如果存在疑问，列出 blocking open questions。

如果已经知道下一步、知道怎么做，简短复述并等待或继续执行用户明确授权的动作；如果有疑问，先提问。

## Controller Role

controller 是总控 Agent。除 `$gateflow` 已定义的职责外，还必须：

- 在读懂 `design_doc` 的基础上裁决 plan review、code review、aggregate deepreview 和 PR review 结果；
- 对每个 accepted / rejected / deferred / needs-more-evidence finding 形成 durable 裁决记录；
- 维护 `control_doc` 中的 phase 状态、已完成项、当前 gate、artifact 路径、commit hash、review 结论和 next entry point；
- 每个 phase 开发结束后，把遗留问题和潜在风险写入 `control_doc`，或明确指定到后续 phase / issue / owner；
- `ready-to-open-draft-PR` 前，`control_doc` 必须更新为当前 phase 完成，且所有 tracking items 都有明确 owner。

controller 不得亲自执行 specialist work，除非用户明确要求；必须按 `$gateflow` / `/gateflow` 约束派发
planning、implementation、fix、review 和 re-review handoff。

## Agent Routing

使用 `$init-agents` / `/init-agents` 获取当前 Agent 通信和 pane 规则。若与本 skill 有冲突，以本 skill 的
phase routing 为准，并记录原因。

默认路由：

- implementation / fix：`AgentCodex` 和 `AgentOpus` 可任选其一。若需要并行实施，必须先确认 file ownership
  互不重叠，并由 controller 明确拆分 scope。
- review / re-review：`AgentMiMo`、`AgentDS`、`AgentGLM` 可任选其二，形成两份独立 review；controller 负责整合、
  去重和裁决 findings。

如果某个 Agent 不在，controller 必须记录不可用事实，并选择可用 Agent 替补或询问用户。

## Gateflow Differences

除非本节明确覆盖，其余全部遵循 `$gateflow` / `/gateflow`。

与普通 `$gateflow` 的差异：

- `design_doc` 是设计真源，`control_doc` 是总控真源；所有 plan、review 裁决和 phase 状态必须回到这两个文档校验。
- design 和 plan 裁决的核心问题是：是否以最佳实践保证 `design_doc` 和/或 `control_doc` 中设计目标达成，同时不引入过度设计。
- `ready-to-open-draft-PR` 前的 aggregate review 必须从 `AgentMiMo`、`AgentDS`、`AgentGLM` 中任选其二同时做。
  若无法取得至少两份独立 aggregate review，必须记录原因，并说明是否需要用户接受单 reviewer 风险。
- controller 必须维护 phase 级遗留问题和潜在风险追踪，不允许把 residual risk 停留在 conversation-only 状态。
- `ready-to-open-draft-PR` 前，`control_doc` 必须更新为当前 phase 完成，且所有 tracking items 都有明确 owner。
- 用户授权进入 draft PR gate 后，controller 继续遵循 `$gateflow` / `/gateflow` 自动推进 push、create draft PR、
  PR review、fix、re-review、accepted PR review commit、push，直到 `draft-PR-pass`；merge、approve、mark ready for review、
  request reviewers、delete branch、对外 comment 或创建/修改外部 issue 仍需额外授权。

## Review Judgment Lens

controller 裁决 design / plan / review finding 时，必须显式考虑：

- 是否满足 `control_doc` 的 phase 目标和 success signal；
- 是否符合 `design_doc` 的架构边界、状态机、契约和非目标；
- 是否采用项目内最佳实践来达成目标；
- 是否引入过度设计、过度耦合或把本应基于 Protocol / interface 的结构设计成基于具体实现；
- 是否让后续 phase 更难推进、让 residual risk 后移但无 owner，或让 implementation agent 需要重新设计。

## Control Document Updates

每个 phase 关键点都要更新或准备更新 `control_doc`：

- plan/re-review 通过后：记录 plan artifact、plan review artifacts、accepted plan commit hash；
- 每个 slice commit 后：记录 slice 状态、artifact、review 结论、commit hash、未覆盖项；
- aggregate deepreview/re-review 通过后：记录 aggregate review artifact、accepted deepreview commit hash；
- ready-to-open-draft-PR 前：把当前 phase 标记为完成，记录 draft PR readiness、剩余风险、owner、后续 phase / issue destination。
- draft-PR-pass 后：记录 draft PR URL、PR review artifacts、accepted PR review commit hash、follow-up push 状态、
  remaining risks / owners 和 next entry point。

如果 `control_doc` 没有合适位置记录这些内容，controller 必须提出具体写入位置或结构，不要跳过。

## Initial Prompt Skeleton

当用户只给出两个文档并要求开始时，controller 应按这个意图执行：

```text
接下来遵循 $gateflow / /gateflow 开始开发。
设计真源在 <design_doc>，总控文档是 <control_doc>。
先阅读总控文档，再按需要阅读设计真源。
你是总控 Agent：负责派发 Agent、裁决 review、形成裁决文档、维护遗留问题和风险追踪、更新总控状态。
AgentCodex / AgentOpus 可任选其一用于 implementation / fix；AgentMiMo / AgentDS / AgentGLM 可任选其二用于 review / re-review，aggregate review 必须至少两者同时做。
design 和 plan 裁决重点考虑：最佳实践是否保证总控文档中的设计目标达成，且不引入过度设计。
请先读 control_doc 后复述你知道的下一步；有疑问先提问。
```
