# Code Review

## Scope

- Mode: current changes
- Branch or PR: `fix/shim-subagent-message-delivery`
- Base: `main` = `0933796` (`Stop automatic reasoning repair on Codex resume (#69)`)
- Output file: `docs/reviews/code-review-20261107-213702-ds-flash.md`
- Included scope: 相对 base 的 4 个已修改文件 `codex-agent/bin/codex-auto-review-shim`、`codex-agent/shim-routes.json`、`README.md`、`README.zh.md`；untracked `tests/test_shim_subagent_delivery.py`；untracked `docs/gateflow/shim-subagent-delivery/` 下的 plan、implementation-validation、closeout、native-probe.py、audit-native-evidence.py、controller-transport-comparison.json、original-live-probe-evidence.json、baseline/setup-failure/candidate-run-1/candidate-run-2 evidence 与 sha256sums.txt。实际读取并核对了 shim adapter 全部改动、路由开关、focused tests、README 中英文说明及 evidence 的 wire/rollout/审计结构。
- Excluded scope: 无关的既有 untracked `docs/reviews/runner-handle-loss-20261023-*`；本并发审核产生的其它 review artifacts（包括审核期间新出现的 `docs/gateflow/shim-subagent-delivery/controller-validation.json`）未读取；用户私有业务、调度、watchlist 及仓库外原始文件未读取；live 8788 服务/网络未调用或修改（仅只读核对安装版 shim/routes hash）；生成的 `__pycache__`/cache 未纳入；私有网关内部实现不可见。
- 版本/完整性核对: 仓库 shim SHA-256 `cd8e9f218c5a65d65bceff6ffac8b723c075913dad7ca08d999941ee34544dda`；仓库 routes SHA-256 `8b04fec825d53d4c60fbbc80256f9d57cc8d3b1f8a91a645cbe83a62bd8ad48d`；测试文件 SHA-256 `d8dc53ebaa1bdb4bf1d485e1ef5a6dd9334e235d87aedfe8b81d764b07b19b40`。安装版 shim/routes 仍为 `7ae5d6d7...` / `afd1e15c...`，与 implementation-validation 声明一致，未被 live 部署覆盖。`git diff --check` 通过；evidence `sha256sums.txt` 全部通过；`audit-native-evidence.py` 两轮 capture 审计通过。
- Parallel review coverage: 无。本次为 controller 指定的独立 reviewer，未派发 subagent，未读取其它 reviewer 结论。

## Findings

### 1-未修复-低-original-live-probe-evidence.json 暴露用户私有业务目录路径与业务语境
- **入口/函数**: 证据文件提交/阅读入口（`docs/gateflow/shim-subagent-delivery/` untracked artifact，非生产代码）
- **文件(行号)**: `docs/gateflow/shim-subagent-delivery/original-live-probe-evidence.json:77`、`:140`（`:2` 另含用户原始 session 路径）
- **输入场景**: 分支 push 或 PR 将 untracked `docs/gateflow/shim-subagent-delivery/` 一并提交后，任何可读该仓库/PR 的人打开该证据文件。
- **实际分支**: 静态证据文件，无条件分支。
- **预期行为**: evidence 只保留失败事实（child 收到/询问任务而非执行），符合 plan “不复制研究上下文或业务文件内容”及本次用户明确的“不读取投资业务文件”边界；不应出现用户私有业务路径。
- **实际行为**: 两处 assistant 输出文本分别包含 `<private-workspace>` 和“[REDACTED: private project context]”等私有工作目录/业务语境。
- **直接证据**: 上述两行 JSON 的 `text` 字段；`git grep '[REDACTED: private directory token]'` 在 tracked 文件中无匹配，该内容为本次 untracked artifact 新引入。
- **影响**: 若仓库或 PR 被共享，会暴露用户私有业务工作目录与业务方向；不影响 adapter 代码正确性，但违反证据最小化和隐私边界，且与 evidence 的“sanitized/omitted”表述不一致。
- **建议改法和验证点**: 提交前将两处 assistant 输出中的私有路径/业务短语替换为 `<private-workspace>` 或泛化描述，保留“assistant 未获得具体任务”的失败证据；提交前运行 `git grep -n '[REDACTED: private directory token]' docs/gateflow` 并人工检查 untracked evidence。
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 低

## Open Questions

- 私有网关内部不可见，evidence 只能证明“原生 agent_message 进入 HTTP 请求但模型未执行，标准 message/input_text 可执行”，无法区分根因在顶层 `agent_message` 解析、嵌套 `encrypted_content` 还是网关其它内部步骤；这不阻止本次局部兼容修复，但不应宣称已定位网关内部具体丢弃函数。
- 单一路由 env mode 是否仍有实际部署使用？`main()` 在无 routes 文件时默认 `SHIM_UPSTREAM=https://api.deepseek.com`、`SHIM_TO=deepseek-flash`，但该 mode 没有 `agent_message_fix` 入口，原始任务丢失仍会发生；当前修复只在 routes 文件的 ds route 生效。若存在此类部署，需要在 routes 文件部署或新增 env 开关，不能仅依赖默认 single-route mode。
- 是否存在 `agent_message.encrypted_content` 真正存放不可读密文的 0.167.0+ 变体？现有观测样本均为明文；若未来 runtime 改变，adapter 会把密文当文本转发，不能恢复任务。

## Residual Risk

- **明文假设**: adapter 只把 `agent_message` 的 `encrypted_content` 字符串当文本提升为 `input_text`，未解密；真正的 opaque ciphertext 无法识别或恢复。README 已说明，但这仍是本修复的核心兼容性假设。
- **严格 400 的未来兼容性**: `set(part) != {"type", key}`、author/recipient 非空字符串、content 非空列表等严格校验，遇到未来 Codex 新增 content 字段/类型（例如 `annotations`、新 part type）会让整个请求 400。按设计要求“未知/非法变体不静默丢任务”，行为可见，但 Codex 升级后可能先失败而非降级；需要随 runtime schema 更新 adapter，或临时关闭该 route flag。
- **single-route env mode**: 无 routes 文件时 adapter 不启用；默认 DeepSeek 用户仍会遇到原问题。必须使用 `shim-routes.json`（ds-flash:8788）部署。
- **测试缺口**: focused suite 未覆盖 live 的“只有 encrypted_content、没有 header”任务、未来变体 400、single-route env mode、超大请求、以及 adapter 生成空 `input_text` 块时的上游接受度；这些不影响已审计的主路径，但属于 residual。
- **验证缺口（本次环境）**: 独立重跑 focused suite 时 10/11 通过；`test_actual_http_handler_framing_compression_and_sanitized_400` 在 `ThreadingHTTPServer` bind 处因本评审 sandbox 的本地端口限制报 `PermissionError: [Errno 1] Operation not permitted`，不是代码失败；该真实 socket 用例的通过记录复用 implementation-validation，本次未能独立复跑。未复跑 `test_install_endpoints.py`（38）、`test_provider_registry.py`（11）、`test_shim_service.py`（11）或全量 suite；未重跑 live API probe，未触碰 live 8788。仓库未发现 CI workflow，测试为手工执行。
- **证据边界**: 两轮 candidate 使用真实 0.167.0 app-server、真实 DeepSeek 和实际 native 工具调用；A 为 `spawn_agent` → 同一 child `followup_task`（`LIVE_FOLLOWUP_OK`）→ `send_message` token 被后续 `followup_task` 消费（`LIVE_MESSAGE_OK_*`）；B child 实际执行 `exec_command cat <fixture>`，exit 0 且 final 等于 driver 生成的唯一 fixture；wire 中 ingress 为 native `agent_message`、egress 为标准 `message(role=user,input_text[])`，非目标 item/非 input 字段一致，实际 upstream body hash 已核对。baseline 失败、setup sandbox failure 均保留；没有用 synthetic SSE 或 parent 自述代替验收。候选 listener 是独立临时端口、forward 到已安装 loopback 8788，不是 live 8788 部署。
- **未覆盖的 native 场景**: 只验证了新 parent/child；未证明已存在、idle/unloaded 或 old failed child 能自动恢复；已有 native history 会在后续请求中被 adapter 标准化，但旧失败任务仍需要显式 native followup/new task，不能承诺自动修复。
- **性能**: route flag 开启时，每个 ds 请求都会多做一次完整 JSON parse（即使没有 `agent_message`），handler 另外还有 guardian 判定和 model swap 的 parse；对超长 history 是可静态预见的额外 CPU/延迟，但与模型推理相比未测出 material impact，暂不列为 finding。
- **部署**: 代码未 live 部署；安装版 shim/routes hash 仍为原值。后续用户授权后从 approved checkout 运行 `./scripts/sync-codex-agent.sh`；新版 adapter 对后续请求生效，不天然要求重开 Agent session，但不能承诺恢复旧失败任务。
- **证据隐私**: 见 Finding 1；`original-live-probe-evidence.json` 两处 assistant 输出含用户私有业务目录/业务语境，建议提交前脱敏。

## Remediation note — 2026-11-07 (fix delegate; independent rereview pending)

Controller accepted Finding 1. The fix delegate redacted the private project path/context and business-specific task options in `/entries/2/payload/content/0/text` and `/entries/4/payload/content/0/text` of `original-live-probe-evidence.json` (original source lines 15 and 24). The remaining text still asks for a concrete task rather than returning `LIVE_PROBE_OK`. The evidence now explicitly marks those excerpts as redacted and records each original decoded text's UTF-8 SHA-256 and reason. Original source identity, source line numbers, source-file SHA-256 and exact harmless task bodies are unchanged. Private quotes/search tokens in this report were also replaced with redaction markers; the finding above retains its original review semantics and historical unresolved status.

See [redaction-fix.md](../gateflow/shim-subagent-delivery/redaction-fix.md) for the actual changes, limited static checks and resulting hashes, including a pre-existing `closeout.md` manifest mismatch left unchanged. This note records remediation by the fix delegate; it does **not** assert independent review of the fix. Controller's two narrowly scoped independent rereviews remain pending. No original session logs/business files were opened, and no inference, probe, tests, commit, push or live deployment was performed for this change.
