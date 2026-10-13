# Goal confirmation v2: terminal-driven completion for both runners

Gate/work unit: goal confirmation / codex-recovered-timeout-demand. Branch remains fix/codex-recovered-timeout-demand; base is 62c3b26adeb994e81043d7b1afbcd4c6eb8974ae. User explicitly replaced and confirmed the previous allowlist-only contract. This file is the authoritative binding goal; v1 snapshots remain under superseded/. No new goal confirmation is needed unless an uncovered material tradeoff changes this contract.

## Goal and success contract

Determine normal call completion from each runtime's native final execution state, not an enumeration of intermediate error text. Native process exit 0, necessary postprocessing exit 0, one valid successful terminal in the same execution, a complete nonempty final answer, intact log structure, and passing explicitly selected mechanical checks imply runner exit 0. Codex terminal is turn.completed; Claude Code uses its own result protocol. Intermediate error/timeout/demand/reconnect diagnostics must remain visible and may set needs_review even when their wording is unfamiliar. No intermediate wording allowlist may be required for acceptance.

Native/postprocessing failure, explicit failure terminal, missing/conflicting/invalid terminal, damaged logs, missing/incomplete final, or selected check failure must still yield nonzero. A success-labeled event does not override those failures. Native refusal/truncation/noncompletion fields must not be masked by a nominal success subtype. result_status remains not_assessed: exit 0 is call completion, never business correctness. Final text and diagnostic evidence remain available for caller judgment.

## Code and protocol evidence

- Both public runners already preserve native exits and delegate collection to scripts/agent-run-result.py; Codex also supplies its precollection last-message postprocessing exit. No automatic retry is performed here.
- Collector currently immediately makes unknown top-level error events fatal in both codex() and claude(). Only narrowly recognized Codex text reaches its recovery exception. This is the source of the wording dependency to remove.
- Strict JSON/UTF-8/event parsing, duplicate-terminal detection, selected checks and process error handling already exist and must remain decisive. Current Codex completed/final validity bookkeeping is only enforced for the narrow notice exception; the plan must make necessary final-state validation explicit without depending on notice words.
- Native Codex 0.162.1 schema snapshot defines thread.started/turn.started, turn.completed/turn.failed, item.completed with agent_message id/text, and top-level error with message. It does not expose a separate refusal/finish-reason field on completed agent messages. Native schema comments call top-level errors unrecoverable, but the read-only original log directly proves successful later turn completion after such events; prose labels do not supersede observed final-state recovery. Protocol snapshots: evidence/protocol/codex-native-events.rs and codex-items.ts.
- Claude Code 2.1.296 real stream records result/subtype/is_error/result plus stop_reason and terminal_reason. One actual old-plan review returned subtype=success/is_error=false/terminal_reason=completed but stop_reason=content_filter; the old collector returned 0. A successful ds review returned stop_reason=end_turn. Sanitized original field evidence and synthetic equivalents are in evidence/protocol/observed-terminal-fields.json.
- Local Claude Agent SDK schema excerpts identify SDKResultSuccess, SDKResultError, SDKAssistantMessage.error, SDKAPIRetryMessage and TerminalReason. Source/version caveat is recorded in evidence/protocol/sources.json. Native completion reasons are protocol fields, not diagnostic wording; using their semantics is within this goal.

## Success signals and required verification

1. Controller-only read-only original-log replay against reviewed repository and installed versions returns 0/needs_review with all five notices and the existing three anomalies retained. All selected checks remain, result_status remains not_assessed, and originals are unchanged. The v1 exact errors/anomalies/warnings category counts are superseded: category choice follows the revised diagnostic contract; no notice is discarded.
2. Both runtimes accept synthetically novel intermediate diagnostic text after valid completion, without adding any text recognition rule. Preserve full bounded diagnostic totals/source locations and raw logs.
3. Both runtimes reject native/postprocessing failures, explicit failed/missing/conflicting/invalid terminals, malformed logs, missing/incomplete finals and explicit check failures. Include Claude's observed success-labeled content_filter result, native truncation/refusal/noncompletion fields and recovered intermediate diagnostics; no text heuristic is a substitute for native evidence.
4. Ordinary tool anomalies, statistics, canary/artifact behavior, report schema, raw detail mode and caller-owned task judgment remain appropriately documented. Tests previously asserting allowlist rejection must be revised to the new confirmed contract rather than counted as passing old-contract acceptance.
5. Complete new-goal planreview and independent dual code/aggregate/actual-PR deepreview in Gateflow order, adjudicate/fix/re-review findings, create a new draft PR with accepted commits. Do not merge/approve/mark-ready/request-reviewers/comment externally.
6. After full review, execute already authorized component-appropriate sync from the reviewed checkout and record installed equality/version. Then controller invokes mimo-flash separately through Codex and Claude Code runtimes for three-step synthetic live probes: tool-read input, program-compute/write a new result, tool-read it back. Actual completion/tool/result records are required. Original replay and synthetic protocol regression prove fault classification; ordinary probes do not reproduce real network failure.

## Boundaries and minimal design

Expected ownership is the existing collector/runtime adapters, existing runner tests and necessary current documentation (README and generic sub-agents result semantics if outdated). No new framework, automatic retry, business rerun, business acceptance or hidden diagnosis suppression. Retain runner CLI/report shape and exit propagation unless a necessary in-scope adjustment is established by plan/code review. No original business contents go to delegates or committed test fixtures; only controller replays original inputs read-only. No merge authorization.

## Concrete protocol questions for plan (not unresolved user tradeoffs)

- Specify native terminal validity/completeness and final-answer ownership separately for Codex and Claude; use actual typed fields and observed records, not invented cross-runtime fields or diagnostic text.
- Specify how optional/absent historical stop/terminal metadata is handled, distinguishing absent information from explicit malformed or noncompletion values. Complete result fields and successful native terminal are still required; reject explicit native negative signals.
- Specify same-execution identity/terminal cardinality, applicable root versus nested Claude messages, final selection/order and permitted post-terminal metadata using available native identity fields. Do not mistake intermediate tool_use/retry/error frames for final refusal/truncation, or accept a different execution's success as recovery.
- Specify which error-shaped events are structurally valid diagnostics versus malformed frames, and how native final failure overrides them without discarding either. Removal of the text allowlist must not turn parse/check failures into anomalies.

These are implementation/protocol decisions to resolve from evidence in plan and review, within the user-confirmed direction. No additional blocking user question has been established.

## History, risks and continuation

Old plan and its reviews are historical only and cannot approve v2. In-flight old reviewer is collected by its original handle without interruption; only unchanged source/baseline/original evidence may be reused with applicability recorded. Authoritative current gate/next entry point is state.json.

Residual risks: Codex JSONL cannot independently reveal a refusal when upstream emits only a completed text response with no native negative field (assigned to later work unit if richer protocol becomes available; owner maintainer/caller; preserve text and not_assessed). Original business correctness remains caller-owned (assigned to caller's existing workflow). Unknown future native terminal/completeness schema variants need separate protocol evidence (assigned to later work unit, owner maintainer). Actual transient faults are not injected by ordinary probes (assigned to later work unit if requested, owner user/controller). Current false rejection and Claude success-labeled negative completion signal are to be fixed in this work unit.

Goal confirmation v2: passed by explicit user redirect. Next entry point: revised plan via gpt-6-sol. Prior allowlist-only implementation has not been performed; no production or live changes have occurred.
