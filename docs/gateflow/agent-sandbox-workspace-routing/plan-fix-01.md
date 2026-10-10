# Plan fix 01: agent-sandbox-workspace-routing

- Date: 2026-10-11.
- Mode: independent GPT-6 Sol plan fix only; implementation has not started.
- Worktree/branch: `/private/tmp/code-is-cheap-workspace-routing`, `fix/agent-sandbox-workspace-routing`.
- Observed HEAD/base: `20fc6c37751836329143567c166990bdffa9de3c`.
- Binding authority: confirmed `goal.md`, root `plan-adjudication.md`, and the delegated fix instructions. The goal remains unchanged.
- Owned writes: `plan.md` and this new `plan-fix-01.md` only. Root owns adjudication, state, statistics, evidence, all routes and kernel/live validation.
- Initial reviewed plan SHA-256: `918ee36380c4c0456f9c7b7448573baee4dfad1c303785bcfdf0ae66284e9409`; frozen `evidence/plan-initial.md` retains that same hash.
- Revised plan SHA-256: `2953a6f37651cf0b1b83c2c3c99bab6a546e82890a3b9fd7b7681e28cff9c47d`.
- Status: all accepted items fixed in plan; independent root-routed re-review and root adjudication remain required. No implementation/pass gate is claimed.

## Accepted-item dispositions

| Item | Status | Exact decision and plan coverage | Evidence / remaining verification owner |
| --- | --- | --- | --- |
| F1 (MiMo1; medium) | Fixed in plan; implementation/re-review pending | Accept both ordinary `CERTIFICATE` and native-supported `TRUSTED CERTIFICATE`. In the single CA helper, scan recognized certificate delimiters in order and reject malformed/incomplete/orphan/nested/mismatched companions; validate every complete certificate separately. Normalize trusted BEGIN/END labels only in the in-memory stdlib validation string; preserve all original bytes, AUX, selected file and canonical native input. Ignore X509 CRLs; CRL-only is no certificate input, and CRLs do not grant trust or revocation checks. Updated evidence, alignment, consumption, parser/errors, S1, unit/native-input tests, docs and residuals consistently. | MiMo finding 1 and static native 0.162.1 strings; root adjudication; root `evidence/trusted-ca-parser-control.json` and genuine public trustout fixture below. S1 implementer exercises real stdlib parsing on ordinary/trusted/mixed/CRL-containing and malformed forms; root owns independent re-review and later native/kernel/live verification. |
| F2 (MiMo2 / DS01; low, deduplicated) | Fixed in plan; implementation/re-review pending | Exactly five allowed implementation files; `README.zh.md` is the fifth. Both user READMEs and `skills/sub-agents/references/advanced.md` receive matching short CA paragraphs and an absolute export example in the same S1. Corrected all counts, file/doc lists, slice/handoff wording and residual ownership. | Both named initial findings and DS A10 identify the mirrored Chinese macOS envelope section. S1 implementer mirrors default, precedence, empty values, forms/CRL handling, located failures and keychain/parser limits; root reviews all three surfaces. |
| F3 (root; low) | Fixed in plan; diagnostic adjudication pending at live gate | Collector status follows actual errors/anomalies, independent of optional-check selection. Require no summary/top-level errors, native/runner/process 0, completed/turn.completed and exact final OK (zero tools for the existing prompt). Preserve `result_status=not_assessed`. Either actual `passed` or `needs_review` is acceptable only after root inspects diagnostics and adjudicates all remaining anomalies; errors/rejected fail. No mandated needs_review, collector edit or invented proof/check field. | Root adjudication cites existing collector `agent-run-result.py:398-402`: ordinary no-check control passed; isolated CA-success needs_review came from a known unstable-feature anomaly. Current plan already contained part of this correction; revised assertions make no-errors and inspection of either status explicit. Root owns actual live diagnostic inspection and gate decision. |
| C1 (DS clarification) | Fixed in plan; implementation/re-review pending | Automatic-default kernel subcase computes expected current public system CA bytes or SHA-256 during test execution immediately before launch, then compares the synthetic native in-sandbox read. No embedded whole OS bundle or historical fixed bundle hash/count/size. The separate explicit synthetic certificate fixture remains fixed/deterministic. Expectation transport belongs only to the test stub. | DS open question 1 documents OS-bundle drift. S1 implementer writes the runtime expectation; root owns execution of the unchanged kernel/native-env chain and evidence. |
| C2 (DS clarification) | Fixed in plan; implementation/re-review pending | New version wording explicitly scopes CA selection/empty-value observations to the measured installed Codex 0.162.1 build. Keep adjacent unrelated whole-envelope Codex 0.161.0 claims and other runtime version wording; no blanket upgrade claim. Applied to evidence, all three doc decisions and parser/runtime residuals. | DS open question 2 and the plan's measured 0.162.1 native binary identity/selection disassembly. S1 implementer supplies narrowly scoped CA wording; root reviews bilingual/Agent equivalence and existing statements. |

No accepted item is intentionally rejected or deferred. In particular, current native-supported trusted labels are supported in the planned helper; remaining parser differences cannot be used to revive F1's ordinary-only contract.

## Exact F1 validation and fixture decisions

The unchanged selection/path/regular-file sequence is HTTPS-only Codex -> nonempty CODEX, else nonempty SSL, else system default -> cwd-relative literal path and strict canonical resolution -> complete existing deny check before bytes -> regular-file lstat/open/fstat -> one read -> certificate syntax validation -> selected env path assignment. Failure leaves env unchanged and never falls through to lower-priority input or starts the runner.

Within that same helper, pairing uses the two recognized labels and file order, rather than counts or extraction of only successful spans. Every recognized certificate block gets its own fresh `SSLContext(PROTOCOL_TLS_CLIENT).load_verify_locations` call; trusted labels alone become ordinary labels in the validation string, and the AUX-bearing payload is unchanged. Noncertificate surrounding comments and X509 CRLs are ignored. The helper does not interpret AUX trust policy or load CRLs/default roots, audit chains/expiry, replace native TLS or create a normalized file. The native client consumes the selected original file and owns endpoint trust/runtime acceptance.

Located invalid-bundle failures distinguish no certificates (including CRL-only), malformed/truncated delimiter, incomplete block, orphan/nested marker, mismatched labels and certificate parse failure, with ordinal/label where useful and bounded reasons. Include source/declared/canonical path as already planned; never print certificate bytes. Missing/denied/nonregular/unreadable categories and deny-before-open order remain unchanged.

Root evidence `evidence/trusted-ca-parser-control.json` reports:

- `trusted_label_present=true`.
- Original trusted-label parsing: `parsed=false`, `error=SSLError`.
- Validation-only label normalization: `parsed=true`, store `x509=1`, `x509_ca=1`, `crl=0`.

The authorized genuine OpenSSL trustout public fixture is `/private/tmp/workspace-routing-gateflow-vVRPod/public-trusted-ca-test.pem`: 2,203 bytes, SHA-256 `6c35f5365ad5d6de53d8445cfcad2c93daad56b49fa1611d2811ec00a34705ce`, one matched trusted BEGIN/END pair and no PRIVATE KEY marker. Its AUX provenance comes from root adjudication/control, not from merely relabeling an ordinary certificate. The fix agent inspected only its public structural/hash metadata; no new parser prototype was needed. Embed those public bytes or a fixed public AUX-bearing equivalent as a test constant, never depend on this scratch path or generate a private key during tests.

Required plan cases now include ordinary/trusted single and multiple certificates; mixed forms in both orders; CRLs before/between/after valid forms; unchanged original file/labels/AUX and native selected path; CRL-only rejection; both labels' incomplete/truncated/malformed/mismatched/orphan/nested delimiter failures; non-ASCII block text, malformed base64 and invalid X.509 DER; and valid+invalid companions in both orders across forms with/without CRLs. These tests exercise real stdlib parsing, including genuine AUX. Non-ASCII surrounding comments remain supported. Other stdlib/native parser, algorithm and AUX-policy differences remain explicit limits below, without claiming full byte-for-byte native parser equivalence.

## Evidence and integrity checks performed by this fix agent

Read only the confirmed goal, current plan, adjudication, the two explicitly named initial reports and the authorized public parser control/fixture. Existing plan source facts were retained; no live/source re-investigation or other review transcripts were needed. Named reports remain original and their conclusions/statistics are not rewritten. In particular, MiMo's original suite record remains root-adjudicated as Ran 52, OK(skipped=9): 43 executed, 9 skipped; that historical test run is not a test run by this fix agent.

Performed read-only branch/HEAD/status checks, bounded artifact reads, public fixture metadata checks, guarded text edits, textual consistency checks and byte-integrity checks for protected work-unit artifacts/reviews and the five product/test/doc files. Initial plan and current plan matched `918ee36380c4c0456f9c7b7448573baee4dfad1c303785bcfdf0ae66284e9409` before fixing. The protected files were unchanged across this edit; tracked Git diff remains empty, and branch/HEAD remain the supplied values. Product tests, parser prototypes, kernel/native/model/API execution, Git writes, delegation, installation/sync, process/pane operations and publishing were not performed. Planned validations are still pending root's accepted-plan and implementation gates.

## Classified residuals and owners

| Residual / outstanding obligation | Classification | Owner and destination |
| --- | --- | --- |
| Implement and verify F1 ordinary/trusted compatibility, every-certificate rejection/error flow, F2/C2 all-three-doc agreement and C1 runtime/default fixture | Required current S1 work; plan fixed, verification pending | Root-routed S1 implementer; implementation/test/doc artifact and root-owned code review. Accepted items are not deferred. |
| Independent plan re-review and acceptance of these five fixes | Required current gate | Root controller; independent re-review reports and updated root adjudication/state after review. This fix agent does not advance them. |
| Collector errors/anomalies and genuine terminal/final/exit evidence | Required live-validation adjudication, not optional-check policy | Root controller; synthetic startup validation artifact. No errors and successful exits/completion/final are mandatory; inspect diagnostics for either passed or needs_review and adjudicate anomalies. |
| Exact denied macOS trust-service operation is unmeasured | Assigned separately scoped later work | Root/maintainer; optional system-trust diagnosis and closeout risk table. No trustd grant, weaker isolation or TLS bypass. |
| System PEM may omit keychain-only roots; explicit roots may not trust the endpoint | Accepted deployment limitation / later deployment verification | Affected caller/deployment owner; permitted explicit PEM configuration, both READMEs/advanced docs and post-deployment verification. |
| Other OpenSSL/native parser/algorithm/AUX-policy differences and future CA env semantics | Deferred runtime-upgrade risk | Runtime-upgrade owner/root; existing boundary-validation process and closeout. Current ordinary/trusted forms are supported now; native rejection stays a real failure. |
| Path/content replacement after setup, including already allowed aliases | Existing input-stability risk | Caller controlling input stability; existing no-external-replacement contract and closeout. Any observed S1 boundary bypass blocks root closure. |
| Original caller details, large business deny graph and task restoration not reproduced | Explicit scope exclusion / later caller verification | Original caller/controller; post-deployment task restoration and final next-entry record. No original/model/kernel task by this dispatch. |
| Validation prerequisites unavailable, auth expiry, service outage or missing live evidence | Conditional gate blocker requiring root/user decision if encountered | Root controller; actual failing gate artifact and next decision. No migration/install/policy relaxation to manufacture a pass. |
| Merge or live sync | Separately authorized user action | User/root after review/PR gates; manual merge and no live deployment in this work unit. |

No future feature or extra implementation slice is proposed. The confirmed goal, provider/auth route, read/write/domain policies, env precedence/path semantics and root ownership of kernel/live tests remain intact.

## Handoff

All F1/F2/F3/C1/C2 plan changes are complete. Blocking questions: **none**. Next uncompleted gate: root-routed independent plan re-review, then root adjudication and accepted-plan checkpoint before any implementation. Root owns downstream routes, state/statistics updates and PR lifecycle; this dispatch stops with the two reviewable plan artifacts.
