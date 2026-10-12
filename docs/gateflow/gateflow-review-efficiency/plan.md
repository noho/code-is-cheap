# Plan — Gateflow review efficiency

本 artifact 属于 `gateflow-review-efficiency` 的 `plan` gate，供总控验收并派发 plan review；尚未实施或通过 review。工作分支为 `feat/gateflow-review-efficiency`，源码基线为 `83e534f71adfdd4d8a0c353642a37dd364045504`。总控持有裁决、状态推进、accepted commits 和后续交付权；本 plan Agent 只写本文件。

## Binding scope 与依据版本

[goal.md](goal.md) 是唯一已确认目标契约，[confirmation.md](confirmation.md) 已记录授权；[state.md](state.md) 的本次输入状态为 `plan`。没有独立 design document，不从其它项目或业务任务引入需求。下列 SHA-256 标识本次实际读取的 artifact 内容；后续派发由总控交接可取回的对应版本，不能只引用可变文件名或一句历史 pass。原消费版本归档于 [evidence/plan-inputs/](evidence/plan-inputs/)，与表中hash严格一致；当前授权以goal.md和confirmation.md中的最新用户更正为准。总控在正常收取后仅同步撤销probe的验收文字，未改变Sol的实现决定。

| 输入 | 本次读取版本 / SHA-256 |
| --- | --- |
| [goal.md](goal.md) | `797e355f62e2ab0fe8f0547235032749897239307b6118e0dd995415794797d7` |
| [confirmation.md](confirmation.md) | `38b5ed9b4986a54f00849e946bcf186c1b576d1c726d3ea15f3a45961004f475` |
| [state.md](state.md) | `5249fbfb6a1797a088e6fd13f40975a2a1a9f4214f2d70d2959ff1da465ef0ea` |
| [AGENTS.md](../../../AGENTS.md) | 基线 commit；SHA-256 `7589427df6bd68904a3ef45140c17d0ea3469c896ae25c7e4bbc6a789bb37d45` |
| 当前安装 Gateflow `/Users/leo/.codex/skills/gateflow/SKILL.md` | SHA-256 `04e60bd1bf3965eed36b4493f6bd0f95ec032babd112c0fbe463aacebad92f60`；`cmp` 确认与基线仓库版本一致 |

源码证据均以该基线 commit 的文件为准，可用 `git show 83e534f71adfdd4d8a0c353642a37dd364045504:<path>` 取回；行号仅定位基线，不冒充未来版本。当前 goal/confirmation/state 未跟踪，accepted plan checkpoint 应保留实际消费的依据版本；本 Agent 不创建 checkpoint 或修改 state。

## 目标、动机与成功信号

将用户批准的四项规则落实为简短且一致的 Agent 指令：三层审核各自履行实质职责；跨 gate 复用仍适用的真实验证；没有待修 finding 且其它放行条件满足时直接到对应 accepted commit；用明确可取回的 artifact 版本引用未变事实。

动机是现有文本把综合审核、验证和 fix/re-review 读成无条件重复，增加了同一工作事实的重复处理。成功信号是代表情形能得出明确的审核责任、验证适用性和下一 gate，真实 blocker、`needs-more-evidence`、失效或不足证据仍不能放行；不声称任何未实测的时间或 token 收益。

完整 work unit 的 review、draft PR、closeout、经授权的 skill sync 与部署文本核对仍按最新 goal 执行；用户已撤销两次运行时 probe，它们不派发且不作为结案条件。它们属于总控后续 gates，不是本 plan Agent 的动作，也不拆成额外业务 slice。

## 第一性原理判断与直接源码证据

一次独立审核的价值是产生当前 gate 所负责的独立判断；同一版本的同一验证结果可作为事实复用，但不能替代该判断。fix/re-review 的价值是确认实际修复及影响；没有修复时，应保留 review、裁决和 accepted checkpoint，不能制造空修复。artifact 的价值是保留可审计事实与当前决策，稳定事实可引用，变化必须明确记录。这些问题可通过现有 workflow 文本解决，无需运行时机制。

| 基线位置 | 当前事实与必要改动 |
| --- | --- |
| `skills/gateflow/SKILL.md:64–112`、`:143–144`、`:310–320` | 主 Gate Order、多 slice 序列、draft PR 序列无条件列出 fix/re-review；状态禁止 skip 的表述需与条件步骤一致。 |
| `skills/gateflow/SKILL.md:94`、`:210–249` | 三个代码审核 gates 都要求 Deepreview，但未分工；复用主要写在 re-review；放行条件需显式保留真实证据与 `needs-more-evidence` 阻断。 |
| `skills/gateflow/SKILL.md:264–277`、`:279–287`、`:298–328` | artifact 要求和 accepted commits 已存在；引用及无 fix pass 应接入这些既有规则，而非新增例外。 |
| `skills/deepreview/SKILL.md:97–132`、`:249–270`、`:272–331`、`:380–429` | 全面 review method、完整变更 scope 和 PR mode 同方法会造成重复解读；需说明 Gateflow 的职责分配与事实复用。PR 精确 OID、快照/hash、同版深挖和收尾检查已经明确，全部保留。 |
| `skills/phaseflow/SKILL.md:100–127`、`:182–227`、`:251–268`、`:289–298` | 版本交接已存在，但复制的 Gate Order/多 slice 顺序及状态推进需要同步条件语义；沿用已有交接与控制文档内容。 |
| `skills/planreview/SKILL.md:93–99`、`:124–127`、`:162–198` | 已支持按 finding/变更影响 re-review 与有效证据复用；要求完整 review 结果，但没有要求复制全部历史事实。当前没有必须修改的冲突。 |

## 最小文件范围与 docs decision

产品源改动为三份 SKILL 的必要文本段落，按一个 workflow 契约一起实施：

| 文件 | 实现范围 |
| --- | --- |
| `skills/gateflow/SKILL.md` | 三层职责、跨 gate 验证适用性、所有 review loops 的条件 fix/re-review、对应序列/状态/放行条件、artifact 引用。必要时同步 readiness 和 commits 周边表述，消除内部冲突。 |
| `skills/deepreview/SKILL.md` | 简短说明在 Gateflow 下如何按 slice/aggregate/PR 职责实质审核并复用适用事实，使 Review Method、mode scope 与 artifact 要求兼容；保留独立调用默认严格审核和全部 PR 版本规则。 |
| `skills/phaseflow/SKILL.md` | 同步重复 Gate Order、多 slice 表达、条件状态推进；在既有 handoff 中交接职责和适用的证据版本，不复制一套审核/验证算法。 |

`skills/planreview/SKILL.md` 已读但不计划修改。若实施发现其明确条文确实与上述已确认规则冲突，先记录具体证据交总控裁决，再仅作必要文字调整；不因已读取或希望对称而预设改动。`agents/openai.yaml`、README、runner、validator、models、provider、工具脚本、业务代码及其它任务均不改。docs decision：产品说明落在必要 SKILL 文本，具体交接、检查、裁决和结果落在本 work unit gate artifacts；不新增用户流程或重复说明文档。

gate artifacts 由相应 gate 的现有权限单独产生：工作单元记录位于 `docs/gateflow/gateflow-review-efficiency/`，Planreview/Deepreview 仍使用各自既有 `docs/reviews/` 输出契约。本 plan 的写权限仅为 `plan.md`。

## 必要实现决定与契约

### 1. 三层审核职责

- **slice code review**：独立审核当前 approved slice 的正确性、必要契约/状态变化、边界和失败路径、测试/文本验证是否能证明该增量。沿真实受影响路径检查；不是只看 diff 或接受实现 Agent 的自报 pass。
- **aggregate deepreview**：独立检查各 accepted slices 的组合、接口/状态/共享假设交互、整体目标覆盖与遗漏，以及既有证据对当前整体版本是否适用。只有一个未变 slice 时，仍完成整体目标和遗漏判断并引用 slice 证据，无需重新全面审核同一 correctness 范围。
- **PR review**：独立检查实际交付 PR 的身份/版本、完整 diff 是否与 accepted 工作一致、title/body、CI/checks 和新增或变更部分的影响。即使代码未变，也实际执行既有精确 OID/快照与收尾核对，不能引用旧 metadata 代替。新增变更、交互风险或证据反例须追踪受影响实现、依赖和 tests。

三层都继续使用 Deepreview，保留适用的独立审核数量和当前项目两路并行 reviewer。各 reviewer 自己审查证据和具体疑点，形成当前 gate 的实质判断；不能把历史结论照抄成独立判断。上述分工只限定 Gateflow gate 的重复工作职责，不放宽 standalone Current Changes、PR 或 All Repository Mode 的默认严格范围。

### 2. 跨 gate 的真实验证复用

消费旧验证前，核对验证来源和结果、实际被验证的版本/范围，以及当前代码、依赖、配置和相关环境。明确说明当前 gate 所需断言是否仍由该证据支持；裸 pass、身份不明、证据不可取回或未覆盖所需行为都不能用于放行。

fix 或其它变化发生后，重验受影响断言和交互，并重新判断未受影响证据的适用性。只有实际影响、证据反例或项目强制检查要求才扩大到全量重跑；不能把 mandatory checks 省略成 reuse。独立 reviewer 可为具体疑点主动调查/执行验证，不要求各 gate、各 reviewer 无条件重复同一整套命令。

不新增验证缓存、工具、字段或 waiver。结果、版本、环境事实、复用理由或重验范围写在现有 artifact 的 reviewed target/scope、validation 和 decision 内容中。artifact 本身变化也形成新版本；受影响证据重新验证，未受影响且可取回的历史事实可继续引用。

### 3. 所有 review loops 的条件推进

沿用既有 gate 名称、finding 裁决、四种 fix 状态和 accepted commit 名称；不增设 gate/state/status。对 plan review、slice code review、aggregate deepreview、PR review 统一以下语义：

```text
review
  -> 有实际需要的修复：fix -> re-review -> 对应 accepted commit
  -> 无待修 finding 且全部放行条件成立：记录 pass -> 对应 accepted commit
```

`记录 pass` 是既有 artifact/裁决动作，不是新 gate。主 Gate Order、section 绑定、多 slice 与 draft PR 序列都明确标注 fix/re-review 的条件性；Phaseflow 复制的顺序保持相同含义。固定必需 gates 的相对次序不变，条件不适用不是跳过必需审核。

放行仍要求必要独立 review 和 artifact 已完成、所需验证有效且充分、accepted findings 的实际修复已被 re-review 验证并回写最终状态、延期符合既有授权/非阻塞理由/owner/destination 要求、无真实 blocker/未解决 `needs-more-evidence`，且 residual risks 已分类。accepted 列表为空不足以证明 pass。补充缺失证据在当前 review 职责内完成；若需实际修复才进入 fix/re-review；证据不全时保持当前 gate，不制造空 fix 来占位。

current gate / next entry point 始终写下一项实际尚未完成的适用 gate：无 fix pass 后到对应 accepted commit；真实 fix 后到 re-review；未满足放行条件时仍停留在当前 review/fix/re-review。controller 读取 artifact 并裁决后推进，子 Agent 无推进权。各类 accepted checkpoint、PR artifacts、final push、`draft-PR-pass` 与 final closeout 的既有约束保留。既有 PR no-commit pass 规则不扩大；本轮若产生待提交 review artifact，按既有规则提交，而不是制造空修复或免除 checkpoint。

### 4. artifact 的可追溯引用

未变且已确认的 goal、scope、plan、实现或验证事实可以引用。引用至少明确 artifact 路径、可取回的版本身份（既有 commit、内容 hash 对应的保存快照等）及相关事实/章节；内容必须真实存在、可读取并适用于当前目标。hash 只标识内容，不替代保存可取回版本。

当前 artifact 仍记录自己的 gate、work unit、目标版本/变化、当前检查与决策/findings、validation 适用性、docs decision、risks/uncovered areas、completion 和下一入口；未变事实可引用满足既有必需信息要求，不复制全文。来源缺失、版本无法唯一确定或内容不符时，先补足/重新取得证据，不能标作完成。final closeout 仍实质总结实际改动、验证、finding 状态、风险/owner、PR 与 next entry，可链接明细，不能只是链接列表。

## Goal scope 映射

| 已确认内容 | 本 plan 的决定 / slice / 验证 |
| --- | --- |
| goal 四项优化 1；success signal 1 | 三层实质职责；S1；单 slice 未变、多 slice 交互、新 PR 变化与 standalone 保持检查。 |
| goal 四项优化 2；success signal 2 | 核对实际验证与代码/依赖/配置/环境；S1；有效复用、真实 fix、失效证据和 mandatory checks 检查。 |
| goal 四项优化 3；success signal 3 | 四类 review loops 的条件推进与既有状态一致；S1；无 finding、真实 blocker、`needs-more-evidence` 和真实 fix 检查。 |
| goal 四项优化 4；success signal 4 | 版本可取回引用与当前 artifact/closeout 实质内容；S1；有效引用与缺失引用检查。 |
| success signal 5 | 三份必要 SKILL 同一 slice；既有 validator、diff whitespace 和代表情形走读。 |
| success signal 6；Execution and authorization | 总控按现有 gates 派发两路独立 review、裁决和交付；review 报告后执行已授权的技能 sync及部署文本一致性核对，保留真实证据与限制，不执行runtime probe。 |

四项规则共同决定同一 review gate 的责任、证据和状态转移，拆成按文件或规则的 slices 会产生中间矛盾并增加 gate 成本。一个 slice 足以独立实施并验证；没有增加目标、验收级别、框架或 future-slice work。未确认改进只能记录并交总控，不纳入实现。

## 唯一 implementation slice

**S1 — 对齐审核、验证、条件推进与引用契约。**

- objective / expected outcome：在三份必要 SKILL 中一次落实上述四项决定，使代表情形得到一致、可追溯的审核和推进结果。
- prerequisites：总控接受 plan review 及必要修复/re-review，保存 accepted plan commit，交接已批准 plan 的确切版本和 S1。
- allowed files / change scope：仅上表三份 SKILL 的必要文本；相关 gate artifact 按当次 handoff 的输出路径产生。保留现有 invocation、工具、模型/provider、权限和状态名称。
- interfaces / data flow / identity：controller 交接已批准 scope/plan、review target 版本和既有证据；reviewer 按本 gate 职责判断并产出 artifact；controller 裁决 findings 和适用性，再记录对应 accepted checkpoint 与下一入口。PR identity 沿 Deepreview 既有精确 OID 协议；其它 artifact 使用可取回的明确版本。
- error handling / invariants：不明版本、失效或不足验证、真实 blocker、未解决 `needs-more-evidence`、未满足延期要求、accepted 未验证修复、缺 artifact 或未分类风险均不放行。条件修复不减少任何必需独立审核、commit/PR 核对或授权。
- non-goals：不新增工具/字段/级别/旁路，不动 runner/models/provider/business，不实现运行时 gate engine，不实测或宣称收益，不启动其它任务。
- validation：运行下面的现有命令，逐项走读代表情形并记录实际判断依据；不要新增复制文本实现的测试框架或运行无关业务 suite。
- completion signal：必要文本一致，命令结果和代表情形证据写入 implementation artifact；交给总控派发 slice code review，不自报 accepted 或进入下 gate。
- stop condition：必要改动超出已批准范围、关键契约需重新决定或 required evidence 无法取得时向总控报告；局部措辞由实施者决定，真实 finding 仍按既有裁决/fix 路径处理。

## 验证命令、断言与代表情形

在仓库根目录执行现有检查；命令成功只证明其实际检查的内容，不代替语义审核：

```bash
./scripts/validate-skills.sh
git diff --check
git diff --cached --check
```

validator 预期所有被扫描 SKILL 有效；diff checks 预期没有 whitespace errors。实际被改文本的人工走读检查所有复制序列及 section/状态/commit/PR 放行表述相容；查看 `git diff --name-only` 和 `git status --short` 确认仅 approved 产品文本与当次授权 artifacts。未跟踪 artifact 另行检查 whitespace，不能把普通 `git diff --check` 当成已经覆盖它。

下表是文本契约的代表情形推演，证据为当前修改版本的具体条文/章节与判断，不是业务运行实测。可合并记录共同依据，不要求逐字符串断言或穷举局部实现。

| 情形 | 必须成立的判断 |
| --- | --- |
| 单 slice 完成后代码未变，已有实际验证有效 | slice review 实质检查 correctness；aggregate 独立查整体目标/遗漏并引用 slice 证据；PR 独立核对交付版本、完整 diff、CI，复用适用验证。无需再做两遍同范围全面审核。 |
| 多 slice 各自通过但组合产生接口/状态冲突 | aggregate 实质查交互并追踪影响路径，不能仅合并历史 pass；产生 finding 后走真实修复/re-review。 |
| 任一 review loop 无待修 finding，全部其它条件满足 | plan、slice、aggregate、PR 四类都记录 review/裁决/pass，下一适用入口为对应 accepted commit；没有空 fix/re-review artifact；accepted checkpoint 和 final push 义务照旧。 |
| accepted finding 触发真实 fix | fix artifact 记录实际版本/变更，重验受影响断言/交互；re-review 独立确认修复及最终状态，再 accepted；未修复、部分修复、证据失效不能通过。 |
| 新 PR 变化，或审查中 head/base OID 移动 | 获取/核对精确当前 OID 与对应完整 diff、快照及同版深挖对象；新变化按影响实质审核。旧结论限定原版本，不能作为新版 PR pass；收尾核对、不可取得即 blocker 不变。 |
| 代码未变，但相关依赖、配置或环境变化；或旧验证无实际来源 | 不能直接 reuse；重验受影响检查并确认其余证据适用性。mandatory checks 仍执行；真实影响要求全量时全量重跑。 |
| accepted 列表为空，却有真实 blocker / 未解决 `needs-more-evidence` / 必需验证不足 | 不记录 pass、不进入 accepted commit；当前 gate 继续取证或报告 blocker，不能改名、延期或引用历史 pass 绕过。 |
| 非阻塞 finding 正式 rejected 或获授权 deferred | 记录直接理由，deferred 同时有授权依据、非阻塞理由、owner/destination；其余条件满足才通过，不强制空修复。真实 blocker 不适用此放行。 |
| 未变事实有可读取的 artifact 与明确保存版本 | 当前 artifact 引用对应事实，保留当前 scope/决策/验证/风险与下一入口；closeout 实质总结结果。 |
| 引用只有可变路径/裸 pass/hash 无对应快照，或缺失/错版来源 | 无法支持相应必需事实；补足来源或当前验证前不放行，不臆造引用内容。 |
| 单独调用 Deepreview 或 Planreview | 原 invocation、strict/exhaustive review、finding/输出契约保持；Gateflow 职责解释不成为通用降级。 |

本 plan 阶段实际检查：分支/HEAD 与给定值一致；tracked 源码无变更，未跟踪内容为总控工作单元目录；安装 Gateflow 与仓库基线 `cmp` 相同。`./scripts/validate-skills.sh` 返回 0，六个现有 skills 均输出 `Skill is valid!`；`git diff --check` 与 `git diff --cached --check` 返回 0。这是基线环境/格式事实，不是未来改动的语义 pass 或效率实测；实施后需验证实际改动版本。后续 gate 只有确认适用性后才能复用其实际验证结果。

## 风险、未决项与后续交接

实施主要风险是把职责分工误写成免审、把 accepted 列表为空误当放行、遗漏复制序列，或把 hash 当可取回版本。上述决定与代表情形直接验证这些已确认目标风险，不引入新硬化目标；总控在后续 artifacts 记录实际覆盖和未覆盖范围，不能把计划中的防范写成已修复。

已确认 residual scope limits：SKILL 是提示约束，不能证明机械强制执行；无本轮测量不能证明速度收益。分类沿用 `assigned to later work unit`，owner 为用户/总控，destination 为只有用户另行确认才可开展的运行时强制或收益测量 work unit；本轮不创建或派发该工作。当前 evidence/docs 的真实性与收尾由本轮总控负责。没有 blocking technical open question，也没有必须由用户再选的实现决定。

下一交接由总控执行：冻结本 plan 版本，按 goal 的已授权路由并行派发 `mimo-flash`/Claude 与 `ds-flash`/Claude 的独立 Planreview，裁决后决定是否派发 Sol/Codex 修复或进入 accepted plan commit。本 Agent 不派发、不修改 state、不创建 commit/push/PR/sync。

后续 implementation/fix 完成报告应简要给出：消费的 approved plan/slice 与版本、实际 changed files/规则、实际执行与适用复用的验证及来源、代表情形结论、finding 最终状态或 blocker、docs decision、residual risks/uncovered areas 与 owner/destination、artifact 路径和交回总控的下一入口。产品 SKILL 保持简短，详证在 gate artifacts。

总控 closeout 应按最新 goal 记录真实 review/PR/sync及部署文本核对结果与限制，保留适用命令 `./scripts/sync-skills.sh`，提醒重新打开 Agent sessions 加载技能；本轮仅技能改动，不计划另外两个 sync 脚本。已授权 skill sync与部署文本核对在成功审核并报告后才由总控执行；用户已撤销所有runtime probe，本轮不启动任何探针或业务任务。用户手动 merge。

Completion status：plan 已形成，待总控验收和 plan review；本 artifact 不宣告其它 gate 通过。
