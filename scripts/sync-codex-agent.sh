#!/usr/bin/env bash
set -euo pipefail

# Sync the tracked codex-agent configuration to ~/.codex-agent:
#
#   codex-agent/profiles/<id>/config.toml   model cards for `codex -p <id>`,
#                                           installed as
#                                           ~/.codex-agent/codex/<id>.config.toml
#   codex-agent/bin/codex-auto-review-shim       自动审批反代（guardian 模型名改写）
#   codex-agent/bin/codex-auto-review-shim-service   launchd 管理脚本
#   codex-agent/shim-routes.json                 反代路由表
#   model-catalogs/<id>.json                     由 scripts/patch-codex-model-catalog.py 现场生成
#
# 共享 home ~/.codex-agent/codex（~/.codex 软链指向它）的 base config.toml 是
# 机器本地运行时状态（政策、[projects.*] trust、[hooks.state]、app 写入的
# [mcp_servers.*]/[plugins.*]/[marketplaces.*]/[tui.*]/[desktop] 及 notify 等根键），
# 本脚本从不写它。模型卡只含模型差量、整文件覆盖即可，无需合并。
#
# `business` 使用独立的 CODEX_HOME（~/.codex-agent/business，另一账号），不在本脚本管理范围。

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
target_root="${CODEX_AGENT_TARGET:-$HOME/.codex-agent}"
shared_home="$target_root/codex"
shim_label="com.leo.codex-auto-review-shim"

mkdir -p "$target_root"
mkdir -p "$shared_home/model-catalogs"

# --- profile cards ----------------------------------------------------------
for src in "$repo_root"/codex-agent/profiles/*/config.toml; do
  [[ -f "$src" ]] || continue
  profile="$(basename "$(dirname "$src")")"
  dest="$shared_home/$profile.config.toml"
  # 模板用 @HOME@ 占位（Codex 只接受绝对路径，~ / $HOME 都不展开），安装时注入本机 home
  tmp="$shared_home/.$profile.config.toml.$$"
  sed "s|@HOME@|$HOME|g" "$src" > "$tmp"
  chmod 600 "$tmp"
  mv "$tmp" "$dest"
  if grep -q '@HOME@' "$dest"; then
    echo "WARNING: $dest 仍含未替换的 @HOME@ 占位符" >&2
  fi
  echo "synced card: $profile -> $dest"
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

# --- model catalogs (generated, never tracked) ------------------------------
# 从 codex debug models 现场生成；结构变化时脚本会 WARNING 并非零退出。
if ! python3 "$repo_root/scripts/patch-codex-model-catalog.py"; then
  echo "WARNING: model-catalog 生成报告了问题（见上）——kimi/mimo/qwen 的 guardian 可能失败。" >&2
  echo "         仓库内不放 catalog（生成型产物）；请按上面的 WARNING 修好取源或结构后重跑本脚本。" >&2
fi

# --- 让运行中的 shim 用上新路由 ----------------------------------------------
if launchctl print "gui/$(id -u)/$shim_label" >/dev/null 2>&1; then
  launchctl kickstart -k "gui/$(id -u)/$shim_label" >/dev/null 2>&1 \
    && echo "restarted launchd service: $shim_label"
else
  echo "note: launchd 服务未加载（若手工跑着 shim，需要重启它才能用上新路由）"
fi

echo "Synced codex-agent cards to $shared_home"
