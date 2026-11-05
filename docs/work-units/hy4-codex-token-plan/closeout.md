# Hy4 Codex runtime closeout

Status: **final closeout pass; work unit completed**. Draft PR: https://github.com/noho/code-is-cheap/pull/66. User merges manually.

## Delivered behavior

Hy4 is restored for Codex CLI and App: `hy` / `hunyuan` runner selection, `hy_codex` / `hy_codex_app`, a model-only card, shared provider registry, Responses shim route on 8796, and a repository-authored runtime catalog retaining the native guardian security instructions. The factory direct endpoint is `https://tokenhub.tencentmaas.com/v1`, model `hy4`, with an empty example key. Hy Claude's factory model is also `hy4`. Existing provider source snapshots and machine-local policies remain preserved.

The sole accepted review finding, DS1, is **已修复** and independently re-reviewed: sync/restart now waits for stable ownership of every configured listening port by the same launchd PID. A kickstart acknowledgement without ready routes returns failure with diagnostics.

## Verification and review

- 205 affected regression tests, with 11 explicit opt-in skips, passed in both independent full reviews. The four native synthetic Hy controls covered tools plus automatic review allow/deny/error.
- The actual staged branch runner completed real tools and native automatic review: native/runner exit 0, five upstream attempts, no retries. Direct Hy4 Responses runtime integration was demonstrated; model-quality/capability evaluation is outside this project's scope.
- All 28 focused readiness/install/conversion checks passed after the fix, both in the isolated implementation and after integration. Source hashes match the tested and independently re-reviewed version.
- Full reviews: `docs/reviews/code-review-20261105-115347.md` and `docs/reviews/code-review-20261105-115349.md`. Affected reviews: `docs/reviews/code-review-20261105-124912.md` and `docs/reviews/code-review-20261105-124913.md`. No accepted unfixed or new material finding remains. Claude DS authentication 403 required the AGENTS-authorized independent Codex DS backup; MiMo remained on Claude.
- Initial PR delivery checked repository/head repository, draft title/body, fixed base/head OIDs, complete 53-file diff and all committed blob OIDs. All 19 reviewed product hashes match source commit `47d66721683205abeaeb11c88d9a9833d7f74063`. GitHub has no statuses, check runs or workflow runs, and the repository defines no CI workflow. Final docs-only tail is checked again before the user-facing completion; the immutable final receipt is `/private/tmp/hy4-codex-task/delivery-final/receipt.json`.

Retained setup failures and measurement corrections are documented in `investigation.md`, `implementation.md`, `fix.md` and `controller.md`; they were not counted as passing native workflows. The first MiMo execution omitted its required report and was not counted as approval until its same-route completion produced a verified report.

## Authorized live rollout

Executed from this reviewed checkout on 2026-11-05, in this order; all exited 0:

```bash
./scripts/sync-agent-tools.sh
./scripts/sync-codex-agent.sh
./scripts/sync-skills.sh
```

Both installed endpoint factories were updated before the private configuration change. The live file and its mode-0600 timestamped backup remain outside Git. The atomic update changed exactly these three authorized nodes, reusing existing private credentials:

| Node | Base URL | Model |
| --- | --- | --- |
| `default.hy.codex` | `https://tokenhub.tencentmaas.com/v1` | `hy4` |
| `override.hy.claude` | `https://tokenhub.tencentmaas.com/plan/anthropic` | `hy4` |
| `override.hy.codex` | `https://tokenhub.tencentmaas.com/plan/v3` | `hy4` |

Unrelated private values and the existing direct Hy default were preserved. Both installed helpers validate the effective Claude/Codex connections. Installed source/factory/route files and skills match the checkout. The native parser accepted the installed Hy catalog. Mock native launcher checks verified Claude's URL, main/subagent model slots and selected authentication, plus Codex's Hy profile/shared home. The effective Codex upstream is `https://tokenhub.tencentmaas.com/plan/v3/responses`.

The restarted launchd job (PID 28987 at verification) owned all nine configured ports, 8788–8796; the installed stable-readiness function also passed. Verification was read-only after the authorized rollout and did not perform another vendor inference. A supplemental `features list -p hy` check was rejected because CLI 0.166.0 does not support profiles on that command; this invalid check was retained privately and replaced with the existing `debug models` native-parser check. No product fix was needed.

Raw sync logs, private-update verification and the sanitized installed-state receipt remain under `/private/tmp/hy4-codex-task/live-sync/`; no private endpoint document, credential or backup is committed.

## Remaining limits and owners

The tested Token Plan key returned **403001: package disabled or invocation permission missing** on both declared attempts. The requested Plan overrides are installed, so effective Hy calls now select Plan and will fail until the account owner enables the package/permission or supplies an authorized key. Direct Hy4 Codex was verified, and the direct default tuple is preserved for fallback; this closeout does not claim working Token Plan access. Owner: user/account administrator; destination: Tencent account/key configuration, outside repository implementation.

Readiness is a bounded startup observation, not an ongoing service guarantee; future operational availability belongs to the operator. Existing opt-in/non-Hy coverage boundaries remain documented in the implementation and review artifacts. There is no open code blocker or unclassified residual risk.

Bilingual README/runtime tables, catalog notes, skill inventory, investigation, implementation, fix and controller records are updated. This work unit has no associated issue, so issue linkage and closeout comments are not applicable.

Next entry point: user manually merges PR #66 and resolves Token Plan account permission. Live already contains these tested changes. Reload interactive launcher functions with `source ~/.zshrc` or a new shell; reopen Agent sessions for updated skills. Installed runner callers already on PATH need no shell reload.
