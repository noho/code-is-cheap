"""Offline-only affected-suite runner; no probe launch or provider access."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
SUITES = ('test_shim_native_namespace.py', 'test_shim_native_evidence.py',
          'test_shim_subagent_delivery.py')


def run(name):
    command = [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', name, '-v']
    started = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    (OUT/(name+'.log')).write_text(result.stdout)
    count = re.search(r'Ran (\d+) tests?', result.stdout)
    return {'command': command, 'exit': result.returncode, 'tests': int(count[1]) if count else None,
            'seconds': round(time.monotonic()-started, 3), 'log': name+'.log'}


def main():
    helper = ROOT/'codex-agent/bin/codex-auto-review-shim'
    before = hashlib.sha256(helper.read_bytes()).hexdigest()
    with ThreadPoolExecutor(max_workers=3) as pool:
        suites = list(pool.map(run, SUITES))
    sources = ('codex-agent/bin/codex-auto-review-shim',
               'docs/gateflow/shim-subagent-delivery/native-probe.py',
               'docs/gateflow/shim-subagent-delivery/audit-native-evidence.py',
               'tests/test_shim_native_namespace.py', 'tests/test_shim_native_evidence.py',
               'tests/test_shim_subagent_delivery.py')
    with tempfile.TemporaryDirectory() as tmp:
        compile_command = [sys.executable, '-m', 'py_compile', *sources]
        compile_result = subprocess.run(compile_command, cwd=ROOT,
            env={**os.environ, 'PYTHONPYCACHEPREFIX': tmp}, capture_output=True, text=True)
    diff_command = ['git', 'diff', '--check']
    diff_result = subprocess.run(diff_command, cwd=ROOT, capture_output=True, text=True)
    after = hashlib.sha256(helper.read_bytes()).hexdigest()
    result = {'helper_before': before, 'helper_after': after, 'helper_unchanged_during_run': before==after,
              'suites': suites, 'total_tests': sum(s['tests'] or 0 for s in suites),
              'py_compile': {'command': compile_command, 'exit': compile_result.returncode,
                             'output': compile_result.stdout+compile_result.stderr},
              'diff_check': {'command': diff_command, 'exit': diff_result.returncode,
                             'output': diff_result.stdout+diff_result.stderr}}
    (OUT/'validation-results.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    return int(before!=after or any(s['exit'] for s in suites) or
               compile_result.returncode or diff_result.returncode)


if __name__ == '__main__':
    raise SystemExit(main())
