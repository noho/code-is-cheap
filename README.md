# code-is-cheap

English | [中文](README.zh.md)

An engineering control framework for automated AI coding. Its core assumption is that architecture, phase boundaries,
entry/exit criteria, and implementation control plans are prepared first; after that, a controller agent can advance each
phase automatically until the local branch reaches `ready-to-open-draft-PR`.

This is not a loose collection of prompts. It is a workflow for putting AI coding inside an engineering loop: adjudicate
design and plans, implement by slices, review code, fix findings, re-review, run aggregate deep review, track residual
risks, and create local accepted commits. The controller stops for the user only when there is a blocking open question,
unclear scope or ownership, validation failure, residual risk requiring human judgment, first entry into the draft PR gate,
or external actions such as merge, approval, marking a PR ready for review, or public comments. After the user authorizes
the draft PR gate, it automatically pushes, creates a draft PR, runs PR review, fixes findings, re-reviews, creates an
accepted PR review commit, and pushes again until `draft-PR-pass`.

This repository contains local skills and supporting scripts for Codex / Claude Code, covering phase-driven development,
gated feature development, plan review, deep code review, and multi-agent handoff.

This repository is the source of truth for the skills under `skills/`. Local Codex and Claude skill directories are installation targets only. Edit skills here, validate them here, then sync them out.

## Screenshot

![code-is-cheap running with multiple agents in tmux](working.png)
![code-is-cheap running with multiple agents in tmux](working-2.png)

## Included Skills

| Skill | Use it when |
| --- | --- |
| `gateflow` | You want to advance a complex feature, migration, refactor, schema change, public contract change, or architecture-sensitive task from plan to `ready-to-open-draft-PR`, then through the draft PR gate to `draft-PR-pass` after user authorization. |
| `phaseflow` | You have a design source document and an implementation control document, and want to advance phase design, planning, implementation, review, risk tracking, and status updates. |
| `planreview` | You want adversarial review of a plan, implementation plan, migration phase plan, feature slice plan, or Gateflow handoff plan. |
| `deepreview` | You want strict code review of current workspace changes, a GitHub PR, or the whole repository. |
| `init-agents` | You want a controller agent to communicate with other Codex / Claude Code agents through tmux panes. |

## Demo

```text
Use $phaseflow. The design is in docs/host/design.md, and the control document is docs/host/implementation-control.md.
```

Equivalent explicit argument form:

```text
$phaseflow design_doc=docs/host/design.md control_doc=docs/host/implementation-control.md
```

## Core Workflow

A typical flow is:

1. Prepare the design source document, such as `docs/design.md` or `docs/host/design.md`.
2. Prepare the implementation control document, such as `docs/implementation-control.md`, with phases, dependencies, entry criteria, exit criteria, validation requirements, and tracking items.
3. Use `phaseflow` to read both documents, identify the current phase, refine design, and produce an implementation-ready plan.
4. `phaseflow` then follows the `gateflow` gate order to automatically run plan review, plan fix, plan re-review, slice implementation, code review, code fix, code re-review, and accepted local commits.
5. After all slices are complete, run aggregate deep review automatically; after fixes and re-review pass, update the control document and mark the phase complete.
6. Stop at `ready-to-open-draft-PR` and report the branch, commits, artifacts, validation results, remaining risks, and draft PR readiness.
7. After user authorization, `phaseflow` / `gateflow` automatically pushes, creates a draft PR, runs PR review, fixes accepted findings, re-reviews, creates an accepted PR review commit, and pushes again until `draft-PR-pass`.

The point is not to let the agent invent architecture on the fly. The point is to let agents execute reliably inside
explicit design boundaries and implementation plans, while leaving durable artifacts for every review conclusion, fix
status, validation result, and residual risk.

## Requirements

- Codex CLI, Claude Code, or another agent runtime that supports local skill-style instruction files.
- Python 3.11+ if you want to run the bundled skill validator.
- `tmux` and `tmux-cli` if you use `init-agents` for multi-agent handoff.

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

Sync skills to any local Codex / Claude skill homes that already exist:

```bash
./scripts/sync-skills.sh
```

The sync script installs to these directories when present:

```text
~/.codex/skills
~/.codex-pro/skills
~/.codex-business/skills
~/.claude/skills
```

After syncing, start a new Codex / Claude session so the runtime reloads the skill list.

## Prepare Agent Environment

`init-agents` works best when each CLI agent runs in its own tmux pane with a stable pane title. The examples below show one practical setup using zsh functions in `~/.zshrc`.

Prerequisites:

- `claude`, `codex`, `tmux`, `jq`, `curl`, and `tmux-cli` are available on `PATH`.
- Provider API keys are exported before starting the matching Claude Code wrappers:
  - `DEEPSEEK_API_KEY`
  - `MIMO_PLAN_API_KEY`
  - `GLM_API_KEY`
  - `KIMI_API_KEY`
- `opus_claude` uses the local Claude proxy at `http://localhost:4141`.
- Codex Pro uses `CODEX_HOME="$HOME/.codex-pro"` so it can use a separate Codex identity/config from the default controller Codex.

Add these functions to `~/.zshrc`:

```zsh
opus_claude() {
  curl -fsS --max-time 2 "http://localhost:4141" >/dev/null 2>&1 || {
    echo "localhost:4141 代理未启动或不可访问"
    return 1
  }

  local set_title=false
  local -a claude_args=()
  local arg
  for arg in "$@"; do
    case "$arg" in
      --title)
        set_title=true
        ;;
      *)
        claude_args+=("$arg")
        ;;
    esac
  done

  if [[ "$set_title" == true && -n "${TMUX:-}" ]] && command -v tmux >/dev/null 2>&1; then
    tmux select-pane -T "AgentOpus" >/dev/null 2>&1 || true
  fi

  local settings_json
  settings_json="$(jq -nc \
    --arg base_url "http://localhost:4141" \
    --arg auth_token "dummy" \
    --arg model "claude-opus-4.7" \
    '{
      env: {
        ANTHROPIC_BASE_URL: $base_url,
        ANTHROPIC_AUTH_TOKEN: $auth_token,
        ANTHROPIC_MODEL: $model,
        CLAUDE_CODE_EFFORT_LEVEL: "high"
      }
    }')"

  claude --settings "$settings_json" "${claude_args[@]}"
}

ds_claude() {
  [[ -z "$DEEPSEEK_API_KEY" ]] && echo "DEEPSEEK_API_KEY 未设置" && return 1

  local set_title=false
  local -a claude_args=("${(@)argv:#--title}")
  if (( ${argv[(Ie)--title]} )); then
    set_title=true
  fi

  if [[ "$set_title" == true && -n "${TMUX:-}" ]] && command -v tmux >/dev/null 2>&1; then
    tmux select-pane -T "AgentDS" >/dev/null 2>&1 || true
  fi

  local settings_json
  settings_json="$(jq -nc \
    --arg base_url "https://api.deepseek.com/anthropic" \
    --arg auth_token "$DEEPSEEK_API_KEY" \
    --arg model "deepseek-v4-pro[1m]" \
    '{
      env: {
        ANTHROPIC_BASE_URL: $base_url,
        ANTHROPIC_AUTH_TOKEN: $auth_token,
        ANTHROPIC_MODEL: $model,
        ANTHROPIC_DEFAULT_SONNET_MODEL: $model,
        ANTHROPIC_DEFAULT_OPUS_MODEL: $model,
        ANTHROPIC_DEFAULT_HAIKU_MODEL: $model,
        CLAUDE_CODE_SUBAGENT_MODEL: $model,
        CLAUDE_CODE_DISABLE_AUTO_TITLE: "1",
        CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1",
        CLAUDE_CODE_DISABLE_SESSIONMETADATA: "1",
        CLAUDE_CODE_DISABLE_QUOTA_CHECK: "1",
        DISABLE_NON_ESSENTIAL_MODEL_CALLS: "1",
        CLAUDE_CODE_EFFORT_LEVEL: "max"
      }
    }')"

  claude --settings "$settings_json" "${claude_args[@]}"
}

mimo_claude() {
  [[ -z "$MIMO_PLAN_API_KEY" ]] && echo "MIMO_PLAN_API_KEY 未设置" && return 1

  local set_title=false
  local -a claude_args=("${(@)argv:#--title}")
  if (( ${argv[(Ie)--title]} )); then
    set_title=true
  fi

  if [[ "$set_title" == true && -n "${TMUX:-}" ]] && command -v tmux >/dev/null 2>&1; then
    tmux select-pane -T "AgentMiMo" >/dev/null 2>&1 || true
  fi

  local settings_json
  settings_json="$(jq -nc \
    --arg base_url "https://token-plan-cn.xiaomimimo.com/anthropic" \
    --arg auth_token "$MIMO_PLAN_API_KEY" \
    --arg model "mimo-v2.5-pro[1m]" \
    '{
      env: {
        ANTHROPIC_BASE_URL: $base_url,
        ANTHROPIC_AUTH_TOKEN: $auth_token,
        ANTHROPIC_MODEL: $model,
        ANTHROPIC_DEFAULT_SONNET_MODEL: $model,
        ANTHROPIC_DEFAULT_OPUS_MODEL: $model,
        ANTHROPIC_DEFAULT_HAIKU_MODEL: $model,
        CLAUDE_CODE_SUBAGENT_MODEL: $model,
        CLAUDE_CODE_DISABLE_AUTO_TITLE: "1",
        CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1",
        CLAUDE_CODE_DISABLE_SESSIONMETADATA: "1",
        CLAUDE_CODE_DISABLE_QUOTA_CHECK: "1",
        DISABLE_NON_ESSENTIAL_MODEL_CALLS: "1",
        CLAUDE_CODE_EFFORT_LEVEL: "max"
      }
    }')"

  claude --settings "$settings_json" "${claude_args[@]}"
}

glm_claude() {
  [[ -z "$GLM_API_KEY" ]] && echo "GLM_API_KEY 未设置" && return 1

  local set_title=false
  local -a claude_args=("${(@)argv:#--title}")
  if (( ${argv[(Ie)--title]} )); then
    set_title=true
  fi

  if [[ "$set_title" == true && -n "${TMUX:-}" ]] && command -v tmux >/dev/null 2>&1; then
    tmux select-pane -T "AgentGLM" >/dev/null 2>&1 || true
  fi

  local settings_json
  settings_json="$(jq -nc \
    --arg base_url "https://open.bigmodel.cn/api/anthropic" \
    --arg auth_token "$GLM_API_KEY" \
    --arg model "GLM-5.1" \
    '{
      env: {
        ANTHROPIC_BASE_URL: $base_url,
        ANTHROPIC_AUTH_TOKEN: $auth_token,
        ANTHROPIC_MODEL: $model,
        ANTHROPIC_DEFAULT_SONNET_MODEL: $model,
        ANTHROPIC_DEFAULT_OPUS_MODEL: $model,
        ANTHROPIC_DEFAULT_HAIKU_MODEL: $model,
        CLAUDE_CODE_SUBAGENT_MODEL: $model,
        CLAUDE_CODE_DISABLE_AUTO_TITLE: "1",
        CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1",
        CLAUDE_CODE_DISABLE_SESSIONMETADATA: "1",
        CLAUDE_CODE_DISABLE_QUOTA_CHECK: "1",
        DISABLE_NON_ESSENTIAL_MODEL_CALLS: "1",
        CLAUDE_CODE_EFFORT_LEVEL: "max"
      }
    }')"

  claude --settings "$settings_json" "${claude_args[@]}"
}

kimi_claude() {
  [[ -z "$KIMI_API_KEY" ]] && echo "KIMI_API_KEY 未设置" && return 1

  local set_title=false
  local -a claude_args=("${(@)argv:#--title}")
  if (( ${argv[(Ie)--title]} )); then
    set_title=true
  fi

  if [[ "$set_title" == true && -n "${TMUX:-}" ]] && command -v tmux >/dev/null 2>&1; then
    tmux select-pane -T "AgentKIMI" >/dev/null 2>&1 || true
  fi

  local settings_json
  settings_json="$(jq -nc \
    --arg base_url "https://api.kimi.com/coding/" \
    --arg auth_token "$KIMI_API_KEY" \
    --arg model "kimi-for-coding" \
    '{
      env: {
        ANTHROPIC_BASE_URL: $base_url,
        ANTHROPIC_AUTH_TOKEN: $auth_token,
        ANTHROPIC_MODEL: $model,
        ANTHROPIC_DEFAULT_SONNET_MODEL: $model,
        ANTHROPIC_DEFAULT_OPUS_MODEL: $model,
        ANTHROPIC_DEFAULT_HAIKU_MODEL: $model,
        CLAUDE_CODE_SUBAGENT_MODEL: $model,
        CLAUDE_CODE_DISABLE_AUTO_TITLE: "1",
        CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1",
        CLAUDE_CODE_DISABLE_SESSIONMETADATA: "1",
        CLAUDE_CODE_DISABLE_QUOTA_CHECK: "1",
        DISABLE_NON_ESSENTIAL_MODEL_CALLS: "1",
        CLAUDE_CODE_EFFORT_LEVEL: "max"
      }
    }')"

  claude --settings "$settings_json" "${claude_args[@]}"
}

controller_codex() {
  local set_title=false
  local -a codex_args=("${(@)argv:#--title}")
  if (( ${argv[(Ie)--title]} )); then
    set_title=true
  fi

  if [[ "$set_title" == true && -n "${TMUX:-}" ]] && command -v tmux >/dev/null 2>&1; then
    tmux select-pane -T "AgentController" >/dev/null 2>&1 || true
  fi

  codex -s danger-full-access -a on-request -c shell_environment_policy.inherit=all "${codex_args[@]}"
}

pro_codex() {
  local set_title=false
  local -a codex_args=("${(@)argv:#--title}")
  if (( ${argv[(Ie)--title]} )); then
    set_title=true
  fi

  if [[ "$set_title" == true && -n "${TMUX:-}" ]] && command -v tmux >/dev/null 2>&1; then
    tmux select-pane -T "AgentCodex" >/dev/null 2>&1 || true
  fi

  mkdir -p "$HOME/.codex-pro"
  CODEX_HOME="$HOME/.codex-pro" codex -s danger-full-access -a on-request -c shell_environment_policy.inherit=all "${codex_args[@]}"
}

```

Start agents in separate tmux panes and pass `--title` so `init-agents` can identify them:

```bash
controller_codex --title
pro_codex --title
opus_claude --title
ds_claude --title
mimo_claude --title
glm_claude --title
kimi_claude --title
```

Expected pane titles:

| Function | Pane title | Typical role |
| --- | --- | --- |
| `controller_codex --title` | `AgentController` | Controller |
| `pro_codex --title` | `AgentCodex` | Implementation / fix |
| `opus_claude --title` | `AgentOpus` | Review / re-review |
| `ds_claude --title` | `AgentDS` | Review / re-review |
| `mimo_claude --title` | `AgentMiMo` | Review / re-review |
| `glm_claude --title` | `AgentGLM` | Review / re-review |
| `kimi_claude --title` | `AgentKIMI` | Review / re-review |

## Usage

### Gateflow

Use `gateflow` when you want the agent to run a gated controller workflow from plan to implementation review and local readiness.

Codex:

```text
Use $gateflow to develop <feature>.
If the requirements are unclear, discuss first.
```

Claude Code:

```text
Use /gateflow to develop <feature>.
If the requirements are unclear, discuss first.
```

`gateflow` is intended for complex work. It creates a plan, reviews the plan, runs implementation slices, reviews code, tracks residual risks, creates local accepted commits, and stops at `ready-to-open-draft-PR` for user authorization. After the user authorizes the draft PR gate, it automatically pushes, creates a draft PR, runs PR review, fixes findings, re-reviews, creates an accepted PR review commit, and pushes again until `draft-PR-pass`.

### Phaseflow

Use `phaseflow` when a project has a design source document and an implementation control document.

Codex:

```text
Use $phaseflow with design_doc=<path/to/design.md> and control_doc=<path/to/control.md> to continue the next phase.
```

Claude Code:

```text
Use /phaseflow with design_doc=<path/to/design.md> and control_doc=<path/to/control.md> to continue the next phase.
```

`phaseflow` follows `gateflow`, but adds control-document maintenance, phase status updates, risk tracking, and multi-agent review conventions.

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

### Init Agents

Use `init-agents` when the controller should not spawn built-in subagents, but should instead delegate work to already-running CLI agents through tmux panes.

Codex:

```text
Use $init-agents to initialize multi-agent communication conventions.
```

Claude Code:

```text
Use /init-agents to initialize multi-agent communication conventions.
```

`init-agents` assumes the controller only works with panes visible in the current tmux session/window via:

```bash
tmux-cli status
tmux-cli send "<prompt>" --pane=<full-pane-id>
tmux-cli wait_idle --pane=<full-pane-id> --idle-time=3 --timeout=<seconds>
tmux-cli capture --pane=<full-pane-id>
```

It uses `tmux-cli send` + `wait_idle` + `capture` for agent-to-agent chat. `tmux-cli execute` is only for shell commands where an exit code is needed.

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
  init-agents/
    SKILL.md
    agents/openai.yaml
scripts/
  validate-skills.sh
  sync-skills.sh
```

## Maintenance

Edit only the source files in this repository:

```text
skills/<skill-name>/SKILL.md
skills/<skill-name>/agents/openai.yaml
```

Validate all skills:

```bash
./scripts/validate-skills.sh
```

Sync to local Codex / Claude homes:

```bash
./scripts/sync-skills.sh
```

The sync script validates first, then copies every skill directory to existing local targets. It does not push, publish, create PRs, or modify remote repositories.

## Notes

- `gateflow` and `phaseflow` are controller workflows. Worker prompts should be role-scoped handoffs, not instructions to restart the full workflow.
- `planreview` and `deepreview` are review skills. They should produce durable artifacts, not just chat-only conclusions.
- `init-agents` is optional unless you run multiple CLI agents through tmux.
