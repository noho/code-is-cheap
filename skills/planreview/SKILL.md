---
name: planreview
description: "对重要契约、架构、迁移或状态机决策，以及显式指定的 plan 做 evidence-based adversarial review；判断是否足以指导已确认目标的正确实现，挑战假设、范围、切分、目标实现方案和过度设计，产出 plan review artifact。"
---

# Planreview

Planreview 通过可信反例和直接证据，判断 plan 是否有实际阻止正确实现已确认目标的问题。主动挑战隐藏耦合、错误假设、
不安全 sequencing、必要信息缺失和过度设计；允许无 material finding 直接通过，不以发现问题的数量衡量审核质量。

## When To Use

重要契约、架构、迁移或状态机决策在 implementation 前使用本 skill，包括涉及这些决策的 implementation、migration phase、
feature slice、schema/storage、concurrency/recovery 或 Gateflow handoff plan。用户或项目显式要求的 plan review 仍执行。
Gateflow 中简单计划由总控核对，不因它是 plan 就自动增加独立审核。

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

- 主动尝试证伪关键假设，以当前证据判断是否有 material issue，不预设一定存在重要问题。
- 不因为 good intent、partial fixes 或可能的 follow-up work 给 plan 加分。
- 如果方案只覆盖 happy path，把它视为真实弱点。
- 判断 plan 是否已明确目标行为、实现方向、必要职责/架构边界、重要契约与状态语义、影响范围和验证依据；
  缺陷类任务还须明确根因。函数拆分、局部数据结构、分支和算法留给实现者，需要实际代码判断的问题交完整代码审核。
- 找 failure modes，不做风格偏好 review。
- 挑战 motivation、scope、sequencing 和 hidden assumptions。
- 优先使用 plan artifact、source docs、code、tests、schemas、state machines 和 existing behavior 的直接证据。
- 不制造 blocker。可信但未证实的问题放到 `Open Questions` 或 `Residual Risk`。
- 对已证实的错误模型或职责边界检查是否解决根因；必要内部重构不因修改较大被否定。非必要机制优先删除或简化。

## Attack Surface

优先寻找高成本、危险、用户可见或难以发现的失败：

- scope、non-goals、ownership、file boundaries 或 implementation slice boundaries 不清；
- goal drift：plan 增加 Goal Confirmation 未确认的目标、验收标准、设计强化、风险修复或 future-slice work；
- plan 缺少正确实现所需的目标行为、关键契约、职责、状态语义或验证依据；
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

1. 识别 Goal Confirmation（若存在）和 plan 声称的 goal、non-goals、success signal、implementation boundary。
   Gateflow / Phaseflow plan review 必须把 Goal Confirmation 当作 binding scope contract；缺少 Goal Confirmation
   artifact 或等价 handoff 时，必须作为 open question 或 finding 记录。
2. 列出 plan 的关键 assumptions。
3. 用 code facts、design docs、tests 和 realistic edge cases 尝试证伪每个 assumption。
4. 压测 architecture boundaries：layering、ownership、dependency direction、public contracts、
   schema/storage contracts、external protocol boundaries，以及是否引入过度耦合。
5. 压测 execution semantics：state transitions、lifecycle、cancellation、retry、idempotency、concurrency、
   recovery、ordering、durability 和 partial failure。
6. 压测 implementation sequencing：默认一个 slice；只因必要验证依赖或安全迁移步骤拆分，每个 slice 有可独立验证的
   行为结果。检查是否过多、过细、按文件/层/角色机械拆分，或依赖顺序不安全、提前做 future-slice work。
   多文件、多模块或代码量本身不构成拆分理由，代码/测试/文档不能机械拆开；通常至多两个，三个及以上须有不可合并的
   具体依赖依据，不仅因数量重新请示。显式项目/用户切分约束按 handoff 执行。
7. 压测 validation：tests 是否证明目标行为、覆盖 failure paths 和 regressions，是否为了贴合实现而削弱 assertions。
8. 如果用户给了 focus area，重点 review 该区域，但仍报告其它有证据支撑的 material issue。
9. 区分 true blockers、deferred risks 和 questions。

## Special Review Lenses

按当前目标和实际风险应用相关 lenses，不逐项填写无关检查。re-review 聚焦已裁决 findings 和实际变更影响，
仅因影响扩大或新的有证据反例扩大范围。复用对当前版本仍有效且未受影响的证据；artifact 变更即新版本，受影响的旧证据须重新验证：

- **Goal-bound minimal design review**：检查每个 slice、design decision、验收标准和 validation 是否能直接映射到
  Goal Confirmation 已确认的 goal、success signal 或必要 correctness/safety 条件。若 plan 把实现中发现的潜在风险升级成
  新目标、架构强化、额外验收标准或 future-slice work，即作为 goal drift / scope creep 报告；正确处理应是 residual risk、
  deferred follow-up、open question，或重新做 goal confirmation。
- **Architecture boundary review**：验证 layering、ownership、dependency direction、public contracts、
  schema/storage boundaries、external protocol boundaries，以及 implementation details 是否泄漏到错误层级。
- **Best-practice review**：用当前需求、具体风险和代码证据判断 testability、maintainability、observability、failure handling
  和 dependency exposure，优先适用的项目惯例；不以“最佳实践”要求更多架构或保留已证实的结构性问题。
- **Optimal-solution review**：只比较有当前问题证据和具体收益的可信替代方案；检查是否遗漏更简单、安全、可维护的路径。
  不以个人架构偏好、假设未来需求或无界替代方案搜索阻塞实施，也不以少改行数保留错误模型或职责边界。
- **Overengineering review**：检查新增 abstraction、layer、wrapper、protocol、配置、migration 或 generalization 是否为
  当前目标与实际风险所必需；非必要机制建议删除或简化，必要机制才继续修正。范围内的根因重构不因改动较大被否定。
- **Overcoupling review**：挑战 plan 是否把可独立演进的概念、层、模块、协议、状态、测试或 rollout 绑定成一个
  必须同步修改的整体；检查是否出现跨层穿透、双向依赖、共享可变状态、过宽公共契约、为了一个 slice 修改太多 ownership
  边界且有具体联动风险、测试只能通过大集成链路证明、把本应基于 Protocol / interface 的结构设计成基于具体实现，或 future work
  被当前实现结构锁死。

当这些 lenses 发现问题时，按普通 finding 写出直接证据。不要把 “best practice” 或 “optimal” 当成抽象偏好；
必须说明具体风险、tradeoff 和更安全的替代方案。

审核建议本身也须保持已确认范围：只提出解决已证实问题所需的调整，不新增无依据的机制、切片、局部实现规格或验收要求。

## Finding Rules

每个 finding 必须 evidence-based 且 actionable。在 orchestration flow 中使用时，可使用这些 status：

- `accepted-candidate`：很可能成立，应由 controller 裁决；
- `needs-evidence`：可信但证据不足；
- `defer-candidate`：风险成立，但可能属于后续 slice、phase 或 issue。

finding 必须判断问题是否实际阻止正确实现已确认目标。措辞重复、明确约束已覆盖的局部表达式，或只能通过已实现代码
判断的问题，不得反复阻塞 plan；局部实现交给 implementation，实际代码问题交给 code review。在 Gateflow / Phaseflow 中，
由 controller 按既有裁决和 fix 状态处理，说明 destination 与非阻塞依据；未解决的真实 scope/contract/architecture/state/acceptance
blocker 仍阻塞，不得靠改名、延期或豁免放行。

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
- **问题类型**: 动机不成立 / 目标漂移 / 范围漂移 / 过度验收标准 / 架构边界 / 过度耦合 / 最佳实践偏离 / 非最优方案 / 过度设计 / 契约缺失 / 状态机漏洞 / 并发恢复风险 / 不必要切片 / 切片依赖不安全 / 缺少必要实现依据 / 测试缺口 / open question 未收敛 / 其它
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

始终把完整 plan review 结果写入 `docs/reviews/` 下的 markdown 文件。目录不存在时创建。

写 plan review artifact 前，必须从本机系统时钟生成 timestamp。不要推断、手写或编造 timestamp。不要使用
`001` 这类计数器。

运行或执行等价操作：

```bash
mkdir -p docs/reviews
ts="$(date +%Y%m%d-%H%M%S)"
```

Plan Review 使用生成的 timestamp：

```text
docs/reviews/plan-review-${ts}.md
```

写入前，确认路径匹配以下格式：

```text
docs/reviews/plan-review-[0-9]{8}-[0-9]{6}.md
```

artifact 必须包含：

- reviewed target and scope；
- assumptions tested；
- 使用上方格式的 findings；
- open questions；
- residual risks and suggested tracking destination；
- final plan review conclusion：`pass`、`pass-with-risks` 或 `fail`。

如果用户只要求 quick adversarial pass，仍必须写 artifact，但最终回复可以简洁。最终回复用户时，只简要说明
plan review conclusion 和 output file path。

## Boundaries

plan review 期间不要实施 fix。除非用户明确要求修复 accepted findings，否则不要编辑 plan。除非用户明确指示，
不要 stage、commit、push、approve、request changes 或对外 comment。
