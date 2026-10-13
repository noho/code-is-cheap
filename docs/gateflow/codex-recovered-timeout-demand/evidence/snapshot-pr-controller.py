import argparse,subprocess,json,hashlib,re,datetime
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--pr',required=True);p.add_argument('--stage',required=True);a=p.parse_args()
d=Path('docs/gateflow/codex-recovered-timeout-demand/evidence')/a.stage;d.mkdir(parents=True,exist_ok=False)
repo='noho/code-is-cheap'
def run(args):
 r=subprocess.run(args,capture_output=True);assert r.returncode==0,(args,r.returncode,r.stderr.decode());return r.stdout
args=['gh','pr','view',a.pr,'--repo',repo,'--json','title,body,url,author,headRefName,baseRefName,headRefOid,baseRefOid,headRepository,headRepositoryOwner,isDraft,state']
f=json.loads(run(args));(d/'facts-before.json').write_text(json.dumps(f,indent=2)+'\n')
b,h=f['baseRefOid'],f['headRefOid'];assert all(re.fullmatch('[0-9a-f]{40}',x) for x in (b,h))
url=f'repos/{repo}/compare/{b}...{h}'
diff=run(['gh','api','-H','Accept: application/vnd.github.v3.diff',url]);assert b'diff --git ' in diff;(d/'exact.diff').write_bytes(diff)
githead=run(['git','rev-parse','HEAD']).decode().strip()
localdiff=run(['git','diff','--no-ext-diff',b+'...'+h]);(d/'local-exact.diff').write_bytes(localdiff)
gh_files=set(re.findall(rb'^diff --git a/(.+) b/(.+)$',diff,re.M));local_files=set(re.findall(rb'^diff --git a/(.+) b/(.+)$',localdiff,re.M))
assert gh_files==local_files,{'github_files':len(gh_files),'local_files':len(local_files),'missing':list(local_files-gh_files)}
canonical=lambda raw:re.sub(rb'(?m)^(@@ -[0-9]+(?:,[0-9]+)? \+[0-9]+(?:,[0-9]+)? @@).*$',rb'\1',raw)
assert canonical(diff)==canonical(localdiff),{'github_sha':hashlib.sha256(diff).hexdigest(),'local_sha':hashlib.sha256(localdiff).hexdigest(),'note':'numeric ranges and all file/index/hunk/add/remove/context content must match; only trailing hunk function labels may differ'}

close=json.loads(run(args));assert (close['baseRefOid'],close['headRefOid'])==(b,h);(d/'facts-after.json').write_text(json.dumps(close,indent=2)+'\n')
checks=subprocess.run(['gh','pr','checks',a.pr,'--repo',repo,'--json','name,state,link,bucket'],capture_output=True)
(d/'checks.stdout').write_bytes(checks.stdout);(d/'checks.stderr').write_bytes(checks.stderr)
sha=hashlib.sha256(diff).hexdigest()
summary={'captured_at':datetime.datetime.now().astimezone().isoformat(),'repo':repo,'pr':int(a.pr),'base_oid':b,'head_oid':h,'compare_url':url,'diff_sha256':sha,'full_diff_content_equals_local_exact_OIDs':True,'raw_bytes_equal':diff==localdiff,'comparison_normalization':'only text after closing @@ in hunk labels; all numeric ranges/file/index/hunk content unchanged','canonical_diff_sha256':hashlib.sha256(canonical(diff)).hexdigest(),'changed_files':len(gh_files),'git_head':githead,'oid_stable':True,'checks_exit':checks.returncode,'facts':str(d/'facts-before.json'),'diff':str(d/'exact.diff')}
(d/'snapshot.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
