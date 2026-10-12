# Evidence version scope

Original artifacts/logs/hashes are retained unchanged. evidence/controller-kernel.json is a preliminary kernel-only observation collected while the implementation harness was still evolving. Its source_sha256 records the source file observed at collection, without a before/after execution freeze; it is not a certificate for the current test bytes or a claim of an independently frozen historical revision. The concrete successful/denied operations remain historical observations.

Current authoritative whole-native/kernel byte binding is evidence/controller-native-final.json: source hashes captured before and after the 12-test execution matched, 11 native fixtures plus1control allpassed (including kernel). Its raw command/ingress/upstream hashes and fixture paths remain independently verified. Later C1 changes only the sync loaded-service error branch and its focused conversion tests; generator/runtime harness/card/catalog/source bytes are unchanged, and current generated catalog bytes were independently matched to real status-probe hashes during aggregate review.

No original preliminary source hash is replaced with a current hash. Restricted-parent failures, relative-canary fixture failure, long temp-root Unix socket EINVAL and later successful short-root runs remain separately described. Use short temp roots for srt Unix socket length; this test path correction did not weaken any sandbox boundary.

Provider acceptance is tiny status-only,8once-per-connection maxrequests, zero tools/retries; Kimi exactlyonce. Native synthetic and vendor evidence classes must not be conflated.
