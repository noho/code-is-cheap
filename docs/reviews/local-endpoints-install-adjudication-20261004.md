# Local endpoint / installer review adjudication

## Scope and authorization

- Work branch: `feat/local-endpoints-installer`; base/HEAD at first and second dispatch: `842eca3642e5d51c6d849870ea42d1deb9569aa3`.
- User requested a new PR for user-owned upstream URLs, a downloadable installer, and bilingual README changes. Later instructions require Qwen as the second reviewer and defaults when local URLs are absent.
- First-round manifest/diff: SHA-256 `bb5a8cfb693ef5d452cde923d48c2e69a7534e07728fa7336d115b9271646f1c` / `e06d59ebe44d0644636033eb61bf3debf819dfe8c54bd802fca64c711b9f620d`, 16 files. Both routes verified the same input. Controller retained the original source snapshot before applying fixes.
- User live configuration, credentials and services were not changed. Installer lifecycle tests use isolated homes and dependency mocks. There was no real network installation or gateway model probe.
- The optional upstream URL file belongs to the user. Default resources are program-owned; sync may update those resources but never writes the user URL/key files.

## First-round dispatch acceptance

### MiMo, `endpoints-install-mimo-20261004-01`

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: complete
required_evidence: complete
canary_status: match
result_status: accepted
warnings:
  - "item_61: privacy assertion failed under a temp path containing private; reproduced defect in the test, retained as finding, and tests passed under another temp path."
  - "item_71: zsh readonly variable status interrupted input comparison; subsequent comparison recovered the exact original diff and hashes. Controller independently checked all original source hashes."
  - "stderr: malformed apply_patch hunk while writing the report; report creation recovered, completed artifact and its content independently checked."
evidence_gaps: []
retry_class: none
```

- Managed process handle `33159`: outer exit 0; valid JSONL with `turn.completed`; exact report token matches the private expected file.
- Evidence directory: `/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.FiqDYC` (stdout, stderr, final message and expected token retained).
- Accepted artifact: `local-endpoints-install-mimo-20261004.md`.

### Qwen, `endpoints-install-qwen-20261004-01`

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: complete
required_evidence: complete
canary_status: match
result_status: accepted
warnings:
  - "stderr: three OpenAI documentation MCP transport initialization errors. Review used local source/tests; that optional MCP was not a required input. No required evidence remained missing."
evidence_gaps: []
retry_class: none
```

- Managed process handle `39531`: outer exit 0; valid JSONL with `turn.completed`; exact report token matches the private expected file. No nonzero completed command event was observed.
- Evidence directory: `/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.PirX7x`.
- Accepted artifact: `local-endpoints-install-qwen-20261004.md`. Its generic startup identity speculation does not establish a wire-model identity; the dispatch used the configured Qwen launcher/profile. No identity probe was required for this source review.

## Findings adjudication and fixes

| Source | Decision | Controller evidence / fix |
| --- | --- | --- |
| MiMo 1 / Qwen 9, hardcoded helper location | accepted | Launcher resolves the helper through PATH; custom-bin URL test verifies the actual installed layout. |
| MiMo 2, privacy test false positive | accepted | Replace generic `private` assertion with a unique secret sentinel. Full suite passes with `TMPDIR=/private/tmp`. |
| MiMo 3 / Qwen 8, stale local/URL prerequisites | accepted | README now distinguishes configurable local health/direct URLs, Python/helper dependency, URL resources and source ownership. |
| Qwen 1, zsh declaration masks URL failure | accepted, blocking | Declare and assign separately in launch/health/helper paths. Negative stub tests prove Claude is never invoked with a missing helper or malformed local JSON; valid defaults still launch. Credentials are prepared/scrubbed before the helper child runs. Actual fallback behavior of a real Claude CLI with an empty URL was not probed or asserted. |
| Qwen 2, missing runtime diagnostics and stale startup destination | accepted | Log sanitized endpoint errors before HTTP 503; managed startup/route output identifies the endpoint ID rather than a cached upstream URL. Do not infer an actual secret disclosure from an ordinary hostname alone. |
| Qwen 3, uncaught startup helper/config exceptions | accepted | Missing helper raises a clear configuration error; startup converts config errors to a one-line nonzero exit. Parser exception chains are suppressed; runtime errors receive a logged 503. |
| Qwen 4, duplicated request-prefix contract | accepted | Add path equality to the existing registry/route pairing test. Current routes were already consistent; no current mismatch was claimed. |
| Qwen 5, deprecated module import | accepted with factual qualification | Use `exec_module` with an explicit loader. Reviewer did not establish removal in Python 3.12; the confirmed evidence was deprecation and inconsistency with the other tests. |
| Qwen 6, local URL override coverage and fragile regex | accepted | Replace the broad section regex with line/section matching; test a comment containing `[docs]`, effective override, idempotence and preservation on missing-setting failure. |
| Qwen 7, restore/sync requiring a new local file | accepted | User's later default requirement removes the precondition: missing local files/fields use deployed defaults. Direct sync is tested with the URL file removed and does not recreate it. Restore docs mention helper/default deployment. |
| Qwen 8, repository/source index omissions | accepted | Add installer/default/helper/validator to source maps and the new lifecycle test to the repository tree. These lists are guides, not a prohibition on editing other repository tests. |

Additional controller fixes: reuse the installer-owned PyYAML environment for subsequent manual skill syncs; make downloaded-script detection distinct from local `install.sh`; preserve the existing Kimi Claude trailing slash; initialize local files exclusively and leave their bytes unchanged on reinstall.

## Controller verification

- First-round source identity verified before mutation; all 16 hashes matched. Fixes were initially made and tested in an isolated temporary copy while Qwen retained the original frozen checkout.
- Updated candidate: 54 tests passed with `TMPDIR=/private/tmp`, covering default fallback without writes, cloud URL hot reload/custom paths, custom-bin resolution, blocked Claude launches, sanitized shim diagnostics, private validator reuse, direct local override, downloaded bootstrap/reinstall and unchanged key/URL/shell/Codex local settings.
- Bash/zsh syntax, six skill metadata validations, and `git diff --check` passed after application to the work branch.
- Existing catalog tests intentionally emit warnings for invalid donor/metadata fixtures. Codex may also warn about helper aliases under temporary homes; catalog extraction still completed.
- Real network dependency installation, actual launchd deployment, and OpenRouter/OpenCode protocol/model compatibility remain outside this test evidence. A URL change does not translate protocols or model IDs.

## Second-round closure

Both managed processes exited 0. Controller parsed every JSONL line, confirmed terminal `turn.completed`, checked each report's exact canary against its private expected file, and inspected nonzero command events and stderr. Both stderr files were empty. Both routes independently checked the same 17 frozen source hashes and ran the 17 selected tests. Original r2 sources were preserved before final controller changes.

### MiMo r2, `endpoints-install-mimo-20261004-02`

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: complete
required_evidence: complete
canary_status: match
result_status: accepted
warnings:
  - "item_46 and item_47 deliberately supplied malformed route configurations. Nonzero exits were counterexample evidence, including the raw TypeError retained as a finding."
evidence_gaps: []
retry_class: none
```

- Managed process handle `12736`; 133 JSONL events; evidence directory `/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.PcoZDI`.
- Artifact: `local-endpoints-install-mimo-r2-20261004.md`.

### Qwen r2, `endpoints-install-qwen-20261004-02`

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: complete
required_evidence: complete
canary_status: match
result_status: accepted
warnings:
  - "item_67 and item_95 were interrupted by zsh expansion of an unquoted separator. Required files and call chains were read in subsequent commands; no required input remained absent."
  - "item_124 intentionally removed jq from PATH and set -e stopped the command at the expected failure. item_126 recovered exit status, stderr and the absence of Claude invocation."
evidence_gaps: []
retry_class: none
```

- Managed process handle `49843`; 236 JSONL events; evidence directory `/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.ZyzEQq`.
- Artifact: `local-endpoints-install-qwen-r2-20261004.md`.
- Static inspection of the installed Claude executable supplied SDK URL-building evidence; no live gateway request was made. The dispatch's launcher/profile identity is not an independent wire-model probe.

### Final adjudication

| Source | Decision | Final controller fix / verification |
| --- | --- | --- |
| MiMo r2 #1, route types bypass normalized startup errors | accepted | Validate root/routes/row types before accessing fields; normalize configuration TypeError. Negative cases include array root, scalar routes and scalar/null rows, asserting one-line nonzero exits without traceback. The malformed row behavior predated this PR, but fixing it is necessary for the diagnostic contract introduced here. |
| MiMo r2 #2, helper inherits selected key | accepted | Save the selected key in a shell-local value and remove its exported alias before spawning the URL helper. Stub helper sees no key/token; stub Claude receives only canonical `ANTHROPIC_AUTH_TOKEN`. |
| MiMo r2 #3, dependency/source guide gaps | accepted | List curl/zsh in installation prerequisites/help and the lifecycle test in the maintenance source guide. |
| Qwen r2 #1, empty factory default can launch Claude | accepted with contract clarification | Project defaults must contain nonempty valid URLs; user-owned empty fields still mean inheritance. Reject empty factory URLs and blank effective values, plus a final launcher nonempty guard. Regression proves Claude is not invoked. The proposed omission of malformed factory entries is not adopted: corrupted program resources should fail explicitly. |
| Qwen r2 #2, isolated PATH relies on system jq | accepted | Add deterministic jq stubs in both launcher fixtures with restricted PATH. The test still cannot accidentally use the live installed URL helper. |
| Qwen r2 #3, initial local defaults pin values | accepted as documentation gap | Preserve full initial editable local config and never overwrite user values, as requested. Both READMEs explain deleting one field or setting it to an empty string to inherit an updated default while keeping other overrides. |

Additional controller finding: local health checks used the Claude URL for both runtimes. They now select the appropriate runtime URL; a regression verifies distinct Claude/Codex ports and terminal Codex `/v1` removal.

Final patches were limited to these adjudicated findings and the demonstrated health-check bug. Controller checked the final diff and regression evidence rather than initiating another broad review round. The two second-round reports describe their frozen input, not an independent review of the later controller fixes. No accepted finding remains unresolved.

### Final verification

- Final source scope remains 17 files. Exact hashes match the isolated tested candidate. Final manifest SHA-256: `f6e4e3b2ac9402e6e8437ce865ba341a433d29b7f383bf79cc07b9125d32d4f2`.
- Final isolated candidate: 57 tests passed with `TMPDIR=/private/tmp`; installer tests mock network/tool/service actions. The affected endpoint test module also passed all 10 tests after the final jq fixture changes.
- Bash/zsh syntax, all six skill metadata validations, and worktree whitespace checks passed after final application.
- No live installation/sync, real launchd deployment or gateway model probe occurred. Preinstalled runtime tools are required; URL changes do not translate protocols/model IDs.
