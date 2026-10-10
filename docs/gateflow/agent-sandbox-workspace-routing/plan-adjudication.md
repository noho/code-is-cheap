# Plan review adjudication: agent-sandbox-workspace-routing

Gate: plan review -> fix -> independent re-review required. Initial plan SHA256 `918ee36380c4c0456f9c7b7448573baee4dfad1c303785bcfdf0ae66284e9409`, retained as `evidence/plan-initial.md`.
Reports: MiMo/Codex `docs/reviews/plan-review-20261011-055758.md`; DS Flash/Claude `docs/reviews/plan-review-20261011-055759.md`. Both completed actual native/runner0; MiMo needs_review from three ordinary exploratory failures, DS passed with one native visibility warning. No top-level errors or unsupported recovery were reinterpreted.

## Decisions

| ID | Candidate / evidence | Decision | Required minimal plan fix / validation | Status |
| --- | --- | --- | --- | --- |
| F1 | MiMo1: regex/parser excludes native-recognized TRUSTED CERTIFICATE | accepted, medium | Specify ordinary and trusted-label certificate support; normalize trusted labels ONLY in in-memory syntax validation, retain original CA file and selected env input for native consumption. Ignore CRL entries as native does; validate every recognized cert and reject malformed/unbalanced companions. Add valid trusted, mixed/CRL and malformed-trusted controls. No full TLS parser replacement. | 已修复 |
| F2 | MiMo2 / DS01: Chinese README omitted from allowed docs | accepted, low, deduplicated | Include README.zh.md as fifth allowed file; mirror CA precedence/default/located errors/keychain limits in both READMEs and advanced skill reference. | 已修复 |
| F3 | Root: plan live assertion incorrectly attributes needs_review to no optional checks | accepted, low | Existing collector lines398-402 derives status from errors/anomalies, not selection absence; ordinary diagnostic succeeded passed without checks, isolated diagnostic needs_review from known unstable-feature anomaly. Accept actual passed or needs_review after diagnostic adjudication; require native/runner0, no errors, successful terminal/final. No fixed needs_review/no-canary causal claim or collector change. | 已修复 |
| C1 | DS open question: automatic default kernel fixture bytes unclear | accepted implementation clarification | Compute expected public system-bundle bytes/hash at test runtime; never embed a whole OS-maintained bundle or assert its fixed historical hash. Test explicit synthetic CA bytes separately. | 已修复 |
| C2 | DS open question: adjacent whole-envelope 0.161.0 statement versus CA 0.162.1 observation | accepted docs clarification | Scope version wording to the actually verified CA behavior; no unrelated blanket version upgrade claim. | 已修复 |

Root independently constructed a genuine OpenSSL trustout public certificate with auxiliary trust data: direct Python cadata trusted-label parsing fails, validation-only ordinary-label normalization accepts the same bytes. Evidence `evidence/trusted-ca-parser-control.json`. No private key, API request or auth data used. MiMo's binary-format evidence is static; native parser/algorithm differences remain documented limits, not a claim of testing every enterprise TLS chain.

MiMo offline test record is **Ran52, OK(skipped=9)**, meaning43 executed and9 skipped, not52 executed passes plus9 more. Root inspected actual event113. Its mistaken binary path and inline Python quoting error were resolved and retained; no conclusion relies on a failed tool output. DS independently simulated the plan algorithm and checked source/environment chain. No product files changed; no kernel/live execution by reviewers.

## Binding limits and remaining owners

One slice; no new schema/route proof, no policy/domain/write changes, trustd grants, TLS disablement, API/auth migrations, caller tasks or old branch edits. Exact denied service unmeasured: separately scoped maintainer diagnosis. System PEM/keychain and native algorithm acceptance: deployment/runtime-upgrade owner, explicit permitted PEM plus verification. File stability: caller contract. Original large caller boundary/task restoration: caller; root checked only retained named boundary configs and found system CA not covered, without running those tasks. Merge/live: separately authorized user action.

Goal remains confirmed; these changes correct the planned implementation of custom-input and documentation success signals. No blocking user question. GPT-6 Sol plan fix next; initial reviews and raw statistics remain unchanged. Plan loop cannot pass until independent re-review verifies all accepted items.

## Plan re-review receipt and final controller adjudication

Both actual calls exited native/runner0. MiMo passed mechanically; DS needs_review from one resolved process-substitution /dev/fd permission error, plus native unrecognized_model visibility warning. Root independently verified selected product/plan hashes unchanged and read both full reports. Real raw statistics retained in review-statistics.json. MiMo actual baseline test outputs were Ran52 OK(skipped9), and collector Ran38 OK; do not count skipped tests as executed passes.

DS report docs/reviews/plan-review-20261011-062441.md verifies all F1/F2/F3/C1/C2 已修复. MiMo docs/reviews/plan-review-20261011-062440.md verifies F1/F2/C1/C2 已修复 and proposed an additional F3 unsupported-notice rule. **New finding rejected-with-reason**: confirmed CA goal preserves the existing collector and rejects errors/nonzero/failed or missing terminal/final; plan actual-pass assertions already require all of these and root evidence-based anomaly inspection. An undefined blanket unsupported item-notice classifier is not a confirmed success signal. The review prompt ambiguously imported an unsupported-recovery preservation sentence from separate recovered-stream work; it does not authorize expanding this goal. Existing top-level errors are fatal, item-level errors can be documented ordinary anomalies. No collector change/downgrade is planned. Root verified original F3 status-attribution fix directly against plan assertions and source398-402; F3 is 已修复. No accepted outstanding plan finding or blocker remains.

Remaining risk ownership remains the binding table above and plan residual table. Plan loop passes with the unchanged reviewed SHA2953a6f37651cf0b1b83c2c3c99bab6a546e82890a3b9fd7b7681e28cff9c47d; next accepted-plan checkpoint then GPT-6 Sol S1 implementation. No product edit yet.
