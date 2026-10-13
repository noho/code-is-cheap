Codex server-request retry notifications made the collector reject an execution even when later events satisfied its existing recovery checks. Recognize the exact observed notification wording, ASCII retry digits 1–5 with a fixed `/5` budget, and a lowercase hexadecimal UUID shape, then let the existing recovery proof decide whether each notification becomes a warning.

Unknown or unrecovered errors, malformed completion evidence, nonzero exits, and failed selected checks retain their rejection behavior. `result_status` remains `not_assessed`; this change does not reassess the historical caller task.

Validation:

- Five new regression entry points and all 61 runner/collector tests passed.
- Six saved-input scenarios replayed: the two supplied server notifications become warnings only with valid recovery; unrecovered and unknown errors remain rejected.
- Independent mimo-flash and ds-flash plan, slice and aggregate reviews passed, with controller adjudication saved under `docs/gateflow/codex-server-retry-recovery/`.

PR review, authorized live sync, and the gpt-6-sol/gpt-6-luna Codex tool probes are recorded in the final closeout artifact after their respective gates. This PR remains draft for the user's manual merge.
