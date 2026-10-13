# Final closeout — SubAgents 上游服务器重连恢复识别修复

Gate: final closeout。Decision: **pass for the confirmed goal contract**；work unit completed。实际shell工具验收通过，保留两条MCP连接环境失败；不声明全部MCP工具健康。
Branch: `fix/codex-server-retry-recovery-20261013`。
Draft PR: https://github.com/noho/code-is-cheap/pull/58（仍draft/open，用户手动merge；未merge/approve/mark-ready/request-reviewers/comment）。
Issue link/comment: N/A，本次为bug-fix work unit，未提供/创建GitHub issue。

## 实际改动

`scripts/agent-run-result.py` 仅在 `recognized_codex_connection_notice` 增加精确服务器请求处理错误重连文案。retry单字符ASCII1–5、分母固定5、request ID小写hex UUID形状；两条诊断历史消息及其他同形ID进入原候选队列，只有既有完整恢复证明与所选机械检查满足时才降为warnings。unknown/近似、未恢复、结构/final/terminal/退出与机械检查拒收规则保持；生产其余AST完全相同。

`tests/test_agent_run_results.py` 新增五个行为回归入口和兼容的可选helper参数，56旧测试方法AST保持；oracle独立于生产matcher，逐条核对行号、原文、分类、前缀及计数。`README.md` 仅更新现有runner-results支持边界。没有新retry/权限/schema/业务判定机制，`result_status=not_assessed`保持。

原诊断、goal/plan/baseline原样，未重派原业务任务、未修改portfolio-manager-v2文件、计数或历史验收。第10次历史整轮恢复与业务完成仍不由本修复重裁。

## Commits、审核与裁决

| Checkpoint | Commit |
| --- | --- |
| accepted plan | `ca98d59242cd16f8305331d310a1bdde93fc0270` |
| accepted S1（代码实现） | `817f2089ac389589a9ac0ded9d2c4d929086e8fc` |
| accepted aggregate deepreview | `cfe37cb36c150df4385516c3ce213ac15b7768c0` |
| draft readiness | `2d1cbbc283d2bc042ba20be713246898f3f4d742` |
| accepted PR review（已push，部署批准版本） | `8c18464d24092d3eabb6cdce727744a755ed27ea` |

plan/implementation由codex-agent-run/gpt-6-sol完成；planreview、slice deepreview、aggregate deepreview、PR deepreview均由claude-agent-run/mimo-flash与ds-flash同时独立派发。8份独立报告与实际退出均可取回，所有外层/runtime/runner退出0；各gate总控实质裁决零material findings、零blocker、零needs-more-evidence，没有实际需要的fix/re-review，未制造空loop。

| Gate | 两路报告 | Controller decision |
| --- | --- | --- |
| plan review | `docs/reviews/plan-review-20261013-093111.md` / `093112.md` | plan-adjudication.md pass |
| S1 code review | `docs/reviews/code-review-20261013-095614.md` / `095616.md` | code-adjudication.md pass |
| aggregate | `docs/reviews/code-review-20261013-101110.md` / `101111.md` | aggregate-adjudication.md pass |
| PR #58 | `docs/reviews/pr-58-review-20261013-103402.md` / `103403.md` | pr-adjudication.md pass |

PR review锁定head `2d1cbbc…` / base `991eb26c…`：三个独立精确GitHub compare响应均1344496 bytes、53 files、rawSHA256 `752ba59000536e904a9417f6728b00f40bf93bceb02f57e4e38eedcfc329efaa`，原始文件与压缩归档实际一致；读前/读后/收尾OID稳定。与本地精确OID diff仅12处hunk函数context展示不同，全部内容/范围/路径/模式/numstat相同，无截断。title/body与实现和实际证据一致，无CI/checks属仓库现状。accepted PR review提交只增加证据/docs，代码仍与受审版本一致，实际push0后才进入draft-PR-pass。

## 修复分支离线验证

- V1五个新回归入口：`Ran 5 tests / OK`，命令exit0，覆盖精确消息、形状/文案/envelope近似拒收、完整恢复门槛、所选checks及实际退出码。
- V2整文件：`Ran 61 tests / OK`，exit0；diff-check0，旧stream/startup、strict JSON、shape/order/final/terminal、canary/artifact/last-message、native/postprocessing、Claude fatal、detail原始输出、count/cap等断言保持。
- V3六组已保存输入真实重放：精确双通知+有效后续变为0/passed/errors0/warnings2；未恢复仍1/rejected/errors4；unknown仍1/rejected/errors1，其余旧场景状态/计数不变。并非历史业务整轮重放。
- 两路slice/aggregate/PR还独立执行边界和保存输入对照；mimo额外25条新通知cap探针通过。所有复用验证均核对实际命令、退出、可取回源/输入快照、hash/环境和范围，不以裸pass替代。

完整命令/输出/退出及冻结版本见 `evidence/implementation-v1.json`、`implementation-v2.json`、`implementation-v3.json`、`implementation-replay-reports.json` 与各review receipts。生产collector SHA256：`8a0be0d0e7d472ff145ee1c691f1849f7480cadd239a9f2dfb4e43900e3a0153`。

## 已授权 sync to live

从本仓库包含已批准改变的checkout执行：

```bash
./scripts/sync-agent-tools.sh
```

实际exit0。部署前12目标实测：只有collector与live不同且为本次批准版本，其他11个相同、均普通文件，无越scope/ownership不明差异。部署后12/12与批准Git源码逐项字节一致，最终复核仍一致。source批准commit为`8c18464…`，安装collector hash为上述`8a0be0d0…0153`。实际stdout/stderr/退出、路径、模式及前后完整manifest见 `evidence/sync-before.json`、`sync-run.json`、`sync-after.json`。

本次live同步已完成。适用的再同步命令为上面的sync-agent-tools；skills/profile/catalog/shim源码未变化，未运行其余sync脚本。交互launcher函数变更后用 `source ~/.zshrc` 或新shell；已在PATH的installed runner调用不需要source。本次launcher内容未变，probes直接调用已安装runner。

## 两路真实 Codex 工具 live probes

实际CLI版本：`codex-cli 0.162.1`（沙箱外实际version命令exit0）。两路各一次，未重试、未换provider、未做长期模板的mimo双runtime探针。

通过已安装 `/Users/leo/.local/bin/codex-agent-run`，显式`--provider`、`--cwd /Users/leo/workspace/code-is-cheap`、`--sandbox workspace-write --no-persist`，独立新目录/输入/输出/logs，声明新产物`--artifact`与`--last-message`。完整实际argv、prompt/input hash、source commit、installed runner/collector/launcher版本见 `evidence/live-probe-dispatch.json`。

| 路由 | 外层 / runtime / runner exit | 原生工具结果 | 实读产物 | runner机械状态 |
| --- | --- | --- | --- | --- |
| gpt-6-sol / Codex | 0 / 0 / 0 | 3次command_execution，均completed/exit0，原生行5/7/9 | `{"probe":"gpt-6-sol","count":3,"sum":41}` | needs_review；errors0/anomalies1/warnings0 |
| gpt-6-luna / Codex | 0 / 0 / 0 | 3次command_execution，均completed/exit0，原生行5/7/9 | `{"probe":"gpt-6-luna","count":3,"sum":41}` | needs_review；errors0/anomalies1/warnings0 |

总控独立核对：第一工具实际读取input并显示`[7,11,23]`；第二工具实际Python从该文件计算`len(values)/sum(values)`，用`open('x')`创建新JSON并打印；第三工具再次cat结果。native command/output、磁盘JSON和独立期待值相同，输入hash未变、产物普通单链接文件、final file与event final一致、安装hash运行前后不变。不是仅源码测试或最终文字回应。完整原生JSONL、stderr、report、managed/outer退出、tool记录、产物及verification均保存：

- `evidence/live-probes-20261013-105713/gpt-6-sol/`
- `evidence/live-probes-20261013-105713/gpt-6-luna/`
- 汇总：`evidence/live-probe-verification.json`、`evidence/final-controller-check.json`。

**两条真实环境失败保留并诊断：** 每路stderr各一行`rmcp::transport::worker`的`UnexpectedServerResponse HTTP 403`，返回`error.code=challenge`、`This request requires a challenge to be completed`，worker transport退出。原文/时间/request id完整保留，没有隐藏或改为warnings。三个builtin shell调用均成功，native没有记录MCP工具请求；本次必须的shell读/算/写/读回因此通过。具体MCP server/endpoint、challenge触发原因及MCP功能可用性仍未知；不能外推为完整runtime/MCP健康。该实际问题归后续独立环境诊断，不改profile/认证/权限来绕过，不重跑以覆盖第一轮失败记录。

普通live成功只证明已安装runner的真实shell工具路径；**重连降级分支仍由同一版本V1–V3离线正反回归证明**，本次没有强制真实服务断流。

## Findings / remaining risks / owners

| 状态 / risk | 分类 | Owner / destination / 本次依据 |
| --- | --- | --- |
| 本案精确服务器消息识别缺口 | fixed in current slice | 已实施、审核及同版离线验证，并sync到live |
| 未来文案/UUID表示/预算变化与三处独立字面量维护 | assigned to later work unit | SubAgents上游维护者；白名单外继续fail-closed，当前无泛化 |
| 历史运行身份/完整恢复证明、服务/网络根因与原业务验收 | assigned to later work unit | 技术归上游维护者，业务/计数归原调用方；本次没有重裁历史 |
| live未强制真实断流 | assigned to later work unit | 上游维护者；本goal已规定离线与普通工具live各自证明范围 |
| 两路实际MCP HTTP403 challenge | assigned to later work unit（非本shell probe blocker） | Codex runtime/MCP连接维护者；需后续server name/非凭据endpoint、握手请求/响应事件核对；当前仅观察到403及未使用该路径，shell证据完整 |

无未修复accepted finding、无未分类风险、无未完成本goal success signal。临时review/探索工具错误和总控一次JS声明解析错误均保留并更正；实际失败没有被替换为另一个测量样本。没有额外外部issue/comment、merge或部署权限扩大。

## Completion / next entry

final-closeout-pass；当前work unit completed。最终证据/docs将作为专属closeout提交push到同一draft分支，代码仍为被审核及已安装的`8a0be0d0…`版本。下一入口：用户手动merge PR #58。后续文案变化或MCP challenge诊断需新的独立work unit；本任务不自动扩张。此同版live同步已完成，无需为当前修复重复部署。
