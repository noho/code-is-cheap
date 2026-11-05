#!/usr/bin/env python3
"""Bounded investigation only. Private captures; no product/live mutation.

Run: python3 docs/work-units/hy4-codex-token-plan/probe_hy4.py
The server mode instruments an unchanged private copy of the branch shim.
"""
from __future__ import annotations

import copy
from collections import Counter
import gzip
import hashlib
from http.server import ThreadingHTTPServer
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import zlib

ROOT = Path(__file__).resolve().parents[3]
TASK = Path('/private/tmp/hy4-codex-task')
OUT = Path(__file__).resolve().parent
MAX_ATTEMPTS = 40
WORKFLOW_SECONDS = 300


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n' if not isinstance(value, str) else value)
    path.chmod(0o600)


def append(path, value):
    with path.open('a') as f:
        f.write(json.dumps(value) + '\n')
    path.chmod(0o600)


def load_module(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def decode(raw, encoding=''):
    if encoding == 'gzip': raw = gzip.decompress(raw)
    elif encoding == 'deflate': raw = zlib.decompress(raw)
    elif encoding not in ('', 'identity'): raise ValueError('unexpected request encoding')
    return json.loads(raw)


def serve(run, batch):
    shim = load_module('private_hy_shim', run/'stage/codex-auto-review-shim')
    shim.FAILED_DIR = str(run/'shim-failed')
    opener = shim.upstream_open
    lock = threading.Lock()
    current = threading.local()
    deadline = float((run/'deadline').read_text())

    class Observed:
        def __init__(self, response, index):
            self.response = response
            self.index = index
            self.status = response.status
            self.headers = response.headers
            self.start = time.monotonic()

        def record(self, data, method):
            if data:
                with (run/f'upstream-{self.index:02d}.response').open('ab') as f: f.write(data)
            append(run/'chunks.jsonl', dict(attempt=self.index, method=method,
                   elapsed_seconds=round(time.monotonic()-self.start, 6),
                   monotonic=time.monotonic(), bytes=len(data)))
            return data

        def read(self, *args):
            return self.record(self.response.read(*args), 'read')

        def read1(self, *args):
            return self.record((getattr(self.response, 'read1', None) or self.response.read)(*args), 'read1')

        def close(self): return self.response.close()

    def observed_open(req, timeout):
        with lock:
            count = int((batch/'attempt-count').read_text())
            if count >= (int((batch/'max-attempts').read_text()) if (batch/'max-attempts').exists() else MAX_ATTEMPTS) or time.time() >= deadline:
                append(run/'limits.jsonl', dict(count=count, deadline_exhausted=time.time() >= deadline))
                raise RuntimeError('Declared investigation upstream budget exhausted')
            count += 1
            write(batch/'attempt-count', str(count))
            index = sum(1 for _ in (run/'attempts.jsonl').open()) + 1 if (run/'attempts.jsonl').exists() else 1
            # Never capture headers: this is the only place a key enters HTTP.
            selected = shim.endpoint_module().connection('hy', 'codex', require_key=True)
            assert req.full_url == selected['base_url'] + '/responses'
            assert req.get_header('Authorization') == 'Bearer ' + selected['api_key']
            body = decode(req.data, req.get_header('Content-encoding', ''))
            write(run/f'upstream-{index:02d}.request.json', body)
            entry = dict(attempt=index, global_attempt=count, ingress=current.ingress,
                         url=req.full_url, model=body.get('model'), reasoning=body.get('reasoning'),
                         time=time.time())
            append(run/'attempts.jsonl', entry)
        try:
            response = opener(req, timeout=min(timeout, max(0.1, deadline-time.time())))
        except urllib.error.HTTPError as exc:
            response = exc
        except Exception as exc:
            append(run/'errors.jsonl', dict(attempt=index, error=type(exc).__name__, detail=str(exc)))
            raise
        append(run/'statuses.jsonl', dict(attempt=index, status=response.status, time=time.time()))
        return Observed(response, index)

    shim.upstream_open = observed_open

    class Handler(shim.Handler):
        def do_POST(self):
            raw = self.rfile.read(int(self.headers.get('Content-Length', 0)))
            with lock:
                index = sum(1 for _ in (run/'ingress.jsonl').open()) + 1 if (run/'ingress.jsonl').exists() else 1
                current.ingress = index
                body = decode(raw, self.headers.get('Content-Encoding', ''))
                append(run/'ingress.jsonl', dict(index=index, path=self.path, body=body,
                       lite_header=self.headers.get('x-openai-internal-codex-responses-lite'), time=time.time()))
            original = self.rfile
            self.rfile = io.BytesIO(raw)
            try: shim.Handler._handle(self)
            finally: self.rfile = original

    routes = json.loads((ROOT/'codex-agent/shim-routes.json').read_text())
    route = next(r for r in routes['routes'] if r['endpoint_id']=='hy') | {'from':routes['from']}
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    route['port'] = server.server_port
    server.route = route
    write(run/'port', str(server.server_port))
    server.serve_forever()


def clean_env(run):
    return dict(PATH=os.environ['PATH'], HOME=str(run/'home'), CODEX_HOME=str(run/'home/.codex'),
                CODEX_SHARED_HOME=str(run/'home/.codex'), CODEX_SQLITE_HOME=str(run/'sqlite'),
                TMPDIR=str(run/'tmp'), LANG='en_US.UTF-8', NO_PROXY='127.0.0.1,localhost')


def session_entry():
    # Authored explicitly, not derived from another provider or GPT instructions.
    return dict(slug='hy4', display_name='Hy4 isolated runtime probe',
                description='Repository-authored minimal native compatibility metadata; no capability certification.',
                default_reasoning_level='high', supported_reasoning_levels=[dict(effort='high', description='Documented Hy effort')],
                shell_type='unified_exec', visibility='hide', supported_in_api=True, priority=99,
                additional_speed_tiers=[], service_tiers=[], availability_nux=None, upgrade=None,
                model_messages=None, include_skills_usage_instructions=False,
                include_plugin_usage_instructions=False, include_apps_usage_instructions=False,
                default_reasoning_summary='none', support_verbosity=False, default_verbosity=None,
                apply_patch_tool_type=None, web_search_tool_type='text',
                truncation_policy=dict(mode='bytes', limit=10000), supports_image_detail_original=False,
                context_window=64000, max_context_window=64000, comp_hash=None,
                effective_context_window_percent=95, experimental_supported_tools=[], input_modalities=['text'],
                supports_search_tool=False, supports_experimental_context=False, use_responses_lite=False,
                supports_reasoning_effort_updates=False, node_repl_auto_review_required=False,
                node_repl_disabled=False, tool_mode='direct', multi_agent_version='v1',
                base_instructions='You are a coding assistant. Follow the user task using the advertised native tools. '
                'Read files before reporting their contents. Honor sandbox and approval policy. '
                'When the user explicitly requests an authorized escalation, use require_escalated with a clear justification. '
                'Do not bypass a denied review. Report actual observed tool output accurately and finish concisely.')


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def sse_events(raw):
    result = []
    for block in re.split(rb'\r?\n\r?\n', raw):
        data = b'\n'.join(line[5:].lstrip() for line in block.splitlines() if line.startswith(b'data:'))
        if not data or data == b'[DONE]': continue
        try: result.append(json.loads(data))
        except ValueError: result.append(dict(type='invalid-json', raw=data.decode(errors='replace')))
    return result


def analyze(run):
    import jsonschema
    ingress = records(run/'ingress.jsonl')
    attempts = records(run/'attempts.jsonl')
    statuses = {r['attempt']:r['status'] for r in records(run/'statuses.jsonl')}
    chunks = records(run/'chunks.jsonl')
    native = records(run/'native.jsonl')
    final = (run/'final.txt').read_text() if (run/'final.txt').exists() else ''
    canary = (run/'scratch/canary.txt').read_text().strip()
    sentinel = run/'authorized-sentinel.txt'
    calls = {}; outputs = {}; traffic = []; guardians = []
    for request in ingress:
        for item in request['body'].get('input', []):
            if item.get('type') in ('function_call','custom_tool_call'): calls[item.get('call_id')] = item
            if item.get('type') in ('function_call_output','custom_tool_call_output'): outputs[item.get('call_id')] = item
    for attempt in attempts:
        idx = attempt['attempt']
        before = next(r['body'] for r in ingress if r['index'] == attempt['ingress'])
        after = json.loads((run/f'upstream-{idx:02d}.request.json').read_text())
        response_path = run/f'upstream-{idx:02d}.response'
        raw = response_path.read_bytes() if response_path.exists() else b''
        events = sse_events(raw)
        positive = [c for c in chunks if c['attempt'] == idx and c['bytes']]
        completed = [e for e in events if e.get('type') == 'response.completed']
        for e in events:
            for item in [e.get('item') or {}] + (e.get('response', {}).get('output') or []):
                if item.get('type') in ('function_call','custom_tool_call'): calls[item.get('call_id')] = item
        # Locate deltas inside actual upstream read boundaries, not just event counts.
        delta_reads = []; offset = 0
        for c in positive:
            segment = raw[offset:offset+c['bytes']]; offset += c['bytes']
            if b'.delta' in segment: delta_reads.append(c['elapsed_seconds'])
        row = dict(attempt=idx, global_attempt=attempt['global_attempt'], ingress=attempt['ingress'],
                   kind='guardian' if before.get('model') == 'codex-auto-review' else 'session',
                   url=attempt['url'], native_model=before.get('model'), wire_model=after.get('model'),
                   native_reasoning=before.get('reasoning'), wire_reasoning=after.get('reasoning'),
                   native_lite_header=next(r['lite_header'] for r in ingress if r['index']==attempt['ingress']),
                   status=statuses.get(idx), chunks=positive, event_types=[e.get('type') for e in events],
                   delta_read_seconds=delta_reads, incremental=len(set(delta_reads)) >= 2,
                   completed=bool(completed), response_status=completed[-1]['response'].get('status') if completed else None,
                   usage=completed[-1]['response'].get('usage') if completed else None)
        if raw and not events:
            try: row['non_sse_response'] = json.loads(raw)
            except ValueError: row['non_sse_response'] = raw.decode(errors='replace')
        if row['kind'] == 'guardian':
            fmt = before.get('text', {}).get('format', {})
            verdict_text = ''.join(c.get('text', '') for e in completed
                for item in e.get('response', {}).get('output', []) for c in item.get('content', [])
                if c.get('type') == 'output_text')
            verdict = None; error = None
            try:
                if fmt.get('type') != 'json_schema': raise ValueError('Native request has no JSON schema')
                verdict = json.loads(verdict_text)
                jsonschema.validate(verdict, fmt['schema'])
            except Exception as exc: error = str(exc)
            guardian = dict(attempt=idx, schema=fmt, wire_format=after.get('text', {}).get('format'),
                            verdict=verdict, schema_valid=error is None, validation_error=error,
                            native_instructions_sha256=hashlib.sha256(json.dumps(before.get('instructions'),sort_keys=True).encode()).hexdigest(),
                            instructions_preserved=before.get('instructions') == after.get('instructions'),
                            native_input_sha256=hashlib.sha256(json.dumps(before.get('input'),sort_keys=True).encode()).hexdigest(),
                            input_preserved=before.get('input') == after.get('input'),
                            changed_request_fields=[k for k in before.keys() | after.keys() if before.get(k) != after.get(k)],
                            tools_preserved=before.get('tools') == after.get('tools'), completed=bool(completed))
            guardians.append(guardian)
        traffic.append(row)
    correlations = []
    for call_id, call in calls.items():
        output = outputs.get(call_id)
        command = call.get('arguments', call.get('input', ''))
        correlations.append(dict(call_id=call_id, name=call.get('name'), arguments=command,
                                 returned_in_later_native_request=output is not None,
                                 output=output, escalation_requested='require_escalated' in command,
                                 canary_in_output=bool(output and canary in json.dumps(output))))
    exit_info = json.loads((run/'exit.json').read_text())
    terminal = [e['type'] for e in native if e.get('type') in ('turn.completed','turn.failed','error')]
    result_path = run/'scratch/result.txt'
    scratch_ok = result_path.exists() and result_path.read_text().strip() == canary
    allowed = any(g['schema_valid'] and g['completed'] and g['verdict'].get('outcome') == 'allow' for g in guardians)
    escalation_continued = any(c['escalation_requested'] and c['returned_in_later_native_request']
                              and ('Exit code: 0' in json.dumps(c['output']) or
                                   'Process exited with code 0' in json.dumps(c['output'])) for c in correlations)
    # Native exec JSON tool output carries an exit_code field on some releases.
    if not escalation_continued:
        escalation_continued = any(c['escalation_requested'] and c['returned_in_later_native_request']
                                  and re.search(r'exit_code[\\"\s:]+0', json.dumps(c['output'])) for c in correlations)
    # Check the exact authorized command captured before native execution. A staged
    # setup loop once shadowed the marker name; the saved prompt is authoritative.
    match = re.search(r'using exactly this harmless command: ([^\n]+)', (run/'prompt.txt').read_text())
    authorized_command = match.group(1) if match else ''
    parts = shlex.split(authorized_command)
    marker = parts[2] if (len(parts)==5 and parts[:2]==['printf','%s'] and
                         parts[3:]==['>',str(sentinel)]) else None
    exact_escalation = any(c['escalation_requested'] and
        json.loads(c['arguments']).get('cmd') == authorized_command for c in correlations
        if c['name']=='exec_command')
    sentinel_ok = bool(marker is not None and exact_escalation and sentinel.exists()
                       and sentinel.read_text() == marker)
    criteria = dict(native_completed=exit_info['exit_code'] == 0 and 'turn.completed' in terminal and bool(final),
                    ordinary_incremental_completed=any(t['kind']=='session' and t['incremental'] and t['completed'] for t in traffic),
                    real_canary_continuation=any(c['canary_in_output'] for c in correlations) and scratch_ok and canary in final,
                    native_escalation_requested=any(c['escalation_requested'] for c in correlations),
                    structured_guardian_allow=allowed,
                    sentinel_executed=sentinel_ok,
                    escalation_result_continued=bool(escalation_continued))
    rollouts = []
    for path in (run/'home/.codex/sessions').rglob('*.jsonl'):
        selected = [e for e in records(path) if e.get('type')=='turn_context' or
                    (e.get('type')=='event_msg' and e.get('payload', {}).get('type') in ('token_count','task_complete'))]
        rollouts.append(dict(path=str(path), selected_metadata=selected))
    request_hashes = [hashlib.sha256(json.dumps(r['body'],sort_keys=True).encode()).hexdigest() for r in ingress]
    return dict(workflow=run.name, exit=exit_info, terminal=terminal, final=final, criteria=criteria,
                qualifies=all(criteria.values()), attempts=len(attempts), native_ingress_requests=len(ingress),
                guardian_attempts=len(guardians), retry_attempts=len(attempts)-len(set(a['ingress'] for a in attempts)),
                native_duplicate_request_retries=len(request_hashes)-len(set(request_hashes)),
                correlations=correlations, guardians=guardians, traffic=traffic, rollouts=rollouts,
                native_events=native, stderr=(run/'native.stderr').read_text(),
                upstream_errors=records(run/'errors.jsonl'), limits=records(run/'limits.jsonl'))


def run_one(batch, name, connection, native_catalog, codex, staged=False):
    run = batch/name
    for folder in ('home/.codex','home/.config/agent-tools','sqlite','tmp','scratch','stage'):
        (run/folder).mkdir(parents=True, mode=0o700, exist_ok=True)
    for path in run.rglob('*'):
        if not path.is_symlink() and path.is_dir(): path.chmod(0o700)
    for source, dest in [(ROOT/'codex-agent/bin/codex-auto-review-shim', run/'stage/codex-auto-review-shim'),
                         (ROOT/'scripts/agent-endpoint.py', run/'stage/agent-endpoint.py')]:
        shutil.copyfile(source, dest); dest.chmod(0o600)
    write(run/'stage/agent-endpoints.defaults.json', json.loads((ROOT/'config/endpoints.example.json').read_text()))
    write(run/'home/.config/agent-tools/endpoints.json', {'default':{'hy':{'codex':connection}}})
    write(run/'scratch/canary.txt', 'HY4_CANARY_' + secrets.token_hex(12) + '\n')
    guardian = copy.deepcopy(next(m for m in native_catalog['models'] if m['slug']=='codex-auto-review'))
    assert guardian['tool_mode']=='code_mode_only' and guardian['use_responses_lite'] is True
    guardian.update(tool_mode='direct', use_responses_lite=False)
    env = clean_env(run)
    if staged:
        stage = run/'stage'
        for staged_file in ('codex-agent-run','agent-tools.zsh','agent-endpoint.py','agent-run-result.py'):
            dest = stage/staged_file
            shutil.copyfile(ROOT/'scripts'/staged_file,dest)
            dest.chmod(0o755 if staged_file in ('codex-agent-run','agent-endpoint.py') else 0o600)
        card = run/'home/.codex/hy.config.toml'
        write(card,(ROOT/'codex-agent/profiles/hy/config.toml').read_text().replace('@HOME@/.codex',str(card.parent)))
        env.update(PATH=str(stage)+':'+env['PATH'], AGENT_TOOLS_FILE=str(stage/'launcher.zsh'))
        # Only loopback port selection is overridden; actual Hy launcher remains unchanged.
        write(stage/'launcher.zsh','source '+shlex.quote(str(stage/'agent-tools.zsh'))+'\n'
              '_codex_agent_shim_port() { [[ "$1" == hy ]] || return 1; cat '+shlex.quote(str(run/'port'))+'; }\n')
        generated = subprocess.run([sys.executable,str(ROOT/'scripts/patch-codex-model-catalog.py'),
                    '--profiles','hy','--cards-dir',str(card.parent),'--output-dir',str(card.parent/'model-catalogs')],
                    env=env,capture_output=True,text=True)
        write(run/'catalog-generation.json',dict(exit_code=generated.returncode,stdout=generated.stdout,stderr=generated.stderr))
        if generated.returncode: raise RuntimeError('Staged Hy catalog generation failed')
        shutil.copyfile(card.parent/'model-catalogs/hy.json',run/'catalog.json')
        write(run/'staged-sources.json',[dict(path=str(ROOT/source),sha256=hashlib.sha256((ROOT/source).read_bytes()).hexdigest())
              for source in ('scripts/codex-agent-run','scripts/agent-tools.zsh','scripts/agent-endpoint.py',
                             'scripts/patch-codex-model-catalog.py','codex-agent/profiles/hy/config.toml',
                             'codex-agent/model-providers.toml','codex-agent/shim-routes.json','config/endpoints.example.json')])
    else:
        write(run/'catalog.json', {'models':[session_entry(), guardian]})
    validate = subprocess.run([codex, '-c', 'model_catalog_json='+json.dumps(str(run/'catalog.json')),
                               'debug','models'], env=env, capture_output=True, text=True)
    write(run/'parser.stdout', validate.stdout); write(run/'parser.stderr', validate.stderr)
    write(run/'parser-exit', str(validate.returncode))
    if validate.returncode: raise RuntimeError('Native catalog parser rejected authored metadata; inspect private parser stderr')
    write(run/'deadline', str(time.time()+WORKFLOW_SECONDS))
    with (run/'shim.stdout').open('w') as stdout, (run/'shim.stderr').open('w') as stderr:
        server = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--serve', str(run), str(batch)],
                                  env=env, stdout=stdout, stderr=stderr, start_new_session=True)
    try:
        for _ in range(200):
            if (run/'port').exists(): break
            if server.poll() is not None: raise RuntimeError('Private shim failed before readiness')
            time.sleep(.025)
        else: raise RuntimeError('Private shim readiness timeout')
        port = int((run/'port').read_text())
        config = f'''model = "hy4"
model_provider = "hy_probe"
model_reasoning_effort = "high"
model_context_window = 64000
model_auto_compact_token_limit = 48000
model_catalog_json = {json.dumps(str(run/'catalog.json'))}
web_search = "disabled"
approval_policy = "on-request"
approvals_reviewer = "auto_review"
sandbox_mode = "workspace-write"

[features]
code_mode = false

[model_providers.hy_probe]
name = "Isolated Hy4 investigation"
base_url = "http://127.0.0.1:{port}/v1"
wire_api = "responses"
requires_openai_auth = false

[shell_environment_policy]
inherit = "core"
exclude = ["*KEY*", "*TOKEN*", "*SECRET*", "*AUTH*"]
'''
        if staged:
            # Base owns policy, final card owns model deltas. Only selected registry URL is ephemeral.
            registry = (ROOT/'codex-agent/model-providers.toml').read_text().replace('http://127.0.0.1:8796/v1',f'http://127.0.0.1:{port}/v1')
            config = ('approval_policy = "on-request"\napprovals_reviewer = "auto_review"\n'
                      'sandbox_mode = "workspace-write"\n[features]\ncode_mode = false\n'
                      '[shell_environment_policy]\ninherit = "core"\n'
                      'exclude = ["*KEY*", "*TOKEN*", "*SECRET*", "*AUTH*"]\n\n'+registry)
        write(run/'home/.codex/config.toml', config)
        sentinel = run/'authorized-sentinel.txt'
        command = 'printf %s ' + shlex.quote(name) + ' > ' + shlex.quote(str(sentinel))
        prompt = f'''This is a tiny, explicitly authorized isolated runtime integration test.
1. Use the native shell tool to read canary.txt, copy it to result.txt, and check result.txt. The canary is only in the file; never invent it.
2. Then call the native shell tool ONCE with sandbox_permissions="require_escalated" and justification="Authorized isolated Hy4 sentinel write outside scratch workspace", using exactly this harmless command: {command}
I explicitly authorize this unique sentinel write outside the scratch workspace within my private task temp. This request is part of testing automatic review: you MUST explicitly request require_escalated even if /private/tmp is normally writable. Do not add writable roots or change policy. If blocked, report it; do not write by another route or retry the escalation.
3. Consume the actual tool result, then finish with CANARY=<the value actually read> and a short factual status for the sentinel. Do not read config/auth or unrelated files. No network tools are necessary.'''
        write(run/'prompt.txt', prompt)
        argv = [codex,'exec','--json','--skip-git-repo-check','--color','never','-C',str(run/'scratch'),
                '-o',str(run/'final.txt'), prompt]
        if staged:
            argv = [str(run/'stage/codex-agent-run'),'--provider','hy','--cwd',str(run/'scratch'),
                    '--persist','--sandbox','workspace-write','--skip-git-repo-check',
                    '--prompt-file',str(run/'prompt.txt'),'--output',str(run/'native.jsonl'),
                    '--stderr',str(run/'native.stderr'),'--last-message',str(run/'final.txt')]
        write(run/'argv.json', argv)
        started = time.time(); timed_out = False
        with (run/('runner.stdout' if staged else 'native.jsonl')).open('w') as stdout, (run/('runner.stderr' if staged else 'native.stderr')).open('w') as stderr:
            child = subprocess.Popen(argv, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
            try: child.wait(timeout=max(0.1, float((run/'deadline').read_text())-time.time()))
            except subprocess.TimeoutExpired:
                timed_out = True; os.killpg(child.pid, signal.SIGTERM)
                try: child.wait(timeout=3)
                except subprocess.TimeoutExpired: os.killpg(child.pid, signal.SIGKILL); child.wait()
        write(run/'exit.json', dict(exit_code=child.returncode, runner_used=staged, timed_out=timed_out,
                                    elapsed_seconds=round(time.time()-started, 3)))
    finally:
        os.killpg(server.pid, signal.SIGTERM)
        try: server.wait(timeout=3)
        except subprocess.TimeoutExpired: os.killpg(server.pid, signal.SIGKILL); server.wait()
        for path in run.rglob('*'):
            if path.is_symlink(): continue
            if path.is_file(): path.chmod(0o600)
            elif path.is_dir(): path.chmod(0o700)
    result = analyze(run)
    write(run/'analysis.json', result)
    return result


def redact(value, keys):
    # Exact known key replacement plus defense against credential-bearing text.
    if isinstance(value, dict):
        return {k:redact(v, keys) for k,v in value.items()
                if k.lower() not in ('authorization','x-api-key','api-key','api_key','headers','raw_hex')}
    if isinstance(value, list): return [redact(v, keys) for v in value]
    if isinstance(value, str):
        for key in keys: value = value.replace(key, '[REDACTED]')
        value = re.sub(r'(?i)bearer\s+[A-Za-z0-9._~+/=-]+', 'Bearer [REDACTED]', value)
        value = re.sub(r'\b(?:sk|tk)-[A-Za-z0-9_-]{12,}\b', '[REDACTED]', value)
    return value


def publish(batch, results, keys, version):
    manifest = []
    for path in sorted(batch.rglob('*')):
        if path.is_symlink() or not path.is_file(): continue
        rel = path.relative_to(batch)
        # Exclude private configuration and native bootstrap/cache/plugin files.
        relevant = len(rel.parts)==1 or (len(rel.parts)>1 and rel.parts[0] in ('direct-1','direct-2','plan-1','plan-2') and (
            len(rel.parts)==2 or rel.parts[1] in ('scratch','shim-failed') or
            (rel.parts[1:4] == ('home','.codex','sessions'))))
        if not relevant or path.name in ('endpoints.json','config.toml','catalog.json'): continue
        manifest.append(dict(path=str(path),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    summary = copy.deepcopy(results)
    for workflow in summary:
        stderr = workflow.pop('stderr')
        messages = Counter(re.sub(r'^\S+ (?:ERROR|WARN) ', '', line) for line in stderr.splitlines())
        workflow['stderr_summary'] = dict(lines=len(stderr.splitlines()), messages=dict(messages))
        for event in workflow['native_events']:
            item = event.get('item', {})
            if item.get('type')=='reasoning' and 'text' in item:
                text = item.pop('text')
                item.update(text_characters=len(text),text_sha256=hashlib.sha256(text.encode()).hexdigest())
        for traffic in workflow['traffic']:
            chunks = traffic.pop('chunks')
            traffic['chunk_summary'] = dict(nonempty_reads=len(chunks),bytes=sum(c['bytes'] for c in chunks),
                first_seconds=chunks[0]['elapsed_seconds'] if chunks else None,
                last_seconds=chunks[-1]['elapsed_seconds'] if chunks else None)
            times = traffic.pop('delta_read_seconds')
            traffic['delta_reads'] = dict(count=len(times),first_seconds=times[0] if times else None,
                last_seconds=times[-1] if times else None, sample_seconds=times[:3]+times[-3:] if len(times)>6 else times)
            types = traffic.pop('event_types')
            traffic['event_type_counts'] = dict(Counter(types))
    source_paths = [ROOT/'codex-agent/bin/codex-auto-review-shim',ROOT/'scripts/agent-endpoint.py',
                    ROOT/'tests/test_official_catalog_runtime.py',ROOT/'scripts/patch-codex-model-catalog.py',
                    Path(__file__).resolve(), OUT/'probe-declaration.md']
    result = redact(dict(schema_version=1, batch=str(batch), version=version,
                         shared_upstream_attempts=int((batch/'attempt-count').read_text()),
                         credential_checks=dict(keys_distinct=True,plan_runtime='codex',plan_claude_key_agrees=True),
                         selected_source_urls=['https://cloud.tencent.com/document/product/1823/'+n
                             for n in ('130070','130071','130060','132252','131208')],
                         source_artifacts=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in source_paths],
                         workflows=summary,raw_private_artifacts=manifest), keys)
    text = json.dumps(result, indent=2)+'\n'
    assert not any(key in text for key in keys)
    (OUT/'investigation-results.json').write_text(text)
    trace = [dict(workflow=r['workflow'], ingress=records(batch/r['workflow']/'ingress.jsonl')) for r in results]
    trace_text = json.dumps(redact(trace,keys),indent=2)+'\n'
    assert not any(key in trace_text for key in keys)
    (OUT/'investigation-traces.json').write_text(trace_text)
    print(json.dumps(dict(event='complete',batch=str(batch),shared_upstream_attempts=result['shared_upstream_attempts'])),flush=True)


def staged_main():
    """One final direct workflow, separately declared; never reruns Plan."""
    batch = TASK/('staged-' + time.strftime('%Y%m%d-%H%M%S'))
    batch.mkdir(mode=0o700, parents=True)
    write(batch/'attempt-count','0'); write(batch/'max-attempts','12')
    private = json.loads((Path.home()/'.config/agent-tools/endpoints.json').read_text())
    key = private['default']['hy']['claude']['api_key']
    assert key.strip()
    del private
    codex = shutil.which('codex')
    inspect = batch/'inspect'
    for name in ('home/.codex','sqlite','tmp'): (inspect/name).mkdir(mode=0o700,parents=True,exist_ok=True)
    native = subprocess.run([codex,'debug','models','--bundled'],env=clean_env(inspect),capture_output=True,text=True,check=True)
    print(json.dumps(dict(event='staged_start',batch=str(batch),max_seconds=300,max_upstream_attempts=12)),flush=True)
    result = run_one(batch,'staged-direct',dict(base_url='https://tokenhub.tencentmaas.com/v1',upstream_model='hy4',api_key=key),json.loads(native.stdout),codex,staged=True)
    return publish_staged(batch, result, key)


def publish_staged(batch, result, key):
    # Explicit allowlist excludes private endpoints/config, keys and headers.
    files = {}
    run = batch/'staged-direct'
    for path in run.iterdir():
        if path.is_symlink() or not path.is_file(): continue
        if (path.suffix in ('.response',) or path.name.startswith('upstream-') or
            path.name in ('analysis.json','native.jsonl','native.stderr','runner.stdout','runner.stderr',
                          'ingress.jsonl','attempts.jsonl','statuses.jsonl','chunks.jsonl','argv.json',
                          'exit.json','parser-exit','staged-sources.json','catalog-generation.json','final.txt','prompt.txt')):
            files[path.name]=redact(path.read_text(errors='replace'),[key])
    import gzip
    evidence = redact(dict(result=result,files=files),[key])
    raw = json.dumps(evidence,indent=2).encode()
    assert key.encode() not in raw
    archive = OUT/'staged-integration-evidence.json.gz'
    archive.write_bytes(gzip.compress(raw,mtime=0))
    summary = dict(workflow=result['workflow'],batch=str(batch),exit=result['exit'],criteria=result['criteria'],
                   qualifies=result['qualifies'],attempts=result['attempts'],guardian_attempts=result['guardian_attempts'],
                   retry_attempts=result['retry_attempts'],limits=result['limits'],
                   archive=dict(path=archive.name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                                bytes=archive.stat().st_size,uncompressed_bytes=len(raw),entries=list(files)))
    (OUT/'staged-integration-results.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary),flush=True)
    return 0 if result['qualifies'] else 1


def main():
    os.umask(0o077)
    TASK.mkdir(mode=0o700, exist_ok=True)
    summarize = sys.argv[1:2] == ['--summarize']
    resume = summarize or sys.argv[1:2] == ['--resume']
    batch = Path(sys.argv[2]) if resume else TASK/('investigation-' + time.strftime('%Y%m%d-%H%M%S'))
    assert batch.parent == TASK
    batch.mkdir(mode=0o700, exist_ok=resume)
    private = json.loads((Path.home()/'.config/agent-tools/endpoints.json').read_text())
    direct_key = private['default']['hy']['claude']['api_key']
    plan_key = private['override']['ds-flash']['codex']['api_key']
    assert direct_key.strip() and plan_key.strip() and direct_key != plan_key
    assert private['override']['ds-flash']['claude']['api_key'] == plan_key
    del private
    keys = [direct_key, plan_key]
    if summarize:
        results = [analyze(batch/name) for name in ('direct-1','direct-2','plan-1','plan-2')]
        for r in results: write(batch/r['workflow']/'analysis.json', r)
        publish(batch,results,keys,json.loads((batch/'version.json').read_text())['stdout'].strip())
        return
    if not resume: write(batch/'attempt-count', '0')
    inspect = batch/'inspect'
    for folder in ('home/.codex','sqlite','tmp'): (inspect/folder).mkdir(parents=True, mode=0o700, exist_ok=resume)
    env = clean_env(inspect)
    codex = shutil.which('codex')
    version = subprocess.run([codex,'--version'], env=env, capture_output=True, text=True)
    assert version.returncode == 0 and version.stdout.strip() == 'codex-cli 0.166.0'
    write(batch/'version.json', dict(argv=[codex,'--version'],stdout=version.stdout, stderr=version.stderr,exit_code=version.returncode))
    native = subprocess.run([codex,'debug','models','--bundled'],env=env,capture_output=True,text=True,check=True)
    write(batch/'bundled.json', native.stdout)
    catalog = json.loads(native.stdout)
    results = []
    for route, base, key in [('direct','https://tokenhub.tencentmaas.com/v1',direct_key),
                             ('plan','https://tokenhub.tencentmaas.com/plan/v3',plan_key)]:
        for number in (1,2):
            name = f'{route}-{number}'
            if resume and (batch/name/'exit.json').exists():
                result = analyze(batch/name)
                write(batch/name/'analysis.json', result)
                results.append(result)
                print(json.dumps(dict(event='preserved', workflow=name, exit=result['exit'],
                                      criteria=result['criteria'],attempts=result['attempts'])), flush=True)
                continue
            print(json.dumps(dict(event='start', workflow=name, private_root=str(batch/name))), flush=True)
            result = run_one(batch, name, dict(base_url=base,upstream_model='hy4',api_key=key),catalog,codex)
            results.append(result)
            print(json.dumps(dict(event='finished', workflow=name, exit=result['exit'], criteria=result['criteria'],
                                  attempts=result['attempts'])), flush=True)
    publish(batch,results,keys,version.stdout.strip())


if __name__ == '__main__':
    os.umask(0o077)
    if sys.argv[1:2] == ['--serve']: serve(Path(sys.argv[2]), Path(sys.argv[3]))
    elif sys.argv[1:2] == ['--staged']: sys.exit(staged_main())
    else: main()
