# Implementation: Codex 服务器请求处理错误重连通知

Gate: `implementation`。Slice: `S1 — 精确服务器重连通知参与现有恢复证明`。
Work unit: `codex-server-retry-recovery`。Status: implementation complete；待 controller code review，未标记 review/slice pass。
Branch: `fix/codex-server-retry-recovery-20261013`。
Target: accepted-plan HEAD `ca98d59242cd16f8305331d310a1bdde93fc0270` 加本次三份工程文件的工作区改动；本实现者没有提交。
Binding plan: [plan.md](plan.md)，SHA256 `b886991abda482b959e90344188c703734d346b20b4a6654fe4195818d4c83be`。
Goal 与裁决沿用 [goal.md](goal.md)、[plan-adjudication.md](plan-adjudication.md)，未扩张契约、门槛或工程范围。
Artifact path: `docs/gateflow/codex-server-retry-recovery/implementation.md`。
Next entry point: `code review`，由 controller 派发两路独立 review 并裁决。

## 目标版本与改动文件

| 工程文件 | 实际改动 | 验证目标 SHA256 |
| --- | --- | --- |
| `scripts/agent-run-result.py` | 仅 `recognized_codex_connection_notice` 新增第二个精确 fullmatch 分支；旧分支保持。 | `8a0be0d0e7d472ff145ee1c691f1849f7480cadd239a9f2dfb4e43900e3a0153` |
| `tests/test_agent_run_results.py` | 静态历史案例、test-only builder、optional notices/exit oracle、五个 plan 指定入口；旧测试方法保持。 | `394d9e6960553dd8b046c5653ed36aed51f23e2154fe878004e518fa42881dae` |
| `README.md` | 现有 Runner results 段落说明两种精确文案、ASCII N1–5/固定5及小写 UUID 形状。 | `23121d6eddb29703fdc2cba7ab3eb7686d0c4cf6092d3f6c83ffd1d0490c6da1` |

三份工程文件的原始快照/哈希、分支/HEAD/dirty status 在 [implementation-before.json](evidence/implementation-before.json)。
V1/V2/V3 各保存三份工程文件及原样 runner/sync 脚本的完整源码快照/哈希、实际版本命令和检查前后身份。
运行版本为 Python 3.11.15；fake runtime 源码包含在保存的测试文件快照中，不使用模型请求。
`state.md` 是派发前已存在的 controller 改动；本实现者未修改，验证前后哈希一致。
goal、plan、adjudication、plan-baseline 及两份原诊断同样保持原样；没有读取调用方项目、凭据或 live 配置。

## D1–D4 的实现与不变项

- **D1：** 保留 exact keys `{type,message}`、`type=error`、string message 的入口条件。新增 fullmatch 的固定文字、大小写、空格、标点、URL 和括号均逐字表达；N 使用 `[1-5]`，分母固定5；UUID 使用 `[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`。没有 substring、宽泛 wildcard、忽略大小写或 `\d`；不加 UUID version/variant 或历史 ID 绑定。
- **D2：** 新文案只改变识别返回值，原 dispatch/count/首末候选行/20条显示 cap/队列/finalize/proof 完全不改。V2 的 AST 检查确认整个 production 文件除 matcher 外相同；新回归实际经过 start、final、terminal、严格 JSON、其他 errors、所选机械检查及 native/precollection 退出门槛。混合/重复通知也验证没有新增序号递增、去重或 request/thread 关联。
- **D3：** report/schema/CLI/退出传播保持；新测试调用原完整 `assert_report_contract`，验证 `schema_version=1`、`result_status=not_assessed`、final/usage/session/terminal/raw logs，native7保留7，native0/precollection1与postprocessing失败保持1。Claude顶层server error仍致命；Codex `--detail` 保留原始流、stderr及原退出，没有分类前缀。
- **D4：** 两条历史 `2/5`、`3/5` fixture 使用 plan 的静态 UUID，额外 `01234567-89ab-cdef-0123-456789abcdef` 与 N1–5 正控证明形状可变。oracle 不导入/调用生产 matcher；显式期望 notices 必须非空且按实际事件顺序完整存在，逐条核对唯一 source line、完整 event 原文、stream、category、完整恢复/失败 prefix、reason、字符数及无截断，同时核对候选和 warning 计数。近似/未知错误使用原始 diagnostic oracle。共享 helper 的默认 stream 行为与旧断言保持；V2 另确认全部56个旧测试方法 AST 完全不变。

## 实际验证与保存证据

所有命令在本仓库 checkout 执行。保存 JSON 包含实际 argv/可运行 command、cwd、开始/结束时间、outer exit、完整 stdout/stderr、源码快照/哈希和版本。
V3 另保存每组输入 events/JSONL/stderr、输入 SHA256、实际 collector argv、outer exit、stdout/stderr、完整 report 和独立期待值。
测试中的拒收退出是被断言的预期；三个验证驱动自身退出均0，没有测试失败或跳过。

### V1 — 五个新入口

实际由 `python3 -B docs/gateflow/codex-server-retry-recovery/evidence/implementation-verify.py v1` 捕获以下命令：

```bash
python3 -B tests/test_agent_run_results.py \
  RunnerResults.test_codex_server_retry_recovered_connection_notice \
  RunnerResults.test_codex_server_retry_notice_lookalikes_rejected \
  RunnerResults.test_codex_server_retry_notice_recovery_fences \
  RunnerResults.test_codex_server_retry_notice_keeps_selected_checks \
  RunnerResults.test_codex_server_retry_notice_keeps_process_failures -v
```

实际 outer exit0；`Ran 5 tests in 6.458s / OK`。完整输出及目标快照在 [implementation-v1.json](evidence/implementation-v1.json)。

| 入口 | 实际期待断言结果 |
| --- | --- |
| `recovered_connection_notice` | 历史双条/各自单条、N1–5/另一UUID、混合及重复通知干净恢复为 passed/exit0/errors0；warnings等于通知数。startup/普通失败工具/stderr保持needs_review及原anomalies；每条来源、原文和恢复前缀准确。 |
| `lookalikes_rejected` | 0/6/01/Unicode N、错误分母、UUID缺失/大写/非hex/Unicode hex/段长或连字符错/braces、文案/URL/标点/空白/前后缀/换行、非string/missing/extra keys及unknown全部exit1/rejected/errors1/warnings0，原文diagnosis完整。双候选+unknown为errors3/warnings0，未知错误阻断全部降级。 |
| `recovery_fences` | 缺失/重复/畸形starts、初始顺序/notice-before-turn、未知或多条startup、missing/blank/malformed final及final-before-last-notice、missing/failed/duplicate/conflicting/malformed terminal、final/notice-after-terminal、其他终态后事件、malformed JSON均拒收/warnings0；候选原文与既有failure reason逐条准确。无final+terminal的历史双条为errors4。Claude fatal及detail原始流/原退出对照均通过。 |
| `keeps_selected_checks` | 分别无/有startup，真实fake工具候选+匹配canary+新artifact+last-message正控通过；canary mismatch/missing proof/expected读取失败、missing/nonregular/log-alias/hardlink artifact、missing/mismatching last-message全部拒收/warnings0；prelaunch返回2且fake runtime没有启动。 |
| `keeps_process_failures` | 分别无/有startup，native7保持outer/report/runtime7；native0/precollection1和last-message缺失/竞态/不可写postprocessing失败保持1；全部rejected/warnings0，逐条候选的nonzero失败原因准确。 |

### V2 — 整文件回归与diff检查

实际由 `implementation-verify.py v2` 顺序捕获：

```bash
python3 -B tests/test_agent_run_results.py -v
git diff --check
git diff -- scripts/agent-run-result.py tests/test_agent_run_results.py README.md
```

实际三个命令均 exit0；整文件 `Ran 61 tests in 50.129s / OK`，diff-check stdout/stderr均空。
完整测试输出和三文件diff在 [implementation-v2.json](evidence/implementation-v2.json)。
旧 stream/startup、strict JSON、完整shape/order/final/terminal/exit/selected-check矩阵、schema、诊断count/cap/retention后末候选、Claude fatal、raw/detail和临时安装等断言全部通过。
临时安装测试按原测试设置只安装到 TemporaryDirectory；没有sync到live。
独立 AST 比较确认除matcher外production不变，56个旧测试方法完全一致，新增恰为五个plan入口。
本轮未运行全仓unittest discover；plan没有要求以全仓回归替代V1–V3。

### V3 — 保存输入重放

实际由 `implementation-verify.py v3` 捕获：

```bash
python3 -B docs/gateflow/codex-server-retry-recovery/evidence/implementation-replay.py
```

驱动将 plan V3 的逐组collector调用和断言移入可保存脚本，并增加完整report/输入hash保存与历史双条的精确diagnostic断言；没有改变输入或预期契约。
实际 outer exit0；输入 baseline SHA256仍为 `516edbd7ed236558d6233f6880fec14653580331b3230e0c89c3be4b367ee90d`，新collector SHA256与上表一致。
命令/输出/源码版本在 [implementation-v3.json](evidence/implementation-v3.json)；六组完整inputs/collector reports在 [implementation-replay-reports.json](evidence/implementation-replay-reports.json)。临时日志路径已清理，保存快照可重建。

| 保存场景 | 实际 outer / validation | errors / anomalies / warnings |
| --- | --- | --- |
| `case10_exact_notices_valid_finish` | 0 / passed | 0 / 0 / 2 |
| `recognized_closed_valid_finish` | 0 / passed | 0 / 0 / 1 |
| `recognized_closed_tool_anomaly` | 0 / needs_review | 0 / 1 / 1 |
| `case10_exact_notices_no_finish` | 1 / rejected | 4 / 0 / 0 |
| `unknown_error_valid_finish` | 1 / rejected | 1 / 0 / 0 |
| `recognized_closed_startup_valid_finish` | 0 / needs_review | 0 / 1 / 1 |

两条历史通知从baseline正控的errors2变为warnings2；未恢复通知改走原队列的recovery-not-proven errors，总数仍4。其他四组状态/计数保持。
每组都验证runner退出、`result_status=not_assessed`、native0；历史通知逐条精确检查行号/原message/category/prefix/stream/字符数。

## Docs decision、findings与residual risks

Docs decision已落实：仅更新README现有runner-results支持边界，不新增恢复指南，也不覆写原诊断、baseline、goal、plan或reviews。
本实现新增本artifact及 `evidence/implementation-*`，验证驱动源码作为可重放证据保留。
实施/验证未发现需要修复或越scope修改的finding；没有blocked技术问题。此结论不替代controller独立code review/裁决。

| Risk / uncovered area | 分类 | Owner / destination / 状态 |
| --- | --- | --- |
| 已证明server通知识别缺口及受影响门槛 | fixed in current slice | S1实施与V1–V3已完成；controller code review仍须裁决后放行。 |
| 将来其他服务文案、uppercase/其他UUID表示、预算或schema变化 | assigned to later work unit | SubAgents上游维护者；当前精确白名单外继续拒收，无新issue或新slice。 |
| 服务/网络根因、历史adapter身份/完整恢复证明、历史业务覆盖与验收 | assigned to later work unit | 技术根因归上游维护者，历史业务归原调用方；此次仅合成start/final/terminal重放，不重裁历史整轮。 |
| 普通live无法强制服务断流 | assigned to later work unit | SubAgents上游维护者；离线恢复分支证据与controller后续普通live工具探针证明范围分开。 |
| 部署时其他sync目标有越授权且ownership不明的实际漂移 | requiring new issue or explicit user decision（仅条件实际出现时） | controller/C1按plan重查manifest及ownership；本implementation未读live配置或执行部署。 |

Uncovered areas：后续双路code review/裁决、accepted slice commit、aggregate/PR reviews、draft PR/push、C1部署一致性与C2两路工具live probes尚由controller完成；不能把离线通过视作work unit全部完成。
新通知没有复制全部display-cap排列；共享cap逻辑未变，原整文件bounds矩阵通过，遵循已通过的plan裁决。没有later approved slice或新开的外部issue。

## Completion / handoff

S1 implementation和V1–V3已完成，工程改动局限于三份许可文件且production仅matcher；原证据与controller既有state改动保持。
实现者未递归派Agent、提交、推送、创建PR、sync/liveprobe或触发业务任务。
主要产物：本 `implementation.md`、`evidence/implementation-before.json`、`implementation-v1.json`、`implementation-v2.json`、`implementation-v3.json`、`implementation-replay-reports.json`及两个driver `.py`。
最终scope/版本/受保护文件一致性receipt另存 `evidence/implementation-final-check.json`。
Next entry=`code review`；controller负责后续独立review及所有部署。
