import argparse, hashlib, json, pathlib, subprocess
p=argparse.ArgumentParser();p.add_argument('--collector',required=True);p.add_argument('--save',required=True);a=p.parse_args()
dpath=pathlib.Path('/Users/leo/workspace/portfolio-manager-v2/orch/workpapers/run-monitor-tencent-20261010/shaanxi-collector-timeout-demand-20261013/diagnosis.json')
d=json.loads(dpath.read_text());old=json.loads((dpath.parent/'replay.json').read_text());cmd=list(d['command'])
assert cmd[:3]==['python3','-B','/Users/leo/.local/bin/agent-run-result.py']
assert cmd[cmd.index('--exit-code')+1]=='0' and cmd[cmd.index('--runner-exit-code')+1]=='0'
cmd[2]=str(pathlib.Path(a.collector).resolve())
files=[dpath,dpath.parent/'replay.json',dpath.parent/'replay.stderr']
for option in ('--output','--stderr','--canary-file','--canary-expected','--artifact'):
 files.extend(pathlib.Path(cmd[i+1]) for i,v in enumerate(cmd[:-1]) if v==option)
files=list(dict.fromkeys(files))
def sha(x):return hashlib.sha256(x).hexdigest()
before={str(f):sha(f.read_bytes()) for f in files}
r=subprocess.run(cmd,capture_output=True,text=True);s=json.loads(r.stdout)
after={str(f):sha(f.read_bytes()) for f in files}
input_events=[json.loads(x) for x in pathlib.Path(cmd[cmd.index('--output')+1]).read_text().splitlines()]
notices=[(i,e) for i,e in enumerate(input_events,1) if e.get('type')=='error']
diags=s['errors']+s['anomalies']+s['warnings']
retained_notices=[{'stream':d['stream'],'line':d['line'],'message':d['message']} for i,e in notices for d in diags if d['line']==i and d['stream']=='output' and e['message'] in d['message']]
checks={'collector_exit_zero':r.returncode==0,'stderr_empty':r.stderr=='','expected_status':all(s[k]==v for k,v in {'runtime_exit_code':0,'runner_exit_code':0,'agent_status':'completed','validation_status':'needs_review','result_status':'not_assessed','terminal':'turn.completed','canary_status':'match','canary_read_candidate':False}.items()),'no_fatal_errors':s['diagnostic_counts']['errors']==0 and s['errors']==[],'original_anomalies_retained':all(x in diags for x in old['anomalies']),'final_unchanged':s['final_answer']==old['final_answer'],'session_usage_tools_unchanged':all(s[k]==old[k] for k in ['session_id','usage','events','tool_results','runtime_metrics']),'selected_artifacts_unchanged':s['artifacts']==old['artifacts'] and len(s['artifacts'])==2 and all(x['exists'] and x['regular_file'] for x in s['artifacts']),'all_five_notices_retained':len(retained_notices)==5 and [x['line'] for x in retained_notices]==[3,176,177,178,179],'original_inputs_unchanged':before==after}
record={'collector_path':cmd[2],'collector_sha256':sha(pathlib.Path(cmd[2]).read_bytes()),'argv':cmd,'actual_exit':r.returncode,'stderr_bytes':len(r.stderr.encode()),'summary':{k:s[k] for k in ['runtime_exit_code','runner_exit_code','agent_status','validation_status','result_status','terminal','diagnostic_counts','canary_status','canary_read_candidate','events','tool_results']},'retained_notices':retained_notices,'anomalies_sha256':sha(json.dumps(s['anomalies'],sort_keys=True).encode()),'final_sha256':sha(s['final_answer'].encode()),'checks':checks,'sources_sha256':before,'source_integrity_after':after}
pathlib.Path(a.save).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'summary':record['summary'],'checks':checks,'collector_sha256':record['collector_sha256']},ensure_ascii=False,indent=2));assert all(checks.values()),checks
