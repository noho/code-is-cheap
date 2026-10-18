"""Opt-in installed native CLI/host against branch staging and two synthetic hops.

No vendor requests or real auth files. Native tests require explicit
OFFICIAL_CATALOG_RUNTIME_TESTS=1. Kernel tests additionally require the existing
AGENT_SANDBOX_KERNEL_TESTS=1 and validated absolute SRT_TEST_BIN. Run kernel
cases from an unrestricted parent; this harness never changes that boundary.
Evidence is retained in OFFICIAL_CATALOG_EVIDENCE_DIR (default private /tmp).
"""
from __future__ import annotations

import gzip
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import re
import signal
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
import unittest
from urllib.parse import urlsplit
import zlib

ROOT = Path(__file__).resolve().parents[1]
PROFILE_IDS = {'ds-flash':'deepseek', 'glm':'glm', 'glm-flash':'glm_flash', 'kimi':'kimi',
               'mimo':'mimo', 'mimo-fast':'mimo_fast', 'mimo-flash':'mimo_flash', 'qwen':'qwen'}


def decoded(raw, headers):
    encoding = headers.get('content-encoding', '').lower()
    if encoding == 'gzip': raw = gzip.decompress(raw)
    elif encoding == 'deflate': raw = zlib.decompress(raw)
    elif encoding not in ('', 'identity'): raise ValueError(f'unsupported fixture encoding {encoding}')
    return json.loads(raw)


def capture(path, headers, raw):
    headers = {k.lower():v for k,v in headers.items()}
    return dict(path=path, headers=headers, raw_hex=raw.hex(), body=decoded(raw,headers))


def append_json(path, doc):
    with path.open('a') as stream: stream.write(json.dumps(doc)+'\n')


def fixture_shim(root):
    """Fresh process: no parent endpoint cache; all listeners owned until exit."""
    loader=importlib.machinery.SourceFileLoader('official_fixture_shim',str(root/'home/.codex-agent/bin/codex-auto-review-shim'))
    spec=importlib.util.spec_from_loader(loader.name,loader)
    shim=importlib.util.module_from_spec(spec); loader.exec_module(shim)
    routes=json.loads((ROOT/'codex-agent/shim-routes.json').read_text())
    expected=json.loads((root/'connections.json').read_text())
    opener=shim.upstream_open
    def checked_open(req,timeout):
        assert req.full_url in {v['base_url']+'/responses' for k,v in expected.items() if k!='local'}, req.full_url
        parsed=urlsplit(req.full_url)
        assert parsed.hostname=='127.0.0.1' and parsed.port==int((root/'upstream-port').read_text())
        return opener(req,timeout)
    shim.upstream_open=checked_open
    resolved=[]; servers=[]
    for route in routes['routes']:
        route=route | {'from':routes['from']}
        selected=shim.endpoint_module().connection(route['endpoint_id'],'codex',require_key=True)
        assert selected==expected[route['endpoint_id']]
        class Handler(shim.Handler):
            def do_POST(self):
                raw=self.rfile.read(int(self.headers.get('Content-Length',0)))
                append_json(root/'ingress.jsonl',capture(self.path,self.headers,raw) | {'endpoint_id':self.route['endpoint_id']})
                original=self.rfile
                try:
                    self.rfile=io.BytesIO(raw)
                    shim.Handler._handle(self)
                finally: self.rfile=original
        Handler.route=route
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler); server.daemon_threads=True
        assert server.socket.getsockname()==('127.0.0.1',server.server_port)
        Handler.route['port']=server.server_port
        servers.append(server); resolved.append(route | {'port':server.server_port})
        threading.Thread(target=server.serve_forever,daemon=True).start()
    (root/'resolved-routes.json').write_text(json.dumps(resolved))
    (root/'shim-ready').write_text('ready')
    threading.Event().wait()


def sse(item,n):
    response=dict(id=f'resp_{n}',object='response',status='completed',output=[item],
                  usage=dict(input_tokens=20,output_tokens=5,total_tokens=25))
    return [dict(type='response.created',response=response | {'status':'in_progress','output':[]}),
            dict(type='response.output_item.added',output_index=0,item=item),
            dict(type='response.output_item.done',output_index=0,item=item),
            dict(type='response.completed',response=response)]


def descriptors(body):
    tools=list(body.get('tools') or [])
    for entry in body.get('input',[]):
        if entry.get('type')=='additional_tools': tools.extend(entry.get('tools',[]))
    expanded=[]
    for tool in tools:
        if tool.get('type')=='namespace': expanded.extend(tool.get('tools',[]))
        else: expanded.append(tool)
    return expanded


def shell_tool(body,command,escalate=False):
    for tool in descriptors(body):
        name=tool.get('name') or tool.get('function',{}).get('name')
        if name in ('exec_command','shell_command','shell'):
            if name=='exec_command': args={'cmd':command,'yield_time_ms':1000,'max_output_tokens':2000}
            elif name=='shell_command': args={'command':command,'timeout_ms':10000}
            else: args={'command':['/bin/sh','-c',command],'timeout_ms':10000}
            if escalate: args.update(sandbox_permissions='require_escalated',justification='Synthetic fixture-only approval write')
            return name,args
    raise ValueError('Native advertised shell schema unavailable: '+json.dumps(descriptors(body)))


def tool_item(body,command,n,escalate=False):
    exec_tool=next((t for t in descriptors(body) if t.get('name')=='exec'),None)
    if exec_tool:
        # The custom descriptor advertises nested exec_command in its native
        # TypeScript declaration; nested tools are not top-level Lite tools.
        if 'exec_command(args:' not in exec_tool.get('description',''):
            raise ValueError('native Code Mode descriptor lacks nested exec_command declaration')
        args={'cmd':command,'yield_time_ms':1000,'max_output_tokens':2000}
        if escalate:args.update(sandbox_permissions='require_escalated',justification='Synthetic fixture-only approval write')
        code=f'const result = await tools.exec_command({json.dumps(args)}); text(result);'
        return dict(id=f'ct_{n}',type='custom_tool_call',call_id=f'call_{n}',name='exec',input=code)
    name,args=shell_tool(body,command,escalate)
    return dict(id=f'fc_{n}',type='function_call',call_id=f'call_{n}',name=name,arguments=json.dumps(args))


def final_item(text):
    return dict(id='msg_fixture_final',type='message',role='assistant',status='completed',
                content=[dict(type='output_text',text=text)])


class Fixture:
    def __init__(self,case,profile,approval=None,host_false=False,kernel=False):
        evidence=os.environ.get('OFFICIAL_CATALOG_EVIDENCE_DIR')
        if evidence: Path(evidence).mkdir(parents=True,exist_ok=True)
        self.root=Path(tempfile.mkdtemp(prefix=f'official-{case}-',dir=evidence or '/private/tmp')).resolve()
        self.profile=profile; self.approval=approval; self.host_false=host_false; self.kernel=kernel
        self.errors=[]; self.requests=[]; self.session_requests=0; self.guardian_requests=0
        self.root.joinpath('fixture.json').write_text(json.dumps(dict(case=case,profile=profile,approval=approval,host_false=host_false,kernel=kernel,external_provider_requests=0)))
        for name in ('home/.codex','home/.config/agent-tools','bin','work','sinks','sqlite','tmp'):
            (self.root/name).mkdir(parents=True,exist_ok=True)
        self.token='SYNTHETIC_CANARY_'+case
        (self.root/'work/canary.txt').write_text(self.token+'\n')
        (self.root/'expected-token').write_text(self.token+'\n')
        self.env=dict(HOME=str(self.root/'home'),CODEX_HOME=str(self.root/'home/.codex'),
                      CODEX_SHARED_HOME=str(self.root/'home/.codex'),CODEX_SQLITE_HOME=str(self.root/'sqlite'),
                      CODEX_AGENT_TARGET=str(self.root/'home/.codex-agent'),TMPDIR=str(self.root/'tmp'),
                      PATH=f"{self.root/'bin'}:{os.environ['PATH']}",NO_PROXY='127.0.0.1,localhost',
                      AGENT_TOOLS_FILE=str(self.root/'launcher.zsh'))
        self.server=None; self.child=None; self.other=None

    def command(self,argv,name,timeout=90):
        process=subprocess.Popen(argv,env=self.env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                 text=True,start_new_session=True)
        timed_out=False
        try: stdout,stderr=process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True; os.killpg(process.pid,signal.SIGKILL)
            stdout,stderr=process.communicate()
        done=subprocess.CompletedProcess(argv,process.returncode,stdout,stderr)
        (self.root/f'{name}.stdout').write_text(done.stdout)
        (self.root/f'{name}.stderr').write_text(done.stderr)
        append_json(self.root/'commands.jsonl',dict(argv=argv,exit_code=done.returncode,name=name,timed_out=timed_out))
        if timed_out:raise AssertionError(f'{name}: synthetic subprocess timeout after {timeout}s; evidence {self.root}')
        return done

    def close(self):
        if self.child:
            self.child.terminate()
            try: self.child.wait(timeout=5)
            except subprocess.TimeoutExpired: self.child.kill(); self.child.wait()
        for server in (self.server,self.other):
            if server: server.shutdown(); server.server_close()
        for handle in getattr(self,'handles',[]):handle.close()

    def prepare(self):
        fixture=self
        class Upstream(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_POST(self):
                try:
                    raw=self.rfile.read(int(self.headers.get('Content-Length',0)))
                    rec=capture(self.path,self.headers,raw); req=rec['body']
                    append_json(fixture.root/'upstream.jsonl',rec); fixture.requests.append(rec)
                    endpoint=self.path.split('/')[2]
                    assert self.path==f'/fixture/{endpoint}/v1/responses'
                    assert endpoint in PROFILE_IDS
                    assert req['model']==f'fixture-wire-{endpoint}'
                    assert rec['headers']['authorization']==f'Bearer fixture-key-{endpoint}'
                    # Guardian identity observed at ingress, before remapping.
                    ingress=[json.loads(line) for line in (fixture.root/'ingress.jsonl').read_text().splitlines()]
                    guardian=ingress[-1]['body']['model']=='codex-auto-review'
                    if guardian:
                        fixture.guardian_requests+=1
                        if fixture.approval=='error': self.send_error(400,'SYNTHETIC_GUARDIAN_HTTP_ERROR'); return
                        fmt=ingress[-1]['body'].get('text',{}).get('format',{})
                        schema=fmt.get('schema',{})
                        (fixture.root/'guardian-schema.json').write_text(json.dumps(schema,indent=2))
                        # Version-matched native schema, fail visibly on drift.
                        verdict=fixture.guardian_verdict(schema)
                        (fixture.root/'guardian-verdict.json').write_text(json.dumps(verdict,indent=2))
                        item=final_item(json.dumps(verdict))
                    else:
                        fixture.session_requests+=1
                        n=fixture.session_requests
                        if fixture.kernel:
                            actions=fixture.boundary_commands()
                            if n<=len(actions): item=tool_item(req,actions[n-1],n)
                            else: item=final_item('CANARY='+fixture.token)
                        elif n==1:
                            command=(f'printf synthetic-approved > {shlex.quote(str(fixture.root/"approval-result"))}'
                                     if fixture.approval else fixture.canary_command())
                            item=tool_item(req,command,n,escalate=bool(fixture.approval))
                        else:
                            # Require native returned output before issuing completion.
                            if not fixture.approval and not fixture.host_false:
                                if fixture.token not in json.dumps(req['input']):
                                    (fixture.root/'unavailable-tool-evidence.json').write_text(json.dumps(req['input'],indent=2))
                            item=final_item('Approval fixture complete' if fixture.approval else 'CANARY='+fixture.token)
                    self.send_response(200); self.send_header('Content-Type','text/event-stream'); self.end_headers()
                    for event in sse(item,len(fixture.requests)):
                        self.wfile.write(('event: '+event['type']+'\ndata: '+json.dumps(event)+'\n\n').encode())
                    self.wfile.flush()
                except Exception as exc:
                    fixture.errors.append(repr(exc)); append_json(fixture.root/'server-errors.jsonl',dict(error=repr(exc)))
                    self.send_error(500,'SYNTHETIC_FIXTURE_ERROR')
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Upstream); self.server.daemon_threads=True
        assert self.server.socket.getsockname()==('127.0.0.1',self.server.server_port)
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
        port=self.server.server_port; (self.root/'upstream-port').write_text(str(port))
        connections={k:dict(base_url=f'http://127.0.0.1:{port}/fixture/{k}/v1',upstream_model=f'fixture-wire-{k}',api_key=f'fixture-key-{k}') for k in PROFILE_IDS}
        connections['local']=dict(base_url=f'http://127.0.0.1:{port}/fixture/local/v1',upstream_model='fixture-wire-local',api_key='')
        (self.root/'connections.json').write_text(json.dumps(connections))
        endpoint=self.root/'home/.config/agent-tools/endpoints.json'
        endpoint.write_text(json.dumps({'default':{},'override':{k:{'codex':v} for k,v in connections.items()}})); endpoint.chmod(0o600)
        for name,target in [('python3',sys.executable),('agent-endpoint.py',ROOT/'scripts/agent-endpoint.py'),
                            ('codex-agent-run',ROOT/'scripts/codex-agent-run')]:
            (self.root/'bin'/name).symlink_to(target)
        launchctl=self.root/'bin/launchctl'
        launchctl.write_text('#!/bin/sh\necho "$*" >> "$HOME/launchctl.log"\nexit 1\n'); launchctl.chmod(0o755)
        stage=self.command(['bash',str(ROOT/'scripts/sync-codex-agent.sh')],'staging')
        if stage.returncode: raise AssertionError(f'Native staging failed: {stage.stderr}')
        assert all(line.startswith('print ') for line in (self.root/'home/launchctl.log').read_text().splitlines())
        self.handles=[(self.root/'shim.stdout').open('w'),(self.root/'shim.stderr').open('w')]
        shim_argv=[sys.executable,str(Path(__file__).resolve()),'--fixture-shim',str(self.root)]
        append_json(self.root/'commands.jsonl',dict(argv=shim_argv,name='fixture-shim-process'))
        self.child=subprocess.Popen(shim_argv,env=self.env,stdout=self.handles[0],stderr=self.handles[1])
        for _ in range(200):
            if (self.root/'shim-ready').exists():break
            if self.child.poll() is not None:raise AssertionError('Fixture shim failed: '+(self.root/'shim.stderr').read_text())
            time.sleep(.025)
        else:raise AssertionError('Fixture shim readiness timeout')
        routes=json.loads((self.root/'resolved-routes.json').read_text())
        by_profile={r['endpoint_id']:r for r in routes}
        assert set(by_profile)==set(PROFILE_IDS)
        config=self.root/'home/.codex/config.toml'
        text=config.read_text()
        for profile,pid in PROFILE_IDS.items():
            route=by_profile[profile]
            url=f'http://127.0.0.1:{route["port"]}{route["request_prefix"]}'
            pattern=rf'(\[model_providers\.{re.escape(pid)}\][\s\S]*?base_url\s*=\s*)"[^"]+"'
            text,count=re.subn(pattern,lambda m:m[1]+json.dumps(url)+'\nrequest_max_retries = 0\nstream_max_retries = 0',text,count=1)
            assert count==1
        text='approval_policy = "'+('on-request' if self.approval else 'never')+'"\napprovals_reviewer = "auto_review"\nsandbox_mode = "workspace-write"\n'+text
        text+='\n[features]\ncode_mode = false\n'
        if self.host_false:text+='code_mode_host = false\n'
        config.write_text(text)
        effective=tomllib.loads(text)['model_providers']
        for profile,pid in PROFILE_IDS.items():
            parsed=urlsplit(effective[pid]['base_url'])
            assert parsed.hostname=='127.0.0.1' and parsed.port==by_profile[profile]['port']
            assert effective[pid]['wire_api']=='responses' and effective[pid]['requires_openai_auth'] is False
        launcher='source '+shlex.quote(str(ROOT/'scripts/agent-tools.zsh'))+'\n_codex_agent_shim_port() {\n case "$1" in\n'
        launcher+=''.join(f' {shlex.quote(k)}) print -r -- {v["port"]} ;;\n' for k,v in by_profile.items())
        launcher+=' *) return 1 ;;\n esac\n}\n'
        (self.root/'launcher.zsh').write_text(launcher)
        version=self.command(['codex','--version'],'native-version')
        if version.returncode:raise AssertionError('native binary unavailable')
        features=self.command(['codex','features','list'],'native-features')
        if features.returncode:raise AssertionError('native feature listing unavailable')
        host=next((line.split() for line in features.stdout.splitlines() if line.startswith('code_mode_host\t') or line.startswith('code_mode_host ')),None)
        assert host and host[-1]==('false' if self.host_false else 'true'), host
        if not self.host_false:assert 'code_mode_host' not in tomllib.loads(text)['features']

    def guardian_verdict(self,schema):
        # Retain a precise error and schema artifact instead of inventing a
        # permissive verdict contract on an incompatible runtime.
        props=schema.get('properties',{})
        if set(props)=={'risk_level','user_authorization','outcome','rationale'}:
            return dict(risk_level='low',user_authorization='high',outcome=self.approval,rationale='Synthetic fixture verdict')
        raise ValueError('native guardian assessment schema drift: '+json.dumps(schema))

    def canary_command(self):
        path=shlex.quote(str(self.root/'work/canary.txt'))
        return f'cat {path}; cp {path} result.txt'

    def boundary_commands(self):
        p=self.root
        return [f'cat {shlex.quote(str(p/"work/denied/secret"))}',
                f'cat {shlex.quote(str(p/"work/alias"))}',
                f'touch {shlex.quote(str(p/"outside-write"))}',
                f'touch {shlex.quote(str(p/"work/.git/protected-write"))}',
                f'curl --noproxy "" --max-time 2 -sS http://127.0.0.1:{self.other.server_port}/unlisted',
                self.canary_command()]

    def run(self):
        argv=[str(ROOT/'scripts/codex-agent-run'),'--provider',self.profile,'--cwd',str(self.root/'work'),
              '--skip-git-repo-check','--sandbox','workspace-write','--prompt','Synthetic fixture task: read canary.txt, write result.txt and report CANARY with equals.',
              '--output',str(self.root/'sinks/events.jsonl'),'--stderr',str(self.root/'sinks/native.stderr'),
              '--last-message',str(self.root/'sinks/final.txt')]
        if not self.approval:
            argv+=['--artifact',str(self.root/'work/result.txt'),'--canary-file',str(self.root/'work/canary.txt'),
                   '--canary-expected',str(self.root/'expected-token')]
        if self.profile=='qwen':argv+=['--persist']
        if self.kernel:
            # Isolation supplies its established inner full-access policy; the
            # actual outer srt boundary remains authoritative.
            i=argv.index('--sandbox'); del argv[i:i+2]
            srt=Path(os.environ.get('SRT_TEST_BIN',''))
            if not srt.is_absolute() or not srt.is_file():raise AssertionError('absolute installed SRT_TEST_BIN required')
            (self.root/'bin/srt').symlink_to(srt)
            denied=self.root/'work/denied'; denied.mkdir()
            (denied/'secret').write_text('FORBIDDEN_OFFICIAL_SYNTHETIC_SECRET')
            (self.root/'work/alias').symlink_to(denied/'secret')
            (self.root/'work/.git').mkdir()
            deny_file=self.root/'denies.json'; deny_file.write_text(json.dumps([str(denied)]))
            fixture=self
            class Unlisted(BaseHTTPRequestHandler):
                def do_GET(self):
                    append_json(fixture.root/'unlisted.jsonl',{'path':self.path}); self.send_error(500)
                def log_message(self,*args):pass
            self.other=ThreadingHTTPServer(('127.0.0.1',0),Unlisted)
            threading.Thread(target=self.other.serve_forever,daemon=True).start()
            argv=[str(ROOT/'scripts/agent-sandbox'),'--cwd',str(self.root/'work'),'--deny-list',str(deny_file),'--',*argv]
        return self.command(argv,'runner',timeout=90)

    def ingress(self):
        return [json.loads(line) for line in (self.root/'ingress.jsonl').read_text().splitlines()]


class FixtureControls(unittest.TestCase):
    def test_test_only_codec_and_native_tool_shapes(self):
        raw=b'{"model":"synthetic"}'
        for encoding,encoded in [('',raw),('gzip',gzip.compress(raw)),('deflate',zlib.compress(raw))]:
            self.assertEqual(decoded(encoded,{'content-encoding':encoding}),{'model':'synthetic'})
        ordinary={'tools':[{'type':'function','name':'exec_command'}]}
        self.assertEqual(tool_item(ordinary,'cat canary.txt',1)['type'],'function_call')
        lite={'input':[{'type':'additional_tools','tools':[{'type':'custom','name':'exec','description':'exec_command(args: {'}, {'type':'function','name':'exec_command'}]}]}
        self.assertEqual(tool_item(lite,'cat canary.txt',1)['type'],'custom_tool_call')
        with self.assertRaises(ValueError):tool_item({},'cat canary.txt',1)


@unittest.skipUnless(os.environ.get('OFFICIAL_CATALOG_RUNTIME_TESTS')=='1','explicit official native-test opt-in')
class OfficialRuntimeTests(unittest.TestCase):
    def fixture(self,case,profile,**kwargs):
        if not shutil.which('codex'):self.fail('installed native Codex CLI prerequisite missing')
        fixture=Fixture(case,profile,**kwargs); self.addCleanup(fixture.close)
        fixture.prepare(); return fixture

    def check_hops(self,fixture):
        self.assertEqual(fixture.errors,[])
        ingress=fixture.ingress()
        self.assertEqual(len(ingress),len(fixture.requests))
        logical=tomllib.loads((fixture.root/f'home/.codex/{fixture.profile}.config.toml').read_text())['model']
        for before,after in zip(ingress,fixture.requests):
            original=before['body']; wire=after['body']
            self.assertIn(original['model'],(logical,'codex-auto-review'))
            self.assertEqual(wire['model'],'fixture-wire-'+fixture.profile)
            self.assertEqual(after['headers']['authorization'],'Bearer fixture-key-'+fixture.profile)
            self.assertNotIn('fixture-key',before['headers'].get('authorization',''))
            self.assertEqual(original.get('instructions'),wire.get('instructions'))
            self.assertEqual(original.get('reasoning'),wire.get('reasoning'))
            if original['model']!= 'codex-auto-review':self.assertEqual(original['reasoning']['effort'],'max')
            lite=fixture.profile.startswith('mimo')
            items=[i for i in original['input'] if i.get('type')=='additional_tools']
            if lite:
                self.assertTrue(items); self.assertNotIn('tools',original)
                self.assertEqual(items,[i for i in wire['input'] if i.get('type')=='additional_tools'])
                self.assertIn('exec',[t.get('name') for t in descriptors(original)])
                self.assertEqual(original['reasoning']['context'],'all_turns')
                self.assertEqual(before['headers'].get('x-openai-internal-codex-responses-lite'),'true')
                self.assertEqual(after['headers'].get('x-openai-internal-codex-responses-lite'),'true')
            else:self.assertFalse(items); self.assertIn('tools',original)
        return ingress

    def check_success(self,fixture,done,clean=True):
        self.assertEqual(done.returncode,0,(str(fixture.root),done.stderr,done.stdout,(fixture.root/'sinks/native.stderr').read_text()))
        result=json.loads(done.stdout)
        self.assertEqual(result['runtime_exit_code'],done.returncode)
        self.assertEqual(result['schema_version'],2)
        self.assertTrue(result['checks']['canary']['proof_matches_expected'])
        self.assertTrue(result['checks']['canary']['read_candidate_observed'])
        self.assertEqual(result['terminal'],'turn.completed')
        self.assertGreater(result['usage']['input_tokens'],0)
        self.assertGreater(result['usage']['output_tokens'],0)
        self.assertIsInstance(result['diagnostics'],list)
        self.assertEqual((fixture.root/'work/result.txt').read_text(),fixture.token+'\n')
        self.assertEqual((fixture.root/'sinks/final.txt').read_text().strip(),'CANARY='+fixture.token)
        self.assertEqual(result['final_answer'].strip(),'CANARY='+fixture.token)
        trace=(fixture.root/'sinks/events.jsonl').read_text()
        self.assertIn('turn.completed',trace); self.assertIn(fixture.token,trace)
        self.assertTrue(result['session_id'])
        self.check_hops(fixture)
        return result

    def test_deepseek_native_read_write(self):
        f=self.fixture('deepseek','ds-flash'); self.check_success(f,f.run())
        source=json.loads((ROOT/'codex-agent/catalog-sources/ds-model-catalogs.json').read_text())['models'][0]
        def strings(value):
            if isinstance(value,str):yield value
            elif isinstance(value,list):
                for item in value:yield from strings(item)
            elif isinstance(value,dict):
                for item in value.values():yield from strings(item)
        rendered='\n'.join(strings(f.ingress()[0]['body']['input']))
        self.assertIn(source['base_instructions'].strip(),rendered)

    def test_kimi_native_logical_wire_separation(self):
        f=self.fixture('kimi','kimi'); self.check_success(f,f.run())
        self.assertEqual(f.ingress()[0]['body']['model'],'k3')

    def test_mimo_native_default_host_lite_read_write(self):
        f=self.fixture('mimo','mimo'); self.check_success(f,f.run())
        self.assertIn('You are MiMo, an AI assistant developed by Xiaomi.',json.dumps(f.ingress()[0]['body']['input'],ensure_ascii=False))

    def test_qwen_native_persisted_context(self):
        f=self.fixture('qwen','qwen'); done=f.run(); result=json.loads(done.stdout)
        matches=list((f.root/'home/.codex/sessions').rglob('*'+result['session_id']+'*.jsonl'))
        self.assertEqual(len(matches),1)
        events=[(n,json.loads(line)) for n,line in enumerate(matches[0].read_text().splitlines(),1)]
        context=[(n,d) for n,d in events if d.get('type')=='turn_context']
        counts=[(n,d) for n,d in events if d.get('type')=='event_msg' and d['payload'].get('type')=='token_count']
        self.assertTrue(any(d['payload']['model']=='qwen3.8-max' and d['payload']['effort']=='max' for n,d in context))
        self.assertTrue(any(d['payload']['info']['model_context_window']==934435 for n,d in counts))
        (f.root/'context-evidence.json').write_text(json.dumps(dict(rollout=str(matches[0]),turn_context=context,token_count=counts),indent=2))
        self.check_success(f,done)

    def test_mimo_explicit_host_false_reports_observed_native_outcome(self):
        f=self.fixture('mimo-host-false','mimo',host_false=True); done=f.run()
        result=json.loads(done.stdout)
        self.assertEqual(done.returncode,result['runtime_exit_code'])
        self.assertEqual(result['schema_version'],2)
        self.assertFalse((f.root/'work/result.txt').exists())
        combined=(f.root/'sinks/events.jsonl').read_text()+(f.root/'sinks/native.stderr').read_text()+done.stdout
        self.assertRegex(combined,r'(?i)(host|code.mode).*(disabled|unavailable|not enabled|requires|not available|failed)')
        self.check_hops(f)
        self.assertEqual(result['logs']['output'],str(f.root/'sinks/events.jsonl'))
        self.assertIn('final_answer',result)

    def approval_case(self,profile,outcome):
        f=self.fixture(profile+'-'+outcome,profile,approval=outcome); done=f.run()
        self.assertEqual(done.returncode,0,(str(f.root),done.stdout,done.stderr))
        result=json.loads(done.stdout); self.assertEqual(result['runtime_exit_code'],done.returncode)
        self.assertGreater(f.guardian_requests,0)
        self.assertEqual((f.root/'approval-result').exists(),outcome=='allow')
        if outcome=='allow':self.assertEqual((f.root/'approval-result').read_text(),'synthetic-approved')
        if outcome!='error':self.assertEqual(json.loads((f.root/'guardian-verdict.json').read_text())['outcome'],outcome)
        ingress=self.check_hops(f)
        guardian=[r for r in ingress if r['body']['model']=='codex-auto-review']
        self.assertTrue(guardian)
        if profile=='mimo':
            for before,after in zip(ingress,f.requests):
                if before['body']['model']=='codex-auto-review':
                    self.assertEqual(before['body']['text']['format']['type'],'json_schema')
                    self.assertEqual(after['body']['text']['format']['type'],'json_object')

    def test_direct_guardian_allow(self):self.approval_case('ds-flash','allow')
    def test_direct_guardian_deny(self):self.approval_case('ds-flash','deny')
    def test_lite_guardian_allow(self):self.approval_case('mimo','allow')
    def test_lite_guardian_deny(self):self.approval_case('mimo','deny')
    def test_guardian_http_error_fail_closed(self):self.approval_case('ds-flash','error')

    @unittest.skipUnless(platform.system()=='Darwin' and os.environ.get('AGENT_SANDBOX_KERNEL_TESTS')=='1','explicit macOS kernel-test opt-in')
    def test_mimo_code_host_outer_kernel_boundary(self):
        f=self.fixture('mimo-kernel','mimo',kernel=True); self.check_success(f,f.run(),clean=False)
        wrapper=(f.root/'runner.stderr').read_text()
        state_match=re.search(r'agent-sandbox: state=(.+)',wrapper)
        self.assertIsNotNone(state_match,wrapper)
        state=Path(state_match[1]).resolve()
        self.assertTrue(state.is_relative_to(f.root/'tmp'))
        settings=json.loads((state/'srt.json').read_text())
        isolated=tomllib.loads((state/'codex/config.toml').read_text())
        self.assertFalse(isolated['features']['code_mode'])
        self.assertNotIn('code_mode_host',isolated['features'])
        self.assertEqual(isolated['approval_policy'],'never')
        selected=tomllib.loads((f.root/'home/.codex/config.toml').read_text())['model_providers']['mimo']['base_url']
        port=urlsplit(selected).port
        self.assertEqual(settings['network'],dict(allowedDomains=[f'127.0.0.1:{port}'],deniedDomains=[],
                         strictAllowlist=True,allowLocalBinding=False,allowAllUnixSockets=False,allowUnixSockets=[]))
        for key in ('allowAppleEvents','enableWeakerNestedSandbox','enableWeakerNetworkIsolation'):
            self.assertFalse(settings[key])
        filesystem=settings['filesystem']
        self.assertEqual(filesystem['allowRead'],[])
        for path in ('sinks/events.jsonl','sinks/native.stderr','sinks/final.txt'):
            self.assertIn(dict(path=str(f.root/path),literal=True),filesystem['allowWrite'])
        self.assertNotIn(str(f.root/'sinks'),[x.get('path') for x in filesystem['allowWrite']])
        protected=[x.get('path') for x in filesystem['denyWrite'] if isinstance(x,dict)]
        self.assertTrue(any(path.endswith('/config.toml') for path in protected))
        self.assertTrue(any(path.endswith('/rules') for path in protected))
        self.assertTrue(any(path.endswith('/.git') for path in protected))
        (f.root/'outer-settings-evidence.json').write_text(json.dumps(dict(state=str(state),settings=settings),indent=2))
        wire=(f.root/'upstream.jsonl').read_text(); trace=(f.root/'sinks/events.jsonl').read_text()
        self.assertNotIn('FORBIDDEN_OFFICIAL_SYNTHETIC_SECRET',wire+trace+(f.root/'sinks/final.txt').read_text()+(f.root/'ingress.jsonl').read_text()+(f.root/'sinks/native.stderr').read_text())
        for path in ('outside-write','work/.git/protected-write'):self.assertFalse((f.root/path).exists())
        self.assertFalse((f.root/'unlisted.jsonl').exists())
        self.assertIn('Operation not permitted',wire)


if __name__=='__main__':
    if sys.argv[1:2]==['--fixture-shim']:fixture_shim(Path(sys.argv[2]))
    else:unittest.main()
