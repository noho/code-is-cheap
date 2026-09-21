#!/usr/bin/env bash
set -euo pipefail

# Sync the tracked codex-agent configuration to ~/.codex-agent:
#
#   codex-agent/profiles/<profile>/config.toml   六个第三方 profile 的配置
#   codex-agent/bin/codex-auto-review-shim       自动审批反代（guardian 模型名改写）
#   codex-agent/bin/codex-auto-review-shim-service   launchd 管理脚本
#   codex-agent/shim-routes.json                 反代路由表
#   model-catalog.json（kimi/mimo/qwen）          由 scripts/patch-codex-model-catalog.py 现场生成
#
# 覆盖 config.toml 前会写时间戳备份（.bak-YYYYmmddHHMMSS）。注意：Codex 自己写入的
# [projects.*] trust 条目不在仓库模板里，覆盖后会丢；Codex 会在再次进入相应目录时重建。

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
  install -m 600 "$src" "$dest"
  # 模板用 @HOME@ 占位（Codex 只接受绝对路径，~ / $HOME 都不展开），安装时注入本机 home
  tmp_inject="$dest.tmp.$$"
  sed "s|@HOME@|$HOME|g" "$dest" > "$tmp_inject"
  chmod 600 "$tmp_inject"
  mv "$tmp_inject" "$dest"
  if grep -q '@HOME@' "$dest"; then
    echo "WARNING: $dest 仍含未替换的 @HOME@ 占位符" >&2
  fi
  if [[ -f "${backup:-}" ]]; then
    # [projects.*] trust 与 [hooks.state] 是 Codex 自己写入的尾部运行时状态，
    # 仓库模板不含它们；从备份逐字节回填（含尾随空行，避免无谓 diff），
    # 否则每次同步都要重新信任目录。
    preserved_file="$dest_dir/.preserved.$$"
    awk '/^\[(projects\.|hooks\.state)/{keep=1} keep' "$backup" > "$preserved_file"
    if [[ -s "$preserved_file" ]]; then
      printf '\n' >> "$dest"
      cat "$preserved_file" >> "$dest"
      echo "preserved runtime sections: $(basename "$backup")"
    fi
    rm -f "$preserved_file"
  fi
  echo "synced profile: $profile"
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
