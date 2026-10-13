# Packaged raw evidence

7 exact raw synthetic evidence files are in `raw-evidence.tar.gz`, SHA256 `d5a012b6f8b5425d9ba650761d57c069431fb97c258bfdf2eda240cef67e9ab2`. Per-file relative paths/hashes are in `raw-evidence-index.json`. The archive was reopened and all entries byte-verified. Original working-copy files remain locally available and ignored; previously committed versions remain in Git history. No business originals or external runner logs were removed or modified.

Retrieve this exact archive from the reviewed commit, extract to a fresh directory (`tar -xzf raw-evidence.tar.gz -C <fresh-directory>`), then verify index hashes. Review/report references to raw files in this directory resolve to identically named archive entries. Extraction into this directory restores those paths; do not execute evidence scripts merely to read logs. Packaging changes artifact storage, not test results or source behavior.
