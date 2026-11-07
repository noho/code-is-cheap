# Runtime override rename closeout

Status: implementation/validation and full review passed; PR delivery and authorized live sync pending.

Runtime names beneath private override providers now follow the same exact-name selection as root/provider names. Unknown names are ignored before inspecting values; valid siblings stay active, empty/all-filtered maps are inert, complete defaults/factory provide fallback, and exact-name restoration validates/reactivates. No suffix rules. Default/factory, active tuple/field/key validation and private-file/JSON/credential boundaries remain strict. Bilingual docs and prior contradictory tests are aligned.

Eight focused cases and all37 endpoint/install tests passed; both independent primary Claude reviewers (MiMo and DS) completed with no substantive findings. Their initial sandbox-localhost errors and successful corrected reruns are retained in the formal reports. No accepted unfixed finding remains. See implementation.md and controller.md for scope, commands and decisions.

Applicable authorized sync commands after delivery checks:

```bash
./scripts/sync-agent-tools.sh
./scripts/sync-codex-agent.sh
```

Both installed helper/factory pairs must match the reviewed source, and the user's private file must stay byte-for-byte identical. Installed checks will cover actual selected-key validation, codex-bak/arbitrary runtime copies with preserved Claude sibling, the installed ds-flash_codex launcher against a native stub, and same-PID route readiness. No vendor inference or skill sync is required.

Remaining coverage limits follow existing test/operator policy: no full repository matrix/vendor API check; old-factory behavior has synthetic coverage; no unrelated owner-UID policy extension. Installed behavior is the next authorized verification. No associated issue or issue comment applies; private config/credentials stay outside Git. PR pending; user merges manually.
