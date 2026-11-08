# MiMoFlash declared A/B scenario validation

2026-11-07；PR #70 / `fix/shim-subagent-message-delivery`；有界 FIX / validation delegate。

**声明式短场景结果：A 严格失败，B 严格通过，A+B 整体失败。** 本次各运行一次，先 A 后 B，无重试。没有将旧 all/2 的 A 改标为新 scenario A，也没有用旧 all/1 的 B 拼出通过结论。未发现新的生产 adapter 内容丢失证据。

## 实现和审计边界

只修改既有 `../shim-subagent-delivery/native-probe.py`、`audit-native-evidence.py`、`tests/test_shim_native_evidence.py`，新增本报告及 `evidence/mimo-flash/scenario-{a,b}-attempt-1`。没有修改生产 helper、routes、catalog、private endpoint、control、旧 captures 或旧报告。没有委派实现/修复、commit、push、部署、重启或 callback message。探针内部 native child 是本次明确授权的被测对象。

- Probe 新增 `--scenario all|a|b`，默认 `all` 保留原 compound prompt、执行方式和旧审计结果。`a` 只要求 A1、同 child A2 和 descriptor 适用的 A3；`b` 只要求一个 fresh child 实际读取随机 fixture。每次独立 parent、临时 cwd、child、随机 marker/fixture、app-server 和 candidate port。
- 保留直接 native namespace、blank void dispatch 成功、canonical target、显式 wait / fresh final 的提示。父线程不得使用 FS/JS/shell/resource discovery，B child 仍按真实 Code Mode 工具读取。未更改 catalog、model、effort、Lite 或 node review 策略。
- Auditor CLI 同样支持 `--scenario all|a|b`，默认 `all`；单份短场景须明确选择匹配 scenario。审计将 summary 的声明与真实 `driver_argv`、独立 `launch.json` 比较；缺 launch、旧 all 改标 A、argv/launch/请求场景不一致均拒绝。
- 每场景独立验证 child 数量、fresh spawn 结果、dispatch 顺序/count、canonical 同 child recipient、无重复 MESSAGE、每个 native dispatch 的 parent/turn/child 归属及 call/result 行号 span、actual model/provider/effort/policy、Code Mode/Lite 和完整 transport stages。A 要求独立 completed turn、exact markers、child 无工具、token 不进入 consume task；advertised `send_message` 不得当作 A3 N/A。B 要求随机内容不在 parent/task prompt、唯一 child file call/result、同 child/turn 的 CommandExecution、exit 0、exact output/final。始终不执行 captured JS。
- `--aggregate-evidence-dir` 可重复传入；整体通过必须覆盖 A+B、每份严格通过、snapshot/settings 匹配且 parent/thread 不重复。单独 A 或 B 不代表整体绿；跳过的 case 不写成通过。本次 aggregate 明确为 `{"a": false, "b": true}`，错误为 `missing required A+B coverage`。

## 实际执行和证据

Source HEAD：`901cea16928ef2db01ce774c99652f62fb3dca68` 加各 launch 的 working-tree hashes。两个 native driver 外层退出均为 0；退出 0 不替代严格验收。

```bash
python3 docs/gateflow/shim-subagent-delivery/native-probe.py --profile mimo-flash --evidence-dir docs/gateflow/shim-subagent-all-providers/evidence/mimo-flash/scenario-a-attempt-1 --attempt 1 --scenario a > docs/gateflow/shim-subagent-all-providers/evidence/mimo-flash/scenario-a-attempt-1/driver.log 2>&1
python3 docs/gateflow/shim-subagent-delivery/native-probe.py --profile mimo-flash --evidence-dir docs/gateflow/shim-subagent-all-providers/evidence/mimo-flash/scenario-b-attempt-1 --attempt 1 --scenario b > docs/gateflow/shim-subagent-all-providers/evidence/mimo-flash/scenario-b-attempt-1/driver.log 2>&1
```

两次均为已授权的本机 escalated diagnostic，native parent/child 保持 read-only / approval `never`、reviewer `auto_review`。每次 native 最多一个在途，未运行 Kimi 或任何未受影响 profile。

| 场景 | Parent / child | Native parent 时间 UTC | 请求 / elapsed | 严格结果 |
| --- | --- | --- | --- | --- |
| A / 1 | `01a1b69c-d26f-72a2-83cc-47ea05d6b51c` / `01a1b69c-f506-7fe0-b93b-7180f2f3b084` | 15:24:53–15:25:39 | 5，全部 200 / 46.90s | **失败**；[audit](evidence/mimo-flash/scenario-a-attempt-1/audit.json) |
| B / 1 | `01a1b69d-eb48-7c11-adc2-262f2bbaadd1` / `01a1b69e-0a9b-7bd2-b5de-08a18ed89ba1` | 15:26:05–15:26:40 | 5，全部 200 / 35.37s | **通过**；[audit](evidence/mimo-flash/scenario-b-attempt-1/audit.json) |

A1 fresh child 完成 exact initial final。父 rollout 第 32 行随后生成 **无 namespace** 的 top-level `wait_agent({})`，第 34 行真实返回 `unsupported call: wait_agent`；模型依指令报告错误并停止。实际 advertised 工具是 `collaboration.wait_agent`。没有 A2 followup 或 A3 MESSAGE/consume，不能接受 A，也不能声称 wait 成功；没有盲试其他 host、重发或恢复会话。此为具体 native 调用符合性阻塞，后续 owner 为 controller / model-tool integration；本 delegate 不再重跑。

B 父线程只有直接 `collaboration.spawn_agent` 和 `collaboration.wait_agent(timeout_ms=30000)`。child 使用唯一实际 Code Mode file call，CommandExecution 在该 custom call/result 的原始行号 span 内（execution 第 18 行），同 child / turn、exact `cat <fixture>`、parsed read path、exit 0、exact aggregated output 与唯一 completed final 一致。fixture 未泄漏到 parent 或 child task prompt。B 的全部九项严格检查通过。

两份 [A launch](evidence/mimo-flash/scenario-a-attempt-1/launch.json) / [B launch](evidence/mimo-flash/scenario-b-attempt-1/launch.json) 的 profile、model、provider、effort、catalog、shim、route、registry、source HEAD/hashes、effective wire model 完全相同；只允许独立 candidate base URL 等运行标识不同。实际为 `mimo-v2.6-flash` / `mimo_flash` / `max`，native v2，Code Mode only + Lite，Codex `0.167.0`。没有 force v2 或降低 node policy。

## Hashes、审计演进与旧失败保留

| Source | SHA-256 |
| --- | --- |
| Probe（两次 launch / 最终相同） | `cb21acef8005a9744bb57aadc263e290c7d88dd0a06106a2066f9f776b6cef42` |
| Auditor（两次 launch） | `1b2d47852afa6ee0b489dcad72da8105aea0631297dc86e911856c915a761653` |
| Auditor（最终离线审计） | `54329420f48692f26d97512f6a8cca365307b81db3a9c06f22dc69d3a185c3c5` |
| Focused tests（最终） | `99f56efeed08c47b1b0a387b864946c872ffdc847a09ceb59745549a53aab536` |
| 生产 helper（未修改） | `cd8e9f218c5a65d65bceff6ffac8b723c075913dad7ca08d999941ee34544dda` |
| Routes（未修改） | `28fabd9da79ff35f7c0d9be8e160f607715cf817c9533091c75fc21b06991d88` |
| Installed MiMoFlash catalog（未修改） | `b0d169e7a5b287453cb6abd00f59d01ecde10225375c5032a523650048c18955` |

两次 launch 之间没有改 probe/auditor。每个新 evidence 目录内保存运行时 probe gzip 和 launch 时 auditor gzip，均已解压验证内容 hash 与文件名、launch 一致。两次 inference 退出后仅继续加强**离线审计**：无 namespace / error / timeout-only / stale wait 不能标为成功，短场景必须具备全部 required task/final；另加入 auditor CLI 的显式 scenario mismatch 拒绝。没有改写原始 summary、launch、wire、native rollout/supplement，也没有再次推理。

每份 `audit-at-launch-auditor.json` 保留首次离线审计：A 已整体失败，但 wait 子项当时因只比较时间被误标通过；最终 auditor 将其严格拒绝。B 首次和最终都通过。最终 `audit.json`、[aggregate audit](evidence/mimo-flash/scenario-b-attempt-1/aggregate-a-b-audit.json) 都带实际 auditor/input hashes，不冒称最终 auditor 是 inference launch 版本。

[preservation.json](evidence/mimo-flash/scenario-a-attempt-1/preservation.json) 记录 114 个既有文件的前后 SHA-256，**变化列表为空**，包含旧九路 attempts、旧 implementation/probe-conformance/control 和生产 helper/routes/registry。默认 all 回归逐项比对原有 checks 与 passed：旧 MiMoFlash all/1、all/2 仍失败；Hy/2 仍严格通过，其他旧结果也完全一致。旧 all/1 的 A3 内容消费子项保持原通过，重复 MESSAGE 仍由旧 dispatch 检查拒绝；没有为了报告形状统一而重写旧判定或旧文件。

## Focused 验证与未完成事项

[offline-validation.json](evidence/mimo-flash/scenario-a-attempt-1/offline-validation.json) 保存最终实际命令、退出码、输出及 hashes：

```bash
python3 -m unittest discover -s tests -p test_shim_native_evidence.py
python3 -m py_compile docs/gateflow/shim-subagent-delivery/audit-native-evidence.py docs/gateflow/shim-subagent-delivery/native-probe.py
python3 docs/gateflow/shim-subagent-delivery/audit-native-evidence.py
git diff --check
```

**24 tests passed**；py_compile、默认 legacy DS 两个 run 审计、diff check 均通过。测试包含历史 all 逐 check 回归、v1/direct 与 v2/Code Mode 短场景离线反例，以及实际新 A 错误不得贡献 coverage、实际 B 不得独自满足 A+B。错误 recipient、token leak、父代 read、重复 MESSAGE/completion、缺 execution、错 call association、篡改 scenario/argv/launch、wait namespace/error/timeout/stale final、缺 B 和 aggregate snapshot mismatch 均有意义明确的拒绝检查；离线切片只在内存/临时目录构造，不当作 native acceptance。

开发期间一次 21-test run 有 1 failure + 1 error：新增 duplicate-MESSAGE 子断言意外改变旧 all/1 的 A3 子结果，以及历史 glob 误包含另一工作单元的 Kimi namespace diagnostic。已恢复 all 旧子结果并限定原九个 profile；后续 21、24 tests 均通过。两次 native 与所有失败审计都保留，没有失败后重跑。

最终 native A 审计 exit 1、B exit 0、A+B aggregate exit 1。**阻塞为 A 的有效 native continuation/MESSAGE 尚未覆盖**；B 已完成本轮独立严格覆盖。组合版本的双独立代码审核、Kimi namespace 工作及最终 closeout 仍由 controller 完成，本报告不宣称全绿，不执行 live 同步。
