# README feature overview — controller closeout

## Scope and frozen identities

- Branch: `docs/readme-feature-overview`; selected base: `1d9b63e35865bb1ef7d8fafe8b7846ff91f98e3e`.
- Initial reviewed HEAD: `171816f4a9d037405af4dd35cceee047d168d79c`.
- Final reviewed HEAD: `4432c68a6e843a713b21426e29280445f28c5ada` (README.md, README.zh.md, AGENTS.md).
- User requested five feature sections and subsequently permanently selected MiMo/Codex + DS Flash/Claude for reviews. Old-route reviews were already in flight when the route changed; they completed before source fixes. Final parallel reviews use the new routes.
- Only documentation/project instructions changed. No runtime, skill implementation, deployment, private configuration, business workflow or business artifact changed.

## Findings and adjudication

| Source | Decision | Evidence / disposition |
| --- | --- | --- |
| Initial MiMo Claude F1: connection-file scope includes adjacent GPT example | accepted, fixed | The GPT/business branch in `scripts/agent-tools.zsh:225-231` skips third-party key resolution; README lower connection/profile sections distinguish account login. Both intros now qualify the JSON as third-party and preserve GPT/business account login/model cards. Both final reviewers verify the correction. |
| Initial MiMo Flash Claude F1: gate summary omits plan/preflight | accepted, fixed | `skills/gateflow/SKILL.md` Preflight/Gate Order and `skills/phaseflow/SKILL.md` Preflight distinguish preflight and plan. Both intros now mention these and describe an inclusive workflow summary rather than a complete gate enumeration. Both final reviewers verify the correction. |
| Initial MiMo Flash residual: external-action authorization list removed | addressed | Restored the original list in both introductions, checked against `skills/gateflow/SKILL.md:18-19`. |
| Final MiMo Codex F1: missing literal “permanent” allows arbitrary route replacement | rejected-with-reason | `AGENTS.md:6` imperatively requires the two exact provider/runtime pairs; `AGENTS.md:10` only gives explicit user task instructions precedence. These tracked project instructions persist across tasks. “Default” does not authorize an Agent to ignore step 2 or replace a route. No bypass behavior is demonstrated; adding this adjective would be a wording preference. |
| Final DS Flash Claude | accepted | No material findings; identity, bilingual content and source-owner checks independently verified by controller. |

No accepted finding remains open. Original reports are retained as historical review evidence; their “未修复” labels refer to their frozen inputs, not this closeout.

## Controller verification

- Each introductory section has exactly five feature headings in requested order.
- Compared both README tails after Included Skills with base: exactly four review-routing example lines per language changed; all other tail text is identical. The latest user route instruction authorizes those changes.
- Verified launcher examples and third-party/account-login distinction against `scripts/agent-tools.zsh`.
- Verified isolation claims against `skills/sub-agents/SKILL.md`, `scripts/agent-sandbox` and pinned srt installer: opt-in macOS, caller deny-list/known copies, kernel checks before runner, conservative original write scope. No new runtime probe is claimed.
- Verified communication against `skills/tmux-agents/SKILL.md`: already running CLI sessions, not live instruction injection into a one-shot runner.
- Verified planning/gates/authorization/continuation against gateflow and phaseflow source instructions.
- `git diff --check 1d9b63e35865bb1ef7d8fafe8b7846ff91f98e3e...4432c68a6e843a713b21426e29280445f28c5ada` passed. File SHA-256 values independently match DS Flash's report; these are file-byte hashes, not evidence of rendered Markdown.
- Remote main was checked and remained 1d9b63e35865bb1ef7d8fafe8b7846ff91f98e3e.

## Dispatch evidence

Each outer exit below was collected through its managed execution handle, not inferred from a report or file growth. Each stream was completely parsed, tool execution checked and actual proof-file read matched. Review reports alone are not the acceptance evidence.

### readme-features-mimo-20261009-131415

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: complete
required_evidence: complete
canary_status: match
result_status: accepted
warnings: ["exact stderr [claude-code:unrecognized_model] diagnostic; nonfatal per sub-agents"]
evidence_gaps: []
retry_class: none
```

- Runtime/provider: `claude/mimo`; managed session `97664` returned exit `0`.
- Report: [code-review-20261009-131415.md](code-review-20261009-131415.md); 30 paired tool calls/results.
- Structured terminal: `result/subtype=success/is_error=false`.
- Stream SHA-256: `55c63484d77c14592939959fc87864ff495b8cbeee418315be10628157c809f9`.
- Local evidence: `/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.vsoPYj/readme-features-mimo-20261009-131415.jsonl`; stderr `/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.vsoPYj/readme-features-mimo-20261009-131415.stderr`.

### readme-features-mimo-flash-20261009-131432

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: complete
required_evidence: complete
canary_status: match
result_status: accepted
warnings: ["exact stderr [claude-code:unrecognized_model] diagnostic; nonfatal per sub-agents", "zsh echo === exploration failed, recovered by direct grep", "process-substitution diff failed; complete exact git diff and controller tail comparison recovered identity", "report model header is incorrect; runtime init identifies mimo-v2.6-flash[1m]"]
evidence_gaps: []
retry_class: none
```

- Runtime/provider: `claude/mimo-flash`; managed session `45881` returned exit `0`.
- Report: [code-review-20261009-131432.md](code-review-20261009-131432.md); 24 paired tool calls/results.
- Structured terminal: `result/subtype=success/is_error=false`.
- Stream SHA-256: `e86e479aa7599472a45836f7408a1d66b845e20183795a10fcd9e8afef7987cf`.
- Local evidence: `/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.anr2x7/readme-features-mimo-flash-20261009-131432.jsonl`; stderr `/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.anr2x7/readme-features-mimo-flash-20261009-131432.stderr`.

### readme-final-mimo-codex-20261009-132708

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: complete
required_evidence: complete
canary_status: match
result_status: accepted
warnings: ["display-truncated broad reads recovered by targeted sed/nl and exact zero-context diffs"]
evidence_gaps: []
retry_class: none
```

- Runtime/provider: `codex/mimo`; managed session `77414` returned exit `0`.
- Report: [code-review-20261009-132708.md](code-review-20261009-132708.md); 46 completed command executions.
- Structured terminal: `turn.completed`; last-message file also checked.
- Stream SHA-256: `aa00c6cba364eb44f37e1583b080cd1998d8dff6af309e09f0edeeff2b6157b0`.
- Local evidence: `/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.4wBPzq/readme-final-mimo-codex-20261009-132708.jsonl`; stderr `/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.4wBPzq/readme-final-mimo-codex-20261009-132708.stderr`; last-message `/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.4wBPzq/readme-final-mimo-codex-20261009-132708.last.md`.

### readme-final-ds-flash-claude-20261009-132717

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: complete
required_evidence: complete
canary_status: match
result_status: accepted
warnings: ["exact stderr [claude-code:unrecognized_model] diagnostic; nonfatal per sub-agents", "duplicate unchanged proof-file Read suppressed by harness; initial actual read remains valid"]
evidence_gaps: []
retry_class: none
```

- Runtime/provider: `claude/ds-flash`; managed session `49566` returned exit `0`.
- Report: [code-review-20261009-132717.md](code-review-20261009-132717.md); 32 paired tool calls/results.
- Structured terminal: `result/subtype=success/is_error=false`.
- Stream SHA-256: `1696d511cae75a220d0456e690f2b1d876d888611b5158c604a4205fe42144d3`.
- Local evidence: `/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.9Hj4Uc/readme-final-ds-flash-claude-20261009-132717.jsonl`; stderr `/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.9Hj4Uc/readme-final-ds-flash-claude-20261009-132717.stderr`.

### Event details and corrections

- Initial MiMo Flash: Claude tool-result line 405 contains zsh `(eval):1: == not found`; later direct grep/Read results establish the required tmux and section evidence. Line 2740 contains `/dev/fd/12: Operation not permitted`; that exploratory comparison is not used as diff identity evidence. The earlier complete exact git diff and controller's exact tail comparison establish the reviewed delta. Neither failure consumes a provider retry.
- Initial MiMo Flash model header says `claude-fable-5`; controller uses actual runtime-init `mimo-v2.6-flash[1m]`. Initial MiMo runtime-init is `mimo-v2.6-pro[1m]`; final DS Flash runtime-init is `deepseek/deepseek-flash[1m]`.
- Final Codex JSONL has no model-init event; the report states `mimo-v2.6-pro`, matching the selected deployed MiMo card (controller read only model/provider/effort). This is configured identity, not independent attestation of an upstream server's internal model.
- Final MiMo broad display truncation was recovered via smaller source ranges and complete zero-context diffs. Its report says the complete skill was supplied in the task; actually the prompt supplied its path and tool reads loaded it (`item_2`, followed by targeted `item_5`). Required task sources were available and independently checked.
- Final DS Flash tool-result line 24698 suppresses a redundant unchanged proof-file read; line 857 contains the actual matching read. Its “whole repository grep” description is narrower in the actual commands; acceptance is bounded to the three changed files and specified supporting source sections, not a whole-repository audit.
- Initial MiMo also inspected the public repository connection example's key set to establish the GPT exception; no private user configuration or credential was read. The final tasks explicitly allow this public source.

### Controller setup / collection corrections

- Prepared DS Flash task `readme-final-ds-flash-claude-20261009-132708` was not dispatched: its report timestamp collided with the concurrently prepared MiMo report. Controller concurrency checks rejected setup before any Agent launch; generated a fresh label/report `...132717`. Program preflight had passed, but semantic/concurrency checks caught the issue. `setup_status=fail`, `agent_status=not_started`, `canary_status=not_run`, `result_status=not_assessed`, `retry_class=setup`; no provider retry consumed.
- A scratch monitor initially used a doubled `.jsonl.jsonl` path for final DS Flash. Corrected it to the actual launched `.jsonl` path and parsed the complete preserved stream after collecting exit 0. No runner or provider defect, no missing terminal, no redispatch.

## Limits and delivery

- Documentation-only static review; no new tests, runtime/model probes, rendered Markdown or link-network checks were needed/run. Existing runtime claims were checked against their source owners.
- Review artifacts added after the final reviewed HEAD are provenance only; README.md, README.zh.md and AGENTS.md remain byte-identical to that reviewed snapshot.
- New default routes are MiMo/Codex and DS Flash/Claude; explicit user task instructions remain authoritative.
- No sync to live is needed for this documentation/project-instruction change. Push and PR are authorized; user merges manually.
