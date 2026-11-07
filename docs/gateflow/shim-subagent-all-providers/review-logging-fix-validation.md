# MiMo-2 日志修复与有界回归验证

本次在现有 `fix/shim-subagent-message-delivery` / draft PR #70 工作，读取 accepted adjudication 和最新 gate 后，只完成指定修复。当前仍是 **fix / affected re-review**，不是交付或部署 closeout。未委派、commit/push、sync/restart、发送消息/callback、访问私有 endpoints/凭据或业务会话，也没有运行真实 provider/native API。

到达时 controller 已集成 README/observer 候选及其 78-test 验证。本报告只描述其后的增量；历史 [review-fix-validation.md](review-fix-validation.md) 未改写。独立证据目录为 [evidence/review-fix-logging](evidence/review-fix-logging/)。

## 最终源码与范围

| 文件 | 本次增量 | 最终 SHA-256 |
| --- | --- | --- |
| `codex-agent/bin/codex-auto-review-shim` | 将同一标准日志块前移到 active-map early return 前；`_summary` 仅迭代数组 tools，非数组安全显示 `none` | `55a5bd5b5e120cac648d9ad86c366430a9a535bf79d796cf58a79b44ffbb9b9a` |
| `README.md` | 三个新兼容开关仅 route 级显式启用，不继承文件顶层默认；legacy flags 维持原惯例 | `bf644dc0c5b7915d54addc45b9333786f052b0b1d74cf8633ea91ebaa6742e95` |
| `README.zh.md` | 同步上述边界；保留已集成的 additional_tools 说明 | `afed954925fd190f2d4317af6cfedb448a8b8b424f42cd3e8bbfacf265d26b31` |
| `tests/test_shim_native_namespace.py` | 5 项日志/等价/时序回归，并让原 Kimi source proof 明确排除已单独证明的日志差异 | `381ffc9bf40f5b16abc6d4dc38b110d6afc65ae05e968d707dc4047799d81bd2` |
| `tests/test_shim_native_evidence.py` | 3 项真实 MiMo A/4、A/3 和实际 A/4 反例回归；fixture loader 可指定 attempt | `914d80e559a38b94d968b00db1946e1887ae3784ce6bd92a1d898b0f33eedc8e` |

除此之外只新增本报告和本次独立 evidence。入口 [entry-manifest.json](evidence/review-fix-logging/entry-manifest.json) 保留 1524 个仓库文件 hash；最终仅上述五个既有文件改变，其余 **1519 个原文件不变**。routes、auditor、native-probe、delivery tests、controller control/adjudication、旧 captures/reports/reviews/source snapshots/freezes、三个无关 runner artifacts 均保持入口字节。检查过程中出现五个 controller 候选保全新增文件，已核对其 receipt 与入口候选 hash 一致，单独记录 [concurrent-controller-additions.json](evidence/review-fix-logging/concurrent-controller-additions.json)，未编辑它们。没有改业务文件。

## 日志与非日志语义证据

helper 入口基线为 `a6246a4bc810125437992791aedcc8f2aa4c072f55e2bcf3691562feecd8e1e6`，与真实 MiMo A/4 的已有 immutable source snapshot 解压字节一致；本次另存入口 gzip，不修改已有 snapshot。相对基线的完整生产差异为 [helper-v-a6246.diff](evidence/review-fix-logging/helper-v-a6246.diff)，全部五文件增量为 [all-authored-changes.diff](evidence/review-fix-logging/all-authored-changes.diff)。

[validation-scope.json](evidence/review-fix-logging/validation-scope.json) 和可复跑的 `verify-scope.py` 证明：只有 `Handler._summary` 与 `_handle` AST 改变；原标准日志三条语句 AST 完全一致，仅位置前移。排除这个诊断块和 `_summary` owner 后，整个 Handler AST 相同；Handler 外整个模块 AST 相同。`_relay_native_response`、`native_agent_request`、JSON/SSE restoration/parser、route/auth/model、guardian/retry、所有模块全局定义均未变。无新全局状态或 native collector fallback；非数组 tools 的诊断防御只在 logging owner 内。错误路径的标准行现在先于原 request-dump 诊断行，dump 的条件和行为不变；native restored/relayed/error 日志原样保留。

真实离线 loopback handler 测试实际比较 A/4 基线 helper 与最终 helper：

- Kimi 顶层 flatten + restore、MiMo immediate additional_tools response-only 两条 active 路径，各测 SSE/JSON × identity/gzip/deflate 入站，共 12 对用例；比较 status、response body bytes、全部响应 headers（仅排除运行时间 Date 和服务标识 Server）、upstream path 和解码后的完整请求 bytes。HTTP framing、identity response encoding 与 Content-Length 去除不变。
- 两条 active 路径的 synthetic endpoint/auth/model 用例只连接 loopback；比较 upstream path、完整转换后 bytes、response status/headers/body，确认原客户端 auth 被测试 managed key 替换、两个 API-key headers 去除、模型改写仍为 `rewrite=json`。没有读取真实 endpoint 文件。
- 两条 active SSE 路径在基线/最终 helper 各阻塞 upstream EOF，先读到第一完整事件；最终标准日志已存在，首块与后续块/headers/请求 bytes 均与基线一致。证明 first-event flush 的先后契约，未声称日志没有任何 CPU/I/O 耗时。
- response-only 顶层 tools 缺失、null、空 object、number、boolean、string、带敏感标记 object 共 7 个子情形，仍从 additional_tools 建 map，原请求 bytes 不变，返回实际恢复后的 collaboration namespace，且有且仅有一条标准日志。

上述日志捕获使用实际 `_log`/stderr，逐条检查 `POST /... -> 200 model=... enc=... rewrite=... tools=...`；同一请求无重复标准行，并保留 `native response: restored=... relayed=...B`。合成 prompt、function arguments、response header、auth key、私有 URL、thread/session 标记均不出现在新增标准日志中。仅使用原 model/encoding/rewrite/顶层工具名摘要/请求路由字段；不遍历 additional_tools 生成另一套日志摘要。已有 nonempty-map SSE/JSON、guardian、flags-off、empty-map、HTTP/error/协议失败、并发隔离与 observer 场景全部继续通过。

## 真实不可变 A/4 与 A/3 回归

测试直接用当前 auditor 读取真实目录，未改旧 audit/verdict、JS 或任何 captured 文件，没有将旧 attempt-1 删除 wait 的合成变体当作这些实际样本。新投影 [actual-a4-a3-current-audits.json](evidence/review-fix-logging/actual-a4-a3-current-audits.json) 保存当前 auditor hash、输入 hashes、判定、map/receipt 计数，不覆盖历史 verdict。

| 样本 | 当前 auditor 重审 | 回归保护 |
| --- | --- | --- |
| `mimo-flash/namespace-scenario-a-attempt-4` | strict PASS，A=true / B=false | 11/11 非空六项 collaboration maps；3 个实际父线程收到的精确 FINAL receipts，来自同一 child 的三个独立 completed turns；源 snapshot 验证通过 |
| 同一真实 A/4 的内存反例 | 全部 FAIL，A coverage=false | 移除 receipts、错误 author、错误 child completed turn、抹掉 active map 均被当前 auditor 拒绝；原文件不写回 |
| `mimo-flash/namespace-scenario-a-attempt-3` | incomplete FAIL，A=false / B=false | transport/maps/source snapshot 仍有效，但生命周期、第三任务完成、MESSAGE 与 completion checks 失败；与真实 B/2 聚合仍不可通过 |

A/4 的 active response 已带 namespace，实际 additions=0，11 次 response pre/post hashes 一致；active map 不等于这次必须修改响应字节。A/3 确有前两项局部完成，完整三阶段 receipt 合同不通过；不能把局部完成或 transport pass 升格为 A coverage。

## 实际命令、计数与修正记录

从仓库根目录执行，完整命令、退出码和耗时见 [validation-results.json](evidence/review-fix-logging/validation-results.json)，stdout/stderr 保存在同目录各 suite `.log`。

```bash
python3 -m unittest discover -s tests -p test_shim_native_namespace.py -v
python3 -m unittest discover -s tests -p test_shim_native_evidence.py -v
python3 -m unittest discover -s tests -p test_shim_subagent_delivery.py -v
python3 docs/gateflow/shim-subagent-all-providers/evidence/review-fix-logging/run-validation.py
PYTHONDONTWRITEBYTECODE=1 python3 docs/gateflow/shim-subagent-all-providers/evidence/review-fix-logging/verify-scope.py
git diff --check
```

`run-validation.py` 并行启动上述三组 unittest，然后对 helper、probe、auditor 和三个 suite 共六个文件执行 `python3 -m py_compile`，bytecode 写临时目录；最后执行 diff check。最终结果 namespace **37**、evidence **36**、delivery **13**，合计 **86 tests 全过**；helper 在整个执行前后均为最终 hash；py_compile / diff check / scope check 均通过。README 的可逆文字修正未新增纯文本镜像测试。

所有初轮失败与修正均保留在 [validation-corrections.json](evidence/review-fix-logging/validation-corrections.json) 及对应 `.initial.log`：

1. 修复前 4 个日志测试产生 20 个失败子用例，真实复现 active 成功路径缺标准行。
2. 初轮 shell 包装误用 zsh 只读 `status` 变量，tests 已执行但 wrapper 失败；保留结果，改用 Python subprocess driver 明确记录退出码。
3. 新 A/4 测试错误假设 active 必须 additions>0，36 tests 中一项失败；按真实 already-qualified 响应修正为检查实际调用与 byte-preserving relay。
4. 最初 helper 编辑改变了非日志语句相对顺序，36 namespace tests 中两个 AST 断言失败；改为只前移共同日志块，使非日志 AST 精确一致。
5. 首次 scope 新文件 allowlist 捕获到五个 controller 并发保全新增文件；保留失败记录，核对其 receipt 并独立固定 hash 后通过，未放宽既有文件五项白名单。

## Native-source 有界适用与待办

本次 **未生成新 native captures**。A/4、B/2 等仍归属于各自原始 launch/helper hashes，不能标成 `55a5bd...` helper 生成。原九路 coverage 依据仍是 [location-current-matrix.json](evidence/location-current-matrix.json)：MiMo A/4+B/2、Kimi A/2+B/2 及七路历史正例（DS 保留 conditional historical reuse），沿用 [final-source-bounded-reuse.json](evidence/location-offline/final-source-bounded-reuse.json) 和原设置/来源约束。现在新增的是 a6246 → 最终 helper 的诊断限定 source proof、真实 loopback byte/headers/first-event 等价和受影响 suite 重跑；不声称最终 helper 对九路做了新 inference 或验证了当前外部可用性。前一 observer 候选的正常分支等价证据也保持原归属，本次未再改 probe。

90 个 prior mandatory checks 按明确 unchanged-path 复用：[unchanged-path-90-reuse.json](evidence/review-fix-logging/unchanged-path-90-reuse.json) 实际核对测试源与既有通过日志 hashes，涵盖 endpoint installation 38、provider registry 11、shim service 11、model catalogs 30。结合最终 86 项实际运行，共 **176 项适用检查 = 86 新执行 + 90 有界复用**，不是 176 项新执行。相关配置、测试源、旧日志和九路 captures 的入口 hashes 均未变，生产非日志语义按上述 source/handler 证据适用。

本 Agent 修复与离线验证已完成；没有遗留失败测试。controller 后续负责冻结 v2、两路独立聚焦复审、裁决及之后的 PR/delivery/final closeout。本次未冻结 v2、更新 gate、commit/push 或部署；live sync/restart 与业务恢复/父线程回报仍未执行。
