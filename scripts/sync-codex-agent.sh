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
# `business` 使用独立的 CODEX_HOME（~/.codex-agent/business，另一账号），不在本脚本管理范围。

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
target_root="${CODEX_AGENT_TARGET:-$HOME/.codex-agent}"
shared_home="${CODEX_SHARED_HOME:-$HOME/.codex}"
shim_label="com.leo.codex-auto-review-shim"

mkdir -p "$target_root"
mkdir -p "$shared_home/model-catalogs"

# Every provider used by a saved thread must be resolvable before resume can
# apply a different model card. Sync this registry before deploying cards.
python3 "$repo_root/scripts/sync-codex-providers.py" \
  --base "$shared_home/config.toml" \
  --registry "$repo_root/codex-agent/model-providers.toml"

# --- stage cards and catalogs before replacing installed cards -------------
stage_dir="$(mktemp -d "$shared_home/.catalog-stage.XXXXXX")"
trap 'rm -rf "$stage_dir"' EXIT
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

for src in "$stage_dir"/catalogs/*.json; do
  [[ -f "$src" ]] || continue
  dest="$shared_home/model-catalogs/$(basename "$src")"
  tmp="$dest.tmp.$$"
  install -m 600 "$src" "$tmp"
  mv "$tmp" "$dest"
  echo "synced catalog: $(basename "$src") -> $dest"
done
for src in "$stage_dir"/cards/*.config.toml; do
  [[ -f "$src" ]] || continue
  dest="$shared_home/$(basename "$src")"
  tmp="$dest.tmp.$$"
  install -m 600 "$src" "$tmp"
  mv "$tmp" "$dest"
  echo "synced card: $(basename "$src" .config.toml) -> $dest"
done

# --- shim + launcher scripts ------------------------------------------------
mkdir -p "$target_root/bin"
for src in "$repo_root"/codex-agent/bin/*; do
  [[ -f "$src" ]] || continue
  install -m 755 "$src" "$target_root/bin/$(basename "$src")"
  echo "synced bin: $(basename "$src")"
done

# --- shim routes ------------------------------------------------------------
install -m 644 "$repo_root/codex-agent/shim-routes.json" "$target_root/shim-routes.json"
echo "synced shim-routes.json"

# --- 让运行中的 shim 用上新路由 ----------------------------------------------
if launchctl print "gui/$(id -u)/$shim_label" >/dev/null 2>&1; then
  launchctl kickstart -k "gui/$(id -u)/$shim_label" >/dev/null 2>&1 \
    && echo "restarted launchd service: $shim_label"
else
  echo "note: launchd 服务未加载（若手工跑着 shim，需要重启它才能用上新路由）"
fi

echo "Synced codex-agent cards to $shared_home"
