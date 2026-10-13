# Packaged raw evidence

5 exact raw synthetic evidence files are in `raw-evidence.tar.gz`, SHA256 `dde8fe203557c99b5bd84b934649a3717354b4f13f0c8ec2e0943dcec36c6c35`. Per-file relative paths/hashes are in `raw-evidence-index.json`. The archive was reopened and all entries byte-verified. Original working-copy files remain locally available and ignored; previously committed versions remain in Git history. No business originals or external runner logs were removed or modified.

Retrieve this exact archive from the reviewed commit, extract to a fresh directory (`tar -xzf raw-evidence.tar.gz -C <fresh-directory>`), then verify index hashes. Review/report references to raw files in this directory resolve to identically named archive entries. Extraction into this directory restores those paths; do not execute evidence scripts merely to read logs. Packaging changes artifact storage, not test results or source behavior.
