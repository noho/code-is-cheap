# Native Codex provider handoff plan

Branch: `fix/codex-native-provider-handoff`. Inspected HEAD: `e58598e3f7d3585c4f0f9ccca2fff486c3ea1e5f`.
This is a delegated plan-only artifact. The controller owns implementation, independent reviews, fixes, commits, push and PR; no recursive delegation or live deployment is required for planning. The user has already authorized this scope; there is no blocking decision or new confirmation gate.

## Intent and evidence

Let Codex own resume, provider compatibility, and continuation in a new conversation. Remove launcher-triggered reasoning-history modification while preserving profile selection and native arguments.

- `scripts/agent-tools.zsh:406–453` currently rewrites leading `resume <id>` into a launcher repair request, restricts the tail to one prompt, locates the rollout through `repair-codex-reasoning-history.py --target-config ... --apply`, and only then invokes Codex. That can delete reasoning even for a same-provider model switch and can prevent Codex from receiving valid native arguments, session names, or selection options.
- `tests/test_repair_codex_reasoning_history.py:test_launcher_resume_repairs_then_calls_codex` explicitly requires rollout mutation, a backup, and launcher rejection of non-UUID/missing IDs. Those are old repair behavior assertions, not native resume requirements. `tests/test_install_endpoints.py:test_subscription_interactive_title_resume_and_missing_card` also installs the repair helper unnecessarily for launcher coverage.
- Controller-supplied official evidence: [Start or resume a thread](https://learn.chatgpt.com/docs/app-server#start-or-resume-a-thread) specifies `-32600` / `modelProviderMismatch` when the saved provider differs, with switching back or starting a new thread as alternatives. Same-provider model changes have their own native warning/instruction behavior. These app-server facts do not establish how the TUI implements its handoff.
- User-observed TUI evidence: the original thread becomes read-only with “Continue in a new chat. This chat uses OpenAI, but Codex now uses DeepSeek, so this chat is read-only.” Choosing `c` starts a new conversation with `Read “<title>” and let’s continue where we left off.\n\nSaved conversation: <absolute rollout path>`. Follow that native flow; do not recreate it or assert it is identical to app-server `thread/fork`.

## Smallest behavior change and ownership

1. Delete the automatic repair block, including repair state, UUID/path lookup dependency, target-config selection, fixed argument counts and repair errors. Leave literal native `resume` arguments alone after the launcher's existing wrapper-option handling.
2. Retain compatibility aliases only at the existing leading-argument position, after wrapper options have been consumed:

   | Input to launcher | Native argument sequence before existing profile/local-model injection |
   | --- | --- |
   | `resume ...` | unchanged |
   | `--resume ...` | `resume ...` |
   | `--resume=<id> ...` | `resume <id> ...` |

   Preserve every remaining argument and its boundaries, order, spaces, Unicode, newlines and empty values. Do not scan/rewrite later prompt text or arguments after the `--` delimiter. Do not enforce launcher UUID, existence, or tail-count checks. Bare `--resume` consequently becomes the native `resume` picker; an empty `--resume=` becomes `resume ""` for Codex to interpret. This is intentional delegation of validation rather than retained repair semantics.
3. Keep existing profile injection (`resume -p <profile> ...`), shared/private CODEX_HOME selection, local model override, credential scrubbing, wrapper title/full-access handling and exit/status propagation. Preserve `gpt_codex` delegation. `exec resume` used by `codex-agent-run` remains native and unchanged; do not reinterpret runner `--resume` as the interactive compatibility alias.
4. Same-provider resume and model switching remain Codex-owned. On a cross-provider mismatch, allow native read-only UI and the offered continuation action to run. No launcher-side detection, automatic selection of `c`, prompt generation, metadata spoofing, custom fork engine, rollout mutation or upstream patching.
5. Retain the standalone repair utility and its installation as explicitly manual legacy recovery. Its tested dry-run, backups, atomic replacement, exact-model matching and fail-closed checks still have independent recovery value; provider mismatch does not show that those transformations are intrinsically broken. There is no evidence-based need to remove it in this change. Clarify its module/help description and both READMEs: it is never called by launchers, deliberately edits rollout reasoning when manually applied, and cannot bypass the new provider boundary. Retain its CLI flags and all independent repair/install unit tests. Do not add a new launcher opt-in repair mode.

## Affected files and documentation

| File | Planned change |
| --- | --- |
| `scripts/agent-tools.zsh` | Remove automatic repair; normalize only the two compatibility aliases. |
| `tests/test_repair_codex_reasoning_history.py` | Replace the automatic-mutation launcher test with native forwarding/no-mutation coverage; retain manual repair and isolated sync tests. Update module description if needed. |
| `tests/test_install_endpoints.py` | Remove launcher fixture dependence on the repair executable; preserve profile/alias/runner/title/home assertions and extend argument coverage where appropriate. |
| `scripts/repair-codex-reasoning-history.py` | Documentation/help clarification only; no repair algorithm or CLI contract change. |
| `README.md`, `README.zh.md` | Matching native resume/handoff guidance and manual legacy recovery boundaries. |

Active-document search found the old behavior in both READMEs only. Update all related prose, not just the repair subsection: installation descriptions and Python requirement (`README.md:295–300`, `README.zh.md:271–276`), app/shared-home cross-model examples (`346`, `325–326`), profile/resume guidance and alias text (`463–490`, `425–443`), and legacy repair sections (`596–620`, `544–570`). Keep valid examples while distinguishing same-provider model switching from cross-provider continuation. Describe the observed `c` flow as current native behavior, subject to the installed Codex version; do not promise identical UI in every version or full transfer of internal state/tool execution. Link the official source and retain the historical payload issue only as legacy context. Remove advice implying that manually stripping reasoning enables current cross-provider resume.

No changes are needed to `scripts/sync-agent-tools.sh`, backup/restore inventories, model/provider registries, catalogs, profiles, runner contracts or skills. Continue installing the manual helper. Preserve historical review/work-unit/gateflow artifacts rather than rewriting them. Leave these pre-existing untracked files untouched and uncommitted: `docs/reviews/runner-handle-loss-20261023-evidence.json`, `docs/reviews/runner-handle-loss-20261023-investigation.md`, and `docs/reviews/runner-handle-loss-20261023-notification.json`.

## Validation and acceptance

Use isolated temporary HOME/CODEX_HOME and a fake native `codex`; never resume or edit real `~/.codex` data. These are meaningful boundary regressions, not a replacement implementation of the upstream provider state machine.

- Cover literal `resume`, `resume <id> [prompt]`, `--resume <id> ...`, `--resume=<id> ...`, bare picker, `--help`, `--last`, flags before/after the selected ID, and a tail longer than the old limits. Use session-name/non-UUID and nonexistent-session inputs to prove the launcher reaches native Codex without inspecting local rollouts.
- Assert exact captured argv after existing profile injection, including `--` and a prompt containing spaces/newlines/Unicode; preserve empty arguments without adding a spurious empty argument to bare resume. Test alias-looking prompt text remains literal. For invalid/empty forms, assert forwarding and the fake native exit code rather than reinstating repair validation.
- For literal and alias resumes, stage a synthetic mixed-model/provider rollout with reasoning and session metadata; assert byte-for-byte preservation and no backup/temp/session artifacts. Use a repair-helper trap that fails/records any invocation, or an explicitly unavailable helper, to prove resume does not depend on or execute repair. Include both managed subscription and third-party profile selection, `gpt_codex`, and the separate business home; retain existing local override/runner tests.
- Have the fake native process emit a provider-mismatch-shaped message and a nonzero status; assert output/status propagate without interception or fallback. This verifies launcher transparency only; it does not claim to test Codex's real read-only UI or new-chat implementation.
- Keep all manual repair tests, including dry-run, affected-item counts, selective removal, backup/permissions, unsupported/malformed input, duplicate lookup and concurrent-change checks. Keep the install test targeting temporary output directories.

Run from the repository checkout after implementation:

```bash
zsh -n scripts/agent-tools.zsh
python3 -m unittest discover -s tests -p 'test_repair_codex_reasoning_history.py'
python3 -m unittest discover -s tests -p 'test_install_endpoints.py'
git diff --check
```

Review the bilingual diff and search active docs again for stale automatic-repair claims (`repair and resume`, `resume repair`, `resume 修复`, `--resume` repair requirements). References to the retained manual utility should remain. Check `git status --short` for the untouched unrelated files. Broaden testing only for newly affected behavior or failures. No live network model request or real-session TUI test is required to establish this launcher change.

The controller dispatches implementation/fixes through Codex `gpt-6-sol`, then independent parallel Deepreviews through Claude `mimo-flash` and Claude `ds-flash` (document the permitted DS Codex-runtime fallback if needed), adjudicates findings and closes accepted fixes before commit/push/PR. This planner does not perform those steps.

## Residual risks and closeout

- Installed Codex versions may differ in provider enforcement, UI wording, shortcut and saved-conversation reading. The native behavior is upstream-owned; forwarding tests cannot prove that the new conversation can read every saved transcript or preserve all context. Do not hard-code the shortcut or generate the handoff in the launcher.
- Users who relied on automatic reasoning deletion lose that behavior by design. Manual legacy recovery remains destructive when explicitly applied and is not a solution to provider mismatch. Retaining it does not promise that legacy payload repairs make current cross-provider replay possible.
- Existing wrapper-specific `--title`/`--full-access` parsing and unsupported placement of compatibility aliases are unchanged. Do not expand this task into a general argument-parser rewrite. Profiles named in this repository are not themselves proof of the effective saved provider; Codex determines compatibility.
- No live deployment in this work. Controller closeout must record the applicable command `./scripts/sync-agent-tools.sh`, run later from the checkout containing approved changes with separate user authorization. Remind the user to run `source ~/.zshrc` or open a new shell for interactive launchers; installed runner callers already on PATH need no shell reload. Skill/profile sync scripts are unnecessary unless implementation expands into those components.
