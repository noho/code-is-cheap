# Codex native provider handoff — controller record

## Scope and plan check

User requested following the current native Codex continuation flow after demonstrating that a cross-provider resume becomes read-only and `c` successfully starts a conversation reading the saved transcript. Scope: remove automatic launcher history repair, preserve native resume and thin compatibility aliases, retain explicitly manual legacy repair, update bilingual documentation and regression tests. No live deployment or real-session modification is authorized by this work.

Plan: [plan.md](plan.md). Controller read the affected launcher block, existing regression tests and README claims and checked the plan against the user evidence and [official OpenAI documentation](https://learn.chatgpt.com/docs/app-server#start-or-resume-a-thread). Accepted: native Codex owns provider compatibility and handoff. Removing the old repair block resolves the destructive pre-launch behavior without a new provider detector or handoff implementation. Alias normalization is local and preserves existing public entry points; no separate architecture/plan review is necessary for this deletion and forwarding change.

Planner: `codex-agent-run --provider gpt-6-sol`, native/outer exit 0; report session `01a1b525-edb6-7671-82e4-4230afb93e43`, logs `/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/agent-run.t56XojU8/`. Current work branch: `fix/codex-native-provider-handoff`, baseline `e58598e3f7d3585c4f0f9ccca2fff486c3ea1e5f`.

Pre-existing unrelated untracked `runner-handle-loss-20261023-{evidence.json,investigation.md,notification.json}` files under `docs/reviews/` are excluded from edits and commits.

## Status

Plan and implementation accepted for independent review. User subsequently confirmed that removing our added resume processing is sufficient; implementation follows that narrow scope, with no new handoff mechanism.

Implementation: [implementation.md](implementation.md), Codex `gpt-6-sol`, native/outer exit 0, session `01a1b528-7bec-7a70-b8af-3c251fa2c913`, original logs `/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/agent-run.UFBL0CeO/`. Controller read all six source/test/documentation diffs, verified every recorded SHA-256 against current files, checked original runtime command outputs and preserved concise [validation evidence](validation-evidence.json). Both suites pass (12 + 38 tests), shell syntax and diff whitespace pass. Test boundaries cover exact argv, literal/alias/picker forms, names/options/empty arguments, byte-identical saved history, repair trap, native output/status and third-party/business homes. Manual repair algorithm and installation remain unchanged; help and bilingual docs now describe native continuation and explicitly manual legacy recovery.

## Independent review and adjudication

Both independent reviews ran concurrently through the required Claude runtime routes and completed with native/outer exit 0:

- `ds-flash`: [review](../../reviews/code-review-20261107-165005.md), session `2ee1c957-ba9d-4211-af2e-16990d72d565`, logs `/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/agent-run.RI3RZqRd/`.
- `mimo-flash`: [review](../../reviews/code-review-20261107-170112.md), session `b9443640-a1d1-43ab-9918-6931994ff177`, logs `/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/agent-run.g0FKgBVB/`.

Both concluded “未发现实质性问题”. Controller read both complete artifacts, checked direct launcher/runner call-chain evidence, exact source hashes, independent temporary-home reproductions and test outcomes. They independently verified the same reviewed content; neither read the other review. No accepted defect, blocking question or required fix remains, so no empty fix/re-review round is needed. The DS Codex-runtime backup was unnecessary.

Reviewer sandbox-local socket/mkdir restrictions were isolated by successful permitted reruns; nonfatal CLI model-label warnings and native tool-error observations remain in the original reports/logs. They do not indicate an unresolved implementation or provider-runtime failure. Required 12 + 38 tests pass; MiMo additionally ran the existing backup suite (11 tests, pass). Broadening/repeating tests further is unnecessary for this three-line alias conversion and removal of automatic repair.

Residual observations are nonblocking: upstream UI/shortcut/transcript-reading behavior belongs to Codex and was not retested against real sessions; existing wrapper option parsing is outside this change; the standalone repair remains an explicitly manual operation. DS noted a hypothetical stale-capture weakness in two consecutive equivalent test cases; current code unconditionally executes native Codex, while independent probes, exact argv assertions and mutation traps supply sufficient evidence. No new issue or scope expansion is warranted.

Review pass. Intended deliverables are the six source/test/documentation files, the work-unit artifacts and the two reviews above; the three unrelated untracked files remain excluded.

## Delivery verification and final closeout

- Draft PR: [noho/code-is-cheap #69](https://github.com/noho/code-is-cheap/pull/69), `Stop automatic reasoning repair on Codex resume`. Head repository and base repository are both `noho/code-is-cheap`; head branch `fix/codex-native-provider-handoff`, base `main`. Title/body accurately describe the final implementation, test evidence, manual legacy tool and live-sync step.
- Reviewed implementation commit `9170045c614b7545ed9f700b12db005c2f24e8b5` was committed and pushed. PR metadata and local HEAD both identify that commit against base `e58598e3f7d3585c4f0f9ccca2fff486c3ea1e5f`. Remote comparison is ahead by one, behind by zero, with exactly the intended 12-file manifest. Public immutable [compare](https://github.com/noho/code-is-cheap/compare/e58598e3f7d3585c4f0f9ccca2fff486c3ea1e5f...9170045c614b7545ed9f700b12db005c2f24e8b5) corresponds to the reviewed changes; all seven recorded file hashes were rechecked after push and still match.
- Complete exact-OID diff snapshot: `/private/tmp/codex-native-handoff-9170045.diff`, SHA-256 `7bc41f2b65356d2cc3ea5d9764a48f7fd1771a9bcbd02af5677c19c4d500b626`. Git commit/tree objects and the immutable comparison provide the retrievable version if the local temporary snapshot is later removed. This final closeout-only update does not alter any reviewed implementation, test or README content.
- PR is open and draft. GitHub `statusCheckRollup` is empty; this repository has no configured workflow checks to await. Local mandatory validation and both independent reviews passed. No merge, review request, external comment, or live deployment was performed. This work is not linked to an issue, so issue closing/comment requirements do not apply.
- Final result: **final closeout pass; work unit completed**. Removed automatic reasoning repair, preserved thin resume aliases and native Codex ownership, updated bilingual guidance and manual-tool help, and delivered tests/review evidence. No accepted finding or blocking residual risk remains. Upstream UI behavior and existing wrapper parsing limitations retain the owners/scope described above.
- Next entry point: user manually reviews/merges PR #69, then authorizes live sync from the checkout containing the approved changes using the commands below. Only this closeout record changes after the reviewed implementation commit; the controller verifies the final documentation push without repeating unaffected code review/tests.

## Live sync after approval

From the checkout containing approved changes:

```bash
./scripts/sync-agent-tools.sh
source ~/.zshrc
```

Opening a new shell may replace `source ~/.zshrc`. Runner callers already using the installed runner on PATH need no shell reload. No skill/profile/catalog changes are planned, so `sync-skills.sh` and `sync-codex-agent.sh` are unnecessary. Live deployment requires user authorization; these commands have not been run against live destinations.
