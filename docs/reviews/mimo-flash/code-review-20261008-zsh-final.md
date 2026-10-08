RUNTIME/PROVIDER/MODEL: codex/mimo-flash/mimo-v2.6-flash
CANARY=mimo-flash-04d7cd5c

**Agent-facing conclusion:** 未发现实质性问题。该 1 行生产变更把 zsh heredoc 临时文件前缀限定在本调用已经允许写入的 `state/tmp` 下；受限 diff、静态生效链、zsh 消费探针、直接测试增量和 candidate receipt 相互一致，未扩大 filesystem allow/deny 权限，也未影响不经过该封装的默认调用。

# Code Review

## Scope

- Mode: current changes（用户指定的独立、小范围补充复审）
- Branch: `feat/agent-deny-list-sandbox`
- Base: `b27a9fd9dd985acadfc41b879088cca1fbcf061b`
- Frozen head: `e995c196930218ada476d9b4e5de0b8de9628dda`
- Repository: `/Users/leo/workspace/code-is-cheap`
- Runtime / provider / model / label: `codex` / `mimo-flash` / `mimo-v2.6-flash` / `deny-zsh-review-mimo-flash-v4-20261008`
- Output file: `docs/reviews/mimo-flash/code-review-20261008-zsh-final.md`
- Included scope: 仅 `scripts/agent-sandbox` 的 1 行生产变更及 `tests/test_agent_sandbox.py` 的 5 行直接测试增量；围绕 `TMPPREFIX` 的环境传递、zsh heredoc 最终消费、既有 `state/tmp` 写权限链、fake runner 实际命令与 workspace-write/read-only 断言。
- Excluded scope: 其它代码、其它测试、既有 denylist/Full Access 功能、旧 review 报告、Git 历史中的报告副本、业务项目、主目录历史/config/key、网络与真实凭据、全套或嵌套 kernel 测试。
- Parallel review coverage: 无；按本轮显式授权未派发 subagent。
- Diff hygiene: `git diff` 显式限定为 `scripts/agent-sandbox tests/test_agent_sandbox.py`；结果为生产文件 `1 insertion, 0 deletions`，测试文件 `5 insertions, 0 deletions`。

## Findings

未发现实质性问题

## Review Evidence

1. **zsh 最终消费确认。** 在本机 `zsh 5.9` 上执行只读小探针：将 `TMPPREFIX` 指向不存在的父目录时，`zsh -fc` heredoc 以退出码 1 失败，错误为 `zsh:1: can't create temp file for here document: no such file or directory`；将它指向可创建的 `<tmp>/state/tmp/zsh` 前缀时，heredoc 以 0 退出并精确输出 `ALLOW_HEREDOC_MARKER\n`。成功/失败随该变量的可写性翻转，证明 zsh 实际消费它，而非仅继承变量。
2. **仅复用既有允许写入的 state。** `scripts/agent-sandbox:392-393` 创建唯一 `state` 和 `state/tmp`；`:411` 将 `str(state)` 放入 `writes`；`:428-437` 的 filesystem settings 由 `writes`、deny 列表和固定文件生成；新增 `scripts/agent-sandbox:444` 仅为 `env["TMPPREFIX"] = str(state / "tmp" / "zsh")`。该值是既有允许根的后代，且受限 diff 未改 `writes`、`settings`、deny 列表或输出文件规则，因此没有扩大写权限。
3. **测试执行真实命令。** `tests/test_agent_sandbox.py:172-173` 的 fake runner 启动 `/bin/zsh -lc`，命令体包含真实 heredoc，并记录返回码、stdout、stderr；workspace-write 在 `:203-204` 同时断言返回码 0 和 marker 精确值。read-only 在 `:216` 断言返回码 0，同时保留同一 fake runner 的 stdout 记录。
4. **两种模式的边界证据。** 可读 candidate receipt `/private/tmp/code-is-cheap-agent-sandbox-evidence-v3/zsh-candidate-check.json`（SHA-256 `22f659bb0946e3ae9a2c9d5ed32a98e1dd15b72dca704cfa02d28055c5395a54`）显示：workspace-write 与 read-only 的 `heredoc_code` 均为 0，`heredoc_stdout` 均为 `ALLOW_HEREDOC_MARKER\n`；两模式 `outside_write`、`protected_write` 均为 `PermissionError`，`sink_write` 均为 `allowed`；workspace-write 的 `cwd_write` 为 `allowed`，read-only 为 `PermissionError`。这与新增断言和原权限语义一致。
5. **不使用封装时的默认行为。** `scripts/agent-sandbox:394` 先复制父环境到局部 `env`，新增赋值位于 `:444`，只通过 `:458` 的定向 `os.execvpe(..., env)` 传入该次 envelope；`--check` 在 `:381-389` 提前返回，不会触达新增行。未调用该封装的进程不会执行该赋值，父进程环境也不会被就地修改，因此直接 runner 的默认行为不受影响。
6. **测试与静态检查。** `python3 -m unittest discover -s tests -p test_agent_sandbox.py -k SetupTests -v` 运行 9 项，结果 `OK`；`git diff --check` 限定相同两个 path 后退出码 0。按授权未在外层 Seatbelt 内重跑 kernel/setup 全套，也未执行嵌套 kernel 测试。

## Open Questions

- 无

## Residual Risk

- candidate receipt 是调用方提供的独立证据，本轮仅校验其结构、关键字段与哈希，未在当前外层 Seatbelt 内重跑 kernel suite。
- 仓库内 read-only 测试直接断言 heredoc 返回码而非 stdout；candidate receipt 已补足该模式的精确 stdout 证据。该限制不影响本次结论，但后续若替换 receipt，应同时保留返回码和 marker 断言。
- 本轮按授权不覆盖 zsh 以外的 shell、未封装调用的其它临时文件行为、CI、旧功能或非目标权限面。
