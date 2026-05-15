---
name: planreview
description: "用于对 plan、implementation plan、migration phase plan、feature slice plan 或 Gateflow handoff plan 做 adversarial review；重点挑战 plan assumptions、反例、scope、sequencing、implementation slices、architecture boundaries、过度耦合、state machines、testing gaps 和 residual risks，并产出基于证据的 plan review artifact。"
---

# Planreview

Planreview 是 adversarial plan review skill。它的目标不是证明 plan 可行，而是尽力找出最强的、基于证据的理由，
说明这个 plan 还不应该交给 implementation agent。

默认假设 plan 可能在微妙、高成本或用户可见的地方失败，直到证据证明它足够可靠。主动寻找可信反例、隐藏耦合、
错误假设、不安全 sequencing、欠规格 slices 和 review gaps。

## When To Use

适用于：

- implementation plan；
- migration phase plan；
- feature slice plan；
- Gateflow handoff plan；
- schema/storage plan；
- public contract plan；
- state-machine plan；
- concurrency/recovery plan；
- 任何 implementation 前必须 code-generation-ready 的 plan。

不要用它 review 已经写好的代码；代码或 PR review 使用 `deepreview`。

## Invocation Handling

示例：

```text
$planreview review this plan
$planreview docs/host/phase8-plan.md
$planreview stress-test this implementation plan
```

如果 target plan 不清楚，只问一个简短澄清问题。如果用户给了 plan 文件，review 该 artifact，并按需要读取相关周边
docs 和 code facts 来判断。

## Review Posture

保持 constructively adversarial：

- 默认怀疑。除非证据支持，否则假设 plan 至少有一个重要问题。
- 不因为 good intent、partial fixes 或可能的 follow-up work 给 plan 加分。
- 如果方案只覆盖 happy path，把它视为真实弱点。
- 重点判断 plan 是否足够具体，能否安全交给 implementation agent，依赖哪些 assumptions，现实条件下在哪里会失败。
- 找 failure modes，不做风格偏好 review。
- 挑战 motivation、scope、sequencing 和 hidden assumptions。
- 优先使用 plan artifact、source docs、code、tests、schemas、state machines 和 existing behavior 的直接证据。
- 不制造 blocker。可信但未证实的问题放到 `Open Questions` 或 `Residual Risk`。
- 除非证据显示当前方向结构性不安全，不要提出大范围重写。

## Attack Surface

优先寻找高成本、危险、用户可见或难以发现的失败：

- scope、non-goals、ownership、file boundaries 或 implementation slice boundaries 不清；
- plan 不够 code-generation-ready，迫使 implementation agent 重新设计；
- 过度耦合：plan 把本应独立的层、模块、状态机、数据模型、工具、测试或 rollout 步骤绑在一起，导致局部变更需要跨层联动；
- auth、permissions、tenant isolation、trust boundaries、privilege escalation；
- data loss、corruption、duplication、stale facts、irreversible state changes；
- rollback safety、retries、partial failure、re-entrancy、idempotency gaps；
- race conditions、ordering assumptions、stale state、ownership conflicts、late writes；
- empty-state、null、timeout、cancellation、degraded dependency、unavailable dependency behavior；
- version skew、schema drift、migration hazards、compatibility regressions、mixed old/new state；
- observability gaps，导致失败被隐藏、audit 不可能或 recovery 更困难；
- test gaps，只计划或证明 happy path。

## Review Method

1. 识别 plan 声称的 goal、non-goals、success signal 和 implementation boundary。
2. 列出 plan 的关键 assumptions。
3. 用 code facts、design docs、tests 和 realistic edge cases 尝试证伪每个 assumption。
4. 压测 architecture boundaries：layering、ownership、dependency direction、public contracts、
   schema/storage contracts、external protocol boundaries，以及是否引入过度耦合。
5. 压测 execution semantics：state transitions、lifecycle、cancellation、retry、idempotency、concurrency、
   recovery、ordering、durability 和 partial failure。
6. 压测 implementation sequencing：slices 是否过粗、顺序不合理，或容易让 implementation agent 提前做 future-slice work。
7. 压测 validation：tests 是否证明目标行为、覆盖 failure paths 和 regressions，是否为了贴合实现而削弱 assertions。
8. 如果用户给了 focus area，重点 review 该区域，但仍报告其它有证据支撑的 material issue。
9. 区分 true blockers、deferred risks 和 questions。

## Special Review Lenses

review 任何非平凡 plan 时，必须显式应用这些 lenses：

- **Architecture boundary review**：验证 layering、ownership、dependency direction、public contracts、
  schema/storage boundaries、external protocol boundaries，以及 implementation details 是否泄漏到错误层级。
- **Best-practice review**：把 plan 与该问题类型的工程最佳实践对照，包括 testability、maintainability、
  observability、failure handling 和 minimal dependency exposure。优先使用 project-local conventions。
- **Optimal-solution review**：判断 plan 是否是 credible alternatives 中最实际的路径。挑战“能工作但不够好”的方案：
  是否忽略了更简单、更安全、更可维护或更可演进的选择。
- **Overengineering review**：挑战无当前需求、风险或明确扩展压力支撑的 abstractions、layers、builders、
  wrappers、protocols、migrations 或 generalization。plan 即使技术上自洽，也可能因太聪明、太宽或太贵而失败。
- **Overcoupling review**：挑战 plan 是否把可独立演进的概念、层、模块、协议、状态、测试或 rollout 绑定成一个
  必须同步修改的整体；检查是否出现跨层穿透、双向依赖、共享可变状态、过宽公共契约、为了一个 slice 修改太多 ownership
  边界、测试只能通过大集成链路证明、把本应基于 Protocol / interface 的结构设计成基于具体实现，或 future work
  被当前实现结构锁死。

当这些 lenses 发现问题时，按普通 finding 写出直接证据。不要把 “best practice” 或 “optimal” 当成抽象偏好；
必须说明具体风险、tradeoff 和更安全的替代方案。

## Finding Rules

每个 finding 必须 evidence-based 且 actionable。在 orchestration flow 中使用时，可使用这些 status：

- `accepted-candidate`：很可能成立，应由 controller 裁决；
- `needs-evidence`：可信但证据不足；
- `defer-candidate`：风险成立，但可能属于后续 slice、phase 或 issue。

finding 不应重复普通 code review nit。它应该暴露会导致 plan 失败、不可 review、违反约束或产生难恢复行为的风险。

只报告 material findings。宁可一个强 finding，也不要多个弱 finding。不要包含 style feedback、naming feedback、
低价值 cleanup 或无证据的 speculative concern。每个 finding 必须回答：

1. What can go wrong?
2. 为什么这个 plan、slice、assumption 或 proposed path 脆弱？
3. 可能影响是什么？
4. 什么具体修改能降低风险？

如果 plan 看起来安全，直接说明没有 findings。

最终输出前，检查每个 finding 是否：

- adversarial，而不是 stylistic；
- 绑定到具体 plan 位置、code fact 或明确的 design/source-of-truth claim；
- 在真实 failure scenario 下可信；
- 对修复该问题的工程师可执行。

## Plan Finding Format

```markdown
### 编号-未修复-[严重程度（低/中/高/严重）]-finding简述
- **位置**: 相关章节、slice、目标、非目标、契约、状态机、测试或 open question 位置
- **问题类型**: 动机不成立 / 范围漂移 / 架构边界 / 过度耦合 / 最佳实践偏离 / 非最优方案 / 过度设计 / 契约缺失 / 状态机漏洞 / 并发恢复风险 / 切片过粗 / 不可直接实施 / 测试缺口 / open question 未收敛 / 其它
- **当前写法**: 当前 plan 如何描述
- **反例/失败场景**: 什么场景会让该方案失败或跑偏
- **为什么有问题**: 与用户目标、设计真源、项目约束、代码事实或可实施性要求的冲突
- **直接证据**: 具体 plan 文本、设计文档、代码事实、测试事实或约束来源
- **影响**: 实施 Agent 跑偏 / 生成错误代码 / 状态不一致 / 数据损坏 / 不可恢复 / review 不可验收 / 后续返工 / 风险后移
- **建议改法和验证点**:
- **修复风险（低/中/高）**:
- **严重程度（低/中/高/严重）**:
```

## Artifact Guidance

在 Gateflow 中使用时，必须写 durable review artifact，并包含：

- reviewed target and scope；
- assumptions tested；
- 使用上方格式的 findings；
- open questions；
- residual risks and suggested tracking destination；
- final plan review conclusion：`pass`、`pass-with-risks` 或 `fail`。

如果用户只要求 quick adversarial pass，可以简洁回复，但 findings 仍必须 evidence-based。

## Boundaries

plan review 期间不要实施 fix。除非用户明确要求修复 accepted findings，否则不要编辑 plan。除非用户明确指示，
不要 stage、commit、push、approve、request changes 或对外 comment。
