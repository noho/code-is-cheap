import json,hashlib,argparse,datetime
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--runtime',choices=['codex','claude'],required=True);p.add_argument('--run',required=True);a=p.parse_args()
u=Path('docs/gateflow/codex-recovered-timeout-demand');v=json.loads(Path(a.run).read_text());s=v['summary'];root=Path('/private/tmp/codex-recovered-timeout-demand/probes')/a.runtime
inp=root/'input.json';out=root/'result.json';expected=json.loads((root/'controller-expected.json').read_text());result=json.loads(out.read_text())
assert {k:result.get(k) for k in expected}==expected,(result,expected)
assert all(type(result[k]) is int for k in ('count','sum','sum_squares'))
assert out.is_file() and not out.is_symlink() and out.stat().st_nlink==1
assert hashlib.sha256(inp.read_bytes()).hexdigest()==expected['input_sha256']
assert v['managed_exit']==s['runtime_exit_code']==s['runner_exit_code']==0
assert s['agent_status']=='completed' and s['validation_status'] in ('passed','needs_review') and s['result_status']=='not_assessed'
assert s['canary_status']=='match' and s['tool_results']>=3
assert not s['errors']
records=[];calls={}
for i,line in enumerate(Path(s['logs']['output']).read_text().splitlines(),1):
 e=json.loads(line)
 if a.runtime=='codex' and e.get('type')=='item.completed' and e.get('item',{}).get('type') in ('command_execution','mcp_tool_call'):
  b=e['item'];records.append({'line':i,'id':b.get('id'),'type':b['type'],'command':b.get('command',b.get('arguments')),'output':b.get('aggregated_output',b.get('result')),'exit':b.get('exit_code'),'status':b.get('status')})
 if a.runtime=='claude' and e.get('type') in ('assistant','user'):
  for b in e.get('message',{}).get('content',[]):
   if b.get('type')=='tool_use':calls[b['id']]={'call_line':i,'id':b['id'],'name':b.get('name'),'input':b.get('input')}
   if b.get('type')=='tool_result':records.append(dict(calls[b['tool_use_id']],result_line=i,content=b.get('content'),is_error=b.get('is_error',False)))
d=u/'evidence/live-probes'/a.runtime;d.mkdir(parents=True,exist_ok=False)
for file in ('input.json','result.json','controller-expected.json','prompt.md'):(d/file).write_bytes((root/file).read_bytes())
(d/'tool-evidence.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
proof={'captured_at':datetime.datetime.now().astimezone().isoformat(),'runtime':a.runtime,'provider':'mimo-flash','managed_exit':v['managed_exit'],'native_exit':s['runtime_exit_code'],'runner_exit':s['runner_exit_code'],'validation_status':s['validation_status'],'result_status':s['result_status'],'terminal':s['terminal'],'math_result_verified':True,'input_unchanged':True,'regular_new_artifact':True,'canary_match':True,'read_candidate':s['canary_read_candidate'],'recorded_tools':len(records),'logs':s['logs'],'kind':'ordinary real provider tool I/O and computation, not a reproduced network fault'}
(d/'controller-audit.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof));print(json.dumps(records,ensure_ascii=False,indent=2))
