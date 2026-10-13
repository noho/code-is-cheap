# Packaged raw evidence

58 exact raw synthetic evidence files are in `raw-evidence.tar.gz`, SHA256 `b37ca7751d9567154d37a23a9f3c1a0f307368169ddb3745bcb9b5f5a7e6a278`. Per-file relative paths/hashes are in `raw-evidence-index.json`. The archive was reopened and all entries byte-verified. Original working-copy files remain locally available and ignored; previously committed versions remain in Git history. No business originals or external runner logs were removed or modified.

Retrieve this exact archive from the reviewed commit, extract to a fresh directory (`tar -xzf raw-evidence.tar.gz -C <fresh-directory>`), then verify index hashes. Review/report references to raw files in this directory resolve to identically named archive entries. Extraction into this directory restores those paths; do not execute evidence scripts merely to read logs. Packaging changes artifact storage, not test results or source behavior.
