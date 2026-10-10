# S1 implementation: agent-sandbox-workspace-routing

- Gate: implementation, S1 only.
- Artifact: `docs/gateflow/agent-sandbox-workspace-routing/implementation.md`.
- Worktree: `/private/tmp/code-is-cheap-workspace-routing`.
- Confirmed branch: `fix/agent-sandbox-workspace-routing`.
- Entry and exit HEAD: `1e6693b06717a70a018355e93bf93164a777259d`, subject `gateflow: accept plan for agent-sandbox-workspace-routing`.
- Binding decisions read: repository `AGENTS.md`, `goal.md`, `plan.md`, `plan-adjudication.md`, and the gateflow skill. Accepted plan SHA-256: `2953a6f37651cf0b1b83c2c3c99bab6a546e82890a3b9fd7b7681e28cff9c47d`. These are requirements, not correctness evidence.
- Status: S1 code, documentation and offline implementation validation complete; **S1 acceptance remains incomplete**, pending root-owned kernel/live validation and independent code review/adjudication. No Git mutation, delegation, installation, sync, publishing or live/model/API probe was performed.
- Entry status had only root-owned `docs/gateflow/agent-sandbox-workspace-routing/state.md` dirty. That file was not read or edited by this dispatch. Goal/plan/adjudication/statistics/root evidence were not edited; peer reports/transcripts, root private diagnosis, original caller/business material and user config/auth/key contents were not accessed.

## Actual changes and behavior

Exactly the five allowed product/test/docs files changed, plus this implementation artifact:

| File | Actual diff versus entry HEAD | Change |
| --- | --- | --- |
| `scripts/agent-sandbox` | +118 / -1 | Add `DEFAULT_CODEX_CA_CERTIFICATE` and shared `prepare_codex_ca`; two Codex call sites after route validation; move the single private environment copy before `--check`. |
| `tests/test_agent_sandbox.py` | +532 / -1 | Fixed public ordinary/trusted/CRL bytes, 24 new offline test methods and one new opt-in kernel test; deterministic explicit CA env in existing kernel setup. All 52 original test methods are preserved. |
| `README.md` | +24 / -0 | Explicit CA behavior, one export example, setup/keychain/parser limits. |
| `README.zh.md` | +19 / -0 | Matching Chinese CA behavior/example/limits. |
| `skills/sub-agents/references/advanced.md` | +19 / -0 | Matching Agent guidance in the existing task boundary section. |
| `docs/gateflow/agent-sandbox-workspace-routing/implementation.md` | New artifact | This bounded implementation handoff; no lifecycle/state transition is written. |

The helper applies only to existing isolated Codex HTTPS. Exact nonempty CODEX then exact nonempty SSL then system-default selection retains empty fallback and literal whitespace. HTTP and Claude do not acquire a CA requirement or mutate CA env. Relative inputs use envelope cwd; literal `~` stays literal; strict canonicalization and the complete existing deny expansion precede any CA open. A selected failure never falls through to SSL/default.

Readable regular-file input uses lstat, `O_RDONLY | O_NONBLOCK | O_NOFOLLOW | O_CLOEXEC`, fstat and one descriptor-backed read, with cleanup. Missing, denied, special, unreadable/cyclic/NUL/unrepresentable and malformed input failures carry source/declared/canonical context where available; they retain exit-1 setup failure through the existing handler. Native cause class/errno and bounded parse reasons replace payload disclosure. Environment assignment occurs only after successful validation.

A local delimiter pairing scan accounts for every ordinary/trusted certificate, rejects malformed/nested/orphan/mismatched/incomplete companions, and syntax-parses each separately with a fresh stdlib SSLContext. Trusted labels change only in the in-memory validation string; base64/AUX and the original file stay unchanged. Genuine X509 CRLs are ignored and never sent to the validator; CRL-only input fails. Syntax validation does not establish endpoint trust or all native algorithm/AUX policy behavior.

Both check and launch use the same selected input. Successful check stdout remains exactly `setup_status=ok\n`; no setup failure reaches final envelope exec. Unit launch assertions cover selected child env, route/model/auth flags, full-access/no-persist command, domains, strict network/socket flags, denies, retained write grants and protected files. All 18 existing wrapper functions other than `main` were source-compared unchanged; the only added function is `prepare_codex_ca`. No collector, proof field, unsupported-notice classifier, runner/launcher/adapter/preflight/schema/installer change was added. Root's rejected notice-classifier request remains rejected.

## Public fixtures and test boundaries

The authorized public files were available and embedded as fixed small bytes, without any private key, generated certificate, runtime crypto dependency or whole OS bundle fixture:

| Embedded constant / authorized source | SHA-256 |
| --- | --- |
| `PUBLIC_CA`; `/private/tmp/workspace-routing-gateflow-vVRPod/public-ca-test.pem` | `6203a5b68239d9625c45da5b986aa05cad1e16e5644c9e325c88b93517be5627` |
| `PUBLIC_TRUSTED_CA`; `/private/tmp/workspace-routing-gateflow-vVRPod/public-trusted-ca-test.pem` | `6c35f5365ad5d6de53d8445cfcad2c93daad56b49fa1611d2811ec00a34705ce` |
| `PUBLIC_CRL`; `/private/tmp/workspace-routing-gateflow-vVRPod/public-crl-test.pem` | `172a97207d979f7c3bd568e22878a981481ff2eac2f622bc4d7563ae506438ed` |

CRL source cited in the test: https://raw.githubusercontent.com/python/cpython/3.11/Lib/test/certdata/revocation.crl . Real stdlib parser tests accept the ordinary and genuine AUX-bearing trusted bytes; a payload-length/prefix assertion also distinguishes actual AUX from mere relabeling. New case files and mocked main state/check directories live inside private TemporaryDirectory roots. Helper env mappings are explicit; mocked main uses a separate synthetic env object and asserts it remains unchanged. No parent environment contents are mutated.

The new `KernelTests.test_codex_ca_reaches_native_cli` is **defined but unexecuted here**. It uses the real wrapper/srt/repository runner/launcher and a native test stub, `--detail`, fresh sinks, existing `profile_fields`/`retain_kernel_evidence`, and no fabricated model events. The automatic-default expectation reads and hashes the current public default only at kernel-test runtime. The explicit empty-CODEX/nonempty-SSL alias case uses the fixed public CA bytes/hash. Assertions require the native canonical path/read, verification-before-runner, first adapter profile/source hashes, unchanged policy grants/flags and no `com.apple.trustd.agent` grant. Test-only expectation env is not a product proof field.

## Commands, real results and retained failures

Preflight/read/hash/inspection commands used structured `exec_command` only. `git branch --show-current`, `git status --short`, `git rev-parse HEAD` and `git show --no-patch --format=%s HEAD` all exited 0 with the branch/checkpoint above. Named binding inputs and all three public fixtures were read successfully (exit 0). No peer reports or private diagnosis were followed.

Offline command for the direct runs:

```bash
env -u AGENT_SANDBOX_KERNEL_TESTS PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_agent_sandbox.py
```

| Attempt | Actual result | Disposition |
| --- | --- | --- |
| Initial run with 1-second tool yield | Partial failure output only; returned session 22309. Final count/exit was not retrieved. | Not counted as a completed validation; no `write_stdin`, process inspection or stop used. |
| First completed run | Exit 1; Ran 76 in 1.204s; failures=8, errors=2, skipped=10. | New harness defects: absolute-runner mock lookup, stream context mock, and newline expectation. Fixed, then rerun. |
| Second completed run | Exit 1; Ran 76 in 1.197s; errors=4, skipped=10. | New harness mkdtemp positional-argument mock defect. Fixed, then rerun. |
| Third completed run | Exit 0; Ran 76 in 1.226s; OK (skipped=10). | 66 executed successfully; kernel methods skipped. |
| Fourth completed run | Exit 0; Ran 76 in 1.653s; OK (skipped=10). | Same executed/skip count after selected-SSL failure coverage and local error wrapping. |
| Fifth completed run | Exit 0; Ran 77 in 2.588s; OK (skipped=10). | Added bounded-parser-diagnostic offline test; 67 executed successfully. |
| Final retained run | Exit 0; Ran 77 in 1.788s; OK (skipped=10). | 67 executed successfully, 10 opt-in kernel skips, no unexpected new offline skips. |

Final retained run launched the same `python3 -m unittest discover -s tests -p test_agent_sandbox.py` argv through a Python subprocess wrapper with a copied env, `AGENT_SANDBOX_KERNEL_TESTS` removed and `PYTHONDONTWRITEBYTECODE=1`. Evidence: `/private/tmp/s1-offline-validation-zzon90a8/{result.json,stdout.txt,stderr.txt}`. This is offline evidence, not kernel/live evidence. All existing offline regressions and existing Python capability rules were preserved; no capability failure was hidden or fallback introduced.

One editing helper exited 1 because nested string quoting interpreted a test-only snippet at edit time, failing at missing `TEST_CA_EXPECTED_PATH` before any CA file read or native/wrapper/kernel launch; no file mutation from that attempt. The quoting was corrected and the succeeding edit exited 0. All other editing helpers exited 0. The failed attempts above remain part of the record rather than being called pass.

`git diff --check -- scripts/agent-sandbox tests/test_agent_sandbox.py README.md README.zh.md skills/sub-agents/references/advanced.md` exited 0. Read-only AST/source checks exited 0: 52 original method bodies preserved unchanged; 77 total methods; 25 added (24 offline, 1 kernel); only the CA helper added and all 18 prior non-main functions byte-for-byte unchanged. A final six-file diff whitespace check also exited 0; the final status lists only the five product files, this new artifact and the pre-existing root-owned dirty state file. Final product hash consistency and preservation of all 52 original test bodies were rechecked (exit 0). Final hashes:

| File | SHA-256 |
| --- | --- |
| `scripts/agent-sandbox` | `f0bb921819d3a72260c7a3916d1916b2469a6064d54d3fa4190c419a1efe1d8c` |
| `tests/test_agent_sandbox.py` | `62a0a53d10670773643d5f617ea15a51b507ca8f871e4d59333edae03ae8d6a9` |
| `README.md` | `6796a65f0d5830e7f5bed54b4172be32bcf040300f702709c47c75eb2aa46e1d` |
| `README.zh.md` | `69f8df0f3e9b98a57e56652d1792ff6ab4d790a99d495d0b1757d5cd97d36181` |
| `skills/sub-agents/references/advanced.md` | `64fa7e26ebebe372d212f602ce029380860834b4feb6e740ecfd5149db8455a7` |

## Documentation decision and findings

All three required documentation surfaces were updated in S1. They agree on default, precedence, exactly-empty/literal path behavior, regular permitted inputs, ordinary/trusted certificates, ignored CRLs, located failure/no fallback, original AUX/file preservation and setup/keychain/native-parser limits. Each includes the absolute CODEX CA export example. The new 0.162.1 claim is explicitly CA-specific; adjacent whole-envelope Codex 0.161.0 wording is preserved.

F1/F2/C1/C2 binding decisions are implemented with the source/tests/docs above; independent verification/adjudication belongs to root. F3 requires root's actual live diagnostic inspection, not a product collector change. No external review finding was adjudicated by this implementer. New harness defects were fixed and verified by the completed offline runs; independent code review remains pending. No scope/fixture input blocker was found.

## Classified residual risks and uncovered areas

| Risk / area | Classification | Owner / destination |
| --- | --- | --- |
| Selected-input precedence, located setup failures, forbidden/special input reads, certificate companions, trusted AUX preservation, CRL ignore | fixed in current slice at implementation/offline level; acceptance still needs root validation/review | Root S1 validation and code-review artifact. |
| Bilingual/Agent docs, public fixture stability and CA-only version wording | fixed in current slice at implementation/offline level | Root S1 code review; current docs/test diff. |
| Native env/policy preservation and actual restored managed-auth startup are unexecuted here | Required S1 validations remain open, not deferred; requiring new issue or explicit user decision if root cannot obtain them | Root kernel/live validation and adjudication; no acceptance claim from mocks or skipped tests. |
| Exact macOS trust-service denial mechanism is unmeasured | assigned to later work unit | Maintainer/root; optional separately scoped diagnosis and final closeout risk table. |
| System PEM may omit keychain-only roots; parse-valid custom roots may not trust the endpoint | assigned to later work unit | Affected deployment/caller; explicit permitted bundle and post-deployment endpoint verification, documented here. |
| Native/OpenSSL parser, AUX-policy/algorithm differences or future native CA env semantics | assigned to later work unit | Runtime-upgrade owner/root; runtime upgrade validation and closeout. Native errors retain real logs/nonzero failure. |
| Input paths/contents may change after setup | assigned to later work unit | Caller controlling file stability; existing no-external-replacement contract and closeout. No snapshot subsystem or new write boundary. |
| Original caller command, large business deny graph and task restoration were not reproduced | assigned to later work unit | Original caller/controller; post-deployment verification/restoration. No original logs or business content used. |
| Missing validation prerequisites, auth expiry, service outage or genuine live failure, if encountered | requiring new issue or explicit user decision | Root failing gate artifact; no install, route/auth migration, TLS weakening or policy relaxation to manufacture success. |

No later approved implementation slice is asserted. Merge and live sync remain user-owned separately authorized actions.

## Completion and next entry

Implementation dispatch is complete within its ownership. Root still must run these selected kernel methods from outside its sandbox, with fresh private retained evidence as specified in the accepted plan:

- `KernelTests.test_codex_ca_reaches_native_cli` (both default and explicit SSL subcases).
- `KernelTests.test_kernel_boundary_and_write_preservation`.
- `KernelTests.test_read_only_does_not_gain_cwd_writes`.
- `KernelTests.test_claude_original_deny_write_wins_over_cwd`.

Root must compare retained profiles to the first trusted-parent hashes, then run the one fresh managed-auth synthetic HTTPS invocation and adjudicate real exit/terminal/final/diagnostic evidence exactly as the accepted plan requires. No kernel/live policy hashes or success evidence are claimed here.

Next Gate Order entry: **code review**, with root-owned S1 validation prerequisites still open. Root routes the two independent reviews, adjudicates/fixes/re-reviews and creates the accepted-slice checkpoint only after required evidence passes, then owns subsequent aggregate/PR gates. This artifact does not advance lifecycle state, accept the slice, restore the caller's business task or claim a deployed entry.
