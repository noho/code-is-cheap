# Plan fix: official provider catalogs

Status: accepted findings incorporated into plan.md; independent re-review pending.
Branch/base: `feat/official-provider-catalogs` / `17ef441`.
Scope: plan-only fix under [plan-review-decision.md](plan-review-decision.md), with [goal.md](goal.md) and [state.md](state.md) read as the approved scope/gate context. The two existing reviews were read only as findings for this fix: [134721](../../reviews/plan-review-20261012-134721.md) and [133906](../../reviews/plan-review-20261012-133906.md). This artifact does not issue a new independent review or close the controller's review gate.

Only [plan.md](plan.md) and this artifact are edited in the repository. Existing branch reused; no product/test/state/review artifact changes, delegation, commit, push, PR, live synchronization, real provider request, merge or finance task. A temporary loopback-only native Qwen probe supplies the requested event evidence below.

## Accepted decisions applied

| Adjudicated item | Concrete plan resolution | Required implementation evidence |
| --- | --- | --- |
| MiMo 1: two-hop fixture URL/auth wiring | Temporary provider registry points each provider ID to its retained OS-assigned shim listener and original request prefix. Owned mode-0600 fixture `endpoints.json` supplies all eight selected Codex endpoint URLs, independent wire slugs and synthetic keys, plus synthetic local sync settings. Effective connections and both listener identities are asserted; fixture-only upstream opener rejects any nonfixture destination. | Native ingress logical slug/auth versus upstream overridden wire slug/Bearer key/path; no factory/user endpoint or credential fallback, including Kimi and guardian forwarding. |
| MiMo 2: partial-install pair skew, narrowed by controller | Stage/native-validate all catalogs first; back up replaced card/catalog destinations and registry config bytes/modes/absence. Move registry update after validation and before cards; retain registry ownership checks. Existing EXIT cleanup restores attempted/replaced destinations on ordinary conversion-block copy/replace/verification failure. Verify installed bytes/pair relationships before disarming recovery. | Inject first-catalog, first-card, later-pair, registry and final-verification failures; recover original bytes/modes/absence and unrelated config. Restore failure reports nonzero and retains backups. No atomic-reader, SIGKILL or whole-deployment guarantee. |
| MiMo 3: pre-shim observation missing | Test-only Handler `do_POST` wrapper records headers/raw/decoded ingress before transforms, replays identical bytes to the original `_handle`, and restores its input stream. Separate upstream capture records transformed data; retries are associated with their original ingress. | Compare actual native model/auth/format/ID changes and preserved instructions/max/Lite items/header at both points. Production logging stays unchanged. |
| MiMo 4: route-wide JSON downgrade | Keep `json_fmt_fix` on all MiMo routes, applying `json_schema` to `json_object` for ordinary sessions and guardian requests. No narrowing or protocol change. | Targeted ordinary-session ingress/upstream assertion plus valid decoded guardian verdict; document the structured-output limitation in both READMEs. |
| DS 1: missing Chinese README | Add `README.zh.md` to allowed implementation files and paired documentation acceptance. | Both READMEs agree on source/generation facts, Kimi names, GLM donor, Qwen values, max, host/Lite/format prerequisites and recovery limits. |
| DS 2: native host default / false negative | Record native 0.162.1 `code_mode_host stable true`, proved in the reviewed evidence and independently by the controller. Omission is a positive-default case. | Positive required Code Mode executes with `code_mode=false` and host key omitted; negative explicitly sets `features.code_mode_host=false`, confirms false, and fails visibly without direct fallback or valid artifact. |
| Controller: redundant host feature machinery | Remove explicit host-true MiMo-card features, app-composer nested overlay and isolated selected-entry/host-enabling machinery from S1 and allowed changes. Retain current composer, sandbox and MiMo cards. Official `code_mode_only` overrides the sandbox's false code_mode feature. | Default-host execution and one official MiMo kernel case prove the current paths. Missing host/unsupported behavior is reported. Removed edits may return only for an actual concrete execution defect adjudicated by the controller; no drift insurance. |
| Controller: CANARY format | Final fixture report is a standalone `CANARY=<token>` line. Expected-token file is not sent to the model; tool must read the input and write a new artifact. | Actual native read/tool output, result-file bytes, final/last-message agreement and unchanged collector status/evidence fields; final text alone is insufficient. |

These are plan resolutions, not claims that the future implementation or its tests have passed.

## Preserved scope and focused validation

All eight profile mappings and complete source metadata remain in plan.md. Official raw snapshots remain the inputs, including unselected entries, instruction objects, effort lists, unknown fields and omission/null distinctions. All eight defaults stay max; MiMo max remains user-confirmed. Kimi card and shim logical source are exactly `k3`; endpoint-owned wire model remains independent. GLM Flash clones official `glm-5.3` metadata for existing `glm-5.3-flash`, changing only its labelled identity fields; no Turbo selection.

Native parsing remains authoritative for nested schema and required native fields. Manual checks are limited to source integrity, mappings, card/path/max invariants, selected tool-mode semantics and budgets. Do not duplicate native enum/message/effort/truncation validation. Fixed test/provenance hashes derive from the approved inventory without a runtime dependency on Gateflow docs or Downloads. Reuse the existing parser/request controls rather than repeating source-wide research.

Every assembled profile receives native staged parsing and mapping/source-equality coverage. Full read/write/collection cases are limited to distinct semantics: DeepSeek official instructions/direct tools, Kimi native logical/wire separation, MiMo Code Mode/Lite/default host, and Qwen default shell/missing maximum/context. Reuse the Qwen persisted task for context; omit duplicate MiMo positive feature runs and equivalent profile/error matrices. Guardian coverage retains allow/deny for direct and Lite paths plus a shared bounded HTTP-error case; one official MiMo outer-boundary case exercises actual host descendants under existing enforcement. Validation-aware stubs cover repeated injected install failures, while real native assembled parsing and a representative native rejection remain separately required.

Already authorized small provider acceptance probes belong to implementation evidence; they are not deferred behind a new permission gate. Use only tiny synthetic prompts and at most one bounded probe per covered effective connection, without automatic retries. Kimi is limited to at most one small debugging/status probe, with no development/review dispatch, tool/guardian use or repeated API calls. No real probe occurred in this fix. Status-only acceptance, mock HTTP/SSE outcomes, native execution and kernel enforcement must be labelled separately.

## Actual temporary Qwen context evidence

Existing evidence contains original-catalog parsing and intentional HTTP-400 request controls, but no resolved context event. This fix therefore ran one persisted native `codex exec` against a dedicated OS-assigned `127.0.0.1` synthetic SSE server. It requested a status only, used no tools and made one captured POST; external provider requests were zero. The server supplied synthetic completion and usage, not a vendor response.

- Fixture: `/private/tmp/official-qwen-context-fix-p2nv1c76`.
- Manifest: `/private/tmp/official-qwen-context-fix-p2nv1c76/manifest.json`; stdout/stderr retained in `stdout.jsonl` and `stderr.log` there.
- Native CLI: installed `codex-cli 0.162.1`.
- Original Qwen source copied to the fixture; actual SHA-256 `4bc94831cb66e43aaf4c375543f92883bfa1d3116a4065c5796c5de29e8a019c`, matching the approved inventory. No source or product file was changed.
- Scrubbed environment: HOME and CODEX_HOME below fixture `home`, CODEX_SQLITE_HOME at fixture `sqlite`, TMPDIR at fixture root, fixed binary PATH and loopback NO_PROXY. No inherited account/auth/provider/proxy settings.
- Fixture config selects `qwen3.8-max`, max, context 983616, compact 737712 and the original Qwen catalog, with `features.code_mode=false`, approvals never, workspace-write sandbox, disabled search, and one synthetic Responses provider with no auth and zero request/stream retries.

Exact argv (persisted because `--ephemeral` is absent):

```text
/opt/homebrew/bin/codex exec --json --skip-git-repo-check -C /private/tmp/official-qwen-context-fix-p2nv1c76/work "Return a diagnostic status only. Do not use tools."
```

Exit code was 0. The single captured `/v1/responses` request had `model="qwen3.8-max"` and `reasoning={"effort":"max","summary":"auto"}`. Stdout emitted `thread.started`, `turn.started`, `item.completed`, `turn.completed`; it did not expose resolved context. Stderr included a temporary-home PATH-alias warning and the stdin notice, so this probe is not a clean collector/tool smoke.

Actual newly created rollout:
`/private/tmp/official-qwen-context-fix-p2nv1c76/home/.codex/sessions/2026/10/12/rollout-2026-10-12T13-58-32-01a12eb0-f8a4-7c60-bf08-a31d6e4962c8.jsonl`.

Observed fields, excerpted from that file (other fields omitted):

```json
{
  "line": 6,
  "timestamp": "2026-10-12T05:58:32.375Z",
  "type": "turn_context",
  "payload": {"model": "qwen3.8-max", "effort": "max"}
}
```

```json
{
  "line": 12,
  "timestamp": "2026-10-12T05:58:32.381Z",
  "type": "event_msg",
  "payload": {
    "type": "token_count",
    "info": {"model_context_window": 934435}
  }
}
```

934435 is read from the native event, not computed for this artifact. This resolves the event-shape/value question for installed 0.162.1 and the original catalog plus explicit override. It does not prove the future assembled catalog/card installation, runner/shim, tools, guardian, kernel boundary or true Qwen max acceptance. Implementation must collect its own matching-session rollout through fixture-local runner `--persist`; the durable excerpts here remain usable even if temporary files are later cleaned.

Document checks passed: eight mapping rows retained, local Markdown links resolve, fences/whitespace are valid, CANARY uses the required form, and the quoted context value was re-read from the actual rollout line. `git diff --exit-code HEAD` confirmed no tracked product changes. Product tests, full native/tool/guardian/kernel smokes and real API probes were not run in this plan-only fix.

## Residual limits and blockers

No accepted plan-fix item remains unresolved. Independent dual re-review is pending with the controller; this fix does not declare a review pass or implementation acceptance.

- Required implementation evidence remains: ordinary pair/registry recovery, actual default-host/nested-tool execution, captured two-hop transformations, collector output, direct/Lite guardian behavior and kernel denial. Missing prerequisites or concrete failures block the affected acceptance and must be reported, never converted to a skip/pass or weakened boundary.
- Actual provider acceptance is unmeasured by this fix. Already authorized small probes will report success/rejection/unverified per effective connection. A rejection does not authorize effort/model/source mutation. Kimi quota limits remain binding.
- MiMo route-wide structured-output downgrade remains an explicit existing limit; GLM Flash remains an authorized derived source, not an independent official Flash catalog.
- Narrow recovery excludes atomic cross-file reader visibility, concurrent-writer coordination, SIGKILL/power loss/disk destruction and failed restoration I/O. Ancillary shim/service/business deployment remains outside its boundary; no whole-install or crash-recovery guarantee is added.
- Unprobed endpoint overrides, vendor tool/guardian behavior beyond the small acceptance calls, desktop builds and future CLI/catalog drift retain specific unverified limits; no compatibility/updater/security framework is introduced.
- Live deployment/merge, original tasks/finance, high-risk investigation and native GPT/business/local conversion remain outside this work unit.

Handoff: re-review the revised plan and this fix evidence before implementation. No authorization blocker or need to reopen the confirmed scope was identified.
