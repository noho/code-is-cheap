# Aggregate targeted re-review evidence (ds-flash route, Claude runtime)

Reviewer-written focused evidence for the DS-A1 re-review at the aggregate gate of work unit
`codex-recovered-timeout-demand`, 2026-10-13. Synthetic events only; no business input, no model request,
no delegation, no source edit. All artifacts below were produced by the reviewer in this session.

Reviewed source versions (SHA-256, measured):

- current `scripts/agent-run-result.py` `aa9b1a3eef7f048e6d8e8a06e06510da9178fcba9097270d422cf2eafc2dd7ff`
- current `tests/test_agent_run_results.py` `6cda405c565c9ebc200885bd61c1d8fe7e480b3562330afacd63e9ac38be891b`
- pre-fix snapshot (== HEAD `edd3d7b` blob) `9b44ac33099f49e8d4904e561e63f4e5dee43a6e177548cbb2edb5226f35ce5b`

## Commands and outcomes

1. Delivered-test differential (scratch trees under `$TMPDIR`, delivered test file, pre-fix vs current collector):

   ```bash
   python3 -B -m unittest discover -s tests -p test_agent_run_results.py -v \
     -k test_claude_result_owns_final_without_assistant_fallback \
     -k test_claude_native_negative_and_malformed_completion_overrides_success
   ```

   - pre-fix collector: exit 1, `FAILED (failures=4)` — all four are the DS-A1 display assertions (`value=''`, `value='  '` with prior partial; `value='  '` nested/no-root). Log: `unit-differential-before.log`.
   - current collector: exit 0, `Ran 2 tests ... OK`. Log: `unit-differential-after.log`.

2. Live current-source re-run of the three modified methods in the repository checkout:

   ```bash
   python3 -B -m unittest discover -s tests -p test_agent_run_results.py -v \
     -k test_claude_result_owns_final_without_assistant_fallback \
     -k test_claude_native_negative_and_malformed_completion_overrides_success \
     -k test_recovered_diagnostics_keep_selected_checks_for_both_runtimes
   ```

   exit 0, `Ran 3 tests in 4.750s OK`. Log: `live-current-3methods.log`.

3. Independent adversarial interaction probe, pre-fix vs current collector (synthetic CLI calls):

   ```bash
   BEFORE_SNAPSHOT=<fix-evidence>/before-agent-run-result.py WORK_DIR="$TMPDIR/rr-probe/work" \
     python3 -B probe_rereview.py
   ```

   Current source: 9/9 cases pass (blank-result-canary-match cannot rescue; canary mismatch with valid artifact; duplicate
   late result never displays; post-terminal assistant cannot overwrite; nested result text never supplies root display;
   whitespace partial retained; normal nonblank Claude unchanged; Codex blank/normal unchanged).
   Differential (only display/terminal fields, acceptance identical): 5 changed cases — exactly the blank/whitespace
   result display-retention delta; 4 unchanged. Full records: `probe-results.json`; per-case reports for the 5 changed
   cases under `current/` and `before/`.

## Files (SHA-256)

```
e6794d785c5b19faa66bcf2b28e97f8c311fde04591dd7dea17f531c9683b4f4  live-current-3methods.log
167493925a6b0de3dbb9f03f191860d310fd7eae3a4cd8a0a5596966eb42e52e  probe-results.json
7bb25e8434ff1369acb70fe8684693e3409544c36a7ad8e9c6a1480bded6e981  probe_rereview.py
d0a8cf256057b4c08eed74ab48f16e630cfa3239dc1ef9f1afb06369b7820629  unit-differential-after.log
4107fbc6b183bb60652d34ae71de7d6ad639e840abd4b448c3df707123b7c446  unit-differential-before.log
a455c4673276a20af7f6d70737f7b0e6a657ab32f7e661b61acbe671764a1783  current/c1-blank-result-cannot-be-rescued-by-canary-match-and-valid-artifact.report.json
8893d62647602735df29756f961325ab5deb46c61b3a57d37f015ae96b4ca740  current/c2-blank-result-with-canary-mismatch-and-valid-artifact.report.json
6e449df627a2c63e49c881a03f2b4f100cfe51e892e24eb56f8095a1ca8962f6  current/c3-duplicate-result-late-text-never-displays-over-retained-partial.report.json
f522ada5eb04cc6e272f7ff2580044c1f7d90a025076bdde1b89e6ca63191d30  current/c4-postterminal-assistant-cannot-overwrite-retained-partial.report.json
941803c784fb82981f71604f7519a93547aa8c5487952c85bc53351a41b17448  current/c6-whitespace-partial-then-blank-result-retained.report.json
c5ca02f32ba049a9b15c881b64317eea2ef7d3fdf4cf44038d00795c1154798f  before/c1-blank-result-cannot-be-rescued-by-canary-match-and-valid-artifact.report.json
ce369f4a991d7ed802ff458354406946fbb95d621a2aa09273e10aded825d23c  before/c2-blank-result-with-canary-mismatch-and-valid-artifact.report.json
129a93a33a2788652c7c10029e6fcdab8eb9f42950e2faef7e3f5480e177fb0c  before/c3-duplicate-result-late-text-never-displays-over-retained-partial.report.json
93d3b6283e71e9542341b702dcb827ab9ad141c6ede5ca7e60b62d06f68247c3  before/c4-postterminal-assistant-cannot-overwrite-retained-partial.report.json
6d968baeac6ce30fc90c307f6d7f5d0b3d37371508d48ca484b3419ec369cb8d  before/c6-whitespace-partial-then-blank-result-retained.report.json
```
