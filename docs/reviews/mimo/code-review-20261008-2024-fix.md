RUNTIME/PROVIDER/MODEL: codex/mimo/mimo-v2.6-pro
CANARY=mimo-a0925cab

# Code Review

## Scope

- Mode: current changes，修复增量复审
- Branch: `feat/agent-deny-list-sandbox`
- Base: `3a563662b959e64234e2ed5a3e4f163bf4ec10ae`
- Frozen HEAD: `a791aa11234e8ace55f5ac954ed2ed3578094659`
- Review time: `2026-10-08 20:42:27 +0800`
- Output file: `docs/reviews/mimo/code-review-20261008-2024-fix.md`
- Frozen diff identity: SHA-256 `6fba620f5be65fcaea0d4d675be63ab3da24a61e8242ae08fe2043209ce9734a`
- Stable patch-id: `98be5d31be820e73406faf6df1ae70909839eda9`
- Included scope: `base...HEAD` 的修复增量；`scripts/agent-sandbox`、`scripts/agent-endpoint.py`、`scripts/agent-tools.zsh`、README/SKILL 和相关测试；runner、preflight、sync/install、srt 0.0.79、Codex 0.161.0、Claude 2.1.294 的相关调用链和行为证据。
- Excluded scope: peer review artifact、真实 endpoints/auth/key、其它项目、tmux pane/workflow、部署状态。未读取 `docs/reviews/mimo-flash/code-review-20261008-2024-fix.md`。
- Parallel review coverage: 无。按本轮明确指令未派发子 Agent。

## Findings

未发现实质性问题。

## Initial Review Fix Conclusions

### 1. `--verify` 伪证和任意 command

结论：安全相关的原缺陷已有效修复；同用户直接调用内部入口仍不是独立权限边界，但不会解除外层 OS 禁读。

- `kernel_denies_read()` 在 `scripts/agent-sandbox:284` 直接查询当前进程的 Seatbelt `file-read-data` 权限，普通 mode/ACL 拒绝不作为成功证据。
- `verify_and_exec()` 在 `scripts/agent-sandbox:299` 要求非空 deny、固定 `manifest.command` 与 argv 完全一致，并要求 basename 为 `codex-agent-run` 或 `claude-agent-run`。
- 每个 deny 同时经过 `sandbox_check` 和实际 `listdir/open`；允许探针还必须可读写，之后才 `execvpe`。
- `tests/test_agent_sandbox.py:65` 的 mode-000 回归实际执行内部入口，确认不启动伪造 runner，并要求错误来自 `effective Seatbelt policy`。
- 原 finding 提出的“父进程一次性凭据/受保护 FD”没有实现。调用者或已在外层 srt 中的模型可构造自己的 manifest/同名 runner，但仍只继承调用者已有 OS 权限，不能读取 deny 内容。本轮授权的安全目标是模型读取前由 OS 阻止，因此该剩余入口身份问题不计作新增实质性回归。

### 2. 必需凭据/配置与 deny-list

结论：按本轮授权正确收窄为运行时依赖，不属于待修 finding。

- endpoints、Codex config/auth 等被识别为 setup/runtime dependency 时，`require_readable()` 在 `scripts/agent-sandbox:158` 对被 deny 的依赖明确失败。
- README、README.zh 和 `skills/sub-agents/SKILL.md:165` 明示：列入 deny-list 会停止 setup，本封装不要求也不提供凭据与 Agent 工具之间的隔离，也不引入 credential broker。
- 原 finding 2 的凭据隔离诉求与本轮“必需认证文件是 runtime 依赖、不要求凭据隔离”的明确授权冲突；行为边界现在被准确文档化并 fail closed。

### 3. stdin 动态 prompt

结论：有效修复。

- `parse_runner()` 在 `scripts/agent-sandbox:129` 要求恰好一个 `--prompt` 或 `--prompt-file`，拒绝 `-`、缺失和双来源。
- `main()` 在 `scripts/agent-sandbox:351` 读取来源并拒绝空白 prompt；在 `scripts/agent-sandbox:419` 写入随机 state 下的 `task.md`，替换 command 中原 prompt 参数。
- `scripts/agent-sandbox:452` 在 exec srt 前把 fd 0 重定向到 `/dev/null`，运行期不能再投递 stdin prompt。
- `task.md` 同时加入 `denyWrite`；kernel test 的 `prompt_write` 实测为 `PermissionError`。
- 测试覆盖缺失、`--prompt-file -`、双 prompt 和命令替换索引。

### 4. Claude helper 的 full-access 冲突参数

结论：有效修复。

- `launch_claude()` 在 `scripts/agent-endpoint.py:173` 于读取连接设置前集中拒绝 `--settings`、`--permission-mode` 和 `--restricted`，支持空格与 `=` 绑定。
- 错误由 `FullAccessConflict` 在 `scripts/agent-endpoint.py:272` 以 exit 2 明确输出，不 exec Claude。
- `scripts/agent-tools.zsh:81` 删除重复 launcher 扫描，实际入口统一由 helper 决定。
- `tests/test_agent_sandbox.py:275` 直接覆盖 helper；现有 launcher full-access 测试继续覆盖 runner -> launcher -> helper 调用链。
- 对最终 prompt 分隔符后的文本不作 flag 解释，避免把 prompt 字面值误判为参数。

### 5. Claude 版本标注

结论：有效修复。

- README、README.zh 和 validation artifact 均标注 `Claude Code 2.1.294`。
- 本机 `claude --version` 为 `2.1.294 (Claude Code)`。
- 原始 `claude-probe.json` 的 init event 为 `claude_code_version: 2.1.294`，terminal result 为 success。

### 附加修复

- Codex `.rules`: `prepare_codex()` 在 `scripts/agent-sandbox:249` 复制用户 `rules/*.rules`，逐文件核对可读依赖并以 `0400` 固化；state 下 rules/config 加入 `denyWrite`。native Codex 测试实际拒绝 `touch`，保留 original justification，且 forbidden output 不存在。
- Claude 原 `denyWrite`: `write_boundary()` 在 `scripts/agent-sandbox:207` 覆盖 user/project/local settings 层，仅接受绝对或 `~/` 字面项，无法推导的相对/glob 配置明确拒绝。srt 0.0.79 文档明确 `denyWrite` 优先于 `allowWrite`；kernel test 证明原 deny 优先于 cwd allow。
- 输出冲突: `scripts/agent-sandbox:376` 在 setup 早期拒绝与原 write denial 冲突的 `--output` / `--stderr` / `--last-message`，包括 `--check`；测试覆盖冲突 fail-closed 和无冲突 selected sink。
- 默认行为: `python3 -m unittest discover -s tests` 中的 full-access/default launcher 测试确认未 opt-in 时不添加 bypass/sandbox 关闭参数，opt-in 时参数固定。

## Parameter Effectiveness

- `deny-list`: caller JSON -> `load_denies()` 规范化/硬链接检查 -> `settings.denyRead/denyWrite` -> `boundary.json` -> Seatbelt query + actual read -> runner。未发现中间值丢失或被默认化。
- `prompt`: runner option -> `parse_runner()` 唯一性检查 -> setup 读取 -> protected `task.md` -> manifest command 替换 -> runner 重读 -> native CLI。启动后 stdin 与原 prompt 参数不再参与。
- `--full-access`: runner normalization -> runner -> launcher -> `launch_claude()` -> fixed `bypassPermissions`/`sandbox.enabled=false`，或 Codex fixed bypass flag。冲突参数在 helper/runner 层显式拒绝。
- Claude original `denyWrite`: discovered settings layer -> literal validation/canonicalization -> final `settings.denyWrite`，与 selected output 冲突时 setup 失败。
- Codex `.rules`: user rules -> snapshot + chmod -> fixed-file write denial -> native Codex execpolicy。测试验证的是实际 native rejection，不只检查文件存在。

## Agent-Facing Assessment

- `skills/sub-agents/SKILL.md` 把任务级 deny-list 明确为 opt-in，且只描述 `codex-agent-run` / `claude-agent-run` 两个 runner，不把 launcher 函数当 sandbox command。
- 独立 Agent 能从 SKILL 知道：先备齐输入；调用 preflight 或显式 envelope；恰好一个非空 prompt；deny-list 是 caller 枚举的普通文件/目录字面路径；必需凭据不在隔离目标内。
- setup 失败要求报告具体 `failure=`，不得自动移除 deny、放宽权限或派发降级命令。preflight 失败时 `command` 为空。
- 启动/收集契约仍完整：Codex 用独立 `exec_command` 并收集 session/exit，Claude 用 harness background handle；运行后核对 exit code、stderr、完整 event/result、最终消息、artifact 和 canary。SKILL 明确 runner 不继承 controller context，必须在 prompt 中交接任务事实。
- 因此 agent-facing contract 不依赖总控上下文；`setup_status=ok` 仍被明确描述为 setup，而不是 kernel proof 或结果可信度证明。

## Covered Files

- 修复增量生产/文档/测试: `README.md`、`README.zh.md`、`scripts/agent-endpoint.py`、`scripts/agent-sandbox`、`scripts/agent-tools.zsh`、`skills/sub-agents/SKILL.md`、`tests/test_agent_sandbox.py`、`tests/test_agent_sandbox_runtimes.py`。
- 允许的证据输入: `docs/reviews/mimo/code-review-20261008-191851.md`、`docs/reviews/agent-sandbox-adjudication-20261008.md`、`docs/reviews/agent-sandbox-validation-20261008.md`。
- 相关调用链/依赖: `scripts/codex-agent-run`、`scripts/claude-agent-run`、`scripts/sub-agent-preflight`、`scripts/install-agent-sandbox.sh`、`scripts/sync-agent-tools.sh`；`@anthropic-ai/sandbox-runtime 0.0.79`；Codex CLI `0.161.0`；Claude Code `2.1.294`。
- 生产 diff file count: 8（review artifact 不计生产 diff）；均 covered，partially-covered 0，not-covered 0。

## Tests And Evidence

- `python3 -m unittest discover -s tests`: 83 tests，OK，6 opt-in kernel/runtime tests skipped。
- `python3 -m py_compile scripts/agent-sandbox scripts/agent-endpoint.py`: 通过。
- `zsh -n scripts/agent-tools.zsh scripts/codex-agent-run scripts/claude-agent-run`: 通过。
- `bash -n scripts/sub-agent-preflight scripts/install-agent-sandbox.sh scripts/sync-agent-tools.sh`: 通过。
- `git diff --check`: 通过。
- `codex-probe.json`: SHA-256 `3f76d63993546265c5d342b787fa8d7f09a999d44fec9671e0106e018671c5c7`，195,585 bytes，6 requests，exit 0，`turn.completed`，无 server error。
- `claude-probe.json`: SHA-256 `456852795841b23a19cf7e778458b629df9d37ffa2cc1a6bde112b75362a8a12`，130,215 bytes，5 requests，exit 0，result success，无 server error。
- 两个 native trace 均未出现 synthetic forbidden text marker；Codex `.rules` 拒绝、escalated approval 拒绝和 forbidden image `EPERM` 均有原始 stderr/request 证据。
- `literal-path-probe.json` 证明 bracket filename 仍按 literal deny，neighbor 可读，selected sink 可写且 neighbor 不可写。
- `app-launch-probe.json` 的 unsandboxed control 可见 synthetic marker，srt 内 LaunchServices 失败且未产生 copy。
- srt 0.0.79 的本地 package README 直接说明 write policy 为 deny-wins，原 `denyWrite` 与 selected output 冲突预检有明确语义依据。
- 本轮未重跑 16 项 nested kernel/native opt-in tests：当前默认 PATH 无 srt，且任务明确禁止通过禁用外层 sandbox 或伪造来重跑。结论核对 controller 的 16-test pass 记录、原始 native traces 和代码/测试，不声称本轮独立重跑 kernel enforcement。

## Adversarial And Architecture Pass

- 失败路径: missing/duplicate/stdin/empty prompt、FIFO、special deny entry、hardlink、unsupported settings、denied dependency、conflicting output、mode-000 false proof、missing/incorrect srt 均 fail closed。
- 权限边界: denyRead 由 Seatbelt 进程树执行；denyWrite 对冲突 allow 具有优先权；inner full-access 不解除 outer Seatbelt。
- State/ownership: prompt、rules、config 的 snapshot owner 是 wrapper；runner 只消费固定 command；native runtime 不负责修正 wrapper policy。
- Overcoupling: 新增检查集中在 `agent-sandbox` / endpoint helper，runner 与 preflight 的公开接口未被穿透修改；重复 Claude validation 被收束到 helper。
- Semantic ownership drift: 版本事实来自 CLI/trace；deny/write precedence 来自 srt policy；Codex rule rejection 来自 native execpolicy。未发现下游用测试或 fallback 重释这些事实。

## Open Questions

- 无。

## Residual Risk

- 未独立重跑 nested kernel tests；runtime/OS/srt 升级后仍须在允许的外层沙箱测试环境重跑 opt-in suite。
- native evidence 覆盖 Bash/Read/view_image/recursive search 和已列 alias，不代表未来新增 runtime-internal file channel 自动被覆盖。
- caller 必须枚举所有已知 forbidden copy；未列副本、运行期由未隔离进程创建/替换的副本，以及并发 rename/mount/hardlink 超出 path-based boundary。
- 非 Darwin、其它 srt/Codex/Claude 版本、自定义无法映射的 permission/settings policy 均明确不支持。
- 直接调用内部 `--verify` 仍要求调用者处于能实际 deny path 的 OS sandbox 中；它不是对同用户的权限提升防护，安全承诺仍以模型所在外层 OS boundary 为准。
