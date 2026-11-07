# DS 两项低风险 finding：隔离候选修复与验证

本候选仅在 `/private/tmp/code-is-cheap-shim-review-fix-20261108`、分支 `fix/shim-observer-review-20261108` 工作。以 controller 本次明确授权为准，未委派、commit/push、sync/restart、发送 Agent 消息或技术 callback，未访问私有 endpoints/凭据、业务文件或真实会话，也未启动 vendor/API/native inference。没有写原主工作树。本文件是候选交接记录，不是 gate closeout 或 v2 freeze；`control.md`、`review-adjudication.md` 仍由 controller 所有。

## 实际改动

相对本隔离 checkout 到达时的 v1 文件状态，只改动四个既有文件：

| 文件 | 改动 |
| --- | --- |
| `README.md` | Kimi request flatten/map 限顶层；MiMo response-only map 可读当前请求顶层 `tools` 和 immediate `input[type=additional_tools].tools`，保持完整请求字节。 |
| `README.zh.md` | 同步上述中文契约。 |
| `docs/gateflow/shim-subagent-delivery/native-probe.py` | observer 解析先判 JSON dict；仅有有效 thread ID 的 Responses 请求进入 native wire；其他请求走原 transforms/handler/original_open，独立记录最小 metadata。 |
| `tests/test_shim_native_namespace.py` | 新增五项有意义的离线 observer/loopback 测试；原两项 observer 测试补合成 thread ID；fake upstream 支持 GET/no body。 |

另外仅新增本文件和独立目录 `evidence/review-fix-observer/`。隔离目录开始时已有未提交 v1 changes；不得将完整 `git diff HEAD` 当成本轮增量。独立目录的 `before-sha256.json` 记录到达时 1503 个仓库文件的 hash，`validation-scope.json` 验证仅上述四个既有文件改变，其余原文件、captures、旧 verdict/报告/计划/reviews/source snapshots/冻结清单均未变。没有修改 watchlist、调度账本、model/catalog/权限策略、runner artifacts 或生产 shim/routes/auditor。

## 修复前反例与修复后行为

`before-counterexamples.py` 用到达时 driver 字节（`before-native-probe.py.gz`）离线重放原 observer；`original_open` 为 mock，不联网：

| 请求 | 原 observer 异常 | 原 original_open 调用次数 |
| --- | --- | --- |
| GET / no body (`None`) | `TypeError` | 0 |
| POST / 空 body | `JSONDecodeError` | 0 |
| POST / 非 JSON body | `JSONDecodeError` | 0 |
| POST / JSON array | `AttributeError` | 0 |

候选 `observe_fix` 仍先调用原生产转换函数，再安全判断 ingress/converted 是否为 dict、有非空字符串 thread ID，且处于 Responses path。无可观测 native record 时，`observe_native`、所有 stage hooks 及响应 hooks 均不会为了记录而解析 JSON；生产函数照常执行。每次 `_handle` 和 `observe_fix` 清空 thread-local record/attempt，每次 `observe_open` 重置 attempt，防止先前 POST 与后续 GET 误关联。

独立 `passthrough-requests.json` 使用单独的 `passthrough_requests` 列表，不进入 `wire.json`。每项只含 `method`、去掉 query 的 `path`、实际 outbound 原始字节的 `body_bytes/body_sha256`、`model=None`、`http_status`、`error_class`；不记录 headers、凭据、完整 body 或 URL。编码请求的该长度/hash 针对原样 outbound 编码字节，正常 native record 原有 decoded hash 定义不变。fallback 返回原 response 对象，不预读或缓冲响应；正常 native ResponseObserver 保持原捕获方式。

新增五项测试覆盖：

1. 一个真实 loopback handler 中的 13 个子情形：GET/no body、空 POST、非 JSON、array/null/number/string/object-without-thread-ID、非 UTF-8、gzip/deflate、无法解压和未知编码；method/path/query/请求 bytes/编码/合成 auth header 到达 fake upstream，200 响应 bytes/指定 header 原样返回；最小 metadata 精确存在，native wire 为空。
2. 串行 HTTPServer 在同一 worker 先处理正常 native POST，再 GET、非 JSON、无 thread ID 的 JSON，最后另一 native POST：旧 record 完全不变、无串联。无 thread ID JSON 仍执行生产 namespace 恢复。
3. 429 错误路径与未安装 observer 的原 handler 对照，保留原 status/body 行为，单独记录 `HTTPError` 和 429，不保存敏感内容。
4. 无 thread ID 的压缩 guardian JSON 仍执行原 model swap、id fix、format downgrade、drop_tools_item 与 gzip 编码路径。
5. passthrough GET 和正常 active-map native POST 均在 upstream EOF 前收到首块；正常 native downstream hash 与实际收到的完整 bytes 一致。

初轮 32 项测试有两条新增测试预期不符合原生产行为：无 thread ID JSON 仍应恢复 namespace；429 应以原 handler 对照而非假定 body。仅修正测试预期，未改生产行为。随后最终三个文件全量通过，结果如下。

## 实际执行命令与结果

以下命令均从隔离 checkout 根目录运行；各 unittest 的 stdout/stderr 保存在独立目录中同名 `.log`。

```bash
python3 -m unittest discover -s tests -p test_shim_native_namespace.py -v
python3 -m unittest discover -s tests -p test_shim_native_evidence.py -v
python3 -m unittest discover -s tests -p test_shim_subagent_delivery.py -v
python3 docs/gateflow/shim-subagent-all-providers/evidence/review-fix-observer/before-counterexamples.py
python3 docs/gateflow/shim-subagent-all-providers/evidence/review-fix-observer/normal-observer-equivalence.py
python3 docs/gateflow/shim-subagent-all-providers/evidence/review-fix-observer/verify-scope.py
git diff --check
```

| 验证 | 最终结果 |
| --- | --- |
| namespace / observer | 32 tests，OK（27 既有 + 5 新增） |
| native evidence / audit | 33 tests，OK |
| subagent delivery | 13 tests，OK |
| unittest 合计 | **78 tests，全部通过**；13 个 passthrough 子情形没有额外计入 test 数 |
| 修复前离线反例 | 4/4 重现，均未调用 mock original_open |
| v1 / 候选正常 observer 对照 | 4/4 synthetic loopback cases 一致 |
| py_compile | driver + 上述三个 test 文件，共 4 个，全部通过 |
| diff / 范围检查 | `git diff --check` exit 0；仅四个既有文件改变 |

`verify-scope.py` 实际调用 `py_compile.compile(..., doraise=True)`，bytecode 写入临时目录并自动清理；同时执行 `git diff --check`、分支及到达基线 hash 检查。`normal-observer-equivalence.py` 比较到达时 v1 与候选 driver，涵盖 Kimi 顶层、MiMo immediate additional_tools、Kimi gzip、guardian bypass；完整 wire 只归一化运行期 monotonic timestamps，gzip 生成时间在 fixture 和生产编码器测试替身中固定为 0。其余字段、stage/outbound/response hashes、来源投影、request/response bytes 完全相同。对照最初遇到独立运行产生的 gzip 时间戳差异，固定测试时间后通过；这不是生产差异。对应结果为 `normal-observer-equivalence.json`。

## Hash 与 frozen captures 的适用关系

| 组件 | SHA-256 |
| --- | --- |
| 到达时 v1 driver | `6fde7ff90f47035520f500b618daf993149450c10b38ac515420e32888dd452f` |
| 候选 driver | `8fc7a3e8d9aed70d86855ce534eef544c2c3d9b915221520c66d6aa8a7c98e73` |
| 生产 helper（未变） | `a6246a4bc810125437992791aedcc8f2aa4c072f55e2bcf3691562feecd8e1e6` |
| routes（未变） | `0dd8e0fdbf4c360470b2102005075a981b1a09393894997faeb18468e59af5c6` |
| auditor（未变） | `5d46cf1c43553c0536454a3877b9e6aa20d3fb00a88a2c24910d77b2ea3014d6` |
| review-freeze-v1.json（未变） | `193f8e2b6b449c0a9d4103a62ded74e95127766f5b7802bd7b8875823559f925` |

原 native requests 为非空 JSON dict，带正常 thread ID，并处于 Responses 链；新增 guard 不改变该有效分支。既有 frozen captures 保留其各自原始 launch/source hash，**不能改标为候选 driver 生成**。本次以正常分支完整记录对照、78 项离线测试以及生产 helper/routes/auditor 不变证明有界适用；不声称在新 driver 上重跑过 inference。MiMo A4+B2、Kimi A2+B2、其余七路和既有 163 项适用检查/独立 73 项重跑仍是原 controller 的 v1 历史证据；本次只实际重跑上述受影响 73 项既有测试，加 5 项新增测试，其余检查按原适用边界复用。没有重跑九路实测或全生产审核。

## 交接与未完成项

修复和上述离线验证已完成，未见本候选需要继续修改的项目。下一步由 controller 安排两位 reviewer 聚焦受影响面复审；等待另一完整审核结束后，controller 才可集成到 `fix/shim-subagent-message-delivery`、创建 v2 freeze 并继续 draft PR #70。本 Agent 没有完成或宣称完成这些 controller gate，也没有 commit/push/部署权限。本任务无需 sync/restart。
