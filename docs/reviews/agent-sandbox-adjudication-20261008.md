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
## First fix re-review (a791aa1)

Both independent fix re-reviews completed with outer exit 0 and one `turn.completed`; both report canaries and observed cat
outputs match their own preflight expected bytes. Reports are `mimo/code-review-20261008-2024-fix.md` and
`mimo-flash/code-review-20261008-2024-fix.md`. Neither found another substantive code defect; accepted fixes were verified.

- MiMo label `deny-fix-review-mimo-v2-20261008-2024`, run directory `sub-agents.mtuEBm` under the same system TMPDIR above.
  `setup_status=ok`, `agent_status=completed`, `tool_evidence=yes`, `tool_trace=complete`, `required_evidence=complete`,
  `canary_status=match`, `result_status=accepted`, `retry_class=none`, `evidence_gaps=[]`.
  Explained command warnings: item_24/25 absent system headers/man entry; item_38 srt not on PATH; item_65 expected no
  forbidden marker match; item_82/83/86 missing/unmatched source distributions; item_95 native binary not a symlink;
  item_96/99 absent Claude source directories. Existing binaries/help, pinned srt package documentation and native traces
  provided the relevant evidence instead. No necessary evidence remained unresolved.
- MiMo Flash label `deny-fix-review-mimo-flash-v2-20261008-2024`, run directory `sub-agents.xutp0F`.
  `setup_status=ok`, `agent_status=completed`, `tool_evidence=yes`, `tool_trace=complete`, `required_evidence=complete`,
  `canary_status=match`, `result_status=partial`, `retry_class=task`.
  item_66 used jq input incorrectly (exit 5); corrected inspection recovered the counts and native evidence.
  **Input-scope gap:** item_34 recursively searched ~/.claude and ~/.config, outside the permitted repository/evidence inputs.
  The output included public cache/plugin source plus two lines from a portfolio project's historical tool-output copy.
  No literal key was returned; the reviewer disclosed the broad search and did not cite it. Nevertheless this is not an
  input-clean review pass. Directly verified technical findings remain usable; this report alone does not close review.
  This is a scope defect, not automatic rejection due to a tool command failure.

## Additional controller fix and final bounded review setup

Controller found a denied-directory symlink to a FIFO could cause load_denies to block while proving pre-sandbox readability.
Minimal fix checks recursively discovered targets are regular files/directories before opening; regression asserts that a special
target is never opened. Final ordinary suite: 84 passed, 6 opt-in skips; kernel/native suite: 17 passed.

Final reviews explicitly use the new envelope to deny the known Claude project-log/history paths, listed Codex sessions/logs/
history databases and peer reports. This is a caller-provided list, not inferred business rules or an all-home allowlist.
An exploratory --check declaring the entire ~/.claude failed before any Agent because file-history contains a pre-existing hardlink.
No fallback occurred. The controller then explicitly selected the concrete project/session logs required for this review's declared
boundary; the hardlink directory is not claimed isolated. Setup with those literal paths succeeds.

## Bounded final reviews (b27a9fd)

Reports: `mimo/code-review-20261008-2048-final.md`, `mimo-flash/code-review-20261008-2048-final.md`.
Both completed naturally with outer exit 0 and `turn.completed`; both canaries match the expected bytes and observed cat.
Both found no substantive defect in the FIFO guard increment. Actual cat of ~/.claude/history.jsonl and recursive rg of
~/.claude/projects returned only Operation not permitted, with no history content. Allowed code and canary reads, and own
report writes succeeded. No peer report content was read. Root independently checked the frozen diff and original tool events.

For both: setup_status=ok, agent_status=completed, tool_evidence=yes, tool_trace=complete, required_evidence=complete,
canary_status=match, result_status=accepted, evidence_gaps=[], retry_class=none. Temporary tooling errors below recovered;
they do not mechanically invalidate the review. Full nested kernel reruns were not necessary evidence for these reviewers;
controller's outside-sandbox suite provides that evidence.

- MiMo: label deny-final-review-mimo-v3-20261008-2048, run_dir sub-agents.av8ddH; 70 commands.
  Expected deny probes item_9/10; item_48 expected no forbidden marker matches; item_55/56 here-document temp failures
  recovered with Python -c. Three focused regression tests and normal symlink expansion passed.
- MiMo Flash: label deny-final-review-mimo-flash-v3-20261008-2048, run_dir sub-agents.nQTH9s.
  Expected deny probes item_12/13; jq item_30 fixed by correct trace parsing; nested kernel item_38/45 failed at socket/ancestor
  config setup and are explicitly not counted as passes. Fixture/import errors item_47/51/60/66/67/68 recovered through
  corrected synthetic checks. Here-doc item_43/87, unsupported apply_patch router call, PTY item_88, /tmp-write item_91,
  malformed shell quoting item_97 and intermediate report validation errors recovered before final artifact/terminal checks.
  Nine SetupTests and end-to-end --check FIFO rejection passed. Intermediate draft corruption was replaced by a complete,
  single-header final report; final provider/model/canary and scope were independently checked.
  User authorized stopping/retrying while report writing stalled; original process then completed naturally, so no stop occurred.

Both streams record skip_host_skill_discovery's experimental-feature warning. That configured reduction in host discovery is
intentional, exercised with the pinned runtime, and not a failed initialization or missing evidence.

## Final operational repair

Native review logs exposed zsh here-doc temporary files defaulting outside the allowed state. Accepted controller fix sets
TMPPREFIX to state/tmp/zsh, alongside existing TMPDIR; the write policy is unchanged. Isolated candidate tests and the applied
15-test kernel/setup suite prove heredoc success in workspace-write and read-only, with denied reads/outside writes unchanged.
MiMo Flash's explicitly authorized focused follow-up checks this one-variable fix using exec_command to write its report.
All earlier attempts/reports remain retained; this follow-up does not replace them or recalculate a measurement batch.

## Authorized focused follow-up and closure (e995c19)

MiMo Flash report: `mimo-flash/code-review-20261008-zsh-final.md`.
Label `deny-zsh-review-mimo-flash-v4-20261008`, run_dir `sub-agents.2MMRPx`; 34 completed commands.
The run completed naturally with outer exit 0 and `turn.completed`. Canary read in item_4, expected bytes and final
report agree. The exact base/head and two-file diff match this operational repair. No substantive finding was reported.
Controller checked actual zsh outputs: missing TMPPREFIX parent fails, the allowed per-run prefix succeeds with the exact
marker. Nine focused SetupTests passed. The independent kernel receipt agrees with the controller's applied 15-test suite.

Warnings adjudicated: an exploratory command containing rm was rejected by the preserved original Codex rule; item_27/32
recovered the consumption probe with Python temporary-directory management. item_37 wrote the complete report, then its
header assertion failed because it compared literal backslash-n text; item_38 independently read the nonempty artifact.
Controller checked the actual header, canary, sections and complete content rather than treating that assertion as a failed
review. The experimental skip_host_skill_discovery warning remains expected. No required evidence gap remains.

Receipt: setup_status=ok, agent_status=completed, tool_evidence=yes, tool_trace=complete, required_evidence=complete,
canary_status=match, result_status=accepted, retry_class=none, evidence_gaps=[].
Both independent full reviews and the authorized final operational follow-up are closed. Existing hardlinks, unlisted
copies, readable runtime credentials and unsupported policies retain the limitations documented in validation/README.
No live sync was performed; the branch is ready for a PR and manual user merge.
