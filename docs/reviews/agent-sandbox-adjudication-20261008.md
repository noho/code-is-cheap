# Agent sandbox review adjudication

## Frozen input and initial reviews

Base `6bc30cd2e47153504a52787643853b756dbf9308`, initial head `3a563662b959e64234e2ed5a3e4f163bf4ec10ae`.
Two independent parallel `$deepreview` runs through `$sub-agents`, Codex runtime, ordinary inherited permissions, no persistence.
Both reviewers read all 15 changed files and relevant dependencies; neither read its peer's report.

| Provider / label | Artifact | Run directory |
| --- | --- | --- |
| mimo / deny-review-mimopro-v1-20261008 | mimo/code-review-20261008-191851.md | `/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.6sXIIn` |
| mimo-flash / deny-review-mimoflash-v1-20261008 | mimo-flash/code-review-20261008-192240.md | `/private/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/sub-agents.uNW1dU` |

Each run has its label's `.jsonl`, `.stderr`, `.last.md`, plus prompt and canary files.
Outer process exits were 0, collected through exec/write_stdin completion; each JSONL contains one `turn.completed`,
no `turn.failed`, and complete command events (MiMo 99 completed commands, MiMo Flash 140).
Both report canaries exactly match their run's expected bytes and the observed cat output. MiMo's final answer links the report;
the canary is in the report, following the deepreview concise final contract. MiMo Flash also repeats it in the final answer.

For both runs:

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: complete
required_evidence: complete
canary_status: match
result_status: accepted
evidence_gaps: []
retry_class: none
```

MiMo warnings: `item_106` exited 1 while counting report field labels; the last two regex matches omitted severity text
inside the bold label. The preceding nine labels matched all five findings. Direct report inspection confirms all findings
have risk and severity fields. This formatting check does not affect source/test evidence and requires no redispatch.
MiMo Flash warnings: report self-identifies as `gpt-5`, inconsistent with its invoked `mimo-flash` provider and selected
`mimo-v2.6-flash` route. Provider invocation/configuration is authoritative; MiMo uses `mimo-v2.6-pro`.
Both reviewers disclosed not rerunning kernel tests because srt was not on their PATH; the controller independently reran
the actual outer sandbox and native CLI tests using the temporary pinned srt installation.

## Finding decisions

| Finding | Decision and implemented response |
| --- | --- |
| MiMo 1: internal verification can falsely prove ordinary permission denial / execute arbitrary command | Accepted false-proof defect. Verification now queries effective Seatbelt file-read-data permission, also attempts the actual read, and checks the fixed runner command against the manifest. Direct mode-000 regression refuses to start. Caller invocation of the internal entry is not itself an elevation of the caller's rights. |
| MiMo 2: required credential/config paths cannot be denied | Rejected as a request to extend this feature to credential isolation. Runtime startup requires selected endpoints/auth. Already fails closed if those dependencies are denied; documents now state this boundary explicitly. No credential broker or external environment introduced. |
| MiMo 3: stdin prompt can introduce unprepared input | Accepted. Exactly one nonempty prepared prompt required; snapshotted to protected state and inherited stdin closed. |
| MiMo 4: direct Claude helper can override full-access permission settings | Accepted. Helper owns validation and rejects conflicting settings/permission-mode/restricted options before loading credentials; duplicate launcher validation removed. |
| MiMo 5 / MiMo Flash 2: Claude version discrepancy | Accepted. README and validation use observed 2.1.294; actual native trace confirms it. |
| MiMo Flash 1: fresh Codex home drops user .rules | Accepted. Copy original rules unchanged into the fresh home, protect against modification, verify actual native rejection and absence of forbidden output. |

Controller separately checked the changed call paths in agent-sandbox, endpoint helper, launchers, runners and preflight;
inspected actual synthetic native request bodies and terminal events; tested Claude denyWrite precedence, case-only aliases,
literal filenames, selected output boundaries and LaunchServices through a temporary background-only app.
Output conflicts with original write bans now fail at setup, including --check. Unsupported policy mappings stop explicitly.
No portfolio business source, data or running workflow was accessed or changed for these tests.

See `agent-sandbox-validation-20261008.md` for commands, observations and implementation limits.
Fix re-review and final closure are recorded below after collection.
