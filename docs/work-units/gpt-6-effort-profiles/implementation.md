# Implementation notes

工作分支：`feat/gpt-6-effort-profiles`。基线：`main` / `bb3454de0d461d97aab1c3bfc71dd87d18b49d61`。

## 实现

- Astra：`gpt-6-astra` / high、`gpt-6-astra-x` / xhigh、`gpt-6-astra-max` / max，上游均为 `gpt-6-astra`。
- Sol：`gpt-6-sol` / high、`gpt-6-sol-x` / xhigh、`gpt-6-sol-max` / max，上游均为 `gpt-6.1-sol`。
- 更新模型卡、CLI/App launcher 和 title、runner help/list/dispatch、launcher 及 sandbox 两处订阅分类。六个 provider 不查询网关 API key，不使用 shim。
- `gpt_codex`、`sol`、`astra` 仍选择相应默认 provider；Luna 保持 max。business 继续由基础 Sol 卡同步两个顶层默认键，因此 effort 更新为 high。
- preflight 通过真实 runner catalog 和 launcher 函数发现 provider；安装和同步通过现有模型卡目录 glob 发现新卡。这些脚本无需增加列表或清理逻辑，使用现有 fixture 验证真实发现。
- 英中 README 与 sub-agents skill 更新 provider 和推理等级说明。文档说明旧卡、App data/session 和个人配置保留，旧卡不代表 runner 支持旧 provider，旧 shell 函数需新 shell 或显式 `unfunction` 清除。
- 移除受管 `gpt-6-astra-xhigh` 卡和 launcher，不提供旧 runner 别名。不改写历史 reviews/work-units，不增加已安装用户数据清理。

## 验证记录

实际命令、时间、stdout/stderr 和退出码见同目录 `validation.log`。测试 subprocess 使用 `PYTHONPATH=tests`。

- 9 个受影响模块：188 tests，175 通过，13 skipped；命令退出 0，耗时 62.77 秒。
- 矩阵覆盖六个 provider 的 runner → launcher → fake native model/effort、runner resume、交互与修复 resume、tmux title、两种 App 入口、真实私有 home compose、重复安装与同步、卡权限、真实 preflight 缺卡、sandbox check/launch 的订阅 key 分类及 OpenAI 域名。
- 重复同步验证旧卡保留、business 模型/effort 更新、其它键/账号数据及文件模式保留；原有 failure/rollback coverage 保留并通过。
- 补充 `gpt_codex` 选择基础 Sol high、business 嵌套个人模型设置保留的两项定向验证，退出 0。
- 两份修改的 zsh 脚本分别通过 `zsh -n`；sandbox Python 与修改的测试通过 `py_compile`；`bash scripts/validate-skills.sh` 通过。
- 13 个跳过项均为原有显式 opt-in 的 macOS Seatbelt/kernel/runtime 测试；本轮未启用。没有因沙箱拒绝导致的测试失败，未绕过授权。App 测试截获 `/usr/bin/open`，未打开真实 App。

## 交接

实现 Agent 未提交、push、创建 PR、部署或修改真实 HOME。独立双 review、裁决、提交和 PR 由控制器继续处理；本文件不作审核或 closeout 裁决。
