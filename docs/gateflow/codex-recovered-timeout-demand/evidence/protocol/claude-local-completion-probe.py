import gzip,hashlib,json,os,pathlib,subprocess,tempfile,threading,datetime
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
root=pathlib.Path(tempfile.mkdtemp(prefix='terminal-protocol-'))
records=[]
for reason in ('end_turn','stop_sequence'):
 state={'requests':0}
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args): pass
  def do_POST(self):
   payload=self.rfile.read(int(self.headers.get('Content-Length','0')))
   if self.headers.get('Content-Encoding')=='gzip':payload=gzip.decompress(payload)
   request=json.loads(payload);state['requests']+=1
   if self.path.endswith('/count_tokens'):
    self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b'{"input_tokens":1}');return
   usage={'input_tokens':1,'output_tokens':1,'cache_read_input_tokens':0,'cache_creation_input_tokens':0}
   events=[{'type':'message_start','message':{'id':'msg_synthetic','type':'message','role':'assistant','model':request.get('model','test-model'),'content':[],'stop_reason':None,'stop_sequence':None,'usage':usage}}, {'type':'content_block_start','index':0,'content_block':{'type':'text','text':''}}, {'type':'content_block_delta','index':0,'delta':{'type':'text_delta','text':'Synthetic protocol final.'}}, {'type':'content_block_stop','index':0}, {'type':'message_delta','delta':{'stop_reason':reason,'stop_sequence':'SYNTHETIC_STOP' if reason=='stop_sequence' else None},'usage':{'output_tokens':1}}, {'type':'message_stop'}]
   self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
   for e in events:self.wfile.write(('event: '+e['type']+'\ndata: '+json.dumps(e)+'\n\n').encode())
   self.wfile.flush()
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True;thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 task=root/reason;task.mkdir();(task/'config').mkdir()
 env={k:v for k,v in os.environ.items() if not any(x in k.upper() for x in ('KEY','TOKEN','SECRET','PASSWORD','CREDENTIAL','AUTHORIZATION')) and not k.startswith(('ANTHROPIC_','CLAUDE_'))}
 env.update(CLAUDE_CONFIG_DIR=str(task/'config'),ANTHROPIC_BASE_URL=f'http://127.0.0.1:{server.server_port}',ANTHROPIC_API_KEY='synthetic-local-test-key')
 argv=['/Users/leo/.local/bin/claude','--print','--output-format','stream-json','--verbose','--no-session-persistence','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--setting-sources','','--tools','','--disable-slash-commands','--model','test-model','--','Reply with synthetic text.']
 r=subprocess.run(argv,cwd=task,env=env,capture_output=True,text=True)
 (task/'output.jsonl').write_text(r.stdout);(task/'stderr.log').write_text(r.stderr)
 terminals=[]
 for line in r.stdout.splitlines():
  try:
   e=json.loads(line)
   if e.get('type')=='result':terminals.append({k:e.get(k) for k in ('type','subtype','is_error','result','stop_reason','terminal_reason','api_error_status')})
  except ValueError:pass
 records.append({'api_response_stop_reason':reason,'argv':argv,'actual_native_exit':r.returncode,'requests':state['requests'],'native_terminals':terminals,'raw_output':str(task/'output.jsonl'),'output_sha256':hashlib.sha256(r.stdout.encode()).hexdigest(),'stderr':str(task/'stderr.log'),'stderr_bytes':len(r.stderr.encode()),'kind':'Deterministic localhost native-protocol observation; no real model/service/business data; not a transient-fault or installed live probe'})
 server.shutdown();server.server_close()
 print(json.dumps(records[-1],ensure_ascii=False),flush=True)
pathlib.Path('/Users/leo/workspace/code-is-cheap/docs/gateflow/codex-recovered-timeout-demand/evidence/protocol/claude-local-completion-probe.json').write_text(json.dumps({'captured_at':datetime.datetime.now().astimezone().isoformat(),'cli_version':'2.1.296','cases':records},ensure_ascii=False,indent=2)+'\n')
