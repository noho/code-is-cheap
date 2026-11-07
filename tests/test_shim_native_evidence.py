"""Adversarial audit controls using actual observed v1/direct and v2/Code Mode data.
These offline mutation checks are not provider-inference acceptance.
"""
import importlib.util
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'docs/gateflow/shim-subagent-delivery/audit-native-evidence.py'
spec = importlib.util.spec_from_file_location('native_audit', PATH)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class NativeAuditTests(unittest.TestCase):
    def load(self, profile, attempt):
        directory = ROOT / 'docs/gateflow/shim-subagent-all-providers/evidence' / profile / ('attempt-' + str(attempt))
        return [json.loads((directory / name).read_text()) for name in
                ('summary.json', 'wire.json', 'rollouts-sanitized.json', 'native-rollout-supplement.json')]

    def short_case(self, scenario, profile='mimo'):
        """In-memory offline controls, never relabel durable provider captures."""
        data = self.load(profile, 2)
        summary, wire, rollouts, supplement = data
        parent = next(r for r in rollouts if r['identity']['id'] == summary['parent_id'])
        children = sorted((r for r in rollouts if r is not parent), key=lambda r: r['identity']['agent_path'] or r['identity']['id'])
        # Spawn result order, rather than random v1 UUID lexical order.
        spawns = [e for e in parent['events'] if e.get('item', {}).get('name') == 'spawn_agent']
        boundary = spawns[1]['line']
        calls = [e['item'] for e in parent['events'] if e.get('item', {}).get('type') == 'function_call'
                 and ((e['line'] < boundary) == (scenario == 'a'))]
        ids = {c['call_id'] for c in calls}
        outputs = {e['item']['call_id']: json.loads(e['item']['output']) for e in parent['events']
                   if e.get('item', {}).get('type') == 'function_call_output' and e['item']['call_id'] in {s['item']['call_id'] for s in spawns}}
        spawn = spawns[0 if scenario == 'a' else 1]['item']
        result = outputs[spawn['call_id']]
        child = next(r for r in children if (r['identity']['agent_path'] == result.get('task_name') if 'task_name' in result else r['identity']['id'] == result['agent_id']))
        parent['events'] = [e for e in parent['events'] if e.get('item', {}).get('type') not in ('function_call', 'function_call_output') or e['item']['call_id'] in ids]
        data[2] = [parent, child]
        tids = {r['identity']['id'] for r in data[2]}
        data[1] = [w for w in wire if w['thread_id'] in tids]
        data[3] = [r for r in supplement if r['thread_id'] in tids]
        summary['scenario'] = scenario
        summary['driver_argv'] += ['--scenario', scenario]
        launch = copy.deepcopy(summary)
        data.append(launch)
        return data

    def write_case(self, directory, data):
        directory.mkdir()
        for name, value in zip(('summary','wire','rollouts-sanitized','native-rollout-supplement','launch'), data):
            (directory/(name+'.json')).write_text(json.dumps(value))

    def test_declared_short_cases_v1_and_v2(self):
        for profile in ('glm', 'mimo'):
            for scenario in ('a', 'b'):
                with self.subTest(profile=profile, scenario=scenario):
                    result = audit.audit_current(*self.short_case(scenario, profile))
                    self.assertTrue(result['passed'], result['details'])
                    self.assertEqual(result['coverage'], {'a':scenario == 'a', 'b':scenario == 'b'})

    def test_old_all_failures_and_successes_unchanged(self):
        evidence = ROOT/'docs/gateflow/shim-subagent-all-providers/evidence'
        profiles = ('ds-flash','glm','glm-flash','kimi','mimo','mimo-fast','mimo-flash','qwen','hy')
        for directory in sorted(d for p in profiles for d in (evidence/p).glob('attempt-*')):
            with self.subTest(directory=directory):
                old = json.loads((directory/'audit.json').read_text())
                new = audit.audit_directory(directory)
                self.assertEqual(new['passed'], old['passed'])
                for key, passed in old['checks'].items():
                    self.assertEqual(new['checks'][key], passed, key)

    def test_posthoc_all_to_a_cannot_hide_missing_b(self):
        data = self.load('mimo-flash', 2)
        data[0]['scenario'] = 'a'
        self.assertFalse(audit.audit_current(*data)['checks']['declared_scenario_matches_driver_launch'])
        data[0]['driver_argv'] += ['--scenario', 'a']
        self.assertFalse(audit.audit_current(*data)['checks']['declared_scenario_matches_driver_launch'])
        launch = json.loads((ROOT/'docs/gateflow/shim-subagent-all-providers/evidence/mimo-flash/attempt-2/launch.json').read_text())
        self.assertFalse(audit.audit_current(*data, launch)['checks']['declared_scenario_matches_driver_launch'])

    def test_wrong_scenario_argv_or_launch_rejected(self):
        for target in (0, 4):
            data = self.short_case('a')
            data[target]['driver_argv'][-1] = 'b'
            self.assertFalse(audit.audit_current(*data)['checks']['declared_scenario_matches_driver_launch'])
        data = self.short_case('b')
        self.assertFalse(audit.audit_current(*data, expected_scenario='a')['passed'])
        self.assertFalse(audit.audit_current(*data, expected_scenario='all')['passed'])

    def test_declared_a_rejects_extra_child_and_duplicate_message(self):
        data = self.short_case('a')
        extra = self.load('mimo', 2)[2]
        data[2].append(next(r for r in extra if r['identity']['agent_path'] == '/root/delivery_b'))
        self.assertFalse(audit.audit_current(*data)['checks']['actual_parent_child_identity_policy'])
        data = self.short_case('a')
        parent = data[2][0]
        message = next(e for e in parent['events'] if e.get('item', {}).get('name') == 'send_message')
        parent['events'].append(copy.deepcopy(message))
        self.assertFalse(audit.audit_current(*data)['checks']['native_dispatch_order_same_child_no_parent_read'])

    def test_declared_a_message_leak_wrong_target_and_duplicate_completion(self):
        for mutation, check in (('leak','A3_message_or_descriptor_backed_NA'), ('target','native_dispatch_order_same_child_no_parent_read'), ('completion','A_exact_distinct_completed_child_turns')):
            data = self.short_case('a')
            if mutation == 'completion':
                child = data[2][1]
                child['events'].append(copy.deepcopy(next(e for e in child['events'] if e.get('event', {}).get('type') == 'task_complete')))
            else:
                call = next(e['item'] for e in data[2][0]['events'] if e.get('item', {}).get('name') == 'followup_task' and 'consume-message' in e['item']['arguments'])
                args = json.loads(call['arguments'])
                if mutation == 'leak': args['message'] += data[0]['message_token']
                else: args['target'] = '/root/delivery_b'
                call['arguments'] = json.dumps(args)
            self.assertFalse(audit.audit_current(*data)['checks'][check])

    def test_declared_wait_and_native_event_linkage(self):
        for scenario in ('a', 'b'):
            data = self.short_case(scenario, 'glm')
            parent = data[2][0]
            parent['events'] = [e for e in parent['events'] if e.get('item', {}).get('name') != 'wait_agent']
            self.assertFalse(audit.audit_current(*data)['checks']['declared_case_native_waits_fresh_completion_order'])
            data = self.short_case(scenario)
            spawn = next(e['item'] for e in data[2][0]['events'] if e.get('item', {}).get('name') == 'spawn_agent')
            event = next(e['event'] for e in data[3][0]['events'] if e.get('event', {}).get('item', {}).get('id') == spawn['call_id'])
            event['item']['agent_thread_id'] = 'wrong-child'
            self.assertFalse(audit.audit_current(*data)['checks']['declared_case_native_event_linkage_actual_modes'])

    def test_wait_error_unqualified_call_timeout_and_stale_final_rejected(self):
        for mutation in ('namespace','error','timeout','stale'):
            data = self.short_case('b', 'glm' if mutation == 'stale' else 'mimo')
            parent = data[2][0]
            wait = next(e['item'] for e in parent['events'] if e.get('item', {}).get('name') == 'wait_agent')
            output = next(e['item'] for e in parent['events'] if e.get('item', {}).get('type') == 'function_call_output' and e['item']['call_id'] == wait['call_id'])
            if mutation == 'namespace': del wait['namespace']
            elif mutation == 'error': output['output'] = 'unsupported call: wait_agent'
            elif mutation == 'timeout':
                output['output'] = '{"timed_out":true}'
                parent['events']=[e for e in parent['events'] if e.get('item',{}).get('type')!='agent_message']
            else:
                result = json.loads(output['output'])
                result['status'][data[2][1]['identity']['id']]['completed'] = 'old final'
                output['output'] = json.dumps(result)
            self.assertFalse(audit.audit_current(*data)['checks']['declared_case_native_waits_fresh_completion_order'])

    def test_actual_short_a_error_never_counts_as_a_coverage(self):
        directory = ROOT/'docs/gateflow/shim-subagent-all-providers/evidence/mimo-flash/scenario-a-attempt-1'
        result = audit.audit_directory(directory)
        self.assertFalse(result['passed'])
        self.assertFalse(result['coverage']['a'])
        self.assertFalse(result['checks']['declared_case_native_waits_fresh_completion_order'])

    def test_actual_short_b_has_no_a_coverage(self):
        directory = ROOT/'docs/gateflow/shim-subagent-all-providers/evidence/mimo-flash/scenario-b-attempt-1'
        result = audit.audit_directory(directory)
        self.assertTrue(result['passed'], result['details'])
        self.assertEqual(result['coverage'], {'a':False,'b':True})
        self.assertFalse(audit.aggregate_directories([directory])['passed'])

    def test_declared_b_rejects_parent_read_leak_and_missing_execution(self):
        for mutation, check in (('parent','native_dispatch_order_same_child_no_parent_read'), ('leak','B_fixture_absent_from_prompts'), ('execution','B_child_owned_call_result_execution_exact_final')):
            data = self.short_case('b')
            if mutation == 'parent':
                data[2][0]['events'].append({'line':1000,'item':{'type':'custom_tool_call','name':'exec','input':'read fixture','call_id':'bad'}})
            elif mutation == 'leak': data[0]['parent_prompt'] += data[0]['fixture']['contents']
            else:
                for r in data[3]:
                    r['events'] = [e for e in r['events'] if e.get('event', {}).get('item', {}).get('type') != 'CommandExecution']
            self.assertFalse(audit.audit_current(*data)['checks'][check])

    def test_separate_message_descriptor_prevents_v1_NA(self):
        data = self.short_case('a', 'glm')
        data[1][0]['native_descriptors'].append({'name':'send_message'})
        self.assertFalse(audit.audit_current(*data)['checks']['A3_message_or_descriptor_backed_NA'])

    def test_aggregate_requires_both_independent_matching_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b = self.short_case('a'), self.short_case('b')
            # Distinct fake thread IDs are strictly offline mutation controls.
            text = json.dumps(b)
            for r in b[2]: text = text.replace(r['identity']['id'], 'independent-' + r['identity']['id'])
            b = json.loads(text)
            self.write_case(root/'a', a); self.write_case(root/'b', b)
            self.assertFalse(audit.aggregate_directories([root/'a'])['passed'])
            self.assertTrue(audit.aggregate_directories([root/'a',root/'b'])['passed'])
            b[0]['effort'] = b[4]['effort'] = 'different'
            (root/'b/summary.json').write_text(json.dumps(b[0])); (root/'b/launch.json').write_text(json.dumps(b[4]))
            self.assertFalse(audit.aggregate_directories([root/'a',root/'b'])['passed'])

    def namespace_case(self, profile, scenario, attempt=1):
        directory=ROOT/'docs/gateflow/shim-subagent-all-providers/evidence'/profile/('namespace-scenario-'+scenario+'-attempt-'+str(attempt))
        return [json.loads((directory/(name+'.json')).read_text()) for name in ('summary','wire','rollouts-sanitized','native-rollout-supplement','launch')]

    def test_actual_mimo_a4_strict_pass_has_three_parent_receipts_and_active_maps(self):
        directory=ROOT/'docs/gateflow/shim-subagent-all-providers/evidence/mimo-flash/namespace-scenario-a-attempt-4'
        result=audit.audit_directory(directory,scenario='a')
        self.assertTrue(result['passed'],result['details'])
        self.assertEqual(result['coverage'],{'a':True,'b':False})
        self.assertTrue(result['checks']['namespace_launch_source_snapshots'])
        summary,wire,*_=self.namespace_case('mimo-flash','a',4)
        self.assertEqual(summary['source_hashes_at_launch']['codex-agent/bin/codex-auto-review-shim'],
                         'a6246a4bc810125437992791aedcc8f2aa4c072f55e2bcf3691562feecd8e1e6')
        receipts=result['details']['declared_case_native_waits_fresh_completion_order']['v2_receipts']
        self.assertEqual([r['text'] for r in receipts],
                         [summary['initial_marker'],summary['followup_marker'],summary['message_token']])
        self.assertEqual(len({r['child_turn_id'] for r in receipts}),3)
        self.assertEqual(len({r['child_id'] for r in receipts}),1)
        self.assertEqual(len(wire),11)
        self.assertFalse(summary['route']['native_agent_request_flatten'])
        self.assertTrue(summary['route']['native_agent_response_restore'])
        for record in wire:
            stage=record['native_request_stage']
            self.assertEqual(len(stage['map']),6)
            self.assertEqual(set(stage['map'].values()),{'collaboration'})
            self.assertEqual(stage['before_sha256'],stage['after_sha256'])
            self.assertTrue(record['outbound_attempts'])
        # A4 took the active relay with already-qualified calls: active does not
        # imply that this particular upstream response needed a namespace added.
        calls=[c for w in wire for a in w['outbound_attempts'] for e in a['native_events'] for c in e['after_calls']]
        self.assertTrue(calls)
        self.assertTrue(all(c['namespace']=='collaboration' for c in calls))
        for record in wire:
            for attempt in record['outbound_attempts']:
                self.assertEqual(attempt['namespace_added_count'],0)
                self.assertEqual(attempt['response_pre_sha256'],attempt['response_post_sha256'])

    def test_actual_mimo_a4_receipts_child_turns_and_active_map_are_required(self):
        good=self.namespace_case('mimo-flash','a',4)
        for mutation in ('missing-receipts','wrong-author','child-turn','empty-map'):
            data=copy.deepcopy(good)
            parent=next(r for r in data[2] if r['identity']['id']==data[0]['parent_id'])
            receipts=[e for e in parent['events'] if e.get('item',{}).get('type')=='agent_message'
                      and 'FINAL_ANSWER' in json.dumps(e['item'])]
            check='declared_case_native_waits_fresh_completion_order'
            if mutation=='missing-receipts':parent['events']=[e for e in parent['events'] if e not in receipts]
            elif mutation=='wrong-author':receipts[1]['item']['author']='/root/wrong'
            elif mutation=='child-turn':
                child=next(r for r in data[2] if r is not parent)
                next(e['event'] for e in child['events'] if e.get('event',{}).get('type')=='task_complete')['turn_id']='wrong'
            else:
                data[1][0]['native_request_stage']['map']={}
                check='wire_helper_and_exact_allowed_outbound_stages'
            with self.subTest(mutation=mutation):
                result=audit.audit_current(*data)
                self.assertFalse(result['passed']);self.assertFalse(result['coverage']['a'])
                self.assertFalse(result['checks'][check],result['details'])

    def test_actual_mimo_a3_incomplete_cannot_supply_a_coverage(self):
        directory=ROOT/'docs/gateflow/shim-subagent-all-providers/evidence/mimo-flash/namespace-scenario-a-attempt-3'
        result=audit.audit_directory(directory,scenario='a')
        self.assertFalse(result['passed'])
        self.assertEqual(result['coverage'],{'a':False,'b':False})
        self.assertTrue(result['checks']['namespace_launch_source_snapshots'])
        self.assertTrue(result['checks']['wire_helper_and_exact_allowed_outbound_stages'])
        for check in ('native_lifecycle','A_exact_distinct_completed_child_turns',
                      'A3_message_or_descriptor_backed_NA','declared_case_native_waits_fresh_completion_order'):
            self.assertFalse(result['checks'][check],check)
        self.assertFalse(audit.aggregate_directories([directory,
            directory.parent/'namespace-scenario-b-attempt-2'])['passed'])

    def test_namespace_actual_cases_preserve_strict_failures_and_b_coverage(self):
        for profile in ('kimi','mimo-flash'):
            for scenario in ('a','b'):
                directory=ROOT/'docs/gateflow/shim-subagent-all-providers/evidence'/profile/('namespace-scenario-'+scenario+'-attempt-1')
                result=audit.audit_directory(directory)
                expected=profile=='mimo-flash' or scenario=='b'
                self.assertEqual(result['passed'],expected,result['details'])
                self.assertTrue(result['checks']['wire_helper_and_exact_allowed_outbound_stages'],result['details'])
                self.assertTrue(result['checks']['namespace_launch_source_snapshots'])
                self.assertEqual(result['coverage'],{'a':profile=='mimo-flash' and scenario=='a','b':scenario=='b'})

    def test_namespace_actual_capture_missing_stage_hash_fields_and_location_rejected(self):
        for mutation in ('stage','outbound','response','field','location'):
            data=self.namespace_case('kimi','b')
            record=next(w for w in data[1] if w['native_request_stage']['map'])
            if mutation=='stage':del record['native_request_stage']
            elif mutation=='outbound':record['outbound_attempts'][0]['body_sha256']='0'*64
            elif mutation=='response':del record['outbound_attempts'][0]['response_pre_sha256']
            elif mutation=='field':record['outbound_attempts'][0]['native_events'][0]['after_calls'][0]['arguments']='changed'
            else:record['descriptor_locations']=[]
            with self.subTest(mutation=mutation):
                result=audit.audit_current(*data)
                self.assertFalse(result['passed'])
                self.assertFalse(result['checks']['wire_helper_and_exact_allowed_outbound_stages'])

    def test_v2_receipt_aware_wait_accepts_actual_finals_and_rejects_counterexamples(self):
        good=self.namespace_case('mimo-flash','a')
        self.assertTrue(audit.audit_current(*good)['passed'])
        for mutation in ('missing','prose','author','recipient','token','stale','order','turn','provenance','duplicate','dispatch-error','wait-error','wait-namespace'):
            data=copy.deepcopy(good);parent=data[2][0]
            receipts=[e for e in parent['events'] if e.get('item',{}).get('type')=='agent_message' and 'FINAL_ANSWER' in json.dumps(e['item'])]
            receipt=receipts[1]
            if mutation=='missing':parent['events']=[e for e in parent['events'] if e not in receipts]
            elif mutation=='prose':
                for entry in receipts:entry['item']['type']='message';entry['item']['role']='assistant'
            elif mutation=='author':receipt['item']['author']='/root/other'
            elif mutation=='recipient':receipt['item']['recipient']='/root/other'
            elif mutation=='token':receipt['item']['content'][0]['text']+='wrong'
            elif mutation=='stale':receipt['item']['internal_chat_message_metadata_passthrough']['create_time']=0
            elif mutation=='order':receipt['line']=0
            elif mutation=='turn':receipt['item']['internal_chat_message_metadata_passthrough']['turn_id']='wrong'
            elif mutation=='provenance':receipt['item']['internal_chat_message_metadata_passthrough']['content_item_metadata']=[]
            elif mutation=='duplicate':parent['events'].append(copy.deepcopy(receipt))
            else:
                call=next(e['item'] for e in parent['events'] if e.get('item',{}).get('name')==('followup_task' if mutation=='dispatch-error' else 'wait_agent'))
                if mutation=='wait-namespace':call.pop('namespace')
                else:
                    output=next(e['item'] for e in parent['events'] if e.get('item',{}).get('type')=='function_call_output' and e['item']['call_id']==call['call_id'])
                    output['output']='unsupported call: failed native dispatch'
            with self.subTest(mutation=mutation):
                result=audit.audit_current(*data)
                self.assertFalse(result['checks']['declared_case_native_waits_fresh_completion_order'],result['details'])
                self.assertFalse(result['passed'])

    def test_corrected_kimi_attempt_two_requires_independent_matched_a_and_b(self):
        base=ROOT/'docs/gateflow/shim-subagent-all-providers/evidence/kimi'
        a,b=(base/('namespace-scenario-'+case+'-attempt-2') for case in ('a','b'))
        self.assertTrue(audit.aggregate_directories([a,b])['passed'])
        self.assertFalse(audit.aggregate_directories([a])['passed'])
        self.assertFalse(audit.audit_directory(base/'namespace-scenario-a-attempt-1')['passed'])

    def test_candidate_route_keeps_prefix_and_flags(self):
        probe_spec = importlib.util.spec_from_file_location('native_probe', PATH.with_name('native-probe.py'))
        probe = importlib.util.module_from_spec(probe_spec)
        probe_spec.loader.exec_module(probe)
        routes = json.loads((ROOT / 'codex-agent/shim-routes.json').read_text())['routes']
        for route in routes:
            candidate = probe.candidate_route(route)
            self.assertNotIn('endpoint_id', candidate)
            self.assertNotIn('request_prefix', candidate)
            self.assertEqual(candidate['upstream'], 'http://127.0.0.1:' + str(route['port']))
            for flag in ('agent_message_fix', 'id_fix', 'json_fmt_fix', 'drop_tools_item'):
                self.assertEqual(candidate[flag], route[flag])
            self.assertEqual(candidate['to'], route['to'])

    def test_observed_native_shapes(self):
        for profile in ('glm', 'mimo'):
            with self.subTest(profile=profile):
                self.assertTrue(audit.audit_current(*self.load(profile, 2))['passed'])

    def test_parent_read_rejected_even_with_all_exact_child_finals(self):
        data = self.load('mimo', 2)
        parent = next(r for r in data[2] if r['identity']['id'] == data[0]['parent_id'])
        parent['events'].append({'line': 1000, 'item': {'type': 'function_call', 'name': 'exec_command', 'arguments': '{"cmd":"cat fixture"}', 'call_id': 'bad'}})
        self.assertFalse(audit.audit_current(*data)['checks']['native_dispatch_order_same_child_no_parent_read'])

    def test_wrong_child_continuation(self):
        data = self.load('glm', 2)
        for r in data[2]:
            for e in r['events']:
                call = e.get('item', {})
                if call.get('name') == 'send_input':
                    args = json.loads(call['arguments']); args['target'] = 'different-child'
                    call['arguments'] = json.dumps(args)
        self.assertFalse(audit.audit_current(*data)['checks']['native_dispatch_order_same_child_no_parent_read'])

    def test_replayed_old_final_does_not_count_as_followup(self):
        data = self.load('glm', 2)
        a = next(r for r in data[2] if len([e for e in r['events'] if e.get('event', {}).get('type') == 'task_complete']) == 2)
        completed = [e for e in a['events'] if e.get('event', {}).get('type') == 'task_complete']
        completed[1]['event']['turn_id'] = completed[0]['event']['turn_id']
        self.assertFalse(audit.audit_current(*data)['checks']['A_exact_distinct_completed_child_turns'])

    def test_message_token_leak_rejected(self):
        data = self.load('mimo', 2)
        for r in data[2]:
            for e in r['events']:
                c = e.get('item', {})
                if c.get('name') == 'followup_task' and 'consume-message' in c['arguments']:
                    args = json.loads(c['arguments']); args['message'] += data[0]['message_token']; c['arguments'] = json.dumps(args)
        self.assertFalse(audit.audit_current(*data)['checks']['A3_message_or_descriptor_backed_NA'])

    def test_code_mode_JS_and_final_are_insufficient_without_execution_event(self):
        data = self.load('mimo', 2)
        for r in data[3]:
            r['events'] = [e for e in r['events'] if e.get('event', {}).get('item', {}).get('type') != 'CommandExecution']
        self.assertFalse(audit.audit_current(*data)['checks']['B_child_owned_call_result_execution_exact_final'])

    def test_custom_call_result_association(self):
        data = self.load('mimo', 2)
        for r in data[2]:
            for e in r['events']:
                item = e.get('item', {})
                if item.get('type') == 'custom_tool_call_output':
                    item['call_id'] = 'wrong-call'
        self.assertFalse(audit.audit_current(*data)['checks']['B_child_owned_call_result_execution_exact_final'])

    def test_wrong_native_execution_thread(self):
        data = self.load('mimo', 2)
        for r in data[3]:
            for e in r['events']:
                if e.get('event', {}).get('item', {}).get('type') == 'CommandExecution':
                    e['event']['thread_id'] = data[0]['parent_id']
        self.assertFalse(audit.audit_current(*data)['checks']['B_child_owned_call_result_execution_exact_final'])

    def test_outbound_change_and_prefix_loss_rejected(self):
        for key in ('body_sha256', 'path'):
            data = self.load('glm', 2)
            data[1][0]['outbound_attempts'][0][key] = 'wrong'
            self.assertFalse(audit.audit_current(*data)['checks']['wire_helper_and_exact_allowed_outbound_stages'])

    def test_kimi_task_failure_never_becomes_final_only_acceptance(self):
        directory = ROOT / 'docs/gateflow/shim-subagent-all-providers/evidence/kimi/attempt-1'
        self.assertFalse(audit.audit_directory(directory)['passed'])



    def test_legacy_location_scope_is_explicit_and_current_source_cannot_use_empty_map(self):
        data=self.namespace_case('mimo-flash','b')
        record=data[1][0]
        self.assertEqual(record['native_request_stage']['map'],{})
        self.assertTrue(record['descriptor_locations'])
        self.assertEqual(audit.audit_namespace_record(data[0],record),record['native_request_stage']['after_sha256'])
        data[0]['source_hashes_at_launch']['codex-agent/bin/codex-auto-review-shim']='current-helper'
        with self.assertRaises((AssertionError,KeyError)):
            audit.audit_namespace_record(data[0],record)

    def test_aggregation_keeps_production_invariants_and_reports_harness_versions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);a,b=self.short_case('a'),self.short_case('b')
            text=json.dumps(b)
            for r in b[2]:text=text.replace(r['identity']['id'],'independent-'+r['identity']['id'])
            b=json.loads(text)
            harness='docs/gateflow/shim-subagent-delivery/audit-native-evidence.py'
            b[0]['source_hashes_at_launch'][harness]='different-launch-reader'
            b[4]=copy.deepcopy(b[0])
            self.write_case(root/'a',a);self.write_case(root/'b',b)
            results=[{'passed':True,'coverage':{'a':True,'b':False}},{'passed':True,'coverage':{'a':False,'b':True}}]
            with patch.object(audit,'audit_directory',side_effect=results):
                result=audit.aggregate_directories([root/'a',root/'b'])
            self.assertTrue(result['passed'],result)
            self.assertNotEqual(result['launch_source_hashes'][0][harness],result['launch_source_hashes'][1][harness])
            for key in [k for k in b[0]['source_hashes_at_launch'] if k!=harness and not k.endswith('native-probe.py')]:
                bad=copy.deepcopy(b[0]);bad['source_hashes_at_launch'][key]='changed-production-source'
                (root/'b/summary.json').write_text(json.dumps(bad))
                with patch.object(audit,'audit_directory',side_effect=results):
                    result=audit.aggregate_directories([root/'a',root/'b'])
                self.assertFalse(result['passed'],key)
                self.assertIn('A/B production source snapshot mismatch',result['errors'])



    def test_v2_fresh_parent_receipts_need_no_extra_mailbox_wait(self):
        good=self.namespace_case('mimo-flash','a')
        parent=good[2][0]
        waits={e['item']['call_id'] for e in parent['events'] if e.get('item',{}).get('name')=='wait_agent'}
        parent['events']=[e for e in parent['events'] if e.get('item',{}).get('call_id') not in waits]
        result=audit.audit_current(*good)
        self.assertTrue(result['passed'],result['details'])
        for mutation in ('missing','author','recipient','token','stale','outside-interval','child-turn','no-completion'):
            data=copy.deepcopy(good);p=data[2][0]
            receipts=[e for e in p['events'] if e.get('item',{}).get('type')=='agent_message' and 'FINAL_ANSWER' in json.dumps(e['item'])]
            receipt=receipts[1]
            if mutation=='missing':p['events']=[e for e in p['events'] if e not in receipts]
            elif mutation=='author':receipt['item']['author']='/root/wrong'
            elif mutation=='recipient':receipt['item']['recipient']='/root/wrong'
            elif mutation=='token':receipt['item']['content'][0]['text']+='wrong'
            elif mutation=='stale':receipt['item']['internal_chat_message_metadata_passthrough']['create_time']=0
            elif mutation=='outside-interval':receipt['line']=max(e['line'] for e in p['events'])+1
            else:
                child=data[2][1];event=next(e for e in child['events'] if e.get('event',{}).get('type')=='task_complete')
                if mutation=='child-turn':event['event']['turn_id']='wrong-child-turn'
                else:child['events'].remove(event)
            with self.subTest(mutation=mutation):
                result=audit.audit_current(*data)
                self.assertFalse(result['passed'])
                self.assertFalse(result['checks']['declared_case_native_waits_fresh_completion_order'])

    def test_actual_waits_remain_validated_even_with_correct_receipts(self):
        for mutation in ('target','error','namespace'):
            data=self.namespace_case('mimo-flash','a');p=data[2][0]
            call=next(e['item'] for e in p['events'] if e.get('item',{}).get('name')=='wait_agent')
            if mutation=='target':call['arguments']='{"target":"/root/wrong"}'
            elif mutation=='namespace':call['namespace']='functions'
            else:
                output=next(e['item'] for e in p['events'] if e.get('item',{}).get('type')=='function_call_output' and e['item']['call_id']==call['call_id'])
                output['output']='{"timed_out":false,"error":"native error"}'
            result=audit.audit_current(*data)
            self.assertFalse(result['checks']['declared_case_native_waits_fresh_completion_order'])

    def test_short_v2_prompt_uses_receipts_without_changing_tasks(self):
        spec=importlib.util.spec_from_file_location('receipt_prompt_probe',PATH.with_name('native-probe.py'))
        probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
        for case in ('a','b'):
            directory=ROOT/'docs/gateflow/shim-subagent-all-providers/evidence/mimo-flash'/('namespace-scenario-'+case+'-attempt-'+('3' if case=='a' else '2'))
            summary=json.loads((directory/'summary.json').read_text());old=summary['parent_prompt'];new=probe.short_v2_completion_prompt(old)
            self.assertIn('Do NOT wait for another mailbox update after receiving that final',new)
            self.assertIn('timeout_ms=30000',new)
            self.assertNotIn('Call native wait_agent and receive',new)
            self.assertNotIn('after every child task in this declared case, call',new)
            # Only completion prose changes; exact task strings/markers survive.
            for task in __import__('re').findall(r'Complete task: "(.*?)"',old):self.assertIn(task,new)
            for key in ('initial_marker','followup_marker','message_token'):
                self.assertEqual(new.count(summary[key]),old.count(summary[key]))
        source=PATH.with_name('native-probe.py').read_text()
        self.assertIn("if selected.get('multi_agent_version')=='v2':\n            prompt=short_v2_completion_prompt(prompt)",source)


if __name__ == '__main__':
    unittest.main()
