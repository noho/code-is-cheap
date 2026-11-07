# Code Review

## Scope

- Mode: current changes — **affected-surface re-review only**（非 full review rerun）
- Branch or PR: `fix/shim-subagent-message-delivery`
- Base: `main` = `0933796`
- Output file: `docs/reviews/code-review-20261107-214607-ds-flash-redaction-rereview.md`
- Included scope: 仅复核 controller 已接受的 Finding 1 修复面——`docs/gateflow/shim-subagent-delivery/original-live-probe-evidence.json` 的两处旧 assistant 文本脱敏、`redactions` 元数据、`selection` 披露；`redaction-fix.md`、`implementation-validation.md` 的脱敏披露、初始 ds-flash review 的自身引用脱敏、`evidence/sha256sums.txt` 完整性；`controller-validation.json` 列出的受保护文件 hash；native capture evidence 的 manifest 完整性。
- Excluded scope: 生产代码、routes、tests 的功能性重审（明确未变，且不属于本次 evidence-only 修复面）；并发 review 与初始 mimo-flash review（未读取）；原始用户 session/business 文件（未读取）；inference、native probe、focused/full test suite（未运行，按指令不需要）。
- Parallel review coverage: 无。按指令未委托 subagent，未读取其它 reviewer 结论；`implementation-validation.md` 与初始 ds-flash review 仅作为 prior scope evidence，不作为本次修复的独立证明。

## Findings

### 1-已修复-低-original-live-probe-evidence.json 两处旧 assistant 文本的私有业务路径/上下文已脱敏

- **入口/函数**: 证据文件提交/阅读入口（`docs/gateflow/shim-subagent-delivery/` 非生产 artifact）。
- **文件(行号)**: `docs/gateflow/shim-subagent-delivery/original-live-probe-evidence.json:77`、`:140`（`redactions` 元数据在 `:155-170`）。
- **输入场景**: 分支 push 或 PR 共享后，任何可读该 artifact 的人打开证据文件。
- **实际分支**: 静态证据文件，无条件分支。
- **预期行为**: 只保留交付失败事实（child 收到任务、assistant 未按要求返回 token），不出现用户私有业务路径、项目上下文或业务任务选项；若脱敏必须显式披露且不削弱证据。
- **实际行为**: 两处 assistant `output_text` 已替换为显式标记（`[REDACTED: private project context]`、`[REDACTED: private business task options]`、`<private-workspace>`），仍保留“请告诉我这次要处理……”的具体任务请求，且不含 `LIVE_PROBE_OK`；`selection` 明示这两处是脱敏摘录而非原始未脱敏文本；`redactions` 为每处记录 JSON pointer、原始 source line、原始解码文本的 UTF-8 SHA-256、hash 输入约定和原因。原始 source 身份/路径、source-file SHA-256、session/thread/message 身份、精确的无害 initial/followup 任务正文和行号均保留。
- **直接证据**: 当前 JSON 结构解析成功（5 entries，行号 1/11/15/22/24）；两处 redaction pointer 均可解析且 `source_line` 与对应 entry 的 `line` 一致（15、24）；两处当前文本 hash 均不等于记录的 `original_text_sha256`，说明记录值指向脱敏前文本而非当前文本；两处文本无 `/Users/` 路径、无 `LIVE_PROBE_OK`、含具体任务请求；全 JSON 仅含 1 处绝对用户路径（即要求保留的 source identity），无已知业务域词组。`plan.md`（manifest 验证未变）独立记录同一 live probe rollout、行号 11/22、任务长度 64/33，且逐字引用 followup 正文，均与当前 evidence 一致。
- **影响**: 原 Finding 关闭；证据仍能证明 native child 收到无害任务、assistant 询问具体任务而非返回要求的 token，交付失败证据未被削弱。
- **建议改法和验证点**: 无需进一步修改。若未来需要验证原始文本 hash 的真实性，只能由获授权的 controller 对原始 session 文件按记录的 hash 输入约定复核；本次不读取原始 session。
- **修复风险（低/中/高）**: 低（已完成，仅证据脱敏）。
- **严重程度（低/中/高/严重）**: 低。

### 未发现新的实质性问题

本次受影响面复核未发现新的 material defect；剩余观察均为可接受的 residual risk，见下。

## Verification Checks

1. **JSON 结构**: `original-live-probe-evidence.json` 可解析；顶层字段 `source`、`sha256`、`selection`、`entries`、`redactions`；5 个 entries 行号为 1/11/15/22/24，其中 2、4 为 assistant `output_text`。
2. **脱敏标记**: 两处 assistant 文本均含显式 redaction 标记，均无绝对用户路径、无已知业务域词组、无 `LIVE_PROBE_OK`，均含具体任务请求。
3. **`redactions` 元数据**: 恰好 2 条，pointer 唯一且可解析；`source_line` 与 entry 行号一致；`original_text_sha256` 均为 64 位小写 hex；`hash_input` 记录 UTF-8/no-added-newline 约定；`reason` 非空；当前文本 hash 与记录值不同（确认记录的是脱敏前文本）。
4. **证据保真交叉核对**: `plan.md`（SHA-256 `1eaf89306b97ca660d9fed025b2375b05076926eb4ce0d687fb7fe61860f61fc`，manifest 验证 OK）记录 source rollout 文件名、行号 11/22、任务长度 64/33、followup 正文逐字引用；当前 evidence 的 session id、source 文件名、行号、两处任务长度、NEW_TASK header、followup 正文全部一致；两处任务正文均含 `LIVE_PROBE_OK`。`closeout.md` 引用同一 child id，身份一致。
5. **原始身份/hash**: `source` 仍为记录的 Codex session rollout 路径，source-file SHA-256 `a1bdc4345be86fd3980ebbe0e839210dd1dc43f30c324be55a3f7bfd0aef45ef` 保留；session/thread/message ID、agent path、provider 均保留。
6. **review 自身引用脱敏**: 当前初始 ds-flash review artifact SHA-256 `111d8fa3b9a3f532b721ba29325fe7d87d9a6264ff9385a2e574776781d97f8a`，与 `redaction-fix.md` 记录一致；私有 workspace 路径、已知业务域词组等私有 token 均为 0 命中，仅保留泛化的边界/范围表述。
7. **artifact 级业务上下文扫描**: 全部 `docs/gateflow/shim-subagent-delivery` 任务 artifact + 初始 ds-flash review 中，evidence JSON 无已知业务域词组；未变化的 plan/closeout 仅保留泛化 scope/边界表述与调查谱系（canonical agent handle、会话身份），未发现具体私有业务任务正文或私有 workspace 路径。任务 artifact 中除按设计要求保留的 source identity 路径外，仅有临时 fixture 路径和模型 catalog 运行路径。
8. **manifest 完整性**: 正确 cwd 为 `docs/gateflow/shim-subagent-delivery`，执行 `shasum -a 256 -c evidence/sha256sums.txt` → **23/23 OK，exit 0**。使用 `cwd=evidence` 会因相对路径前缀失败，本次未使用。
9. **受保护文件**: `controller-validation.json` 列出的 7 个文件全部与当前文件 hash 精确一致（见下表）。
10. **manifest 调和核对**: `redaction-fix.md` 记录的 `evidence/sha256sums.txt` hash `a7d0b1908e73a95c7e2acc52780abdb29a753517073eefbdb444ee6eed22f8f4`，与将当前 manifest 中 `closeout.md` 一行还原为旧值 `ce69c8de…` 后重建的 hash 完全一致；当前 manifest 为 `839bec5e452aaa8bed888acb248da2da09cfcf83d894d693336cff50944f9875`。这证明 fix handoff 之后唯一变化是 controller 对 `closeout.md` 文档 checksum 的已说明调和，raw native evidence 与代码 hash 未变。
11. **fix report 其它 hash**: `original-live-probe-evidence.json` = `f04e8576…`、`implementation-validation.md` = `f3b9621a…`、初始 review = `111d8fa3…`，均与 `redaction-fix.md` 记录一致。
12. **工作区状态**: `git status` 仅有预期的 4 个 tracked modified 与既有/本次 untracked artifact；本次未 stage/commit/push/deploy，未改动任何文件；未运行 inference/native/full tests（evidence-only 修复，按要求不需要）。

### Protected hashes（controller-validation.json 7/7 匹配）

| File | SHA-256 |
| --- | --- |
| `codex-agent/bin/codex-auto-review-shim` | `cd8e9f218c5a65d65bceff6ffac8b723c075913dad7ca08d999941ee34544dda` |
| `codex-agent/shim-routes.json` | `8b04fec825d53d4c60fbbc80256f9d57cc8d3b1f8a91a645cbe83a62bd8ad48d` |
| `tests/test_shim_subagent_delivery.py` | `d8dc53ebaa1bdb4bf1d485e1ef5a6dd9334e235d87aedfe8b81d764b07b19b40` |
| `README.md` | `bdc0a65cc7264986133705e4b4d71f29f0b90b7feed9b678cb8e0237416f11ee` |
| `README.zh.md` | `af0c43a91600341e57873dc12027869aa5bdaeded6d75f62e60a6d818b10673f` |
| `docs/gateflow/shim-subagent-delivery/native-probe.py` | `f14b59295fa04f4cb925ae3791c9ff47c4a117749e9db8e6b5153d3001002ab3` |
| `docs/gateflow/shim-subagent-delivery/audit-native-evidence.py` | `9cbc234b274ea6149b17ceb4539d484c7c0e21aaea54bf7fd394e8c1ffdb6a37` |

### Native capture hashes（manifest 23/23 OK 中的关键项）

| File | SHA-256 |
| --- | --- |
| `evidence/baseline-rollouts-sanitized.json` | `0db120cec15d9cfdb7d96127f56d7e3e86ab139745c352b72b29422be1efdc7e` |
| `evidence/baseline-wire-shapes.json` | `bbfa9a1e9f85730261de1fbc8c0b8514e99891991fe8cd633dc1e3f89c1e5c3a` |
| `evidence/baseline-summary.json` | `d3912b4a007d8096e823709464b53ae719c0e416adeecfc92702760faa84eec9` |
| `evidence/candidate-run-1/rollouts-sanitized.json` | `dd8c56624255c6a4ef81b579233a9b5dd791021cd5deb55f8fcf8f2e211d5e77` |
| `evidence/candidate-run-1/wire.json` | `9d8d9c2424f93ae52d3bab6102edae01abef787bade17be6a3a04dea988b385a` |
| `evidence/candidate-run-2/rollouts-sanitized.json` | `8176c533fc6acca2bfaf2c9f328d5525332fe2bddc46367781ff1746a68eba78` |
| `evidence/candidate-run-2/wire.json` | `0e393bd0e5c5c0dec8e998a656d2f47dbf1c3bcea9084aca0c82216bb4002754` |
| `evidence/native-audit.json` | `0d21aaaa0716917cc24db04e86efcf8fb34f46f93e186a9fa0fcc6a582b3b9a2` |
| `original-live-probe-evidence.json` | `f04e8576df4dbf571788066cdaa1ddc04c5f29ef494bc46ace408dde841ddf12` |

## Open Questions

无。

## Residual Risk

- **原始文本 hash 不可独立复算**: 两处 `original_text_sha256` 的正确性依赖 fix delegate 的脱敏前计算；独立复算需要读取原始 session 文件，本次明确不在范围内（且被禁止）。当前只能确认 hash 格式、输入约定、pointer/行号一致，且与当前文本不同；这些 hash 作为后续获授权核对的 provenance anchor。
- **无脱敏前字节快照**: 未保留 fix 前 evidence 文件副本，因此无法用 diff 证明所有非脱敏字段逐字节未变。保真性由 `redactions` 仅指向两个 assistant 文本、plan 记录的行号/长度/逐字 followup、身份一致性和 manifest 重建共同佐证；initial 任务正文由 plan 记录长度 64 与内容类别交叉核对（plan 未逐字引用该正文），仍属间接验证。
- **扫描方法边界**: 本次未读取原始 session/business 文件，因此无法用“被移除的确切私有短语”做精确字符串搜索；改用绝对用户路径 + 已知业务域类别 + artifact 全量人工检查。未发现具体私有业务任务正文或私有 workspace 路径。
- **保留的泛化业务引用**: plan/closeout/review 中仍有泛化的业务边界表述和调查谱系 canonical agent handle；判断为 scope/证据链所需，不含具体私有任务内容或私有 workspace 路径，未列为新 finding。若 controller 要求进一步最小化，可作为后续文档整理项。
- **manifest 成员范围**: manifest 保持 23 项，未包含 `redaction-fix.md`、`controller-validation.json` 和 review artifact；这些 control/审计文档的完整性依赖 controller 与 git 状态，不影响 raw native evidence 的 hash 锁定。
- **验证范围**: 本次为 evidence-only 脱敏修复的受影响面复核；未重跑 inference/native/focused/full tests，交付行为与测试结论沿用既有实现验证（生产代码 hash 未变，7/7 受保护文件匹配）。
- **source identity 路径**: 原始 source session 路径按任务要求作为证据身份保留，不属于“不必要私有业务上下文”。
