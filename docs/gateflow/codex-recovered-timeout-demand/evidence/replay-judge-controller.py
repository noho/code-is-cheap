import argparse,ast,hashlib,json,pathlib,subprocess
p=argparse.ArgumentParser();p.add_argument('--collector',required=True);p.add_argument('--save',required=True);a=p.parse_args()
root=pathlib.Path('/Users/leo/workspace/portfolio-manager-v2/orch/jobs/20261012-601225.SH-01/g1-judge-02-evidence')
old=json.loads((root/'runner-summary.json').read_text());diag=json.loads((root/'collector-tls-notice-diagnostic.json').read_text())
assert old['runtime_exit_code']==0 and diag['native_runtime_exit_code']==0
cmd=['python3','-B',str(pathlib.Path(a.collector).resolve()),'--runtime','codex','--provider',old['provider'],'--output',old['logs']['output'],'--stderr',old['logs']['stderr'],'--exit-code','0','--runner-exit-code','0','--canary-file',str(root/'canary.txt'),'--canary-expected',str(root/'canary.expected')]
for x in old['artifacts']:cmd+=['--artifact',x['path']]
files=[root/x for x in ['runner-summary.json','collector-tls-notice-diagnostic.json','controller-failure-record.json','actual-exit.json','output.jsonl','stderr.log','canary.txt','canary.expected']]+[pathlib.Path(x['path']) for x in old['artifacts']]
sha=lambda b:hashlib.sha256(b).hexdigest();before={str(f):sha(f.read_bytes()) for f in files}
events=[json.loads(l) for l in (root/'output.jsonl').read_text().splitlines() if l.strip()]
term=[i for i,e in enumerate(events,1) if e['type']=='turn.completed'];failed=[i for i,e in enumerate(events,1) if e['type']=='turn.failed']
finals=[(i,e['item']['text']) for i,e in enumerate(events,1) if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='agent_message']
assert len(term)==1 and not failed and finals and finals[-1][0]<term[0] and finals[-1][1].strip()
r=subprocess.run(cmd,capture_output=True,text=True);s=json.loads(r.stdout);after={str(f):sha(f.read_bytes()) for f in files};all_diags=s['errors']+s['anomalies']+s['warnings']
notices=[(x['native_line'],x['event']['message']) for x in diag['recognizer_results']]
retained=[{'line':i,'message':text} for i,text in notices if any(x['stream']=='output' and x['line']==i and text in x['message'] for x in all_diags)]
def original_retained(old_diagnostic):
 if old_diagnostic in all_diags:return True
 # V2 retains completed error-item diagnostics with the full native envelope,
 # whereas V1 displayed the identical item payload only. Prove payload and location.
 for candidate in all_diags:
  if any(candidate[k]!=old_diagnostic[k] for k in ['stream','line','path','proof_line']):continue
  try:
   old_payload=ast.literal_eval(old_diagnostic['message']);new_payload=ast.literal_eval(candidate['message'])
   if (old_payload.get('type')=='error' and new_payload.get('type')=='item.completed'
       and new_payload.get('item')==old_payload and not old_diagnostic['truncated'] and not candidate['truncated']):return True
  except (ValueError,SyntaxError,AttributeError):pass
 return False
checks={'exit_zero' :r.returncode==0,'stderr_empty':r.stderr=='','expected_completion':all(s[k]==v for k,v in {'runtime_exit_code':0,'runner_exit_code':0,'agent_status':'completed','validation_status':'needs_review','result_status':'not_assessed','terminal':'turn.completed','canary_status':'match'}.items()),'no_fatal_errors':s['diagnostic_counts']['errors']==0,'native_unique_success':len(term)==1 and not failed,'four_unknown_TLS_notices_retained':len(retained)==4,'original_anomalies_retained':all(original_retained(x) for x in old['anomalies']),'final_unchanged':s['final_answer']==old['final_answer']==finals[-1][1],'statistics_unchanged':all(s[k]==old[k] for k in ['session_id','usage','events','tool_results','runtime_metrics']),'selected_artifacts_unchanged':s['artifacts']==old['artifacts'] and len(s['artifacts'])==4 and all(x['exists'] and x['regular_file'] for x in s['artifacts']),'original_inputs_unchanged':before==after}
record={'collector_path':cmd[2],'collector_sha256':sha(pathlib.Path(cmd[2]).read_bytes()),'argv':cmd,'actual_exit':r.returncode,'summary':{k:s[k] for k in ['runtime_exit_code','runner_exit_code','agent_status','validation_status','result_status','terminal','diagnostic_counts','canary_status','canary_read_candidate','events','tool_results']},'unique_terminal_line':term[0],'final_line':finals[-1][0],'final_sha256':sha(s['final_answer'].encode()),'retained_notices':retained,'checks':checks,'sources_sha256':before,'source_integrity_after':after,'diagnostic_display_note':'Line 53 fallback item retained at same source location with identical item payload inside full native item.completed envelope (V1 displayed item only); first harness exact-display assertion failed and is preserved separately, not a collector rejection','business_disposition':'Developer and Judge remain caller-unaccepted candidates; collector replay is technical completion only, not business validation'}
pathlib.Path(a.save).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'summary':record['summary'],'checks':checks},ensure_ascii=False,indent=2));assert all(checks.values()),checks
