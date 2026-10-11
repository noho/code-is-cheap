# Aggregate fix 01: agent-sandbox-workspace-routing

- Gate: aggregate deepreview -> fix; local fix handoff only, aggregate gate remains open.
- Worktree: `/private/tmp/code-is-cheap-workspace-routing`.
- Branch: `fix/agent-sandbox-workspace-routing`.
- Observed HEAD: `b2ac329ec410b11ffc2f8a873add800ad1957290` (accepted S1).
- Date: 2026-10-11.
- Binding definitions read: repository `AGENTS.md`, confirmed `goal.md`, accepted `plan.md`, and root `aggregate-adjudication.md` in this work unit.
- Artifact: `docs/gateflow/agent-sandbox-workspace-routing/aggregate-fix-01.md`.
- Root owns gate decisions, current-source affected-path validation, dual aggregate re-review and subsequent checkpoints. This dispatch has no Git-write, review delegation, kernel/live/model/API-test, install/sync, publishing, merge or business-task authorization.

## Scope and exact changes

Only accepted A1 is fixed. The confirmed goal and plan are unchanged. The five changed product/test/doc files are the five explicitly allowed files; this record is the sole new repository artifact owned by this dispatch.

| Changed file | Exact change |
| --- | --- |
| `scripts/agent-sandbox` | Replace the unanchored certificate-prefix candidate search with a marker-line-anchored match. A supported label must end at a delimiter boundary or the end of the line; CSR, space-suffixed and hyphen-suffixed longer labels are not certificate labels. Preserve the existing exact full-delimiter match and pairing/per-certificate validation. Recognized markers with incomplete dashes, leading/trailing ASCII whitespace or trailing text still fail. |
| `tests/test_agent_sandbox.py` | Add three bounded offline methods for noncertificate compositions, decorative comments and active-block input retention. Add seven synthetic noncertificate labels with deliberately invalid payloads, no private keys. Extend the existing no-certificate and malformed-delimiter cases; retain all old invalid companion, pairing, CRL, AUX and environment/boundary assertions. |
| `README.md` | One short matching clarification: surrounding comments and noncertificate entries, including CSRs, are ignored and do not count as certificates. Existing setup/native-parser limits remain explicit. |
| `README.zh.md` | Matching clarification, explicitly limited to material outside certificate blocks. |
| `skills/sub-agents/references/advanced.md` | The same Chinese clarification as the user README. |

The scanner recognizes only `CERTIFICATE` and `TRUSTED CERTIFICATE`. Full supported BEGIN/END spellings remain strict; malformed supported delimiters are not repaired. Every recognized ordinary/trusted block still enters the existing pairing checks and individual stdlib validation. Unknown labels and comment text inside an active certificate block are retained in that block's validation input, including non-ASCII text that must fail ASCII decoding. Ignoring surrounding material does not hide a recognized invalid certificate companion.

The original selected file, original labels/AUX and canonical child path are preserved. There is no CA file normalization/copy, CSR trust or syntax-validation requirement, native parser redesign, extra dependency, or change to selection precedence, route, authentication, boundary policy, environment contract or result schema.

## A1 status and decision boundary

| Finding | Binding decision | Local fix status | Evidence / remaining requirement |
| --- | --- | --- | --- |
| A1 (accepted DS F1) | `accepted`, low; prefix/embedded matches violate the plan's noncertificate-surrounding-text rule | `已修复` locally; final root validation/re-review pending | Before-fix regressions reproduced malformed-delimiter failures for CSR/comment compositions. After-fix full offline suite passes. Root must validate the changed wrapper on the affected path and obtain both independent aggregate re-reviews before assigning final finding status and passing the aggregate gate. |

This record does not alter root adjudication or claim aggregate pass, accepted deepreview checkpoint, deployed state or business-task restoration. No current peer transcript/report was read. Prior root failures and live successes remain historical records and are not repurposed as evidence for this changed wrapper.

## Actual validation

All test commands ran through structured `exec_command` in this worktree. A Python `TemporaryDirectory` under `/private/tmp` supplied fresh `home` and `tmp` directories. The child environment contained only inherited executable `PATH`, synthetic `HOME`/`TMPDIR`, `PYTHONDONTWRITEBYTECODE=1`, and `LANG=en_US.UTF-8`; focused regression selection additionally used `PYTHONPATH=tests`. CA overrides and kernel opt-in were absent. Interpreter: Python 3.11.15, already installed. No opt-in kernel test, live Agent/model/API call, installation or sync was run.

| Stage | Command / selection | Collected actual result |
| --- | --- | --- |
| Before product fix | `python3 -m unittest` selecting the new noncertificate-composition method, new decorative-comment method and extended existing empty/non-PEM/CRL-only method | Child exit 1; `Ran 3 tests in 0.023s`; `FAILED (failures=8, errors=48)`. The controlling harness expected a nonzero result and exited 0. A1 reproduced. |
| First collected full suite after product fix | `python3 -m unittest discover -s tests -p test_agent_sandbox.py -v` | Exit 1; `Ran 80 tests in 1.263s`; `FAILED (failures=2, skipped=10)`. Both failures were new ordinary-certificate validation-input assertions that added a newline absent from the original fixture. The expectation was corrected to preserve EOF bytes and compare hashes, with no product normalization. |
| Final full offline suite | `python3 -m unittest discover -s tests -p test_agent_sandbox.py -v` | Exit 0; `Ran 80 tests in 1.646s`; `OK (skipped=10)`: 70 executed tests, 10 expected `KernelTests` skips, all three new methods executed, no unexpected skips. |
| Diff whitespace | `git diff --check -- scripts/agent-sandbox tests/test_agent_sandbox.py README.md README.zh.md skills/sub-agents/references/advanced.md` | Exit 0, no output. |
| Scope inspection | `git diff` restricted to the five allowed files; read-only branch/HEAD/status checks | Intended five-file diff only. Root-owned state/statistics/adjudication/evidence/reports were already dirty/untracked at preflight and were not modified by this dispatch. No Git writes. |

An earlier identical full-suite invocation returned a running exec session before its captured output was available. Its output was not retrieved and no result is claimed for it; no `write_stdin` or process-control operation was used. The two fully collected full-suite outcomes above are the evidence for this fix.

New/extended bounded assertions include:

- Ordinary and genuine AUX-bearing trusted certificates with CSR/longer-label blocks before, after, repeated among CRLs, and in an ordinary+trusted composition; original file bytes and selected path remain intact.
- Decorative `#` comments containing ordinary/trusted delimiter spelling and non-ASCII surrounding decorative text before/after/between recognized blocks.
- Empty/non-PEM/CRL-only, each synthetic noncertificate-only input, comment-only and combined CSR/comment/CRL-only inputs all fail with `no certificate blocks`.
- Leading/trailing space, tab, vertical tab and form feed on supported BEGIN/END markers, truncated markers and trailing text fail with the existing malformed-delimiter reason, both alone and following a valid certificate/CRL companion.
- Inside an active ordinary/trusted block, unknown PEM/comment text reaches the validation input unchanged apart from the existing supported trusted-marker adaptation; non-ASCII active-block text fails rather than being ignored.
- All existing malformed/truncated/nested/orphan/mismatched and invalid base64/non-X.509/non-ASCII companion tests still execute and pass in both certificate orders/forms with and without CRLs.

These results establish wrapper setup behavior and offline regressions. They do not measure native acceptance of CSR compositions or establish current changed-source kernel/native startup success.

## Current source fingerprints

These SHA-256 values identify the locally tested five-file target; root must independently collect fresh affected-path evidence for the changed wrapper.

| File | SHA-256 |
| --- | --- |
| `scripts/agent-sandbox` | `2fc5c03e7ed069e032860c6e0c4f71be9b39bb702bcf9d08bd9d97298bd23e04` |
| `tests/test_agent_sandbox.py` | `26fa402b7fb7e01442cbd43544f83bb5a892cceef9b31d7358b9e6353bac2fdf` |
| `README.md` | `66bd5be62f3c0e860007de335e36eb4fb5f910818703b4a514a09a446cca124e` |
| `README.zh.md` | `9e086ea41b835b6417b1a61b23ce04746d071d2fe48a57741f550e3e28460180` |
| `skills/sub-agents/references/advanced.md` | `18d9f258bd3791e55b8c53e5e229de73d4ad0a50f4cae0cc25d67eead66067ee` |

## Classified residual risks and uncovered areas

| Risk / uncovered area | Classification | Owner / destination |
| --- | --- | --- |
| A1 false certificate-prefix/comment classification and strict supported-marker regression | fixed in current slice (local offline evidence; required root validation/re-review remains pending) | Root controller; aggregate re-review and adjudication. |
| Full native parser/algorithm/AUX-policy equivalence, including unmeasured native acceptance of CSR compositions and future version semantics | assigned to later work unit | Runtime-upgrade owner/root; existing runtime-upgrade boundary-validation process and final closeout risk table. No native CSR-composition success claim is made. |
| System PEM may omit keychain-only roots; parse-valid roots may not trust the endpoint | assigned to later work unit | Affected deployment/caller owner; explicit permitted bundle and post-deployment trust verification, existing documentation and root closeout. |
| Original CA file/path stability after setup | assigned to later work unit | Caller controlling input stability; existing no-external-replacement contract and root closeout. No snapshot or extra write restriction is introduced. |
| Exact blocked macOS trust-service operation remains unmeasured | assigned to later work unit | Root/maintainer; separately scoped service diagnosis and root closeout. No service-causality claim. |
| Original caller task and large business deny graph have not been reproduced | assigned to later work unit | Original caller/controller; separately authorized post-deployment task restoration/verification. No business material was read or restored. |

Fresh current-wrapper kernel/native evidence and independent dual aggregate re-review are required current-gate work owned by root, not waived or deferred residual risks. Merge/live deployment remain separate user-authorized actions. No new unclassified risk or blocking scope question was found by this bounded fix.

## Completion and next entry point

Local A1 implementation, requested bounded regressions, matching doc clarification and full offline sandbox suite are complete. Aggregate gate remains open. Next Gate Order entry: **re-review**, with root collecting fresh current-source affected-path evidence and routing the two independent aggregate re-reviews, preserving prior test/live successes and failure records. Root alone adjudicates final statuses and advances downstream gates.
