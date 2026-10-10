# S1 implementation

Gate: implementation; work unit sub-agents-defaults. Accepted plan commit: 1e20493. Existing branch/PR retained.

## Changes

- Direct runners keep lifecycle/private logs/permissions/routes, reject whitespace-only inputs and non-regular prompt files, measure elapsed via floating zsh SECONDS.
- Optional preflight checks only selected runtime, generates task-<fresh suffix>, accepts plain task sources, copies file input, appends brief final-answer instruction. Optional --canary and existing --artifact; exact optional envelope argv retained. No mandatory identity self-report or fixed headings.
- Result adapter adds terminal-only verbatim usage, optional runtime_metrics and wall_clock_seconds; unavailable/conflicting data stays null/empty, repeated stream usage not summed, failed terminals can retain actual reported metrics. No price estimates or new requests.
- SKILL ordinary path is 119 lines; advanced isolation/optional proof details in references/advanced.md. Both READMEs updated. Other skills unchanged.

## Validation

- python3 -m unittest tests.test_sub_agent_preflight tests.test_agent_run_results: 42 passed (11.619s).
- python3 -m unittest discover -s tests: 131 run, 122 passed, 9 skipped (34.352s). Skips are opt-in/macOS external tests, not asserted pass.
- bash scripts/validate-skills.sh: all six valid.
- bash -n preflight, zsh -n both runners, python3 -m py_compile adapter, git diff --check: pass.
- Actual Codex/Claude runtime Seatbelt synthetic tests: 2 passed (2.374s), local endpoint/synthetic credentials only. Evidence /private/tmp/defaults-native-20261010/{codex,claude}-probe.json; both exit 0, read-boundary kernel validation before runner, expected denied access not returned. These existing native tests exercise raw detail mode; collected metrics are verified by deterministic runner fixtures, not claimed as native collected-statistics proof.
- Fixed test setup PATH fallback and correct existing Claude ephemeral --name identity assertion; no implementation weakening to fit these tests.

## Finding and risk state

Implementation pending independent code review and Agent-facing synthetic evaluation; no accepted slice yet. Explicit proof/artifact failure behavior, detail output, known tool anomalies and routing have focused regression coverage.
Residual risks: legacy ceremony reliance assigned to later work unit if needed (user excludes migration); final-answer truth owned by calling project; native visibility/interruption owned by existing result-collection follow-up. No unclassified risk or extra live deployment. Docs decision implemented.

Next gate: code review.
