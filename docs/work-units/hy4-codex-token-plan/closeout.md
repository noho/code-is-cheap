# Hy4 Codex runtime closeout

Status: code/tests/full review/fix re-review passed; delivery and live rollout pending.

Hy4 Codex CLI/App profiles, `hy`/`hunyuan` runner selection, shared registry/shim route8796, endpoint defaults and runtime catalog are restored. Existing provider snapshots, protocol mapping, approval policy and machine-local settings are preserved. Sync now checks stable same-PID ownership of every configured route before reporting restart success.

Verification: independent affected regression reruns205tests/11opt-in skips passed;4native Hy tool/allow/deny/error controls passed; actual staged branch runner completed native tools and automatic review with native/runner0,5upstream attempts,no retries. Post-fix28focused checks passed on byte-identical sources in isolated and actual workspaces. Two full reviews and two affected reviews are complete; sole accepted DS1 is fixed/closed, no new material findings. See implementation.md, fix.md, controller.md and the four timestamped reports.

Docs: bilingual README/runtime tables, catalog notes, skill inventory, plan/investigation/implementation/fix evidence updated. Live files and credentials are excluded.

Remaining external limit: tested Token Plan key returns403001(package disabled/no invocation permission); direct Hy4 native workflows pass. User/account owner must resolve permission before Token Plan use can succeed. Runtime service observation is bounded; unchanged opt-in test boundaries remain documented.

Draft PR: pending. No issue is associated with this work unit; issue linkage/comment are not applicable. User merges manually.

Authorized rollout from this reviewed checkout, after delivery check:

```bash
./scripts/sync-agent-tools.sh
./scripts/sync-codex-agent.sh
./scripts/sync-skills.sh
```

Update both installed factories before adding private Hy Codex entries. Then atomically add direct `default.hy.codex` and both Token Plan `override.hy` runtimes, with private0600backup and unrelated-value preservation. Backend permission failure must remain disclosed, not described as working Plan access.

Reload interactive functions with `source ~/.zshrc` or a new shell; reopen Agent sessions for skills. Installed runner callers already on PATH need no shell reload.

Next entry: draft PR delivery check, authorized rollout/private update, then final closeout pass.
