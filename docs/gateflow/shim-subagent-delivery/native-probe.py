#!/usr/bin/env python3
"""Isolated real-model probe, chaining a candidate to the selected installed route.

No private settings writes, deployment, forced catalog/tool modes, synthetic SSE,
child RPC or automatic retries. Only newly created test threads are inspected.
"""
import argparse
import collections
import gzip
import hashlib
import http.client
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
import urllib.parse
import uuid
import zlib

ROOT = Path(__file__).resolve().parents[3]


def sha(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def changes(before, after, path=()):
    """Exact changed leaves; values are hashed to avoid saving global context."""
    if before == after:
        return []
    if isinstance(before, dict) and isinstance(after, dict) and before.keys() == after.keys():
        return [v for k in before for v in changes(before[k], after[k], (*path, k))]
    if isinstance(before, list) and isinstance(after, list) and len(before) == len(after):
        return [v for k in range(len(before)) for v in changes(before[k], after[k], (*path, k))]
    return [{'path': list(path), 'before_sha256': sha(json.dumps(before, ensure_ascii=False, sort_keys=True)),
             'after_sha256': sha(json.dumps(after, ensure_ascii=False, sort_keys=True)), 'before': before, 'after': after}]



def native_supplement(ids):
    """Only allowlisted native events from explicitly known new test threads."""
    supplements = []
    for tid in sorted(ids):
        for path in (Path.home()/'.codex/sessions').glob(f'*/*/*/*{tid}.jsonl'):
            events = []
            for line, raw in enumerate(path.read_text().splitlines(), 1):
                item = json.loads(raw)
                p = item.get('payload', {})
                if item['type'] != 'event_msg':
                    continue
                if p.get('type') == 'item_completed' and p.get('item', {}).get('type') in ('CommandExecution', 'SubAgentActivity', 'CollabAgentToolCall'):
                    events.append({'line': line, 'event': p})
                if p.get('type') == 'thread_settings_applied':
                    settings = p['thread_settings']
                    events.append({'line': line, 'settings': {k:settings.get(k) for k in ('model','model_provider_id','reasoning_effort','approval_policy','approvals_reviewer','permission_profile','cwd')}})
            supplements.append({'thread_id':tid, 'source_rollout_sha256':sha(path.read_bytes()), 'events':events})
    return supplements


def candidate_route(route):
    """Preserve the installed incoming prefix by omitting stripping metadata."""
    candidate = {**route, 'listen': '127.0.0.1:0',
                 'upstream': f'http://127.0.0.1:{route["port"]}', 'from': 'codex-auto-review'}
    candidate.pop('endpoint_id')
    candidate.pop('request_prefix')
    return candidate


def descriptor_sources(doc):
    """Project only the two declaration containers, never input/history content."""
    sources=[]
    def append(path, item_type, tools):
        if isinstance(tools,list):
            projection=[t if isinstance(t,dict) and t.get('type')=='namespace' and t.get('name') in ('multi_agent_v1','collaboration')
                        else {k:t[k] for k in ('type','name') if k in t} if isinstance(t,dict) else None for t in tools]
            sources.append({'path':path,'containing_item_type':item_type,'tools':projection})
    append(['tools'],None,doc.get('tools'))
    if isinstance(doc.get('input'),list):
        for i,item in enumerate(doc['input']):
            if isinstance(item,dict) and item.get('type')=='additional_tools':
                append(['input',i,'tools'],item['type'],item.get('tools'))
    return sources


def install_observers(shim, route, passthrough_requests=None):
    wire, lock, local = [], threading.Lock(), threading.local()
    # Keep requests outside the native thread/stage chain out of wire.json.
    if passthrough_requests is None:
        passthrough_requests = []
    original_fix, original_open = shim.fix_agent_messages, shim.upstream_open
    original_native = shim.native_agent_request
    original_event = shim.restore_native_sse_event
    original_json = shim.restore_native_response
    original_handle = shim.Handler._handle
    original_relay = shim.Handler._relay_native_response

    def json_object(body):
        try:
            doc = json.loads(body)
        except (ValueError, TypeError):
            return None
        return doc if isinstance(doc, dict) else None

    def observe_fix(body):
        local.record = local.attempt = None
        converted, count = original_fix(body)
        doc, fixed = json_object(body), json_object(converted)
        metadata = doc.get('client_metadata') if doc is not None else None
        thread_id = metadata.get('thread_id') if isinstance(metadata, dict) else None
        if (doc is None or fixed is None or not isinstance(thread_id, str) or not thread_id
                or not getattr(local, 'responses_request', True)):
            return converted, count
        inputs = doc.get('input') if isinstance(doc.get('input'), list) else []
        fixed_inputs = fixed.get('input') if isinstance(fixed.get('input'), list) else []
        items = [{'index': i, 'ingress': b, 'egress': a} for i, (b, a) in enumerate(zip(inputs, fixed_inputs)) if isinstance(b, dict) and b.get('type') == 'agent_message']
        record = {'thread_id': thread_id, 'ingress_sha256': sha(body),
                  'egress_sha256': sha(converted), 'model': doc.get('model'), 'stream': doc.get('stream'), 'converted': count, 'items': items,
                  'types': dict(collections.Counter(i.get('type') for i in inputs if isinstance(i, dict))),
                  'non_target_items_equal': len(inputs) == len(fixed_inputs) and all(b == a for b, a in zip(inputs, fixed_inputs) if not isinstance(b, dict) or b.get('type') != 'agent_message'),
                  'non_input_fields_equal': {k:v for k,v in doc.items() if k != 'input'} == {k:v for k,v in fixed.items() if k != 'input'},
                  'stages': [], 'outbound_attempts': []}
        wanted = ('spawn_agent', 'send_input', 'followup_task', 'send_message', 'wait', 'wait_agent', 'list_agents', 'exec', 'exec_command', 'multi_agent_v1', 'collaboration', 'functions')
        top=doc.get('tools') if isinstance(doc.get('tools'),list) else []
        record['native_descriptors'] = [t for t in top if isinstance(t, dict) and t.get('name') in wanted]
        record['descriptor_sources'] = descriptor_sources(doc)
        record['descriptor_locations'] = [
            {'path':source['path']+[j], 'containing_item_type':source['containing_item_type'],'descriptor':t}
            for source in record['descriptor_sources'] for j,t in enumerate(source['tools'])
            if isinstance(t,dict) and t.get('type')=='namespace' and t.get('name') in ('multi_agent_v1','collaboration')]
        for i,item in enumerate(inputs):
            if isinstance(item,dict) and item.get('type') == 'additional_tools' and isinstance(item.get('tools'),list):
                for j,t in enumerate(item.get('tools', [])):
                    if isinstance(t,dict) and t.get('name') in ('functions','collaboration','multi_agent_v1'):
                        record['native_descriptors'].append(t)
        if doc.get('model')=='codex-auto-review':record['native_stage_bypass']='guardian'
        record['lite_header_observed'] = None
        with lock:wire.append(record)
        local.record = record
        return converted, count

    def observe_native(body, flatten):
        converted, mapping = original_native(body, flatten)
        record = getattr(local, 'record', None)
        if record is not None:
            before,after=json_object(body),json_object(converted)
            if before is None or after is None:
                return converted,mapping
            record['native_request_stage'] = {'before_sha256':sha(body),'after_sha256':sha(converted),
                'flatten':flatten,'map':dict(mapping),'before_tools':before.get('tools'), 'after_tools':after.get('tools'),
                'descriptor_source_version':2,'descriptor_sources':descriptor_sources(before),
                'selected_descriptor_paths':[source['path']+[j] for source in descriptor_sources(before)
                    if not flatten or source['path']==['tools'] for j,t in enumerate(source['tools'])
                    if isinstance(t,dict) and t.get('type')=='namespace' and t.get('name') in ('multi_agent_v1','collaboration')],
                'outside_tools_equal':{k:v for k,v in before.items() if k!='tools'}=={k:v for k,v in after.items() if k!='tools'},
                'changes':changes(before,after)}
        return converted,mapping

    def stage_observer(flag, function):
        def observe(body,*argv):
            out,count=function(body,*argv)
            record=getattr(local,'record',None)
            if record is not None:
                before,after=json_object(body),json_object(out)
                if before is None or after is None:
                    return out,count
                record['stages'].append({'flag':flag,'enabled':True,'count':int(count!='none') if flag=='model_swap' else count,
                    'before_sha256':sha(body),'after_sha256':sha(out),'changes':changes(before,after)})
            return out,count
        return observe

    class ResponseObserver:
        def __init__(self,response,attempt):
            self.response=response;self.attempt=attempt;self.digest=hashlib.sha256();self.total=0
        def __getattr__(self,key):return getattr(self.response,key)
        def capture(self,data):
            self.digest.update(data);self.total+=len(data)
            self.attempt['response_pre_sha256']=self.digest.hexdigest();self.attempt['response_pre_bytes']=self.total
            if data and 'response_first_read_at' not in self.attempt:self.attempt['response_first_read_at']=time.monotonic()
            if not data:self.attempt['response_eof_at']=time.monotonic()
            return data
        def reading(self,method,*argv):
            try:return self.capture(method(*argv))
            except http.client.IncompleteRead as exc:
                self.capture(exc.partial or b'');raise
        def read1(self,n):return self.reading(getattr(self.response,'read1',None) or self.response.read,n)
        def read(self,*argv):return self.reading(self.response.read,*argv)

    def observe_open(req, timeout):
        local.attempt = None
        record = getattr(local, 'record', None)
        if record is None:
            body = req.data or b''
            metadata = {'method': req.get_method(), 'path': urllib.parse.urlsplit(req.full_url).path,
                        'body_bytes': len(body), 'body_sha256': sha(body), 'model': None,
                        'http_status': None, 'error_class': None}
            with lock:passthrough_requests.append(metadata)
            try:
                response = original_open(req, timeout)
                metadata['http_status'] = response.status
                return response
            except Exception as exc:
                metadata['error_class'] = type(exc).__name__
                metadata['http_status'] = getattr(exc, 'code', None)
                raise
        body = req.data
        encoding = (req.get_header('Content-encoding') or '').lower()
        body = {'gzip': gzip.decompress, 'deflate': zlib.decompress}.get(encoding, lambda x:x)(body)
        attempt = {'body_sha256': sha(body), 'path': urllib.parse.urlsplit(req.full_url).path,'model': json.loads(body).get('model')}
        if record is not None:
            previous=record.get('native_request_stage',{}).get('after_sha256',record['egress_sha256'])
            observed={stage['flag']:stage for stage in record['stages']}
            stages=[]
            for flag in ('model_swap','id_fix','json_fmt_fix','drop_tools_item'):
                stage=observed.get(flag,{'flag':flag,'enabled':False,'count':0,'before_sha256':previous,'after_sha256':previous,'changes':[]})
                stages.append(stage);previous=stage['after_sha256']
            record['stages']=stages;record['expected_outbound_sha256']=previous
            record['actual_upstream_body_verified'] = sha(body) == previous
            record['outbound_attempts'].append(attempt)
            record['lite_header_observed'] = {k:v for k,v in req.header_items() if 'lite' in k.lower()}
        local.attempt=attempt
        try:
            response = original_open(req, timeout)
            attempt['http_status'] = response.status
            attempt['response_metadata']={key:response.headers.get_all(key,[]) for key in ('Content-Encoding','Content-Type','Content-Length','Transfer-Encoding')}
            attempt.update(response_pre_sha256=sha(b''),response_pre_bytes=0,response_post_sha256=sha(b''),response_post_bytes=0,native_events=[],namespace_added_count=0)
            return ResponseObserver(response,attempt)
        except Exception as exc:
            attempt['error_class'] = type(exc).__name__;attempt['http_status'] = getattr(exc, 'code', None)
            raise

    def observe_event(raw,mapping):
        out,count=original_event(raw,mapping)
        attempt=getattr(local,'attempt',None)
        if attempt is not None:
            attempt['native_sse_events_processed']=attempt.get('native_sse_events_processed',0)+1
            def payload(data):
                values=[]
                for line in data.decode().splitlines():
                    if line=='data' or line.startswith('data:'):
                        value=line[5:] if line.startswith('data:') else ''
                        values.append(value[1:] if value.startswith(' ') else value)
                try:return json.loads('\n'.join(values))
                except ValueError:return {}
            def native_calls(doc):
                candidates=([doc.get('item')] if doc.get('type') in ('response.output_item.added','response.output_item.done') else doc.get('response',{}).get('output',[]) if doc.get('type')=='response.completed' else [])
                return [item for item in candidates if isinstance(item,dict) and item.get('type')=='function_call' and item.get('name') in mapping]
            before,after=payload(raw),payload(out)
            calls=native_calls(before)
            if calls:
                record={'changes':changes(before,after),'type':before.get('type'),'before_calls':calls,'after_calls':native_calls(after),'added':count,'pre_event_sha256':sha(raw),'post_event_sha256':sha(out)}
                # completed.output also includes hidden reasoning: retain only its
                # mapped calls and hashes, never that whole event's raw payload.
                if before.get('type') in ('response.output_item.added','response.output_item.done'):
                    record.update(before_native_sse=raw.decode(),after_native_sse=out.decode())
                attempt['native_events'].append(record)
            attempt['namespace_added_count']+=count
        return out,count

    def observe_json(raw,mapping,event=False):
        out,count=original_json(raw,mapping,event)
        attempt=getattr(local,'attempt',None)
        if not event and attempt is not None:
            attempt['native_json_outputs_processed']=attempt.get('native_json_outputs_processed',0)+1
            before,after=json.loads(raw),json.loads(out)
            calls=lambda doc:[item for item in doc.get('output',[]) if isinstance(item,dict) and item.get('type')=='function_call' and item.get('name') in mapping]
            if calls(before):
                attempt['native_events'].append({'type':'json.output','before_calls':calls(before),'after_calls':calls(after),'changes':changes(before,after),'added':count,'pre_event_sha256':sha(raw),'post_event_sha256':sha(out)})
            attempt['namespace_added_count']+=count
        return out,count

    def observe_relay(self,response,mapping):
        attempt=getattr(local,'attempt',None)
        if attempt is not None:
            attempt['native_parser_invocation']={'map':dict(mapping),'media':response.headers.get('Content-Type','').split(';')[0].strip().lower()}
        return original_relay(self,response,mapping)

    class OutputObserver:
        def __init__(self,wrapped):self.wrapped=wrapped;self.headers=bytearray();self.body=False;self.digest=hashlib.sha256();self.total=0
        def __getattr__(self,key):return getattr(self.wrapped,key)
        def write(self,data):
            result=self.wrapped.write(data)
            if not self.body:
                self.headers.extend(data)
                if b'\r\n\r\n' not in self.headers:return result
                header,data=bytes(self.headers).split(b'\r\n\r\n',1);self.headers.clear();self.body=True
            if data:
                self.digest.update(data);self.total+=len(data)
                attempt=getattr(local,'attempt',None)
                if attempt is not None:
                    attempt.update(response_post_sha256=self.digest.hexdigest(),response_post_bytes=self.total)
                    if 'downstream_first_body_at' not in attempt:attempt['downstream_first_body_at']=time.monotonic()
            return result

    def observe_handle(handler):
        local.record=local.attempt=None
        local.responses_request=handler.path.split('?',1)[0].endswith('/responses')
        original=handler.wfile;handler.wfile=OutputObserver(original)
        try:return original_handle(handler)
        finally:handler.wfile=original

    shim.fix_agent_messages, shim.upstream_open = observe_fix, observe_open
    shim.native_agent_request,shim.restore_native_sse_event=observe_native,observe_event
    shim.restore_native_response=observe_json
    shim.Handler._relay_native_response=observe_relay
    for flag,name in (('model_swap','_swap'),('id_fix','fix_message_ids'),('json_fmt_fix','json_object_format'),('drop_tools_item','drop_tools_item')):
        setattr(shim,name,stage_observer(flag,getattr(shim,name)))
    shim.Handler._handle=observe_handle
    shim.Handler.do_GET=shim.Handler.do_POST=shim.Handler.do_PUT=shim.Handler.do_DELETE=shim.Handler.do_PATCH=observe_handle
    return wire, lock, local


def short_v2_completion_prompt(prompt):
    """Align declared v2 cases with mailbox-edge waits and persistent receipts."""
    contract=('Completion contract: after every child task, an exact fresh native FINAL_ANSWER notification '
              'already present in your context from the SAME canonical child is completion and permits the next step. '
              'Match its payload to this task, not an old final. Do NOT wait for another mailbox update after receiving that final. '
              'Only when no matching fresh FINAL_ANSWER is present, call native collaboration.wait_agent with timeout_ms=30000, '
              'then inspect the notifications now in context. A timeout alone is never completion; if the exact fresh final is '
              'already there, proceed without another wait. If still absent, further bounded waits are allowed. '
              'Never redispatch a task or MESSAGE because a wait times out. A dispatch acknowledgement is not a child final.')
    prompt=re.sub(r'(?m)^Completion contract:[^\n]*',lambda _:contract,prompt)
    return re.sub(r'Call native wait_agent and receive its (?:actual completed final|NEW completed final, not its old final|new completed final)',
                  'Require its exact fresh native FINAL_ANSWER notification',prompt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default='ds-flash')
    parser.add_argument('--evidence-dir', type=Path)
    parser.add_argument('--attempt', default='1')
    parser.add_argument('--scenario', choices=('all', 'a', 'b'), default='all')
    parser.add_argument('--initial-marker')
    args = parser.parse_args()
    routes_path = ROOT / 'codex-agent/shim-routes.json'
    route = next(r for r in json.loads(routes_path.read_text())['routes'] if r['endpoint_id'] == args.profile)
    card_path = ROOT / 'codex-agent/profiles' / args.profile / 'config.toml'
    card = tomllib.loads(card_path.read_text().replace('@HOME@', str(Path.home())))
    provider = card['model_provider']
    registry_path = ROOT / 'codex-agent/model-providers.toml'
    registry = tomllib.loads(registry_path.read_text())['model_providers'][provider]
    assert registry['base_url'] == f'http://127.0.0.1:{route["port"]}' + route['request_prefix'], 'profile registry/route mismatch'
    catalog = Path(card['model_catalog_json'])
    selected = next(m for m in json.loads(catalog.read_text())['models'] if m['slug'] == card['model'])
    out = args.evidence_dir or Path(tempfile.mkdtemp(prefix='shim-native-' + args.profile + '-'))
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'summary.json').exists():
        parser.error('Evidence directory already has an attempt; choose a new directory')
    cwd = Path(tempfile.mkdtemp(prefix='shim-fixture-' + args.profile + '-'))
    fixture = cwd / 'harmless-target.txt'
    fixture_text = 'HARMLESS_NATIVE_CONTENT_' + uuid.uuid4().hex
    fixture.write_text(fixture_text)
    token = 'LIVE_MESSAGE_OK_' + uuid.uuid4().hex[:12]
    initial, followup = (args.initial_marker or 'LIVE_INITIAL_' + uuid.uuid4().hex[:12], 'LIVE_FOLLOWUP_' + uuid.uuid4().hex[:12])
    shim_path = ROOT / 'codex-agent/bin/codex-auto-review-shim'
    shim = load('candidate_shim', shim_path)
    shim.FAILED_DIR = str(cwd / 'failed')
    dumps = []
    # Failures retain content hashes, never full global prompts/contexts.
    def observe_dump(self, payload, status, kind='req'):
        dumps.append({'kind':kind, 'status':status, 'sha256':sha(payload), 'bytes':len(payload)})
    shim.Handler._dump = observe_dump
    endpoint = shim.endpoint_module()
    # Retain only the selected model and equality check, never URL/key.
    connection = endpoint.connection(args.profile, 'codex', require_key=True)
    effective = {'wire_model': connection['upstream_model'], 'key_present': bool(connection['api_key'])}
    if args.profile == 'kimi':
        ds = endpoint.connection('ds-flash', 'codex', require_key=True)
        effective['user_override_destination_equals_ds_flash'] = connection['base_url'] == ds['base_url'] and connection['api_key'] == ds['api_key']
        del ds
    del connection
    passthrough_requests = []
    wire, lock, local = install_observers(shim, route, passthrough_requests)
    # The candidate has no endpoint_id: installed corresponding route owns auth
    # and logical->wire model remapping. Preserve its incoming prefix exactly.
    server = shim._make_server(candidate_route(route))
    port = server.server_address[1]
    server.route['port'] = port
    listener = threading.Thread(target=server.serve_forever)
    listener.start()
    version = subprocess.check_output(['codex', '--version'], text=True).strip()
    base_policy = tomllib.loads((Path.home()/'.codex/config.toml').read_text())
    # Keep auto-review where the model requires it; never disables node review.
    approval = base_policy.get('approval_policy', 'on-request') if selected.get('node_repl_auto_review_required') else 'never'
    settings = {**card, f'model_providers.{provider}.base_url': f'http://127.0.0.1:{port}' + route['request_prefix'],
                'features.apps': False, 'features.plugins': False, 'approval_policy': approval, 'sandbox_mode': 'read-only'}
    cmd = ['codex', 'app-server']
    for key,value in settings.items():
        cmd += ['-c', key + '=' + json.dumps(value)]
    hashes = {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): sha(p.read_bytes()) for p in (shim_path, routes_path, card_path, registry_path, catalog, Path(__file__), Path(__file__).with_name('audit-native-evidence.py'), ROOT/'tests/test_shim_native_namespace.py', ROOT/'tests/test_shim_native_evidence.py', ROOT/'tests/test_shim_subagent_delivery.py')}
    summary = {'schema': 2, 'profile': args.profile, 'attempt': args.attempt, 'scenario': args.scenario, 'source_head': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
               'source_hashes_at_launch': hashes, 'version': version, 'model': card['model'], 'provider': provider, 'effort': card['model_reasoning_effort'],
               'catalog_selected': {k:selected.get(k) for k in ('slug','multi_agent_version','tool_mode','use_responses_lite','node_repl_auto_review_required','node_repl_disabled','shell_type')},
               'effective_endpoint': effective, 'route': route, 'cwd':str(cwd), 'candidate_port':port,
               'command': cmd, 'driver_argv': [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
               'settings': settings, 'inherited_approval_reviewer': base_policy.get('approvals_reviewer'),
               'fixture': {'path':str(fixture), 'contents':fixture_text, 'sha256':sha(fixture_text)},
               'initial_marker':initial,'followup_marker':followup,'message_token':token}
    snapshots = (ROOT / 'docs/gateflow/shim-subagent-all-providers/evidence/source-snapshots') if args.scenario == 'all' else out
    snapshots.mkdir(parents=True, exist_ok=True)
    for source_path in hashes:
        source=Path(source_path)
        if not source.is_absolute():source=ROOT/source
        source_bytes=source.read_bytes()
        snapshot=snapshots/(sha(source_bytes)+'.source.gz')
        if not snapshot.exists():snapshot.write_bytes(gzip.compress(source_bytes,mtime=0))
    (out/'launch.json').write_text(json.dumps(summary,indent=2))
    print('PROBE_DIR=' + str(out), flush=True)
    stderr = (out/'app-server.stderr').open('w')
    proc = subprocess.Popen(cmd,cwd=cwd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,text=True,bufsize=1)
    messages = queue.Queue()
    def reader():
        for line in proc.stdout:
            try: messages.put(json.loads(line))
            except ValueError: messages.put({'parse_error':True})
        messages.put(None)
    thread = threading.Thread(target=reader); thread.start()
    def send(method,params,request_id=None):
        msg = {'method':method,'params':params}
        if request_id is not None: msg['id']=request_id
        proc.stdin.write(json.dumps(msg)+'\n'); proc.stdin.flush()
    prompt = f'''NATIVE_CANDIDATE_PROBE: explicitly authorized isolated collaboration diagnostic. Perform once, in sequence, using actual advertised native APIs. Do not retry dispatches, repair, interrupt or close agents. On an explicit tool error, report the error and stop; do not try alternate invocation paths.
Native API contract: collaboration (v2) and multi_agent_v1 (v1), when advertised, are native tool namespaces. Invoke their tools directly with the exact descriptor arguments. They are not MCP servers or JavaScript globals. Even when file tools use Code Mode, native collaboration is called directly, NEVER via functions.exec, tools.collaboration__*, tools.multi_agent_v1__*, node_repl or RPC. Parent may use ONLY the advertised native collaboration tools; no parent file, shell, JavaScript, resource discovery or introspection calls, even harmless ones. Determine capabilities from the actual descriptors alone; do not search for them through other tools or simulate calls.
Dispatch/result contract: a completed followup_task or send_message call with blank/empty output and no explicit error is a SUCCESSFUL dispatch. Do not resend it, test another spelling/host, or treat the blank result as a failure. Dispatch acknowledgement is not a child final. For every continuation, MESSAGE and targeted wait, use the exact canonical task_name returned by spawn_agent (v2) or its exact returned agent_id (v1); never guess a relative target or substitute a nickname. Omit model/effort overrides and follow the actual descriptors.
Completion contract: after A1, A2, A3's consume task and B, call the native wait_agent with its advertised arguments and wait for that child's actual fresh completed final before proceeding to the next step. A wait timeout or mailbox update alone is not a new final; further native waits are allowed without repeating any dispatch. An old final cannot satisfy a new task.
A1: Spawn a fresh child (name delivery_a when supported), with no inherited conversation (fork_turns="none" or fork_context=false, as advertised). Its complete task: "NATIVE_CANDIDATE_PROBE initial. Reply exactly one line {initial}. Do not use tools, read/write files, or delegate." Call native wait_agent and receive its actual completed final before A2.
A2: Continue the SAME child exactly once using its actual native continuation API (followup_task or send_input as advertised, without interrupting). Complete task: "NATIVE_CANDIDATE_PROBE followup. Reply exactly one line {followup}. Do not use tools, read/write files, or delegate." Call native wait_agent and receive its NEW completed final, not its old final, before A3.
A3: If and only if the actual descriptors advertise a separate send_message capability, send the SAME now-idle child exactly ONE MESSAGE: "NATIVE_CANDIDATE_PROBE MESSAGE token: {token}. Remember this token for the next task." Its successful result may be blank; send_message does not trigger a child turn. Then continue that same child exactly once with task: "NATIVE_CANDIDATE_PROBE consume-message. Reply exactly the token in your most recent MESSAGE. Do not use tools, read/write files, or delegate." This continuation task must NOT contain the token. Call native wait_agent and receive its new completed final before B. Only if the actual v1 descriptors lack separate send_message, explicitly report A3 N/A with that descriptor-based reason and proceed to B.
B: Spawn a DIFFERENT fresh child (name delivery_b when supported) with no inherited conversation (fork_turns="none" or fork_context=false, as advertised). Complete task: "NATIVE_CANDIDATE_PROBE file task. Use your advertised file-reading tool (exec_command or equivalent, via Code Mode if required) to run cat {fixture}. Return exactly its entire contents as final, no formatting. Do not delegate, read other files or write anything." Call native wait_agent and receive its actual completed final. The fixture contents are unknown to you; never read it yourself, guess it, or give contents to any child. Code Mode file execution, when required, belongs only to this B child.
Finally report observed finals and any unavailable capability. Parent self-report is informational; independent wire/native evidence determines acceptance.'''
    if args.scenario != 'all':
        # Keep the default compound prompt byte-for-byte; declared short cases
        # have independent parents, not a truncated/relabelled all execution.
        common, steps = prompt.split('\nA1:', 1)
        a_steps, b_step = ('A1:' + steps).split('\nB:', 1)
        b_step, final = ('B:' + b_step).split('\nFinally', 1)
        common = common.replace("after A1, A2, A3's consume task and B", "after every child task in this declared case")
        common = common.replace('Omit model/effort overrides and follow the actual descriptors.', 'Omit model/effort overrides and follow the actual descriptors. Fork arguments are API-specific: multi_agent_v1.spawn_agent uses fork_context=false (JSON boolean, NEVER "none" or "false" strings); collaboration.spawn_agent uses fork_turns="none" (string). Never send v2-only task_name/agent_type fields to v1; use only fields actually in its descriptor.')
        if args.scenario == 'a':
            a_steps = a_steps.replace('before B.', 'before finishing.').replace('and proceed to B.', 'and finish.')
            prompt = common + '\nDeclared scenario A only: complete A1, A2 and applicable A3, then finish.\n' + a_steps
        else:
            b_step = b_step.replace('a DIFFERENT fresh child', 'one fresh child')
            prompt = common + '\nDeclared scenario B only: spawn exactly one child for the following file task, then finish.\n' + b_step
        prompt += '\nFinally' + final
        if selected.get('multi_agent_version')=='v2':
            prompt=short_v2_completion_prompt(prompt)
    if args.initial_marker == 'LIVE_PROBE_OK' and args.scenario in ('all','a'):
        prompt=prompt.replace('NATIVE_CANDIDATE_PROBE initial. Reply exactly one line LIVE_PROBE_OK. Do not use tools, read/write files, or delegate.', '只回复一行 LIVE_PROBE_OK，不要调用工具、不要读写文件')
    summary['parent_prompt']=prompt
    parent_id, done, errors, native_events = None, False, [], []
    started=time.time()
    try:
        send('initialize', {'clientInfo':{'name':'shim_native_candidate','title':'Shim native candidate','version':'2'},'capabilities':{'experimentalApi':True}},0)
        while True:
            try: msg=messages.get(timeout=30)
            except queue.Empty:
                print(f'WAITING elapsed={int(time.time()-started)} requests={len(wire)}',flush=True); continue
            if msg is None:
                errors.append({'process_eof_before_completed':not done}); break
            if msg.get('error'):
                errors.append(msg['error']); break
            if msg.get('id')==0 and 'result' in msg:
                send('initialized',{})
                send('thread/start',{'model':card['model'],'modelProvider':provider,'cwd':str(cwd),'sandbox':'read-only','approvalPolicy':approval,'experimentalRawEvents':True},1)
            if msg.get('id')==1 and 'result' in msg:
                parent_id=msg['result']['thread']['id'];summary['thread_start_identity']={k:msg['result'].get(k) for k in ('model','modelProvider','reasoningEffort','approvalPolicy','sandbox')}
                print('PARENT_ID='+parent_id,flush=True)
                send('turn/start',{'threadId':parent_id,'input':[{'type':'text','text':prompt}]},2)
            # Retain only native execution/collaboration events of this new run.
            method=msg.get('method','')
            params=msg.get('params',{})
            event=params.get('msg',{})
            et=event.get('type','') if isinstance(event,dict) else ''
            if method.startswith('codex/event/') and any(s in et for s in ('exec_command','mcp_tool_call','collab','tool_call','task_complete')):
                native_events.append(msg)
            if method=='turn/completed' and params.get('threadId')==parent_id:
                done=True; summary['parent_turn_status']=params['turn']['status']
                summary['parent_turn_error']=params['turn'].get('error')
                if summary['parent_turn_status']!='completed': errors.append({'turn_status':summary['parent_turn_status']})
                break
    finally:
        proc.stdin.close();code=proc.wait();thread.join();stderr.close()
        server.shutdown();server.server_close();listener.join()
    ids={r['thread_id'] for r in wire if r.get('thread_id')}
    if parent_id: ids.add(parent_id)
    rollouts=[]
    for tid in sorted(ids):
        for path in (Path.home()/'.codex/sessions').glob(f'*/*/*/*{tid}.jsonl'):
            events,identity,contexts=[],{},[]
            for lineno,line in enumerate(path.read_text().splitlines(),1):
                item=json.loads(line);p=item.get('payload',{});typ=item['type']
                if typ=='session_meta': identity={k:p.get(k) for k in ('id','parent_thread_id','cli_version','model_provider','agent_path','source','cwd')}
                if typ=='turn_context': contexts.append({k:p.get(k) for k in ('turn_id','model','model_provider','effort','approval_policy','sandbox_policy')})
                if typ=='response_item' and (p.get('type') in ('agent_message','function_call','function_call_output','custom_tool_call','custom_tool_call_output') or p.get('type')=='message' and p.get('role')=='assistant'):
                    events.append({'line':lineno,'item':p})
                if typ=='event_msg' and (p.get('type') in ('task_started','task_complete') or any(s in p.get('type','') for s in ('exec_command','mcp_tool_call','collab','tool_call'))):
                    events.append({'line':lineno,'event':p})
            rollouts.append({'file':path.name,'identity':identity,'contexts':contexts,'events':events})
    summary.update(parent_id=parent_id,app_server_exit=code,errors=errors,parent_completed=done and not errors and code==0,elapsed_seconds=round(time.time()-started,2),request_count=len(wire))
    for name,value in (('wire',wire),('passthrough-requests',passthrough_requests),('rollouts-sanitized',rollouts),('native-events',native_events),('dump-metadata',dumps),('native-rollout-supplement',native_supplement(ids)),('summary',summary)):
        (out/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2))
    print(json.dumps({'profile':args.profile,'parent_completed':summary['parent_completed'],'app_server_exit':code,'errors':errors,'requests':len(wire),'elapsed_seconds':summary['elapsed_seconds']}),flush=True)
    return 0 if summary['parent_completed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
