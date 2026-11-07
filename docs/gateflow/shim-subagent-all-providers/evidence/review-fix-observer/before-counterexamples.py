#!/usr/bin/env python3
"""Reproduce the four pre-fix observer failures offline from arrival bytes."""
import gzip
import json
from pathlib import Path
import types
import urllib.request
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent


def main():
    path = ROOT / 'docs/gateflow/shim-subagent-delivery/native-probe.py'
    probe = types.ModuleType('before_observer_probe')
    probe.__file__ = str(path)
    exec(compile(gzip.decompress((OUT / 'before-native-probe.py.gz').read_bytes()), str(path), 'exec'), probe.__dict__)
    rows = []
    for method, body, expected in [('GET', None, 'TypeError'), ('POST', b'', 'JSONDecodeError'),
                                   ('POST', b'not-json', 'JSONDecodeError'), ('POST', b'[]', 'AttributeError')]:
        shim = probe.load('counterexample_shim_' + str(len(rows)), ROOT / 'codex-agent/bin/codex-auto-review-shim')
        original_open = Mock()
        shim.upstream_open = original_open
        probe.install_observers(shim, {})
        error = None
        try:
            if body:
                shim.fix_agent_messages(body)
            shim.upstream_open(urllib.request.Request('http://127.0.0.1/responses', data=body, method=method), timeout=1)
        except Exception as exc:
            error = type(exc).__name__
        assert error == expected and original_open.call_count == 0
        rows.append({'method': method, 'body_bytes': len(body or b''), 'body_sha256': probe.sha(body or b''),
                     'observer_error_class': error, 'original_open_calls': original_open.call_count})
    result = {'offline_only': True, 'source_driver_sha256': probe.sha(gzip.decompress((OUT / 'before-native-probe.py.gz').read_bytes())),
              'results': rows}
    (OUT / 'before-counterexamples.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
