# GPT-6 effort provider plan

Branch: `feat/gpt-6-effort-profiles`. Base: `main` at `bb3454de0d461d97aab1c3bfc71dd87d18b49d61`.

## Confirmed target

The user corrected the tentative `gpt-6-M` / `gpt-6-sol-M` names to `gpt-6-sol-max`, then requested the same three-provider structure for Astra.

| Provider | Upstream model | Reasoning effort |
|---|---|---|
| gpt-6-astra | gpt-6-astra | high |
| gpt-6-astra-x | gpt-6-astra | xhigh |
| gpt-6-astra-max | gpt-6-astra | max |
| gpt-6-sol | gpt-6.1-sol | high |
| gpt-6-sol-x | gpt-6.1-sol | xhigh |
| gpt-6-sol-max | gpt-6.1-sol | max |

Rename the canonical `gpt-6-astra-xhigh` provider to `gpt-6-astra-x`. Preserve Luna, existing short aliases, and business's derivation from the base Sol card (therefore business also becomes high).

## Implementation and verification

1. Update model cards and explicit lists/dispatch in CLI/App launchers, runner and sandbox subscription handling. Preflight and sync discover cards dynamically.
2. Update current English/Chinese READMEs and the sub-agents skill provider table. Preserve historical artifacts.
3. Extend existing boundary tests for selected model/effort across all six providers, CLI/resume, both App entry points, private home composition, preflight missing cards, sandbox authentication/domains, repeated isolated sync/install, and business defaults.
4. Run the affected suites, syntax/skill validation and diff checks. No live model requests or live deployment are required for this configuration task.
5. Dispatch independent full Deepreviews through Claude `mimo-flash` and `ds-flash` in parallel; adjudicate direct evidence and dispatch any accepted fixes through Codex `gpt-6-sol`. Commit, push and create a new draft PR for manual merge.

## Controller decisions

The read-only plan was dispatched via Codex `gpt-6-sol`, native/outer exit 0. Its final answer and transcript are retained at `/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/agent-run.ZvGSn0to/output.jsonl`. The user clarified the final names while that investigation was running; the implementation handoff explicitly supersedes tentative names and adds Astra max.

Adopt the plan's existing-boundary approach. Do not introduce deletion of installed user files: the existing sync policy retains extra model cards, so an old directly selected native card may remain. The old name is removed from managed canonical runner/launcher lists. Document retained old cards/App history and the need for a fresh shell or explicit obsolete-function removal. This avoids expanding a provider change into installed-state migration; it does not claim old on-disk cards are removed.

Live sync is deferred to separate user authorization. Closeout must record `./scripts/sync-skills.sh`, `./scripts/sync-agent-tools.sh`, `./scripts/sync-codex-agent.sh`, interactive shell reload and Agent session restart guidance.

## Authorized review runtime fallback

The initial independent Claude `ds-flash` invocation exited 1 with upstream HTTP 403: package disabled or invocation permission missing; it performed no review. Its full runner result is retained in `ds-flash-attempt.json`.

The user explicitly requested the `ds-flash` Codex runtime instead and asked to add that backup route to `AGENTS.md`. A separate Codex `gpt-6-sol` implementation task changed only the root instructions: default reviewers remain Claude `mimo-flash` and Claude `ds-flash`; after recording Claude DS unavailability, the controller may use Codex `ds-flash` as its backup while retaining independence. Both native/outer exits were 0 and diff validation passed. No executable behavior changed in this supplemental task. The Codex DS full review includes this instruction change; the Mimo review must also cover it or receive a focused affected-scope follow-up.
