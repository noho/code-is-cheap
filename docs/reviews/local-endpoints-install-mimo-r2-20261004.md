RUNTIME/PROVIDER/MODEL: codex/mimo/mimo-v2.6-pro
CANARY=mimo-f5267864

# Code Review

## Scope

- Mode: current changes (`$deepreview --base main`), incremental closure review of final fixes
- Branch: `feat/local-endpoints-installer`
- Base: `main` at `842eca3642e5d51c6d849870ea42d1deb9569aa3`
- Frozen HEAD: `842eca3642e5d51c6d849870ea42d1deb9569aa3`
- Review timestamp: `20261004-190612` (Asia/Shanghai, from local system clock)
- Output file: `docs/reviews/local-endpoints-install-mimo-r2-20261004.md`
- Included scope: the 17 paths in `/private/tmp/code-is-cheap-endpoint-review/r2/manifest.json`, the final fix delta in `/private/tmp/code-is-cheap-endpoint-review/r2/fix-delta.patch`, and the necessary entry points/call chains. The tracked diff was `/private/tmp/code-is-cheap-endpoint-review/r2/diff.patch`.
- Excluded scope: no other r2 review report was read. Unchanged skill-usage prose, unrelated repository files, live installation/synchronization, network/API/model probes, process/session/auth inspection, and external mutations were excluded as instructed.
- Parallel review coverage: 无. This route did not dispatch sub-agents. The second full-review route was explicitly Qwen, overriding the repository default `mimo-flash`.
- Mutation boundary: no implementation, test, source, frozen input, manifest, or existing review artifact was changed. No commit, push, PR, merge, or gate advancement was performed. The only repository write is this artifact.

### Frozen identity and hash evidence

| Input | SHA-256 | Verification |
| --- | --- | --- |
| `r2/manifest.json` | `35c0d9f0f2188eeac0cdd714feec65b1a5f9ceae9e8f8e9fefd187ea6fb499ec` | recorded before and after review |
| `r2/diff.patch` | `22f96ebf902d62ab6b0c69d90865f7462030a46e4efead27a92b675a2653f44c` | recorded before and after review |
| `r2/fix-delta.patch` | `878c602907b0518da03c51645305baf0cb39612671add02f12f1e1548eaeec70` | recorded before and after review |

All 17 manifest path hashes matched the worktree before source/test review and again after testing. `git rev-parse main` and `git rev-parse HEAD` both returned the frozen OID. The branch has no commit beyond `main`; the reviewed state is the frozen uncommitted worktree state.

## Findings

### 1-未修复-[中]-shim 启动仍未把所有 malformed route config 收敛为单行诊断

- **入口/函数**: `codex-auto-review-shim` -> `main()` -> `load_routes()`
- **文件(行号)**: `codex-agent/bin/codex-auto-review-shim:219`; `codex-agent/bin/codex-auto-review-shim:221`; `codex-agent/bin/codex-auto-review-shim:465`
- **输入场景**: `SHIM_ROUTES` 指向一个 JSON 结构合法但 route 行不是对象的文件，例如 `{"routes":[42]}`
- **实际分支**: `for i, r in enumerate(...)` 得到整数 `42`，随后 `key not in r` 在检查 `port`/`to` 前抛出 `TypeError`
- **预期行为**: 启动配置校验应 fail closed，并输出单行可操作诊断；这与本轮明确要求的“startup errors have single-line diagnostics”一致
- **实际行为**: `main()` 只捕获 `(ValueError, OSError)`，`TypeError` 原样逃逸。实跑退出码为 1，stderr 为完整 Python traceback
- **直接证据**: `load_routes()` 的首个 route-key 检查在 `codex-agent/bin/codex-auto-review-shim:221` 直接对任意 JSON 类型执行 membership；`main()` 的收口在 `:465-468` 不包含 `TypeError`。复现输入 `{"routes":[42]}` 产生 `TypeError: argument of type 'int' is not iterable`
- **影响**: malformed route config 无法诊断性失败。launchd `KeepAlive` 场景可能形成带 traceback 的启动循环；这使原 Qwen Finding 3 只能算部分关闭
- **建议改法和验证点**:
  - 在读取 route 字段前显式要求 `isinstance(r, dict)`，并抛出带 `routes[i]` 位置的 `SystemExit`
  - 将结构校验后的意外类型错误也收敛为单行 `SystemExit`，不要依赖宽泛 traceback
  - 回归测试覆盖 route 行为整数、字符串、`null` 时退出码非 0、stderr 单行且不含 `Traceback`
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 中

### 2-未修复-[低]-endpoint helper 子进程仍继承当前 provider key，凭据隔离只完成了部分 scrub

- **入口/函数**: `_claude_agent_launch()` -> `_agent_tools_prepare_credentials()` -> `_claude_agent_base_url()`
- **文件(行号)**: `scripts/agent-tools.zsh:34`; `scripts/agent-tools.zsh:39`; `scripts/agent-tools.zsh:158`; `scripts/agent-tools.zsh:159`
- **输入场景**: provider key 来自环境或用户 key 文件，然后启动任一 Claude provider；URL helper 必须作为子进程读取本地 endpoint 配置
- **实际分支**: `_agent_tools_prepare_credentials` 先 scrub 其它敏感变量，但随后在 `:39` 导出选中的 provider key；`:159` 才启动 `python3 agent-endpoint.py`
- **预期行为**: endpoint 解析子进程执行前应完成凭据隔离，URL helper 不需要 provider key；key 只应在最终 `claude` 调用处以 `ANTHROPIC_AUTH_TOKEN` 提供
- **实际行为**: 其它继承凭据确实被移除，但选中的 `DEEPSEEK_API_KEY` 仍对 endpoint helper 子进程可见。隔离探针输出 `helper_env_selected=fake-key helper_env_other=unset`
- **直接证据**: `scripts/agent-tools.zsh:34-40` 在 helper 调用前把 `selected_value` 写成 exported parameter；`scripts/agent-tools.zsh:158-159` 的顺序证明 helper 继承该导出值。最终 Claude 调用在 `:222-224` 只需要 `ANTHROPIC_AUTH_TOKEN`，因此 helper 阶段的 provider-key export 不是必要契约
- **影响**: 范围较小但真实的凭据暴露面扩大到 Python 子进程及其启动/import 环境。它不恢复原 Qwen Finding 1 的“坏配置仍启动 Claude”缺陷，但没有完全满足本轮明确的 endpoint-subprocess credential scrub 要求
- **建议改法和验证点**:
  - 将 selected key 保存为 shell-local 值而不 export；在 URL helper 完成后再执行最终 Claude 环境构造
  - 增加 stub helper 环境断言：所有 `*_KEY`/`*_TOKEN`/secret 变量均不存在，且 stub `claude` 只收到 `ANTHROPIC_AUTH_TOKEN`
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 低

### 3-未修复-[低]-README/install 的依赖与 source ownership 清单仍有可验证的不一致

- **入口/函数**: 新用户执行 documented install；维护者按 Maintenance 清单判断仓库真源
- **文件(行号)**: `install.sh:12`; `install.sh:19`; `README.md:94`; `README.zh.md:90`; `README.md:591`; `README.md:611`; `README.zh.md:570`; `README.zh.md:591`
- **输入场景**: 用户严格按 README 准备安装依赖，或维护者只编辑两份 README 的“source files”权威清单所列文件
- **实际分支**: installer 实际强制检查 `curl` 与 `zsh`，README 安装前置和 `--help` 未完整列出；Maintenance 清单没有新增的 `tests/test_install_endpoints.py`
- **预期行为**: README/install 的实际步骤、依赖和 ownership 应与脚本行为一致；本改动新增的测试也属于可编辑仓库真源
- **实际行为**: README 的下载命令使用 `curl`，但安装前置句漏列 `curl`；`install.sh --help` 漏列 `zsh`、`curl`；Repository Layout 已列 `tests/test_install_endpoints.py`，Maintenance 清单却遗漏它
- **直接证据**: `install.sh:19` 的依赖数组包含 `zsh curl`，而 `install.sh:12` 与 `README.md:94`/`README.zh.md:90` 的清单不完整；两份 Maintenance 清单列出其它 tests，但没有 `tests/test_install_endpoints.py`
- **影响**: 新用户可能按不完整清单准备环境；维护者可能漏改本特性的核心回归测试。属于文档/ownership drift，不影响当前执行正确性
- **建议改法和验证点**:
  - `install.sh --help` 和两份 README 安装前置补齐 `zsh`、`curl`
  - 两份 Maintenance source list 补 `tests/test_install_endpoints.py`
  - 用文本检索同时确认 Repository Layout 与 Maintenance 两处出现该测试路径
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 低

## 原 Findings Closure

本轮只把原 review artifacts 用于识别历史 findings 和检查关闭情况，没有把它们当作当前正确性证明。

| Original finding | Closure status | Independent evidence |
| --- | --- | --- |
| MIMO-1 custom `AGENT_RUN_BIN_DIR` helper path mismatch | 已关闭 | `_claude_agent_base_url` now resolves `agent-endpoint.py` through `PATH`; focused test uses a custom directory containing spaces |
| MIMO-2 sensitive-value test false positive on `/private/tmp` | 已关闭 | assertions use `SENSITIVE_SENTINEL_7e61`; tests pass with `TMPDIR=/private/tmp` |
| MIMO-3 README fixed local URL wording | 已关闭 | both READMEs distinguish `local.claude` health URL and `local.codex` direct URL and identify 8080 as default |
| QWEN-1 bad URL/helper continued into Claude | 已关闭 for Claude non-invocation | assignment propagation is separated from `local`; stub Claude negative tests prove no invocation on missing helper/malformed config. Endpoint credential exposure remains in Finding 2 |
| QWEN-2 runtime 503 diagnostics/URL secrecy | 已关闭 | runtime path logs `endpoint error: ...` and returns 503; managed `--routes` prints `endpoint:<id>`, not resolved upstream URL |
| QWEN-3 startup exception leakage | 部分关闭 | missing helper and endpoint errors are normalized; malformed non-object route rows still reproduce Finding 1 |
| QWEN-4 route prefix/provider registry pairing | 已关闭 | `tests.test_provider_registry` asserts `request_prefix == urlsplit(base_url).path` |
| QWEN-5 deprecated `load_module()` | 已关闭 | test uses `spec_from_loader` plus `exec_module`; no deprecation warning appeared |
| QWEN-6 local URL override parser/test/error | 已关闭 | comment-bearing section, custom path, byte-preserving idempotence, and failure preservation are tested |
| QWEN-7 restore flow contradicted missing endpoint file | 已关闭 | direct sync with missing local endpoint file succeeds without recreating it; README states defaults are used |
| QWEN-8 README resource/prerequisite/ownership drift | 部分关闭 | local/resource/restore wording and new source files are mostly corrected; residual prerequisite and test ownership drift is Finding 3 |
| QWEN-9 custom bin PATH mismatch | 已关闭 | launcher uses `command -v`; custom-bin test passes |

## Open Questions

- 无。Finding 2 is assessed against the explicit requirement that credentials be scrubbed before the endpoint subprocess; if “selected provider key allowed, inherited unrelated credentials scrubbed” were the intended narrower contract, that finding could be downgraded to a contract clarification rather than an implementation defect.

## Residual Risk

- No live installation, synchronization against the real user home, launchd activation, network request, API call, or model/protocol probe was performed. Existing tests mock `git`, `uv`, `launchctl`, and service dependencies and use the local Codex CLI only to read its bundled model catalog.
- The controller reported 54 tests under isolated `TMPDIR`; this route independently reran the two requested modules rather than claiming to reproduce the full 54-test controller run.
- Existing endpoint/key files with unusual ownership, permissions, symlinks, or hostile content remain outside the defined behavior. The installer preserves existing files but does not normalize them.
- The shim's real streaming/HTTP forwarding and production launchd log permissions were not exercised. Static tracing shows runtime 503 logging avoids the resolved URL, but live service behavior remains unverified.
- `codex debug models` emitted a test-only warning about PATH aliases under `/private/tmp`; the isolated lifecycle test still passed and no live installation was performed.

## Tests and Validation

- `HOME=/private/tmp/code-is-cheap-endpoint-review/r2-mimo-review-home TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_install_endpoints tests.test_provider_registry`
  - Result: `17 tests`, all passed in `9.290s`
  - Coverage included malformed/missing local config fail-closed behavior, Claude stub negative invocation, custom PATH helper resolution, hot Codex URL updates with custom path, default fallback without writes, private validator venv reuse, safe shim diagnostics, downloaded bootstrap/reinstall, missing-file direct sync, provider/route/path pairing, local URL comment handling/idempotence/failure preservation, registry ownership conflicts, symlink/damaged-block rejection, and app-home composition.
- Focused rerun of five closure-critical tests passed in `1.023s`.
- `bash -n` passed for `install.sh`, `scripts/sync-agent-tools.sh`, `scripts/sync-codex-agent.sh`, and `scripts/validate-skills.sh`; `zsh -n` passed for `scripts/agent-tools.zsh`; `jq empty` passed for both JSON resources.
- Adversarial startup probe `{"routes":[42]}` reproduced Finding 1 with a nonzero exit and traceback. A separate synthetic credential probe reproduced Finding 2. These exploratory nonzero results are review evidence, not whole-task test failures.
- Manifest path hashes were verified again after testing and reviewing: 17 of 17 matched.

## Verdict

不建议按当前状态直接关闭 review loop。核心 hot URL、fallback, installer/reinstall, custom PATH, local override, route pairing, validator reuse and most original failure-path fixes are closed, but the startup diagnostic contract, endpoint-subprocess credential isolation, and documented dependency/ownership contract each retain a concrete defect.
