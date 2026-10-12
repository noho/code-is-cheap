# Official provider catalog inputs

These are the five user-supplied official catalogs copied byte for byte from
`/Users/leo/Downloads` on 2026-10-12. Deployment reads these tracked files;
it does not read Downloads or fetch vendor documents. No source URL was
supplied for DS, GLM, Kimi or Qwen. MiMo documentation was supplied in the
conversation; no URL is invented here. The source strings are model
configuration data. Generated per-profile outputs remain untracked.

| Original filename | Bytes | SHA-256 |
| --- | ---: | --- |
| ds-model-catalogs.json | 76106 | d47876f3bca395fe2d9d3c7fc7312282a60da8a2479dd13b995cb8e0fe2695dd |
| glm-model-catalogs.json | 2471 | 94cf9e8df540be39aa2948bf14ae665ec76699b1740d5344f499dd67fc71d1a3 |
| kimi-model-catalogs.json | 1952 | 61990fe840fe299eafc08460b16da5b53c720cc34ccd147e820265dd2f1f50d4 |
| mimo-model-catalogs.json | 85255 | 8834dc34d879b8489b7376a5a1788f0d1b696f8410fc2df3544ad38ab145601a |
| qwen-model-catalogs.json | 15100 | 4bc94831cb66e43aaf4c375543f92883bfa1d3116a4065c5796c5de29e8a019c |

Each cloud output preserves the complete source object, root metadata,
ordering, unselected entries and unknown fields. It appends one independent
bundled `codex-auto-review` guardian. DS/GLM/Kimi/Qwen guardian transport uses
direct tools and disables Responses Lite; MiMo retains native Code Mode/Lite.
Session instructions never come from a GPT donor. Local alone keeps the
existing compatible native direct-session fallback; GPT/business are unchanged.

| Profile | Source slug | Selected slug | Context / compact |
| --- | --- | --- | --- |
| ds-flash | deepseek-flash | deepseek-flash | 1048576 / 786432 |
| glm | glm-5.3 | glm-5.3 | 1048576 / 786432 |
| glm-flash | glm-5.3 | glm-5.3-flash | 1048576 / 786432 |
| kimi | k3 | k3 | 1048576 / 786432 |
| mimo | mimo-v2.6-pro | mimo-v2.6-pro | 1048576 / 786432 |
| mimo-fast | mimo-v2.6-pro-ultraspeed | mimo-v2.6-pro-ultraspeed | 1048576 / 786432 |
| mimo-flash | mimo-v2.6-flash | mimo-v2.6-flash | 1048576 / 786432 |
| qwen | qwen3.8-max | qwen3.8-max | 983616 / 737712 |

GLM Flash is explicitly user-authorized derived metadata: deep-copy official
`glm-5.3` and change only slug, display_name and description to label the
derivation. No independently supplied Flash card or Turbo migration is claimed.
Kimi's card and shim logical slug are `k3`; the endpoint resolver continues to
own upstream URL, model and key (including its existing factory wire default).

All eight card efforts remain `max`. Official supported-level lists/defaults
are preserved. MiMo's snapshot omits max and the user reports official max
confirmation; Qwen's snapshot advertises low/medium/xhigh and omits max.
The generator emits informational notes for these discrepancies. Synthetic
native forwarding does not establish vendor acceptance; controller owns the
small acceptance probes, with Kimi limited to at most one tiny status/debug call.

Native Codex parses assembled catalogs in fresh homes before installation.
The inspected CLI 0.162.1 has stable/default-true code_mode_host; the host key
stays omitted. Required Code Mode needs the installed host and existing outer
sandbox to execute it. Explicit host false must fail visibly. MiMo's existing
route-wide json_schema-to-json_object downgrade applies to ordinary and
guardian requests and loses schema enforcement. No metadata or boundary
fallback is supplied on runtime failure. See the bilingual root READMEs and
implementation evidence for measured outcomes and remaining prerequisites.
