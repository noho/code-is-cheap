# Gate state

- Work unit: subagent-native-exit-contract
- Branch: fix/subagent-native-exit-contract
- Confirmed goal: [goal.md](goal.md)
- Base: 32a244d1e286086be86dba837976d3d72fdd6c1f
- Goal confirmation: pass; user confirmed branch and inclusion of two existing investigation files.
- Current gate / next entry point: plan (independent review of plan-v2.md)
- Roles: gpt-6-sol Codex runner for plan/implementation/fix; mimo and ds-flash Claude runners for independent parallel reviews; controller adjudicates.
- Plan review applicability: required, public exit/status contract; use Planreview on both review routes.
- Controller plan check: plan.md covers root exit/acceptance coupling and one slice; independent review must challenge wrapper exit precedence and necessity of narrow launcher changes. Not approved for implementation yet.
- Plan delivery: plan.md; plan-receipt.json, actual outer/native/runner 0/0/0. One ordinary diff --no-index exit-1 diagnostic is retained, not a failed plan interaction.
- Implementation: not started.
- User steering: scope-amendment.md explicitly rejects multiple status verdicts/new wrapper status and requires thin CLI/native-final behavior; remove custom 12000 final cap and associated fields. Initial plan/reviews are superseded for conflicting contract, not current approval.
- Initial independent Planreview: ds-flash pass-with-risks delivered; mimo still in flight on old target. Do not cancel or misstate its result; it may complete as historical evidence while a separate plan-v2.md is authored.
- Revised plan delivered: plan-v2.md; plan-v2-receipt.json, actual outer/native/runner 0/0/0. Controller check: matches thin CLI + full untruncated final, removes all competing verdict fields, one concise slice; independent revised-plan review still required. User reiterated thin CLI and no final truncation.
- Findings: none adjudicated yet.
- Residual risk: see goal.md; no unclassified risk.
- Completion: active; no PR or deployment yet.
