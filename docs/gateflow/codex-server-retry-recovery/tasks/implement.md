你负责 Gateflow 的 S1 implementation。用户goal已正式确认；plan的两路独立planreview及controller裁决通过，当前进入唯一行为slice。你已由controller按AGENTS.md指定 codex-agent-run/gpt-6-sol 派发，只实现当前slice，不递归派Agent，不提交/推送/部署/创建PR。

必读 docs/gateflow/codex-server-retry-recovery/{goal.md,plan.md,plan-adjudication.md}。原诊断及plan-baseline仅是基线证据，禁止覆写。plan SHA256=b886991abda482b959e90344188c703734d346b20b4a6654fe4195818d4c83be；plan定义D1-D4、S1和V1-V3，严格实施，不扩大契约、拒收规则或范围。

只在 /Users/leo/workspace/code-is-cheap 当前fix/codex-server-retry-recovery-20261013分支工作。工程允许文件仅 scripts/agent-run-result.py（仅matcher及必要邻近常量/注释）、tests/test_agent_run_results.py（fixture/兼容helper和新回归，保留旧断言）、README.md（现有runner-results支持边界）。其他文件只读。可写本work unit的implementation.md和evidence/implementation-*新增证据。不要改state、goal、plan、reviews。不要读取或修改调用方项目/计数、凭据、live配置；不重派任何业务任务，不运行sync/liveprobe。

精确支持第10次服务器请求错误重连文案和小写UUID/ASCII N1-5固定/5，送入原恢复队列；其余proof/finalize/result_status/schema不改。旧stream-closed/startup保持；未知/近似、未恢复、结构/终态/退出和机械检查失败继续拒收。禁止泛化Reconnecting/error。

必须执行plan V1五个新入口、V2整文件回归和diff检查、V3保存输入重放。保存实际命令、退出、stdout/stderr、源码及输入hash/版本和完整replay reports在新evidence；不可只写“pass”。测试oracle独立，不用生产matcher筛选期望；逐条校验通知行号/原message/category/prefix/count，旧测试不得弱化。

完成后写 docs/gateflow/codex-server-retry-recovery/implementation.md：gate/S1、目标版本和改动文件、如何达成D1-D4、实际验证/期待断言结果、docs decision、finding/分类residual risks及uncovered areas、完成状态/产物路径/next entry=code review。若目标必须修改matcher之外production或其他scope，停止具体报告；不要自行扩张。最终仅给改动、验证、产物路径和未完成事项。controller负责后续独立code review和所有部署。
