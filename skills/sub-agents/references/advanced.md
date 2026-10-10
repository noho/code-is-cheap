# 高级调用参考

仅在任务选择以下能力时使用。普通调用见 SKILL.md，不要求预检、canary 或额外报告。

## 可选预检

```bash
sub-agent-preflight --runtime codex --provider mimo --cwd /absolute/workspace --task-file /absolute/task.md
```

只检查所选 runner 的 canonical provider、launcher、workspace 和所选 Codex 模型卡，不要求安装另一 runtime。
接受恰好一种 --task / --task-file / --prompt-file 非空白任务，不要求固定小节。自动 label 为 task-<fresh run suffix>；
显式 --label 可用字母、数字、下划线、点和连字符，但不能是 . 或 ..。不同 run_dir 可重复使用显式 label。
输出 key=value，包括 setup_status、私有 run_dir、生成 prompt/log 路径和经过 shell quoting 的 command。
失败时 command 为空；不要带着 setup 错误派发。预检只生成命令，不执行 Agent；生成的文件副本保留原任务并
追加简短的最终答复要求，原文件不变。

## 可选 canary / artifact

需要证明读取某个新文件时，preflight 加 --canary；默认不创建 proof 文件，不传 proof 参数，也不增加证明指令。
它生成无尾换行 token 的 canary.txt 与 canary.expected，私有文件权限 600；prompt 只给读取路径，不能包含 token。
直接 runner 调用可成对传 --canary-file / --canary-expected；预期 token 不应写进 prompt。

子 Agent 将读取内容报告为单独、不缩进的一行 CANARY=<token>，不附说明、不放代码块；证明可在 final answer
或显式 --artifact 文本文件中。比较只剥离常见成对引号/句末排版标点，token 仍严格比较。
显式启用 canary 后，讨论旧 token 的示例须放围栏/缩进代码块或行内示例中；其它独立 CANARY 行会被当作
当前证明并可能造成冲突拒收。普通任务正文可以讨论 canary，不再按宽泛 regex 拒绝。
直接 runner 在启动前检查成对输入是可读、非空普通文件，expected token 非空且内部无空白；不满足时不启动 runtime。
运行后仍核对证明。匹配只证明指定 token 被报告；candidate read 是路径和工具输出的候选记录，不能证明其它输入或整个任务正确。

需要机械检查交付文件时，重复传 --artifact /absolute/new-file。文件必须是本轮新建普通文件，不是既有源码、
目录、符号链接或日志路径别名。预检把路径加入任务并传给 runner；收尾检查不存在/非普通文件时拒收。
收尾拒绝多硬链接及 retained log 的文件别名；“新建”只检查调用前该路径不存在，不证明 inode 来源或文件内容。
需要硬链接产物的任务可不声明 --artifact，由调用方按任务核对。
不声明时 runner 不从 final answer 自动抽取路径，调用方按任务需要直接使用其中的文件。
--detail 不进行这些自动收尾检查。所选显式检查未满足不能悄悄视为通过。

### 可选的任务禁读边界（macOS）

默认调用没有任务级读取隔离。调用方需要禁止读取指定材料时，先备齐本次输入，创建 JSON 数组文件，
其中每项为禁止读取的文件或目录的绝对路径；目录递归禁止。路径必须为已存在的普通文件或目录，按字面值处理，不是 glob。
调用方决定范围：业务报告、历史日志及已知副本分别列出；封装不推断角色、业务规则或内容相同的未知副本。

```bash
sub-agent-preflight --runtime codex --provider mimo --cwd /absolute/workspace \
  --task-file /absolute/task.md --deny-list /absolute/denied.json
```

预检生成 `agent-sandbox ... -- codex-agent-run ... --full-access ...` 命令；Claude 同样通过对应 runner。
也可显式用 `agent-sandbox --cwd /absolute/workspace --deny-list /absolute/denied.json -- <runner> ...`。
封装隐含 `--full-access --no-persist`，固定本次文件系统策略。它不支持 resume、native 参数透传、stdin prompt、动态投递或追加 prompt。必须恰好一个非空 `--prompt` 或普通
`--prompt-file`，启动前复制到受写保护的状态；随后关闭 stdin。
`--cwd` 只决定工作目录；获准来源、Python 依赖和 canary 仍可按原路径读取，禁读名单之外没有读取白名单。
启动后在外层 Seatbelt 内验证禁读路径确实被拒绝，再启动 Agent；setup 通过本身不是隔离证据。

封装必须从总控沙箱外启动：Codex 总控仍使用独立 `exec_command(require_escalated)`；Claude 总控须将
`agent-sandbox` 加入自己的 `sandbox.excludedCommands`，并以独立裸命令派发。内层 Full Access 无法解除
外层 Seatbelt。保留生命周期和调用方显式选择的结果检查；权限错误应报告具体缺项，不自动移除禁读项或放宽权限。

首次使用前，由用户按仓库 README 安装可选 srt 依赖。封装只支持经测试的 macOS/srt 版本，检查失败立即停止。
大名单通过策略文件加载，同一禁令的路径条件仅做等价压缩；仍须逐项通过内核禁读验证。
策略原路径禁止写入/移动，但硬链接别名可能改写留存文件，不影响已加载的内核策略。
总控须通过可信父进程 pipe 收集封装 stderr 中 runner 启动前第一条 seatbelt_profile= 适配器记录的
profile_sha256/source_sha256；后续重复行可能由子进程伪造，不得覆盖首条或采用 last-wins 解析。
使用留存策略作证据前比对哈希，不可信任 Agent 可修改的日志或仅凭留存文件。
stderr 中的 state/seatbelt_profile 可定位保留的策略证据。启动参数超限或原生策略编译失败属于封装启动失败，
runner 尚未启动，不能算 provider 已执行任务；向调用方报告原始错误，不删减禁读项、跳过验证或退回普通派发。
它保留原 runtime 写范围的保守子集及指定输出文件，复制并保护 Codex 用户 `.rules`；不能推导的自定义权限配置会拒绝启动。隔离调用不加载
宿主 MCP、hooks、plugins 或浏览器工具；Claude 仅启用 Bash/Read/Write/Edit/Glob/Grep，Codex 使用本地原生工具。
禁读路径在运行期间不得由其它未隔离进程替换或复制；已有硬链接会拒绝启动。需要的工具/网络缺项须报给调用方裁定。必需的凭据/配置文件列入禁读时 setup 会停止；不提供凭据与 Agent 工具之间的隔离。
