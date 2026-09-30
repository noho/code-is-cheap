RUNTIME/PROVIDER/MODEL: codex/mimo/mimo-v2.6-pro
CANARY=mimo-76de0816

# Code Review

## Scope

- Mode: current changes
- Branch: `codex/sub-agents-result-validation`
- Base: `main` (`a827aff`)
- Review timestamp: `20260930-113640`
- Output file: `docs/reviews/sub-agents-result-validation-mimo-20260930.md`
- Included scope: `git diff main...HEAD`、当前未提交的 `skills/sub-agents/SKILL.md` 改动、`scripts/sub-agent-preflight`、`scripts/codex-agent-run`、`scripts/claude-agent-run`、`README.md`，以及仓库中可发现的相关项目约束。
- Git evidence: `git diff main...HEAD` 为空；`git diff --stat` 显示唯一未提交改动为 `skills/sub-agents/SKILL.md`，`35 insertions / 16 deletions`；staged diff 为空。
- Excluded scope: Kimi 本轮审核产物、其它 review artifact、与本次结果验收契约无关的配置/历史会话内容。
- Parallel review coverage: 无。按任务要求未派发子 Agent。
- Project instructions: 仓库内未发现 `AGENTS.md` 或 `CLAUDE.md`；按 `skills/deepreview/SKILL.md` 执行 current changes review。

## Findings

### 1-未修复-高-Codex 工具证据谓词把命令结果和工具执行混为一谈
- **入口/函数**: `Controller Adjudication` 的 `tool_evidence` 裁决，以及 `Result Validation` 的 Codex 工具证据 predicate。
- **文件(行号)**: `skills/sub-agents/SKILL.md:145`、`skills/sub-agents/SKILL.md:170`、`skills/sub-agents/SKILL.md:172`、`skills/sub-agents/SKILL.md:233`
- **输入场景**: Codex 子 Agent 执行 `rg` 预期无匹配并返回 1；或运行测试并以失败结果证明待审代码存在缺陷；或只调用 MCP/file-change 类工具而不产生 `command_execution`。
- **实际分支**: `item.completed` 存在但 `item.type != "command_execution"`，或 `command_execution.exit_code != 0`，固定块只能写 `tool_evidence: no`。
- **预期行为**: `tool_evidence` 应证明“要求的工具路径执行过且取得可核验证据”，与命令的业务语义退出码分开。预期无匹配和暴露缺陷的测试失败可以是有效证据。
- **实际行为**: 新文本在 `skills/sub-agents/SKILL.md:170-173` 明确允许这些非零结果支持 finding 或 warning，但 `skills/sub-agents/SKILL.md:145` 和 `skills/sub-agents/SKILL.md:233` 又要求 `exit_code == 0` 才算工具证据，产生直接冲突。
- **直接证据**: `skills/sub-agents/SKILL.md:145` 写死 `item.type == "command_execution"` 与 `exit_code == 0`；`skills/sub-agents/SKILL.md:170` 明示 `rg` 无匹配可以是已解释 warning；`skills/sub-agents/SKILL.md:172-173` 明示测试失败可保留为有效 finding。
- **影响**: 有效反例、负向搜索结果和缺陷复现会被记为缺少工具证据，导致 `result_status` 被错误降为 `partial/rejected`，或触发不必要重试/切路由。
- **建议改法和验证点**:
  - 把证据维度拆成 `tool_trace`、`evidence_status` 和 `command_outcome`，不要用 shell exit code 代替工具是否执行成功。
  - `tool_trace` 至少区分 `complete | partial | missing | not_required`，并记录实际 event 类型。
  - 增加三类 fixture：预期 `exit_code=1` 的无匹配、作为 finding 的失败测试、无 `command_execution` 的 MCP/file-change 工具；三者都不得仅因退出码或 event 类型被误判。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 高

### 2-未修复-高-Claude canary 不足以证明全部必需工具执行成功
- **入口/函数**: Claude 侧 `Result Validation` 与 `tool_evidence` 裁决。
- **文件(行号)**: `skills/sub-agents/SKILL.md:143`、`skills/sub-agents/SKILL.md:146`、`skills/sub-agents/SKILL.md:148`、`skills/sub-agents/SKILL.md:194`、`skills/sub-agents/SKILL.md:233`
- **输入场景**: Claude 任务要求读取指定 diff、运行测试并写 review artifact；子 Agent 成功读取 canary，但关键 diff 读取或测试命令失败，仍返回合法 JSON `result`。
- **实际分支**: JSON 汇总满足 `subtype`、`is_error=false`、有 `result`，canary 也匹配，因此按 `skills/sub-agents/SKILL.md:233` 得到 `tool_evidence: yes`。
- **预期行为**: canary 只能证明一次指定文件读取成功；不能证明其它必需工具成功。要求工具证据的任务必须逐项核对 artifact、原始命令结果或可用的执行 trace。
- **实际行为**: `skills/sub-agents/SKILL.md:194` 已承认 Claude JSON 无法证明中间工具均成功，但固定块仍把“以 canary 为准”作为 `tool_evidence` 的充分条件，造成结论强于证据。
- **直接证据**: `skills/sub-agents/SKILL.md:146` 只要求 canary；`skills/sub-agents/SKILL.md:154` 也只对 canary 不匹配规定硬失败；`skills/sub-agents/SKILL.md:194` 明示汇总 JSON 不能证明中间工具成功；`skills/sub-agents/SKILL.md:233` 仍写 `Claude: 以 canary 为准`。
- **影响**: 可能把未运行/失败的关键测试、读取或修改步骤标为有工具证据，继而把缺少直接依据的 review 结论误设为 `accepted`。
- **建议改法和验证点**:
  - 把 Claude `tool_evidence` 限定为“canary read 证据”，另设 `required_evidence` / `evidence_status` 核对每个任务要求。
  - 对工具 trace 是验收必需条件的 Claude 派发，使用可审计的 `stream-json` 或独立 artifact/原始输出；否则将相关结论标为 `not_assessed/partial`。
  - 验证一个“canary 匹配但测试从未运行”的反例，必须阻止 `result_status: accepted`。
- **修复风险（低/中/高）**: 中
- **严重程度（低/中/高/严重）**: 高

### 3-未修复-高-正常完成派发缺少强制的失败事件和证据缺口清单
- **入口/函数**: `Controller Adjudication` 的固定裁决块和其后的人读叙述契约。
- **文件(行号)**: `skills/sub-agents/SKILL.md:167`、`skills/sub-agents/SKILL.md:174`、`skills/sub-agents/SKILL.md:176`、`skills/sub-agents/SKILL.md:235`、`skills/sub-agents/SKILL.md:236`、`skills/sub-agents/SKILL.md:242`
- **输入场景**: `setup_status=ok`、`agent_status=completed`，但某条读取关键来源的工具失败未恢复，最终只采纳部分 finding，`result_status=partial`。
- **实际分支**: 可写固定块中的 `result_status` 和 `warnings`；但 `skills/sub-agents/SKILL.md:242` 的逐事件清单只在 `setup_status=fail` 后强制出现。
- **预期行为**: 只要存在非豁免失败、关键证据缺口或非 `accepted` 裁决，就必须列出事件、依赖的证据、受影响结论、恢复情况和最终处置。
- **实际行为**: `warnings` 只允许记录“已解释且不影响结论”的项目；未解决的关键证据缺口没有专门字段。按现有语法，正常派发可在 `warnings: []` 下留下 `partial/rejected`，却没有强制审计链。
- **直接证据**: `skills/sub-agents/SKILL.md:167-174` 要求逐条判断并停 gate；`skills/sub-agents/SKILL.md:236` 只收留不影响结论的 warning；详细清单从 `skills/sub-agents/SKILL.md:242` 开始，语义上限定在 `setup_status=fail`。
- **影响**: 静默丢失关键工具失败或证据依赖，后续 controller 无法复算为什么采纳/驳回，也无法确认 `partial` 的边界。
- **建议改法和验证点**:
  - 将人读清单改为所有 dispatch 的必填项，至少在存在非豁免事件或 `result_status != accepted` 时强制。
  - 固定块增加 `evidence_gaps: []`、`affected_findings: []`、`attempts`，分别记录缺口、受影响结论和重试/切换历史。
  - 验证 `setup_status=ok + result_status=partial + unresolved critical gap` 不能只提交 YAML 而不写事件账本。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 高

### 4-未修复-中-退出证据来源互相冲突，Codex runner 不会写规定的退出标记
- **入口/函数**: `Sandbox Process Management` 与 `Result Validation` 的退出证据收集。
- **文件(行号)**: `skills/sub-agents/SKILL.md:126`、`skills/sub-agents/SKILL.md:129`、`skills/sub-agents/SKILL.md:132`、`skills/sub-agents/SKILL.md:138`、`scripts/codex-agent-run:438`、`scripts/codex-agent-run:440`、`scripts/codex-agent-run:460`
- **输入场景**: Codex 总控通过 `exec_command` 启动 runner，先得到 `session_id`，再由 `write_stdin` 收到宿主的 `Process exited with code N`。
- **实际分支**: runner 把 Codex stdout/stderr 分别重定向到 `--output` / `--stderr`，自身记录 `run_exit` 后直接 `exit "$run_exit"`；输出文件不会追加 `[exited with code N]`。
- **预期行为**: 托管调用句柄返回的退出码应是 Codex 路径的权威证据，并由总控写入报告；文件尾标记只能在对应 harness 确实生成时使用。
- **实际行为**: `skills/sub-agents/SKILL.md:132` 泛化要求 `wait "$pid"` 或输出文件末尾标记，而 `skills/sub-agents/SKILL.md:138-139` 又要求使用 `exec_command` / `write_stdin` 状态。按前者检查 Codex run 会找不到标记，尽管退出码已由句柄返回。
- **直接证据**: `scripts/codex-agent-run:438-440` 只重定向流并保存 `run_exit`；`scripts/codex-agent-run:460` 只退出，不写 marker。`skills/sub-agents/SKILL.md:138-139` 明示 Codex 权威来源是托管句柄退出码。
- **影响**: 正常完成的派发可能被误判为“缺少可信终态”的硬失败，进而错误重试、切换 provider 或阻塞 gate。
- **建议改法和验证点**:
  - 按总控类型明确证据优先级：Codex 用 `exec_command` / `write_stdin` 的终态；Claude 后台用 harness completion；前台用直接返回状态。
  - 删除“所有后台输出文件必有 marker”的泛化，除非该 harness 契约明确保证。
  - 要求把实际取得的退出证据来源和值写进报告，避免只写 `exit status` 而不可复核。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 中

### 5-未修复-中-结果验收失败的重试规则与测量失败禁重试规则缺少优先级
- **入口/函数**: `Retry And Sessions` 的失败分类和 provider switch 边界。
- **文件(行号)**: `skills/sub-agents/SKILL.md:201`、`skills/sub-agents/SKILL.md:204`、`skills/sub-agents/SKILL.md:206`、`skills/sub-agents/SKILL.md:208`、`skills/sub-agents/SKILL.md:211`、`skills/sub-agents/SKILL.md:215`
- **输入场景**: provider 测量批次中的子 Agent 已真实运行，但因任务/工具失败缺少关键 artifact，触发“结果验收失败”。
- **实际分支**: `skills/sub-agents/SKILL.md:206-209` 允许一次同 provider 重试并在再次失败后按上层授权切路由；`skills/sub-agents/SKILL.md:211-212` 又规定测量失败必须计数且禁止重试到成功。
- **预期行为**: 测量批次中的任何已运行 attempt 都应保留为测量数据；不能用 replacement attempt 覆盖。修复性重派只能进入新的、预先定义的批次。
- **实际行为**: 当前文本没有规定“测量禁止重试”优先于通用结果验收重试，也没有把结果验收失败明确归入哪一类，实施者可选择有利于通过率的解释。
- **直接证据**: `skills/sub-agents/SKILL.md:206` 将“派发或结果验收失败”并列放入通用重试路径；`skills/sub-agents/SKILL.md:211-212` 对测量失败给出相反动作；`skills/sub-agents/SKILL.md:215` 要求另建新批次但未说明原失败何时禁止 replacement。
- **影响**: 产生重试到成功的选择偏差、污染测量样本，或在上层没有替补授权时误切 provider。
- **建议改法和验证点**:
  - 写明优先级：measurement attempt 一旦启动即计入，禁止 replacement；只有 controller setup error 可原地修复并另列。
  - 把普通任务的 retry、measurement rerun、provider switch 分成三个显式决策表。
  - 增加反例验证：已运行但缺 artifact 的测量 attempt 必须保留失败并停止该批次，不得用第二次结果覆盖。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 中

## Open Questions

- 无。未读取 Kimi 本轮审核产物，因此本报告不对其结论作任何推断。

## Residual Risk

- 本次改动是协议文档，仓库中未发现针对 `sub-agent-preflight`、runner 输出解析或裁决块的自动化测试；上述反例目前只能靠人工协议执行。
- `turn.completed` 的 JSONL 生命周期事实有本地历史 runner-output 证据支持，但本次没有运行新的 Codex/Claude 子 Agent，故未做实时 provider round-trip 验证。
- Claude `stream-json` 的具体事件 schema 未在仓库中固化；若要以中间工具 trace 作为硬证据，仍需单独定义可稳定解析的 provider contract。
- 本次只读取并审查指定源文件及其直接 runner/README 证据，没有扩大到全部 provider launcher 实现。

## Conclusion And Verification

- Conclusion: 不建议按当前文本直接放行。核心方向“派发生命周期与结果可信度分开、工具失败不自动拒收”是正确的，但 `tool_evidence` 谓词、Claude canary 证据边界、正常派发的失败账本、退出码来源和测量重试优先级仍会造成误判或审计缺口。应先修复高严重度项 1-3，再收敛项 4-5 的契约。
- Verification: 已读取 canary 文件并逐字记录；已检查 `git diff main...HEAD`、`git diff`、`git diff --cached` 和 `git status`；`git diff --check` 通过；`bash -n scripts/sub-agent-preflight`、`zsh -n scripts/codex-agent-run`、`zsh -n scripts/claude-agent-run` 通过；没有派发子 Agent，没有修改待审源文件，也没有 commit、push、创建 PR 或 merge。
