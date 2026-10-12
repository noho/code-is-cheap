# PR55 finding1 fix

Accepted finding1 (P3) from [pr-review-decision.md](pr-review-decision.md) is addressed in the working tree, pending controller publication and exact-OID dual PR re-review. Branch: `feat/official-provider-catalogs`; inspected/current HEAD: `5d25d37f16b69fd4b8a47b6c4aba31dd4c691d71`. This artifact does not declare a review or Gateflow gate pass.

## Change and source behavior

Both current manual recovery examples in `README.md` and `README.zh.md` now include `--drop-reasoning-model k3` alongside the existing `kimi-k3` and `mimo-v2.6-pro` flags, in dry-run and apply commands. Both explanations specify exact matching against the logical model recorded in `turn_context`, independently of the endpoint's upstream wire model and profile alias. Legacy flags and historical examples remain present.

The existing `repair_lines` implementation tracks `payload.model` from each `turn_context` and drops a reasoning record when that model belongs to the supplied exact-match set. It already handles `k3`; no repair code or test-framework change is needed.

## Actual synthetic verification

Executed from `/Users/leo/workspace/code-is-cheap`:

```bash
python3 /private/tmp/pr55-reasoning-doc-fix-iwgx9znj/verify.py
```

Exit 0. The one-off temporary probe creates independent synthetic JSONL only, extracts both README command pairs and checks that they are identical, substitutes its own rollout path, and invokes the actual repository CLI with these exact commands, in this order:

```bash
python3 scripts/repair-codex-reasoning-history.py /private/tmp/pr55-reasoning-doc-fix-iwgx9znj/rollout-synthetic.jsonl --drop-reasoning-model k3 --drop-reasoning-model kimi-k3 --drop-reasoning-model mimo-v2.6-pro
python3 scripts/repair-codex-reasoning-history.py /private/tmp/pr55-reasoning-doc-fix-iwgx9znj/rollout-synthetic.jsonl --drop-reasoning-model k3 --drop-reasoning-model kimi-k3 --drop-reasoning-model mimo-v2.6-pro --apply
python3 scripts/repair-codex-reasoning-history.py /private/tmp/pr55-reasoning-doc-fix-iwgx9znj/rollout-synthetic.jsonl --drop-reasoning-model k3 --drop-reasoning-model kimi-k3 --drop-reasoning-model mimo-v2.6-pro
python3 scripts/repair-codex-reasoning-history.py /private/tmp/pr55-reasoning-doc-fix-iwgx9znj/rollout-synthetic.jsonl --drop-reasoning-model k3 --drop-reasoning-model kimi-k3 --drop-reasoning-model mimo-v2.6-pro --apply
```

| Run | Exit | Affected / per-model counts | Observed result |
| --- | --- | --- | --- |
| Documented dry-run | 0 | 3; k3=1, kimi-k3=1, mimo-v2.6-pro=1 | Original bytes and 0644 mode unchanged; no backup created; stderr empty. |
| Documented apply | 0 | 3; k3=1, kimi-k3=1, mimo-v2.6-pro=1 | 20 records become 17; one private byte-exact backup; rollout and backup modes 0600; stderr empty. |
| Repeat dry-run | 0 | 0 for every selected model | Three expected zero-match warnings; no further change. |
| Repeat apply | 0 | 0 for every selected model | Three expected zero-match warnings; bytes unchanged and no additional backup. |

The fixture has four turns: `k3`, legacy `kimi-k3`, `mimo-v2.6-pro`, and `unrelated-synthetic-model`. Each has a context, reasoning item, message, function call, and tool output. The selected reasoning items contain synthetic encrypted-content/summary fields; k3 also has nonempty `reasoning_text`. All 17 retained records equal their original lines byte for byte, including all five unrelated-model records and every selected model's context/messages/tool history. Backup bytes equal the complete pre-apply input, verified directly as well as by SHA-256.

`git diff --check` exited 0 with no output. `git diff -- README.md README.zh.md` confirmed only the requested command additions and matching explanation changes. A local SHA-256 scope check compared all 385 repository files present at task start: only the two READMEs changed; the other 383 stayed byte-identical. The sole new file at that check was the synthetic evidence below; this fix artifact is the additional authorized write. Pre-existing state/decision/review artifacts remain untouched. HEAD and branch were also verified unchanged.

## Evidence and hashes

Durable [pr-fix-synthetic.json](evidence/pr-fix-synthetic.json) contains exact argv/cwd, stdout/stderr/return codes for all four CLI invocations, Python version, byte/mode assertions, original and repaired synthetic JSONL, timestamps and hashes. Its SHA-256 is `73eaae60150ef997c152f0a30c368b69c826e7d835545f11892794e0f1d726c2`.

Temporary evidence paths (synthetic only; may be removed by later temp cleanup):

- Probe: `/private/tmp/pr55-reasoning-doc-fix-iwgx9znj/verify.py`; SHA-256 `d284fcbdfcd12893a7ccb314d38d3cf25d07739f6b40fabd948159f591994d15`.
- Initial repository byte manifest: `/private/tmp/pr55-reasoning-doc-fix-iwgx9znj/source-baseline.json`.
- Initial dirty status: `/private/tmp/pr55-reasoning-doc-fix-iwgx9znj/initial-status.txt`.
- Scope-check result: `/private/tmp/pr55-reasoning-doc-fix-iwgx9znj/scope-check-before-artifact.json`.
- Synthetic input copy: `/private/tmp/pr55-reasoning-doc-fix-iwgx9znj/synthetic-before.jsonl`.
- Repaired synthetic rollout: `/private/tmp/pr55-reasoning-doc-fix-iwgx9znj/rollout-synthetic.jsonl`.
- Actual CLI backup: `/private/tmp/pr55-reasoning-doc-fix-iwgx9znj/rollout-synthetic.jsonl.backup-20261012-170838-1791796118005735000`.
- Duplicate probe report: `/private/tmp/pr55-reasoning-doc-fix-iwgx9znj/probe-results.json`.

| Synthetic bytes | SHA-256 |
| --- | --- |
| Input and actual backup (identical) | `2c6f850bfe8cdd5aeb17602559cc074073f2818d8fb05c16147868c709577f8b` |
| Repaired rollout | `d4d31bbd68a8f3da3e59e023aeb64a0d38599588590582fef4fe758e15a15f15` |

Read source SHA-256 values, unchanged before/after:

| Source | SHA-256 |
| --- | --- |
| `AGENTS.md` | `b474e46fc40db1cf7bbd61e6afecaf0380ca25bfcec1836e6eeacaa068fb6205` |
| `docs/gateflow/official-provider-catalogs/goal.md` | `21d238ba1f9e53332d6e81726bdadcaac1cdb9c11dc7dbe527b0dc6edca8e687` |
| `docs/gateflow/official-provider-catalogs/accepted-plan.md` | `b0983ed478c168ded84feebc8991f205eadc0c8cc4f886d826451ba11c5a9540` |
| `docs/gateflow/official-provider-catalogs/plan.md` | `dd0cd1c37fbe382732fbd152898b4721a9b40ea951d57a8ff9262448e8df327d` |
| `docs/gateflow/official-provider-catalogs/pr-review-decision.md` | `3684f3cf897aecacd0812daa74b40fee0fe5dd4e3a35d95a406c2a7504998e34` |
| `scripts/repair-codex-reasoning-history.py` | `4719f28cb11ef7e0630bc50b7ddd70a405ee9db2736e2e00118b4193d5627c08` |

| Changed documentation | Before SHA-256 | After SHA-256 |
| --- | --- | --- |
| `README.md` | `1dd24bea3f7bbf38c7c03e735b69a23a4ff8a8dd5f4a01c4187bdc2ca10610a5` | `56f2dfc23d77b92140bf3c7261ddca0d03cbbf9b0748f5aaa014125b1748ae63` |
| `README.zh.md` | `2c7f064581fa5bbc62ed4f6e9b20b13675f435b25c0ae5c3b0e635db06b5ca27` | `1cf6d71b60e641100d2017b114bcd2f814fe58b006c25a4d5c537f2e79f3077e` |

## Remaining limits and controller handoff

This verifies documented flag selection, counts, byte preservation, backup privacy and idempotence on synthetic data. The unrelated reasoning item uses `content=null`, which the existing default normalization preserves; unselected items with nonempty `reasoning_text` can still have that content normalized by the tool. No claim is made that arbitrary unselected reasoning content is immune to that existing behavior.

No original user sessions, private authentication, business artifacts, real provider/Kimi API requests, native/kernel/provider replay, deployment or services were accessed or exercised. No delegation, commit, push, merge, source-snapshot/catalog/shim/endpoint/metadata/runner/sandbox/alias/compatibility/migration change, or state/review-report edit was performed. This narrow documentation correction does not require repeating the broader runtime/provider tests. Real cross-provider resume success remains outside this synthetic check. Root owns publishing the fixed head and running both exact-OID PR re-reviews before closing the review loop.
