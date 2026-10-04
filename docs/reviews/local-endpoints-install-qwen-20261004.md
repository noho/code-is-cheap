# Code Review

RUNTIME/PROVIDER/MODEL: codex/qwen/qwen3.8-max (controller-configured identity). Actual runtime model per my own
system context is Codex (GPT-5 family); I cannot self-verify the wire model from inside this session, and per
instruction no wire-identity probing was performed. The configured label above is reported as given, not as a
self-observed fact.

CANARY=qwen-616b403b

## Scope

- Mode: current changes (`$deepreview --base main`)
- Branch or PR: `feat/local-endpoints-installer` (no PR opened; no commit/push performed)
- Base: `main`
- Frozen HEAD: `842eca3642e5d51c6d849870ea42d1deb9569aa3`
- Note: `git rev-parse main` == `git rev-parse HEAD` == `842eca3642e5d51c6d849870ea42d1deb9569aa3`. The branch has
  no commits beyond `main`; the entire reviewed change is uncommitted worktree state (11 modified tracked files,
  5 untracked new files).
- Review date/time: 2026-10-04 18:43 CST (from system clock)
- Output file: `docs/reviews/local-endpoints-install-qwen-20261004.md`
- Output-path deviation: `skills/deepreview/SKILL.md` prescribes `docs/reviews/code-review-<ts>.md`. The task
  explicitly fixes the output path to `docs/reviews/local-endpoints-install-qwen-20261004.md`; explicit user
  instruction takes precedence (also per `AGENTS.md`).
- Second-review-route deviation: `AGENTS.md` defaults the second reviewer to `mimo-flash`. This task explicitly
  routes it to Qwen. Recorded, not treated as a violation.
- No sub-agents dispatched (per task instruction; this overrides the `Large Scope Parallel Review` default).

### Input identity verification (before review and before completion)

| Input | Expected | Observed | Result |
| --- | --- | --- | --- |
| `HEAD` | `842eca3642e5d51c6d849870ea42d1deb9569aa3` | same | match |
| branch | `feat/local-endpoints-installer` | same | match |
| `manifest.json` sha256 | n/a (self) | `bb5a8cfb693ef5d452cde923d48c2e69a7534e07728fa7336d115b9271646f1c` | recorded |
| `diff.patch` sha256 | n/a (self) | `e06d59ebe44d0644636033eb61bf3debf819dfe8c54bd802fca64c711b9f620d` | recorded |
| `diff.patch` reproducibility | regenerable | `git diff main > /tmp/mydiff.patch` yields the identical sha256 `e06d59eb...` | match |
| 16 manifest path->sha256 entries | all match worktree | all 16 match, 0 missing, 0 mismatch | match |

Re-verified immediately before writing this artifact: `HEAD` still `842eca36...`, `diff.patch` still `e06d59eb...`,
all 16 manifest hashes still match. The reviewed state did not move during the review.

### Included scope (all 16 manifest files read in full)

Modified tracked: `README.md`, `README.zh.md`, `codex-agent/bin/codex-auto-review-shim`,
`codex-agent/model-providers.toml`, `codex-agent/shim-routes.json`, `scripts/agent-tools.zsh`,
`scripts/sync-agent-tools.sh`, `scripts/sync-codex-agent.sh`, `scripts/sync-codex-providers.py`,
`scripts/validate-skills.sh`, `tests/test_codex_model_defaults.py`.

Untracked new: `config/endpoints.example.json`, `install.sh`, `scripts/agent-endpoint.py`,
`scripts/validate-skill.py`, `tests/test_install_endpoints.py`.

Read for entry-point tracing (not in diff, unmodified): `AGENTS.md`, `codex-agent/bin/codex-auto-review-shim-service`,
`scripts/sync-skills.sh`, `scripts/compose-codex-app-config.py` (grep only), `scripts/claude-agent-run` (grep only),
`tests/test_provider_registry.py`, `tests/test_shim_service.py`, `.gitignore`.

### Excluded scope

- Other reviewers' artifacts under `docs/reviews/` (explicitly not review inputs).
- No process inspection, session-history inspection, credential inspection, or runtime authentication probing.
- No live install, no live sync against the real `$HOME`, no network or model probing.
- `skills/*/SKILL.md` bodies: only validated through the new validator, not line-reviewed (outside the diff).

### Coverage statement

Covered: all 16 manifest files. Partially covered: `README.md` / `README.zh.md` were read for every hunk in the diff
plus the Install, Prepare Agent Environment, Requirements, Repository Layout, Maintenance, and restore-to-another-Mac
sections; the remaining ~450 lines of unrelated skill-usage prose in each were skimmed, not line-reviewed.
Not covered: `skills/*/SKILL.md` bodies, `scripts/claude-agent-run` and `scripts/codex-agent-run` bodies (only
grep-verified that neither resolves base URLs), `codex-agent/profiles/*/config.toml` bodies.

---

## Findings

### 1-未修复-高-Claude 启动器在 URL 解析失败时静默使用空 `ANTHROPIC_BASE_URL` 并携带真实 key 启动，`|| return 1` 是死代码

- **入口/函数**: `<agent-id>_claude` -> `scripts/agent-tools.zsh:_claude_agent_launch()`（`ds-flash_claude` 等 10 个入口，`scripts/agent-tools.zsh:220-229`）
- **文件(行号)**:
  - `scripts/agent-tools.zsh:73-75`（新的 `_claude_agent_base_url`）
  - `scripts/agent-tools.zsh:142`（失效的守卫）
  - `scripts/agent-tools.zsh:193`（`ANTHROPIC_BASE_URL: $base_url`）
  - `scripts/agent-tools.zsh:216-217`（带 `ANTHROPIC_AUTH_TOKEN` 执行 `claude`）
- **输入场景**: `~/.config/agent-tools/endpoints.json` 缺失、JSON 语法错误、URL 校验失败、缺少对应 provider/runtime 条目，或 `~/.local/bin/agent-endpoint.py` 缺失、或 `python3` 不在 PATH。任意一种即可，且都是本次改动新引入的失败面。
- **实际分支**: `scripts/agent-tools.zsh:74` 的 `python3 ... --provider "$1" --runtime claude` 以非 0 退出，只向 stderr 打印原因，stdout 为空；`scripts/agent-tools.zsh:142` 的 `local base_url="$(...)" || return 1` **不触发** `return 1`，因为 zsh 中 `local`/`typeset` 声明加命令替换的退出状态是 `local` 自身的 0，不传播命令替换的失败。函数继续走到 `scripts/agent-tools.zsh:185-213` 构造 settings JSON，再到 `scripts/agent-tools.zsh:216-217` 启动 `claude`。
- **预期行为**: 按本仓库既有约定（`_claude_agent_title`/`_claude_agent_key_name`/`_claude_agent_model` 全部 `|| return 1`，`_claude_agent_require_provider` 缺 key 时显式报错退出），URL 无法解析应当 fail closed：不启动 Claude，并给出可操作错误。
- **实际行为**: 启动器以 `ANTHROPIC_BASE_URL: ""` 和真实的 `ANTHROPIC_AUTH_TOKEN`（例如 `DEEPSEEK_API_KEY`）执行 `claude`，函数返回 0，用户看到的是"启动成功"。
- **直接证据**:
  - zsh 5.9 语义验证（`/private/tmp/ep-review/probe2.zsh`）：
    `a() { local u="$(_f)" || return 1; ... }` 其中 `_f` 返回 3 -> 输出 `A: reached end, u=[]`，`A rc=0`；
    改成 `b() { local u; u="$(_f)" || return 1; }` -> `B rc=1`（守卫生效）；
    改成 `c() { local u="$(_f)"; [[ -n "$u" ]] || return 1; }` -> `C rc=1`（守卫生效）。
  - 真实 `scripts/agent-tools.zsh` 端到端验证（隔离 `HOME=/private/tmp/ep-review/home2`，stub `claude` 打印 `--settings` 实参，无任何网络调用）：
    - CASE A（`~/.local/bin/agent-endpoint.py` 缺失）：stderr 只有 `can't open file ...agent-endpoint.py`，随后 `SETTINGS_JSON={"env":{"ANTHROPIC_BASE_URL":"","ANTHROPIC_MODEL":"deepseek-flash[1m]",...}}`，`LAUNCH rc=0`。
    - CASE B（helper 存在但 `endpoints.json` 为 `{broken`）：stderr 只有 `Cannot load endpoints from ...`，同样 `ANTHROPIC_BASE_URL":""`，`LAUNCH rc=0`。
    - CASE C（健康对照）：`ANTHROPIC_BASE_URL":"https://api.deepseek.com/anthropic"`。
  - 这是本次改动引入的回归，不是既有隐患：改动前 `_claude_agent_base_url` 是纯 `case`/`print -r --`（见 diff `scripts/agent-tools.zsh` 旧 71-83 行），其接受的 provider 集合与先于它执行的 `_claude_agent_title`（`scripts/agent-tools.zsh:43-57`）完全一致，对已知 provider 不可能输出空串。新实现把纯函数换成了带外部 I/O 的子进程调用，失败面从"不可能"变成"任何配置或依赖问题"。
  - `_local_agent_require_service`（`scripts/agent-tools.zsh:110`）使用同样的死守卫，但它随后 `curl "${base_url%/}/health"` 会因空 URL 失败而 `return 1`，因此 `local` 意外地 fail closed（代价是错误信息误导，见下）；`ds-flash`/`mimo`/`mimo-fast`/`mimo-flash`/`qwen`/`kimi`/`glm`/`glm-flash`/`hy` 九个云端 provider 在 `_claude_agent_require_provider`（`scripts/agent-tools.zsh:121-132`）里只检查 key 是否存在，没有任何东西拦住空 base_url。
- **影响**: 静默失效 + 凭据外发风险。启动器报告成功并进入一个 base URL 为空的 Claude 会话，同时把第三方 provider 的真实 API key 作为 `ANTHROPIC_AUTH_TOKEN` 传给 `claude`。Claude Code 对空 `ANTHROPIC_BASE_URL` 的确切处理未经本轮验证（见 Open Questions），但两种可能结果都不可接受：要么回落到 Claude Code 内置默认 API 主机（把用户的第三方网关 key 送到非预期上游），要么以难以归因的方式失败。无论哪种，本应 fail closed 的守卫没有生效，且这是本改动新引入的路径。
- **建议改法和验证点**:
  - 把 `scripts/agent-tools.zsh:142` 改为先声明后赋值：`local base_url; base_url="$(_claude_agent_base_url "$agent_id")" || return 1`；或保留一行写法但补空值断言：`local base_url="$(_claude_agent_base_url "$agent_id")"; [[ -n "$base_url" ]] || { print -u2 -- "无法解析 $agent_id 的 Claude base URL"; return 1; }`。两种写法均已用上面的 probe 验证会返回 1。
  - 同一模式同时修 `scripts/agent-tools.zsh:110`，并让 `_local_agent_require_service` 的错误信息区分"helper/配置不可用"与"本地服务未启动"（当前 `scripts/agent-tools.zsh:116` 在 helper 缺失时也只会说"请检查 endpoints.json 的 local/claude URL"，指向错误原因）。
  - 建议在 `_claude_agent_base_url` 内部对 helper 做存在性检查并给出与 `scripts/agent-tools.zsh:384` 同风格的提示（`compose-codex-app-config.py 不在 PATH（是否忘了跑 sync-agent-tools.sh？）`），因为该文件已有这个约定。
  - 验证点：新增测试，在隔离 HOME 下分别制造"helper 缺失""endpoints.json 非法""provider 条目缺失"三种状态，断言 `_claude_agent_launch` 返回非 0 且**从未调用** `claude`（用 stub 记录调用即可，不需要真实 CLI）。现有 `tests/test_install_endpoints.py:34-36` 只验证了成功路径的 stdout。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 高

### 2-未修复-中-shim 唯一的请求失败分支不产生任何日志，而启动日志打印的是过期的已解析上游，导致 URL 热更新失败无法诊断

- **入口/函数**: `codex-agent/bin/codex-auto-review-shim` `Handler._handle()` 的 URL 解析分支，以及 `main()` 的启动日志
- **文件(行号)**:
  - `codex-agent/bin/codex-auto-review-shim:316-320`（`except ValueError:` -> `send_error(503, ...)`，无日志）
  - `codex-agent/bin/codex-auto-review-shim:480-483`（启动时打印已解析的 `r['upstream']` 到 stderr）
  - `codex-agent/bin/codex-auto-review-shim:468-471`（`--routes` 把已解析上游打印到 stdout）
  - 对照 `scripts/agent-endpoint.py:28-30`（明确声明"Do not echo file content: URLs can contain private routing information"）
  - 对照同文件既有日志密度：`codex-auto-review-shim:342`、`355`、`371-374`、`427-430`
- **输入场景**: 用户按本次改动的核心承诺编辑 `~/.config/agent-tools/endpoints.json`（例如把 `ds-flash.codex` 改成网关地址），但写错 scheme、留下空格、误加 query、删掉某个 provider 的 `codex` 键，或整个文件 JSON 语法损坏。
- **实际分支**: `route_url()`（`codex-auto-review-shim:91-101`）调用 `endpoint_module().endpoint(...)` -> `load_endpoints()`（`scripts/agent-endpoint.py:9-30`）抛出带具体原因的 `ValueError`（`invalid URL: ds-flash/codex` 或 `Missing endpoint: kimi/codex` 或 `Cannot load endpoints from ...`）-> `codex-auto-review-shim:318` 捕获后**丢弃异常对象**，只返回通用 503。
- **预期行为**: 该分支是整条请求链路上唯一新增的失败点，也是本特性最可能的用户错误点，应当像同文件其它失败分支一样把原因写进 `~/.codex-agent/shim.log`；启动日志不应把已经过期的已解析上游当作当前事实呈现。
- **实际行为**: 请求返回 503 与通用文案，日志里**一行都不增加**；同时日志顶部仍然显示改动前解析出的旧上游 URL，主动误导排查方向。
- **直接证据**（`/private/tmp/ep-review/shimtest`，隔离 HOME、自定义 `SHIM_ROUTES`、回环端口 18788，未触达任何真实上游）：
  - 启动日志：`[shim] 127.0.0.1:18788 -> https://api.deepseek.com/v1  (codex-auto-review -> deepseek-flash)`（证明已解析的用户私有 URL 会进入 launchd 日志；`codex-auto-review-shim-service:59-60` 把 stdout/stderr 都指向 `$HOME/.codex-agent/shim.log`）。
  - 运行中把 `endpoints.json` 改成 `{"ds-flash":{"codex":"ftp://gw.example/v1"}}` 后发一次 POST `/v1/responses`：`HTTP status = 503`，body 为 `Message: Invalid local endpoint settings or request prefix.`。
  - 请求后 `tail err.log` 仍只有那条启动行；`rg -i 'endpoint|503|prefix|ftp|invalid' err.log out.log` -> `(NO diagnostic logged at all)`。
  - 同时启动行仍显示 `https://api.deepseek.com/v1`，而实际配置已是 `ftp://gw.example/v1`：日志与真实状态不一致。
  - 隐私一致性：`--routes` 实测把用户改成私有网关后的值原样打印到 stdout（`127.0.0.1:8788  https://secret-gw.internal/custom/v1`）。改动前 `route['upstream']` 来自仓库内的公开厂商 origin（见 `git show main:codex-agent/shim-routes.json`），同一行日志不构成隐私问题；改动后同一行输出的是用户私有文件内容，与 `scripts/agent-endpoint.py:29` 自己声明的策略相反。
- **影响**: 可观测性缺失。headline 特性（"改完 URL 下一次请求就生效，无需 sync 或重启"）在最典型的失败情形下完全不可诊断：用户只看到 503，日志无任何线索，且日志显示的旧 URL 会把人引向错误结论。附带影响是把用户私有路由信息写入由 launchd 创建、权限不受本仓库控制的日志文件（`sync-codex-agent.sh:33` 的 `mkdir -p "$target_root"` 在普通 shell umask 022 下产生 0755 的 `~/.codex-agent`；install.sh 路径下因 `umask 077`（`install.sh:4`）而是 0700，两种安装路径的暴露面不一致）。
- **建议改法和验证点**:
  - 在 `codex-auto-review-shim:318` 改为 `except ValueError as exc:` 并先 `self._log(f"endpoint error: {exc}")` 再 `send_error(503, ...)`。`agent-endpoint.py` 抛出的消息本身已刻意不含 URL 值（`scripts/agent-endpoint.py:29-30`），因此记录它是安全的、不违反 no-echo 策略。
  - 启动日志（`codex-auto-review-shim:480-483`）与 `--routes`（`codex-auto-review-shim:470`）改为只打印 `endpoint_id`（托管路由）而不打印已解析 URL，例如 `[shim] 127.0.0.1:8788 -> endpoint:ds-flash (codex-auto-review -> deepseek-flash)`；显式 `upstream` 路由可保持原样。
  - 验证点：断言"损坏 endpoints.json 后发一次请求 -> 503 且日志新增一行含 `invalid URL` 或 `Missing endpoint`"；并断言启动日志/`--routes` 输出中不含 endpoints.json 里的任何 host。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 中

### 3-未修复-中-`endpoint_module()`/`load_routes()` 让原始异常逃逸，违反本文件既有的 `SystemExit` 约定；launchd `KeepAlive` 下变成带 traceback 的崩溃循环

- **入口/函数**: `codex-auto-review-shim` `main()` -> `load_routes()` -> `endpoint_module()`
- **文件(行号)**:
  - `codex-agent/bin/codex-auto-review-shim:80-88`（`endpoint_module()`，`spec.loader.exec_module` 在 `:87`）
  - `codex-agent/bin/codex-auto-review-shim:219-223`（`load_routes()` 内解析 endpoint）
  - 同文件既有约定：`codex-auto-review-shim:217`、`225`、`238`、`453` 全部使用 `raise SystemExit(<可操作消息>)`
  - `codex-agent/bin/codex-auto-review-shim-service:57-58`（`RunAtLoad: True`, `KeepAlive: True`）
  - `codex-agent/bin/codex-auto-review-shim:318`（`except ValueError` 过窄）
- **输入场景**: 服务启动时 `agent-endpoint.py` 不可解析（两个候选路径都不存在），或 `endpoints.json` 缺失/损坏/缺条目。最现实的触发路径是跨机恢复：`README.md:273-275` / `README.zh.md:264-266` 指示恢复后直接跑 `codex-auto-review-shim-service install`，而 `~/.codex-agent/bin/agent-endpoint.py` 只由 `sync-codex-agent.sh:92` 安装。
- **实际分支**: `endpoint_module()` 的 `spec_from_file_location` 对不存在的 `.py` 路径仍返回 spec（不检查存在性），于是 `:87` 的 `exec_module` 抛 `FileNotFoundError`；`load_routes()` 不捕获，`main()` 不捕获，进程以裸 traceback 退出 1。若失败发生在 `endpoint()`（缺条目/URL 非法），逃逸的是 `ValueError` traceback。
- **预期行为**: 与本文件其余配置错误一致，抛出 `SystemExit("...")` 形式的单行可操作消息（例如 `cannot load agent-endpoint.py helper: <path>; run scripts/sync-codex-agent.sh`），让日志可读、让失败原因一眼可见。
- **实际行为**: 进程以多行 Python traceback 退出；`KeepAlive: True` 使 launchd 反复重启，`~/.codex-agent/shim.log` 被 traceback 刷屏（受 launchd 10s 节流，不会忙等）。所有端口都不监听。
- **直接证据**（`/private/tmp/ep-review/nohelper`，隔离 HOME，仅复制 shim 本体使两个候选 helper 路径都不存在）：
  - 启动日志为完整 traceback，末行 `FileNotFoundError: [Errno 2] No such file or directory: '/private/tmp/ep-review/scripts/agent-endpoint.py'`；从未打印任何 `[shim] ... -> ...` 绑定行。
  - 向 127.0.0.1:18799 发请求：`HTTP=000`，`curl failed rc=7`（连接被拒，未投递任何 HTTP 响应）。
  - 缺条目场景（删除 `endpoints.json` 的 `kimi`）：`--routes` 退出码 1，末行 `ValueError: Missing endpoint: kimi/codex`，同样是裸 traceback 而非 `SystemExit` 消息。
  - `codex-auto-review-shim:318` 的 `except ValueError` 覆盖不到 `FileNotFoundError`；若 helper 在服务运行中被删除，异常会穿出 `_handle()`，由 socketserver 打印 traceback 并直接关闭连接，客户端拿不到 503（此路径未实测，属静态推论）。
- **影响**: 部分缓解但仍实质。`_codex_agent_require_shim`（`scripts/agent-tools.zsh:290-307`）会因端口无监听而 fail closed 并提示跑 `install`/`restart`，所以不会静默走错上游；但用户按提示操作会持续失败，唯一线索是日志里的 traceback，而 traceback 指向的是 importlib 内部帧，不指向"`~/.codex-agent/bin/agent-endpoint.py` 缺失"这个真因。
- **建议改法和验证点**:
  - 在 `endpoint_module()` 内先 `if not helper.exists(): raise SystemExit(f"cannot find agent-endpoint.py next to {__file__} or in <repo>/scripts; run scripts/sync-codex-agent.sh")`，并在 `load_routes()` 的 `:222-223` 外包一层把 `ValueError` 转成 `SystemExit(f"routes[{i}] endpoint {r['endpoint_id']!r} unresolvable: {exc}")`，与 `:217`/`:225` 保持同一风格。
  - 把 `codex-auto-review-shim:318` 收窄为 `except (ValueError, OSError) as exc:` 并记录原因（与 Finding 2 同一处修改）。
  - 验证点：隔离 HOME 下分别制造"helper 缺失""endpoint 缺条目"两种状态，断言 stderr 是单行消息、不含 `Traceback`、退出码非 0；这一断言风格本仓库已有先例（`tests/test_provider_registry.py:163` 的 `assertNotIn("Traceback", ...)`）。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 中

### 4-未修复-中-`request_prefix` 与注册表 `base_url` 的 path 是同一事实的两处独立编码，且既有的配对测试不校验它

- **入口/函数**: `codex-auto-review-shim` `route_url()` 的前缀剥离；契约由 `codex-agent/shim-routes.json` 与 `codex-agent/model-providers.toml` 共同决定
- **文件(行号)**:
  - `codex-agent/shim-routes.json:12,21,30,39,48,57,66,75`（8 个 `request_prefix`）
  - `codex-agent/model-providers.toml:9,16,23,30,43,50,57,64`（8 个 loopback `base_url`，其 path 即托管前缀）
  - `codex-agent/bin/codex-auto-review-shim:96-100`（`path.startswith(prefix + "/")` -> 否则 `ValueError`）
  - `tests/test_provider_registry.py:39-57`（既有配对测试：只校验 `port`（`:49-50`）与 `routes[port]["to"] == data["model"]`（`:51`）与 `_codex_agent_shim_port`（`:56`），**不校验 path**）
- **输入场景**: 后续任何一次只改其中一处的编辑，例如把 `model_providers.kimi.base_url` 从 `http://127.0.0.1:8790/coding/v1` 改成 `http://127.0.0.1:8790/v1`（换网关时很自然的动作）而没有同步改 `shim-routes.json:30` 的 `"/coding/v1"`。
- **实际分支**: Codex 按新 base_url POST 到 `/v1/responses`；`route_url()` 中 `prefix = "/coding/v1"`，`path.startswith("/coding/v1/")` 为假 -> `codex-auto-review-shim:99` 抛 `ValueError("Unexpected route prefix")` -> `:319` 返回 503。
- **预期行为**: 这两个值描述的是同一个"托管请求前缀"事实。它应当只有一个真源，或者由测试强制配对。既有测试已经把 port 与 model 的配对固定下来了，path 配对属于同一类契约，却被漏掉。
- **实际行为**: 两处独立手写，无自动校验；漂移后该 provider 的每一次 guardian 升级都 503，且（结合 Finding 2）日志中无任何原因。
- **直接证据**:
  - 本轮用 `tomllib` + `json` 对当前状态做了完整比对，8 个 provider 全部一致（`deepseek`/`mimo`/`mimo_fast`/`mimo_flash` = `/v1`，`glm`/`glm_flash` = `/api/v1`，`kimi` = `/coding/v1`，`qwen` = `/compatible-mode/v1`）。所以这是潜在缺陷而非当前 live bug。
  - `rg -n 'request_prefix'` 全仓命中只有 `codex-agent/shim-routes.json` 与 `codex-auto-review-shim`；没有任何测试文件出现该键，证明配对未被固定。
  - `tests/test_provider_registry.py:49` 已经用 `urlsplit(provider["base_url"]).port` 取 port 做配对，取 `.path` 做同样断言只需一行，说明遗漏是缺口而非设计取舍。
  - semantic ownership：本改动之前，请求 path 原样转发给厂商 origin（`upstream_url()`，`codex-auto-review-shim:73-77`），托管前缀这一事实只存在于 `model-providers.toml` 的 `base_url`。本改动新增了第二份编码（`request_prefix`），扩大了双真源模式。
- **影响**: 可维护性 + 静默失效。任何一次网关/端口调整都可能只改一处，导致该 provider 的自动审批升级全部 503；错误信息还会把原因归到"local endpoint settings"（`:319`），把排查方向从真正的 `request_prefix` 漂移引开。
- **建议改法和验证点**:
  - 最小改动：在 `tests/test_provider_registry.py:39-57` 的现有循环里补一行 `self.assertEqual(urlsplit(provider["base_url"]).path, routes[port].get("request_prefix", ""))`（`local_llama` 已在 `:45-46` 被跳过，不受影响）。
  - 更彻底：从注册表派生前缀，取消 `shim-routes.json` 中的 `request_prefix` 字段（例如让 `sync-codex-agent.sh` 在写 `~/.codex-agent/shim-routes.json` 时按 port 从 `model-providers.toml` 注入 path）。这会消除双真源，但改动面更大，可作为独立后续。
  - 验证点：临时把某个 `request_prefix` 改错，断言测试失败。
- **修复风险（低/中/高）**: 低（测试补充方案）
- **严重程度（低/中/高/严重）**: 中

### 5-未修复-中-新增测试文件使用 Python 3.12 已移除的 `load_module()`，仓库却声明支持 3.11+，导致本特性最重要的生命周期回归护栏在新解释器上整体消失

- **入口/函数**: `tests/test_install_endpoints.py` 模块级导入
- **文件(行号)**: `tests/test_install_endpoints.py:14`
- **输入场景**: 在 Python 3.12 或更新版本上运行 `python3 -m unittest discover -s tests`（`README.md:617` 记载的官方测试命令）。`install.sh:21` 只要求 `sys.version_info >= (3, 11)`，`README.md:69` 写 "Python 3.11+"。
- **实际分支**: `importlib.machinery.SourceFileLoader(...).load_module()` 在 3.12 中已被移除，模块导入即抛 `AttributeError`，整个文件（含 `EndpointTests` 与 `InstallTests`）无法收集。
- **预期行为**: 与同目录其余四个测试一致，使用 `importlib.util.spec_from_file_location` + `spec.loader.exec_module`。
- **实际行为**: 在 3.11 上产生 `DeprecationWarning: the load_module() method is deprecated and slated for removal in Python 3.12`；在 3.12+ 上整文件报错。
- **直接证据**:
  - `rg -n 'load_module|exec_module|spec_from_file_location|SourceFileLoader' tests/*.py`：`test_install_endpoints.py:14` 是唯一使用 `SourceFileLoader(...).load_module()` 的文件；`test_provider_registry.py:21,24`、`test_codex_model_defaults.py:19,22`、`test_model_catalog_generation.py:20,23`、`test_repair_codex_reasoning_history.py:20,23` 全部使用 `spec_from_file_location` + `exec_module`。
  - 本轮实测（Python 3.11.15）运行输出确实带该 DeprecationWarning。
  - 该文件承载的正是本任务要求的核心生命周期证据：`test_switch_gateway_path_without_sync_or_restart`（`tests/test_install_endpoints.py:18`，热更新、错误前缀、损坏 JSON）与 `test_downloaded_bootstrap_reinstall_and_sync_preserve_local_state`（`:56`，下载式 bootstrap、重装保真、`git pull --ff-only`、0600 权限、`trust_level` 保留）。3.12+ 上这些断言全部不再执行，而 `unittest discover` 只会显示一个导入错误，很容易被当成环境问题忽略。
- **影响**: 测试面回归。核心需求（"改 URL 必须在所有 sync/reinstall 后存活"）的唯一自动化护栏在受支持的解释器版本上失效。
- **建议改法和验证点**:
  - 改为：
    ```python
    spec = importlib.util.spec_from_file_location('endpoint_shim', ROOT / 'codex-agent/bin/codex-auto-review-shim')
    shim = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shim)
    ```
  - 验证点：在 3.11 上确认 DeprecationWarning 消失且 25 项仍通过；若环境有 3.12+，确认 `unittest discover` 能收集该文件。
  - 附带：该写法会把字节码缓存写进仓库工作树（本轮观察到 `codex-agent/bin/__pycache__/codex-auto-review-shimcpython-311.pyc`）。`.gitignore:3` 已忽略 `__pycache__/`，因此不会污染 `install.sh:32` 的 `git status --porcelain` 洁净度守卫，也不影响 `sync-codex-agent.sh:85-89` 的 `[[ -f "$src" ]]` 过滤（目录被跳过）。无需修改，仅记录。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 中

### 6-未修复-中-`sync-codex-providers.py` 新增的 `--local-base-url` 正则改写路径零测试覆盖，且失败消息指向错误原因

- **入口/函数**: `scripts/sync-codex-providers.py:main()` 的 `--local-base-url` 分支；唯一调用方 `scripts/sync-codex-agent.sh:31,41`
- **文件(行号)**: `scripts/sync-codex-providers.py:58`（新参数）、`:70-76`（`re.subn` 改写注册表文本）
- **输入场景**: 用户在 `~/.config/agent-tools/endpoints.json` 改 `local.codex` 后跑 `sync-codex-agent.sh`（`README.md:123` 记载的正式流程）；或后续有人编辑 `codex-agent/model-providers.toml` 的 `[model_providers.local_llama]` 段。
- **实际分支**: `scripts/sync-codex-providers.py:71-74` 用正则 `(\[model_providers\.local_llama\]\n[^\[]*?base_url = )"[^"\n]*"` 在**注册表文本**上做替换，`:75-76` 在 `count != 1` 时抛 `ValueError("local_llama base_url missing from registry")`。
- **预期行为**: 这是一条会写入用户 live `~/.codex/config.toml` 的新路径，应当有测试证明：替换生效、幂等、以及在注册表结构变化时报出准确原因。
- **实际行为**: 无任何测试触及该分支；错误消息在"段落里出现 `[`"这类结构变化时会说"base_url missing"，而真因是正则锚点失配，排查方向被引开。
- **直接证据**:
  - `rg -n 'local-base-url|local_base_url' tests/ scripts/ install.sh`：命中仅在 `scripts/sync-codex-agent.sh:31,41` 与 `scripts/sync-codex-providers.py:58,70,73`；`tests/` 下 0 命中。
  - `tests/test_provider_registry.py` 中所有 `SYNC` 子进程调用（`:77`、`:109`、`:112`、`:113` 附近）与所有 `compose()` 直接调用（`:62-63`、`:71`、`:147`）都不传 `--local-base-url`；`test_sync_preserves_local_config_and_is_idempotent`（`:59-66`）覆盖的是未替换路径的幂等性。
  - `[^\[]*?` 的脆弱性可由当前注册表结构直接看出：`codex-agent/model-providers.toml:35-39` 的 `local_llama` 段今天不含 `[`，本轮实测 `count == 1`；但只要有人在该段加一行含 `[` 的注释（例如 `# see [docs]`），替换即失败。
  - 缓解因素（如实记录，不改变"无覆盖"结论）：`compose()` 在 `scripts/sync-codex-providers.py:50` 会用 `tomllib.loads(result)` 复验最终文本，`:96-98` 还有"写入前 base 未被并发改动"的检查与 `os.replace` 原子替换，`:78-79` 把 `ValueError` 转成 `ap.error`（退出码 2，无 traceback）。所以损坏写入被挡住了，缺陷是"新路径无测试 + 错误归因不准"，不是"会写坏配置"。
- **影响**: 测试缺口。`local` 端点按文档只能通过这条路径生效，而它完全没有回归保护；一旦注册表排版调整，用户会得到一条指向错误原因的消息。
- **建议改法和验证点**:
  - 新增测试：以临时注册表副本调用 `SYNC --base ... --registry ... --local-base-url http://127.0.0.1:9999/v1`，断言输出 `tomllib` 中 `model_providers.local_llama.base_url == "http://127.0.0.1:9999/v1"`；再跑一次断言字节不变（幂等）；再断言不传该参数时保留注册表默认值；最后断言注册表缺 `local_llama` 段时退出码非 0 且 base 文件未被改动（可复用 `tests/test_provider_registry.py:73-88` 的既有断言风格）。
  - 把 `:76` 的消息改成能区分两种情形，例如 `cannot locate [model_providers.local_llama] base_url in registry (section missing or contains a '[' character)`。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 中

### 7-未修复-中-两个 README 的"恢复到另一台 Mac"章节未随新依赖更新，与新增的"先跑一次 installer"要求互相矛盾

- **入口/函数**: 文档化的跨机恢复流程 vs `scripts/sync-codex-agent.sh` 的新前置校验
- **文件(行号)**:
  - `README.md:273-275` / `README.zh.md:264-266`（"If the archive contains an older service script, run `./scripts/sync-codex-agent.sh` from an updated checkout first"）
  - `README.md:123` / `README.zh.md:119`（新增的"For an existing installation, run the installer once to initialize the URL file before using the updated sync scripts"）
  - `scripts/sync-codex-agent.sh:29`（`agent-endpoint.py --check`，缺失即退出）
  - `scripts/sync-codex-agent.sh:92`（`agent-endpoint.py` 的唯一安装点）
  - `codex-agent/bin/codex-auto-review-shim-service:18-19`（服务只依赖 `~/.codex-agent/bin/codex-auto-review-shim` 与 `shim-routes.json`，自身不校验 helper 是否存在）
- **输入场景**: 按 README 把 Agent 环境恢复到一台新 Mac：归档里有旧的 `~/.codex-agent`，没有 `~/.config/agent-tools/endpoints.json`。用户照 `README.md:275` 先跑 `./scripts/sync-codex-agent.sh`。
- **实际分支**: `scripts/sync-codex-agent.sh:29` 立即失败退出，`~/.codex-agent/bin/` 保持为空（helper 与 shim 都没装）。用户若转而照 `README.md:270` 直接跑 `codex-auto-review-shim-service install`，则得到 Finding 3 证明的崩溃循环。
- **预期行为**: 恢复章节应当说明新的前置条件（先跑 installer 初始化 `endpoints.json`），或至少与 `README.md:123` 一致。
- **实际行为**: 同一份 README 的两处对同一操作给出矛盾指令；恢复章节完全没提 `endpoints.json` 或 `agent-endpoint.py`。
- **直接证据**:
  - 隔离 HOME（无 `endpoints.json`）实跑 `bash scripts/sync-codex-agent.sh`：输出 `Cannot load endpoints from /private/tmp/ep-review/noep/.config/agent-tools/endpoints.json; run install.sh or fix the local JSON`，随后 `ls $HOME/.codex-agent/bin/` 为空——确认 fail closed 且无半成品写入（这一点是好的）。
  - `rg -n 'endpoints' README.md` 的命中全部集中在新的 `### Local API keys and upstream URLs` 小节（`:108-123`）；`README.md:273-275` 所在段落无任何 `endpoints.json` / `agent-endpoint.py` 字样。`README.zh.md` 同样（`:264-266` vs `:104-119`）。
  - 错误消息本身指向 `install.sh`，属于有效缓解；缺陷在于文档流程会先把用户导向一条必然失败的路径。
- **影响**: 文档与实际行为不一致，跨机恢复（本仓库明确支持的场景）第一步即失败，且失败信息不在用户正在阅读的那一节。
- **建议改法和验证点**:
  - 在 `README.md:275` / `README.zh.md:266` 之前插入一句：恢复后先运行一次 `bash install.sh`（或至少确保 `~/.config/agent-tools/endpoints.json` 存在），再运行 `./scripts/sync-codex-agent.sh`；并说明 `sync-codex-agent.sh` 现在会安装 `~/.codex-agent/bin/agent-endpoint.py`，shim 运行时依赖它。
  - 验证点：文档走查——`rg -n 'sync-codex-agent.sh' README.md README.zh.md` 的每一处出现，都应能在其上下文中找到 `endpoints.json` 前置条件的说明或指向 `:123`/`:119` 的引用。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 中

### 8-未修复-中-两个 README 的仓库结构与"真源文件"清单未收录本改动新增的 5 个仓库文件，且若干前置条件陈述被本改动改为过时

- **入口/函数**: Agent 面向的文档可用性（本任务明确要求检查）
- **文件(行号)**:
  - `README.md:522-581`（Repository Layout）与 `README.md:583-605`（Maintenance："Edit only the source files in this repository"）
  - `README.zh.md:501-560`（仓库结构）与 `README.zh.md:562-584`（维护流程："只编辑本仓库中的真源文件"）
  - `README.md:130` / `README.zh.md:125`（`sync-agent-tools.sh` 的安装清单）
  - `README.md:135` / `README.zh.md:130`（python3 前置条件）
  - `README.md:140` / `README.zh.md:135`、`README.md:254`、`README.md:337` / `README.zh.md:245`、`README.zh.md:321`（`local` 的固定 8080）
  - `install.sh:12` vs `install.sh:18`；`README.md:94` vs `install.sh:18`
- **输入场景**: 一个 Agent 或新维护者按 README 的"Maintenance/Edit only the source files"清单判断哪些文件属于仓库真源、哪些属于用户本地。
- **实际分支**: 清单不含 `install.sh`、`config/endpoints.example.json`、`scripts/agent-endpoint.py`、`scripts/validate-skill.py`、`tests/test_install_endpoints.py`；Repository Layout 的 `scripts/` 段（`README.md:563-576`）不含 `agent-endpoint.py` 与 `validate-skill.py`，`tests/` 段（`README.md:577-580`）不含 `test_install_endpoints.py`，且整棵树没有顶层 `config/` 与 `install.sh`。
- **预期行为**: 本改动的核心正是"区分仓库真源与用户自有文件"（`README.md:20` 新增句、`README.md:108-123` 新小节）。作为该区分权威枚举的 Maintenance 清单，应当收录新增的仓库侧文件；尤其 `config/endpoints.example.json` 是用户文件的模板真源，`scripts/agent-endpoint.py` 是启动器与 shim 共同的运行时依赖。
- **实际行为**: 权威清单缺失，读者无法从文档得知 `config/endpoints.example.json` 属于仓库真源（改动它会影响所有新安装）。
- **直接证据**:
  - `sed -n '522,582p' README.md` 实测输出：`scripts/` 段 13 项，无 `agent-endpoint.py`/`validate-skill.py`；`tests/` 段 3 项，无 `test_install_endpoints.py`；无 `config/`、无 `install.sh`。`README.zh.md:501-560` 同构。
  - `rg -n 'agent-endpoint' README.md README.zh.md` -> 0 命中。而 `scripts/agent-tools.zsh:74` 对 `$HOME/.local/bin/agent-endpoint.py` 是硬依赖，`README.md:130` 又恰好在同一节列举 `sync-agent-tools.sh` 安装了什么（只提 `repair-codex-reasoning-history.py`），说明这里是有意维护的清单，遗漏是缺口。
  - 过时陈述一：`README.md:135` / `README.zh.md:130` 仍称 python3 只用于"launcher-only `--resume` repair option"。改动后每次 Claude 启动都要 `python3`（`scripts/agent-tools.zsh:74`），每次 `sync-codex-agent.sh` 也要（`:29-31`）。
  - 过时陈述二：`README.md:140` / `README.zh.md:135` 仍称 `local` 启动器需要 `http://127.0.0.1:8080` 上的服务，`README.md:254`、`:337` 与 zh `:245`、`:321` 也写死 8080；但改动后该地址来自用户自有的 `endpoints.json` `local/claude` 与 `local/codex`（`scripts/agent-tools.zsh:110-118`、`scripts/sync-codex-agent.sh:31`），用户完全可以改成别的端口。`README.md:123` 已说明 `local.codex` 由 sync 注入注册表，与 `:140`/`:337` 的固定值陈述冲突。
  - 次要：`install.sh:12` 的 `--help` 文案列 `Git, Codex CLI, Claude Code, Python 3.11+, jq, uv, tmux and rsync`，而 `install.sh:18` 实际强制检查 `git codex claude python3 jq uv tmux rsync zsh curl`——`--help` 漏 `zsh` 与 `curl`；`README.md:94` 的安装前置句列了 `zsh` 但漏 `curl`，而 `curl` 恰是 README 自己给出的下载命令所必需。
  - 公平性说明：这两棵树在 `main` 上已经部分过时（缺 `test_shim_service.py`、`test_model_catalog_generation.py`、`test_sub_agent_preflight.py`，已由 `git show main:README.zh.md` 核对）。本 finding 只针对**本次新增的 5 个文件**与**被本次改动改为过时的陈述**，不把既有陈旧计入。
- **影响**: 文档与实际契约漂移。Agent 依据 Maintenance 清单判断所有权时会漏掉 `config/endpoints.example.json`（可能误以为它是用户本地文件而不敢改，或反之在用户文件里改而期望生效）；依据 `README.md:135`/`:140` 会低估 python3 的必要性、误信 `local` 地址固定。
- **建议改法和验证点**:
  - 在两份 README 的 Repository Layout 树补 `install.sh`、`config/endpoints.example.json`、`scripts/agent-endpoint.py`、`scripts/validate-skill.py`、`tests/test_install_endpoints.py`；在 Maintenance 真源清单补同样 5 项。
  - `README.md:130` / `README.zh.md:125` 补上 `agent-endpoint.py`。
  - `README.md:135` / `README.zh.md:130` 改为"python3 3.11+ 为启动器与同步脚本的必需依赖（Claude base URL 解析、`sync-codex-agent.sh` 校验），并用于 `--resume` 修复选项"。
  - `README.md:140`、`:254`、`:337` 与 zh 对应行改为指向 `endpoints.json` 的 `local` 条目，不再写死 8080。
  - `install.sh:12` 与 `README.md:94` 补齐 `curl`（`--help` 再补 `zsh`）。
  - 验证点：`rg -n 'agent-endpoint|endpoints.example|validate-skill|install\.sh|test_install_endpoints' README.md README.zh.md` 在树与清单两处都有命中；`rg -n '8080' README.md README.zh.md` 的每一处都明确标注为默认值而非固定要求。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 中

### 9-未修复-低-`agent-tools.zsh` 硬编码 `$HOME/.local/bin/agent-endpoint.py`，与 `sync-agent-tools.sh` 支持的 `AGENT_RUN_BIN_DIR` 及本文件既有的 PATH 解析约定不一致

- **入口/函数**: `scripts/agent-tools.zsh:_claude_agent_base_url()`
- **文件(行号)**: `scripts/agent-tools.zsh:74`；对照 `scripts/sync-agent-tools.sh:7`（`agent_run_bin_dir="${AGENT_RUN_BIN_DIR:-$HOME/.local/bin}"`）与 `:16`（helper 的安装点）；对照 `scripts/agent-tools.zsh:383-386`（既有约定：`command -v compose-codex-app-config.py` + 明确的"是否忘了跑 sync-agent-tools.sh？"提示）
- **输入场景**: 设置 `AGENT_RUN_BIN_DIR` 到非默认目录后运行 `sync-agent-tools.sh`（该变量确实被支持，`tests/test_repair_codex_reasoning_history.py:115` 就在用它）；或用户把 `~/.local/bin` 迁走。
- **实际分支**: helper 被装到 `$AGENT_RUN_BIN_DIR`，但已安装的 `agent-tools.zsh` 仍去 `$HOME/.local/bin/agent-endpoint.py` 找，`python3` 报 `can't open file`。
- **预期行为**: 与同文件对其它已安装 runner 的处理一致——按 PATH 解析，或在不可用时给出与 `:384` 同风格的可操作提示。
- **实际行为**: 路径写死；失败后没有任何提示，直接落入 Finding 1 的空 `base_url` 静默路径。
- **直接证据**: `rg -n 'AGENT_RUN_BIN_DIR|AGENT_TOOLS_TARGET|AGENT_TOOLS_LOCAL_FILE'` 显示 `AGENT_RUN_BIN_DIR` 只出现在 `scripts/sync-agent-tools.sh:7` 与 `tests/test_repair_codex_reasoning_history.py:115`；`scripts/agent-tools.zsh` 内 0 命中，而同一文件对 `AGENT_TOOLS_LOCAL_FILE`（`:9`）是尊重的。`scripts/agent-tools.zsh:383` 对 `compose-codex-app-config.py` 用 `command -v` 并配了明确错误文案，证明本文件已有更好的既有约定。
- **影响**: 局部行为错误，且是 Finding 1 的一个触发器。当前无生产路径设置非默认 `AGENT_RUN_BIN_DIR`（仅测试使用），故列为低；但一旦使用，故障表现是 Finding 1 的静默错误而非明确报错。
- **建议改法和验证点**:
  - 改为 `local helper="${AGENT_ENDPOINT_HELPER:-agent-endpoint.py}"; command -v "$helper" >/dev/null 2>&1 || { print -u2 -- "agent-endpoint.py 不在 PATH（是否忘了跑 sync-agent-tools.sh？）"; return 1; }`，或至少在 `:74` 前加 `[[ -r "$HOME/.local/bin/agent-endpoint.py" ]] || { print -u2 -- "..."; return 1; }`。
  - 注意与 Finding 1 一起修：只加存在性检查而不修 `:142` 的死守卫，仍然会被静默吞掉。
  - 验证点：`AGENT_RUN_BIN_DIR` 指向临时目录跑 `sync-agent-tools.sh`，再 source `agent-tools.zsh`，断言 `_claude_agent_base_url ds-flash` 返回非 0 并输出可操作提示。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 低

---

## 需求符合性核对（逐条，基于上面的证据）

| 用户要求 | 结论 | 证据 |
| --- | --- | --- |
| 上游 base URL 放在用户自有本地文件（与 API key 同级） | 满足 | `~/.config/agent-tools/endpoints.json` 与 `~/.config/zsh/agent-tools.local.zsh` 均由 `install.sh:55-65` 以 `O_WRONLY|O_CREAT|O_EXCL, 0o600` 独占创建；`rg` 全仓确认没有任何 sync 脚本写这两个文件 |
| 云端 Codex URL 改动在 sync/reinstall 后存活 | 满足 | 注册表云端条目全部保持 loopback（`codex-agent/model-providers.toml:9,16,23,30,43,50,57,64`），`compose()` 只替换带标记块（`scripts/sync-codex-providers.py:35-49`）；`shim-routes.json` 不含任何 URL，只有 `endpoint_id` + `request_prefix`；shim 每次请求重读（`codex-auto-review-shim:91-101`）。实测：改 `ds-flash` 为 `https://secret-gw.internal/custom/v1` 后 `--routes` 立即反映新值，未跑任何 sync |
| 云端 Claude URL 改动在 sync/reinstall 后存活 | 满足（但见 Finding 1） | `scripts/agent-tools.zsh:73-75` 已删除全部厂商 URL 硬编码，改为每次启动查用户文件；`sync-agent-tools.sh:10` 只覆盖 `agent-tools.zsh` 本身，不碰 endpoints.json。实测 CASE C 正确返回；CASE A/B 暴露失败处理缺陷 |
| 提供下载式/本地 installer | 满足 | `install.sh` 双模式：checkout 内直接跑（`:24-25` 探测 `scripts/sync-codex-agent.sh` + `skills/`），或下载后跑（`:27-37` clone/ff-only pull，并强制校验 origin URL、分支为 main、工作树洁净，任一不符即 `die`） |
| 更新两个 README | 部分满足 | 新增 `### Local API keys and upstream URLs`（`README.md:108-123`）与 zh 对应小节，内容准确；但见 Finding 7（恢复章节矛盾）与 Finding 8（结构/真源清单缺失、多处陈述过时） |
| URL 只选上游，不做协议/模型翻译 | 满足 | `route_url()` 只做前缀剥离与拼接（`codex-auto-review-shim:96-101`），模型 id 改写仍由既有的 `rewrite()`/`_swap()` 按 `from`/`to` 完成，未与 URL 逻辑耦合；`README.md:119` 明确写出"changing URLs does not translate protocols or change model IDs" |
| guardian shim 仍是内部 loopback 传输，云端上游 URL 从本地文件热加载 | 满足 | 注册表保持 `127.0.0.1:<port>`；`route_url()` 的注释与实现都是每请求重读（`codex-auto-review-shim:92-95`），`lru_cache` 只缓存模块对象（`:80-88`）不缓存配置。实测运行中改 endpoints.json，下一次请求即反映（改成非法 scheme 立刻 503） |
| `local` llama 直连端点由 sync 按文档更新 | 满足（但见 Finding 6） | `scripts/sync-codex-agent.sh:31` 读 `local/codex`，`:41` 传给 `--local-base-url`，`scripts/sync-codex-providers.py:70-76` 注入注册表文本；`README.md:123` 记载需重跑该脚本。实测本轮 `count == 1`，默认值与 `config/endpoints.example.json:36` 一致 |

其它检查项：

- **prerequisites**：`install.sh:17-21` 检查 Darwin、10 个命令、Python 3.11+；fail closed，消息明确。缺陷仅为文档列举不全（Finding 8）。
- **failure/reinstall preservation**：`install.sh:55-65` 用 `O_EXCL` 保证"仅缺失时初始化，重装保留精确字节"；`tests/test_install_endpoints.py:107-121` 断言二次安装后 `endpoints.json`、`agent-tools.local.zsh`、`.zshrc` 三者字节完全相同，且 `~/.codex/config.toml` 里用户自加的 `trust_level="trusted"` 保留、`git pull` 恰好发生一次。本轮独立复跑通过。
- **fresh skill validation**：`install.sh:43-47` 用 uv 建私有 venv 装 `PyYAML==6.0.3`，导出 `SKILL_VALIDATOR_PYTHON`/`SKILL_VALIDATOR` 后跑 `validate-skills.sh`；`scripts/validate-skills.sh:5` 的默认校验器已从 `~/.codex/skills/.system/skill-creator/scripts/quick_validate.py` 改为仓库自有的 `scripts/validate-skill.py`，消除了对"已安装 skill home"的依赖。本轮实跑 `scripts/validate-skill.py` 对 6 个仓库 skill 全部通过（`deepreview`/`gateflow`/`phaseflow`/`planreview`/`sub-agents`/`tmux-agents`），证明新校验器不会在干净机器上把安装卡死。
- **key/URL ownership**：两个用户文件均 0600，`install.sh:4` 的 `umask 077` 与 `os.open(..., 0o600)` 一致；`tests/test_install_endpoints.py:109` 断言权限。`scripts/agent-endpoint.py:22-24` 拒绝带 userinfo 的 URL（`parts.username`/`parts.password`），避免凭据被写进 URL；`:29` 显式不回显文件内容，`tests/test_install_endpoints.py:43-51` 用 4 个含 `private` 标记的非法 URL 断言 stderr 不泄露。这两处设计是本次改动中质量较高的部分。
- **path/protocol forwarding**：8 条路由的前缀剥离逐条手工核算，与 `main` 上的旧 `upstream_url()` 行为等价（`ds-flash` -> `https://api.deepseek.com/v1/responses`；`glm`/`glm-flash` -> `.../api/v1/responses`；`kimi` -> `.../coding/v1/responses`；`qwen` -> `.../compatible-mode/v1/responses`；`mimo`/`mimo-flash`/`mimo-fast` 各自对应）。显式 `upstream` 路由与单路由 env 模式（`codex-auto-review-shim:460-466`）保持旧的逐字转发 + `/v1` 去重语义，向后兼容。
- **CLI/App/runner use**：Codex CLI 与 App 都经共享注册表的 loopback 地址走 shim，因此都享有热加载（App 侧由 `compose-codex-app-config.py` 在每次启动重组 home，`scripts/agent-tools.zsh:382-393`，注册表值来自 `~/.codex/config.toml`，不含云端 URL）。`claude-agent-run` 通过 `source "$agent_tools_file"`（`scripts/claude-agent-run:329`）复用同一 `_claude_agent_base_url`，因此同样受 Finding 1 影响；`rg` 确认 `claude-agent-run`/`codex-agent-run`/`sub-agent-preflight` 自身都不解析 base URL，没有第二处真源。
- **AGENTS.md 合规**：本次 review 未修改实现/测试/文档、未 stage/commit/push、未建 PR、未推进 gate、未派发子 Agent；唯一写入是本文档。任务显式授权 Qwen 作为第二 review 路线，覆盖 `AGENTS.md` 的 `mimo-flash` 默认（`AGENTS.md` 自身也写明"Explicit user instructions for a task take precedence"）。

---

## Open Questions

1. Claude Code 对 `ANTHROPIC_BASE_URL=""`（空字符串，非未设置）的确切行为是什么？是回落到内置默认 API 主机、还是启动即报错？这决定 Finding 1 是"凭据被送往非预期上游"还是"启动失败但报错难归因"。本轮未验证：验证需要真实运行 `claude` 并触达网络，超出授权范围。两种结果都要求修复，但严重程度的表述取决于答案。
2. `install.sh` 的下载式路径依赖 `patch-codex-model-catalog.py` 通过 `codex debug models` 读取内置目录（`tests/test_install_endpoints.py:58` 用真实 `codex` 取得该输出）。在一台**已装 Codex CLI 但尚未登录**的干净机器上，`codex debug models` 是否仍成功？若失败，`install.sh` 会在 `:71`（`sync-codex-agent.sh`）中断，此时 skills 与 launchers 已同步、`.zshrc` 未写、服务未装，属部分安装。本轮未验证：需要真实执行安装器，未获授权。
3. `~/.codex-agent/shim.log` 由 launchd 创建，其权限不受本仓库控制。Finding 2 中"用户私有网关 URL 落入日志"的实际暴露面取决于该文件模式与 `~/.codex-agent` 的创建路径（install.sh 的 umask 077 vs 普通 shell 的 022）。未做真实安装，故未实测该文件模式。
4. `codex-agent/shim-routes.json` 允许同一路由同时写 `endpoint_id` 与 `upstream`；`load_routes()`（`:219-223`）与 `route_url()`（`:94-95`）都一致地优先 `endpoint_id` 并静默忽略 `upstream`。这是有意设计还是应当报错拒绝歧义配置？当前仓库文件不含这种混用，故无法从代码判断意图。

## Residual Risk

- **测试证据**：本轮独立运行两套。
  - `HOME=/private/tmp/ep-review/testhome python3 -m pytest tests/test_install_endpoints.py tests/test_provider_registry.py tests/test_codex_model_defaults.py tests/test_shim_service.py -q` -> `25 passed, 1 warning, 27 subtests passed in 14.16s`。
  - `HOME=/private/tmp/ep-review/fullhome python3 -m pytest tests -q`（隔离 HOME，预置 `config/endpoints.example.json` 副本）-> `49 passed, 1 warning, 97 subtests passed in 21.84s`，与 controller 报告的 49 项一致。唯一 warning 即 Finding 5 的 `load_module()` DeprecationWarning。
  - 全部测试均在临时 HOME 下运行；未对真实 `$HOME` 执行 installer 或任何 sync 脚本。`scripts/sync-codex-agent.sh` 的一次实跑使用 `HOME=/private/tmp/ep-review/noep` 且在第 29 行即失败退出，未写入任何目标目录（事后 `ls` 确认 `~` 下 `.codex-agent/bin` 为空）。
- **未覆盖区域**：
  - 未做真实安装、真实 `git clone`/`git pull`、真实 `uv venv`/`uv pip install`/`uv tool install`、真实 launchd `bootstrap`/`bootout`。`tests/test_install_endpoints.py` 用 mock 替代了 `git`/`uv`/`launchctl`/`codex`/`claude`，因此 `uv venv --allow-existing` 的实际行为、`PyYAML==6.0.3` 的真实安装、以及 `claude-code-tools==1.29.1` 的真实安装都未被任何测试证明。
  - 未验证 launchd 服务在真实登录环境下的 `HOME` 解析。静态判断为安全：plist 只注入 `SHIM_ROUTES`（`codex-auto-review-shim-service:56`），gui domain 用户 agent 会继承用户 `HOME`；即使 `HOME` 未设，`Path.home()` 也会回落到 `pwd.getpwuid()`。
  - `endpoint_module()` 的 `lru_cache`（`codex-auto-review-shim:80`）在 `ThreadingHTTPServer` 多线程首次并发调用时可能重复执行被装饰函数（CPython 的 `lru_cache` 不在用户函数执行期间持锁）。后果仅为构造出两个等价模块对象、其中一个被缓存，不影响正确性，故未列为 finding。
  - 未审阅 `skills/*/SKILL.md` 正文、`codex-agent/profiles/*/config.toml` 正文、`scripts/claude-agent-run` 与 `scripts/codex-agent-run` 全文（仅 grep 确认它们不解析 base URL）。
  - `README.md`/`README.zh.md` 中与本改动无关的 skill 使用说明（各约 450 行）只做略读。
- **CI**：本仓库工作树内未见 CI 配置文件纳入本次 review 范围；无 PR，因此没有远端 check 状态可核对。测试通过与否的证据完全来自上面的本地运行。
- **本轮结论的时效性**：所有结论严格绑定 `842eca3642e5d51c6d849870ea42d1deb9569aa3` 的未提交工作树状态，以及 `diff.patch` sha256 `e06d59eb...`、`manifest.json` sha256 `bb5a8cfb...`。若该状态被修改，本 review 不再适用。
