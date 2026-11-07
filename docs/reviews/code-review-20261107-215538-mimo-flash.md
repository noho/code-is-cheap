# Code Review

## Scope

- Mode: current changes
- Branch: `fix/shim-subagent-message-delivery`（相对 base 无提交；全部改动为 unstaged/untracked 工作区状态）
- Base: `main` = `09337967910277785b82874326d7f49156c9395b`
- Output file: `docs/reviews/code-review-20261107-215538-mimo-flash.md`
- Included scope:
  - `codex-agent/bin/codex-auto-review-shim`（`fix_agent_messages`、路由开关加载、handler 挂点）
  - `codex-agent/shim-routes.json`（仅 8788/`ds-flash` 新增 `agent_message_fix: true`）
  - `tests/test_shim_subagent_delivery.py`（新增 11 个测试）
  - `README.md` / `README.zh.md`（ds-flash 网关修复列与新增说明段）
  - `docs/gateflow/shim-subagent-delivery/`：`plan.md`、`implementation-validation.md`、`closeout.md`、`native-probe.py`、`audit-native-evidence.py`、`controller-transport-comparison.json`、`original-live-probe-evidence.json`、`evidence/**`（baseline、setup-failure、candidate-run-1/2、sha256sums）
- Excluded scope: `docs/reviews/runner-handle-loss-20261023-*`（与本任务无关的既有 untracked 文件，未读取）；本并发 review 的其他 reviewer artifact（未读取）；仓库外原始会话、业务/投资/scheduler 文件
- Parallel review coverage: 无（本 reviewer 独立完成，未派发 subagent）
- 本 reviewer 独立复验（未重跑 native probe / 未触碰 live 网络与已安装服务）：
  - `python3 -m unittest discover -s tests -p 'test_shim_subagent_delivery.py'` → 11 tests OK
  - `test_install_endpoints.py` → 38 OK、`test_provider_registry.py` → 11 OK、`test_shim_service.py` → 11 OK（沙箱内本地 bind 被 EPERM 拦截一次，按沙箱规则放开 local binding 后全部通过；失败为环境性，非代码缺陷）
  - `python3 docs/gateflow/shim-subagent-delivery/audit-native-evidence.py` → 两次 candidate run 全部断言通过，与 `evidence/native-audit.json` 一致
  - `evidence/sha256sums.txt` → 23/23 校验通过
  - `git diff --check` → 0；shim/probe/audit `py_compile` → 通过
  - 候选 shim SHA-256 = `cd8e9f218c5a65d65bceff6ffac8b723c075913dad7ca08d999941ee34544dda`，与 `implementation-validation.md` 记录一致
  - 已安装 `~/.codex-agent/bin/codex-auto-review-shim` = `7ae5d6d7…`、`~/.codex-agent/shim-routes.json` = `afd1e15c…`，与改动前原值一致 → 代码确实未 live 部署

## Findings

### 1-未修复-[低]-未知 `agent_message*` 族顶层 item 静默透传，README 的“未知 agent 内容 400”保证不覆盖该情形

- **入口/函数**: `Handler._handle` → `fix_agent_messages`（按路由开关调用）
- **文件(行号)**: `codex-agent/bin/codex-auto-review-shim:209`（`item.get("type") != "agent_message"` 即原样 append 透传）、`:410-419`（仅 `n>0` 才在 `how` 记录 `+agentmsg`，`n==0` 无任何日志信号）；对照承诺 `README.md:524`、`README.zh.md:482`
- **输入场景**: 同一请求 `input` 中出现 type 以 `agent_message` 开头但不等于 `agent_message` 的顶层 item（如未来 Codex 升级产生的 `agent_message_v2` 变体），可与已知 `agent_message` 混合
- **实际分支**: 走 `shim:209-211` 的非目标分支 `converted.append(item)` 原样转发；若全请求无已知 type，`fix_agent_messages` 返回 `(body, 0)`，`how` 保持 `none`，日志与普通请求无差别
- **预期行为**: 按本 change 已确立的契约（“don't silently lose unknown variants”；README 声称 “Unknown or invalid agent content fails with a sanitized HTTP 400 rather than forwarding a partial task”），未知 agent 族内容应整请求显式失败（仅含位置的诊断）或至少留下可见信号，而不是原样交给已证实会以 HTTP 200 静默丢弃非标准 agent 项的网关
- **实际行为**: 本 reviewer 实际执行场景：① `agent_message` + `agent_message_v2` 混合请求仅转换前者（`count=1`），v2 项仍随请求发往上游；② 仅含 v2 的请求完全 no-op（`count=0`、`how=none`、无日志）；③ 对照组——已知 `agent_message` 内的未知 content variant 正确 `raise ValueError("Invalid agent_message at input[0]")`，证明 400 契约只覆盖 item 内部 content，不覆盖顶层类型族
- **直接证据**: `shim:209` 透传条件与 `shim:410-419` 的 `n>0` 才记录；`controller-transport-comparison.json` 证实原生 `agent_message` 到网关 HTTP 200 但任务被忽略——即非标准 agent 项在该网关上是被静默丢弃的已证实现象；上述 scenario 输出为本 reviewer 现场执行结果
- **影响**: Codex item 类型一旦演进，回到本次修复的原始症状：任务静默丢失、HTTP 200、无 400、无日志差异；README 保证对读者形成过度承诺，排障时会被误导为“未知变体一定会 400”
- **建议改法和验证点**: 对 `type.startswith("agent_message")` 但 `!= "agent_message"` 的顶层 item 复用同一“整请求 400（仅位置）”路径，或至少 `_log` 一条告警；补一条混合请求测试；或将 README 两句收窄为“`agent_message` 内未知/非法 content variant 会 400”。验证：构造 v2 混合请求断言 400 或日志信号
- **修复风险（低）**: 仅触及未知变体分支；已知 `agent_message` 路径与默认关闭路由完全不变
- **严重程度（低）**: 锁定 Codex 0.167.0 的 schema（`agent_message` 为正式类型）与两轮实测 wire 中未出现变体，当前版本无实际错误；属契约完整性/文档承诺与前向兼容缺口，非现行正确性缺陷

## Open Questions

- 顶层 `agent_message_fix` 键被 `load_routes`（`shim:312`）显式忽略，不继承 doc 级默认，与 `id_fix`/`json_fmt_fix`/`drop_tools_item` 的继承语义不一致；且被 `test_route_flag_explicit_default_off_ds_only` 固化为有意行为（与 plan“只对 ds-flash 开启”一致）。当前配置无实际错误，但后续维护者若按其他开关的习惯在顶层置该键会静默不生效——是否需要在 `load_routes` 对该顶层键告警或显式拒绝？

## Residual Risk

- **未做 live 部署验证**：按 AGENTS.md，live 同步/重启需用户显式授权；已安装 shim/routes 哈希确认未变，安装服务加载新代码后的行为（含 launchd 重启路径）留待授权后的 closeout
- **网关内部不可观测**：`encrypted_content` 槽为明文的兼容假设无法在网关侧证实；若未来运行时放入真实密文，任务将以“模型看不懂正文”方式失败（响亮失败，非静默损坏），README/implementation-validation 已如实披露
- **版本漂移可用性代价**：严格 shape 白名单（author/recipient 非空字符串、content 恰为已知两键、无多余字段）意味着 Codex 升级引入新字段时 ds 路由所有含该历史项的请求整体 400——这是“宁可失败可见”契约的既定取舍，但属硬故障面
- **证据复用而非重跑**：native A/B（2 次通过 + 1 次失败 baseline + 1 次沙箱 setup 失败均保留）与网关对照为已有可归属证据；本 reviewer 只独立重跑了离线测试、证据审计与哈希校验，未重跑 native probe、未访问 live 8788/上游网络。candidate run 证据未在运行时嵌入当次 shim 哈希（仅 closeout 记录最终哈希且与当前 checkout 一致；run 2 的 400 顺序调整不改变转换输出格式）
- **probe 拓扑 ≠ 生产拓扑**：candidate 临时 shim（无 endpoint_id）→ 已安装 8788 → 网关；probe 中 guardian 模型替换发生在安装版之前，与生产直连顺序不同。guardian 判定/缓冲重试在生产路径仅由单测覆盖（`test_guardian_original_identity_buffer_retry_and_adapter`）
- **role 语义**：所有 agent 消息（含子→父 FINAL_ANSWER 回传）统一 `role=user`，靠信封文本携带来源；在本路由两轮实测可接受，未在其他模型/路由验证（开关默认关闭，不外溢）
- **测试面**：failure path、压缩、凭据、guardian、真实 socket 400 消毒均有覆盖；未覆盖并发请求下的行为（handler 无共享可变状态，风险低）
