#!/usr/bin/env python3
"""Independent checks of durable captures, without calling a model or helper."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'evidence'
reports = []
for directory in sorted(ROOT.glob('candidate-run-*')):
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
print(json.dumps(reports, indent=2))
