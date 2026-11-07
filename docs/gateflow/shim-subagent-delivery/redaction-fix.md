# Evidence redaction fix — 2026-11-07

Scope: controller-accepted Finding 1 (low) in the ds-flash review, branch `fix/shim-subagent-message-delivery`. This is a fix-delegate handoff; independent rereview remains pending.

## Actual changes

- `original-live-probe-evidence.json`: replaced unnecessary private workspace/project context and business-specific task options in the two assistant text fields below with explicit redaction markers. Preserved the surviving request for a concrete task instead of `LIVE_PROBE_OK`. Updated `selection` to state that the assistant excerpts are redacted, not verbatim unredacted source; added `redactions` with field pointers, original source line numbers, original text SHA-256 values and reasons.
- `implementation-validation.md`: added one evidence-redaction disclosure paragraph and the pending-rereview status.
- `evidence/sha256sums.txt`: refreshed only the existing entries for those two changed files. All other manifest entries are unchanged.
- `docs/reviews/code-review-20261107-213702-ds-flash.md`: replaced private quoted path/context/search tokens with redaction markers and generic private-business wording. Appended a remediation note without changing the historical finding status or claiming independent verification of the fix.
- `redaction-fix.md`: this handoff and integrity record.

## Redacted fields and original text hashes

Hashes below cover each original decoded JSON text string encoded as UTF-8, without an added newline. Original text is deliberately not reproduced.

| JSON pointer | Original source line | Original text SHA-256 |
| --- | --- | --- |
| `/entries/2/payload/content/0/text` | 15 | `95b16c3e42817cd526689f753f9199f44866a536dea9adebcc0333d8ba963895` |
| `/entries/4/payload/content/0/text` | 24 | `a06e2947d3bd7e30697b0505d82d5872d728d5fd8aa51dbea2500f799bf96259` |

Reason for both redactions: unnecessary private project paths/context and business-specific task options are unrelated to the delivery failure. Retained wording clearly shows that the assistant asked for a task instead of returning the requested token.

The original source identity/path, source line numbers and source-file SHA-256 (`a1bdc4345be86fd3980ebbe0e839210dd1dc43f30c324be55a3f7bfd0aef45ef`) are unchanged. That source-file hash identifies the original source; it is not the hash of the sanitized JSON. Session/thread/message identities, exact harmless initial/followup task bodies, and all remaining evidence values were preserved. No original source log or business file was opened to make or verify this fix.

## Checks actually performed

- Parsed the current evidence JSON and computed the original text hashes from its two existing fields before replacement.
- Structurally compared before/after JSON: only the two specified text fields, `selection`, and new `redactions` metadata differ. Exact task bodies, source identities, line numbers and source hash are unchanged.
- Searched only the five changed task files for the removed private path and business phrases; zero matches. No broad user-file search was performed.
- Verified all 23 manifest entries before and after updating the two affected hashes: 22 match; the same pre-existing `closeout.md` mismatch remains unchanged (details below). Both refreshed entries match their current files.
- Compared SHA-256 values of the 26 protected files before/after: production shim/routes, focused tests, both READMEs, native probe/audit driver and every other manifest-listed artifact (including all native test evidence) are unchanged.
- Ran `git diff --check` and a trailing-whitespace check of all five changed files; both pass.
- No delegation, original source/probe reruns, inference, tests, native audit-driver execution, commit, push, deployment or user-data modification. The other independent review artifact/conclusions were not read. Controller's two narrowly scoped independent rereviews are still required.

## Pre-existing integrity difference

The mismatch below existed before any fix edit and remains unchanged. It is outside this evidence-only redaction fix; the controller should reconcile it separately. The manifest entry was deliberately preserved rather than silently updating an unrelated closeout artifact.

| File | Manifest SHA-256 | Current file SHA-256 |
| --- | --- | --- |
| `closeout.md` | `ce69c8de4f070b7dcf1c38286a1b8d8ced317ca73b4ec714de5d1418001bde8a` | `f20a5d4107537c74402909d807bf1cc4c1959b5d3d8bfb5e5560f725bc38cbc9` |

## Resulting hashes

| File | SHA-256 |
| --- | --- |
| `docs/gateflow/shim-subagent-delivery/original-live-probe-evidence.json` | `f04e8576df4dbf571788066cdaa1ddc04c5f29ef494bc46ace408dde841ddf12` |
| `docs/gateflow/shim-subagent-delivery/implementation-validation.md` | `f3b9621a0904a4b40a7be45f537371f79578710c6ad2b6abaaa37a46b71c0492` |
| `docs/reviews/code-review-20261107-213702-ds-flash.md` | `111d8fa3b9a3f532b721ba29325fe7d87d9a6264ff9385a2e574776781d97f8a` |
| `docs/gateflow/shim-subagent-delivery/evidence/sha256sums.txt` | `a7d0b1908e73a95c7e2acc52780abdb29a753517073eefbdb444ee6eed22f8f4` |

This handoff omits its own hash to avoid a self-referential digest; its hash is returned separately in the fix process output. The manifest retains its existing membership and does not include this new handoff or the review report.
