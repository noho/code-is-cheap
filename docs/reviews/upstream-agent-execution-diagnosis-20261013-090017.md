# 五次 gpt-6-sol / Codex Agent 上游技术诊断

记录时间：2026-10-13 09:00:17 +08:00。范围：诊断，不实施工程。基线：`991eb26c082e006da80474ff85efc4cfeb1116c0`；报告分支：`docs/upstream-execution-diagnosis-20261013`。

## 结论

**确认一项当前 collector 的恢复消息识别缺口：第 10 次的两条原生重连通知不在现有匹配范围内。** 仓库与当前安装版本字节一致；在具备有效后续 final/terminal 的离线合成事件流中，两者仍返回 `runner_exit_code=1 / rejected / errors=2 / warnings=0`。所以不能把它解释成仅历史版本未同步，也不能说当前 collector 已支持该案文案。服务端请求处理错误确实由 runtime 报告过，但其服务/网络根因未知。

**第 13 次没有展示 Seatbelt 禁读失效。** 候选属于按时序暂不读内容的获准输入，query 得到 `kernel_denies_read=false` 且未尝试内容读取是预期；另一个固定 deny-list 保护的是其他材料。将候选暂不读解释为候选应永久物理 deny，是任务语义误读。现有 helper 没有识别业务阶段或动态解除 deny 的功能。

第 9 次有直接可见的自行脚本过滤错误；第 11 次有直接可见且同次恢复的 Python SyntaxError。第 10、15 次的业务覆盖遗漏不在本报告裁决范围内，也没有证据可归因于 runner 丢输出。五案均不能因为 runtime 退出 0 或 canary 匹配而判定原任务完成。

**尚未确认工具输出丢失、runtime 上下文异常或隔离泄露；最小包也不足以排除这些现象。** 特别是 excerpt 的主动截短不能充当原始工具输出截断证据。以下分别标注证据层次及未知项。

## 范围与证据

业务仓库只读了指定目录中的三份文件：

- `/Users/leo/workspace/portfolio-manager-v2/orch/jobs/20261011-TSM-01/upstream-agent-execution-check-20261013/request.md`
- 同目录 `cases.json`：五案终态、任务相关句子、父级边界统计及解释。
- 同目录 `native-excerpts.json`：12 个脱敏定点事件。

没有读取原完整日志、业务 workflow、角色报告、schema、来源库、私有 canary；没有重派任何 Agent，没有启动原 runner 或 wrapper，没有改 portfolio-manager-v2 的文件或计数。技术检查仅阅读本仓库及已安装 runner/collector/helper，执行无网络、无模型调用的离线 collector 控制。使用了 sub-agents 技能的结果/隔离契约及 OpenAI Docs 的原生事件格式说明。

证据层次：

1. **原生摘录**：可核对其中展示的命令、实际 exit 和输出；未展示部分不能推断。摘录中携带的原日志/事件 hash 是回源定位标识，本轮没有读取原日志验证这些 hash。
2. **包内摘要**：`cases.json` 的边界统计、终态及 `current_controller_reason_not_upstream_verdict` 是调用方提供的事实/解释，后者不当作已确认上游根因。
3. **当前源码与安装文件**：本轮实际读取并计算 hash。
4. **离线控制**：使用两条精确 error 事件，其他 start/final/terminal 为明确合成的有效结构；不是历史整轮重放，不含原 canary/artifact 检查。

[离线控制记录](upstream-agent-execution-diagnosis-20261013-090017-offline.json) 保存输入 hash、两种 collector 的各五项控制结果。

## 各案分类

包内五案均为 `agent_status=completed / terminal=turn.completed / runtime_exit=0 / canary=match`。这只是执行及机械检查状态；当前 collector 的 `result_status` 始终为 `not_assessed`。

| 次数 | runner / validation；errors/anomalies/warnings | 能支持的技术分类 | 限制或未知 |
| --- | --- | --- | --- |
| 9 | 0 / needs_review；0/2/0 | 自行脚本过滤键错误。原日志第 51 行 `item_26` 的命令排除 `stdout/canary/CANARY`，但输出对象实际保留 `command/aggregated_output`，旧 canary 事件因此被打印。命令 exit=0，是逻辑过滤错，不是 collector 当前 canary 失败。 | 主动停止来自包内解释；未展示 final 原文。未裁决旧事件读取授权和业务停点，也没有证据称 wrapper 自动泄露当前 deny 材料。 |
| 10 | 1 / rejected；2/4/0 | 原日志第 135、136 行是两种重试序号的服务器错误重连通知；当前 collector 不识别该文案，离线复核确认仍致命。runtime 服务错误与 collector 分类缺口分开。 | 完整恢复证明帧和选定机械检查结果未展示；精确历史 adapter hash 未提供。业务选择器 AND 条件漏行仅由父级解释报告，本包的截短命令不能独立确认选择器细节。 |
| 11 | 0 / needs_review；0/3/0 | 第 116 行 `item_59` 执行 `build-stop-report.py`，exit=1，Python 报 U+FF1A SyntaxError；第 120 行 `item_61` 再执行同路径 exit=0，输出 `professional_complete=false / candidate_content_read=false / independent_source_sealed=false`。普通脚本装配错误已同次恢复；未完状态被如实记录。 | 不能仅凭错误箭头确定具体引号/字符串拼接失误；其他 anomalies 未展示。没有展示强制 abort、上下文重置或 runner 提前终止证据。 |
| 13 | 0 / needs_review；0/3/0 | 第 14 行 `item_6` exit=0、stderr 空、`denied=[]`；阶段数为 690+12+625+14+13=1354。第 39 行 `item_19` 展示候选 `read_attempted=false / kernel_denies_read=false`。query-only 与固定物理 deny 被混淆的解释符合现有语义。 | 1340 项 read1 成功和全部 14 候选均未读来自包内统计；截短输出未逐项展示。停止时的 Agent 原文未提供；固定 deny 清单及本次 wrapper 验证事件未在包中，不独立宣称其全部通过。 |
| 15 | 0 / needs_review；0/3/0 | 第 128 行 `item_66` 源稿修正脚本 exit=0，报告 `candidate_content_read=false` 并输出源文件 hash；第 133 行 `item_69` 候选读取脚本 exit=0，真实工具事件中有候选解析输出。没有此处传输或权限失败证据。 | 封存后读取的完整证据链及 1381 必读可读由包内摘要报告；原生摘录仅直接展示修正先于读取，不含完整封存事件。业务漏记保留给原验收，不回裁、不归因于上下文故障。 |

## 第 10 次：当前终态如何产生

涉及文件：

- [scripts/agent-run-result.py:49](/Users/leo/workspace/code-is-cheap/scripts/agent-run-result.py:49)：`recognized_codex_connection_notice` 仅全匹配 `Reconnecting... [1-5]/5 (stream disconnected before completion: stream closed before response.completed)`，且事件只能含 `type/message`。
- [scripts/agent-run-result.py:262](/Users/leo/workspace/code-is-cheap/scripts/agent-run-result.py:262)：未识别的顶层 `error` 直接进入 errors，不进入待证明恢复队列。
- [scripts/agent-run-result.py:309](/Users/leo/workspace/code-is-cheap/scripts/agent-run-result.py:309)：已识别通知还须满足单一有效 thread/turn 起始、规定顺序、后续有效 final、唯一成功 terminal、原生与收尾退出均 0、其他机械检查无 errors 才降为 warnings。startup anomaly 可保留，普通工具异常仍可导致 needs_review。
- [scripts/agent-run-result.py:506](/Users/leo/workspace/code-is-cheap/scripts/agent-run-result.py:506)：errors 使 validation rejected，并在原退出均 0 时给 runner_exit_code=1。`agent_status=completed` 与 `rejected` 可同时出现，分别描述 runtime terminal 与机械验收，不是成功结论。
- [scripts/codex-agent-run:539](/Users/leo/workspace/code-is-cheap/scripts/codex-agent-run:539)：传入实际 runtime 及**收集前** run_exit；最后采用 collector 非零码。离线复核传 `--runner-exit-code 0`，不能把历史汇总的最终 runner1 倒灌为收集前退出码。

本案通知的冒号后内容是：

```text
An error occurred while processing your request. You can retry your request, or contact us through our help center at help.openai.com if the error persists. Please include the request ID <UUID> in your message.
```

因此即便随后充分恢复，现规则仍将第 135、136 行保持为 errors。已有提交 `e3f7723`（#52，2026-10-11）也是仅上述 stream-closed 文案；`17ef441`（#54，2026-10-12）增加 startup 诊断恢复证明，没有扩展服务器错误文案。**当前覆盖不足已确定；当次具体用哪个历史安装版本仍未知。** 安装文件 mtime 不能独立证明历史执行版本。

当前仓库/安装一致性（2026-10-13 实测 SHA-256）：

| 文件 | 仓库 `scripts/` 与 `/Users/leo/.local/bin/` 共同 hash |
| --- | --- |
| agent-run-result.py | `ea836b684381420045b064c7ba865ac2b1cf6fa5501b308d0379661253df7301` |
| codex-agent-run | `45baef1f77019a09c2c7d92567de8e9447eea5f8708cea838f2cf89daf954f01` |
| agent-sandbox | `2fc5c03e7ed069e032860c6e0c4f71be9b39bb702bcf9d08bd9d97298bd23e04` |

离线控制，两种 collector 结果完全相同，runtime/precollection exit 均设 0：

| 事件流 | collector exit / validation | errors/anomalies/warnings |
| --- | --- | --- |
| 两条第 10 次精确 error + 有效后续 final/terminal | 1 / rejected | 2/0/0 |
| 已识别 stream-closed 通知 + 有效后续 final/terminal | 0 / passed | 0/0/1 |
| 已识别通知 + 普通失败工具事件 + 有效后续 final/terminal | 0 / needs_review | 0/1/1 |
| 两条第 10 次 error，缺失后续 final/terminal | 1 / rejected | 4/0/0 |
| 未知 error + 有效后续 final/terminal | 1 / rejected | 1/0/0 |

最小复现命令如下。只读取脱敏包和 collector，临时目录只含合成事件，无 Agent 或 wrapper 启动：

```bash
python3 - <<'PY'
import json, subprocess, tempfile
from pathlib import Path
package = Path('/Users/leo/workspace/portfolio-manager-v2/orch/jobs/20261011-TSM-01/upstream-agent-execution-check-20261013/native-excerpts.json')
data = json.loads(package.read_text())
notices = [json.loads(e['native_event']) for e in data['events']
           if e['attempt'] == 10 and e['event_type'] == 'error']
events = [{'type': 'thread.started', 'thread_id': 'diagnostic-synthetic'},
          {'type': 'turn.started'}, *notices,
          {'type': 'item.completed', 'item': {'id': 'final',
           'type': 'agent_message', 'text': 'Synthetic; business not assessed.'}},
          {'type': 'turn.completed', 'usage': {'input_tokens': 1, 'output_tokens': 1}}]
with tempfile.TemporaryDirectory(prefix='collector-diagnostic-') as tmp:
    output, stderr = Path(tmp)/'output.jsonl', Path(tmp)/'stderr.log'
    output.write_text(''.join(json.dumps(e)+'\n' for e in events))
    stderr.write_text('')
    for adapter in ['/Users/leo/workspace/code-is-cheap/scripts/agent-run-result.py',
                    '/Users/leo/.local/bin/agent-run-result.py']:
        result = subprocess.run(['python3', adapter, '--runtime', 'codex',
            '--provider', 'gpt-6-sol', '--output', str(output), '--stderr', str(stderr),
            '--exit-code', '0', '--runner-exit-code', '0'], capture_output=True, text=True)
        report = json.loads(result.stdout)
        print(adapter, result.returncode, {k: report[k] for k in
              ['terminal', 'runner_exit_code', 'validation_status', 'diagnostic_counts']})
PY
```

**最小建议，未实施：** 后续若授权修复，只扩展精确原生服务器重试文案的识别，保留现有结构、顺序、最终答复、退出码和所选检查的恢复证明；不要把所有 `Reconnecting`、所有服务器 error 或 runtime0 泛化为 warning。补此文案的恢复/未恢复/未知错误离线控制。若历史完整证据满足这些门槛，两条错误才可降为 warnings；其他 4 条 anomalies 和业务遗漏继续独立保留，不能因此验收原任务。

## 第 13 次：query-only 与物理 deny

[scripts/agent-sandbox:514](/Users/leo/workspace/code-is-cheap/scripts/agent-sandbox:514) 的 `kernel_denies_read(path)` 对**调用进程**执行 `sandbox_check(getpid(), "file-read-data", SANDBOX_FILTER_PATH, path)`：返回 1 → True，0 → False，其他值抛错。它不打开文件内容，不评价 Source-first 是否完成；False 仅表示当前 Seatbelt 查询未拒绝，并不保证文件存在或 Unix 权限等其他条件允许实际读取。

[scripts/agent-sandbox:553](/Users/leo/workspace/code-is-cheap/scripts/agent-sandbox:553) 在 runner 启动前对固定 deny 清单逐项核对实际拒读并检查允许 probe。技能高级参考也明确：名单外没有读取白名单，封装不推断业务角色、阶段或未知副本，策略固定且不支持动态输入。候选的 query-only 是任务中的读取时序约束，不是 wrapper 的阶段权限。

第 13 次任务已写“candidate-after-source 只 query 不读内容”；但没有像第 15 次明确补上“kernel false 是预期、不需永久 deny 候选”。结合父级记录的误停，可支持**本案交接措辞有澄清空间**，不能据此证明工具接口错误或确认 Agent 为什么误读。本包未展示其停报原文。

最小建议：复用第 15 次已有区分句，明确真正 deny 清单出现 kernel false 或实际可读才是边界告警；候选 kernel false 且 `read_attempted=false` 属于预期。保持既有 deny、query-only 及 Source-first 时序；不增加授权、不把候选改为永久 deny、不添加动态解除机制。1340 次 read1 或候选权限查询均不能替代专业任务完成。

第 9 次的最小建议是对获准技术对象输出采用明确字段白名单，并按实际 schema 排除旧 canary 事件及其 command/output，不依赖另一 runtime 的 `stdout` 键；先在脱敏对象上验证。无需重派原任务或放宽边界。

## 输出、上下文与仍缺的精确证据

当前 runner 把原 runtime stdout/stderr 直接写 retained logs 后才调用 collector。collector 只限制**汇总展示**：final 12000 字符、各诊断最多 20 条/每条 2000 字符；它不回写或截短原 JSONL。[OpenAI Docs：Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode#make-output-machine-readable) 只证实 `--json` 输出 JSONL，含 thread/turn/item/error 事件；没有保证本案工具输出无截断，也没有将后续 turn.completed 定义为业务成功。

`native-excerpts.json` 的 `command_excerpt_truncated/output_excerpt_truncated` 是本技术包的摘录标记。不能把这些标记解释为 runtime 截断，更不能反推模型没看到某内容。五案 counts 未超过展示条数上限，但包没有完整 anomalies、final 长度或原工具结果，仍不能排除单条汇总截短、命令主动限长、runtime 工具输出限长、未送达的结果或上下文压缩。

如要继续缩小未知，只需以下定点字段/事件；本轮不索取也不读取整个项目：

| 要闭合的问题 | 最小追加资料 |
| --- | --- |
| 第 10 次当次能否严格证明恢复 | 从该案 `output.jsonl` 给 `thread.started`、`turn.started`、turn 前 startup 诊断（若有）、135/136 后最后 `item.completed` 的 agent_message、全部 terminal 的行号与原生键集合；thread/item ID 可一致脱敏，final 可给类型、长度、非空性和 hash。另给终态后非空事件的 type/行号及 JSON 解析异常计数；无需业务 final 正文。 |
| 历史版本与机械检查 | 当次实际执行的 codex-agent-run/adapter/helper 路径与 SHA-256（有留存才给）；collector 的 runtime/precollection exit 参数；汇总 `errors/anomalies/warnings` 的 stream、line、message（去业务内容）、`diagnostics_truncated`、canary 状态及 artifact 状态/类型（不给 token/内容）。当前 mtime 不替代当次 hash。 |
| 第 13 次的误停与真正 deny | 只给导致停止的 agent_message 相关句/行号；14 候选逐项 stage、kernel_denies_read、read_attempted；非候选 read1 的成功/失败计数、失败 errno。固定 deny 与候选路径交集数，以及 wrapper 的 deny 逐项校验结果/允许 probe 结果，可路径一致脱敏；不需要整份来源路径库。 |
| 第 10 次脚本漏行归因 | 仅父级指称的原 AND 选择器代码片段、原命令事件行号/exit、脱敏漏选例的两个匹配布尔值与期望；第 111 行续表修正输出不足以替代原选择器。业务覆盖结论不由本诊断重审。 |
| 输出截断/丢失/上下文异常（仅具体怀疑的调用） | 精确 item ID 及 item.started/completed 配对行号、原 `aggregated_output` 长度/hash、输出首尾中的截断标记、工具响应 envelope 中 total/returned/truncated 元数据（若保留）、命令自身限长参数。另给实际存在的重连/compaction/context-limit 事件或脱敏 stderr 行与时序；runtime 没记录的内部行为继续标未知。 |

诊断交付已完成；未做工程修复、原任务重试、业务验收、计数修订、commit/push/PR 或部署。本轮仅新增本仓库诊断文档与离线结果，**无需运行任何 sync 脚本**。若另行授权 collector 修复，再走本仓库开发/审核流程，所涉 runner/helper 的适用部署命令为 `./scripts/sync-agent-tools.sh`；本轮没有批准该变更，也没有执行同步。
