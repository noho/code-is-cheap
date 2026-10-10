# Plan: agent-sandbox-workspace-routing

- Gate: plan; complete for independent plan review, **not accepted or implemented**.
- Binding scope: `goal.md`, confirmed by the user/delegated caller on 2026-10-11.
- Worktree: `/private/tmp/code-is-cheap-workspace-routing`.
- Work branch: `fix/agent-sandbox-workspace-routing`.
- Baseline/observed HEAD: `20fc6c37751836329143567c166990bdffa9de3c`.
- Plan artifact: `docs/gateflow/agent-sandbox-workspace-routing/plan.md`.
- Controller: root; owns adjudication, routing and subsequent gate transitions.
- This dispatch writes this plan only. It does not update goal/state/evidence, edit products, run probes, delegate, write Git, install/sync or publish. Root dispatches the two independent planreview calls. Repository AGENTS.md defaults yield to this explicit dispatch boundary.

## Confirmed goal, motivation and success

Restore the existing Codex `gpt-6-sol` managed-auth HTTPS startup inside the current macOS agent-sandbox envelope by preparing explicit certificate input. Preserve the provider/model/auth route, kernel-enforced read denials, retained write scope, strict network restrictions and real failure diagnostics.

The confirmed success signals are:

1. A fresh synthetic isolated `codex-agent-run --provider gpt-6-sol` produces a genuine final answer and successful native/runner terminal. Original failures remain intact.
2. Kernel read-boundary verification still succeeds; direct and symlink reads of denied material remain inaccessible; write/network restrictions are unchanged. A CA input cannot override a caller deny.
3. Effective caller CA inputs retain runtime precedence. Missing, denied or invalid selected input yields a located failure without a boundary-bypassing fallback.
4. Focused CA/launch regressions and necessary existing sandbox tests pass.
5. Root closes the required independent reviews and gateflow gates with evidence/checkpoints and a new draft PR. User merges manually; no live sync.

Non-goals: provider/model/auth migration; collector or recovered-stream changes; extra routing/proof fields or prompt protocol; trustd grants, weaker isolation or TLS verification bypass; changed business files/contracts/deny lists; original caller task replay; process/pane operations; new installer, runtime dependency, scheduler or platform; broad certificate/security refactoring; merge or live installation.

The only design authority is the confirmed goal and sanitized diagnostic evidence; no separate design document was supplied. There are no blocking scope questions. Existing untracked goal/state/evidence belong to root; this dispatch owns only the new plan.

## Facts and direct evidence

All source locations below refer to the baseline, before implementation.

| Source | Observed fact and design implication |
| --- | --- |
| `AGENTS.md:3-12`; `goal.md`; `state.md` | Work branch already exists, automatic downstream gates are authorized, root owns review routing. This dispatch is plan only. |
| `evidence/diagnostic-controls.json`, `synthetic_probes` | Ordinary run: `OK`, native/runner 0, `turn.completed`. Unmodified isolated run: native/runner 1, `turn.failed`, zero tools, 25.536161 s. Isolated home without outer sandbox: `OK`, native/runner 0. Same strict outer envelope with only `CODEX_CA_CERTIFICATE=/etc/ssl/cert.pem`: `OK`, native/runner 0, 5.465033 s. These are observations supporting a fix, not an accepted implementation. |
| Same evidence, `config_comparison` | Failed and CA-success controls retain the same selected model/provider, authentication fingerprint, normalized deny list and strict network settings; both verified the read boundary. Model-card resolution remains the existing `gpt-6-sol` route even though selected model is `gpt-6.1-sol`. Do not change or add routing assertions to product output. |
| `scripts/agent-sandbox:280-285,343-377` | `require_readable` checks denial and file existence but does not actually read or parse a certificate. `prepare_codex` prepares the isolated config/rules/auth home and returns the selected URL; it does not prepare CA input. Add a CA-specific helper, not broader changes to `require_readable`. |
| `scripts/agent-sandbox:541-558,564-570,589-620` | `--check` and launch have separate `prepare_codex` call sites. Launch inherits a copied environment, changes to envelope cwd before exec and sets strict filesystem/network policy. Shared CA preparation must run in both paths after route validation and before sandbox/runner startup. |
| `scripts/agent-sandbox:412-475` | Internal verification queries effective Seatbelt permission, actually attempts denied reads, proves the allowed probe read/write, then execs the fixed command with `os.environ`. Leave it and its manifest unchanged. |
| `scripts/agent-sandbox-launch.mjs:95-113,156-183` | The adapter preserves srt's env prefix and inherits the outer environment into srt; it changes transport of the policy, not certificate selection. No adapter edit needed. |
| `scripts/sub-agent-preflight:264-275` | Existing preflight invokes `agent-sandbox --check`; sharing CA preparation automatically gives it the same setup failure. No preflight edit needed. |
| `scripts/codex-agent-run:371-380,475-505,536-552`; `scripts/agent-tools.zsh:4-14,138-145,420-448` | Runner loads the launchers and changes to workdir; the credential scrub patterns do not match either CA variable; the launcher selects isolated CODEX_HOME and executes native Codex with inherited CA variables. Native/runner failures remain nonzero and go through existing collection. No runner/launcher/collector edit needed. |
| `tests/test_agent_sandbox.py:56-216,528-657,661-756,939-1016,1019-1056` | Existing test utilities cover setup failures, verify-before-exec, kernel reads/writes, read-only, Claude write denials and actual runner/launcher argv. Extend these fixtures for CA behavior rather than create a new test framework. |
| `README.md:184-258`; `skills/sub-agents/references/advanced.md:35-83` | Existing user and Agent docs explain setup-only preflight, fixed boundary, fresh runtime state and required readable inputs. Both need a short explicit-CA paragraph. |

Official OpenAI documentation was searched and fetched on 2026-10-11: [Custom CA bundles](https://learn.chatgpt.com/docs/auth#custom-ca-bundles). It states that `CODEX_CA_CERTIFICATE` takes precedence, `SSL_CERT_FILE` is the fallback, and these settings apply to login, HTTPS and secure WebSocket clients. It does not specify empty-string behavior.

Empty-string behavior was checked statically, without running Codex or reading any user config/auth/key: installed package `/opt/homebrew/lib/node_modules/@openai/codex/package.json` reports `0.162.1`; its native executable is `node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex`, SHA-256 `74c6a6d263f40d65f99c27a815275f5b4ed0bcc2baecc396b4cf3255498bdfc0`. Address-bounded disassembly shows:

- HTTP builder calls the custom-CA path at `0x106d02b4c`; it reads `CODEX_CA_CERTIFICATE` first and branches past a successful zero-length value at `0x106d02bc8` to the `SSL_CERT_FILE` lookup at `0x106d02be4`. The latter skips zero length at `0x106d02c34`.
- `codex_http_client::custom_ca::maybe_build_rustls_client_config_with_custom_ca` at `0x106d0408c` has the same selection: zero-length CODEX value branches at `0x106d040ec` to SSL lookup at `0x106d0410c`, with SSL zero length skipped at `0x106d04154`.
- Neither selection path trims a successful nonempty string before sending it to CA loading. Embedded runtime guidance requires one or more PEM `CERTIFICATE` blocks.

Thus exactly empty values are ineffective; whitespace is a literal nonempty path. This evidence is version-specific, not a claim about every future Codex build.

Installed srt 0.0.79 package source was read only for the launch chain: `dist/cli.js:432-441` inherits env for the macOS child; `dist/sandbox/macos-sandbox-utils.js:739-744` grants `com.apple.trustd.agent` only under weaker network isolation; `:1057,1113-1125` composes the env prefix. `dist/sandbox/sandbox-utils.js:655-662` overwrites CA trust env only when TLS termination supplies a CA path. This wrapper supplies no TLS-termination configuration. This establishes the environment path, not the exact macOS operation denied in the reported failure.

No original caller index, business input, raw caller log, private diagnosis report, peer report or recovered-stream checkout was read. The sanitized evidence's paths are references only and must not be followed for this plan/review.

## First-principles decision and goal alignment

TLS needs a readable trust input. A matched control already demonstrates success when that input is explicit, without changing the envelope. Prepare that input at the wrapper's existing setup boundary; do not change the runtime route or grant system IPC.

| Decision / validation | Binding goal or necessary condition |
| --- | --- |
| One shared CA helper for isolated Codex HTTPS; system PEM only if neither variable is effective | Restore the affected HTTPS startup; avoid relying on unavailable default trust discovery. |
| Exact precedence, literal path semantics, canonical child path, selected-input validation only | Honor custom inputs and ensure the checked path is the one native Codex consumes. |
| Deny check before opening; readable regular file; minimum PEM/X.509 parse | Specific missing/denied/invalid failure without reading forbidden input or blocking on a FIFO. |
| No policy, route, auth, collector or manifest edits | Preserve all confirmed boundaries and real failure records. |
| Setup/launch tests, one native-environment kernel test, existing small kernel boundary checks, one fresh managed-auth synthetic call | Establish prepared env, actual boundary preservation and restored affected startup. |
| Two short doc updates | Make default/custom-root behavior and setup limits actionable to caller and Agent. |

There is one behavior slice. Tests and docs support that same behavior; they do not warrant separate implementation gates. No CA snapshot subsystem, trust-store abstraction, keychain export, input size policy, additional platform support, certificate expiry/chain audit or generalized setup hardening is introduced. Risks beyond this goal remain owned follow-ups below.

## Affected files and interfaces

Exactly four product/test/documentation files may change in the implementation slice:

1. `scripts/agent-sandbox`: stdlib imports `re` and `ssl`; a default CA path constant and one CA preparation helper; calls in `--check` and normal Codex setup; move the private env copy to serve both paths.
2. `tests/test_agent_sandbox.py`: CA helper/setup/environment regressions, one kernel env-consumption test, and deterministic CA env initialization where existing fixtures now encounter the new setup requirement.
3. `README.md`: optional macOS envelope section only, adjacent to required startup inputs.
4. `skills/sub-agents/references/advanced.md`: task read-boundary section only, matching README behavior/limits.

No CLI option, provider identifier, persistent config/schema, result schema, routing-proof field or prompt protocol is added. `--check` retains `setup_status=ok` only on successful setup. The only child-env change is the effective selected CA path (normalized to an absolute canonical path), or automatic CODEX CA default for HTTPS when both are ineffective. The parent environment is unchanged. Setup rejection continues to exit 1 through the existing error handler.

`prepare_codex`, the launcher, preflight, result collector, srt adapter, manifest, installer/sync and boundary algorithms remain otherwise unchanged. Normal unwrapped runner launches are untouched. HTTP-only Codex routes and Claude are outside CA preparation: no new default-file requirement or CA env mutation for them. This is a scheme-based condition on the already selected URL, not a provider-name routing redesign. Codex HTTPS profiles use the same native trust channel and therefore the same helper, including an HTTPS override of an existing profile.

## Implementation decisions: CA selection and consumption

Add `DEFAULT_CODEX_CA_CERTIFICATE = "/etc/ssl/cert.pem"` and `prepare_codex_ca(route, cwd, env, denies)`. `env` is a private copied mapping, `cwd` is the already canonical envelope cwd, and `denies` is the complete output of existing deny expansion. The helper returns nothing and mutates at most one env key **after** validation succeeds.

1. If validated `urlsplit(route).scheme` is not `https`, return without inspecting CA paths or changing env. Caller invokes this helper only for Codex.
2. Select effective input exactly as the installed native clients do:

| CODEX value | SSL value | Selected input / child-env effect |
| --- | --- | --- |
| Nonempty, including whitespace | Any | CODEX value; normalize only `CODEX_CA_CERTIFICATE`. Do not inspect or alter the lower-priority SSL input. |
| Unset or exactly `""` | Nonempty, including whitespace | SSL value; normalize only `SSL_CERT_FILE`. Leave an inherited empty CODEX value empty (native clients skip it). |
| Unset or exactly `""` | Unset or exactly `""` | System default `/etc/ssl/cert.pem`; set `CODEX_CA_CERTIFICATE` to its canonical path after validation. Leave SSL unchanged. |

Use explicit iteration over those two names with `value != ""` (or equivalent nonempty string logic). Do not treat a nonempty but failing CODEX value as permission to fall through to SSL/default. Do not validate an ineffective or lower-priority path. Do not strip whitespace, expand `~`, expand environment references or perform shell evaluation. An exported literal `~/ca.pem` names the literal `~` directory under runtime cwd; shell expansion, if desired, happens before export.

3. Construct `Path(raw)` and, if relative, prefix envelope `cwd`, because both wrapper and runner execute from that cwd. Resolve with `strict=True`, preserving stdlib symlink/`..` traversal semantics. Do not use the general `absolute()` helper here: it expands `~`, which native CA file loading does not do. Do not use ALLOW_MISSING/non-strict fallback for a required CA file.
4. Check the canonical file against every canonical deny and denied ancestor, using existing `is_denied` on the canonical absolute path. Existing `load_denies` already expands symlinks discovered inside denied directories, including conservative missing-target ancestors. Apply the complete expanded deny list; do not prune it or add an allow. A permitted alias resolving to a denied file/directory fails; a CA target reached from within a denied scanned tree also fails under that expansion. No CA bytes are opened/read before this check.
5. Validate/read as below, then assign the canonical absolute string to the selected key. Normalization changes spelling only, preserving selected input and bytes at setup. Unselected variables retain their exact values. No CA copy, extra allowRead, allowWrite, deny rule or child-state field is required.

The environment must reach native Codex, not merely a retained setup artifact:

`main env -> execvpe(node, ..., env) -> adapter -> srt/macOS env prefix -> sandbox-exec -> --verify -> execvpe(fixed runner, ..., os.environ) -> codex-agent-run -> _codex_agent_launch -> native codex`.

Existing credential scrubbing preserves both names. The pinned srt configuration has no TLS termination and therefore does not supply a replacement CA. Test this consumption through the actual wrapper/srt/runner/launcher chain with a synthetic native executable; do not modify those components or infer success merely from env stored in a file.

## Minimum validation and precise failures

Keep validation CA-specific. Do not broaden `require_readable` or general filesystem policy.

- After canonical deny check, `lstat` the canonical leaf and require `stat.S_ISREG`. A directory, FIFO, socket or device, directly selected or reached through a symlink, fails before an open. A broken link/missing target fails strict resolution.
- Read the regular file with `os.open` using macOS-supported `O_RDONLY | O_NONBLOCK | O_NOFOLLOW | O_CLOEXEC`, then `os.fstat` to require regular-file type before reading. Close the descriptor on every failure; use `os.fdopen`/context-manager ownership on success. Static special files are never opened. `O_NONBLOCK` and the post-open type check avoid blocking reads if the checked leaf is replaced with a FIFO during setup; `O_NOFOLLOW` rejects a late leaf-symlink replacement. Do not attempt an atomic whole-filesystem redesign. No `os.access`-only proof and no second path-based open by a validator.
- Read the bytes once. Extract complete `-----BEGIN CERTIFICATE-----` through `-----END CERTIFICATE-----` blocks with a local bytes regex and DOTALL; require at least one block and equal begin/end delimiter counts to complete-block count. This rejects empty content, no certificates and incomplete delimiters. Ignore noncertificate surrounding text, so comments outside the PEM blocks need not be ASCII.
- Decode each extracted block as ASCII and parse it with a fresh `ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT).load_verify_locations(cadata=block_text)`. Validate every certificate block, so a valid block cannot hide a malformed companion. This uses stdlib OpenSSL parsing with no system/default-root loading, network request, trustd operation or third-party dependency. It catches malformed encoding and non-X.509 bytes. Do not call `create_default_context`, require a valid current date/chain, require a particular CA subject, or build a replacement TLS transport.
- The parser checks usable certificate syntax, not whether the bundle trusts the selected server or exactly matches all native TLS implementations. Parse-valid but unsuitable roots, unsupported native certificate algorithms, handshake/auth/network failures remain native failures, with existing runner logs and exit codes. No silent fallback or invented success.

Wrap `OSError`, `RuntimeError` from strict resolution, `ValueError`, Unicode parsing errors and `ssl.SSLError` locally into `ValueError` with a CA-specific stable prefix. Do not print certificate bytes, config/auth data, keys or a bundle body. Use the following diagnostic contract (repr-quoted path fields, native cause class/errno where available; OpenSSL's detailed wording is not a portable assertion). For parser failures, render a fixed reason or exception class plus at most 256 characters of SSL reason text; Unicode errors use the exception class only, never a repr of input bytes:

| Failure | Required final stderr prefix/detail and behavior |
| --- | --- |
| Strict resolution ENOENT | `agent-sandbox: required Codex CA input missing:`; `source`, `declared` and cause/errno=2; canonical path if available. Exit 1, no fallback/runner. |
| Denied canonical file or ancestor | `agent-sandbox: required Codex CA input is denied:`; `source`, `declared`, `canonical`. Deny failure precedes open/parse; exit 1. |
| Directory/FIFO/socket/device or fstat special type | `agent-sandbox: required Codex CA input is not a regular file:` with selected source/path context; exit 1, no data read. |
| EACCES/EPERM/open/read/other resolution failure, symlink cycle or late symlink | `agent-sandbox: cannot read required Codex CA input:` with selected source/path context and cause class/errno (ELOOP where reported). Exit 1; do not mislabel it as absence. |
| Empty/no blocks/unbalanced delimiters/invalid certificate encoding or ASN.1 | `agent-sandbox: invalid Codex CA bundle:` with source/path context and a bounded reason, e.g. `no CERTIFICATE blocks`, `incomplete CERTIFICATE block`, or parse exception class/reason. Exit 1. |

`source` identifies `CODEX_CA_CERTIFICATE`, `SSL_CERT_FILE`, or `system-default`; `declared` is the literal selected path. These are located error text, not new result/proof fields. If canonicalization has not succeeded, omit canonical rather than claim a path was checked. NUL/unrepresentable path input fails with the same selected-source context, with no env mutation or launch. No certificate failure grants an extra domain, removes a deny or invokes an unwrapped runner.

## Call sites, state transitions and invariants

Copy `env = dict(os.environ)` once immediately before the existing `if args.check` branch (currently line 541); reuse it for launch rather than copying again at line 554.

- `--check`: existing temporary `prepare_codex` -> existing `host_port(route)` -> `prepare_codex_ca(route, cwd, env, denies)` -> successful temporary cleanup -> exact stdout `setup_status=ok\n`. It does not spawn a sandbox/Agent or claim kernel enforcement. Claude check stays unchanged. Failed CA validation does not print successful status.
- Normal launch: existing private state/home preparation -> existing `host_port(route)` -> Codex CA helper -> existing loopback/model-domain handling -> unchanged settings/manifest/task protection -> kernel verification -> unchanged fixed runner. Put CA preparation before the existing loopback connection check and final exec. Failed setup never reaches kernel verification or runner. A private preparation directory may already exist, as with other current setup failures; do not introduce a cleanup subsystem or claim zero allocated state.
- Both calls use the same helper and input environment, cwd and complete denies. The temporary check directory does not become a basis for relative CA resolution. A successful check remains a setup observation at that time; launch revalidates input rather than trusting a prior check.

Mandatory invariants:

- Provider/model card/auth preparation and domain calculation remain byte-for-byte unchanged by the CA helper.
- `enableWeakerNetworkIsolation`, `enableWeakerNestedSandbox`, `allowAppleEvents`, local binding and all Unix-socket settings remain false/empty exactly as baseline.
- `denyRead`, `denyWrite`, `allowRead`, write roots and selected output-file grants remain the existing policy. No CA allowlist exception, copying around a deny, permission chmod, trustd grant or TLS-check disabling.
- Existing `--verify`, kernel query/actual denial/allowed probe order, fixed runner command, private task, protected config/rules and stdin handling remain unchanged.
- Setup/verification rejection and native failures remain real nonzero failures; no collection/classification change. Logs from diagnostics are not overwritten or reinterpreted.

## Slice S1: prepare explicit Codex HTTPS trust input

- Owner: root-routed implementation agent; root alone adjudicates and routes review/fix. No peer ownership is inferred.
- Objective/outcome: isolated Codex HTTPS uses the selected readable CA input with exact precedence, or stops with a located setup failure; the affected managed-auth synthetic call succeeds under the same strict envelope.
- Allowed files: the four files listed above, plus root-owned required gate artifacts under this work unit when separately dispatched. This plan-author dispatch owns only `plan.md`.
- Prerequisites: root's two independent planreview artifacts, adjudication/fixes/re-review and accepted-plan checkpoint; branch/baseline/ownership reconfirmed; macOS, current Python 3.11+ stdlib SSL, installed pinned srt/Node available for later kernel validation; existing managed-auth session for the later synthetic startup validation. No install/login/migration is part of S1.
- Exact changes: implement the constant/helper and two calls with the described env/path/error flow; add only the tests below and short docs. Do not refactor route/home creation, broaden `require_readable`, add new output schemas or modify any launch/collector adapter.
- Dependencies: none beyond that accepted plan and existing installed validation prerequisites. No later approved implementation slice exists.
- Stop conditions: blocker in scope/ownership; native version semantics contradict the plan; stdlib SSL required for minimal parse is unavailable; selected required CA cannot be provided without relaxing policy; required kernel/live evidence cannot be obtained by the authorized root; focused tests fail for a reason needing changed boundaries or contract. Retain actual failure and route the decision to root. Service outage/auth expiry is not evidence this fix works; do not migrate credentials or weaken TLS to obtain a pass.
- Completion signal: S1 tests/necessary existing checks below pass, source diff contains only intended changes, one live synthetic affected call has genuine success under verified strict policy, docs match actual behavior, and residual risks/findings are adjudicated with owner/destination. Root then executes code review -> fix/re-review -> accepted slice commit and the remaining gateflow chain. Ordinary slice completion is not final closeout.

## Validation: necessary scope, commands and actual expected outputs

These validations are for implementation after plan acceptance. **None were run in this plan-only dispatch.** Use fresh private synthetic directories and clean new log paths. Do not use the original caller index, frozen branch, business files, diagnostic raw logs or peer reports as fixtures. Do not export auth/key contents into evidence.

### Unit and setup regression in `tests/test_agent_sandbox.py`

Add `CodexCATests` (or equivalently scoped methods) with a fixed small public valid CA PEM constant in this file, no private key. A public certificate block from the system PEM may be embedded once as a test fixture; tests must not depend on reading user trust/keychain/config. Write all case files under `TemporaryDirectory`, with a mocked default-path constant and an explicit test env mapping. Test values must not inherit the user's CA overrides.

Required cases, combining parameterized subtests where useful:

1. CODEX wins over SSL even if the ignored SSL file is missing/denied/invalid; only CODEX is opened and its canonical path replaces that key. Neither lower input nor parent mapping is modified. Invalid/missing/denied CODEX must fail without falling through to valid SSL/default.
2. CODEX unset and CODEX exactly empty both select nonempty SSL and retain its priority semantics. SSL unset/empty with ineffective CODEX selects the mocked valid system default. Both empty values are not interpreted as `.`. Default missing/denied/invalid fails with `system-default` context. Selected whitespace is a literal filename: absent whitespace name fails; an existing regular valid file with that name is usable. No `.strip()` selection.
3. Relative path resolves against envelope cwd when invocation cwd/check temp dir differs. Valid symlink resolves to the same canonical child input. An exported literal `~/ca.pem` is treated as a literal cwd path, not expanded HOME. Direct/alias/ancestor-denied targets and a target included by existing deny expansion fail before open. Broken/cyclic links fail with source and cause; no missing-aware CA fallback.
4. Directory and FIFO, plus a symlink to a FIFO, fail before any open (guard/mock the open boundary). Open/read EACCES/EPERM is distinguishable from missing. Mock post-open fstat special type to prove no read and descriptor cleanup. NUL input produces a located error rather than an unhandled traceback.
5. Empty/non-PEM/unbalanced blocks/malformed base64/invalid DER and mixed valid+invalid certificates fail with `invalid Codex CA bundle`; a valid one-/multi-certificate PEM and non-ASCII surrounding comment pass. Stdlib parser is exercised on real synthetic certificate bytes, not entirely mocked. No logs contain certificate bodies.
6. Exercise `main()` for check and launch with synthetic config/runner fixtures and dependency calls mocked only where needed to avoid actual sandbox/network/model execution. Assert same selected-input error prefix/path and no final envelope exec for each representative missing/denied/invalid case; no `setup_status=ok`. On valid check stdout is exactly `setup_status=ok\n`; on valid launch capture final `execvpe` env and assert selected canonical CA reaches that call. Compare resulting settings/command route to the existing fixture expectation: network flags/domain list/denies/write grants remain unchanged. Preserve existing verify-before-run tests.
7. Claude and Codex HTTP preparation paths do not call/open the CA helper input or change either CA env value. A nonexistent default does not create a new HTTP/Claude setup failure.

Run from repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_agent_sandbox.py
```

Expected: exit 0, `OK` with the existing explicit kernel skips when opt-in is absent, and no unexpected skips of the new unit cases. Existing dangling-symlink tests still enforce their current Python capability rules; do not install a different Python or add fallback for this fix. Any existing capability-specific failure must be separated with its evidence and adjudicated by root, not silently called pass.

No whole-repository suite, large-policy compiler test or native-model test matrix is newly required: CA preparation does not change those algorithms. Broaden only if an actual change/failure gives a reason.

### Kernel and effective native env

Extend `KernelTests` with `test_codex_ca_reaches_native_cli`. Keep its existing synthetic HOME/config/endpoints and denied-file fixture. Use a test-bin symlink to the repository `codex-agent-run`, `AGENT_TOOLS_FILE` pointing to repository launchers, and a synthetic `codex` executable. The synthetic native program reads only the effective selected CA path, checks expected bytes from its public fixture, and prints the selected env path; use `--detail` so no fake model terminal is sent to the collector. This is a test stub for native environment consumption, not proof of managed-auth TLS success. Test two subcases with fresh sinks: automatic default with both overrides absent (system public PEM), and CODEX empty plus valid SSL fixture/alias. Unit coverage already establishes CODEX priority.

Assert each completes exit 0, prints the expected canonical CA path at native startup, follows `read boundary verified; starting runner`, and preserves the first trusted-parent adapter profile/source hashes. Use existing `profile_fields` and `retain_kernel_evidence`, not a new proof format. Retained `srt.json` must preserve current domain/strictAllowlist/socket/weaker-isolation flags; effective policy must not add the trustd.agent grant. Clear the two CA override names in fixture env before assigning explicit synthetic values so user custom inputs do not affect this test or the other synthetic kernel fixtures.

Run outside the controller sandbox through root's authorized structured `exec_command(require_escalated)`, using the already installed srt. The commands below assume its observed entrypoint remains `/Users/leo/.local/bin/srt`; verify availability without installation before use. `AGENT_SANDBOX_EVIDENCE_DIR` must name a fresh private synthetic directory created by root, never an existing diagnostic/caller directory.

```bash
PYTHONPATH=tests PYTHONDONTWRITEBYTECODE=1 AGENT_SANDBOX_KERNEL_TESTS=1 SRT_TEST_BIN=/Users/leo/.local/bin/srt python3 -m unittest \
  test_agent_sandbox.KernelTests.test_codex_ca_reaches_native_cli \
  test_agent_sandbox.KernelTests.test_kernel_boundary_and_write_preservation \
  test_agent_sandbox.KernelTests.test_read_only_does_not_gain_cwd_writes \
  test_agent_sandbox.KernelTests.test_claude_original_deny_write_wins_over_cwd
```

Expected: exit 0 and `OK`, no skipped selected tests. Existing boundary test outputs are actual `PermissionError` for direct/symlink/directory aliases/history and protected/outside/unrequested writes as asserted; nested read attempt exits nonzero without forbidden content. Allowed input/cwd/selected output and heredoc still work. Read-only test permits no cwd write; Claude's original denyWrite still wins. Compare retained policies using their first pre-spawn adapter hashes before citing them; state paths/ephemeral proxy ports vary. Do not assert byte-identical whole-policy hashes across runs or replay a large business deny list.

### One fresh managed-auth synthetic startup validation

Root runs one independent minimal synthetic invocation after unit/kernel success, from outside its sandbox. No extra runtime controls need repeating: the sanitized matched controls already establish motivation. Prepare a private temporary root containing `work`, `denied/report`, a readable `work/alias` symlink to that denied report, a nonempty absolute JSON deny list and separate new log sinks. Use the repository wrapper/runner/launchers via a task-local PATH, and clear only the two CA override names to exercise the automatic default. The unchanged wrapper consumes existing selected managed-auth state internally; the verifier does not read/publish its contents or inspect caller business inputs.

Exact invocation template (substitute fresh absolute synthetic fixture paths; no live installation):

```bash
env -u CODEX_CA_CERTIFICATE -u SSL_CERT_FILE \
  AGENT_TOOLS_FILE=/private/tmp/code-is-cheap-workspace-routing/scripts/agent-tools.zsh \
  PATH=/private/tmp/code-is-cheap-workspace-routing/scripts:"$PATH" \
  /private/tmp/code-is-cheap-workspace-routing/scripts/agent-sandbox \
  --cwd /private/tmp/FRESH_CA_VALIDATION/work \
  --deny-list /private/tmp/FRESH_CA_VALIDATION/denies.json -- \
  codex-agent-run --provider gpt-6-sol --prompt 'Reply exactly OK without calling tools.' \
  --output /private/tmp/FRESH_CA_VALIDATION/logs/events.jsonl \
  --stderr /private/tmp/FRESH_CA_VALIDATION/logs/runtime.stderr
```

Use a finite parent timeout (e.g. 120 s), collect wrapper stderr through its trusted parent pipe and save returned runner summary/new logs privately. The wrapper's real temporary state can also be retained privately. Do not overwrite diagnostic failures. Do not require new artifacts, canary/proof prompt sections or product output keys.

Actual pass assertions:

- Process, existing summary `runtime_exit_code` and `runner_exit_code` are 0; `agent_status` is `completed`; `terminal` is `turn.completed`; `final_answer` is `OK`; `tool_results` is 0 for this no-tool prompt.
- Existing collector must output `result_status=not_assessed` and a non-rejected `validation_status` (`passed` when it records no errors/anomalies, `needs_review` when anomalies remain, as implemented in `agent-run-result.py:397-406`). The sanitized CA-success control observed `needs_review`; the ordinary control observed `passed`. Do not require one fixed value merely because no canary/artifact was selected. Root must examine and adjudicate any actual anomalies before acceptance; neither value proves business-task correctness. Do not manufacture a proof field.
- Wrapper stderr contains the first adapter profile record before `read boundary verified; starting runner`. Verify retained policy hashes against this first record, not a later duplicate.
- Generated settings retain the same selected HTTPS route/auth domains, strict allowlist, empty Unix sockets, disabled weaker/network/nested isolation and Apple Events, exact synthetic denies and unchanged write-root/output-file rules. Loaded policy has no added `com.apple.trustd.agent` grant. Do not inspect/publish generated auth or user config.
- Independent kernel tests, not the model's text answer, establish direct/symlink read and write denial. Successful minimal startup does not claim restoration of the original business task or measurement of the exact blocked macOS service.

If final answer/terminal/exit evidence is missing, retain actual failure, classify the reason and stop at the applicable gate. No retry with weaker isolation, altered auth/model, removed denies or disabled TLS. A live custom private-root deployment is not a prerequisite for this slice; custom-path/parse/precedence/native-env behavior is covered locally and its trust limits are documented.

## Documentation decision

Update both existing envelope sections in S1. State:

- Isolated Codex HTTPS automatically selects `/etc/ssl/cert.pem` when neither CA env variable is effective; the exported child path may be canonicalized (e.g. macOS `/etc` alias).
- Nonempty CODEX takes priority over nonempty SSL; exactly empty values fall through in verified Codex 0.162.1; whitespace is literal. Only selected input is validated; explicit bad CODEX is not ignored in favor of SSL/default.
- Inputs must resolve to permitted readable regular PEM certificate files; `--check` and launch use the same preparation and located failures, but setup does not prove kernel enforcement or endpoint trust. No automatic permission/network expansion.
- The system PEM is a public root bundle and may omit enterprise/custom roots installed only in the macOS keychain. Caller must provide a permitted explicit PEM containing the needed roots. This fix does not export keychain roots, grant trustd or disable TLS verification. Syntax validation does not establish trust of a particular endpoint.
- Original task restoration/large deny-list validation belongs to its caller after deployment; no merge/live sync is performed here.

Use one short example exporting an absolute `CODEX_CA_CERTIFICATE` path before the existing envelope command. Do not describe the exact denied service as proved or change README's unrelated runtime/version claims.

## Residual risks, uncovered areas and ownership

No unclassified residual risk is left. These classifications do not waive a required S1 validation or an accepted finding.

| Risk / uncovered area | Classification | Owner and destination | Why it does not expand/block the confirmed slice |
| --- | --- | --- | --- |
| Missing/denied/unreadable/special/invalid selected CA or env mismatch | fixed in current slice (planned; must be verified before closure) | S1 implementer; root-owned S1 implementation/code-review artifact | These are the directly required setup correctness/safety cases and the focused tests above. |
| Exact denied macOS trust-service operation is unmeasured | assigned to later work unit | Root controller; carry in final closeout residual-risk table, optional separately scoped system-trust diagnosis | Matched controls support explicit input preparation without requiring a service grant or proving trustd causality. |
| System PEM omits roots present only in keychain; custom root may not trust endpoint | assigned to later work unit | Affected deployment/caller owner; explicit-bundle configuration and post-deployment verification, referenced in README/advanced docs and closeout | Confirmed goal explicitly accepts this limit; no automated export, trust-store merge or live custom-root test is added. |
| OpenSSL syntax acceptance and native TLS parser/algorithm acceptance can differ; future Codex env semantics can change | assigned to later work unit | Runtime-upgrade owner/root; existing documented runtime-upgrade boundary-validation process and closeout | The plan states the minimum parser guarantee and verified 0.162.1 semantics; live affected-path success is still mandatory now. Native rejection remains a real failure. |
| CA contents/path may be changed by another unsandboxed process after setup; aliases may be writable within already allowed cwd | assigned to later work unit | Caller controlling input stability; existing README no-external-replacement contract plus closeout | Runtime reopens the canonical original under the unchanged deny policy. No snapshot/immutability subsystem or extra write boundary is authorized. Any observed boundary bypass in S1 must still block and be adjudicated. |
| Original caller command/isolation details and large business deny graph were not reproduced | assigned to later work unit | Original caller/controller; post-deployment task restoration/verification, final closeout next-entry entry | User explicitly excludes business rerun and original material from this dispatch. Synthetic startup and existing kernel tests are the confirmed local success signals. |
| Validation prerequisites unavailable, managed session expired, service outage or live terminal failure | requiring new issue or explicit user decision if encountered | Root controller; current failing gate artifact with actual error and next decision | Not a passed validation or permission to migrate auth/install/change policy. Stop dependent closure until root obtains permitted evidence or an explicit scope decision. |

There is no later approved slice, existing issue number or external issue creation authorization asserted by this plan. Root must carry deferred risks into downstream artifacts with their owners/destinations; accepted findings still require fixing and re-review or a formally authorized nonblocking deferral.

## Completion and handoff format

Plan-author completion: artifact path, `plan drafted; awaiting independent plan review`, blocking questions (`none` unless a new blocker emerged). This dispatch does not advance `state.md`, commit or run review itself. Next root entry is **plan review**, using the two independent prescribed routes; root adjudicates before the accepted-plan checkpoint and implementation.

S1 implementation completion artifact must record: gate/work unit/S1, branch and baseline/implemented target, the four changed files, actual selection/error behavior, commands with real exit/skip/assertion results, synthetic evidence paths and first-record policy-hash verification, docs decision, findings with evidence-based disposition/status, classified residual risks/owners/destinations, completion/stop status and next uncompleted gate. Do not label planned tests as executed, collector `needs_review` as reviewed/accepted without adjudicating its actual anomalies, or a minimal synthetic call as business restoration.

Root's final closeout retains the gateflow-required changed/verified/docs/findings/risks/new draft PR URL/issue-link applicability/next-entry summary. It must follow PR review and final push, and explicitly retain user manual merge and no live-sync boundaries. This plan is not a substitute for those downstream artifacts.
