# Shim service Python path review adjudication

Branch: `fix/shim-service-python-path`
Base: `main`
Reviews: [Kimi](code-review-20260925-220602.md), [MiMo](code-review-20260925-221307.md)

## Decisions

| Finding | Decision | Resolution |
| --- | --- | --- |
| Reinstall can stop the previous service before a failed install | Accepted | Build and validate a candidate plist first; keep a copy of the old plist; restore it and reload the old service when port checks, bootstrap, or listener readiness fail. |
| Port check omits routes on 8794/8795; startup can report success without listeners | Accepted | Read every port from `shim-routes.json`; check conflicts and require all listeners after bootstrap. Status uses the same route list. |
| Dynamic paths are inserted into XML without escaping | Accepted | Generate the plist with Python `plistlib` and validate it with `plutil` before switching the service. |
| `assert` version check disappears under `PYTHONOPTIMIZE` | Accepted | Use an explicit Python 3.11+ check under `-I -S`; test with an old system Python and `PYTHONOPTIMIZE=1`. |

## Verification

- `python3 -m unittest discover -s tests`: 31 tests passed.
- `zsh -n codex-agent/bin/codex-auto-review-shim-service`: passed.
- `codex-auto-review-shim-service print-plist | plutil -lint -`: passed.
- `git diff --check`: passed.
- Tests use isolated HOME directories and fake `launchctl`/`lsof`; no live service was restarted during review.

## Residual risk

- Rollback is best effort if the old plist refers to a Python executable that no longer exists on the destination Mac; the command reports a reload failure in that case.
- A live launchd smoke test on the destination Mac remains necessary after copying the updated service script and running `install` there.
