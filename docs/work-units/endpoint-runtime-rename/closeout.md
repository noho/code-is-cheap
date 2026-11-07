# Runtime override rename closeout

Status: **final closeout pass; work unit completed**. Draft PR: https://github.com/noho/code-is-cheap/pull/68. User merges manually.

## Result

Private override root/provider/runtime names now consistently use exact factory-schema selection. Rename `override.ds-flash.codex` to `codex-bak` or any unrecognized name to disable only that runtime; sibling `claude` and other providers remain active. Empty/all-filtered override provider maps are inert. Complete private defaults, then omitted-runtime factory tuples, supply fallback. Restoring the exact name validates/reactivates it. No suffix matching or name normalization.

Default/factory, active connection-field/URL/model/key validation, global duplicate JSON rejection, owned regular mode-0600 checks, snapshots and credential isolation remain strict. Connection-field rename is not disablement. Both READMEs and prior contradictory unknown-runtime/old-Hy-schema expectations are aligned with this contract. Private files and credentials are outside Git.

## Evidence and findings

Eight focused cases and all37 endpoint/install tests passed in implementation and both independent primary Claude full reviews: MiMo `docs/reviews/code-review-20261107-104533.md`, DS `docs/reviews/code-review-20261107-104313.md`. Both found no substantive issue or open question. No fallback reviewer or fix/re-review loop was required. Initial reviewer sandbox-localhost failures and successful corrected runs are retained, not counted as passing first runs. Both source hashes and complete four-file snapshot match the final product. See implementation.md, test-results.json and controller.md for actual commands/results and scope.

## Delivery and authorized sync

Initial PR delivery verified repository/head repository `noho/code-is-cheap`, base `f5e16766a94b7f19680296b0aee1c7a16a1402a3`, source head `23bd6c4971adf8dd78395ddec28bd8244abc7266`, all12 changed-file blob OIDs, all4 frozen product hashes, draft title/body and remote push. The GitHub plugin's fixed-OID comparison agreed with the full immutable diff/blob metadata preserved using `gh api`. Full diff SHA256: `8332d2fad71694beef7882a38c29b60c2e56644943db0135c794150eaf9d24c9`; retrievable evidence `/private/tmp/endpoint-runtime-rename/delivery-initial/`. No repository workflow is configured and GitHub returned zero statuses/checks/runs. Creation transitioned to controller delivery check before draft-PR-pass; then final closeout/authorized rollout proceeded.

Executed from the reviewed checkout on 2026-11-07, both exit0:

```bash
./scripts/sync-agent-tools.sh
./scripts/sync-codex-agent.sh
```

Both installed helper/factory pairs match reviewed sources. The actual current file with `claude` and `codex-bak` passes the selected DS Codex key check; the private file stayed byte-for-byte identical with mode0600. On private temporary copies, both installed helpers passed `codex-bak` and arbitrary-name disablement, whole-default fallback, unchanged Claude sibling and excluded backup data. The installed `ds-flash_codex` launcher passed pre-exec checks and reached the native stub with the correct profile. The restarted launchd PID44558 owned all9 ports8788–8796 at verification. No vendor inference was performed. Raw sync logs and sanitized verification remain private under `/private/tmp/endpoint-runtime-rename/live/`.

The final two-file factual closeout tail is pushed and PR identity/full immutable diff/head/base checked again before the user-facing completion; receipt `/private/tmp/endpoint-runtime-rename/delivery-final/receipt.json`. No product change follows the reviewed version. Three original unrelated runner-handle-loss artifacts remain untracked/excluded.

## Limits and next entry

Full repository/vendor API coverage remains under existing testing/operator policy; startup readiness is a bounded observation. Old-factory runtime filtering has synthetic coverage and both installed factories were synced together. Existing unrelated owner-UID policy gaps remain excluded. No code blocker, accepted unfixed finding or unclassified new risk remains. No associated issue exists, so issue linkage/comments do not apply.

Next: user manually merges PR68 and directly retries `ds-flash_codex`, retaining `codex-bak`. Runtime root/provider renames also remain supported. Live is already synced; no skill update applies. If interactive launcher definitions are reloaded, use `source ~/.zshrc` or a new shell; installed runners already on PATH need no shell reload.
