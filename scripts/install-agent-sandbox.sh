#!/usr/bin/env bash
# Optional dependency: normal runners and sync do not require srt.
set -euo pipefail
command -v node >/dev/null || { echo 'Node >=22.12 is required' >&2; exit 1; }
node -e 'const [a,b]=process.versions.node.split(".").map(Number);process.exit(a<22||(a===22&&b<12))'
command -v npm >/dev/null
prefix="${AGENT_SANDBOX_INSTALL_DIR:-$HOME/.local/share/agent-sandbox}"
bin_dir="${AGENT_RUN_BIN_DIR:-$HOME/.local/bin}"
npm install --prefix "$prefix" --omit=dev --ignore-scripts '@anthropic-ai/sandbox-runtime@0.0.79'
mkdir -p "$bin_dir"
ln -sfn "$prefix/node_modules/.bin/srt" "$bin_dir/srt"
echo "Installed optional srt 0.0.79 to $prefix"
