# Runtime backup maintenance

## Plan and boundaries

- Work on existing `fix/agent-backup-runtime-tools` (baseline `eb8a384`); preserve controller snapshots and `baseline.json`. Both maintenance copies initially match the two authorized original files (`cmp`, exit 0).
- Add required `agent-run-result.py` and optional sandbox wrapper/adapter/installer to both copies. Keep USB restore paths, executable modes and previous-file rollback aligned. Preserve complete `.codex`/catalog, credentials/endpoints and existing session policies and HOME relocation.
- Record only source SRT presence/version, inspecting the Node package without running SRT. Match `scripts/agent-sandbox-launch.mjs:validateRuntime` layout checks and the installer pin `@anthropic-ai/sandbox-runtime@0.0.79`; never copy SDK, node_modules or source `srt` links. Restore validates Node >=22.12, npm, package/version/modules; only a source with SRT and explicit `--install-deps` can invoke the archived installer.
- Black-box test copied scripts and synthetic archives in independent `/private/tmp` fake HOMEs; stub package managers, network and CLIs. Check missing collector, optional helpers, rollback/modes, catalog/HOME relocation, metadata, offline restore, pinned install and invalid runtimes; run bash/zsh syntax and diff checks.

Only the requested maintenance scripts, test, this document, optional README and payload ignore rule may change. No separate review, commit/push/PR, live deployment, real HOME/config/keys, SRT/Agent tasks, package installation or service/API operations. The original implementation invocation used a nested same-provider `gpt-6-sol` implementer through `codex-agent-run` under the repository AGENTS workflow; that delegation remained inside the authorized file/test scope. This accepted remediation is performed directly by the assigned Sol implementer.

## Implementation and validation

- Both copies cover all four tools. USB backup/restore requires a regular collector (rejects source symlinks and archive symlinks/directories before moving target files); all four restore with mode 755 and participate in previous-file rollback. Sandbox helpers remain optional. The function preserves helper modes and removes stale optional copies.
- USB `manifest.txt` and function `agent-sandbox-runtime.txt` record only `sandbox_runtime_installed`/`sandbox_runtime_version`. Probes read package files, never execute SRT. Both omit node_modules and never select the machine SDK or source `srt` link; the function also prunes old node_modules copies while retaining shared sessions. Source versions can differ; restore requires the pinned 0.0.79 layout.
- Offline restore reports prerequisites and an exact target-HOME installer command. `--install-deps` uses only an installer present in the archive, forces target install/bin directories, and rejects bad package version, bin mapping, required modules, old Node or missing npm. A target already meeting requirements is reused. Source without SRT never triggers optional installation. The existing general CLI installer does not upgrade an already present old Node; the new SRT gate reports that prerequisite explicitly.
- Accepted DS Flash finding 1 is limited to remediation/documentation: missing-collector archives still fail before confirmation or target mutation. Only that missing member gets the explanation that the archive predates the required collector. Old payloads must be recreated on the source using the updated backup script to use the new restore; install current agent tools with `./scripts/sync-agent-tools.sh` on the source if the collector is missing, then run updated `backup` and `verify` before migration. If the source is unavailable, `verify` remains usable and the archive should be retained for separate manual data recovery; this does not automatically restore a working runner. No archive generations, permissive fallback or new restore flags were added.
- Accepted MiMo Flash finding 1 adds an explicit guarded archived-installer call, preserving installer/npm stderr and reporting the concrete installer path on failure. The guarded optional SRT restore call returns nonzero with an explicit statement that environment files were already restored, optional dependencies are not ready and previous files are retained at `rollback_root`. It does not perform or claim automatic rollback or report restore success. Installation/network defaults are unchanged.

Original implementation verification (retained evidence):

```bash
test_home=$(mktemp -d /private/tmp/agent-backup-test-home.XXXXXX)
HOME="$test_home" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_agent_backup_restore.py -v
result=$?
rm -rf "$test_home"
exit "$result"
```

Original exit **0**, **10 tests passed** (16.759s). Scripts are copied into temporary USB/function locations; source and target HOME differ. Subprocess environments do not inherit personal config/credential variables. npm creates synthetic package layouts and logs its exact arguments; brew/curl/uv/Agent CLIs/crontab are stubbed. Legacy function copies from `/etc`/USB are intercepted. No SRT/Agent execution or real package installation occurs. Tests cover rollback/modes, complete nested/hidden catalogs, `model_catalog_json` HOME replacement, private fixture data/sessions, absent helpers/SRT, offline prompts, fixed SDK installation, bad target and post-install layouts, Node/npm prerequisites, and refusing an unarchived target installer. Initial test exit 1 was caused by fixture quoting/missing directories; fixed before the passing runs.

- `env -i HOME="$syntax_home" PATH=/usr/bin:/bin /bin/bash -n scripts/backup/agents-backup-restore.sh`: exit 0; independent mktemp HOME removed afterward.
- `env -i HOME="$syntax_home" PATH=/usr/bin:/bin /bin/zsh -f -n scripts/backup/backupsysfiles.zsh`: exit 0, same syntax-only fake HOME.
- `git diff --check`: exit 0. `git diff --no-index --check` against both authorized originals, and `/dev/null` for new test/document/README: exit 1 because files differ, **no whitespace diagnostics**.
- `git check-ignore scripts/backup/payload/agent-home.tar`: exit 0, matches the only new ignore rule. No payload or private shell configuration was placed in the repository. Sol final runs used `-B`. Later controller verification generated ignored bytecode; bytecode is ignored and not committed, and this document does not claim that the current workspace contains none.

## Accepted remediation verification

Changes are limited to `scripts/backup/agents-backup-restore.sh`, `scripts/backup/README.md`, `tests/test_agent_backup_restore.py` and this document. Frozen peer reviews, baseline, `backupsysfiles.zsh` and controller snapshots were not modified. The original nested delegation evidence is retained; no additional delegation was used for this fix.

```bash
validation_home=$(mktemp -d /private/tmp/agent-backup-fix-home.XXXXXX)
env -i HOME="$validation_home" PATH="$PATH" python3 -B -m unittest discover -s tests -p test_agent_backup_restore.py -v
validation_status=$?
rm -rf "$validation_home"
exit "$validation_status"
```

Actual final test exit **0**, **11 tests passed** (18.013s). The existing synthetic missing-collector test now checks source installation/rebackup/verify guidance, the source-unavailable manual-recovery limitation, successful standalone `verify` and unchanged target files with no rollback directory. Existing invalid-post-install/old-Node/missing-npm cases now check the restored-files diagnostic, reported previous-files path and retained previous contents without success/ready output. One focused npm-failure case checks preserved npm stderr, the concrete installer error, retained prior `.zshrc` and installer at the reported path, newly restored files and nonzero exit. Normal restore/helper/catalog/optional SRT cases still pass. All installations remain stubs; no real backup, package install, model probe, service or live operation was run.

The controller's **10 tests / 17.179s** and DS Flash's **10 tests / 17.400s** results apply to the frozen pre-fix inputs. Their raw review evidence is unchanged; the 11-test result above is this remediation's validation.

Final syntax checks used separate temporary HOMEs: `bash -n scripts/backup/agents-backup-restore.sh` and `zsh -f -n scripts/backup/backupsysfiles.zsh` both exited **0**. `git diff --check` exited **0**. Explicit `git diff --no-index --check` on the restore script against its authorized sanitized original and on README/test/this document against `/dev/null` returned **1** because files differ, with **no whitespace diagnostics**; these explicit checks cover the untracked files as well.

No implementation blockers remain. Actual dependency downloads, macOS isolation, live backup/restore and services/API operations were intentionally not exercised. `baseline.json` and private snapshots remain unchanged. No commit/push/PR or live write; independent reviews and deployment remain with the controller.
