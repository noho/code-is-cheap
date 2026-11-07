# Shim subagent 消息投递修复 closeout

## Result and current gate

代码修复、实现验证、双路完整审核和必要双路受影响面复审已完成。当前 gate / next entry: `ready-to-open-draft-PR` → commit/push → create draft PR → 总控交付核对。此刻未声明 PR gate 或 final closeout pass；后续交付事实在本文件补全。

Branch: `fix/shim-subagent-message-delivery`; base: `09337967910277785b82874326d7f49156c9395b`。用户授权调查、最小修复、真实 A/B 回归；AGENTS.md 授权分支、指定 runner 委派、提交、push 和 PR，用户手工 merge。三个既有 `docs/reviews/runner-handle-loss-20261023-*` untracked 文件未修改或纳入。

## Root cause and change

任务并未丢失在 spawn/followup 队列或 child rollout：0.167.0 的原生 `agent_message` 已携带正文，实测 `content[].encrypted_content` 字符串与父端 task 参数相同，是明文。原生 child HTTP 请求也完整携带任务。当前上游网关对该表示返回 HTTP 200，但模型未消费任务；相同任务改为标准 `message/input_text` 后可执行。私有网关内部具体丢弃函数不可见，根因定位到该 Responses 兼容边界，不假称已定位其内部代码。

DeepSeek 路由独立开启 `agent_message_fix`，转换精确 `agent_message` 类型为标准 user 消息，保留正文块顺序、空白、Unicode 和来源/接收者/id/其他元数据的文本表示。原生 rollouts 与请求其它语义字段保留。未知/非法的已知 Agent item 内容明确 400；其它顶层类型透传。推理加密内容、函数参数、其它 provider 和原 app-server RPC 生命周期保持既有职责。该适配不解密真正密文。

Shim 原用途是将继承第三方 provider 的 guardian 请求模型 `codex-auto-review` 映射为实际支持的模型；现在同时负责私有连接凭据和有界协议兼容。线程创建、resume、queue 的 owner 是 Codex app-server。原 unloaded child 的 -32600 控制限制与本次正文兼容问题分开；没有绕过、重写或修改原会话。

## Verification

- 71 项离线测试通过：shim delivery 11、install endpoints 38、provider registry 11、shim service 11；git diff/check 和真实 socket framing/压缩/凭据/guardian 检查通过。
- 修复前原生基线确实失败；沙箱启动失败为零模型请求，单独保留。两次真实 DeepSeek 原生候选运行通过，使用当前 0.167.0 和新父子线程，临时候选 listener 转发到既有 8788，不是 synthetic SSE 或直接注入子任务。
- A 同一 child 三个不同 turn，严格返回 LIVE_PROBE_OK、LIVE_FOLLOWUP_OK、send_message 中的独立 token；最后 followup 不含 token；通信 child 无工具调用。
- B 另一 child 实际执行唯一 cat 调用，输出/exit 0/final 与 prompt 未包含的随机文件内容一致；parent 未读取文件。
- 每轮 15 个真实请求，27 项转换含历史重放；ingress/egress 与实际 outbound hash 关联，非目标内容/其它字段一致，父子 ID、parent_thread_id、agent_path 与原生工具记录可核对。总控独立审计、双路 reviewer 复核了保存证据。
- 原生成功 final-code parent `01a1b62c-12cb-77a3-a479-f14f6e38b218`，A child `01a1b62c-23b6-7f42-aca0-a3e3b2568035`，B child `01a1b62c-5643-7b33-bf4b-c9cb869260fe`。

实际命令、结果、所有尝试及证据链接见 [implementation-validation.md](implementation-validation.md)，可重复驱动为 [native-probe.py](native-probe.py)，脱离模型的证据审计为 [audit-native-evidence.py](audit-native-evidence.py)。[controller-validation.json](controller-validation.json) 锁定实际代码/测试/probe hash；[review-adjudication.md](review-adjudication.md) 记录审核路线、发现裁决和风险分类。

## Review and docs decision

gpt-6-sol / Codex 完成 plan、实现与 accepted 修复。完整 review 为 mimo-flash / Claude 和 ds-flash / Claude 并行；均 exit 0，无需备用 runtime。ds-flash 的低严重度隐私发现 accepted，gpt-6-sol 脱敏后两路并行受影响面复审均证实已修复。mimo-flash 的假设未来 top-level agent_message_v2 前缀建议 rejected-with-reason：当前 schema 无该类型，前缀分类会改变其它顶层 item 的透传不变量。无未修复 accepted finding。

README 中英文已更新；保留 baseline、setup failure、两轮原生回归的 harmless captures、命令、来源与哈希。两段旧 assistant 回复中不必要的私有业务上下文显式脱敏，并记录原文哈希与源行号；真实新 probe captures 均不含业务数据。Manifest 从任务目录执行 `shasum -a 256 -c evidence/sha256sums.txt`，控制文档更新时刷新对应 checksum，原生 captures 未变。

## Operations, remaining risk and next owner

运行中 8788 仍是原版；未做 live 部署/重启。仓库 AGENTS.md 明确要求 live deployment 获用户授权。用户手工 merge 后，从包含 approved changes 的 checkout 同步：

```bash
./scripts/sync-codex-agent.sh
~/.codex-agent/bin/codex-auto-review-shim-service status
# 单独重启已安装的新代码/路由时：
~/.codex-agent/bin/codex-auto-review-shim-service restart
```

sync 脚本在 launchd 服务已加载时会重启它。未改 skills/launcher，所以 sync-skills.sh、sync-agent-tools.sh 与 source ~/.zshrc 不适用。shim 更新在后续 HTTP 请求生效，不需要为加载此补丁新开 Codex 会话；现有空跑任务不会因此自动重做。原 parent 若已卸载，按 Codex 既有方式加载 parent 后再显式 native followup/new task。本次不恢复新闻 run、不发布业务 receipt、不改自选股、调度账本或业务资料。

风险 owner / destination：当前版本交付问题 fixed in current slice；未来真实密文、Codex schema/新 provider/单路由 env 部署为 maintainer 后续兼容 work unit；私有网关内部更细归因由 endpoint owner 后续调查；既有业务任务恢复由原父线程在授权部署后另行执行；live 同步由用户授权；并发 parent stream client-gone 观察由 runtime owner 在复发时单独排查。新任务两轮成功不承诺旧 child 自动恢复或所有网关/未来版本通用支持。

## PR delivery / final closeout

Pending concrete PR creation and controller delivery verification. No GitHub issue was supplied, so issue link/closeout comment are not applicable. Next entry: necessary commit/push and draft PR creation; final closeout will record the actual PR and source identity before marking this code work unit complete.
