# S1 implementation: official provider catalogs

Branch `feat/official-provider-catalogs`, product base `17ef441`, accepted-plan checkpoint `9f66fc3`.
Binding decisions: [accepted-plan.md](accepted-plan.md), [plan.md](plan.md),
[plan-fix.md](plan-fix.md) and [plan-review-decision.md](plan-review-decision.md).

Implementation is delivered for controller review. The implementer parent blocked native read/write;
concurrent controller evidence now reports **12/12 official native tests passed**, including the outer kernel
case, against the current test/generator hashes. Existing kernel regression suites and gate adjudication
remain controller-owned. No delegation, staging, commit, push, PR,
merge, production sync, service start/restart or implementer provider API call occurred.
The controller's preexisting/concurrent state and probe artifacts are preserved.

## Changed behavior and files

- Five new `codex-agent/catalog-sources/{ds,glm,kimi,mimo,qwen}-model-catalogs.json` inputs are byte-exact
  copies of the approved Downloads files. [Source provenance](../../../codex-agent/catalog-sources/README.md)
  records original filenames, byte counts, fixed SHA-256 values, mappings and authorized adaptations.
  The actual copy/hash check printed all five approved hashes and exited 0. Deployment has no Downloads dependency.
- `scripts/patch-codex-model-catalog.py` assembles the complete official source object for each of the eight
  cloud profiles and appends exactly one independent native guardian. It preserves source ordering,
  unselected entries, instruction objects, empty values, omission/null and unknown extension data.
  Cloud assembly never calls `session_entry`; the existing local donor/composition remains separate.
  GPT/business cards, provider IDs and endpoint resources are unchanged.
- Native source is obtained offline with `codex debug models --bundled` in a fresh home. `--source FILE`
  still injects only native guardian/local metadata. Each full output is parsed using
  `codex -c model_catalog_json=<JSON-quoted absolute path> debug models` in another fresh home.
  Native serialization is not used to regenerate inputs. Repository checks cover source integrity,
  exact mappings, selected tool selector and card/budget invariants; native parsing owns nested schema.
  All requested assemblies/checks finish before any output replacement; dry-run writes no output directory.
- `glm-flash` retains `glm-5.3-flash`: official `glm-5.3` is deep-copied with only slug, display_name and
  description changed and explicitly labelled as user-authorized derived metadata. Original GLM entries
  are preserved; there is no Turbo switch. Cloud guardians for DS/GLM/Kimi/Qwen use direct tools and
  `use_responses_lite=false`; MiMo guardians retain native Code Mode/Lite and all other native fields.
- `codex-agent/profiles/kimi/config.toml` and the Kimi logical `to` in `codex-agent/shim-routes.json`
  now select exact `k3`. Endpoint-owned URL/key/wire model remain independent, including the existing
  factory wire default. `codex-agent/profiles/qwen/config.toml` now uses 983616/737712. Other cloud
  cards retain 1048576/786432. All eight retain max; official effort lists/defaults stay intact.
  MiMo/Qwen discrepancy notes are informational, outside the fatal warning accumulator.
- `scripts/sync-codex-agent.sh` stages/native-validates before registry replacement, preflights/backups
  registry and all replaced cards/catalogs, then installs catalog/card pairs with private temp-file replacement.
  Exact installed byte equality proves the previously validated card/slug/path/context/effort relationships.
  The EXIT cleanup restores attempted destinations and changed registry bytes on ordinary copy/replace/update/
  verification failure, preserving original modes and absence. A restoration failure is nonzero and retains
  backups. Recovery is disarmed only after verification; subsequent shim/service/business operations remain
  outside this block and can still fail the overall sync.
- `tests/test_model_catalog_generation.py` covers complete mappings/source integrity, source extensions,
  budget/name/tool/guardian failures, native acceptance/rejection, local donors, temporary-home repeat sync
  and fault injection. `tests/test_install_endpoints.py` adds a validation-aware installer stub and an
  ordinary MiMo JSON downgrade/auth/Lite preservation assertion for plain/gzip/deflate bodies.
- New `tests/test_official_catalog_runtime.py` contains the opt-in two-hop staged native fixture, four distinct
  tool/canary cases, fixture-local Qwen persistence, host=false failure, direct/Lite allow/deny, a shared
  HTTP-error case and one actual-srt official MiMo boundary case. Its commands/evidence are retained below.
- Both `README.md` and `README.zh.md` describe the same source, naming, context/effort, guardian/host/Lite,
  route-wide JSON downgrade and narrow recovery contract. Historical `kimi-k3` rollout examples remain intact.

No product edits were made to MiMo features/cards, app composition, isolation, launchers, runners,
collection/statistics, endpoint defaults, provider registry definitions or shim implementation.
No actual Lite forwarding defect was found that required a product shim change.

## Actual validation commands and outcomes

The durable command manifest is [implementation-validation.json](evidence/implementation-validation.json).
It retains argv/commands, exit codes, individual log paths/hashes, counts and source hashes.
Complete output is retained at `/private/tmp/official-implementation-checks-20261012`.
The parallel *process* driver was `python3 /private/tmp/run-official-focused-checks.py` (exit 0);
it dispatched the following checks, with no agent delegation:

| Actual command | Outcome |
| --- | --- |
| `python3 -m unittest discover -s tests -p 'test_model_catalog_generation.py'` | 25 tests, exit 0 |
| `python3 -m unittest discover -s tests -p 'test_provider_registry.py'` | 10 tests, exit 0 |
| `python3 -m unittest discover -s tests -p 'test_install_endpoints.py'` | 19 tests, exit 0 |
| `python3 -m unittest discover -s tests -p 'test_agent_sandbox.py'` | 80 tests, 10 kernel skips, exit 0 |
| `python3 -m unittest discover -s tests -p 'test_agent_sandbox_launch.py'` | 6 tests, 1 kernel skip, exit 0 |
| `python3 -m unittest discover -s tests -p 'test_agent_run_results.py'` | 56 tests, exit 0 |
| `python3 -m unittest discover -s tests -p 'test_codex_model_defaults.py'` | 5 tests, exit 0 |
| `python3 -m unittest discover -s tests -p 'test_shim_service.py'` | 8 tests, exit 0; service commands use fixture stubs |
| `python3 -m unittest discover -s tests -p 'test_official_catalog_runtime.py'` | 12 tests, 11 opt-in skips, exit 0; only the fixture control executes |
| `bash -n scripts/sync-codex-agent.sh` | exit 0 |
| `zsh -n scripts/agent-tools.zsh scripts/codex-agent-run` | exit 0 |
| `python3 -m py_compile scripts/patch-codex-model-catalog.py tests/test_model_catalog_generation.py tests/test_official_catalog_runtime.py tests/test_install_endpoints.py` | exit 0 |
| `git diff --check` | exit 0 |

The focused matrix ran 221 tests, with 22 explicit skips (199 executed). Skipped kernel/native tests
are **not** acceptance passes. Subsequent targeted/syntax checks and exact commands are also in the manifest.

Earlier iterations are preserved rather than replaced with a final pass:

- Catalog tests initially ran 23 tests, exit 0 (`/tmp/official-catalog-unit-first.log`); the final 25 add
  absent-original recovery and actual native rejection before registry/pair mutation.
- Install tests initially ran 18 tests, exit 0 (`/tmp/official-install-first.log`); the final 19 add
  route-wide ordinary-session format/auth/Lite coverage.
- The first opt-in full native command ran 12 tests, 7 failures, 1 skip, exit 1
  (`/tmp/official-native-first.log`). Its synthetic fixture incorrectly tried to find nested Code Mode tools
  among top-level descriptors; diagnostic HTTP500s were fixture errors, not vendor failures.
- The second identical command ran 12 tests, 6 failures, 1 skip, exit 1
  (`/tmp/official-native-second.log`). Native output identified `functions.exec` as unsupported:
  the custom call must use `exec`, while nested `tools.exec_command` is advertised in its native descriptor.
  The fixture was corrected to that actual shape; no production dialect or boundary was changed.
- A targeted five-test command (exact argv in manifest, `/tmp/official-native-third.log`) then ran
  MiMo tool/allow/deny/host=false and Qwen context: 3 passed, 2 failed due to parent Seatbelt, exit 1.
- Final full opt-in command below ran 12 tests: **7 passed, 4 failed, 1 skipped**, exit 1
  (`native-final.log`). The four failures are DS/Kimi/MiMo/Qwen read/write under the restricted parent.
- Final targeted direct allow + host=false ran 2 tests, exit 0 (`native-final-targeted.log`);
  final Lite allow ran 1, exit 0 (`native-lite-final-targeted.log`).
- `PYTHONPATH=tests python3 -m unittest test_model_catalog_generation.ConversionSyncTests.test_actual_native_rejection_before_registry_and_pair_mutation`
  ran 1, exit 0; `native-parser-rejection-final.log` preserves the actual CLI diagnostic:
  `unknown variant native-invalid-enum, expected bytes or tokens`, native exit 1. Registry/pair sentinels
  stayed unchanged. The incidental temporary-helper PATH warning did not substitute for native rejection.
- Installer bootstrap was rechecked after giving its native catalog read a fully temporary HOME/CODEX_HOME/SQLITE_HOME;
  exact command/outcome are retained in the manifest. Its stubs never invoke a model API.

Read-only preflight used `pwd`, `git status --short --branch`, `git log -4 --oneline`, `rg --files`, `rg -n`,
`cat`/`sed` for AGENTS/approved artifacts and affected source/tests, and `command -v codex`/`command -v srt`.
It confirmed the accepted plan/current branch and permitted paths. One search named nonexistent
`tests/test_auto_review_shim.py` (rg reported that specific missing file); existing shim tests were found
in `test_install_endpoints.py`. One source-metadata inspection attempted to iterate MiMo's null
`instructions_variables` and exited 1 with TypeError; product loading preserves that native-valid null.
No repeated source/version research or real auth/business read followed either diagnostic.

## Native and two-hop evidence

[implementation-native.json](evidence/implementation-native.json) retains final fixture paths,
command manifests, observed version/feature output, per-hop model/auth/effort/Lite/format facts,
collector status, actual tool failure outputs and Qwen event excerpts.
Each private fixture retains `commands.jsonl`, `resolved-routes.json`, `connections.json`, raw/decoded
`ingress.jsonl` and `upstream.jsonl`, staging/native/runner stdout/stderr, event stream and final message.
Only synthetic keys/prompts/files are present. External provider requests by this harness: **zero**.

The fixture binds owned OS-assigned loopback upstream and eight shim listeners, validates effective
provider URLs against their retained listener identities, fills all eight private Codex endpoint overrides
plus synthetic local, and starts a fresh shim subprocess. A checked upstream opener rejects any URL outside
this fixture. Native ingress is captured before transforms by the test-only `do_POST` byte replay;
upstream captures are independent. Endpoint wire slugs/keys differ from logical slugs; an explicit wrong
inbound-key case proves replacement without changing production logging. Ordinary streams retain their
existing unbuffered behavior. Mock/synthetic format tests also retain plain/gzip/deflate Lite data.

Measured native CLI output is `codex-cli 0.162.1`. Feature output reports `code_mode_host stable true`
with the key omitted and `code_mode=false`. Native MiMo emits the Lite header, `additional_tools`
with the real exec descriptor, no top-level tools, and reasoning context all_turns. Its JS cell actually
calls the advertised nested command tool. The nested tool cannot enter Seatbelt here:

```text
sandbox-exec: sandbox_apply: Operation not permitted
Process exited with code 71
```

Direct sessions show the same parent restriction. No direct-mode substitution, host-enabling feature,
full-access replacement or weaker sandbox was introduced. Native final CANARY text after this failure is
not counted as a smoke pass: required result files are absent, native tool-result count is zero and the
unchanged collector rejects the result. All four failed in the implementer parent. The later controller final evidence below supplies their
actual successful execution without changing the boundary.

The positive host JS-cell observation is distinct from tool-read/write acceptance. Explicit
`features.code_mode_host=false` produced the actual unavailable-host error, no direct fallback or artifact,
and failed collection; its negative test passed. All covered card defaults remain max, and actual native
session ingress and upstream preserve max. Complete source metadata coverage is eight profiles;
full runtime cases are the four distinct profiles specified by the plan.

Direct DS and Lite MiMo guardian allow/deny, plus direct HTTP400 error, passed using native auto_review
and on-request policy (without isolation/full-access). Guardian identity is captured as codex-auto-review
before wire remapping. The native assessment schema is risk_level/user_authorization/outcome/rationale;
valid synthetic verdicts are retained in `guardian-verdict.json`. A real fixture write occurs only on allow,
with exact synthetic bytes; deny/error create no write. MiMo's captured json_schema becomes json_object for
guardian traffic, with a valid decoded verdict. The ordinary-session downgrade is tested independently;
this remains route-wide and loses schema enforcement.

The Qwen persisted run creates its own matching fixture rollout. It proves actual turn_context model
qwen3.8-max/effort max and native event_msg/token_count/info.model_context_window **934435**, from the
983616/737712 card and source's absent maximum. Path and line excerpts are in the native evidence JSON
and fixture `context-evidence.json`. This event is measured despite the blocked shell; it is not a computed
substitute or a complete Qwen read/write success. Only this newly created matching fixture session was read.

The controller's [preliminary native artifact](evidence/controller-native-preliminary.json) separately
recorded successful actual DS execution outside the parent but a relative-path canary evidence issue.
The fixture now supplies the absolute canary path and asserts canary_read_candidate; collection semantics
were not edited. That preliminary test was not a clean pass. The later matching-source controller final run below
verifies the corrected canary fixture.

## Controller-owned checks and residual classifications

Run the prepared native/kernel commands outside a restrictive parent, without adding a weaker boundary:

```bash
OFFICIAL_CATALOG_RUNTIME_TESTS=1 python3 -m unittest discover -s tests -p 'test_official_catalog_runtime.py'
AGENT_SANDBOX_KERNEL_TESTS=1 SRT_TEST_BIN=/absolute/path/to/srt python3 -m unittest discover -s tests -p 'test_agent_sandbox.py'
AGENT_SANDBOX_KERNEL_TESTS=1 SRT_TEST_BIN=/absolute/path/to/srt python3 -m unittest discover -s tests -p 'test_agent_sandbox_runtimes.py'
OFFICIAL_CATALOG_RUNTIME_TESTS=1 AGENT_SANDBOX_KERNEL_TESTS=1 SRT_TEST_BIN=/absolute/path/to/srt python3 -m unittest discover -s tests -p 'test_official_catalog_runtime.py'
```

Optional `OFFICIAL_CATALOG_EVIDENCE_DIR` and existing `AGENT_SANDBOX_EVIDENCE_DIR` retain synthetic evidence.
Kernel cases require a real absolute installed srt 0.0.79; the existing adapter validates its package.
The implementer did not run these parent-unsandboxing-dependent commands or the outer kernel case.
The controller subsequently supplied the complete official native/kernel run below.
The fixture preserves the established isolation command contract (no native passthrough sandbox option),
actual srt enforcement, default host, fixed config/rules and literal sink permissions. Its MiMo case attempts
denied/symlink reads, outside-root and protected .git writes, an unlisted loopback connection, then a permitted
canary read/write. It checks retained real settings, denies, absent disallowed files/no listener request,
no leaked denied content, successful lifecycle and needs_review denial diagnostics. It was unverified by the implementer execution and is now verified by the separate controller evidence below.

Final controller evidence arrived during the handoff: [controller-native-final.json](evidence/controller-native-final.json)
reports the exact command

```bash
OFFICIAL_CATALOG_RUNTIME_TESTS=1 AGENT_SANDBOX_KERNEL_TESTS=1 SRT_TEST_BIN=/Users/leo/.local/bin/srt OFFICIAL_CATALOG_EVIDENCE_DIR=/private/tmp/ocf54 python3 -m unittest discover -s tests -p test_official_catalog_runtime.py
```

It exited 0: 12 tests passed, zero skipped, 35.754 seconds. The short fixture root avoids native Unix
socket path-length limits; no socket allowance was added to the outer policy. The reported frozen
SHA-256 values match the current runtime test and generator exactly. The separate earlier
[controller-kernel.json](evidence/controller-kernel.json) also reports one actual official MiMo kernel pass.
These are controller commands; the implementer did not execute them or request parent unsandboxing.

`python3 /private/tmp/verify-official-controller-evidence.py` exited 0 and wrote
[implementation-controller-check.json](evidence/implementation-controller-check.json). It independently
verified current source hashes, all retained capture/command hashes, actual new result-file bytes versus
last messages for DS/Kimi/MiMo/Qwen/kernel, positive native tool/read evidence, max and synthetic wire/auth
at both hops, Qwen's own newly matched rollout event value 934435, and the kernel's absent forbidden
writes/unlisted request/denied content with strict binding/network policy. No business/auth/private-key
input was read. This closes the observed official harness prerequisites through controller evidence;
it does not turn the earlier restricted-parent failures into implementer passes.

The existing `test_agent_sandbox.py` and `test_agent_sandbox_runtimes.py` opt-in kernel regression
commands remain controller checks unless separately supplied; their ordinary skips are still not passes.
No review or implementation-gate acceptance is inferred merely from test success.

[provider-acceptance.json](evidence/provider-acceptance.json) is controller-owned concurrent evidence:
it reports eight accepted tiny status-only calls, max before/after shim, zero retries and Kimi exactly once.
The implementer made no vendor requests and did not read its private endpoints/keys/raw business inputs.
This supplied artifact is distinct from implementer synthetic evidence and does not certify provider tools,
guardian, desktop or kernel behavior. Kimi quota must not be spent again by this implementation.

| Area | Classification / owner |
| --- | --- |
| Four native canary read/write/collection successes in a Seatbelt-capable parent | Passed in matching-source controller final evidence; implementer parent failure retained; controller adjudicates gate |
| Official MiMo host descendants under real outer deny/write/network policy | Passed in matching-source controller final evidence, with expected needs_review denial diagnostics; controller adjudicates gate |
| Existing opt-in kernel regression suites | Prepared controller checks; not supplied or executed by implementer |
| Native parsing, source/card/mapping/guardian invariants and ordinary rollback | Current implementation checks passed; independent controller review remains |
| Tiny actual max acceptance | Separate controller-provided status-only evidence; no implementer/API or tool/guardian certification |
| Derived GLM Flash | Explicit user decision implemented; official independent Flash source belongs to later user/controller work |
| Route-wide MiMo structured format downgrade | Existing documented residual limit; retained with direct coverage |
| Cross-file reader visibility, concurrent writers, SIGKILL/power loss/disk destruction or restoration-I/O recovery | Excluded broader guarantees; maintainer/controller owns residual risk |
| Ancillary shim/service/business deployment after conversion block | Outside narrow rollback; maintainer/controller owns deployment outcomes |
| Desktop builds, unprobed overrides/vendor tools, future CLI/schema/host drift | Specific unverified limits/later maintainer work; no compatibility/updater framework |
| Original tasks, high-risk investigation, GPT/business/local conversion, merge/live deploy | Outside S1; user/controller ownership |

Next entry point: controller completes remaining kernel regression checks, adjudicates the implementation
evidence, then owns the two independent review/fix gates, commits and PR workflow. This handoff makes no
implementation acceptance, review-pass or work-unit-closeout claim.
