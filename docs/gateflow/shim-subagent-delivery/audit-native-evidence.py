#!/usr/bin/env python3
"""Independent checks of durable captures, without calling a model or helper."""
import argparse
import hashlib
import gzip
import json
import re
from pathlib import Path

def legacy_audit(root):
    reports = []
    for directory in sorted(root.glob('candidate-run-*')):
        summary = json.loads((directory / 'summary.json').read_text())
        wire = json.loads((directory / 'wire.json').read_text())
        rollouts = json.loads((directory / 'rollouts-sanitized.json').read_text())
        parent = next(r for r in rollouts if r['identity']['id'] == summary['parent_id'])
        children = {r['identity']['agent_path']: r for r in rollouts if r['identity']['parent_thread_id'] == summary['parent_id']}
        calls = [e['item'] for e in parent['events'] if e.get('item', {}).get('type') == 'function_call']
        dispatches = [(c['name'], json.loads(c['arguments'])) for c in calls if c['name'] in ('spawn_agent', 'followup_task', 'send_message')]
        assert [n for n, _ in dispatches] == ['spawn_agent', 'followup_task', 'send_message', 'followup_task', 'spawn_agent']
        assert [args['task_name'] for name, args in dispatches if name == 'spawn_agent'] == ['delivery_a', 'delivery_b']
        assert all(args['fork_turns'] == 'none' for name, args in dispatches if name == 'spawn_agent')
        assert all(args['target'] == '/root/delivery_a' for name, args in dispatches if name != 'spawn_agent')
        assert summary['message_token'] in dispatches[2][1]['message']
        assert summary['message_token'] not in dispatches[3][1]['message']
        fixture = summary['fixture']['contents']
        assert fixture not in summary['parent_prompt']
        assert all(fixture not in args['message'] for _, args in dispatches)
        assert not any('exec_command' in c['name'] for c in calls)
        item_count = 0
        for record in wire:
            assert record['actual_upstream_body_verified']
            assert record['non_target_items_equal'] and record['non_input_fields_equal']
            for pair in record['items']:
                before, after = pair['ingress'], pair['egress']
                assert after['type'] == 'message' and after['role'] == 'user'
                assert set(after) == {'type', 'role', 'content'}
                metadata = json.loads(after['content'][0]['text'].split(': ', 1)[1])
                assert metadata == {k: v for k, v in before.items() if k not in ('type', 'content')}
                assert [p['text'] for p in after['content'][1:]] == [p['text'] if p['type'] == 'input_text' else p['encrypted_content'] for p in before['content']]
                assert all(p['type'] == 'input_text' for p in after['content'])
                item_count += 1
        actual_finals = {}
        final_turn_ids = {}
        for path, child in children.items():
            assert child['identity']['model_provider'] == 'deepseek' and child['identity']['cli_version'] == '0.167.0'
            finals = [e['item'] for e in child['events'] if e.get('item', {}).get('type') == 'message' and e['item'].get('phase') == 'final_answer']
            actual_finals[path] = [''.join(p['text'] for p in f['content']) for f in finals]
            final_turn_ids[path] = [f['internal_chat_message_metadata_passthrough']['turn_id'] for f in finals]
        assert actual_finals['/root/delivery_a'] == ['LIVE_PROBE_OK', 'LIVE_FOLLOWUP_OK', summary['message_token']]
        assert len(set(final_turn_ids['/root/delivery_a'])) == 3
        assert actual_finals['/root/delivery_b'] == [fixture]
        b = children['/root/delivery_b']
        b_calls = [e['item'] for e in b['events'] if e.get('item', {}).get('type') == 'function_call']
        assert len(b_calls) == 1 and b_calls[0]['name'] == 'exec_command'
        args = json.loads(b_calls[0]['arguments'])
        assert args['cmd'] == 'cat ' + summary['fixture']['path']
        outputs = [e['item'] for e in b['events'] if e.get('item', {}).get('type') == 'function_call_output' and e['item']['call_id'] == b_calls[0]['call_id']]
        assert len(outputs) == 1 and 'Process exited with code 0' in outputs[0]['output']
        assert outputs[0]['output'].split('Output:\n', 1)[1] == fixture
        assert summary['app_server_exit'] == 0 and all(summary['checks'].values())
        reports.append({'run': directory.name, 'parent_id': summary['parent_id'], 'requests': len(wire),
                        'target_items_including_replayed_history': item_count, 'final_turn_ids': final_turn_ids,
                        'child_file_tool_call_id': b_calls[0]['call_id'], 'all_checks_passed': True})
    return reports

def text_content(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return ''.join(p.get('text', '') for p in value if isinstance(p, dict))
    return ''


def items(rollout, *types):
    return [e['item'] for e in rollout.get('events', []) if e.get('item', {}).get('type') in types]


def completed_finals(rollout):
    """Pair native completed turns with their own final response, including Lite
    messages which have no phase. Never accept parent reports as child finals.
    """
    result = []
    seen = set()
    for event in rollout.get('events', []):
        complete = event.get('event', {})
        if complete.get('type') != 'task_complete':
            continue
        turn = complete['turn_id']
        assert turn not in seen, 'duplicate completed turn'
        seen.add(turn)
        responses = [e['item'] for e in rollout['events'] if e['line'] < event['line'] and e.get('item', {}).get('type') == 'message'
                     and e['item'].get('role') == 'assistant' and e['item'].get('internal_chat_message_metadata_passthrough', {}).get('turn_id') == turn]
        assert responses, 'completed turn without child assistant response'
        final = responses[-1]
        assert final.get('phase') in (None, 'final_answer'), 'last message is not final'
        value = text_content(final['content'])
        assert complete['last_agent_message'] == value, 'completion/final mismatch'
        result.append({'turn_id': turn, 'text': value, 'completed_at': complete.get('completed_at')})
    return result


def descriptor_names(descriptors):
    names = set()
    for descriptor in descriptors:
        names.add(descriptor.get('name'))
        names.update(descriptor_names(descriptor.get('tools', [])))
    return names


def declared_scenario(record):
    """Resolve the launch argv, rejecting ambiguous/invalid declarations."""
    argv = record['driver_argv'][2:]
    parser = argparse.ArgumentParser(exit_on_error=False)
    parser.add_argument('--profile')
    parser.add_argument('--evidence-dir')
    parser.add_argument('--attempt')
    parser.add_argument('--initial-marker')
    parser.add_argument('--scenario', choices=('all', 'a', 'b'), default='all')
    assert sum(a == '--scenario' or a.startswith('--scenario=') for a in argv) <= 1, 'duplicate scenario option'
    try:
        parsed, unknown = parser.parse_known_args(argv)
    except argparse.ArgumentError as exc:
        raise ValueError(str(exc)) from exc
    assert not unknown, 'unknown driver options'
    assert parsed.profile == record['profile'] and parsed.attempt == record['attempt'], 'driver identity mismatch'
    assert parsed.scenario == record.get('scenario', 'all'), 'declared scenario/driver argv mismatch'
    return parsed.scenario


def audit_namespace_record(summary, record):
    """Independent new-stage contract, required only by actual opted-in routes."""
    route=summary['route']
    if not route.get('native_agent_response_restore'):
        return record['egress_sha256']
    if record.get('model')=='codex-auto-review':
        assert record['native_stage_bypass']=='guardian' and 'native_request_stage' not in record
        return record['egress_sha256']
    stage=record['native_request_stage']
    assert stage['before_sha256']==record['egress_sha256'], 'native stage not after agent-message stage'
    assert stage['flatten']==route.get('native_agent_request_flatten',False)
    assert stage['outside_tools_equal'], 'native request changed history/non-tools'
    assert all(change['path'] and change['path'][0]=='tools' for change in stage['changes']), 'native change outside tools'
    before=stage['before_tools'];after=stage['after_tools']
    top=before if isinstance(before,list) else []
    selected=[(i,t) for i,t in enumerate(top) if isinstance(t,dict) and t.get('type')=='namespace' and t.get('name') in ('multi_agent_v1','collaboration')]
    # These immutable launch helpers predate the accepted additional-tools source.
    # Missing new fields are permitted only for these known historical versions.
    legacy=summary.get('source_hashes_at_launch',{}).get('codex-agent/bin/codex-auto-review-shim') in (
        '5d47d38af39bcb1819f4076ee7fc379c3bb98d53071650639115537f9f1aba12',
        '7cdaf30d198433d261672185ef11ee12b4f155294c60fbd22b61f0401012493d')
    if legacy:
        groups=[t for _,t in selected]
        assert [entry for entry in record['descriptor_locations'] if entry['path'][0]=='tools']==[{'path':['tools',i],'descriptor':t} for i,t in selected], 'missing exact descriptor location'
    else:
        assert stage['descriptor_source_version']==2, 'missing current source contract'
        sources=stage['descriptor_sources']
        assert sources==record['descriptor_sources'], 'ingress/native source projection mismatch'
        locations=[];groups=[];paths=[];seen=[]
        for source in sources:
            path=source['path']
            assert path not in seen, 'repeated source container'
            seen.append(path)
            if path==['tools']:
                assert source['containing_item_type'] is None
                assert isinstance(before,list)
                projection=[t if isinstance(t,dict) and t.get('type')=='namespace' and t.get('name') in ('multi_agent_v1','collaboration')
                            else {k:t[k] for k in ('type','name') if k in t} if isinstance(t,dict) else None for t in before]
                assert source['tools']==projection, 'top-level source projection mismatch'
            else:
                assert len(path)==3 and path[0]=='input' and type(path[1]) is int and path[1]>=0 and path[2]=='tools', 'unknown descriptor source'
                assert source['containing_item_type']=='additional_tools', 'wrong containing item type'
            assert isinstance(source['tools'],list)
            for j,t in enumerate(source['tools']):
                if isinstance(t,dict) and t.get('type')=='namespace' and t.get('name') in ('multi_agent_v1','collaboration'):
                    locations.append({'path':path+[j],'containing_item_type':source['containing_item_type'],'descriptor':t})
                    if not stage['flatten'] or path==['tools']:
                        groups.append(t);paths.append(path+[j])
        assert (['tools'] in seen)==isinstance(before,list), 'missing top-level source'
        assert record['descriptor_locations']==locations, 'missing exact descriptor location/type'
        assert [entry['descriptor'] for entry in locations]==[
            t for t in record['native_descriptors'] if isinstance(t,dict) and t.get('type')=='namespace'
            and t.get('name') in ('multi_agent_v1','collaboration')], 'missing native source projection'
        assert stage['selected_descriptor_paths']==paths, 'wrong selected source paths'
    mapping={}
    for group in groups:
        assert isinstance(group.get('tools'),list)
        for child in group['tools']:
            assert child.get('type')=='function' and isinstance(child.get('name'),str) and child['name']
            assert child['name'] not in mapping, 'duplicate selected native callable'
            mapping[child['name']]=group['name']
    assert stage['map']==mapping, 'wrong or empty native map'
    expected=[]
    for i,t in enumerate(top):
        if stage['flatten'] and any(i==j for j,_ in selected):
            prefix='Namespace '+t['name']+': '+t.get('description','')+'\n\n'
            expected.extend({**child,'description':prefix+child.get('description','')} for child in t['tools'])
        else:expected.append(t)
    assert after==(expected if isinstance(before,list) else before), 'unallowed native descriptor change'
    if not stage['flatten'] or not mapping:
        assert stage['after_sha256']==stage['before_sha256'] and not stage['changes']
    for attempt in record['outbound_attempts']:
        metadata=attempt['response_metadata']
        assert 200 <= attempt['http_status'] < 300
        if mapping:
            assert all(value.strip().lower()=='identity' for value in metadata['Content-Encoding']), 'active response is not identity'
        assert len(metadata['Content-Type'])==1 and metadata['Content-Type'][0].split(';')[0].strip().lower() in ('text/event-stream','application/json')
        if not legacy and mapping:
            media=metadata['Content-Type'][0].split(';')[0].strip().lower()
            assert attempt['native_parser_invocation']=={'map':mapping,'media':media}, 'actual native parser not invoked'
            assert attempt['native_sse_events_processed' if media=='text/event-stream' else 'native_json_outputs_processed']>0, 'native parser did not process response'
        assert attempt['response_pre_bytes']>0 and attempt['response_post_bytes']>0
        for key in ('response_pre_sha256','response_post_sha256'):
            assert re.fullmatch('[0-9a-f]{64}',attempt[key]), 'missing actual response bytes hash'
        count=0
        for event in attempt['native_events']:
            assert len(event['before_calls'])==len(event['after_calls'])
            added=0
            for b,a in zip(event['before_calls'],event['after_calls']):
                assert b['type']=='function_call' and b['name'] in mapping
                if b.get('namespace') is None:
                    assert a=={**b,'namespace':mapping[b['name']]}, 'changed native call fields'
                    added+=1
                else:assert b['namespace']==mapping[b['name']] and a==b
            assert event['added']==added
            count+=added
            for change in event['changes']:
                path=change['path']
                # Adding a dict key is recorded at that call's object; it must
                # be exactly one of the retained native call pairs.
                if path[-1]=='namespace':
                    assert change['before'] is None and change['after'] in mapping.values(), 'unallowed namespace change'
                    path=path[:-1]
                else:
                    assert (change['before'],change['after']) in list(zip(event['before_calls'],event['after_calls'])), 'non-call response leaf changed'
                assert path==['item'] or (len(path)==3 and path[:2]==['response','output'] and isinstance(path[2],int)) or (len(path)==2 and path[0]=='output' and isinstance(path[1],int))
            if 'before_native_sse' in event:
                for prefix in ('before','after'):
                    raw=event[prefix+'_native_sse'].encode()
                    assert hashlib.sha256(raw).hexdigest()==event['pre_event_sha256' if prefix=='before' else 'post_event_sha256']
                    payload='\n'.join(line[6:] if line.startswith('data: ') else line[5:] for line in raw.decode().splitlines() if line.startswith('data:'))
                    assert json.loads(payload)['item']==event[prefix+'_calls'][0]
        assert count==attempt['namespace_added_count']
        if count==0:
            assert attempt['response_pre_sha256']==attempt['response_post_sha256'] and attempt['response_pre_bytes']==attempt['response_post_bytes'], 'non-target response changed'
        assert attempt['response_first_read_at']<=attempt['downstream_first_body_at']
        if metadata['Content-Type'][0].split(';')[0].strip().lower()=='text/event-stream':
            assert attempt['downstream_first_body_at']<=attempt['response_eof_at']
    return stage['after_sha256']


def audit_current(summary, wire, rollouts, supplement, launch=None, expected_scenario=None):
    checks, details = {}, {}

    def check(name, fn):
        try:
            details[name] = fn()
            checks[name] = True
        except (AssertionError, KeyError, ValueError, TypeError, IndexError, StopIteration) as exc:
            checks[name] = False
            details[name] = str(exc) or type(exc).__name__

    scenario = summary.get('scenario', 'all')
    has_a, has_b = scenario in ('all', 'a'), scenario in ('all', 'b')

    def declaration():
        assert scenario in ('all', 'a', 'b'), 'unknown scenario'
        if expected_scenario is not None:
            assert expected_scenario == scenario, 'requested/declared scenario mismatch'
        assert declared_scenario(summary) == scenario
        if scenario != 'all':
            assert launch is not None, 'declared short case needs original launch record'
        if launch is not None:
            assert declared_scenario(launch) == scenario, 'summary/launch scenario mismatch'
            for key, value in launch.items():
                assert summary[key] == value, 'summary/launch mismatch: ' + key
        return {'scenario': scenario, 'required_cases': [c for c, present in (('a', has_a), ('b', has_b)) if present]}
    check('declared_scenario_matches_driver_launch', declaration)

    parent = next((r for r in rollouts if r['identity'].get('id') == summary['parent_id']), {})
    by_id = {r['identity']['id']: r for r in rollouts}
    parent_calls = items(parent, 'function_call', 'custom_tool_call')
    calls = [c for c in parent_calls if c.get('type') == 'function_call']
    dispatches = [(c, json.loads(c['arguments'])) for c in calls if c.get('name') in ('spawn_agent', 'followup_task', 'send_input', 'send_message')]
    all_descriptors = [d for w in wire for d in w.get('native_descriptors', [])]
    advertised = descriptor_names(all_descriptors)
    mode = 'v2' if 'followup_task' in advertised else 'v1' if 'send_input' in advertised else 'unavailable'
    details['observed_mode'] = mode
    details['advertised_names'] = sorted(n for n in advertised if n)
    outputs = {o['call_id']: o for o in items(parent, 'function_call_output')}
    spawn = [(c, a) for c, a in dispatches if c['name'] == 'spawn_agent']
    children = []
    for c, a in spawn:
        try:
            output = json.loads(outputs[c['call_id']]['output'])
            if mode == 'v1':
                child = by_id[output['agent_id']]
            else:
                child = next(r for r in rollouts if r['identity'].get('agent_path') == output['task_name'] and r['identity'].get('parent_thread_id') == summary['parent_id'])
            children.append(child)
        except (KeyError, ValueError, StopIteration):
            children.append({})
    a = children[0] if has_a and children else {}
    b_index = 1 if has_a else 0
    b = children[b_index] if has_b and len(children) > b_index else {}
    case_children = ([a] if has_a else []) + ([b] if has_b else [])
    supplements = {r['thread_id']: r for r in supplement}

    def identity():
        assert mode == ('v2' if summary['catalog_selected']['multi_agent_version']=='v2' else 'v1'), 'observed native mode/catalog mismatch'
        expected_count = int(has_a) + int(has_b)
        assert len(spawn) == expected_count and all(case_children), 'need declared distinct native spawn results'
        assert len({r['identity']['id'] for r in case_children}) == expected_count, 'duplicate child'
        assert len(rollouts) == expected_count + 1 and len(by_id) == len(rollouts), 'unexpected/missing threads'
        for r in [parent, *case_children]:
            i = r['identity']
            assert i['model_provider'] == summary['provider'] and i['cli_version'] == summary['version'].removeprefix('codex-cli ')
            assert i['cwd'] == summary['cwd']
            if r is not parent:
                assert i['parent_thread_id'] == summary['parent_id']
            contexts = r['contexts']
            assert contexts and all(c['model'] == summary['model'] and c['effort'] == summary['effort'] for c in contexts)
            if scenario != 'all':
                assert summary['settings']['sandbox_mode'] == 'read-only'
                assert all(c['approval_policy'] == summary['settings']['approval_policy'] and c['sandbox_policy'] == {'type':'read-only'} for c in contexts), 'actual child/parent policy mismatch'
            settings = [e['settings'] for e in supplements.get(i['id'], {}).get('events', []) if 'settings' in e]
            assert settings and all(s['model'] == summary['model'] and s['model_provider_id'] == summary['provider'] and s['reasoning_effort'] == summary['effort'] for s in settings)
            assert all(s['approval_policy'] == summary['settings']['approval_policy'] and s['approvals_reviewer'] == summary['inherited_approval_reviewer'] for s in settings)
        return {r['identity']['id']: {'provider':r['identity']['model_provider'], 'contexts':r['contexts']} for r in [parent, *case_children]}
    check('actual_parent_child_identity_policy', identity)

    def dispatch():
        assert mode in ('v1','v2'), 'native continuation not advertised'
        expected = (['spawn_agent', 'followup_task', 'send_message', 'followup_task'] if mode == 'v2' else ['spawn_agent', 'send_input']) if has_a else []
        if has_b:
            expected += ['spawn_agent']
        assert [c['name'] for c, _ in dispatches] == expected, 'native dispatch order/count'
        all_outputs=items(parent,'function_call_output','custom_tool_call_output')
        assert len({o['call_id'] for o in all_outputs})==len(all_outputs)==len(parent_calls), 'duplicate/missing parent call output'
        assert {o['call_id'] for o in all_outputs}=={c['call_id'] for c in parent_calls}
        assert len({c['call_id'] for c in parent_calls}) == len(parent_calls), 'duplicate parent call id'
        assert all(c.get('namespace') in ('collaboration','multi_agent_v1') for c,_ in dispatches)
        assert all(c.get('name') in ('spawn_agent','followup_task','send_input','send_message','wait_agent','list_agents') for c in parent_calls), 'parent used non-collaboration tool'
        assert all(c.get('namespace') in ('collaboration','multi_agent_v1') for c in parent_calls), 'non-native parent namespace'
        for c,args in spawn:
            assert args.get('fork_turns') == 'none' if mode == 'v2' else args.get('fork_context') is False
            assert not any(k in args for k in ('model','effort','reasoning_effort')), 'child model override'
        handle = (a['identity']['agent_path'] if mode == 'v2' else a['identity']['id']) if has_a else None
        activities = [e['event']['item'] for e in supplements.get(summary['parent_id'], {}).get('events', []) if e.get('event',{}).get('item',{}).get('type') == 'SubAgentActivity']
        for c,args in dispatches:
            if c['name'] == 'spawn_agent':
                continue
            assert args['target'] == handle or (mode == 'v2' and args['target'] == handle.rsplit('/',1)[-1]), 'wrong continuation recipient'
            if scenario != 'all':
                assert args['target'] == handle, 'short case must use canonical target'
            if mode == 'v2':
                assert any(e['id']==c['call_id'] and e['agent_thread_id']==a['identity']['id'] for e in activities), 'native activity does not link target to A child'
        if has_a:
            assert summary['initial_marker'] in spawn[0][1]['message'] and summary['followup_marker'] in json.dumps(dispatches[1][1])
        if has_a and mode == 'v1':
            assert 'send_message' not in advertised, 'cannot exempt advertised separate messaging'
        return [{'name':c['name'],'call_id':c['call_id'],'args':args} for c,args in dispatches]
    check('native_dispatch_order_same_child_no_parent_read', dispatch)

    def a_finals():
        finals = completed_finals(a)
        expected = [summary['initial_marker'],summary['followup_marker']] + ([summary['message_token']] if mode == 'v2' else [])
        assert [f['text'] for f in finals] == expected, 'initial/continuation finals or distinct turn count'
        assert len({f['turn_id'] for f in finals}) == len(expected)
        assert not items(a,'function_call','custom_tool_call'), 'A unexpectedly used tools'
        # A1 completion must have reached parent before it issues continuation.
        continuation = dispatches[1][0]
        before = calls[:calls.index(continuation)]
        if mode == 'v1' or scenario == 'all':
            assert any(c['name'] == 'wait_agent' for c in before), 'no native wait before continuation'
        cont_at = outputs[continuation['call_id']].get('internal_chat_message_metadata_passthrough',{}).get('create_time')
        assert cont_at is not None and finals[0]['completed_at'] <= cont_at
        return finals
    if has_a:
        check('A_exact_distinct_completed_child_turns', a_finals)

    def message():
        if mode == 'v1':
            assert 'send_message' not in advertised and 'send_input' in advertised
            return {'status':'N/A','reason':'actual native v1 descriptors expose send_input but no separate send_message'}
        messages=[args for c,args in dispatches if c['name']=='send_message']
        continuations=[args for c,args in dispatches if c['name']=='followup_task']
        assert messages and len(continuations)==2
        if scenario != 'all':
            assert len(messages)==1, 'duplicate MESSAGE'
        consume=continuations[1]
        token = summary['message_token']
        assert all(token in msg['message'] for msg in messages) and token not in json.dumps(consume), 'token leaked in continuation'
        envelopes = items(a,'agent_message')
        assert any(token in json.dumps(e,ensure_ascii=False) and 'MESSAGE' in json.dumps(e,ensure_ascii=False) for e in envelopes), 'no child-owned MESSAGE token'
        return 'separate native MESSAGE consumed; token absent from followup'
    if has_a:
        check('A3_message_or_descriptor_backed_NA', message)

    def fixture_prompts():
        fixture = summary['fixture']['contents']
        assert fixture not in summary['parent_prompt']
        assert all(fixture not in json.dumps(args,ensure_ascii=False) for _,args in dispatches), 'fixture leaked into dispatched task'
        assert summary['fixture']['path'] in spawn[b_index][1]['message']
        return 'unpredictable contents absent from parent/task prompts'
    if has_b:
        check('B_fixture_absent_from_prompts', fixture_prompts)

    def file_read():
        fixture = summary['fixture']['contents']; path=summary['fixture']['path']
        assert hashlib.sha256(fixture.encode()).hexdigest() == summary['fixture']['sha256']
        finals=completed_finals(b)
        assert len(finals)==1 and finals[0]['text']==fixture, 'wrong child final'
        b_calls = items(b,'function_call','custom_tool_call')
        assert len(b_calls)==1, 'need exactly one actual child file-tool call'
        call=b_calls[0]
        b_outputs=items(b,'function_call_output','custom_tool_call_output')
        matched=[o for o in b_outputs if o['call_id']==call['call_id']]
        assert len(matched)==1, 'missing/wrong call_id output'
        native = [e for e in supplements.get(b['identity']['id'],{}).get('events',[]) if e.get('event',{}).get('item',{}).get('type')=='CommandExecution']
        assert len(native)==1, 'missing/extra child-owned execution event'
        event=native[0]['event']; execution=event['item']
        assert event['thread_id']==b['identity']['id'] and event['turn_id']==finals[0]['turn_id']
        assert execution['status']=='completed' and execution['exit_code']==0 and execution['aggregated_output']==fixture
        assert execution['command'][-1]=='cat '+path
        assert len(execution['parsed_cmd'])==1 and execution['parsed_cmd'][0]['type']=='read' and execution['parsed_cmd'][0]['path']==path
        call_line=next(e['line'] for e in b['events'] if e.get('item')==call)
        output_line=next(e['line'] for e in b['events'] if e.get('item')==matched[0])
        assert call_line < native[0]['line'] < output_line, 'native execution outside this call/result span'
        if call['type']=='function_call':
            assert call['name']=='exec_command' and json.loads(call['arguments'])['cmd']=='cat '+path
            out=matched[0]['output']
            assert 'Process exited with code 0' in out and out.split('Output:\n',1)[1]==fixture
        else:
            assert call['name']=='exec' and path in call['input']
            # Never evaluate captured JS. Native child-owned command + exact
            # result inside this custom call span supplies execution evidence.
            result=matched[0]['output']
            assert isinstance(result,list) and len(result)==2
            assert result[1]=={'type':'input_text','text':fixture}
            assert re.fullmatch(r'Script completed\nWall time [0-9.]+ seconds\nOutput:\n', result[0]['text'])
        return {'call_id':call['call_id'],'tool':call['name'],'execution':execution,'finals':finals}
    if has_b:
        check('B_child_owned_call_result_execution_exact_final', file_read)

    def short_case_completion_order():
        # V2 completion is an exact parent-received native FINAL, not another
        # mailbox edge. Validate every actual wait; v1 retains persistent waits.
        wait_results = {}
        for wait in [c for c in calls if c['name'] == 'wait_agent']:
            assert wait.get('namespace') == ('collaboration' if mode == 'v2' else 'multi_agent_v1'), 'non-native wait namespace'
            result = json.loads(outputs[wait['call_id']]['output'])
            assert isinstance(result, dict) and isinstance(result.get('timed_out'), bool) and 'error' not in result, 'invalid/error native wait result'
            wait_results[wait['call_id']] = result
        child = case_children[0]  # Only called for single-case declarations.
        task_dispatches = [c for c, _ in dispatches if c['name'] != 'send_message']
        finals = completed_finals(child)
        required = (3 if mode == 'v2' else 2) if has_a else 1
        assert len(task_dispatches) == len(finals) == required, 'required task/final count mismatch'
        completion_proofs=[]
        for call, final in zip(task_dispatches, finals):
            start = calls.index(call)
            following = next((c for c in calls[start+1:] if c['name'] in ('spawn_agent','followup_task','send_input','send_message')), None)
            end = calls.index(following) if following else len(calls)
            waits = [c for c in calls[start+1:end] if c['name'] == 'wait_agent']
            completed_waits = [c for c in waits if wait_results[c['call_id']]['timed_out'] is False]
            if mode == 'v1':
                assert waits, 'no explicit native wait after child task'
                assert completed_waits, 'native wait only timed out'
                times = [outputs[c['call_id']]['internal_chat_message_metadata_passthrough']['create_time'] for c in completed_waits]
                assert final['completed_at'] is not None and max(times) >= final['completed_at'], 'wait did not reach fresh child final'
            else:
                # v2 wait observes a NEW mailbox update. A fresh exact native
                # FINAL may already have arrived before a subsequent timeout.
                child_path=child['identity']['agent_path']
                # Root CLI session metadata has no agent_path; derive the
                # parent path from the actual canonical child path returned by
                # spawn and its separately verified parent_thread_id.
                parent_path=parent['identity']['agent_path'] or child_path.rsplit('/',1)[0]
                expected='Message Type: FINAL_ANSWER\nTask name: '+parent_path+'\nSender: '+child_path+'\nPayload:\n'+final['text']
                dispatch_line=next(e['line'] for e in parent['events'] if e.get('item')==call)
                next_line=next(e['line'] for e in parent['events'] if e.get('item')==following) if following else float('inf')
                dispatch_at=outputs[call['call_id']]['internal_chat_message_metadata_passthrough']['create_time']
                end_at=outputs[following['call_id']]['internal_chat_message_metadata_passthrough']['create_time'] if following else completed_finals(parent)[-1]['completed_at']
                receipts=[]
                for entry in parent['events']:
                    receipt=entry.get('item',{})
                    if receipt.get('type')!='agent_message' or receipt.get('author')!=child_path or receipt.get('recipient')!=parent_path:
                        continue
                    if text_content(receipt.get('content'))!=expected:
                        continue
                    metadata=receipt.get('internal_chat_message_metadata_passthrough',{})
                    if (metadata.get('turn_id')!=call['internal_chat_message_metadata_passthrough']['turn_id']
                            or metadata.get('content_item_metadata')!=[{'provenance':{'type':'tool','namespace':'collaboration'}}]):
                        continue
                    received_at=metadata.get('create_time')
                    if (dispatch_line < entry['line'] < next_line and received_at is not None and final['completed_at'] is not None
                            and max(dispatch_at,final['completed_at']) <= received_at <= end_at):
                        receipts.append(entry)
                assert len(receipts)==1, 'missing/duplicate exact fresh parent native FINAL receipt'
                completion_proofs.append({'dispatch_call_id':call['call_id'],'child_id':child['identity']['id'],'child_turn_id':final['turn_id'],'text':final['text'],'parent_receipt_line':receipts[0]['line'],'received_at':receipts[0]['item']['internal_chat_message_metadata_passthrough']['create_time'],'child_completed_at':final['completed_at']})
                for dispatch_call,_ in dispatches:
                    if dispatch_call['name']!='spawn_agent':
                        assert outputs[dispatch_call['call_id']]['output']=='', 'failed/non-void native dispatch'

            if following:
                assert final['completed_at'] <= outputs[following['call_id']]['internal_chat_message_metadata_passthrough']['create_time'], 'next dispatch before child completed'
            for wait in waits:
                args = json.loads(wait['arguments'])
                if mode == 'v1':
                    assert args['targets'] == [child['identity']['id']], 'wrong wait target'
                    if wait in completed_waits:
                        assert wait_results[wait['call_id']]['status'][child['identity']['id']] == {'completed': final['text']}, 'wait returned old/wrong final'
                elif 'target' in args:
                    assert args['target'] == child['identity']['agent_path'], 'wrong wait target'
        return {'contract':'v2 exact parent FINAL receipts with optional validated waits; v1 persistent wait status','v2_receipts':completion_proofs}
    if scenario in ('a', 'b'):
        check('declared_case_native_waits_fresh_completion_order', short_case_completion_order)

    def short_case_native_linkage_modes():
        events = supplements[summary['parent_id']]['events']
        for call, args in dispatches:
            child = case_children[spawn.index((call, args))] if call['name'] == 'spawn_agent' else a
            linked = [e for e in events if e.get('event', {}).get('item', {}).get('id') == call['call_id']]
            assert len(linked) == 1, 'missing/duplicate native dispatch event'
            event = linked[0]['event']; activity = event['item']
            assert event['thread_id'] == summary['parent_id']
            assert event['turn_id'] == call['internal_chat_message_metadata_passthrough']['turn_id']
            output_line = next(e['line'] for e in parent['events'] if e.get('item') == outputs[call['call_id']])
            call_line = next(e['line'] for e in parent['events'] if e.get('item') == call)
            assert call_line < linked[0]['line'] < output_line, 'native dispatch outside call/result span'
            if mode == 'v2':
                assert activity['type'] == 'SubAgentActivity'
                assert activity['agent_thread_id'] == child['identity']['id'] and activity['agent_path'] == child['identity']['agent_path']
                assert activity['kind'] == ('started' if call['name'] == 'spawn_agent' else 'interacted')
            else:
                assert activity['type'] == 'CollabAgentToolCall' and activity['status'] == 'completed'
                assert activity['tool'] == call['name'] and activity['sender_thread_id'] == summary['parent_id']
                assert activity['receiver_thread_ids'] == [child['identity']['id']]
            if call['name'] == 'spawn_agent':
                assert activity['model'] == summary['model'] and activity['reasoning_effort'] == summary['effort']
        assert all(c['name'] != 'list_agents' for c in parent_calls), 'extraneous parent call'
        catalog = summary['catalog_selected']
        if catalog['tool_mode'] == 'code_mode_only':
            assert 'exec' in advertised and 'exec_command' not in advertised, 'actual Code Mode mismatch'
        if catalog['use_responses_lite']:
            assert all(any(k.lower() == 'x-openai-internal-codex-responses-lite' and v == 'true'
                           for k,v in w['lite_header_observed'].items()) for w in wire), 'actual Lite header absent'
        return 'native dispatch events, actual catalog modes and Lite header verified'
    if scenario in ('a', 'b'):
        check('declared_case_native_event_linkage_actual_modes', short_case_native_linkage_modes)

    def transport():
        assert wire, 'no requests'
        total=0
        for record in wire:
            assert record['thread_id'] in by_id, 'request belongs to unknown thread'
            assert record['non_target_items_equal'] and record['non_input_fields_equal']
            assert record['actual_upstream_body_verified']
            previous=audit_namespace_record(summary,record)
            assert [s['flag'] for s in record['stages']] == ['model_swap','id_fix','json_fmt_fix','drop_tools_item'], 'incomplete observer stage schema (pre-fix attempt)'
            for stage in record['stages']:
                assert stage['before_sha256']==previous
                flag=stage['flag']
                assert flag in ('model_swap','id_fix','json_fmt_fix','drop_tools_item')
                assert stage['enabled'] == (True if flag=='model_swap' else summary['route'][flag])
                assert not (flag=='drop_tools_item' and stage['count']), 'unexpected tool drop'
                if not stage['enabled'] or stage['count']==0:
                    assert not stage['changes'] and stage['before_sha256']==stage['after_sha256']
                for change in stage['changes']:
                    path=change['path']
                    assert (flag=='model_swap' and path==['model']) or (flag=='id_fix' and path[-1]=='id') or (flag=='json_fmt_fix' and path==['text','format']), 'unallowed stage change'
                    before,after=change['before'],change['after']
                    for key,value in (('before_sha256',before),('after_sha256',after)):
                        assert hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()==change[key]
                    if flag=='model_swap':
                        assert before=='codex-auto-review' and after==summary['route']['to']
                    elif flag=='id_fix':
                        assert isinstance(before,str) and before.startswith('at_') and after=='msg_'+before[3:]
                    elif flag=='json_fmt_fix':
                        assert before['type']=='json_schema' and after=={'type':'json_object'}
                previous=stage['after_sha256']
            assert previous==record['expected_outbound_sha256']
            for attempt in record['outbound_attempts']:
                assert attempt['body_sha256']==previous
                assert attempt['path']==summary['route']['request_prefix']+'/responses', 'candidate lost incoming prefix'
                assert attempt['model']==summary['route']['to'], 'wrong candidate logical model'
            assert record['outbound_attempts']
            for pair in record['items']:
                before,after=pair['ingress'],pair['egress']
                assert set(after)=={'type','role','content'} and after['type']=='message' and after['role']=='user'
                assert json.loads(after['content'][0]['text'].split(': ',1)[1])=={k:v for k,v in before.items() if k not in ('type','content')}
                assert [p['text'] for p in after['content'][1:]]==[p['text'] if p['type']=='input_text' else p['encrypted_content'] for p in before['content']]
                assert all(p['type']=='input_text' for p in after['content'])
                total+=1
        if mode=='v2':
            for child in case_children:
                assert any(w['thread_id']==child['identity']['id'] and w['converted'] for w in wire)
        return {'requests':len(wire),'converted_including_history':total,'http_statuses':dict(__import__('collections').Counter(str(a.get('http_status')) for w in wire for a in w['outbound_attempts']))}
    check('wire_helper_and_exact_allowed_outbound_stages', transport)

    def lifecycle():
        assert summary['parent_completed'] and summary['app_server_exit']==0 and not summary['errors']
        return {'exit':summary['app_server_exit'],'parent_turn_status':summary['parent_turn_status']}
    check('native_lifecycle', lifecycle)
    passed = all(checks.values())
    return {'profile':summary['profile'],'attempt':summary['attempt'],'scenario':scenario,'passed':passed,
            'coverage':{c: bool(present and passed) for c,present in (('a',has_a),('b',has_b))},
            'checks':checks,'details':details}


def audit_directory(directory, scenario=None):
    values=[json.loads((directory/name).read_text()) for name in ('summary.json','wire.json','rollouts-sanitized.json')]
    supplement=directory/'native-rollout-supplement.json'
    launch=directory/'launch.json'
    result=audit_current(*values, json.loads(supplement.read_text()) if supplement.exists() else [],
                         json.loads(launch.read_text()) if launch.exists() else None, scenario)
    summary=values[0]
    route_hash=summary.get('source_hashes_at_launch',{}).get('codex-agent/shim-routes.json')
    route_snapshot=directory/(str(route_hash)+'.source.gz')
    if route_snapshot.exists() or summary['route'].get('native_agent_response_restore') or summary['route'].get('native_agent_request_flatten'):
        try:
            for source_hash in summary['source_hashes_at_launch'].values():
                raw=gzip.decompress((directory/(source_hash+'.source.gz')).read_bytes())
                assert hashlib.sha256(raw).hexdigest()==source_hash, 'source snapshot hash mismatch'
            routes=json.loads(gzip.decompress(route_snapshot.read_bytes()))['routes']
            actual=next(r for r in routes if r['endpoint_id']==summary['profile'])
            assert actual==summary['route'], 'actual route snapshot mismatch'
            result['checks']['namespace_launch_source_snapshots']=True
            result['details']['namespace_launch_source_snapshots']='all launch sources retrievable and verified; exact route flags'
        except (OSError, ValueError, AssertionError, StopIteration) as exc:
            result['checks']['namespace_launch_source_snapshots']=False
            result['details']['namespace_launch_source_snapshots']=str(exc)
            result['passed']=False
            result['coverage']={'a':False,'b':False}
    result['auditor_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['input_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [directory/name for name in ('summary.json','wire.json','rollouts-sanitized.json')] + ([supplement] if supplement.exists() else []) + ([launch] if launch.exists() else [])}
    return result


def aggregate_directories(directories):
    results = [audit_directory(directory) for directory in directories]
    summaries = [json.loads((directory/'summary.json').read_text()) for directory in directories]
    coverage = {case: any(r['coverage'][case] for r in results) for case in ('a', 'b')}
    errors = []
    keys = ('profile','model','provider','effort','version','catalog_selected','route','source_head',
            'effective_endpoint','inherited_approval_reviewer')
    if not summaries:
        errors.append('no evidence')
    elif any(any(s[k] != summaries[0][k] for k in keys) for s in summaries[1:]):
        errors.append('A/B launch snapshot mismatch')
    harness_keys={'docs/gateflow/shim-subagent-delivery/native-probe.py',
                  'docs/gateflow/shim-subagent-delivery/audit-native-evidence.py'}
    production=[{k:v for k,v in s['source_hashes_at_launch'].items() if k not in harness_keys and not k.startswith('tests/')} for s in summaries]
    if any(s!=production[0] for s in production[1:]):
        errors.append('A/B production source snapshot mismatch')
    normalized_settings = [{k:v for k,v in s['settings'].items() if k != f"model_providers.{s['provider']}.base_url"} for s in summaries]
    if any(s != normalized_settings[0] for s in normalized_settings[1:]):
        errors.append('A/B launch settings mismatch')
    parents = [s['parent_id'] for s in summaries]
    if len(set(parents)) != len(parents):
        errors.append('independent cases reused parent')
    thread_ids = []
    for directory in directories:
        thread_ids += [r['identity']['id'] for r in json.loads((directory/'rollouts-sanitized.json').read_text())]
    if len(set(thread_ids)) != len(thread_ids):
        errors.append('cases reused thread')
    if not all(coverage.values()):
        errors.append('missing required A+B coverage')
    return {'passed':bool(results) and all(r['passed'] for r in results) and not errors,
            'coverage':coverage,'errors':errors,'results':results,
            'launch_source_hashes':[s['source_hashes_at_launch'] for s in summaries],
            'source_comparison':'production/routes/registry/profile/catalog exact; each harness independently audited with retrievable launch hashes'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir',type=Path)
    parser.add_argument('--scenario',choices=('all','a','b'),default='all')
    parser.add_argument('--aggregate-evidence-dir',type=Path,action='append',default=[])
    args=parser.parse_args()
    if args.aggregate_evidence_dir:
        if args.evidence_dir or args.scenario != 'all':
            parser.error('aggregate audit requires all coverage and no single evidence directory')
        result=aggregate_directories(args.aggregate_evidence_dir)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if result['passed'] else 1
    if args.evidence_dir:
        result=audit_directory(args.evidence_dir,args.scenario)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if result['passed'] else 1
    if args.scenario != 'all':
        parser.error('short scenario requires an evidence directory')
    print(json.dumps(legacy_audit(Path(__file__).resolve().parent/'evidence'),indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
