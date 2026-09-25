RUNTIME/PROVIDER/MODEL: claude/mimo/mimo-v2.6-pro[1m]
任务标签: mimo-reasoning-review-20260925

# Code Review

## Scope

- Mode: current changes（`$deepreview --base main` 方法；审查对象为 PR #39 分支 `fix/shared-provider-resume` 上的**最新未提交修复**）
- Branch: `fix/shared-provider-resume`（committed 背景：`7f43e75`、`edfd821`；本轮只审未提交 delta）
- Base: `main`
- Output file: 由总控保存（任务禁止 reviewer 写仓库文件；本报告即 artifact 全文）
- Included scope（按任务重点）：
  - `scripts/repair-codex-reasoning-history.py`（新增，137 行）
  - `tests/test_repair_codex_reasoning_history.py`（新增，5 用例）
  - `README.md` / `README.zh.md` 未提交双语说明（"Repairing reasoning history for cross-provider resume" 节 + Repository Layout 树 + Maintenance 清单）
- 被审修订 pin（审查期间工作区**多次并发变更**，以下 hash 决定结论适用范围）：
  | 文件 | mtime | sha256（前 16 位） |
  |---|---|---|
  | `scripts/repair-codex-reasoning-history.py` | 12:59:03 | `e4926ca742a74f4c…` |
  | `tests/test_repair_codex_reasoning_history.py` | 12:59:10 | `b8063e74b0e57fee…` |
  | `README.md` | 13:11:40 | `a24ed290b45777ff…` |
  | `README.zh.md` | 13:11:40 | `a51bbd6ee33ad62a…` |
- Excluded scope（按任务约束/独立性）：`auth.json`、真实会话正文（未读取）、发往模型的请求（未发送）、Codex 二进制内部 resume/回放语义（闭源，见 Residual Risk）、`~/.codex-agent/business` 独立 home、并发出现的 `docs/reviews/code-review-20260925-121930.md`（他人 review artifact，**刻意未读**以保持本审独立）
- Parallel review coverage: 无（任务禁止派发子 Agent；全部走读与实测由本 reviewer 完成）
- 项目指令检查：仓库内无 `AGENTS.md`/`CLAUDE.md`（`find` 无命中）；以 README 双语版本为契约文档
- 实测面：`python3 -m unittest discover -s tests` **14/14 通过**（含本套件 5 用例）；$TMPDIR 内 8 组对抗探针（行尾/权限/umask/并发/新 drop 路径），未触碰仓库与真实会话
- 上游一致性核对：`openai/codex#36551` 页面全文（只读抓取；无 maintainer 回复、无关联 PR）

## Findings

### 1-未修复-低-同一秒内第二次 `--apply` 因备份名碰撞以误导性报错退出，README 记载的两步修复流程第二步会被挡住
- **入口/函数**: `main()` 的备份命名与碰撞检查
- **文件(行号)**: `scripts/repair-codex-reasoning-history.py:107-110`（`stamp = datetime.now().strftime("%Y%m%d-%H%M%S")` 秒级粒度；`if backup.exists(): parser.error(f"backup already exists: …")`）
- **输入场景**: 按 README 新增命令块的记载顺序，在同一秒内连续执行 content-null 的 `--apply` 与 `--drop-reasoning-model … --apply`（脚本化 wrapper、快速重试）；或并发中止路径（`test_aborts_if_rollout_changes_during_backup`）残留 backup 后立即重试
- **实际分支**: 第二次运行 `count > 0` → 命中 `backup.exists()` → `parser.error` → exit 2，第二步 drop 完全未执行（`private_new_file` 尚未创建，无残留 temp，原始文件无损）
- **预期行为**: README 列出的连续两条 `--apply` 都应完成各自修复；或报错直指"同名备份、请稍候/改名"，而不是把问题指向备份文件本身
- **实际行为**: exit 2 + `error: backup already exists: …backup-<同一时间戳>`；实测（探针 P8）step2 失败、rollout 行数不变（3 行）；1.1 秒后重试成功
- **直接证据**: `:107` 时间戳仅到秒；`:109-110` 在 `os.open(O_EXCL)` 之前用 `exists()` 抢先报错（O_EXCL 仅是兜底）；README 命令块把两条 `--apply` 写成待执行序列；P8 实测输出逐步复现
- **影响**: 自动化/快速重试场景下文档主流程失败；报错误导排障方向（形如文件冲突）；fail-closed，无数据损坏，等待 ≥1s 可恢复
- **建议改法和验证点**: 备份名加唯一成分（`mkstemp` 式、纳秒时间戳或 `-1` 递增后缀）；或碰撞时明示"已有同秒备份，请稍候重试"。验证点：同秒连跑两条 `--apply` 均 exit 0 且各自留下备份；abort 后立即重试不再被残留备份挡住
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 低

### 2-未修复-低-`turn_context.payload.model` 未做类型校验：非字符串 model 触发未捕获 `TypeError` 裸 traceback，纯统计模式亦崩
- **入口/函数**: `repair_lines()`
- **文件(行号)**: `scripts/repair-codex-reasoning-history.py:36-37`（`current_model = payload.get("model")` 无条件信任取值）、`:41`（`if current_model in drop_reasoning_models:` 对左值求 hash）
- **输入场景**: rollout 中存在 `turn_context` 行且 `payload.model` 为对象/数组（schema 漂移、手工编辑、损坏数据）；**不带任何 `--drop-reasoning-model` 参数也触发**
- **实际分支**: `hash(dict/list)` → `TypeError: unhashable type`，绕过 `:98-101` 的 `except ValueError` 与 `:133-136` 的 `except OSError` → 原始 traceback、exit 1
- **预期行为**: 与工具自身错误契约一致的干净报错（如 `invalid JSONL at line N …; no files changed`、exit 2、无写入）
- **实际行为**: 裸 traceback（实测 P1 复现，exit=1）；发生在 `repair_lines` 阶段，写入前崩溃，文件无损
- **直接证据**: P1 探针输出（`File "…repair-codex-reasoning-history.py", line 41 … TypeError: unhashable type: 'dict'`）；`in frozenset()` 对空集合也求左值 hash
- **影响**: 违反"畸形输入 → 干净报错"的既有契约；仅崩溃体验，无数据损坏
- **建议改法和验证点**: `model = payload.get("model"); if isinstance(model, str): current_model = model`（同时解决 hash 安全与"未知 model 应保留上文"的语义）。验证点：`turn_context` 带 `{}`/`[]` model 时输出行号化错误、exit 2、文件不变
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 低

### 3-未修复-低-备份与替换文件的权限处理不一致且被静默改写：`os.open` 受 umask 截断，替换文件被归一为 `orig & 0600`
- **入口/函数**: `main()` 的 mode 计算 + `write_backup()` / `private_new_file()`
- **文件(行号)**: `scripts/repair-codex-reasoning-history.py:106`（`mode = stat.S_IMODE(before_stat.st_mode) & 0o600`）、`:74`（`os.open(..., mode)` —— 创建 mode 被 umask 截断）、`:62`（`os.fchmod` —— 不受 umask 影响）
- **输入场景**: 原 rollout 为 0644/0640（被替换文件权限静默收紧）；或进程 umask 含 owner 位（如 0277、0777）
- **实际分支**: 备份最终 mode = `mode & ~umask`，temp/替换文件 = fchmod 精确值 —— 两条路径对同一 `mode` 给出不同结果
- **预期行为**: README 承诺的"private timestamped backup"在任意 umask 下成立；替换文件若发生权限变化应保持原样或被文档声明
- **实际行为**: 实测 0644 输入 → 修复后文件与备份均变 0600（组/其他位被剥除，超出"只把 content 置 null"的文档承诺）；umask 0277 下备份成 **0400**、修复文件仍 0600；极端 umask（0777）下备份可成 0000、回滚路径（"copy the backup over the rollout"）失效
- **直接证据**: 探针 B（`m644.jsonl 0o600` / backup `0o600`）、探针 B2（umask 0277 → backup `0o400`、file `0o600`）；单测只覆盖 0600 输入 + 默认 umask（`tests/…:50-53,64`）
- **影响**: 常规场景（会话文件本就 0600、umask 022/027/077）无实际损害；非常规 umask 下备份权限与"private"承诺不符、极端情形废掉文档记载的回滚路径
- **建议改法和验证点**: `write_backup` 内对 fd 做 `os.fchmod(fd, mode)` 与 temp 路径一致；替换文件保留原始 mode 或在 README 声明归一化。验证点：umask 0277 下备份仍 0600；0644 输入的替换文件 mode 与预期一致
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 低

### 4-未修复-低-`--drop-reasoning-model` 的模型串零校验：拼错或用 profile 别名静默 0 命中、exit 0，与"无需修复"不可区分
- **入口/函数**: `main()` 参数生效链（`:89-90` 声明 → `:99` `frozenset(...)` → `:41` 精确匹配）
- **文件(行号)**: `scripts/repair-codex-reasoning-history.py:41,89-90,99`；README 示例 `:284-285`（EN）用 `kimi-k3`/`mimo-v2.6-pro`
- **输入场景**: 用户按 profile 名传参（如 `--drop-reasoning-model mimo`/`kimi`），而 README profile 表中卡的 model 是 `mimo-v2.6-pro`/`kimi-k3`；或 turn_context 记录的模型串带后缀/被网关改名（见 OQ2）
- **实际分支**: `current_model in drop_reasoning_models` 精确匹配不中 → 0 行被删
- **预期行为**: 按 parameter effectiveness 契约，零命中的参数值应被报告（warning 或 per-model 命中计数）
- **实际行为**: `affected reasoning items: 0` + exit 0；实测 P4/P5 同形输出（应删未删时也报 0）；用户以为已修复，resume 仍失败，排障方向被带偏
- **直接证据**: `:41` 无模糊匹配、无按参数值的命中统计；README 示例与 profile 别名不一致（表中 `kimi` 卡 → `kimi-k3`）
- **影响**: 仅诊断体验；数据无损（fail 方向是"少删"）
- **建议改法和验证点**: 输出每个 `--drop-reasoning-model` 值命中的 turn 数，0 命中给显式 warning。验证点：`--drop-reasoning-model wrong-name` 时 stderr 有 warning
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 低

（核心修复语义——`content→null` 与上游 workaround 一致、未修改行逐字节保持、同目录 mkstemp+`os.replace` 原子替换、备份先于替换、二次运行 0 命中、双 stat+全内容并发检查、错误路径 fail-closed 无写入——经逐路径走读与实测**未发现实质性 correctness/stability 问题**。`--drop-reasoning-model` 整行删除的数据丢失面已在 13:11 双语 README 修订中明确披露（"被删记录中的内部推理及推理摘要不再出现在修复后的会话中，但仍保留在带时间戳的备份里"），不再计为 finding。）

## Open Questions

- **OQ1（`content: []` 的端点可接受性）**：上游报错原文 "Expected an array with maximum length 0, but got an array with length 1 instead" 字面上允许空数组；工具对 `content: []` 零改动（探针 P6：affected 0）。若官方端点严格要求 `null`，`[]` 行仍会在 resume 时失败而工具报"0 命中"。需一次真实 resume 验证（本任务禁止发模型请求）。
- **OQ2（drop 匹配串的真源）**：`turn_context` 是否恒带字符串 `model`、其值是卡侧模型 ID 还是 shim "model-name rewrite" 之后的名字、是否可能带 `:effort` 后缀——均无法静态确定（禁止读真实会话）。若记录值与 CLI 参数不同形，finding 4 的"静默 0 命中"会成为常态而非边角。
- **OQ3（删除 reasoning 是否打断引用链）**：README 自己以 "missing reasoning item ID" 作为 drop 的动机，说明 item ID 存在引用关系；删除整行 reasoning 后，后续 `function_call` 等对 reasoning item ID 的引用是否被回放层容忍，需真实 resume 验证。若不容忍，drop 会把一种 resume 失败换成另一种。
- **OQ4（compacted/嵌套历史）**：修复只处理顶层 `response_item` 行；若 `compacted` 等行内嵌历史 reasoning（带 `reasoning_text` content），不在修复范围。上游 workaround 也只改顶层行且报告者确认有效，大概率够用，未验证。
- **OQ5（双语确定性不对称）**：EN "The official OpenAI endpoint **rejects** that history…"（确定式）vs ZH "可能收到"（可能式）；EN "reports zero affected items" vs ZH "应显示零条命中"。按仓库先例（`code-review-20260925-100425` OQ1 同类问题）记为措辞问题，一行可修。

## Residual Risk

- **活跃会话/并发（任务检查项）**：双 stat+全内容比对（`:113-123`）能在 backup 前后截获并发追加（单测 `test_aborts_if_rollout_changes_during_backup` 实证），但 check2 与 `os.replace`（`:124`）之间的微窗内追加仍会被替换掉；更根本地，`os.replace` 换 inode 后，仍持有旧 fd 的 Codex 会把后续回合写进被 unlink 的旧 inode（静默丢数据）。唯一防线是 README/docstring 的"先关闭所有使用该会话的客户端"。无 flock/lsof 检测。前置条件已文档化，接受为 residual。
- **崩溃持久性**：temp 与 backup 均 fsync 文件数据，但 `os.replace`/备份创建后未 fsync 父目录；掉电极端情形下 rename 或备份目录项可能丢失（文件内容本身已落盘）。
- **被改行的字节级重写**：仅被修改行经 `json.dumps` 重序列化（未修改行逐字节一致，实测确认）；空白、数字格式、非 ASCII 转义会被规范化，重复键会被折叠；含 lone-surrogate 转义（`\ud800`）的被改行会在 `.encode()` 抛 `UnicodeEncodeError`（`ValueError` 子类，被 `main` 捕获成干净 exit 2、无写入，但报错无行号上下文）。
- **测试缺口**：`--drop-reasoning-model` 无端到端测试（仅 `repair_lines` 单元级；CLI 接线、`--apply` 备份、二次运行 0 命中均未覆盖）；`:52` 的 `\r\n` 改写分支无单测（实测正确）；symlink 拒绝、非对象 JSON 行（"JSONL object expected"）、`content: []`/字符串 content 静默跳过、权限归一（0644→0600）、同秒备份碰撞均无测试。现有 5 用例覆盖主路径/拒绝路径/行尾边界/并发中止，对一次性修复工具而言扎实。
- **审查期间并发变更**：脚本/测试在 12:18、12:59 两次被改（12:59 引入 `--drop-reasoning-model`），README 在 12:18、13:00、13:11 三次被改（13:11 补数据丢失披露）；另有他人写入 `docs/reviews/code-review-20260925-121930.md`（未读）。本报告结论严格对应 Scope 表中 pin 的修订；若后续再改，需按新修订复核相关 findings（尤其 finding 2/4 的行号）。
- **未验证面**：真实 rollout 样本（任务禁止读会话正文）、Codex 二进制 resume/回放语义（闭源）、live 端点对 `content: []`/字符串 content 的实际校验（禁止发模型请求）、PR #39 元数据与 CI（任务允许面为 git diff/源码/测试；此前轮次 `gh` 亦有 TLS 失败记录）。
- **上游一致性结论（核对过，供参考）**：content-null 路径与 #36551 的 workaround（"reasoning item 且 content 为数组 → 置 null"）一致，报错串 `Invalid 'input[n].content': array too long` 为原文 `[7]` 的合理泛化；drop 路径是超出上游 workaround 的本地扩展，README 已声明动机（`invalid_encrypted_content`/缺失 item ID）与数据丢失。上游 issue 无 maintainer 确认、无关联修复，"null 是正确形态"目前是报告者实证而非官方定论。
