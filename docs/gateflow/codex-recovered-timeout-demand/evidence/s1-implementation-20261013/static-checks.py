"""Save exact local static-check commands and exits; no runtime/provider requests."""
import ast
import json
import platform
from pathlib import Path
import subprocess
import sys
root=Path(__file__).resolve().parents[5]
evidence=Path(__file__).resolve().parent
checks=[]
for file in ('scripts/agent-run-result.py','tests/test_agent_run_results.py',str(Path(__file__).relative_to(root)),
             str((evidence/'synthetic-samples.py').relative_to(root))):
    ast.parse((root/file).read_text())
    checks.append(dict(command=['ast.parse',file],exit_code=0,stdout='syntax OK',stderr=''))
commands=[['zsh','-n','scripts/codex-agent-run','scripts/claude-agent-run'],['git','diff','--check'],
    ['rg','-n','unknown or unrecovered errors remain fatal|Other wording or shapes remain unsupported|未知或未恢复的错误仍属致命|recognized_codex_connection_notice|recognized_codex_startup_diagnostic|codex_connection_recovery_failure|finalize_codex_connection_notices',
     'README.md','README.zh.md','skills/sub-agents/SKILL.md','scripts/agent-run-result.py'],
    [sys.executable,'--version'],['zsh','--version'],['codex','--version'],['claude','--version'],['srt','--version']]
for command in commands:
    result=subprocess.run(command,cwd=root,capture_output=True,text=True)
    checks.append(dict(command=command,exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr))
    assert result.returncode == (1 if command[0]=='rg' else 0), checks[-1]
checks.append(dict(check='bilingual/generic semantics manual inspection',outcome='matched',
    topics=['native/process/final/identity/check predicate','wording-independent intermediate anomalies',
      'negative completion signal rejects','root-result ownership','end_turn/stop_sequence and optional historical metadata',
      'completed execution versus rejected call validation','partial visibility and not_assessed',
      'statistics/detail/optional checks unchanged']))
(evidence/'static-checks.json').write_text(json.dumps(dict(platform=platform.platform(),checks=checks),indent=2)+'\n')
print(f'{len(checks)} checks recorded; no obsolete contract matches; all expected exits observed')
