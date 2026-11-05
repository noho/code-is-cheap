# Endpoint rename-disable implementation

Branch: `fix/endpoint-rename-disable`. Implemented the accepted `plan.md` and
controller scope. No agents, commits, push, PR creation, or live deployment were
invoked in this implementation pass.

## Changes

- `scripts/agent-endpoint.py`: `validate_document` returns the validated active
  sections. With factory defaults supplied, it ignores unknown private root
  fields and selects only exact recognized override-provider names before
  inspecting their contents. `load_endpoints` merges this view rather than raw
  private data. Factory validation and strict private default/active runtime and
  tuple validation remain in the existing owner; file ownership/type/mode,
  duplicate parsing, whole-tuple replacement, and credential rules are unchanged.
- `tests/test_install_endpoints.py`: four focused table-driven regressions cover
  `ds-flash-bak`, the user's `overrideds-flash-bak`, and root `overridexxx`
  rename/restore; complete private-default and factory fallback; other active
  overrides; retained snapshots; input and private-file preservation; existing
  file `--initialize`; malformed inactive content versus exact-name restoration;
  strict default/factory/runtime/tuple boundaries; malformed JSON and duplicates
  inside backups; real zsh `mimo_claude` startup against a native stub in both
  disabled shapes; and rejection of backup/environment credential fallback for
  empty effective cloud keys. Existing tests were retained.
- `README.md` and `README.zh.md`: updated only the private-connection sections
  with matching exact-name activation/restoration, fallback, inert-content,
  strict active/default schema, duplicate JSON, and key requirements.

No suffix rules, normalization, provider registry, field inheritance, or vendor
inference were added. The live private endpoint file and private keys were not
read. The three preexisting unrelated untracked review artifacts were not read
or changed. Only the four planned files and this work-unit artifact were edited.

## Actual verification

Run from `/Users/leo/workspace/code-is-cheap`, with synthetic private files,
isolated temporary homes, fake credentials, and native stubs:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_install_endpoints.py' -k rename_disable -k malformed_backups -k backup_selection -k mimo_native_launch
```

Exit 0: `Ran 4 tests in 2.536s`, `OK`.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_install_endpoints.py'
```

Exit 0: `Ran 34 tests in 29.681s`, `OK`. This includes the existing Hy
old-factory runtime rejection, file-security, factory-credential, local Codex,
launcher credential isolation, shim mapping/snapshot, and install-preservation
regressions.

```bash
git diff --check
```

Exit 0, no output. `git status --short --branch` confirmed the existing work
branch and only the four planned tracked-file changes, alongside the existing
untracked work-unit directory and three unrelated untracked review artifacts.

## Failure corrections and remaining limits

No test failures occurred; no failure-driven corrections were required. No known
implementation issues remain from these checks. Live endpoints, vendor APIs,
installed helpers, and service deployment were not exercised. The optional
unrelated ownership-mismatch mock was not added; existing owned regular
mode-0600 checks remain unchanged.

Independent reviews, any accepted fixes, delivery, and final closeout belong to
the controller. For eventual controller-approved live deployment, the applicable
commands are `./scripts/sync-agent-tools.sh` and `./scripts/sync-codex-agent.sh`;
neither was run here. No skill sync is needed for this scope.
