# Current Hy4 native runtime investigation

2026-11-05; branch `feat/hy4-codex-token-plan`; prerequisite only. The controller's reductions in `controller.md` govern this investigation.

**Direct demonstrated complete native compatibility once, but the declared batch is not a clean two-workflow qualification. Plan does not qualify with the selected Token Plan key.** No Hy product restoration, endpoint override, commit, push, service restart or sync was performed. The setup incidents below remain part of the result.

## Declared matrix and actual outcomes

The declaration is [probe-declaration.md](probe-declaration.md). Four sequential samples, 300 seconds maximum each, shared maximum 40 upstream attempts including existing retries. No compatibility calls, replacement samples, synthetic verdicts, chat-completions fallback or effort substitutions. Actual total: **32 attempts**. All ephemeral listeners were closed after investigation.

| Sample | Native exit / seconds | Upstream attempts | Stream / native tool continuation | Guardian / sentinel | Classification |
| --- | --- | --- | --- | --- | --- |
| direct-1 | Exact native exit unavailable; stopped at 146.584 s | 14 | Incremental completed session streams; native shell returned sandbox errors | Explicit escalation requested; guardian pending when stopped; no sentinel | Incomplete local setup evidence; not an endpoint failure |
| direct-2 | **0 / 91.430 s** | 6 | **Completed incremental streams, real canary read/copy/check, correlated results and final** | **Schema-valid allow, successful escalated execution and result continuation** | **Complete workflow pass** |
| plan-1 | **1 / 7.817 s** | 6 | No streamed turn or native shell execution | Not reached | Gateway permission failure, HTTP 403 / `403001` |
| plan-2 | **1 / 7.482 s** | 6 | No streamed turn or native shell execution | Not reached | Same gateway permission failure; separate retained parser setup incident |

Neither direct sample incurred a shim retry. Each Plan sample had five native duplicate-request retries after its initial request, for six identical request bodies and six HTTP 403 responses. These were existing native retries, not manual reruns. The shim's configured guardian retry loop was unchanged. No request/time budget was exceeded.

Plan returned this actual gateway error on both samples:

```json
{"type":"permission_error","code":"403001","message":"The package is disabled or you do not have invocation permission. Please check the package status in the console.","source":"gateway"}
```

This is evidence about this endpoint/key's invocation permission, not about Hy model quality or generic Responses support. No Plan guardian/schema result can be inferred from it.

## Isolation, credential selection and native configuration

Actual installed CLI: `codex-cli 0.166.0`. The harness privately copied the existing branch shim and endpoint resolver; staged factory validation allowed only `hy.codex`. The native provider used an ephemeral `127.0.0.1` listener and `/v1` request prefix. The unchanged resolver selected one complete URL/model/key snapshot per request. The observed wire model was `hy4` throughout:

- Direct: `https://tokenhub.tencentmaas.com/v1/responses`; key from explicit `default.hy.claude.api_key`.
- Plan: `https://tokenhub.tencentmaas.com/plan/v3/responses`; key from explicit `override.ds-flash.codex.api_key`. Private comparison confirmed agreement with the Claude Plan key and inequality with the direct key. Neither key nor a key hash is published.

Each sample had separate HOME, CODEX_HOME, SQLite directory, TMPDIR and scratch workspace. No live auth/config/plugin tree was copied. Native startup generated its own bundled skill/bootstrap files inside these private homes; those unrelated files are excluded from the artifact manifest. Private directories are 0700 and regular files 0600. Permission maintenance now explicitly skips symlinks. No production port/service or outer `agent-sandbox` wrapper was used.

Session policy was `workspace-write`, `on-request`, `approvals_reviewer="auto_review"`. No full-access flag, approval bypass or additional writable root was configured. The shell environment excluded credential-like environment variables. Direct-2's persisted native turn context confirms this policy, model `hy4` and effort `high`.

The session catalog entry was authored explicitly for this probe, not copied from another model: simple coding instructions, text only, direct tools, no Lite, no search, `high`, conservative 64,000-token operating window and 48,000 compaction. These are probe client settings, not a context-capacity certification. Native token-count metadata resolved the effective session window to **60,800**. The independent bundled guardian retained all instructions, security context, tools and schema; only the repository's established `tool_mode="direct"` / `use_responses_lite=false` metadata mapping was applied. All route repair flags remained false.

## Complete direct-2 evidence

Five session responses and one guardian response all ended with actual `response.completed`, `status="completed"`. Session responses contained multiple nonterminal deltas in separate timed reads; the first response alone had **434 reads containing deltas from 1.005945 s to 15.319970 s** after upstream headers. These were incrementally forwarded through the unchanged ordinary shim path. The guardian was intentionally buffered: 207,404 response bytes, one completed buffered read at 39.078743 s. Full raw bytes and timing records are retained, rather than treating HTTP 200 or a final answer as streaming proof.

Actual native tool: ordinary `exec_command` function calls, no Lite header. The canary was random, present only in the scratch file, and absent from the user prompt. Native shell execution read it, copied it to `result.txt`, compared the files, then fed the actual outputs back to Hy. Relevant correlation IDs:

| Native call ID | Action | Subsequent upstream result |
| --- | --- | --- |
| `chatcmpl-tool-850684718863c65f` | Read fresh canary | Actual output containing canary |
| `chatcmpl-tool-a81ecd2c8b976e8c` | Copy/check scratch result | Actual output containing canary and successful comparison |
| `chatcmpl-tool-bc720fea118f065b` | Exact authorized sentinel command, `require_escalated` | `Process exited with code 0`, consumed by next session request |
| `chatcmpl-tool-8f91f4509b3ba64b` | Read-only sentinel confirmation | Actual successful native output |

The escalation command wrote only `direct-2` into the unique `direct-2/authorized-sentinel.txt` outside scratch. Native auto-review requested logical `codex-auto-review`; only `model` changed on the wire to `hy4`. Original input, instructions, tools and `text.format` were preserved byte-semantically. Captured native schema:

```json
{
  "type": "json_schema", "strict": false, "name": "codex_output_schema",
  "schema": {
    "type": "object", "additionalProperties": false,
    "properties": {
      "risk_level": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
      "user_authorization": {"type": "string", "enum": ["unknown", "low", "medium", "high"]},
      "outcome": {"type": "string", "enum": ["allow", "deny"]},
      "rationale": {"type": "string"}
    },
    "required": ["outcome"]
  }
}
```

Hy's actual completed guardian output was **`{"outcome":"allow"}`**, validated against that captured schema using `jsonschema`. The optional fields were not fabricated. The original and mapped guardian request both used **`reasoning.effort="low"`**, independently selected by native review, while every session request used **`high`**. The low request was accepted and completed in this observation; this is not a claim about documented effort vocabulary or justification for a new remapping. Bundled guardian metadata's default is `medium`; neither that value nor the session setting predicts native review's observed `low`.

Native's internally generated guardian rollout reports read-only / `approval_policy="never"`, effective window 258,400. This is native's own review sub-session, not a harness override or a bypass for the session's escalated command. The session remained workspace-write/on-request/auto_review. The automatic verdict allowed the command, native executed it, the sentinel contents matched, and its successful result returned to Hy before native emitted `turn.completed`, the observed canary final and exit 0.

Nonfatal errors remain visible: direct-2 stderr contained 6 `ReasoningSummaryPartAdded without active item` and 1,265 `ReasoningSummaryDelta without active item` messages. Direct-1 had 13 and 1,407 respectively. They did not prevent direct-2 tools, structured review, final or completion. No normalization was silently applied. This is residual stream-dialect noise for controller adjudication, not a clean-log claim.

## Retained setup failures and correction

**Direct-1 outer sandbox:** the initially sandboxed harness parent could not let native macOS `sandbox-exec` apply its own policy. Twelve shell attempts returned `sandbox-exec: sandbox_apply: Operation not permitted` (native tool code 71); the thirteenth tool call requested the explicit escalation. Ordinary Hy streams continued, but the real canary read never succeeded. At 146.584 seconds the harness and its isolated native/server processes were signaled to stop. The native parent was stopped before reaping its child, so the exact native exit code is **unavailable**, recorded as JSON null with signal-sent 15, not falsely inferred as -15. There is no final/terminal or complete guardian verdict for this sample. Subsequent samples ran from an approved unrestricted parent while preserving native policy. Direct-1 was not repeated or replaced.

**Plan-2 preflight incident:** my permission cleanup mistakenly followed native-generated `apply_patch`/`applypatch` symlinks left in Plan-1's isolated HOME and changed the installed Codex executable mode to 0600. Plan-2's first parser invocation exited **-6** with Node `process.execve ... EACCES`, before any workflow request. I restored that executable's normal 0755 mode and corrected cleanup/manifest traversal to skip symlinks. No executable contents were written. The incident, parser stdout/stderr/exit and correction are retained privately as `plan-2/setup-failure.json` and `parser.*.setup-failure`. The same declared Plan-2 workflow then started for the first time and failed with HTTP 403 as recorded above. This was an accidental installed-file metadata mutation, corrected during the investigation; it must not be described as an entirely untouched-live run. No live endpoint/config or feature integration changes occurred.

Two evidence-only parser corrections were also made: handle native SSE `output:null` and recognize actual native tool text `Process exited with code 0`. They neither changed any upstream request nor replaced any outcome. Frozen native configuration remained the same across all four samples.

## Artifacts, checks and controller handoff

- [investigation-results.json](investigation-results.json): concise per-sample criteria/outcomes and archive pointer. Full original results are preserved in the archive.
- [investigation-evidence.tar.gz](investigation-evidence.tar.gz), indexed by [investigation-evidence-index.json](investigation-evidence-index.json): original sanitized results and native ingress traces, including original review context/schema before mapping. Member and archive SHA256 values permit retrieval verification; no auth headers or private configs.
- [probe_hy4.py](probe_hy4.py): bounded harness, including resumable retention and evidence-only `--summarize`. No further upstream samples were sent during summarization.
- Exact raw private evidence root: `/private/tmp/hy4-codex-task/investigation-20261105-112805`. The archived full results JSON's `raw_private_artifacts` array gives exact paths, lengths and SHA-256 values for every selected raw request, response, chunk trace, native log/final/rollout, exit and setup-failure artifact. Private endpoint/config/catalog files, stage configs, symlinks and native bootstrap/cache files are excluded from this manifest. `source_artifacts` hashes identify the branch shim/resolver/fixture/catalog helper and probe declaration/harness.

Primary guardian raw evidence is `direct-2/ingress.jsonl` (ingress 4), `direct-2/upstream-04.request.json`, `direct-2/upstream-04.response`, `direct-2/chunks.jsonl` and `direct-2/native.jsonl` under that exact root. Their hashes are in the JSON manifest. Guardian response SHA-256: `68df163b81b76b6d07a9606c2f5d9a4149b37b770a99aaeda732499caad05728`. All published strings were redacted against both exact selected keys, with credential-field/header filtering and additional bearer/token filtering. The keys themselves and their hashes are absent.

Source selection follows controller-provided current Tencent references: [Codex Plan setup](https://cloud.tencent.com/document/product/1823/130071), [Plan models/endpoints](https://cloud.tencent.com/document/product/1823/130060), [Hy4 direct API](https://cloud.tencent.com/document/product/1823/132252), [documented high/no_think effort](https://cloud.tencent.com/document/product/1823/131208), and [Claude Plan setup](https://cloud.tencent.com/document/product/1823/130070). No catalog search, provenance investigation or capability benchmark was performed.

Investigation verification covers native parser acceptance and actual workflows, schema validation, sentinel/result contents, all selected artifact hashes, private file modes, no selected keys in work-unit artifacts, unchanged tracked product files and closed ephemeral listeners. No product suite or synthetic guardian failure controls were run because this handoff changes no product behavior.

**Smallest now-supported next step:** controller may accept the single complete direct observation as evidence for a direct-only existing-provider extension: `hy4`/`high`, minimal authored text/direct catalog, existing guardian mapping unchanged, `/v1` default, registry/card/route/launcher/factory entries and affected existing tests/docs. This batch alone does not warrant a two-clean-sample or reliability claim; the first sample remains incomplete and any further sample requires a separate declaration. No Hy schema downgrade, tool removal, guardian effort adaptation or fallback is justified by these results. Do not stage a working Plan Codex override or claim Plan viability: access must first be resolved and native evidence obtained. Stop here for controller adjudication; no product implementation or live rollout is included in this handoff.
