# Hy / MiMo Flash probe contract fix

本次为 PR #70、`fix/shim-subagent-message-delivery` 上的有界 FIX；controller 接受的两个问题均属探针任务契约。仅修改既有 `../shim-subagent-delivery/native-probe.py` 的 parent prompt；不修改 transport、生产 helper、routes、catalog、模型或安全策略，也不改严格审计器。Kimi 的独立调查与用户已配置的 override 不在本次写入范围。

## 已核实的旧证据

- [Hy attempt-1 audit](evidence/hy/attempt-1/audit.json)：A1/A2、descriptor-backed A3 N/A、B 的 child-owned read/final、wire/lifecycle 均通过；父线程 rollout 第 12、19、26 行另有三个 `mcp__node_repl.js` 全局/RPC 探查，严格拒绝 `parent used non-collaboration tool`。
- [MiMo Flash attempt-1 audit](evidence/mimo-flash/attempt-1/audit.json)：A/B exact finals/read 存在，但父线程 rollout 第 38、51 行的 `followup_task` / `send_message` 返回空字符串后，第 55 行通过 Code Mode 调用不存在的 `tools.collaboration__send_message`，得到真实 TypeError；第 61 行重复原生 MESSAGE。严格拒绝 dispatch order/count。A2 后还缺少下一步前的显式 native wait。
- 实际 wire descriptors：Hy 是 `multi_agent_v1` namespace，提供 `spawn_agent`、`send_input`、`wait_agent(targets=...)`，没有独立 `send_message`；MiMo Flash 是原生 `collaboration` namespace，提供 `spawn_agent`、`followup_task`、`send_message`、`wait_agent(timeout_ms=...)`，与文件工具的 Code Mode host 分开。由实际 descriptors 判断 capability，不强制 catalog version。

## 指令修订

删除旧提示中的 “If collaboration is hosted in Code Mode, invoke its native functions through that host.”，明确以下契约：

1. 原生 `collaboration` / `multi_agent_v1` 是直接调用的工具 namespace，不是 MCP server 或 JS global；父线程禁止 `functions.exec`、`tools.collaboration__*`、Node/RPC、文件/shell、resource discovery 和任何无害探查。
2. completed `followup_task` / `send_message` 的空返回在没有显式错误时是成功派发；不得重发、换拼写或换 host。显式错误则停止并报告，不修复、不盲试。
3. 所有 continuation、MESSAGE、targeted wait 使用 spawn 实际返回的完整 canonical `task_name` / `agent_id`；不猜相对目标或 nickname，不覆盖 model/effort。
4. A1、A2、A3 consume 和 B 各自派发一次后，必须 native wait 并收到该 child 本次新 completed final，再进入下一步；timeout/mailbox update/旧 final 不算完成，可继续 wait 而不重复派发。A3 只发一个 MESSAGE，consume task 不含 token。
5. 保留全部 A/B/MESSAGE 条件、fresh child / 无继承 conversation、B 实际文件工具读取及父线程不得知道 fixture 内容；A3 N/A 只适用于实际 v1 descriptors 缺少独立 send_message。Code Mode 文件读取仅归 B child。

修订前工作树 probe SHA-256：`f14aee11f19d9998442355ce8b291e9d5bfc57954e84f9101120e017ae03ca13`。修订后：`4f5f65ac6b7b799ef08908b9169fa6065c6c7604f5c5b47c3e64804a1f8885d6`。两个 attempt-1 实际 launch 时 probe 是 `1014545686e189a423ed3ed27c805d2084a2c864288fcc4ad440a0243693b94c`；这些运行时版本不混同。

## 一次受影响重验声明及结果

在完成具体提示修改和 focused 检查后，已在当前任务声明 Hy/attempt-2、MiMo Flash/attempt-2 各一次受影响 native 重验，严格串行，先 Hy 后 MiMo Flash；本任务最多一个 profile，给独立 Kimi 调查保留另一并发槽。没有以相同任务盲重试到绿。此前所有 attempt-1 文件保留。

```bash
python3 docs/gateflow/shim-subagent-delivery/native-probe.py --profile hy --evidence-dir docs/gateflow/shim-subagent-all-providers/evidence/hy/attempt-2 --attempt 2
python3 docs/gateflow/shim-subagent-delivery/native-probe.py --profile mimo-flash --evidence-dir docs/gateflow/shim-subagent-all-providers/evidence/mimo-flash/attempt-2 --attempt 2
```

| Profile / attempt | 实际 model / provider / catalog mode | 请求 / elapsed / exit | 严格结果 |
| --- | --- | --- | --- |
| Hy / 1 | hy4 / hy / v1 direct high | 14 / 108.64s / 0 | 失败：三个父 Node 探查 |
| Hy / 2 | hy4 / hy / v1 direct high | 11，均 200 / 111.49s / 0 | **通过**：[audit.json](evidence/hy/attempt-2/audit.json) |
| MiMo Flash / 1 | mimo-v2.6-flash / mimo_flash / v2 Code Mode + Lite max | 17 / 144.13s / 0 | 失败：非原生调用、重复 MESSAGE |
| MiMo Flash / 2 | mimo-v2.6-flash / mimo_flash / v2 Code Mode + Lite max | 11，均 200 / 84.41s / 0 | **仍失败**：[audit.json](evidence/mimo-flash/attempt-2/audit.json)；未派发 B |

Hy/2 全部八项严格检查通过。A 的两个 distinct completed turn、B child 唯一实际 `exec_command` / `CommandExecution exit 0` / exact final 均成立；无父线程 Node/JS/file/shell 调用。A3 仍仅因实际 v1 descriptors 无独立 send_message 而 N/A，没有制造 v2 覆盖。

MiMo Flash/2 仅生成 parent 与 A 两个线程。父 rollout 中第 36、49、56 行分别为完整 `/root/delivery_a` 目标的 followup、唯一 MESSAGE、consume followup；对应第 39、52、59 行结果为空，均未重发或经 Code Mode 尝试。A 的三个新 completed finals 与 MESSAGE envelope/token 隔离通过，原先两个错误行为在本次没有重现。但只有 A1 后一次 native wait；A2、A3 consume 的 fresh final 分别已在第 46、66 行送达，未按提示额外调用 wait。随后 parent `task_complete.last_agent_message=null`、turn status completed / exit 0，**没有第二个 spawn、B 文件工具或 B final**。因此不能接受为完整 native pass；没有显式 native tool error，也没有最终解释消息可据以认定遗漏 B 的原因。

MiMo Flash/2 的严格失败项原样保存：缺少两个 distinct spawn、dispatch order/count、B prompt/read/final 均不满足。`wire_helper_and_exact_allowed_outbound_stages` 在最终要求 A/B 两个 child 均有实际 converted 请求时，因 B 缺失报 `'identity'`；这不是该项通过，也不能据此断言新的 transport defect。全部 11 次真实 HTTP 请求为 200，实际 Lite、原生 v2 descriptors 保留。**不再重跑，不改审计器或生产 helper 来取绿。** 后续缺失 B / 空终止原因交 controller 裁决。

两次 parent native event 时间（UTC）为 Hy `15:02:13–15:04:04`，MiMo Flash `15:04:35–15:05:58`，无本任务 profile 重叠。完整 argv、app-server settings、catalog/model/provider/effort、source hashes 分别见 [Hy launch](evidence/hy/attempt-2/launch.json)、[MiMo Flash launch](evidence/mimo-flash/attempt-2/launch.json)；两次 HEAD 均为 `901cea16928ef2db01ce774c99652f62fb3dca68`，probe 均为上述 `4f5f65…`，而非旧运行 source。driver 原生保存的 summary、wire、native-events、allowlisted rollout/supplement、stderr 以及复制的 candidate-transport.log 均位于各 attempt-2。source-snapshots 下新 probe gzip 已验证解压 SHA-256 与 launch 一致；未覆盖旧快照或失败 attempts。

## 验证与交接边界

- `py_compile`：probe 与未改 auditor 通过；cache 定向 `/tmp`。
- `python3 -m unittest discover -s tests -p test_shim_native_evidence.py`：11 tests passed，包含 driver route/prefix 与现有严格 audit mutation checks；未重跑无关全套或未受影响 vendor profiles。
- 本次使用既有 generic `audit_directory`，auditor 文件 SHA-256 固定为 `2c1b96f0263980a614148772982eb3a50b192cc42090938578d90f13a1715bf3`；生产 helper 固定为 `cd8e9f218c5a65d65bceff6ffac8b723c075913dad7ca08d999941ee34544dda`。
- 两个新 `audit.json` 均由未改的 `audit_directory` 写出，包含 auditor/input hashes，失败不隐藏。以旧 source snapshot 的 prompt assignment 反向替换本次 assignment 后，精确重建修订前 `f14aee…` 文件 hash，证明源文件只改 prompt。两份 attempt-1 全部文件、auditor、helper、control、implementation report 的本次前后 hashes 一致；两次新 launch 与旧 launch 的 model/provider/effort/catalog/effective endpoint 及非 probe/auditor source hashes 一致。`git diff --check` 通过。
- 未委派实现/修复、提交、push、部署、重启或向其他线程回报。native test 内部 A/B child 仅执行已授权探针。组合版本完整并行双 review、裁决与最终 closeout 由 controller 继续完成；本 handoff 不宣称九路全绿。
