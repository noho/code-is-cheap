# Goal confirmation: simplify ordinary sub-agent calls

- Work unit: sub-agents-defaults
- Confirmed: user accepted the proposed simplification and explicitly removed runtime/provider/model self-reporting, then requested Gateflow on the current branch and current PR.
- Branch: feat/sub-agent-result-collection; PR: #50, open. Starting head: 8aadd980b4b8606ef44f06bc5375b13233dbdc02. Clean worktree verified.
- This is a continuation of the existing PR, not a new branch or replacement PR. At the draft PR gate reuse #50 and convert it to draft; the user retains manual merge.

## Goal and motivation

Make ordinary external sub-agent calls require only runner/provider selection, explicit cwd and sufficient task context. Caller waits for actual completion, reads the final answer and uses task artifacts by the paths in that answer. Remove universal audit ceremony that duplicates runner work.

## Confirmed behavior

- Direct runner calls are the default; standalone preflight is optional early setup/diagnostic convenience.
- Runner retains automatic setup/exit/terminal/log checks and automatic private logs / Claude instance identity.
- Natural-language tasks are accepted without fixed Goal/Non-goals/Stop condition headings, N/A entries, caller-generated labels or runtime/provider/model self-report.
- Canary and --artifact checks are opt-in; file deliverables normally appear by path in the final answer. Do not force an additional report to describe existing source edits.
- Default caller consumes status/final answer, including reported unfinished items and result-impacting problems. Ordinary tool failures are retained, not automatic Agent failure or a mandatory per-event adjudication document.
- Fixed adjudication YAML is not required for ordinary calls; explicit project review/audit/workflow requirements remain authoritative.
- User subsequently approved retaining runtime token usage in the compact report and recording runner wall-clock duration, so callers need not parse logs for statistics. Absent runtime metrics stay unavailable, never estimated.
- Preserve independent prompt context, managed process exit evidence, authorization and concurrent write boundaries, persistence/provider behavior, and optional macOS deny-list isolation.

## Success signals

Both runtimes accept a plain task with no preflight/canary/artifact/custom instance/output path and return the collected final answer with accessible private logs. Optional preflight accepts the same plain task, generates identity, does not create or pass canary unless requested, and does not require the other runtime to be installed. Explicit checks still fail clearly when unmet; generated isolated invocation is identical to the validated invocation and does not relax its write/read boundary.

The report exposes measured wall_clock_seconds and runtime-reported usage; optional native timing/cost/modelUsage fields remain runtime_metrics, not normalized or estimated.

## Direct evidence

- scripts/claude-agent-run already generates UUID/default instance and validates provider/cwd/prompt/output/launcher.
- scripts/codex-agent-run already validates provider/cwd/output/launcher and automatically handles non-Git workspaces.
- Both runners already collect logs privately when --output/--stderr are omitted and return the compact result.
- scripts/sub-agent-preflight currently mandates label, both catalogs, fixed headings, fresh canary and a self-report line.
- skills/sub-agents/SKILL.md currently mandates preflight, verification canaries, extra report conventions and fixed YAML regardless of ordinary task needs.

## Non-goals / boundaries

No new mid-run channel, scheduler, runtime, provider, automatic business acceptance or content-based artifact path extraction. No compatibility/migration work, live sync, API key/config changes, other-project operations or merge. No change to other workflow/review skills; their explicit audit requirements still apply when invoked, including this Gateflow run. Existing checks only become optional where the caller previously had to opt into or unnecessarily repeat them; configured checks and mandatory OS isolation are not silently bypassed.

## Scope

sub-agent-preflight; small runner setup/help/timing changes and result adapter statistics; sub-agents SKILL and its advanced reference; README English/Chinese; relevant runner/preflight tests; Gateflow/review evidence. agent-sandbox is a validation dependency, not a planned redesign.

## Decision

Goal confirmed from the user's explicit acceptance. No blocking open question. One behavior slice is sufficient. Next gate: plan.
