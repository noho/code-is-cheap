# Override rename-disable closeout

Status: implementation, validation and independent full-review gate passed; PR delivery and authorized live sync pending.

Private configuration now activates only exact root `override` and recognized provider names under it. Unknown private roots and override-provider names are inert and preserved. Renaming a provider disables that provider's overrides; renaming `override` disables the entire block; restoring the recognized name revalidates and reactivates it. Complete default/factory connections are selected without backup/environment credential borrowing. Active/default/factory validation, global duplicate JSON rejection, owned regular mode-0600 checks and whole-tuple semantics remain intact.

Four focused regressions and all34 endpoint/install tests passed, independently confirmed by MiMo Claude and DS Codex full reviews. Both reports and controller adjudication are retained. The sole MiMo suggestion was rejected-with-reason under the pre-implementation decision for an unchanged owner-UID branch; there is no accepted unfixed finding. See controller.md and implementation.md for commands, results and scope. Bilingual private-connection documentation is updated.

Applicable authorized deployment commands, after delivery checks:

```bash
./scripts/sync-agent-tools.sh
./scripts/sync-codex-agent.sh
```

Both installed copies of agent-endpoint.py must match the reviewed source. The private endpoints file must stay byte-for-byte unchanged; verification uses private temporary copies and mocked native launch rather than vendor inference. No skill changes require sync.

Residuals: existing UID-mismatch dynamic coverage is maintainer-owned later file-security testing work if the guard changes; full-repository/network coverage follows existing policy and operator ownership. No open code blocker or unclassified new risk. This work has no associated issue, so issue linkage/comments are not applicable. Live configuration and credentials remain outside Git.

Draft PR: pending. Next: immutable delivery check, authorized sync/installed verification and final closeout. User merges manually.
