# Implementation plan: official provider catalogs

Gate: plan. Work unit: `official-provider-catalogs`. Branch: `feat/official-provider-catalogs`.
Base: `main=17ef441` (`17ef441bb9beac92914cc4a9c1c1dfc7108dd2a6`).
Status: plan-only fix of the controller's accepted findings; awaiting independent re-review. No product implementation or deployment has occurred.
Binding scope: [goal.md](goal.md), confirmed user steering, and [source-inventory.json](source-inventory.json).
There is no separate design document. This fix changes only this file and writes [plan-fix.md](plan-fix.md); the controller owns subsequent gates. [plan-review-decision.md](plan-review-decision.md) is the binding adjudication; the two reviewed artifacts supply findings, not a new independent review in this task.

## Goal, motivation and success signals

Replace the eight managed cloud profiles' GPT-derived session entries with the five user-supplied official catalogs. Installation must use tracked repository inputs, preserve the supplied instructions and capability metadata, and execute those capabilities through the existing Codex paths. A catalog is executable configuration: changing its tool dialect without arranging the matching runtime produces an unusable session even if JSON parsing succeeds.

Use the existing goal success signals as the acceptance boundary:

- **G1 — source/deployment:** tracked snapshots with provenance; exact selected entries; specific errors for missing mappings; staged cards/catalogs validated before installation.
- **G2 — selection:** all eight cloud defaults remain `max`; context settings agree with official metadata; Kimi logical slug is `k3`; endpoint-owned URL/key/upstream model remain independent.
- **G3 — execution:** actual Codex read/write/tool/final/result paths, MiMo Code Mode/Responses Lite, and automatic approval forwarding work in synthetic staged homes or fail visibly with a precise limitation.
- **G4 — boundaries:** existing outer read denial, write limits, network limits and approval behavior remain effective.
- **G5 — delivery:** meaningful tests/docs and controller-owned review artifacts, with required independent reviews adjudicated before the later draft PR/manual merge workflow.

## Scope and non-goals

Convert `ds-flash`, `glm`, `glm-flash`, `kimi`, `mimo`, `mimo-fast`, `mimo-flash`, and `qwen`. Preserve provider IDs, profile names, launcher/runner arguments, route ports/prefixes, credential ownership, session lifecycle, statistics, result schema and the outer isolation contract.

Do not convert GPT/account/business or the local nonofficial fallback; do not investigate high-risk refusals, access original business/financial tasks or artifacts, retry caller tasks, synchronize live homes, merge, add model routing fields, build a migration/compatibility layer, create a general configuration system, alter a scheduler, or redesign security. Do not mutate an official supported-effort list to disguise a limitation. Preserve existing endpoint defaults including the Kimi wire default; this work changes the logical selection, not endpoint-owned wire settings.

## Evidence and first-principles decisions

Repository evidence inspected at the stated base:

| Path / call path | Existing behavior and implication |
| --- | --- |
| `scripts/patch-codex-model-catalog.py`: `patch`, `profile_model`, `select_session_template`, `session_entry`, `write_targets`, `verify`, `main` | All third-party sessions clone a bundled direct GPT entry and replace instructions-related metadata, capability fields and windows. `profile_model` demands a positive card window and the final absolute catalog path. The guardian patch changes only `tool_mode`; that alone does not disable Lite. Retain donor selection only for `local`. |
| `scripts/sync-codex-agent.sh` | Endpoint/route checks and the provider registry update currently precede card/catalog staging; catalogs and cards are then installed in separate loops. Move registry replacement after staged native validation, and add narrow backup/rollback for replaced card/catalog pairs and changed registry bytes. Shim/service/business operations remain outside this conversion recovery boundary; this is not an all-files transaction. |
| `scripts/agent-tools.zsh` and `scripts/codex-agent-run` | Normal launchers use `$HOME/.codex`, not `CODEX_SHARED_HOME`; isolation uses `AGENT_SANDBOX_CODEX_HOME`. Managed CLI invocations inject `-p <profile>`, endpoint validation and fixed shim-port readiness checks. Runner supplies ephemeral JSON events, last-message handling and result collection. No new launcher or runner interface is needed. |
| `scripts/compose-codex-app-config.py` | Composes card root scalars and provider tables, without a nested feature overlay. Native 0.162.1 already defaults `code_mode_host` to true; no card feature or composer change is required by the present evidence. |
| `scripts/agent-sandbox`: `MODEL_KEYS`, `FEATURES`, `prepare_codex`, `main` | Copies model keys/provider/catalog path, disables `code_mode` and other extension surfaces, and sets inner full access/never approvals because the outer srt envelope enforces the boundary. Catalog is referenced, not copied. Retain this configuration: official `code_mode_only` overrides `code_mode=false`, and the omitted host key uses the native true default. No selected-entry inspection or host-enabling machinery is planned. |
| `codex-agent/bin/codex-auto-review-shim`: `Handler._handle`, `route_url` | Classifies guardian requests before remapping. Resolves one endpoint URL/model/key snapshot per request; ordinary responses stream, guardian SSE is buffered/retried. Managed routes replace incoming auth, refuse redirects, and preserve `additional_tools` (`drop_tools_item=false`). This already accommodates Lite payloads; prove it with real request shapes before changing transport. |
| `scripts/agent-run-result.py`: `Collection.codex`, `terminal_metrics`, `tool` | Counts native command/file/MCP result events and retains terminal usage, session identity and final text. Nested commands must still produce this evidence; an asserted final alone is insufficient. No collector redesign is planned. |
| Existing tests / README | Catalog tests assume GPT donors for clouds; runtime isolation tests use `gpt-5.4` with an empty `mimo` card, so they do not prove official MiMo behavior. Endpoint tests already cover auth ownership, redirects and streaming/retries. README describes all nine third-party catalogs as GPT-derived. Update affected assertions and descriptions, preserving historical rollout examples. |

The five Downloads files were read and their byte counts/hashes match the existing source inventory. Codex CLI `0.162.1` was inspected in fresh temporary `CODEX_HOME`/`CODEX_SQLITE_HOME` directories. `codex -c model_catalog_json=<source> debug models` successfully parsed every original file without contacting a model API. Native parser omission/type probes confirmed the constraints below; temporary probes did not modify repository inputs.

Version-matched public source evidence (reference, not an installation dependency):

- [ModelInfo and catalog instruction promotion](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/protocol/src/openai_models.rs): required fields, nullable optional fields, empty instructions accepted, context resolution and 90% compaction cap.
- [Config context overrides and unknown-model fallback](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/models-manager/src/model_info.rs): explicit context is clamped only when `max_context_window` exists; unknown model fallback has 272000 context/max.
- [Reasoning normalization](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/protocol/src/openai_models/reasoning_effort.rs) and [request construction](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/core/src/client.rs): `max` passes unchanged; list membership does not normalize it. Lite places tools in an `additional_tools` input item, omits ordinary top-level tools, sets reasoning context to `all_turns` and sends the Lite header.
- [Tool-mode selection](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/core/src/tools/mod.rs): a recognized model `tool_mode` takes precedence over feature-based selection. Unavailable `code_mode_only` does not fall back to direct tools. This establishes selection logic, not worker availability or successful tool execution.
- [Host selection](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/core/src/thread_manager.rs), [host connection](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/code-mode/src/remote_session/connection.rs): native 0.162.1 reports `code_mode_host stable true` in an empty home, independently reproduced by the controller and documented in the reviewed evidence. Transport uses inherited stdin/stdout pipes, without a new listener or Unix-socket allowance. The installed npm platform package contains `bin/codex-code-mode-host`; actual execution under srt still needs verification. Omitting the key is a positive-default case; the negative case must explicitly set false.
- [Guardian assessment contract](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/ext/guardian-reviewer/src/assessment.rs): synthetic verdicts can use `{"outcome":"allow"}` / `{"outcome":"deny"}`; malformed/no verdict is a failure, not permission.

Reuse [native-parser-controls.json](evidence/native-parser-controls.json), [native-request-controls.json](evidence/native-request-controls.json) and [runtime-findings.md](evidence/runtime-findings.md). They establish parsing and max/Lite request construction; intentional HTTP 400 stops establish neither tool execution nor provider acceptance. A focused temporary Qwen probe during this fix actually observed the native persisted context event; its exact path, event excerpts and scope are pinned in [plan-fix.md](plan-fix.md). No source-wide or version research needs repetition.

## Catalog inputs and exact profile mapping

Store the original bytes in `codex-agent/catalog-sources/`. Add a short `README.md` there recording filename, SHA-256, byte count and user-supplied official provenance from the inventory. Do not invent vendor URLs or fetch new catalogs. Files are deployment inputs, not generated outputs; installation never reads Downloads or needs the goal artifact.

Keep a small explicit mapping constant in the existing generator, not a new routing/configuration document:

| Profile | Source filename | Source slug → selected slug | Provider ID | Card context / compact limit |
| --- | --- | --- | --- | --- |
| `ds-flash` | `ds-model-catalogs.json` | `deepseek-flash` → same | `deepseek` | 1048576 / 786432 |
| `glm` | `glm-model-catalogs.json` | `glm-5.3` → same | `glm` | 1048576 / 786432 |
| `glm-flash` | `glm-model-catalogs.json` | `glm-5.3` → `glm-5.3-flash` (derived) | `glm_flash` | 1048576 / 786432 |
| `kimi` | `kimi-model-catalogs.json` | `k3` → same | `kimi` | 1048576 / 786432 |
| `mimo` | `mimo-model-catalogs.json` | `mimo-v2.6-pro` → same | `mimo` | 1048576 / 786432 |
| `mimo-fast` | `mimo-model-catalogs.json` | `mimo-v2.6-pro-ultraspeed` → same | `mimo_fast` | 1048576 / 786432 |
| `mimo-flash` | `mimo-model-catalogs.json` | `mimo-v2.6-flash` → same | `mimo_flash` | 1048576 / 786432 |
| `qwen` | `qwen-model-catalogs.json` | `qwen3.8-max` → same | `qwen` | 983616 / 737712 |

All eight cards retain `model_reasoning_effort="max"`. GLM Flash is the sole authorized derivation: deep-copy the official GLM 5.3 entry; change its slug, display label and description to identify `glm-5.3-flash` and explicitly say it is derived from official `glm-5.3` by user authorization. Every other field must equal the donor, including empty instructions and supported efforts. Do not select `glm-5-turbo`. Keep the original GLM entries intact in the generated catalog.

Kimi changes only the managed card's `model` and the route at port 8790's logical `to` to `k3`. The generator must select exact `k3`, without a `kimi-k3` alias. `config/endpoints.example.json`, private endpoints, upstream key/URL/model, provider IDs and public `kimi_*` names remain unchanged. Both `k3` and guardian requests must still map to whatever wire model the endpoint resolver selects.

## Validation/schema contract

Implement two layers inside the existing generator, without adding a schema library or generic configuration framework.

1. **Repository/deployment checks:** source byte integrity against fixed provenance hashes, JSON object root, nonempty `models` array of objects, nonempty unique string `slug`s (no `id` fallback), exact mapped source/selected slug, staged card model/max effort/final absolute catalog path, selected tool selector, and the budget relationships below. These are conversion invariants, not a second native schema implementation. Errors name profile, source path/slug and the violated invariant; exit nonzero without a GPT cloud donor.
2. **Native acceptance:** validate every fully assembled staged output with the installed CLI using a fresh empty home and `codex -c model_catalog_json=<absolute staged path> debug models`. Do not use `--bundled` here: it deliberately ignores the configured catalog. Capture native parser failures; do not replace output JSON with the CLI's normalized serialization. Use `--bundled` only when obtaining the independent native guardian/local source. Retain `--source FILE` as the existing test/native-source injection, not as a cloud source override.

Native parsing owns required fields, instruction/message nesting, effort-item types, shell/truncation enums and flag types. Do not reproduce those validators in Python. Preserve empty instruction strings (GLM/Kimi/Qwen), empty effort arrays (unselected GLM Turbo), optional model_messages and unknown extension data; the native parser accepts the supplied sources. Report its actual error with the staged profile/path, rather than generating a parallel field-by-field error catalog.

`context_window`, `max_context_window` and `auto_compact_token_limit` are optional/nullable native i64 values. For this deployment, the selected official entry must provide a positive resolved context (`context_window`, else `max_context_window`); any present selected maximum must be positive and consistent. `effective_context_window_percent` defaults natively to 95; retain a supplied value and check its selected value is in 1..100 for budget validation. Reject Python bools as integer budgets. Preserve omission versus null, unselected entries, ordering and root metadata; do not generate a required-field projection.

Known `tool_mode` values are `direct`, `code_mode`, `code_mode_only`; omitted/null is valid. Native code treats an unknown selector as absent, so this one selected-entry semantic check must reject it visibly. Leave Qwen's native-valid `shell_type="default"` unchanged. Native parser remains authoritative for other enums/nesting; do not invent a closed effort enum or require catalog default effort membership.

### Context and effort settings

Require the managed card's context to equal the selected official resolved context. Require its explicit compact limit to equal the planned 75% value, remain positive, and not exceed the model's effective input window or native 90% cap. Validate rather than silently rewriting a contradictory card or enlarging source metadata. Qwen changes to 983616/737712; the other cloud values stay as listed.

Native behavior is precise: `resolved_context_window()` prefers context, then maximum; an explicit config context replaces it, clamped only by a present maximum. With Qwen's missing maximum, an oversized card is not automatically corrected. Preserve the missing key; do not add a maximum to satisfy the old verifier. Qwen's actual temporary native `event_msg`/`token_count` event reports `payload.info.model_context_window=934435` with the 983616 card override; this is observed evidence, not an arithmetic substitute. Its explicit compact limit is 737712, also below the native 90% cap. Other selected entries retain 1048576/786432.

DeepSeek, GLM 5.3 and Kimi advertise `max`. MiMo 2.6 snapshots advertise none/low/medium/high; user confirms official max support. Qwen advertises low/medium/xhigh, omitting max. Preserve these lists and catalog defaults exactly. All cards stay max; emit informational discrepancy notes (MiMo user-confirmed, Qwen selected but unadvertised). Notes do not enter the fatal-warning accumulator. Capture max before/after the shim and perform the already authorized small acceptance probes below. Do not remap effort, append max to source lists, or count a mock response as vendor acceptance. Report any actual rejection by configuration; changing effort/model/source metadata requires user direction.

## Assembly, guardian and runtime decisions

For each cloud profile, deep-copy its complete official catalog and append exactly one native `codex-auto-review` entry obtained independently from the installed bundled catalog. Do not append other GPT session models. Fail on a missing, duplicate or unexpected native guardian or a source collision with that reserved slug. Keep native guardian instruction/security metadata and approval semantics intact.

Only the guardian receives these explicit transport adaptations:

- For DeepSeek/GLM/GLM Flash/Kimi/Qwen, set guardian `tool_mode="direct"` **and** `use_responses_lite=false`, so the review request uses the ordinary tool envelope. Setting only direct does not disable Lite on Codex 0.162.1. Test the actual review request, not just fields.
- For MiMo 2.6 profiles, retain the native guardian's recognized Code Mode/Lite metadata; verify `code_mode_only` and Lite true. Preserve required `additional_tools`.

The existing MiMo `json_fmt_fix` is route-wide: all three routes downgrade `text.format.type="json_schema"` to `json_object` for ordinary sessions as well as guardian requests. Retain this behavior exactly, document its structured-output limit, and assert an ordinary-session downgrade plus a valid decoded guardian verdict. This plan neither narrows the flag to guardian traffic nor changes the protocol.

This is a deployment adaptation of the native approval entry, not a rewrite of an official session card. Leave the local generator's existing direct-session donor/fallback behavior and catalog composition intact; restrict its old session-template tests to `local`. Keep GPT/business paths unchanged. Verify local still finds a compatible donor (the inspected CLI has a direct/non-Lite `gpt-5.5` entry); do not pin that donor name in production.

Use native 0.162.1's stable/default-true host with the host key omitted. Remove the proposed explicit true features in MiMo cards, the app composer's feature overlay, and isolated selected-catalog/host-enabling logic from S1. Preserve sandbox `features.code_mode=false`; official `code_mode_only` takes precedence. Existing app composition and sandbox model/provider/catalog copying remain sufficient on the collected evidence. Do not copy base feature/credential/extension state into isolation or alter its inner approval policy and outer protections.

Tests must execute required Code Mode with default host and `code_mode=false`, then explicitly set `features.code_mode_host=false` for a visible unavailable-host negative case. A missing native binary/host is a reported prerequisite failure, never silently enabled or replaced. Restore any removed product edit only if an actual concrete execution defect demonstrates its necessity and the controller adjudicates the smallest repair; future default/machine-state drift is not a justification.

The standalone host inherits the outer envelope and communicates via pipes. No network/Unix-socket/read/write relaxation is authorized. If the actual installed runtime cannot execute it under that boundary, stop with a specific unsupported configuration instead of forcing direct mode, dropping tools, changing the model or weakening srt.

Keep shim code behavior unless the following targeted tests expose a concrete Lite forwarding defect. The allowed repair is limited to forwarding existing Lite headers/body/items/compression and terminal SSE correctly through the current handler; retain model/auth snapshot ownership, no redirects, unbuffered ordinary streams, bounded guardian retries and non-2xx status propagation. No alternate protocol or new route fields. Merely importing official catalogs does not justify a shim rewrite.

## One coherent implementation slice

**S1 — Deploy official cloud metadata through the existing execution paths.**

Objective/outcome: a sync from repository inputs produces native-valid official cloud catalogs, correct managed settings, narrow installation recovery and usable staged execution, while native/local and outer-boundary contracts remain intact. It covers G1–G4 and supplies tests/docs for G5. Source selection, card limits, guardian dialect and runtime validation determine this one behavior; no host-enabling feature layer is needed.

Prerequisites: controller completes required planreview/fix/re-review and accepted-plan gate; confirms branch/base and changes owned by this work unit. No approval choice remains at the goal gate. The author does not run those gates in this task.

Allowed files/modules:

- New `codex-agent/catalog-sources/{ds,glm,kimi,mimo,qwen}-model-catalogs.json` and `codex-agent/catalog-sources/README.md`.
- `scripts/patch-codex-model-catalog.py`, `scripts/sync-codex-agent.sh` (staging, registry ordering and the conversion-specific card/catalog/registry recovery block).
- Cards `codex-agent/profiles/kimi/config.toml` and `qwen/config.toml`; `codex-agent/shim-routes.json` (Kimi logical slug only). No MiMo-card host features.
- `codex-agent/bin/codex-auto-review-shim` only if a demonstrated defect needs the bounded forwarding fix above; otherwise no product change there.
- `tests/test_model_catalog_generation.py`, `tests/test_provider_registry.py`, `tests/test_install_endpoints.py`, `tests/test_agent_sandbox.py`, and a new focused `tests/test_official_catalog_runtime.py`. Existing `tests/test_agent_sandbox_runtimes.py` remains a regression harness; extend it only to share the required small runtime fixture without changing its original coverage.
- Root `README.md` and `README.zh.md`, plus controller-owned implementation/review/evidence artifacts under `docs/gateflow/official-provider-catalogs/` during subsequent gates.

Inspected but not planned for behavior changes: `scripts/compose-codex-app-config.py`, `scripts/agent-sandbox`, `scripts/agent-tools.zsh`, `scripts/codex-agent-run`, `scripts/agent-run-result.py`, `scripts/agent-sandbox-launch.mjs`, `codex-agent/model-providers.toml`, `config/endpoints.example.json`, service lifecycle scripts, local/GPT/MiMo cards and business-default synchronization. Do not update historical `kimi-k3` rollout tests merely to rename old sessions.

Implementation order within S1:

1. Copy the five snapshots byte-for-byte; record provenance. Add fixed profile mapping and official loader/checks. Keep native guardian/local source loading independent, offline and fresh-home; cloud session construction never invokes `session_entry`.
2. Assemble all requested catalogs in memory after source/card checks, apply the sole GLM derivation and per-provider guardian adaptations, write stage files atomically, and run native parser validation before sync begins installing them. Rework `verify` to check source equality/authorized delta, exact selected slug and guardian dialect instead of demanding a generated direct session/max_context_window. Preserve `--dry-run` as no output-directory writes (native validation may use private temporary files). Preserve existing CLI flags and final installed paths.
3. Align Kimi card/route and Qwen budgets; implement the narrow conversion install recovery below. Do not edit endpoint resources, MiMo feature cards, composer or isolation feature logic. Native/local outputs and provider registry behavior receive regression coverage.
4. Exercise staged sync success, repeat sync, all source/card failure paths, and actual runtime fixtures below. Repair only accepted in-scope failures. Record unexpected transport/event/worker behavior as evidence and stop if satisfying it would require scope expansion.
5. Run the already authorized bounded provider acceptance probes without live sync, update both READMEs/provenance with measured behavior and limits, and deliver the implementation artifact to the controller. Do not deploy live or merge.

Data/state flow: tracked snapshots + independent native guardian/local source + staged cards → validated catalogs → native parser accepted → backed-up registry/pair replacement and installed-pair checks → existing launchers/composer/isolation → endpoint snapshot → tools/final → unchanged collection. Invalid stage/native parse leaves registry/cards/catalogs intact; ordinary conversion-install failure restores replaced pairs and changed registry bytes. Runtime failure retains existing diagnostics, without a smoke pass or model/effort/dialect substitution.

### Conversion-specific ordinary installation recovery

Keep this inside the existing sync script's shared-home conversion block, without a transaction service or migration mechanism:

1. Finish staging and native validation of all outputs before touching installed cards, catalogs or the managed provider registry. Before the first replacement, back up each staged card/catalog destination that will be replaced, preserving original bytes/mode and recording absence, plus the original base config bytes/mode/absence for registry recovery. Backup/preflight failure exits without replacements.
2. Move the existing registry update here, after catalog validation and before exposing new cards, so all managed provider IDs are resolvable. Its ownership/conflict checks remain authoritative. Restore its snapshot only if this block actually changed registry bytes; do not touch private endpoints or auth.
3. Install each staged catalog and its card using the existing mode-600 temporary-file/replace pattern. Keep backups and record attempted destinations before replacement for the whole block, not just the current pair. Verify installed bytes against staged bytes and the selected slug/card path/context/effort relationship before success; use staged native parsing rather than rerunning the expensive parser for identical bytes.
4. Arm the existing EXIT cleanup for this block: on ordinary copy, replacement, registry update or installed-pair validation failure, restore every attempted/replaced destination and any changed registry snapshot; remove new destinations whose originals were absent. Exit nonzero. Test failures after the first catalog replacement, after its card replacement, during a later pair and at final verification/registry update. Report a rollback error and retain its backups (rather than deleting the stage) if restoration itself fails; never print a successful sync.
5. Disarm recovery only after the registry and all installed pairs pass verification, then continue existing shim/routes/service/business operations. They are outside this recovery boundary; their failure must not be described as a successful overall sync.

This addresses conversion-created Kimi namespace/Qwen budget skew on normal failure. It provides neither atomic visibility to concurrent readers/writers nor guaranteed recovery after SIGKILL, power loss, disk destruction or a restoration I/O failure. Individual file replacement remains atomic; cross-file visibility and ancillary deployment are not made transactional.

Completion signal: all required deterministic checks and supported native/kernel smokes pass, docs name every limitation, and controller has an implementation artifact containing changed files, commands, outcomes and residual-risk classifications. Stop for native schema drift that cannot preserve supplied semantics, missing required runtime capability, a boundary failure, silent max mutation, missing native result evidence, or any fix outside allowed scope.

## Exact tests and smallest synthetic execution strategy

### Pure/unit and staged-sync checks

Extend the existing catalog test file with these concrete assertions:

- Five tracked byte hashes match fixed expected hashes copied from the approved source inventory into the test/provenance data; deployment tests do not depend on mutable Gateflow docs or Downloads. All source objects/root metadata/unselected entries survive generation; one unknown nested extension fixture proves deep-copy preservation. No cloud instruction/tool/Lite/effort/summary/image/compaction metadata is copied from GPT.
- All eight exact mappings, no Kimi alias, and GLM Flash donor equality except the three labelled identity fields. No substitution by GLM Turbo.
- Conversion checks cover missing source, malformed root/models, duplicate/absent slug, bad selected tool selector, wrong card model/path/max effort, oversized/mismatched window and invalid compact limit, including a boolean budget. Source equality preserves empty instructions/effort arrays and optional fields; do not build a combinatorial native-schema test suite or duplicate native required-field validation.
- Qwen's missing maximum stays absent, 983616/737712 settings are enforced, all eight cards remain max, and mismatch notes for MiMo/Qwen are visible without an error exit. Advertised/default levels remain byte-for-byte semantic copies.
- Only the native guardian is added for clouds; its instruction/security fields stay intact, direct providers disable guardian Lite, MiMo retains both Code Mode and Lite. Native source drift/missing guardian fails rather than borrowing an unrelated model.
- Local donor tests continue to cover renamed compatible donors and no-compatible-donor failure; GPT/business cards and provider IDs are unchanged.
- Native validation parses every assembled staged catalog once under an empty home; original-source acceptance already has collected native evidence. Debug serialization is evidence, not regenerated input. One representative malformed nested native field proves parser rejection before card/catalog/registry replacement; retain the actual native diagnostic instead of testing every schema permutation.
- Sync into a temporary HOME with `CODEX_SHARED_HOME=<HOME>/.codex` and `CODEX_AGENT_TARGET=<HOME>/.codex-agent`; stub `launchctl` to fail `print`, assert no kickstart/bootstrap/bootout. Seed synthetic endpoint overrides and no business account. Success installs expected bytes/modes/pairs; repeat sync is idempotent. Stage/native/registry ownership failure leaves preinstalled card/catalog/registry sentinels unchanged. Inject ordinary failures after first catalog, first card, a later pair, registry replacement and installed-pair verification; require original bytes/modes/absence and unrelated base settings restored for the entire replacement set. A rollback failure must exit nonzero with retained backup location. Do not infer SIGKILL or atomic-reader guarantees from these tests.
- Staged install/bootstrap tests use repo source snapshots after the fake clone; no Downloads dependency. Fixture Codex should distinguish bundled-source rendering from explicit catalog validation or use the actual CLI only for offline parsing. Do not let a stub that always prints the native catalog stand in for validation of official files.

Use validation-aware stubs for repeated install/failure-injection unit cases; real native acceptance of all assembled outputs plus one representative native rejection is a separate check. Runtime/guardian/kernel cases reuse those immutable generated bytes. Do not run the full native parser matrix again for each I/O injection or schema permutation; normal production sync still validates every staged output before installation.

In provider-registry/composition tests, compose Kimi `k3` and the unchanged MiMo card; preserve desktop/machine state and all existing `[features]` keys. Registry/shim/provider/launcher-port identities remain. Sandbox tests assert existing model/catalog copying, `code_mode=false`, no newly written `code_mode_host` key and unchanged disabled surfaces/boundaries. Missing/duplicate selection is a generator failure; do not add a duplicate selected-entry parser in sandbox preparation.

In endpoint/shim tests, add Kimi logical and guardian mapping with a different synthetic upstream slug/URL/key; ordinary streaming remains ordinary. Cover real-shape Lite `additional_tools`, exec descriptors, max, Lite header, compression and existing ID transformation. Include an ordinary MiMo session with `text.format.type="json_schema"`: ingress retains that schema, upstream uses `json_object`, and instructions/effort/Lite items survive. Keep a guardian counterpart and existing non-2xx/retry/redirect coverage. Retain production behavior and logging.

Run once after the slice is implemented, from the repository:

```bash
python3 -m unittest discover -s tests -p 'test_model_catalog_generation.py'
python3 -m unittest discover -s tests -p 'test_provider_registry.py'
python3 -m unittest discover -s tests -p 'test_install_endpoints.py'
python3 -m unittest discover -s tests -p 'test_agent_sandbox.py'
python3 -m unittest discover -s tests -p 'test_agent_sandbox_launch.py'
python3 -m unittest discover -s tests -p 'test_agent_run_results.py'
python3 -m unittest discover -s tests -p 'test_codex_model_defaults.py'
python3 -m unittest discover -s tests -p 'test_shim_service.py'
python3 -m unittest discover -s tests -p 'test_official_catalog_runtime.py'
bash -n scripts/sync-codex-agent.sh
zsh -n scripts/agent-tools.zsh scripts/codex-agent-run
```

Existing kernel-only tests may skip in ordinary unit runs; the following explicit native/kernel validation may not be reported as passed if skipped. No full-suite expansion is needed unless an actual affected dependency/failure warrants it.

### Staged-home actual Codex smoke (synthetic endpoints)

Put the small harness in `tests/test_official_catalog_runtime.py`, gated by `OFFICIAL_CATALOG_RUNTIME_TESTS=1` for native execution. It uses the installed Codex CLI/host but the branch's scripts/cards/catalogs/shim, not a deployed live home. All prompts/files/keys/responses are synthetic.

For each fixture, create a canonical temporary root with `home/.codex`, `home/.codex-agent`, `home/.config/agent-tools`, `bin`, `work`, and new output sinks. Scrub inherited auth/provider/proxy/config variables; HOME, CODEX_HOME, CODEX_SQLITE_HOME and state-directory overrides point only to the fixture. Set `AGENT_TOOLS_FILE` to its launcher and use branch/sync-installed helpers with the actual CLI/host/Node binaries. Stage through real sync with fake launchctl. Never source `.zshrc`, copy real auth/private endpoints or invoke running services. `CODEX_SHARED_HOME` alone does not redirect normal launchers; temporary HOME is mandatory.

Wire both independent hops explicitly before any native request:

1. Bind dedicated synthetic upstream and shim listeners on `127.0.0.1:0`, retain the resulting server objects, and use their actual OS-assigned ports. In a temporary route copy preserve endpoint IDs, `from`/logical `to`, `request_prefix` and flags; change only listener addresses/ports. For each managed provider table, set fixture `base_url="http://127.0.0.1:<shim-port><request_prefix>"`, preserving provider ID, responses API and auth policy. This is the Codex-to-shim hop.
2. Write owned regular `<fixture HOME>/.config/agent-tools/endpoints.json` with mode `0600` and schema `{"default":{},"override":{"<endpoint_id>":{"codex":{"base_url":"http://127.0.0.1:<upstream-port>/fixture/<endpoint_id>/v1","upstream_model":"fixture-wire-<endpoint_id>","api_key":"fixture-key-<endpoint_id>"}}}}`. Populate all eight selected endpoint IDs, not just the current case; add the sync-required `local.codex` connection to a fixture listener with an empty key. No selected Codex connection may inherit a factory/user URL, model or key. The managed route strips its request prefix and appends `/responses` to this upstream base. This is the shim-to-upstream hop; the shim reloads this fixture file through its existing resolver on every request.
3. The fixture launcher sources branch `agent-tools.zsh` and overrides only `_codex_agent_shim_port` to the corresponding actual shim port. In the fixture-only shim process, wrap `upstream_open` with an assertion on the exact registered upstream host/port/path before calling the unchanged opener. Preflight effective resolver snapshots and registry routes against retained `getsockname()` identities; every selected host must be `127.0.0.1` and every port belong to this fixture. No missing override/default fallback is accepted. Fail local bind/readiness errors without stopping or reusing a live listener.
4. Use a fresh shim subprocess under fixture HOME so endpoint-module caches cannot inherit other tests' state. Endpoint keys remain shim-owned; Codex has no real credentials. Upstream must receive only `Authorization: Bearer fixture-key-<endpoint_id>`, including guardian requests. A separate synthetic inbound-key replacement case proves incoming auth cannot override this snapshot.

Capture the two observation points in test code, without a production logging feature. Load the branch shim in the fixture subprocess and subclass `Handler`; bind `do_POST` to a wrapper that reads exactly Content-Length bytes, records path/headers/raw body plus a decoded JSON copy (gzip/deflate as indicated), replays the identical raw bytes through `io.BytesIO` to `Handler._handle(self)`, then restores the original stream. Explicitly override `do_POST`: overriding `_handle` alone would leave the inherited method alias bound to the original implementation. Do not transform/re-serialize the replay. The separate upstream server records its received path/headers/raw/decoded body. Pair captures by fixture case/ingress sequence, allowing bounded guardian retries to forward one ingress more than once. Compare logical versus wire model/auth, structured format/ID changes, instructions, max and Lite items/header. This observes real native ingress before endpoint/model/format transformations; upstream data alone and old HTTP-400 controls do not substitute for it.

All eight profiles require mapping, source-equality, card and staged native-parser coverage. Execute full read/write/final/collection only for distinct cases: `ds-flash` (direct tools with official instructions), `kimi` (native `k3` with independently overridden wire model), `mimo` (required Code Mode/Lite/default host), and `qwen` (native default shell plus missing maximum/resolved context). GLM/derived Flash and the other MiMo profiles share these behaviors; no duplicate full runtime runs are required without a concrete difference.

Each task reads `work/canary.txt`, writes the read token to a new `work/result.txt`, and returns a standalone final `CANARY=<token>` line. The controller's expected-token file is outside prompt/input delivery. Use the real runner with explicit cwd and fresh `--output`, `--stderr`, `--last-message`, `--artifact`, `--canary-file` and `--canary-expected` paths and synthetic writable-workspace policy. Runs are ephemeral except the Qwen case, which uses fixture-local `--persist` for native context evidence. The upstream emits only the advertised tool/schema (`shell_command.command`, `exec_command.cmd`, or `shell.command` argv). Unsupported schemas fail visibly.

MiMo receives a native `custom_tool_call` for advertised `exec`; its JS awaits the advertised nested command tool and emits output. Do not fake file actions or tool results. This proves host cell/nested-tool execution; direct cases use their advertised native shell. Include terminal SSE/usage and bound each subprocess run.

Required assertions:

- Selected logical slug/source instruction rendering reaches captured native ingress; endpoint-controlled synthetic wire slug/key reaches the registered upstream. Only official catalog instructions and synthetic prompts/files/keys are used; no real user task or credential data.
- In each executed case, max survives both observation points. MiMo contains `additional_tools`, the actual exec descriptor and Lite header, omits ordinary top-level tools and sets reasoning context `all_turns`. Non-Lite sessions use the ordinary envelope. Empty/absent source instructions receive native rendering without injected GPT text. Mapping/metadata assertions cover all eight; do not label four executed cases as eight runtime successes.
- Positive MiMo leaves `code_mode_host` absent and sets `code_mode=false`; record fixture `features list` showing stable/default true, then prove actual Code Mode execution. Existing false/true request controls already cover selector precedence; do not repeat a full positive run with code_mode true merely to duplicate them. Negative fixture explicitly writes `features.code_mode_host=false` (or passes the exact CLI override), confirms false in `features list`, then requires visible unavailable-host failure, no direct fallback/artifact and failed collection. A model final after a failed tool is not a smoke pass. Report missing CLI/host or incompatible behavior explicitly rather than adding host-enabling insurance.
- Real canary read/output content, new result artifact and last-message agree. Collection retains session identity, terminal completion/usage, positive native tool-result count and the existing `recorded_events_only` evidence scope. With valid canary/artifact evidence and no diagnostics, require `canary_status="match"`, `validation_status="passed"` and `result_status="not_assessed"`. Do not count nested tools twice or alter metrics to make a check pass.
- Reuse the single persisted Qwen read/write run for context evidence: capture its `thread.started` session ID and inspect only the newly created matching fixture rollout. Assert `type="turn_context"`, `payload.model="qwen3.8-max"`, `payload.effort="max"`, and `type="event_msg"`, `payload.type="token_count"`, `payload.info.model_context_window=934435`. This exact schema/value was actually observed in the temporary fix probe recorded in plan-fix.md; implementation must obtain its own event from the staged card with 983616/737712 and missing maximum. Retain rollout path/line numbers/event excerpts. Ephemeral stdout and `debug models` do not prove resolved context; no hand-computed substitute or scan of live sessions. Missing event/schema drift blocks this check visibly.

Native smoke command:

```bash
OFFICIAL_CATALOG_RUNTIME_TESTS=1 python3 -m unittest discover -s tests -p 'test_official_catalog_runtime.py'
```

### Automatic approval smoke, separate from outer isolation

The isolated launcher intentionally disables inner approvals, so an isolation pass cannot prove guardian behavior. Use the same staged-home harness with ordinary launcher/runtime sandbox and synthetic `approval_policy="on-request"`, `approvals_reviewer="auto_review"`. Do not pass `--full-access` or run this case through `agent-sandbox`.

Use the same two-hop/ingress harness. For direct `ds-flash` and Lite `mimo`, prove one valid allow and one valid deny for a benign escalated write outside the workspace but inside the fixture. Add one bounded deterministic HTTP-error case to prove the shared fail-closed path; do not repeat equivalent error matrices per profile. Capture guardian identity before remapping, correct wire model/auth/dialect after remapping, an actual write only on allow, and no write on deny/error. Existing malformed verdict/retry tests remain; no hidden manual bypass. MiMo retains the route-wide JSON-object downgrade, and its decoded verdict must be valid. No real authorization decision is involved.

Include these cases in the opt-in native smoke command above. Reuse the current 0.162.1 assessment shape and recorded request schema; if the installed schema changes, report the concrete drift rather than loosening the parser or approvals.

### Smallest outer-boundary smoke

Add one official MiMo Code Mode case to the focused native harness using the actual `agent-sandbox` + installed srt `0.0.79`, with the same staged HOME, real branch runner, synthetic shim and host. Keep the existing Claude/direct runtime regression probes intact. The official MiMo case must execute nested allowed canary read and result write, attempt one denied synthetic file read (also through a symlink), one write outside retained roots and one write under protected `.git`, and one connection to an unlisted synthetic loopback listener. Denied content must never appear in tool/wire/final logs, disallowed files stay absent, and the unlisted listener receives no request. A follow-up allowed read/tool/final proves the failures do not prevent legitimate work.

Assert existing literal output-file sink permissions, strict selected-endpoint domain list, `allowLocalBinding=false`, no Unix-socket allowance, fixed config/rules protections, and the original read/write boundary remain unchanged. Code Mode host/descendant tools must run inside the same envelope. Do not weaken the launcher, adapters or srt to make the test pass. Intentional denied operations retain their anomaly/needs-review evidence; assert successful lifecycle and the expected denial observations separately rather than demanding a clean result-validation status for this negative probe.

Run kernel tests outside a restrictive parent sandbox where the existing harness requires it, with a validated explicit srt path and no real provider/account inputs:

```bash
AGENT_SANDBOX_KERNEL_TESTS=1 SRT_TEST_BIN=/absolute/path/to/srt python3 -m unittest discover -s tests -p 'test_agent_sandbox.py'
AGENT_SANDBOX_KERNEL_TESTS=1 SRT_TEST_BIN=/absolute/path/to/srt python3 -m unittest discover -s tests -p 'test_agent_sandbox_runtimes.py'
OFFICIAL_CATALOG_RUNTIME_TESTS=1 AGENT_SANDBOX_KERNEL_TESTS=1 SRT_TEST_BIN=/absolute/path/to/srt python3 -m unittest discover -s tests -p 'test_official_catalog_runtime.py'
```

The path is a supplied local prerequisite, not a committed machine path. Optional `AGENT_SANDBOX_EVIDENCE_DIR` may point to synthetic evidence. Missing CLI/host/srt or kernel permission is an unverified prerequisite, never a pass. These native/kernel fixtures make no real provider requests and perform no live synchronization, service installation/restart or original-task replay.

### Already authorized small provider acceptance probes

Provider dispatch and project access are already authorized. During implementation acceptance, use staged catalogs/cards in a separate temporary probe home, existing approved endpoint/key resolution and the branch shim, and a tiny synthetic status-only prompt to make at most one bounded acceptance probe per covered effective endpoint/wire-model configuration. Resolve the approved real connection via the existing helper, keep its key in private temporary endpoint settings rather than native argv/logs, and label this separately from the loopback-only fixtures. Do not synchronize the live home or restart services. Set temporary provider `request_max_retries=0` and `stream_max_retries=0`, bound the subprocess timeout, and stop at the first outcome; no broad repository prompts, development/review dispatch or retry campaign. Kimi is limited to at most one small debugging/status probe, without tools/guardian/review/development requests or repeated API calls. This plan-only fix performs none of these real probes.

Record only sanitized endpoint identity/wire slug, profile/catalog selection, actual effort/Lite envelope, response status and short synthetic outcome; keys stay private. A successful status-only response establishes acceptance of that request, not tool/guardian/kernel execution or general provider certification. Offline/native/mock evidence remains separately labelled. If an endpoint rejects max, Lite or the selected model, report the exact unsupported configuration and keep the confirmed defaults/official lists; a metadata/model change requires user direction. If a prerequisite is unavailable, state the precise unverified limit instead of inventing a new authorization requirement. Endpoint overrides with different wire capabilities are assessed only for the connection actually probed.

## Documentation, risks and handoff

Update both `README.md` and `README.zh.md`: profile tables, sync/generation explanation, repository layout, five tracked raw snapshots versus generated installation outputs, Kimi `k3`/endpoint-owned wire separation, labelled GLM Flash donor, Qwen 983616/737712, all covered max defaults/advertised gaps, native default-true host and Code Mode/Lite prerequisites, route-wide MiMo JSON downgrade, guardian adaptation, narrow normal-failure recovery and validation commands. Keep paired names/numbers/limitations consistent. Preserve historical `kimi-k3` rollout examples. Distinguish synthetic/native evidence from actual small API outcomes; make no unmeasured vendor-support or high-risk remedy claims.

Residual-risk classification and ownership:

| Risk / uncovered area | Classification and owner/destination |
| --- | --- |
| Source validation, Qwen oversize override/native context, missing slug fallback, guardian dialect, default-host Code Mode execution, tool/result/boundary behavior, ordinary conversion-install pair/registry rollback | **Required in current slice** through the specified checks; not claimed complete by this plan fix. A remaining failure blocks the affected acceptance/review, with no silent fallback or boundary relaxation. |
| MiMo max omission despite user-confirmed support; Qwen unadvertised max; actual gateway acceptance | **Current implementation evidence** from already authorized small probes, controller-owned. Preserve exact lists/defaults and distinguish success/rejection/unverified outcomes. Actual rejection **requires user decision** before changing effort/model/source. Synthetic evidence alone cannot close this limit. |
| Unprobed endpoint overrides, provider tool/guardian behavior beyond status-only probes, desktop App's separate build/sandbox | **Residual limit**, controller/maintainer tracks specific gaps in implementation/closeout; no universal provider or desktop certification and no new compatibility machinery. |
| GLM Flash metadata is derived, not an independently supplied official Flash catalog | **Assigned to later work unit**, user/controller owns obtaining an official Flash source if desired. Current slice implements the explicit authorized donor unchanged except identity labels; no inferred Turbo migration. |
| Future catalog/CLI schema, host or verdict-contract drift | **Assigned to later work unit**, repository maintainer owns the next snapshot/CLI update. This slice validates the installed version and fails clearly on incompatible drift; no updater/compatibility framework. |
| Concurrent-reader/writer cross-file visibility, SIGKILL/power loss/disk destruction, failed rollback I/O, shim/service/business deployment outside the conversion block | **Residual limit**, maintainer/controller records exact guarantee and any observed failure. Ordinary conversion copy/replace/validation failure is covered now; broad transactional/crash-safe deployment remains outside this goal. |
| Real vendor policy/high-risk behavior, native GPT/business/local conversion, original task results | **Assigned to later work unit**, user/controller; explicitly outside this scope and untested. No promise of correction or task retry. |

No scope/architecture blocker is currently unresolved: GLM derivation and MiMo/Kimi decisions are authorized; raw catalogs parse natively; the inspected package contains the required host. Actual host execution, guardian handling, resolved context and outer enforcement are mandatory implementation evidence, not presumed facts. Failure needing broader authority or a different architecture must return to the controller before scope expansion.

Why this is minimal: one fixed generator mapping, five raw inputs, Kimi/Qwen selection/budget edits, narrow pair/registry recovery, existing default-host/composer/isolation paths, and focused native/transport evidence. All eight mappings preserve source metadata; runtime cases cover distinct semantics rather than every equivalent profile. Every decision/check maps to G1–G4; paired docs/reviews map to G5. There is no new feature layer, platform, migration, routing product or security redesign.

Controller completion report format: changed behavior/files; source hashes and authorized adaptations; exact validation commands with pass/fail/skip counts and synthetic evidence paths; runtime version and Code Mode host result; max before/after-shim evidence and vendor-acceptance limitations; context/card values; approval allow/deny/error evidence; outer denial/write/network evidence; unchanged lifecycle/statistics/result interfaces; docs updates; adjudicated findings/fix/re-review status; classified residual risks/owners; next gate. Later closeout adds accepted commits and draft PR URL, states manual merge/live deployment remain user-owned, and does not claim work-unit completion before Gateflow final closeout.

Plan-fix handoff: only plan.md and plan-fix.md. Next controller entry point is the prescribed independent dual plan re-review; later code/aggregate/PR reviews retain the repository routes. This fix performs no delegation, state edit, product implementation, real API probe, commit, push, PR, live deployment, merge or finance task.
