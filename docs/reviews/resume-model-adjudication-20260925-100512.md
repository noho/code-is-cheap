# Resume model selection: review adjudication

Branch: `fix/shared-provider-resume` (PR #39, still unmerged).

## Reproduction and scope

- The reported thread `01a0d626-0a68-7913-8394-a73c79d0f977` has a final recorded turn model of `mimo-v2.6-pro`; its local thread index likewise records provider `mimo` and model `mimo-v2.6-pro`.
- The shared base config defaults to `gpt-6-sol`. The user's plain `codex resume <id>` displayed MiMo. Thus the base default alone does not switch an existing thread.
- `codex resume -p gpt-6-sol <id>` displayed `GPT-6-Sol medium` in Codex CLI 0.156.1. The thread was locked by another app, so this check did not send a new turn or verify response routing.
- The launcher already inserts `-p <agent-id>` for `resume`; no launcher code change is needed. README examples incorrectly implied plain `codex resume` selected a new model.

## Parallel review and validation

- MiMo artifact: [code-review-20260925-100425.md](code-review-20260925-100425.md). Exit 0, success JSON, 38 turns, canary matched. One known `unrecognized_model` diagnostic warning.
- Kimi artifact: [code-review-20260925-095816.md](code-review-20260925-095816.md). Exit 0, success JSON, 33 turns, canary matched. One known `unrecognized_model` diagnostic warning.
- The primary agent checked both findings against the repository, the CLI help, the reported thread metadata, and the TUI startup display. `python3 -m unittest discover -s tests -v` passed 9/9; `git diff --check` passed.

## Decisions

| Review point | Decision | Action |
| --- | --- | --- |
| README omitted `tests/` from the repository tree (MiMo) | Accept | Added `tests/test_provider_registry.py` to both language versions. |
| Removing a provider ID can break old sessions (Kimi) | Accept as a maintenance contract | Documented retention of retired IDs and their last usable routes in the registry and both READMEs. |
| Plain resume model behavior needed evidence (MiMo question) | Resolved for the reported case | The user observed MiMo; thread metadata records MiMo; explicit `-p gpt-6-sol` displayed GPT-6 Sol. Chinese wording now states that plain resume cannot guarantee the base default. |
| Actual first request route after cross-provider resume (MiMo residual risk) | Remains unverified | The reported thread was locked by another app. The result establishes selected model at startup, not a completed model request. |

README now gives explicit `gpt-6-sol_codex resume <session-id>` and `codex resume -p gpt-6-sol <session-id>` examples. It also states that desktop app instances use separate session homes, whereas managed CLI profiles share `~/.codex`.
