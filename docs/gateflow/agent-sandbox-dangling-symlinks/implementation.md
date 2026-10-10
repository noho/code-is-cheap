# Implementation: agent-sandbox dangling symlinks — S1

- Gate: implementation; work unit: `agent-sandbox-dangling-symlinks`.
- Scope: approved S1, safely retain dangling targets with a verified existing ancestor.
- Prerequisite: accepted plan commit `44d652ac8459ae4fa74c977b931fbe905bc6da57`; base main `d51765b`; branch `fix/agent-sandbox-dangling-symlinks`.
- Status: implementation and required validation complete, ready for controller code review/adjudication. This is not review-loop, PR, work-unit or live-deployment completion.
- Artifact: `docs/gateflow/agent-sandbox-dangling-symlinks/implementation.md`.

## Changed files / ownership

- `scripts/agent-sandbox`: private stdlib wrapper, contextual setup errors and expansion logs, existing scan graph with missing-target ancestors, metadata return/manifest, two-pass actual verification.
- `tests/test_agent_sandbox.py`: focused setup/verification state combinations, local dangling kernel fixture and two real srt materialization controls; optional trusted-parent evidence retention.
- `README.md`, `README.zh.md`, `skills/sub-agents/references/advanced.md`: supported dangling handling, conservative ancestor/cascade restrictions, capability and canonicalization limits, required actual proof.
- `plan.md`: only the two probe-location references in section 3 were corrected to the actual directory and `/private/tmp/dangling-plan-fix-0c4fzu_t/stdlib-contract-probe.json`; no accepted design contract changed.
- Existing controller-owned dirty `state.md` was present at entry and was not edited by this implementation Agent. Old review/evidence artifacts were not changed.

No staging, commits, push, review dispatch, PR operation, merge, live sync, environment installation, native-provider/runtime test or original caller task was performed. All new scratch/evidence is in newly created `/private/tmp` fixtures, principally `/private/tmp/dangling-s1-PleSSk/`. HOME/config/runner/key inputs are synthetic fixture inputs; no real key configuration was used for testing.

## Decisions / implementation contract

1. `_resolve_deny_target` retains `entry.resolve(strict=True)` unchanged on success. Only an OSError with exact `errno.ENOENT` calls `os.path.realpath(strict=os.path.ALLOW_MISSING)`. No custom resolver, component restrictions, version selection, strict=False fallback or installation. Missing capability produces a located failure retaining the strict error/filename.
2. Declaration resolution and scan/readlink/lstat/resolution failures include declared entry, actual entry/link, available raw/canonical target and ancestor, plus cause type/errno/filename. Non-ENOENT failures and loops remain failures. Existing hardlink and expanded special-target refusal remains effective.
3. Final missing classification uses lstat, retains exact missing target and nearest existing non-root directory ancestor in both denyRead/denyWrite, and registers first-origin metadata. The ancestor enters the same pending/visited graph. Every missing-aware result is logged before dedup or conflict checks, including existing reentry and each cascade with `discovered_in`.
4. A retains existing strict `plain/../good` canonicalization. B logs and conservatively denies existing reentry after missing components and `..`, including covered/deduplicated results. C propagates later ENOTDIR with context. No raw-path reachability or kernel-identical error precedence is promised.
5. `load_denies` returns `(denies, missing_targets)`; main fixes the full policy and private manifest. Existing setup input/output/write/result checks consume the full denial set. The multi-link conflict fixture proves both origins are reported before the specific denied prompt path, with no srt/runner launch.
6. Verifier validates lexical canonical metadata and component-based ancestor coverage, then queries and actually reads every existing entry first. Only query=True plus actual PermissionError enters `verified_existing`. Registered missing entries still require query=True and actual access; ENOENT is tolerated only after exact ancestor proof. Non-ENOENT, unexpected existing disappearance, query failure or successful forbidden reads prevent exec. Allowed probe actual read/write success remains required before a single fixed exec.
7. MiMo 2/3 rejected scope remains intact: no expected-kind, O_NOFOLLOW, fstat/identity, external mutation support or full-chain role origin mapping was added. Launcher, srt package, runners, lifecycle and result collection were not modified.

## Validation: exact commands and actual results

Environment: macOS 26.6.2 (25G83), arm64, Python 3.11.15 with ALLOW_MISSING, existing srt 0.0.79. Kernel invocations used `exec_command(sandbox_permissions="require_escalated")` to actually launch outside the parent sandbox; approval succeeded. All kernel cases ran; no mock or skip substituted for kernel execution.

Executed from repository cwd:

```sh
TMPDIR=/tmp/dangling-s1-PleSSk/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_agent_sandbox.py' > /private/tmp/dangling-s1-PleSSk/focused-final.stdout 2> /private/tmp/dangling-s1-PleSSk/focused-final.stderr
TMPDIR=/private/tmp/dangling-s1-PleSSk/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_agent_sandbox_launch.py'
TMPDIR=/private/tmp/dangling-s1-PleSSk/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_sub_agent_preflight.py'
TMPDIR=/tmp/dangling-s1-PleSSk/tmp PYTHONDONTWRITEBYTECODE=1 AGENT_SANDBOX_EVIDENCE_DIR=/private/tmp/dangling-s1-PleSSk/kernel-final-evidence AGENT_SANDBOX_KERNEL_TESTS=1 SRT_TEST_BIN=/Users/leo/.local/bin/srt python3 -m unittest discover -s tests -p 'test_agent_sandbox.py' > /private/tmp/dangling-s1-PleSSk/kernel-final.stdout 2> /private/tmp/dangling-s1-PleSSk/kernel-final.stderr
git diff --check
```

| Check | Actual exit | Total / passed / skipped | Result |
| --- | --- | --- | --- |
| Focused sandbox | 0 | 52 / 43 / 9 | Kernel opt-in skips reported honestly |
| Focused launcher | 0 | 6 / 5 / 1 | Existing opt-in kernel skip |
| Focused preflight | 0 | 13 / 13 / 0 | Pass |
| Full sandbox with kernel opt-in | 0 | 52 / 52 / 0 | All 9 kernel cases actually ran; 12.478 seconds |
| git diff --check | 0 | n/a | Pass |

Exact command/result index: `/private/tmp/dangling-s1-PleSSk/validation-commands.json`; focused raw stderr and trusted-tool summary transcriptions are in that directory. Kernel stdout/stderr are retained both at suite level and as per-fixture `raw.json` containing exact argv/exit/stdout/stderr. No `test_agent_sandbox_runtimes.py` or real provider task was run.

### Recovered test issues, retained failures

The first kernel run actually exited 1: 50 cases, zero skips, one error and one failure (`kernel-1.stderr`; evidence in `kernel-evidence/`). The new dangling case assumed a source profile always existed; the unchanged launcher retains only `seatbelt.sb` when there is no compaction. The test now verifies both first hashes against the effective profile and their equality in that documented case, retaining source/effective comparisons when source exists.

The original profile-hardlink/hash fixture failed at hardlink creation when TMPDIR used the canonical `/private/tmp/dangling-s1-PleSSk/tmp` spelling. A targeted outer execution with the `/tmp/dangling-s1-PleSSk/tmp` spelling of the same physical new fixture passed its original assertions unchanged (exit 0, one case, zero skips):

```sh
TMPDIR=/tmp/dangling-s1-PleSSk/tmp PYTHONDONTWRITEBYTECODE=1 AGENT_SANDBOX_EVIDENCE_DIR=/private/tmp/dangling-s1-PleSSk/kernel-path-probe AGENT_SANDBOX_KERNEL_TESTS=1 SRT_TEST_BIN=/Users/leo/.local/bin/srt python3 -m unittest discover -s tests -p 'test_agent_sandbox.py' -k profile_hardlink > /private/tmp/dangling-s1-PleSSk/kernel-path-probe.stdout 2> /private/tmp/dangling-s1-PleSSk/kernel-path-probe.stderr
```

The final full command uses that spelling and passes all original hardlink/hash assertions. This harness/path sensitivity is recorded, not converted into a product-policy change or a claim of uniform hardlink behavior across TMPDIR spellings. Initial focused diagnostics also corrected nondeterministic walk-order assumptions to assert the actual discovered local origin, and an overly broad `state=` substring match to the exact state-log prefix. No boundary assertion was weakened or skipped.

## Actual kernel boundary evidence / first adapter hashes

Trusted-parent evidence index: `/private/tmp/dangling-s1-PleSSk/evidence-index.json`. Every first adapter record was parsed from the parent's captured stderr before possible child duplicates. Source/effective retained-byte matches are in this index; the original intentional post-load profile-mutation test has mismatches by design and confirms the loaded kernel policy still denies reads.

| Fixture evidence directory under `kernel-final-evidence/` | First profile SHA256 | First source SHA256 |
| --- | --- | --- |
| `test_dangling_targets_with_verified_ancestor_boundary-mzkg0iu9` | `6bce7ef2d9bdccfc26b659db359800fe1dea0af2d10315299551231dfe58923a` | `6bce7ef2d9bdccfc26b659db359800fe1dea0af2d10315299551231dfe58923a` |
| `test_missing_query_and_ENOENT_are_ambiguous_under_allow_default-j6h774ak` | `d669401822c5507e08469c5781b602c7caec74ab164de8ac61dc54a42addbfcf` | `d669401822c5507e08469c5781b602c7caec74ab164de8ac61dc54a42addbfcf` |
| `test_verified_ancestor_policy_denies_after_fixture_materialization-oox_jff8` | `6fde625bf2fcd5fec50d59c767154ce12e38db33c16a8bc59d457db7eb3fac89` | `6fde625bf2fcd5fec50d59c767154ce12e38db33c16a8bc59d457db7eb3fac89` |
| `test_large_deny_list_verifies_every_entry_before_runner-wjq18cyo` | `ba6452701dcee7b00c802c01dc43c3ec0c1e404406adf44d008642947e1dc86a` | `bad6eb0c0743dc1eea5d411e777000cb0c67f6942f86d8973b68848d6b8d8d82` |

These four fixture pairs match retained bytes. The large-list composition remains exactly 2 original declared denies + 4106 files = **4108**; its effective/source profiles are 690704/2167580 bytes and the source exceeds SC_ARG_MAX. New dangling inputs are local to their own case.

- Dangling case: exit 0; verified/start stderr precedes the synthetic runner marker. Manifest, srt settings and actual SBPL retain declared denies, missing target, ancestor, valid external directory/file and secondary target. Metadata is exact; all three absolute/relative/chain origins are logged.
- Ancestor, existing sentinel and effective external target queries are 1. Actual ancestor listdir, sentinel/direct valid-target reads and dangling alias reads are PermissionError. Sentinel writes and creating `ancestor/new-entry` are PermissionError. Missing direct open is FileNotFoundError; it is not treated as independent proof.
- Original direct/symlink/dir_alias/dotdot/history/data_alias/tmp_alias/case-alias and hardlink attempts are refused. Recursive rg and nested sandbox contain no forbidden content. Allowed input is readable; cwd output, requested sink and heredoc succeed. Protected/outside/sink-neighbor/task/profile writes remain PermissionError.
- Separate read-only and Claude original-denyWrite cases pass unchanged: read-only gains no cwd write; Claude's original denial wins while cwd/sink writes remain allowed.
- Real srt allow-default control: before materialization, missing directory/file query=1 and actual ENOENT while existing ancestor is query=0/readable; after the fixture parent creates the target, query=0/read succeeds. This demonstrates the ambiguity directly.
- Real srt ancestor-deny control: existing ancestor and sentinel query=1/actual PermissionError before and after materialization. Missing target starts at query=1/ENOENT; after the parent handshake creates the directory/file, listdir/open remain PermissionError. Outside-ancestor allowed reads and writes succeed in both snapshots. Handshake/subprocess deadline is 45 seconds without sleep-based evidence; it proves fixed-policy coverage, not external mutation support.

## Diagnostics, docs and residual risks

README EN/ZH and advanced reference now distinguish declared missing paths from scanned dangling targets, retain valid strict semantics, describe existing reentry/cascades and sibling breadth, explain capability failure/non-ENOENT failure, and require verified ancestor plus allowed actual probes. Existing known-copy, credential, external mutation, --check, macOS/srt and no-fallback exclusions remain.

| Risk / uncovered area | Classification | Owner / destination / disposition |
| --- | --- | --- |
| Unlocated dangling ENOENT, swallowed non-ENOENT, missing-only/query-only false proof | fixed in current slice | Implementation Agent; source + focused/kernel evidence above; controller owns code review acceptance |
| Missing ALLOW_MISSING on some Python 3.11+ environments | fixed in current slice | Implementation Agent; located failure injection and docs, valid strict path unaffected; no installation/compatibility promise |
| Canonicalization/raw reachability/error precedence differences | fixed in current slice | Implementation Agent; A/B/C assertions, existing-reentry logs and docs define supported behavior |
| Broad ancestor/cascade denial, sibling scanning and required-input conflicts | fixed in current slice | Implementation Agent; exact nearest ancestor, graph traversal, source logs, root/scan/conflict refusal and tests; arbitrary-directory startup is not promised |
| TMPDIR-spelling sensitivity of original synthetic profile-hardlink fixture | assigned to later work unit | Maintainer/controller; separately scoped harness/platform analysis if uniform behavior is needed. Nonblocking here: all original assertions pass under `/tmp` spelling of the new physical fixture; loaded-policy/hash limitation remains documented |
| Unsandboxed concurrent replacement, copies/snapshot guarantees, real business-directory ancestry, other platforms | assigned to later work unit | Caller/maintainer; separately confirmed work unit or caller revalidation, as already excluded by goal/plan |
| Merge/live deployment and live caller validation | requiring new issue or explicit user decision | Controller/caller; after source reviews/PR and separate deployment authorization. This Agent did not inspect or change live entry |

Blocking problems: **none for S1 implementation/required validation**. No unclassified risk. Next owner/entry point: controller code review and adjudication; accepted-slice commit and later gates remain controller work.
