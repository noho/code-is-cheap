# Override rename-disable closeout

Status: **final closeout pass; work unit completed**. Draft PR: https://github.com/noho/code-is-cheap/pull/67. User merges manually.

## Behavior and documentation

Private configuration activates only exact root `override` and recognized provider names beneath it. Unknown private roots and override-provider names are inert and preserved. Rename `override.ds-flash` to `override.ds-flash-bak` or `override.overrideds-flash-bak` to disable that provider only; rename root `override` to `overridexxx` to disable the entire block. Restore the exact recognized name to revalidate/reactivate. Affected connections fall back to complete private defaults, then factory connections when omitted. Backup contents and inherited environment credentials never supply a fallback key.

Selection, validation and merging share the endpoint schema owner. Factory/default and known active runtime/tuple validation, global duplicate JSON rejection, owned regular mode-0600 checks, credential isolation and whole-tuple replacement remain intact. Both READMEs document exact-name activation, fallback and retained strict boundaries. No user configuration or credentials are committed.

## Verification and review

Four new table-driven regressions cover rename/restore, inactive malformed data versus active rejection, fallback keys, snapshots/no writes, and unrelated real-zsh `mimo_claude` dispatch against a native stub. All34 endpoint/install tests passed in implementation and both independent reviews; no skips. Whitespace checks and frozen product hashes passed.

Independent reports: `docs/reviews/code-review-20261105-145627.md` (MiMo Claude) and `docs/reviews/code-review-20261105-144106.md` (DS Codex, the AGENTS-authorized backup after actual Claude403). DS retained its Python3.9 setup failures and successful Python3.11/PATH rerun. The sole MiMo suggestion, adding an unchanged owner-UID branch test, is rejected-with-reason under the controller's pre-implementation scope decision; the guard is unchanged and correct. The original report remains unchanged. No accepted unfixed finding or code blocker remains. See controller.md and implementation.md for evidence and adjudication.

## PR delivery and authorized live sync

Initial delivery verified repository/head repository `noho/code-is-cheap`, base `f2ba5abe8b123a6581632860e59e9bf797b76133`, source head `a5a799454ba406d58a18d422db0a998cdb1b8fbf`, all13 changed files and GitHub blob OIDs, all4 reviewed product hashes, title/body, draft state and final push. Full immutable diff SHA256: `3c7e61ef1c08c2bc0ff29bbf7daedc15d700efe4cda76e6a6ef817115b95b936`. No CI workflow is configured and GitHub reported zero statuses/checks/runs. Plugin creation succeeded; immutable comparison used `gh api` because the plugin lacks that interface. Retrievable PR metadata/diff/receipt: `/private/tmp/endpoint-rename-disable/delivery-initial/`.

Executed from this reviewed checkout on 2026-11-05, after delivery passed; both exited0:

```bash
./scripts/sync-agent-tools.sh
./scripts/sync-codex-agent.sh
```

Both installed endpoint helpers and their factories match the reviewed source. The actual private file remained byte-for-byte identical with mode0600. Using private temporary copies, both installed helpers accepted provider `overrideds-flash-bak` and root `overridexxx`; all four mocked native `mimo` launches selected the expected model/authentication and passed without vendor inference. The restarted launchd job (PID51064 at verification) owned all9 ports, 8788–8796. Host `lsof` emitted nonfatal warnings about an unrelated TimeMachine SMB mount; all individual PID/port checks exited0. Raw sync logs and sanitized verification are outside Git at `/private/tmp/endpoint-rename-disable/live/`.

The final docs-only closeout tail is pushed and its PR identity/full diff/head/base checked again before user-facing completion; final immutable receipt is `/private/tmp/endpoint-rename-disable/delivery-final/receipt.json`. No product change follows the reviewed source. Three unrelated original untracked runner-handle-loss artifacts remain excluded.

## Remaining limits and next entry

Existing owner-UID mismatch dynamic coverage is maintainer-owned later file-security testing work if that guard changes. Full-repository/network coverage remains under existing testing policy/operator ownership; this fix performs no model-quality work or live vendor inference. Startup readiness is a bounded observation. No new unclassified risk or required user decision remains. No associated issue exists, so issue linkage and closeout comments are not applicable.

Next: user manually merges PR67 and can directly retry `mimo_claude` after applying the desired private rename. Live already has the tested helper; launchers invoke it anew and the shim was restarted. If reloading interactive launcher definitions, use `source ~/.zshrc` or a new shell; no skill changes require session reopening.
