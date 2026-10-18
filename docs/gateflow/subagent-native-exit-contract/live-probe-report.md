# Authorized live sync and two-runtime probe evidence

2026-10-18. Controller executed the user's later explicit live-delivery authorization after code and draft-PR gates passed. Source checkout: pushed commit `812aceced5e2a5a72cf7ca3eea63a0e974f205b2`; all15 product files are byte-identical to independently reviewed `781a239982631ab0ba8baf0bf6dd72069f3cee68`, bundle `b580c570bdd9e43bfc79861440f4ff48f2cb8bc2b1b22bb7cddd4b8cef512502`. No merge or original financial-task replay occurred.

## Actual deployment and identity

Ran from `/Users/leo/workspace/code-is-cheap`, separately with the user's authorized escalation:

```bash
./scripts/sync-agent-tools.sh
./scripts/sync-skills.sh
```

Both actually exited0; skill validation passed all6 skills. `live-sync-commands.json` retains exact tool results. Immediately pre-sync38 installed files matched the earlier baseline, no environment target override or extra/obsolete skill file was found. After sync **all38 installed files match source bytes**, including the launcher, installed runners/collector/helpers/defaults, and both Codex/Claude skill trees (`live-installed-identity.json`). Rechecked after both probes: still identical; reviewed15-source bundle unchanged. No profiles/catalogs/routes/shim changed, so `sync-codex-agent.sh` was not applicable. Scripts use this checkout and require no merge.

Installed paths used: `/Users/leo/.local/bin/codex-agent-run`, `/Users/leo/.local/bin/claude-agent-run`, launcher `/Users/leo/.config/zsh/agent-tools.zsh`, skill `/Users/leo/{.codex,.claude}/skills/sub-agents/SKILL.md` (SHA256 `a40660709e3c9d3fa5e6bbebbacb8895e1ad47797c75a7d135508ce0e1518796`).

## Real calls and acceptance evidence

Each launched exactly once through a separate escalated managed runner call using installed source, no canary/artifact check, no `--full-access`, no wrapper retry/provider switch. Explicit cwd/input/output paths and the exact prompt bytes are in `live-probe-inputs.json`, `live-probes/prelaunch.json`, each runtime's `input.json`/`prompt.md`, and runs.md. Both result paths were absent before launch; distinct nonce/input hashes bind fresh results. Codex explicitly passed `--skip-git-repo-check` for its non-Git temporary workspace. The child tasks each required actual tool-read → program compute/exclusive-new-file write → tool-readback, not prose/tool-like final syntax.

| Runtime/provider | Actual outer/native | Real completed tool anchors in native JSONL | Native final anchor | Independent values: count / sum / squares / weighted |
| --- | --- | --- | --- | --- |
| Codex / mimo-flash | 0 / 0 | input cat line4; Python program line7 (`open(mode='x')`, exit0); result cat line9 | completed agent_message line11; turn.completed line12 | 9 / -2675 /1365847 / -14008 |
| Claude / mimo-flash | 0 / 0 | Read call/result lines10/11; Bash program324/327 (`open(...,"x")`, non-error result); Read335/336 | unique root result line351 | 9 / -761 /3830989 / -4098 |

Codex input nonce `bb7fa872976eba74649cf776`, SHA256 `3ddfd7aeac7285fd3ab7a845024c5bb0f416dc474b6293019a53974675e2d68d`. Claude nonce `c40ee8a352c034a1f14ab30b`, SHA256 `1996124f47465ca48f29398f74a999b4540d7e8c583e1d60a6ea70cc7d53074a`. Controller independently recalculated count/sum/squares/1-based weighted sum with a separate loop and checked the complete result dictionary against both original manifest and observed tool-readback JSON. Inputs remain unchanged. Native tool calls/results are actually ordered; program writes used exclusive mode and printed the new absolute path. No additional child tool operation/delegation was observed.

Each runtime directory contains `result.json`, `runner-summary.json`, **full unmodified `final.txt`**, exact selected `tool-and-terminal-events.json`, copied stderr and `verification.json`; actual host receipts are `live-probe-{codex,claude}-receipt.json`. Summary final equals the native final string exactly (not merely a length/prefix comparison), and saved final bytes equal that string's UTF-8 bytes. Both summaries have exactly the14 schema2 fields, empty artifact list/null canary, no legacy verdicts/exit rollup/final cap metadata. `live-probes/verification.json` records combined caller-owned evidence checks; these explicit probe checks are not new runner task-acceptance logic.

Original complete native logs remain untouched:

- Codex `/private/tmp/subagent-native-exit-contract/live-probe-codex.jsonl`, SHA256 `093fe7d8e4bb88478cade49ef9a036c2f62b7012b7de24bc419a01739cfbd052`; stdout/stderr paths in actual summary. Selected exact events retain original line anchors without copying reasoning blocks.
- Claude `/private/tmp/subagent-native-exit-contract/live-probe-claude.jsonl`, SHA256 `6517d67526735b40f3de94d0383c2ee0428173ed1b09c3db7035e8a6edd478bb`; same preservation and selection policy.

## Diagnostic text remained visible without verdicts

Codex stderr is empty, but native JSONL has these exact `type:error` messages at lines5 and10, preserved unchanged in the factual `diagnostics` list with path/line:

```text
Reconnecting... 1/5 (stream disconnected before completion: failed to parse ResponseCompleted: missing field `cached_tokens`)
Reconnecting... 1/5 (stream disconnected before completion: idle timeout waiting for SSE)
```

Claude stderr line1 (including its newline) is preserved verbatim in diagnostics:

```text
[claude-code:unrecognized_model] {"model":"mimo-v2.6-flash[1m]","query_source":"sdk"}
```

These are observations with original source envelopes, not a benign/error/recovered text classification. Both real CLIs ultimately exited0 and supplied full native finals; the thin wrapper returned0 and retained all three texts. Codex reconnects were native CLI events within this one call, not this wrapper/controller retrying the task. The waiting period ended only when the real process completed. The underlying response-metadata/SSE cause has not been investigated or attributed to provider/adapter/runtime; it is outside this wrapper fix, owner runtime/provider maintainers, destination separate diagnostic work if requested. No route/config change or additional paid reproduction was made.

## Limits and caller handoff

This verifies the installed reviewed wrapper/skill behavior through two actual tool-capable runtime interactions. It does not constitute A-route financial/business/code acceptance, resume the old FY2025 task, test every native/kernel variant, or solve abrupt host loss. Conditional opt-in skips and malformed-final-frame policy remain disclosed in closeout/decisions with owners. External callers must adopt schema2 and reload the new skill; caller alone owns business acceptance, continuation/retry and routing under authorization.

Interactive launcher users run `source ~/.zshrc` or open a new shell; reopen Agent sessions for updated skills. Installed runner callers already on PATH need no zshrc reload. Caller patrol entry remains this existing directory; the caller-side controller can inspect this report/full-final/tool/math/identity evidence, then notify its callers that SKILL is updated. User still merges PR61 manually.
