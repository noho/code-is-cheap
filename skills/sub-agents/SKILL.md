---
name: sub-agents
description: "通过 claude-agent-run 或 codex-agent-run 子进程启动外部子 Agent。用于隔离或并发派发调查、实现和 review 任务，并检查进程与结构化输出。"
---

# Sub Agents

使用下述 runner 子进程派发子 Agent。此 skill 激活时，所有子 Agent 调用都必须遵循本协议。

## Runners

| Runtime | Command | Providers | Default structured output |
| --- | --- | --- | --- |
| Claude Code | `claude-agent-run` | `ds mimo qwen kimi glm local` | one JSON result |
| Codex | `codex-agent-run` | `ds mimo qwen kimi glm local gpt gpt-5.6 business` | JSONL event stream |

两个 runner 已在 PATH，直接以命令名调用。调用前先跑 `<runner> --help` 确认可用与接口，并用 `pwd -P` 得到当前任务
workspace 的绝对路径。每次调用必须显式传入 `--cwd "<absolute-workspace>"`，不得依赖总控当前目录。

codex 的 runner 按 `--cwd` 自动判定并追加 `--skip-git-repo-check`（非 git 仓库时），无需手工传；claude-agent-run 无此参数。

## Preflight Checklist

每次派发前逐项过，优先用 `sub-agent-preflight` 机器化完成——它执行全部检查、生成 run_dir / canary / prompt 骨架，
并打印可直接执行的完整命令：

```bash
sub-agent-preflight --runtime <claude|codex> --provider <name> --cwd "<absolute-workspace>" --label "<unique-label>"
```

`setup_status=ok` 才可派发；任何 `failure=` 都是 **controller setup error**（见失败分类），修好后重跑，不得带着
setup 错误派发。手工派发时必须自行完成同样八项：

- [ ] workspace 用 `pwd -P` 解析为绝对路径，`--cwd` 显式传入，不依赖总控当前目录；
- [ ] Git 条件已判定（`git -C "$workspace" rev-parse --is-inside-work-tree`）；codex 的非仓库情形由 runner 自动处理；
- [ ] runner 在 PATH，且 `<provider>` 出现在 `<runner> --list-providers`；
- [ ] launcher 函数与 profile 已部署（codex：`~/.codex-agent/<provider>/config.toml` 可读）；
- [ ] prompt 非空可读，且**不含 canary token**；
- [ ] 输出路径（`--output` / `--stderr` / `--last-message`）全新，label / `--instance` 唯一；
- [ ] 一次性任务用 `--no-persist`；权限继承默认，不得传 `bypassPermissions`；
- [ ] 并发无写冲突：写入范围重叠或有依赖时必须串行。

## Dispatch Contract

每个子 Agent 的 prompt 必须明确：

- 目标、非目标和 stop condition；
- 探针 / 验证类任务的非目标必须包含"不得再派发子 Agent"（任务本身是编排时除外）；
- 可读取、可修改以及禁止修改的文件；
- 是否允许调用工具和允许的副作用；
- 相关代码、文档和约束的路径；
- 预期输出格式、artifact 路径和 validation；
- 报告开头必须声明自身的 runtime、provider 和 model；自报与 event stream 不符时以 event stream 为准；
- 禁止 commit、push、PR、merge 或进入其它 gate，除非任务明确授权。

一次性任务默认使用 `--no-persist`。Claude 调用必须使用唯一 `--instance`。Codex runner 没有
`--instance` 参数，应使用唯一 task label、输出文件名，并把该 label 写入 prompt。

子 Agent 权限默认继承 auto 模式，无需显式传 `--permission-mode`；需要收紧时显式指定。不得传
`bypassPermissions`（父会话 auto 分类器会拒绝该派发）。Codex 用 `--sandbox` 选择沙箱级别。
不得通过宽权限扩张用户授权或任务 scope。

## Execution And Isolation

为每轮派发创建独立目录：

```bash
run_dir="$(mktemp -d "${TMPDIR:-/tmp}/sub-agents.XXXXXX")"
workspace="$(pwd -P)"
```

默认调用：

```bash
claude-agent-run \
  --provider ds \
  --cwd "$workspace" \
  --instance "review-ds-01" \
  --no-persist \
  --output-format json \
  --output "$run_dir/review-ds-01.json" \
  --stderr "$run_dir/review-ds-01.stderr" \
  --prompt "<bounded task>"

codex-agent-run \
  --provider gpt \
  --cwd "$workspace" \
  --no-persist \
  --output-format json \
  --output "$run_dir/review-gpt-01.jsonl" \
  --stderr "$run_dir/review-gpt-01.stderr" \
  --last-message "$run_dir/review-gpt-01.last.md" \
  --prompt "<bounded task>"
```

派发必须在沙箱外运行，方式取决于总控环境：

- Claude 总控：以独立的一次 Bash 调用发出——裸命令、无引号、无 `$HOME` 前缀、不管道、不复合，run_dir 等准备
  工作在之前的调用完成，使命令命中 `excludedCommands`；
- Codex 总控：每个子 Agent 使用一次独立的 `exec_command` 调用，显式设置 `sandbox_permissions:
  "require_escalated"`（附 justification）；若返回 session_id，通过对应的 `write_stdin` 收集。

沙箱内派发的典型症状：codex 子 Agent 初始化失败（`failed to initialize in-process app-server client`）；
claude 子 Agent 能启动但自身 Bash 不可用（`EPERM ... srt-mux`）。出现这些症状时优先检查派发是否仍在沙箱内；
若派发已显式提权，则检查子进程自身的沙箱配置——该报错不唯一指向父级派发未出沙箱。

并发派发 = 多次**独立**调用（Claude 总控：多次 `run_in_background: true`；Codex 总控：每个子 Agent 一次独立的
`exec_command`，若返回 session_id 则用对应的 `write_stdin` 收集）。Claude 环境中复合命令（`&`、`&&`、管道）
可能无法命中 `excludedCommands`，导致子 Agent 的 Bash 失效。
收集时逐个核对各自退出码与 artifact。存在数据依赖、
写入顺序依赖或 file ownership 重叠时必须串行。不得让多个子 Agent 并发修改同一文件，除非已划分互不重叠的写入范围。

不要仅因运行时间长而 kill、重派或切换 provider。后台任务仍在运行、或输出文件仍有变化时，默认仍为 in-flight；
判活不得依赖 ps / pgrep / kill -0 等进程查询。只有明确失败、阻塞、用户停止或进程退出证据才能结束该次派发。

### Sandbox Process Management

沙箱（`sandbox.enabled`）下进程管理一律使用下列配套方法，不要在协议里使用 `ps` / `pgrep` 或其它进程列表工具。

- **派发与收集（Claude 总控）**：用 Bash 工具的 `run_in_background: true` 独立发出；harness 托管的后台任务跨调用
  存活，通过后台任务句柄收集完成状态与退出码，输出由 harness 落盘。不要用 shell `&`——其子进程在沙箱下会随
  Bash 调用结束被回收；
- **派发与收集（Codex 总控）**：每个子 Agent 一次独立的 `exec_command`；可能直接返回退出码，也可能返回 session_id，
  后者用 `write_stdin` 持续收集，直到取得退出码；
- **进度判据**：run_dir 内输出文件（或后台任务的 harness 输出文件）的大小 / mtime 变化，不要用进程列表；
- **退出码**：前台取 `wait "$pid"` 的返回值；后台取完成通知（其输出文件末尾留有 `[exited with code N]` 标记）；
- **输出流**：后台模式会把 stdout/stderr 合并进同一文件，因此结构化输出与日志必须继续通过 `--output` /
  `--stderr` 落到 run_dir。

## Result Validation

每个进程结束后必须检查 exit code、stderr 和输出文件，不得只读取最终自然语言。退出码来源：前台 `wait "$pid"`
的返回值，或后台任务完成通知（输出文件末尾同样留有 `[exited with code N]` 标记）。

任务要求工具调用时，"完成"不算成功，必须有工具执行成功的证据：

- Codex：event stream 存在 `item.completed` 且 `item.type == "command_execution"`、`exit_code == 0`；
- Claude：`num_turns >= 2` 只证明调用过工具，不证明调用成功——以 canary 为准。

验证类派发（探针、验收、产出会被下游信任）必须使用 canary：

1. `TOKEN="<prefix>-$(openssl rand -hex 4)"`，用 `printf '%s' "$TOKEN" > canary.txt` 写入 run_dir 内文件
   （**不带尾换行**，消除"逐字比较"在结尾空白上的歧义）；总控侧另存一份字节相同的 `canary.expected` 作为比对基准；
2. prompt 只给文件路径，不得包含 TOKEN 本身（`sub-agent-preflight` 会自检并拒绝含 token 的 prompt）；
3. 比对规则：子 Agent 报告的 token 字符串与基准**逐字一致**（仅边缘空白不计）；需要字节级证据时，直接比对子 Agent
   `cat canary.txt` 的原始输出与文件字节。不等即判失败——即使其它检查全部通过。

伪造型静默失败是硬失败，不重试，记录并上报：最终消息含字面工具调用语法（`<tool_call>`、`<tool_result>`、
裸 JSON 工具对象）而 event stream 无对应执行事件——provider 级缺陷特征。

已确认的非致命诊断不构成失败，但必须逐条记录为 warning。豁免只适用于与下表逐字匹配的模式：

| 诊断模式 | 检查位置 | 处理 |
| --- | --- | --- |
| `[claude-code:unrecognized_model] {...}`（行首前缀） | Claude 侧 stderr | 记录 warning，不判失败 |
| `Model metadata for <model> not found` | Codex event stream 中 `item.type == "error"` 的 message（必要时也在 stderr） | 记录 warning，不判失败 |
| message 内含 `unrecognized_model` | 同上 | 记录 warning，不判失败 |

其它 error / failed 事件一律按失败处理；只有在退出码、turn completion、工具执行证据与 canary 全部满足、且无其它
失败证据时才判为通过，并附上 warning。

Claude JSON：

- 文件必须是有效 JSON；
- 检查外层 `subtype`、`is_error` 和 `result`；
- 非成功 subtype、`is_error=true`、缺少 result 或非零退出码均不得判定成功；
- `result` 可能包含 Markdown code fence。解析其中的 JSON 时先去除 fence，再进行结构化解析。

Codex JSONL：

- 每个非空行都必须是有效 JSON event；
- 检查 error / failed events，并要求存在明确的 turn completion；上段列出的已确认非致命诊断不按失败计；
- 非零退出码、失败 event 或缺少 completion evidence 均不得判定成功（已确认非致命诊断除外）；
- 优先使用 `--last-message` 保存最终消息，但仍必须同时审查完整 event stream 和 stderr。

空 stderr 不证明成功，非空 stderr 也不自动证明失败；结合退出码和结构化状态裁决。

## Retry And Sessions

失败先归类，再决定动作：

- **controller setup error**（派发前失败，子 Agent 根本没跑起来）：prompt 文件缺失或为空、`--cwd` 不存在、git 条件
  处理错、输出路径已存在、runner / launcher / profile 未部署、prompt 含 canary token。**不计入 provider 重试额度，
  也不计入任何测量批次**；修好后用**新 label** 重派（同修复性重试规则），并在报告里单列为 setup 失败。
- **provider / 测量失败**（子 Agent 真的运行过）：按下方规则处理。

失败后先根据 stderr 和结构化输出区分配置错误、超时、模型错误或任务错误。只允许一次有明确理由的同 provider 重试；
再次失败后可切换 provider，并记录两次失败和切换原因。不得无上限重试。

区分派发错误与测量数据：基础设施失败（起不来、超时、配置错）可按上一条重试；测量 provider/环境行为的派发，
失败必须计数，禁止重试到成功，且必须固定并发度。

修复性重试必须使用新的 task label，并同步用于 prompt、输出文件名和 Claude `--instance`，同时记录与原尝试的关联
标识；修复性重试不得并入原测量批次的通过率，如需重新测量，另建固定并发度、预定样本数的新批次。

需要多轮延续时，第一次使用 `--persist`：

- Claude 后续使用返回的 session ID 配合 `--resume`；
- Codex 后续使用 `--resume <id>` 或在明确需要时使用 `--resume-last`；
- 一次性任务不得持久化 session。

## Controller Adjudication

子 Agent 输出只是输入证据。总控必须读取相关 artifact、review 关键代码或数据、交叉核对冲突，并自行采纳或驳回。
不得因多个 Agent 表述一致就跳过证据检查。

完成报告必须以固定键的裁决块开头（值取自实际检查，不得凭印象；确实未检查的写 `unknown`）：

```yaml
setup_status: ok | fail          # sub-agent-preflight 或手工预检的结果
agent_status: completed | blocked | failed
tool_evidence: yes | no          # Codex: item.completed + command_execution + exit_code=0；Claude: 以 canary 为准
canary_status: match | mismatch | not_run
warnings: []                     # 非致命诊断逐条列出
retry_class: none | setup | provider
```

其后接人读叙述，逐个列出：

- runtime、provider 和唯一 task label；
- 子任务；
- exit status；
- stdout、stderr、last-message 或 artifact 路径；
- 总控采纳、部分采纳或驳回的结论及理由；
- retry、provider switch 和未解决风险。
