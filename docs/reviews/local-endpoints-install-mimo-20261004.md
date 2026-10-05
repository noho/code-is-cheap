RUNTIME/PROVIDER/MODEL: codex/mimo/mimo-v2.6-pro
CANARY=mimo-ef76ef3d

# Code Review

## Scope

- Mode: current changes (`$deepreview --base main`)
- Branch or PR: `feat/local-endpoints-installer`
- Base: `main` at `842eca3642e5d51c6d849870ea42d1deb9569aa3`
- Frozen HEAD: `842eca3642e5d51c6d849870ea42d1deb9569aa3`
- Review timestamp: `20261004-183122` (Asia/Shanghai, from local system clock)
- Output file: `docs/reviews/local-endpoints-install-mimo-20261004.md`
- Included scope: all 16 files in `/private/tmp/code-is-cheap-endpoint-review/manifest.json`; covered 16, partially covered 0, not covered 0. The 549-line tracked diff in `/private/tmp/code-is-cheap-endpoint-review/diff.patch` was read in full.
- Input identity: manifest SHA-256 `bb5a8cfb693ef5d452cde923d48c2e69a7534e07728fa7336d115b9271646f1c`; diff SHA-256 `e06d59ebe44d0644636033eb61bf3debf819dfe8c54bd802fca64c711b9f620d`. All 16 path hashes matched before review and again after testing. A fresh `git diff --no-ext-diff` was byte-identical to the frozen diff (`cmp_status=0`, same SHA-256).
- Excluded scope: other review reports were ignored. Related untouched entry points were read only to trace behavior: `scripts/claude-agent-run`, `scripts/codex-agent-run`, `scripts/sync-skills.sh`, `scripts/compose-codex-app-config.py`, `scripts/patch-codex-model-catalog.py`, `codex-agent/bin/codex-auto-review-shim-service`, all `codex-agent/profiles/*/config.toml`, and existing provider/shim-service tests.
- Parallel review coverage: 无. Explicit task instructions prohibited sub-agent dispatch. The alternate second review route was designated as Qwen, but it was not dispatched in this independent route.
- Mutation boundary: no implementation, test, README, manifest, or frozen diff was changed. No live install/sync, network/model probe, commit, push, PR, merge, or gate advancement was performed.

## Findings

### 1-未修复-[中]-Claude endpoint helper 的安装路径与解析路径不一致
- **入口/函数**: `_claude_agent_base_url`，由 `ds-flash_claude` / `claude-agent-run` 启动链调用
- **文件(行号)**: `scripts/agent-tools.zsh:73`; `scripts/sync-agent-tools.sh:7`; `scripts/sync-agent-tools.sh:16`
- **输入场景**: 使用 `AGENT_RUN_BIN_DIR=/custom/bin ./scripts/sync-agent-tools.sh` 安装工具，然后 source 同一 launcher 并运行 `ds-flash_claude`
- **实际分支**: sync 把 `agent-endpoint.py` 安装到 `$AGENT_RUN_BIN_DIR`；Claude launcher 仍固定执行 `$HOME/.local/bin/agent-endpoint.py`
- **预期行为**: launcher 应读取它实际安装的 endpoint helper，或从同一受控 PATH 解析；自定义安装目标不应半可用
- **实际行为**: 默认布局可用，但自定义 `AGENT_RUN_BIN_DIR` 下 sync 成功、Claude URL 解析失败；Codex shim 则按 `$target_root/bin` 正确部署 helper
- **直接证据**: `sync-agent-tools.sh:7` 允许覆盖 bin 目录，`:16` 将 helper 安装到该目录；`agent-tools.zsh:74` 忽略该变量并硬编码 `$HOME/.local/bin/agent-endpoint.py`。现有测试只创建默认 `$HOME/.local/bin`，未覆盖 override
- **影响**: 非默认安装布局下 Claude cloud URL 无法从用户文件读取，launcher 在请求前失败；sync 的成功输出与实际可用状态不一致
- **建议改法和验证点**: 让 launcher 使用 `AGENT_RUN_BIN_DIR` 的规范化值或 `command -v agent-endpoint.py`，并增加自定义 bin 目录下 Claude URL 切换测试
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 中

### 2-未修复-[低]-敏感信息测试把文件路径中的 `private` 误判为泄密
- **入口/函数**: `EndpointTests.test_invalid_urls_never_echo_sensitive_values`
- **文件(行号)**: `tests/test_install_endpoints.py:43`; `tests/test_install_endpoints.py:51`; `scripts/agent-endpoint.py:28`
- **输入场景**: 在 `TMPDIR=/private/tmp/...` 或任何路径包含字符串 `private` 的隔离环境中运行该测试
- **实际分支**: invalid URL 被 `load_endpoints` fail closed，异常消息只包含 endpoints 文件路径，不包含 URL
- **预期行为**: 测试应验证指定 secret sentinel 未被回显，不应把文件系统路径中的普通单词当作 secret
- **实际行为**: 本次首轮运行 4 个 subtest 均因错误路径含 `/private/tmp/...` 而失败；改用不含该字符串的 `/tmp/...` 后通过
- **直接证据**: 测试在 `:51` 断言 stderr 不含通用字符串 `private`；实现按 `agent-endpoint.py:28-30` 输出 `Cannot load endpoints from <path>`，因此测试夹具路径本身触发断言
- **影响**: CI/本机 tempdir 布局会造成假失败，削弱该隐私回归测试的可信度，并可能掩盖真正的 URL 泄露
- **建议改法和验证点**: 使用唯一值如 `SENSITIVE_SENTINEL` 写入 URL，并断言该 sentinel 不在 stderr；如需避免路径展示，可另行测试错误是否只暴露允许的配置路径
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 低

### 3-未修复-[低]-两份 README 仍把 local endpoint 写成固定地址
- **入口/函数**: Agent 用户按 README 配置并检查 `local_claude` / `local_codex`
- **文件(行号)**: `README.md:140`; `README.zh.md:135`; contract source at `README.md:123`, `README.zh.md:119`, `scripts/agent-tools.zsh:109`
- **输入场景**: 用户把 `~/.config/agent-tools/endpoints.json` 的 `local/claude` 或 `local/codex` 改离默认 `127.0.0.1:8080`
- **实际分支**: `_local_agent_require_service` 读取 `local/claude` 并探测 `${base_url%/}/health`；sync 把 `local/codex` 写入 managed registry
- **预期行为**: prerequisites 应指向用户拥有且可修改的 endpoints 文件，并区分 Claude health URL 与 Codex direct URL
- **实际行为**: 新增的 URL contract 明确支持用户配置，但两份 prerequisites 仍声明 local launcher 固定需要 `http://127.0.0.1:8080`
- **直接证据**: `README.md:123` / `README.zh.md:119` 描述 `local.codex` 可配置，`agent-tools.zsh:109-117` 动态读取 `local/claude`；`README.md:140` / `README.zh.md:135` 仍写死默认 URL
- **影响**: Agent-facing 文档会让用户误判 local endpoint 是否已生效，并在非默认端口下按错误地址排查健康状态
- **建议改法和验证点**: 两份 README 都改为引用 `~/.config/agent-tools/endpoints.json` 的 `local/claude` 与 `local/codex`，说明后者需重跑 `sync-codex-agent.sh`
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 低

## Open Questions

- `AGENT_RUN_BIN_DIR` 若仅是内部测试参数而非受支持安装参数，Finding 1 可降为低；但当前 sync 接受该参数且安装成功，却没有把同一路径 contract 传给 launcher。
- 对已经存在但权限不是 `0600` 的 endpoints/key 文件，产品预期是“严格保留原状”还是“重安装时收紧权限并保留内容”？当前实现和测试只保证新建文件为 `0600`。
- downloaded bootstrap 与随后 `git clone/pull` 的 `main` 是两次可变读取，未校验二者属于同一 commit。若要求严格可复现安装，需要 pin 到 commit 或校验 checkout 内 `install.sh` 与 bootstrap 的一致性。

## Residual Risk

- `tests/test_install_endpoints.py:58` 用共享 `tempfile.gettempdir()` 作为 `CODEX_HOME` 读取 catalog，而生产 catalog generator 使用真正的新建空 HOME。通常可用，但不如生产路径严格。
- install lifecycle 测试 mock 了 `git`、`uv`、`launchctl` 等依赖；它证明脚本编排和用户文件保留，不证明真实网络 clone/pull、PyYAML wheel 安装或 launchd 启动。
- custom `local/codex` 的 `--local-base-url` 由本次临时动态检查证明可写入正确 TOML，但仓库内没有永久回归测试。
- HTTP Handler 级转发、真实 Responses/Anthropic protocol compatibility、OpenRouter/OpenCode model slug 和 live launchd service 均未探测，符合本轮禁止 live install/network/model probe 的边界。
- 现有 endpoints 文件为 symlink、错误 owner 或宽松权限时的策略未定义；`O_EXCL` 只保证 installer 不覆盖已存在文件。

## Test Evidence

- Relevant isolated tests: `python3 -m unittest -v tests.test_install_endpoints tests.test_codex_model_defaults tests.test_provider_registry tests.test_shim_service` with isolated `HOME`/`TMPDIR` and `PYTHONDONTWRITEBYTECODE=1`: 25 tests passed in 10.794s.
- Initial same command under `/private/tmp/...` produced four recovered test assertion failures exactly explained by Finding 2; rerun under `/tmp/...` passed. This was a test-path collision, not an implementation or task failure.
- Static validation: `bash -n` passed for 5 shell entry points, `zsh -n` passed for 4 zsh entry points, and Python AST parsing passed for 10 implementation/test files.
- Lifecycle coverage exercised: downloaded `install.sh` bootstrap versus copied checkout, first install plus reinstall, custom ds-flash Codex/Claude URL preservation, key file preservation, `.zshrc` preservation, unrelated Codex config preservation, fresh repo-local skill validation invocation, CLI runner/card/skill deployment, route prefix forwarding, invalid prefix fail-closed, malformed endpoints fail-closed, provider registry idempotency/ownership conflicts, App config composition, and launchd service rollback.
- Local direct endpoint check: `sync-codex-providers.py --local-base-url http://127.0.0.1:9999/v1` wrote exactly `http://127.0.0.1:9999/v1` into `[model_providers.local_llama].base_url` in a temporary config.
- Controller-reported full suite: 49 tests with isolated HOME and dependency mocks. This review independently reran the 25 tests most relevant to installer, endpoint ownership/hot reload, provider registry, App composition, business sync failure containment, and service rollback.
