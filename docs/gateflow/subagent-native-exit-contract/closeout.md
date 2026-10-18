# Sub-agent thin CLI contract — closeout

Draft PR: [noho/code-is-cheap#61](https://github.com/noho/code-is-cheap/pull/61). Branch `fix/subagent-native-exit-contract`; base `32a244d1e286086be86dba837976d3d72fdd6c1f`. Independently reviewed implementation commit `781a239982631ab0ba8baf0bf6dd72069f3cee68`, source bundle `b580c570bdd9e43bfc79861440f4ff48f2cb8bc2b1b22bb7cddd4b8cef512502`. User merges manually; no merge/approval/ready/reviewer request/external message occurred. No issue supplied; issue linking/comment/auto-close is not applicable.

## What changed

The runners now expose a single fresh native CLI interaction: observed native exit, complete untruncated final and factual identity/usage/log/diagnostic/check observations. Schema2 removes the three competing statuses, runner-exit rollup,12000-character cap, final-length/truncation fields, diagnostic classes/counts/caps and semantic tool-text suspicion. Optional missing reports/canary observations no longer become runner failure. Genuine pre-exec setup and primary-result delivery errors remain honest wrapper failures; native nonzero is preserved. Auxiliary final-copy/race/cleanup observations never override native exit. Codex captures the CLI pipeline component; a narrow pre-exec error-only handoff distinguishes launch failure from identical numeric native returns and rejects stale custom launchers before entry.

Warning strings remain opaque, unfiltered and unchanged with source. Caller alone accepts the business task and decides follow-up/retry/routing under authorization; the fixed same-provider retry ceiling was removed. Both READMEs and the installed sub-agents skill/reference explain schema2 and custom-launcher migration. JSON output escaping fixes the independently found malformed duplicate-key surrogate delivery failure while preserving decoded final/diagnostic strings exactly. Two requested pre-existing investigation files are included unmodified as historical evidence, not new durability/recovery implementation.

## Verified source and findings

- Actual full final offline suite:236 tests,24 conditional skips,exit0; final log SHA256 `ff6ce7ad1b116ac20f1bcf5a42a02980b7758c4c7b804988b4f3ac371f50bec5`. Focused26,16 before-fail/after-pass high/low-surrogate cases across both runtimes/collector/native0-7, syntax and6 skill validations passed. Native codes, SIGPIPE, long Unicode/whitespace finals, root-final attribution, opaque warnings, no-clobber/auxiliary copy, custom/interactive launch and FD boundaries have actual retained regression proof. No unchanged passing full-suite repeat was required.
- Independent DS complete review (`code-review-20261018-100303.md`) found DS-C1 encoding and DS-C2 README omissions; controller reproduced/adjudicated them. Authorized gpt-6-sol fixed them and dead clean parameter in781a239. DS affected review (`code-review-20261018-105548.md`) independently closed all three; Mimo complete combined review (`code-review-20261018-105547.md`) found no material issue on the same15-file bundle. Controller read full reports/native tool trajectories/source/logs, verified file hashes and closed C-P1–C-P4/M-01/M-02/M-v2-1 and DS findings. No accepted finding remains open or unre-reviewed. Decisions.md records rejected superseded status/after-merge-sync suggestions and risk ownership.
- The first complete Mimo interaction ended native0 with content_filter explanatory final and no review report. Installed v1 changed outer to1; actual receipt/raw event anchors are preserved. It was not accepted as a complete review. Offline schema2 replay preserved native0/full final, and the later actual complete fixed-source report supplies the required independent review. No fixed retry rule/provider fallback or false provider-failure claim was used.
- An early implementation fake-exec fixture fell through to host Codex and401s, disclosed and retained without an invented native final/result. Single-target execve and hermetic fixtures closed that boundary with meaningful tests before frozen verification. It is not counted as an authorized live probe.

## Actual live delivery

Latest user authorization superseded the initial “PR only/no sync” boundary, recorded in delivery-amendment.md. After code and draft-PR delivery passed, controller ran from pushed checkout812acec:

```bash
./scripts/sync-agent-tools.sh
./scripts/sync-skills.sh
```

Both exited0; all6 skills validated.38 installed scripts/launcher/defaults/skill files matched baseline before sync and source bytes after sync and after probes. Source15 files equal reviewed781a239/b580c570.... Both Codex/Claude sub-agents SKILL copies now have SHA256 `a40660709e3c9d3fa5e6bbebbacb8895e1ad47797c75a7d135508ce0e1518796`. No merge prerequisite exists in these scripts. `sync-codex-agent.sh` was not applicable: profiles/catalogs/routes/shim unchanged.

Both **mimo-flash** calls used installed runners with independent fresh nonce-bearing inputs and prelaunch-absent outputs; actual outer/native0/0 in each. Native tool steps prove read→program exclusive-create/write→readback. Controller independently verified nonce/input SHA and all math, exact complete native-final/summary/file equality, exact schema2 fields and post-probe installed/source identity:

| Runtime | Actual tool-completion anchors | Native final / terminal | Count / sum / squares / weighted sum |
| --- | --- | --- | --- |
| Codex | JSONL4,7,9; all command exits0 | agent_message11 / turn.completed12 | 9 / -2675 /1365847 / -14008 |
| Claude | tool call/result10/11,324/327,335/336 | root result351 | 9 / -761 /3830989 / -4098 |

Codex emitted native type:error reconnect messages at5/10 (missing cached_tokens and SSE idle timeout); Claude emitted unrecognized-model stderr text. All originals and source locations remain visible in schema2 diagnostics, and both actual exits/full finals were preserved. No wrapper/controller retry or warning-text judgment occurred. Underlying response/SSE cause is not attributed or repaired in this slice.

Full evidence: live-probe-report.md, live-sync-commands.json, live-installed-identity.json, live-probes/{codex,claude}/ (exact selected native tools/terminal events, full final.txt, actual runner-summary.json, result/verification/input/prompt), both real receipts and untouched original JSONL/stderr paths/hashes. This is caller-owned explicit probe validation, not a new runner task-success mechanism.

## PR delivery and remaining risks

Controller verified actual PR repository/head/base, full OID diff and complete file list/source correspondence, title/body, required local validation, actual push and external checks. Initial record pr-delivery.md/pr-delivery-initial.json binds570993b; approved pre-sync snapshot pr-delivery-approved.json binds812acec. Both exact source/diff snapshots are retrievable. No configured CI workflow/check/branch rule was observed; no pending/failing status was waived. SSH push actually failed128 due connection closure; invocation-local HTTPS rewrite with existing gh credentials succeeded without persistent remote/config change. Later commits contain evidence/control records only, preserving the reviewed source. Final evidence push/PR body refresh and actual current head/base observation are the remaining closeout steps at this record's initial creation; final checks are recorded below when completed, without self-referential hash/commit loops.

Classified residuals:

- **Assigned to later caller integration**, owner caller/custom-launcher maintainers: schema-v1 consumers and custom launcher contract migration; refresh Agent sessions to load SKILL. Capability declaration cannot prove an arbitrary custom implementation honest.
- **Assigned to later runtime coverage**, owner runtime maintainers:24 conditional native/kernel opt-ins remain unexecuted; two live probes cover their actual routes, not every OS/profile/protocol variant. Same-frame malformed-Unicode salvage and the exact missing-capability preflight fixture are **deferred-with-owner** to future parser/test policy if needed; raw invalid frame/native exit remain preserved. No known current contract defect is waived.
- **Requiring new issue or explicit user decision**, owner maintainer: abrupt host/wrapper-loss recovery; no supervisor/persistence/result store was introduced.
- **Deferred diagnostic work if requested**, owner runtime/provider maintainers: observed missing-cached_tokens/SSE events' underlying cause, not investigated or attributed. Native call completed0/full final; no new source/route/config change or extra paid reproduction was necessary for this fix.
- Verbatim stderr/JSON escaping can increase output volume; owner caller/runtime maintainers, destination caller output handling if needed. No text filter or final cap was added.
- Reviewed-vs-installed skew and both required live probes are **fixed in this slice**, controller-owned, with completed byte/tool/math/final/exit proof. No unclassified residual or missing required live evidence remains.

## Caller handoff / next entry

Caller patrol entry remains this directory. Caller-side controller can now inspect live-probe-report.md and both verification/full-final/tool/identity artifacts, then notify its callers that SKILL is updated. Interactive launcher users run `source ~/.zshrc` or open a new shell; reopen Agent sessions for updated skills. Installed runner callers already on PATH do not need zshrc reload.

User manually merges PR61 when ready. Live sync was already explicitly authorized and performed from the reviewed branch; repeat the two applicable sync commands after any later approved source change, not merely because an unchanged source was merged. This upstream fix/probe does **not** resume, replace, approve or release A-route FY2025 business/code review. Caller retains its business acceptance/recovery authority; no paid old financial-task rerun occurred.
