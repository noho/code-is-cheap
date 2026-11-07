# Plan Review — MiMoLite additional_tools native descriptor location (bounded supplement)

- **Reviewed target**: `docs/gateflow/shim-subagent-all-providers/native-descriptor-location-plan.md`
- **Plan SHA-256**: `4c979cf413d610705fd5ad26d3ca86355e097a72daa3d17e21cf78f5856dbd2f`
- **Branch / HEAD**: `fix/shim-subagent-message-delivery` / `901cea16928ef2db01ce774c99652f62fb3dca68` (PR #70)
- **Review type**: independent affected PLAN review only; no implementation, native probe/inference, tests, delegation, commit/push, deployment or messages.
- **Reviewer provider/model**: `deepseek/deepseek-flash[1m]`, Claude runtime.
- **Timestamp**: 2026-11-08T00:24:58+0800
- **Scope**: only the newly evidenced MiMoLite current-HTTP `additional_tools` descriptor source/map/collision/duplicate invariants and the targeted fresh A2/B2 acceptance. Not a re-review of the accepted SSE/guardian/Kimi contracts in `native-namespace-plan.md`.

## 1. Evidence checked

- A1 wire has 18 requests and B1 has 5 (23 total). Every request has exactly one selected `collaboration` descriptor location at `['input', 0, 'tools', 2]`; no selected `['tools', i]` location is present. The probe records that input path only for an immediate item with `type == "additional_tools"` (`native-probe.py:103-110`). This confirms the cited actual wire location and the absent selected top-level descriptor.
- The selected wrapper advertises six function children in all 23 requests: `followup_task`, `interrupt_agent`, `list_agents`, `send_message`, `spawn_agent`, `wait_agent`.
- All 23 `native_request_stage` records show `flatten=false`, `map={}`, `before_tools=null`, `after_tools=null`, and identical before/after hashes. The implementation report records zero MiMoFlash restorations. The current top-level-only helper is therefore not active on the evidenced path.
- The same `additional_tools` items contain unselected `functions` namespaces whose children are `exec`, `wait`, `request_user_input`, `request_user_input_async`, with repeated `functions` group labels. None equals a selected bare name, so the plan's mapped-name collision rule does not reject the actual requests; unrelated duplicate labels/children remain passthrough.
- The current helper returns an empty map before inspecting `additional_tools` when top-level `tools` is absent/non-array (`codex-auto-review-shim:290-296`). Plan §4 explicitly removes that early return only on the response-only path.

## 2. Contract check

| Invariant | Plan position | Verdict |
| --- | --- | --- |
| Source: current request top-level `tools[]` plus immediate `input[i].type=="additional_tools".tools[]` only; exact allowlist; no index hardcoding/recursion/text/schema mining; no early return on absent top-level `tools` | §§2-4 | Adequate; matches the 23/23 observed shape and the current helper defect |
| Map: immutable per-request bare-name → namespace map; no cross-request state; response-only original request bytes/lexical identity; no reserialize merely to collect | §5 | Adequate; current flatten=false path already returns original bytes |
| Collision: mapped names only vs other declared callables in both known sources; every selected wrapper occurrence excluded from the second scan; group labels are not callable names; unrelated duplicates allowed; unknown explicit mapped-name collision fails | §6 | Adequate; actual `functions` children do not collide with the six selected names |
| Duplicates: repeated selected native callable declarations rejected, including identical repeats in one/across containers; conflicting/nonidentical duplicates fail 400 with zero upstream calls; no first/last-wins; disjoint unambiguous declarations may merge; a newly required repeat needs a bounded decision | §7 | Adequate and conservative for the 23 observed one-wrapper requests; no repeated selected declaration occurs |
| Fresh A2/B2: nonempty maps on actual parent/child requests advertising native tools; unchanged native-stage bytes; active map path with identity/absent encoding; response namespace/field preservation; v2 FINAL-receipt ordering; old A1/B1 preserved; zero restoration count not inferred without a missing/null namespace | §§33-34 | Adequate, targeted acceptance; activation remains pending fresh evidence |
| Boundaries: no aliases/global state/catalog/policy/new flags/MCP flatten/argument repair; no sync/restart/callback before authorization | §§20, 38 | Adequate |

## 3. Findings

**0 material findings.** No scope, source-location, map, collision, duplicate or acceptance blocker was found in the supplement within the requested scope.

## 4. Open questions (non-blocking)

1. **Kimi reuse wording is stale, not a MiMo blocker.** Plan §35 says to run a fresh Kimi A2. The controller `control.md` records Kimi A/2 strict audit pass (and Kimi B/1/B/2 strict passes) on the final helper hash; the user states A2 already PASS. This review does not re-prove Kimi. Controller should record the existing A/2/B1 strict evidence plus bounded source/path equivalence for the final helper rather than require an unnecessary new Kimi attempt. Destination: controller adjudication.
2. **Auditor "allowed selected paths" scope.** Plan §27 says the auditor rejects empty/mismatched maps when actual native children are present. For the Kimi `flatten=true` path, `additional_tools` native children are intentionally not mapped, so the auditor's allowed-path derivation must be scoped by route/flatten mode to avoid a false rejection. Destination: observer/auditor tests and code review; no current-evidence blocker.

## 5. Residual risks

- Fresh MiMoFlash A2/B2 have not yet been executed; actual activation remains unproven until they show nonempty maps and the active response path. The plan requires exactly that.
- The duplicate rule may need a bounded contract revision if a required repeated selected declaration is later observed; the plan already reserves that decision.
- The observer/auditor extension must record containing item type and independently derive the map; otherwise fresh evidence is not location-proof. Destination: implementation/code review.
- Old MiMoFlash A1/B1 empty-map passes remain regression evidence, not activation proof, as the plan states.
- No live sync/restart or pre-authorization callback is implied.

## 6. Final conclusion

**pass-with-risks** — 0 material findings. The supplement is sufficient to guide the bounded response-only mapping implementation and targeted fresh A2/B2; remaining risks are the explicitly planned fresh-evidence/auditor gates and the non-blocking Kimi reuse wording.

Artifact: `docs/reviews/plan-review-20261108-002458-ds-native-location.md`
