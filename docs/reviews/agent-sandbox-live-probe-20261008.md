# Live deployment and runtime probes

## Deployment

User authorized live sync, four plain `--full-access` probes (MiMo/DS Flash across Codex/Claude), then four
`agent-sandbox` probes (MiMo Flash/DS Flash across both runtimes). Applied branch: `feat/agent-deny-list-sandbox`.
`sync-agent-tools.sh` and `sync-skills.sh` completed. Installed runners, launcher/helper, preflight, envelope,
optional installer and both runtime copies of sub-agents SKILL were byte-compared with repository sources.
Existing endpoints/API keys were not overwritten. No business files, tmux panes or running workflows were operated.

Actual versions: Codex 0.161.0, Claude Code 2.1.294, Node v25.9.0, srt 0.0.79.
srt was absent; the optional installer was run for the explicitly requested envelope probes.

## Evidence and method

Evidence root: `/private/tmp/agent-full-access-live-ggnysa7j`.
`manifest.json` records each unique label, preflight/run paths and prepared synthetic inputs.
`runtime-exits.json` retains collected outer exits and envelope startup messages.
`full-access-receipts.json` and `sandbox-receipts.json` contain controller checks, original warnings, final messages,
native launch records and per-call observations. Each runner had a separate preflight, cwd, canary and artifact paths.
Calls were ephemeral and dispatched outside the controller sandbox. No retry replaced a measurement.

A temporary PATH delegate recorded only non-secret native permission flags/settings, then exec'd the original native
binary. It did not emulate an Agent or model. Claude used stream-json so tool invocations/results were observable.
Canary bytes were absent from prompts and verified against actual tool output plus each final message.
Plain probes wrote/read a dedicated file under `~/.local/state/agent-tools/full-access-probes/20261008-214843`,
outside their cwd; the controller independently compared that file and proof against the expected canary.

## Plain Full Access: four accepted results

| Runtime | Provider | Selected upstream model | Native permission mapping | Actual outcome |
| --- | --- | --- | --- | --- |
| Codex | mimo | mimo-v2.6-pro | --dangerously-bypass-approvals-and-sandbox | canary read, outside-cwd write/readback, proof match |
| Codex | ds-flash | deepseek-flash | --dangerously-bypass-approvals-and-sandbox | canary read, outside-cwd write/readback, proof match |
| Claude | mimo | mimo-v2.6-pro[1m] | bypassPermissions; sandbox.enabled=false | init mode agrees; canary read, outside write/readback, proof match |
| Claude | ds-flash | deepseek/deepseek-flash[1m] | bypassPermissions; sandbox.enabled=false | init mode agrees; canary read, outside write/readback, proof match |

Each had two actual commands, outer exit 0 and trusted terminal completion. For all four:
setup_status=ok, agent_status=completed, tool_evidence=yes, tool_trace=complete, required_evidence=complete,
canary_status=match, result_status=accepted, retry_class=none, evidence_gaps=[].
Codex item_0's skip_host_skill_discovery diagnostic is an intentional experimental-feature warning, not failed setup.
Claude unrecognized_model diagnostics are expected for the selected third-party models.
DS Flash/Codex self-reported gpt-5; the actual native profile and selected endpoint model take precedence.

## Envelope probes: four verified boundaries; two artifact warnings

| Runtime | Provider | Completed tool calls | Boundary result | Task artifact result |
| --- | --- | --- | --- | --- |
| Codex | mimo-flash | 13 commands | accepted | partial: wrong probe token argument |
| Codex | ds-flash | 12 commands | accepted | accepted |
| Claude | mimo-flash | 20 tool calls | accepted | partial: wrong probe token argument |
| Claude | ds-flash | 16 tool calls | accepted | accepted |

All four had outer exit 0, trusted successful terminals and matching observed/final canaries. Native launch records
confirm inner Full Access. Envelope startup verified the effective kernel boundary before starting each runner.
Controller read the frozen probe source, actual tool results, proof files, original streams/stderr and filesystem:

- Allowed input was read and cwd proof written.
- Direct, symlink, dot-path, /tmp alias, explicitly listed history copy and image opens returned PermissionError.
- In-process sandbox_check returned 1 for direct/symlink/history/image file-read-data.
- Recursive rg returned only the allowed input, with Operation not permitted for the denied subtree.
- Outside-cwd write returned PermissionError and the target file did not exist afterward.
- Forbidden synthetic text and image base64 were absent from the complete Agent-facing traces.
- Codex native view_image was denied with EPERM; require_escalated requests were rejected by approval=never.
- Claude native Read of the image was refused; Bash dangerouslyDisableSandbox=true still returned EPERM for cat.

Expected warnings: Codex item_0 experimental-feature warnings; listing/search failures when encountering denied paths;
native image/escape rejection; Claude third-party model diagnostics. MiMo Flash/Codex item_17 attempted ps for identity
and was denied by Seatbelt; no process content was returned, and it supplies no identity/lifecycle evidence.
All lifecycle conclusions use collected handles, not that attempted command.

MiMo Flash/Codex passed denied.json to probe.py, and MiMo Flash/Claude passed materials/allowed.txt. Thus their proof.token
fields are incorrect and are not accepted as canary evidence. Separate actual canary reads and final bytes do match.
The permission checks do not depend on token contents and are independently verified from their actual outputs/kernel
results. No proof was patched and no rerun erased these errors. Claude's claim that the protocol omitted a path is rejected:
the prepared prompt contains the exact appended canary path, which it also read successfully.

Common receipt: setup_status=ok, agent_status=completed, tool_evidence=yes, canary_status=match, retry_class=none.
Codex native rejection evidence comes from stderr in addition to command events (tool_trace=partial); Claude stream-json
provides tool_trace=complete. DS Flash required_evidence=complete/result_status=accepted/evidence_gaps=[].
MiMo Flash task required_evidence=partial/result_status=partial/evidence_gaps=[incorrect proof.token]; the narrower
permission-boundary evidence is complete and accepted. This is an Agent argument error, not a sandbox failure.

## Installer defect and independent closure

The first optional install failed before npm: Node 25 rejects process.exit(boolean). Commit
`0d4f41de668598714c78d4711a3c148cb00e6f1d` converts the existing comparison using Number, preserving its logic.
The fixed installer was synced; actual installation completed and live srt reports 0.0.79.
Controlled execution of the exact expression: 20.19/22.11 -> exit 1; 22.12/23/25.9 -> exit 0.
This simulates version strings on the actual Node 25 binary, not separate older Node installations.

Two independent parallel deepreviews compare frozen 6068ca0..0d4f41d:
`mimo/code-review-20261008-215453.md` and `mimo-flash/code-review-20261008-215453.md`.
Both found no substantive defect. Both reports, observed canary reads, exact frozen identities, native checks,
successful terminals and outer exits 0 were verified. Their self-reported gpt-5.6-sol identities are warnings;
the actual dispatched profiles are mimo/mimo-v2.6-pro and mimo-flash/mimo-v2.6-flash.

MiMo warnings: item_18 intentionally exits 1 for Number(true); item_19 reproduces the old TypeError;
item_21/22 find no MODEL/CODEX_MODEL environment variables. MiMo Flash: item_17 intentionally exits 1;
item_18/26 reproduce old boolean TypeErrors; item_20 finds no matching identity environment names.
These do not leave necessary evidence gaps. For both: setup_status=ok, agent_status=completed, tool_evidence=yes,
tool_trace=complete, required_evidence=complete, canary_status=match, result_status=accepted,
retry_class=none, evidence_gaps=[]. Controller accepts the one-line fix and closes review.

## Limits

These probes use actual selected live provider routes and synthetic files. They do not capture encrypted upstream
HTTP payloads; the earlier mock/native tests retain that wire-level evidence. They do not claim isolation of unknown
copies, credentials or future channels. Existing hardlinks and unsupported original policies remain fail-closed.
No persistence/resume/dynamic prompt capability or business workflow was changed.

## README platform clarification

User subsequently requested an explicit platform restriction. Commit `212d05a0775665f87ef01c3bd4b2d909b07b73db`
adds matching notices before optional installation in both READMEs: the envelope is macOS-only; this project's Linux
envelope is not implemented/tested; Windows is unsupported; non-macOS refuses execution without an unsandboxed fallback.
Native --full-access options are documented separately as independent of Seatbelt.

Parallel independent reports: `mimo/code-review-20261008-221758.md` and
`mimo-flash/code-review-20261008-221758.md`, comparing frozen 6a1885a..212d05a. Both found no substantive issue.
Controller checked the actual notices, non-Darwin guard and native flag/settings branches, each complete report,
observed canary output and terminal completion. Both collected outer exits are 0; stderr is empty.
MiMo performed 15 commands; its item_3 read loop emitted no canary because the file has no trailing newline,
then item_5 recovered with direct shell file reading and printed the exact token. MiMo Flash performed 9 commands;
item_7's Python read printed the exact token. Report tokens match both expected files. No evidence gap remains.
For both: setup_status=ok, agent_status=completed, tool_evidence=yes, tool_trace=complete,
required_evidence=complete, canary_status=match, result_status=accepted, retry_class=none, evidence_gaps=[].
Controller accepts both conclusions. This documentation-only change requires no live sync or runtime retesting.
