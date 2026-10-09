# agent-sandbox large policy validation (2026-10-09)

## Scope and authorization

Maintenance of code-is-cheap after the upstream E2BIG report. No business Agent,
financial review, original dispatch command, workflow, or business output was
started or changed. The reported strategy snapshots were read only. No live sync.

## Confirmed startup chain

macOS 26.6.2, Node 25.9.0, srt Node package 0.0.79. `SC_ARG_MAX` is 1048576.
srt `dist/sandbox/macos-sandbox-utils.js` renders `env ... sandbox-exec -p
<whole SBPL> <shell> -c <inner command>` into a quoted shell command.
`dist/cli.js:437` passes it to `spawn(command, {shell:true,...})`.

A synthetic 4108-entry list, with distinct long parents/leaves, reproduced outer
exit 1 / `Error: spawn E2BIG`. A Node preload recording only size, stack and
outcome measured the shell command at 6496467 UTF-8 bytes and environment at
2838 bytes. The synchronous failing spawn was exactly cli.js:437:25. No child
or Agent started. Local evidence: `/private/tmp/agent-sandbox-e2big-repro-8171e7by/`.

File transport alone eliminated E2BIG but revealed a second native limit:
- Very long, distinct-parent stress profile (6493935 bytes): compiler SIGABRT,
  `push_jne_instr` assertion.
- Shorter 4108 distinct-parent profile: `data object length 166575 exceeds
  maximum (65535)`.
- Representative 4108-entry, 66-parent profile without compaction:
  `data object length 114695 exceeds maximum (65535)`.
- Merely compacting read/write deny rules while omitting srt's additional
  read-protection `file-write-unlink` rule also failed; all relevant deny
  operation sets must retain their coverage in bounded form.

These failed experiments are not claimed as successful kernel verification.

## Implementation and invariants

The adjacent Node adapter loads the pinned, installed srt CLI. It retains srt's
proxy setup, signal handlers, stdio, cleanup and child status handling. Its one
shell-spawn interception accepts only the canonical pinned quote format and
expected `env / sandbox-exec -p / absolute shell -c / exact inner command`
layout, without shell evaluation. Alternate launchers/layouts fail closed.

Within each top-level file deny rule, sibling literal/subpath filters are
replaced by exact regex unions, each at most 900 encoded SBPL string bytes.
The unions escape literal names, distinguish exact paths from descendants,
include newline descendants, and do not merge rules or alter allows, operation
sets, rule order, other filters or logging. Unmatched/small/oversized individual
filters are retained. There is no deny-list truncation or widening of write
permissions. Both the source and effective profiles are retained in fresh private
state; the generated policy denies direct-path writes/moves. See the hard-link
evidence limitation and pre-spawn hashes below.
The effective profile is loaded with `sandbox-exec -f`, removing the policy from
spawn argv. Every original manifest deny still goes through Seatbelt queries
and actual open denial before runner startup.

## Actual results

- Synthetic 4108 entries across 66 parents: complete envelope exit 0; every
  manifest entry verified before fake runner startup. Allowed input/output
  worked; recursive rg returned no forbidden content; outside/protected/profile
  writes failed. Source profile exceeded ARG_MAX; effective policy was smaller.
- Native original vs compacted profile comparison passed for 145 directories:
  Unicode, quote, backslash, regex metacharacters, newline names/descendants,
  case aliases, near-miss siblings, writes and renames. Actual kernel-backed
  access results were identical; forbidden reads/writes/renames were denied.
- Latest reported snapshot: all 4108 denies preserved. Source SBPL 2001632 bytes,
  effective SBPL 715785 bytes. Non-Agent metadata probe exit 0, `sandbox_check`
  denied 4108/4108 and actual read-only open denied 4108/4108. No business contents
  were read. Local evidence: `/private/tmp/agent-sandbox-reported-verified.tt2yodhg/`.
- Real Seatbelt suite: 23 tests passed in 9.169 seconds, including native Codex
  and Claude tools against deterministic local API endpoints with synthetic
  credentials. The captured requests contained allowed canary/image data and
  tool-denial output, not forbidden text/image bytes. Codex escalation could not
  read denied input; original rules still blocked writes; Claude bypass mode
  and absence of MCP were confirmed. Evidence:
  `/private/tmp/agent-sandbox-e2big-runtime-evidence/`.

Reproduce synthetic/native suite (outside controller sandbox):

```sh
AGENT_SANDBOX_KERNEL_TESTS=1 SRT_TEST_BIN=/path/to/srt \
  python3 -m unittest discover -s tests -p 'test_agent_sandbox*.py'
python3 -m unittest discover -s tests
```

## Review fix and final verification

The accepted preflight finding was fixed: `--check` and real launch now share a
non-spawning Node-package validator, checking canonical CLI path, pinned
package/name/version/bin layout and readable regular required modules. A fake
standalone CLI that prints 0.0.79, a mismatched package and missing modules are
rejected with a reinstall instruction before `setup_status=ok`.

After this fix the complete native suite passed **25 tests in 11.852 seconds**.
The earlier 23-test result above records the original reviewed snapshot.

The first historical reported policy also compiled with all 4476 entries:
source 2153855 bytes, effective 770148 bytes. All 4476 kernel queries denied;
4111 actual opens denied, 365 returned ENOENT because historical paths are now
missing. Those missing entries are not claimed as complete open verification.
No content read or business Agent start occurred. Local evidence:
`/private/tmp/agent-sandbox-first-verified.5qrn3u4b/`.

## Limits and deployment

macOS only, installed srt 0.0.79 Node package CLI required. Native policy compiler
limits are not removed universally: lists with thousands of unrelated parents,
very long names or insufficient grouping can still fail before verification.
Failure remains explicit and does not start an Agent, weaken denies or trigger
an unsandboxed fallback. Caller-defined known-copy/path boundaries remain as
before; no content-based isolation is claimed.

The normal install/sync path deploys the adjacent adapter. Caller invocation,
preflight, provider routing, lifecycle collection and result acceptance are
unchanged. The skill now describes startup failure classification and retained
policy evidence. Sync to live is a separate user action after review/merge.

## MiMo review adjudication

The preflight ordering finding was accepted: structural validation now precedes
`srt --version`, and an ordinary (non-kernel-gated) marker fixture proves an
unsupported standalone candidate is never executed.

The hard-link concern was confirmed with a synthetic native probe: both retained
policy files could be linked into cwd, chmodded and written through the alias.
This changes evidence files after loading, not the already loaded kernel policy.
The minimal remedy is explicit provenance: the adapter hashes the exact source
and effective bytes before spawn and prints both SHA-256 values to envelope
stderr. A caller must collect that stream through a trusted parent pipe and
compare retained files before auditing; Agent-writable logs/files alone are not
trusted evidence. This does not claim inode-level immutability or broaden writes.
A native regression covers both alias mutations, hash mismatch detection and
continued enforcement of the original loaded read boundary.

After MiMo adjudication, ordinary suite: **93 tests, OK, 9 explicit opt-in skips**
(35.883 seconds). Native Seatbelt plus Codex/Claude local-mock suite:
**26 tests, all passed** (15.844 seconds). These supersede earlier counts for
current HEAD; earlier results above retain their original snapshot identities.

Final MiMo closure identified a shared-stderr parsing ambiguity. The controller
accepted it: README/skill explicitly select the first pre-spawn adapter record,
ignore later child-authored duplicates, and forbid last-wins parsing. Tests now
use that rule; an ordinary duplicate-record fixture and a native post-mutation
forged-hash line prove the true digest cannot be replaced. The ordinary marker
fixture also pins AGENT_TOOLS_FILE to repository source for clean-machine use.
Only docs/tests changed in this closure; production code remains ac5b244.

Final closure verification: **94 ordinary tests, OK, 9 opt-in skips** (33.354s);
**27 native tests, all passed** (12.423s), including the forged post-startup hash
record scenario. Full adjudication and review-attempt lifecycle records:
[controller closeout](agent-sandbox-e2big-review-closeout-20261009.md).
