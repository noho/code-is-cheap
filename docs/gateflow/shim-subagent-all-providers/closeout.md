# All-provider shim repair closeout

**Final closeout PASS（代码工作单元）**。实现、适用验证、独立双审/修复/复审、draft PR交付核对均已完成。下一入口：用户manual merge，再明确授权live sync；部署和原业务恢复尚未执行。

本次继续 `fix/shim-subagent-message-delivery` / draft [PR #70](https://github.com/noho/code-is-cheap/pull/70)，覆盖九条**现有托管云端 shim 路由**：DS Flash、GLM、GLM Flash、Kimi、MiMo、MiMo Fast、MiMo Flash、Qwen、Hy。`local` 与 OpenAI 订阅 profiles 没有新增 shim。源码最终 helper SHA-256 为 `55a5bd5b5e120cac648d9ad86c366430a9a535bf79d796cf58a79b44ffbb9b9a`；已审源提交 `27e0bf77d9524e9730cfafabd67a44b3c3fad1cd`，base `09337967910277785b82874326d7f49156c9395b`。

## 根因和修复

0.167.0 的任务已存在 child rollout 和 HTTP 请求的原生 `agent_message` 中；先前只看 user message 会漏掉它。实测 `content[].encrypted_content` 字符串承载明文任务。当前 Responses 网关接受该结构并返回 200，却没有把任务交给模型；标准 user/input_text 表示可以执行。修复边界是已观察到的 Responses 表示兼容，不假称定位了网关内部丢弃函数，也不解密真实密文。

九路显式启用 `agent_message_fix`，保留正文顺序/空白/Unicode及作者、接收者、id等元数据，未知/非法目标内容在转发前 sanitized 400；reasoning、工具参数、其它顶层类型不改。Kimi TokenHub 路径还需要仅顶层原生工具展开和响应 namespace 恢复。MiMo Flash 可能返回裸 native call，实际 Lite 描述符在 immediate `input[type=additional_tools].tools`；response-only map 因此读取这两个已证实容器，保持请求字节。恢复仅限本请求实际声明的原生函数，保留参数/ID，没有别名、跨会话状态、MCP 泛化或 app-server RPC 代理。

所有新兼容 flag 仅 route 级显式启用，不继承文件顶层默认；guardian 的模型/凭据映射和原 buffering/retry保持。SSE逐事件流式转发、有界8MiB；active map只接受identity/absent编码，异常不伪造完成。原 unloaded child queue/resume 的 -32600 仍是 Codex 所有权/加载控制，不是 shim 的线程路由实现；本次未绕过它。

## 实际验证与审核

九路 A/B 覆盖通过：A为实际 fresh child 初始任务及同 child 的新 continuation；有独立 MESSAGE API 时还验证单次投递及不含 token 的 consume任务。B为另一 child 实际读取父代未见内容的随机无害文件，有原生执行、call/result span、exit 0和精确 final。Kimi采用A/2+B/2，v1无独立send_message才标N/A；MiMo Flash采用active-map A/4+B/2，16个请求都建六项map并实际调用响应parser，初始精确返回 `LIVE_PROBE_OK`。实际响应已有namespace，所以MiMo此次additions=0；真实旧裸wait的恢复另由原记录replay和真实handler测试验证，没有把空map当激活。

其余七路使用已验证且有明确source/flag/catalog/settings等价的历史正例，DS保留两轮历史条件复用的原断言边界。没有假称最终helper重新调用了九路或验证了当前外部可用性。最后的日志/observer修正有source AST、normal-observer和真实loopback bytes/headers/auth/model/首事件时序等价链，原native captures仍归原始launch hash。

176项适用检查：86项最终受影响测试实际执行，90项既有检查按未变路径复用；控制器另独立重跑最终86项并审计九路保存证据，均通过。MiMo Flash和DS Flash分别完成独立全量deepreview及受影响面复审，四次均正常exit 0/PASS；三项accepted findings均已修复并经两方复核，无新增material finding。详见两份code-review和两份code-rereview及review-adjudication。

复现、失败、启动权限错误、A/3隔离测试中止、各版reader/verdict和source snapshots全部保留。v2 FINAL可能先于下一次update-wait到达，旧探针强制再等新消息会卡住；新短场景按真实parent FINAL和独立child completed turn判断，仍拒绝超时单独、旧/错作者/错token回执和失败调用，不弱化实际投递要求。业务线程或修复Agent未被中止；仅A/3独立测试app-server按已核对fd2身份清理，原wire和rollout已保存。

当前总索引：[controller-final-matrix.json](controller-final-matrix.json)；实际命令/原生ID/参数/结果：[location-implementation-validation.md](location-implementation-validation.md)；最后修正及适用性：[review-fix-validation.md](review-fix-validation.md)、[review-logging-fix-validation.md](review-logging-fix-validation.md)；裁决：[review-adjudication.md](review-adjudication.md)。源码/证据冻结v1/v2均保留，未触碰三个无关runner artifacts。

## 部署边界和下一入口

用户要求的Kimi私有override已在测试前完成，schema provider为`kimi`，Codex/Claude分别使用`kimi-k3`/`kimi-k3[1m]`，URL/key与相应DS Flash连接相同，文件0600。实际Kimi使用Tencent TokenHub；仓库只保留相等性和模型/权限证明，不含凭据或私有URL。

**源码/路由未sync live，服务未重启；原业务父线程的技术回报继续暂缓。** 自选股、调度账本、新闻run/receipt和其它业务资料未改动或恢复。用户手工merge并明确授权部署后，从含approved changes的checkout执行：

```bash
./scripts/sync-codex-agent.sh
~/.codex-agent/bin/codex-auto-review-shim-service status
# 仅重启已经安装的新代码/路由时：
~/.codex-agent/bin/codex-auto-review-shim-service restart
```

sync脚本会重启已加载的launchd shim。没有skills/runner改动，不需其它sync脚本或`source ~/.zshrc`。仅为HTTP shim补丁通常无需重开Codex会话：服务更新后下一请求使用新逻辑；应在会话空闲时执行重启。旧空跑任务不会自动重做；若原parent已卸载，按Codex原生方式先加载parent，再明确派新任务/续接。原业务恢复和部署后的技术回报另行执行，本次不自动研究新闻。

未来真实密文、重复selected callable、其它descriptor容器/模型版本或压缩active响应由shim/provider维护者按新证据开启有界兼容工作；当前identity/8MiB及已配置模型/模式边界不被扩大成所有未来provider能力承诺。默认compound all的旧提示由probe维护者按需更新；本次可复现命令明确使用short A/B。当前无未分类residual，也无未修复accepted blocker。

## 交付核对

控制器交付核对PASS / draft-PR-pass。远端source head `27e0bf77d9524e9730cfafabd67a44b3c3fad1cd` 与本地完全一致，base维持 `09337967910277785b82874326d7f49156c9395b`。通过fetched完整Git对象核对全部581个变更文件、26,502,195字节binary diff，SHA-256 `c66de4066f92589b0dc242d58a018d18c654ae8fe91088f16aed17c5e3220f62`；本地与远端diff相同，536个冻结source/evidence文件在提交中逐一匹配。两次PR metadata读取确认head/base稳定、open/draft、同仓库正确分支、标题/正文准确，mergeable=true。没有configured GitHub Actions workflows，commit statuses/check runs/workflow runs均空，远端CI为N/A；本地适用检查PASS。见[delivery-verification.json](delivery-verification.json)。

三份原始diff/失败测试log存在数据自身的尾部空格，已按冻结hash原样保存；其余已暂存内容的`git diff --cached --check`通过。没有将这三份证据的格式诊断改写为源码失败。最后关闭提交仅增加closeout/交付状态记录，最终远端head/完整diff证明另存`/private/tmp/shim-all-provider-pr70-final-delivery.json`，避免文档自引用提交循环。

没有用户提供的GitHub issue，issue关联/closeout comment不适用。PR保持draft；未merge、approve、mark-ready、request-reviewers或对外comment。完成后下一入口：用户manual merge及授权live sync；不得在未sync前向`01a1b57a-8e5d-76e1-934d-1847728240be`投递技术回报。
