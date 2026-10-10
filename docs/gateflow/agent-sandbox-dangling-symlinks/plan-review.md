# Plan review adjudication

- Gate: plan review -> fix. Work unit: agent-sandbox-dangling-symlinks.
- Reviewed plan SHA256: b314400191c522751ba0588852a657d1f383712870a80a7c87afb1d632f67844.
- Independent artifacts: docs/reviews/plan-review-20261010-173815.md (mimo/Codex, fail); docs/reviews/plan-review-20261010-173816.md (ds-flash/Claude, pass-with-risks).
- Both managed processes actually exited 0. Ordinary introspection/shell/fixture command errors are retained diagnostics, not grounds to reject the complete reviews. Reports, hashes and direct evidence were read by controller.

## Decisions

| Finding | Adjudication | Final fix state / required change |
| --- | --- | --- |
| MiMo 1: full custom resolver/minimal primitive/semantic change | accepted | 已修复; independently verified by plan-review-20261010-181201.md and -181202.md. Use existing strict resolution for valid targets; only confirmed ENOENT invokes os.path.realpath(strict=os.path.ALLOW_MISSING). Preserve existing valid-link canonicalization. Missing capability fails explicitly; no custom full resolver, version fallback, environment installation or compatibility framework. |
| DS 1: path behavior disclosure/observability | accepted | 已修复; independently verified by plan-review-20261010-181201.md and -181202.md. Explicitly disclose/test A preserves existing strict canonicalization; B strict ENOENT followed by missing-aware canonicalization may reach an existing target and must report the conservative expansion; C subsequent ENOTDIR propagates with context, without claiming identical syscall error precedence. |
| DS 2: missing-aware primitive rationale | accepted (rationale gap, not its prescribed custom-helper direction) | 已修复; independently verified by plan-review-20261010-181201.md and -181202.md. Revised choice and capability failure must be explicit and code-generation-ready. |
| MiMo 2: verifier FIFO/hardlink identity hardening | rejected-with-reason | Its FIFO reproduction used an unsandboxed open, not the required effective denial plus verified ancestor. Controller actual Seatbelt probe shows query=1 and immediate PermissionError under the relevant ancestor read/write denials (see evidence below). External replacement/no-snapshot scenarios and arbitrary manifest identity hardening are explicitly outside confirmed scope. Keep existing setup hardlink/special-target rejection and actual policy/open checks; do not introduce expected-kind/O_NOFOLLOW/fstat identity machinery. |
| MiMo 3: every conflict role needs provenance propagation | rejected-with-reason | The proposed contract already emits each declared/link/raw-target/canonical-target/ancestor expansion before required-input/output/write checks, followed by the concrete conflicting path. Together these deterministically locate the covering expansion. The finding adds a new all-role error mapping and broad test/propagation matrix rather than showing absence of the confirmed diagnostic. Retain this localized approach; add a focused multi-link conflict check so sufficiency is evidenced. |

## Open-question disposition

- DS ancestor cascade: preserve the existing visited graph traversal, report every additional missing->ancestor pair, test a nested dangling link discovered in an added ancestor. No arbitrary breadth limit/new fallback; root/conflict/scan failures stay closed. This clarifies the existing planned traversal.
- Path semantics: retain stdlib strict behavior on initially valid targets. On confirmed ENOENT use missing-aware stdlib canonicalization. Do not newly reject plain/../good targets that the existing resolver accepts; do not promise kernel-identical error precedence or reachability after lexical cancellation of a missing component.
- Python: current machine has ALLOW_MISSING. This optional missing-link handling requires that capability; absent capability produces a located setup failure, never non-strict/custom fallback or installation. Ordinary runner behavior and environment remain unchanged.
- Concurrent external mutation: existing exclusion retained. Synthetic materialization tests verify policy behavior, not production snapshot support.
- Real caller ancestry/configuration: outside allowed read/execute scope. Closeout reports source/live state and restrictions; caller owns real revalidation after separately authorized deployment.

## Controller validation

Independent temporary proof /private/tmp/dangling-controller-proof-5dj33yor/fifo-under-deny.json: sandbox-exec -f with actual recursive file-read*/file-write* ancestor denial; exit=0, sandbox_check=1, open=PermissionError errno=1, within 3s fixture timeout. No real Agent, business files or old Python installation. This contradicts the FIFO finding's claimed blocking path under the required policy.
Plan baseline/srt/materialization/resolution raw outputs and hashes were inspected; retained index: evidence/plan-experiments.json. No implementation tests run yet.

## Residual risks / docs / next gate

Current accepted rationale/observability findings: fixed in current slice's plan fix and verified at plan re-review before implementation. Conservative ancestor/cascade denial can block unrelated resources; implement/report/test within S1 and document it. Existing external replacement/content-copy/snapshot limitations: caller/maintainer, later separately confirmed work unit if required. Missing ALLOW_MISSING capability: explicit supported limitation documented by S1; no automatic environment change. No unclassified risk or blocking open question.

Docs decision: revise plan only now; README EN/ZH and advanced contract updates remain S1 work. Next gate: fix (gpt-6-sol plan revision), then parallel plan re-review. No accepted-plan commit yet.

Final plan-review loop decision: accepted findings 已修复 at plan layer; re-review verified. See plan-rereview.md.
