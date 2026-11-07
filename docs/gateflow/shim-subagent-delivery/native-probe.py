#!/usr/bin/env python3
"""Real-model native regression. No deployment or credential/config writes.

Run from the checkout: python3 docs/gateflow/shim-subagent-delivery/native-probe.py
Requires installed Codex 0.167.0 + DeepSeek catalog and managed shim on 8788.
A candidate Handler listens on an OS-assigned loopback port, forwarding to 8788.
Only the app-server child receives process-local config overrides. Evidence is
allowlisted; no headers, full prompts, private configuration or global context.
No fake SSE, direct child RPC, synthetic function calls, or forced termination.
"""
import collections
import gzip
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import queue
import re
import subprocess
import tempfile
import threading
import time
import uuid
import zlib

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(tempfile.mkdtemp(prefix='shim-subagent-candidate-'))
CWD = OUT / 'workspace'
CWD.mkdir()
FIXTURE = CWD / 'harmless-target.txt'
FIXTURE_TEXT = 'HARMLESS_NATIVE_CONTENT_' + uuid.uuid4().hex
FIXTURE.write_text(FIXTURE_TEXT)
TOKEN = 'LIVE_MESSAGE_OK_' + uuid.uuid4().hex[:12]
loader = importlib.machinery.SourceFileLoader('candidate_shim', str(ROOT / 'codex-agent/bin/codex-auto-review-shim'))
spec = importlib.util.spec_from_loader(loader.name, loader)
shim = importlib.util.module_from_spec(spec)
loader.exec_module(shim)
shim.FAILED_DIR = str(OUT / 'failed')  # never write to ~/.codex-agent
wire = []
lock = threading.Lock()
original_fix = shim.fix_agent_messages
original_open = shim.upstream_open


def sha(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def observe_fix(body):
    out, count = original_fix(body)
    doc, fixed = json.loads(body), json.loads(out)
    record = {'thread_id': doc.get('client_metadata', {}).get('thread_id'),
              'ingress_sha256': sha(body), 'egress_sha256': sha(out),
              'model': doc.get('model'), 'stream': doc.get('stream'),
              'types': dict(collections.Counter(i.get('type') for i in doc.get('input', []) if isinstance(i, dict))),
              'converted': count, 'items': [], 'non_target_items_equal': True,
              'non_input_fields_equal': {k: v for k, v in doc.items() if k != 'input'} == {k: v for k, v in fixed.items() if k != 'input'}}
    for index, (before, after) in enumerate(zip(doc.get('input', []), fixed.get('input', []))):
        if before.get('type') == 'agent_message':
            record['items'].append({'index': index, 'ingress': before, 'egress': after})
        elif before != after:
            record['non_target_items_equal'] = False
    with lock:
        wire.append(record)
    return out, count


def observe_open(req, timeout):
    body = req.data
    enc = (req.get_header('Content-encoding') or '').lower()
    body = {'gzip': gzip.decompress, 'deflate': zlib.decompress}.get(enc, lambda x: x)(body)
    with lock:
        matches = [r for r in wire if r['egress_sha256'] == sha(body)]
        for record in matches:
            record['actual_upstream_body_verified'] = True
    # Headers/credentials never enter evidence; installed 8788 owns auth.
    return original_open(req, timeout)


shim.fix_agent_messages = observe_fix
shim.upstream_open = observe_open
server = shim._make_server({'listen': '127.0.0.1:0', 'upstream': 'http://127.0.0.1:8788',
                           'from': 'codex-auto-review', 'to': 'deepseek-flash', 'agent_message_fix': True})
port = server.server_address[1]
server.route['port'] = port
listener = threading.Thread(target=server.serve_forever)
listener.start()
version = subprocess.check_output(['codex', '--version'], text=True).strip()
if version != 'codex-cli 0.167.0':
    server.shutdown(); server.server_close(); listener.join()
    raise SystemExit('This diagnostic requires codex-cli 0.167.0')
catalog = Path.home() / '.codex/model-catalogs/ds-flash.json'
settings = {
    'model_provider': 'deepseek', 'model': 'deepseek-flash',
    'model_catalog_json': str(catalog), 'model_reasoning_effort': 'max',
    'model_providers.deepseek.name': 'DeepSeek',
    'model_providers.deepseek.base_url': f'http://127.0.0.1:{port}/v1',
    'model_providers.deepseek.wire_api': 'responses',
    'model_providers.deepseek.requires_openai_auth': False,
    'features.apps': False, 'features.plugins': False, 'web_search': 'disabled',
    'approval_policy': 'never', 'sandbox_mode': 'read-only',
}
cmd = ['codex', 'app-server']
for key, value in settings.items():
    cmd += ['-c', key + '=' + json.dumps(value)]
# These are process overrides only; managed endpoint credentials remain in 8788.
(OUT / 'command.json').write_text(json.dumps(cmd, indent=2))
print('PROBE_DIR=' + str(OUT), flush=True)
print('CANDIDATE_PORT=' + str(port), flush=True)
stderr = (OUT / 'app-server.stderr').open('w')
proc = subprocess.Popen(cmd, cwd=CWD, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr, text=True, bufsize=1)
messages = queue.Queue()


def reader():
    for line in proc.stdout:
        try:
            messages.put(json.loads(line))
        except ValueError:
            messages.put({'parse_error': True})
    messages.put(None)


thread = threading.Thread(target=reader)
thread.start()


def send(method, params, request_id=None):
    msg = {'method': method, 'params': params}
    if request_id is not None:
        msg['id'] = request_id
    proc.stdin.write(json.dumps(msg) + '\n'); proc.stdin.flush()


parent_id = None
turn_done = False
errors = []
started = time.time()
prompt = f'''NATIVE_CANDIDATE_PROBE. This is an explicitly authorized isolated native collaboration diagnostic. Do these steps exactly once, in sequence; no retries or repairs. Use only native collaboration tools in the parent. Never use shell or read files in the parent. Do not interrupt or close agents.
A1: spawn_agent task_name=delivery_a fork_turns=none. Message exactly: "NATIVE_CANDIDATE_PROBE initial. Reply exactly one line LIVE_PROBE_OK. Do not use tools, read/write files, or delegate." Wait for its actual final using wait_agent/list_agents.
A2: followup_task to SAME child /root/delivery_a. Message exactly: "NATIVE_CANDIDATE_PROBE followup. Reply exactly one line LIVE_FOLLOWUP_OK. Do not use tools, read/write files, or delegate." Wait for its NEW final; distinguish it from the old final.
A3: send_message to SAME idle child with message exactly: "NATIVE_CANDIDATE_PROBE MESSAGE token: {TOKEN}. Remember this token for the next task."
Then followup_task to SAME child with message exactly: "NATIVE_CANDIDATE_PROBE consume-message. Reply exactly the token in your most recent MESSAGE. Do not use tools, read/write files, or delegate." Wait for its new final. Do not include the token in this followup task message.
B: spawn_agent task_name=delivery_b fork_turns=none. Message exactly: "NATIVE_CANDIDATE_PROBE file task. Use exec_command to read only the harmless fixture {FIXTURE} with cat. Return exactly its entire contents as final, no formatting. Do not delegate, read other files or write anything." Wait for its actual final. The contents are unknown to you; never read the file yourself. Do not send guesses to the child.
After both children finish, report the actual observed finals. Parent self-report is only informational; external rollout and wire evidence determines success. If any native tool is unavailable report it; do not simulate function calls or child responses.'''
try:
    send('initialize', {'clientInfo': {'name': 'shim_native_candidate', 'title': 'Shim native candidate', 'version': '1'}, 'capabilities': {'experimentalApi': True}}, 0)
    while True:
        try:
            msg = messages.get(timeout=30)
        except queue.Empty:
            print(f'WAITING elapsed={int(time.time()-started)} requests={len(wire)}', flush=True)
            continue
        if msg is None:
            errors.append({'process_eof_before_completed': not turn_done})
            break
        if msg.get('error'):
            errors.append(msg['error'])
            break
        if msg.get('id') == 0 and 'result' in msg:
            send('initialized', {})
            send('thread/start', {'model': 'deepseek-flash', 'modelProvider': 'deepseek', 'cwd': str(CWD), 'sandbox': 'read-only', 'approvalPolicy': 'never', 'experimentalRawEvents': True}, 1)
        if msg.get('id') == 1 and 'result' in msg:
            parent_id = msg['result']['thread']['id']
            print('PARENT_ID=' + parent_id, flush=True)
            send('turn/start', {'threadId': parent_id, 'input': [{'type': 'text', 'text': prompt}]}, 2)
        if msg.get('method') == 'turn/completed' and msg.get('params', {}).get('threadId') == parent_id:
            turn_done = True
            status = msg['params']['turn']['status']
            print('PARENT_TURN_STATUS=' + status, flush=True)
            if status != 'completed':
                errors.append({'turn_status': status})
            break
finally:
    # No kill/interrupt: completed parent turns are closed via EOF and joined.
    proc.stdin.close()
    code = proc.wait()
    thread.join()
    stderr.close()
    server.shutdown(); server.server_close(); listener.join()

# Read only new rollout IDs seen by our candidate; do not scan unrelated text.
ids = {r['thread_id'] for r in wire if r.get('thread_id')}
if parent_id:
    ids.add(parent_id)
rollouts = []
for tid in sorted(ids):
    paths = list((Path.home() / '.codex/sessions').glob(f'*/*/*/*{tid}.jsonl'))
    for path in paths:
        selected = []
        identity = {}
        for line_no, line in enumerate(path.read_text().splitlines(), 1):
            item = json.loads(line)
            payload = item.get('payload', {})
            if item['type'] == 'session_meta':
                identity = {k: payload.get(k) for k in ('id', 'parent_thread_id', 'cli_version', 'model_provider', 'agent_path', 'source', 'cwd')}
            if item['type'] == 'response_item':
                keep = payload.get('type') in ('agent_message', 'function_call', 'function_call_output') or (payload.get('type') == 'message' and payload.get('role') == 'assistant')
                if keep:
                    selected.append({'line': line_no, 'item': payload})
            if item['type'] == 'event_msg' and payload.get('type') in ('task_started', 'task_complete'):
                selected.append({'line': line_no, 'event': payload})
        rollouts.append({'file': path.name, 'identity': identity, 'events': selected})
children = {r['identity'].get('agent_path'): r for r in rollouts if r['identity'].get('parent_thread_id') == parent_id}


def finals(rollout):
    return [''.join(p.get('text', '') for p in e['item'].get('content', [])) for e in rollout.get('events', []) if e.get('item', {}).get('type') == 'message' and e['item'].get('role') == 'assistant' and e['item'].get('phase') == 'final_answer']


a = children.get('/root/delivery_a', {})
b = children.get('/root/delivery_b', {})
a_finals, b_finals = finals(a), finals(b)
b_calls = [e['item'] for e in b.get('events', []) if e.get('item', {}).get('type') == 'function_call']
b_outputs = [e['item'] for e in b.get('events', []) if e.get('item', {}).get('type') == 'function_call_output']
read_calls = [c for c in b_calls if 'exec_command' in c.get('name', '') and str(FIXTURE) in c.get('arguments', '') and 'cat' in c.get('arguments', '')]
read_outputs = [o for o in b_outputs if o.get('call_id') in {c['call_id'] for c in read_calls}]
parent = next((r for r in rollouts if r['identity'].get('id') == parent_id), {})
parent_calls = [e['item'] for e in parent.get('events', []) if e.get('item', {}).get('type') == 'function_call']
# Also verify fixture absence from every actual parent/child task, not just prompt.
all_tasks = [json.dumps(e['item']) for r in rollouts for e in r['events'] if e.get('item', {}).get('type') == 'agent_message']
checks = {
    'parent_completed': turn_done and not errors and code == 0,
    'A_exact_initial_followup_message_finals': a_finals == ['LIVE_PROBE_OK', 'LIVE_FOLLOWUP_OK', TOKEN],
    'A_native_spawn_followup_send': all(any(name in c.get('name', '') for c in parent_calls) for name in ('spawn_agent', 'followup_task', 'send_message')),
    'B_exact_file_final': b_finals == [FIXTURE_TEXT],
    'B_actual_child_cat_output_exit_zero': bool(read_calls) and any(FIXTURE_TEXT in o.get('output', '') and re.search(r'exit(?:ed with)? code[: ]+0', o.get('output', ''), re.I) for o in read_outputs),
    'B_content_absent_from_prompts_tasks': FIXTURE_TEXT not in prompt and all(FIXTURE_TEXT not in text for text in all_tasks if 'FINAL_ANSWER' not in text),
    'wire_all_egress_verified': bool(wire) and all(r.get('actual_upstream_body_verified') and r['non_target_items_equal'] and r['non_input_fields_equal'] for r in wire),
    'wire_native_children_converted': bool(a) and bool(b) and all(any(r['thread_id'] == c['identity']['id'] and r['converted'] for r in wire) for c in (a, b)),
}
summary = {'version': version, 'parent_id': parent_id, 'children': {k: v['identity']['id'] for k, v in children.items()},
           'cwd': str(CWD), 'candidate_port': port, 'upstream': 'installed loopback 8788 (managed credentials)',
           'app_server_exit': code, 'errors': errors, 'elapsed_seconds': round(time.time()-started, 2),
           'fixture': {'path': str(FIXTURE), 'contents': FIXTURE_TEXT, 'sha256': sha(FIXTURE_TEXT)},
           'message_token': TOKEN, 'A_finals': a_finals, 'B_finals': b_finals, 'checks': checks,
           'passed': all(checks.values()), 'command': cmd, 'parent_prompt': prompt}
(OUT / 'wire.json').write_text(json.dumps(wire, ensure_ascii=False, indent=2))
(OUT / 'rollouts-sanitized.json').write_text(json.dumps(rollouts, ensure_ascii=False, indent=2))
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
print(json.dumps({k: summary[k] for k in ('parent_id', 'children', 'A_finals', 'B_finals', 'checks', 'passed', 'app_server_exit', 'elapsed_seconds')}, indent=2), flush=True)
raise SystemExit(0 if summary['passed'] else 1)
