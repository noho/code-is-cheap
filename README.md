# code-is-cheap

English | [中文](README.zh.md)

Tools for using multiple models in Codex / Claude Code, with an engineering control framework for automated AI coding.

## Features

### Claude Code / Codex launchers for common models

Use consistent launchers for models supported by each runtime, such as `mimo_claude`, `ds-flash_codex`, and `gpt_codex`.
Choose a model for interactive work in Claude Code / Codex CLI, or use a runner for non-interactive tasks.
For third-party models, a private local connection file manages upstream URLs, model IDs, and API keys, so you can switch
gateways that support the corresponding API. GPT/business profiles retain their Codex account login and model cards.
See the launcher table below for the commands available in each runtime.

### Replace built-in subagents with the sub-agents SKILL

Different models suit different tasks. Built-in subagents are constrained by the model choices and routing offered by
their runtime. The `sub-agents` skill launches external agents through `claude-agent-run` / `codex-agent-run`, letting an
Orchestrator choose the provider and runtime for each task in place of built-in subagent dispatch.

More importantly, large AI workflows consume many tokens, and not every step needs an expensive model.
Assign demanding reasoning to capable models and retrieval, organization, or routine checks to more economical ones.
The controller checks results, adjudicates disagreements, and accepts artifacts.

### Stricter isolation for child agents

Large AI workflows often need roles to reach independent conclusions without reading another role's answers.
For example, Agent A creates questions and answers; Agent B may read the questions but must not read A's answers,
analysis, or historical records before solving them independently.

Default Codex / Claude Code sandboxes, working directories, and prompt-only read prohibitions do not themselves define
that task-specific read boundary. On **macOS**, code-is-cheap offers the optional `agent-sandbox` envelope: the caller
supplies forbidden files/directories through `--deny-list`, reads are blocked at the filesystem access layer, and the
runner starts only after kernel read-denial verification. It retains a conservative subset of the original write limits.
Install the pinned srt dependency first; ordinary runner calls do not enable this isolation automatically. The caller
must also list known copies; unlisted copies remain readable. See "Optional task read restrictions (macOS)" below.

### Communication between agents

With `tmux-agents` and `tmux-cli`, running CLI agents can exchange prompts, wait for responses, and read feedback.
For example, project A depends on project B. When A's agent finds a bug, it sends reproduction evidence and a repair
request to B's agent; after receiving the fix result, A's agent verifies the dependency and continues its workflow.
Repairs, merges, and further execution follow each project's process and user authorization.
This connects existing CLI sessions; it does not inject instructions into a running one-shot runner task.

### Engineering controls for automated coding of large features

Prepare the architecture and implementation control plan first, then complete preflight. `phaseflow` advances phases /
work units according to `gateflow`'s gate order. After goal confirmation, the controller checks simple plans and uses
Planreview for important decisions. Implementation defaults to one slice, followed by one complete review of the final
combined version, necessary fixes and affected re-review, commits as needed, a draft PR, controller delivery checks, and final closeout.

Each step leaves traceable artifacts, review decisions, residual risks, and a next entry point, so a long workflow can
proceed within explicit boundaries. The user merges PRs manually. Across sessions, the control document and accepted
artifacts provide the basis for resuming work.
Merging, approving, marking a PR ready for review, requesting reviewers, deleting branches, public comments, and
creating or modifying external issues still require explicit user authorization.

This repository is the source of truth for the skills under `skills/`, the agent launcher under
`scripts/agent-tools.zsh`, the child-agent runners under `scripts/*-agent-run`, and the provider registry under
`codex-agent/model-providers.toml`. Local runtime files are installation
targets for project code. Edit and validate sources here, then sync them out. The private connection JSON is user-owned and never overwritten by sync.

## Included Skills

| Skill | Responsibility |
| --- | --- |
| `gateflow` | Defines the gated workflow for one work unit: preflight, goal confirmation, necessary planning and applicable plan review, implementation/validation, one complete code review, necessary fixes, draft PR delivery checks, and final closeout. It does not define project-level control documents or multi-agent routing. |
| `phaseflow` | Project step controller. It reads `design_doc` and `control_doc`, identifies the current `phase = work unit`, performs preflight and goal confirmation, checks simple plans and PR delivery, dispatches plan / implementation / fix and applicable independent reviews to Agents, adjudicates results, updates `control_doc`, and reconciles residual risks. |
| `planreview` | Adversarial review of important contract, architecture, migration or state-machine decisions, or an explicitly requested plan review. |
| `deepreview` | You want strict code review of current workspace changes, a GitHub PR, or the whole repository. |
| `tmux-agents` | Defines tmux communication only: Agent CLI type, `/skill` vs `$skill`, pane discovery, clear/session rules, `tmux-cli send/wait_idle/capture`, and send-safety rules. It does not assign roles. |
| `sub-agents` | Launches external Claude Code or Codex child agents through runner subprocesses, validates structured results, and supports isolated parallel dispatch without assigning roles. |

## Demo

```text
Proceed with $phaseflow; the design source of truth is docs/host/design.md, and the control document is docs/host/issues-implementation-control.md.
Strictly follow the constraints in AGENTS.md.
```

Equivalent explicit argument form:

```text
$phaseflow design_doc=docs/host/design.md control_doc=docs/host/issues-implementation-control.md
```

## Core Workflow

A typical flow is:

1. Prepare the design source document, such as `docs/design.md` or `docs/host/design.md`.
2. Prepare the implementation control document, such as `docs/implementation-control.md`, with phases/work units, status, validation requirements, artifacts, residual risks, and the next entry point.
3. Use `phaseflow` to read both documents, identify the current `phase = work unit`, and perform preflight plus goal confirmation with the user.
4. `phaseflow` reads Gateflow's `Gate Order`, dispatches planning, checks simple plans itself, and dispatches Planreview for important contract, architecture, migration or state-machine decisions or explicit review requirements.
5. After each Agent return, `phaseflow` reads the artifact, adjudicates findings, updates `control_doc`, and advances to the next gate.
6. Dispatch implementation/validation, defaulting to one slice. After all necessary slices finish, run one complete Deepreview of the final combined version, including overall goal coverage and slice interactions. Repair accepted findings and re-review affected paths; record readiness and residual-risk ownership when the review passes.
7. Commit as needed, push, and create a draft PR. The controller checks PR identity, head/base versions, the complete diff against the reviewed version, title/body, necessary CI, and final push status before `draft-PR-pass`. Changed content or base/diff requires affected review/validation; identical content does not trigger another complete review.
8. Final closeout then records what changed, what was verified, docs updates, finding status, remaining risks and owners, the draft PR URL, and the next entry point.
9. For issue work units, the draft PR body should link the issue; final closeout should confirm the issue closeout comment and the merge-time closing expectation.
10. After final closeout passes, the user manually merges the PR, pulls the latest target base branch, clears the agent session if desired, and resumes `phaseflow` from the `control_doc` next entry point.

Plans give enough direction for correct implementation, while agents choose local implementation details within the
confirmed scope. Records may share a file or reference existing evidence; separate artifacts and commits for every gate are not required.

## Requirements

- Codex CLI, Claude Code, or another agent runtime that supports local skill-style instruction files.
- Python 3.11+ (invoked as `python3`) and the `pyyaml` package if you want to run the bundled skill validator.
- `tmux` and `tmux-cli` if you use `tmux-agents` for multi-agent handoff.

If you use the zsh agent launcher functions below, their `tmux select-pane -T` calls rely on stable pane titles. Add this to `~/.tmux.conf` first so running programs cannot overwrite the title:

```tmux
# Keep pane titles fixed; do not let running programs overwrite them.
set -gw allow-set-title off
```

`tmux-cli` is part of the `claude-code-tools` package. Install or update to the pinned official release:

```bash
uv tool install --force 'claude-code-tools==1.29.1'
```

This command updates the entire `claude-code-tools` package, not just `tmux-cli`. Release [v1.29.1](https://github.com/pchalasani/claude-code-tools/releases/tag/v1.29.1) includes our [PR #212](https://github.com/pchalasani/claude-code-tools/pull/212) through merged upstream [PR #213](https://github.com/pchalasani/claude-code-tools/pull/213): remote status/preflight no longer create a managed session, and cached window targets are revalidated before reuse. The fork is no longer required. Sync this project's skills separately with `./scripts/sync-skills.sh`.

Official documentation:

- `tmux-cli`: https://pchalasani.github.io/claude-code-tools/tools/tmux-cli/
- `claude-code-tools` installation: https://pchalasani.github.io/claude-code-tools/getting-started/

## Install

On macOS, with Git, Codex CLI, Claude Code, Python 3.11+, jq, uv, tmux, rsync, zsh and curl available, download and run the installer:

```bash
curl -fsSL https://raw.githubusercontent.com/noho/code-is-cheap/main/install.sh -o install-code-is-cheap.sh
bash install-code-is-cheap.sh
```

Run the second command only after the download succeeds. From an existing checkout, run `bash ./install.sh` instead.
The downloaded installer clones to `~/.local/share/code-is-cheap`; rerunning it updates that clean `main` checkout with a fast-forward pull. Set `AGENT_INSTALL_DIR` to choose another checkout location.

The installer creates a private validator environment with PyYAML (also reused automatically by later manual syncs), installs `claude-code-tools==1.29.1`, syncs skills to both `~/.codex/skills` and `~/.claude/skills`, deploys launchers/runners/model cards, adds PATH and launcher loading to `~/.zshrc`, and installs the launchd shim service. Use `bash install.sh --no-service` to skip service installation. It does not install the Codex/Claude CLIs, log in, create the optional business account home, or start a local model server.

Existing private connection JSON, Codex login and unrelated Codex settings are preserved. Reopen Agent sessions to reload skills, and run `source ~/.zshrc` to load launchers in the current shell.

### Private connections: default and override

`~/.config/agent-tools/endpoints.json` now owns the upstream URL, model ID and API key for each provider/runtime. Keep it private with mode `600`. The installer creates it only when absent; sync never creates or changes it. Project defaults in `config/endpoints.example.json` contain no cloud credentials and are deployed separately. Existing default URLs and model choices remain the initial values; the examples below do not select a new gateway automatically.

- `default`: your baseline connections. Each runtime contains `base_url`, `upstream_model` and `api_key`.
- `override`: optional connections with the same provider/runtime nesting. An override replaces **all three fields together**, so a new gateway cannot inherit an old gateway's key. Other runtimes/providers keep their defaults. Delete that runtime's override to revert.
- Missing files or omitted runtime connections use program defaults; a cloud launch still requires a nonempty key in the effective connection. Existing files must have `default`; unknown fields, incomplete overrides, blank URLs/models, duplicate JSON fields and unsafe permissions fail explicitly. Empty strings do not mean inheritance.

For example, add this connection under `override` to change only `ds-flash_codex` (use the gateway's actual URL/model/key):

```json
{
  "default": {},
  "override": {
    "ds-flash": {
      "codex": {
        "base_url": "https://gateway.example/custom/v1",
        "upstream_model": "gateway/model-id",
        "api_key": "YOUR_GATEWAY_KEY"
      }
    }
  }
}
```

In your initialized file, retain the existing `default` block and add the override; the empty block above only shortens the example. For Codex, `base_url` is the full Responses API base URL without `/responses`. For Claude, it is the Anthropic API base URL without `/v1/messages`; `upstream_model` is passed exactly, without adding `[1m]`. Both use Bearer authentication through their existing mechanisms. Protocols are not translated: a gateway must support streaming/tool calls and the selected API/model. Profile context limits/catalog metadata are retained; confirm the gateway supports those capabilities before switching.

Claude resolves one connection snapshot at launch and passes only its selected token to the Claude process, outside argv/settings JSON. Codex cloud profiles keep their logical model cards/catalogs and loopback provider IDs. The shim resolves one URL/model/key snapshot per request, maps the ordinary logical model and `codex-auto-review` to the configured upstream model, and supplies the selected Bearer token itself. Ordinary streams remain unbuffered; guardian retry behavior remains separate. Upstream redirects are rejected to avoid forwarding a key to another destination. Cloud URL/model/key edits affect the next request without sync or service restart, including app sessions.

`local.codex` remains a direct, unauthenticated connection (`api_key` must be empty); its URL requires `sync-codex-agent.sh`, while its model is applied at CLI/app launch. `local.claude` uses the configured URL/model/token just like other Claude connections; its initial token is `local`. GPT/business profiles continue to use their existing account login and model cards. Gateway API keys are not written into provider registries, catalogs, app config or service plists; account login still uses Codex's auth files. Inherited credential environment variables are still scrubbed; mode `600` does not isolate the file from other processes running as the same user.

## Optional task read restrictions (macOS)

**Platform support:** `agent-sandbox --deny-list` currently supports **macOS only**, using Seatbelt through srt.
This project's Linux envelope is not implemented or tested; Windows is unsupported. On non-macOS systems the command
fails explicitly without falling back to an unsandboxed run. `--full-access` uses native runtime options and does not require Seatbelt.

Normal runner/launcher behavior is unchanged. `--full-access` is opt-in: Codex skips approvals and its inner sandbox;
Claude uses `bypassPermissions` with its inner sandbox disabled. This flag alone does not isolate input.

For filesystem read denials, install the optional dependency after normal installation (Node >=22.12 and npm required):

```bash
install-agent-sandbox.sh
```

This pins Anthropic's Apache-2.0 `@anthropic-ai/sandbox-runtime` to 0.0.79. Normal installation/sync does not install or require srt.
The envelope requires the installed **Node package CLI** (not a standalone srt executable). Sync deploys its adjacent
`agent-sandbox-launch.mjs` adapter. It groups sibling literal/subpath conditions within each deny rule into bounded, exact regex unions to avoid
Seatbelt's literal data table limit; it preserves every path, descendant coverage, rule order and operation.
It retains the generated source as `seatbelt.source.sb` when compacting, saves the effective policy
as `seatbelt.sb`, and loads it with `sandbox-exec -f`, avoiding inline-argv `spawn E2BIG`.
Their original paths deny writes/moves, but hard-link aliases can alter retained files after loading;
this does not change the loaded kernel policy. Before spawning, the adapter prints `profile_sha256`
and `source_sha256` to envelope stderr. The caller must collect that stream through a trusted parent
pipe and compare retained files against those hashes before using them as evidence; an Agent-writable
log or the retained files alone do not prove integrity. Keep the first adapter `seatbelt_profile=`
record in envelope stderr, before runner startup; later duplicates can be child-authored and must
never overwrite it (do not use last-wins parsing). When no compaction occurs, only `seatbelt.sb`
is retained and the source/effective hashes are identical.
Preflight and launch share a non-spawning package/module-layout check; preflight validates the layout before executing `srt --version`. Unsupported CLI layouts fail closed. Native macOS policy compiler limits still apply; a compiler failure stops
the run before verification/runner startup and does not remove denies or grant additional permissions.
Both helper commands are deployed by `scripts/sync-agent-tools.sh`. Tested with Codex 0.161.0 and Claude Code 2.1.294 on macOS.

Create `denied.json` containing a nonempty JSON array of **absolute, existing** files/directories. Entries are literal regular-file paths;
directories are recursive. Include every known forbidden history/report copy yourself. Unlisted copies remain readable.

```bash
agent-sandbox --cwd /path/to/workspace --deny-list /path/to/denied.json -- \
  codex-agent-run --provider mimo --prompt-file /path/to/task.md \
  --output /path/to/new-events.jsonl --stderr /path/to/new-stderr
# claude-agent-run works through the same envelope.
```

Valid symlink targets keep strict stdlib canonicalization. For a dangling symlink discovered while scanning a denied directory,
only a confirmed ENOENT uses `os.path.realpath(strict=os.path.ALLOW_MISSING)`; this capability is required for that branch
and its absence produces a located setup failure, with no installation or fallback (the Python 3.11+ minimum is unchanged).
Missing-aware canonicalization can reach an existing target after `..`; setup reports and conservatively denies that target,
without claiming the raw link is currently reachable. Subsequent non-ENOENT errors fail with declared/link/raw-target context;
stdlib resolution and kernel open need not report the same error first.

A final missing target remains denied, together with its nearest existing directory ancestor, recursively for reads and writes.
That ancestor is scanned through the same symlink expansion graph; further dangling links can add ancestors in other trees.
Each expansion reports its origin and discovery directory. This can block siblings, enlarge scanning or conflict with required
inputs; root ancestors, unreadable/unsupported targets, scan failures and input conflicts stop setup without relaxing the policy.
Verification first queries and actually proves denial of every existing boundary. Only a registered missing target covered by
an actually verified ancestor may return ENOENT; ENOENT or a denied-looking query alone is never isolation proof. Allowed
probe reads and writes must still succeed before the fixed runner starts.

The envelope adds `--full-access --no-persist`, fixes the policy before launch, and checks the denial **inside Seatbelt** before starting the runner.
It rejects unsupported arguments, declared missing paths, incompatible srt, pre-existing hardlinks and configurations whose original write boundary
cannot be preserved. It keeps a conservative subset of the runtime's original writes: Codex read-only retains no cwd writes;
workspace-write retains cwd with `.git/.codex/.agents/.aws` protected. Additional write roots are not carried over. Claude retains cwd
and absolute/home-relative literal sandbox `denyWrite` rules across discovered settings layers. Only explicitly selected output **files**, plus private per-run state, are added; their parent
directories are not granted. Codex permission profiles/project-layer configs and Claude custom read, glob/relative write or tool deny rules are currently unsupported. User Codex `.rules` are copied into the fresh home and protected against writes.
Required credential/config files (including endpoints JSON and selected Codex auth) must remain readable for runtime startup. Listing them as denied stops setup; this wrapper does not isolate credentials from the Agent or its tools. Denied paths also become unwritable. The process exits on setup or verification failure, with no unsandboxed fallback.

Isolated Codex HTTPS prepares explicit CA input in both `--check` and launch. Nonempty
`CODEX_CA_CERTIFICATE` takes priority over nonempty `SSL_CERT_FILE`; exactly empty values fall through,
while whitespace remains a literal path (CA behavior verified on Codex 0.162.1). When neither is effective,
the wrapper selects `/etc/ssl/cert.pem`. Only the selected input is checked; a bad explicit input fails
with its source/path and is never replaced by a lower-priority bundle. Relative paths use `--cwd`,
exported literal `~` is not expanded, and the child receives the canonical path without changing the parent env.

Inputs must be permitted, readable regular PEM files with one or more `CERTIFICATE` and/or
`TRUSTED CERTIFICATE` entries. Every recognized certificate is syntax-checked; malformed companions fail.
Trusted labels are normalized only in memory for validation; native Codex reads the original file and AUX data.
`X509 CRL` entries are ignored, with no revocation validation. Surrounding comments and noncertificate
entries (including CSRs) are ignored and do not count as certificates. Setup does not prove endpoint trust,
kernel enforcement or full native parser/algorithm equivalence, and grants no extra permissions or network access.

The public system PEM may omit enterprise roots installed only in the macOS keychain; provide an explicit
permitted PEM containing the required roots. The wrapper does not export keychain roots, grant trustd or disable TLS verification.
For example, export an absolute custom bundle path before the envelope command above:

```bash
export CODEX_CA_CERTIFICATE=/absolute/path/to/permitted-ca.pem
```

Original task restoration and large deny-list verification remain with the caller after deployment;
this work does not merge or sync a live installation.

This envelope uses fresh runtime state, disables host integrations (MCP/hooks/plugins/browser tools), blocks Apple Events/Unix sockets,
and restricts network access to the selected model route. Claude tools are Bash/Read/Write/Edit/Glob/Grep; Codex native local tools
remain available. Optional `--allow-domain host[:port]` adds a caller-authorized network destination. Permission failures report missing
access; the runner does not expand the policy. Per-run policy/evidence paths are printed to stderr and retained under the temporary directory.
Do not let another unsandboxed process replace denied paths or create readable copies during a run. Path denial does not identify identical
content elsewhere or isolate information already supplied in prompts. A runtime upgrade needs boundary tests before claiming coverage.

Preflight supports `--deny-list /absolute/denied.json` and prints the wrapped command; `--check` validates setup only, not kernel enforcement.
Launch the envelope outside the **controller's** sandbox: Codex uses `exec_command` with `require_escalated`; Claude must add
`agent-sandbox` to its own `sandbox.excludedCommands` and invoke it as a standalone bare command. Lifecycle and explicitly selected result checks still apply.
There is no resume, dynamic input delivery or native argument passthrough in an isolated invocation. Exactly one nonempty `--prompt` or regular `--prompt-file` is required; stdin is closed and the prepared prompt is copied to protected per-run state. Verification queries Seatbelt itself as well as actual file opens; ordinary Unix permission errors are insufficient proof.

## Prepare Agent Environment

If `install.sh` completed successfully, skip the manual deployment steps in this section: it has deployed the launchers/runners and model cards and configured shell loading. You still need to set API keys and any custom URLs as described above, then run `source ~/.zshrc` (or open a new shell) to load the launchers; also reopen Agent sessions to reload skills. The optional `business` profile and local models still require their account home or local service to be prepared separately. The steps below are for manual installation or later updates.

The versioned sources are `scripts/agent-tools.zsh`, `scripts/claude-agent-run`, and `scripts/codex-agent-run`. Their
installed copies live under `~/.config/zsh` and `~/.local/bin`; edit the repository sources and sync them rather than
editing installed copies.
`sync-agent-tools.sh` also installs the URL helper, default URL resources and `repair-codex-reasoning-history.py` to `~/.local/bin`.

Prerequisites:

- `zsh`, `claude`, `codex`, `jq`, and `curl` are available on `PATH`.
- `python3` 3.11 or newer is required for URL resolution and the `--resume` repair option; `agent-endpoint.py` must be on `PATH` alongside the runners.
- `~/.local/bin` is on `PATH` so the child-agent runners can be invoked by name.
- The selected cloud runtime has a nonempty `api_key` in the private connection JSON.
- Each Codex profile has its model card deployed at `~/.codex/<agent-id>.config.toml` (`business` excepted: `~/.codex-agent/business/config.toml`).
- Local service URLs come from `local.claude.base_url` and `local.codex.base_url` under `default` or `override` in `~/.config/agent-tools/endpoints.json`, defaulting to `http://127.0.0.1:8080`; health checks use the matching runtime URL plus `/health` (Codex first removes a terminal `/v1`), so Claude and Codex can use different local ports.

Keep credentials only in the private connection JSON, outside the repository.

Install or update the launcher and child-agent runners:

```bash
./scripts/sync-agent-tools.sh
```

Load it from `~/.zshrc`:

```zsh
[[ -r "$HOME/.config/zsh/agent-tools.zsh" ]] && source "$HOME/.config/zsh/agent-tools.zsh"
```

Reload the current shell after syncing:

```bash
source ~/.zshrc
```

Available launchers:

| Runtime | Agent IDs | Commands |
| --- | --- | --- |
| Claude Code | `ds-flash`, `mimo`, `mimo-fast`, `mimo-flash`, `qwen`, `kimi`, `glm`, `glm-flash`, `local`, `hy` | `<agent-id>_claude [args...]` |
| Codex CLI | `ds-flash`, `mimo`, `mimo-fast`, `mimo-flash`, `qwen`, `kimi`, `glm`, `glm-flash`, `local`, `gpt-6-astra`, `gpt-6-sol`, `gpt-6-luna`, `business` | `<agent-id>_codex [args...]` |
| Codex app | Same as Codex CLI | `<agent-id>_codex_app [workspace]` |

Pass `--title` to a CLI launcher to set a stable tmux pane title such as `ClaudeAgent-DS-Flash` or `CodexAgent-GPT-6-Astra`.
`hy` (hy4-preview on tokenhub.tencentmaas.com, with its JSON `api_key`) is **Claude-runtime only**: the gateway's `/v1/responses` SSE
upstream proved too unreliable for Codex auto-review escalations (2026-09-24), so the Codex-side profile was dropped.
The app launchers open a new Codex app instance with the selected profile and optional workspace. The desktop app reads `$CODEX_HOME/config.toml` in full (no `-p` layering), so each managed app instance gets its own **composed home** under its user-data directory (shared base + the selected model card, composed idempotently at launch by `compose-codex-app-config.py`) — the app starts on the selected model. These app homes have separate session histories. To continue a CLI conversation on another model, use the shared-home CLI with an explicit profile, for example `gpt-6-sol_codex resume <session-id>` or `codex resume -p gpt-6-sol <session-id>`.

```bash
mimo_claude --title
gpt-6-astra_codex --title
business_codex_app /path/to/workspace
```

`tmux-agents` discovers these pane titles but does not assign roles. Put the desired assignment in the current user
prompt.

For non-interactive child-agent calls, use the installed runner commands:

```bash
claude-agent-run --provider mimo --cwd /path/to/workspace --prompt-file task.md
codex-agent-run --provider gpt-6-astra --cwd /path/to/workspace --prompt-file task.md
```

The runners accept prompts through `--prompt`, `--prompt-file`, positional text, or stdin, and support output files,
ephemeral or persistent sessions, and provider-specific passthrough arguments. Run either command with `--help` for the
complete interface. Orchestrators must always pass `--cwd` explicitly so child agents do not accidentally inherit the
controller's workspace.

Direct runner calls are the ordinary path. Private logs and a Claude instance identity are generated automatically;
no separate preflight, label, fixed prompt headings, runtime/provider/model self-report, canary or extra report is required.
Provide sufficient task context: child agents do not inherit the controller conversation. For file deliverables, ask for
paths in the final answer and use/verify the files according to the task. Existing source edits need no separate artifact report.

`sub-agent-preflight` is an optional early setup check and command generator:

```bash
sub-agent-preflight --runtime codex --provider gpt-6-sol --cwd /path/to/workspace --task-file task.md
```

It checks only the selected runner/provider/launcher/profile, creates a private run directory and auto label, copies the
task and appends a brief final-answer instruction. Exactly one non-whitespace `--task`, `--task-file` or `--prompt-file`
is required; no headings are prescribed. It prints `key=value` and a quoted runnable command on success, no command on
failure. `--label` is optional. Add `--canary` only when a file-read proof is needed; by default no proof files or arguments
are created. The token is never printed or embedded in the prompt.

### Runner results

After actual runtime exit, the runner returns one schema-v2 JSON report on stdout with `final_answer`, diagnostics, full log
paths and statistics. `--output` / `--stderr` retain raw logs, even when stdout returns the summary; omitted destinations
get private files. Explicit `-` destinations (`--output`, `--stderr`, Codex `--last-message`) require `--detail`;
collected mode rejects them instead of silently replacing them. Claude uses stream-json internally. Wait for the managed process handle's exit, then consume the final
answer and task artifacts. This adds no mid-run channel or automatic completion notification.

```bash
codex-agent-run --provider mimo --cwd /path/to/workspace --prompt-file task.md
claude-agent-run --provider ds-flash --cwd /path/to/workspace --prompt-file task.md
# Raw output and original redirection behavior:
codex-agent-run --provider mimo --cwd /path/to/workspace --prompt-file task.md --detail
```

The outer exit is the actual native CLI exit, including nonzero 1/2/126/127. Final prose explaining missing input,
blocked work or inability is a normal reply. Missing artifacts, canary mismatches, tool errors, damaged logs and protocol
observations never change a known native exit. The caller owns task acceptance and any further interactions under its
user/project authorizations and routing rules. Preserve attempts/logs and measurement batch membership/concurrency;
a retry must not replace a failed measured sample. No automatic retry or provider switch is added.

Collected schema version **2** has these fields:

| Fields | Meaning |
| --- | --- |
| `schema_version`, `source`, `runtime`, `provider` | `2`, `subagent_report`, selected runtime/provider. |
| `runtime_exit_code`, `final_answer` | Actual native exit and **full, untruncated** native text, preserving whitespace and Unicode. |
| `session_id`, `terminal` | Observed native identity and terminal type/subtype; null when unavailable/ambiguous. |
| `wall_clock_seconds`, `usage`, `runtime_metrics` | Measured time to collection invocation; single-terminal native totals and Claude duration/cost/modelUsage. Missing values are null/empty, genuine zero remains zero; streaming fragments are not summed. |
| `logs` | Absolute `output`, `stderr`, optional `last_message` paths. Raw partial material remains in logs. |
| `diagnostics` | One list of `{message, path, line}` facts. Warning text is opaque and preserved verbatim with its source; wording never changes behavior. No severity/status classifier or text-based recovery inference. |
| `checks` | `artifacts: [{path, exists, regular_file}]`; `canary: null` unless requested, otherwise `{proof_observed, proof_matches_expected, read_candidate_observed}`. Matching is null when no comparable proof is available. |

Migration from v1: remove dependencies on `agent_status`, `validation_status`, `result_status`, `runner_exit_code`,
`final_answer_chars`, `final_answer_truncated`, the three diagnostic classes/counts/truncation fields and tool/event
rollups. Use `runtime_exit_code`, `final_answer`, source diagnostics and `checks`; missing files/check observations no
longer produce rejection exits. No replacement wrapper verdict exists. The collector itself exits 0 when it successfully
serializes observations, including missing/malformed sources; its process exit is not task acceptance.

Codex's latest completed agent message owns final; Claude's unique root `result` string owns final. Claude assistant
text and nested results never substitute. Missing/nontext/ambiguous final is null; an observed empty string stays empty.
An identifiable final remains available despite negative native metadata or unrelated damaged frames. Missing/conflicting
identity or terminal is diagnostic information. Only explicitly persisted sessions can be resumed; an ID does not imply
an ephemeral run was saved. Usage/metrics require an unambiguous native terminal.

Before native exec, argument/input/path/dependency/launcher failures return setup code 2, with cause and allocated log
paths on stderr and no invented native report. If the wrapper cannot execute/serialize/write the primary result after
native exit, stderr reports that delivery failure, known native code and retained paths; outer exit is 1 for native 0,
or the exact native nonzero. Codex auxiliary `--last-message` missing/copy/race/cleanup problems preserve native exit,
retain available temporary source and report its location; existing destinations are never clobbered. `--detail` returns
raw streams, skips collection and optional post-run checks, and keeps the same native exit behavior.

`AGENT_TOOLS_FILE` remains supported, but custom launchers must explicitly implement **pre-exec-error-v1**. After sourcing,
`_agent_tools_runner_contract` must print exactly `pre-exec-error-v1` and return 0 only when its terminal helper supports
that contract. Under runner invocation, `AGENT_RUN_ERROR_FD` names an internal error-only pipe: report any return/failure
before native exec there, and close it on successful exec (CLOEXEC), removing that variable from the native environment.
No success messages or post-exit protocol are used. Repository launchers use `agent-endpoint.py` for terminal exec; the
capability check detects helper skew before launch. Unsupported/stale custom launchers fail as setup before running.
Ordinary interactive launcher calls without the internal descriptor retain their behavior. Sync runners, launchers and
helper together; native attribution is never inferred from missing events, numeric sentinels or warning prose.

Optional repeatable `--artifact /path/to/new-file` requires a fresh path before dispatch. Post-run existence, file type,
hard links/log aliases and read errors are observations; they do not prove provenance or content. No artifact option
means no automatic extraction of final-answer paths. Paired `--canary-file` / `--canary-expected` validate readable,
nonempty regular inputs and a valid token before launch; preflight `--canary` supplies the pair. Proofs are standalone,
unindented `CANARY=<token>` lines outside code blocks. A match and candidate read trace do not prove task correctness;
secondary proof-line offsets are included in diagnostic messages. Under `agent-sandbox`, checks stay within existing
boundaries. `text` output and Claude `json` are available with `--detail`.
See [advanced sub-agent calls](skills/sub-agents/references/advanced.md) when selecting these capabilities.

## Codex Agent Profiles

All managed profiles share one Codex home (`~/.codex`, Codex's default home — it must be a real directory; the desktop app's sandbox rejects symlink components in its writable paths): the base
`config.toml` carries policy and machine-local runtime state, and each profile is a model card at
`~/.codex/<agent-id>.config.toml` layered in with `codex -p <agent-id>` — picking a card at launch
is model switching, and the session pool is shared. Resume through the target model's launcher
(`gpt-6-sol_codex resume <session-id>`) or pass `-p` explicitly
(`codex resume -p gpt-6-sol <session-id>`). Plain `codex resume <session-id>` can restore the
session's last selected model instead of the base config's default. The nine
third-party profiles (`ds-flash`, `glm`, `glm-flash`, `kimi`, `mimo`, `mimo-fast`, `mimo-flash`, `qwen`, `local`) and the three subscription-backed OpenAI
profiles (`gpt-6-astra`, `gpt-6-sol`, `gpt-6-luna`) are versioned in this repository under `codex-agent/profiles/`;
`business` keeps its own CODEX_HOME (`~/.codex-agent/business`, a separate account). The shared base config remains
machine-owned except for the marked provider registry managed by this repository.

To repair and resume a cross-model session in one step, close other Codex clients using it and run
`gpt-6-sol_codex resume <session-id> [prompt]` or `gpt-6-sol_codex --resume <session-id> [prompt]`
(replace the launcher with the intended target model; `--resume=<session-id>` also works).
Both launcher forms find the session under its Codex home, save a private backup when needed, and remove reasoning records
from turns whose model differs from the target card, then runs `codex resume` with that card. Messages and tool history
remain; reasoning and summaries from other models are unavailable in the repaired session but remain in the backup.
If there is nothing to remove, the session is left untouched and no backup is created.
Run `./scripts/sync-agent-tools.sh` and open a new shell before using this option. Bare `resume` and Codex resume options
such as `--help` or `--last` still go directly to Codex because no session ID has been selected for repair.

`gpt-6-astra` is kept for important, low-volume work; `gpt-6-sol` runs the high-volume daily tasks and
`gpt-6-luna` the low-cost bulk work. Astra defaults to high reasoning effort, Sol to xhigh,
and Luna to max. The `gpt-6-sol` profile selects GPT-6.1 Sol. `sync-codex-agent.sh`
copies the Sol card's model and effort defaults (GPT-6.1 Sol / xhigh) into the separate
`business` CODEX_HOME, leaving its account and other local settings intact.
`gpt_codex` is an alias for `gpt-6-sol_codex`, including its resume handling and arguments.

| Profile | Model | Gateway | Shim port | Gateway fix |
| --- | --- | --- | --- | --- |
| `ds-flash` | `deepseek-flash` | api.deepseek.com | 8788 | model-name rewrite + patched catalog |
| `glm` | `glm-5.3` | open.bigmodel.cn | 8789 | model-name rewrite + patched catalog |
| `glm-flash` | `glm-5.3-flash` | open.bigmodel.cn | 8795 | model-name rewrite + patched catalog |
| `kimi` | `k3` | api.kimi.com | 8790 | + patched catalog |
| `mimo` | `mimo-v2.6-pro` | token-plan-cn.xiaomimimo.com | 8791 | + patched catalog + `json_object` downgrade |
| `mimo-fast` | `mimo-v2.6-pro-ultraspeed` | api.xiaomimimo.com | 8794 | + patched catalog + `json_object` downgrade |
| `mimo-flash` | `mimo-v2.6-flash` | token-plan-cn.xiaomimimo.com | 8793 | + patched catalog + `json_object` downgrade |
| `qwen` | `qwen3.8-max` | dashscope.aliyuncs.com | 8792 | + patched catalog + message-id prefix fix |
| `local` | `qwen3.8-27b-local` | user-configurable (default 127.0.0.1:8080) | none | patched catalog, runs unsandboxed, no shim |
| `gpt-6-astra` | `gpt-6-astra` | OpenAI (ChatGPT login) | none | no shim, subscription-backed |
| `gpt-6-sol` | `gpt-6.1-sol` | OpenAI (ChatGPT login) | none | no shim, subscription-backed |
| `gpt-6-luna` | `gpt-6-luna` | OpenAI (ChatGPT login) | none | no shim, subscription-backed |

Cloud credentials come from the private connection JSON and are added by the shim. `local` needs none; the three OpenAI profiles share the shared home's `auth.json`, and `business` keeps its own login under `~/.codex-agent/business/`.

Set up or update the profiles:

```bash
# install profiles, shim scripts, routes, and regenerate the model catalogs
./scripts/sync-codex-agent.sh

# optional but recommended: keep the shim running as a launchd service
~/.codex-agent/bin/codex-auto-review-shim-service install
```

After restoring the agent environment on another Mac, run `install` again. It discovers that machine's Python 3.11+
interpreter, rewrites the launchd plist, and reloads an existing service. `restart` only restarts the current plist.
Run `./scripts/sync-codex-agent.sh` from an updated checkout to deploy the service, connection helper and default resources. Missing connection files use credential-free project defaults; initialize and fill cloud keys before launching. Existing custom files are preserved.

The tracked templates write machine paths as `@HOME@`; the sync script substitutes your home directory on
install (Codex accepts only absolute paths in these fields).

Model cards carry only model deltas (model, `model_provider`, reasoning effort, context/compact windows,
`web_search`, `model_catalog_json`). The nine third-party gateway definitions live in
`codex-agent/model-providers.toml`; sync installs them as a marked block in the shared base config so resume can
resolve a provider used earlier in the same conversation. `glm-flash`, `mimo-fast`, and `mimo-flash` now have distinct
provider IDs because they use distinct gateway ports. Legacy sessions recorded with the shared `glm` or `mimo` IDs
cannot identify which variant created them; those IDs retain the normal `glm` and `mimo` routes.
Keep retired provider IDs in the registry with their last usable routes; deleting an ID breaks resume for sessions that recorded it.
Policy (sandbox, approvals, shell environment
policy, `service_tier`, …) and the per-machine state Codex itself and the ChatGPT desktop app write —
`[projects.*]` trust entries, `[hooks.state]`, `[mcp_servers.*]`, `[plugins.*]`, `[marketplaces.*]`,
`[tui.*]`, `[desktop]`, and root-level keys such as `notify` — stay in the shared home's base `config.toml`.
The sync script changes only its marked provider block and refuses to overwrite a matching provider ID outside it.
Cards are pure artifacts and are overwritten wholesale on sync. To change
one model's setting, edit its card in the repo and re-sync (layering makes card keys win over base).

`model-catalogs/<id>.json` remain **generated, untracked outputs**. The eight cloud profiles
use byte-verified [official source snapshots](codex-agent/catalog-sources/README.md), preserving
complete source metadata and instructions. Each appends only an independently obtained bundled native
guardian; cloud sessions have no GPT donor. `glm-flash` is a user-authorized clone of official `glm-5.3`,
labelled derived for `glm-5.3-flash` with only its three identity fields changed; it does not switch to Turbo.
Kimi's card and shim logical slug are `k3`; endpoint-owned URL/key/upstream model stay independent.
Qwen uses context **983616** and compact limit **737712**, preserving its absent maximum. Other cloud
cards retain 1048576/786432. All eight efforts stay **max**. Official advertised/default levels stay intact:
MiMo's snapshot omits max (user reports official confirmation); Qwen advertises low/medium/xhigh.
Informational notes expose these differences. Mock forwarding is not vendor acceptance.

DS/GLM/Kimi/Qwen guardian transport uses direct tools with Lite disabled; MiMo retains native
Code Mode/Responses Lite and `additional_tools`. Native 0.162.1 has stable/default-true
`code_mode_host`; its key stays omitted, including isolation's existing `code_mode=false` configuration.
Required Code Mode needs the installed native host and a working kernel sandbox. Explicit host false
fails visibly. MiMo's route-wide `json_schema` → `json_object` downgrade applies to ordinary sessions
and guardians and loses schema enforcement. The local profile alone retains the compatible native
direct-session donor, chosen by capabilities rather than a fixed model ID; GPT/business are unchanged.

The generator gets the native source with `codex debug models --bundled` in an empty home, then validates
every assembled catalog with `codex -c model_catalog_json=... debug models` in another empty home.
Native parsing owns nested schema. Missing mappings, source/hash/card mismatches or native rejection fail
before registry/card/catalog replacement. Sync backs up all replaced cards/catalogs and registry bytes,
installs each pair and verifies installed bytes. Ordinary copy/replace/registry/verification failure restores
prior bytes/modes/absence; restoration failure reports an error and retains backups. This does not guarantee
atomic cross-file visibility, concurrent-writer coordination, SIGKILL/power-loss recovery or recovery from
restoration I/O failure. Later shim/service/business deployment is outside this recovery block.

Focused validation (synthetic endpoints only):

```bash
python3 -m unittest discover -s tests -p 'test_model_catalog_generation.py'
OFFICIAL_CATALOG_RUNTIME_TESTS=1 python3 -m unittest discover -s tests -p 'test_official_catalog_runtime.py'
```

Native read/write/collection and kernel tests require a parent that permits Seatbelt execution.
For the official MiMo outer-boundary case, also set `AGENT_SANDBOX_KERNEL_TESTS=1` and
`SRT_TEST_BIN=/absolute/path/to/srt` (installed 0.0.79). Missing prerequisites remain failures/unverified,
with no weaker fallback. [Implementation evidence](docs/gateflow/official-provider-catalogs/implementation.md)
records actual outcomes; vendor acceptance and desktop/future-runtime compatibility are separate checks.

### Repairing reasoning history for cross-provider resume

A third-party Responses provider can save `reasoning_text` in a reasoning item's `content` array. The official OpenAI
endpoint rejects that history on resume with `Invalid 'input[n].content': array too long` (see [upstream issue #36551](https://github.com/openai/codex/issues/36551)). Close every Codex client using the session, then locate its rollout file under `~/.codex/sessions/` and run:

```bash
python3 scripts/repair-codex-reasoning-history.py /path/to/rollout-<session-id>.jsonl
python3 scripts/repair-codex-reasoning-history.py /path/to/rollout-<session-id>.jsonl --apply
# If cross-provider resume then reports invalid_encrypted_content or a missing reasoning item ID:
python3 scripts/repair-codex-reasoning-history.py /path/to/rollout-<session-id>.jsonl --drop-reasoning-model k3 --drop-reasoning-model kimi-k3 --drop-reasoning-model mimo-v2.6-pro
python3 scripts/repair-codex-reasoning-history.py /path/to/rollout-<session-id>.jsonl --drop-reasoning-model k3 --drop-reasoning-model kimi-k3 --drop-reasoning-model mimo-v2.6-pro --apply
```

The first command only counts affected items. `--apply` changes only reasoning items whose nonempty `content` consists
entirely of `reasoning_text`, setting that field to `null`; it saves a private timestamped backup beside the rollout
before replacing the file. Third-party encrypted reasoning may still fail validation, or its item ID may not exist on
OpenAI's endpoint. In that case, use `--drop-reasoning-model` for each source model: it removes only reasoning records
from those models' turns, keeping messages and tool history. Their private reasoning and any reasoning summaries in those
records are lost from the repaired rollout, but remain in the timestamped backup. The second run of each repair reports zero affected items.
Flags match the exact logical model name recorded in `turn_context`, not the endpoint's upstream wire model or a profile alias.
The examples cover current Kimi `k3`, legacy Kimi `kimi-k3`, and MiMo `mimo-v2.6-pro`; a zero-match model produces a warning.
Both the repaired rollout and its backup have owner-only permissions (`0600` when the original is writable by its owner).
Reopen the session with the target model's profile after repair. If the tool reports unsupported reasoning content or malformed JSONL, it leaves the rollout
unchanged; inspect that line separately. To roll back, close the session again and copy the reported
`rollout-*.jsonl.backup-<timestamp>` file over the rollout. Keep the backup until the resumed conversation works.

### Switching sandbox mode

The shared home's base `config.toml` defines the default sandbox: `"workspace-write"` — writes confined to the
workspace, `[sandbox_workspace_write] network_access = true` keeps the network open (requires the shim to be
running). For a per-model exception, set `sandbox_mode` in that model's card to override base — this is how
`local` gets `"danger-full-access"` (no sandbox; used from a terminal, not dispatched as a sub-agent). Re-run
`./scripts/sync-codex-agent.sh` after editing a card.

`local` connects directly to `local.codex` (default `http://127.0.0.1:8080/v1`); its route is in the shared provider registry.

## Usage

### Gateflow

Use `gateflow` for one work unit: a feature, issue, bug fix, migration, refactor, schema/public contract change, or
architecture-sensitive task. Gateflow defines the gates only: preflight, goal confirmation, necessary planning and
applicable plan review, implementation/validation, one complete code review, necessary fixes and affected re-review,
draft PR delivery checks, and final closeout.

Standalone Gateflow example:

```text
Develop <work-unit> with $gateflow.
Optional design basis: docs/host/design.md.
Start with preflight and goal confirmation; after the user confirms goals, non-goals, and boundaries, advance through the Gate Order to final closeout.
Strictly follow the constraints in AGENTS.md.
```

Gateflow with `tmux-agents` example:

```text
Develop <work-unit> with $gateflow.
$tmux-agents routes Agents: CodexAgent-GPT-6-Astra handles plan / implement / fix, while CodexAgent-MiMo / ClaudeAgent-DS-Flash run required independent reviews in parallel and affected re-review when needed.
Re-discover panes before every send, clear the session for new tasks, and avoid bare #numbers.
Strictly follow the constraints in AGENTS.md.
```

Gateflow with `sub-agents` example:

```text
Develop <work-unit> with $gateflow.
$sub-agents dispatches through runner subprocesses: Codex gpt-6-astra handles plan / implement / fix, while Codex mimo / Claude ds-flash run required independent reviews in parallel and affected re-review when needed.
Pass the workspace absolute path explicitly in every call and use separate output / stderr files; the controller checks the structured results and adjudicates itself.
Strictly follow the constraints in AGENTS.md.
```

### Phaseflow

Use `phaseflow` when a project has a design source document and an implementation control document. Phaseflow is the
project step controller: it reads the current `phase = work unit`, performs preflight and goal confirmation with the user,
reads Gateflow's `Gate Order`, checks simple plans and PR delivery itself, dispatches concrete work and applicable reviews
to Agents, adjudicates results, updates `control_doc`, and reconciles residual risks.

Standalone Phaseflow example:

When no dispatch protocol is named, Phaseflow uses `sub-agents` by default. Use `$tmux-agents` explicitly to route through
already-running tmux panes.

```text
Proceed with $phaseflow; the design source of truth is docs/host/design.md, and the control document is docs/host/issues-implementation-control.md.
Read control_doc first to identify the current phase/work unit, then read design_doc.
The controller Agent completes preflight and goal confirmation first; after user confirmation, follow Gateflow's Gate Order, check simple plans and PR delivery, and dispatch concrete work and applicable independent reviews to Agents.
After each gate returns, update control_doc and record the artifact / finding adjudication / residual risk.
After final closeout, explain that the user merges the PR, pulls the target base branch, and continues the next round from the next entry point in control_doc.
Strictly follow the constraints in AGENTS.md.
```

Phaseflow with `tmux-agents` example:

```text
Proceed with $phaseflow; the design source of truth is docs/host/design.md, and the control document is docs/host/issues-implementation-control.md.
$tmux-agents routes Agents: CodexAgent-MiMo / ClaudeAgent-DS-Flash run required independent reviews in parallel and affected re-review when needed, while CodexAgent-GPT-6-Astra handles plan / implement / fix.
The controller Agent completes preflight and goal confirmation first; after confirmation, follow Gateflow's Gate Order, checking simple plans and PR delivery itself.
After each Agent returns, the controller reads the artifact, adjudicates findings, updates control_doc, collects residual risks, and closes resolved risks.
After final closeout, explain that the user merges the PR, pulls the target base branch, and continues the next round from the next entry point in control_doc.
Strictly follow the constraints in AGENTS.md.
```

Phaseflow with `sub-agents` example:

```text
Proceed with $phaseflow; the design source of truth is docs/host/design.md, and the control document is docs/host/issues-implementation-control.md.
$sub-agents dispatches through runner subprocesses: Codex mimo / Claude ds-flash run required independent reviews in parallel and affected re-review when needed, while Codex gpt-6-astra handles plan / implement / fix.
The controller follows Gateflow's Gate Order, checks simple plans and PR delivery, checks each subprocess's exit status and structured output, and updates control_doc.
Strictly follow the constraints in AGENTS.md.
```

### Planreview

Use `planreview` for important decisions or explicit review requests. Check whether the plan gives enough direction for
correct implementation, uses only necessary slices and mechanisms, and addresses proven root causes without prescribing local code details.

Codex:

```text
$planreview docs/path/to/plan.md
```

Claude Code:

```text
/planreview docs/path/to/plan.md
```

Expected output is a durable review artifact, usually under `docs/reviews/` or a project-specific review directory.

### Deepreview

Use `deepreview` for strict code review.

Review current branch changes against `main`:

```text
$deepreview
```

Equivalent explicit form:

```text
$deepreview --base main
```

Review a PR:

```text
$deepreview --pr 123
```

Review the whole repository:

```text
$deepreview --all
```

For Claude Code, use `/deepreview` with the same arguments.

Expected output is a durable review artifact with evidence-based findings, status tracking, and residual risk notes.

### Tmux Agents

Use `tmux-agents` when work should be sent to already-running CLI agents through tmux panes. It only defines communication:
CLI type, `/skill` vs `$skill`, pane discovery, clear/session rules, `tmux-cli send/wait_idle/capture`, and send safety.
It does not assign roles.

Codex:

```text
Use $tmux-agents to initialize multi-agent communication conventions.
```

Claude Code:

```text
Use /tmux-agents to initialize multi-agent communication conventions.
```

`tmux-agents` works through:

```bash
tmux-cli status
tmux-cli send "<prompt>" --pane=<full-pane-id>
tmux-cli wait_idle --pane=<full-pane-id> --idle-time=3 --timeout=<seconds>
tmux-cli capture --pane=<full-pane-id>
```

It uses `tmux-cli send` + `wait_idle` + `capture` for agent-to-agent chat. `tmux-cli execute` is only for shell commands where an exit code is needed.

### Sub Agents

Use `sub-agents` when the controller should launch external Claude Code or Codex child processes through the installed
runners. The skill covers independent prompt context, explicit workspace, managed parallel execution, final-answer collection,
bounded retries and optional checks/isolation. Task-specific verification remains with the caller.

Codex:

```text
Use $sub-agents to dispatch and adjudicate the current subtasks through runner subprocesses.
```

Claude Code:

```text
Use /sub-agents to dispatch and adjudicate the current subtasks through runner subprocesses.
```

The underlying commands are:

```bash
claude-agent-run --provider <provider> --cwd <absolute-workspace> ...
codex-agent-run --provider <provider> --cwd <absolute-workspace> ...
```

Independent tasks may run concurrently when their write ownership does not overlap. Runners collect execution evidence;
the controller consumes final answers and verifies unresolved issues and deliverables according to task requirements.

## Repository Layout

```text
skills/
  gateflow/
    SKILL.md
    agents/openai.yaml
  phaseflow/
    SKILL.md
    agents/openai.yaml
  planreview/
    SKILL.md
    agents/openai.yaml
  deepreview/
    SKILL.md
    agents/openai.yaml
  tmux-agents/
    SKILL.md
    agents/openai.yaml
  sub-agents/
    SKILL.md
    agents/openai.yaml
codex-agent/
  model-providers.toml
  profiles/
    ds-flash/config.toml
    glm/config.toml
    glm-flash/config.toml
    kimi/config.toml
    mimo/config.toml
    mimo-fast/config.toml
    mimo-flash/config.toml
    qwen/config.toml
    local/config.toml
    gpt-6-astra/config.toml
    gpt-6-sol/config.toml
    gpt-6-luna/config.toml
  bin/
    codex-auto-review-shim
    codex-auto-review-shim-service
  shim-routes.json
install.sh
config/
  endpoints.example.json
scripts/
  agent-endpoint.py
  validate-skill.py
  agent-tools.zsh
  claude-agent-run
  codex-agent-run
  compose-codex-app-config.py
  sub-agent-preflight
  sync-codex-providers.py
  patch-codex-model-catalog.py
  repair-codex-reasoning-history.py
  sync-codex-model-defaults.py
  sync-agent-tools.sh
  sync-codex-agent.sh
  validate-skills.sh
  sync-skills.sh
tests/
  test_install_endpoints.py
  test_codex_model_defaults.py
  test_provider_registry.py
  test_repair_codex_reasoning_history.py
```

## Maintenance

Edit only the source files in this repository:

```text
skills/<skill-name>/SKILL.md
skills/<skill-name>/agents/openai.yaml
install.sh
config/endpoints.example.json
scripts/agent-endpoint.py
scripts/validate-skill.py
scripts/agent-tools.zsh
scripts/claude-agent-run
scripts/agent-run-result.py
scripts/codex-agent-run
scripts/compose-codex-app-config.py
codex-agent/model-providers.toml
codex-agent/profiles/<agent-id>/config.toml
codex-agent/bin/
codex-agent/shim-routes.json
scripts/patch-codex-model-catalog.py
scripts/repair-codex-reasoning-history.py
scripts/sync-codex-model-defaults.py
scripts/sync-codex-providers.py
tests/test_codex_model_defaults.py
tests/test_provider_registry.py
tests/test_install_endpoints.py
tests/test_repair_codex_reasoning_history.py
```

Validate all skills:

```bash
./scripts/validate-skills.sh
```

Check the provider registry sync and desktop migration paths:

```bash
python3 -m unittest discover -s tests
```

Sync to local Codex / Claude homes:

```bash
./scripts/sync-skills.sh
```

Sync the agent launcher and child-agent runners:

```bash
./scripts/sync-agent-tools.sh
```

Sync the Codex agent profiles, shim scripts and routes:

```bash
./scripts/sync-codex-agent.sh
```

The skill sync validates first, then copies every skill directory to existing local targets. The agent-tools sync installs
the launcher to `~/.config/zsh/agent-tools.zsh` with mode `600` and the runners to `~/.local/bin` with mode `755`.
The codex-agent sync updates only the marked provider block in the shared base `config.toml`, writes each model card
wholesale into the shared home (`~/.codex/<agent-id>.config.toml`), installs the shim scripts and routes, and regenerates
the untracked `model-catalogs/`. None of these scripts push, publish, create PRs, or modify remote
repositories.

## Notes

- `gateflow` defines the gates for one work unit.
- `phaseflow` checks simple plans and PR delivery; concrete plan / implementation / fix and applicable independent review work is delegated to Agents.
- `planreview` and `deepreview` are review skills. They should produce durable artifacts, not just chat-only conclusions.
- `tmux-agents` is only needed when you route work to multiple CLI agents through tmux.
- `sub-agents` is used when the controller launches external child agents through the runner subprocesses.
