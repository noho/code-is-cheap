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
state, and are protected against Agent writes/moves by the generated policy.
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
