# code-is-cheap

English | [中文](README.zh.md)

An engineering control framework for automated AI coding. Its core assumption is that architecture, phase/work-unit
boundaries, entry/exit criteria, and implementation control plans are prepared first; after that, agents can execute inside
explicit gates with durable artifacts, review decisions, residual-risk tracking, and accepted checkpoints.

This is not a loose collection of prompts. It is a workflow for putting AI coding inside an engineering loop: confirm goals
and non-goals, plan, review, implement by slices, review code, fix findings, re-review, run aggregate deep review, track
residual risks, create accepted commits, open a draft PR, run PR review, and continue through final closeout. Merge,
approval, marking a PR ready for review, requesting reviewers, deleting branches, public comments, and external issue
changes still require explicit user authorization.

This repository contains local skills and supporting scripts for Codex / Claude Code, covering phase-driven development,
gated feature development, plan review, deep code review, and multi-agent handoff.

This repository is the source of truth for the skills under `skills/`, the agent launcher under
`scripts/agent-tools.zsh`, the child-agent runners under `scripts/*-agent-run`, and the provider registry under
`codex-agent/model-providers.toml`. Local runtime files are installation
targets only. Edit and validate sources here, then sync them out.

## Included Skills

| Skill | Responsibility |
| --- | --- |
| `gateflow` | Defines the gated workflow for one work unit: preflight, goal confirmation, fixed gate order, artifacts, residual risks, accepted commits, draft PR gate, and final closeout. It does not define project-level control documents or multi-agent routing. |
| `phaseflow` | Project step controller. It reads `design_doc` and `control_doc`, identifies the current `phase = work unit`, performs preflight and goal confirmation with the user, reads Gateflow's `Gate Order`, dispatches concrete gates to Agents, adjudicates results, updates `control_doc`, and reconciles residual risks. |
| `planreview` | You want adversarial review of a plan, implementation plan, migration phase plan, feature slice plan, or Gateflow plan. |
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
4. `phaseflow` reads Gateflow's `Gate Order` and dispatches concrete plan / implementation / review / fix gates to Agents.
5. After each Agent return, `phaseflow` reads the artifact, adjudicates findings, updates `control_doc`, and advances to the next gate.
6. After all slices are complete, run aggregate deep review; after fixes and re-review pass, record draft PR readiness and residual-risk ownership.
7. The draft PR gate pushes, creates a draft PR, runs PR review, fixes accepted findings, re-reviews, creates an accepted PR review commit, and pushes again until `draft-PR-pass`.
8. Final closeout then records what changed, what was verified, docs updates, finding status, remaining risks and owners, the draft PR URL, and the next entry point.
9. For issue work units, the draft PR body should link the issue; final closeout should confirm the issue closeout comment and the merge-time closing expectation.
10. After final closeout passes, the user manually merges the PR, pulls the latest target base branch, clears the agent session if desired, and resumes `phaseflow` from the `control_doc` next entry point.

The point is not to let the agent invent architecture on the fly. The point is to let agents execute reliably inside
explicit design boundaries and implementation plans, while leaving durable artifacts for every review conclusion, fix
status, validation result, and residual risk.

## Requirements

- Codex CLI, Claude Code, or another agent runtime that supports local skill-style instruction files.
- Python 3.11+ (invoked as `python3`) and the `pyyaml` package if you want to run the bundled skill validator.
- `tmux` and `tmux-cli` if you use `tmux-agents` for multi-agent handoff.

If you use the zsh agent launcher functions below, their `tmux select-pane -T` calls rely on stable pane titles. Add this to `~/.tmux.conf` first so running programs cannot overwrite the title:

```tmux
# Keep pane titles fixed; do not let running programs overwrite them.
set -gw allow-set-title off
```

`tmux-cli` is part of the `claude-code-tools` package. Install it with:

```bash
uv tool install claude-code-tools
```

Official documentation:

- `tmux-cli`: https://pchalasani.github.io/claude-code-tools/tools/tmux-cli/
- `claude-code-tools` installation: https://pchalasani.github.io/claude-code-tools/getting-started/

## Install

Clone the repository:

```bash
git clone <repo-url> code-is-cheap
cd code-is-cheap
```

Install the Python dependency required by the skill validator:

```bash
python3 -m pip install pyyaml
```

> **Note:** On macOS with Homebrew Python you may need `--break-system-packages`, or use a virtual environment.

Sync skills to any local Codex / Claude skill homes that already exist:

```bash
./scripts/sync-skills.sh
```

The sync script installs to these directories when present:

```text
~/.codex/skills
~/.claude/skills
```

After syncing, start a new Codex / Claude session so the runtime reloads the skill list.

## Prepare Agent Environment

The versioned sources are `scripts/agent-tools.zsh`, `scripts/claude-agent-run`, and `scripts/codex-agent-run`. Their
installed copies live under `~/.config/zsh` and `~/.local/bin`; edit the repository sources and sync them rather than
editing installed copies.
`sync-agent-tools.sh` also installs `repair-codex-reasoning-history.py` to `~/.local/bin`.

Prerequisites:

- `zsh`, `claude`, `codex`, `jq`, and `curl` are available on `PATH`.
- `python3` 3.11 or newer is required for the launcher-only `--resume` repair option.
- `~/.local/bin` is on `PATH` so the child-agent runners can be invoked by name.
- Provider credentials are exported before launching the matching agent:
  `DEEPSEEK_API_KEY`, `MIMO_PLAN_API_KEY`, `QWEN_API_KEY`, `KIMI_API_KEY`, and `GLM_API_KEY`.
- Each Codex profile has its model card deployed at `~/.codex/<agent-id>.config.toml` (`business` excepted: `~/.codex-agent/business/config.toml`).
- The `local` launchers require a healthy OpenAI-compatible service at `http://127.0.0.1:8080`.

Keep credentials in the environment or in the untracked local file
`~/.config/zsh/agent-tools.local.zsh`. The installed launcher loads that file automatically when it exists. Never add
credentials to `scripts/agent-tools.zsh`.

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
`hy` (hy4-preview on tokenhub.tencentmaas.com, `HY_API_KEY`) is **Claude-runtime only**: the gateway's `/v1/responses` SSE
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

Before dispatching, `sub-agent-preflight` runs the `$sub-agents` preflight checks (workspace, git condition, provider and
launcher deployment, fresh output paths) and creates the run directory, canary files, and the full prompt — the task body
plus the fixed report protocol:

```bash
sub-agent-preflight --runtime codex --provider gpt-6-sol --cwd /path/to/workspace --label review-sol-01 --task-file task.md
```

It prints a `key=value` report plus the exact runnable command (`setup_status=ok` means the dispatch may proceed). A
dispatch needs a real task: pass `--task` / `--task-file` and the script composes the prompt, or `--prompt-file` with a
complete prompt; without exactly one of them the preflight fails and prints no command. The prompt must also carry the
dispatch-contract sections — `Goal` / `Non-goals` / `Stop condition`, one per line with the section name first (the
Chinese equivalents are accepted) — and the preflight checks those. The canary token is never printed and never placed
in the prompt — the child reads it from the generated file.

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
`gpt-6-luna` the low-cost bulk work. All three run at medium reasoning effort.
`gpt_codex` is an alias for `gpt-6-sol_codex`, including its resume handling and arguments.

| Profile | Model | Gateway | Shim port | Gateway fix |
| --- | --- | --- | --- | --- |
| `ds-flash` | `deepseek-flash` | api.deepseek.com | 8788 | model-name rewrite + patched catalog |
| `glm` | `glm-5.3` | open.bigmodel.cn | 8789 | model-name rewrite + patched catalog |
| `glm-flash` | `glm-5.3-flash` | open.bigmodel.cn | 8795 | model-name rewrite + patched catalog |
| `kimi` | `kimi-k3` | api.kimi.com | 8790 | + patched catalog |
| `mimo` | `mimo-v2.6-pro` | token-plan-cn.xiaomimimo.com | 8791 | + patched catalog + `json_object` downgrade |
| `mimo-fast` | `mimo-v2.6-pro-ultraspeed` | api.xiaomimimo.com | 8794 | + patched catalog + `json_object` downgrade |
| `mimo-flash` | `mimo-v2.6-flash` | token-plan-cn.xiaomimimo.com | 8793 | + patched catalog + `json_object` downgrade |
| `qwen` | `qwen3.8-max` | dashscope.aliyuncs.com | 8792 | + patched catalog + message-id prefix fix |
| `local` | `qwen3.8-27b-local` | 127.0.0.1:8080 (llama.cpp) | none | patched catalog, runs unsandboxed, no shim |
| `gpt-6-astra` | `gpt-6-astra` | OpenAI (ChatGPT login) | none | no shim, subscription-backed |
| `gpt-6-sol` | `gpt-6-sol` | OpenAI (ChatGPT login) | none | no shim, subscription-backed |
| `gpt-6-luna` | `gpt-6-luna` | OpenAI (ChatGPT login) | none | no shim, subscription-backed |

Credentials stay in the environment (`DEEPSEEK_API_KEY`, `GLM_API_KEY`, `KIMI_API_KEY`, `MIMO_PLAN_API_KEY`, `MIMO_API_KEY`,
`QWEN_API_KEY`, `HY_API_KEY`); `local` needs none, and the three OpenAI profiles share one ChatGPT account login (the
shared home's `auth.json`, not tracked here); `business` keeps its own `auth.json` under `~/.codex-agent/business/`.

Set up or update the profiles:

```bash
# install profiles, shim scripts, routes, and regenerate the model catalogs
./scripts/sync-codex-agent.sh

# optional but recommended: keep the shim running as a launchd service
~/.codex-agent/bin/codex-auto-review-shim-service install
```

After restoring the agent environment on another Mac, run `install` again. It discovers that machine's Python 3.11+
interpreter, rewrites the launchd plist, and reloads an existing service. `restart` only restarts the current plist.
If the archive contains an older service script, run `./scripts/sync-codex-agent.sh` from an updated checkout first.

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

`model-catalogs/<id>.json` for all nine third-party profiles are **generated artifacts and are not tracked**. The sync
script regenerates them from Codex's built-in catalog (`codex debug models` under a fresh `CODEX_HOME`), patches the
guardian tool mode, and adds each profile's model with its card's context window and direct tool mode. Without that
entry, Codex clamps unknown models to its 272K fallback maximum. If Codex changes the required catalog shape, the
generator exits non-zero; sync stages all cards and catalogs first, so installed cards and catalogs stay intact.

### Repairing reasoning history for cross-provider resume

A third-party Responses provider can save `reasoning_text` in a reasoning item's `content` array. The official OpenAI
endpoint rejects that history on resume with `Invalid 'input[n].content': array too long` (see [upstream issue #36551](https://github.com/openai/codex/issues/36551)). Close every Codex client using the session, then locate its rollout file under `~/.codex/sessions/` and run:

```bash
python3 scripts/repair-codex-reasoning-history.py /path/to/rollout-<session-id>.jsonl
python3 scripts/repair-codex-reasoning-history.py /path/to/rollout-<session-id>.jsonl --apply
# If cross-provider resume then reports invalid_encrypted_content or a missing reasoning item ID:
python3 scripts/repair-codex-reasoning-history.py /path/to/rollout-<session-id>.jsonl --drop-reasoning-model kimi-k3 --drop-reasoning-model mimo-v2.6-pro
python3 scripts/repair-codex-reasoning-history.py /path/to/rollout-<session-id>.jsonl --drop-reasoning-model kimi-k3 --drop-reasoning-model mimo-v2.6-pro --apply
```

The first command only counts affected items. `--apply` changes only reasoning items whose nonempty `content` consists
entirely of `reasoning_text`, setting that field to `null`; it saves a private timestamped backup beside the rollout
before replacing the file. Third-party encrypted reasoning may still fail validation, or its item ID may not exist on
OpenAI's endpoint. In that case, use `--drop-reasoning-model` for each source model: it removes only reasoning records
from those models' turns, keeping messages and tool history. Their private reasoning and any reasoning summaries in those
records are lost from the repaired rollout, but remain in the timestamped backup. The second run of each repair reports zero affected items.
Use the exact model name recorded in `turn_context`, rather than its profile alias; a zero-match model produces a warning.
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

`local` points straight at llama.cpp (`http://127.0.0.1:8080/v1`); its route is in the shared provider registry.

## Usage

### Gateflow

Use `gateflow` for one work unit: a feature, issue, bug fix, migration, refactor, schema/public contract change, or
architecture-sensitive task. Gateflow defines the gates only: preflight, goal confirmation, plan, review, implementation
slices, fixes, aggregate deep review, accepted commits, draft PR gate, and final closeout.

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
$tmux-agents routes Agents: CodexAgent-GPT-6-Astra handles plan / implement / fix, while ClaudeAgent-MiMo / ClaudeAgent-DS-Flash run two parallel review / re-review passes.
Re-discover panes before every send, clear the session for new tasks, and avoid bare #numbers.
Strictly follow the constraints in AGENTS.md.
```

Gateflow with `sub-agents` example:

```text
Develop <work-unit> with $gateflow.
$sub-agents dispatches through runner subprocesses: Codex gpt-6-astra handles plan / implement / fix, while Claude mimo / ds-flash run the two review / re-review passes.
Pass the workspace absolute path explicitly in every call and use separate output / stderr files; the controller checks the structured results and adjudicates itself.
Strictly follow the constraints in AGENTS.md.
```

### Phaseflow

Use `phaseflow` when a project has a design source document and an implementation control document. Phaseflow is the
project step controller: it reads the current `phase = work unit`, performs preflight and goal confirmation with the user,
reads Gateflow's `Gate Order`, dispatches concrete gates to Agents, adjudicates results, updates `control_doc`, and
reconciles residual risks.

Standalone Phaseflow example:

When no dispatch protocol is named, Phaseflow uses `sub-agents` by default. Use `$tmux-agents` explicitly to route through
already-running tmux panes.

```text
Proceed with $phaseflow; the design source of truth is docs/host/design.md, and the control document is docs/host/issues-implementation-control.md.
Read control_doc first to identify the current phase/work unit, then read design_doc.
The controller Agent completes preflight and goal confirmation first; after user confirmation, dispatch Agents gate by gate following Gateflow's Gate Order to do the concrete work.
After each gate returns, update control_doc and record the artifact / finding adjudication / residual risk.
After final closeout, explain that the user merges the PR, pulls the target base branch, and continues the next round from the next entry point in control_doc.
Strictly follow the constraints in AGENTS.md.
```

Phaseflow with `tmux-agents` example:

```text
Proceed with $phaseflow; the design source of truth is docs/host/design.md, and the control document is docs/host/issues-implementation-control.md.
$tmux-agents routes Agents: ClaudeAgent-MiMo / ClaudeAgent-DS-Flash run two parallel review passes, while CodexAgent-GPT-6-Astra handles plan / implement / fix.
The controller Agent completes preflight and goal confirmation first; after confirmation, dispatch gate by gate following Gateflow's Gate Order.
After each Agent returns, the controller reads the artifact, adjudicates findings, updates control_doc, collects residual risks, and closes resolved risks.
After final closeout, explain that the user merges the PR, pulls the target base branch, and continues the next round from the next entry point in control_doc.
Strictly follow the constraints in AGENTS.md.
```

Phaseflow with `sub-agents` example:

```text
Proceed with $phaseflow; the design source of truth is docs/host/design.md, and the control document is docs/host/issues-implementation-control.md.
$sub-agents dispatches through runner subprocesses: Claude mimo / ds-flash run the two review passes, while Codex gpt-6-astra handles plan / implement / fix.
The controller advances through Gateflow's Gate Order, checks each subprocess's exit status and structured output, and updates control_doc.
Strictly follow the constraints in AGENTS.md.
```

### Planreview

Use `planreview` to challenge whether a plan is specific, implementable, correctly sliced, architecturally sound, and not over-designed.

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
runners. The skill defines workspace isolation, bounded prompts, parallel execution, output validation, retry limits,
session continuation, and controller adjudication.

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

Independent tasks may run concurrently when their write ownership does not overlap. The controller must check exit codes,
stderr, and structured output before accepting any result.

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
scripts/
  agent-tools.zsh
  claude-agent-run
  codex-agent-run
  compose-codex-app-config.py
  sub-agent-preflight
  sync-codex-providers.py
  patch-codex-model-catalog.py
  repair-codex-reasoning-history.py
  sync-agent-tools.sh
  sync-codex-agent.sh
  validate-skills.sh
  sync-skills.sh
tests/
  test_provider_registry.py
  test_repair_codex_reasoning_history.py
```

## Maintenance

Edit only the source files in this repository:

```text
skills/<skill-name>/SKILL.md
skills/<skill-name>/agents/openai.yaml
scripts/agent-tools.zsh
scripts/claude-agent-run
scripts/codex-agent-run
scripts/compose-codex-app-config.py
codex-agent/model-providers.toml
codex-agent/profiles/<agent-id>/config.toml
codex-agent/bin/
codex-agent/shim-routes.json
scripts/patch-codex-model-catalog.py
scripts/repair-codex-reasoning-history.py
scripts/sync-codex-providers.py
tests/test_provider_registry.py
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
- `phaseflow` is the project step controller; concrete plan / implementation / review / fix work is delegated to Agents.
- `planreview` and `deepreview` are review skills. They should produce durable artifacts, not just chat-only conclusions.
- `tmux-agents` is only needed when you route work to multiple CLI agents through tmux.
- `sub-agents` is used when the controller launches external child agents through the runner subprocesses.
