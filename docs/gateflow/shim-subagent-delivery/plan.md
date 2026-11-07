# Shim subagent message delivery：调查与最小修复计划

日期：2026-11-07。角色：总控指定的 gpt-6-sol / Codex runtime planner/investigator；未再次派发调查或实现 Agent。本轮只做取证、隔离通信基线与计划，未修改实现、服务、配置或既有会话；工作分支为已存在的 `fix/shim-subagent-message-delivery`。

## 结论与证据强度

**任务没有从子线程 rollout 丢失。** 原生 `spawn_agent`、`followup_task`、`send_message` 的任务正文均已写入子线程的 `response_item.type=agent_message`，正文放在其 `content[].type=encrypted_content` / `encrypted_content` 字段中。六条指定会话样本的该字符串与父端工具参数 `arguments.message` 逐字相等，实际是明文任务，不是本次调查解密所得。

**新的真实原生基线进一步证明：任务也没有在 Codex 到本地 shim 的 HTTP 请求之前消失。** 全新父子线程经只观察、不改包的临时 loopback relay 转发到现有 `127.0.0.1:8788/v1/responses`；子线程初始请求与 followup 请求都带有上述结构和完整的任务标记，但两次子 final 都未返回要求的 `LIVE_PROBE_OK`。这是实际 DeepSeek 模型、原生 collaboration 工具和真实子线程，不是伪造模型 SSE 或注入人工子回复。

因此，已定位到的故障边界是 **原生 v2 inter-agent Responses 表示到当前上游模型可见文本之间的兼容性**。本地队列/rollout 已接收任务；当前 shim 无相应兼容转换。不能声称已经找到私有网关内部某个具体丢弃函数，也不能仅凭目前证据断言只是不支持外层 `agent_message`，或只是不支持嵌套 `encrypted_content`。

优先方案：在 DeepSeek 路由上，将已观测的 `agent_message` 整项无损地转换为标准 Responses `message(role=user, content=input_text[])`。总控已有独立 HTTP 对照，标准表示能正确执行同一任务；该对照是诊断证据，不能代替修复后的原生 A/B 验收。

## 直接证据

### 安装版与仓库、调用链

- 本机 `codex --version`：`codex-cli 0.167.0`；入口 `/opt/homebrew/bin/codex`，npm 包安装目录含原生二进制与资源，未发现随包 Rust 源码。没有把其他版本的源码当作 0.167.0 实现证据。
- 仓库与 `~/.codex-agent/bin/codex-auto-review-shim` 的 SHA-256 均为 `7ae5d6d7dc86050b466d06cc63685eb1589d873cf730fa0ac3479dfed44d7cc7`；仓库与安装版 `shim-routes.json` 均为 `afd1e15ca3a914993987382abaf148227ef6a97a796cdb73791b4787bea26bfe`。
- `codex-agent/model-providers.toml:7`：provider `deepseek` 使用 `http://127.0.0.1:8788/v1`，`wire_api="responses"`。`codex-agent/shim-routes.json` 的 8788 路由使用 endpoint `ds-flash`，逻辑模型 `deepseek-flash`，三个现有兼容开关均为 false。只核对选中连接的 upstream model 为 `deepseek/deepseek-flash` 且凭据存在，未输出 key 或私有连接 URL。
- `codex-agent/catalog-sources/ds-model-catalogs.json:21` 声明 `multi_agent_version="v2"`。`codex-agent/profiles/ds-flash/config.toml` 使用对应模型和 catalog。没有通过降级 catalog/禁用多 Agent 绕过问题。
- `codex-agent/bin/codex-auto-review-shim:314` 起的 `_handle` 解压请求，替换模型，以及按开关改 message id / text format / 删除 `additional_tools`，然后构造 HTTP 上游请求。它没有处理 `agent_message` 或其嵌套 `encrypted_content`，也不实现 app-server JSON-RPC。`codex-auto-review-shim-service` 只负责 launchd 安装、重启与监听就绪检查。

### 指定会话：原生任务正文确实在 rollout 中

源文件均位于 `~/.codex/sessions/2026/11/07/`。这里只记录会话身份、行号、长度、比较结果和无害探针文本，不复制新闻任务、研究上下文或业务文件内容。

父文件：`rollout-2026-11-07T18-07-50-01a1b57a-8e5d-76e1-934d-1847728240be.jsonl`。

| 父端行号 / 原生调用 | 子端 rollout / 行号 | 正文字符数 | 子端 encrypted_content 与父 message 相等 |
| --- | --- | ---: | --- |
| 315 / spawn_agent | `rollout-2026-11-07T20-38-11-01a1b604-34fb-7a63-b818-38f9873b6eb5.jsonl:11` | 1244 | 是 |
| 377 / followup_task | 同一新闻子文件：52 | 1348 | 是 |
| 396 / send_message | 同一新闻子文件：61 | 264 | 是 |
| 401 / followup_task | 同一新闻子文件：63 | 96 | 是 |
| 515 / spawn_agent | `rollout-2026-11-07T20-52-22-01a1b611-301f-7973-acc1-4d6108f37dc2.jsonl:11` | 64 | 是 |
| 541 / followup_task | 同一 live probe 子文件：22 | 33 | 是 |

两个子文件首行 `source.subagent.thread_spawn` 分别确认 canonical handle `/root/schedule_news_20261107t2000`、`/root/live_probe_20261107t2052`，parent 均为指定父 ID，版本均为 0.167.0，provider 均为 deepseek。`/root/...` 在这里是 Agent canonical handle，不是要读取的本机目录。

live probe 的实际形状（删去 ID 和内部 metadata）：

```json
{
  "type": "agent_message",
  "author": "/root",
  "recipient": "/root/live_probe_20261107t2052",
  "content": [
    {
      "type": "input_text",
      "text": "Message Type: NEW_TASK\nTask name: /root/live_probe_20261107t2052\nSender: /root\nPayload:\n"
    },
    {
      "type": "encrypted_content",
      "encrypted_content": "只回复一行：LIVE_PROBE_OK。不要调用工具，不要改文件。"
    }
  ]
}
```

初始 task 也是同样形状。live probe 子文件 15、24 行均是询问具体任务的 final；新闻子文件 45、54、67 行也报告没有具体任务。新闻子线程确有 `pwd`、`git`、`find` 类工具调用，不能据此认定它执行了被委托任务或读了目标文件。

父文件 462 行工具输出包含 `thread/queue/add failed: direct app-server input is not allowed for unloaded spawned sub-agents (code -32600)`；499 行包含 `thread/resume failed: cannot resume an unloaded multi-agent v2 sub-agent through its parent ... (code -32600)`。这些是另行直接操作 unloaded child 的失败事实，不解释此前已进入子 rollout 的初始任务为何不可见，不作为本次根因。

窄范围检查 `shim-failed/8788-179405*-req-*.json` 的 26 个请求，仅按 `client_metadata.thread_id/session_id` 寻找两个指定 child，未找到匹配。两个包含新闻 child 回信的 `client-gone` dump 均属于父会话。因此既有失败 dump 不能证明历史子请求的完整 wire 形状；成功请求默认也不保存 body。

总控已有 [原始 live probe 证据](original-live-probe-evidence.json) 和 [HTTP 对照](controller-transport-comparison.json)。后者在同一配置 endpoint 上依次发送同任务：原生 `agent_message + encrypted_content` 得到 HTTP 200 但模型询问任务；标准 `message + input_text` 返回 `SHIM_TRANSPORT_OK`。其 `not_native_regression=true` 标记正确；本计划只读引用，未改动这两个文件。

### 本轮新增：真实 native spawn + followup 基线

最初受控 probe 的 app-server 在父沙箱内启动即 `Operation not permitted`，退出 1，**0 个模型请求，未启动任务**。随后明确使用提权托管命令运行相同范围的隔离诊断；未改服务或全局配置。只通过进程级 `-c` 覆盖 deepseek base URL 到临时只观察 relay，relay 原样转发到现有 8788；apps/plugins 在该诊断进程关闭，cwd 是全新临时目录，sandbox 为 read-only。

- 父 ID：`01a1b621-382e-7830-bf3b-8ed286860bd9`。
- 子 ID：`01a1b621-4922-7a50-9ca8-3d6d12ca8f96`，handle `/root/wire_probe_a`。
- 原生父 rollout：`rollout-2026-11-07T21-09-52-01a1b621-382e-7830-bf3b-8ed286860bd9.jsonl`；14 行 `spawn_agent(fork_turns=none)`，41 行 `followup_task` 指向同一 child；两次 message 都明确要求 `LIVE_PROBE_OK`。
- relay 共观察 10 个真实 HTTP 请求。记录 2（零起算）是 child 初始请求：`input` 含 5 个 `message`、1 个 `agent_message`；正文 `encrypted_content` 长 102 字符，含独有 `NATIVE_WIRE_PROBE_20261107` 标记和 `LIVE_PROBE_OK`，SHA-256 `78dfc33e1f9bad5588b987b2a7e0206f8030cd6f3ea755d5ddde5fed5d8b82b4`。
- 记录 6 是同一 child followup：历史初始 `agent_message` 与新 task 均存在；新正文长 103 字符，同样包含两个标记，SHA-256 `0578230fefbd4dfbfa72e04ca32e0fb5fa5236b12b0d3f1872237652e594b24b`。
- 实测 HTTP item keys 为 `type,id,author,recipient,content`；任务头是 `input_text/text`，正文是 `encrypted_content/encrypted_content`。rollout 内部的 `internal_chat_message_metadata_passthrough` 未在这两个 wire item 中出现。
- 两次 child final 都回答通用的“Diagnostic received...”诊断说明，均不等于 `LIVE_PROBE_OK`。child 只调用过 `list_agents`，未调用 shell 或读取文件。parent 的 `list_agents` 输出另含 child final，因此不能仅凭 parent 能复述 final 就断言上游已支持普通文本形式的 `agent_message`。
- parent turn completed 后关闭 app-server stdin，等待实际退出；外层进程退出 0，约 21.22 秒。没有 kill、重试到成功或修改老会话。该结果是 **A 的修复前失败基线**，不是 A 验收通过。

只存请求结构、类型、长度、哈希、标记布尔值及这次无害诊断事件的本机证据：

`/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/shim-subagent-native-baseline-1c6l3k4n/wire-shapes.json`

SHA-256：`bbfa9a1e9f85730261de1fbc8c0b8514e99891991fe8cd633dc1e3f89c1e5c3a`。未保存 auth headers 或完整 HTTP prompt；该临时文件可供总控核对，不是长期制品路径承诺。

### 版本匹配 schema 与文档

使用本机 `codex app-server generate-json-schema --experimental --out /private/tmp/shim-subagent-schema-20261107`，没有连接或恢复既有线程。`v2/RawResponseItemCompletedNotification.json` 定义：

- `ResponseItem` 的正式分支 `agent_message` 必需 `author,recipient,content,type`；
- `AgentMessageInputContent` 允许 `input_text/text` 或 `encrypted_content/encrypted_content`；普通 `ContentItem` 则不同；
- `ThreadStartParams` 支持 `modelProvider,cwd,config,ephemeral,experimentalRawEvents`；`TurnStartParams` 支持 `threadId,input`。旧 `multiAgentMode` 字段已标为 deprecated/ignored，不用它作为修复手段。

schema 文件 SHA-256：`8c8d487c03a5d189ed57b31430246879287b26dbc04b9fbf134133183016b051`。已实际读取 [OpenAI Docs: Codex App Server](https://developers.openai.com/codex/app-server)，其说明 app-server 使用双向 JSON-RPC、版本匹配 schema 应从当前 CLI 生成；这里以本机 schema 和原生实测为具体字段依据，文档不能证明私有网关实现。

## 边界与拟议改动

实现阶段限定在 `codex-agent/bin/codex-auto-review-shim`、`codex-agent/shim-routes.json`、直接相关测试和该任务证据文档。不开新 orchestration 系统，不改 runner 生命周期、catalog multi-agent v2、app-server RPC、rollout、scheduler、watchlist、业务数据；不读取既有任务的目标业务文件。保留三个不相关 `docs/reviews/runner-handle-loss-20261023-*` untracked 文件原样。

1. 新增明确的路由开关（例如 `agent_message_fix`），默认 false，只对 `ds-flash:8788` 开启。`load_routes` 保留开关；其他 provider、官方直连和无开关路由行为保持原状。没有实测证据时不顺手对所有第三方 provider 开启。
2. 在现有解压后的请求转换路径加入小的独立 JSON helper，仅处理顶层 `input` 数组中 `type=agent_message` 的 item。按原顺序将 `input_text.text`、已观察到的字符串 `encrypted_content.encrypted_content` 转为 `input_text`；保留正文原字节语义、Unicode、空白和顺序，不删掉只有任务正文而没有头部的内容。
3. 生成标准 `message(role=user,content=[input_text,...])`，用普通文本携带原 author/recipient；保留已有 `Message Type / Task name / Sender / Payload` 信封，防止来源身份在标准化中丢失。不要提升为 system/developer。原 `amsg_` id 不能直接冒充 provider 的 `msg_` message id：新 wire item 可省略可选 id。内部 inter-agent metadata 不强塞入标准协议字段；只转发 provider 支持的必要字段。持久化的原生 rollout 仍保存原始 item 和 ID。
4. 这是所选非原生 gateway 的协议适配，不是通用解密器。不得处理 `reasoning.encrypted_content`、function/custom tool arguments、普通 message 或其他保留的加密字段。对未知 content variant 或非法形状须整项明确失败并给出不含正文的诊断，不能只丢掉不认识的片段后继续生成一个看似成功的空任务；具体 HTTP 错误码和 helper 返回契约在实现前核对现有风格，避免引入请求重试或自动换 provider。
5. 沿用现有模型映射、endpoint URL/model/key 单请求快照、凭据替换、压缩恢复、普通 SSE 即时转发和 guardian 身份判定。普通请求不因本次转换获得额外重试/响应缓冲。日志只增加转换条数等结构信息，不新增完整成功请求落盘。

若总控希望进一步分辨外层 type 与嵌套内容的责任，可在实现前做四格、无工具、同任务的受控 HTTP 诊断：原生混合 content、agent_message 全 input_text、标准 message 分块 input_text、标准 message 合并 input_text。必须标为诊断、保留各实际结果；它可选择更小转换，但不能代替下述原生验收。当前已有证据支持一次标准化整个已知 item，避免押注上游支持某个私有变体。

## 验证和验收

### 离线契约测试

补充有意义的 input/HTTP handler 测试：初始 NEW_TASK、followup NEW_TASK、MESSAGE、FINAL_ANSWER；混合 input_text/明文 encrypted_content、中文/换行/空字符串；非目标 item 顺序和内容不变；普通消息、reasoning 和函数加密字段保持不变；未知/非法 content 不被部分吞掉；无开关路由完全不变；identity、gzip、deflate 下结果等价。用无害 fixture，不导入业务会话内容。

通过真实 handler 捕获发出的 Request，核对转换后的标准 message、模型映射、凭据替换、压缩头/长度和正常流式 `read1` 行为；保留 guardian 原判断/重试行为。现有直接相关用例在 `tests/test_install_endpoints.py:867`、`:950` 附近；launchd 范围测试为 `tests/test_shim_service.py`。新增专门的 message 兼容测试文件也可，避免让 endpoint 测试进一步失去边界。

建议运行（新增文件名以最终实现为准）：

```bash
python3 -m unittest discover -s tests -p 'test_shim_subagent_delivery.py'
python3 -m unittest discover -s tests -p 'test_install_endpoints.py'
python3 -m unittest discover -s tests -p 'test_provider_registry.py'
python3 -m unittest discover -s tests -p 'test_shim_service.py'
git diff --check
```

`tests/test_official_catalog_runtime.py` 的 upstream 会人工生成 SSE/tool output，属于 synthetic runtime contract 测试；可复用其 schema/HTTP 取证思路，不能把它跑绿叫作真实 DeepSeek 原生子任务回归。

### 修复后真实 native A / B：必过门槛

不部署安装版。用仓库候选 shim 在空闲临时端口（例如 18788）启动，仅该临时 routes 文件开启兼容开关；显式上游可设为 `http://127.0.0.1:8788`，将 `/v1/responses` 原样送进现有已管理 route，由安装版继续负责私有连接和凭据。这使候选补丁得到真实执行，又不重启/替换 live 服务、不导出 key。也可在总控确认后使用临时 managed endpoint route，但两种方式不能混称已部署 8788。

使用实际 0.167.0 `codex app-server --stdio`，`initialize` 启用 experimentalApi 后 `thread/start` / `turn/start`，进程级覆盖 `model_provider=deepseek`、ds catalog 和该 provider 的 base URL 到候选端口。使用全新临时 cwd；新线程自然隔离，不 resume 指定历史线程。工具调用必须由真实上游模型生成；不得发送人工 spawn function-call SSE、伪造 child output、直接注入任务 item，或用普通两个 user turn 代替 native followup。观察候选 shim ingress 与其去往 8788 的 egress，仅记录本轮无害数据。

**A：初始任务与同 child 的 followup 均成功。**

- parent 明确要求原生 `spawn_agent(fork_turns=none)`；child 初始任务仅回复一行 `LIVE_PROBE_OK`。
- 等真实 child final 后，parent 用原生 `followup_task` 对同一 canonical handle 再发独立任务，也仅回复 `LIVE_PROBE_OK`。
- 核对两个独立 child turn、两个 final 的原始文本严格等于 `LIVE_PROBE_OK`，以及 parent/child ID、原生工具调用、对应 ingress agent_message、egress 标准 message 的任务内容/顺序一致。parent 自称成功、HTTP 200 或进程 0 都不算通过。
- 各阶段固定一轮观察并保留失败；不把多次失败丢掉只报成功样本。

**B：实际 child 文件工具读取。**

- 测试驱动在新临时 cwd 写唯一的无害 `harmless-target.txt`，内容是驱动生成的不可猜测标记。parent/child prompt 只给该文件绝对路径和“用工具读取并返回原文”的任务，绝不包含文件内容；不用仓库业务文件作靶子。
- parent 通过原生 `spawn_agent(fork_turns=none)` 委托一个新 child。child 必须真正执行文件读取工具（如 `exec_command` 的定向 `cat`），然后返回文件实际内容。
- 核对读取工具事件属于 child thread，不是 parent；目标路径等于 fixture 路径，真实 tool output/exit 0、child final 与驱动文件内容一致。只在 final 中出现标记、读过目录、读了 AGENTS、runner canary 观察或 parent 代读都不算通过。
- 保存仅本轮 fixture 的原生调用/工具结果、parent/child ID 和标准化 wire 证据；不记录用户配置、auth headers 或完整全局上下文。

A/B 结束后关闭所建 app-server 输入并等待实际退出，关闭临时 listener；不改既有 session、服务或调度状态。若初始化遇到 EPERM，先记录“启动失败，模型请求数 0”，再按已授权范围用托管提权调用；不把 setup 失败计为模型通信结果。

## 总控后续与当前阻塞

本轮调查/计划已交付。实现尚未开始；A 修复后验收、B child 文件读验收、单元测试、独立双 deepreview、总控裁决、修复闭环与 PR 均未执行，不声称完成修复。阻塞实现的当前门槛是用户指定的“总控先审核计划”；上游私有实现不可见是归因精度限制，不阻止做局部兼容修复和真实 A/B 验证。

总控审核后按仓库 AGENTS 路由派发实现与修复，组织 mimo-flash / ds-flash 两个独立审核，裁决实际证据，再推进 commit/push/PR。未经后续总控方向及 live 授权，本轮不得运行同步或服务重启。最终 closeout 应记录适用的 `./scripts/sync-codex-agent.sh`，提醒用户同步；这里只有计划，不执行部署，也不将临时测试端口结果冒充 live 验收。
