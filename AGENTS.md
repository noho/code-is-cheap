# Project development workflow

These instructions apply to development of this repository.

1. Create a work branch before changing files; reuse the current work branch when continuing an unmerged PR.
2. Use `$sub-agents` to dispatch two independent `$deepreview` reviews in parallel, with providers `mimo` and `mimo-flash`.
3. The controller checks the evidence, adjudicates findings, and fixes accepted findings before closing the review loop.
4. Commit as needed, push the work branch, and create a PR. The user merges it manually.

`mimo-flash` permanently replaces `kimi` as the default second reviewer for this repository. Explicit user instructions for a task take precedence.
