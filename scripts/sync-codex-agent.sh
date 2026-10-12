#!/usr/bin/env bash
set -euo pipefail

# Sync the tracked codex-agent configuration to ~/.codex-agent:
#
#   codex-agent/profiles/<id>/config.toml   model cards for `codex -p <id>`,
#                                           installed as ~/.codex/<id>.config.toml
#   codex-agent/bin/codex-auto-review-shim       自动审批反代（guardian 模型名改写）
#   codex-agent/bin/codex-auto-review-shim-service   launchd 管理脚本
#   codex-agent/shim-routes.json                 反代路由表
#   model-catalogs/<id>.json                     由 scripts/patch-codex-model-catalog.py 现场生成
#
# 共享 home ~/.codex（真目录——桌面 app 沙箱拒绝路径中的 symlink 成分）的 base
# config.toml 是机器本地运行时状态（政策、[projects.*] trust、[hooks.state]、app 写入的
# [mcp_servers.*]/[plugins.*]/[marketplaces.*]/[tui.*]/[desktop] 及 notify 等根键），
# 模型卡只含模型差量、整文件覆盖即可，无需合并。
# 本脚本只通过 sync-codex-providers.py 更新 base config 中有明确标记的
# [model_providers.*] 注册表；其它本机设置保持原样。
#
# `business` 使用独立的 CODEX_HOME（~/.codex-agent/business，另一账号）。
# 只同步其 model / model_reasoning_effort；其它本机设置与账号不在管理范围。

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
target_root="${CODEX_AGENT_TARGET:-$HOME/.codex-agent}"
shared_home="${CODEX_SHARED_HOME:-$HOME/.codex}"
shim_label="com.leo.codex-auto-review-shim"

# Validate effective settings (local overrides + defaults), without writing user files.
python3 "$repo_root/scripts/agent-endpoint.py" --check
SHIM_ROUTES="$repo_root/codex-agent/shim-routes.json" python3 "$repo_root/codex-agent/bin/codex-auto-review-shim" --routes >/dev/null
local_base_url="$(python3 "$repo_root/scripts/agent-endpoint.py" --provider local --runtime codex)"

mkdir -p "$target_root"
mkdir -p "$shared_home/model-catalogs"

# --- stage cards and catalogs before replacing installed cards -------------
stage_dir="$(mktemp -d "$shared_home/.catalog-stage.XXXXXX")"
recovery_active=false
keep_backups=false
attempted=()
destinations=()
backups=()
original_present=()
cleanup_conversion() {
  local rc=$? index dest tmp
  trap - EXIT
  if [[ "$recovery_active" == true ]]; then
    # Registry is restored only when this block changed its bytes/absence.
    if [[ "${original_present[0]}" == true ]]; then
      if ! cmp -s "${backups[0]}" "${destinations[0]}"; then attempted+=(0); fi
    elif [[ -e "${destinations[0]}" ]]; then
      attempted+=(0)
    fi
    for ((index=${#attempted[@]}-1; index>=0; index--)); do
      local slot="${attempted[index]}"
      dest="${destinations[slot]}"
      tmp="$dest.tmp.$$"
      if [[ "${original_present[slot]}" == true ]]; then
        if ! cp -p "${backups[slot]}" "$tmp" || ! mv "$tmp" "$dest"; then keep_backups=true; fi
      else
        if ! rm -f "$dest"; then keep_backups=true; fi
      fi
      rm -f "$tmp" || keep_backups=true
    done
    if [[ "$keep_backups" == true ]]; then
      echo "ERROR: conversion rollback failed; backups retained: $stage_dir" >&2
      rc=1
    else
      echo "ERROR: conversion failed; restored cards/catalogs and changed registry" >&2
    fi
  fi
  if [[ "$keep_backups" != true ]]; then rm -rf "$stage_dir"; fi
  exit "$rc"
}
trap cleanup_conversion EXIT
mkdir -p "$stage_dir/cards" "$stage_dir/catalogs"
for src in "$repo_root"/codex-agent/profiles/*/config.toml; do
  [[ -f "$src" ]] || continue
  profile="$(basename "$(dirname "$src")")"
  # 模板用 @HOME@/.codex 占位；测试可通过 CODEX_SHARED_HOME 改写目标 home。
  dest="$stage_dir/cards/$profile.config.toml"
  sed "s|@HOME@/.codex|$shared_home|g" "$src" > "$dest"
  chmod 600 "$dest"
  if grep -q '@HOME@' "$dest"; then
    echo "ERROR: $dest 仍含未替换的 @HOME@ 占位符" >&2
    exit 1
  fi
done

# The generator reads staged cards but validates their final installed paths.
# A catalog failure leaves every installed card and catalog as it was.
python3 "$repo_root/scripts/patch-codex-model-catalog.py" \
  --cards-dir "$stage_dir/cards" \
  --output-dir "$stage_dir/catalogs"

# Back up all destinations before the first mutation. Recovery covers only
# ordinary failures in this conversion block, not crash/concurrent visibility.
mkdir -p "$stage_dir/backups"
backup_destination() {
  local dest="$1" slot="${#destinations[@]}"
  destinations+=("$dest")
  backups+=("$stage_dir/backups/$slot")
  if [[ -L "$dest" || ( -e "$dest" && ! -f "$dest" ) ]]; then
    echo "ERROR: conversion destination is not a regular file: $dest" >&2
    exit 1
  fi
  if [[ -e "$dest" ]]; then
    cp -p "$dest" "${backups[slot]}"
    original_present+=(true)
  else
    original_present+=(false)
  fi
}
backup_destination "$shared_home/config.toml"
# Pair catalogs with cards, retaining the existing install policy for GPT cards.
sources=()
for src in "$stage_dir"/cards/*.config.toml; do
  profile="$(basename "$src" .config.toml)"
  catalog="$stage_dir/catalogs/$profile.json"
  if [[ -f "$catalog" ]]; then
    sources+=("$catalog")
    backup_destination "$shared_home/model-catalogs/$profile.json"
  fi
  sources+=("$src")
  backup_destination "$shared_home/$(basename "$src")"
done
recovery_active=true
# Saved-thread provider IDs must resolve before new cards become visible.
python3 "$repo_root/scripts/sync-codex-providers.py" \
  --base "$shared_home/config.toml" \
  --registry "$repo_root/codex-agent/model-providers.toml" \
  --local-base-url "$local_base_url"
for ((slot=1; slot<${#destinations[@]}; slot++)); do
  src="${sources[slot-1]}"
  dest="${destinations[slot]}"
  tmp="$dest.tmp.$$"
  attempted+=("$slot")
  install -m 600 "$src" "$tmp"
  mv "$tmp" "$dest"
  echo "synced: $(basename "$src") -> $dest"
done
# Staged native parsing already proved the pair relationships. Exact installed
# byte equality proves we installed those same cards/catalogs without reparsing.
for ((slot=1; slot<${#destinations[@]}; slot++)); do
  if ! cmp -s "${sources[slot-1]}" "${destinations[slot]}"; then
    echo "ERROR: installed conversion bytes differ: ${destinations[slot]}" >&2
    exit 1
  fi
done
recovery_active=false

# --- shim + launcher scripts ------------------------------------------------
mkdir -p "$target_root/bin"
for src in "$repo_root"/codex-agent/bin/*; do
  [[ -f "$src" ]] || continue
  install -m 755 "$src" "$target_root/bin/$(basename "$src")"
  echo "synced bin: $(basename "$src")"
done

# --- shim routes ------------------------------------------------------------
install -m 755 "$repo_root/scripts/agent-endpoint.py" "$target_root/bin/agent-endpoint.py"
install -m 600 "$repo_root/config/endpoints.example.json" "$target_root/bin/agent-endpoints.defaults.json.tmp.$$"
mv "$target_root/bin/agent-endpoints.defaults.json.tmp.$$" "$target_root/bin/agent-endpoints.defaults.json"
install -m 644 "$repo_root/codex-agent/shim-routes.json" "$target_root/shim-routes.json"
echo "synced shim-routes.json"

# --- 让运行中的 shim 用上新路由 ----------------------------------------------
if launchctl print "gui/$(id -u)/$shim_label" >/dev/null 2>&1; then
  if ! launchctl kickstart -k "gui/$(id -u)/$shim_label" >/dev/null 2>&1; then
    echo "ERROR: failed to restart launchd service: $shim_label" >&2
    exit 1
  fi
  echo "restarted launchd service: $shim_label"
else
  echo "note: launchd 服务未加载（若手工跑着 shim，需要重启它才能用上新路由）"
fi

# The business app cannot layer a -p card. Sync its independent defaults last
# so a damaged business config cannot interrupt shared-home shim deployment.
business_config="$target_root/business/config.toml"
if [[ -e "$business_config" || -L "$business_config" ]]; then
  python3 "$repo_root/scripts/sync-codex-model-defaults.py" \
    --config "$business_config" \
    --card "$repo_root/codex-agent/profiles/gpt-6-sol/config.toml"
else
  echo "note: business config not found; skipped model defaults: $business_config"
fi

echo "Synced codex-agent cards to $shared_home"
