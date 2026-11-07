# Native Codex provider handoff implementation

Implemented on branch `fix/codex-native-provider-handoff`, against HEAD
`e58598e3f7d3585c4f0f9ccca2fff486c3ea1e5f` on 2026-11-07 (Asia/Shanghai).
This delegated implementation follows the controller-accepted `plan.md` and leaves that plan unchanged.
No recursive delegation, reviews, commit, push, PR or live deployment was performed by this implementer.

## Behavior and scope

- `scripts/agent-tools.zsh`: removed the automatic repair/session lookup block and its UUID/existence/tail-count restrictions. Native `resume` is forwarded as supplied. Only leading `--resume` and `--resume=<value>` normalize to `resume` and `resume <value>` after the existing wrapper parsing. Bare `--resume` adds no session argument; `--resume=` preserves one empty session argument.
- Profile injection, shared/private `CODEX_HOME` and `CODEX_SQLITE_HOME`, credential scrubbing, title/full-access handling, local-model override and runner `exec resume` are unchanged. `gpt_codex` still delegates to the Sol launcher.
- `scripts/repair-codex-reasoning-history.py`: module description and `--apply` help only. The standalone utility, flags, repair algorithms and sync installation remain available for explicitly manual legacy recovery; its help states that it cannot bypass provider mismatch.
- `README.md` / `README.zh.md`: removed active auto-repair and launcher-resume Python claims; documented native forwarding, the observed read-only/new-chat flow, provider/model compatibility distinction and manual legacy recovery boundaries. The official app-server source is linked without equating the observed TUI continuation with `thread/fork`.
- `tests/test_repair_codex_reasoning_history.py`: replaced the auto-mutation expectation with exact JSON argv capture using the existing temporary-home fixture; retained manual recovery/install tests and made the sync test HOME explicitly temporary.
- `tests/test_install_endpoints.py`: removed the launcher fixture's repair installation; reused the existing native/profile fixture for third-party and separate business-home coverage.

No provider detection, custom continuation/fork engine, metadata rewriting or automatic `c` action was added. Historical artifacts and the three initial unrelated untracked `docs/reviews/runner-handle-loss-20261023-*` files were left untouched.

## Validation actually performed

Commands ran from `/Users/leo/workspace/code-is-cheap`. Python: `3.11.15`.
Shell: `zsh 5.9 (arm64-apple-darwin26.0)`.

| Command | Actual result |
| --- | --- |
| `zsh -n scripts/agent-tools.zsh` | PASS, exit 0, no diagnostics. |
| `python3 -m unittest discover -s tests -p test_repair_codex_reasoning_history.py` | PASS, 12 tests, `OK`; final run 1.969 seconds. |
| `python3 -m unittest discover -s tests -p test_install_endpoints.py` | PASS, 38 tests, `OK`, 34.095 seconds. |
| `git diff --check` | PASS, exit 0, no diagnostics. |
| `python3 scripts/repair-codex-reasoning-history.py --help` | PASS, exit 0; manual legacy recovery and provider mismatch boundary visible in CLI help. |
| `git status --short` | Only the six allowed source/doc/test files modified plus the work-unit directory; the three initial unrelated review files remain untracked. |

The repair/history suite passed initially as well (12 tests, 2.403 seconds); its final run followed the addition of explicit wrapper-title and empty separate-session-argument cases. No source/endpoint-test changes followed the passing endpoint suite.

The launcher matrix covers both `gpt-6-sol_codex` and `gpt_codex`: literal and aliased resumes, bare pickers, empty session values, help/last/all options, names and unavailable sessions, flags before/after the selected session, more arguments than the former repair limit, delimiter handling, alias-looking prompt text, Unicode/newline/space/empty arguments, and `exec resume`. It checks shared home selection, byte-identical mixed-provider reasoning/session metadata, no new home artifacts or backups, and an uninvoked repair trap. Fake native stdout/stderr and exit 23 propagate exactly for unavailable, empty and bare forms. Endpoint tests additionally exercise subscription profiles without connection queries, real third-party connection validation with fake credentials, business's private home without profile injection, existing title/local-model behavior and runner resume.

All launcher/native processes use temporary homes and fake native executables. Sync/install checks use temporary homes and destinations. The third-party resume fixture stubs only the shim-presence check to avoid contacting a live shim. Existing endpoint suite HTTP checks use local fixtures. No live model call, real-session read/write or live installation was used.

The bilingual diff was checked, and the following active-file search returned no matches (expected `rg` exit 1):

```bash
rg -n 'repair and resume|resume repair|resume 修复|--resume.*repair|--resume.*修复|修复并恢复|cross-provider resume|跨 provider 恢复' README.md README.zh.md scripts/agent-tools.zsh scripts/repair-codex-reasoning-history.py tests/test_repair_codex_reasoning_history.py tests/test_install_endpoints.py
```

## Tested content identity (SHA-256)

```text
70add1f738874b8cc9b5068013713b0e1e851bb058184730d960fda2a7469c5c  scripts/agent-tools.zsh
706b6c9da1574feb6aa843e83ccfca790af82f0df97c9f54df623f1ec1af73e5  scripts/repair-codex-reasoning-history.py
48edfcf4d772cb9cb49973b3df42f2b65f216546793ece813fe8184b433113e0  tests/test_repair_codex_reasoning_history.py
0f9ded83ea09776f822161b38622ffc67965e64c90ce2f50e08c7c43b690a004  tests/test_install_endpoints.py
8708c63c5e3c3e32f76807799dc66671ce5111da75ba2201474257dd18b55b01  README.md
b416a91ed78af909071396223d5fb90c6f30b2c9696fc2612f7a9e092aa031b0  README.zh.md
96001ee03dc33a07b47858508f2a71bda6e712722044a12a52a370bb5dbfa5dc  docs/work-units/codex-native-provider-handoff/plan.md
```

## Limits and controller closeout

No known implementation blocker remains. Independent review/adjudication and repository delivery remain with the controller. This boundary test does not validate upstream Codex UI implementation, version-specific shortcut wording, actual provider enforcement or successful transcript reading in every session. It does not promise complete internal-state/tool-execution transfer. The native TUI observation and official app-server evidence come from the user/controller, not a new live experiment in this implementation.

After the controller completes final closeout, remind the user to sync from the repository checkout containing the approved changes. The applicable command is:

```bash
./scripts/sync-agent-tools.sh
source ~/.zshrc  # or open a new shell to reload interactive launchers
```

Live sync requires separate user authorization and was not run here. Skill/profile sync is unnecessary for this scope. Runner callers already using the installed runner on PATH do not need a shell reload.
