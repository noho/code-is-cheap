#!/usr/bin/env bash
set -euo pipefail

# Sync the tracked codex-agent configuration to ~/.codex-agent:
#
#   codex-agent/profiles/<profile>/config.toml   profile 配置（仓库只存核心设置）
#   codex-agent/bin/codex-auto-review-shim       自动审批反代（guardian 模型名改写）
#   codex-agent/bin/codex-auto-review-shim-service   launchd 管理脚本
#   codex-agent/shim-routes.json                 反代路由表
#   model-catalog.json（kimi/mimo/qwen）          由 scripts/patch-codex-model-catalog.py 现场生成
#
# config.toml 写入的是"仓库模板 + live 独有内容"的合并结果，合并逻辑在
# scripts/codex-config-merge.py：模板拥有它定义的设置（model、reasoning effort、沙箱、
# 审批、env 策略等），live 拥有模板没有的内容（[projects.*] trust、[hooks.state]、app
# 写入的 [mcp_servers.*]/[plugins.*]/[marketplaces.*]/[tui.*]/[desktop] 及 notify 等根键）。
# 合并失败时脚本中止，live 文件保持原样。覆盖前会写时间戳备份（.bak-YYYYmmddHHMMSS）。

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
target_root="${CODEX_AGENT_TARGET:-$HOME/.codex-agent}"
shim_label="com.leo.codex-auto-review-shim"

mkdir -p "$target_root"

# --- profiles ---------------------------------------------------------------
for src in "$repo_root"/codex-agent/profiles/*/config.toml; do
  [[ -f "$src" ]] || continue
  profile="$(basename "$(dirname "$src")")"
  dest_dir="$target_root/$profile"
  dest="$dest_dir/config.toml"
  backup=""
  mkdir -p "$dest_dir"
  if [[ -f "$dest" ]]; then
    backup="$dest.bak-$(date +%Y%m%d%H%M%S)"
    cp -p "$dest" "$backup"
    echo "backup: $backup"
  fi
  # 先合并再装入：合并失败就中止，live 文件保持原样。
  merged_file="$dest_dir/.merged.$$"
  merge_args=(--template "$src")
  if [[ -f "$backup" ]]; then
    merge_args+=(--live "$backup")
  fi
  if ! python3 "$repo_root/scripts/codex-config-merge.py" "${merge_args[@]}" > "$merged_file"; then
    rm -f "$merged_file"
    echo "ERROR: $profile 配置合并失败，$dest 未改动" >&2
    exit 1
  fi
  chmod 600 "$merged_file"
  # 模板用 @HOME@ 占位（Codex 只接受绝对路径，~ / $HOME 都不展开），安装时注入本机 home
  tmp_inject="$merged_file.inject.$$"
  sed "s|@HOME@|$HOME|g" "$merged_file" > "$tmp_inject"
  chmod 600 "$tmp_inject"
  mv "$tmp_inject" "$dest"
  rm -f "$merged_file"
  if grep -q '@HOME@' "$dest"; then
    echo "WARNING: $dest 仍含未替换的 @HOME@ 占位符" >&2
  fi
  if [[ -f "$backup" ]]; then
    echo "synced profile: $profile (template + live runtime state, backup $(basename "$backup"))"
  else
    echo "synced profile: $profile (template only)"
  fi
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

echo "Synced codex-agent config to $target_root"
