# Plan: Codex 服务器请求处理错误重连通知

Gate artifact: `plan`。Work unit: `codex-server-retry-recovery`。
Status: plan authored; pending independent plan review; not approved for implementation by this artifact alone。
Branch: `fix/codex-server-retry-recovery-20261013`。
Reviewed source/base: `991eb26c082e006da80474ff85efc4cfeb1116c0`。
Artifact path: `docs/gateflow/codex-server-retry-recovery/plan.md`。
Current gate / next entry point: `plan review`（由上游 controller 进入；本 plan agent 不执行）。

## Binding scope、goal、motivation、success

Binding contract 是已正式确认的 [goal.md](goal.md)，读取版本 SHA-256 为
`7f88eb63ff250492996719f6d137c7ffce4951b3db65311cca9a2d4c318adcca`。
没有另行提供 design document；诊断报告与离线 JSON 是缺口证据，不另行扩大验收范围。
遵循根目录 `AGENTS.md` 与 `/Users/leo/.codex/skills/gateflow/SKILL.md` 的 plan 要求。
本任务已经由上游按 `codex-agent-run / gpt-6-sol` 派发；当前 agent 仅产出 plan 与离线 baseline evidence，
不递归派发、不执行其他 gate、不修改源码/tests、不 commit/push、不部署或 live probe。

目标是让 `recognized_codex_connection_notice` 额外精确识别诊断第 10 次的服务器请求处理错误重连通知，
将它们送入现有待证明恢复队列。随后必须由原有完整恢复证明与所选机械检查决定 warnings 或 errors。
当前缺口会把已完整恢复的这类原生通知仍记成致命 errors；修复识别入口即可改变该结果，无需新的恢复机制。

沿用 goal 的六个成功信号，本文记为 G1–G6：

1. G1：两条案例消息在完整有效后续结构、native/precollection exit0、所选机械检查通过时降为 warnings；`result_status=not_assessed`。
2. G2：未恢复、未知/不支持近似文案、结构/顺序/final/terminal/退出/所选机械检查失败仍拒收；stream-closed 与 startup 原规则保持。
3. G3：修复版本有真实离线正反对照，普通 live 成功不能替代重连分支证明。
4. G4：controller 按固定 Gate Order 完成必需双路独立 reviews、裁决、commits、新 draft PR 与最终 push；保持 draft、不 merge。
5. G5：审核通过后 controller 执行 `./scripts/sync-agent-tools.sh`，保存输出/退出/安装一致性，并先核清该脚本其他目标的版本与 ownership。
6. G6：sync 后 controller 使用已安装 `codex-agent-run` 的 `gpt-6-sol` 与 `gpt-6-luna` 各做独立真实工具读、算、写、读回探针；保存原生事件、产物及版本/退出证据。

G4–G6 是已有 work unit 完成条件，并非新增 implementation slices；当前 gate 只制定交接与验证，不宣称它们已完成。

## Non-goals / scope boundary

工程最小范围是 matcher、同一行为的回归和 README 的现有 runner-results 段落。
不泛化全部 `Reconnecting` 或服务器 error，不改变恢复门槛/state machine、schema/result_status、业务验收责任。
不新增 retry、自动重派、动态权限、通用解析机制，不重构 collector，不做顺手硬化。
不改 runner、Seatbelt、provider routing、模型配置、业务输入语义或其他安装组件源码。
不读取/修改其他业务仓库，不读取凭据，不重派原业务任务，不回裁历史业务覆盖、计数与验收。
原诊断 `.md` / `-offline.json` 和已确认 goal 原样保留；修复证据另存，不能把历史结论覆写为修复后结果。
本任务不采用长期模板的 mimo-flash 双 runtime live 探针。

## First-principles judgment 与直接证据

以下行号针对上述 base；实际输入/源码 hashes、命令、六组合成输入与完整 collector 输出存于
[evidence/plan-baseline.json](evidence/plan-baseline.json)。该证据的 SHA-256 为
`516edbd7ed236558d6233f6880fec14653580331b3230e0c89c3be4b367ee90d`。
原诊断位于 `docs/reviews/upstream-agent-execution-diagnosis-20261013-090017.md` 及同名 `-offline.json`；
仅阅读本仓库内已有成果，没有沿报告里的旧复现命令读取原业务包。
另已核对 controller 保存在本目录的 [server-error-notices.json](evidence/server-error-notices.json)
（SHA-256 `65d7dd1ee9d43f682c9c3fae05e1e63891afa52bee48c987f88e27b75ee05595`），
两条 events 与本 baseline 从原离线 JSON 提取的 events 完全相同；原生摘录行号 135/136 只是历史定位。
[pre-sync-inventory.json](evidence/pre-sync-inventory.json)
（SHA-256 `998f5c9a6e894509f30f3052b0b6d4b09e4f8dae17b8155997bd89ca2a2ee9e4`）记录了 12 对 source/installed hash 全部相同。
该 controller manifest 不含本次读取时的安装复查命令/时间，也不是修复后 sync receipt，C1 仍须重新核对部署时版本。

| 直接代码/离线证据 | 对当前方案的约束 |
| --- | --- |
| `scripts/agent-run-result.py:49–53`：exact keys/type/string + `re.fullmatch`，只支持 stream-closed。 | 缺口在白名单文案；新增第二种精确文案，保留 envelope 与旧文案。 |
| `:262–271`：已识别 error 才记录 count、首末行及限量候选；未识别直接 `note("errors")`。 | 新文案进入同一个候选队列；不在 dispatch 直接降级或吞错。 |
| `:237–259, :285–295, :309–328`：记录 starts/final/terminal 的 shape/order，检查退出与其他 errors。 | 恢复证明现成且与通知原因无关；无需改变 state transitions。 |
| `:398–505`：严格 JSON、终态后事件、last-message、canary/artifact、stderr/退出等检查先执行。`:505–518`：随后 finalize、生成报告。 | 所选检查 errors 必须继续阻止通知降级；anomalies 仍按原规则保留。 |
| `scripts/codex-agent-run:503–550`：取得 native exit、处理 final 后把收集前 `run_exit` 传给 collector，最后合并 collector exit。 | 不把已汇总的历史 runner1 当作 precollection 输入；runner 无需修改。 |
| `tests/test_agent_run_results.py:16–91`：临时 fake runtime、`codex` / `recovered_codex` / `run_collector` / `run_agent`。`:93–125`：完整 schema、通知、来源诊断断言。 | 复用 deterministic helpers 和独立测试 oracle，不新增模型/网络测试基础设施。 |
| `tests/...:332–381, :453–569, :577–670`：已有 shape/order/final/terminal、所选检查、native/postprocessing 拒收矩阵。 | 旧矩阵保留，新文案证明经过这些门槛；不得删减旧断言换取通过。 |
| `README.md:389–396` 已说明 warnings 的完整恢复条件与 `not_assessed`。 | 只补精确支持边界，保持语义和业务责任说明。 |
| `scripts/sync-agent-tools.sh:10–22` 同时安装 launcher、两种 runner、collector 与其他 helpers/defaults。 | 后续 sync 是多文件部署；controller 必须先核对未变组件，不能顺带发布无关版本。 |

第一性原理判断：顶层 error 文案只是恢复候选，不是恢复证明；当前队列和最终分类已经实现了需要的证明职责。
因此一个精确 matcher 分支和一个行为 slice 足够。不存在支持通用服务器错误 taxonomy、请求身份关联或 retry 执行器的需求。

## 必要 decisions、interfaces、identity 与状态不变项

**D1：文案/形状白名单。** 保留 `recognized_codex_connection_notice(event) -> bool` 的调用契约和旧分支。
新分支只接受顶层 keys 恰为 `{"type", "message"}`、`type == "error"`、message 为 string，且整个 message 精确为：

```text
Reconnecting... N/5 (stream disconnected before completion: An error occurred while processing your request. You can retry your request, or contact us through our help center at help.openai.com if the error persists. Please include the request ID UUID in your message.)
```

这里 N 只接受一个 ASCII 字符 `[1-5]`，分母固定 `5`；UUID 只接受
`[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`。
小写 canonical hex 是观察到的文案形状；不加 UUID version/variant 位限制，不绑定历史两个 ID。
新的其他小写 UUID 形状均可匹配；大写 hex、非 ASCII hex、错误段长/连字符/braces、前后缀/换行/额外空格均不匹配。
固定文字、大小写、空格、标点和括号逐字匹配；采用 `fullmatch`，固定部分转义或等价精确表达，
不能使用 substring、宽泛 `.*`、忽略大小写或 `\d` 扩大字符集。
实现者可决定 regex 的局部排版/常量组织，不能改变此语言边界。

**D2：复用恢复数据流。** 新文案通过现有 bool 入口进入 `connection_notice_count` / 首末行 / `connection_notices`，
由既有 `finalize_codex_connection_notices` 统一裁决。下面都是保留项，production 只能改 matcher：

- 唯一且 shape 有效的 `thread.started` 与 `turn.started`；thread ID 非空白 string，首个有效事件必须是 thread，turn 只能紧随或中间有一条既有精确 startup diagnostic。
- startup 原生 `item.completed/error` 仍为 anomaly；它只影响既有起始证明，不被新 matcher 识别、不改降级类别。
- 所有候选在已开始的 turn 内；**最后一条**候选之后必须有有效非空 final，且 final 早于唯一 shape 有效的成功 `turn.completed`。
- 缺失/重复/冲突/失败 terminal、错误 final/envelope/item、terminal 后不允许的事件、严格 JSON 解析 errors 均继续阻断。
- native exit 与 **收集前** runner exit 都为 0，并且其他 collector errors 为 0，才能把全部候选降为 warnings。
- stderr/普通失败工具/startup 的 anomalies 不被抹掉；完整恢复可为 `needs_review / exit0`，不是一律 `passed`。
- `usage` 不是证明条件，保持既有 omitted/non-dict 处理；terminal 后 `rate_limit_event`、空行、旧支持 shape 均保持现状，不硬化。

Request UUID 仅是 message 的词法形状，不是 `thread_id` / final item ID，不新增跨通知关联、去重或 session 匹配。
每条消息的 N 都受限，但不新增序号递增、唯一、从 1 开始或总通知数最多 5 的约束；已有重复/25 条诊断计数规则保持。
首末候选行及总数不能因显示保留 20 条而失效；显示 cap/truncation 和 raw logs 均沿用现有逻辑。

**D3：结果契约不变。** CLI 参数、runner 文件位置/收集模式/退出传播、report 全部 keys 与 `schema_version=1` 不变。
`result_status` 始终 `not_assessed`。native/postprocessing 非零保留相应 runner 非零；仅机械拒收且原退出为 0 时 runner 为 1。
`agent_status=completed` 可以同时出现 `validation_status=rejected`，不改成业务成功/失败判断。
新文案唯一可见变化是正确证明恢复时由原生 errors 变为既有前缀的 warnings；未证明时用既有 `recovery not proven` errors。
Claude runtime 的顶层 error 不享受此 Codex 例外；`--detail` 仍输出原始流而不走分类。

**D4：复用测试 helper，但测试识别 oracle 独立。** 增加 test-only server notice builder，
使用诊断的两条 `2/5`、`3/5` 与原 UUID 作为静态脱敏 fixtures；不让测试依赖读取原业务文件或 untracked 诊断文档。
两个案例 ID 分别为 `4324720a-d6d1-4f28-ab30-43742ac44125`、`0e6e96e9-f41d-457f-8df2-0d8d4d366d47`；
额外形状正控可用 `01234567-89ab-cdef-0123-456789abcdef`，证明不固定案例 ID、不要求 UUID version/variant。
`recovered_codex` 可以增加 optional explicit notices（默认保持旧 stream-closed 行为）。
`assert_connection_result` 可以增加 optional explicit expected notice list（默认保留旧 1–5 fixtures），
对每个指定通知实际所在行继续核对唯一 diagnosis、完整 message、类别、stream、recovery prefix/reason。
不能调用 production recognizer 筛选待断言通知，也不能只断言 status 而让 server notice 的逐条断言空跑。
negative lookalikes 用 `assert_report_contract` / `assert_output_diagnostic` 断言原始 error，不能把它们指定为恢复候选。
所选检查和 process-failure 现有共享 helper 可添加 optional notices，默认/旧计数断言不变；新调用用单条 server notice，
两条案例及混合通知单独明确总数/逐条断言。不为本改动重写整个测试框架。

## Goal alignment 与受影响文件

| 项目 | 绑定依据 |
| --- | --- |
| D1、新精确 matcher、S1 的支持/近似拒收测试 | G1 的案例识别与 G2 的未知错误边界。 |
| D2/D3、S1 的恢复门槛、schema/exit/原文证据断言 | G1/G2 的完整证明、机械拒收与原规则不变。 |
| D4、baseline replay、定向与整文件离线测试 | G3 的可取回实际正反对照，也验证 G2 无回归。 |
| README 小范围更新、原诊断保留 | 已确认 docs decision；让 G1/G2 支持范围可理解而不改变历史结论。 |
| controller 的固定 reviews/PR 交接 | G4 与项目指令；不在当前 agent 执行。 |
| 审核后 sync manifest/exit 和两路 Codex 工具探针 | G5/G6；与 G3 的断流离线证明分开。 |

| 文件/module | Allowed change |
| --- | --- |
| `scripts/agent-run-result.py` | 仅 `recognized_codex_connection_notice` 的精确新文案识别；必要的邻近 matcher 常量/注释。不改其他 parser/dispatch/proof/finalize/report。 |
| `tests/test_agent_run_results.py` | 小型 server fixture、兼容 helper seam、新文案支持/拒收/原门槛测试；保留所有既有测试与断言。 |
| `README.md` | 仅 Runner results 的 recognized notice 段落：明确 stream-closed 与完整 server 文案白名单、受限 N/UUID 与完整恢复要求。 |
| `docs/gateflow/codex-server-retry-recovery/` | 当前 plan/baseline；后续 implementation/review/验证/closeout artifacts，只记录实际版本和事实。 |
| 两份原诊断、`goal.md` | Read-only 依据；controller checkpoint 可原样纳入，不修改内容。 |

runner/sync/launcher/skills/provider config 属于阅读/后续部署验证边界，不是 implementation allowed files。
没有新的 public interface、schema、状态机或模块 ownership 迁移。

## 唯一行为 slice：S1 — 精确服务器重连通知参与现有恢复证明

**Objective / expected outcome：** 在有效同次恢复时把诊断两条 server 通知降为 warnings；否则保持机械拒收，旧 stream/startup 不变。
一个实现 pass + 一个 slice code-review pass 足够；matcher 与验证共同构成一个行为增量，拆成文件/测试 slices 不增加行为价值。

**Prerequisites：** binding goal 不变；controller 完成双路独立 plan review、finding 裁决及适用 fix/re-review，创建 accepted plan checkpoint。
维持指定工作分支，已有 docs ownership 按用户 handoff 处理，无需重新问 ownership。

**Allowed files/scope：** 严格使用上表三份工程文件与当前 work unit artifacts；实现 D1–D4，不修改其他行为。
**Interfaces/data flow/identity/invariants：** 严格遵循上节 bool 入口 → 同一候选队列 → 既有 collect/checks → finalize → 原 report/exit；
未知/近似通知直接记 errors；匹配但未证明恢复的通知继续 errors。不存在新增 retry 动作、error suppression 或 request-ID 关联。
**Non-goals：** 上述非目标全部适用；不能提前实施另一个 work unit 或部署。

**Verification / completion：** 下节 V1–V3 对实现版本有保存的实际命令、退出、断言与 source/input hashes；
新文案经过完整门槛，三份工程文件 diff 无越界，README 与实现一致，旧测试断言完整。
实现 artifact 写明 changed files、reviewed version、docs decision、residual risks/uncovered areas、验证事实及 next entry=`code review`。
完成 slice 的放行仍需 controller 独立审核/裁决及 accepted slice commit；实现者自报通过不等于 gate pass。

**Stop：** 需要改变 matcher 外 production、恢复门槛/schema/公开行为/文件 ownership 或新增机制才能实现目标时停止，交 controller 回到 scope 判定。
当前目标相关测试失败先查明具体反例，不能删弱断言或顺手修复无关问题；超 scope 的真实问题记录风险/交 controller。
验证环境不具备导致必要断言不可验证时保存失败并交 controller；不要假定通过、改走 live 或重派业务任务。

## Validation：已执行 baseline 与待执行修复回归

### 已执行的最小离线 baseline（不是修复验收）

时间 `2026-10-13T01:22:23.739026+00:00`；上述 base 的 repository collector SHA-256：
`ea836b684381420045b064c7ba865ac2b1cf6fa5501b308d0379661253df7301`。
证据 JSON 保存每个实际 collector argv、输入 events/JSONL/hash、完整 report、collector stderr/exit、recognizer 结果。
临时 log 路径已经清理，JSON 内输入/输出快照可重建；这里只合成 start/final/terminal，不是历史整轮重放。
没有复读当前 installed collector；原诊断的安装一致性仅是历史证据，后续 sync 不能据此宣称当前 live 一致。

实际每次 collector 命令是 `python3 -B scripts/agent-run-result.py --runtime codex --provider gpt-6-sol --output <临时 JSONL> --stderr <空临时文件> --exit-code 0 --runner-exit-code 0`，绝对 argv 存 evidence。

| 合成场景 | 实际 outer exit / validation | errors / anomalies / warnings |
| --- | --- | --- |
| 两条精确 server 通知 + 有效后续 final/terminal | 1 / rejected；recognizer=`false,false` | 2 / 0 / 0 |
| stream-closed + 有效恢复 | 0 / passed | 0 / 0 / 1 |
| stream-closed + 失败工具 + 有效恢复 | 0 / needs_review | 0 / 1 / 1 |
| 两条精确 server 通知，无后续 final/terminal | 1 / rejected | 4 / 0 / 0 |
| unknown error + 有效 final/terminal | 1 / rejected | 1 / 0 / 0 |
| 既有 startup + stream-closed + 有效恢复 | 0 / needs_review | 0 / 1 / 1 |

实际执行并通过以下 4 项原有测试，outer exit0，`Ran 4 tests in 5.546s / OK`；stdout/stderr 存 evidence：

```bash
python3 -B tests/test_agent_run_results.py \
  RunnerResults.test_codex_recovered_connection_notice \
  RunnerResults.test_codex_startup_diagnostic_recovery_and_controls \
  RunnerResults.test_codex_connection_notice_keeps_selected_checks \
  RunnerResults.test_codex_connection_notice_keeps_process_failures -v
```

这些测试使用临时 fake launcher/runtime 输出，不调用模型或其他真实 Agent。
运行前后源码、tests、README、goal 与两份诊断 hashes 全部一致（evidence 字段 `source_and_inputs_unchanged_after_run=true`）。
该 baseline 证明当前缺口和四组旧控制；不能替代实现后新文案完整回归。

### V1 — 新文案集成正反对照（implementation 执行）

新增以下测试入口，名称用于下方可执行命令；复用既有 helpers，局部组织由实现者决定。

| 测试入口 | 必须断言 |
| --- | --- |
| `test_codex_server_retry_recovered_connection_notice` | 诊断 `2/5 + 3/5` 两条同流及各自单独恢复；N=1–5、另一个 lowercase UUID；新/旧通知混合、startup 组合与普通失败工具。干净恢复 exit0/passed/errors0、warnings 等于通知数；startup/工具异常保留 needs_review/anomaly，原 schema/result、final/terminal/usage/session/raw logs 不变。逐条核对 source line/message/prefix。 |
| `test_codex_server_retry_notice_lookalikes_rejected` | N=0/6/01/Unicode 数字、分母不为5；UUID 缺失/大写/非hex/段长或连字符错/braces；固定文字或 URL/标点/空白变化、前后缀/换行、非string/missing/extra keys；unknown error。单个未知顶层 error 在完整 finish 下 exit1/rejected/errors1/warnings0，原始 event diagnosis 精确可见。支持通知+未知错误同流时，未知错误也阻止全部候选降级。 |
| `test_codex_server_retry_notice_recovery_fences` | 新文案至少覆盖：缺失/重复/畸形 starts 或错误起始顺序/notice-before-turn；startup 未知/多条不能桥接；missing/blank/malformed final 和 final-before-last-notice；missing/failed/duplicate/malformed terminal、final/notice-after-terminal；无 final+terminal 的两条历史通知；malformed JSON/其他 collector errors。均 exit1/rejected/warnings0，并核对候选的既有 recovery-failure reason/来源。保留旧完整矩阵。新 server error 在 Claude 流仍致命；server `--detail` 输出原始流/原 exit，不输出分类前缀。 |
| `test_codex_server_retry_notice_keeps_selected_checks` | 复用现有 selected-check helper，可选 server notice，分别无/有 startup：有效 canary 实际工具候选+artifact+last-message 正控；canary mismatch/missing proof/expected input failure、missing/nonregular/log-alias/hardlink artifact、last-message 缺失或 mismatch 均 errors/rejected/warnings0；保留 prelaunch 拒收/未启动 fake runtime 断言。 |
| `test_codex_server_retry_notice_keeps_process_failures` | 复用 process-failure helper，可选 server notice，无/有 startup：native exit7 保留 outer/report runner7；native0/precollection1 与 last-message postprocessing failure 仍 exit1；均 rejected/warnings0、失败原因准确，不能把 final/terminal 当作退出0证明。 |

```bash
python3 -B tests/test_agent_run_results.py \
  RunnerResults.test_codex_server_retry_recovered_connection_notice \
  RunnerResults.test_codex_server_retry_notice_lookalikes_rejected \
  RunnerResults.test_codex_server_retry_notice_recovery_fences \
  RunnerResults.test_codex_server_retry_notice_keeps_selected_checks \
  RunnerResults.test_codex_server_retry_notice_keeps_process_failures -v
```

期待 outer exit0、所有 subtests 无 failure/error。negative 场景的 runner/collector 非零是被测试断言的预期，不是测试命令失败。
新文案逐条独立 oracle 不得从 production matcher 生成。已有完整大矩阵不要求复制所有排列，
但以上受影响类别要有新 server 通知实际经过的对照，不只重跑旧 stream fixtures。

### V2 — 原有 runner/collector 整文件回归

```bash
python3 -B tests/test_agent_run_results.py -v
git diff --check
git diff -- scripts/agent-run-result.py tests/test_agent_run_results.py README.md
```

期待整文件测试 outer exit0，包含 stream/startup、严格 JSON、结构/final/terminal/exit/所选检查、report schema、
诊断 count/cap/last-candidate beyond retention、Claude fatal、raw/detail、临时安装等既有断言全部保持。
其中 `test_sync_installs_self_contained_result_adapter` 只安装到 test 临时目录，不是 sync to live。
`diff --check` 无错误；实际 diff 仅允许上表范围，不能削弱旧 tests。
没有新增 skill/模型/registry/runner 源码，故不新增这些组件的验证要求。
仓库 README 提供的 `python3 -B -m unittest discover -s tests` 可由 controller 因 mandatory check 或具体影响追加；
本 plan 不以重跑全仓替代上述有针对性的证据，不设置任何 live-runtime 测试 opt-in 环境变量。

### V3 — 用保存输入复核历史文案的修复后效果

以下命令只读取本仓库 baseline JSON 并重建临时合成流；**期待修复后通过，当前 baseline 应失败于两条 server 正控**。
implementation 执行并把命令、输出/退出和新 collector hash 另存 implementation evidence，不覆盖 plan-baseline 或原诊断。

```bash
python3 -B - <<'PY'
import hashlib, json, subprocess, tempfile
from pathlib import Path
root = Path.cwd()
saved = json.loads((root/'docs/gateflow/codex-server-retry-recovery/evidence/plan-baseline.json').read_text())
adapter = root/'scripts/agent-run-result.py'
print('collector_sha256', hashlib.sha256(adapter.read_bytes()).hexdigest())
with tempfile.TemporaryDirectory(prefix='server-retry-replay-') as temp:
    output, stderr = Path(temp)/'output.jsonl', Path(temp)/'stderr.log'
    for case in saved['offline_cases']:
        output.write_text(case['input_jsonl'])
        stderr.write_text(case['stderr_input'])
        argv = ['python3', '-B', str(adapter), '--runtime', 'codex', '--provider', 'gpt-6-sol',
                '--output', str(output), '--stderr', str(stderr), '--exit-code', '0', '--runner-exit-code', '0']
        run = subprocess.run(argv, capture_output=True, text=True)
        report = json.loads(run.stdout)
        positive = case['scenario'] == 'case10_exact_notices_valid_finish'
        expected_exit = 0 if positive else case['outer_exit']
        expected_status = 'passed' if positive else case['report']['validation_status']
        expected_counts = {'errors': 0, 'anomalies': 0, 'warnings': 2} if positive else case['report']['diagnostic_counts']
        assert run.returncode == expected_exit, (case['scenario'], run.stderr)
        assert report['runner_exit_code'] == expected_exit
        assert report['validation_status'] == expected_status
        assert report['diagnostic_counts'] == expected_counts
        assert report['result_status'] == 'not_assessed' and report['runtime_exit_code'] == 0
        category = 'warnings' if positive else 'errors'
        if case['scenario'].startswith('case10_'):
            for line, event in enumerate(case['input_events'], 1):
                if event['type'] == 'error':
                    matches = [d for d in report[category] if d['line'] == line and event['message'] in d['message']]
                    assert len(matches) == 1 and matches[0]['stream'] == 'output'
                    prefix = 'Recovered Codex connection notice:' if positive else 'recovery not proven'
                    assert prefix in matches[0]['message']
        print(case['scenario'], run.returncode, report['validation_status'], report['diagnostic_counts'])
PY
```

期待两条历史通知正控为 0/passed/0-0-2；未恢复仍 1/rejected/4-0-0（通知改经队列拒收），
其余四组 baseline 计数/状态不变。V1/V2 负责此简短 replay 未涵盖的新文案边界与全部门槛。

## 审核通过后的 controller verification：sync 与真实工具探针

以下是 G5/G6 的执行交接，当前 plan agent **没有执行**。controller 在 reviewed changes/version 稳定、
必需 review/裁决及 draft PR gate chain 通过后，在 final closeout 中记录实际结果；不能用本节代替 reviews 或实现验收。
goal 已授权该范围 sync/probes，无需为同一授权再索要许可；出现真实无关部署差异时按既有 ownership 条件停下处理。

### C1 — sync to live

从含 approved changes 的本仓库 checkout 执行。先冻结 reviewed commit + working-tree diff/文件 hash，
按 `scripts/sync-agent-tools.sh:10–22` 列出全部 source→target 映射，逐项保存 source/current-installed SHA-256 与存在性，
包括 launcher、两种 runner、collector、preflight、sandbox helpers、compose/repair/endpoint helper 和 defaults JSON。
只记录 hash/metadata，不把 launcher/config/凭据内容写进 evidence。
collector 是本 work unit 的预期部署差异；其他目标若与 approved checkout 不一致，先核查 ownership/既有授权，
不能直接运行会覆写无关 live 版本的 sync。

```bash
./scripts/sync-agent-tools.sh
shasum -a 256 scripts/agent-run-result.py "$HOME/.local/bin/agent-run-result.py"
shasum -a 256 scripts/codex-agent-run "$HOME/.local/bin/codex-agent-run"
```

controller 把实际 sync stdout/stderr/exit、安装路径、前后完整 manifest 与一致性判定存 evidence。
期待 sync exit0；全部部署目标与对应 approved source 字节一致，collector hash 是修复版本。
需要更新交互 shell launcher 时 `source ~/.zshrc` 或开新 shell；已在 PATH 上的 installed runner 调用不需要 source。
本改动无 skill/profile/shim 变更，不运行 `sync-skills.sh` / `sync-codex-agent.sh`。

### C2 — installed gpt-6-sol / gpt-6-luna Codex 工具读写探针

controller 为两路分别创建本仓库内唯一新 probe 目录（例如当前 work unit 的 `evidence/live-probes.<run-id>/<provider>/`）。
每路预置 `input.json` 为 `{"probe":"<provider>","values":[7,11,23]}`，`result.json` 不存在。
`prompt.md` 明确这是一次独立工具探针：只读指定 input，使用真实工具从文件计算 count/sum，写新 result 为
`{"probe":"<从输入取得>","count":3,"sum":41}` 的结构，随后再用真实工具读取 result 并显示它；
prompt 不给出计算答案，要求分别保留读取、计算/写入、读回的可见工具结果。
限制在该 probe 输入/产物，不开发仓库、不递归调用 Agent、不读凭据/其他仓库、不运行原业务任务。
expected content 由 controller 独立保存/核对，不凭 final 文字声明通过。

下面每路各执行一次（`probe_case_dir` 由 controller 设为已准备好的该路绝对新目录）；
所有 runner destinations 是互不重叠且尚不存在的新文件：

```bash
probe_provider=gpt-6-sol # 第二路单独设为 gpt-6-luna
probe_case_dir="$PWD/docs/gateflow/codex-server-retry-recovery/evidence/live-probes.<run-id>/$probe_provider"
"$HOME/.local/bin/codex-agent-run" --provider "$probe_provider" \
  --cwd /Users/leo/workspace/code-is-cheap --sandbox workspace-write --no-persist \
  --prompt-file "$probe_case_dir/prompt.md" --artifact "$probe_case_dir/result.json" \
  --output "$probe_case_dir/native.jsonl" --stderr "$probe_case_dir/native.stderr.log" \
  --last-message "$probe_case_dir/final.md" \
  >"$probe_case_dir/report.json" 2>"$probe_case_dir/outer.stderr.log"
probe_outer_exit=$?
printf '%s\n' "$probe_outer_exit" >"$probe_case_dir/outer-exit.txt"
```

上面 `<run-id>` 是本次创建目录的具体标识，不能直接使用未准备输入的示例路径。
实际运行用结构化 argv 或安全引用路径，保存 argv/prompt/input hash 和 input 快照。
无 fake launcher override，调用 installed runner；不改 runtime/provider 配置以使探针通过。
controller 如使用带 errexit 的驱动，要先捕获退出，确保失败的报告/原生日志/退出仍保存。

可对每路实际目录执行以下独立机械复核（路径设为实际目录）：

```bash
python3 -B - "$probe_case_dir" "$probe_provider" <<'PY'
import json, sys
from pathlib import Path
p, provider = Path(sys.argv[1]), sys.argv[2]
report = json.loads((p/'report.json').read_text())
actual = json.loads((p/'result.json').read_text())
assert int((p/'outer-exit.txt').read_text()) == 0
assert (report['runtime'], report['provider']) == ('codex', provider)
assert (report['runtime_exit_code'], report['runner_exit_code']) == (0, 0)
assert (report['agent_status'], report['terminal']) == ('completed', 'turn.completed')
assert report['result_status'] == 'not_assessed' and report['schema_version'] == 1
assert report['validation_status'] in ('passed', 'needs_review') and report['diagnostic_counts']['errors'] == 0
assert report['tool_results'] > 0
assert (p/'result.json').is_file() and not (p/'result.json').is_symlink()
assert actual == {'probe': provider, 'count': 3, 'sum': 41}, actual
assert (p/'final.md').read_text().strip() == report['final_answer'].strip()
print(provider, 'mechanical probe checks passed; controller must inspect native tool read/write/readback evidence')
PY
```

另由 controller 读取该 probe 的 native events，核对实际 input 读取输出、从该输入计算和写新文件的成功工具结果、
随后的 result 读回输出与 controller 实读 JSON 一致；排除只在 final 写工具示例或只有文件存在却没有原生工具证据。
保存 code/install hashes、runtime 版本、实际 argv、outer/runtime/runner exit、terminal、tool item IDs/commands/outputs、
产物 hash/内容及 anomalies 的具体影响判断。`needs_review` 只可在相关 anomaly 证据经裁决后通过，不能单凭 exit0放行。
任一路失败保留失败证据并诊断；重试使用新的目录，不覆写/隐去失败，不触发原业务任务。
两路普通成功只证明 installed runner 的普通工具读写路径；不能证明真实服务器断流或替代 V1–V3。

## Docs decision、residual risks / uncovered areas

Docs decision：更新 README 现有 runner-results 支持边界一段；不新增通用恢复指南或长期模板，不修改原诊断结论。
本 plan 新增 `plan.md` 与 `evidence/plan-baseline.json`；后续验证/closeout 另存本 work unit artifacts，记录事实和适用版本。

| Risk / uncovered area | Gateflow 分类 | Owner / destination / 非阻塞依据 |
| --- | --- | --- |
| 已证明的新文案识别缺口及其门槛回归 | fixed in current slice（计划；尚未修复） | S1 implementer + controller；以 V1–V3 与后续 review 证据关闭，不能在本 plan 声称 fixed。 |
| 将来不同服务器文案、uppercase/其他 UUID 表示、变化的预算或 schema | assigned to later work unit | SubAgents 上游维护者；当前只接受已确认精确文案形状，不新建 issue/不扩大 matcher。 |
| 服务/网络根因、历史执行 adapter identity、历史完整恢复证明与业务覆盖未知 | assigned to later work unit | 上游维护者处理技术根因，原调用方处理历史业务；本次合成回归不重裁历史，不需要业务输入。 |
| 普通 live 无法强制原服务断流 | assigned to later work unit | SubAgents 上游维护者；goal 明确离线恢复分支与普通 live 各自证明范围，本 work unit 不加故障注入。 |
| 部署时 sync 其他目标可能有无关版本差异（已有 controller baseline manifest，当前 plan 未直接复查 live） | requiring new issue or explicit user decision（仅差异超出既有授权且 ownership 无法判定时） | controller/C1；先重新做 manifest/ownership 核查；既有 collector sync 授权有效，不凭假想差异阻塞 plan。不得绕过真实越界。 |

没有 later approved slice，也没有已知 existing issue 可挂靠；不把未确认的额外硬化列为当前或 future slice。
当前 blocking technical/scope questions：无。上述风险均有分类、owner、destination；发现新的未分类风险须交 controller 裁决。

当前 uncovered validation：只运行上述最小 baseline；新 matcher/V1–V3 尚未实现/执行，
全部独立 review/commit/PR 尚由 controller 完成，installed manifest/sync/C2 两路 live 尚未执行。
这些是已确认 work unit 的待完成验证，不是可延期豁免的 success signals。

## Completion report / next entry

Plan 完成信号：绑定 goal 明确；唯一行为 slice 的文件/行为/interfaces/identity/invariants/stop 已确定；
支持和拒收边界、真实命令与断言、docs decision、风险/缺项/owner 可供实现；baseline 可取回且原源码/tests/诊断未改。
这份 artifact 只标记 plan authored，不标记 plan-review-pass、accepted plan 或 work unit 完成。

交 controller 的 report 应包含：artifact path；reviewed source/input hashes；D1–D4 与 S1；实际验证命令/退出/范围；
docs decision；风险分类/owner；尚缺的实现、reviews、sync/probes；current gate / next entry=`plan review`。
下一入口由 controller 使用 `$planreview`，按已确认路由派发 `claude-agent-run / mimo-flash` 与 `claude-agent-run / ds-flash`
独立并行审核，读取证据并裁决，然后按固定 Gate Order 进入 accepted plan commit 和 S1；当前 agent 不执行该入口。
最终 closeout 由 controller 写实际改动/验证/finding 状态/remaining owners/draft PR/最终 push，
并记录适用 sync 命令 `./scripts/sync-agent-tools.sh` 与已授权 sync、两路工具探针的真实结果；本 plan 不代写 closeout pass。
