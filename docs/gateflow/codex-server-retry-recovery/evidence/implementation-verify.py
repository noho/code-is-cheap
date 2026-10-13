"""Capture S1's offline checks; never invoke a real runtime or deploy to live."""
import ast
import hashlib
import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
BEFORE = json.loads((EVIDENCE / 'implementation-before.json').read_text())
SOURCES = ['scripts/agent-run-result.py', 'tests/test_agent_run_results.py', 'README.md',
           'scripts/codex-agent-run', 'scripts/claude-agent-run', 'scripts/sync-agent-tools.sh']


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(argv):
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    return {'argv': argv, 'command': shlex.join(argv), 'cwd': str(ROOT), 'started_at': started,
            'finished_at': datetime.now(timezone.utc).isoformat(), 'exit': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr}


def main():
    mode = sys.argv[1]
    assert mode in ('v1', 'v2', 'v3')
    destination = EVIDENCE / f'implementation-{mode}.json'
    assert not destination.exists(), destination
    metadata = [run(argv) for argv in (['python3', '--version'], ['git', 'rev-parse', 'HEAD'],
                                      ['git', 'branch', '--show-current'])]
    record = {'gate': 'implementation', 'slice': 'S1', 'mode': mode,
              'driver_sha256': digest(Path(__file__).read_bytes()), 'metadata_commands': metadata,
              'source': {p: {'sha256': digest((ROOT / p).read_bytes()), 'text': (ROOT / p).read_text()}
                         for p in SOURCES}, 'commands': []}
    try:
        assert metadata[1]['stdout'] == BEFORE['commands'][1]['stdout']
        assert metadata[2]['stdout'].strip() == 'fix/codex-server-retry-recovery-20261013'
        if mode == 'v1':
            commands = [['python3', '-B', 'tests/test_agent_run_results.py',
                'RunnerResults.test_codex_server_retry_recovered_connection_notice',
                'RunnerResults.test_codex_server_retry_notice_lookalikes_rejected',
                'RunnerResults.test_codex_server_retry_notice_recovery_fences',
                'RunnerResults.test_codex_server_retry_notice_keeps_selected_checks',
                'RunnerResults.test_codex_server_retry_notice_keeps_process_failures', '-v']]
        elif mode == 'v2':
            commands = [['python3', '-B', 'tests/test_agent_run_results.py', '-v'],
                        ['git', 'diff', '--check'],
                        ['git', 'diff', '--', 'scripts/agent-run-result.py', 'tests/test_agent_run_results.py', 'README.md']]
        else:
            commands = [['python3', '-B', str(EVIDENCE / 'implementation-replay.py')]]
            record['input_sha256'] = digest((EVIDENCE / 'plan-baseline.json').read_bytes())
            record['replay_driver_sha256'] = digest((EVIDENCE / 'implementation-replay.py').read_bytes())
        for argv in commands:
            item = run(argv)
            record['commands'].append(item)
            print(item['command'], 'exit', item['exit'], flush=True)
            if argv[0] == 'python3':
                print(item['stdout'], end='', flush=True)
                print(item['stderr'], end='', flush=True)
            assert item['exit'] == 0, item['command']
        for path, expected in BEFORE['protected'].items():
            assert digest((ROOT / path).read_bytes()) == expected['sha256'], path
        record['protected_unchanged'] = True
        record['source_unchanged_during_checks'] = all(
            digest((ROOT / p).read_bytes()) == snapshot['sha256'] for p, snapshot in record['source'].items())
        assert record['source_unchanged_during_checks']
        if mode == 'v2':
            before = ast.parse(BEFORE['source']['scripts/agent-run-result.py']['text'])
            after = ast.parse((ROOT / 'scripts/agent-run-result.py').read_text())
            def without_matcher(tree):
                return [ast.dump(node, include_attributes=False) for node in tree.body
                        if not isinstance(node, ast.FunctionDef) or node.name != 'recognized_codex_connection_notice']
            assert without_matcher(before) == without_matcher(after)
            record['production_ast_outside_matcher_unchanged'] = True
            def old_tests(text):
                tree = ast.parse(text)
                return {node.name: ast.dump(node, include_attributes=False) for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')}
            old = old_tests(BEFORE['source']['tests/test_agent_run_results.py']['text'])
            new = old_tests((ROOT / 'tests/test_agent_run_results.py').read_text())
            assert all(new[name] == body for name, body in old.items())
            record['old_test_methods_ast_unchanged'] = sorted(old)
            record['new_test_methods'] = sorted(set(new) - set(old))
        record['assertions_completed'] = True
    except BaseException as error:
        record['failure'] = repr(error)
        raise
    finally:
        with destination.open('x') as output:
            json.dump(record, output, ensure_ascii=True, indent=2)
            output.write('\n')
        print('saved', destination.relative_to(ROOT), flush=True)


if __name__ == '__main__':
    main()
