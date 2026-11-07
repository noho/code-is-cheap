# Implementation and validation — 2026-11-07

Implementation delegate: repository-required gpt-6-sol through Codex runtime. No further delegation. Branch `fix/shim-subagent-message-delivery`. Controller accepted [plan.md](plan.md) and its closeout adjudication before implementation. This is the implementation/validation handoff; independent reviews and controller closeout are pending. No commit, push, live sync, restart, or original-session modification was performed.

## Result and attribution limits

The selected DeepSeek boundary now accepts observed native Codex 0.167.0 inter-agent tasks. Two real native candidate runs completed A initial, same-child followup, queued MESSAGE consumption, and B child file-read checks. These are actual DeepSeek inference and native collaboration calls, not synthetic SSE, direct child task injection, or two ordinary user turns. Rollout evidence, child tool output, and captured HTTP requests establish the results independently of the parent's report.

The failing baseline proves that task text reached native child rollouts and HTTP ingress. The controller's standard-message comparison and candidate runs show that standardizing those items restores execution on this connection. The private gateway internals remain unavailable: evidence does not distinguish whether its loss occurs at outer `agent_message` parsing, nested `encrypted_content`, or another internal step. This is a selected gateway protocol adapter, not a general native orchestration repair.

**Plaintext assumption:** observed `agent_message.content[].encrypted_content` strings are readable task text and match native task arguments. The adapter promotes only those slots, alongside `input_text`, on the explicitly enabled route. It does not decrypt anything, cannot recover actual opaque ciphertext, and cannot reliably distinguish ciphertext from an arbitrary plaintext string. If a future runtime places real ciphertext in this same slot, this compatibility assumption no longer holds; forwarding it as text would not restore the task. No reasoning encryption or function arguments are inspected or promoted.

## Changes

- `codex-agent/bin/codex-auto-review-shim`: small `fix_agent_messages` helper, route flag loading, and one handler hook after decompression and original-model guardian classification, before model serialization. This ordering allows malformed agent Unicode to return a controlled 400 before an ordinary model swap attempts serialization.
- For each top-level input `agent_message`, validate nonempty author/recipient and a nonempty list of known, string-valued content slots. Convert to standard `message`, `role=user`. Preserve every original text block in sequence, including empty strings, whitespace and Unicode. Do not collapse or infer task headers.
- A prepended input-text block carries JSON containing original non-content fields, including author, recipient, native id and optional routing metadata. Native `amsg_` id is metadata text, not a provider message id. Existing NEW_TASK/MESSAGE/FINAL_ANSWER text envelopes remain intact. Native persistence/rollouts are unchanged.
- Unknown content variants, malformed shapes or invalid Unicode produce sanitized HTTP 400 before an upstream request; no partially converted task is sent or dumped. Errors contain only a fixed description and input position, never arbitrary content/keys.
- Non-target items and other request fields preserve JSON values/order. Requests without target items return original bytes from the helper. Default-off flag is per-route only (no global inheritance); only `ds-flash:8788` enables `agent_message_fix` in repository routes. Existing single-route environment mode remains off.
- Existing model mapping, one-snapshot managed credentials, other compatibility switches, original guardian classification/retry, and normal streaming remain in their existing paths. Logs add only conversion counts.
- Focused tests plus relevant English/Chinese README usage; reproducible [native-probe.py](native-probe.py) and independent [audit-native-evidence.py](audit-native-evidence.py).

Final candidate shim SHA-256: `cd8e9f218c5a65d65bceff6ffac8b723c075913dad7ca08d999941ee34544dda`.

## Offline validation

Executed from this checkout, all exit 0:

```bash
python3 -m unittest discover -s tests -p 'test_shim_subagent_delivery.py'
# Ran 11 tests in 0.547s — OK
python3 -m unittest discover -s tests -p 'test_install_endpoints.py'
# Ran 38 tests in 29.545s — OK (also passed before the invalid-Unicode refinement)
python3 -m unittest discover -s tests -p 'test_provider_registry.py'
# Ran 11 tests in 0.816s — OK
python3 -m unittest discover -s tests -p 'test_shim_service.py'
# Ran 11 tests in 7.284s — OK
python3 docs/gateflow/shim-subagent-delivery/audit-native-evidence.py
# Both retained model runs pass the independent capture audit
python3 -m py_compile docs/gateflow/shim-subagent-delivery/native-probe.py
# Exit 0

git diff --check
# Exit 0
```

The focused suite exercises helper and production `Handler._handle`, plus actual socket/HTTP framing with a real handler and intercepted upstream network boundary. Coverage includes initial/history-followup, MESSAGE/FINAL_ANSWER envelopes, mixed plaintext slots, body-only tasks, empty text, Unicode/whitespace, routing and optional metadata, non-target reasoning/function arguments/messages, unknown/invalid variants and invalid author/recipient, invalid Unicode, enabled/disabled routes, byte no-op, identity/gzip/deflate, model and credentials, schema/tool compatibility switches, `read1` forwarding, and original guardian identity/buffering/retry. Invalid requests are checked for zero upstream sends and zero body dumps. No unrelated full suite was needed.

## Retained baseline and all candidate attempts

**Evidence redaction (2026-11-07):** [Original live probe evidence](original-live-probe-evidence.json) now explicitly redacts private project paths/context and business-specific options in its two historical assistant text fields; those excerpts are not verbatim unredacted source. Field pointers, original decoded-text UTF-8 SHA-256 values and reasons are recorded in its `redactions` array. Source identity/line numbers/source-file SHA-256 and exact harmless task bodies remain unchanged. [Redaction fix](redaction-fix.md) records static integrity checks and a pre-existing manifest mismatch; no inference, probe or test reruns were performed for this documentation-only fix. Independent rereview is pending.

[Baseline summary](evidence/baseline-summary.json), [baseline wire shapes](evidence/baseline-wire-shapes.json), [sanitized baseline native rollouts](evidence/baseline-rollouts-sanitized.json). Baseline wire file is a byte-for-byte durable copy of the planner's temp capture, SHA-256 `bbfa9a1e9f85730261de1fbc8c0b8514e99891991fe8cd633dc1e3f89c1e5c3a`.

Baseline parent `01a1b621-382e-7830-bf3b-8ed286860bd9`, child `01a1b621-4922-7a50-9ca8-3d6d12ca8f96` (`/root/wire_probe_a`): 10 real requests through an unchanged temporary relay to installed 8788. Both child finals fail strict `LIVE_PROBE_OK`; native initial/followup task strings are present. Exit 0 did not mean task success. See [plan.md](plan.md) for original request indices, task hashes and event lines. The planner did not retain its literal original driver/argv; do not describe a reconstructed command as the exact historical command. The recorded launch recipe was:

```bash
codex --version
# codex-cli 0.167.0
codex app-server \
  -c 'model_provider="deepseek"' \
  -c 'model="deepseek-flash"' \
  -c 'model_catalog_json="/Users/leo/.codex/model-catalogs/ds-flash.json"' \
  -c 'model_providers.deepseek.base_url="http://127.0.0.1:<temporary-observer-port>/v1"' \
  -c 'features.apps=false' -c 'features.plugins=false' \
  -c 'sandbox_mode="read-only"'
```

Then experimental `initialize` / `initialized`, fresh `thread/start` in the baseline temporary cwd, `turn/start` asking the parent for native spawn and same-child followup. The relay forwarded unchanged to 8788. This recipe is descriptive, with a port placeholder; it is not a new claimed baseline execution. Baseline actual task arguments/calls and child finals are durable in the sanitized native rollouts.

Candidate command actually executed three times (one setup failure and two model runs):

```bash
python3 docs/gateflow/shim-subagent-delivery/native-probe.py
```

The first attempt in the controller sandbox failed with `Operation not permitted` before initialization: no parent id, zero HTTP/model requests, exit 1, 0.43s. Preserved in [setup-failure](evidence/setup-failure/summary.json) and [stderr](evidence/setup-failure/app-server.stderr). This is a setup failure, not a model failure.

The next two invocations used controlled `require_escalated` execution, as authorized, with independently created temporary cwd/ports. The subprocess's exact argv is in each summary's `command`; the driver writes it into its temp `command.json` too. Both candidate listeners forward to installed loopback 8788, which retains ownership of private URLs/models/keys. No key is read/exported by the driver. New parent and child sessions use the installed ds catalog and actual 0.167.0 app-server; tools come from actual DeepSeek responses.

| Attempt | Parent | A child | B child | Result |
| --- | --- | --- | --- | --- |
| [Model run 1](evidence/candidate-run-1/summary.json) | `01a1b629-e2e7-7561-bee5-e21e57608f8b` | `01a1b629-fa9f-7931-9906-8eadd36411f4` | `01a1b62a-2dec-7912-966a-ed2fdc6be5b3` | All checks pass, exit 0, 27.53s |
| [Final-code run 2](evidence/candidate-run-2/summary.json) | `01a1b62c-12cb-77a3-a479-f14f6e38b218` | `01a1b62c-23b6-7f42-aca0-a3e3b2568035` | `01a1b62c-5643-7b33-bf4b-c9cb869260fe` | All checks pass, exit 0, 26.10s |

Run 1 passed before the invalid-Unicode refinement. Code was then reordered to validate agent input before model serialization, and regression tests were added. Run 2 intentionally verifies final code after that change; it was not a retry hiding a failed model run. All attempts are retained.

Each run has 15 observed ingress/egress request pairs, with 27 converted items counting replayed history. All captured non-target items and non-input fields compare equal; the actual outbound request hashes match captured converted bytes. Both child identities are tied to the recorded parent and provider/version by native session metadata. Full inter-agent items from this harmless diagnostic are retained, but global instructions/context, reasoning payloads, auth headers, user/account identity and unrelated business text are omitted.

**A:** `/root/delivery_a` has three distinct native turn IDs and exact finals: `LIVE_PROBE_OK`, `LIVE_FOLLOWUP_OK`, then `LIVE_MESSAGE_OK_6c8754e63c16` (run 1) / `LIVE_MESSAGE_OK_cde52a2ce9de` (run 2). Parent rollout proves native spawn, followup to the same handle, send_message, and another same-handle followup. The last followup task contains no token; child MESSAGE carries it. [Independent audit](evidence/native-audit.json) records distinct final turn IDs and verifies call order, recipients, and source/content equality for every converted item. The parent did not read files or run shell tools.

**B:** `/root/delivery_b` executed exactly one `exec_command`: `cat <its temporary harmless-target.txt>`. Tool call IDs `call_00_ET_tLDHTnOhpTL2UUFL9B9p8159` (run 1), `call_00_ET_jLQFt3bLaVEmJkbxVdzI8637` (run 2) match native child function outputs with `Process exited with code 0`. Output and exact child final match the actual driver-generated fixture:

- Run 1: `HARMLESS_NATIVE_CONTENT_fbe967ef8f084438afd316bd1379f8ca`
- Run 2: `HARMLESS_NATIVE_CONTENT_4a241c793f3046468799c225b0502ade`

Fixture contents are absent from parent prompts and all dispatched task messages. The fixture path, content, SHA-256, child tool arguments/output and final are retained. [Run 1 rollouts](evidence/candidate-run-1/rollouts-sanitized.json), [run 2 rollouts](evidence/candidate-run-2/rollouts-sanitized.json), [run 1 wire](evidence/candidate-run-1/wire.json), [run 2 wire](evidence/candidate-run-2/wire.json).

Transport observations: all observed HTTP statuses were 200. In each run one concurrent parent stream logged `client-gone` before `response.completed` (35577 / 34444 relayed bytes respectively); this was not a child-final failure. Its precise cancellation cause was not instrumented. No forced interruption, kill, or new retry mechanism was used. Native child finals, parent turn completion and clean app-server exit were independently verified. Driver closes app-server stdin after parent completion, waits for actual process exit, then shuts down/closes the temporary listener and joins its thread. Temporary artifacts remain for audit. Candidate failure dumps are redirected into its own temporary directory, never the installed shim directory.

## Live boundary and reopening assessment

No live deployment is claimed. Read-only post-test hashes show installed shim and routes remain the original values from the plan:

- shim: `7ae5d6d7dc86050b466d06cc63685eb1589d873cf730fa0ac3479dfed44d7cc7`
- routes: `afd1e15ca3a914993987382abaf148227ef6a97a796cdb73791b4787bea26bfe`

Only the allowed repository shim/routes, focused tests/README and task artifacts were changed. No direct writes to `~/.codex-agent`, original user rollouts, investment/watchlist/scheduler files or unrelated runner-handle-loss artifacts. New diagnostic rollouts were created normally by Codex; native persistence is not rewritten. Structural checks of durable JSON reject credential/global-instruction/account-identity fields.

After independent reviews, accepted fixes, controller closeout and explicit live authorization, run from the approved checkout:

```bash
./scripts/sync-codex-agent.sh
# Loads updated shim code/routes and restarts the installed launchd shim if loaded.
~/.codex-agent/bin/codex-auto-review-shim-service status
# If manual restart is needed instead:
~/.codex-agent/bin/codex-auto-review-shim-service restart
```

No skills/launchers changed, so `sync-skills.sh`, `sync-agent-tools.sh` and `source ~/.zshrc` are inapplicable. An HTTP-boundary adapter applies on subsequent requests to the updated route; reopening sessions is not inherently required to load this shim change. Existing native history remains native, so historical agent items can be normalized on later requests. However, probes used new sessions and do not prove automatic recovery of an existing idle/unloaded child or an already-failed task; do not promise those recover without a deliberate native followup/new task. Old business sessions were not resumed to test this. No blocker remains for the controller's independent review stage.

Official OpenAI documentation used to verify probe lifecycle: [Codex App Server — Getting started](https://developers.openai.com/codex/app-server#getting-started), including stdio initialization, fresh thread/turn, checking completed status and closing stdin. Exact observed item shapes and runtime identity come from installed 0.167.0 and retained native evidence, not assumptions about a newer schema.
