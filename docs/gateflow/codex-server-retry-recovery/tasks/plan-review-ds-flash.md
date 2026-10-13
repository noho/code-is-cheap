使用 $planreview 完成 Gateflow plan review，独立 adversarial 审核，不实施、不提交、不部署、不派其他 Agent。
你已由上游按项目指令通过 claude-agent-run/ds-flash 派发，本任务只负责当前 review；不要递归执行 AGENTS.md 的派发流程。
必须阅读 /Users/leo/.codex/skills/planreview/SKILL.md 并按其要求实质审核。Goal contract已正式确认：/Users/leo/workspace/code-is-cheap/docs/gateflow/codex-server-retry-recovery/goal.md，plan=/Users/leo/workspace/code-is-cheap/docs/gateflow/codex-server-retry-recovery/plan.md，本次冻结SHA256=b886991abda482b959e90344188c703734d346b20b4a6654fe4195818d4c83be，base=991eb26c082e006da80474ff85efc4cfeb1116c0。
核对 goal-bound minimal design、必要文案/UUID/retry形状、完整恢复证明不放宽、单一行为slice、实现边界与独立测试oracle，及受影响的所有拒收门槛。基线 evidence/plan-baseline.json 可复用，但不能当作修复验证。已有诊断保留，不读取调用方业务仓库或凭据。按 Gateflow 判断真实 blocker，避免把局部代码问题、措辞重复或scope外硬化当作新plan门槛。
唯一可写文件：/Users/leo/workspace/code-is-cheap/docs/reviews/plan-review-20261013-093112.md。此路径时间戳由controller在本机系统时钟真实生成，避免两路同秒冲突。按skill完整格式写 assumptions/lenses/findings/open questions/residual risks含owner和分类、pass/pass-with-risks/fail、当前target哈希、validation及next entry。保持plan和源码只读，不改state。reviewer不得因对方可能通过而省略独立判断。
最终只给结论、报告绝对路径和实际需controller裁决项。
