# Plan: agent-sandbox dangling symlinks

- Gate: plan review -> fix；本次 plan 修订 prepared，待总控安排独立 plan re-review，尚未 accepted。
- Binding contract: [goal.md](goal.md)；无独立 design document，goal confirmation 是设计依据；[plan-review.md](plan-review.md) 的总控裁决约束本次 fix。
- Work unit: `agent-sandbox-dangling-symlinks`。
- Branch: `fix/agent-sandbox-dangling-symlinks`；base: main `d51765b`，PR #50 已合并。
- 本 Agent 仅写此 plan 和自己新建的 `/private/tmp` 实验材料；不实现、提交、推送、派发 Agent、修改 state 或推进其他 gate。

## 1. 目标、边界及成功信号

使已存在的合法禁读目录含失效软链接时，setup 不再以缺乏定位的 `FileNotFoundError` 中断。保留声明目录的递归禁读、有效软链接的目标扩展、原写权限的保守子集以及启动前的真实内核验证。不存在的目标不能成为授权读取或宣称已隔离的理由。

成功信号：自包含的 `denied/old-python -> missing-framework/Versions/old/bin/python` fixture 能完成解析、策略生成、有效 Seatbelt 验证并到达只操作 fixture 的 runner；声明目录和有效外部目标的 direct/alias/recursive 读取仍被拒绝，允许的 fixture 输入及允许写入仍成功，原有 protected/outside/sink-neighbor/read-only 写入限制仍生效。解析或验证遇到非 ENOENT、无法定位的路径语义、无法保留原限制时，带上下文失败且 runner 未启动。

非目标：不安装旧 Python 或其它环境、不读改业务目录、不启动真实 provider/native Agent 或原业务任务、不删减禁读、不退回普通派发、不重构 sandbox/runner/provider/result/lifecycle 系统、不增加一般化安全强化或新权限模型。禁止读取或执行 `/private/tmp/paradigm-mimo-review-vn24sy1t`、`/Users/leo/workspace/portfolio-manager-v2` 等业务仓库。无 merge、live deployment 授权。后续由总控创建全新 draft PR，不复用 PR #50。

## 2. 直接代码证据与第一性原理判断

| 位置（当前基线） | 当前行为及必要改动 |
| --- | --- |
| `scripts/agent-sandbox:38-85` | 声明路径必须已存在；遍历目录；第 78 行 `entry.resolve(strict=True)` 在失效链接处抛异常。保留这一 strict 调用，仅在确证 ENOENT 后接入现成 missing-aware primitive、分类和错误上下文。 |
| `scripts/agent-sandbox:54-83` | 现有目标进入 pending，目录必须预先可列举，普通文件必须预先可读；拒收已有 hardlink，扩展到 FIFO 等特殊目标时拒收而不打开。保留这些步骤。 |
| `scripts/agent-sandbox:324-336` | `kernel_denies_read` 调用 `sandbox_check(file-read-data, SANDBOX_FILTER_PATH=1)`。返回 1 对不存在路径并非规则命中的充分证据。保留此查询，不能单独依赖它。 |
| `scripts/agent-sandbox:339-363` | 查询后实际 `listdir/open`，只有 `PermissionError` 才通过，再测试允许读写并 exec 固定 runner。只在有已验证祖先覆盖的已登记缺失目标上处理 ENOENT。 |
| `scripts/agent-sandbox:383, 470-490` | `load_denies -> denies -> srt filesystem.denyRead/denyWrite -> boundary.json -> --verify`。同一有效集合控制禁读和禁写；保留字面路径对象。 |
| `scripts/agent-sandbox-launch.mjs` | 固定 srt 0.0.79；接管其已生成 SBPL，等价压缩、文件加载、预启动 hash、原 srt 生命周期。无需改动。 |
| `tests/test_agent_sandbox.py` | SetupTests 覆盖有效 alias、hardlink、FIFO 和无 Seatbelt 的 Unix-mode 假证明；KernelTests 使用临时 synthetic config 和 fake runner 覆盖真实读写边界。新增本缺口，不运行 `test_agent_sandbox_runtimes.py` 的 native Agent。 |

安装契约仍为 Python 3.11+；当前 Python 3.11.15 已提供 `os.path.ALLOW_MISSING`，本次缺失链接处理明确依赖这个现成能力。先保留 `entry.resolve(strict=True)` 对有效目标的现有处理；只在该调用确证 `FileNotFoundError`/`errno.ENOENT` 时调用 `os.path.realpath(entry, strict=os.path.ALLOW_MISSING)`。该 primitive 仅容忍缺失，继续解析已有软链接和 `..`，传播循环、权限、ENOTDIR 等非 ENOENT 错误，恰好覆盖本缺口，无需自研完整 resolver。能力缺失时只在遇到本分支的 setup 明确定位失败；有效目标不受影响。不安装或升级 Python，不使用 `strict=False` fallback，不自行拼接缺失后的字符串，不写版本兼容分支或更严格的逐组件目录判定。

## 3. 真实 macOS 实验与决策

原 plan 留存证据根目录：`/private/tmp/dangling-symlink-plan-87_cajj0/`。环境：macOS 26.6.2 arm64，Python 3.11.15，Node v25.9.0，srt 0.0.79。没有调用真实 provider 或业务任务；本次 fix 不重跑或改写这些证据。

| 实验 | 原始证据 | 结果 |
| --- | --- | --- |
| 无新增 sandbox 的 baseline；最小 SBPL；真实 srt + 仓库 launcher | `baseline-raw.json`、`minimal-raw.json`、`srt-raw.json` | 三者对缺失叶节点/祖先/子路径都返回 `sandbox_check=1`、实际 open ENOENT。baseline 对存在的允许文件为 check=0、可读；两种 deny 策略对存在的声明内容、有效外部目标、失效链接本身为 check=1、open EPERM。 |
| 固定 allow-default 或 missing-only SBPL 后，由父进程只在 fixture 内创建目标 | `allow-default-materialization-raw.json`、`missing-only-materialization-raw.json` | 创建前两者均 check=1/ENOENT；创建后前者 check=0/可读，后者 check=1/EPERM。缺失路径过滤器有未来覆盖能力，但创建前的查询不能证明该过滤器存在。 |
| 真实 srt 的 missing-only 目录过滤器，父进程随后创建目录与子文件 | `srt-directory-materialization-raw.json` | 创建前目标和子文件均 ENOENT；创建后目录 listdir 和子文件 open 均 EPERM，check=1。验证实际 subpath 覆盖。 |
| 真实 srt，同时保留缺失目标并 deny 已存在目录祖先 | `ancestor-srt-materialization-raw.json` | 创建前祖先 check=1、listdir EPERM，祖先内存在的 sibling 也 EPERM；祖先外 allowed 可读。目标创建后 open EPERM。这是可在目标缺失时实测的边界。 |
| 原目标解析矩阵 | `resolution-matrix-raw.json`、`resolution-matrix.py` | 保留为历史实验模型，不能作为实现自研 resolver 的依据。总控已裁定保留 strict 的既有 canonicalization，ENOENT 后用 ALLOW_MISSING；原模型对 `plain/../good` 的额外拒绝不采纳。非严格解析掩盖错误、missing-aware 解析可重入既有目标的证据仍相关。 |
| 当前真实 `--verify`，临时 manifest + 只打印标记的 fake `codex-agent-run` | `current-verify-raw.json` | exit=1，缺失目标仍在实际 open 处抛 ENOENT，runner 标记不存在；只修 load_denies 不足以完成目标。 |

每份 sandbox 原始 JSON 保存 exact argv、exit、stdout/stderr；materialization JSON 保存 before/after。`*.sb`、srt settings、spec、探针与 driver 脚本留在同目录。`evidence-summary.json` 记录环境、源脚本 hash、4 份 srt 策略文件 hash；与可信父 pipe 收集的首条适配器 hash 一致。`assert-evidence.py` 已通过 **63 个断言**。父进程创建 fixture 目标仅用于辨别策略语义，不构成生产中的外部修改支持承诺。

已执行的实验命令（sandbox driver 从父沙箱外执行；材料一次性，重复实验必须创建新临时目录，不能覆盖留存证据）：

```sh
python3 /private/tmp/dangling-symlink-plan-87_cajj0/driver.py
python3 /private/tmp/dangling-symlink-plan-87_cajj0/materialize-driver.py
python3 /private/tmp/dangling-symlink-plan-87_cajj0/srt-directory-driver.py
python3 /private/tmp/dangling-symlink-plan-87_cajj0/resolution-matrix.py
PYTHONDONTWRITEBYTECODE=1 python3 /private/tmp/dangling-symlink-plan-87_cajj0/current-verify-driver.py
python3 /private/tmp/dangling-symlink-plan-87_cajj0/assert-evidence.py
```

本次 plan fix 另在新建 `/private/tmp/dangling-plan-fix-0c4fzu_t/` 验证现成 stdlib 契约；原始结果 `/private/tmp/dangling-plan-fix-0c4fzu_t/stdlib-contract-probe.json` 保存 Python 版本、link/raw target、strict/ALLOW_MISSING/open 各自的结果，**12 个断言通过**。A：`plain/../good/data` 的 strict canonicalization 成功而 open 为 ENOTDIR，保留现状；B：strict ENOENT 后 canonicalization 重入 existing `otherdir/config`，open 仍 ENOENT，必须披露保守 target expansion；C：strict ENOENT 后 ALLOW_MISSING 报 ENOTDIR，open 仍 ENOENT，不声称错误优先级相同。还验证缺失路径返回 canonical target、缺失后续遇循环传播 ELOOP。本次没有实现 helper、运行 runner 或重做 kernel 实验。

**方案决定：不采用“只保留不存在目标 + query=1 + ENOENT 即通过”。** 规则未来有效已证实，但它在目标缺失时不能提供当前调用要求的独立内核拒读证明。采用最小可验证保守替代：**仍保留安全解析的不存在目标作为 deny 路径，同时添加其最近的已存在目录祖先作为递归 denyRead/denyWrite 路径，并实际验证这个祖先。** 这不授予新读写权限，但会连带拒绝该祖先下的 sibling；setup 必须逐条报告此扩展，文档必须说明。祖先若为 `/`、不可预先列举、扫描失败、有现有不支持的 hardlink/扩展特殊目标，或者包含启动必需输入/允许 probe，则上下文失败，不上移到更广祖先、不移除规则、不采用 missing-only fallback。普通 setup 必需输入检查仍会拒绝与扩展集合冲突的配置、工具和输出。

missing target + 最近 existing ancestor 保留为已确认目标下的保守方案；本次只修总控 accepted findings 及其明确的级联/冲突 focused 断言。修订仍须 plan re-review 和 accepted plan checkpoint 后才能实现。不存在“missing-only 已完成有效 kernel proof”的结论。

## 4. 准确路径、数据流与错误契约

### 4.1 声明输入与最小 stdlib 解析 wrapper

外部 CLI、非空 JSON 数组、absolute/literal/recursive-directory 契约不变；用户直接声明的不存在路径仍拒绝，不能借此扩大外部输入契约。不要修改通用 `absolute()`、runner 参数解析或其它调用点的路径策略。

在 `load_denies` 使用严格的声明路径解析；将 OSError/RuntimeError 包装成 ValueError，使缺失、循环等声明错误也包含原始声明。对子链接先读取 `os.readlink(entry)` 保存原始 target 文本，不提前 normpath；只在此入口使用私有 `_resolve_deny_target(entry)`，返回 `(canonical_target: Path, used_missing_aware: bool)`，不引入通用 resolver：

1. 原样调用 `entry.resolve(strict=True)`；成功返回 `(target, False)`，不调用 ALLOW_MISSING，不新增逐组件目录、尾 slash、hop-limit 或其它更严格检查。既有有效 absolute/relative/chain/plain/../good canonicalization 全部保留。
2. 捕获严格解析的 OSError 时，只有 `FileNotFoundError` 且 errno 为 ENOENT，或其它 OSError 明确 `errno == errno.ENOENT`，才进入缺失分支；其余 OSError、RuntimeError/RecursionError 直接交上下文包装层。不能把循环、EACCES、ENOTDIR、False/None 或缺 errno 的异常当作缺失。
3. 此时检查 `os.path.ALLOW_MISSING` 能力；缺失则抛 RuntimeError，说明 setup 缺少该能力并保留刚捕获的 strict ENOENT 类型/errno/filename，由 caller 包装为带 declared/link/raw target 和可知 target 的 ValueError。此检查只通向支持能力或失败，不按 Python 版本选择不同算法，不安装环境。能力可用时仅调用 `os.path.realpath(entry, strict=os.path.ALLOW_MISSING)`，返回 `(Path(canonical), True)`。不重试 strict=False，不自研组件栈/循环检测/完整 resolver；该调用的所有非 ENOENT 错误传播到定位包装层。
4. 返回后用 lstat 分类，不能用 `exists()/is_file()` 的 False 将未知错误归为缺失。存在目标按既有 regular-file/directory validation、pending 扫描、hardlink/special 拒收处理。只有 `used_missing_aware=True` 且最终 lstat 确证 ENOENT，才进入第 4.2 节 missing 分支；strict 成功后条目意外消失则定位失败，不新增外部置换支持。

路径披露与实现分支必须一致：

- **A / 保留既有 canonicalization**：`link -> ../plain/../good/data`，plain 为普通文件、good/data 存在；strict 当前成功就继续处理 good/data，不增加 ENOTDIR 拒绝。保留 stdlib 现状不等于承诺 raw path 与 kernel open 的可达性一致。
- **B / 缺失后重入 existing**：`link -> ../anchor/missing/../../otherdir/config`，strict ENOENT 后 ALLOW_MISSING 可返回已存在的 otherdir/config；按 existing 流程保守 deny/扫描，并在去重和后续冲突检查前报告 `declared/link/raw_target/canonical_target`、`resolution=missing-aware`、`target_state=existing`、`ancestor=not-applicable`。即使未产生 missing metadata 或该 target 已被覆盖，也不能静默跳过报告。这是保守 target expansion，不是 raw link 当前可读的证明。
- **C / 缺失后后续错误**：`link -> ../anchor/missing/../../plain/child`，ALLOW_MISSING 继续解析得到 ENOTDIR，带上下文失败，无 runner；kernel open 可能先报 ENOENT。只传播所选 stdlib primitive 的非 ENOENT，不声称与 syscall 的错误优先级相同，也不另外强化 plain/../good 语义。

实现只包装现成 API 及必要上下文，不采用原 `resolution-matrix.py` 的自研算法。有效外部目录继续递归扫描、普通文件预读、hardlink 拒收、扩展到 special-file 的拒收均保留。

### 4.2 load_denies 输出、pending 与 missing 元数据

内部返回值改为 `(denies, missing_targets)`；只有 `main` 和本模块 tests 消费 `load_denies`，无 public API。`denies` 仍是有序的 canonical absolute string list。`missing_targets` 是 dict，key 为 canonical 缺失目标，value 形状固定：

```json
{
  "/absolute/anchor/absent/leaf": {
    "declared": "/absolute/declared-denied-directory",
    "link": "/absolute/declared-denied-directory/old-python",
    "raw_target": "../anchor/absent/leaf",
    "ancestor": "/absolute/anchor"
  }
}
```

处理缺失目标：沿 canonical target 的父链向上逐个 lstat，只跳过 ENOENT；首个存在节点必须是可预先列举的目录，其他错误/类型拒绝。该节点是该 target 唯一的最近 existing ancestor；若为 `/`，在扫描前立即上下文拒绝。缺失目标和 ancestor 都按 exact-string 去重添加到 `denies`，即使被其它已有 directory deny 包含也保留这两个具体路径。缺失目标不进 pending、不执行预读；ancestor 进入现有 pending 路径扫描。缺失元数据的重复 key 保留首次来源，以稳定定位；但每个链接的扩展报告须在去重前输出，不丢掉其它来源。

pending 项携带局部扫描上下文 `(path, declared, originating_link, raw_target, canonical_target, ancestor)`；declared 始终保留 JSON 原始声明字符串，原声明项的 link/raw target/ancestor 为 None，canonical target 为声明解析结果，扩展项记录当次已知值。visited 仍按 canonical path 去重，避免新 ancestor 重新包含原目录造成无限 pending。新 ancestor 的扫描必须执行现有有效目标扩展和 hardlink/特殊扩展目标检查，不能新增一条不扫描的旁路。

若新增 ancestor 内又发现二级 dangling link，使用**同一** strict -> ENOENT -> ALLOW_MISSING -> 分类流程：保留新 missing target 及其最近 existing ancestor，登记 metadata，向同一 pending 入队，并按同一 visited 去重继续扫描至 pending 为空。该 link 的 declared 保留初始声明，link/raw target 更新为实际发现的二级链接；逐条报告其 canonical target/ancestor 及 `discovered_in=<当前扫描的 ancestor>`，前一扩展日志和该目录路径足以定位级联来源。已 visited ancestor 不重复扫描，但不省略本次来源报告或 missing 登记。级联可到另一子树或更广的 ancestor；每个 target 仍只选最近 existing ancestor，不人为加广度阈值、不因扫描失败向上寻找替代、不加 fallback，遇 `/`、冲突或扫描失败即定位失败。所有已登记 missing target 仍须各自满足第 4.4 节真实祖先证明。

已有 declared deny 和有效扩展路径不因更广 ancestor 出现而删除。existing 目标的 containment 去重逻辑可以保留；missing 目标/ancestor 的 exact 保留按本段执行。级联可连带拒绝非必需 sibling、增加扫描量或使 setup 失败，必须在文档与 residual 中说明，不保证任意业务目录可启动。

扫描、lstat、readlink、类型、能力缺失或预读失败时，用 ValueError 保留 `declared`、被遍历的 `entry/link`、raw target（读取成功时）、canonical target/ancestor（已知时）、错误类型/errno/filename；canonicalization 未完成时明确标记 target 尚未知，附上异常可知的失败 path，不杜撰成功 canonical target。例如：`cannot resolve denied symlink: declared=... link=... raw_target=... cause=NotADirectoryError(errno=20, path=...)`。walk 的 onerror 同样附上当前局部来源；不要只输出库异常，不吞掉非 ENOENT。顶层既有异常打印/exit=1 足够，包装 RuntimeError/RecursionError 后不需要新 runner fallback 或全局 exception 处理。

扩展日志在 `load_denies` 发现每次 missing-aware 结果时写 stderr：existing 重入按第 4.1.B 节报告；missing 目标在选定祖先后报告 `declared/link/raw_target/canonical_target/ancestor`、`target_state=missing` 和当前扫描目录。报告在去重/祖先扫描及 main 的必需输入/输出/write 检查前发生；解析或祖先选择失败则由上述错误报告已知上下文。只保留这种局部日志和现有具体冲突 path，不建立全链 role origin mapping。

### 4.3 main -> srt -> manifest -> verifier

1. `main` 解包两份数据；前置 `load_denies` 已逐条报告 missing-aware existing expansion 和每个 missing->ancestor 扩展（含去重来源及级联），main 不再重复报告 metadata。`--check` 也显示这些 setup 决定，但仍仅打印 setup_status，不能声称 kernel verified。
2. required setup inputs、output、write-root/result checks 继续使用完整 `denies`。因此 ancestor 冲突仍在 runner/srt 启动前拒绝；先行扩展日志 + 既有错误的具体冲突 path 足以定位覆盖 ancestor 及其 origin，不增加全角色来源映射、错误类型系统或 allow exception。
3. `srt.json` 的 `denyRead` 和 `denyWrite` 逐项使用同一完整集合及 `{path, literal: true}`。当前 srt 将 literal 输入编译成 subpath 覆盖；缺失目标仍出现在策略文件中。原 write roots、protected paths、输出 files、network 和 fixed-state 规则不变。
4. `boundary.json` 保留 `denies/probe/command`，新增 `missing_targets`；这一私有 per-run manifest 没有持久化迁移或 public schema 承诺。不新增模块/类型系统/通用 policy service。
5. launcher/srt 继续按当前顺序编译并加载策略，再在同一子进程边界内进入 `--verify`；编译或包布局失败仍直接结束，不能省略 missing 路径以促成启动。

### 4.4 verify_and_exec：两轮实际验证，顺序不靠 deny list 排序

入口保留固定 nonempty boundary、command identity 校验。读取 `missing_targets`，缺省为空以保持没有缺失目标的既有内部 fixture；使用 missing 例外前必须验证：dict 及字段类型正确，target 和 ancestor 是 canonical absolute 路径且均在 `denies`，target 严格在 ancestor 子树内，ancestor 不在 missing key 集合中。这里 canonical spelling 校验是纯 lexical 检查：单个开头 `/`、无 NUL、`os.path.normpath(value) == value`；实际软链接消除已由 sandbox 前 helper 完成，不能在 verifier 对 missing target 调用 strict resolve。祖先包含关系使用 Path 的 parent 关系，不能使用无组件边界的 string prefix。无法验证元数据立即拒绝；不能从 sandbox 内的 ENOENT 临时推断哪些条目“可忽略”。

第一轮处理所有非 missing 条目：

- 每项仍调用 `kernel_denies_read`；False 或 query error 拒绝。
- 仍实际 listdir(directory) 或 open/read(file)。**只有 PermissionError 通过**，之后将此 exact path 加入 `verified_existing`。
- ENOENT、ENOTDIR、ELOOP、其它错误或读取成功都拒绝并带 target/来源（可用时）上下文。不可把已存在条目被外部删除当作本轮 missing 语义。

第二轮处理登记的 missing 条目：

- metadata.ancestor 必须已经在 `verified_existing`；不能只检查它在 deny list 中。目标查询 `kernel_denies_read` 仍必须返回 True；这个检查是必要一致性检查，**本身不构成缺失路径证明**。
- 仍尝试真实 listdir/open/read；PermissionError 可通过；仅 `OSError.errno == ENOENT` 可在上述已验证祖先覆盖下通过。ENOTDIR/循环/其他错误、成功读取都拒绝。错误文字携带 declared/link/raw_target/target/ancestor。
- 接受 ENOENT 的理由是已存在 ancestor 的递归策略和实际拒读已证明，而非文件不存在或 target 的 query=1。如果祖先验证失败、没有登记、query=False，都不得 exec。

两轮后，既有 allowed probe 的内容读取及同内容写回必须成功，然后打印既有 verified/start 日志并且仅 exec 固定 fixture/runner 一次。无 bypass、普通 runner fallback、重试放宽或 provider 行为改动。原 lifecycle/result collection 代码无需修改。

保留现有实际 query/open/listdir 验证，不引入 expected-kind、O_NOFOLLOW、fstat、inode identity 或外部置换处理。总控已用实际 Seatbelt ancestor deny 复核 FIFO：query=1，open 立即 PermissionError（留存 `/private/tmp/dangling-controller-proof-5dj33yor/fifo-under-deny.json`）；不采用无 sandbox FIFO open 作为此验证路径会阻塞的依据。setup 对既有 hardlink/特殊扩展目标的拒收仍保留，运行期 unsandboxed replacement/no-snapshot 限制仍是既有 scope boundary。

## 5. Goal alignment 与 affected files

| 设计/验收 | 绑定 goal / 必要 correctness |
| --- | --- |
| strict 保留 + ENOENT-only ALLOW_MISSING、能力失败及来源上下文 | 合法声明目录的失效链接不再无定位失败；保留有效链接语义，非 ENOENT 不得假装缺失；不用自研 resolver/兼容/安装。 |
| missing-aware 重入 existing 的报告及 A/B/C focused 断言 | stdlib canonicalization 保留且保守 deny 可定位；不新增 plain/../good 拒绝或承诺 kernel-identical 错误优先级。 |
| 保留 missing target + 最近 existing ancestor，级联扫描及逐条报告 | 不删减禁读、不扩大读写授权；missing-only proof 不可证时采用可验证最小保守替代，说明级联支持限制。 |
| 元数据及两轮 kernel + 实际读取验证 | ENOENT 不是隔离证据；每个缺失目标必须被真实验证的递归祖先覆盖。 |
| valid-link/pending/hardlink/special 保留 | 保持已有安全语义和有效目标扩展。 |
| synthetic kernel fixtures、原边界断言 | runner 可达、允许读写成功、direct/alias/recursive 禁读及原写限制仍在。 |
| 多 missing 链接 + 必需输入冲突 focused 断言 | 扩展日志和具体冲突 path 能定位覆盖 ancestor 及 origin，setup 无 runner；不用全链 role origin mapping。 |
| 简短双语与 advanced docs | 说明新增保守语义、祖先扩展和 fail-closed 限制，不改变调用流程。 |

唯一 implementation slice 的 allowed source/docs files：

- `scripts/agent-sandbox`：最小 stdlib wrapper、load_denies 返回/局部来源/扩展报告、main manifest、verify 的必要 ENOENT 契约。
- `tests/test_agent_sandbox.py`：新增 focused setup/verify/kernel regression；现有 `test_symlink_canonicalization` 解包内部输出。其余 fixtures 无缺失目标时行为不变。
- `README.md`、`README.zh.md`：可选 read restrictions 段落的缺失目标及祖先语义；“missing paths rejected” 精确改为 declared missing paths rejected。
- `skills/sub-agents/references/advanced.md`：同样的操作契约、祖先扩展可能造成必需输入冲突；不改 dispatch/skill main workflow。

`scripts/agent-sandbox-launch.mjs`、srt package、installer、runner、preflight/result adapter、runtime tests 均为读取/回归依赖，计划不修改。其余 gate artifacts 由总控在各 gate 创建，不由本 plan Agent 写入。

## 6. 单个行为 slice

**S1 — safely retain dangling targets with a verified existing ancestor**

- Prerequisite: 总控接受 plan review/re-review 及 accepted plan checkpoint；现有工作分支，源代码仍对应审定 base。
- Objective/outcome: 一个失效链接能从 load 到固定 policy、双重验证、fixture runner 全链通过；非缺失错误和不可证明边界在 runner 前带定位拒绝；既有边界不放宽。
- Allowed changes: 仅第 5 节文件及第 4 节定义的 stdlib wrapper/返回值/manifest/两轮验证/日志/测试/说明。不改 generic absolute、公开 deny-list 输入、权限模式或 runner 生命周期；不做自研 resolver/版本兼容/安装、identity/no-follow/type machinery 或全链 role origin mapping。
- Data/state: JSON declared existing -> strict success 或确证 ENOENT 后 ALLOW_MISSING -> existing/registered missing + 逐条扩展报告 -> 同一 pending/visited existing graph（含最近 ancestor 及发现的级联）-> fixed srt policy + manifest -> all existing verified -> registered missing covered -> allowed read/write probe -> single exec。任何失败 -> exit=1/no runner。
- Invariants: 每个 missing target 和 ancestor 均留在 read/write deny 集合；每次 missing-aware 扩展（即使重入 existing 或去重）及每个级联来源可定位；没有 ENOENT-only 或 sandbox_check-only pass；原声明、valid-target expansion、hardlink/special rejection、输出授权和 protected writes 保留。
- Completion signal: 第 7 节 focused 与真实 kernel fixtures 全部通过（kernel 不能以 skip 替代），docs 与实现一致，review evidence 可重复定位，无未分类风险。
- Stop condition: 无法严格识别 ENOENT、缺失目标或其 ancestor 在真实 kernel 下不符合已证契约、只能删规则/扩大权限才能启动、需要触及业务目录或依赖升级；停止并回报总控，不自选一般化硬化。ALLOW_MISSING 缺失是已定义的 located setup failure，验证该失败契约后报告支持限制，不走安装/fallback。

只用一个 slice，因为解析、策略集合及验证例外必须一起形成可执行安全行为，拆为文件/技术层 slices 会留下不完整契约并增加 gate 成本。没有 later approved slice，也没有提前做 future work 的入口。

## 7. Tests、exact commands 与断言

所有 fixture 用新建 `/private/tmp`，临时 home/config、synthetic key 和 PATH 首位 fake runner；不使用当前真实 provider 配置、native Codex/Claude 或业务任务。加载源模块/编译检查设置 `PYTHONDONTWRITEBYTECODE=1`；compile 如需 pycache 只能使用独立 tmp destination。

### Setup/resolution 必须覆盖

- 缺失叶节点、缺失多个祖先、absolute/relative/chained 链接：返回完整 canonical target + 最近 existing directory ancestor；两者都在 denies，metadata 有准确 declared/link/raw_target；缺失目标不被预读；祖先按现有要求预读/扫描。
- 相同缺失目标 dedup、metadata 保留首次来源，但不同 link 的扩展日志各自保留；ancestor 再包含原目录不会 pending 无限循环；缺失 target 在已声明目录内部时也有具体 ancestor 及完整 metadata。
- **A / valid canonicalization**：`../plain/../good/data`（plain 是普通文件）保留 `entry.resolve(strict=True)` 当前成功结果；denies 含 good/data，无 missing metadata，不新增 ENOTDIR 拒绝。普通 valid file/dir/chain 也走 strict success；missing-aware primitive 不介入这一分支。
- **B / existing reentry observability**：`../anchor/missing/../../otherdir/config` 的 strict ENOENT 后 ALLOW_MISSING 返回 existing config；denies 含 canonical config，无该 target 的 missing metadata；stderr 必须含 declared/link/raw target/canonical target、missing-aware existing expansion 和 ancestor 不适用，不能因去重/containment 静默。再覆盖缺失后 `..` 重入并遇 valid-link 到外部目录：继续按 existing 流程扫描及原 hardlink 拒收，不宣称 raw link 可达。
- **C / later ENOTDIR**：`../anchor/missing/../../plain/child` 的 strict ENOENT 后 missing-aware 解析得到 ENOTDIR；ValueError 含 declared/link/raw target/可知失败 path/errno=20，无 runner，不转换 missing。文档和测试说明中不宣称与 kernel open 的错误优先级相同。
- 直接 ELOOP、自环/两节点环、permission error、ENOTDIR，以及 strict ENOENT 后 ALLOW_MISSING 再报 ELOOP/EACCES：传播定位失败。strict 非 ENOENT 不得触发 missing-aware 调用；错误有声明/link/raw target（可读时）、可知 target 或失败组件/原始 errno。permission 测试以 strict/realpath/lstat/readlink error injection 为稳定主断言，chmod 仅可加 fixture 实测。不添加对 stdlib 当前接受路径的更严格尾 slash/组件检查。
- 缺失 ALLOW_MISSING 能力的 focused injection：strict ENOENT 后明确 setup failure，含 declared/link/raw target、缺失能力名和可知 target/strict filename，无 runner；strict 成功的有效目标仍按原路径处理，不产生能力失败。不能安装环境、调用 strict=False 或自研/版本 fallback。
- 顶层声明 missing 仍拒绝；valid file/dir links 仍扩展，包括外部 valid directory 内二级 link；有效 target 的 hardlink/FIFO 仍在打开前拒收。不要把当前目录中所有未扩展 special-file 的一般强化加入本轮。
- **ancestor cascade**：初始 `denied/old-python -> anchor-one/absent/leaf` 添加 anchor-one；anchor-one 内二级 link 指向 anchor-two/absent/leaf，再在 anchor-two 放回指已 visited 目录的 valid link。断言两个 missing target/ancestor 都 exact 保留、metadata 各有准确 link/raw target/同一 declared、扫描完整且终止；两条扩展日志分别含 origin，二级日志 `discovered_in=anchor-one`。有效回指不新增无限扫描，不跳过原 hardlink/特殊扩展目标拒收；每个登记目标仍引用自己的可验证祖先。
- nearest ancestor 为 `/`、不可列举、扫描/现有类型检查失败：明确拒绝，不上移或 fallback。
- **multi-link required-input conflict**：同一 denied 目录内两个 missing 链接分别指向 safe-anchor 和 input-anchor；prepared prompt-file 放在 input-anchor，两个 target 与 ancestor 独立。用 synthetic config/PATH fake runner 分别执行 --check/launch；断言 exit=1、两条扩展日志含各自 declared/link/raw/canonical target/ancestor，随后既有 `required setup input is denied` 含具体 prompt path；从日志能唯一定位覆盖它的 input-anchor 及该 link 的 origin，runner 标记不存在（无 srt launch）。不改所有 conflict role 的错误/来源传播框架。

### Verifier 必须覆盖

patch `os.execvpe` 作为 exec sentinel，实际 probes/mock errors 与 query 调用记录配合断言；这些是安全状态组合测试，不只是复述 helper 实现。

- target query=1 + actual ENOENT + **没有** metadata/verified ancestor：拒绝，exec sentinel 未调用。
- ancestor query=False、query exception、实际读取成功/ENOENT，即使 target query=1/ENOENT：拒绝，不能用 target 的“缺失”掩盖。
- ancestor 已实际 PermissionError + query=True；registered target ENOENT：允许继续，但 allowed probe 仍读写成功才 exec；deny list 的 target 放在 ancestor 前也得到相同行为。
- registered target 的 query=False/indeterminate、actual ENOTDIR/ELOOP/其它 OSError、actual read success、invalid/missing/non-containing ancestor metadata：拒绝且错误带可用来源。
- 普通 existing 条目意外 ENOENT 仍拒绝；Unix mode PermissionError + query=False 仍拒绝。无 missing 的原内部 fixture 和 allowed probe 失败路径不变。

### 真实 KernelTests 必须覆盖

沿用 `tests/test_agent_sandbox.py::KernelTests` 的 tmp config + fake runner；增加 fixture `work/denied/old-python -> root/anchor/missing-framework/Versions/old/bin/python`，anchor 在 work、state、sinks 和所需执行工具之外，anchor 有预先可读 sentinel。同时放入 relative/chain 缺失链接及有效外部目标链接；有效外部目录有嵌套文件及二级 valid link。

断言 exit=0、可信 stderr verified 日志在 runner 标记之前；boundary/srt/真实 seatbelt 文件保留原 declared、missing target、ancestor、所有外部有效扩展；metadata 匹配；首条 adapter hash 匹配保留 profile。runner 查询 ancestor 与 existing sentinel check=1，实际 listdir/open PermissionError；覆盖写 ancestor 的 existing sentinel 与直接创建 ancestor/new-entry 都是 PermissionError；missing direct open 允许 ENOENT（**不作为 proof**），denied/old-python alias open PermissionError；outside-anchor allowed read/write 成功。保留原 direct/symlink/dir_alias/dotdot/history/data_alias/tmp_alias、recursive rg 无 forbidden 内容、hardlink/nested envelope 拒绝及所有原写限制断言。现有 read-only 和 Claude original-denyWrite fixture 回归必须通过。

加入一个独立、只操作 fixture 的真实 srt 对照：allow-default 的 missing 查询仍为 1/ENOENT；拒绝祖先的 loaded policy 对 existing ancestor 的查询和 listdir 实际拒绝。再用同步握手的父进程创建临时目标目录/子文件，确认 loaded policy 的 open/listdir 拒绝且 outside-anchor allowed 成功。握手与 subprocess timeout 固定最多 45 秒，不用 sleep 作为证据；测试内创建新文件只限该 fixture，不推导生产 TOCTOU 支持。测试 case 名应分别表明 missing ambiguity 和 verified-ancestor boundary。

实现后执行（仓库 cwd；kernel 命令使用 `exec_command(require_escalated)` 从父 sandbox 外运行）：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_agent_sandbox.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_agent_sandbox_launch.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_sub_agent_preflight.py'
PYTHONDONTWRITEBYTECODE=1 AGENT_SANDBOX_KERNEL_TESTS=1 SRT_TEST_BIN=/Users/leo/.local/bin/srt python3 -m unittest discover -s tests -p 'test_agent_sandbox.py'
git diff --check
```

前 3 个命令必须 exit=0（第一个 kernel opt-in skips 如实记录）；第 4 个必须真正运行全部本模块 kernel cases、零 kernel skip、exit=0，包含大 deny-list 与原写限制回归。不使用 `test_agent_sandbox*.py` 通配符开启 kernel，以免同时启动 native-runtime tests。只要这些相关检查通过，不为本次局部改动额外扩展到 provider/业务验证或环境安装。

若命令因 shell/路径等可恢复工具问题失败，可按原 scope 修正执行；行为断言失败必须报告并修复或回到总控裁决，不能以 skip/弱化断言收尾。保留 exact command、真实 exit、测试摘要、fixture raw evidence 路径及首条 profile hash。

## 8. Docs decision 与无 goal drift 说明

更新第 5 节三份现有文档，不新增操作流程：

- 直接声明路径仍必须存在；有效 target 保留 strict stdlib canonicalization（含 plain/../good），不增加更严格的路径拒绝。仅 strict 确证 ENOENT 后用现成 ALLOW_MISSING；缺失该能力时定位 setup failure，Python 3.11+ 下限不变，不自动安装/升级，不设兼容或非严格 fallback。
- 缺失-aware canonicalization 可在 `..` 后重入 existing target，仍保守扩展 deny 并逐条报告；这不证明 raw path 当前可达。后续 ENOTDIR/循环/权限错误传播，不宣称 resolver 与 kernel open 有相同错误优先级。
- 最终缺失 target 保留为 deny，最近 existing ancestor 整体递归禁读/禁写。新增祖先扫描中发现二级 dangling link 时同流程级联，每个 missing->ancestor 及其发现来源均报告。可能连带拒绝全部 ancestor 下的非必需资源、扩大扫描或导致输入冲突；不承诺任意业务目录可启动，不设新广度阈值或放宽 fallback。
- ancestor 实测 kernel/读取拒绝后才容忍登记目标 ENOENT；ENOENT/query=1 单独均不是证明；非 ENOENT、不支持 ancestor、root/扫描/冲突失败均 fail closed。先行扩展日志和具体 conflict path 用于定位，不改全角色来源系统。

保留所有现有 known-copy、外部修改、credential、macOS/srt、--check 非隔离证明及不回退说明。

当前增加的设计全用于修复一个已确认行为及其必要证明；不改变公开输入格式、provider/runner 参数、写权限推导、生命周期或结果收集。祖先扩展是 missing-only 证明失败后所需的最小保守替代；现成 ALLOW_MISSING 取代自研解析，保留 strict 语义和既有 visited traversal。未引入新 policy engine、类型框架、版本迁移/兼容分支、快照隔离、expected-kind/no-follow/fstat/identity machinery、全链 role origin mapping、广泛 special-file 检查或 future slice。MiMo 2/3 的 rejected-with-reason 裁决保持不变；这里只固化总控 accepted findings 和指定的 focused 断言。

## 9. Residual risks、owners/destinations 与 open questions

| 风险/未覆盖领域 | 分类 | Owner / destination；放行条件 |
| --- | --- | --- |
| dangling link 的 ENOENT、未定位错误、非 ENOENT 被吞及 missing-only 假证明 | fixed in current slice | Implementation/fix Agent；S1 + focused/kernel evidence。只在上述断言与 review 闭环后标为已修复，本 plan 不宣称已修。 |
| ALLOW_MISSING 能力在部分 Python 3.11+ 环境缺失 | fixed in current slice | Implementation/fix Agent；S1 只在 strict ENOENT 分支明确 located setup failure，focused 注入及 docs 固化支持限制；有效目标不受影响，不安装/升级/兼容 fallback。 |
| stdlib canonicalization 与 raw path 可达性/内核错误优先级不同；strict ENOENT 后可重入 existing 并保守扩大 deny | fixed in current slice | Implementation/fix Agent；S1 保留有效语义、A/B/C focused 测试、逐条重入日志及 docs。canonicalization 是 deny 策略输入，不承诺 kernel-identical path reachability/error precedence。 |
| ancestor 及级联可能范围较广、扫描较大、连带禁读写非必需 sibling 或与 required input/允许 probe 冲突 | fixed in current slice | Implementation/fix Agent；S1 同 pending/visited 级联、逐条报告最近 ancestor 及 origin、保留扫描/冲突拒绝、禁止 root/fallback；二级 dangling 与多链接冲突 focused 断言。docs 说明这是支持限制，不承诺每个业务目录都能启动。 |
| 缺失 target 后续被外部进程改成 symlink/硬链接/特殊节点，祖先被替换、内容被复制到未列出位置 | assigned to later work unit | 调用方负责执行既有“运行中不得由未隔离进程替换/复制”限制；若要放宽该限制，由总控交新的经用户确认 work unit。本轮不规划实现，不以实验的受控 materialization 承诺此能力。 |
| 未知副本、凭据/已供 prompt 信息、当前模型之外渠道、非 macOS/未来 srt 或 runtime 行为 | assigned to later work unit | 调用方/维护者；既有 README/advanced boundary；升级或新平台要求时另行确认目标和边界验证。与 dangling 修复无关，不增加本轮验收。 |
| 无新增 generally hardened special-file-in-directory 策略、全量 resolver/property fuzz、全文件系统身份一致性保证 | assigned to later work unit | 总控；如有具体需求，另作 goal confirmation。维持现有 supported-target 拒收测试；不是本轮未完成 finding。 |
| 合并后 live entry 可能仍是旧版本；本 plan 未修改部署 | requiring new issue or explicit user decision | 调用方/总控；final closeout 报告 source/live 版本与状态，用户另行安排部署和真实调用复验。本目标明确无 live deployment 授权，不能将 source tests 当成 live 已修复。 |

没有 later approved slice；没有已知可引用的 existing issue；无未分类 residual risk。当前无 blocking open question：最小 stdlib 解析、祖先方案、级联/重入扩展范围、能力限制及失败行为已按总控 binding 裁决固化，仍待 plan re-review 验证。不能改为 query=1/ENOENT-only pass；若实现实测不能复现祖先证明，则这成为明确 blocking semantic question，报告具体路径、query/open 原始结果并暂停，不静默放宽。范围之外问题只交总控/residual，不扩大 S1。

## 10. Completion report format / handoff

Implementation/fix 完成报告必须包含：S1 outcome；实际 changed files；load 输出/缺失目标与 ancestor metadata 实例；strict/ALLOW_MISSING 能力与 A/B/C 行为；是否发生 existing 重入/祖先级联扩展及 required-input 冲突、逐条日志来源；exact commands + exits + pass/skip 数；真实 kernel 证明（含 allow-default 对照、ancestor query + actual refusal、allowed read/write、valid-target/原写限制）；raw evidence 路径与首条可信 adapter hashes；docs decision；每个 finding 的裁决/最终修复状态；按上述类别列 residual risks/owner/destination；blocking open question 或明确 none；next entry point 交给总控。不得报告 provider 已完成原任务、live 已部署或 work unit 已全部 closeout。

本次 plan fix 对 binding 裁决的对应：

| 裁决项 | 本文件修订 / 待验证 |
| --- | --- |
| MiMo 1 accepted | 第 2/4.1/7/8 节：保留 strict 成功路径、确证 ENOENT 后仅用现成 ALLOW_MISSING、能力缺失定位 setup failure；移除完整自研 resolver/额外有效路径拒绝/兼容分支。 |
| DS 1 accepted | 第 4.1/4.2/7/8 节：A 语义保留；B existing 重入逐条可定位报告；C 后续 ENOTDIR 带上下文传播且不承诺 syscall 优先级；各有 focused case。 |
| DS 2 accepted（rationale gap） | 第 2/4.1/7/9 节：选择现成 primitive 的必要性、当前可用与缺失能力失败契约明确；不采用原 review 的自研方向。 |
| 总控 cascade / localized conflict 指令 | 第 4.2/4.3/7/8/9 节：同 pending/visited 级联并逐条报告来源；二级 dangling 与多 missing + 必需输入冲突 focused 断言。MiMo 2/3 仍 rejected，不扩展 identity/no-follow 或 role origin mapping。 |

本次只改本 plan，未改 goal/state/review 报告或原证据；原 plan 的 63 assertions 为留存证据，本次独立 stdlib probe 12 assertions pass，不将其计为实现或真实 kernel 回归。实现、focused/source/kernel 回归及文档落地均尚未执行；上述 plan 修订内容仍待独立 re-review 确认，不自行回写 finding 最终状态。artifact 是本文件，下一入口交总控的 plan re-review；本 Agent 不提交/推送、不派其他 Agent、不创建 PR、不进入后续 gates。
