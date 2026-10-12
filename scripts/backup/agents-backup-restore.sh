#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
PAYLOAD_DIR="$SCRIPT_DIR/payload"
ARCHIVE_NAME="agent-home.tar"
ARCHIVE_PATH="$PAYLOAD_DIR/$ARCHIVE_NAME"
CHECKSUM_PATH="$PAYLOAD_DIR/SHA256SUMS"
MANIFEST_PATH="$PAYLOAD_DIR/manifest.txt"

usage() {
  cat <<'EOF'
Usage:
  bash agents-backup-restore.sh backup
  bash agents-backup-restore.sh verify
  bash agents-backup-restore.sh restore [--yes] [--install-deps]

Commands:
  backup         Back up the active Claude/Codex environment from $HOME.
  verify         Verify the archive checksum and tar structure.
  restore        Restore into the current user's $HOME on another macOS computer.

Restore options:
  --yes          Skip the confirmation prompt.
  --install-deps Install missing CLI dependencies through Homebrew/npm/uv.
                 Install pinned optional SRT only if it was present on the source.

The restore command first moves any existing target files into:
  ~/.agent-restore-backups/<timestamp>/

The archive contains session history and credentials. Keep it private.
EOF
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Required command not found: $1" >&2
    exit 1
  }
}

command_version() {
  local command_name="$1"
  shift
  if command -v "$command_name" >/dev/null 2>&1; then
    "$command_name" "$@" 2>/dev/null | head -n 1 || true
  else
    printf 'not-installed'
  fi
}

# Inspect package files only: srt is a Node package, not a standalone binary.
# Keep these checks aligned with agent-sandbox-launch.mjs:validateRuntime.
sandbox_runtime_version() {
  local srt_path
  srt_path="$(command -v srt || true)"
  [[ -n "$srt_path" ]] || srt_path="$HOME/.local/bin/srt"
  command -v node >/dev/null 2>&1 || return 1
  node - "$srt_path" <<'NODE'
const fs = require('node:fs');
const path = require('node:path');
try {
  const cli = fs.realpathSync(process.argv[2]);
  const root = path.dirname(path.dirname(cli));
  const pkg = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
  if (pkg.name !== '@anthropic-ai/sandbox-runtime' || typeof pkg.version !== 'string' ||
      !pkg.version || path.resolve(root, pkg.bin?.srt ?? '') !== cli) throw Error('package/layout mismatch');
  for (const file of [cli, path.join(root, 'dist/utils/shell-quote.js'),
                      path.join(root, 'dist/sandbox/macos-sandbox-utils.js')]) {
    if (!fs.statSync(file).isFile()) throw Error('required module is not a file');
    fs.accessSync(file, fs.constants.R_OK);
  }
  console.log(pkg.version);
} catch { process.exitCode = 1; }
NODE
}

write_manifest() {
  local temporary_manifest="$MANIFEST_PATH.tmp.$$"
  local srt_version
  srt_version="$(sandbox_runtime_version 2>/dev/null || true)"
  {
    printf 'format_version=1\n'
    printf 'created_at=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'source_home=%s\n' "$HOME"
    printf 'source_user=%s\n' "$(id -un)"
    printf 'source_host=%s\n' "$(scutil --get ComputerName 2>/dev/null || hostname)"
    printf 'source_arch=%s\n' "$(uname -m)"
    printf 'source_macos=%s\n' "$(sw_vers -productVersion 2>/dev/null || uname -r)"
    printf 'claude_version=%s\n' "$(command_version claude --version)"
    printf 'codex_version=%s\n' "$(command_version codex --version)"
    printf 'tmux_version=%s\n' "$(command_version tmux -V)"
    printf 'tmux_cli_version=%s\n' "$(command_version tmux-cli --version)"
    if [[ -n "$srt_version" ]]; then
      printf 'sandbox_runtime_installed=true\nsandbox_runtime_version=%s\n' "$srt_version"
    else
      printf 'sandbox_runtime_installed=false\nsandbox_runtime_version=not-installed\n'
    fi
    printf 'archive=%s\n' "$ARCHIVE_NAME"
  } > "$temporary_manifest"
  mv "$temporary_manifest" "$MANIFEST_PATH"
}

backup_environment() {
  require_command tar
  require_command shasum

  local relative_path
  local temporary_archive="$PAYLOAD_DIR/.$ARCHIVE_NAME.tmp.$$"
  local -a backup_paths=(
    ".claude"
    ".codex-agent"
    ".codex"
    ".claude.json"
    ".zshrc"
    ".config/zsh/agent-tools.zsh"
    ".local/bin/claude-agent-run"
    ".local/bin/codex-agent-run"
    ".local/bin/agent-run-result.py"
  )
  local -a optional_paths=(
    ".config/zsh/agent-tools.local.zsh"
    ".config/agent-tools/endpoints.json"
    ".local/bin/agent-endpoint.py"
    ".local/bin/agent-endpoints.defaults.json"
    ".tmux.conf"
    ".local/bin/sub-agent-preflight"
    ".local/bin/compose-codex-app-config.py"
    ".local/bin/repair-codex-reasoning-history.py"
    ".local/bin/agent-sandbox"
    ".local/bin/agent-sandbox-launch.mjs"
    ".local/bin/install-agent-sandbox.sh"
    "Library/LaunchAgents/com.leo.codex-auto-review-shim.plist"
  )

  mkdir -p "$PAYLOAD_DIR"

  for relative_path in "${backup_paths[@]}"; do
    if [[ ! -e "$HOME/$relative_path" && ! -L "$HOME/$relative_path" ]]; then
      echo "Backup source is missing: $HOME/$relative_path" >&2
      exit 1
    fi
  done
  [[ -f "$HOME/.local/bin/agent-run-result.py" && ! -L "$HOME/.local/bin/agent-run-result.py" ]] || {
    echo "Required runner collector must be a regular file, not a symlink: $HOME/.local/bin/agent-run-result.py" >&2
    exit 1
  }

  for relative_path in "${optional_paths[@]}"; do
    if [[ -e "$HOME/$relative_path" || -L "$HOME/$relative_path" ]]; then
      backup_paths+=("$relative_path")
    fi
  done

  rm -f "$temporary_archive"
  trap 'rm -f "$temporary_archive"' EXIT INT TERM

  echo "Creating $ARCHIVE_PATH"
  echo "For the most consistent session snapshot, close other Claude/Codex processes first."
  COPYFILE_DISABLE=1 tar \
    --exclude='node_modules' \
    --exclude='*.sock' \
    --exclude='*.ipc' \
    --exclude='.codex-agent/app-data/*/Singleton*' \
    --exclude='.codex-agent/app-data/*/RunningChromeVersion' \
    -cpf "$temporary_archive" \
    -C "$HOME" \
    "${backup_paths[@]}"

  mv "$temporary_archive" "$ARCHIVE_PATH"
  trap - EXIT INT TERM

  write_manifest
  (
    cd "$PAYLOAD_DIR"
    shasum -a 256 "$ARCHIVE_NAME" > "$(basename "$CHECKSUM_PATH").tmp.$$"
    mv "$(basename "$CHECKSUM_PATH").tmp.$$" "$(basename "$CHECKSUM_PATH")"
  )

  verify_environment
  echo "Backup complete: $ARCHIVE_PATH"
}

verify_environment() {
  require_command tar
  require_command shasum

  [[ -f "$ARCHIVE_PATH" ]] || {
    echo "Archive not found: $ARCHIVE_PATH" >&2
    exit 1
  }
  [[ -f "$CHECKSUM_PATH" ]] || {
    echo "Checksum file not found: $CHECKSUM_PATH" >&2
    exit 1
  }
  [[ -f "$MANIFEST_PATH" ]] || {
    echo "Manifest not found: $MANIFEST_PATH" >&2
    exit 1
  }

  (
    cd "$PAYLOAD_DIR"
    shasum -a 256 -c "$(basename "$CHECKSUM_PATH")"
  )
  tar -tf "$ARCHIVE_PATH" >/dev/null
  echo "Archive structure: OK"
}

load_brew_environment() {
  if command -v brew >/dev/null 2>&1; then
    return 0
  fi
  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
}

install_dependencies() {
  load_brew_environment
  if ! command -v brew >/dev/null 2>&1; then
    echo "Installing Homebrew..."
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    load_brew_environment
  fi

  local -a formulae=()
  command -v node >/dev/null 2>&1 || formulae+=(node)
  command -v jq >/dev/null 2>&1 || formulae+=(jq)
  command -v tmux >/dev/null 2>&1 || formulae+=(tmux)
  command -v rsync >/dev/null 2>&1 || formulae+=(rsync)
  command -v uv >/dev/null 2>&1 || formulae+=(uv)
  if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
    formulae+=(python)
  fi
  if (( ${#formulae[@]} > 0 )); then
    brew install "${formulae[@]}"
  fi
  if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
    export PATH="$(brew --prefix)/bin:$PATH"
  fi

  if ! command -v codex >/dev/null 2>&1; then
    npm install -g @openai/codex
  fi
  if ! command -v claude >/dev/null 2>&1; then
    curl -fsSL https://claude.ai/install.sh | bash
    export PATH="$HOME/.local/bin:$PATH"
  fi
  if ! command -v tmux-cli >/dev/null 2>&1; then
    uv tool install claude-code-tools
    export PATH="$HOME/.local/bin:$PATH"
  fi
}

validate_sandbox_dependencies() {
  command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1 || return 1
  node -e 'const [a,b]=process.versions.node.split(".").map(Number);process.exit(Number(a<22||(a===22&&b<12)))' || return 1
  [[ "$(sandbox_runtime_version 2>/dev/null || true)" == '0.0.79' ]]
}

restore_sandbox_dependencies() {
  local should_install="$1"
  local source_installed
  source_installed="$(sed -n 's/^sandbox_runtime_installed=//p' "$MANIFEST_PATH" | head -n 1)"
  [[ "$source_installed" == true ]] || return 0
  local installer="$HOME/.local/bin/install-agent-sandbox.sh"
  # Select the target's managed installation, never a source-home symlink.
  local PATH="$HOME/.local/bin:$PATH"
  if validate_sandbox_dependencies; then
    echo 'Optional SRT: validated Node package 0.0.79.'
    return 0
  fi
  echo 'Optional SRT requires Node >=22.12, npm and @anthropic-ai/sandbox-runtime@0.0.79 with its required modules.' >&2
  if [[ ! -f "$installer" || -L "$installer" ]] \
    || ! tar -tf "$ARCHIVE_PATH" '.local/bin/install-agent-sandbox.sh' >/dev/null 2>&1; then
    echo 'Archived install-agent-sandbox.sh is missing or not a regular file; obtain it with sync-agent-tools.sh before installing optional SRT.' >&2
    if [[ "$should_install" == true ]]; then return 1; fi
    return 0
  fi
  printf 'Install optional SRT: AGENT_SANDBOX_INSTALL_DIR=%q AGENT_RUN_BIN_DIR=%q bash %q\n' \
    "$HOME/.local/share/agent-sandbox" "$HOME/.local/bin" "$installer" >&2
  [[ "$should_install" == true ]] || return 0
  if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1 \
    || ! node -e 'const [a,b]=process.versions.node.split(".").map(Number);process.exit(Number(a<22||(a===22&&b<12)))'; then
    echo 'Install Node >=22.12 and npm first, then run the optional SRT command above.' >&2
    return 1
  fi
  if ! AGENT_SANDBOX_INSTALL_DIR="$HOME/.local/share/agent-sandbox" \
    AGENT_RUN_BIN_DIR="$HOME/.local/bin" bash "$installer"; then
    echo "Optional SRT installer failed: $installer; see installer error above." >&2
    return 1
  fi
  if ! validate_sandbox_dependencies; then
    echo 'Optional SRT installation failed Node package/version/layout validation.' >&2
    return 1
  fi
  echo 'Optional SRT: validated Node package 0.0.79.'
}

relocate_file() {
  local file_path="$1"
  local old_home="$2"
  local new_home="$3"
  [[ -f "$file_path" ]] || return 0
  OLD_HOME="$old_home" NEW_HOME="$new_home" perl -pi -e \
    's/\Q$ENV{OLD_HOME}\E/$ENV{NEW_HOME}/g' "$file_path"
}

relocate_home_symlinks() {
  local old_home="$1"
  local link_path
  local link_target

  [[ -n "$old_home" && "$old_home" != "$HOME" ]] || return 0
  while IFS= read -r -d '' link_path; do
    link_target="$(readlink "$link_path")"
    case "$link_target" in
      "$old_home/"*)
        rm "$link_path"
        ln -s "$HOME/${link_target#"$old_home/"}" "$link_path"
        ;;
    esac
  done < <(find "$HOME/.claude" "$HOME/.codex" "$HOME/.codex-agent" -type l -print0)
}

repair_legacy_business_links() {
  local name
  local link_path
  for name in plugins rules skills; do
    link_path="$HOME/.codex-agent/business/$name"
    if [[ -L "$link_path" && "$(readlink "$link_path")" == "../codex/$name" ]]; then
      rm "$link_path"
      ln -s "../../.codex/$name" "$link_path"
    fi
  done
}

regenerate_shim_plist() {
  local plist="$HOME/Library/LaunchAgents/com.leo.codex-auto-review-shim.plist"
  local service="$HOME/.codex-agent/bin/codex-auto-review-shim-service"
  local candidate
  [[ -f "$plist" && -x "$service" ]] || return 0

  candidate="$(mktemp "$plist.tmp.XXXXXX")" || return 1
  if "$service" print-plist > "$candidate" \
    && plutil -lint "$candidate" >/dev/null 2>&1 \
    && mv "$candidate" "$plist"; then
    echo "Regenerated auto-review shim plist for this Mac: $plist"
  else
    rm -f "$candidate"
    echo "Could not regenerate the auto-review shim plist; install Python 3.11+ and run: $service install" >&2
  fi
}

relocate_configuration() {
  local old_home="$1"
  local config_file

  [[ -n "$old_home" && "$old_home" != "$HOME" ]] || return 0
  echo "Relocating configuration paths: $old_home -> $HOME"

  relocate_file "$HOME/.zshrc" "$old_home" "$HOME"
  relocate_file "$HOME/.tmux.conf" "$old_home" "$HOME"
  relocate_file "$HOME/.claude.json" "$old_home" "$HOME"
  relocate_file "$HOME/.config/zsh/agent-tools.zsh" "$old_home" "$HOME"
  relocate_file "$HOME/.config/zsh/agent-tools.local.zsh" "$old_home" "$HOME"
  relocate_file "$HOME/Library/LaunchAgents/com.leo.codex-auto-review-shim.plist" "$old_home" "$HOME"

  for config_file in "$HOME/.codex/config.toml" "$HOME/.codex/"*.config.toml \
    "$HOME/.codex-agent/app-data/"*/home/config.toml; do
    relocate_file "$config_file" "$old_home" "$HOME"
  done

  while IFS= read -r -d '' config_file; do
    relocate_file "$config_file" "$old_home" "$HOME"
  done < <(find "$HOME/.codex-agent" -maxdepth 2 -name config.toml -type f -print0)

  while IFS= read -r -d '' config_file; do
    relocate_file "$config_file" "$old_home" "$HOME"
  done < <(find "$HOME/.claude" -maxdepth 2 -name 'settings*.json' -type f -print0)

  relocate_home_symlinks "$old_home"
}

restore_environment() {
  local assume_yes=false
  local should_install_dependencies=false
  local option
  local relative_path
  local source_path
  local rollback_path
  local source_home
  local timestamp
  local rollback_root
  local archived_codex_link
  local -a required_paths=(
    ".claude"
    ".codex-agent"
    ".codex"
    ".claude.json"
    ".zshrc"
    ".config/zsh/agent-tools.zsh"
    ".local/bin/claude-agent-run"
    ".local/bin/codex-agent-run"
    ".local/bin/agent-run-result.py"
  )
  local -a optional_paths=(
    ".config/zsh/agent-tools.local.zsh"
    ".config/agent-tools/endpoints.json"
    ".local/bin/agent-endpoint.py"
    ".local/bin/agent-endpoints.defaults.json"
    ".tmux.conf"
    ".local/bin/sub-agent-preflight"
    ".local/bin/compose-codex-app-config.py"
    ".local/bin/repair-codex-reasoning-history.py"
    ".local/bin/agent-sandbox"
    ".local/bin/agent-sandbox-launch.mjs"
    ".local/bin/install-agent-sandbox.sh"
    "Library/LaunchAgents/com.leo.codex-auto-review-shim.plist"
  )
  local -a restore_paths=("${required_paths[@]}")

  for option in "$@"; do
    case "$option" in
      --yes) assume_yes=true ;;
      --install-deps) should_install_dependencies=true ;;
      *)
        echo "Unknown restore option: $option" >&2
        usage >&2
        exit 2
        ;;
    esac
  done

  verify_environment
  source_home="$(sed -n 's/^source_home=//p' "$MANIFEST_PATH" | head -n 1)"
  [[ -n "$source_home" ]] || {
    echo "source_home is missing from $MANIFEST_PATH" >&2
    exit 1
  }

  for relative_path in "${required_paths[@]}"; do
    if ! tar -tf "$ARCHIVE_PATH" "$relative_path" >/dev/null 2>&1; then
      echo "Required path is missing from archive: $relative_path" >&2
      if [[ "$relative_path" == '.local/bin/agent-run-result.py' ]]; then
        echo 'This archive predates the required runner collector and cannot restore a complete current runner.' >&2
        echo 'On the source, install current agent tools with ./scripts/sync-agent-tools.sh from the current repository if the collector is missing, then use the updated backup script:' >&2
        echo '  bash agents-backup-restore.sh backup' >&2
        echo '  bash agents-backup-restore.sh verify' >&2
        echo 'Verify the regenerated backup before migration. If the source is unavailable, verify remains usable; retain this archive for separate manual data recovery. It does not automatically restore a working runner.' >&2
      fi
      exit 1
    fi
  done
  # A source-home symlink or directory cannot provide the required collector.
  if [[ "$(tar -tvf "$ARCHIVE_PATH" '.local/bin/agent-run-result.py')" != -* ]]; then
    echo 'Required runner collector in archive must be a regular file, not a symlink or directory.' >&2
    exit 1
  fi
  for relative_path in "${optional_paths[@]}"; do
    if tar -tf "$ARCHIVE_PATH" "$relative_path" >/dev/null 2>&1; then
      restore_paths+=("$relative_path")
    fi
  done

  if [[ "$assume_yes" != true ]]; then
    printf 'Restore the Agent environment into %s? [y/N] ' "$HOME"
    read -r answer
    case "$answer" in
      y|Y|yes|YES) ;;
      *) echo "Restore cancelled."; exit 0 ;;
    esac
  fi

  timestamp="$(date '+%Y%m%d-%H%M%S')"
  rollback_root="$HOME/.agent-restore-backups/$timestamp"
  mkdir -p "$rollback_root"

  for relative_path in "${restore_paths[@]}"; do
    source_path="$HOME/$relative_path"
    if [[ -e "$source_path" || -L "$source_path" ]]; then
      rollback_path="$rollback_root/$relative_path"
      mkdir -p "$(dirname "$rollback_path")"
      mv "$source_path" "$rollback_path"
    fi
  done

  echo "Extracting Agent environment into $HOME"
  tar -xpf "$ARCHIVE_PATH" -C "$HOME"

  if [[ -L "$HOME/.codex" ]]; then
    archived_codex_link="$(readlink "$HOME/.codex")"
    case "$archived_codex_link" in
      "$source_home/.codex-agent/codex"|"$HOME/.codex-agent/codex"|.codex-agent/codex)
        if [[ ! -d "$HOME/.codex-agent/codex" || -L "$HOME/.codex-agent/codex" ]]; then
          echo "Legacy .codex target is missing from the archive; previous files are in $rollback_root" >&2
          exit 1
        fi
        rm "$HOME/.codex"
        mv "$HOME/.codex-agent/codex" "$HOME/.codex"
        ;;
      *)
        echo "Unexpected .codex symlink in archive: $archived_codex_link" >&2
        echo "Previous files are in $rollback_root" >&2
        exit 1
        ;;
    esac
  fi
  if [[ ! -d "$HOME/.codex" || -L "$HOME/.codex" ]]; then
    echo "Restored .codex is not a real directory; previous files are in $rollback_root" >&2
    exit 1
  fi

  relocate_configuration "$source_home"
  repair_legacy_business_links

  chmod 600 "$HOME/.zshrc" "$HOME/.claude.json" "$HOME/.config/zsh/agent-tools.zsh"
  chmod 755 "$HOME/.local/bin/claude-agent-run" "$HOME/.local/bin/codex-agent-run" \
    "$HOME/.local/bin/agent-run-result.py"
  if [[ -f "$HOME/.config/zsh/agent-tools.local.zsh" ]]; then
    chmod 600 "$HOME/.config/zsh/agent-tools.local.zsh"
  fi
  for relative_path in sub-agent-preflight compose-codex-app-config.py repair-codex-reasoning-history.py agent-endpoint.py \
    agent-sandbox agent-sandbox-launch.mjs install-agent-sandbox.sh; do
    if [[ -f "$HOME/.local/bin/$relative_path" ]]; then
      chmod 755 "$HOME/.local/bin/$relative_path"
    fi
  done

  for relative_path in ".config/agent-tools/endpoints.json" ".local/bin/agent-endpoints.defaults.json" ".tmux.conf"; do
    if [[ -f "$HOME/$relative_path" ]]; then
      chmod 600 "$HOME/$relative_path"
    fi
  done

  if [[ "$should_install_dependencies" == true ]]; then
    install_dependencies
  fi
  if ! restore_sandbox_dependencies "$should_install_dependencies"; then
    echo 'Environment files were restored, but optional SRT dependencies are not ready.' >&2
    echo "Previous files are in: $rollback_root" >&2
    return 1
  fi

  regenerate_shim_plist

  if command -v zsh >/dev/null 2>&1; then
    zsh -n "$HOME/.zshrc"
  fi

  echo "Restore complete. Previous files are in: $rollback_root"
  echo "Open a new terminal or run: exec zsh"
  if [[ -f "$HOME/Library/LaunchAgents/com.leo.codex-auto-review-shim.plist" ]]; then
    echo "Regenerate the auto-review shim service for this Mac: $HOME/.codex-agent/bin/codex-auto-review-shim-service install"
  fi

  local -a missing_commands=()
  for dependency in claude codex jq tmux tmux-cli; do
    command -v "$dependency" >/dev/null 2>&1 || missing_commands+=("$dependency")
  done
  if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
    missing_commands+=("python3 (3.11+)")
  fi
  if (( ${#missing_commands[@]} > 0 )); then
    echo "Missing commands: ${missing_commands[*]}" >&2
    echo "Run again with --install-deps to install them." >&2
  fi
}

main() {
  local command_name="${1:-}"
  if (( $# > 0 )); then
    shift
  fi
  case "$command_name" in
    backup) backup_environment "$@" ;;
    verify) verify_environment "$@" ;;
    restore) restore_environment "$@" ;;
    help|-h|--help|'') usage ;;
    *)
      echo "Unknown command: $command_name" >&2
      usage >&2
      exit 2
      ;;
  esac
}

main "$@"
