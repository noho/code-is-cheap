"""Reproducible collector samples: synthetic protocol inputs only, no provider calls."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[5]
evidence = Path(__file__).resolve().parent
protocol = evidence.parent / 'protocol'
collector = root / 'scripts/agent-run-result.py'
codex = [dict(type='thread.started', thread_id='synthetic-s1'), dict(type='turn.started'),
         dict(type='item.completed', item=dict(id='final', type='agent_message', text='Synthetic final.')),
         dict(type='turn.completed', usage=dict(input_tokens=0, output_tokens=2))]
novel = dict(type='error', message='Novel recovered demand Ω\nindependent second line', future=dict(code=42))
cases = [('codex-novel-after-final', 'codex', codex[:-1] + [novel] + codex[-1:], 0, 'needs_review', 'completed')]
startup = [dict(type='item.completed', item=dict(id=f'd{i}', type='error', message=f'Unfamiliar startup {i}')) for i in range(3)]
cases.append(('codex-many-startup', 'codex', codex[:1]+startup+codex[1:], 0, 'needs_review', 'completed'))
cases.append(('codex-missing-terminal', 'codex', codex[:-1]+[novel], 1, 'rejected', 'failed'))
cases.append(('codex-parse-error-with-proof', 'codex', codex[:2]+['not-json']+codex[2:], 1, 'rejected', 'completed'))
for reason in ('end_turn', 'stop_sequence'):
    events = [json.loads(line) for line in (protocol/f'claude-local-{reason}-minimal.jsonl').read_text().splitlines()]
    cases.append((f'claude-{reason}-clean-equivalent', 'claude', events, 0, 'passed', 'completed'))
    diagnostics = [novel, dict(type='system', subtype='api_retry', attempt=dict(future=True), error=None),
                   dict(type='assistant', error=None, message=dict(content=[dict(type='text', text='Synthetic intermediate.')]))]
    cases.append((f'claude-{reason}-unknown-diagnostics', 'claude', events[:-1]+diagnostics+events[-1:], 0, 'needs_review', 'completed'))
    failed = events[:-1] + [novel, events[-1] | dict(stop_reason='content_filter')]
    cases.append((f'claude-{reason}-negative-overrides-success', 'claude', failed, 1, 'rejected', 'failed'))
summary = []
for name, runtime, events, expected_exit, expected_validation, expected_agent in cases:
    directory = evidence / 'samples' / name
    directory.mkdir(parents=True, exist_ok=True)
    output = directory/'output.jsonl'
    output.write_text('\n'.join(json.dumps(event, ensure_ascii=False) if isinstance(event, dict) else event for event in events)+'\n')
    stderr = directory/'stderr.log'; stderr.write_text('')
    command = [sys.executable, '-B', str(collector), '--runtime', runtime, '--provider', 'synthetic',
               '--output', str(output), '--stderr', str(stderr), '--exit-code', '0', '--runner-exit-code', '0']
    run = subprocess.run(command, capture_output=True, text=True)
    (directory/'report.json').write_text(run.stdout)
    (directory/'collector.stderr').write_text(run.stderr)
    report = json.loads(run.stdout)
    assert (run.returncode, report['validation_status'], report['agent_status']) == (expected_exit, expected_validation, expected_agent), (name, run.stdout, run.stderr)
    assert report['result_status'] == 'not_assessed'
    summary.append(dict(case=name, command=command, exit_code=run.returncode,
        agent_status=report['agent_status'], validation_status=report['validation_status'],
        result_status=report['result_status'], counts=report['diagnostic_counts'],
        input_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        report_sha256=hashlib.sha256(run.stdout.encode()).hexdigest()))
(evidence/'synthetic-samples.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps(dict(cases=len(summary), passed=len(summary), failed=0,
    collector_sha256=hashlib.sha256(collector.read_bytes()).hexdigest())))
