#!/usr/bin/env python3
"""Check candidate scope against this isolated checkout's arrival state."""
import hashlib
import json
from pathlib import Path
import py_compile
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
ALLOWED = {
    'README.md', 'README.zh.md',
    'docs/gateflow/shim-subagent-delivery/native-probe.py',
    'tests/test_shim_native_namespace.py',
}
REPORT = 'docs/gateflow/shim-subagent-all-providers/review-fix-validation.md'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    before = json.loads((OUT / 'before-sha256.json').read_text())
    missing = [p for p in before if not (ROOT / p).is_file()]
    changed = {p: {'before': h, 'after': digest(ROOT / p)} for p, h in before.items()
               if (ROOT / p).is_file() and digest(ROOT / p) != h}
    assert not missing, missing
    assert set(changed) == ALLOWED, changed
    paths = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
    new = sorted(p for p in paths if p and p not in before)
    prefix = str(OUT.relative_to(ROOT)) + '/'
    assert all(p == REPORT or p.startswith(prefix) for p in new), new
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip()
    assert branch == 'fix/shim-observer-review-20261108', branch
    diff = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True)
    assert diff.returncode == 0, diff.stdout + diff.stderr
    compile_paths = ['docs/gateflow/shim-subagent-delivery/native-probe.py',
                     'tests/test_shim_native_namespace.py', 'tests/test_shim_native_evidence.py',
                     'tests/test_shim_subagent_delivery.py']
    with tempfile.TemporaryDirectory(prefix='shim-observer-compile-') as temp:
        for i, p in enumerate(compile_paths):
            py_compile.compile(str(ROOT / p), cfile=str(Path(temp) / (str(i) + '.pyc')), doraise=True)
    result = {'branch': branch, 'baseline_file_count': len(before), 'changed_existing_files': changed,
              'new_files': new, 'all_other_baseline_files_unchanged': True,
              'git_diff_check_exit': diff.returncode, 'py_compile_passed': compile_paths,
              'protected_sha256': {p: digest(ROOT / p) for p in (
                  'codex-agent/bin/codex-auto-review-shim', 'codex-agent/shim-routes.json',
                  'docs/gateflow/shim-subagent-delivery/audit-native-evidence.py',
                  'docs/gateflow/shim-subagent-all-providers/review-freeze-v1.json')}}
    (OUT / 'validation-scope.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
