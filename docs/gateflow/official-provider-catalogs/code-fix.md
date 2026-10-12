# C1 fix: loaded launchd restart failure

Branch: `feat/official-provider-catalogs`. Scope: accepted C1 only, as adjudicated in
[code-review-decision.md](code-review-decision.md) and the approved plan's ordinary-recovery step 5.
**C1 status: 已修复 in product/tests; controller acceptance and independent dual re-review remain.**
C2 is already controller-owned/corrected. State, review reports, adjudication and prior evidence are unchanged.

## Exact change

- `scripts/sync-codex-agent.sh`: replace the loaded-service `kickstart && echo` with an explicit
  failure branch. Failed `launchctl kickstart -k` emits
  `ERROR: failed to restart launchd service: com.leo.codex-auto-review-shim` to stderr and exits 1.
  The restart message and final `Synced codex-agent cards` banner are unreachable on that failure.
  Successful restart continues through the existing business-default step and final success banner.
  The unloaded-service path is unchanged.
- `tests/test_model_catalog_generation.py`: extend the existing fake launchctl with opt-in loaded
  status and configurable kickstart exit, retaining unloaded status by default. Add two full-script
  temporary-home tests: loaded `print=0`/`kickstart=77` failure, and loaded successful restart.
  Both require exactly one print and one kickstart, with no bootstrap/bootout or extra service action.
  Failure requires nonzero, the explicit diagnostic, no restart/final success message and no conversion
  rollback diagnostic. Success requires exit 0, both success messages and empty stderr.
  Both verify all nine generated card/catalog pairs against current rendered cards and complete assembled
  catalogs, mode 0600, the complete current provider registry, preserved unrelated synthetic base settings
  and base mode 0640, current route bytes, and removal of the temporary conversion stage.
- This document records the fix and validation. No other existing repository file was changed by this task:
  SHA-256 comparison against `/private/tmp/official-catalog-c1-before/workspace-hashes.json` confirmed
  only the two allowed product/test paths changed among the 31 preexisting changed/untracked files.

Recovery remains disarmed before ancillary deployment. Restart failure retains the already installed
conversion pairs/registry and ancillary files; the EXIT handler cleans staging without rolling them back.
No transaction, service lifecycle, compatibility, catalog/source/guardian/max/route metadata, runtime,
statistics or isolation behavior was expanded. The existing narrow conversion recovery is unchanged.
All script executions used the existing copied-repository fixture and fake launchctl; no actual services,
provider/Kimi API calls, business/auth/live reads, delegation, Git staging/commit/push/merge or live sync occurred.

## Actual commands and outcomes

Before changing the product script, the two new tests ran against its existing behavior:

```bash
PYTHONPATH=tests python3 -m unittest -v test_model_catalog_generation.ConversionSyncTests.test_loaded_service_restart_failure_keeps_conversion_and_reports_failure test_model_catalog_generation.ConversionSyncTests.test_loaded_service_restart_success_keeps_conversion_and_prints_success
```

Exit 1; 2 tests in 3.937 seconds, 1 failed and 1 passed. The failure test observed script exit 0
and failed `assertNotEqual(done.returncode,0)` (`0 == 0`); the successful restart test passed.
This expected pre-fix failure is retained alongside the original isolated full-script reproduction,
[service-failure-reproduction.json](evidence/service-failure-reproduction.json), which records swallowed
kickstart exit 77, script exit 0 and the erroneous final success banner. That evidence was not rewritten.

After the script fix:

| Actual command | Actual outcome |
| --- | --- |
| `PYTHONPATH=tests python3 -m unittest -v test_model_catalog_generation.ConversionSyncTests` | Exit 0; 15 tests passed, zero skipped, 19.449 seconds. Both new restart cases and all existing conversion recovery cases passed. |
| `bash -n scripts/sync-codex-agent.sh` | Exit 0. |
| `PYTHONPYCACHEPREFIX=/private/tmp/official-catalog-c1-pycache python3 -m py_compile tests/test_model_catalog_generation.py` | Exit 0. |
| `git diff --check` | Exit 0. |

The 15-test run includes the existing actual offline native staged-rejection test. Its intended native
parser exit 1 reported `unknown variant native-invalid-enum, expected bytes or tokens`; registry/card/catalog
sentinels remained unchanged. The incidental temporary-helper PATH warning was also present and did not
replace the parser-rejection evidence. This negative case passed; it is not a provider/runtime execution.
No broader native/kernel/provider matrix was rerun: the only behavior change is after verified conversion.

## Preserved evidence and residual owners

All earlier failures remain in [implementation.md](implementation.md) and its linked evidence, including
fixture-shape failures, restricted-parent read/write failures and preliminary controller canary issues.
This fix does not convert them into passes or alter original review reports.
Current controller evidence, as supplied by the controller/user: **12 native tests passed (11 native fixtures
plus 1 fixture control); 80 kernel tests and 2 dual-runtime tests passed; 8 real status-only probes
accepted max, Kimi exactly once.** These are prior controller results, not commands executed by this fix.
The older implementation handoff's outstanding-kernel language does not supersede those supplied results.

| Remaining area | Owner / disposition |
| --- | --- |
| C1 evidence adjudication and required independent MiMo/Codex + DS Flash/Claude re-review | Controller; next gate. No delegation or review-pass claim in this task. |
| C2/state reconciliation and original review records | Controller; already corrected, left untouched. |
| Ancillary shim/service/business outcomes, cross-file reader visibility, concurrent writers, crash/power loss/disk destruction and restoration-I/O failure | Maintainer/controller; outside narrow rollback. Restart failure now fails overall sync visibly while retaining installed conversion. |
| Vendor tools/guardian/App, alternate overrides, future CLI/schema/host behavior and unchanged shim protocol edges | Maintainer/user follow-up; existing status-only acceptance does not certify these areas. |
| User-authorized derived GLM Flash source and MiMo route-wide schema downgrade | Existing user/controller/maintainer ownership; preserved. |
| Accepted-slice Git staging/commit, push/draft PR and later manual merge/live deployment | Controller/user workflow after re-review; not performed here. |

No additional expensive matrix is required by an observed remaining C1 risk. Controller owns any further
checks justified by re-review findings and final gate acceptance.
