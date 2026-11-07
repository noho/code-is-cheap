# Native namespace implementation / validation

Implementation/FIX delegate; existing branch `fix/shim-subagent-message-delivery`, draft PR #70. Controller's current `control.md` closes the applicable plan review and accepts `native-namespace-plan.md` (reviewed plan SHA e6d474dd431c2ccf8e43bd31ee78c0dab043b62e8dad1d57ef94d961b0500188). This report records the implementation and new evidence; it does not replace the controller's final adjudication or combined independent reviews.

## Implemented boundary

`codex-agent/bin/codex-auto-review-shim` derives an immutable per-request bare-name map only from top-level `multi_agent_v1` / `collaboration` namespace function descriptors. Kimi flattens just those wrappers and carries their description into each preserved child descriptor. MiMo Flash maps responses without changing its request wrappers, Code Mode/Lite/catalog/policies. Both route flags default off; request flatten requires response restore. Other seven routes explicitly keep both false and all nine retain agent_message_fix=true. Guardian bypass is based on its original model, before model substitution.

Only missing/null namespace leaves on mapped function_call items are restored at added/done/completed.output and JSON.output. Names, arguments, call IDs, item IDs, status and extension fields are unchanged. Unknown/custom calls, unrelated descriptors, choices and history pass through. Scoped collisions and unsupported selected-native structure/choice fail sanitized 400 before upstream send. No aliases, registry/session orchestration state, generalized MCP flattening or catalog forcing were added.

SSE uses actual incremental framing, including UTF-8, LF/CRLF/CR, multiple data fields, comments and raw non-target preservation; each event and buffered JSON input is bounded at 8 MiB. The first complete event is validated and flushed before upstream EOF. An active nonempty map accepts only identity/absent response Content-Encoding and SSE/JSON media; unsupported success encoding/media fails sanitized 502 before downstream headers. Late protocol failure closes the stream without retry or synthetic terminal/HTTP error. Connection-token headers, hop-by-hop headers and stale lengths are removed on the adapted response. For active-map non-2xx responses, already-buffered error data is forwarded with its original status/headers. Flags-off/empty-map non-2xx behavior remains exactly the saved baseline; the correction is scoped to the new mapped path.

The generic probe now observes the actual post-native-request stage, actual subsequent stages/final outbound hash, top-level descriptor locations, actual response pre/post byte counts and streaming hashes, mapped call pairs/restored count and encoding/content metadata. It retains native-call SSE only for added/done; completed events retain call projections/hashes without hidden reasoning. All launch source hashes have retrievable compressed snapshots. Historical probes and audit verdicts are preserved. `--initial-marker LIVE_PROBE_OK` uses the required literal Chinese initial task while preserving historical defaults.

## Offline verification

[offline-validation.json](evidence/namespace-offline/offline-validation.json) records **146 pre-inference passed tests**, actual logs, source hashes and successful py_compile, unchanged legacy DS audit and git diff --check. Commands:

```bash
python3 -m unittest discover -s tests -p test_shim_native_namespace.py    # 19
python3 -m unittest discover -s tests -p test_shim_subagent_delivery.py   # 13
python3 -m unittest discover -s tests -p test_shim_native_evidence.py     # 26 final (24 pre-inference)
python3 -m unittest discover -s tests -p test_install_endpoints.py        # 38
python3 -m unittest discover -s tests -p test_provider_registry.py        # 11
python3 -m unittest discover -s tests -p test_shim_service.py             # 11
python3 -m unittest discover -s tests -p test_model_catalog_generation.py # 30
python3 -m py_compile codex-agent/bin/codex-auto-review-shim docs/gateflow/shim-subagent-delivery/native-probe.py docs/gateflow/shim-subagent-delivery/audit-native-evidence.py
python3 docs/gateflow/shim-subagent-delivery/audit-native-evidence.py
git diff --check
```

The 19 new contract tests include captured Kimi spawn and MiMo Flash bare wait replay; immutable request mapping/field preservation; unrelated duplicates vs mapped collisions; actual service zero-upstream request rejection; all response locations/null/matching/conflicting namespaces; one-byte/varied chunks, Unicode/CRLF/multidata/comments/deltas/interleaving; malformed/truncated/oversize and total-stream-over-cap cases; real first-event read1 timing with an upstream gate; concurrent identical bare names in different native groups; actual HTTP transfer decoding and header filtering; success encoding/media rejection, no-map/flags-off passthrough, JSON and non-2xx behavior; guardian buffering/retry; observer capture plus independent auditor mutations; seven flags-off routes' request/success-response equality against the saved cd8e baseline. Existing auth/snapshot/prefix/ID/JSON/drop/custom/Lite tests remain applicable.

Development checks are retained separately, including the first 15-test run's error-body forwarding failure (corrected above). Later 15/16/18/19-test runs passed. No synthetic fixture is claimed as provider acceptance. Actual native declarations are in [declared-native-attempts.json](evidence/namespace-offline/declared-native-attempts.json).

## Fresh native evidence

All four declared attempt-1 runs exited normally, without any model retry/relaunch. Maximum observed concurrency was **2**: Kimi A began first; while it was pending MiMo Flash A started; each profile's B started only after that profile's A actually exited. The original serial scheduling declaration is preserved, with the reason for advancing independent work in [scheduling-note.json](evidence/namespace-offline/scheduling-note.json). App-server exit 0 and HTTP 200 did **not** override the strict failures below.

| Profile / case | Strict verdict | Actual parent | Actual child | Requests / seconds | Namespace leaves added |
| --- | --- | --- | --- | --- | --- |
| Kimi A | **FAIL** | `01a1b6bc-3889-7780-a011-9e0351097e2f` | none: spawn arguments rejected | 2 / 139.99 | 3 |
| Kimi B | **PASS** | `01a1b6be-ef54-7dd2-9c63-c5357864013b` | `01a1b6bf-1043-79a3-afab-bc0e0350430a` | 5 / 22.86 | 6 |
| MiMo Flash A | **FAIL** | `01a1b6be-2464-7403-a828-d7b9676a1d87` | `01a1b6be-59dd-7750-9b15-f25b5917cd63` (`/root/delivery_a`) | 18 / 331.53 | 0 |
| MiMo Flash B | **PASS** | `01a1b6c3-c25b-7f13-88a8-536879f1783e` | `01a1b6c3-e266-7611-8688-f267266d2d82` (`/root/delivery_b`) | 5 / 31.36 | 0 |

Each scenario's complete launch, wire, sanitized rollout, native execution supplement, audit, transport log and exact launch-source snapshots are under `evidence/<profile>/namespace-scenario-{a,b}-attempt-1/`. [Audit commands and exits](evidence/namespace-offline/native-audit-commands.json) retain the final B audit and strict aggregate commands. Each single A audit exited 1, each B audit exited 0; both independent A+B aggregates exited **1**, coverage `a=false, b=true`. [Kimi aggregate](evidence/namespace-offline/kimi-aggregate-a-b-audit.json) and [MiMo Flash aggregate](evidence/namespace-offline/mimo-flash-aggregate-a-b-audit.json) retain all required assertions. No all-nine pass is claimed.

**Kimi A:** the exact upstream call was restored to `multi_agent_v1.spawn_agent`, so the original unsupported-bare-name boundary is repaired. Its arguments were preserved exactly, including the model's invalid `"fork_context":"none"`; native Codex rejected that string because v1 requires a boolean. There was no child, A2/A3 could not execute. The literal initial task was exactly `只回复一行 LIVE_PROBE_OK，不要调用工具、不要读写文件`. The parent already received the advertised boolean schema and prompt's `fork_context=false` guidance. Changing arguments, schema, model or guessing another dispatch would violate the adapter boundary; this is recorded as a model conformance blocker, with no same-code fishing attempt.

**Kimi B:** real child-owned `exec_command` read the random fixture; its linked CommandExecution/call-result span, exit 0 and exact child final pass. Parent native spawn/wait history reached the gateway unchanged outside approved transforms, and native rollouts contain restored `multi_agent_v1` calls. This does not validate the unexecuted same-child A2 followup or unknown future history formats. The actual top-level descriptor location was `tools`; maps contained five advertised names on parent requests and were empty when a child did not advertise native tools. Actual user-selected TokenHub equality check is true, wire model `kimi-k3`, installed prefix `/coding/v1` on 8790. The original v1/direct/max catalog remains unchanged.

**MiMo Flash A:** three distinct child completed turns and exactly one separate MESSAGE/consume with token absent from its continuation are present. However, A2's post-dispatch waits only timed out, even though its distinct child completion was observed. The required valid fresh wait therefore fails; the later exact finals do not waive it. No duplicate MESSAGE was hidden. B independently passes its actual child Code Mode read, exact execution/call-result span, exit 0 and final. Existing v2/Code Mode/Lite/max and on-request/auto_review settings remain unchanged.

**New exact-location limitation:** every actual MiMo Flash native descriptor was in an input `additional_tools` list, with no selected top-level native tools. Therefore the approved top-level-only request map was **empty**, every response was byte-equivalent and restoration count is zero. This fresh evidence does not prove native activation of MiMo Flash's response repair. The saved bare wait is covered by offline response replay, but supporting actual additional-tools advertisement requires a bounded plan/contract adjudication by the controller. The implementation deliberately does not mine that location into a map, alias calls, force catalogs/v2, or create session lookup state. This is a concrete acceptance blocker, not a waived future risk.

All 30 actual Responses HTTP statuses were 200 (2+5+18+5). All recorded response Content-Encoding lists are empty, establishing **absent/identity encoding on the candidate's actual upstream boundary**; Content-Type is recorded per response. All first downstream body timestamps precede observed EOF; native timing is informational, while the gated offline read1 test is the controlled first-event proof. Actual response native call before/after pairs preserve name, arguments, call_id, id, status and all other leaves, with only 9 namespace additions total. Responses without a map or changed call have identical pre/post streaming hashes. No hidden reasoning was retained in call captures and no captured JS was executed.

## Final refinements and evidence applicability

After the four scenarios had launched from saved helper SHA `5d47d38af39bcb1819f4076ee7fc379c3bb98d53071650639115537f9f1aba12`, two bounded offline corrections were made: namespace **group labels** are excluded from bare callable collision checks while their known children remain inspected; error-body forwarding is restricted to an active map so the other seven/empty-map response paths remain unchanged. Final helper SHA is `7cdaf30d198433d261672185ef11ee12b4f155294c60fbd22b61f0401012493d`. [Applicability evidence](evidence/namespace-offline/final-source-native-applicability.json) proves neither branch refinement changes any fresh captured path: all statuses are 2xx, and none has an unrelated namespace group label equal to a mapped bare callable. This is explicit bounded evidence reuse, **not** a fresh inference claim on the final hash; controller combined review must adjudicate it.

Final affected reruns pass **19 namespace + 13 delivery + 26 auditor tests**; the other five applicable suite results above remain unchanged, giving **148 applicable passing tests**. The two added actual-capture audit tests preserve both real A failures/B-only coverage and reject missing request stages, outbound hashes, actual response hashes, changed call arguments and lost descriptor-location evidence. The original 24 historical auditor tests/results remain intact. Final namespace tests also prove seven flags-off routes match saved baseline success **and non-2xx** request/response behavior, and that a namespace group label matching a native bare name does not falsely collide.

## Current matrix and preservation

[namespace-current-matrix.json](evidence/namespace-current-matrix.json) is a **new** current matrix, retaining all 15 historical attempts/diagnostics including every prior failure, plus these four new attempts, exact source hashes, IDs, locations, restored counts and strict coverage. The original attempt matrix and all earlier reports/reviews/captures were not rewritten. Current strict whole-profile coverage remains **7/9**, with DS conditional historical reuse; affected profiles each have fresh B but failed A.

[seven-route-bounded-reuse.json](evidence/namespace-offline/seven-route-bounded-reuse.json) records DS historical conditional reuse, GLM/2, GLM Flash/1, MiMo/2, MiMo Fast/1, Qwen/1 and Hy/2. Their route objects differ only by two explicit false flags, installed catalog hashes still match, and real loopback success/error equivalence against saved cd8e source plus existing guardian/auth/prefix/ID/JSON/custom tests justify reuse. No all-nine rerun was made merely because the helper hash changed. No new fields are retroactively required from old captures. External destinations were not independently dumped or re-probed; only the sanctioned probe endpoint resolver read private configuration internally for actual routing.

## Ownership and remaining work

- fixed in current slice: request/response namespace repair and offline boundary contracts described above.
- completed in this slice: four declared native cases, strict failing A+B aggregates, new current matrix and seven-route bounded reuse.
- requiring controller contract/model decision: Kimi invalid v1 spawn arguments; MiMo Flash valid-wait conformance and actual additional-tools-only descriptor location. These are not marked fixed or deferred away from acceptance. No further native attempt was declared.
- covered by later approved controller review/closeout: combined dual independent deepreviews, evidence adjudication, accepted fixes and affected re-review, PR delivery checks. This delegate does not commit, push or send callbacks.
- requiring explicit user authorization: live deployment/restart. From the checkout containing approved changes, the applicable command is `./scripts/sync-codex-agent.sh`; no live sync was performed. No skills/runner changes require the other sync scripts. Business files/sessions/watchlists/ledgers and the three unrelated runner artifacts are untouched.
