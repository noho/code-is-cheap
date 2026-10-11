# Final closeout: agent-sandbox-workspace-routing

Gate decision: **final closeout pass**. Confirmed scope completed through draft-PR-pass: accepted PR review `129b539a2bf55e70fad89fa04d760bc8183e7bb7` pushed, GitHub head equals it, PR remains draft, base unchanged, statusCheckRollup empty. This closeout checkpoint adds only evidence/lifecycle documentation, not product changes. Work unit completed; merge and live deployment are separate user actions.

## What changed

Five product/test/doc files: scripts/agent-sandbox prepares an explicit permitted CA for Codex HTTPS in both --check and launch; tests/test_agent_sandbox.py verifies selection/failures/parser/actual consumption; README.md, README.zh.md and skills/sub-agents/references/advanced.md document behavior and limits. Nonempty CODEX_CA_CERTIFICATE wins over nonempty SSL_CERT_FILE; absent/exact-empty selects /etc/ssl/cert.pem. Relative paths use envelope cwd; selected canonical regular permitted PEM is checked before runtime, original bytes/AUX preserved, missing/denied/invalid selected input fails with location without fallback. HTTP and Claude do not gain a CA requirement. No runner/collector/provider/auth/installer, business or boundary change.

## Verification

- Current wrapper2fc5c03e… and tests26fa402b…: offline Ran80 OK(skipped10), **70 executed**,10 opt-in kernel skips.
- Actual selected kernel **4 methods pass,0skip**,5 envelopes including2 native CA subcases. Real wrapper/runner/launcher chain reaches native stub with original selected path/bytes/hash and real --output sink. Direct/symlink/history/recursive/nested denies and original writes retained; first trusted-parent profile/source hashes verified, strict domains/no trustd/no weaker isolation/TLS bypass.
- Fresh strict source Sol default-CA managed-auth: outer/native/runner0, turn.completed, finalOK,0tools/0errors, **5.727766s**. Existing under-development anomaly needs_review retained and root-adjudicated; no collector change or broad error downgrade.
- Original two business failures, synthetic failure, initial K1 assertion failure and historical firstsource success6.564470s remain intact. Native per-call wall/token usage retained in review-statistics.json (21 actual collected calls including two live minima; overlapping calls are not summed as elapsed workflow time).
- Four diagnostic controls support default TLS trust-input incompatibility under the strict envelope; explicit permitted CA restores minimum startup. **Exact blocked system service remains unmeasured**. Additional Astra sample linked in evidence/additional-astra-sample.json: native/runner1,turn.failed,0tools; it is a same-family original failure, **not post-fix Astra proof**.
- Immutable PR target e21f3070f3701335808b36fef66189fe3a183093/base20fc6c37751836329143567c166990bdffa9de3c: complete40file manifest/diff/linecounts matched GitHub/local; both reviewers and root verified stable GH facts. Later accepted PR review delta is six review/statistics/lifecycle/evidence files only, audited by root; product/binding-plan hashes unchanged. CI response empty, no check claimed; no .github directory in this baseline.

## Findings and docs

Plan, S1 code, aggregate and PR gates completed with independent MiMo/Codex and DS Flash/Claude reviews; GPT-6 Sol owns all plan/implementation/fix changes. Plan accepted findings closed; **K1 and A1 已修复** and dual re-review verified. PR reports docs/reviews/pr-53-review-20261011-084858.md and pr-53-review-20261011-084859.md: no new material product findings, no fix/re-review required. Root read full reports and actual intermediate tool recovery evidence; true statuses/diagnostics retained. Decisions in plan-adjudication.md, code-adjudication.md, aggregate-adjudication.md and pr-adjudication.md. All three documentation surfaces updated, no unclassified or blocking residual.

Checkpoints: accepted plan1e6693b; S1b2ac329; aggregate9298c2d; readiness e21f307; accepted PR review `129b539a2bf55e70fad89fa04d760bc8183e7bb7`. Metadata-only closeout follows. Separate recovered-stream draft PR52 is complete and was neither interrupted nor mixed into this diff.

## Remaining limits / owners

| Limit | Classification / owner / destination |
|---|---|
| Exact blocked service | Assigned later work unit; maintainer, separately authorized diagnosis; no service-causality claim |
| Native parser/algorithm/AUX/CSR/exotic PEM and future native CA semantics | Assigned later runtime-upgrade validation work; runtime-upgrade owner; syntax is not endpoint trust/full equivalence |
| System PEM omits keychain-only roots, input paths/bytes may change | Assigned deployment/caller verification work; caller supplies explicit permitted PEM and stable inputs, no boundary exception |
| Original large804/808 graph, business tasks and Astra post-fix success not rerun | Assigned caller restoration/verification work after authorized deployment; original caller owns notification/continuation |
| Empty CI checks | Assigned separate maintainer CI-policy work; no invented pass/check |
| Merge/live deployment | Separate user authorization; deployment owner syncs and original caller revalidates; this task does not deploy |

No external issue assigned: PR issue link/closing keyword and issue-closeout comment **N/A**. No issue/comment/review request, mark-ready or merge performed.

## Applicable entry / live state / next step

Source entry `/private/tmp/code-is-cheap-workspace-routing/scripts/agent-sandbox` was validated with matching worktree scripts PATH and AGENT_TOOLS_FILE and explicit provider gpt-6-sol. Applicable to existing **Codex HTTPS routes** inside macOS/srt strict envelope; current CA behavior proven on Codex0.162.1/srt0.0.79. User custom CA must be permitted/readable/regular/valid/stable. Sol managed-auth minimum is the real post-fix proof; other models/production entry success is not claimed.

Read-only closeout entry check: installed `/Users/leo/.local/bin/agent-sandbox` SHA `18d54243b1302aa8ebb4097821c47c44e38776f241185047f771e5c30f1b3eb5`, CA helper **absent**, still baseline. Source SHA `2fc5c03e7ed069e032860c6e0c4f71be9b39bb702bcf9d08bd9d97298bd23e04`. **Standard live entry has not received the repair and is not yet cleared for caller restoration.** Entry status evidence: evidence/pr-pass-entry-status.json.

Next: user manually merges PR53; separate explicit authorization for sync to live; caller then validates its original deny boundary/actual entry and decides recovery notification/task restoration. Do not interrupt the currently running substitute Developer. No original tasks or business prompts/reports/contracts/denies were read/changed/replayed, except authorized metadata/log structure diagnosis.

Draft PR: https://github.com/noho/code-is-cheap/pull/53.
