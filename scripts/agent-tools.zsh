# Agent launcher helpers for Claude Code and Codex.
# Source this file from ~/.zshrc. Keep credentials in the environment or in
# ~/.config/zsh/agent-tools.local.zsh; never add credentials to this file.

_agent_tools_local_file="${AGENT_TOOLS_LOCAL_FILE:-$HOME/.config/zsh/agent-tools.local.zsh}"
if [[ -r "$_agent_tools_local_file" ]]; then
  source "$_agent_tools_local_file"
fi
unset _agent_tools_local_file

_claude_agent_title() {
  case "$1" in
    ds)    print -r -- "ClaudeAgent-DS" ;;
    mimo)  print -r -- "ClaudeAgent-MiMo" ;;
    qwen)  print -r -- "ClaudeAgent-Qwen" ;;
    kimi)  print -r -- "ClaudeAgent-Kimi" ;;
    glm)   print -r -- "ClaudeAgent-GLM" ;;
    local) print -r -- "ClaudeAgent-Local" ;;
    *)     return 1 ;;
  esac
}

_claude_agent_key_name() {
  case "$1" in
    ds)    print -r -- "DEEPSEEK_API_KEY" ;;
    mimo)  print -r -- "MIMO_PLAN_API_KEY" ;;
    qwen)  print -r -- "QWEN_API_KEY" ;;
    kimi)  print -r -- "KIMI_API_KEY" ;;
    glm)   print -r -- "GLM_API_KEY" ;;
    local) print -r -- "" ;;
    *)     return 1 ;;
  esac
}

_claude_agent_base_url() {
  case "$1" in
    ds)    print -r -- "https://api.deepseek.com/anthropic" ;;
    mimo)  print -r -- "https://token-plan-cn.xiaomimimo.com/anthropic" ;;
    qwen)  print -r -- "https://dashscope.aliyuncs.com/apps/anthropic" ;;
    kimi)  print -r -- "https://api.moonshot.cn/anthropic" ;;
    glm)   print -r -- "https://open.bigmodel.cn/api/anthropic" ;;
    local) print -r -- "http://127.0.0.1:8080" ;;
    *)     return 1 ;;
  esac
}

_claude_agent_model() {
  case "$1" in
    ds)    print -r -- "deepseek-flash[1m]" ;;
    mimo)  print -r -- "mimo-v2.5-pro[1m]" ;;
    qwen)  print -r -- "qwen3.7-plus[1m]" ;;
    kimi)  print -r -- "kimi-k3[1m]" ;;
    glm)   print -r -- "glm-5.3" ;;
    local) print -r -- "qwen3.8-27b-local" ;;
    *)     return 1 ;;
  esac
}

_claude_agent_compact_window() {
  case "$1" in
    ds|mimo|qwen|kimi|glm) print -r -- "786432" ;;
    local)                 print -r -- "229376" ;;
    *)                     return 1 ;;
  esac
}

_local_agent_require_service() {
  command -v curl >/dev/null 2>&1 || {
    echo "curl 未安装" >&2
    return 1
  }
  curl -fsS --max-time 2 "http://127.0.0.1:8080/health" >/dev/null 2>&1 || {
    echo "Qwen3.8 本地服务未启动或不可访问（http://127.0.0.1:8080）" >&2
    echo "请启动本地模型服务后重试。" >&2
    return 1
  }
}

_claude_agent_require_provider() {
  local agent_id="$1"
  local key_name="$(_claude_agent_key_name "$agent_id")" || return 1

  if [[ -n "$key_name" && -z "${(P)key_name}" ]]; then
    echo "$key_name 未设置" >&2
    return 1
  fi
  if [[ "$agent_id" == local ]]; then
    _local_agent_require_service || return 1
  fi
}

_claude_agent_launch() {
  local agent_id="$1"
  shift

  local title="$(_claude_agent_title "$agent_id")" || return 1
  local key_name="$(_claude_agent_key_name "$agent_id")" || return 1
  local base_url="$(_claude_agent_base_url "$agent_id")" || return 1
  local model="$(_claude_agent_model "$agent_id")" || return 1
  local compact_window="$(_claude_agent_compact_window "$agent_id")" || return 1
  local auth_token="local"
  local max_context=""
  local api_timeout=""
  local set_title=false
  local settings_json
  local -a claude_args=()

  _claude_agent_require_provider "$agent_id" || return 1
  command -v jq >/dev/null 2>&1 || {
    echo "jq 未安装" >&2
    return 1
  }

  [[ -n "$key_name" ]] && auth_token="${(P)key_name}"
  [[ "$agent_id" == qwen ]] && max_context="1000000"
  [[ "$agent_id" == local ]] && api_timeout="3600000"

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
      *)
        claude_args+=("$1")
        shift
        ;;
    esac
  done

  if [[ "$set_title" == true && -n "${TMUX:-}" ]] && command -v tmux >/dev/null 2>&1; then
    tmux select-pane -T "$title" >/dev/null 2>&1 || true
  fi

  settings_json="$(jq -nc \
    --arg base_url "$base_url" \
    --arg auth_token "$auth_token" \
    --arg model "$model" \
    --arg compact_window "$compact_window" \
    --arg max_context "$max_context" \
    --arg api_timeout "$api_timeout" \
    '{
      env: {
        ANTHROPIC_BASE_URL: $base_url,
        ANTHROPIC_AUTH_TOKEN: $auth_token,
        ANTHROPIC_MODEL: $model,
        ANTHROPIC_DEFAULT_SONNET_MODEL: $model,
        ANTHROPIC_DEFAULT_OPUS_MODEL: $model,
        ANTHROPIC_DEFAULT_HAIKU_MODEL: $model,
        ANTHROPIC_DEFAULT_FABLE_MODEL: $model,
        CLAUDE_CODE_SUBAGENT_MODEL: $model,
        CLAUDE_CODE_DISABLE_AUTO_TITLE: "1",
        CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1",
        CLAUDE_CODE_DISABLE_SESSIONMETADATA: "1",
        CLAUDE_CODE_DISABLE_QUOTA_CHECK: "1",
        DISABLE_NON_ESSENTIAL_MODEL_CALLS: "1",
        CLAUDE_CODE_EFFORT_LEVEL: "max",
        CLAUDE_CODE_AUTO_COMPACT_WINDOW: $compact_window
      }
    }
    | if $max_context != "" then .env.CLAUDE_CODE_MAX_CONTEXT_TOKENS = $max_context else . end
    | if $api_timeout != "" then .env.API_TIMEOUT_MS = $api_timeout else . end')" || return 1

  command claude --settings "$settings_json" "${claude_args[@]}"
}

ds_claude()    { _claude_agent_launch ds "$@"; }
mimo_claude()  { _claude_agent_launch mimo "$@"; }
qwen_claude()  { _claude_agent_launch qwen "$@"; }
kimi_claude()  { _claude_agent_launch kimi "$@"; }
glm_claude()   { _claude_agent_launch glm "$@"; }
local_claude() { _claude_agent_launch local "$@"; }

_codex_agent_home() {
  print -r -- "$HOME/.codex-agent/$1"
}

_codex_agent_title() {
  case "$1" in
    ds)       print -r -- "CodexAgent-DS" ;;
    mimo)     print -r -- "CodexAgent-MiMo" ;;
    qwen)     print -r -- "CodexAgent-Qwen" ;;
    kimi)     print -r -- "CodexAgent-Kimi" ;;
    glm)      print -r -- "CodexAgent-GLM" ;;
    local)    print -r -- "CodexAgent-Local" ;;
    gpt)      print -r -- "CodexAgent-GPT" ;;
    business) print -r -- "CodexAgent-Business" ;;
    *)        return 1 ;;
  esac
}

_codex_agent_key_name() {
  case "$1" in
    ds)   print -r -- "DEEPSEEK_API_KEY" ;;
    mimo) print -r -- "MIMO_PLAN_API_KEY" ;;
    qwen) print -r -- "QWEN_API_KEY" ;;
    kimi) print -r -- "KIMI_API_KEY" ;;
    glm)  print -r -- "GLM_API_KEY" ;;
    local|gpt|business) print -r -- "" ;;
    *) return 1 ;;
  esac
}

_codex_agent_require_home() {
  local agent_id="$1"
  local codex_home="$(_codex_agent_home "$agent_id")" || return 1
  local key_name="$(_codex_agent_key_name "$agent_id")" || return 1

  [[ -d "$codex_home" ]] || {
    echo "$agent_id Codex home 不存在：$codex_home" >&2
    return 1
  }
  [[ -r "$codex_home/config.toml" ]] || {
    echo "$agent_id Codex 配置不存在：$codex_home/config.toml" >&2
    return 1
  }
  if [[ -n "$key_name" && -z "${(P)key_name}" ]]; then
    echo "$key_name 未设置" >&2
    return 1
  fi
  if [[ "$agent_id" == local ]]; then
    _local_agent_require_service || return 1
  fi
}

_codex_agent_app() {
  local agent_id="$1"
  shift

  (( $# <= 1 )) || {
    echo "${agent_id}_codex_app: 只接受一个 workspace 路径" >&2
    return 2
  }

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
  local key_name="$(_codex_agent_key_name "$agent_id")"
  local workspace_url
  local -a open_args

  [[ -d "$workspace" ]] || {
    echo "workspace 不存在或不是目录：$workspace" >&2
    return 1
  }
  workspace="${workspace:A}"
  workspace_url="$(jq -rn --arg path "$workspace" '"codex://threads/new?path=\($path | @uri)"')" || return 1

  mkdir -p "$user_data" || return 1
  open_args=(
    -n
    --env "CODEX_HOME=$codex_home"
    --env "CODEX_SQLITE_HOME=$codex_home"
    --env "CODEX_ELECTRON_USER_DATA_PATH=$user_data"
  )
  if [[ -n "$key_name" ]]; then
    open_args+=(--env "$key_name=${(P)key_name}")
  fi
  open_args+=(
    -a /Applications/ChatGPT.app
    "$workspace_url"
    --args "--user-data-dir=$user_data"
  )

  /usr/bin/open "${open_args[@]}"
}

_codex_agent_launch() {
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

  _codex_agent_require_home "$agent_id" || return 1
  if [[ "$set_title" == true && -n "${TMUX:-}" ]] && command -v tmux >/dev/null 2>&1; then
    tmux select-pane -T "$title" >/dev/null 2>&1 || true
  fi

  CODEX_HOME="$codex_home" CODEX_SQLITE_HOME="$codex_home" command codex "${codex_args[@]}"
}

ds_codex()       { _codex_agent_launch ds "$@"; }
mimo_codex()     { _codex_agent_launch mimo "$@"; }
qwen_codex()     { _codex_agent_launch qwen "$@"; }
kimi_codex()     { _codex_agent_launch kimi "$@"; }
glm_codex()      { _codex_agent_launch glm "$@"; }
local_codex()    { _codex_agent_launch local "$@"; }
gpt_codex()      { _codex_agent_launch gpt "$@"; }
business_codex() { _codex_agent_launch business "$@"; }

ds_codex_app()       { _codex_agent_app ds "$@"; }
mimo_codex_app()     { _codex_agent_app mimo "$@"; }
qwen_codex_app()     { _codex_agent_app qwen "$@"; }
kimi_codex_app()     { _codex_agent_app kimi "$@"; }
glm_codex_app()      { _codex_agent_app glm "$@"; }
local_codex_app()    { _codex_agent_app local "$@"; }
gpt_codex_app()      { _codex_agent_app gpt "$@"; }
business_codex_app() { _codex_agent_app business "$@"; }
