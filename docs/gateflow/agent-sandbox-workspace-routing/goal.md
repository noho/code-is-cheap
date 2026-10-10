# Goal confirmation: agent-sandbox-workspace-routing

Status: delegated caller/controller explicitly confirmed on 2026-10-11; plan authorized, no implementation started.

## Goal and motivation

Restore the Codex `gpt-6-sol` managed-auth HTTPS startup inside the existing macOS agent-sandbox envelope. Prepare the necessary explicit certificate trust input for this envelope rather than relying on unavailable default system trust discovery. A startup connectivity problem must retain actionable diagnostics and actual failure records.

## Direct evidence

- Baseline `20fc6c37751836329143567c166990bdffa9de3c`; independent branch `fix/agent-sandbox-workspace-routing`, worktree `/private/tmp/code-is-cheap-workspace-routing`. Recovered-stream branch and frozen product diff remain separate.
- Two caller attempts in the specifically authorized diagnostic index ended native/runner 1, `turn.failed`, zero tool results. These are genuine startup failures, not successfully recovered notifications.
- `scripts/agent-sandbox:343-377` prepares an isolated model/profile/auth home; `:550-616` retains the parent environment and installs strict srt network restrictions, but does not prepare explicit Codex certificate input.
- Installed srt 0.0.79 excludes `com.apple.trustd.agent` unless weaker network isolation is enabled. The wrapper correctly keeps weaker network isolation disabled. This is a plausible implementation mechanism, not a measured identification of the exact blocked macOS operation.
- Synthetic controlled probes, same provider/cwd/prompt: ordinary runner succeeds (`OK`, native/runner 0); unmodified isolated runner fails in 25.536161 seconds with the reported routing error; isolated home without the outer sandbox succeeds; unchanged outer isolation with only `CODEX_CA_CERTIFICATE=/etc/ssl/cert.pem` succeeds (`OK`, native/runner 0, 5.465033 seconds).
- Failed and successful isolated probes have identical selected model (`gpt-6.1-sol`, existing `gpt-6-sol` route), authentication bytes, network settings and normalized deny paths. Both passed kernel read-boundary verification. No credentials are included in artifacts.
- Official documentation specifies explicit `CODEX_CA_CERTIFICATE` with fallback to `SSL_CERT_FILE` for HTTPS and secure WebSocket trust: https://learn.chatgpt.com/docs/auth#custom-ca-bundles.
- Evidence: `evidence/diagnostic-controls.json`; full private diagnostic report `/private/tmp/workspace-routing-diagnosis-eprmtk6q/diagnosis.md`. Named caller evidence was read only; no caller business prompt/results were used.

## Smallest intended boundary

One behavior increment: prepare a readable certificate bundle for the affected Codex HTTPS channel inside the existing envelope, respecting explicitly configured custom certificate inputs and failing with the specific missing/denied/invalid input rather than silently ignoring it. Retain the same provider/model/auth route and all existing read/write/network restrictions. Change only the wrapper, directly necessary tests and user/Agent documentation. Exact implementation is delegated to the approved plan gate.

## Success signals

1. An independent synthetic `agent-sandbox ... codex-agent-run --provider gpt-6-sol` call starts and completes successfully with a genuine final answer and successful terminal; original failure logs remain intact.
2. Kernel verification still succeeds, denied content remains inaccessible by direct path and symlink, and existing write/network restrictions remain unchanged. Explicit CA preparation does not override a caller deny or enable weaker isolation.
3. Caller custom CA inputs are honored; missing or denied required inputs produce located errors without fallback that bypasses the boundary.
4. Focused regression tests validate selected CA/environment preparation, failure handling and unchanged route/boundary behavior; necessary existing sandbox tests pass.
5. Two independent reviews and all required gateflow gates close with recorded evidence, commits and a NEW draft PR. No merge or live installation is performed.

## Non-goals

No provider/model migration, authentication redesign, collector/recovered-stream classification changes, extra model-routing proof fields, new scheduler or platform, broad certificate/security refactor, weaker network isolation or trustd grant, changes to business files/contracts/deny lists, rerunning caller work, pane/clear/process interruptions, merge or live sync. No need to install old Python or change user business directories.

## Limits and questions

- User manual command and isolation mode remain unknown; the matched synthetic controls establish the local difference without assuming their exact command.
- The explicit system PEM bundle may not include custom certificates installed only in the macOS keychain. Such deployments must supply an appropriate explicit CA bundle; do not widen IPC or bypass TLS verification.
- Original large business deny lists were not rerun. Their caller owns post-deployment verification and task restoration.
- No blocking question for the minimal scope. Confirmation is required before plan; delegated caller confirmation is authorized by the user's latest instruction.

## Routes and authorization

Controller adjudication; external runner subprocesses: GPT-6 Sol plan/implement/fix; MiMo/Codex and DS Flash/Claude concurrently independent planreview/deepreview. Authorized work branch, commits, push and new draft PR. Merge/live deployment and original task restoration remain separately authorized actions.
