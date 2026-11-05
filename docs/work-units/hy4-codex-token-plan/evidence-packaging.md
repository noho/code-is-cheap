# Evidence packaging

`fix.patch.gz` preserves the exact tested/reviewed patch bytes, SHA-256 `a806a748d59378eaa82d861c943775febbe4c29f7096cb1c02ff43769627fd4d` after decompression. The raw `fix.patch` remains locally available and is ignored only in this work-unit directory. Unified-diff blank context lines contain their required leading space; storing that raw patch inside another Git diff causes a whitespace false positive. No product source, test, review judgment or original patch byte was changed.

To reconstruct the raw artifact on another checkout:

```bash
gzip -dc docs/work-units/hy4-codex-token-plan/fix.patch.gz > /private/tmp/hy4-readiness-fix.patch
```

Review reports reference the original local raw path; the compressed artifact is its byte-identical durable source. All other evidence archive/index paths remain unchanged.
