RUNTIME/PROVIDER/MODEL: claude/mimo/mimo-v2.6-pro
CANARY=mimo-6201af6f

# Focused Deepreview Closure — e2big-mimo-claude-20261009-r4

## Scope

- Mode: current changes（focused closure review，非全量重复审查）
- Task: e2big-mimo-claude-20261009-r4（standalone scope，显式禁止派发子 Agent，已遵守）
- Frozen HEAD（开始/结束各核对一次）: `ac5b244637e926b8658f5b336e4247b106fd96b8`
- Selected base: `6672741e6a58939aba3a65c57c03843d2c92aa10`
- Diff 身份: `git diff --stat 6672741..ac5b244` = 8 files, +106/−24，与任务声明一致
  （README.md、README.zh.md、docs/reviews/agent-sandbox-e2big-validation-20261009.md、
  scripts/agent-sandbox、scripts/agent-sandbox-launch.mjs、skills/sub-agents/SKILL.md、
  tests/test_agent_sandbox.py、tests/test_agent_sandbox_launch.py）
- Output file: `docs/reviews/e2big-mimo-claude-20261009-r4.md`（任务指定路径，覆盖 deepreview 默认命名）
- Included scope: 仅 base..HEAD 新 diff 的闭合验证（两处 accepted finding 的修复、测试、文档、Agent-facing 措辞）；
  unchanged code 仅按必要上下文读取（scripts/agent-sandbox 全文、agent-sandbox-launch.mjs 全文、
  两个测试文件全文，用于走读修复的完整执行路径）
- Excluded scope: 重复全量依赖/算法审查（prior full E2BIG source review 覆盖 f818dde→6672741）；
  其他 reviewer 报告（docs/reviews/e2big-ds-flash-*、e2big-mimo-claude-20261009-r3 均未读取）；
  原生/内核测试重跑；源码编辑、git 写操作、网络调用、tmux/workflows；未变更模块
- Parallel review coverage: 无（本 standalone 任务禁止子 Agent）
- Model provenance: harness 声明运行模型 `mimo-v2.6-pro[1m]`，系统标识为 Claude Fable 5 族
- 裁决上下文: 任务给定两处 accepted findings 及 native probe 结论为 supplied evidence（非本人执行，下文 Own vs supplied 区分）

## Findings

### 1-未修复-低-共享 stderr 流上的 pre-spawn 哈希行缺少“首次出现”锚定约定

- **入口/函数**: 调用方按新增文档执行的证据审计流程（README.md:160-164、skills/sub-agents/SKILL.md:164-166）；
  哈希行由 scripts/agent-sandbox-launch.mjs:174 的 `console.error` 产生
- **文件(行号)**: README.md:160-164；skills/sub-agents/SKILL.md:165-166；scripts/agent-sandbox-launch.mjs:174-175；
  参照（脆弱解析惯用法）tests/test_agent_sandbox.py:250、290
- **输入场景**: 恶意 Agent 在沙箱内经硬链接别名改写 seatbelt.sb / seatbelt.source.sb 后，向 stderr 追加伪造行
  `agent-sandbox: seatbelt_profile=... profile_sha256=<tampered-bytes 的哈希> source_sha256=... file-backed`；
  调用方审计器对整段捕获流做解析时采用 last-wins（例如 tests/test_agent_sandbox.py:250 的
  `dict(item.split('=',1) for item in stderr.split() if '=' in item)`，或 grep 全流取最后匹配）
- **实际分支**: 审计器取到伪造哈希 → 与被改写的留存文件比对 → 匹配通过 → 篡改未被发现
- **预期行为**: 收集契约应明确：只认启动前唯一一行（适配器在整个生命周期恰好打印一次——
  launch.mjs:166-176 的 `launched` 标志；且 `console.error` 在 `originalSpawn` 之前完成，launch.mjs:174-175），
  即流上**第一个** `seatbelt_profile=` 行；其后任何重复行都是 Agent 可写内容，必须丢弃
- **实际行为**: README 写明 “Before spawning, the adapter prints … collect that stream through a trusted parent
  pipe”，skill 写明收集“启动前的 profile_sha256/source_sha256”，但两处都没有声明 first-occurrence 锚定规则，
  也没有警告该 stderr 流与 runner/Agent 共享（srt 保留 stdio 传递，见 validation doc 的启动链）、可携带伪造重复行；
  仓库内现成的解析惯用法恰为 last-wins
- **直接证据**: (a) runner/Agent 继承封装 stderr（originalSpawn 以 srt 原 stdio 选项派生，launch.mjs:175），
  Agent 可写同一 fd；(b) 真实行在 spawn 前同步写出，伪造行只能出现在其后 → 第一行锚定在时序上可靠；
  (c) `launched` 标志保证恰好一行真实哈希行；(d) tests/test_agent_sandbox.py:250、290 的 dict 构造对同键后出现者覆盖
- **影响**: 该修复的全部目的就是篡改取证；若调用方按自然写法实现收集器（last-wins / 取最后匹配），
  恰在修复所针对的对抗场景下篡改检测被静默绕过（错误审计结论 / 静默失效）
- **建议改法和验证点**: 在 README 与 skill 各加一句：审计只取启动前（流上第一个）`seatbelt_profile=` 行，
  后续重复行按 Agent 可写内容丢弃，禁止 last-wins 解析；可选加一个小的 ordinary 回归：
  向流中注入伪造后行，断言 first-wins 解析结果仍为真实哈希
- **修复风险（低）**: 仅文档契约精确化，可选 test-only；不涉及权限、通道重设计或范围扩张
- **严重程度（低）**: 机制本体（hash exact bytes + spawn 前打印 + trusted capture）成立，
  skill 已有“启动前的”限定；缺的是防伪造重复行的显式锚定约定

未发现其他实质性问题：两处 accepted findings 的修复本身（详见下节闭合判定）经逐行走读与本人
ordinary 测试验证，未发现 correctness 回归或新的实质缺陷。

## Accepted-finding closure

### Issue 1 — unsupported standalone srt 在结构校验前被执行 —— CLOSED

**修复机制（直接证据）**:
- scripts/agent-sandbox:367-369：`subprocess.run([node, str(launcher), "--validate", srt], …)` 现在先于
  scripts/agent-sandbox:370-372 的 `subprocess.run([srt, "--version"], …)` 执行；base 版本为 version 先行（diff 可证）
- `validateRuntime`（launch.mjs:132-148）为非派生子进程校验：仅 realpathSync / readFileSync / statSync /
  accessSync，检查 canonical CLI 路径、package.json 的 name/version/bin 解析到该 CLI、三个必需模块为可读常规文件；
  失败统一抛 `…reinstall with install-agent-sandbox.sh (…)`（launch.mjs:146）
- 因此 unsupported standalone 候选（无包布局）在任何执行之前即 fail-closed；`srt --version` 只可能针对
  已通过结构校验的 pinned 包布局执行

**测试证据**:
- tests/test_agent_sandbox.py:113-129（ordinary SetupTests，非 kernel 门控）：
  marker fixture 的假 srt 会 `touch must-not-execute` 并 `echo 0.0.79`；断言 returncode≠0、
  无 `setup_status=ok`、stderr 含 `reinstall with install-agent-sandbox.sh`、且 **marker 不存在**
- 回归检测属性（走读推演）: 若顺序退回 version 先行，假 srt 必被执行 → marker 存在 → assertFalse 失败；
  该校验不能被“同样失败于 validation”假阳性掩盖——断言组合同时钉住错误消息与未执行事实
- 旧 kernel 门控测试 `test_preflight_rejects_standalone_srt_before_reporting_success` 已由该 ordinary
  marker 测试取代（diff 中删除）；被测代码路径在任何 sandbox 门控之前，ordinary 覆盖等效
- 本人复跑该测试：ok（见 Own vs supplied）

**行为变化（可接受）**: 合法包布局但 package.json 版本不符的候选，现在以 reinstall 消息失败而非
`srt 0.0.79 required, found X`；仍为 fail-closed，方向一致。

**残余边界（按任务范围明确不闭合）**: 结构校验通过后执行 `srt --version` 及随后导入 CLI 是
pre-existing trusted-package execution——validateRuntime 只证布局不证包内容完整性（无模块级哈希）；
任务明确不要求移除该执行、不要求 supply-chain 加固。本 finding 的闭合判定只覆盖
“unsupported standalone 在校验前被执行”这一命题，该命题已消除。

### Issue 2 — 硬链接别名可改写留存策略文件 —— CLOSED（按最小证据溯源方案）

**修复机制（直接证据）**:
- launch.mjs:127-129：`fileBackedArgv` 对内存中的 `original`（source）与 `profile`（effective）字符串取
  SHA-256（createHash('sha256').update(string) → UTF-8 字节），与 writeFileSync（:122、:124，'wx' 独占创建）
  写入的正是同一字符串，故哈希 = 写入的 exact bytes
- launch.mjs:174：哈希行在 `originalSpawn`（:175）**之前**打印 → 时序上为 pre-spawn 证据；
  `launched` 标志（:168-173）保证每个 envelope 生命周期恰好一行
- 文档明确降格为取证而非防护：README.md:160-164、README.zh.md:155-157、
  skills/sub-agents/SKILL.md:164-166、validation doc「MiMo review adjudication」段——
  明说别名可改写留存文件、不改变已加载内核策略、不是 inode 不可变声明、不新增权限限制

**本人独立验证（ordinary，非内核）**: 自建 scratch 检查（/private/tmp/claude/e2big-r4-hash-check.py），
压缩路径下：source 文件留存、compacted ≠ source、`profile_sha256` == sha256(effective 文件字节)、
`source_sha256` == sha256(source 文件字节) == sha256(输入字符串 UTF-8)，两哈希在压缩时不同 —— 全部通过。
仓库 ordinary 传输测试（test_agent_sandbox_launch.py:78-79）覆盖无压缩路径：
`profileSha256` == Python sha256(encode) 且 `sourceSha256 == profileSha256`。

**测试证据（supplied，native，未由本人重跑）**:
- test_profile_hardlink_changes_detected_by_prespawn_hashes（tests/test_agent_sandbox.py:229-255）：
  150 项强制压缩 → 两文件均留存；runner 内经别名 `os.link`+chmod+write 改写两文件；
  断言哈希行长 64、留存文件哈希 ≠ pre-spawn 哈希（取证生效）、且已加载策略仍拒绝 `direct` 读
  （内核策略不受影响）；改写代码若失败会使 runner 非零退出/无 JSON → 测试不可能静默通过
- test_large_deny_list_verifies_every_entry_before_runner（:290-292，4108 列表回归）：
  未改写场景下 pre-spawn 哈希 == 留存文件字节 —— 与硬链接回归互补（相等性 + 不匹配检测各归其位）

### 精确哈希信任边界（本报告的闭合表述）

**是什么**: launch.mjs 在写盘后、spawn 前对 source/effective 策略 exact bytes 计算的 SHA-256（hex），
打印到封装 stderr 一行 `agent-sandbox: seatbelt_profile=… bytes=… source_bytes=… profile_sha256=… source_sha256=… file-backed`。

**能证明**: 若可信父进程 pipe 收集到启动前该行，且事后留存文件字节与之哈希相等，则留存文件
与适配器写入（亦即 `sandbox-exec -f` 加载之 effective 文件所写内容）逐字节一致；不等则留存证据已被改写。

**不能证明**（必须随证据一并声明）:
1. **不阻止别名写**——不是权限修复；硬链接别名 link/chmod/write 改写共享 inode 成功是已证实行为；
2. **不提供 inode 不可变**——chmod/替换经别名仍发生，内容哈希不覆盖 mode/元数据；
3. **不认证整条 stderr 流**——runner/Agent 共享该 fd，可伪造后置重复哈希行（见 Finding 1）；
   可信的是**父进程 pipe 的捕获与启动前锚定**，不是流内容自证；
4. **无 trusted capture 则无效**——Agent 可改写的日志或留存文件本身不能自证（README.md:163-164、
  skill 明文）；哈希行与文件一样处于 Agent 可达面，证明力全部来自收集时序与通道；
5. **仅内容字节**——不覆盖 mode、inode、路径名复用。

**调用方协议**: 可信父进程 pipe 收集封装 stderr → 锚定启动前（第一个）`seatbelt_profile=` 行 →
审计留存策略前比对两文件哈希；比对失败视为证据被改写，而已加载内核策略不受影响（native 回归已证）。
边界情形：未压缩时 seatbelt.source.sb 不落盘（launch.mjs:120-123 仅当 profile≠original 写 source），
此时 `source_sha256 == profile_sha256`，审计以实际存在的留存文件为准。

## Agent-facing wording

skills/sub-agents/SKILL.md:163-166（本 diff 更新）逐项核验：
- 「大名单通过策略文件加载」——删除了原「受写保护的策略文件」overclaim，正确；
- 「策略原路径禁止写入/移动，但硬链接别名可能改写留存文件，不影响已加载的内核策略」——
  防护/影响分离准确，无 immutability 误标；
- 「总控须通过可信父进程 pipe 收集封装 stderr 中启动前的 profile_sha256/source_sha256；
  使用留存策略作证据前比对哈希，不可信任 Agent 可修改的日志或仅凭留存文件」——
  责任主体（总控）、通道（可信父进程 pipe）、时点（启动前）、用途（审计前比对）、
  反例（Agent 可改写日志/单独留存文件）齐全；
- 与 README.md:160-165 / README.zh.md:155-158 / validation doc 表述一致，无互相矛盾；
- 唯一缺口即 Finding 1 的 first-occurrence 锚定未写明（skill 的「启动前的」是隐式锚定，未展开为解析规则）。

## Own vs supplied tests

**本人执行（ordinary，无 kernel 门控，无权限扩张）**:
- `python3 -m unittest discover -s tests -p 'test_agent_sandbox_launch.py'`：6 tests，5 ok，
  1 explicit native opt-in skip（含新哈希断言的传输测试通过）
- `python3 -m unittest discover -s tests -p 'test_agent_sandbox.py'`：18 tests，12 ok，
  6 explicit kernel opt-in skips；其中 `test_preflight_rejects_standalone_srt_without_executing_it` ok
- 自建 scratch 哈希字节同一性检查（压缩路径）：全部断言通过（/private/tmp/claude/e2big-r4-hash-check.py）

**Supplied（给定证据，非本人执行，如实标注）**:
- ordinary 全套：93 tests OK，9 explicit opt-in skips（35.883s）
- native Seatbelt + 实际 Codex/Claude local mock：26 tests 全过（15.844s）
- synthetic native probe：两留存文件经别名 link/chmod/write 成功、已加载内核策略仍强制
- prior full E2BIG source review：f818dde→6672741（本任务不重复）

**未执行（按范围禁止）**: native/kernel 测试重跑；测试结果以 supplied 身份引用。

## Tool failures and recovery

无。本轮全部工具调用（git 身份核对、文件读取、两次 ordinary 测试、scratch 检查、grep 定位）一次成功，
无 sandbox 拒绝、无超时、无需要恢复的探索性失败；因此无失败影响可述。唯一写入的仓库工件是本报告；
scratch 仅在 /private/tmp/claude。

## Open Questions

- 无。Finding 1 有同一数据路径直接证据支撑，不属不确定项。

## Residual Risk

- **共享流伪造解析面**（Finding 1 的残余面）：在文档补上 first-occurrence 锚定前，任何按仓库内
  dict last-wins 惯用法实现的审计器都可被 Agent 后置伪造行绕过；部署侧（live sync 为用户独立动作）应
  先按上述协议人工锚定第一行。
- **source_sha256 的条件性**：无压缩时无 seatbelt.source.sb 可比对（仅 source_sha256==profile_sha256），
  审计工具若硬性要求两文件存在会误报；建议审计侧以“存在的留存文件逐一比对”实现。
- **marker 测试的环境前提**：tests/test_agent_sandbox.py:113-129 未像 KernelTests.setUp 那样固定
  AGENT_TOOLS_FILE，依赖真实 `$HOME/.config/zsh/agent-tools.zsh` 存在（scripts/agent-sandbox:347-349）；
  缺失时测试会响亮失败（断言 reinstall 消息不匹配）而非静默通过，但跨机/CI 可能假失败。低风险 test-robustness 缺口。
- **压缩路径哈希相等性的仓库内覆盖仅在 native 门控测试**：ordinary 传输测试只证无压缩路径；
  本次由 scratch 补证（未入库）。若后续重构 fileBackedArgv，建议将该断言移入 ordinary 传输测试。
- **包内容完整性**：validateRuntime 只证布局不证模块内容（无 hash pinning），tampered-but-conformant
  包仍会执行——属任务明确排除的 supply-chain 面，记为已知边界而非缺陷。
- **内核测试证据依赖 supplied**：硬链接回归、4108 哈希相等性均在 opt-in native suite 内，
  本次未重跑（范围禁止），结论以任务给定的 26 全过为准。
