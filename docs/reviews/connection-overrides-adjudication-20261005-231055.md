# Connection overrides: controller adjudication

## Final scope and user decisions

- Branch: `feat/connection-overrides`; base/HEAD before commit: `d072c806a2950d3e21fc9c35e76ddd5736c1cb6d`.
- Private JSON owns complete `{base_url, upstream_model, api_key}` tuples under `default` and optional `override`. Factory defaults retain existing provider URL/model choices and contain no cloud keys. Valid user files are preserved by reinstall/sync.
- During the parallel initial reviews the user explicitly removed backward compatibility and migration from this PR. All legacy parsing/import, deployed-card seeding, `--migrate`, migration tests and migration instructions have been deleted. `--initialize` only creates a missing factory-default JSON, mode 600; no old key file or provider key environment variable is consumed.
- The user wants a one-time conversion of this machine's configuration immediately before a future, explicitly requested live sync. No live conversion, synchronization or restart was performed here.
- Original reviews concern a frozen earlier candidate containing migration. They are preserved unchanged as audit inputs; they do not certify the final controller fixes. The controller independently checked the final affected paths and tests below. No unresolved accepted findings remain.

## Independent review inputs

- MiMo: [code-review-20261005-225917.md](code-review-20261005-225917.md), label `connections-mimo-20261005-223351`, runtime Codex.
- MiMo Flash: [code-review-20261005-224550.md](code-review-20261005-224550.md), label `connections-mimo-flash-20261005-223351`, runtime Codex.
- Both preflights returned `setup_status=ok`. They received the complete independent task context, explicit user/scope boundaries, exact base/branch, 12-file SHA256 manifest and immutable diff, unique output directories, no-persist mode, and no-subagent instructions. Calls were independent and parallel, each escalated through its own managed `exec_command`.
- All 12 frozen source hashes remained unchanged until both outer processes exited. Both artifacts matched their own canary exactly and included actual source/tool evidence. Both JSONL streams parsed in full, contained one `turn.completed`, no `turn.failed`, and had clean final answers without literal fabricated tool syntax.
- Both outer exit codes were 0, collected via managed handles: MiMo session 13867 and MiMo Flash session 20435. A completed process is not a code approval: initial blocking findings were adjudicated below.
- Provider identity is the configured runner route. MiMo's self-description as GPT-5 is not serving-model evidence; neither JSONL stream proves the actual upstream model identity. No live identity probe was authorized or performed.

## Finding decisions

| Review finding | Decision | Closure and evidence |
| --- | --- | --- |
| MiMo 1: guardian `IncompleteRead` escapes retries | Accepted, fixed | The buffered read now catches HTTP/I/O errors per attempt, closes failed responses and tries up to three times. Exhausted read failures return 502 without a handler traceback. Mock regression verifies two failed reads then success, and all-three-failed exhaustion; ordinary requests remain unbuffered. This was also present in the base; it was fixed within the touched request path. |
| MiMo 2 / Flash 1: initialization imports old credentials | Accepted, fixed through scope removal | Deleted legacy import/seeding and migration entirely. Initialization reads only factory defaults. Isolated probe with a fake inherited provider key confirms exact factory JSON, mode 600, and no backup; initialization test checks equality to factory. |
| MiMo 3: direct helper retains alternative auth | Accepted, fixed | `launch_claude` scrubs inherited credential variables before inserting the selected canonical token. Direct-helper regression seeds fake `ANTHROPIC_API_KEY`, old token and other keys; only selected `ANTHROPIC_AUTH_TOKEN` reaches the fake Claude. Key absent from argv/settings. |
| MiMo 4: gzip/deflate skip existing provider transforms | Accepted, fixed | Handler decodes the body once, applies model/id/schema/tool transformations to plain bytes, then restores encoding once if changed. Unmodified requests preserve their original bytes; unknown/broken encodings retain visible pass-through diagnostics. Tests assert all enabled transformations for plain, gzip and deflate and ordinary `read1` streaming. These existing protocol transforms are preserved; no legacy configuration compatibility is added. |
| MiMo 5: mixed legacy key-file migration blocked | Closed by user scope removal | No migration/legacy-key parser remains. This finding no longer applies to the final implementation; no new migration mechanism or mixed-file parser is added. |
| MiMo 6: local Claude documentation contradicts configurable tuple | Accepted, fixed | Both READMEs now say local Claude consumes configured URL/model/token, with initial token `local`. |
| MiMo open question: broad credential wording vs app auth files | Accepted clarification, fixed | Docs distinguish gateway API keys (not placed in app config/registry/catalog/plist) from Codex account login auth files. Existing login behavior retained. |
| Flash 2: ambiguous local URL file guidance | Accepted, fixed | Both READMEs name the exact JSON path and `local.claude.base_url` / `local.codex.base_url` under default or override, plus health-check behavior. |
| Flash 3: permission check accepts 0400/0700 despite 600 contract | Accepted, fixed | Require owned regular file with exact `stat.S_IMODE == 0o600`. Regression cases reject 0400/0700/0644 and accept 0600. |
| Flash 4: clean EOF loses diagnostic dump | Accepted, fixed | Dump condition uses current `json` rewrite category, including transform suffixes, rather than removed `bytes` fast path. Regression verifies incomplete ordinary stream dumps request/response without buffering/retry; complete streams do not dump. |

## Dispatch acceptance and warnings

### MiMo

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: complete
required_evidence: complete
canary_status: match
result_status: accepted
warnings:
  - item_2 hash command exit 127 recovered with absolute command paths
  - initial guardian probe was not HOME-isolated and is excluded
  - item_58 direct-helper fixture exit 1 recovered with resolved Python interpreter
evidence_gaps: []
retry_class: none
```

- Output directory: `/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.rBpkpt`; JSONL, stderr and last-message files share the unique task label. Stderr was empty.
- `item_2` failed to resolve shasum/awk. Its loop used zsh's special `path` parameter, changing PATH; absolute tools restored verification. The subsequent 12-hash match and byte-identical frozen diff are the identity evidence.
- Initial guardian probe accidentally read the real private endpoint path and stopped at validation (zero upstream attempts, no contents printed). This violated the isolation instruction. Excluded from evidence; a later fresh-HOME fake-config probe reproduced the real read failure with one upstream attempt. Controller independently verified the fixed path using isolated regression tests; no conclusion relies on the accidental real-HOME probe.
- `item_58` failed because the fake Claude's interpreter was unavailable; no capture was generated. The successful subsequent probe supplies evidence, and the controller's direct-helper regression independently verifies the final fix.
- Syntax checks generated ignored bytecode files; reviewer removed the generated files. No source hash changed. No retry/provider switch was needed.

### MiMo Flash

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: partial
required_evidence: complete
canary_status: match
result_status: accepted
warnings:
  - item_8 hash command exit 127 recovered
  - item_10 alternate hash command exit 127 recovered by item_12
  - stderr router diagnostics recovered without losing required evidence
  - intermediate literal tool syntax is not execution evidence
evidence_gaps: []
retry_class: none
```

- Output directory: `/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.4f2SQB`; JSONL, stderr and last-message files share its unique task label.
- `item_8` and `item_10` failed to resolve hash tools after assigning zsh `path`; `item_12` successfully verified all 12 hashes with absolute tools. Later final hash verification also passed.
- Stderr contained six router diagnostics not represented as normal structured tool results: unavailable `request_user_input`, four malformed-argument errors, and unsupported `apply_patch`. These are recorded as partial tool trace. No missing user input blocked this fully specified review; the long find command completed; artifact creation succeeded through actual recorded shell execution after the patch tool failure. The controller read the artifact and independently checked each required finding path/test.
- Intermediate messages `item_18`, `item_19`, `item_21`, `item_22` contained literal tool syntax; no execution is inferred from those messages. The final answer was clean, essential source/hash/test/artifact operations have actual recorded command results, and the review conclusions are independently verified.
- Reviewer also inspected redacted runtime environment metadata contrary to the request to avoid environment output. No credential values were printed; no finding depends on that metadata. A broad find completed normally and was not finding evidence. No retry/provider switch was needed.

## Final controller verification

- Independently checked configuration layering/validation/init, Claude shell and direct helper auth boundary, Codex CLI/App/local launchers, provider registry removal of env_key, shim URL/model/auth snapshot, ordinary streaming, response-read retries, compression transforms and diagnostic dumps, installer user-data ownership, bilingual guidance and associated tests.
- Focused suites: 33 tests passed in 14.166 seconds.
- Full repository unittest discovery: 65 tests passed in 27.233 seconds (exit 0).
- Shell syntax, Python compilation, all six skill validations and `git diff --check` passed.
- A deliberate `rg` absence check for legacy/migration function/flag names returned no matches (exit 1), confirming deletion; this is expected absence, not a failed validation.
- Tests use isolated fixtures, fake keys/mocked launches and loopback HTTP only; static `codex debug models` catalog read is permitted. No live gateway request, deployment or key migration was performed.
- Residual limits: actual hosted gateway streaming/tool/schema support must match the retained profile metadata; no protocol conversion or catalog/context resizing is implemented. Real serving-model identity and actual application runtime precedence were not measured. Same-user file access remains possible; mode 600 and env scrubbing do not create a same-user security sandbox.

## Final source identity

Final source diff SHA256: `36d11c425b79a4c3b4df9e76f2b5cf55898a8a463a1815daacc00bff73ab698b`.

```text
README.md bca4bcb5130f47942d22f93a47d0686a1988133e6f1a8bfd15d68e94f9447106
README.zh.md d214886a8aaea7591f0b1a1ce4c5d4397e6b5d75ddc07309c133876e140aa2d0
codex-agent/bin/codex-auto-review-shim 7ae5d6d7dc86050b466d06cc63685eb1589d873cf730fa0ac3479dfed44d7cc7
codex-agent/model-providers.toml ce1f5cb1fd5ded1be4df904f03bade8c88a2daa5354fb8284a16508dd1af7ba8
config/endpoints.example.json d27ed29a4e3cf24063ee803fb103c71fc669a97275a0d643c2a3bfcca28bc2b0
install.sh 645e440c086959ad33e0fc844df5a1e6bda6bca231f2e1f781775b340c8dbdef
scripts/agent-endpoint.py 605c823a922765d6d56af6defea7f6a7f8bade71de9d81da85a518b557a7a475
scripts/agent-tools.zsh ae2c484a05fa0c8dadaa3c6d48e2947e6f4002cb407e1290e6cb03f3cb6978fd
scripts/compose-codex-app-config.py b383400ace0e1d5e92d20b721eb887920126a24f59f3fa07c79e797d53f73e2c
tests/test_codex_model_defaults.py f5939434a10379fe40bd4cf031bfd4ab7bc3404f9af631c934f66bc354186a3f
tests/test_install_endpoints.py 74b12921dd6a35db74357ff73540dbd92d83c0f86f1d5f58995f3038fc383c37
tests/test_provider_registry.py 673e39ab5fae29106a7870f20c782dea871e4ee8c29d7ecf7edcf0fff0f36585
```

Controller conclusion: accepted findings are fixed or removed by the explicit user scope decision. Final isolated tests and source checks pass; ready for commit/push/PR, with manual user merge and no live deployment in this task.
