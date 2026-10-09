RUNTIME/PROVIDER/MODEL: claude/mimo/mimo-v2.6-pro[1m]
CANARY=mimo-fdaad899

# Code Review — E2BIG final fix (e2big-mimo-claude-20261009-r3)

## Scope

- Mode: current changes（独立 $deepreview，task e2big-mimo-claude-20261009-r3）
- Branch or PR: fix/agent-sandbox-large-policy-launch（无 PR，base...HEAD 两点间 diff）
- Base: f818dde2d361dea5313aefb7d7383399f947e0c9
- Frozen HEAD: 6672741e6a58939aba3a65c57c03843d2c92aa10（审查前后各核对一次，均一致；git status 仅含他轮 review 产物与本报告）
- Output file: docs/reviews/e2big-mimo-claude-20261009-r3.md
- Included scope:
  - 完整 diff（f818dde...6672741，2 commits，10 files，+545/-4）：scripts/agent-sandbox、scripts/agent-sandbox-launch.mjs、scripts/sync-agent-tools.sh、tests/test_agent_sandbox.py、tests/test_agent_sandbox_launch.py、tests/test_install_endpoints.py、README.md、README.zh.md、skills/sub-agents/SKILL.md、docs/reviews/agent-sandbox-e2big-validation-20261009.md
  - 核心链路逐段走读：scripts/agent-sandbox（preflight→settings 构造→exec）→ scripts/agent-sandbox-launch.mjs（decodeArgv / compactDenyRules / fileBackedArgv / validateRuntime / main）→ 已装 srt 0.0.79 Node 包（package.json、dist/cli.js:394-474、dist/utils/shell-quote.js 全文、dist/sandbox/macos-sandbox-utils.js 的 renderRule / generateReadRules / generateWriteRules / generateMoveBlockingRules / generateReadDenyUnlinkRules / groupLiteralDenyPaths / entryBaseDir / getAncestorDirectories / escapePath / wrappedCommand）→ sandbox-exec 加载 → --verify → runner
  - 配套映射：dist/sandbox/sandbox-config.js（settings schema）、dist/sandbox/sandbox-manager.js（filesystem.* → readConfig/writeConfig）
- Excluded scope（按任务约束）：其他 reviewer 报告、prior MiMo logs、business inputs/history、原始派发命令、endpoint/auth/key 文件、环境变量、用户会话、无关仓库模块；原生内核测试不重跑；无网络、无 git 写、无子 Agent。scratch 仅在 /private/tmp（本会话沙箱写限制下落在 /private/tmp/claude/ 子树）
- Parallel review coverage: 无（任务禁止派发子 Agent；全部走读与裁决由本 reviewer 完成）

## Findings

### 1-未修复-[低]-预检在 non-spawning 校验之前先执行未验证的 srt 二进制

- **入口/函数**: `scripts/agent-sandbox` `main()` 预检段（含 `--check` 全路径）
- **文件(行号)**: scripts/agent-sandbox:367-372
- **输入场景**: PATH 上解析到不受信的 `srt`（旧安装残留、目录注入等），调用 `agent-sandbox --check ...` 或任何启动
- **实际分支**: 先执行 `subprocess.run([srt, "--version"])`（第 367 行），随后才执行 `node agent-sandbox-launch.mjs --validate srt`（第 370-372 行）
- **预期行为**: 本轮新增的 "non-spawning package/module-layout check" 应在执行被检对象之前完成结构校验；`--check` 文档语义是 "validate setup without starting a sandbox or Agent"，不应执行尚未通过结构校验的 srt
- **实际行为**: 仅回显 `0.0.79` 的 standalone shim 在被拒绝之前已经被执行一次；tests/test_agent_sandbox.py:210-218 的 `test_preflight_rejects_standalone_srt_before_reporting_success` 断言的正是"先执行、后拒绝"的序列（returncode≠0 且无 setup_status=ok，但 shim 的 `echo` 已跑）
- **直接证据**: scripts/agent-sandbox:367 版本子进程先于 370 的 validation 子进程；validateRuntime 本身确认 non-spawning（agent-sandbox-launch.mjs:128-144 仅 realpath/readFileSync/statSync/accessSync）；`shutil.which("srt")` 解析到什么，367 行就执行什么
- **影响**: 预检/`--check` 阶段以用户权限在沙箱外执行未验证二进制（任意代码执行面）；与校验器 "non-spawning" 的自我定位不一致。启动路径最终 fail-closed（standalone 过不了 validateRuntime），但执行副作用已经发生
- **建议改法和验证点**: 将 validateRuntime 调整到版本检查之前（结构通过后再核对 `--version` 数字），或 `--check` 阶段只读 package.json 做结构校验、完全不 spawn srt。验证点：把写 marker 的伪 shim srt 置于 PATH 首位跑 `--check`，断言 marker 从未产生、stderr 含 reinstall 指引
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 低

### 2-未修复-[低]-受保护策略证据文件可经硬链接别名被改写（路径规则不绑定 inode）

- **入口/函数**: 沙箱内 runner 的任意本地工具（Bash/Python）
- **文件(行号)**: scripts/agent-sandbox:420、434-443；scripts/agent-sandbox-launch.mjs:114-123；对照 dist/sandbox/macos-sandbox-utils.js:331、356、535-558、663、683、697
- **输入场景**: runner 执行 `link(state/seatbelt.sb, cwd/alias)`（或 source.sb），随后经 `cwd/alias` open(O_WRONLY)+write
- **实际分支**: denyWrite 生成 `(deny file-write* ...)`、move 生成 `(deny file-write-unlink file-write-create ...)`，filter 只含固定路径的 subpath 及其祖先 literal；cwd 是 write root（agent-sandbox:420 `writes = [str(state), *write_roots]`），新名字判定为 write root 内的 file-write-create，无 deny 命中；之后 file-write-data 作用于 alias 路径，同样不命中
- **预期行为**: README/验证文档宣称的 "protected seatbelt.source.sb / seatbelt.sb"、"write-denied" 应覆盖到达同一 inode 的一切写法。repo 自己承认路径规则不绑定 inode（scripts/agent-sandbox:53-54 "Seatbelt checks resolved paths, not inode identities"，并对读禁用项拒绝预存硬链接），但运行期新建链接没有对应防线
- **实际行为**: 直接写/直接移动已被拒（tests/test_agent_sandbox.py:171 断言 `profile_write=PermissionError`；state 目录 rename 也被 move 规则的祖先 literal 钉住，entryBaseDir=entry.path 使 getAncestorDirectories 含 state 本身）；但硬链接别名通道没有任何规则覆盖，可在 runner 存活期间改写两份策略文件的内容
- **直接证据**: macos-sandbox-utils.js:683/536 规则只以路径 filter 表达；663 行 `(allow file-write* ...)` 覆盖整个 write root；agent-sandbox-launch.mjs:114-123 的 `wx`+0o400 只约束创建期与直接路径写。link(2) 在 Seatbelt 操作映射中按目标路径 file-write-create 判定——该映射本身本轮未做内核验证（见 Open Questions 验证点）
- **影响**: 仅证据完整性：不影响已加载的内核策略、不影响启动前 verify 结论、无数据外泄或越权；但事后审计 seatbelt.sb / seatbelt.source.sb 时可能被 runner 伪造的策略误导
- **建议改法和验证点**: 启动时（spawn 前）把两份策略的 SHA-256 打进 stderr（runner 无法收回已输出行），收尾比对；或为两文件设置 uchg 并对 alias 方向补防线。验证点：一次原生探针 `link()`+写 alias 看是否 PermissionError（按约束本轮未执行）；若内核确放行，controller 收证应以 stderr 哈希为准
- **修复风险（低/中/高）**: 低
- **严重程度（低/中/高/严重）**: 低

## Open Questions

- link(2)/rename 在 macOS Seatbelt 的确切操作映射（是否仅按目标路径 file-write-create 判定，还是对源路径另有检查）需一次原生探针确认；按任务约束不离开控制器沙箱做内核测试。若内核对 link 源路径也检查，则 finding 2 不成立，可降为文档性残余。rename 方向已由源路径 unlink deny 覆盖，不在此列。

## Residual Risk

- 原生编译器容量限制未被"消除"：rule body <128 行、同父 <4 项、单名 regex >900 escaped bytes、非 subpath/literal 行等情形不压缩；异父海量/超长名 deny list 仍可能编译失败——fail-closed 于 verify/runner 之前，不减 deny、不扩权、无降级 fallback（README 与验证文档 Limits 已如实声明）
- `--check` 不彩排 decodeArgv/fileBackedArgv/压缩与原生编译：结构校验通过后启动仍可能 fail-closed 收场。钉死 0.0.79 下布局是确定性的，概率极低，但 preflight 与启动的失败面不完全重合
- tests/test_agent_sandbox.py:210 的 `test_preflight_rejects_standalone_srt_before_reporting_success` 位于 KernelTests（:113-115 skipUnless 门控），普通套件不覆盖 agent-sandbox→launcher 的校验接线回归（LaunchTests 只覆盖校验器本身）；建议挪出内核门控
- LaunchTests 内嵌 quote() 副本（tests/test_agent_sandbox_launch.py）而非引用包内 dist/utils/shell-quote.js；本轮回对二者逐字符一致（空串/裸词字符集/`'"'"'` 规则相同），0.0.79 钉死期内无害，升级 srt 时需同步
- 信任根仍是已安装 srt 包内容完整性：validateRuntime 只校验 name/version/bin 布局与必需模块可读（agent-sandbox-launch.mjs:128-144），不校验 dist 内容哈希；改前策略同样由 srt 生成，信任面未扩大，但审计"策略由谁生成"时应记住这一点
- case-alias（大小写别名）行为依赖内核路径匹配语义：原/压对比只断言两者等价（tests/test_agent_sandbox_launch.py:164-168 probe 含 value.upper() 路径），未断言一律禁读；属 srt/内核既有语义，非本补丁引入
- 供给证据（验证文档：4108/4108 内核查询+实际禁读、原/压内核对比、25 native Seatbelt、92 ordinary 等）仅作对照阅读，未计入本轮自有执行；未重跑原生内核测试

## Coverage（走读与验证覆盖）

核心链路逐行走读（禁止猜测，均以直接证据落锚）：

1. **scripts/agent-sandbox**：load_denies（含硬链接/符号链接收拢）→ parse_runner → 预检（node/launcher 可读性、srt 版本、validate 子进程、输出路径）→ write_boundary → prepare_codex/claude → settings 构造（denyRead/denyWrite/allowWrite/fixed_files）→ boundary.json → execvpe(node, launcher, srt, profile, --settings, --, inner)。确认 `--check` 在 validate 之后、建 state 之前返回 setup_status=ok；profile/source 进入 denyWrite；inner 以 `/usr/bin/env NO_PROXY= no_proxy=` 包裹。
2. **scripts/agent-sandbox-launch.mjs**：
   - decodeArgv：只接受 srt 0.0.79 quote() 的规范形（单引号串 + `'"'"'` + 裸词字符集），拒绝操作符/双空格/尾空格/未闭合引号；
   - compactDenyRules：仅重写 srt renderRule 产出的四种 deny 形（file-read* / file-write* / file-write-unlink file-write-create / file-write-unlink），同规则内同父同 kind 的 literal/subpath 兄弟合并为锚定 regex 并集；literal 尾 `$`、subpath 尾 `(/(.|\n)*)?$`；≥128 行、≥4 项、≤900 escaped bytes 三个阈值；不碰 allow、carve（require-all/require-not）、deny default、其他 op、规则顺序与 message；
   - fileBackedArgv：quote 回环校验、env 前缀白名单（仅 `-u NAME` / `NAME=value`）、布局钉死（env…/usr/bin/sandbox-exec -p <(version 1)…> <abs shell> -c <exact inner>），随后才 `wx` 写 source（0o400）与 seatbelt.sb（0o600→0o400），splice 换 `-f`；
   - validateRuntime：realpath→packageRoot→package.json name/version/bin 与三模块可读，非派生；
   - main：spawn 钩子仅拦 `shell:true` 单串调用且只允许一次，转 shell:false 后交回原 spawn；`syncBuiltinESMExports` 后 import cli；非 shell spawn 原样放行（含 srt 的 log stream）。
3. **srt 0.0.79 包对照**：package.json（type:module、bin srt=dist/cli.js、version 0.0.79）；dist/cli.js:406 `command=quote(commandArgs)`、:437 `spawn(sandboxedCommand,{shell:true,...})` 与钩子契约一致；dist/utils/shell-quote.js 与 decodeArgv 互逆（含 `'`、空串、`=` 起始、裸词集）；macos-sandbox-utils.js escapePath=JSON.stringify（与压缩输出编码一致）、SBPL_STRING_MAX_BYTES=900、MIN_DENY_GROUP_SIZE=4（与阈值一致）、renderRule 文档明确 sibling filters 为 "one of `filters`"（OR 语义，压缩的并集语义成立前提）、entryBaseDir(entry.path) 使 move 规则 literal 钉含 state 目录；settings schema（filesystemPathEntrySchema literal 形）与 agent-sandbox 写出的 srt.json 形状一致；sandbox-manager.js getFsReadConfig/getFsWriteConfig 映射 denyRead→denyOnly、denyWrite→denyWithinAllow 确认 denyWrite 生成的是 `deny file-write*`（含 data/mode/create/unlink），固定文件的直接写、chmod、unlink 均被拒。
4. **部署与文档**：sync-agent-tools.sh 部署 launcher 与 agent-sandbox 相邻；test_install_endpoints.py:955 断言部署字节一致；README.md/README.zh.md/skills/sub-agents/SKILL.md 的行为声明（等价压缩、受保护 source/effective、-f 加载、fail-closed、失败归类）与实现逐条对上。
5. **测试走读**：tests/test_agent_sandbox_launch.py 全部（decode 各类坏输入、validate 非派生+四类拒绝、大 profile 字节保持/0400/重复拒绝/argv 减肥、布局漂移 fail-closed 且不落盘、压缩语义近失配/子孙换行/元字符、原/压内核对比含写与 rename）；tests/test_agent_sandbox.py 新增三处（profile_write、standalone 预检拒绝、4108 大名单全量 verify）。

## Verification（本轮自有执行；与供给证据严格区分）

自有执行（本会话内，普通测试与 /private/tmp scratch，无原生内核）：

- scratch 探针全部通过：
  - decodeArgv 对真实 srt 0.0.79 quote() 是左逆（引号/空串/Unicode/换行/制表/反斜杠/`=`/shell 元字符/50 词长列表），并对非规范分隔与操作符一律抛错；
  - compactDenyRules 在对抗性名单（正则元字符、引号、换行名、反斜杠、emoji、600+ 长名、ab/abc/abcd 前缀对、首尾空格、NFC/NFD）上：覆盖与原文语义逐点一致（literal 精确 / subpath 含子孙与换行子孙）、near-miss（`extra`、尾换行、上界路径）不多禁、无条目丢失、每条 regex ≤900 escaped bytes、127/128 行阈值边界正确、<4 组不合并、混 kind 分组不互相污染、carve/allow/deny default/其他 op 原样、多规则顺序与 message 保留；
  - fileBackedArgv 用真实 quote：布局接受、`-p`→`-f`、覆盖经压缩保持、source 仅在压缩时落盘且字节一致、`wx` 拒绝重复写；
  - validateRuntime 接受真实安装、以 reinstall 指引拒绝 standalone；
  - 换行/引号文件名不能注入 SBPL（JSON 字符串转义保持单行、良构）。
  - 过程注记：初版 scratch 的 mkRule 漏写 `deny` 前缀、coverage 传空原名单，导致一批假失败；修正 harness 后全绿——失败归 harness，不归实现。
- 仓库普通测试（python3 -m unittest）：tests.test_agent_sandbox_launch 6 项（1 内核跳过）OK；tests.test_agent_sandbox 17 项（6 内核跳过）OK。
- 冻结身份：审查前 HEAD=6672741e6a58939aba3a65c57c03843d2c92aa10，报告落盘后复核一致；未做任何 git 写。

供给证据（验证文档等，未在本轮重跑，不计为自有执行）：4108 全量内核查询与实际禁读、原/压内核访问对比（Unicode/引号/元字符/换行/别名/near-miss/写/rename）、25 项 native Seatbelt、92 项 ordinary、E2BIG 复现与 65535 literal 上限实验。其结论与本轮静态走读和 scratch 探针不矛盾。

## Residual limits（本审查自身的边界）

- 未重跑任何 native Seatbelt/内核测试（按约束不离开控制器沙箱、不扩权）；finding 2 的 link(2) 操作映射因此保留一个原生探针验证点。
- 未读其他 reviewer 报告与 prior logs，结论独立形成。
- srt 包以安装快照（/Users/leo/.local/share/agent-sandbox/node_modules/@anthropic-ai/sandbox-runtime）为对照对象，未做供应链哈希核对。
