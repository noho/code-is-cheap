"""Actual CLI tools under srt; deterministic local model endpoints, no real keys.
Opt in like test_agent_sandbox.py. Requires deployed Codex and Claude binaries.
"""
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import struct
import subprocess
import tempfile
import threading
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]


def png(rgb):
    def chunk(kind, data):
        return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',1,1,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0'+bytes(rgb)))+chunk(b'IEND',b'')


@unittest.skipUnless(platform.system() == 'Darwin' and os.getenv('AGENT_SANDBOX_KERNEL_TESTS') == '1', 'explicit macOS kernel-test opt-in')
class RuntimeTests(unittest.TestCase):
    def probe(self, runtime):
        if not shutil.which(runtime): self.fail(f'{runtime} must be installed')
        with tempfile.TemporaryDirectory(prefix=f'agent-sandbox-{runtime}.') as temp:
            p = Path(temp).resolve()
            for name in ('work/denied', 'work/allowed', 'home/.codex', 'home/.config/agent-tools', 'bin', 'sinks'):
                (p/name).mkdir(parents=True)
            secret = 'DENIED_TEXT_723039ca'
            (p/'work/denied/report').write_text(secret)
            forbidden_image = png((255,255,255))
            allowed_image = png((0,0,0))
            (p/'work/denied/image.png').write_bytes(forbidden_image)
            (p/'work/allowed/image.png').write_bytes(allowed_image)
            (p/'work/allowed/canary').write_text('ALLOW_CANARY_002912')
            (p/'work/alias').symlink_to(p/'work/denied/report')
            (p/'denies.json').write_text(json.dumps([str(p/'work/denied')]))
            requests = []
            errors = []
            shell = f"cat {shlex.quote(str(p/'work/alias'))}; rg -n DENIED_TEXT {shlex.quote(str(p/'work'))}; cat {shlex.quote(str(p/'work/allowed/canary'))}"
            class Handler(BaseHTTPRequestHandler):
                def log_message(self,*args): pass
                def do_POST(self):
                    try:
                        raw = self.rfile.read(int(self.headers.get('Content-Length',0)))
                        if self.headers.get('Content-Encoding') == 'gzip': raw = zlib.decompress(raw,31)
                        req = json.loads(raw)
                        requests.append(req)
                        n = len(requests)
                        if runtime == 'codex':
                            actions = [
                                ('exec_command',{'cmd':'touch '+str(p/'work/rule-forbidden-output')}),
                                ('exec_command',{'cmd':'cat '+str(p/'work/denied/report'),'sandbox_permissions':'require_escalated','justification':'synthetic isolation test'}),
                                ('exec_command',{'cmd':shell}),
                                ('view_image',{'path':str(p/'work/denied/image.png')}),
                                ('view_image',{'path':str(p/'work/allowed/image.png')}),
                            ]
                            if n <= len(actions):
                                name, arguments = actions[n-1]
                                item = dict(id=f'fc{n}',type='function_call',call_id=f'call{n}',name=name,arguments=json.dumps(arguments))
                            else:
                                item = dict(id='final',type='message',role='assistant',status='completed',content=[dict(type='output_text',text='Probe complete')])
                            events = [dict(type='response.created',response=dict(id=f'r{n}',object='response',status='in_progress',output=[])),
                                dict(type='response.output_item.added',output_index=0,item=item),dict(type='response.output_item.done',output_index=0,item=item),
                                dict(type='response.completed',response=dict(id=f'r{n}',object='response',status='completed',output=[item],usage=dict(input_tokens=1,output_tokens=1,total_tokens=2)))]
                        else:
                            actions = [('Read',{'file_path':str(p/'work/denied/report')}),('Bash',{'command':shell}),
                                ('Read',{'file_path':str(p/'work/denied/image.png')}),('Read',{'file_path':str(p/'work/allowed/image.png')})]
                            if n <= len(actions):
                                name, arguments = actions[n-1]
                                block = dict(type='tool_use',id=f'tool{n}',name=name,input={})
                                delta = dict(type='input_json_delta',partial_json=json.dumps(arguments))
                                reason = 'tool_use'
                            else:
                                block = dict(type='text',text='')
                                delta = dict(type='text_delta',text='Probe complete')
                                reason = 'end_turn'
                            events = [dict(type='message_start',message=dict(id=f'm{n}',type='message',role='assistant',model='test-model',content=[],stop_reason=None,stop_sequence=None,usage=dict(input_tokens=1,output_tokens=0))),
                                dict(type='content_block_start',index=0,content_block=block),dict(type='content_block_delta',index=0,delta=delta),
                                dict(type='content_block_stop',index=0),dict(type='message_delta',delta=dict(stop_reason=reason,stop_sequence=None),usage=dict(output_tokens=1)),dict(type='message_stop')]
                        self.send_response(200); self.send_header('Content-Type','text/event-stream'); self.end_headers()
                        for event in events: self.wfile.write(('event: '+event['type']+'\ndata: '+json.dumps(event)+'\n\n').encode())
                        self.wfile.flush()
                    except Exception as e:
                        errors.append(repr(e)); self.send_error(500)
            server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
            server.daemon_threads = True
            thread = threading.Thread(target=server.serve_forever,daemon=True); thread.start()
            self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
            port = server.server_port
            config = f'sandbox_mode = "workspace-write"\nmodel = "gpt-5.4"\nmodel_provider = "mock"\n[model_providers.mock]\nname = "mock"\nbase_url = "http://127.0.0.1:{port}/v1"\nwire_api = "responses"\nrequires_openai_auth = false\n'
            (p/'home/.codex/config.toml').write_text(config); (p/'home/.codex/mimo.config.toml').write_text('')
            (p/'home/.codex/rules').mkdir()
            (p/'home/.codex/rules/default.rules').write_text('prefix_rule(pattern=["touch"], decision="forbidden", justification="deny synthetic write")\n')
            endpoints = json.loads((ROOT/'config/endpoints.example.json').read_text())
            endpoints['default']['mimo'][runtime] = dict(base_url=f'http://127.0.0.1:{port}',upstream_model='test-model',api_key='synthetic-test-key')
            ep = p/'home/.config/agent-tools/endpoints.json'; ep.write_text(json.dumps(endpoints)); ep.chmod(0o600)
            (p/'bin/srt').symlink_to(os.environ['SRT_TEST_BIN'])
            (p/f'bin/{runtime}-agent-run').symlink_to(ROOT/f'scripts/{runtime}-agent-run')
            env = {k:v for k,v in os.environ.items() if not any(part in k.upper() for part in ('KEY','TOKEN','SECRET','PASSWORD','CREDENTIAL','AUTHORIZATION'))}
            env.update(HOME=str(p/'home'),PATH=str(p/'bin')+':'+os.environ['PATH'],AGENT_TOOLS_FILE=str(ROOT/'scripts/agent-tools.zsh'))
            command = [str(ROOT/'scripts/agent-sandbox'),'--cwd',str(p/'work'),'--deny-list',str(p/'denies.json'),'--',f'{runtime}-agent-run','--provider','mimo','--prompt','Synthetic tool boundary test','--output',str(p/'sinks/events'),'--stderr',str(p/'sinks/stderr')]
            command += ['--last-message',str(p/'sinks/final')] if runtime == 'codex' else ['--instance','synthetic-boundary','--output-format','stream-json']
            result = subprocess.run(command,env=env,capture_output=True,text=True,timeout=80)
            trace = (p/'sinks/events').read_text() if (p/'sinks/events').exists() else ''
            stderr = (p/'sinks/stderr').read_text() if (p/'sinks/stderr').exists() else ''
            if os.getenv('AGENT_SANDBOX_EVIDENCE_DIR'):
                evidence = Path(os.environ['AGENT_SANDBOX_EVIDENCE_DIR'])
                evidence.mkdir(parents=True, exist_ok=True)
                (evidence/f'{runtime}-probe.json').write_text(json.dumps(dict(
                    exit_code=result.returncode, wrapper_stderr=result.stderr,
                    runtime_stderr=stderr, trace=trace, requests=requests, server_errors=errors),indent=2))
            self.assertEqual(result.returncode,0,(result.stderr,stderr,trace,errors))
            collected=json.loads(result.stdout)
            self.assertEqual(collected['agent_status'],'completed')
            self.assertEqual(collected['validation_status'],'needs_review')
            self.assertEqual(collected['result_status'],'not_assessed')
            self.assertGreater(collected['tool_results'],0)
            self.assertEqual(collected['logs']['output'],str(p/'sinks/events'))
            self.assertEqual(collected['tool_evidence_scope'],'recorded_events_only')
            self.assertEqual(len(requests),6 if runtime == 'codex' else 5,(result.stderr,stderr,trace,errors))
            wire = json.dumps(requests)
            self.assertNotIn(secret,wire)
            self.assertNotIn(base64.b64encode(forbidden_image).decode(),wire)
            self.assertIn('ALLOW_CANARY_002912',wire)
            self.assertIn(base64.b64encode(allowed_image).decode(),wire)
            self.assertIn('Operation not permitted',wire)
            if runtime == 'codex':
                self.assertFalse((p/'work/rule-forbidden-output').exists())
                self.assertIn('deny synthetic write',json.dumps(requests[1]))
            else:
                init = next(json.loads(line) for line in trace.splitlines() if json.loads(line).get('subtype') == 'init')
                self.assertEqual(init['permissionMode'],'bypassPermissions')
                self.assertEqual(init['mcp_servers'],[])
            # Agent-facing trace shows actual tools and a terminal success, not agent assertions.
            self.assertIn('turn.completed' if runtime == 'codex' else '"type":"result"',trace.replace(' ',''))

    def test_codex_native_tools(self): self.probe('codex')
    def test_claude_native_tools(self): self.probe('claude')


if __name__ == '__main__': unittest.main()
