"""V3: replay saved synthetic inputs and keep every collector report and invocation."""
import hashlib
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    destination = EVIDENCE / 'implementation-replay-reports.json'
    assert not destination.exists(), destination
    baseline = EVIDENCE / 'plan-baseline.json'
    saved = json.loads(baseline.read_text())
    adapter = ROOT / 'scripts/agent-run-result.py'
    evidence = {'created_at': datetime.now(timezone.utc).isoformat(), 'cwd': str(ROOT),
                'baseline_sha256': digest(baseline.read_bytes()),
                'collector_sha256': digest(adapter.read_bytes()),
                'replay_driver_sha256': digest(Path(__file__).read_bytes()), 'cases': []}
    print('collector_sha256', evidence['collector_sha256'])
    try:
        with tempfile.TemporaryDirectory(prefix='server-retry-replay-') as temp:
            output, stderr = Path(temp) / 'output.jsonl', Path(temp) / 'stderr.log'
            for case in saved['offline_cases']:
                output.write_text(case['input_jsonl'])
                stderr.write_text(case['stderr_input'])
                argv = ['python3', '-B', str(adapter), '--runtime', 'codex', '--provider', 'gpt-6-sol',
                        '--output', str(output), '--stderr', str(stderr), '--exit-code', '0', '--runner-exit-code', '0']
                run = subprocess.run(argv, capture_output=True, text=True)
                item = {'scenario': case['scenario'], 'argv': argv, 'outer_exit': run.returncode,
                        'stdout': run.stdout, 'stderr': run.stderr,
                        'input_events': case['input_events'], 'input_jsonl': case['input_jsonl'],
                        'input_sha256': digest(output.read_bytes()), 'stderr_input': case['stderr_input'],
                        'stderr_input_sha256': digest(stderr.read_bytes())}
                evidence['cases'].append(item)
                report = json.loads(run.stdout)
                item['report'] = report
                positive = case['scenario'] == 'case10_exact_notices_valid_finish'
                expected_exit = 0 if positive else case['outer_exit']
                expected_status = 'passed' if positive else case['report']['validation_status']
                expected_counts = {'errors': 0, 'anomalies': 0, 'warnings': 2} if positive else case['report']['diagnostic_counts']
                item['expected'] = {'outer_exit': expected_exit, 'validation_status': expected_status,
                                    'diagnostic_counts': expected_counts}
                assert run.returncode == expected_exit, (case['scenario'], run.stderr)
                assert report['runner_exit_code'] == expected_exit
                assert report['validation_status'] == expected_status
                assert report['diagnostic_counts'] == expected_counts
                assert report['result_status'] == 'not_assessed' and report['runtime_exit_code'] == 0
                category = 'warnings' if positive else 'errors'
                if case['scenario'].startswith('case10_'):
                    for line, event in enumerate(case['input_events'], 1):
                        if event['type'] == 'error':
                            matches = [d for d in report[category] if d['line'] == line and event['message'] in d['message']]
                            assert len(matches) == 1 and matches[0]['stream'] == 'output'
                            prefix = 'Recovered Codex connection notice:' if positive else 'recovery not proven'
                            assert prefix in matches[0]['message']
                            # Independent exact diagnostic oracle, beyond the plan's substring check.
                            exact_prefix = ('Recovered Codex connection notice: ' if positive else
                                            'Codex connection notice recovery not proven (terminal identity or shape): ')
                            expected_message = exact_prefix + str(event)
                            assert matches[0] == {'stream': 'output', 'line': line, 'message': expected_message,
                                                  'message_chars': len(expected_message), 'truncated': False,
                                                  'path': None, 'proof_line': None}
                item['assertions_completed'] = True
                print(case['scenario'], run.returncode, report['validation_status'], report['diagnostic_counts'])
        evidence['assertions_completed'] = True
    except BaseException as error:
        evidence['failure'] = repr(error)
        raise
    finally:
        with destination.open('x') as output:
            json.dump(evidence, output, ensure_ascii=True, indent=2)
            output.write('\n')
        print('saved', destination.relative_to(ROOT))


if __name__ == '__main__':
    main()
