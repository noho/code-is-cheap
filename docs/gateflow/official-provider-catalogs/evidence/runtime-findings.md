# Native request evidence before implementation

Codex 0.162.1 directly parses all five user catalogs. A loopback-only synthetic HTTP server captured the first POST request and returned an intentional HTTP400 SYNTHETIC_DIAGNOSTIC_STOP. No external provider calls were made; all client exits1 are expected diagnostic stops, not provider acceptance or tool execution evidence.

All five configured profiles serialize reasoning.effort=max even where supported_reasoning_levels omits max. MiMo 2.6 with official code_mode_only/use_responses_lite emits input[].type=additional_tools and no top-level tools. Both features.code_mode=false and true emit this Lite structure. Therefore do not assume the sandbox false flag prevents the model-required Code Mode; retain it unless actual execution shows a necessary change.

Complete argv and bounded request summaries in native-request-controls.json, parser results in native-parser-controls.json. These controls deliberately do not include raw credentials or business prompts. Provider acceptance, JS tool execution, approval transport and kernel denial still require their approved verification.
