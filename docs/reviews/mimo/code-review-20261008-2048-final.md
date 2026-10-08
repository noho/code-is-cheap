RUNTIME/PROVIDER/MODEL: codex/mimo/mimo-v2.6-pro
CANARY=mimo-13028c30

# Code Review

## Scope

- Mode: current changes，最后小增量针对性复审
- Branch or PR: `feat/agent-deny-list-sandbox`
- Base: `a791aa11234e8ace55f5ac954ed2ed3578094659`
- Frozen HEAD: `b27a9fd9dd985acadfc41b879088cca1fbcf061b`
- Review label: `deny-final-review-mimo-v3-20261008-2048`
- Review time: `2026-10-08 21:02:12 +0800`
- Output file: `docs/reviews/mimo/code-review-20261008-2048-final.md`
- Frozen identity: base OID `a791aa11234e8ace55f5ac954ed2ed3578094659`；head OID `b27a9fd9dd985acadfc41b879088cca1fbcf061b`；head tree OID `503029817e9bcb8bea13a27acb4e730536fbd091`；单提交 `b27a9fd fix: reject special-file symlink targets before sandbox setup`
- Reviewed-scope diff identity: SHA-256 `bae19ae167d7e95ac97c3ba0fb5836a51939c7a94422a1c1c08c6d22926adfc0`；stable patch-id `1d6f039ffca9446e7cd58766ab34d897bcf23eba`
- Frozen worktree check: 本报告写入前，四个 reviewed-scope 文件与 head OID 一致，`git diff --quiet HEAD -- ...` 退出 0
- Included scope: 精确 `base..head` 中的 `scripts/agent-sandbox`、`tests/test_agent_sandbox.py`、controller 文档 `docs/reviews/agent-sandbox-adjudication-20261008.md`、validation 文档 `docs/reviews/agent-sandbox-validation-20261008.md`；`load_denies` 直接调用链、正常目录/符号链接路径、原 Seatbelt deny enforcement 衔接、`skills/sub-agents/SKILL.md` 的 opt-in 固定输入和禁止静默放宽约定、本轮真实封装探针，以及指定的 v3 合成 native evidence
- Excluded scope: peer report 内容、其它个人历史/配置路径、其它项目、真实 endpoints/auth/key、tmux、动态 prompt/inbox/resume、凭据隔离、新平台或全局权限模式。`docs/reviews/mimo-flash/` 内容未读取；`git status` 对该 peer-report 目录只返回 `Operation not permitted`，没有返回文件内容
- Parallel review coverage: 无。按本轮明确指令未派发子 Agent，也未读取 peer report

## Findings

未发现实质性问题。

## Increment And Call Chain

- 唯一生产改动位于 `scripts/agent-sandbox:63`：递归队列取出的路径在任何目录列举或文件打开前再次要求 `is_file()` 或 `is_dir()`，否则以 `deny target must be a regular file or directory` 明确失败。
- 直接输入仍在 `scripts/agent-sandbox:47` 至 `:50` 做存在性和普通文件/目录检查。目录内符号链接在 `scripts/agent-sandbox:76` 至 `:80` 经 `resolve(strict=True)` 取得规范 target；target 若在既有 deny 树外则进入 `result` 和 `pending`。下一轮 `pending` 现在先做类型检查，再进入 `:65` 的目录分支或 `:72` 的文件打开分支。
- FIFO/socket/device 等特殊 target 的 `stat` 类型判断不会打开 target。FIFO target 会在 `p.open("rb")` 之前被拒绝，因此不会阻塞在无对端的 FIFO 上。直接把 FIFO 写进 deny-list 仍由 `:49` 的初始检查拒绝。
- 正常普通文件 target 仍走 `:72` 至 `:73` 的 sandbox 前可读性确认；正常目录 target 仍走 `:65` 至 `:70` 的 `listdir`/`os.walk`；既有符号链接规范化、hardlink 拒绝和结果去重路径未改变。
- 返回的 `denies` 在 `scripts/agent-sandbox:429` 至 `:433` 原样进入 srt 的 literal `denyRead`/`denyWrite`，并在 `:441` 写入固定 manifest。内层 `verify_and_exec()` 在 `:307` 至 `:318` 先查有效 Seatbelt `file-read-data` 再尝试实际读，最后才在 `:325` 启动固定 runner。
- 因特殊 target 已在 setup 阶段 fail closed，它不会进入后续 manifest 或 `verify_and_exec()` 的打开逻辑；普通 deny 集合及其 OS enforcement 生成路径没有变化。

## Agent-facing Conclusion

- `skills/sub-agents/SKILL.md:153` 至 `:160` 的约定保持成立：封装隐含 opt-in `--full-access --no-persist`，固定本次文件系统策略；只接受恰好一个非空 prepared prompt 或普通 `--prompt-file`，snapshot 后关闭 stdin；不支持 resume、native 参数透传、动态投递或追加 prompt。权限/输入缺项必须明确报错，不得静默删除 deny 或放宽权限。
- `skills/sub-agents/SKILL.md:163` 至 `:165` 的边界也未变化：保留原 runtime 写范围的保守子集，不能映射的配置明确拒绝；必需凭据/配置仍是 runtime dependency，本功能不做 credential broker 或凭据隔离。
- 新增检查只让无法可靠映射的特殊 symlink target 更早失败，不修改 runner argv、prompt owner、tool surface、write boundary 或 outer Seatbelt policy。内层 native Full Access 仍处于外层 Seatbelt 内，不能解除 caller 的 literal deny。
- 真实顶层封装探针使用固定 `--prompt 'fixed synthetic check'` 和全新 output 调用 `scripts/agent-sandbox --check ... -- codex-agent-run`，返回 `setup_status=ok`，退出 0，且未创建 output、未启动 Agent。当前复审进程的 `AGENT_SANDBOX_ACTIVE` 为 `1`，两条实际禁读探针也被同一外层边界阻止。

## Boundary And Wrapper Evidence

实际执行的两条禁读工具验证：

```text
$ cat /Users/leo/.claude/history.jsonl
cat: /Users/leo/.claude/history.jsonl: Operation not permitted
exit=1

$ rg -n 'settings.local.json' /Users/leo/.claude/projects
rg: /Users/leo/.claude/projects: Operation not permitted (os error 1)
exit=2
```

两条命令均在模型工具调用处被 OS 阻止，递归搜索未返回任何 project log 内容。这里只证明 caller 列出的具体路径在本进程内被拒读，不宣称全部用户历史或所有副本已隔离。

允许输入和产物证据：

- `cat /private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.av8ddH/canary.txt` 实际输出为 `mimo-13028c30`；本报告逐字写为 `CANARY=mimo-13028c30`。
- `/private/tmp/deny-final-review-mimo.json` 可读，共 24 个 caller 提供的 literal path，覆盖列出的 Codex sessions/log/history 数据库与状态文件、`docs/reviews/mimo-flash`、`~/.claude/projects` 和 `~/.claude/history.jsonl`。`~/.claude/file-history` 未列入；controller 记录其存在 hardlink，整目录 `~/.claude` deny 会明确拒绝，因此本报告不宣称该目录隔离。
- 精确 OID 的 repo source、controller/validation 文档、`skills/sub-agents/SKILL.md` 和指定 v3 合成 evidence 均通过 `git show`、`jq`、`shasum` 等只读工具取得。未读取其它未授权个人路径或 peer report 内容。
- 顶层 `--check` 探针输出：`{"returncode": 0, "stdout": "setup_status=ok\n", "stderr": "", "output_exists": false}`。该探针只验证 setup 调用链，不冒充 kernel proof。
- 本报告是本轮唯一持久化写产物，写入路径固定为上述 output file；写入后以 `test -s docs/reviews/mimo/code-review-20261008-2048-final.md` 核验，输出 `artifact_nonempty_exit=0`。

## Covered Files

- 生产改动: `scripts/agent-sandbox`，2 行新增，covered。
- 回归测试: `tests/test_agent_sandbox.py`，14 行新增，covered。
- Controller 文档: `docs/reviews/agent-sandbox-adjudication-20261008.md`，36 行新增/1 行删除，covered。
- Validation 文档: `docs/reviews/agent-sandbox-validation-20261008.md`，4 行新增/3 行删除，covered。
- 未改动但直接核对的调用约定: `skills/sub-agents/SKILL.md`，covered as contract evidence。
- 允许的历史上下文: `docs/reviews/mimo/code-review-20261008-2024-fix.md`，covered as prior own-route context，不计生产 diff。
- 允许的原始合成证据: `/private/tmp/code-is-cheap-agent-sandbox-evidence-v3/codex-probe.json`、`claude-probe.json`、`/private/tmp/deny-final-review-mimo.json`，covered as evidence。
- Reviewed-scope file count 4；covered 4；partially-covered 0；not-covered 0。

## Tests And Evidence

- 定向普通测试运行 3 项，全部通过：`test_symlink_canonicalization`、`test_fifo_denial_is_rejected_without_open`、`test_denied_directory_symlink_to_fifo_is_rejected_without_open`；`Ran 3 tests in 0.002s`，`OK`。新回归用 `Path.open` guard 证明 FIFO target 从未打开。
- 额外临时合成检查验证 denied directory 内的普通 file symlink、directory symlink 及其子文件仍被加入并由 `is_denied()` 覆盖，输出 `{"normal_recursive_symlinks": "ok", "deny_count": 3}`。
- 真实 `agent-sandbox --check` 使用固定 prompt、synthetic deny-list 和全新 output，退出 0 并输出 `setup_status=ok`；没有执行 `--verify`，没有向 `--verify` 注入任意 command，也没有切换 native 权限。
- 两次 shell heredoc 临时 fixture 尝试被当前写边界以 `zsh: can't create temp file for here document: operation not permitted` 阻止；等价的 `python3 -c` 临时合成执行成功。该限制不影响产品结论。
- `git diff --check` 对 reviewed-scope diff 通过。未在本轮重跑 84 项普通全套或 17 项 kernel/native 全套。
- Controller/validation 记录此前完整验证为 84 项普通测试通过、6 skip，17 项 kernel/native 通过；本报告把它们作为已决 controller 证据，不冒充本轮独立重跑。
- v3 Codex synthetic probe: SHA-256 `757e87d98272a88da8adaa566560f97dc66345dc6a06983111bb35b24956e4f0`，195,585 bytes，6 requests，exit 0，1 个 `turn.completed`，0 server errors。
- v3 Claude synthetic probe: SHA-256 `4894b10e458f700db97e0e503aae734a819c28a090872e30b304e180e2a42572`，130,215 bytes，5 requests，exit 0，result `success`/`is_error=false`/`num_turns=5`，0 server errors。
- 两个 probe 的请求/trace 均无 `FORBIDDEN_*` 合成内容 marker。其模型 metadata 为 synthetic test route（Codex `gpt-5.4`、Claude `test-model`），不用于识别本轮 reviewer model；本轮实际 runtime/provider/model 以首行为准。

## Adversarial And Architecture Pass

- Failure path: FIFO target 不再可能进入 `p.open()` 阻塞；不支持的 special target 在 runner、output、srt policy 创建前明确退出 1。
- Normal path: 普通文件、普通目录、递归发现的普通 file/directory symlink 仍进入原有可读性验证和 deny expansion；新增判断只排除非普通 target。
- Enforcement path: `denies` 到 literal `denyRead`/`denyWrite`、manifest、`sandbox_check`、实际 read、固定 runner exec 的数据链未变化。当前两条真实禁读命令继续被 outer OS 阻止。
- Ownership: special target 的可验证性由 `load_denies` 在 setup owner 处裁决并 fail closed；测试不通过 mock 重新解释 OS deny 语义。
- Overcoupling/semantic drift: 未扩大 runner 或 native runtime contract，也未用 fallback、忽略 special target 或放宽 deny 来补齐输入。未发现新增耦合或语义漂移。

## Open Questions

- 无。

## Residual Risk

- 回归以 FIFO 为代表覆盖“不打开 special target”；socket、device 由同一 `is_file()/is_dir()` predicate 排除，但没有逐类型参数化测试。broken symlink 仍会在 `resolve(strict=True)` 处明确失败。
- 本轮没有独立重跑 kernel/native 全套，因为该 suite 要求在当前 outer sandbox 之外以 opt-in 方式运行，而本轮禁止关闭/绕过封装或切换 native 权限。原 OS deny enforcement 的结论结合既有 17-test controller 证据、未改动的 policy 数据链和本轮两条真实禁读输出。
- `load_denies` 与后续 sandbox setup 之间仍存在 path-based TOCTOU：未隔离进程并发 rename、mount、copy 或替换 target 超出既有边界；已有 hardlink 已拒绝，但本增量不解决并发替换。
- 原有限制继续成立：caller 必须列出已知 forbidden copy，未列副本不做语义推断；不能映射的 custom/managed policy 明确拒绝；必需 runtime credentials/config 仍可读，不提供 credential isolation。
