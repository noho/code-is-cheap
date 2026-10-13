你负责 Gateflow 的 plan gate，禁止实现源码、提交 git、部署、调用其他 Agent。

用户已正式确认 docs/gateflow/codex-server-retry-recovery/goal.md。以它为 binding scope contract，阅读诊断报告与离线 JSON、相关 collector/runner/test 源码及项目指令。此任务已由上游按 AGENTS.md 指定 gpt-6-sol runner 路由派发；你只负责当前 plan，不递归派发，也不执行其他 gate。

只在 /Users/leo/workspace/code-is-cheap 工作。不要读取或修改 portfolio-manager-v2，不重派原业务任务，不修改原诊断成果，不读取凭据。当前新工作分支 fix/codex-server-retry-recovery-20261013，基线991eb26c082e006da80474ff85efc4cfeb1116c0。现有未提交 docs 是本 work unit 成果，无需澄清 ownership。

产物：docs/gateflow/codex-server-retry-recovery/plan.md。必须 code-generation-ready，包含 goal/motivation/success/non-goals、goal alignment、直接代码证据、受影响文件、契约/状态不变项、必要决策、一个行为 slice（含 allowed files/scope/interfaces/invariants/non-goals/verification/completion/stop）、真实验证命令和期待断言、docs decision、分类 residual risks/uncovered areas、完成信号/next entry。按 Gateflow 文件 /Users/leo/.codex/skills/gateflow/SKILL.md 的 plan 要求。

最小实现目标是 recognized_codex_connection_notice 额外精确支持诊断第10次服务器请求处理错误重连通知，将它们加入现有恢复证明队列，不修改恢复门槛或 result_status/schema。明确 retry序号受限与 request ID UUID 形状，但不得泛化所有 Reconnecting/error。正控保留 stream-closed/startup; 回归恢复、未恢复、未知/近似文案、所选机械检查与结构/final/terminal/exit拒收规则，复用已有测试helper而不削弱断言。不引入新机制或顺手硬化。

验证计划需区分离线恢复分支 vs 审核通过后 controller 的 sync及两路 gpt-6-sol/gpt-6-luna Codex真实工具读写探针。本次不要执行 live probe 或部署。不要采用长期模板的 mimo-flash双runtime探针。

你可实际运行最小离线baseline来核清事实，保存命令/结果在plan或独立evidence中；不能让tests/源码进入修改状态。最终答复仅报告plan路径、关键决策、验证事实和缺项。
