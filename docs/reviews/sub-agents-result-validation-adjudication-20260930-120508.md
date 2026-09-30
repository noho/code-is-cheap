# Sub-agents result validation adjudication

- Branch: `codex/sub-agents-result-validation`
- Final source: `skills/sub-agents/SKILL.md`
- Final unstaged diff SHA-256: `612bfbd36cb7f2cf7c04d80c60228def7cba55441e0698802cf13ee44e126204`
- Scope: amend the external runner skill's dispatch lifecycle, failed-tool impact, evidence review, retry, and reporting instructions. No runner or installed skill was changed.

## Review inputs and acceptance boundary

- Kimi initial review: `docs/reviews/sub-agents-result-validation-kimi-20260930.md`; runner exit 0, Claude JSON success, matching canary, one exact known `unrecognized_model` stderr warning. Kimi re-review: `docs/reviews/code-review-20260930-115748.md`; same terminal/canary outcome, covering the `427c3c15...` diff and five Agent-facing scenarios.
- MiMo initial review: `docs/reviews/sub-agents-result-validation-mimo-20260930.md`; runner exit 0, `turn.completed`, matching canary, but five failed command/tool events. MiMo re-review: `docs/reviews/code-review-20260930-115252.md`; runner exit 0, `turn.completed`, matching canary in the artifact, but four failed commands and additional router/tool stderr errors. Under the **currently installed** skill's any-failed-event rule, neither MiMo run is a formally accepted review. Their findings were retained as diagnostics and checked against the source, runner and preflight paths before adoption. This PR proposes changing that rule; it does not retroactively validate those runs.
- The initial review tasks requested fixed artifact names, which differ from `$deepreview`'s timestamp filename convention. Both re-reviews used system-generated `code-review-YYYYMMDD-HHMMSS.md` names. All four reports are retained for audit.
- An additional read-only Agent-facing check walked the current instructions against sandbox handles, `rg` no match, frozen-diff mismatch, Node kernel reset, and Claude summary-only output. Its final finding about setup failure without a process terminal was fixed after the external re-reviews.

## Adjudication

| Finding or question | Decision and final behavior |
| --- | --- |
| Any failed tool event voids an otherwise completed run | Accepted. All Codex error/failed items and nonzero command exits are inspected for purpose, recovery and impact. A command failure is not an outer runner failure. Unrecovered critical evidence blocks affected conclusions. |
| Completion status must work in a sandbox | Accepted. Claude uses the managed background completion; Codex uses `exec_command` / `write_stdin` status. Output inactivity and process-list commands do not prove exit. In-flight updates are separate from terminal adjudication. A preflight failure may be reported without a spawned process. |
| Canary or one successful tool call proves the review | Rejected. Canary proves its own read. `tool_evidence`, `tool_trace` and `required_evidence` now distinguish observed execution, trace visibility and independently checked task evidence. Claude JSON's intermediate events are unavailable by default; a summary-only or partial trace needs independent verification of every required item before acceptance. |
| Frozen diff mismatch, test failure and kernel reset | Accepted as distinct cases. Input identity must be recovered before accepting review of that snapshot. A failing test may be an actionable finding. A lost kernel call is classified by whether necessary evidence was recovered. |
| Status schema and retry ambiguity | Accepted. The completion block separates agent status from result status, records evidence gaps, disallows contradictory acceptance, and distinguishes setup, provider and task retry causes. Measurement failures remain in their original batch. Project-specific fallback restrictions outrank the skill's default provider switch. |
| Mandatory timeout for every unattended dispatch | Not adopted. The existing user instruction forbids ending or re-dispatching solely because an agent runs long. A task may specify a timeout in advance; without one, output silence alone is not proof of terminal failure or permission to kill. A documented blockage can be reported while its process remains in flight. |

## Verification and residual risk

- `quick_validate.py skills/sub-agents`: valid; `git diff --check`: passed; final diff SHA above. No runtime or preflight script changed, so no behavioral test was added for a documentation-only protocol edit.
- The final post-review wording change was checked against the same five Agent-facing scenarios by the controller: setup failure now has an explicit no-process exception; a partial or summary-only trace can support acceptance only after required evidence is independently verified.
- The currently installed `~/.codex/skills/sub-agents/SKILL.md` remains on its prior rule until a separate sync. This PR changes repository source only.
