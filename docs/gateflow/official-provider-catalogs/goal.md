# Goal confirmation: official provider catalogs

Status: confirmed by user steering after the scope proposal. Branch: `feat/official-provider-catalogs`.
Baseline: `17ef441` (merged PR #54). Working tree was clean before branch creation.

## Request and motivation

Use the provider-supplied official model catalogs found in `~/Downloads` in a new PR. The high-risk diagnosis is put aside. The current generator clones an installed Codex direct-tool/GPT instruction template and overwrites provider metadata; MiMo now documents Code Mode plus Responses Lite.

## Proposed goal and scope

- Adopt the five user-provided catalogs for DeepSeek, GLM, Kimi, MiMo and Qwen as tracked deployment inputs; record their source filenames and hashes. Do not depend on the user's Downloads directory at installation time.
- Preserve official model instructions and capabilities instead of generating cloud session metadata from a generic GPT template. Make only explicit, necessary deployment/model-name adaptations, with evidence and tests.
- User steering: default reasoning effort must be `max` for all covered provider profiles; do not silently downgrade it because a vendor catalog omits it. Preserve official reasoning metadata and verify how Codex/provider handle the explicit max selection. Report unsupported behavior specifically rather than declaring it supported or changing the default without direction. Align context settings with actual official capabilities where needed.
- Preserve provider IDs, user-owned endpoint/key overrides and public runner/launcher entry names except an explicitly agreed GLM Flash decision. Align Kimi's card and shim logical model name to the official `k3` slug; the endpoint resolver continues to control the upstream wire model independently.
- Adapt catalog staging/synchronization and the affected runner/sandbox/shim paths as actually required to execute the official catalog; preserve existing read/write/network boundaries, approval behavior and result collection. Do not silently delete `additional_tools` or fall back to the old cloud GPT-template metadata.
- Update the relevant README and meaningful tests. Validate sync in temporary homes and minimal synthetic provider/runtime tasks as needed; do not deploy to live during this PR.

## Non-goals

- No further high-risk investigation or promised remedy for risk refusals.
- No financial workflow, source, artifacts, caller task retries or background process changes.
- No API key/endpoint changes; no new model/provider routing product.
- GPT/account/business profiles and the local model's nonofficial fallback are outside this conversion; retain their existing intended behavior.
- No compatibility/migration framework, recurring catalog updater, scheduler or general sandbox redesign.
- No merge or live synchronization without separate authorization.

## Direct evidence

- `scripts/patch-codex-model-catalog.py`: clones a Codex direct session template, patches guardian tool mode to direct, and overrides session `tool_mode`, instructions fields, summaries and context metadata.
- `scripts/sync-codex-agent.sh`: stages cards/catalogs before installation but currently invokes that generator for every third-party profile.
- `scripts/agent-sandbox`: explicitly disables `features.code_mode` and copies only its declared model keys into the isolated home.
- `codex-agent/bin/codex-auto-review-shim`: forwards request/response data with model/auth/route-specific transformations; MiMo routes do not drop additional_tools. Full official Lite execution remains to be verified.
- Downloads files: `ds-model-catalogs.json`, `glm-model-catalogs.json`, `kimi-model-catalogs.json`, `mimo-model-catalogs.json`, `qwen-model-catalogs.json`.
- GLM file lacks `glm-5.3-flash`; Kimi file uses slug `k3`; MiMo 2.6 entries declare `code_mode_only` and Responses Lite and support none/low/medium/high. Qwen `qwen3.8-max` supports low/medium/xhigh and declares context 983616.

## Success signals

1. Installation/sync can deploy the approved provider metadata entirely from repository inputs, and the installed selected entries preserve the official semantics. Missing model mappings fail with a specific message, rather than inventing an official model card.
2. Covered provider profiles retain default effort max as explicitly requested, with actual handling verified or a precise unsupported limitation reported. Official context metadata and explicit model-name mappings apply. User-owned endpoint/key overrides still work.
3. Minimal actual Codex tool/read/write/final/result paths work for the approved configuration; MiMo Code Mode/Lite and the shim/approval path are tested to their relevant extent, with unverified limits stated explicitly.
4. A minimal isolated task retains deny protection and the existing write/network limits while tools and required outputs work; unsupported configurations fail visibly.
5. Independent MiMo/Codex and DS Flash/Claude reviews are adjudicated and closed, tests/documentation agree, and a new draft PR and final closeout are delivered for manual merge.

## Confirmed decisions

The user explicitly directed: if GLM Flash metadata is absent, copy the official glm-5.3 entry for glm-flash. Preserve the current glm-5.3-flash wire/logical model and label this as a user-authorized derived entry, not an independently supplied official Flash card. Do not switch the actual model to glm-5-turbo.

The user reports MiMo officially confirmed support for max reasoning. Keep max defaults for all covered provider profiles; do not edit an official supported-levels list merely to mask a runtime limitation.

The user explicitly confirmed official Kimi config.toml uses model="k3". Change the managed Kimi model card itself to k3 as well as the shim logical source name; do not implement a kimi-k3 alias as the selected catalog entry.

The user explicitly authorized dispatch to all providers and all providers' access to project files after an automatic approval rejection. Delegated plan/implementation/fix may use GPT-6 Sol; required independent review routes remain MiMo/Codex and DS Flash/Claude. This authorization does not expand product scope or authorize merge/live deployment.

Kimi quota is explicitly limited: use only for debugging/small live probes. No Kimi development/review dispatches. Prefer offline catalog/name tests and at most one small synthetic Kimi probe; do not continuously retry or consume its quota on repository-wide prompts.

The user's request and follow-up decisions resolve the proposed goal's scope and the blocking model gap. Enter plan and proceed through the gates. The request authorizes the new work branch and draft PR; merge/live remain outside authorization.
