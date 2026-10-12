# Plan review adjudication

Gate: plan review -> fix. Both independent subprocesses actually exited 0, runtime/runner 0. Their needs_review diagnostics are ordinary read/source-query failures; final durable reports and local direct evidence are available. Do not mechanically reject reports because of those tool errors.

- MiMo/Codex: `docs/reviews/plan-review-20261012-134721.md`, fail; wall1560.937354, native usage retained in private records.
- DS Flash/Claude: `docs/reviews/plan-review-20261012-133906.md`, pass-with-risks; wall837.571, native usage/metrics retained in private records.
- Plan freeze: c376940054522bd7242b0c441bffae206c4d42b08bcffd428a4e9e75cd5e32d8.

## Decisions for plan-only fix

| Finding | Decision | Required resolution |
|---|---|---|
| MiMo 1: two-hop fixture URL wiring | accepted; 未修复 | Specify managed provider URL to synthetic shim; private fixture endpoints.json mode600 with all selected upstream URLs/slugs/keys to synthetic upstream only. Assert loopback listener identities; no real user settings, auth or provider traffic. |
| MiMo 2: card/catalog mismatch after partial install | accepted, narrowed to conversion-specific ordinary failure; 未修复 | Existing Kimi namespace and Qwen budget changes introduce real pair skew. Add minimal backup/rollback of replaced card/catalog pairs for normal copy/replace/validation failures; move provider registry update after catalog validation and include any newly changed managed registry bytes in the same narrow recovery. No general deployment platform, migration framework or claim of atomic reader visibility/SIGKILL/disk-destruction recovery. Explicitly state those limits. |
| MiMo 3: missing pre-shim observation point | accepted; 未修复 | Specify test-only Handler ingress capture/replay (or equivalent) before transforms, separately capture upstream, compare intended model/auth/format and preserved effort/instructions/Lite. Keep production logging unchanged. |
| MiMo 4: route-wide json_fmt_fix | accepted documentation/coverage correction; 未修复 | Preserve existing route-wide MiMo json_schema->json_object behavior, state it accurately and add a targeted ordinary-session assertion. No narrowing or protocol behavior change without evidence. |
| DS 1: missing Chinese README | accepted; 未修复 | Include README.zh.md and keep paired descriptions/values consistent. |
| DS 2: host default true and negative test | accepted; 未修复 | Record native 0.162.1 code_mode_host stable/default true; negative test explicitly sets false. Controller independently reproduced the default. |
| Controller: redundant host feature wiring | accepted; 未修复 | Remove proposed explicit true MiMo-card features, app nested-feature overlay and isolation host-enabling machinery unless an actual execution defect proves them required. Their stated reason is default-drift insurance, outside this minimal conversion. Official code_mode_only overrides code_mode=false; default host is true. Test current native behavior and explicitly disabled/missing-host failure; document prerequisite instead of adding compatibility insurance. |
| Controller: CANARY colon in fixture | accepted; 未修复 | Fix CANARY: to CANARY= per existing collector/skill. Assert actual read/write and unchanged collection, not only fixture final text. |

## Other open questions / evidence boundaries

- Resolved Qwen context must be observed with an actual version-matched native event. Define exact temporary fixture evidence collection; a fixture-local persisted Qwen run is allowed if ephemeral exec JSON does not expose it. No live session, no computed value substituted for event evidence.
- Native CLI parsing remains authoritative for nested catalog schema; avoid duplicating its complete schema in hand-maintained Python checks. Keep checks needed for mappings/budgets/source integrity and meaningful specific errors.
- Eight profile mapping/metadata tests are needed; keep execution matrix focused on distinct native/tool/guardian behaviors, not mechanical duplication. Do not expand validation into an unrelated framework.
- Kimi quota is small: debugging/small synthetic real probe only; no review/dev or repeated vendor calls. Native fixture tests do not spend provider quota. User authorized provider dispatch/project access; no merge/live deployment.

All accepted items require plan fix and independent re-review. Product implementation has not started.
