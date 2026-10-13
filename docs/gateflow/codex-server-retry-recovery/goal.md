# Goal confirmation: SubAgents 上游服务器重连恢复识别修复

Gate: goal confirmation。Status: confirmed by user。Work unit: codex-server-retry-recovery。
Branch: `fix/codex-server-retry-recovery-20261013`。Base commit: `991eb26c082e006da80474ff85efc4cfeb1116c0`。

## 已获授权与 ownership

用户已授权新工作分支、新 draft PR、按 Gateflow 推进至 final closeout、自行总控裁决；修复通过审核后 sync to live，并以 gpt-6-sol 与 gpt-6-luna 分别在 Codex runtime 执行真实工具读写探针。未授权 merge。

Preflight: 原分支 `docs/upstream-execution-diagnosis-20261013`，仅两份未跟踪成果：`docs/reviews/upstream-agent-execution-diagnosis-20261013-090017.md` 及同名 `-offline.json`。两者属于本 work unit 的诊断依据，原样保留，在 accepted plan checkpoint 纳入；没有无关 dirty changes。已按授权创建新的修复分支，源码尚未修改。

执行路由：plan/implementation/fix 由 `$sub-agents` 的 codex-agent-run / gpt-6-sol；plan review 用 `$planreview`，其余代码/aggregate/PR review 用 `$deepreview`，每个对应 gate 由 claude-agent-run / mimo-flash 和 ds-flash 两路独立并行完成。总控读证据并裁决，不用 reviewer 共识替代验证。

## 目标与动机

修复已证明的当前 collector 识别缺口：精确识别诊断第 10 次两条服务器请求处理错误的原生重连通知。识别仅将它们加入现有待证明恢复队列；只有现有完整恢复证明及所选机械检查均满足，才降为 warnings。否则仍拒收。

文案固定部分为 `Reconnecting... N/5 (stream disconnected before completion: An error occurred while processing your request. You can retry your request, or contact us through our help center at help.openai.com if the error persists. Please include the request ID UUID in your message.)`。N/UUID 的精确受限形状由 plan 明确，不能固定为两个历史 request ID，也不能泛化成任意服务器 error。

直接源码依据：`scripts/agent-run-result.py:49` 只 fullmatch stream-closed 文案；`:262` 未识别顶层 error 直接记 errors；`:309` 现有恢复证明检查单一有效起始帧、顺序、有效后续 final、成功 terminal、实际 native/precollection 退出以及其他机械 errors；`:506` 据 errors 拒收并返回 runner1。诊断离线包中两种当前 collector 的精确错误消息复核均为 rejected/errors2，正控已支持的 stream-closed 可恢复，证明此 work unit 成立。

诊断依据：`docs/reviews/upstream-agent-execution-diagnosis-20261013-090017.md` 与 `docs/reviews/upstream-agent-execution-diagnosis-20261013-090017-offline.json`。当前复核源码与上述诊断匹配。无需进一步读取调用方业务资料。

## 成功信号

1. 两条案例消息在完整有效后续结构、native/precollection exit0、所选机械检查通过时被降为 warnings；仍输出 `result_status=not_assessed`。
2. 未恢复、未知或近似而不受支持的 error，以及结构/顺序/final/terminal/退出码/所选机械检查失败仍拒收；现有 stream-closed 和 startup 恢复规则保持。
3. 对修复版本有真实离线回归与失败对照，覆盖恢复、未恢复、未知错误及受影响的现有拒收门槛。普通 live 成功不能替代重连分支离线证据。
4. 所有必需 gates 的双路独立 review、裁决和适用验证齐备，新 draft PR 保持 draft，并记录 commit、PR 身份及最终 push。
5. 审核通过后执行 `./scripts/sync-agent-tools.sh`，保存实际输出、退出和安装文件一致性；若脚本涉及的其他组件与 live 不一致，先检查 ownership/授权范围再部署，不顺带发布无关版本。
6. sync 后用已安装 codex-agent-run 的 gpt-6-sol 与 gpt-6-luna 各做独立普通 live probe：真实工具读取预置输入、计算确定结果、写新产物并读回，总控核验文件内容与原生工具结果。保存代码/安装 hash、调用 argv、runtime/runner/外层退出、终态、工具结果和产物。失败保留并诊断，不凭文字答复通过，不触发原业务任务。

## 范围、非目标与 docs decision

预计工程变更限 `scripts/agent-run-result.py`、`tests/test_agent_run_results.py`、必要的现有 runner 文档及本 work unit artifacts/脱敏回归证据。plan 负责明确最小实际文件集和单个可验证行为 slice。

不扩展为所有 Reconnecting/error 放行；不改恢复证明 state machine、结果 schema 或业务判定职责；不重构通用 collector、不新增重试/自动重派/动态权限机制；不改 Seatbelt、provider routing、模型配置或业务输入语义。不能重派原业务任务，不修改 portfolio-manager-v2 文件、计数或历史验收。不执行长期模板的 mimo-flash 双 runtime 探针，不 merge/approve/mark-ready/request-reviewers/外部 comment/新建 issue。

新 matcher、回归及必要说明构成一个行为增量，避免多 slice/新机制的 gate 成本和 goal drift。保存原诊断的历史结论，不覆盖为修复后结果。

## Blocking questions 与 residual risks

无技术或 ownership blocking open question。用户已正式确认本 goal contract，目标、非目标、单一行为增量、审核路由和成功信号均通过；本确认没有新增范围或授权 merge。

- 识别/降级缺口：fixed in current slice（计划）；放行前以实际修复及 review 证据确认。
- 新的服务器错误文案及不可见的服务/网络根因：assigned to later work unit；owner 为 SubAgents 上游维护者，本次不新增 issue、不泛化识别。
- 第 10 次历史业务未完成和原整轮恢复证明未知：assigned to later work unit；owner 为原调用方，当前授权明确不重裁历史验收，不阻塞对现有精确文案的离线修复。
- live 探针无法强制真实服务断流：assigned to later work unit；owner 为 SubAgents 上游维护者；当前授权已指定普通工具 live + 重连分支离线回归各自证明范围，不把普通 live 当成断流实测。

Artifact path: `docs/gateflow/codex-server-retry-recovery/goal.md`。
Next entry point: plan，随后按固定 Gate Order 自动推进至 final closeout。
