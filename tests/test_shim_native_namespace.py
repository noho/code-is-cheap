"""Native namespace contracts, captured-call replay and real loopback service I/O."""
import copy
import ast
import hashlib
from contextlib import contextmanager, redirect_stderr
from email.message import Message
import gzip
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'docs/gateflow/shim-subagent-all-providers/evidence'
loader = importlib.machinery.SourceFileLoader('namespace_shim', str(ROOT/'codex-agent/bin/codex-auto-review-shim'))
spec = importlib.util.spec_from_loader(loader.name, loader)
shim = importlib.util.module_from_spec(spec); loader.exec_module(shim)


def enc(doc):
    return json.dumps(doc, ensure_ascii=False).encode()


def group(ns='multi_agent_v1', name='spawn_agent'):
    return {'type':'namespace','name':ns,'description':'原生 🧪','tools':[{'type':'function','name':name,'parameters':{'type':'object'},'strict':False,'description':'child','extension':{'name':'opaque'}}]}


def request(ns='multi_agent_v1', name='spawn_agent'):
    return {'model':'test','tools':[group(ns,name)],'input':[], 'stream':True}


def event(item=None, typ='response.output_item.added'):
    return b'data: '+enc({'type':typ,'item':item or {'type':'function_call','name':'spawn_agent','arguments':'{}','call_id':'c','id':'i','status':'in_progress'}})+b'\n\n'


def replay(data, mapping, size=65536):
    stream = io.BytesIO(data)
    return list(shim.native_sse_events(lambda n:stream.read(min(size,n)),mapping))


@contextmanager
def service(action, flatten=True, restore=True):
    seen=[]
    class Upstream(BaseHTTPRequestHandler):
        protocol_version='HTTP/1.1'
        def log_message(self,*args): pass
        def do_POST(self):
            seen.append((self.path, self.headers, self.rfile.read(int(self.headers.get('Content-Length') or 0))))
            action(self, seen[-1][2], len(seen))
        do_GET = do_POST
    upstream=ThreadingHTTPServer(('127.0.0.1',0),Upstream)
    candidate=shim._make_server({'listen':'127.0.0.1:0','upstream':f'http://127.0.0.1:{upstream.server_port}', 'port':0,'from':'codex-auto-review','to':'test','native_agent_request_flatten':flatten,'native_agent_response_restore':restore})
    threads=[threading.Thread(target=s.serve_forever) for s in (upstream,candidate)]
    for t in threads:t.start()
    try:
        yield candidate.server_port,seen
    finally:
        for s in (candidate,upstream):s.shutdown();s.server_close()
        for t in threads:t.join()


def reply(h, data, media='text/event-stream', encoding=None, status=200, extra=()):
    h.send_response(status); h.send_header('Content-Type',media)
    if encoding is not None:h.send_header('Content-Encoding',encoding)
    h.send_header('Content-Length',str(len(data)))
    for k,v in extra:h.send_header(k,v)
    h.end_headers();h.wfile.write(data);h.wfile.flush()


def call(port, doc, encoding=''):
    data=enc(doc);data={'gzip':gzip.compress,'deflate':zlib.compress}.get(encoding,lambda x:x)(data)
    conn=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
    conn.request('POST','/v1/responses',data,{'Content-Type':'application/json','Content-Encoding':encoding})
    response=conn.getresponse();body=response.read();status=response.status;headers=dict(response.getheaders());conn.close()
    return status,headers,body


class RequestContracts(unittest.TestCase):
    def test_actual_descriptors_native_only_history_and_schema_preservation(self):
        for profile, attempt, ns in [('kimi','attempt-1','multi_agent_v1'),('mimo-flash','scenario-a-attempt-1','collaboration')]:
            wire=json.loads((EVIDENCE/profile/attempt/'wire.json').read_text())
            native=next(t for w in wire for t in w['native_descriptors'] if t.get('name')==ns)
            doc=request(); doc['tools']=[{'type':'namespace','name':'mcp','future':True,'tools':[{'type':'function','name':'x'}]},native,{'type':'namespace','name':'functions','tools':[{'type':'custom','name':'exec','format':{'type':'text'}}]}]
            doc['input']=[{'type':'function_call','namespace':ns,'name':'spawn_agent','arguments':'{"do":"not rewrite"}'},{'type':'additional_tools','tools':[group('unrelated','other')]}]
            raw=enc(doc);out,m=shim.native_agent_request(raw,profile=='kimi');fixed=json.loads(out)
            self.assertEqual(dict(m),{c['name']:ns for c in native['tools']})
            with self.assertRaises(TypeError):m['x']='y'
            self.assertEqual(fixed['input'],doc['input']);self.assertEqual(fixed['tools'][0],doc['tools'][0]);self.assertEqual(fixed['tools'][-1],doc['tools'][-1])
            if profile=='mimo-flash':self.assertEqual(out,raw)
            else:
                for b,a in zip(native['tools'],fixed['tools'][1:-1]):
                    self.assertEqual({k:v for k,v in a.items() if k!='description'},{k:v for k,v in b.items() if k!='description'})
                    self.assertEqual(a['description'],f'Namespace {ns}: '+native.get('description','')+'\n\n'+b.get('description',''))

    def test_no_group_original_bytes_and_unrelated_duplicates(self):
        raw=b'{ "tools": [{"type":"namespace","name":"mcp","tools":[]}], "input": [] }'
        out,m=shim.native_agent_request(raw,True);self.assertEqual(out,raw);self.assertFalse(m)
        doc=request();doc['tools'] += [group('mcp','exec'),group('functions','exec'),group('spawn_agent','unrelated'),{'type':'future'},{'type':'future','name':'different'}]
        doc['tools'][0]['tools'][0]['parameters']={'properties':{'spawn_agent':{'name':'spawn_agent'}}}
        shim.native_agent_request(enc(doc),True)

    def test_scoped_collisions_all_known_declarations(self):
        for extra in [group('collaboration'),group('mcp'),{'type':'function','name':'spawn_agent'},{'type':'custom','name':'spawn_agent'},{'type':'future','name':'spawn_agent'}]:
            for additional in (False,True):
                doc=request()
                if additional:doc['input']=[{'type':'additional_tools','tools':[extra]}]
                else:doc['tools'].append(extra)
                with self.subTest(extra=extra,additional=additional),self.assertRaisesRegex(ValueError,'^Invalid native agent protocol$'):shim.native_agent_request(enc(doc),True)

    def test_selected_structure_and_choices(self):
        for mutate in [lambda d:d['tools'][0].update(future='SECRET'),lambda d:d['tools'][0].update(tools=[{'type':'custom','name':'spawn_agent'}]),lambda d:d['tools'][0].update(description=1),lambda d:d['tools'][0]['tools'].append(copy.deepcopy(d['tools'][0]['tools'][0]))]:
            doc=request();mutate(doc)
            with self.assertRaises(shim.NativeProtocolError):shim.native_agent_request(enc(doc),True)
        doc=request();doc['tools'][0]['future']=True
        self.assertEqual(shim.native_agent_request(enc(doc),False)[0],enc(doc))
        for choice in ({'type':'function','name':'spawn_agent'},{'type':'function','namespace':'multi_agent_v1','name':'spawn_agent'}):
            doc=request();doc['tool_choice']=choice
            with self.assertRaises(shim.NativeProtocolError):shim.native_agent_request(enc(doc),True)
            self.assertEqual(shim.native_agent_request(enc(doc),False)[0],enc(doc))
        for choice in (None,'auto','none','required',{'type':'function','namespace':'unrelated','name':'different'}):
            doc=request();doc['tool_choice']=choice
            self.assertEqual(json.loads(shim.native_agent_request(enc(doc),True)[0])['tool_choice'],choice)

    def test_loader_flags_defaults_and_invalid_combination(self):
        for flags in ({},{'native_agent_response_restore':True},{'native_agent_response_restore':True,'native_agent_request_flatten':True},{'native_agent_request_flatten':True}):
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'routes';p.write_text(json.dumps({'native_agent_response_restore':True,'native_agent_request_flatten':True,'routes':[{'port':1,'upstream':'http://test','to':'test',**flags}]}))
                with patch.dict(os.environ,{'SHIM_ROUTES':str(p)}):
                    if flags=={'native_agent_request_flatten':True}:
                        with self.assertRaises(SystemExit):shim.load_routes()
                    else:
                        route=shim.load_routes()[0]
                        for k in ('native_agent_request_flatten','native_agent_response_restore'):self.assertEqual(route[k],flags.get(k,False))
        routes=json.loads((ROOT/'codex-agent/shim-routes.json').read_text())['routes']
        self.assertEqual({r['endpoint_id'] for r in routes if r['native_agent_request_flatten']},{'kimi'})
        self.assertEqual({r['endpoint_id'] for r in routes if r['native_agent_response_restore']},{'kimi','mimo-flash'})
        self.assertTrue(all(r['agent_message_fix'] for r in routes))


class ResponseContracts(unittest.TestCase):
    def test_captured_kimi_spawn_and_mimo_wait_field_invariants(self):
        capture=json.loads((EVIDENCE/'kimi-namespace-diagnostic/attempt-1/response-native-calls.json').read_text())
        raw_items=[json.loads(raw[6:])['item'] for r in capture for raw in r['raw_function_call_sse']]
        rollout=json.loads((EVIDENCE/'mimo-flash/scenario-a-attempt-1/rollouts-sanitized.json').read_text())
        raw_items += [e['item'] for r in rollout for e in r['events'] if e.get('item',{}).get('name')=='wait_agent' and e['item'].get('namespace') is None]
        self.assertGreaterEqual(len(raw_items),3)
        for item in raw_items:
            ns='collaboration' if item['name']=='wait_agent' else 'multi_agent_v1';mapping={item['name']:ns}
            for namespace in ('absent',None,ns):
                original=copy.deepcopy(item)
                if namespace!='absent':original['namespace']=namespace
                for typ in ('response.output_item.added','response.output_item.done','response.completed','json'):
                    doc=({'output':[original]} if typ=='json' else {'type':typ,'response':{'output':[original]}} if typ=='response.completed' else {'type':typ,'item':original})
                    out,n=shim.restore_native_response(enc(doc),mapping,typ!='json')
                    expected=copy.deepcopy(doc);target=expected['output'][0] if typ=='json' else expected['response']['output'][0] if typ=='response.completed' else expected['item'];target['namespace']=ns
                    self.assertEqual(json.loads(out),expected);self.assertEqual(n,0 if namespace==ns else 1)
            for conflict in ('','functions','other',False):
                with self.assertRaises(shim.NativeProtocolError):shim.restore_native_response(enc({'output':[{**item,'namespace':conflict}]}),mapping)

    def test_sse_arbitrary_chunks_utf8_crlf_multidata_interleave_raw_passthrough(self):
        raw=b': comment\r\n\r\nevent: delta\r\ndata: {"type":"response.function_call_arguments.delta","delta":"'+ '中文 🧪'.encode()+b'"}\r\n\r\n'
        raw+=b'event: added\r\nid: 1\r\ndata: {"type":"response.output_item.added",\r\ndata: "item":{"type":"function_call","name":"spawn_agent","arguments":"{}"}}\r\n\r\n'
        raw+=b'data: {"type":"response.output_item.done","item":{"type":"custom_tool_call","name":"spawn_agent"}}\n\n'+event({'type':'function_call','name':'other'})+b'data: [DONE]\n\n'
        expected=replay(raw,{'spawn_agent':'multi_agent_v1'})
        for size in (1,2,3,7,31,65536):self.assertEqual(replay(raw,{'spawn_agent':'multi_agent_v1'},size),expected)
        self.assertEqual(sum(n for _,n in expected),1)
        self.assertEqual(expected[0][0],b': comment\r\n\r\n');self.assertIn(b'id: 1\r\n',expected[2][0])
        noop=raw.replace(b'"name":"spawn_agent"',b'"name":"unknown"')
        self.assertEqual(b''.join(c for c,n in replay(noop,{'spawn_agent':'multi_agent_v1'},1)),noop)
        self.assertEqual(replay(b': lone CR\r\r',{}),[(b': lone CR\r\r',0)])

    def test_malformed_truncated_utf8_conflict_and_event_bound(self):
        for raw in (b'data: nope\n\n',b'data: {}\n',b'data: {"x":"\xff"}\n\n',event({'type':'function_call','name':'spawn_agent','namespace':'wrong'})):
            with self.assertRaises(shim.NativeProtocolError):replay(raw,{'spawn_agent':'multi_agent_v1'},1)
        with self.assertRaises(shim.NativeProtocolError):replay(b':'+b'x'*shim.NATIVE_RESPONSE_LIMIT,{},65536)
        # Total stream exceeds cap, with bounded individual events.
        raw=(b':'+b'x'*65536+b'\n\n')*130
        self.assertGreater(len(raw),shim.NATIVE_RESPONSE_LIMIT)
        self.assertEqual(b''.join(c for c,n in replay(raw,{})),raw)
        upstream_error=b'data: {"type":"error","error":{"code":"upstream"}}\n\n'
        self.assertEqual(replay(upstream_error,{}),[(upstream_error,0)])


class ServiceContracts(unittest.TestCase):
    def test_first_event_read1_before_eof_and_midstream_conflict_no_fabrication(self):
        first=event();conflict=event({'type':'function_call','name':'spawn_agent','namespace':'SECRET'})
        blocked,release=threading.Event(),threading.Event()
        def action(h,body,n):
            h.send_response(200);h.send_header('Content-Type','text/event-stream');h.send_header('Connection','close');h.end_headers()
            h.wfile.write(first);h.wfile.flush();blocked.set();release.wait(5)
            h.wfile.write(conflict);h.wfile.flush();h.close_connection=True
        with service(action) as (port,seen):
            conn=http.client.HTTPConnection('127.0.0.1',port,timeout=3)
            try:
                conn.request('POST','/responses',enc(request()))
                self.assertTrue(blocked.wait(2));resp=conn.getresponse();part=resp.read1(65536)
                self.assertFalse(release.is_set());self.assertIn(b'"namespace": "multi_agent_v1"',part)
                release.set();rest=resp.read();self.assertEqual(rest,b'');self.assertNotIn(b'HTTP/1.1 400',part);self.assertEqual(len(seen),1)
            finally:release.set();conn.close()

    def test_concurrent_same_bare_name_distinct_native_maps(self):
        barrier=threading.Barrier(2)
        def action(h,body,n):barrier.wait(3);reply(h,event())
        with service(action,flatten=False) as (port,seen):
            results={}
            def run(ns):results[ns]=call(port,request(ns))[2]
            ts=[threading.Thread(target=run,args=(ns,)) for ns in ('collaboration','multi_agent_v1')]
            for t in ts:t.start()
            for t in ts:t.join()
            for ns,data in results.items():self.assertEqual(json.loads(data[6:])['item']['namespace'],ns)
            self.assertEqual(len(results),2)

    def test_success_encoding_media_rejected_before_headers_and_empty_map_bypass(self):
        for encoding in ('gzip','deflate','br','identity, gzip'):
            with service(lambda h,b,n:reply(h,b'compressed',encoding=encoding)) as (port,seen):
                status,headers,body=call(port,request());self.assertEqual(status,502);self.assertNotIn('Content-Encoding',headers);self.assertNotIn(b'compressed',body)
                doc=request();doc['tools']=[]
                self.assertEqual(call(port,doc)[2],b'compressed')
            with service(lambda h,b,n:reply(h,b'compressed',encoding=encoding),flatten=False,restore=False) as (port,seen):self.assertEqual(call(port,request())[2],b'compressed')
        for media in ('text/plain','application/octet-stream'):
            with service(lambda h,b,n:reply(h,event(),media=media)) as (port,seen):self.assertEqual(call(port,request())[0],502)

    def test_json_headers_compression_and_non2xx_preservation(self):
        payload=enc({'output':[{'type':'function_call','name':'spawn_agent','arguments':'  {"x":1}  ','id':'x','call_id':'y','status':'completed'}]})
        for encoding in ('','gzip','deflate'):
            with service(lambda h,b,n:reply(h,payload,'application/json','identity',extra=[('Keep-Alive','timeout=1'),('X-Kept','yes')])) as (port,seen):
                status,headers,out=call(port,request(),encoding);self.assertEqual(status,200);self.assertNotIn('Content-Length',headers);self.assertNotIn('Keep-Alive',headers);self.assertEqual(headers['X-Kept'],'yes')
                self.assertEqual(json.loads(out),{ 'output':[{**json.loads(payload)['output'][0],'namespace':'multi_agent_v1'}]})
                sent={'gzip':gzip.decompress,'deflate':zlib.decompress}.get(encoding,lambda x:x)(seen[0][2]);self.assertEqual(json.loads(sent)['tools'][0]['name'],'spawn_agent')
        with tempfile.TemporaryDirectory() as tmp,patch.object(shim,'FAILED_DIR',tmp):
            with service(lambda h,b,n:reply(h,b'{"error":"upstream"}','application/json','gzip',status=429)) as (port,seen):
                status,headers,body=call(port,request());self.assertEqual(status,429);self.assertEqual(body,b'{"error":"upstream"}');self.assertEqual(headers['Content-Encoding'],'gzip')

    def test_request_failures_zero_upstream_and_safe_error(self):
        for change in ('collision','metadata','choice'):
            doc=request()
            if change=='collision':doc['tools'].append({'type':'future','name':'spawn_agent','SECRET':'PRIVATE_URL'})
            elif change=='metadata':doc['tools'][0]['SECRET']='PRIVATE_URL'
            else:doc['tool_choice']={'type':'function','name':'spawn_agent','namespace':'multi_agent_v1'}
            with service(lambda h,b,n:reply(h,event())) as (port,seen):
                status,headers,body=call(port,doc);self.assertEqual(status,400);self.assertFalse(seen);self.assertNotIn(b'SECRET',body);self.assertNotIn(b'PRIVATE_URL',body)

    def test_json_limit_and_first_event_errors_502_no_retry(self):
        for data,media in [(b'x'*(shim.NATIVE_RESPONSE_LIMIT+1),'application/json'),(b'data: nope\n\n','text/event-stream'),(b'data: {}\n','text/event-stream')]:
            with service(lambda h,b,n:reply(h,data,media)) as (port,seen):
                self.assertEqual(call(port,request())[0],502);self.assertEqual(len(seen),1)

    def test_guardian_bypass_original_buffer_and_retry_unchanged(self):
        incomplete=b'data: {"type":"response.created"}\n\n';complete=b'data: {"type":"response.completed"}\n\n'
        with service(lambda h,b,n:reply(h,incomplete if n<3 else complete,encoding='gzip')) as (port,seen):
            doc=request();doc['model']='codex-auto-review';doc['tools'][0]['unsupported']='bypass'
            status,headers,out=call(port,doc);self.assertEqual(status,200);self.assertEqual(out,complete);self.assertEqual(headers['Content-Encoding'],'gzip');self.assertEqual(len(seen),3)
            self.assertTrue(all(json.loads(b)['tools']==doc['tools'] for _,_,b in seen))



class LoggingContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        baseline = 'a6246a4bc810125437992791aedcc8f2aa4c072f55e2bcf3691562feecd8e1e6'
        cls.source = gzip.decompress((EVIDENCE/'mimo-flash/namespace-scenario-a-attempt-4'/
                                     (baseline+'.source.gz')).read_bytes())
        assert hashlib.sha256(cls.source).hexdigest() == baseline
        cls.tmp = tempfile.TemporaryDirectory()
        path = Path(cls.tmp.name)/'baseline.py'; path.write_bytes(cls.source)
        loader = importlib.machinery.SourceFileLoader('logging_baseline_shim',str(path))
        spec = importlib.util.spec_from_loader(loader.name,loader)
        cls.baseline = importlib.util.module_from_spec(spec); loader.exec_module(cls.baseline)
        cls.addClassCleanup(cls.tmp.cleanup)

    @staticmethod
    def without_request_diagnostics(handler):
        """Compare control flow after removing only the existing standard log block."""
        handler = copy.deepcopy(handler)
        handler.body = [n for n in handler.body if getattr(n,'name',None) != '_summary']
        method = next(n for n in handler.body if getattr(n,'name',None) == '_handle')
        method.body = [n for n in method.body if not (
            isinstance(n,ast.Assign) and any(
                isinstance(t,ast.Name) and t.id == 'warn' or
                isinstance(t,ast.Tuple) and [getattr(e,'id',None) for e in t.elts] == ['model','tools']
                for t in n.targets) or
            isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and
            isinstance(n.value.func,ast.Attribute) and n.value.func.attr == '_log' and
            any(isinstance(v,ast.Constant) and isinstance(v.value,str) and 'rewrite=' in v.value
                for v in ast.walk(n)))]
        return ast.dump(handler)

    def test_a4_baseline_all_nonlogging_source_semantics_unchanged(self):
        old, new = (ast.parse(source) for source in
                    (self.source,(ROOT/'codex-agent/bin/codex-auto-review-shim').read_bytes()))
        old_handler, new_handler = (next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Handler')
                                    for tree in (old,new))
        self.assertEqual(self.without_request_diagnostics(old_handler),
                         self.without_request_diagnostics(new_handler))
        old.body.remove(old_handler); new.body.remove(new_handler)
        self.assertEqual(ast.dump(old),ast.dump(new))

    def test_active_sse_and_json_standard_logs_private_payload_and_byte_equivalence(self):
        current = shim
        private = ('PROMPT_OFFLINE_PRIVATE','ARGS_OFFLINE_PRIVATE','HEADER_OFFLINE_PRIVATE',
                   'SESSION_OFFLINE_PRIVATE','https://offline.invalid/private')
        item = {'type':'function_call','name':'spawn_agent','arguments':private[1],'id':'i','call_id':'c'}
        for flatten in (True,False):
            doc = request() if flatten else {'model':'test','input':[{'type':'additional_tools','tools':[group('collaboration')]}]}
            doc['input'].append({'type':'message','role':'user','content':private[0]+private[4]})
            doc['client_metadata'] = {'thread_id':private[3]}
            for media in ('text/event-stream','application/json'):
                for encoding in ('','gzip','deflate'):
                    with self.subTest(flatten=flatten,media=media,encoding=encoding):
                        data = event(item) if media=='text/event-stream' else enc({'output':[item]})
                        results=[]
                        for module in (self.baseline,current):
                            logs=io.StringIO()
                            def action(h,b,n):
                                reply(h,data,media,'identity',extra=(('X-Offline',private[2]),))
                            with patch(__name__+'.shim',module),redirect_stderr(logs):
                                with service(action,flatten=flatten) as (port,seen):
                                    status,headers,body=call(port,doc,encoding)
                            decoder={'gzip':gzip.decompress,'deflate':zlib.decompress}.get(encoding,lambda b:b)
                            results.append((status,{k:v for k,v in headers.items() if k not in ('Server','Date')},
                                            body,seen[0][0],decoder(seen[0][2])))
                            if module is current:
                                lines=logs.getvalue().splitlines()
                                standard=[line for line in lines if 'rewrite=' in line]
                                self.assertEqual(len(standard),1,lines)
                                self.assertIn('POST /v1/responses -> 200 model=test enc='+
                                              (encoding or '-')+' rewrite=none tools=',standard[0])
                                self.assertIn('tools=[spawn_agent]' if flatten else 'tools=none',standard[0])
                                self.assertTrue(any('native response: restored=1 relayed=' in line for line in lines))
                                for secret in private:self.assertNotIn(secret,logs.getvalue())
                        self.assertEqual(results[0],results[1])
                        self.assertEqual(results[1][0],200)
                        self.assertNotIn('Content-Length',results[1][1])

    def test_response_only_non_array_top_tools_still_restores_and_logs(self):
        for top in ('absent',None,{},42,True,'TOOLS_OFFLINE_PRIVATE',{'secret':'TOOLS_OFFLINE_PRIVATE'}):
            with self.subTest(top=top):
                doc={'model':'test','input':[{'type':'additional_tools','tools':[group('collaboration')]}]}
                if top!='absent':doc['tools']=top
                logs=io.StringIO()
                with redirect_stderr(logs),service(lambda h,b,n:reply(h,event()),flatten=False) as (port,seen):
                    status,headers,body=call(port,doc)
                self.assertEqual(status,200);self.assertEqual(seen[0][2],enc(doc))
                self.assertEqual(json.loads(body[6:])['item']['namespace'],'collaboration')
                self.assertEqual(sum('rewrite=' in line for line in logs.getvalue().splitlines()),1)
                self.assertIn('-> 200 model=test enc=- rewrite=none tools=none',logs.getvalue())
                self.assertNotIn('TOOLS_OFFLINE_PRIVATE',logs.getvalue())

    def test_active_route_auth_and_model_rewrite_match_a4_baseline(self):
        current=shim
        for flatten in (True,False):
            results=[]
            for module in (self.baseline,current):
                original=module._make_server;logs=io.StringIO()
                with patch.object(module,'endpoint_module') as endpoint:
                    def make_server(route):
                        endpoint.return_value.connection.return_value={
                            'base_url':route['upstream'],'upstream_model':'offline/model',
                            'api_key':'KEY_OFFLINE_PRIVATE'}
                        return original({**route,'endpoint_id':'offline','request_prefix':'/offline'})
                    with patch(__name__+'.shim',module),patch.object(module,'_make_server',make_server),redirect_stderr(logs):
                        with service(lambda h,b,n:reply(h,event()),flatten=flatten) as (port,seen):
                            doc=request() if flatten else {'model':'test','input':[{'type':'additional_tools','tools':[group('collaboration')]}]}
                            conn=http.client.HTTPConnection('127.0.0.1',port,timeout=3)
                            try:
                                conn.request('POST','/offline/responses',gzip.compress(enc(doc)),
                                    {'Content-Encoding':'gzip','Authorization':'Bearer CLIENT_OFFLINE_PRIVATE',
                                     'X-Api-Key':'CLIENT_OFFLINE_PRIVATE','Api-Key':'CLIENT_OFFLINE_PRIVATE'})
                                response=conn.getresponse();body=response.read()
                                results.append((response.status,body,
                                    {k:v for k,v in response.getheaders() if k not in ('Server','Date')},
                                    seen[0][0],gzip.decompress(seen[0][2])))
                            finally:conn.close()
                            endpoint.return_value.connection.assert_called_once_with('offline','codex',require_key=True)
                            self.assertEqual(seen[0][1]['Authorization'],'Bearer KEY_OFFLINE_PRIVATE')
                            self.assertIsNone(seen[0][1].get('X-Api-Key'));self.assertIsNone(seen[0][1].get('Api-Key'))
                if module is current:
                    self.assertIn('POST /offline/responses -> 200 model=offline/model enc=gzip rewrite=json tools=',logs.getvalue())
                    for secret in ('KEY_OFFLINE_PRIVATE','CLIENT_OFFLINE_PRIVATE','127.0.0.1:'):
                        self.assertNotIn(secret,logs.getvalue())
            self.assertEqual(results[0],results[1]);self.assertEqual(results[1][3],'/responses')
            self.assertEqual(json.loads(results[1][4])['model'],'offline/model')

    def test_both_active_paths_log_before_first_event_without_waiting_for_eof(self):
        current=shim
        for flatten in (True,False):
            results=[]
            for module in (self.baseline,current):
                started,release=threading.Event(),threading.Event();logs=io.StringIO()
                last=b'data: {"type":"response.completed","response":{"output":[]}}\n\n'
                def action(h,b,n):
                    h.send_response(200);h.send_header('Content-Type','text/event-stream')
                    h.send_header('Connection','close');h.end_headers()
                    h.wfile.write(event());h.wfile.flush();started.set();release.wait(5)
                    h.wfile.write(last);h.wfile.flush();h.close_connection=True
                with patch(__name__+'.shim',module),redirect_stderr(logs):
                    with service(action,flatten=flatten) as (port,seen):
                        conn=http.client.HTTPConnection('127.0.0.1',port,timeout=3)
                        try:
                            doc=request() if flatten else {'model':'test','input':[{'type':'additional_tools','tools':[group('collaboration')]}]}
                            conn.request('POST','/responses',enc(doc));self.assertTrue(started.wait(2))
                            response=conn.getresponse();first=response.read1(65536)
                            self.assertFalse(release.is_set());self.assertIn(b'"namespace":',first)
                            if module is current:
                                self.assertIn('POST /responses -> 200 model=test enc=- rewrite=none tools=',logs.getvalue())
                            release.set();rest=response.read()
                            results.append((response.status,{k:v for k,v in response.getheaders() if k not in ('Server','Date')},first,rest,seen[0][2]))
                        finally:release.set();conn.close()
            self.assertEqual(results[0],results[1])


class ObserverAuditContracts(unittest.TestCase):
    def test_actual_handler_observers_and_independent_auditor_mutations(self):
        def load_script(name,file):
            spec=importlib.util.spec_from_file_location(name,file);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
        probe=load_script('observer_probe',ROOT/'docs/gateflow/shim-subagent-delivery/native-probe.py')
        auditor=load_script('observer_audit',ROOT/'docs/gateflow/shim-subagent-delivery/audit-native-evidence.py')
        module=probe.load('observed_namespace_shim',ROOT/'codex-agent/bin/codex-auto-review-shim')
        route={'to':'test','native_agent_request_flatten':True,'native_agent_response_restore':True,'agent_message_fix':True,'id_fix':False,'json_fmt_fix':False,'drop_tools_item':False}
        wire,lock,local=probe.install_observers(module,route)
        original=module._make_server
        def make_server(r):return original({**r,**route})
        with patch(__name__+'.shim',module),patch.object(module,'_make_server',make_server):
            with service(lambda h,b,n:reply(h,event()+b'data: {"type":"response.completed","response":{"output":[]}}\n\n')) as (port,seen):
                doc=request();doc['client_metadata']={'thread_id':'offline-observer'}
                status,headers,body=call(port,doc);self.assertEqual(status,200)
        self.assertEqual(len(wire),1);record=wire[0]
        self.assertEqual(record['native_request_stage']['after_sha256'],record['stages'][0]['before_sha256'])
        self.assertEqual(record['expected_outbound_sha256'],record['outbound_attempts'][0]['body_sha256'])
        self.assertEqual(record['outbound_attempts'][0]['namespace_added_count'],1)
        self.assertEqual(auditor.audit_namespace_record({'route':route},record),record['native_request_stage']['after_sha256'])
        for mutation in ('stage','encoding','fields','count','location','hash','non-target'):
            bad=copy.deepcopy(record)
            if mutation=='stage':del bad['native_request_stage']
            elif mutation=='encoding':bad['outbound_attempts'][0]['response_metadata']['Content-Encoding']=['gzip']
            elif mutation=='fields':bad['outbound_attempts'][0]['native_events'][0]['after_calls'][0]['arguments']='changed'
            elif mutation=='count':bad['outbound_attempts'][0]['namespace_added_count']=0
            elif mutation=='location':bad['descriptor_locations']=[]
            elif mutation=='hash':del bad['outbound_attempts'][0]['response_pre_sha256']
            else:bad['native_request_stage']['outside_tools_equal']=False
            with self.subTest(mutation=mutation),self.assertRaises((AssertionError,KeyError)):auditor.audit_namespace_record({'route':route},bad)

class ObserverPassthroughContracts(unittest.TestCase):
    @contextmanager
    def observed_service(self, action):
        path=ROOT/'docs/gateflow/shim-subagent-delivery/native-probe.py'
        spec=importlib.util.spec_from_file_location('passthrough_probe',path)
        probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
        module=probe.load('passthrough_shim',ROOT/'codex-agent/bin/codex-auto-review-shim')
        route={'to':'test','agent_message_fix':True,'native_agent_request_flatten':True,
               'native_agent_response_restore':True,'id_fix':True,'json_fmt_fix':True,'drop_tools_item':True}
        passthrough=[]
        wire,lock,local=probe.install_observers(module,route,passthrough)
        original=module._make_server
        def make_server(r):return original({**r,**route})
        # A serial server deliberately reuses one worker for all requests.
        with patch(__name__+'.shim',module),patch.object(module,'_make_server',make_server), \
                patch.object(module,'ThreadingHTTPServer',HTTPServer), \
                patch.object(module.Handler,'_dump'),patch.object(module.Handler,'_log'):
            with service(action) as (port,seen):
                yield port,seen,wire,passthrough,module

    def raw_call(self, port, method, body, encoding=''):
        conn=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
        try:
            conn.request(method,'/v1/responses?offline-query=omit',body,
                         {'Content-Type':'application/json','Content-Encoding':encoding,
                          'Authorization':'Bearer OFFLINE_TEST_ONLY'})
            response=conn.getresponse()
            return response.status,dict(response.getheaders()),response.read()
        finally:conn.close()

    def test_empty_non_json_and_non_object_requests_reach_upstream_with_minimal_metadata(self):
        received_methods=[];response=b'raw upstream response\x00\xff'
        def action(h,body,n):
            received_methods.append(h.command)
            reply(h,response,'application/octet-stream',extra=(('X-Offline','preserved'),))
        cases=[('GET',None,''),('POST',b'',''),('POST',b'not-json',''),
               ('POST',b'[]',''),('POST',b'null',''),('POST',b'123',''),
               ('POST',b'"text"',''),('POST',b'{}',''),('POST',b'\xff',''),
               ('POST',gzip.compress(b'not-json'),'gzip'),
               ('POST',zlib.compress(b'[]'),'deflate'),
               ('POST',b'undecodable','gzip'),('POST',b'opaque','unknown')]
        with self.observed_service(action) as (port,seen,wire,metadata,module):
            for method,body,encoding in cases:
                with self.subTest(method=method,body=body,encoding=encoding):
                    status,headers,out=self.raw_call(port,method,body,encoding)
                    self.assertEqual((status,out),(200,response))
                    self.assertEqual(headers['X-Offline'],'preserved')
                    self.assertEqual(seen[-1][0],'/v1/responses?offline-query=omit')
                    self.assertEqual(seen[-1][2],body or b'')
                    self.assertEqual(seen[-1][1]['Content-Encoding'],encoding)
                    self.assertEqual(seen[-1][1]['Authorization'],'Bearer OFFLINE_TEST_ONLY')
                    self.assertEqual(metadata[-1],{'method':method,'path':'/v1/responses',
                        'body_bytes':len(body or b''),'body_sha256':hashlib.sha256(body or b'').hexdigest(),
                        'model':None,'http_status':200,'error_class':None})
            self.assertEqual(wire,[])
            self.assertEqual(len(metadata),len(cases))
            self.assertEqual(received_methods,[case[0] for case in cases])

    def test_same_worker_native_post_then_get_does_not_mutate_previous_native_record(self):
        response=event()+b'data: {"type":"response.completed","response":{"output":[]}}\n\n'
        with self.observed_service(lambda h,b,n:reply(h,response)) as (port,seen,wire,metadata,module):
            doc=request();doc['client_metadata']={'thread_id':'offline-first'}
            self.assertEqual(call(port,doc)[0],200)
            first=copy.deepcopy(wire[0])
            for method,body in (('GET',None),('POST',b'not-json'),('POST',enc(request()))):
                status,headers,out=self.raw_call(port,method,body)
                self.assertEqual(status,200)
                # Missing observer identity must not disable production mapping.
                if body==enc(request()):self.assertIn(b'"namespace": "multi_agent_v1"',out)
                else:self.assertEqual(out,response)
                self.assertEqual(wire,[first])
            doc['client_metadata']['thread_id']='offline-second'
            self.assertEqual(call(port,doc)[0],200)
            self.assertEqual(len(wire),2);self.assertEqual(len(metadata),3)
            self.assertEqual(wire[0],first)
            self.assertEqual([w['thread_id'] for w in wire],['offline-first','offline-second'])
            for record in wire:
                self.assertEqual(len(record['outbound_attempts']),1)
                self.assertEqual(record['outbound_attempts'][0]['namespace_added_count'],1)

    def test_passthrough_http_error_is_returned_and_recorded_without_body_or_headers(self):
        response=b'upstream rejection'
        # Compare the original handler's error semantics, including its body.
        with patch.object(shim.Handler,'_dump'),patch.object(shim.Handler,'_log'):
            with service(lambda h,b,n:reply(h,response,'text/plain',status=429)) as (port,seen):
                baseline=self.raw_call(port,'POST',b'not-json')
        with self.observed_service(lambda h,b,n:reply(h,response,'text/plain',status=429)) as (port,seen,wire,metadata,module):
            status,headers,out=self.raw_call(port,'POST',b'not-json')
            self.assertEqual((status,out),(baseline[0],baseline[2]))
            self.assertEqual(len(seen),1);self.assertEqual(wire,[])
            self.assertEqual(metadata[0]['http_status'],429)
            self.assertEqual(metadata[0]['error_class'],'HTTPError')
            self.assertEqual(set(metadata[0]),{'method','path','body_bytes','body_sha256','model','http_status','error_class'})

    def test_untracked_json_still_uses_guardian_model_and_encoding_transforms(self):
        response=b'data: {"type":"response.completed","response":{"output":[]}}\n\n'
        doc={'model':'codex-auto-review','input':[{'type':'additional_tools','tools':[]},
            {'type':'message','id':'at_offline','role':'user','content':'offline'}],
            'text':{'format':{'type':'json_schema','schema':{'type':'object'}}}}
        body=gzip.compress(json.dumps(doc,separators=(',',':')).encode())
        with self.observed_service(lambda h,b,n:reply(h,response)) as (port,seen,wire,metadata,module):
            self.assertEqual(self.raw_call(port,'POST',body,'gzip')[2],response)
            forwarded=json.loads(gzip.decompress(seen[0][2]))
            self.assertEqual(forwarded,{'model':'test','input':[{'type':'message','id':'msg_offline','role':'user','content':'offline'}],
                'text':{'format':{'type':'json_object'}}})
            self.assertEqual(wire,[]);self.assertEqual(len(metadata),1)
            self.assertEqual(metadata[0]['body_sha256'],hashlib.sha256(seen[0][2]).hexdigest())

    def test_observed_passthrough_and_native_first_chunk_arrive_before_upstream_eof(self):
        for native in (False,True):
            with self.subTest(native=native):
                started,release=threading.Event(),threading.Event()
                first=event();last=b'data: {"type":"response.completed","response":{"output":[]}}\n\n'
                def action(h,body,n):
                    h.send_response(200);h.send_header('Content-Type','text/event-stream')
                    h.send_header('Connection','close');h.end_headers()
                    h.wfile.write(first);h.wfile.flush();started.set()
                    release.wait(5);h.wfile.write(last);h.wfile.flush();h.close_connection=True
                with self.observed_service(action) as (port,seen,wire,metadata,module):
                    conn=http.client.HTTPConnection('127.0.0.1',port,timeout=3)
                    try:
                        doc=request();doc['client_metadata']={'thread_id':'offline-stream'}
                        conn.request('POST' if native else 'GET','/responses',enc(doc) if native else None)
                        self.assertTrue(started.wait(2));response=conn.getresponse();chunk=response.read1(65536)
                        self.assertFalse(release.is_set())
                        if native:self.assertIn(b'"namespace": "multi_agent_v1"',chunk)
                        else:self.assertEqual(chunk,first)
                        release.set();rest=response.read();self.assertIn(b'response.completed',rest)
                    finally:release.set();conn.close()
                self.assertEqual(len(wire),int(native));self.assertEqual(len(metadata),int(not native))
                if native:
                    attempt=wire[0]['outbound_attempts'][0]
                    self.assertLess(attempt['downstream_first_body_at'],attempt['response_eof_at'])
                    self.assertEqual(attempt['response_post_sha256'],hashlib.sha256(chunk+rest).hexdigest())


class AdditionalServiceContracts(unittest.TestCase):
    def test_transfer_decoding_connection_tokens_and_legitimate_error_event(self):
        data=event()+b'data: {"type":"error","error":{"code":"upstream"}}\n\n'
        def action(h,body,n):
            h.send_response(200);h.send_header('Content-Type','text/event-stream');h.send_header('Transfer-Encoding','chunked');h.send_header('Connection','close, X-Remove');h.send_header('X-Remove','gone');h.send_header('Trailer','X-Final');h.end_headers()
            for start in range(0,len(data),7):
                part=data[start:start+7];h.wfile.write(format(len(part),'x').encode()+b'\r\n'+part+b'\r\n')
            h.wfile.write(b'0\r\nX-Final: end\r\n\r\n');h.wfile.flush();h.close_connection=True
        with service(action) as (port,seen):
            status,headers,out=call(port,request());self.assertEqual(status,200)
            for key in ('Transfer-Encoding','Trailer','X-Remove','Content-Length'):self.assertNotIn(key,headers)
            self.assertEqual(out,b''.join(part for part,n in replay(data,{'spawn_agent':'multi_agent_v1'})))
            self.assertEqual(len(seen),1)

    def test_guardian_waits_for_eof_flags_off_and_empty_map_bytes_equivalence(self):
        first=b'data: {"type":"response.created"}\n\n';last=b'data: {"type":"response.completed"}\n\n'
        started,release,received=threading.Event(),threading.Event(),threading.Event()
        def action(h,body,n):
            h.send_response(200);h.send_header('Content-Type','text/event-stream');h.send_header('Connection','close');h.end_headers()
            h.wfile.write(first);h.wfile.flush();started.set();release.wait(3);h.wfile.write(last);h.wfile.flush();h.close_connection=True
        with service(action) as (port,seen):
            results=[]
            def run():
                doc=request();doc['model']='codex-auto-review';results.append(call(port,doc));received.set()
            t=threading.Thread(target=run);t.start()
            try:self.assertTrue(started.wait(2));self.assertFalse(received.wait(.1))
            finally:release.set();t.join()
            self.assertEqual(results[0][2],first+last);self.assertEqual(len(seen),1)
        raw=b'  {"output": [{"type":"function_call","name":"unknown"}]}\n'
        for flatten,restore,doc in [(False,False,request()),(True,True,{'model':'test','input':[],'stream':True,'tools':[]})]:
            with service(lambda h,b,n:reply(h,raw,'application/json'),flatten,restore) as (port,seen):
                status,headers,out=call(port,doc);self.assertEqual(out,raw);self.assertEqual(seen[0][2],enc(doc))

class SevenRouteEquivalence(unittest.TestCase):
    def test_flags_off_success_request_and_response_match_saved_baseline(self):
        source=gzip.decompress((EVIDENCE/'namespace-baseline/cd8e9f218c5a65d65bceff6ffac8b723c075913dad7ca08d999941ee34544dda.gz').read_bytes())
        routes=json.loads((ROOT/'codex-agent/shim-routes.json').read_text())['routes']
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'baseline.py';path.write_bytes(source)
            loader=importlib.machinery.SourceFileLoader('saved_baseline_shim',str(path));spec=importlib.util.spec_from_loader(loader.name,loader);old=importlib.util.module_from_spec(spec);loader.exec_module(old)
            current=shim
            for route in routes:
                if route['endpoint_id'] in ('kimi','mimo-flash'):continue
                self.assertFalse(route['native_agent_request_flatten']);self.assertFalse(route['native_agent_response_restore'])
                for encoding in ('','gzip'):
                    results=[]
                    for module in (old,current):
                        original=module._make_server
                        def make_server(r):
                            return original({**r,**{k:route[k] for k in ('to','agent_message_fix','id_fix','json_fmt_fix','drop_tools_item')},'native_agent_request_flatten':False,'native_agent_response_restore':False})
                        with patch(__name__+'.shim',module),patch.object(module,'_make_server',make_server),patch.object(module,'FAILED_DIR',tmp):
                            data=event()+b'data: {"type":"response.completed","response":{"output":[]}}\n\n'
                            upstream_status=429 if encoding=='gzip' else 200
                            with service(lambda h,b,n:reply(h,data,encoding='gzip',status=upstream_status),False,False) as (port,seen):
                                doc=request();doc['model']=route['to'];doc['input']=[{'type':'agent_message','author':'/root','recipient':'/root/a','content':[{'type':'encrypted_content','encrypted_content':'TEST_ONLY'}]}]
                                status,headers,out=call(port,doc,encoding)
                                decoder={'gzip':gzip.decompress}.get(encoding,lambda b:b)
                                results.append((status,out,decoder(seen[0][2]),{k:v for k,v in headers.items() if k not in ('Server','Date')}))
                    self.assertEqual(results[0],results[1],route['endpoint_id'])



class LiteLocationContracts(unittest.TestCase):
    def lite(self, ns='collaboration', name='spawn_agent'):
        return {'model':'test','input':[{'type':'additional_tools','tools':[group(ns,name)]}], 'stream':True}

    def test_all_23_actual_parent_child_six_entry_maps_and_whitespace_identity(self):
        threads=set();count=0
        for scenario in ('a','b'):
            directory=EVIDENCE/'mimo-flash'/f'namespace-scenario-{scenario}-attempt-1'
            summary=json.loads((directory/'summary.json').read_text())
            for w in json.loads((directory/'wire.json').read_text()):
                threads.add(w['thread_id']);count+=1
                self.assertIsNone(w['native_request_stage']['before_tools'])
                self.assertEqual(len(w['descriptor_locations']),1)
                location=w['descriptor_locations'][0]
                self.assertEqual(location['path'],['input',0,'tools',2])
                native=location['descriptor'];doc=self.lite()
                doc['input'][0]['tools']=[{'type':'unknown'},group('functions','exec'),native]
                for top in ('absent',None,{},42,'invalid',[]):
                    candidate=copy.deepcopy(doc)
                    if top!='absent':candidate['tools']=top
                    raw=(' \n'+json.dumps(candidate,indent=3,ensure_ascii=False)+'\n  ').encode()
                    out,m=shim.native_agent_request(raw,False)
                    self.assertEqual(out,raw);self.assertEqual(len(m),6)
                    self.assertEqual(dict(m),{c['name']:'collaboration' for c in native['tools']})
                    self.assertIn('wait_agent',m);self.assertIn('spawn_agent',m)
        self.assertEqual(count,23);self.assertEqual(len(threads),4)

    def test_disjoint_sources_self_exclusion_and_exact_allowlist(self):
        doc=self.lite();doc['input'].insert(0,{'type':'message','tools':[group('collaboration','not_current')]})
        doc['tools']=[group('multi_agent_v1','wait')]
        doc['input'] += [{'type':'additional_tools','tools':[group('collaboration','send_message')]},
                         {'type':'future','content':{'type':'additional_tools','tools':[group('collaboration','nested')]}}]
        out,m=shim.native_agent_request(enc(doc),False)
        self.assertEqual(out,enc(doc));self.assertEqual(dict(m),{'wait':'multi_agent_v1','spawn_agent':'collaboration','send_message':'collaboration'})
        for items in (None,{},[{'type':'additional_tools','tools':None}],[{'type':'message','tools':[group()]}]):
            candidate={'input':items,'tools':'opaque'}
            self.assertEqual(shim.native_agent_request(enc(candidate),False),(enc(candidate),{}))
        doc=self.lite();doc['input'][0]['tools'] += [group('spawn_agent','other'),group('mcp','exec'),group('functions','exec'),{'type':'future'}, {'type':'future','name':'other'}]
        self.assertEqual(shim.native_agent_request(enc(doc),False)[0],enc(doc))

    def test_combined_source_collision_and_duplicates_zero_upstream(self):
        cases=[]
        for extra in (group(),group('collaboration'),group('mcp'),{'type':'function','name':'spawn_agent'},
                      {'type':'future','name':'spawn_agent'},{'type':'custom','name':'spawn_agent'}):
            for container in ('top','same','other'):
                doc=self.lite()
                if container=='top':doc['tools']=[extra]
                elif container=='same':doc['input'][0]['tools'].append(extra)
                else:doc['input'].append({'type':'additional_tools','tools':[extra]})
                cases.append(doc)
        bad=self.lite();bad['input'][0]['tools'][0]['tools'].append(copy.deepcopy(bad['input'][0]['tools'][0]['tools'][0]));cases.append(bad)
        bad=copy.deepcopy(bad);bad['input'][0]['tools'][0]['tools'][1]['parameters']={'type':'string'};cases.append(bad)
        bad=self.lite();bad['input'][0]['tools'][0]['tools']=[{'type':'custom','name':'spawn_agent'}];cases.append(bad)
        with service(lambda h,b,n:reply(h,event()),flatten=False) as (port,seen):
            for doc in cases:
                with self.subTest(doc=doc):
                    status,headers,out=call(port,doc);self.assertEqual(status,400)
                    self.assertIn(b'Invalid native agent protocol',out)
            self.assertEqual(seen,[])

    def test_saved_bare_wait_new_lite_map_namespace_only_at_all_response_locations(self):
        wire=json.loads((EVIDENCE/'mimo-flash/namespace-scenario-a-attempt-1/wire.json').read_text())
        native=wire[0]['descriptor_locations'][0]['descriptor']
        _,mapping=shim.native_agent_request(enc({'input':[{'type':'additional_tools','tools':[native]}]}),False)
        rollouts=json.loads((EVIDENCE/'mimo-flash/scenario-a-attempt-1/rollouts-sanitized.json').read_text())
        item=next(e['item'] for r in rollouts for e in r['events'] if e.get('item',{}).get('name')=='wait_agent' and e['item'].get('namespace') is None)
        for doc,event_mode in (({'output':[item]},False),({'type':'response.completed','response':{'output':[item]}},True),
                               ({'type':'response.output_item.added','item':item},True),({'type':'response.output_item.done','item':item},True)):
            out,n=shim.restore_native_response(enc(doc),mapping,event_mode)
            self.assertEqual(n,1)
            self.assertEqual(json.loads(out),json.loads(json.dumps(doc).replace(json.dumps(item),json.dumps({**item,'namespace':'collaboration'}))))

    def test_kimi_baseline_top_only_actual_a2_b2_and_history_equivalence(self):
        baseline='7cdaf30d198433d261672185ef11ee12b4f155294c60fbd22b61f0401012493d'
        directory=EVIDENCE/'kimi/namespace-scenario-a-attempt-2'
        source=gzip.decompress((directory/(baseline+'.source.gz')).read_bytes())
        self.assertEqual(hashlib.sha256(source).hexdigest(),baseline)
        old_defs={n.name:ast.dump(n) for n in ast.parse(source).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        new_defs={n.name:ast.dump(n) for n in ast.parse((ROOT/'codex-agent/bin/codex-auto-review-shim').read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        self.assertEqual(set(old_defs),set(new_defs))
        self.assertEqual([k for k in old_defs if k!='Handler' and old_defs[k]!=new_defs[k]],['native_agent_request'])
        handlers=[next(n for n in ast.parse(s).body if isinstance(n,ast.ClassDef) and n.name=='Handler')
                  for s in (source,(ROOT/'codex-agent/bin/codex-auto-review-shim').read_bytes())]
        self.assertEqual(*(LoggingContracts.without_request_diagnostics(h) for h in handlers))
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'baseline.py';path.write_bytes(source)
            loader=importlib.machinery.SourceFileLoader('kimi_location_baseline',str(path));spec=importlib.util.spec_from_loader(loader.name,loader);old=importlib.util.module_from_spec(spec);loader.exec_module(old)
            for case in ('a','b'):
                wire=json.loads((EVIDENCE/'kimi'/f'namespace-scenario-{case}-attempt-2/wire.json').read_text())
                for w in wire:
                    doc={'tools':w['native_request_stage']['before_tools'],'input':[v['ingress'] for v in w['items']]}
                    history={'type':'function_call','namespace':'multi_agent_v1','name':'spawn_agent','arguments':' {"opaque":true} '}
                    doc['input'] += [history,{'type':'additional_tools','tools':[group('collaboration','disjoint')]}]
                    raw=enc(doc)
                    self.assertEqual(shim.native_agent_request(raw,True),old.native_agent_request(raw,True))
                    self.assertNotIn('disjoint',shim.native_agent_request(raw,True)[1])
                    self.assertEqual(json.loads(shim.native_agent_request(raw,True)[0])['input'],doc['input'])
            for top in ('absent',None,{},[]):
                doc=self.lite()
                if top!='absent':doc['tools']=top
                self.assertEqual(shim.native_agent_request(enc(doc),True),old.native_agent_request(enc(doc),True))
            for ns in ('multi_agent_v1','mcp'):
                doc=request();doc['input']=[{'type':'additional_tools','tools':[group(ns)]}]
                for module in (old,shim):
                    with self.assertRaises(module.NativeProtocolError):module.native_agent_request(enc(doc),True)

    def test_real_additional_only_handler_bytes_streaming_identity_and_json(self):
        doc=self.lite();raw=('  '+json.dumps(doc,indent=2)+' \n').encode()
        release,started=threading.Event(),threading.Event()
        def action(h,b,n):
            h.send_response(200);h.send_header('Content-Type','text/event-stream');h.send_header('Connection','close');h.end_headers()
            h.wfile.write(event());h.wfile.flush();started.set();release.wait(3)
            h.wfile.write(b'data: {"type":"response.completed","response":{"output":[]}}\n\n');h.wfile.flush();h.close_connection=True
        with service(action,flatten=False) as (port,seen):
            conn=http.client.HTTPConnection('127.0.0.1',port,timeout=3)
            try:
                conn.request('POST','/responses',raw);self.assertTrue(started.wait(2));response=conn.getresponse();first=response.read1(65536)
                self.assertIn(b'"namespace": "collaboration"',first);self.assertFalse(release.is_set());self.assertEqual(seen[0][2],raw)
                self.assertIsNone(response.getheader('Content-Encoding'));release.set();response.read()
            finally:release.set();conn.close()
        with service(lambda h,b,n:reply(h,enc({'output':[{'type':'function_call','name':'spawn_agent','arguments':' exact '}]}),'application/json','identity'),flatten=False) as (port,seen):
            self.assertEqual(json.loads(call(port,doc)[2])['output'][0],{'type':'function_call','name':'spawn_agent','arguments':' exact ','namespace':'collaboration'})
            self.assertEqual(seen[0][2],enc(doc))

    def test_additional_only_request_isolation_flags_guardian_and_empty_map(self):
        barrier=threading.Barrier(2)
        def action(h,b,n):barrier.wait(3);reply(h,event())
        with service(action,flatten=False) as (port,seen):
            results={}
            def run(ns):results[ns]=call(port,self.lite(ns))[2]
            threads=[threading.Thread(target=run,args=(ns,)) for ns in ('collaboration','multi_agent_v1')]
            for t in threads:t.start()
            for t in threads:t.join()
            self.assertEqual(set(results),{'collaboration','multi_agent_v1'})
            for ns,data in results.items():self.assertEqual(json.loads(data[6:])['item']['namespace'],ns)
        raw=b'data: {"type":"response.completed","response":{"output":[]}}\n\n'
        for flatten,restore,model in ((False,False,'test'),(False,True,'codex-auto-review')):
            with service(lambda h,b,n:reply(h,raw,encoding='gzip'),flatten,restore) as (port,seen):
                doc=self.lite();doc['model']=model
                self.assertEqual(call(port,doc)[2],raw);self.assertEqual(json.loads(seen[0][2])['input'],doc['input'])

    def test_current_observer_source_proof_and_adversarial_missing_or_wrong_paths(self):
        def load(name,path):
            spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
        probe=load('location_probe',ROOT/'docs/gateflow/shim-subagent-delivery/native-probe.py')
        auditor=load('location_audit',ROOT/'docs/gateflow/shim-subagent-delivery/audit-native-evidence.py')
        module=probe.load('location_observed_shim',ROOT/'codex-agent/bin/codex-auto-review-shim')
        route={'to':'test','native_agent_request_flatten':False,'native_agent_response_restore':True,'agent_message_fix':True,'id_fix':False,'json_fmt_fix':False,'drop_tools_item':False}
        wire,lock,local=probe.install_observers(module,route);original=module._make_server
        def make_server(r):return original({**r,**route})
        with patch(__name__+'.shim',module),patch.object(module,'_make_server',make_server):
            with service(lambda h,b,n:reply(h,event()+b'data: {"type":"response.completed","response":{"output":[]}}\n\n'),flatten=False) as (port,seen):
                doc=self.lite();doc['client_metadata']={'thread_id':'offline-location-observer'}
                self.assertEqual(call(port,doc)[0],200)
        record=wire[0];summary={'route':route,'source_hashes_at_launch':{'codex-agent/bin/codex-auto-review-shim':'current-source'}}
        stage=record['native_request_stage'];self.assertEqual(stage['map'],{'spawn_agent':'collaboration'})
        self.assertEqual(stage['selected_descriptor_paths'],[['input',0,'tools',0]])
        self.assertEqual(record['descriptor_locations'][0]['containing_item_type'],'additional_tools')
        self.assertEqual(stage['before_sha256'],stage['after_sha256']);self.assertEqual(record['expected_outbound_sha256'],record['outbound_attempts'][0]['body_sha256'])
        self.assertEqual(auditor.audit_namespace_record(summary,record),stage['after_sha256'])
        for mutation in ('empty-map','missing-source','wrong-type','unknown-source','missing-path','location-type','missing-version','missing-container','erased-sources','missing-parser','mutated-call'):
            bad=copy.deepcopy(record);s=bad['native_request_stage']
            if mutation=='empty-map':s['map']={}
            elif mutation=='missing-source':del s['descriptor_sources']
            elif mutation=='wrong-type':s['descriptor_sources'][0]['containing_item_type']='message';bad['descriptor_sources']=copy.deepcopy(s['descriptor_sources'])
            elif mutation=='unknown-source':s['descriptor_sources'][0]['path']=['history',0,'tools'];bad['descriptor_sources']=copy.deepcopy(s['descriptor_sources'])
            elif mutation=='missing-path':s['selected_descriptor_paths']=[]
            elif mutation=='location-type':bad['descriptor_locations'][0]['containing_item_type']='message'
            elif mutation=='missing-version':del s['descriptor_source_version']
            elif mutation=='missing-container':s['descriptor_sources']=[];bad['descriptor_sources']=[]
            elif mutation=='erased-sources':
                s['descriptor_sources']=[];bad['descriptor_sources']=[];bad['descriptor_locations']=[];s['selected_descriptor_paths']=[];s['map']={}
            elif mutation=='missing-parser':del bad['outbound_attempts'][0]['native_parser_invocation']
            else:bad['outbound_attempts'][0]['native_events'][0]['after_calls'][0]['arguments']='repair'
            with self.subTest(mutation=mutation),self.assertRaises((AssertionError,KeyError)):auditor.audit_namespace_record(summary,bad)


if __name__=='__main__':unittest.main()
