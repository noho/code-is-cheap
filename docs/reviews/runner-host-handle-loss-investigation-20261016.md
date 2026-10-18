# sub-agents / runner 与外层托管句柄丢失调查

调查日期：2026-10-16。范围：只读静态实现及指定事件材料；仅新增本报告和同目录 `runner-host-handle-loss-investigation-20261016-evidence.json`。未进入开发/PR流程，未修改源码、SKILL 或业务产物，未调用 runner、collector、resume、旧句柄或业务验收，未 probe、sync、重启、终止或重派进程。当前仓库基线 `32a244d1e286086be86dba837976d3d72fdd6c1f`，分支 main；报告写入沿用现有 docs/reviews 调查目录，按本次明确指令不创建开发分支。

## 结论与未定项

维护线推测**部分成立，但须限定含义**：runner 已封装 runtime 启动、原始日志保留、原生完成证明解析、选定机械检查和正常结束后的统一 JSON；当前没有独立于 stdout 的持久结果/真实退出回执，也没有恢复外层托管句柄的接口。外层句柄失效属于宿主执行工具边界；runner 的结果耐久性不足使该故障下无法仅靠 retained logs 补齐完成证明。不能据此认定 runner 引发宿主重启，或宿主承诺过跨重启恢复却违反承诺。

SKILL 明确把等待和外层回执收取交给总控，因此“总控现已只需调用并读取最终结果、完全无需生命周期操作”不是现行契约。正常路径分工有文档；丢句柄后的处理缺少闭环，属于宿主失效现象、runner 耐久性能力缺口与文档异常路径缺项的组合。没有证据证明本案是调用方遗漏正常等待造成。

三个原调用都已有唯一 `turn.completed`；旧 B 还存在独立问题：完整现存日志没有任何 `item.completed/agent_message`。A/Developer 有最终答复，但三者均没有可查到的真实外层/runtime/runner 退出回执或原 runner 汇总。**现有证据不足以恢复三个可信的成功统一结果**。可交付保留未知值的证据状态，不可把未知退出码置 0、补造 completed/passed 或验收业务。

## A. Unknown process id 的层级与身份

本次使用的接口定义：`exec_command` 在命令尚在执行时返回 `session_id`；`write_stdin` 接收这个托管会话编号以继续收集输出/完成状态。该字段是执行工具句柄，不等同 runner 汇总内的原生 `session_id`，也不能据数值称为 OS PID。

父会话原始记录路径：`/Users/leo/.codex/sessions/2026/10/14/rollout-2026-10-14T16-59-08-01a139a3-0b08-7840-8a13-0f1e050d84ab.jsonl`（下称 P）。已把以下少量原始回执复制到证据 JSON，未复制业务任务全文：

| P 行号 | 北京时间 | 证据 |
|---|---|---|
| 1898、1900 | 10-16 06:00:52、06:00:57 | 外层 exec 内并行启动 A/B 两个独立 exec_command；返回 A=33799、B=79319，无 exit_code、stdout 为空 |
| 1927、1929 | 06:02:13、06:02:16 | Developer 的独立 exec_command 返回 49796，无 exit_code；并非与 A/B 同在 06:00:57 返回 |
| 1940、1948 | 06:03:27、06:04:30 | 三个 write_stdin 均仍返回相同 session_id，调用方记录 running，尚无退出码 |
| 1983、1985 | 06:07:21、06:07:23 | daemon_recovery 启动恢复 turn；系统恢复文本称 server restarted，要求先检查再重复动作 |
| 1998、2000 | 06:07:41 附近 | 对三个原句柄调用 write_stdin；三个 Promise 均 rejected，原因分别为 `write_stdin failed: Unknown process id ...` |

33799 由 **exec_command 所属的托管执行实现**在接口层分配/持有；父控制器再用 `store("msft-g1-review-a-01-last", r)` 保存返回对象（P:1898），并写入 dispatch.json（P:1902）。它关联 A：provider gpt-6-sol、任务 `g1-review-a-01-task.md`、日志 `g1-review-a-01-evidence/output.jsonl`。B 为 mimo，Developer 为 gpt-6-sol，三者都用 Codex runtime。具体 native thread 对照见下表与证据 JSON。

错误由 **write_stdin 的托管进程查找层**通过工具失败返回，再由外层 functions.exec 的 Promise.allSettled 显示为 rejected；不是 codex-agent-run 的 JSON、子 Agent 最终答复或 runtime 日志错误。仓库三个 runner/collector 源文件内没有该报错或这些外层句柄的管理逻辑。宿主实现源码不在本次核查材料中，不能进一步指认发出该字符串的具体二进制、daemon、服务实例或其内部注册表。

能确认的是“先能用、恢复通知后不再能用”的时间链和系统自报 server restarted。**未知**：具体哪一个 server/进程重启、原因、句柄为何失效（状态丢失、会话作用域改变、清理等内部机制均未证实）、子进程实际存活/退出情况、stdout 是否曾写出但未送达。没有整机重启、模型服务故障或 runner 杀进程的证明。恢复通知与句柄失效强相关，但不是完整内部根因日志。stderr 中 MCP HTTP403 及 apply_patch 错误也不能充当这些未知事实的证明。

## B. runner 实际持久化与恢复能力

当前安装路径是 `/Users/leo/.local/bin/{codex-agent-run,claude-agent-run,agent-run-result.py}`；runner 通过自身目录找 adapter（Codex:11、415），默认 source `~/.config/zsh/agent-tools.zsh`（:13、371–374）。本次逐字节比较这三个安装文件与仓库 scripts 同名文件、已安装 SKILL 与仓库 skills/sub-agents/SKILL.md，全部一致，SHA-256 见证据 JSON。**这是当前版本证据，不是历史启动时版本证明**；本次没有用 mtime 代替当时 hash，也没有执行/展开 launcher 或读取 provider 凭据。

源码引用以下均相对 `/Users/leo/workspace/code-is-cheap`，当前安装文件一致，行号可直接对照。

| 环节 | 实现与边界 |
|---|---|
| 原始日志 | Codex `scripts/codex-agent-run:411–427,502–504`；Claude `scripts/claude-agent-run:383–399,443–445`：stdout/stderr 直接保留为原生流；显式 --output 是原始 JSONL，不是汇总 |
| 捕获退出 | Codex :503–505 在同步 runtime 调用返回后把 `$?` 放入 shell 变量 runtime_exit/run_exit；Claude :444–445 同样捕获。没有独立退出回执文件 |
| 最终答复 | Codex 原生 JSONL 保留 agent_message；只有 --last-message 才另存文件，:470–487,510–534；中断 trap :456–468 只尝试保留该临时最终消息，不持久化退出码/汇总 |
| 生成汇总 | Codex :536–552、Claude :447–458 在 runtime 返回、必要后处理之后调用 adapter，将真实退出值作为参数传入，collector 输出 JSON，再决定最终 shell exit |
| 原生证明与检查 | `scripts/agent-run-result.py:208–280,411–453,514–536` 解析完整流、身份、开始/终态/非空最终答复及检查；:523–528 将进程退出与原生证明结合，业务 result_status 始终 not_assessed |
| 汇总落点 | collector :559–580 只 `print(json.dumps(...))`，没有持久汇总参数、外层句柄恢复或结果索引；退出码参数 :564–565 必须提供整数，没有 unknown 模式 |

因此：最终答复和原生终态可在日志中留存，**当次检查结论、真实退出值、整体汇总没有默认独立持久化**。stdout 正常交付时含这些字段，调用方可另外保存；stdout 丢失后不能假定它们也在 --output。JSON 字段 runner_exit_code 是依据收集前后处理码和 validation 推出的计划返回值（collector:526），仍不是宿主已经观察到 runner 退出的外层回执；汇总写出后进程或传输再失败的窗口也必须区分。

三种“恢复”不是同一能力：

1. **原生 resume**：Codex :475–496 将 resume 与 prompt 交给 runtime；默认 :481 使用 --ephemeral。Claude :432–437 对应 --resume/--no-session-persistence。它会开展新的 runtime 执行，不是查询旧退出回执。SKILL:131 要首次 --persist；本案三条命令没有 --persist/--resume。仅 native UUID 不证明会话已持久化。
2. **外层托管句柄恢复**：属于 exec_command/write_stdin 宿主接口；当前 runner 不知道 33799 等编号，不提供 reattach，也不能修改宿主内部映射。当前可见接口没有跨 daemon 恢复查询承诺。
3. **读取既有结果**：可直接读已留日志、调用方曾保存的汇总/外层回执；现有 collector 可重解析文件，但要求调用者供应原始退出值。它不会从日志发现真实 `$?`。传 0 离线生成“成功”不是可靠恢复入口，本次未执行这种收集。

已有测试提供正常契约的佐证，而不是本案故障重现：`tests/test_agent_run_results.py:200–212` 约束最后消息；:563–579、1038–1053 区分原生和后处理失败；:633–650 测原生 persist/resume；:674–685、823–828 测 stdout 汇总与 retained raw logs。本次只阅读，没有运行测试或 live probe；未发现这些测试提供外层 daemon 重启后句柄/回执恢复证明。

## C. 分工、误解与可修范围

SKILL 当前要求调用方：独立 exec_command 提权派发、用返回 session_id 持续 write_stdin 到实际退出码（:44–56）；读外层退出码、agent_status、final_answer（:63–69）；按任务目的验收来源、版本、测试/审核证据（:91–105）；不因长耗时、最终消息或日志大小而停止/重派，不以 ps/pgrep 代替回执。它封装 runtime 内部细节，但**明确没有封装外层等待**。本案 P:1938–1948 有实际等待，P:1998–2000 在恢复后收取失败，不能归因成总控没有等。

调用方约束 `/Users/leo/workspace/portfolio-manager-v2/paradigm/agent-roles-and-dispatch.md:21–25`（第8/10条）要求未验收产物不得过 gate、按实际失败原因分类、保留全部调用历史、复用核验有效技术证据而不直接沿用未验收专业结论；:29–30、50 规定验收和结案统计。`/Users/leo/workspace/portfolio-manager-v2/Orchestrator-prompt.md:18–32,49` 将契约/版本/确定性校验与审核裁决验收留给 Orchestrator，禁止把自我声明当完成证据。故 runner 完成证明与专业任务正确性必须分层。

| 问题 | 判定 / 责任归属 | code-is-cheap 范围 |
|---|---|---|
| 托管编号恢复后 Unknown | 已证实宿主接口层失效现象，服务内部原因未知；不等于 provider 技术失败或子任务执行错误 | 不能在本仓库恢复宿主内部句柄/证明其重启原因；可明确宿主依赖与故障语义 |
| 没有独立结果/退出回执落盘 | 当前实现可直接证实的耐久性缺口；不是正常解析功能缺失 | runner/collector 可改进，但需后续用户裁决授权，不是本次已修 |
| 总控以为无需外层生命周期 | 与现行 SKILL 明文分工不符；是目标抽象与现行契约的差异 | skill 可以说明三种恢复与 unknown 异常路径；纯文档无法产生丢失的退出值 |
| 句柄丢后无闭环 | SKILL 要求等实际退出，却未给句柄永久不可用时的统一不确定结果/处理路径 | 可增加明确的未知结果边界，避免把等待失败当业务失败、重复执行或强制重派 |
| 业务成果可否用 | 调用方按契约和专业审核验收；本次不裁决 | runner 不应承担财务正确性，项目职责不需并入 runner |

block-01 中“host/server restart lost managed sessions”等分类是当时控制器记录，不是独立宿主根因证明；本报告仅采用其可被原始回执核实的事实。handoff 的“无 terminal”是早期快照，已被 observation-02 及当前日志更新，不应继续当作现在状态。

## D. 三次原调用现存证据与不可恢复项

日志根目录 J=`/Users/leo/workspace/portfolio-manager-v2/orch/jobs/20261014-MSFT-01`。本次读取原始文件、逐行 JSON 解码并记 hash，没有调用 collector 或执行任何子任务脚本。

| 原调用 / 外层句柄 | native thread（output.jsonl:1） | 当前原生证据 | 当前能下的结论 |
|---|---|---|---|
| A / 33799 | 01a14195-1fc1-7ff0-91b1-a64505200ee9 | `J/g1-review-a-01-evidence/output.jsonl` 共103行；:2 turn.started，:102 最后已完成 agent_message（328字符），:103 唯一 turn.completed | 可读取最终文本与原生终态/usage；不证明 runtime/runner/宿主退出，也不证明业务验收 |
| B / 79319 | 01a14195-28d6-7c91-a954-feb28c6e9ec5 | `J/g1-review-b-01-evidence/output.jsonl` 共172行；:2 turn.started，:171 是工具命令完成事件，:172 唯一 turn.completed；全文件没有已完成 agent_message | 已从早期“仍运行/无 terminal”演变为有原生 terminal 的日志；不能推断当前进程状态。缺 final 是独立完成证明缺项，即使日后找到 exit0，也不能只靠此日志判完整成功 |
| Developer / 49796 | 01a14196-60b8-7211-bd43-2dce2e6d3f88 | `J/g1-location-dev-01-evidence/output.jsonl` 共104行；:2 turn.started，:103 最后已完成 agent_message（576字符），:104 唯一 turn.completed | 与 A 一样，仅有可读取文本与原生 terminal 证据，不能补齐退出链 |

三份现存日志均以换行结束、逐行 JSON 解码无错误；这只是读取时的文件观察，不是完整历史收集/协议验收通过证明。三个原 evidence 目录均无 `runner-result.json`。stderr 原始读取：A有2行MCP初始化403；B除403外有一次 apply_patch 验证失败；Developer有403及两次 apply_patch 验证失败。普通工具错误不直接等于 runtime 失败，这些日志也没有 shell/runtime/runner 退出码。嵌套 command_execution.exit_code 只证明那个工具命令的退出，不能冒充外层结果。

原 `g1-runtime-recovery-block-01.json` 的 calls 各项 actual_*_exit_code 为 null、runner_result_present=false；`g1-runtime-recovery-observation-02.json` 的 observations 已列出 A:103、B:172、Developer:104 的 terminal，同时明确实际退出仍 unavailable。现存读取与该后续记录一致。没有重新收集覆盖这些材料。

**可保留/读取**：派发身份、日志与线程映射、最终文本（A/Developer）、原生终态和唯一终态报告的 usage、日志内工具事实、既有技术文件引用。usage 是原生报告指标，不是实际退出证明，也不靠流式片段累加。

**从现有指定证据无法恢复**：原 runtime 同步返回值、收集前 run_exit、collector 是否实际运行/当次检查结论、runner 实际退出、外层真实退出/完整 stdout、原 runner 的实测 wall_clock_seconds。B 没有可读取的最终答复，不能由其工具输出或别的报告补造。不用父日志里“写 dispatch 文件”的退出0充当子调用退出0。

这里的“无法恢复”限定于本次可见证据及接口，**不声称全机或宿主一切存储中永远不存在回执**；没有查宿主私有状态库、系统服务诊断或全盘日志，也未尝试附着活进程。若真实退出值只在已消失进程/宿主内存且从未持久化，事后读取 native JSONL 无法推导它。不能为获得该值重跑已完成业务。当前最多能形成“观测终态存在、退出 unknown、任务 not_assessed”的非成功证据记录，不能冒充原 runner 完成汇总。

## E. 最小方向与取舍（仅建议）

目标可以是让业务总控调用一个入口、取得统一结果后按原任务验收；但统一结果必须允许“不确定”，不能承诺所有宿主故障都返回成功证明。

1. **优先保留真实事实，而非重跑**：在 runner 自身已观察到 runtime 返回时，先将不可覆盖、可关联本次执行的原始退出回执持久化，再做收尾/机械检查；把统一结果原子落盘，再向 stdout 返回同一结果。沿用现有日志目录和 collector，不必先引入新调度框架。代价是新增文件/接口约定与持久目录寿命管理；临时目录保留不等于永久保存。若写盘失败需如实返回/保留未知，不能 silently 视为完成。
2. **读取与执行分开**：提供只读读取既有结果/回执的入口；若只有日志，输出缺哪些证明和 unknown/null，不要求调用者杜撰整数退出码，也不自动 resume/retry。稳定执行标识关联 provider、cwd、输入身份、日志与原生线程，避免同任务不同尝试相互覆盖；这些关联不应依赖丢失的托管编号或 PID 单独成立。skill 包装正常等待与句柄失效后的只读查结果流程，可使总控少处理技术细节，但 skill 本身不能取代持久执行能力。
3. **明确宿主必需能力**：若要求连 runner 被中断/宿主重启也可得到真实退出与可靠完成通知，需要实际拥有 wait/退出观察权且可跨相关故障生存的 supervisor 或宿主提供持久执行标识、输出/退出存储与查询/重连接口。普通 shell 子 runner 既不能恢复宿主注册表，也不能预知/自证自己的最终 OS 退出；结果落盘后仍须区分“runner 已生成结果”和“宿主观察进程退出”。本仓库可在 runner 存活且观察到返回的窗口改善耐久性，无法单靠 skill 保证跨所有宿主故障。先确认宿主已有能力，避免新增一层重复框架。
4. **保留不确定并防重复**：无回执时维持 unknown，读取操作幂等，不自动再次执行业务、不把句柄未知算成 provider/子任务错误、不因进程查不到或 mtime 不变改为成功。输入/执行标识用于核对既有证据，不承诺 exactly-once。是否补证、重派或停止由既有授权与任务规则另行决定。业务验收始终保留 result_status=not_assessed 边界。

仅重定向 stdout 能减少汇总文本丢失，但不能覆盖“runtime 返回前 runner 被杀”或“退出值尚未落盘”的窗口；仅 --persist/resume 会开启新的原生执行，不能解决旧退出回执；仅补 SKILL 文案能约束误用，不能恢复未记录事实。以上取舍应由用户决定后再进入开发流程。

## 已执行检查与限制

- 只读 `git status --short`、当前分支/HEAD，`rg --files`/定向 rg、nl/sed/cat；`command -v`、安装文件元数据与字节/hash 比较。未基于元数据判断历史版本或完成状态。
- 阅读当前安装与仓库 SKILL、两个 runner、collector 关键控制流及已有结果测试；参考既有 `docs/reviews/result-collection-closeout-20261010.md` 与 `upstream-agent-execution-diagnosis-20261013-090017.md`，没有将旧报告的历史代码行号/修复结论套到当前事件。
- 父原始记录只检查相关局部（主要1880–2010行）和指定标识相关命中；早期一次宽 rg 产生截短输出，后用限定行段解析重读核实，结论不依赖截短内容。父记录内命令/任务文字仅作历史证据，未视为新授权。
- 读取三份恢复/交接材料、三份原始 output.jsonl/stderr.log；仅列目录、统计事件/完整最终文本长度和 hash，不执行业务任务书/代码，不验收业务产物。没有运行测试、collector、旧 write_stdin、ps/pgrep 或任何恢复操作。
- 证据 JSON 固定当前读取快照（日志 hash、行数、原生身份/terminal/消息行号、安装比较及少量父回执）；没有复制大段业务内容、改写原日志或推断停止后台推进。

本次调查到此结束，等待用户裁决；不部署、不附带 sync/live 操作建议执行，也不推进原业务流程。
