RUNTIME/PROVIDER/MODEL: codex/mimo-flash/mimo-v2.6-flash
CANARY=mimo-flash-c0cb127d

# Code Review

## Scope

- Mode: current changes, independent fix re-review
- Repository: `/Users/leo/workspace/code-is-cheap`
- Branch: `feat/agent-deny-list-sandbox`
- Base: `3a563662b959e64234e2ed5a3e4f163bf4ec10ae`
- Frozen head: `a791aa11234e8ace55f5ac954ed2ed3578094659`
- Task label: `deny-fix-review-mimo-flash-v2-20261008-2024`
- Output file: `docs/reviews/mimo-flash/code-review-20261008-2024-fix.md`
- Frozen diff identity: `git diff --no-ext-diff --binary 3a563662b959e64234e2ed5a3e4f163bf4ec10ae...a791aa11234e8ace55f5ac954ed2ed3578094659` SHA-256 `6fba620f5be65fcaea0d4d675be63ab3da24a61e8242ae08fe2043209ce9734a`; 12 changed files.
- Included scope: the fix-increment production files `README.md`, `README.zh.md`, `scripts/agent-endpoint.py`, `scripts/agent-sandbox`, `scripts/agent-tools.zsh`, `skills/sub-agents/SKILL.md`, `tests/test_agent_sandbox.py`, and `tests/test_agent_sandbox_runtimes.py`; the directly exercised runner/preflight/install/sync call chain; the controller adjudication and validation documents; this reviewer's prior report; and the four supplied synthetic evidence JSON files.
- Excluded scope: the peer report `docs/reviews/mimo/code-review-20261008-191851.md` was not read; no other repository, real project, real auth/endpoint/key, tmux pane/workflow, deployment, external message, source change, commit, push, PR or merge was used or changed.
- Scope limitation: one broad local `rg` command incidentally returned cache/path lines outside this repository. Those lines were not used as review evidence; no credential or endpoint file was opened or sought.
- Parallel review coverage: none. Per the task, no sub-Agent was dispatched.

## Findings

未发现实质性问题

## Open Questions

- 无。声明范围外的未来 runtime/channel 扩展仍需新的边界测试，但不构成当前冻结增量的开放裁决问题。

## Residual Risk

- 本轮没有重跑 opt-in 嵌套 kernel/native tests。当前默认沙箱内 `python3 -m unittest discover -s tests` 会跳过 6 项 kernel/runtime tests；按任务限制，本轮未禁用外层沙箱、未伪造 `srt` 来重跑。结论依赖对 controller 的 16 项 kernel/native 原始结果、两份 v2 native evidence、保留的 synthetic state/policy 文件和静态调用链的交叉核对。
- Codex `.rules` 的原生反例只覆盖一个有效 `prefix_rule(... decision="forbidden" ...)`，证明本轮修复的关键策略丢失已消失；没有穷举全部 `.rules` 语法、project rule 布局或未来 Codex rule-format 变化。
- Claude 原 `denyWrite` 的声明支持面是已发现设置层中的绝对路径和 `~/` 字面规则；glob、相对路径、custom read/tool deny、managed policy 均明确拒绝。本轮复核了实现、单测和 controller 结果，但没有独立重跑该 kernel case。
- 同一用户的未隔离进程仍可在运行期替换禁读路径或制造新副本；这是文档已声明的非目标，不是本增量引入的回归。

## Agent-facing Assessment

### 结论

普通独立 Agent 可以仅依赖仓库 SKILL/README 和 preflight 输出正确理解并执行隔离调用，不需要继承总控对话上下文：

- **opt-in 与默认不变**：`README.md:141-143` 明确 `--full-access` 是 opt-in，单独不提供读取隔离；`skills/sub-agents/SKILL.md:140-143` 要求调用方先备齐输入并自建非空绝对字面 deny JSON。
- **具体调用**：`skills/sub-agents/SKILL.md:146-152` 给出 `sub-agent-preflight --deny-list ...` 和显式 `agent-sandbox ... -- <runner>` 两条独立可执行路径；`scripts/sub-agent-preflight:322-340` 先做 `--check`，失败时不打印 dispatch command。
- **输入准备与固定边界**：`skills/sub-agents/SKILL.md:153-156` 说明隐含 `--full-access --no-persist`、不支持 resume/native passthrough/stdin/dynamic prompt、恰一个非空 prompt、启动前快照并关闭 stdin，以及 setup 成功不等于 kernel 证据。
- **缺项与失败报告**：`skills/sub-agents/SKILL.md:158-165` 要求权限错误报告具体缺项、不得自动放宽，并明确 credential/config 被禁读时 setup 停止；实现分别在 `scripts/agent-sandbox:307-320`、`:366-378` 和 `scripts/agent-endpoint.py:164-170` 给出具体失败。
- **生命周期与验收**：`skills/sub-agents/SKILL.md:167-245` 保留独立调用句柄收集、退出码、canary、结构化终态、逐事件错误和 result adjudication，不依赖父对话记忆。

### 参数来源到最终消费点

| 参数 | 来源/规范化 | 最终消费点 | 失效处理 |
| --- | --- | --- | --- |
| `--deny-list` | `sub-agent-preflight:84,327-334`；直接调用由 `agent-sandbox:343` 读取 | `load_denies` → `settings.filesystem.denyRead/denyWrite` (`:427-431`) → `boundary.json` (`:439`) → `verify_and_exec` (`:305-316`) | 非数组、空、非绝对、缺失、special file、hardlink、required input conflict 均 setup fail |
| `--prompt` / `--prompt-file` | `parse_runner:97-132` 恰一且非空 | 内存文本 (`:349-355`) → `state/task.md` (`:419-420`) → 固化 command (`:421-423`) → runner prompt-file | dual/missing/stdin/empty/denied prompt fail；stdin 在 exec 前转 `/dev/null` (`:452-455`) |
| `--full-access` | preflight `:84` 或 runner/launcher 显式 flag | Codex/Claude runner native flag；Claude helper 再注入 `bypassPermissions` 和 `sandbox.enabled=false` (`agent-endpoint.py:228-231`) | Claude 自定义 settings/permission/restricted 冲突由 helper 中心拒绝 (`:164-170`)；Codex sandbox conflict 由 runner/launcher 拒绝 |
| 输出路径 | `parse_runner:107-113` 规范为绝对新文件 | new-path/deny 检查 (`:362-367`) → original-write conflict (`:375-378`) → 仅文件级 `allowWrite` (`:410-418,428`) | 已存在、symlink、deny-list 或 original `denyWrite` 冲突在 runner 前失败 |

SKILL 只依赖可现场取得的事实：runner `--help`、`pwd -P`、preflight key=value 输出、显式 prompt 背景、输出路径和托管句柄。隔离章节没有要求读取 controller conversation、peer report 或隐藏状态。

## 初审与本轮修复逐项结论

| 修复项 | 结论 | 直接证据 |
| --- | --- | --- |
| 初审 1：fresh Codex home 丢弃用户 `.rules` | **已修复** | `prepare_codex` 枚举 `source/rules/*.rules`、逐文件校验可读并复制 (`scripts/agent-sandbox:249-257`)；`rules` 目录进入 `denyWrite` (`:424-431`)。保留 state 中 `default.rules` 内容完全匹配 fixture、mode `0400`、rules dir/state mode `0700`。v2 Codex evidence 的 stderr 实际返回 `rejected: deny synthetic write`，`rule-forbidden-output` 不存在，6 个 mock requests 中禁读 marker 命中为 0。 |
| 初审 2：Claude 版本标注不一致 | **已修复** | `README.md:151`、`README.zh.md:147` 和 validation `:5` 均改为 `2.1.294`；v2 Claude trace 的 init 事件为 `claude_code_version=2.1.294`，本机 `claude --version` 也为 `2.1.294`。 |
| kernel `sandbox_check` + 实际读验证 | **已修复** | `kernel_denies_read` 调 macOS `sandbox_check(file-read-data)` (`:284-296`)；随后实际 `listdir/open/read(1)`，再读写 allowed probe (`:299-323`)。direct mode-000 单测通过并拒绝启动 runner；v2 wrapper stderr 有 `read boundary verified; starting runner`。 |
| 固定 command manifest | **已修复** | 唯一 prompt option 写入 `_prompt_index` (`:117-118`)；快照后替换 command (`:421-423`)；同一 command 写入 manifest (`:439`)，inner invocation (`:446`) 与 manifest 必须逐项相等且 runner basename 合法 (`:299-304`)。v2 保留 manifest 显示 `--prompt-file state/task.md`、固定 outputs、`--full-access --no-persist`。 |
| prepared prompt 快照 + stdin 关闭 | **已修复** | exactly-one/nonempty 检查 (`:129-132`)；读入内存 (`:349-355`)；写入 mode `0600` 的 `state/task.md` 并替换 command (`:419-423`)；exec 前 stdin 指向 `/dev/null` (`:452-455`)。kernel runner 实测 `prompt_write=PermissionError`；保留 task 为 mode `0600`。 |
| Claude helper 参数冲突中心校验 | **已修复** | `launch_claude` 在读取 connection 前检查 `--restricted`、`--settings[=...]`、`--permission-mode[=...]` (`scripts/agent-endpoint.py:164-170`)，以 exit 2 输出冲突 (`:272-273`)；launcher 重复检查已删除。4 类 direct-helper 冲突测试全部通过。 |
| Claude 原 `denyWrite` 层发现与字面保留 | **已修复（声明支持面内）** | 读取原 `CLAUDE_CONFIG_DIR/settings.json` 及 cwd/全部父目录的 settings/local (`scripts/agent-sandbox:207-210`)；绝对/`~/` literal 转为 blocked (`:221-227`)；glob、relative、custom read、tool deny 和 managed policy 明确拒绝。kernel fixture 验证原 deny 胜过 cwd allow，冲突 output 在 `--check` 前失败。 |
| 输出与原写禁令冲突预检 | **已修复** | `original_write_denies` 获取后立即检查全部非 `-` outputs (`:375-378`)，发生在 state/output 创建之前；该列表同时覆盖 Codex `.git/.codex/.agents/.aws` 和 Claude preserved deny。Claude kernel test 对 `cwd/original-blocked` 的 `--check` 得到 `output conflicts with original write denial`。 |
| 正确版本标注 | **已修复** | Codex `0.161.0`、Claude `2.1.294`、srt `0.0.79` 与 README/install/validation/code pin 一致；保留 evidence 中 Claude init 再次确认 `2.1.294`。 |

## Evidence Review

- `/private/tmp/code-is-cheap-agent-sandbox-evidence-v2/codex-probe.json`: exit 0、6 requests、`server_errors=[]`、forbidden request marker 0；wrapper 已完成 kernel read verification；实际 runtime stderr 同时出现 rule rejection、approval=Never 拒绝和 denied image `EPERM`；terminal 为 `turn.completed`。
- `/private/tmp/code-is-cheap-agent-sandbox-evidence-v2/claude-probe.json`: exit 0、5 requests、`server_errors=[]`、forbidden request marker 0；init 为 `2.1.294`、`bypassPermissions`、`mcp_servers=[]`、六工具固定 inventory；terminal 为 `result subtype=success`、`is_error=false`。
- 两份 v2 request body 中 `synthetic-test-key` 命中均为 0；未使用真实 key。
- `/private/tmp/code-is-cheap-agent-sandbox-evidence/literal-path-probe.json`: denied 路径为 `PermissionError`，字面 neighbor 可读，selected sink 可写而 neighbor 为 `PermissionError`。
- `/private/tmp/code-is-cheap-agent-sandbox-evidence/app-launch-probe.json`: unsandboxed control 成功读取 synthetic marker；封装内 LaunchServices 启动失败且 `app_files={}`，未产生副本。
- 保留 Codex `srt.json` 显示 literal `denyRead`、空 `allowRead`、仅 state/cwd/selected-file writes、protected `.git/.codex/.agents/.aws`、task/rules/config `denyWrite`，并关闭 Apple Events 和 nested/network weakening。

## Covered Files

Fix-increment production files read completely:

`README.md`, `README.zh.md`, `scripts/agent-endpoint.py`, `scripts/agent-sandbox`, `scripts/agent-tools.zsh`, `skills/sub-agents/SKILL.md`, `tests/test_agent_sandbox.py`, `tests/test_agent_sandbox_runtimes.py`.

Related call-chain/dependency files read completely or along the exercised paths:

`scripts/claude-agent-run`, `scripts/codex-agent-run`, `scripts/sub-agent-preflight`, `scripts/install-agent-sandbox.sh`, `scripts/sync-agent-tools.sh`.

Allowed review inputs read:

`docs/reviews/mimo-flash/code-review-20261008-192240.md`, `docs/reviews/agent-sandbox-adjudication-20261008.md`, `docs/reviews/agent-sandbox-validation-20261008.md`, and the four synthetic evidence JSON files listed above.

Not covered by content read:

`docs/reviews/mimo/code-review-20261008-191851.md` (peer report, explicitly forbidden), real credentials/endpoints/keys, other projects, tmux panes/workflows, and runtime code outside the fixed version surface.

## Verification Performed

- Frozen identity: `git rev-parse HEAD` = `a791aa11234e8ace55f5ac954ed2ed3578094659`; base object resolves to `3a563662b959e64234e2ed5a3e4f163bf4ec10ae`.
- Frozen diff SHA-256: `6fba620f5be65fcaea0d4d675be63ab3da24a61e8242ae08fe2043209ce9734a`; `git diff --check` passed.
- `python3 -m unittest discover -s tests`: 83 tests, `OK`, 6 skipped.
- Targeted `SetupTests`, `FullAccessTests`, and `PreflightStaleCanaryTests`: 18 tests, `OK`.
- Python compilation, `zsh -n`, and `bash -n` syntax checks passed.
- Version probes: Codex `0.161.0`, Claude `2.1.294`, retained/pinned srt `0.0.79`.
- Worktree remained clean before writing this artifact; no source/test/README/SKILL file was modified.
- No nested kernel/native test was freshly executed by this reviewer; the supplied raw evidence and retained synthetic state were cross-checked instead, as required by the task limits.
