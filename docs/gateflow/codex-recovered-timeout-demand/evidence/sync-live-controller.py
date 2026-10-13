import subprocess,json,hashlib,datetime,shutil
from pathlib import Path
root=Path('/Users/leo/workspace/code-is-cheap');u=root/'docs/gateflow/codex-recovered-timeout-demand';d=u/'evidence/live-sync';d.mkdir(parents=True,exist_ok=False)
expected='406ec8697cd516f335d3334b8a554353c9cc587d5e60428c4b9ba21e5817891d';assert hashlib.sha256((root/'scripts/agent-run-result.py').read_bytes()).hexdigest()==expected
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip();commands=[]
for name in ['sync-agent-tools.sh','sync-skills.sh']:
 args=['./scripts/'+name];r=subprocess.run(args,cwd=root,capture_output=True,text=True);(d/(name+'.stdout')).write_text(r.stdout);(d/(name+'.stderr')).write_text(r.stderr);commands.append({'argv':args,'actual_exit':r.returncode});assert r.returncode==0,(name,r.returncode,r.stderr)
entries=[]
for src,target in [('scripts/agent-run-result.py','/Users/leo/.local/bin/agent-run-result.py'),('scripts/codex-agent-run','/Users/leo/.local/bin/codex-agent-run'),('scripts/claude-agent-run','/Users/leo/.local/bin/claude-agent-run'),('skills/sub-agents/SKILL.md','/Users/leo/.codex/skills/sub-agents/SKILL.md'),('skills/sub-agents/SKILL.md','/Users/leo/.claude/skills/sub-agents/SKILL.md')]:
 s=root/src;t=Path(target);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert s.read_bytes()==t.read_bytes();entries.append({'source':src,'installed':target,'source_sha256':sha(s),'installed_sha256':sha(t),'equal':True})
versions={}
for name in ['codex','claude']:
 binary=shutil.which(name);r=subprocess.run([binary,'--version'],capture_output=True,text=True);assert r.returncode==0;versions[name]={'entry':binary,'version':r.stdout.strip(),'version_exit':r.returncode}
record={'at':datetime.datetime.now().astimezone().isoformat(),'checkout':str(root),'deployment_commit':head,'commands':commands,'installed_equality':entries,'runtime_versions':versions,'actual_runner_PATH_entries':{n:shutil.which(n) for n in ['codex-agent-run','claude-agent-run']},'sync_codex_agent':'not selected; no profiles/catalog/routes/shim changes','authorization':'user explicit after full review; no merge','next':'installed Developer/Judge read-only replay and real mimo-flash Codex/Claude three-step probes'}
(d/'summary.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
