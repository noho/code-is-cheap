RUNTIME/PROVIDER/MODEL: codex/mimo/gpt-5
CANARY=mimo-91d5f673

# Code Review

## Scope

- Mode: current changes (`$deepreview --base 61f19e42b439aa034d4f5738cc916af2b7e5fdd4`)
- Task label: `install-skip-mimo-20261004-01`
- Branch or PR: `feat/local-endpoints-installer`, follow-up documentation scope for open PR #45 in `noho/code-is-cheap`
- Base: `61f19e42b439aa034d4f5738cc916af2b7e5fdd4` (frozen HEAD/base)
- Output file: `docs/reviews/install-skip-readme-mimo-20261004.md`
- Generated timestamp from system clock: `20261004-205249`
- Included scope: only the two added paragraphs in `README.md` and `README.zh.md`, as present in `/private/tmp/code-is-cheap-readme-install-skip/diff.patch`
- Supporting static evidence: `install.sh`, `scripts/sync-agent-tools.sh`, and `scripts/sync-codex-agent.sh`
- Excluded scope: all earlier PR implementation/source changes, other repository files, tests, CI, credentials, live configuration, sessions, installed binaries, live/network/API probes, installer or sync execution, runtime installation claims, and the other reviewer's report
- Parallel review coverage: 无. This task explicitly prohibited sub-agent dispatch; this artifact is the independent MiMo route only. The external Qwen route was neither read nor integrated.

## Identity Checks

The exact frozen input and three manifest hashes were checked before evidence review and again after evidence review. Both observations matched.

| Identity | Expected | Observed before | Observed after | Result |
| --- | --- | --- | --- | --- |
| `git rev-parse HEAD` | `61f19e42b439aa034d4f5738cc916af2b7e5fdd4` | `61f19e42b439aa034d4f5738cc916af2b7e5fdd4` | `61f19e42b439aa034d4f5738cc916af2b7e5fdd4` | PASS |
| `README.md` SHA-256 | `184c412263f9245d4621e7f2ebc13b11176e7753904141648fd3083566b2b8be` | same | same | PASS |
| `README.zh.md` SHA-256 | `291c395c07a1f68cb2c582e6cf8d2124a6825294dbf01d5bb00b5272552d0e2f` | same | same | PASS |
| `install.sh` SHA-256 | `9305fa6e4a6df3aa5c22325831bb3a38f10b494936cf79df95da97c336a96f94` | same | same | PASS |

Frozen input files also remained stable during review:

- `/private/tmp/code-is-cheap-readme-install-skip/diff.patch`: `4fc2313efadb0219010066a714415882ef350269fa3770dca30c931102ef8c73`
- `/private/tmp/code-is-cheap-readme-install-skip/manifest.json`: `4cacce22bd15cb8182a482008f05d97419f52c0d2daef934353b5851189928f7`

## Findings

未发现实质性问题。

## Direct Evidence

### Prerequisites and successful installer path

- `install.sh:12` declares macOS, Git, Codex CLI, Claude Code, Python 3.11+, `jq`, `uv`, `tmux`, `rsync`, `zsh`, and `curl` as prerequisites.
- `install.sh:17-22` enforces macOS, all listed commands, and Python 3.11+ before deployment. Therefore the paragraph's precondition, "if `install.sh` completed successfully," is supported by a fail-fast prerequisite path.
- `install.sh:71-72` invokes `sync-agent-tools.sh` and `sync-codex-agent.sh`; these are the deployment steps the paragraph tells successful installer users to skip.
- `scripts/sync-agent-tools.sh:10-18` installs `agent-tools.zsh`, the Claude/Codex runners, supporting tools, `agent-endpoint.py`, and the default endpoint resource.
- `scripts/sync-codex-agent.sh:47-81` stages and installs Codex profile cards and model catalogs. This supports the statement that a successful installer deploys model cards.

### Shell reload

- `install.sh:75-84` adds `$HOME/.local/bin` to `PATH` and sources `~/.config/zsh/agent-tools.zsh` from `~/.zshrc`.
- `install.sh:90` explicitly directs the user to run `source ~/.zshrc` or open a new shell.
- Both new paragraphs preserve that requirement rather than implying the current shell changes automatically.

### Credentials and custom URLs

- `install.sh:50-67` creates `~/.config/zsh/agent-tools.local.zsh` only through exclusive creation and writes only a commented `DEEPSEEK_API_KEY` placeholder. `FileExistsError` leaves an existing file unchanged.
- `install.sh:88-89` tells the user to set provider keys and customize upstream URLs after installation.
- The new English paragraph says the user "still need[s] to set API keys and any custom URLs"; the Chinese paragraph says "仍需...填写 API key 和可选的自定义 URL." Neither claims that the installer supplies credentials or user-specific endpoints.

### Optional business profile and local service

- `scripts/sync-codex-agent.sh:106-115` updates business model defaults only when `~/.codex-agent/business/config.toml` already exists; otherwise it reports that the business config was not found and skips that work. The script does not create the business account home.
- The installer path contains no local model-server start operation. Its optional service branch at `install.sh:85-87` installs the repository's launchd shim service, not a local model service.
- Both new paragraphs explicitly keep the optional `business` account home and local model service outside installer responsibility.

### Diff boundary

- `/private/tmp/code-is-cheap-readme-install-skip/diff.patch` contains exactly one added paragraph in each README and no source or test changes.
- The English paragraph is at `README.md:127`; its Chinese counterpart is at `README.zh.md:123`.
- `git diff --check -- README.md README.zh.md` completed without output.

## Agent-Facing Check

- **Redundant installation:** PASS. After a successful `install.sh` run, an Agent must not run `./scripts/sync-agent-tools.sh`, `./scripts/sync-codex-agent.sh`, or other deployment steps merely because they appear below. The paragraph explicitly says to skip those manual deployment steps and limits them to manual installation or a later update.
- **Shell state:** PASS. The Agent should require `source ~/.zshrc` or a new shell after installer completion and credential/URL setup.
- **Credential ownership:** PASS. The instructions do not imply that `install.sh` creates, fetches, logs in, or supplies provider credentials. API keys remain user-owned and must be set explicitly.
- **Endpoint ownership:** PASS. Custom URLs remain user-owned; the installer may initialize defaults but does not claim to provide user-specific endpoints.
- **Optional `business` account home:** PASS. The installer does not create it; the paragraph explicitly leaves it to the user.
- **Optional local model service:** PASS. The installer does not start a local model server; the paragraph explicitly leaves local service preparation to the user.
- **Runtime claim:** PASS. This review makes no claim that installation was executed successfully; only the meaning and consistency of the documentation were checked statically.

## Open Questions

- 无。

## Residual Risk

- This was a narrowly scoped, static documentation review. Per task constraints, no installer, sync script, test, live service, or network/API probe was executed, so this artifact makes no runtime installation claim.
- Earlier PR implementation and unrelated documentation were not re-reviewed. The conclusion applies only to the two added paragraphs at the frozen HEAD/base shown above.
- The MiMo artifact intentionally does not inspect or adjudicate the independent Qwen review.
