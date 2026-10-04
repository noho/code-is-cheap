RUNTIME/PROVIDER/MODEL: codex/qwen/qwen3.8-max
CANARY=qwen-6e44735f

# Code Review

## Scope

- Mode: current changes（`$deepreview --base main`），本轮为 final fix delta 的增量收口 review，不是新的全仓审计
- Branch or PR: `feat/local-endpoints-installer`
- Base: `main` = `842eca3642e5d51c6d849870ea42d1deb9569aa3`
- HEAD: `842eca3642e5d51c6d849870ea42d1deb9569aa3`（与 base 同一 commit；全部改动都是未提交的工作树状态：12 个 modified + 5 个 untracked 路径）
- Output file: `docs/reviews/local-endpoints-install-qwen-r2-20261004.md`
- Review timestamp: `20261004-192528`（Asia/Shanghai，取自本机系统时钟 `date +%Y%m%d-%H%M%S`）
- Configured identity: 派发方配置的 runtime/provider/model 为 `codex` / `qwen` / `qwen3.8-max`。按任务指令只报告配置标签，未做任何 wire-model 探测；通用 Codex 系统身份不作为 wire-model 证据。
- 第二 review 路由：本轮由用户显式指定 Qwen，覆盖 `AGENTS.md:6` 的默认 `mimo` + `mimo-flash`；`AGENTS.md:10` 明确“Explicit user instructions for a task take precedence”，故不违反仓库指令。
- Frozen inputs（本轮全部按要求校验）:
  - manifest: `/private/tmp/code-is-cheap-endpoint-review/r2/manifest.json`，sha256 `35c0d9f0f2188eeac0cdd714feec65b1a5f9ceae9e8f8e9fefd187ea6fb499ec`，17 条路径
  - tracked diff: `/private/tmp/code-is-cheap-endpoint-review/r2/diff.patch`，sha256 `22f96ebf902d62ab6b0c69d90865f7462030a46e4efead27a92b675a2653f44c`（12 files changed, 231 insertions, 100 deletions）
  - fix delta: `/private/tmp/code-is-cheap-endpoint-review/r2/fix-delta.patch`，sha256 `878c602907b0518da03c51645305baf0cb39612671add02f12f1e1548eaeec70`，688 行，逐 hunk 全读
- Hash verification: 17/17 manifest sha256 在 review 前与 review/测试后各校验一次，两次均 `ALL OK`（无 MISSING、无 MISMATCH）。review 结束时重新生成的 `git diff --no-ext-diff main` 与冻结 `diff.patch` 字节相同（同一 sha256 `22f96ebf...`），即冻结身份在整个 review 期间未漂移。
- 并发写入说明: review 过程中工作树新增了两个非本 review 创建的 untracked 文件（`docs/reviews/local-endpoints-install-adjudication-20261004.md`、`docs/reviews/local-endpoints-install-mimo-r2-20261004.md`）。按任务禁令未读取另一份 r2 报告；17 条冻结路径的哈希未受影响。
- Included scope: manifest 的全部 17 个路径（`README.md`、`README.zh.md`、`codex-agent/bin/codex-auto-review-shim`、`codex-agent/model-providers.toml`、`codex-agent/shim-routes.json`、`scripts/agent-tools.zsh`、`scripts/sync-agent-tools.sh`、`scripts/sync-codex-agent.sh`、`scripts/sync-codex-providers.py`、`scripts/validate-skills.sh`、`tests/test_codex_model_defaults.py`、`tests/test_provider_registry.py`、`config/endpoints.example.json`、`install.sh`、`scripts/agent-endpoint.py`、`scripts/validate-skill.py`、`tests/test_install_endpoints.py`）。为追踪调用链另读取（未修改）：`scripts/sync-skills.sh`、`scripts/claude-agent-run`、`scripts/codex-agent-run`、`skills/sub-agents/SKILL.md` 的 runner 调用方式、`git show main:scripts/agent-tools.zsh`、`git show main:codex-agent/shim-routes.json`、本机已安装 Claude Code 2.1.286 二进制的静态字符串。两份 r1 review artifact 仅用于理解原 findings 与核对收口，不作为正确性证据。
- Excluded scope: 其它 review 报告；未改动的 skill 正文与逐行用法说明；`codex-agent/profiles/*`、`scripts/patch-codex-model-catalog.py`、`scripts/compose-codex-app-config.py`、`codex-auto-review-shim-service` 内部逻辑（仅按调用点核对）；假设性的未来平台/策略问题。
- Mutation boundary: 未改任何 source/test/docs/manifest/frozen diff；未派发子 Agent；未做 live install/sync、API/model/network 探测、进程/会话/凭据检查；未 commit/push/PR/merge/推进 gate。唯一仓库写入为本 artifact。临时证据位于 `/private/tmp`（`ep-r2-jqprobe`、`ep-r2-emptydefault`、`fresh-main-diff.patch`、`claude-strings.txt`），全部使用隔离 HOME 与 stub。
- Parallel review coverage: 无。任务明确禁止子 Agent 派发，全部 17 个路径由主 reviewer 亲自走读；无未覆盖的 manifest 文件。

## Findings

### 1-未修复-中-默认资源里的空字符串 URL 会让 Claude 以空 `ANTHROPIC_BASE_URL` 携带真实 key 启动且返回 0（r1 Finding 1 的失效模式经新“空值继承”规则复活）
- **入口/函数**: `agent-endpoint.py:load_endpoints()` → `_claude_agent_base_url()` → `_claude_agent_launch()`（即 `ds-flash_claude` 等 10 个启动函数，以及 `claude-agent-run --provider <id>`：`scripts/claude-agent-run:329` source 安装版 `agent-tools.zsh` 后调用 `<provider>_claude`）
- **文件(行号)**: `scripts/agent-endpoint.py:18`（`if not url: continue`，对 defaults 文档同样生效）、`:43`（`result = {provider: dict(runtimes) ...}` 原样复制默认空值）、`:54-58`（`endpoint()` 只对 KeyError 报错，空串正常返回）；`scripts/agent-tools.zsh:73-79`（helper 输出无非空校验）、`:148`/`:159`（`|| return 1` 只看退出码）、`:200`（`ANTHROPIC_BASE_URL: $base_url`）、`:224`（`command claude`）；同一数据路径的次生消费点 `scripts/sync-codex-providers.py:70`（`if args.local_base_url:` 对空串为假 → 静默跳过覆盖）
- **输入场景**: 维护者把 `config/endpoints.example.json` 中“只有一个 runtime 的 provider”写成空字符串而不是省略键。该文件已经存在这种 provider（`hy` 只有 `claude`，`config/endpoints.example.json:39-41`），因此把 `"codex": ""` 写进去是很自然的一步。用户侧无需任何操作，`~/.config/agent-tools/endpoints.json` 甚至可以完全不存在。
- **实际分支**: `validate_document(defaults)` 在 `:18` 对空串 `continue` → 校验通过；merge 在 `:43` 把空串当作有效默认值复制进 `result`；本地无覆盖时 `endpoint()` 在 `:57` 命中键并返回 `""`（不是 KeyError）；CLI `print("")` 且退出码 0；zsh 侧 `base_url="$(...)"` 得到空串、`|| return 1` 不触发；`_claude_agent_require_provider`（`:126-137`）对云端 provider 只检查 key 是否存在；jq 门通过后 `command claude --settings` 以 `ANTHROPIC_BASE_URL: ""` + `ANTHROPIC_AUTH_TOKEN=<真实 key>` 启动。
- **预期行为**: 解析结果为空必须 fail closed（与 r1 Finding 1 的裁决一致）：要么在 merge 时丢弃默认文档中的空值，使其退化为 `Missing endpoint: <provider>/<runtime>`；要么在 zsh 侧拒绝空 base_url。无论哪种，都不得带真实凭据启动并报告成功。
- **实际行为**: 启动器返回 0，Claude 被真实调用，settings JSON 中 `ANTHROPIC_BASE_URL` 为空串，第三方 provider 的真实 API key 作为 `ANTHROPIC_AUTH_TOKEN` 传入。
- **直接证据**（隔离 HOME + stub，全在 `/private/tmp/ep-r2-emptydefault`，未改仓库、未触网）：把 `scripts/agent-endpoint.py` 复制到探针 bin 目录，并把随附默认资源里的 `ds-flash.claude` 改成 `""`，PATH 指向该目录：
  - `_claude_agent_base_url ds-flash` → stdout 只有一个空行，`rc=0`
  - `ds-flash_claude -p ping` → `LAUNCH rc=0`，stub `claude` 被调用；stub 记录的 settings 解析结果为 `ANTHROPIC_BASE_URL = ''`、`ANTHROPIC_MODEL = deepseek-flash[1m]`
  - 同一契约缺口在 Codex 侧表现为另一种静默：`scripts/sync-codex-agent.sh:31` 取到的 `local_base_url` 为空时，`scripts/sync-codex-providers.py:70` 的 `if args.local_base_url:` 为假，注册表覆盖被整段跳过且不报错，仓库硬编码的 `http://127.0.0.1:8080/v1`（`codex-agent/model-providers.toml:37`）保留下来
  - 当前 `config/endpoints.example.json` 内没有空串字段，因此这不是 live bug，而是本轮新规则打开的回归缺口
- **影响**: 静默失效 + 凭据外发风险，正是 r1 已裁决为“高”的失效模式；触发点只是仓库侧一行 JSON，现有校验和测试都不会拒绝它，用户端没有任何信号。次生的 sync 侧表现是“覆盖被静默跳过”，同样无信号。
- **建议改法和验证点**:
  1. `load_endpoints()` 构造默认基线时丢弃空值：`result = {p: {rt: u for rt, u in r.items() if u} for p, r in defaults.items()}`，使空默认退化为 `endpoint()` 的 KeyError → `ValueError("Missing endpoint: ...")`（fail closed，消息不含 URL）。
  2. 在 `_claude_agent_base_url` 增加非空兜底，覆盖所有未来的空解析路径：先 `url="$(python3 "$helper" ...)" || return 1`，再 `[[ -n "$url" ]] || { print -u2 -- "endpoint URL 解析为空（检查默认资源或 endpoints.json）"; return 1; }`。
  3. 可选：`scripts/sync-codex-agent.sh:31` 之后断言 `[[ -n "$local_base_url" ]]`，让 local 侧显式失败而不是静默跳过覆盖。
  - 验证点：在隔离副本里把某个默认字段设为 `""`，断言 `_claude_agent_base_url` 返回非 0 且 claude stub 未被调用（可直接复用 `tests/test_install_endpoints.py:82-113` 的负向对照写法）；并断言 `--check` 仍为 0 而 `--provider X --runtime claude` 非 0，避免把“空默认”误判成整份配置损坏。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 中

### 2-未修复-低-新 fail-closed 护栏的正向对照依赖 `/usr/bin/jq`，宿主缺该文件时唯一证明“claude 不被调用”的测试会假失败
- **入口/函数**: `EndpointTests.test_claude_never_starts_when_helper_or_local_config_is_invalid`
- **文件(行号)**: `tests/test_install_endpoints.py:96`（`'PATH': f'{bins}:/usr/bin:/bin'`）、`:109-113`（healthy 对照断言 `returncode == 0` 且 marker 存在）；被依赖的真实门在 `scripts/agent-tools.zsh:161-164`（`command -v jq` 失败 → `jq 未安装` → `return 1`）
- **输入场景**: 在 jq 不位于 `/usr/bin` 的机器上运行该测试（例如只装了 Homebrew 的 `/opt/homebrew/bin/jq`，或不随系统提供 jq 的 macOS 版本 / Linux 环境）
- **实际分支**: 前两段负向断言（helper 缺失、`endpoints.json` 为 `{broken`）仍按预期通过；第三段 healthy 对照在 `scripts/agent-tools.zsh:161` 的 jq 门失败，启动器 `return 1`
- **预期行为**: 该测试已经把 `claude`（`:88-90`）和 `python3`（`:92`）做成 stub，jq 也应 stub 进 `bins`，让正向对照只检验“配置健康时确实会调用 claude”这一件事
- **实际行为**: `assertEqual(healthy.returncode, 0)` 与 `assertTrue(marker.exists())` 同时失败，报错指向 jq 缺失而非被测行为
- **直接证据**: 隔离复现（`/private/tmp/ep-r2-jqprobe`：stub `claude`/`python3`/helper/defaults + 假 HOME，未改仓库）：
  - PATH 含 `/usr/bin` 时：`rc=0`，`$HOME/claude-called` 生成
  - PATH 改为 `<probe>/bin:/bin`（jq 不可达）时：`rc=1`，stderr 恰为 `jq 未安装`，marker 未生成
  - 本机 `/usr/bin/jq` 确实存在（macOS 26.6.2；`pkgutil --file-info /usr/bin/jq` 无 receipt 归属，属基础系统文件），所以该测试在本机通过；而 `README.md:134` 把 jq 列为用户需自备的 PATH 依赖，从未承诺它位于 `/usr/bin`
  - 注意不能简单把 PATH 放宽为 `os.environ["PATH"]`（`:202` 的 InstallTests 那样）：在已 sync 的开发机上 `~/.local/bin/agent-endpoint.py` 会被真实解析到，反而破坏“helper 缺失”的负向对照
- **影响**: 仅测试面，但影响不小：本改动最重要的 fail-closed 护栏（唯一证明“配置坏时 claude 不被调用、配置好时会调用”的测试）会在部分宿主上假失败，容易被误判为修复回归，或被当成环境问题跳过。
- **建议改法和验证点**: 在 `:88-92` 旁增加一个 jq stub（`#!/bin/sh` + `printf '{}'` 即可，测试不校验 settings 内容，只需 `command -v jq` 命中），保持 PATH 仍为 `{bins}:/usr/bin:/bin`；验证点：临时把 jq 从该 PATH 移除（或在无 `/usr/bin/jq` 的环境）后测试仍通过，且三段断言（missing helper / broken config / healthy）语义不变。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 低

### 3-未修复-低-installer 一次性种入完整默认副本，使新部署的默认资源对主安装路径永久失效，且没有文档化的“重新继承默认值”流程
- **入口/函数**: `install.sh` 的一次性初始化 heredoc；`agent-endpoint.py:load_endpoints()` 的优先级规则
- **文件(行号)**: `install.sh:56-57`（把 `config/endpoints.example.json` 的完整字节写入 `~/.config/agent-tools/endpoints.json`）、`:62-64`（`O_EXCL` + `except FileExistsError: continue` → 后续安装保留原字节）；`scripts/agent-endpoint.py:44-47`（本地非空值总是覆盖默认）；`README.md:117` / `README.zh.md:113`（“安装器首次生成完整默认配置，后续安装保留原文件”）；`tests/test_install_endpoints.py:218`（断言第二次安装后 endpoints.json 字节完全不变）
- **输入场景**: 任何由 installer 建好的机器，在仓库之后修改 `config/endpoints.example.json`（本轮 fix delta 自己就改了 kimi 的 `claude` 默认值）后重装或重跑 sync
- **实际分支**: 用户文件里 10 个 provider 的每个字段都非空 → merge 在 `:44-47` 全部走本地分支 → 部署到 `~/.local/bin`（`scripts/sync-agent-tools.sh:17-18`）与 `~/.codex-agent/bin`（`scripts/sync-codex-agent.sh:93-94`）的 `agent-endpoints.defaults.json` 对这些用户永远不被读取
- **预期行为**: 既然本轮引入了“默认资源随程序部署 + 缺失字段继承默认”的机制，主安装路径应让未自定义的字段继续跟随项目默认；或至少文档化如何让单个字段重新继承默认值
- **实际行为**: 默认值更新到不了已安装用户。想吃回新默认只能删掉整个文件（连带丢失真实自定义，且 sync 不会重建它，见 `tests/test_install_endpoints.py:224-228`），或手动把对应字段改成 `""`；后者在 README 里只作为“继承规则”出现，没有作为升级流程说明。
- **直接证据**: `install.sh:57` 写入的是 example 的完整字节（不是 `{}`，也不是“仅自定义项”）；`install.sh:62-64` 保证重装不更新它；`scripts/agent-endpoint.py:44-47` 只在本地值缺失或为空时回落默认；`README.md:120` 明确 “Sync updates default resources and validates the merged URLs without creating or overwriting the user URL file”。三者叠加即“默认资源对 installer 用户不生效”。
- **影响**: 升级期静默陈旧：厂商 URL 变更后，installer 建好的机器仍指向旧地址，sync/reinstall 都不会纠正，也没有任何提示指向“你文件里的值是旧默认”。当前不存在陈旧默认值（本轮已把 example 与 `main` 的 launcher 表逐条核对一致，见 Verification Evidence），因此这是升级路径缺陷而非 live bug。
- **建议改法和验证点**: 最小改法是文档：在 `README.md:117` / `README.zh.md:113` 补一句“要重新继承某个更新后的项目默认值，把该字段设为 `""` 或删除该字段；删除整个文件会丢失全部自定义”。更彻底（可作为独立后续）：installer 只写入 `{}` 或仅写入与默认不同的项，让部署的默认资源保持权威，并加一条测试断言“修改 example 后，installer 建好的 HOME 能读到新默认值”。
- **修复风险（低/中/高）**: 低（文档方案）/ 中（改种入策略会影响“打开文件即见可编辑模板”的现有体验）
- **严重程度（低/中/高/严重）**: 低

## Original findings closure

首轮两份 review 的 findings 全部逐条核对收口。证据均来自本轮实读代码与实跑测试，不以原 artifact 的结论作为正确性证明。

`docs/reviews/local-endpoints-install-qwen-20261004.md`（9 条）：

1. Finding 1（高，空 `ANTHROPIC_BASE_URL` 静默启动 / `|| return 1` 是死代码）→ **已修复，残留见本轮 Finding 1**。`scripts/agent-tools.zsh:148` 单独声明 `local base_url`、`:159` 才赋值，命令替换的退出码因此不再被 `local` 掩盖；`:158` 把 `_agent_tools_prepare_credentials` 移到 endpoint 子进程之前，无关凭据先被 scrub；`tests/test_install_endpoints.py:82-113` 用 stub claude 证明 helper 缺失与 `{broken` 两种情况下 marker 不生成、healthy 时生成。本轮实跑通过。残留：默认文档里的空串仍能绕过该守卫。
2. Finding 2（中，唯一失败分支无日志 + 启动日志打印过期已解析上游 + 隐私）→ **已修复**。`codex-auto-review-shim:323-326` 在 503 前 `self._log(f"endpoint error: {exc}")`；`:479`/`:490` 对托管路由改打 `endpoint:<id>` 而非已解析 URL；`tests/test_install_endpoints.py:115-139` 断言 503、日志含 `endpoint error:`、`--routes` 输出含 `endpoint:ds-flash` 且不含 `secret-route.example`。可达异常消息逐条核对（`agent-endpoint.py:11/14/17/24/51/60`、`shim:86/90/103`）均不含 URL 值，符合 no-echo 策略。
3. Finding 3（中，原始异常逃逸、launchd `KeepAlive` 下 traceback 崩溃循环）→ **已修复**。`shim:85-86` 先 `is_file()` 检查再 `spec_from_file_location`，`:88-91` 把 `exec_module` 的 `OSError` 转成带可操作文案的 `ValueError ... from None`；`main()` `:465-468` 把 `load_routes()` 的 `(ValueError, OSError)` 转成 `SystemExit(str(exc))`。`load_routes()` 自身的 `SystemExit`（`:222/:230/:241`）不被该 except 捕获，仍是单行消息。测试断言 rc≠0 且 stderr 无 `Traceback`，本轮实跑通过。
4. Finding 4（中，`request_prefix` 与注册表 `base_url` path 双真源且配对测试不校验）→ **已按最小方案修复**。`tests/test_provider_registry.py:52` 新增 `assertEqual(routes[port]["request_prefix"], urlsplit(provider["base_url"]).path)`，覆盖全部非 `openai`/非 `local_llama` 的 profile 卡（8 条路由），本轮实跑通过。双真源本身仍在（见 Residual Risk），彻底方案（从注册表派生前缀）未做，与原 finding 的分档建议一致。
5. Finding 5（中，`load_module()` 在 3.12 已移除，导致整文件无法收集）→ **已修复**。`tests/test_install_endpoints.py:15-18` 改为 `SourceFileLoader` + `spec_from_loader` + `module_from_spec` + `exec_module`，与同目录其余测试一致；`rg -n 'load_module' tests/ scripts/ codex-agent/` → 0 命中；本机 Python 3.11.15 下模块正常导入、17 项测试全部执行。
6. Finding 6（中，`--local-base-url` 正则改写零覆盖 + 失败消息指向错误原因）→ **已修复**。`scripts/sync-codex-providers.py:70-83` 改为按行状态机改写，容忍表内注释与空行，`count != 1` 时消息为 `cannot replace local_llama base_url: expected one single-line setting in registry`；`tests/test_provider_registry.py:69-86` 覆盖注释容忍、二次运行字节幂等、注册表缺 `local_llama` 时 rc≠0 + 消息匹配 + base 文件字节不变。本轮实跑通过，mimo r1 的 Residual Risk（该路径无永久回归测试）随之关闭。
7. Finding 7（中，两份 README 的“恢复到另一台 Mac”章节与新依赖矛盾）→ **已修复**。`README.md:275` / `README.zh.md:266` 改为“先跑 `./scripts/sync-codex-agent.sh`；它也部署 URL helper 和默认资源；缺少本地 URL 文件时仍用默认地址，已有自定义文件保持原样”，并删除“先跑一次 installer 初始化 URL 文件”的旧要求（`README.md:120` / `README.zh.md:116`）。与 `scripts/sync-codex-agent.sh:29-31`、`:92-94` 的实际行为一致；`tests/test_install_endpoints.py:224-228` 证明删掉用户文件后直接 sync 成功且不重建该文件。
8. Finding 8（中，仓库结构与真源清单缺 5 个新文件、若干前置条件陈述过时）→ **已修复**。结构清单新增 `install.sh`、`config/endpoints.example.json`、`scripts/agent-endpoint.py`、`scripts/validate-skill.py`、`tests/test_install_endpoints.py`（`README.md:563-568`、`:583`；`README.zh.md:542-547`、`:562`），真源清单同步（`README.md:596-599`；`README.zh.md:575-578`）；前置条件更新为 URL 解析需要 python3 3.11+ 且 helper 需在 PATH（`README.md:135` / `README.zh.md:130`）、local 服务地址由 URL 文件决定并区分 `local.claude` 健康检查与 `local.codex` 请求（`README.md:140` / `README.zh.md:135`）。逐条与实际代码核对一致（`scripts/agent-tools.zsh:114-124`）。
9. Finding 9（低，硬编码 `$HOME/.local/bin/agent-endpoint.py`）→ **已修复**。`scripts/agent-tools.zsh:74-79` 改为 `command -v agent-endpoint.py` + 明确提示，与同文件 `compose-codex-app-config.py`（`:392-395`）的既有约定一致；`tests/test_install_endpoints.py:35-42` 用带空格的自定义目录 `custom tools/bin` 放 helper 与默认资源并置于 PATH 首位，断言解析成功。

`docs/reviews/local-endpoints-install-mimo-20261004.md`（3 条）：

1. Finding 1（中，helper 安装路径与解析路径不一致，自定义 `AGENT_RUN_BIN_DIR` 半可用）→ **已修复**。解析改为 PATH（`scripts/agent-tools.zsh:74-79`），默认资源同时部署到两个 helper 位置（`scripts/sync-agent-tools.sh:16-18` → `$agent_run_bin_dir`；`scripts/sync-codex-agent.sh:92-94` → `$target_root/bin`），且都用 `install -m 600 <tmp>` + `mv` 的原子替换；`agent-endpoint.py:30-32` 的 `with_name` 优先正好命中同目录资源，回退路径对 repo 布局仍成立（`parents[1]/config/endpoints.example.json`）。自定义 bin 目录（含空格）的切换测试已补。
2. Finding 2（低，隐私测试把路径里的 `private` 误判为泄密）→ **已修复**。`tests/test_install_endpoints.py:141-149` 改用唯一 sentinel `SENSITIVE_SENTINEL_7e61`，覆盖 userinfo、query、非 http scheme、非法 port 四种畸形 URL。本轮以 `TMPDIR=/private/tmp` 实跑通过（原假失败条件已消除）。
3. Finding 3（低，两份 README 仍把 local endpoint 写成固定地址）→ **已修复**。`README.md:140` / `README.zh.md:135`（前置要求）、`README.md:254` / `README.zh.md:245`（provider 表 local 行改为 user-configurable）、`README.md:337` / `README.zh.md:321`（local 直连 `local.codex`）三处双语一致，且与 `_local_agent_require_service`（`scripts/agent-tools.zsh:114-124`，`curl "${base_url%/}/health"`）和 `sync-codex-agent.sh:31`（local.codex 写注册表）的实际行为对应。

## Open Questions

- Claude Code 对 `ANTHROPIC_BASE_URL=""`（空串而非未设置）的最终行为未联网验证。本轮从本机已安装的 2.1.286 二进制中静态提取到打包 SDK 的 `buildURL`：`new URL(h + (h.endsWith("/") && n.startsWith("/") ? n.slice(1) : n))`，其中 `h` 为 baseURL；`h=""` 时该表达式得到 `new URL("/v1/messages")`，不是合法绝对 URL，因此更可能是客户端立即失败而非回落内置主机。两种结果都要求 fail closed，不改变本轮 Finding 1 的裁决，只影响对外描述措辞。
- `--local-base-url` 解析为空时，产品期望是显式报错还是沿用注册表内既有值？当前 `scripts/sync-codex-providers.py:70` 是静默跳过（Finding 1 的次生点），需要 owner 裁决语义。
- 两份部署的 `agent-endpoints.defaults.json`（`~/.local/bin` 与 `~/.codex-agent/bin`）是否需要一致性/版本校验？只跑 `sync-agent-tools.sh` 或只跑 `sync-codex-agent.sh` 时，两侧默认值会短暂不一致（Claude 侧新、shim 侧旧）。`install.sh:71-72` 顺序跑两者，installer 路径无此问题。

## Residual Risk

- 未触网、未调用任何真实模型或厂商端点：HTTP 转发实链路、真实 Responses/Anthropic 协议兼容性、launchd 实机服务生命周期、真实 `git clone/pull`、PyYAML wheel 安装均未验证；`tests/test_install_endpoints.py:152-228` 用 stub `git`/`uv`/`launchctl`/`claude`/`codex` 证明编排与用户文件保留，不证明真实网络与 launchd 行为。`codex debug models` 仅读取本地内置目录（隔离 `CODEX_HOME`），不构成模型探测。
- `request_prefix`（`codex-agent/shim-routes.json`）与注册表 `base_url` path（`codex-agent/model-providers.toml`）仍是同一事实的两处编码，现由 `tests/test_provider_registry.py:52` 的配对断言守护；漏改一处会被测试拦下，但双真源结构本身保留。
- 默认资源存在两份部署副本，由两个不同 sync 脚本各自维护（见 Open Questions 第 3 条），属结构性残留。
- `scripts/agent-endpoint.py:11-24` 的校验错误消息刻意不含 provider/runtime 定位（避免把用户文件里的键回显到日志），因此本地文件语法或字段错误只能得到一条统一提示，用户需自行检查 JSON。这是可辩护的隐私取舍（`endpoint():60` 的 `Missing endpoint` 只回显调用方传入的 id，不回显文件键，二者并不矛盾），但确实降低了可诊断性。
- `codex-auto-review-shim:348` 的 `UPSTREAM ERROR` 日志本轮未改动（`git diff main` 对该行 0 命中），其异常文本是否可能带出上游主机不在本轮结论范围内。
- 本机测试解释器为 Python 3.11.15；Finding 5 相关的 3.12+ 收集问题已从代码层消除，但未在 3.12 解释器上实跑验证。
- 本轮为增量收口 review：未重新审计未改动的 skill 正文、profile 卡、catalog 生成器与 app-config 组合器；对这些文件只按调用点做了必要追踪。

## Verification Evidence

- 冻结身份：17/17 manifest sha256 前后两次全部匹配；review 后新生成的 `git diff --no-ext-diff main` 与冻结 `diff.patch` sha256 相同（`22f96ebf902d62ab6b0c69d90865f7462030a46e4efead27a92b675a2653f44c`）。
- 独立测试（`TMPDIR=/private/tmp`，未做 live install/sync）：
  - `python3 -m unittest tests.test_provider_registry tests.test_install_endpoints.EndpointTests -v` → Ran 16 tests, OK（2.18s）
  - `python3 -m unittest tests.test_install_endpoints.InstallTests -v` → Ran 1 test, OK（5.93s；隔离 HOME `home with spaces`、stub git/uv/launchctl/claude/codex；`codex debug models` 在临时 `CODEX_HOME` 下输出一条 “Refusing to create helper binaries under temporary dir” 警告，不影响断言）
- Claude URL 等价性（`config/endpoints.example.json` 把 kimi 的 `claude` 从 `.../coding` 改成 `.../coding/`，同时 `endpoint()` 不再对 claude 做 `rstrip("/")`）：`git show main:scripts/agent-tools.zsh` 的 `_claude_agent_base_url` 表（第 73-85 行）与 example 的 10 个 `claude` 值逐条比对完全一致，kimi 在 `main` 上本来就是 `https://api.kimi.com/coding/`。因此该改动是恢复与 `main` 的等价，而不是行为变更。
- 尾斜杠安全性：从本机 Claude Code 2.1.286 二进制静态提取的打包 SDK `buildURL` 为 `new URL(h + (h.endsWith("/") && n.startsWith("/") ? n.slice(1) : n))`，baseURL 带尾斜杠时不会产生 `//v1/messages`。未发起任何网络请求。
- Codex 侧 URL 等价性：`main` 的 `shim-routes.json` 用厂商 origin + `upstream_url()` 拼接，新版用 `endpoint_id` 解析出的完整 base + `request_prefix` 剥离（`codex-auto-review-shim:96-105`）。8 条托管路由逐条核算最终 URL 相同（如 kimi：`https://api.kimi.com` + `/coding/v1/responses` == `https://api.kimi.com/coding/v1` + `/responses`）。显式 `upstream` 路由与单路由 env 模式（`:470-476`）保持旧语义，向后兼容旧路由文件。
- 两个隔离探针（均在 `/private/tmp`，未改仓库）：
  - `/private/tmp/ep-r2-jqprobe`：PATH 含 `/usr/bin` → `ds-flash_claude` rc=0 且 stub claude 被调用；PATH 去掉 `/usr/bin` → rc=1、stderr `jq 未安装`、stub 未被调用（Finding 2 的直接证据）。
  - `/private/tmp/ep-r2-emptydefault`：默认资源里 `ds-flash.claude` 设为 `""` → `_claude_agent_base_url` 输出空行且 rc=0；`ds-flash_claude -p ping` rc=0，stub claude 记录到 `ANTHROPIC_BASE_URL = ''`（Finding 1 的直接证据）。
- 其它静态核对：`rg -n 'load_module' tests/ scripts/ codex-agent/` → 0 命中；`scripts/sync-skills.sh:13` 确实调用 `validate-skills.sh`，故 `README.md:104` / `README.zh.md:100` 关于“手动 sync 自动复用私有校验环境”的表述与 `scripts/validate-skills.sh:15` 的候选顺序一致；`scripts/claude-agent-run:329` source 安装版 `agent-tools.zsh` 后调用 `<provider>_claude`，`skills/sub-agents/SKILL.md:96` 以裸名调用 runner，故 PATH 解析约定在子 Agent 派发路径上同样成立（仓库内无 `env -i`/PATH 清洗调用方）。
