---
name: deepreview
description: "用于对当前未合并 workspace changes、指定 GitHub Pull Request 或仓库全部代码做严格深度 code review；支持 `$deepreview`、`$deepreview 当前改动`、`$deepreview --base main`、`$deepreview --base ref`、`$deepreview --pr 123` 和 `$deepreview --all`；在 docs/reviews 下写完整 review artifact，优先 correctness、stability、maintainability findings，包含 adversarial failure pass、项目指令检查、过度耦合检查，并最终只简要报告结论和输出路径。"
---

# Deepreview

Deepreview 执行严格、基于证据的 code review。它有三种 mode：

- Current Changes Mode：review 当前 workspace 和 branch 相对 `main` 或指定 base ref 的 changes。
- PR Review Mode：review 指定 Pull Request 相对其 base branch 的完整 diff。
- All Repository Mode：review 仓库中的全部代码。

当用户要求 strict review、deep review、current unmerged changes review、PR review 或 full repository review 时，使用这个 skill。

## Invocation Handling

直接映射这些短指令：

```text
$deepreview
$deepreview 当前改动
$deepreview current changes
$deepreview --base main
$deepreview --base <ref>
```

使用 Current Changes Mode。裸 `$deepreview` 等价于 `$deepreview --base main`。如果提供了 `--base <ref>`，
就 review 当前 workspace 和 branch 相对该 base ref 的 changes，而不是默认 `main`。

```text
$deepreview PR 123
$deepreview pr 123
$deepreview --pr 123
```

对 PR number `123` 使用 PR Review Mode。

```text
$deepreview --all
$deepreview all
$deepreview full
$deepreview repo
$deepreview 全部代码
$deepreview 整个仓库
```

使用 All Repository Mode。

如果同时提供 `--all` 和 `--pr <number>`，必须询问用户是要 review 整个仓库还是指定 PR，不要自行选择。
如果同时提供 `--all` 和 `--base <ref>`，使用 All Repository Mode，并把 `--base` 仅作为可选参照基线记录到 scope。
如果同时提供 `--pr <number>` 和 `--base <ref>`，使用 PR Review Mode，并把 `--base` 仅作为需要核对 PR base
branch 的显式期望。如果用户要求 PR review 但没有给 PR number，先询问 PR number。若请求无法判断是 current
changes、PR mode 还是 All Repository Mode，只问一个简短澄清问题。

## Output Contract

始终把完整 review 结果写入 `docs/reviews/` 下的 markdown 文件。目录不存在时创建。

写 review artifact 前，必须从本机系统时钟生成 timestamp。不要推断、手写或编造 timestamp。不要使用 `001` 这类计数器。

运行或执行等价操作：

```bash
mkdir -p docs/reviews
ts="$(date +%Y%m%d-%H%M)"
```

Current Changes Mode 使用生成的 timestamp：

```text
docs/reviews/code-review-${ts}.md
```

PR Review Mode 使用生成的 timestamp：

```text
docs/reviews/pr-<pr_number>-review-${ts}.md
```

All Repository Mode 使用生成的 timestamp：

```text
docs/reviews/repo-review-${ts}.md
```

写入前，确认路径匹配以下格式之一：

```text
docs/reviews/code-review-[0-9]{8}-[0-9]{4}.md
docs/reviews/pr-<pr_number>-review-[0-9]{8}-[0-9]{4}.md
docs/reviews/repo-review-[0-9]{8}-[0-9]{4}.md
```

最终回复用户时，只简要说明 review conclusion 和 output file path。

## Review Method

Current Changes Mode：

1. 先理解 change intent：阅读相关 notes、diff、commit scope、关键实现和 tests，判断改动声称要解决什么问题。
2. 再对齐 contracts 和 sources of truth：检查 `AGENTS.md` / `CLAUDE.md`、相关 README 或 design docs、
   public interfaces、schemas、state machines、configuration、storage 或 external protocols。
3. 继续追踪 implementation paths：跟随关键 call chains、data flow、error paths 和 risk points，例如
   concurrency、idempotency、retry、cancellation、recovery。不要只 review 表层 diff。
4. 以真实入口为起点检查完整主链路。必须沿真实代码路径逐行走读，禁止猜测；root cause 必须来自同一条逻辑或数据路径上的直接证据。
5. 对关键 public functions，以及分支复杂、状态更新复杂或 I/O 边界明显的 private helpers，按这个顺序展开：

   ```text
   入参 -> 条件判断 -> 下游调用 -> 返回值 / raise -> 副作用
   ```

6. 检查所有关键 `if` / `elif` / `match` / dispatch / router 是否由真正决定该分支的事实驱动，而不是由间接信号、
   historical flag、cached marker 或碰巧相关字段驱动。
7. 对关键参数、配置、override 和 request options 展开生效链：来源 -> 覆盖关系 -> 最终消费点 -> 非法值处理。
   如果值只进入中间对象但最终未被执行层读取，或在链路中被重新默认化、覆盖、丢失、静默忽略，即报告。
8. 对返回值、持久化状态、外部可见状态、event/log/trace 做一致性检查。任何“返回成功但状态半提交”“外部显示完成但系统仍可恢复或运行中”
   或“错误被默认成功值掩盖”的情况，都必须沿同一执行事实追踪。
9. 执行 adversarial failure pass：默认怀疑，寻找最强的、基于证据的理由说明该 change 还不该 ship。如果只覆盖
   happy path，把它视为真实弱点。
10. 最后 review tests and risk：判断 tests 是否覆盖真实行为、failure paths、boundary conditions 和 regression
   surfaces，识别重要剩余未覆盖风险。

PR Review Mode 使用相同方法，但从 PR title/description 开始，并在最后的 tests and risk review 中包含
CI/check information。

All Repository Mode 使用相同方法，但没有单一 diff intent。reviewer 必须先建立 repository map：读取项目指令、
目录结构、README/design docs、public entry points、package/module boundaries、tests、schemas、storage、
external protocol adapters 和关键 runtime paths。然后按风险优先级选择真实入口与关键链路逐条走读。不能只做
文件列表式扫描，也不能把没有覆盖的区域写成已 review。

## Adversarial Attack Surface

adversarial failure pass 中，优先寻找高成本、危险、用户可见或难以发现的失败：

- auth、permissions、tenant isolation、trust boundaries、privilege escalation；
- data loss、corruption、duplication、stale facts、irreversible state changes；
- rollback safety、retries、partial failure、re-entrancy、idempotency gaps；
- race conditions、ordering assumptions、stale state、ownership conflicts、late writes；
- empty-state、null、timeout、cancellation、degraded dependency、unavailable dependency behavior；
- missing required parameters、type errors、invalid enum/string values、empty content/message/prompt、
  out-of-range numbers、negative numbers、oversized inputs；
- duplicate requests、conflicting parameters、already-terminal state being advanced again；
- version skew、schema drift、migration hazards、compatibility regressions、mixed old/new state；
- observability gaps，导致失败被隐藏、audit 不可能或 recovery 更困难；
- externally visible inconsistency between return values, persisted state, delivery state, events,
  logs, traces, and read models；
- external protocol/API boundary issues：payload shape mismatch、correlation id mismatch、one-to-one
  response mapping errors、stream/page/chunk assembly bugs、finish/error reason conflation、malformed
  response handling gaps、protocol-layer product semantics leakage；
- overcoupling issues：本应独立演进的层、模块、状态机、数据模型、工具、测试或 rollout 被绑成一个必须同步修改的整体；
  本应基于 Protocol / interface 的结构被设计成基于具体实现，导致替换实现、隔离测试或跨层复用时需要穿透修改；
- statically provable performance problems：loop-internal expensive recomputation or I/O、repeated
  JSON/regex parsing、list membership where set is required、unnecessary full loading、blocking I/O
  in async code、N+1 I/O patterns；
- test gaps，只证明 happy path。

## Large Scope Parallel Review

当 review scope 很大、跨多个模块，或同时涉及 state machine、storage、concurrency、contract、public API、migration
等多个高风险面时，可以使用 subagents 做并行专项 review，以提高覆盖和深挖质量。

使用 subagents 时必须遵守：

- 主 reviewer 仍对最终 review artifact 负责；
- 每个 subagent 必须有明确 scope，例如文件集合、真实入口、调用链、状态机、contract boundary、测试面或风险面；
- 不要让 subagent 泛泛 review 整个 diff；
- 每个 subagent 必须沿真实代码路径走读，只输出 evidence-based findings、open questions、residual risks 和未覆盖区域；
- 主 reviewer 必须整合、去重、复核证据链、裁决 severity，并丢弃无法被同一逻辑 / 数据路径直接证据支撑的 finding；
- 主 reviewer 必须检查不同 subagent 结论之间是否冲突，必要时回到代码路径复核；
- 最终 artifact 必须记录哪些区域由 subagent 覆盖，哪些区域仍未覆盖。

subagent 适合做并行深挖，不适合替代主 reviewer 的最终判断。不要把多个 subagent 输出直接拼接成 review 结论。

## Review Requirements

- 使用 code review mode。优先找真正影响 correctness、stability 或 maintainability 的 defects。
- 默认怀疑。目标不是证明改动看起来合理，而是找出最强证据说明它可能不适合 merge。
- 不因为 good intent、partial fixes 或可能的 follow-up work 给改动加分。
- 先检查改动是否违反 repository instructions，例如 `AGENTS.md` / `CLAUDE.md`。
- 重点关注 intent 与 implementation 的 semantic mismatch、logic errors、boundary conditions、regression risk、
  type issues、exception handling、resource release、concurrency safety、idempotency、data consistency、
  observability、missing tests，以及与 existing architecture constraints 的不一致。
- findings 必须基于直接证据：code、diff、docs、test gaps、CI information 或可复现推理。不确定的问题放到
  `Open Questions`，不要当成确定 defect。
- root cause 必须与触发输入、实际分支、状态写入、返回值或副作用处在同一条逻辑 / 数据路径上。禁止用间接迹象、
  相邻代码味道或“看起来相关”的字段替代根因证据。
- 审查 architecture boundary：下层接口不得泄漏上层治理、业务受理或展示状态；禁止反向 import；警惕跨层穿透调用。
- 审查 overcoupling / 过度耦合：检查代码是否把本应独立演进的层、模块、状态机、数据模型、工具、测试或 rollout
  步骤绑成一个必须同步修改的整体；是否出现跨层穿透、双向依赖、共享可变状态、过宽公共契约、为了局部行为修改过多
  ownership boundary，或 future work 被当前实现结构锁死。
- 审查 Protocol / interface 边界：本应依赖稳定 Protocol、interface、ABC 或公共契约的调用方，不应直接依赖具体实现类、
  concrete storage/runner/executor/client、内部 builder 或测试替身。若具体实现依赖导致替换实现、隔离测试、分层复用或
  contract evolution 需要跨模块联动，即作为 maintainability / architecture finding 报告。
- 审查 public API exposure：检查 public modules、package exports、README/examples 或便利 import 是否把内部实现对象呈现为推荐接口，
  诱导上层或调用方绕过稳定契约。若暴露面会造成 contract drift 或错误依赖内部对象，即报告。
- 审查 contract ownership：如果语义真源只在一层，契约归属该语义真源所在层；如果多个层都需要独立实现、产生、
  解释或持久化同一语义，且它描述的是层间协作协议而不是某一层的调用参数，则契约应落在公共契约。
- 审查 branch ordering：宽条件是否抢先命中导致更具体分支不可达；条件是否重叠但无明确优先级；是否缺少默认分支导致异常输入悄悄落空；
  dispatch/router/builder/handler 是否同时承担参数转换、分支选择和结果合并，导致分支逻辑被错误复用或漏判。
- 审查 structural clarity / spaghetti-code risk：控制流是否清晰，职责是否收敛，函数或类是否承担过多分支，状态是否被多处隐式修改；
  是否出现跨多层长链路 glue code、布尔标记驱动的隐式流程、深层嵌套、分支交叉复用、隐藏副作用、god function/object/dataclass
  或难以局部推理的实现。即使当前行为正确，只要结构让后续修改容易引入回归，也应作为 maintainability / architecture finding 报告。
- 审查 parameter effectiveness：关键参数必须能追踪来源、覆盖优先级、最终消费点和失效处理。若传入值与最终生效值之间没有直接数据链，
  或 caller 预期与实现优先级不一致，即报告。
- 凡是存在“真源状态 + 触发条件 + 状态写入 + 对外事件 / 副作用 + 后续收敛”的闭环，都按 state machine 审查。
  每个关键 state machine 至少展开正常主路径、失败路径、取消 / 超时 / interrupt 路径、resume / retry /
  redelivery / continuation 恢复路径，以及竞争写入、孤儿状态、cleanup 或外部终态收敛等并发 / 调和路径。
- 审查 state machine ownership：明确 state source of truth、谁有权推进状态、哪些状态是 terminal/absorbing、重复操作是否应幂等吸收。
  若同一事实存在多个可写真源、推进权分散、终态可回退/覆盖，或异常路径和正常路径使用不同转换规则，即报告。
- 审查 external protocol/API boundaries：协议适配层必须区分协议事实和产品语义；payload shape、关联 id、顺序、一一对应关系、
  stream/page/chunk 拼接、finish/error reason 和畸形返回必须有明确处理。不要把业务判断塞进协议层，也不要把协议错误当正常成功。
- 主动检查非预期输入：缺失必填参数、类型错误、非法枚举 / 非法字符串、空内容 / 空消息 / 空 prompt、越界数值、
  负数、超长输入，以及重复请求、冲突参数、已终态再次推进。
- 只报告可通过静态代码阅读证明的性能问题，例如循环内重复重计算或 I/O、重复 JSON/regex parsing、应使用 set 却用 list 成员查找、
  不必要全量加载、async 路径中的同步阻塞 I/O、N+1 I/O。不要提出猜测性优化建议。
- 不只问 tests 是否存在。要判断 tests 是否真正证明关键行为，是否遗漏 failure paths、boundary conditions 或
  regression scenarios，assertions 是否为了适配实现而被削弱。
- 每个 finding 必须回答：what can go wrong、为什么该 code path 脆弱、可能影响是什么、什么具体修改能降低风险。
- 宁可一个强 finding，也不要多个弱 finding。不要用 style feedback、naming feedback、低价值 cleanup 或无证据猜测稀释严重问题。
- 如果没有明确实质问题，写 `未发现实质性问题`。
- findings 放在最前面，并按 severity 排序。每个 finding 必须使用下方固定 finding format。
- findings 之后包含 `Open Questions` 和 `Residual Risk`；为空时写 `无`。
- 不要以 summary 开头。不要泛泛表扬。不要把风格偏好当作主要 findings。

最终输出前，检查每个 finding 是否：

- 绑定到具体 code location 或 explicit behavior；
- 在真实 failure scenario 下可信；
- evidence-based，而不是 speculative；
- 对修复问题的工程师可执行。

固定 finding format 用于强制 reviewer 识别 entry point、triggering input、actual branch、expected behavior、
actual behavior、direct evidence、impact、fix direction、fix risk 和 severity。

## Current Changes Mode

用户要求 review current code changes、current branch changes 或 unmerged changes 时使用。

review scope：

- 相对 selected base ref 的所有 workspace changes，默认 base 是 `main`；
- staged changes；
- unstaged changes；
- 当前 branch 上尚未 merge 到 selected base ref 的 committed changes。

判断前，检查相关 git diff、changed files、关键 implementation files、tests 和 project instructions。优先直接证据，
不要用间接迹象代替根因判断。

推荐命令：

```text
git branch --show-current
git status --short
git diff <base>...HEAD
git diff
git diff --cached
```

除非用户提供 `--base <ref>` 或 repository facts 表明 base 应不同，否则使用 `main` 作为 `<base>`。review artifact
中必须记录 selected base。

## PR Review Mode

用户要求 review PR 或提供 PR number 时使用。

review 前收集 PR facts：

- repository；
- PR number；
- title；
- author；
- head branch；
- base branch；
- URL。

review scope：

- PR 相对 base branch 的完整 diff；
- key implementation files；
- related tests；
- CI/check information，若相关。

推荐命令：

```text
gh repo view --json nameWithOwner --jq '.nameWithOwner'
gh pr view <pr_number> --json title,url,author,headRefName,baseRefName
gh pr diff <pr_number>
gh pr checks <pr_number>
```

如果无法读取 GitHub metadata，清楚说明 blocker，不要编造 PR facts。

## All Repository Mode

用户要求 review 全部代码、整个仓库、full repository review，或使用 `$deepreview --all` 时使用。

review scope：

- 仓库中所有生产代码；
- 与生产代码行为相关的 tests；
- public entry points、package/module exports、README/design docs；
- schemas、storage/migration、configuration、external protocol adapters；
- CI/check 配置，若它影响 review 结论。

先建立 repository map，再按风险优先级划分 review slices。至少记录：

- repository root；
- branch；
- review date/time；
- included directories；
- excluded directories and reason，例如 generated/vendor/build/cache；
- high-risk entry points and subsystems；
- parallel review coverage，若使用 subagents；
- not-covered areas，若因为范围过大无法完整走读。

推荐命令：

```text
git branch --show-current
git status --short
rg --files
find . -maxdepth 3 -type f \( -name 'README*' -o -name 'AGENTS.md' -o -name 'CLAUDE.md' \)
```

All Repository Mode 默认应使用 Large Scope Parallel Review。每个 subagent 或 review slice 必须有明确范围：
目录、入口、调用链、状态机、contract boundary、storage/schema、external protocol 或测试面。最终 artifact 必须清楚区分
covered、partially-covered 和 not-covered areas。

不要把全仓 review 做成纯 lint、命名或风格 review。仍然只报告有直接证据、真实执行路径或明确架构风险支撑的 material findings。

## Review Artifact Format

使用这个结构：

```markdown
# Code Review

## Scope

- Mode: current changes | PR | all repository
- Branch or PR:
- Base:
- Output file:
- Included scope:
- Excluded scope:
- Parallel review coverage: 无，或列出 subagent 覆盖的文件/链路/风险面与未覆盖区域

## Findings

### 编号-未修复-[严重程度（低/中/高/严重）]-finding简述
- **入口/函数**: 问题发生在什么执行入口或什么函数
- **文件(行号)**: 具体位置
- **输入场景**: 什么输入会触发问题
- **实际分支**: 代码实际走到了哪个分支
- **预期行为**: 按当前系统设计应该如何处理
- **实际行为**: 现在返回了什么、写入了什么状态、或漏做了什么
- **直接证据**: 具体判断条件、参数传递路径、返回值或状态更新位置（行号）
- **影响**: 错误 answer / 错误状态 / 静默失效 / 不可恢复 / 仅局部行为错误
- **建议改法和验证点**:
- **修复风险（低/中/高）**:
- **严重程度（低/中/高/严重）**:

## Open Questions

- 无，或列出阻碍 confident judgment 的问题。

## Residual Risk

- 记录 test gaps、CI gaps 或未检查区域。
```

如果没有 findings，保留简短的 `## Findings`，写 `未发现实质性问题`。

## Boundaries

review 期间不要修代码，除非用户明确要求 fix。除非用户明确指示，不要 stage、commit、push、approve、
request changes 或在 GitHub comment。

当这个 skill 在 Gateflow 中使用时，review findings 必须方便 controller 把每项裁决为 `accepted`、
`rejected-with-reason`、`deferred-with-owner` 或 `needs-more-evidence`。
