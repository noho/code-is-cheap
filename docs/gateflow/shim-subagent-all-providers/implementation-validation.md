# 九条 managed cloud shim routes：implementation / validation

2026-11-07；gpt-6-sol Codex implementation delegate；分支 `fix/shim-subagent-message-delivery`，沿用 draft PR #70。模型运行 source HEAD 均为 `901cea16928ef2db01ce774c99652f62fb3dca68` 加各 attempt 落盘的 working-tree 哈希。**实现完成；原生严格验收为 6/9（含 DS 历史条件复用），不是九路全绿。** Kimi、MiMo Flash、Hy 各有保留的 task/conformance 阻塞，交总控裁决；无已证实的 shim helper 内容丢失缺陷。本 slice 未委派、提交、push、部署、重启或向原业务线程回报。

[本轮 control](control.md) 是扩展后的权威状态。前作 `shim-subagent-delivery/closeout.md`、review conclusions、controller snapshot hashes 仍是 901cea 时的 DS 历史记录，不作为本次九路组合版本的独立审核。

## 实现范围

- `codex-agent/shim-routes.json`：给另外八条既有 managed route 显式启用 `agent_message_fix=true`；DS 对象语义不变。`id_fix/json_fmt_fix/drop_tools_item`、port、model alias、endpoint ID、prefix 均保持原值；所有 route 的 drop 仍 false。无新增 route，env-only / 未显式配置 / 新 route 仍默认关闭；local/OpenAI 不走 managed shim。
- **生产 helper 未改动**，SHA-256 仍为 `cd8e9f218c5a65d65bceff6ffac8b723c075913dad7ca08d999941ee34544dda`。只处理实际 `agent_message`；相似名称、其他 native top-level items 原样通过，非法已知内容仍 sanitized 400，零 upstream send。
- 参数化原来的 `native-probe.py`、`audit-native-evidence.py`；没有复制九套脚本或改 catalog/tool 架构。参数为 `--profile`、`--evidence-dir`、`--attempt`。每次直接读取 card/registry/route/installed catalog，继承模型、effort、context/compaction 和原始工具策略，不覆盖 multi-agent version、Lite、Code Mode、node review。
- 双语 README 更新为九路显式 opt-in；focused route tests 与新增 `test_shim_native_evidence.py` 验证实际 v1/direct、v2/Code Mode 证据的审计边界。

## 原生验收矩阵

每行是本模型本次独立运行，没有使用同族模型代替。A1/A2 为同一 native child 的不同 completed turn；B 是另一个 child 的实际文件工具、子线程 CommandExecution exit 0、call/result span、exact output/final。v1 的 A3 N/A 仅来自本次实际 descriptors 缺少独立 send_message；不是泛化豁免。Kimi 未 spawn，所以不能宣称 A/B 通过。

| Route / provider | Logical → resolver wire model | Native / 工具 / effort | A1 / A2 | A3 | B | 严格结果 / evidence |
| --- | --- | --- | --- | --- | --- | --- |
| ds-flash / deepseek | deepseek-flash → deepseek/deepseek-flash | v2 / direct / max | 通过 / 通过 | 通过 | 通过 | **历史条件复用通过**；[reuse check](evidence/ds-reuse-check.json)、[原生历史审计](evidence/legacy-ds-audit.json)；不复制旧 captures |
| glm / glm | glm-5.3 → 同名 | 实际 v1 / direct / max | 通过 / 通过 | N/A | 通过 | **通过**；[attempt 2](evidence/glm/attempt-2/audit.json)；[attempt 1 失败保留](evidence/glm/attempt-1/summary.json) |
| glm-flash / glm_flash | glm-5.3-flash → 同名 | 实际 v1 / direct / max | 通过 / 通过 | N/A | 通过 | **通过**；[attempt 1](evidence/glm-flash/attempt-1/audit.json) |
| kimi / kimi | k3 → kimi-k3 | 实际 advertised v1 / direct / max | 未执行 / 未执行 | descriptor N/A | 未执行 | **阻塞：未调用原生协作**；[attempt 1](evidence/kimi/attempt-1/audit.json) |
| mimo / mimo | mimo-v2.6-pro → 同名 | v2 / Code Mode + Lite / max | 通过 / 通过 | 通过 | 通过 | **通过**；[attempt 2](evidence/mimo/attempt-2/audit.json)；[attempt 1 失败保留](evidence/mimo/attempt-1/summary.json) |
| mimo-fast / mimo_fast | mimo-v2.6-pro-ultraspeed → 同名 | v2 / Code Mode + Lite / max | 通过 / 通过 | 通过 | 通过 | **通过**；[attempt 1](evidence/mimo-fast/attempt-1/audit.json) |
| mimo-flash / mimo_flash | mimo-v2.6-flash → 同名 | v2 / Code Mode + Lite / max | 通过 / 通过 | 实际消费通过；流程偏离 | 通过 | **阻塞：重复 MESSAGE / 非原生错误调用**；[attempt 1](evidence/mimo-flash/attempt-1/audit.json) |
| qwen / qwen | qwen3.8-max → 同名 | 实际 v1 / direct / max | 通过 / 通过 | N/A | 通过 | **通过**；[attempt 1](evidence/qwen/attempt-1/audit.json) |
| hy / hy | hy4 → 同名 | 显式/实际 v1 / direct / high | 通过 / 通过 | N/A | 通过 | **阻塞：父线程额外 Node 探查**；[attempt 1](evidence/hy/attempt-1/audit.json) |

GLM/GLM Flash/Kimi/Qwen catalog 没有 `multi_agent_version`，本机 0.167.0 实际广告 `multi_agent_v1.spawn_agent/send_input/wait_agent`；不称作 v2 覆盖。上述 v1 实际请求均零 agent_message 转换，符合原生路径；没有注入 v2 数据制造覆盖。MiMo 三模型分别实测：转换数（含历史重放）为 27 / 27 / 32；第三个严格流程仍未通过。

Kimi 的每次请求均使用新的有效 TokenHub 连接：launch 的 `effective_endpoint.user_override_destination_equals_ds_flash=true`，wire model `kimi-k3`。没有修改、回滚或输出 private URL/key；[用户前置配置记录](local-endpoint-override.json) 保留。GET /models 的 404 没有被当成推理失败，本轮 Kimi 的 8 个实际 Responses 请求均 200。

## 全部 native attempts 与版本

[attempt-matrix.json](evidence/attempt-matrix.json) 包含全部 10 次声明执行；没有隐藏失败或成功后重试策略。并发从未超过 2 个 profile：GLM+MiMo 首轮，修复后两者重验，随后 Kimi / GLM Flash、MiMo Fast / Qwen、MiMo Flash / Hy 按空出的名额启动。各 profile 独立 OS-random candidate port、临时 cwd、随机 fixture/markers、app-server、parent/children。没有恢复旧会话。

| Profile / attempt | HTTP requests | 状态 | 秒 / native exit | 原因 |
| --- | --- | --- | --- | --- |
| glm / 1 | 30 | 全 503 | 30.14 / 0；parent failed | 探针 relay 错误剥离 prefix，见下文；无 child、无已证实 vendor inference |
| mimo / 1 | 30 | 全 503 | 29.86 / 0；parent failed | 同一探针 defect；无 child、无已证实 vendor inference |
| glm / 2 | 11 | 全 200 | 57.43 / 0 | 修复后严格通过 |
| mimo / 2 | 15 | 全 200 | 48.93 / 0 | 修复后严格通过；保留 on-request + auto_review |
| kimi / 1 | 8 | 全 200 | 54.30 / 0 | 模型任务失败，未 spawn |
| glm-flash / 1 | 11 | 全 200 | 66.60 / 0 | 严格通过 |
| mimo-fast / 1 | 15 | 全 200 | 36.59 / 0 | 严格通过 |
| qwen / 1 | 11 | 全 200 | 80.52 / 0 | 严格通过 |
| mimo-flash / 1 | 17 | 全 200 | 144.13 / 0 | 流程偏离；不以 exact finals 代替全过程验收 |
| hy / 1 | 14 | 全 200 | 108.64 / 0 | 流程偏离；不以 exit 0 代替验收 |

首轮 GLM/MiMo candidate 复制了 `request_prefix`，而 helper 的 `route_url` 即使没有 endpoint_id 也会按该字段剥离前缀，实际 outbound path 变成 `/responses`，被 installed route 拒绝 503。已修正 candidate builder，省略 endpoint_id 和 request_prefix 元数据，使真实 incoming `/api/v1/responses` 等完整进入对应 installed port。新增 driver regression 覆盖全部九条 prefix/port/flag。只对受此已证实探针 defect 影响的 GLM/MiMo 各声明重验一次；没有更换 model/provider。首轮各 30 次为 Codex 原有请求重试，wire 中逐次保留；不是 probe 重新启动 30 次。候选 guardian 的已有 retry 逻辑也未改变。

首轮 observer 还未记录 model-swap stage，现已补齐；当时没有 guardian swap，且失败轮不作为 acceptance。每次的 `summary.json` / `launch.json` 都保留**运行当时** source hashes（shim/routes/card/registry/installed catalog/probe/auditor）、实际 driver argv、完整 app-server argv/settings、version `codex-cli 0.167.0`。每份运行时 probe source 在 [source-snapshots](evidence/source-snapshots) 按 SHA-256 去重 gzip 保存，已逐一验证解压后的 hash 等于 launch 记录；不是九份脚本。后续 capture/audit 改进不冒称已在旧 run-time source 执行。

实际 driver 调用为下面各命令（首轮未重定向；后续 stdout/stderr 重定向 `/tmp/shim-<profile>-attempt-<n>.log`，其安全 transport 日志已复制至对应 evidence）：

```bash
python3 docs/gateflow/shim-subagent-delivery/native-probe.py --profile glm --evidence-dir docs/gateflow/shim-subagent-all-providers/evidence/glm/attempt-1 --attempt 1
python3 docs/gateflow/shim-subagent-delivery/native-probe.py --profile mimo --evidence-dir docs/gateflow/shim-subagent-all-providers/evidence/mimo/attempt-1 --attempt 1
python3 docs/gateflow/shim-subagent-delivery/native-probe.py --profile glm --evidence-dir docs/gateflow/shim-subagent-all-providers/evidence/glm/attempt-2 --attempt 2
python3 docs/gateflow/shim-subagent-delivery/native-probe.py --profile mimo --evidence-dir docs/gateflow/shim-subagent-all-providers/evidence/mimo/attempt-2 --attempt 2
python3 docs/gateflow/shim-subagent-delivery/native-probe.py --profile kimi --evidence-dir docs/gateflow/shim-subagent-all-providers/evidence/kimi/attempt-1 --attempt 1
python3 docs/gateflow/shim-subagent-delivery/native-probe.py --profile glm-flash --evidence-dir docs/gateflow/shim-subagent-all-providers/evidence/glm-flash/attempt-1 --attempt 1
python3 docs/gateflow/shim-subagent-delivery/native-probe.py --profile mimo-fast --evidence-dir docs/gateflow/shim-subagent-all-providers/evidence/mimo-fast/attempt-1 --attempt 1
python3 docs/gateflow/shim-subagent-delivery/native-probe.py --profile qwen --evidence-dir docs/gateflow/shim-subagent-all-providers/evidence/qwen/attempt-1 --attempt 1
python3 docs/gateflow/shim-subagent-delivery/native-probe.py --profile mimo-flash --evidence-dir docs/gateflow/shim-subagent-all-providers/evidence/mimo-flash/attempt-1 --attempt 1
python3 docs/gateflow/shim-subagent-delivery/native-probe.py --profile hy --evidence-dir docs/gateflow/shim-subagent-all-providers/evidence/hy/attempt-1 --attempt 1
```

这些实际执行使用已授权的 escalated local diagnostic 环境，避免 sandbox 阻止 app-server 的正常本地资源；native child 本身仍按所记录的 read-only / approval 策略运行。没有部署 installed 源码或服务。

## 证据和审计契约

每个 attempt 保留 `summary.json`、launch、wire、allowlisted native rollout、audit；已有 transport log 时一并保留。wire 独立记录 helper ingress → post-agent_message bytes hash、每个后续 model/ID/JSON/drop stage、实际发送给对应 installed loopback route 的 outbound bytes hash、真实 path/model/status。依据实际 handler 顺序构造精确 expected outbound，逐请求/线程关联，不再以 helper output hash 必须等于最终 outbound 为假设。当前成功模型任务没有触发 ID/JSON format 的非零后续修改；focused offline tests 单独覆盖它们与适配同时启用的真实 Handler 路径，不能声称 native inference 已触发了这些修改。

所有实际目标项逐内容段和 metadata 精确核对，其他 input / non-input fields 在 helper 边界保持精确相等；后续 stages 只准许确定的 model swap、`at_`→`msg_` ID 或 json_schema→json_object 路径和值变化。没有广泛忽略 reasoning/context、additional_tools 或其他字段。实际 Lite header 在三个 MiMo 的 wire 记录中为 true；drop 未打开，custom call/output 和 additional_tools 保留。

实际管理连接仍由 installed route 按自己的每请求 snapshot 持有 URL/key/wire-model；候选只观察发往该 installed route 的真实正文，不伪称观察了私有 gateway 内部请求。launch 记录本轮 resolver 的 wire model，原 helper 的单快照、auth replacement、URL join 与 streaming/guardian 契约由 focused Handler tests 验证；生产 helper 没有变化。

新 audit 采用观察到的两种 completion 形状：普通响应带 final_answer；Lite 实际 assistant message 没有 phase。后者必须与**本 child / 本 turn 的 task_complete.last_agent_message 精确一致**，且独立 turn IDs、dispatch、call/result、执行事件全部成立，绝非 final-only 放宽。Code Mode 输出不含 shell exit header，因此必须有实际 child-owned `item_completed.CommandExecution`，位于该 custom call/result 的原始行号 span 内，thread_id / turn_id / exact cat command / parsed read path / aggregated_output / exit_code=0 全部一致。审计从不执行 captured JS。

`native-rollout-supplement.json` 保存明确新 test IDs 的上述执行/协作 events、实际 model/provider/effort/approval/reviewer 和源 rollout hash。GLM、MiMo、Kimi 的 supplement 是在初版 allowlist 漏掉 nested item_completed 后，从其已完成的新 test rollouts 补取；没有重新推理、改写原捕获或读取业务线程。其他 profile 由当时 driver 自动写出 supplement。对 A3 的短名 target，只在实际 SubAgentActivity call ID 明确关联同一个 child ID 时接受；重复 MESSAGE / 多余调用依然失败。

最早失败轮在其自建临时 cwd 中生成了原始 request failure dumps。它们含不必要全局上下文，已仅保存文件名/hash/大小清单后移除，见对应 `omitted-global-dumps.json`；durable allowlisted wire/native trace 未删改。最终 probe 直接以 hash-only dump observer 避免此类上下文落盘。没有 credentials、private URLs、全局 prompt 或业务内容进入仓库 evidence。

历史 DS 默认 audit 的原断言保留为 legacy path，默认命令仍审计原来的两个 candidate-run。DS reuse check 同时证明 helper/handler hash、DS route 对象、catalog hash、selected wire model 不变。本轮新泛化断言不追溯声称旧 captures 具有原本没有的字段；旧 snapshot hash、review 结论都未更改。

## Offline checks

[offline-validation.json](evidence/offline-validation.json) 保存实际命令、结果和最终 source hashes。最终 **114 tests passed**：

| Command pattern (`python3 -m unittest discover -s tests -p …`) | Tests |
| --- | --- |
| test_shim_subagent_delivery.py | 13 |
| test_shim_native_evidence.py | 11 |
| test_install_endpoints.py | 38 |
| test_provider_registry.py | 11 |
| test_shim_service.py | 11 |
| test_model_catalog_generation.py | 30 |

另：两个 probe/audit 的 py_compile、默认历史 DS audit、git diff --check 均通过。catalog generator 未改；其测试是适用依赖验证，输出中的预期 invalid-enum rejection / no-compatible-template warnings 属测试控制，不是 vendor acceptance。没有执行合成 SSE 作为模型成功证据。

新增 route tests 覆盖九且仅九个 true、global true 不继承、真实 env-only 默认 off、全部 routes/四种已有编码回归、snapshot/key replacement、prefix、未知相似 top-level item、Lite/custom call/output/additional_tools、保留 flags、streaming 与 guardian。实际新增 all-route interaction loop 覆盖 identity/gzip/deflate；既有测试另含空编码。新 audit mutation tests 拒绝错 child、旧 completed turn 重放、父代读、token 泄漏、缺失/错属 native execution、custom result 错 call_id、outbound hash/path 改动，以及 Kimi final-only 假通过。

新增 env-only 测试在开发时失败两次，原因是测试误用显式 missing/empty routes 文件（生产按既有契约拒绝），后改为真正 absent default + empty SHIM_ROUTES；未修改生产 loader 来迁就测试。最终相关测试均通过；两次开发失败也记录在 offline-validation 中。

## Blockers / residual owners / 下一 gate

- **Kimi — task/model native tool visibility/use，owner 总控 + endpoint/model integration owner。** wire 实际广告 multi_agent_v1（含 spawn/send_input），模型却调用 11 次 MCP resource/template discovery（8 次 HTTP 模型请求承载），最终声称没有协作能力。没有 child、A/B 未覆盖。只能得出该次模型未使用广告能力，不能据此证明 gateway 内部剥离 namespace。未改 catalog、展平 namespace、切模型/endpoint 或盲重试。
- **MiMo Flash — task/tool conformance，owner 总控 + model/tool integration owner。** A1/A2/A3 exact completed finals 和 B actual Code Mode read 均存在；父线程在 A2 后未先 wait，就 send_message，随后执行 `tools.collaboration__send_message` 得到真实 TypeError，又重复原生 send_message。没有 token 泄漏进实际 consume followup，但全过程违反 once/in-sequence/native-only 条件，因此严格失败。未把重复发送隐藏为成功，也未改变 Code Mode host 或关 review。
- **Hy — parent discipline，owner 总控。** v1 A1/A2、独立 B child 读文件和 native exit 均成功；父线程额外三次调用 mcp__node_repl.js 探查全局/RPC 名称，违反 parent-only-native-collaboration 约束。其捕获没有 fixture 代读；audit 仍保守拒绝非协作父工具。不能为全绿而删除这项检查。
- **本轮 adapter defect：未发现。** 内容/source/transport 审计通过的样本没有显示生产 helper 需要修改。上述三行需总控决定后续有针对性的 task/protocol 诊断或独立 work unit；本 delegate 不自发迁移 catalog/API 或重试至成功。
- **组合版本独立 review：pending，owner 总控。** 必须按仓库 mimo-flash / ds-flash 独立并行 review、裁决、必要修复/受影响复审；前作 DS 审核不替代它。未创建本轮新 review conclusion。

## Live scope

这只是候选临时端口 + installed route 链接验证。Installed shim/routes 的 read-only hashes 仍为前作计划值，见 ds-reuse-check；没有 sync/restart。三个无关 runner-handle-loss untracked 文件未读取内容、未修改/纳入交付；原投资/业务会话、watchlist、scheduler 未操作。

总控最终 closeout 后提醒用户，从含已批准改动的 checkout、取得明确 live 授权后执行：

```bash
./scripts/sync-codex-agent.sh
```

本轮未改 skills、launchers/runners，不需另外两个 sync 脚本或 source ~/.zshrc。没有执行同步，也没有向用户禁止的原 parent thread 发送 technical callback。
