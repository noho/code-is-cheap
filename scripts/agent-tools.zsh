# Agent launchers use private JSON connections. Loading this file exports no keys.
# Remove inherited credentials before helpers/Agents run; this is environment
# isolation, not protection against same-user reads of the private JSON file.
_agent_tools_scrub_credentials() {
  local variable_name
  for variable_name in ${(k)parameters}; do
    [[ ${parameters[$variable_name]} == *export* ]] || continue
    case "${(U)variable_name}" in
      *KEY*|*TOKEN*|*SECRET*|*PASSWORD*|*CREDENTIAL*|*AUTHORIZATION*|ANTHROPIC_CUSTOM_HEADERS|SSH_AUTH_SOCK)
        unset "$variable_name" || return 1
        ;;
    esac
  done
}

_agent_tools_connection_helper() {
  command -v agent-endpoint.py || {
    print -u2 -- "agent-endpoint.py 不在 PATH（请运行 sync-agent-tools.sh）"
    return 1
  }
}

_claude_agent_title() {
  case "$1" in
    ds-flash)    print -r -- "ClaudeAgent-DS-Flash" ;;
    mimo)  print -r -- "ClaudeAgent-MiMo" ;;
    mimo-fast) print -r -- "ClaudeAgent-MiMo-Fast" ;;
    mimo-flash) print -r -- "ClaudeAgent-MiMo-Flash" ;;
    qwen)  print -r -- "ClaudeAgent-Qwen" ;;
    kimi)  print -r -- "ClaudeAgent-Kimi" ;;
    glm)   print -r -- "ClaudeAgent-GLM" ;;
    glm-flash) print -r -- "ClaudeAgent-GLM-Flash" ;;
    local) print -r -- "ClaudeAgent-Local" ;;
    hy)    print -r -- "ClaudeAgent-HY" ;;
    *)     return 1 ;;
  esac
}

_agent_tools_base_url() {
  local helper
  helper="$(_agent_tools_connection_helper)" || return 1
  python3 "$helper" --provider "$1" --runtime "${2:-claude}"
}

_claude_agent_base_url() { _agent_tools_base_url "$1" claude; }

_claude_agent_compact_window() {
  case "$1" in
    ds-flash|mimo|mimo-fast|mimo-flash|qwen|kimi|glm|glm-flash|hy) print -r -- "786432" ;;
    local)                 print -r -- "229376" ;;
    *)                     return 1 ;;
  esac
}

_claude_agent_max_context() {
  case "$1" in
    glm|glm-flash)   print -r -- "1000000" ;;
    local) print -r -- "262144" ;;
    *)     print -r -- "" ;;
  esac
}

_local_agent_require_service() {
  local base_url
  base_url="$(_agent_tools_base_url local "${1:-claude}")" || return 1
  [[ "${1:-claude}" == codex ]] && base_url="${base_url%/v1}"
  command -v curl >/dev/null 2>&1 || {
    echo "curl 未安装" >&2
    return 1
  }
  curl -fsS --max-time 2 "${base_url%/}/health" >/dev/null 2>&1 || {
    echo "本地模型服务未启动或不可访问，请检查 endpoints.json 的 local/claude URL" >&2
    return 1
  }
}

_claude_agent_launch() (
  emulate -L zsh
  unsetopt xtrace verbose
  local agent_id="$1"
  shift
  local title="$(_claude_agent_title "$agent_id")" || return 1
  local compact_window="$(_claude_agent_compact_window "$agent_id")" || return 1
  local max_context="$(_claude_agent_max_context "$agent_id")" || return 1
  local api_timeout="" helper
  local set_title=false
  local -a claude_args=()
  _agent_tools_scrub_credentials || return 1
  helper="$(_agent_tools_connection_helper)" || return 1
  [[ "$agent_id" == local ]] && { _local_agent_require_service || return 1; api_timeout="3600000"; }
  while (( $# > 0 )); do
    case "$1" in
      --title)
        set_title=true
        shift
        if (( $# > 0 )); then title="$1"; shift; fi
        ;;
      *) claude_args+=("$1"); shift ;;
    esac
  done
  if [[ "$set_title" == true && -n "${TMUX:-}" ]] && command -v tmux >/dev/null 2>&1; then
    tmux select-pane -T "$title" >/dev/null 2>&1 || true
  fi
  # One helper snapshot selects URL/model/key; only exec'd Claude receives the
  # canonical token. No key is printed or placed in argv/settings JSON.
  python3 "$helper" --launch-claude "$agent_id" --compact-window "$compact_window" \
    --max-context "$max_context" --api-timeout "$api_timeout" -- "${claude_args[@]}"
)

ds-flash_claude() { _claude_agent_launch ds-flash "$@"; }
mimo_claude()  { _claude_agent_launch mimo "$@"; }
mimo-fast_claude() { _claude_agent_launch mimo-fast "$@"; }
mimo-flash_claude() { _claude_agent_launch mimo-flash "$@"; }
qwen_claude()  { _claude_agent_launch qwen "$@"; }
kimi_claude()  { _claude_agent_launch kimi "$@"; }
glm_claude()   { _claude_agent_launch glm "$@"; }
glm-flash_claude() { _claude_agent_launch glm-flash "$@"; }
local_claude() { _claude_agent_launch local "$@"; }
hy_claude()    { _claude_agent_launch hy "$@"; }

# Shared home for every managed profile (`codex -p <id>` model cards): the real
# directory ~/.codex (must not be a symlink — the desktop app's sandbox rejects
# symlink components in its writable paths). business keeps its own CODEX_HOME
# (separate ChatGPT login) and is the sole exception.
_codex_agent_home() {
  if [[ "$1" == business ]]; then
    print -r -- "$HOME/.codex-agent/business"
  else
    print -r -- "$HOME/.codex"
  fi
}

_codex_agent_title() {
  case "$1" in
    ds-flash)       print -r -- "CodexAgent-DS-Flash" ;;
    mimo)     print -r -- "CodexAgent-MiMo" ;;
    mimo-fast) print -r -- "CodexAgent-MiMo-Fast" ;;
    mimo-flash) print -r -- "CodexAgent-MiMo-Flash" ;;
    qwen)     print -r -- "CodexAgent-Qwen" ;;
    kimi)     print -r -- "CodexAgent-Kimi" ;;
    glm)      print -r -- "CodexAgent-GLM" ;;
    glm-flash) print -r -- "CodexAgent-GLM-Flash" ;;
    local)    print -r -- "CodexAgent-Local" ;;
    gpt-6-astra) print -r -- "CodexAgent-GPT-6-Astra" ;;
    gpt-6-sol)   print -r -- "CodexAgent-GPT-6-Sol" ;;
    gpt-6-luna)  print -r -- "CodexAgent-GPT-6-Luna" ;;
    business)    print -r -- "CodexAgent-Business" ;;
    *)        return 1 ;;
  esac
}

_codex_agent_shim_port() {
  case "$1" in
    ds-flash)   print -r -- "8788" ;;
    glm)  print -r -- "8789" ;;
    glm-flash) print -r -- "8795" ;;
    kimi) print -r -- "8790" ;;
    mimo) print -r -- "8791" ;;
    mimo-fast) print -r -- "8794" ;;
    mimo-flash) print -r -- "8793" ;;
    qwen) print -r -- "8792" ;;
    *)    print -r -- "" ;;
  esac
}

# 走反代的 profile 在启动前确认 shim 端口有监听；否则所有模型请求都会连接失败。
_codex_agent_require_shim() {
  local agent_id="$1"
  local port="$(_codex_agent_shim_port "$agent_id")" || return 1
  [[ -n "$port" ]] || return 0

  zmodload zsh/net/tcp 2>/dev/null || {
    echo "无法加载 zsh/net/tcp，跳过 shim 端口检查" >&2
    return 0
  }
  local fd
  if ! ztcp 127.0.0.1 "$port" 2>/dev/null; then
    echo "Codex 反代 shim 未运行（127.0.0.1:$port 无监听）" >&2
    echo "启动：\"$HOME/.codex-agent/bin/codex-auto-review-shim-service\" install  # 已安装过则用 restart" >&2
    return 1
  fi
  fd=$REPLY
  ztcp -c "$fd" 2>/dev/null
}

_codex_agent_require_home() {
  local agent_id="$1"
  local codex_home="$(_codex_agent_home "$agent_id")" || return 1

  [[ -d "$codex_home" ]] || {
    echo "$agent_id Codex home 不存在：$codex_home" >&2
    return 1
  }
  if [[ "$agent_id" == business ]]; then
    [[ -r "$codex_home/config.toml" ]] || {
      echo "$agent_id Codex 配置不存在：$codex_home/config.toml" >&2
      return 1
    }
  else
    [[ -r "$codex_home/$agent_id.config.toml" ]] || {
      echo "$agent_id 模型卡未部署：$codex_home/$agent_id.config.toml（跑 scripts/sync-codex-agent.sh）" >&2
      return 1
    }
  fi
  case "$agent_id" in
    local|gpt-6-astra|gpt-6-sol|gpt-6-luna|business) ;;
    *)
      local helper
      helper="$(_agent_tools_connection_helper)" || return 1
      python3 "$helper" --check --provider "$agent_id" --runtime codex --require-key || return 1
      ;;
  esac
  if [[ "$agent_id" == local ]]; then
    _local_agent_require_service codex || return 1
  fi
  _codex_agent_require_shim "$agent_id" || return 1
}

_codex_agent_app() (
  emulate -L zsh
  unsetopt xtrace verbose
  local agent_id="$1"
  shift

  (( $# <= 1 )) || {
    echo "${agent_id}_codex_app: 只接受一个 workspace 路径" >&2
    return 2
  }

  _agent_tools_scrub_credentials || return 1
  _codex_agent_require_home "$agent_id" || return 1
  command -v jq >/dev/null 2>&1 || {
    echo "jq 未安装" >&2
    return 1
  }
  [[ -d /Applications/ChatGPT.app ]] || {
    echo "未找到 /Applications/ChatGPT.app" >&2
    return 1
  }

  local codex_home="$(_codex_agent_home "$agent_id")"
  local user_data="$HOME/.codex-agent/app-data/$agent_id"
  local workspace="${1:-$PWD}"
  local workspace_url
  local -a open_args

  [[ -d "$workspace" ]] || {
    echo "workspace 不存在或不是目录：$workspace" >&2
    return 1
  }
  workspace="${workspace:A}"
  workspace_url="$(jq -rn --arg path "$workspace" '"codex://threads/new?path=\($path | @uri)"')" || return 1

  mkdir -p "$user_data" || return 1

  # The desktop app reads $CODEX_HOME/config.toml in full and has no -p card
  # layering (we launch it via `open`, not `codex app`), so each managed app
  # instance gets its own real composed home under its user-data dir: shared
  # base + this agent's model card overlaid. Compose is idempotent and reruns
  # on every launch. business keeps its own full CODEX_HOME (no composition).
  if [[ "$agent_id" != business ]]; then
    command -v compose-codex-app-config.py >/dev/null 2>&1 || {
      echo "compose-codex-app-config.py 不在 PATH（是否忘了跑 sync-agent-tools.sh？）" >&2
      return 1
    }
    local app_home="$user_data/home"
    mkdir -p "$app_home" || return 1
    local -a compose_args=(--base "$HOME/.codex/config.toml" --card "$HOME/.codex/$agent_id.config.toml" --out "$app_home/config.toml")
    if [[ "$agent_id" == local ]]; then
      local helper local_model
      helper="$(_agent_tools_connection_helper)" || return 1
      local_model="$(python3 "$helper" --provider local --runtime codex --field upstream_model)" || return 1
      compose_args+=(--model "$local_model")
    fi
    compose-codex-app-config.py "${compose_args[@]}" || return 1
    [[ -f "$app_home/auth.json" ]] || cp -p "$HOME/.codex/auth.json" "$app_home/auth.json" 2>/dev/null || true
    codex_home="$app_home"
  fi
  open_args=(
    -n
    --env "CODEX_HOME=$codex_home"
    --env "CODEX_SQLITE_HOME=$codex_home"
    --env "CODEX_ELECTRON_USER_DATA_PATH=$user_data"
  )
  open_args+=(
    -a /Applications/ChatGPT.app
    "$workspace_url"
    --args "--user-data-dir=$user_data"
  )

  /usr/bin/open "${open_args[@]}"
)

_codex_agent_launch() (
  emulate -L zsh
  unsetopt xtrace verbose
  local agent_id="$1"
  shift

  local title="$(_codex_agent_title "$agent_id")" || return 1
  local codex_home="$(_codex_agent_home "$agent_id")" || return 1
  local set_title=false
  local -a codex_args=()

  while (( $# > 0 )); do
    case "$1" in
      --title)
        set_title=true
        shift
        if (( $# > 0 )); then
          title="$1"
          shift
        fi
        ;;
      app)
        if (( ${#codex_args[@]} == 0 )); then
          shift
          _codex_agent_app "$agent_id" "$@"
          return $?
        fi
        codex_args+=("$1")
        shift
        ;;
      *)
        codex_args+=("$1")
        shift
        ;;
    esac
  done

  _agent_tools_scrub_credentials || return 1
  _codex_agent_require_home "$agent_id" || return 1
  local repair_requested=false
  local repair_session_id=""
  local -a resume_tail=()
  # `resume <id>` uses the same repair path as the launcher-only `--resume`.
  # Bare `resume` and Codex's own options (for example --help/--last) stay native.
  if (( ${#codex_args[@]} >= 2 )) && [[ "${codex_args[1]}" == resume && "${codex_args[2]}" != -* ]]; then
    codex_args[1]=--resume
  fi
  if (( ${#codex_args[@]} > 0 )); then
    case "${codex_args[1]}" in
      --resume)
        repair_requested=true
        (( ${#codex_args[@]} >= 2 && ${#codex_args[@]} <= 3 )) || {
          echo "用法：${agent_id}_codex {resume|--resume} <session-id> [prompt]" >&2
          return 2
        }
        repair_session_id="${codex_args[2]}"
        (( ${#codex_args[@]} == 3 )) && resume_tail=("${codex_args[3]}")
        ;;
      --resume=*)
        repair_requested=true
        (( ${#codex_args[@]} <= 2 )) || {
          echo "用法：${agent_id}_codex --resume=<session-id> [prompt]" >&2
          return 2
        }
        repair_session_id="${codex_args[1]#--resume=}"
        (( ${#codex_args[@]} == 2 )) && resume_tail=("${codex_args[2]}")
        ;;
    esac
  fi
  if [[ "$repair_requested" == true ]]; then
    [[ -n "$repair_session_id" ]] || {
      echo "session-id 不能为空" >&2
      return 2
    }
    command -v repair-codex-reasoning-history.py >/dev/null 2>&1 || {
      echo "repair-codex-reasoning-history.py 不在 PATH（请先运行 scripts/sync-agent-tools.sh）" >&2
      return 1
    }
    local target_config="$codex_home/$agent_id.config.toml"
    [[ "$agent_id" == business ]] && target_config="$codex_home/config.toml"
    repair-codex-reasoning-history.py \
      --session-id "$repair_session_id" \
      --sessions-root "$codex_home/sessions" \
      --target-config "$target_config" \
      --apply || return $?
    codex_args=(resume "$repair_session_id" "${resume_tail[@]}")
  fi
  if [[ "$set_title" == true && -n "${TMUX:-}" ]] && command -v tmux >/dev/null 2>&1; then
    tmux select-pane -T "$title" >/dev/null 2>&1 || true
  fi

  # Managed profiles select their model card with `codex -p <id>` on the shared
  # home. `exec resume` has no -p of its own, so the flag goes right after
  # `exec`; for the other subcommands (interactive, `resume`, `review`) it goes
  # right after the subcommand name. business keeps the per-home switch.
  if [[ "$agent_id" != business ]] && (( ${#codex_args[@]} > 0 )); then
    case "${codex_args[1]}" in
      exec|resume|review)
        codex_args=("${codex_args[1]}" -p "$agent_id" "${(@)codex_args[2,-1]}")
        ;;
      *)
        codex_args=(-p "$agent_id" "${codex_args[@]}")
        ;;
    esac
  elif [[ "$agent_id" != business ]]; then
    codex_args=(-p "$agent_id")
  fi

  if [[ "$agent_id" == local ]]; then
    local helper local_model model_option
    helper="$(_agent_tools_connection_helper)" || return 1
    local_model="$(python3 "$helper" --provider local --runtime codex --field upstream_model)" || return 1
    model_option="model=\"$local_model\""
    case "${codex_args[1]:-}" in
      exec|resume|review) codex_args=("${codex_args[1]}" -c "$model_option" "${(@)codex_args[2,-1]}") ;;
      *) codex_args=(-c "$model_option" "${codex_args[@]}") ;;
    esac
  fi
  CODEX_HOME="$codex_home" CODEX_SQLITE_HOME="$codex_home" command codex "${codex_args[@]}"
)

ds-flash_codex() { _codex_agent_launch ds-flash "$@"; }
mimo_codex()     { _codex_agent_launch mimo "$@"; }
mimo-fast_codex() { _codex_agent_launch mimo-fast "$@"; }
mimo-flash_codex() { _codex_agent_launch mimo-flash "$@"; }
qwen_codex()     { _codex_agent_launch qwen "$@"; }
kimi_codex()     { _codex_agent_launch kimi "$@"; }
glm_codex()      { _codex_agent_launch glm "$@"; }
glm-flash_codex() { _codex_agent_launch glm-flash "$@"; }
local_codex()    { _codex_agent_launch local "$@"; }
gpt-6-astra_codex() { _codex_agent_launch gpt-6-astra "$@"; }
gpt-6-sol_codex()   { _codex_agent_launch gpt-6-sol "$@"; }
gpt_codex()         { _codex_agent_launch gpt-6-sol "$@"; }
gpt-6-luna_codex()  { _codex_agent_launch gpt-6-luna "$@"; }
business_codex() { _codex_agent_launch business "$@"; }

ds-flash_codex_app() { _codex_agent_app ds-flash "$@"; }
mimo_codex_app()     { _codex_agent_app mimo "$@"; }
mimo-fast_codex_app() { _codex_agent_app mimo-fast "$@"; }
mimo-flash_codex_app() { _codex_agent_app mimo-flash "$@"; }
qwen_codex_app()     { _codex_agent_app qwen "$@"; }
kimi_codex_app()     { _codex_agent_app kimi "$@"; }
glm_codex_app()      { _codex_agent_app glm "$@"; }
glm-flash_codex_app() { _codex_agent_app glm-flash "$@"; }
local_codex_app()    { _codex_agent_app local "$@"; }
gpt-6-astra_codex_app() { _codex_agent_app gpt-6-astra "$@"; }
gpt-6-sol_codex_app()   { _codex_agent_app gpt-6-sol "$@"; }
gpt-6-luna_codex_app()  { _codex_agent_app gpt-6-luna "$@"; }
business_codex_app() { _codex_agent_app business "$@"; }
