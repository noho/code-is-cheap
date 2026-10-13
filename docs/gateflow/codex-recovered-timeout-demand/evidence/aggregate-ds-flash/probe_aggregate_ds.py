#!/usr/bin/env python3
"""Aggregate-gate focused probes for ds-flash (work unit codex-recovered-timeout-demand).

Synthetic inputs only: no business data, no model requests, no deployment. Reconstructs the
same-goal Judge TLS regression at collector level from the sanctioned minimal synthetic file,
demonstrates the V1/V2 diagnostic display difference that failed the first Judge replay harness
(harness display-equivalence assertion, not collector acceptance), and exercises cross-runtime
input-exit -> proof -> checks -> status/exit interactions.
"""
import ast
import datetime
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path('/Users/leo/workspace/code-is-cheap')
COLLECTOR = ROOT / 'scripts/agent-run-result.py'
EVID = ROOT / 'docs/gateflow/codex-recovered-timeout-demand/evidence'
OUT = EVID / 'aggregate-ds-flash'
BASE = '62c3b26adeb994e81043d7b1afbcd4c6eb8974ae'
SENTINEL = {'type': 'error', 'message': 'Synthetic upstream diagnostic: TLS handshake eof (unfamiliar wording)'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_collector(events_text, runtime='codex', native=0, runner=0, collector=COLLECTOR, extra=()):
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        output = td / 'output.jsonl'
        stderr = td / 'stderr.log'
        output.write_text(events_text)
        stderr.write_text('')
        result = subprocess.run(
            ['python3', '-B', str(collector), '--runtime', runtime, '--provider', 'synthetic',
             '--output', str(output), '--stderr', str(stderr),
             '--exit-code', str(native), '--runner-exit-code', str(runner), *extra],
            capture_output=True, text=True)
        report = json.loads(result.stdout) if result.stdout.strip() else None
        return {
            'exit': result.returncode,
            'stderr': result.stderr,
            'output_text': output.read_text(),
            'report': report,
            'summary': None if report is None else {k: report[k] for k in
                ('runtime_exit_code', 'runner_exit_code', 'agent_status', 'validation_status',
                 'result_status', 'terminal', 'session_id', 'usage', 'final_answer',
                 'diagnostic_counts')},
        }


def as_text(events):
    return '\n'.join(events if isinstance(events[0], str) else (json.dumps(e) for e in events)) + '\n'


def codex_ok(text='done'):
    return [{'type': 'thread.started', 'thread_id': 'test'}, {'type': 'turn.started'},
            {'type': 'item.completed', 'item': {'id': 'm', 'type': 'agent_message', 'text': text}},
            {'type': 'turn.completed', 'usage': {'tokens': 1}}]


def claude_ok(text='done'):
    return [{'type': 'system', 'subtype': 'init', 'model': 'synthetic'},
            {'type': 'result', 'subtype': 'success', 'is_error': False, 'result': text,
             'stop_reason': 'end_turn', 'terminal_reason': 'completed', 'api_error_status': None,
             'usage': {'tokens': 1}}]


def probe_a_judge_tls():
    """Sanctioned synthetic equivalent of the Judge TLS replay, run through the delivered collector."""
    src = EVID / 'minimal-judge-tls-recovery.jsonl'
    text = src.read_text()
    lines = [json.loads(l) for l in text.splitlines() if l.strip()]
    r = run_collector(text)
    rep = r['report']
    anomalies = [a for a in rep['anomalies']]
    checks = {
        'exit_zero': r['exit'] == 0,
        'completed': rep['agent_status'] == 'completed',
        'needs_review': rep['validation_status'] == 'needs_review',
        'not_assessed': rep['result_status'] == 'not_assessed',
        'terminal_turn_completed': rep['terminal'] == 'turn.completed',
        'counts': rep['diagnostic_counts'] == {'errors': 0, 'anomalies': 4, 'warnings': 0},
        'events_8': rep['events'] == 8,
        'final_text': rep['final_answer'] == lines[6]['item']['text'],
        'anomaly_lines_3_to_6': [a['line'] for a in anomalies] == [3, 4, 5, 6],
        'anomaly_full_event': all(a['message'] == str(lines[a['line'] - 1]) for a in anomalies),
        'anomaly_stream_and_source': all(a['stream'] == 'output' and a['path'] is None for a in anomalies),
        'four_tls_texts_retained': [f'Reconnecting... {n}/5' in anomalies[n - 2]['message'] for n in (2, 3, 4, 5)] == [True] * 4,
        'tls_notices_not_errors': rep['diagnostic_counts']['errors'] == 0,
    }
    # Negative control 1: same stream without the successful terminal must still reject.
    missing = run_collector(as_text(lines[:-1]))
    checks['missing_terminal_rejects'] = (
        missing['exit'] == 1 and missing['report']['agent_status'] == 'failed'
        and missing['report']['validation_status'] == 'rejected'
        and missing['report']['terminal'] is None
        and missing['report']['diagnostic_counts']['errors'] >= 1)
    # Negative control 2: malformed diagnostic message stays a structural error but the
    # independent native proof still yields completed + rejected + nonzero.
    malformed = run_collector(text.replace('{"type": "error", "message": "Reconnecting... 2/5', '{"type": "error", "message": 42, "was": "Reconnecting... 2/5'))
    checks['malformed_diag_completed_but_rejected'] = (
        malformed['exit'] == 1 and malformed['report']['agent_status'] == 'completed'
        and malformed['report']['validation_status'] == 'rejected'
        and malformed['report']['diagnostic_counts'] == {'errors': 1, 'anomalies': 3, 'warnings': 0})
    return {
        'input': str(src.relative_to(ROOT)), 'input_sha256': sha(src),
        'command': ['python3', '-B', 'scripts/agent-run-result.py', '--runtime', 'codex',
                    '--provider', 'synthetic', '--output', '<synthetic minimal-judge-tls-recovery.jsonl>',
                    '--stderr', '<empty>', '--exit-code', '0', '--runner-exit-code', '0'],
        'exit': r['exit'], 'summary': r['summary'],
        'anomaly_lines': [a['line'] for a in anomalies],
        'checks': checks,
        'missing_terminal': missing['summary'],
        'malformed_diag': {'exit': malformed['exit'], **malformed['summary']},
    }


def probe_b_display_equivalence():
    """Reconstruct the first Judge harness failure: V1 displayed the error item payload only."""
    events = [{'type': 'thread.started', 'thread_id': 'test'}, {'type': 'turn.started'},
              {'type': 'item.completed', 'item': {'id': 'fallback-1', 'type': 'error',
               'message': 'Synthetic fallback error item retained at the same source location.'}},
              {'type': 'item.completed', 'item': {'id': 'm', 'type': 'agent_message', 'text': 'done'}},
              {'type': 'turn.completed'}]
    v1 = OUT / 'v1-base-collector.py'
    v1.write_bytes(subprocess.run(['git', '-C', str(ROOT), 'show', f'{BASE}:scripts/agent-run-result.py'],
                                  capture_output=True, check=True).stdout)
    v1_run = run_collector(as_text(events), collector=v1)
    v2_run = run_collector(as_text(events))
    v1_diag = next(d for d in v1_run['report']['anomalies'] if 'fallback-1' in d['message'])
    v2_diag = next(d for d in v2_run['report']['anomalies'] if 'fallback-1' in d['message'])
    old_payload = ast.literal_eval(v1_diag['message'])
    new_payload = ast.literal_eval(v2_diag['message'])
    same_location = all(v1_diag[k] == v2_diag[k] for k in ('stream', 'line', 'path', 'proof_line'))
    checks = {
        'v1_message_is_item_payload': isinstance(old_payload, dict) and old_payload.get('type') == 'error'
                                     and old_payload.get('id') == 'fallback-1',
        'v2_message_is_full_envelope': new_payload.get('type') == 'item.completed'
                                       and isinstance(new_payload.get('item'), dict),
        'inner_item_identical': new_payload.get('item') == old_payload,
        'same_source_location': same_location,
        'both_untruncated': not v1_diag['truncated'] and not v2_diag['truncated'],
        'exact_display_equality_fails': v1_diag not in v2_run['report']['anomalies'],
        'text_identity': v1_diag['message'] == str(old_payload) and v2_diag['message'] == str(new_payload),
        'v1_retained_this_item': any('fallback-1' in d['message'] for d in v1_run['report']['anomalies']),
    }
    checks['revised_relation_holds'] = (checks['inner_item_identical'] and checks['same_source_location']
                                        and checks['both_untruncated'] and checks['v2_message_is_full_envelope'])
    return {
        'synthetic_stream': str(OUT / 'probe-b-events.jsonl'),
        'v1_collector_sha256': sha(v1),
        'v2_collector_sha256': sha(COLLECTOR),
        'v1_run': {'exit': v1_run['exit'], **v1_run['summary']},
        'v2_run': {'exit': v2_run['exit'], **v2_run['summary']},
        'v1_anomaly_message': v1_diag['message'],
        'v2_anomaly_message': v2_diag['message'],
        'checks': checks,
    }


def probe_c_cross_runtime():
    results = {}
    # C1: Claude accepts unfamiliar diagnostics after valid native completion.
    c1_events = claude_ok()
    c1_events[1:1] = [SENTINEL, {'type': 'error', 'message': 'unfamiliar demand timeout marker 29/5'}]
    c1 = run_collector(as_text(c1_events), runtime='claude')
    results['c1_claude_recovered_diagnostics_accept'] = {
        'exit': c1['exit'], **c1['summary'],
        'exit_ok': c1['exit'] == 0,
        'anomalies_2': c1['report']['diagnostic_counts'] == {'errors': 0, 'anomalies': 2, 'warnings': 0},
        'raw_log_retained': 'unfamiliar demand timeout marker' in c1['output_text'],
    }
    # C2: observed success-labeled content_filter must reject with diagnostics retained.
    c2_events = claude_ok()
    c2_events[1:1] = [SENTINEL]
    c2_events[-1]['stop_reason'] = 'content_filter'
    c2 = run_collector(as_text(c2_events), runtime='claude')
    results['c2_claude_content_filter_rejects'] = {
        'exit': c2['exit'], **c2['summary'],
        'exit_ok': c2['exit'] == 1,
        'anomaly_retained': c2['report']['diagnostic_counts']['anomalies'] == 1,
    }
    # C3: native nonzero input exit stays decisive and visible while diagnostics are retained.
    c3_events = codex_ok()
    c3_events.insert(2, SENTINEL)
    c3 = run_collector(as_text(c3_events), native=7, runner=7)
    results['c3_codex_native_nonzero'] = {
        'exit': c3['exit'], **c3['summary'],
        'exit_ok': c3['exit'] == 1,
        'report_keeps_native_code': c3['report']['runtime_exit_code'] == 7,
        'anomaly_retained': c3['report']['diagnostic_counts']['anomalies'] == 1,
    }
    # C4: duplicate/conflicting terminals reject in both runtimes and keep the first final.
    c4_codex = codex_ok()
    c4_codex.insert(-1, {'type': 'turn.failed', 'error': {'message': 'native failure'}})
    c4a = run_collector(as_text(c4_codex))
    c4_claude = claude_ok()
    c4_claude.append({'type': 'result', 'subtype': 'success', 'is_error': False, 'result': 'second'})
    c4b = run_collector(as_text(c4_claude), runtime='claude')
    results['c4_duplicate_terminals_conflict'] = {
        'codex': {'exit': c4a['exit'], 'exit_ok': c4a['exit'] == 1, **c4a['summary']},
        'claude': {'exit': c4b['exit'], 'exit_ok': c4b['exit'] == 1, **c4b['summary']},
        'first_final_kept': c4a['report']['final_answer'] == 'done' and c4b['report']['final_answer'] == 'done',
        'conflicting_both': c4a['report']['terminal'] == 'conflicting' and c4b['report']['terminal'] == 'conflicting',
    }
    # C5: trailing rate_limit_event metadata cannot alter proof, identity or totals.
    c5 = {}
    for runtime, events in (('codex', codex_ok()), ('claude', claude_ok())):
        events = list(events)
        events.append({'type': 'rate_limit_event', 'session_id': 'other', 'usage': {'tokens': 99},
                       'result': 'fake', 'terminal_reason': 'max_turns'})
        run = run_collector(as_text(events), runtime=runtime)
        c5[runtime] = {
            'exit': run['exit'], 'exit_ok': run['exit'] == 0, **run['summary'],
            'usage_unchanged': run['report']['usage'] == {'tokens': 1},
            'final_unchanged': run['report']['final_answer'] == 'done',
        }
    results['c5_trailing_metadata_inert'] = c5
    return results


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'probe-b-events.jsonl').write_text(as_text([
        {'type': 'thread.started', 'thread_id': 'test'}, {'type': 'turn.started'},
        {'type': 'item.completed', 'item': {'id': 'fallback-1', 'type': 'error',
         'message': 'Synthetic fallback error item retained at the same source location.'}},
        {'type': 'item.completed', 'item': {'id': 'm', 'type': 'agent_message', 'text': 'done'}},
        {'type': 'turn.completed'}]))
    a = probe_a_judge_tls()
    b = probe_b_display_equivalence()
    c = probe_c_cross_runtime()
    record = {
        'probe': 'aggregate-ds-flash', 'work_unit': 'codex-recovered-timeout-demand',
        'generated_at': datetime.datetime.now().astimezone().isoformat(),
        'python': sys.version.split()[0], 'platform': sys.platform,
        'collector_sha256': sha(COLLECTOR),
        'base_commit': BASE,
        'probe_a_judge_tls': a, 'probe_b_display_equivalence': b, 'probe_c_cross_runtime': c,
    }
    (OUT / 'results.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    def bools(obj):
        for value in obj.values():
            if isinstance(value, dict):
                yield from bools(value)
            elif isinstance(value, bool):
                yield value
    all_checks = list(a['checks'].values()) + list(b['checks'].values()) + list(bools(c))
    print(json.dumps({'all_bool_checks_true': all(all_checks), 'n_checks': len(all_checks),
                      'probe_a': a['checks'], 'probe_b': b['checks']}, ensure_ascii=False, indent=2))
    return 0 if all(all_checks) else 1


if __name__ == '__main__':
    raise SystemExit(main())
