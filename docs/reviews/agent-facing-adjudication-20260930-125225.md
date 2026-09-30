# Agent-facing 审查裁决

审查输入：`docs/reviews/agent-facing-skills-20260930-121558.md`，仓库 HEAD `d65a4ae741ef89d278f5bb6195b763d6bf75c6b5`。本文件是总控裁决与修复交接；Astra 报告不是自动放行依据。

## 裁决

| ID | 裁决 | 理由与修复边界 |
| --- | --- | --- |
| S1 | 采纳，高 | `--prompt` / `--prompt-file` 在新 Agent 独立上下文执行；现有 Dispatch Contract 未提示总控交接父对话中必要的决定、授权、输入版本及依赖。先修技能文本；预检只声明机械检查，不尝试从自然语言推导授权。 |
| P1 | 采纳，高 | Phaseflow 的跨 gate 派发清单缺少被消费 artifact 的精确身份。按 gate 给出必要输入、版本及缺失即停止规则，不传整段历史。 |
| G1 | 采纳，中 | Gateflow 通用通过条件允许 accepted finding 仅有“部分修复”状态就进入 commit。要求阻塞 finding 修复并复核，延期须有明确非阻塞裁决与 owner。 |
| T1 | 有限定采纳，中 | 当前安装的 tmux-cli 在无 `TMUX` 时，`status` 构造 remote controller 可新建 session；技能把它写成只读 socket 预检。修技能的环境前提及安全 discovery 顺序；不声称所有版本都相同，也不修改外部依赖。 |
| P2 | 采纳，中 | Phaseflow 把任务自报完成与 runner 进程终态并列为返回条件。区分任务状态、派发生命周期、结果验收；runner 采用 sub-agents 终态规则，tmux 长驻 CLI 采用 pane completion。 |
| S2 | 采纳，中 | preflight 的 `--prompt-file` 分支未加入本轮 CANARY 协议。让完整 prompt 也产生本轮 run_dir 内的最终副本并追加固定报告协议；保留原文件，不把 token 本文写入 prompt。 |
| S3 | 采纳，中 | 手工预检中的 Codex profile 路径与当前 launcher 不符。按 business/非 business 当前解析路径更新并对照脚本。 |
| D1 | 采纳，中 | PR review 缺少不可变 head/base 身份及本地深挖版本核对。记录 OID、审查快照和收尾版本，不改动用户工作树。 |

Planreview 无实质性 finding，不作修改。报告中的其它可选改进暂不纳入本轮，以免扩大范围。

## 交给实现 Agent 的任务边界

- 只改以上八项所需的六份技能与 `scripts/sub-agent-preflight`，必要时添加紧贴行为的轻量验证；保留现有 Result Validation 的按证据影响裁决，不回退到“任何工具失败一律拒收”。
- `sub-agents` 必须明确：独立上下文指 runner 收到的任务 prompt 在新 Agent 中执行；相同 `--cwd`、同一文件系统或相同 provider 不代表继承总控对话。只交接本任务必要事实及可定位文件/版本，不要求转发完整历史或秘密。
- `setup_status=ok` 只代表可机械验证的 setup 通过；总控仍检查 prompt 语义、授权、scope、并发写边界。子 Agent 必需信息缺失时应报告 blocked，不能猜。
- 所有修改保持技能可读、不过度模板化；不要静默改变 runner 对外参数契约。若发现需扩大范围，先报告，不自行扩展。
- 不 commit、push、创建 PR、修改 live 安装，或再派发 Agent。报告改动、验证与剩余风险，供总控和 MiMo/Kimi 复审。

## 验收信号

八项均有对应的最小修订及可复核的反例/验证；`--prompt-file` 和 `--task-file` 两条 preflight 路径都能让子 Agent 得到本轮 CANARY 文件路径，且 prompt 不含 token。六份技能没有互相矛盾的终态或 gate 条款。审查完成后由总控逐条复核并派 MiMo/Kimi 独立 review。
