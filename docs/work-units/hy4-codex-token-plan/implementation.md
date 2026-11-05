# Hy4 Codex implementation handoff

Status: implementation and validation complete; **controller next-entry = code review**.
Branch `feat/hy4-codex-token-plan`, baseline `2cb3127`. No agents dispatched by
this implementer. No live endpoint/config changes, sync, commit, push or production
listener/service changes were performed. Controller owns independent reviews,
adjudication, accepted fixes, commit/push/PR and eventual authorized deployment.

## Implemented behavior

- Restored model-only `hy` card: logical model `hy4`, provider ID `hy`, effort
  `high`, context1048576 / compact786432, web search disabled. Registry/route and
  launcher agree on stable port8796 and prefix `/v1`. The port was absent from
  repository allocations and a local bind check succeeded before addition.
- Factory `default.hy.codex` is direct `https://tokenhub.tencentmaas.com/v1`,
  `hy4`, blank key. `default.hy.claude` moves preview to `hy4`, preserving its
  base and blank key. Existing whole-runtime default/override semantics remain.
  Private direct keys are not automatically borrowed from another runtime.
- Runner supports `hy` / `hunyuan`, help and inventory. Existing launch paths
  provide `hy_codex`, `hy_codex_app`, `CodexAgent-HY` title and shim readiness.
- `hy_session_entry()` constructs repository-authored compatibility metadata
  field by field with generic coding instructions. No native session donor or
  official provider instructions are copied. It uses text input, direct tools,
  no Lite/search and high effort. Window settings follow the existing Hy docs
  table convention, without measured context/vision claims.
- Hy-only assembly validates the exact card and appends the independently
  bundled native guardian, preserving security/instructions/tools and changing
  only established direct/non-Lite metadata. The five official snapshots,
  hashes, mappings, existing assembled outputs and strict checks are unchanged.
  Generic shim behavior, approval policies, native exits/finals and other
  providers are unchanged. No effort remap or JSON/protocol downgrade was added.
- English/Chinese READMEs document both placeholder Token Plan overrides and
  the current account-permission blocker. Skill inventory includes Hy Codex.
  The operative plan is condensed to accepted runtime integration scope.

## Validation and actual exits

Detailed commands/results and compressed logs:
[implementation-test-results.json](implementation-test-results.json),
[implementation-test-evidence.json.gz](implementation-test-evidence.json.gz).

| Check | Actual outcome |
| --- | --- |
| Eight affected deterministic suites | 205 tests, 11 skips, exit1 only for stale expected catalog count9 instead of10 |
| Affected sync/install inventory recheck after count fix | 1 test, exit0; two syncs parse20 catalogs, installed bytes/modes/registry preserved |
| Native Hy synthetic ordinary/tool + allow + deny + HTTP error | 4 tests, exit0 in19.654s, unrestricted parent, all fake credentials |
| Python syntax, zsh syntax, diff whitespace | exit0 |
| All skill validation | exit0, six skills |
| Final actual direct staged native workflow | native0, runner0; saved-evidence qualification0, details below |

The affected suites were `test_model_catalog_generation`, `test_provider_registry`,
`test_install_endpoints`, `test_sub_agent_preflight`, `test_agent_sandbox`,
`test_agent_sandbox_launch`, `test_agent_run_results`, `test_shim_service`.
The sole failed assertion and subsequent correction are retained, not reported as
an all-green original suite exit. Eleven skips were explicit outer-kernel opt-ins;
outer kernel tests were not required because no outer boundary changed. The
reasoning-history suite was not rerun because its source/tests were unchanged.
An accidentally broad initial discovery was interrupted (exit130) before running
the affected selection; no completion/pass claim is made for that command.

Coverage includes actual native parsing of every assembled catalog, unchanged
complete official-source assembly, Hy identity/effort/card consistency and no
source borrowing, route/registry/launcher consistency, Hy app composition,
whole-connection direct-vs-Plan resolution with fake distinct keys, old-schema
whole-document rejection and both updated factory locations accepting Hy Codex,
CLI credential scrubbing, staging/install/reinstall preservation, and existing
native exit/final contracts. The native ordinary Hy fixture selects through the
`hunyuan` alias and actual launcher/card; both ingress and mapped wire model/key
are checked. Guardian allow executes its sentinel; deny and error leave it absent.

## One final staged actual direct workflow

Predeclared in [staged-integration-declaration.md](staged-integration-declaration.md):
one workflow, maximum300 seconds /12 upstream attempts including retries, no
Plan calls, fallback or retry to green. Parent exec used `require_escalated` to
avoid nested sandbox EPERM; native retained workspace-write/on-request/auto_review.

Actual private evidence root:
`/private/tmp/hy4-codex-task/staged-20261105-114719/staged-direct`.
Sanitized summary [staged-integration-results.json](staged-integration-results.json)
and compressed complete evidence [staged-integration-evidence.json.gz](staged-integration-evidence.json.gz)
contain actual requests/responses, chunk timings, native events/stderr, runner
report, source hashes and saved initial measurement. No private config, key or
auth header is included. The summary records archive SHA256 and entries.

The harness staged this branch's runner, launcher, result adapter, endpoint helper,
factory and actual `hy.config.toml`; it generated the final Hy catalog with the
repository generator and native parser. Shared provider ID remained `hy`; only
its loopback URL and launcher port check used an ephemeral listener. The route
came from branch `shim-routes.json`. Production port8796 was not bound.

Actual result: **72.148s, five upstream attempts, zero retries, all HTTP200**.
Four session streams completed incrementally at high effort. Native read a fresh
canary, copied/compared `result.txt`, and returned actual correlated tool outputs
to Hy. Native requested the exact authorized escalation. The independent guardian
used native-selected low effort, returned schema-valid `{"outcome":"allow"}`,
and preserved original instructions/input/tools/schema; only `model` changed on
the wire. Native executed the sentinel command, continued its successful tool
result and completed a final with the observed canary. Runner/native exits are0.
Persisted turn context confirms `hy4`/high/on-request/workspace-write; native's
separate guardian rollout is its internally generated read-only/never context.

**Retained tooling correction:** the staged copy loop shadowed workflow variable
`name` with its last filename, so the saved prompt explicitly authorized writing
marker `agent-run-result.py`, and Hy wrote that exact marker. The original analyzer
incorrectly expected the directory name `staged-direct`: initial harness exit1
with sentinel criterion false despite native/runner0 and successful execution.
[Original measurement](staged-integration-initial-measurement-results.json) remains
preserved, with its full result inside the evidence archive. The analyzer now
checks the saved exact harmless `printf %s <marker> > <sentinel>` command, exact
path, correlated escalation and actual contents. Saved-evidence-only reanalysis
passes every criterion (exit0). The copy-loop variable is fixed for future use;
**no new inference or upstream request was made**. Controller can adjudicate this
local measurement correction directly from saved prompt/tool/result evidence.

## Evidence hygiene and residual risks

Historical direct-1 remains setup-invalid, direct-2 remains the accepted full
pass, and Plan-1/2 remain HTTP403001 permission failures (32 historical attempts).
The staged workflow is a separate single observation, not a replacement sample.
Historical full results/ingress traces (1674292 bytes) are preserved in
[investigation-evidence.tar.gz](investigation-evidence.tar.gz) (343164 bytes), with
member hashes and extraction instructions in
[investigation-evidence-index.json](investigation-evidence-index.json).
The readable [investigation-results.json](investigation-results.json) is4595 bytes.
Archives contain sanitized evidence only, never private endpoint/config/key files
or captured auth headers. Known direct/Plan key values were checked absent.
Cleanup skips every symlink before chmod; no installed executable was touched.
The earlier investigation's corrected executable-mode incident remains documented
in investigation.md and archived historical results; it was not repeated here.

Residual risks: Token Plan account/package permission is unresolved; no new Plan
calls were made. Current direct acceptance is bounded runtime evidence (one prior
complete observation plus one staged integration), not a reliability guarantee.
The final run retained1081 native stderr lines, including stream reasoning-summary
noise, without affecting observed tools/review/completion. No context or vision
capacity was measured. Live private Hy Codex key/override provisioning remains
controller-owned; factory keys stay blank. Preference about enabling a known
permission-blocked Plan override is separate from repository acceptance.

## Changed file manifest and next entry

Product/config/documentation:
`codex-agent/profiles/hy/config.toml`, `codex-agent/model-providers.toml`,
`codex-agent/shim-routes.json`, `config/endpoints.example.json`,
`scripts/codex-agent-run`, `scripts/agent-tools.zsh`,
`scripts/patch-codex-model-catalog.py`, `codex-agent/catalog-sources/README.md`,
`skills/sub-agents/SKILL.md`, `README.md`, `README.zh.md`.

Tests: `tests/test_model_catalog_generation.py`, `tests/test_provider_registry.py`,
`tests/test_install_endpoints.py`, `tests/test_sub_agent_preflight.py`,
`tests/test_official_catalog_runtime.py`.

Work-unit edits/additions: this handoff, final `plan.md`, `probe_hy4.py` staged mode
and analyzer correction, investigation summary/archive/index and readable
investigation archive links, staged declaration/summary/initial measurement/evidence,
and test summary/evidence. Existing `scope.md`, `controller.md`, `sources.md` and
initial probe declaration remain the controller/investigation record. The three
unrelated untracked `docs/reviews/runner-handle-loss-20261023-*` files are untouched
and excluded from this work unit.

**Next: controller code review**, including the required independent review pair;
no review dispatch, commit or PR action by this implementer. After review/final
closeout, controller should run the authorized component sync from this checkout:

```bash
./scripts/sync-agent-tools.sh
./scripts/sync-codex-agent.sh
./scripts/sync-skills.sh
```

Both installed endpoint factories must understand Hy Codex before any new private
`hy.codex` tuple is exposed. Preserve whole direct-vs-Plan tuples and unrelated
private settings. Reload interactive functions with `source ~/.zshrc` or a new
shell, reopen Agent sessions for skills; installed runner callers need no shell
reload. No sync was performed in this implementation stage.
