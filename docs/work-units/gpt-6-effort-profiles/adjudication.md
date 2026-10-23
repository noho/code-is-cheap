# Controller adjudication

Decision: **review pass; no accepted implementation fixes remain**.

## Version and independent evidence

Reviewed implementation: `626dd0ef1f4dd4938b0b1d77693955de76c6daa5`, including provider implementation `2b96ae803e1e6c8cd78c6ec56a6d75c73bb506a3`. Base: `bb3454de0d461d97aab1c3bfc71dd87d18b49d61`. The 19 file states in `reviewed-version.json` include the removed old card; Git represents that deletion/addition as one rename. The substantive diff SHA-256 is `59a0009a41d04bde4910b5dbfb356250f00f7631ed0f85cffa8393c26d78a56a`.

- Claude `mimo-flash`: [full Deepreview](../../reviews/code-review-20261023-112748.md), native/outer exit 0. Final conclusion: no substantive findings. It verified the final commit identities and independently reran the nine affected modules: 188 tests, 175 passed and 13 existing opt-in skips.
- Codex `ds-flash`: [full Deepreview](../../reviews/code-review-20261023-111949.md), native/outer exit 0. No substantive findings. It independently reran the same suite with the same result and checked the six effort choices against the bundled native catalog. It explicitly covered the added AGENTS.md rule.
- Claude `mimo-flash`: [AGENTS.md supplemental review](../../reviews/code-review-20261023-112229.md), native/outer exit 0. No substantive findings. This independently covers the user-added scope after the first Mimo invocation began; the final full report also included that scope.

The two full reviews overlapped in execution and did not read one another's new reports. No further code fix or affected-code review is required. Runner summaries are retained beside this artifact.

## Controller checks and dispositions

The controller inspected the final cards, explicit routing/subscription predicates, current English/Chinese documentation, and test changes. All six provider IDs map to the confirmed upstream model and effort. Existing aliases select base high; business derives its two defaults from base Sol. Dynamic preflight/install/sync discovery is exercised without new routing machinery. Old runner identity is rejected even when an old installed card remains. App history and machine-local settings are preserved. All substantive file identities were rechecked against the reviewed manifest.

There are no material findings to accept, reject or defer. The Mimo supplement's two nonblocking questions are resolved for this work unit:

- The runtime fallback reason is recorded in `plan.md`, `ds-flash-attempt.json`, and this artifact. No particular filename is needed for the instruction to be enforceable.
- If both DS runtimes are unavailable, the two-review requirement remains unmet; the controller must obtain an explicit user route change rather than silently downgrade to one review. No new general failover mechanism is needed here.

Observed runner diagnostics do not represent unresolved implementation failures. Mimo initially named a nonexistent `Bfunction` tool, and a separate shell command used an unquoted `====` separator; both observations were followed by successful direct inspection and final validation. Codex DS attempted to read a parent `AGENTS.md` that was a directory before reading the repository instruction file. Claude's model-name warning did not prevent either Mimo task from completing. These facts are preserved in the original logs and receipts.

## Routing exception and authorization

The original Claude DS review exited 1 before review with HTTP 403 (disabled package or missing invocation permission). The user explicitly selected `ds-flash` through Codex and requested the AGENTS.md backup rule. Codex `gpt-6-sol` implemented that rule in a separate task with native/outer exit 0. Default Claude routes remain unchanged; only DS Claude unavailability, with a recorded reason, permits the Codex DS backup. Implementation/fix routing and live-deployment authorization were not broadened.

## Residual risks and owners

- User: remote account entitlement and actual live model/App behavior remain for separately authorized post-merge smoke testing. The bundled catalog advertises the selected upstream IDs and efforts; this work makes no live model request.
- Maintainer: the 13 existing opt-in native Seatbelt/kernel/runtime tests were skipped; no isolation policy internals changed. The six-provider check/launch matrix passed.
- Maintainer: existing repeated membership lists still require coordinated future edits. Current lists and behavioral tests cover all six providers; there is no evidence requiring a registry redesign in this task.
- User: installed obsolete cards and App data intentionally remain, and previously loaded shell functions require a fresh shell or documented explicit removal. Current docs explain these boundaries accurately.

None blocks this confirmed configuration and review-routing scope. Live sync remains a separately authorized action.
