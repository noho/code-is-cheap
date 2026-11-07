# Shim subagent delivery：九条 managed cloud routes 扩展计划

2026-11-07；gpt-6-sol / Codex-runtime plan delegate；只读调查及本计划写入，未再次委派。工作分支 `fix/shim-subagent-message-delivery`，HEAD `901cea16928ef2db01ce774c99652f62fb3dca68`，base `09337967910277785b82874326d7f49156c9395b`；沿用 open draft PR #70（身份由总控后续交付核对）。用户本次明确扩展目标，goal confirmation 已给出。当前 gate / next entry：**总控简单计划核对 → implementation / validation**；本计划不授权提前实现。

## 范围与已有证据

目标是在全部九条现有 managed cloud shim routes 显式启用已实现的 `agent_message_fix`，用各 profile 的实际模型、catalog 和工具行为验收原生子任务传递。保留默认关闭及 per-route opt-in；不把“所有第三方”解释为新增 route、统一 catalog 或新协议架构。`local` 使用 `local_llama:8080` 直连，无 managed shim route；OpenAI 订阅 profiles 不走 shim，均不在启用范围。

已完整读取前作 [plan](../shim-subagent-delivery/plan.md)、[implementation-validation](../shim-subagent-delivery/implementation-validation.md)、[review-adjudication](../shim-subagent-delivery/review-adjudication.md)、[controller-validation](../shim-subagent-delivery/controller-validation.json)，以及源 shim/routes、全部九个 profile、五份 catalog source 的相关字段、catalog generator、现有 native probe/audit 和相关测试。不重新调查已经证实的 DS 根因：0.167.0 实际 `agent_message` 中 `input_text` 与名为 `encrypted_content` 的明文任务经过标准 user message 适配后可见；不能据此声称解密或知道私有 gateway 内部实现。

本次只读检查结果：

- branch/HEAD 与交接一致；仅有三个既有 `docs/reviews/runner-handle-loss-20261023-*` untracked 文件，本轮不读取其内容、不修改、不纳入提交。
- `controller-validation.json` 的七个源码/README/probe/audit 文件 SHA-256 全部匹配；shim 为 `cd8e9f218c5a65d65bceff6ffac8b723c075913dad7ca08d999941ee34544dda`。执行现有 `audit-native-evidence.py`，两次保存的 DS 实测均通过：各 15 个 HTTP 请求、27 个含历史重放的转换项，同 child 三个不同 turn，以及新 child 的真实 fixture cat/output。
- 已安装 shim/routes 仍分别为 `7ae5d6d7dc86050b466d06cc63685eb1589d873cf730fa0ac3479dfed44d7cc7` / `afd1e15ca3a914993987382abaf148227ef6a97a796cdb73791b4787bea26bfe`，未激活 PR #70。
- 九份 installed cards 都等于仓库模板展开 `@HOME@` 的结果；对应 selected catalog 条目均唯一。本机 `codex-cli 0.167.0` 在临时空 home 用 `codex -c model_catalog_json=<installed-path> debug models` 解析九份 catalog 全部退出 0；未运行推理。该 parser 会把旧 `shell_command` / `default` 解析成 `unified_exec`，但不会补出省略的 `multi_agent_version`。
- 用现有 endpoint resolver 只读检查九个选中连接，配置均有效且 key 存在；九个 `127.0.0.1` 端口 TCP connect 均成功。没有模型请求、私有 URL/key 输出或修改。监听可用与配置存在不能证明上游授权、工具或任务成功。

## 必须逐 profile 保持的矩阵

下表的 provider 是 Codex registry ID，route 是 endpoint ID；logical model 来自 card/route，wire model 是本轮 resolver 选择的模型名（仍由 installed managed route 每请求快照拥有）。prefix 必须原样保留。

| Route / installed port | Provider ID | Logical model → 当前 wire model | Prefix | 实际 catalog / runtime 差异 | 既有兼容开关 |
| --- | --- | --- | --- | --- | --- |
| ds-flash / 8788 | deepseek | deepseek-flash → deepseek/deepseek-flash | /v1 | v2；非 Lite；max | agent_message_fix 已 true |
| glm / 8789 | glm | glm-5.3 → 同名 | /api/v1 | multi-agent 版本省略；非 Lite；max | 全 false |
| glm-flash / 8795 | glm_flash | glm-5.3-flash → 同名 | /api/v1 | 由官方 glm-5.3 派生身份；版本省略；非 Lite；max | 全 false |
| kimi / 8790 | kimi | k3 → kimi-k3 | /coding/v1 | 版本省略；非 Lite；max | 全 false |
| mimo / 8791 | mimo | mimo-v2.6-pro → 同名 | /v1 | v2；code_mode_only / Lite；max；node_repl_auto_review_required=true | json_fmt_fix=true |
| mimo-fast / 8794 | mimo_fast | mimo-v2.6-pro-ultraspeed → 同名 | /v1 | v2；code_mode_only / Lite；max；node_repl_auto_review_required=false | json_fmt_fix=true |
| mimo-flash / 8793 | mimo_flash | mimo-v2.6-flash → 同名 | /v1 | v2；code_mode_only / Lite；max；node_repl_auto_review_required=false | json_fmt_fix=true |
| qwen / 8792 | qwen | qwen3.8-max → 同名 | /compatible-mode/v1 | 版本省略；非 Lite；max；parallel tool calls=false | id_fix=true |
| hy / 8796 | hy | hy4 → 同名 | /v1 | 显式 v1；direct / 非 Lite；high | 全 false |

表中未列为 true 的 `id_fix/json_fmt_fix/drop_tools_item` 均为 false；所有 route 的 `drop_tools_item=false`，目前仅 DS 的 `agent_message_fix=true`。九个 selected 条目经 0.167.0 parser 的 shell 均为 `unified_exec`。前三类 source 的旧 shell 拼写、Qwen 的 `default` 不能被 probe 当成固定 shell 工具名。

生成边界：`scripts/patch-codex-model-catalog.py` 保留官方 source；本轮逐一比较八个 official-source selected entries 与 installed entries，只有 GLM Flash 的 slug/display_name/description 三项派生变化，其余逐字段一致。Hy 是 `hy_session_entry()` 显式构造 v1/direct 的独立条目。Guardian 是独立 bundled entry：三条 MiMo 保留 Code Mode/Lite，其余六条 cloud routes 保留既有 direct/non-Lite 适配。不修改这些生成逻辑、effort 或 catalog 元数据来让测试过关。MiMo source supported levels 未列 max、Qwen 未列 max 的既有差异仍保留；旧 status-only acceptance 或 synthetic runtime 通过不能替代本次 native 验收。

## 最小实现（一个 implementation / validation slice）

1. `codex-agent/shim-routes.json` 给其余八条 route 显式加 `agent_message_fix: true`；DS 保持 true。`load_routes` 的缺省 false、无 global inheritance、single-route env mode 默认关闭不变。正常路径原则上无需改 shim helper；如真实矩阵揭示当前适配的具体兼容缺陷，只修已证实且在目标内的缺陷，记录受影响面并重验。
2. 复用并参数化 `docs/gateflow/shim-subagent-delivery/native-probe.py` 与 `audit-native-evidence.py`，不复制九份、不建新 orchestration 系统。增加显式 profile/evidence 输入；从实际 card、registry、route 读取模型、provider、prefix、effort、catalog 和兼容 flags，不把 DS 常量换成另一组硬编码。保留旧 DS evidence 的读取/审计能力。探针新增的 profile 参数命名可用 `--profile`，审计可用 `--evidence-dir`；最终实际 argv 与输入哈希必须落盘。
3. 让 probe 提示模型使用实际 advertised native collaboration 和文件工具；让 audit 保留并识别真实工具形状。当前 probe/audit 只采 `function_call/function_call_output`，固定 v2 名称、`deepseek`、`exec_command` 和整份 egress hash，不能照搬到所有 profile。扩展 allowlist 至实际 `custom_tool_call/custom_tool_call_output`、Code Mode `exec` 的原始 input/result 及可关联的原生嵌套工具事件；独立审计其调用目标、参数、结果与顺序，不能仅做名称子串匹配或执行捕获的 JS。按本轮公开的工具 descriptor/事件审计，而非伪造调用。
4. 更新直接相关 deterministic tests、双语 README 的启用范围、该目录的 implementation-validation / evidence。预期生产变更只有 routes；源 shim 的改动须有矩阵实证必要性。catalog/profile/registry/endpoint 私有连接保持原样。未知 top-level 非目标 item（包括未定义的相似名称）照传；实际 `agent_message` 的未知 content 或非法形状仍整请求 sanitized 400，零 upstream send / 零正文 dump。不得加 `agent_message*` prefix heuristic、provider fallback、禁用 multi-agent 或吞掉工具项。

## Native probe 适配与验收

每个 profile 独立临时 cwd、唯一 fixture/markers、app-server、新 parent/children、随机候选 loopback port 和 evidence 目录。候选 handler 显式 upstream 为该行 installed loopback origin，例如 `http://127.0.0.1:8789`，**不配置 managed endpoint_id，也不剥离 prefix**；进程级 provider base URL 为候选 origin + 原 prefix，使 `/api/v1/responses`、`/coding/v1/responses`、`/compatible-mode/v1/responses` 等完整送入对应 installed route，再由 installed resolver 管凭据和 wire model。不能全转发 8788，也不能把 logical slug 预先换成私有 wire slug。

候选保留对应 route 的原有 id/json-format/drop flags 并开启 agent-message 适配；记录 helper ingress/post-agent-message 与最终 outbound 三个边界的结构/哈希。原 probe 的 outbound hash 等于 helper output 假设会被后续 Qwen ID、MiMo JSON format 转换破坏，必须改为分别核对允许的逐阶段差异，并证实实际发出的 body。离线 handler 测试证明两层链路不会误改模型/prefix/flags；native capture 不接管 managed credentials、不记录认证头、私有 URL 或全局 prompt。Lite header、`additional_tools`、custom 工具、reasoning.context 及非目标项保持其实际值；不能为了适配 audit 删除它们。

进程仅覆盖本次隔离所需的 base URL、临时 cwd、read-only/never、安全关闭 apps/plugins 等既有 probe 设置；模型、effort、catalog、上下文/compaction 从该 card 继承，记录确切 argv 与 parent/child 实际 model/provider/version。不要强制 `multi_agent_version=v2`、`tool_mode=direct`、关闭 Lite、Code Mode host 或 node review；保留 MiMo `node_repl_auto_review_required` 的差异。若 host、审批或沙箱让真实工具不可用，保留为 setup/tool blocker，不能绕过原策略。

**先按该 profile 的第一次真实请求 advertised descriptors 及实际事件确定 native 模式，随后完成同一次声明的任务。** GLM/GLM Flash/Kimi/Qwen 的省略值不能被写成“已验证 v2”；Hy 明确 v1。v2 使用原生 `spawn_agent`、同 handle `followup_task`、`send_message`；v1 使用实际暴露的等价 spawn / 同 child 继续输入能力（例如仅当真实 descriptor 提供时使用 `send_input`）。任务正文、child ID、完成事件是共同断言，工具名和 JSON 形状按实际模式审计。v1 若本来发送普通 message，零 `agent_message` 转换可以是正确行为，须如实记录“native v1 路径通过；未产生 v2 转换项”，不能注入 agent_message 补覆盖。若无必要的 native 能力，记录 blocker，不改 catalog 迁移版本。

所有九条的验收列相同，证据分开保存：

| 检查 | 必须观测到的事实 |
| --- | --- |
| 实际模型 | card 的 selected logical model/provider/effort/catalog；该 profile 独立 parent/child 归属；managed route 当前 selected wire model 名称。不得用同家族另一模型替代。 |
| A1 初始任务 | 模型生成的 native spawn，child 独立 final 严格等于本次 initial marker。 |
| A2 followup | 等 A1 完成，给 **同一 child** 原生继续任务；新的 turn/final 严格等于不同的 followup marker。两次普通 parent user turn 不算。 |
| A3 MESSAGE | 现有 v2 probe 已可行：向同 child 原生 send_message 给独立 token，再 followup 要求返回最新 MESSAGE token，followup 本身不含 token。v1 若真实 API 无独立 send_message，记录不适用及 descriptor 证据，不伪造等价覆盖；若有此能力则实测。 |
| B 文件读取 | 另 spawn 一个新 child；驱动生成不可猜测、无害唯一 fixture，任务只含路径，parent/child prompt 不含内容。child 真实 shell/Code Mode 工具定向读取；原始调用、child-owned 实际 output/exit 0、call/result 关联和 exact child final 均匹配 fixture。parent 不使用文件或 shell 工具。 |
| Wire / 生命周期 | 所有实际 agent_message 已无损转换，非目标项仅有既有 flags 允许的变化；v1 记录真实原形状。实际 HTTP 状态、完成/错误事件、native 退出码、所有请求/重试次数与 stderr 分类保留；结束后关 stdin，等待实际退出，关闭自建 listener。 |

Parent 自称成功、HTTP 200、runner/native 退出 0、synthetic SSE 均不算上述 native acceptance。Code Mode 的 B 必须关联真实 `exec` 调用到子线程工具执行和 output，不能只因为 JS 文本提到 cat 就判通过；必要时保留该调用相关的 allowlisted 原生事件。新证据只取本次新 thread IDs，不扫描或恢复旧业务 session。

**执行并发上限固定 2 个 profile**（每个 profile 内任务顺序执行）；建议 DS 证据核对后先各跑一个 direct/省略版本 profile 与一个 MiMo profile，再按同一上限完成其余 profile，不提前假定同族通用。每 profile 首次声明一轮，不以重跑覆盖失败；保留 attempt 编号、声明/实际 argv、版本与输入哈希、完整结果和原因。既有 native HTTP/guardian 重试单独计数并披露，不新增 probe 自动重试、切换模型或 provider。修复已证实缺陷后可声明受影响重验，保留修复前样本及版本关联。

DS 允许复用两次既有 real native A/B/MESSAGE 证据：本轮已核对七个哈希、0.167.0、DS catalog hash `58ca2d8599ccbbfb64733b30ee83acf78b424bcc7729f32815826677f2e2ceb8` 和当前 resolver 模型名，离线 audit 通过；原生 acceptance 的范围仍成立。实现者还须证明最终 DS helper/handler/route 行为未变，以及参数化后的 audit 对旧证据仍验证同样断言；旧记录没有的新增断言不能凭空补为通过。影响 DS 路径或证据适用性时重跑 DS。其余八个 profile 必须实际运行，三条 MiMo 共享 catalog hash 也不能共用一个模型的成功样本。

## Offline 验证与交付门槛

保留已有 71 项测试的契约覆盖，新增最少的路由/交互断言：九个且仅这九个 endpoint flag=true；任意未显式 route、全局 true 不继承、env 单路由仍默认 false；local/OpenAI 没有被纳入 route；非目标/未知 top-level 原样、已知项未知 content sanitized 400。用实际九条 route 数据核对 prefix/model mapping、managed key replacement 单快照、identity/gzip/deflate、普通 `read1` streaming / guardian 原身份和既有 retry 行为。MiMo `additional_tools` / custom-call input/output、Lite header、json_schema downgrade 与适配共存；Qwen message ID fix 与适配共存；未开启 drop 时工具项完整保留。为参数化 probe/audit 补少量已观测 direct / v1 / Code Mode 证据形状控制，防止 parent 代读、错 child、重复旧 final、token 泄漏和漏审 custom tool 获得 false pass。

实现后预期命令（新增测试按实际文件名记录）：

```bash
python3 -m unittest discover -s tests -p 'test_shim_subagent_delivery.py'
python3 -m unittest discover -s tests -p 'test_install_endpoints.py'
python3 -m unittest discover -s tests -p 'test_provider_registry.py'
python3 -m unittest discover -s tests -p 'test_shim_service.py'
python3 -m unittest discover -s tests -p 'test_model_catalog_generation.py'
python3 -m py_compile docs/gateflow/shim-subagent-delivery/native-probe.py docs/gateflow/shim-subagent-delivery/audit-native-evidence.py
git diff --check
```

Native 实现者以参数化后实际支持的命令逐 profile 调用 probe，再独立 audit 新 evidence；建议接口 `python3 docs/gateflow/shim-subagent-delivery/native-probe.py --profile <route>`。这不是当前已经存在或已执行的命令；最终 artifact 必须记录实际 argv、输出目录与验收矩阵，不能只贴模板。旧 `test_official_catalog_runtime.py` 的合成 SSE 可作离线协议参考，不能列为真实 provider 通过。

本扩展复用现成适配、逐 route opt-in 和现成 probe，无新公共契约、架构或状态机决策；**无需另行 broad planreview**，由总控核对本 bounded plan。若实证表明必须迁移 v1/catalog、改变工具架构或突破已确认边界，应携具体证据回总控裁决，不悄悄扩展本计划。实现完成后，总控按仓库要求组织 mimo-flash / ds-flash 独立并行 deepreview（ds-flash Claude 不可用时才记录原因后用既定 Codex backup），裁决并交 gpt-6-sol 修复及受影响复审；旧 DS review 不替代当前九路组合审核。提交/push/更新 draft PR #70 由总控后续处理，本 delegate 不执行。

## Blockers、风险与授权边界

- **计划阶段无已确认实现 blocker**；新八条 native 验收尚未执行，是下一 gate 必做工作，不能写成 all-provider success。配置、TCP 与 parser 检查已过，不保证模型权限/配额或工具可用。
- setup（EPERM、缺 host）、model/access（401/403/429、模型拒绝）、tool（native capability/沙箱/host 失败）、task（模型未按任务执行）、adapter defect（转换丢正文、误改 flags/prefix 等）分别保留证据。前四类不能自动归咎适配；实际兼容 defect 在范围内修复重验。不可用 profile 保持明确 blocker，由总控/endpoint owner 处理，不切 provider、不省略、不通过总矩阵。历史 Hy Plan 403 只说明当时连接，不能推断当前 installed Hy 失败或改用另一私有连接。
- 版本省略/v1、Code Mode/custom 证据适配和后续 flag 变化影响 outbound hash：**covered by this approved implementation slice**；owner 为实现 delegate，destination 为上述 probe/audit 与逐 profile 矩阵；未证实前不声称覆盖。
- 真正 ciphertext、未来 schema 的兼容性：**assigned to later work unit**，maintainer 按具体新事实处理；本次不解密、不加虚构类型前缀规则。私有网关内部归因精度也归 endpoint owner 后续调查，不阻挡当前边界适配。
- 旧失败/idle/unloaded 业务 child 的恢复：**assigned to later work unit**，原 parent 在明确 live 授权后决定原生 followup/new task；本次不修改或恢复原 session、业务文件、watchlist、scheduler ledger。
- Live sync/restart：**requiring explicit user decision**，owner 为用户/总控；本次无授权且不执行。最终 closeout 从含 approved changes 的 checkout 记录适用命令 `./scripts/sync-codex-agent.sh`，提醒同步；skills/runner 未改则不需要其他 sync 脚本。候选临时端口验证不能称作 deployed/live 成功。
- 不向 `01a1b57a-8e5d-76e1-934d-1847728240be` 做 technical callback/report；用户明确禁止 live sync 前回报该 thread。本任务也不向任何其他 thread/联系人发送消息；本计划和当前对话交付不构成外部联系授权。

本阶段仅创建本文件，未改生产实现、installed 配置/服务、业务或原始会话，未跑新 native matrix，未 commit/push/sync/restart。下一步是总控简单计划核对，然后由已指定的实现/验证 delegate 执行。
