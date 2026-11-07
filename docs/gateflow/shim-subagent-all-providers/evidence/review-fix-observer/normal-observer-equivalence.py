#!/usr/bin/env python3
"""Offline synthetic loopback comparison of frozen-v1 and candidate observers."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import types
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
DRIVER = ROOT / 'docs/gateflow/shim-subagent-delivery/native-probe.py'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize(value):
    # Wall-clock scheduling differs; all other fields must be exactly equal.
    if isinstance(value, dict):
        return {k: '<monotonic>' if k.endswith('_at') else normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize(v) for v in value]
    return value


def main():
    ns = load('equivalence_namespace_tests', ROOT / 'tests/test_shim_native_namespace.py')
    old = types.ModuleType('frozen_v1_probe')
    old.__file__ = str(DRIVER)
    old_source = gzip.decompress((OUT / 'before-native-probe.py.gz').read_bytes())
    exec(compile(old_source, str(DRIVER), 'exec'), old.__dict__)
    new = load('candidate_probe', DRIVER)
    compress = gzip.compress
    results = []
    for name, flatten, additional, guardian, encoding in (
        ('kimi-top-level', True, False, False, ''),
        ('mimo-additional-tools', False, True, False, ''),
        ('kimi-gzip', True, False, False, 'gzip'),
        ('guardian-bypass', False, False, True, ''),
    ):
        records = []
        responses = []
        for version, probe in (('v1', old), ('candidate', new)):
            module = probe.load('equivalence_' + version, ROOT / 'codex-agent/bin/codex-auto-review-shim')
            route = {'to': 'test', 'native_agent_request_flatten': flatten,
                     'native_agent_response_restore': True, 'agent_message_fix': True,
                     'id_fix': False, 'json_fmt_fix': False, 'drop_tools_item': False}
            wire, lock, local = probe.install_observers(module, route)
            original = module._make_server
            def make_server(r):
                return original({**r, **route})
            doc = ns.request()
            doc['client_metadata'] = {'thread_id': 'offline-' + name}
            if additional:
                doc['input'] = [{'type': 'additional_tools', 'tools': doc.pop('tools')}]
            if guardian:
                doc['model'] = 'codex-auto-review'
            data = ns.event() + b'data: {"type":"response.completed","response":{"output":[]}}\n\n'
            with patch.object(ns, 'shim', module), patch.object(module, '_make_server', make_server), \
                    patch.object(ns.gzip, 'compress', lambda value: compress(value, mtime=0)), \
                    patch.dict(module.ENCODERS, {'gzip': lambda value: compress(value, mtime=0)}), \
                    patch.object(module.Handler, '_log'):
                with ns.service(lambda h, b, n: ns.reply(h, data)) as (port, seen):
                    status, headers, body = ns.call(port, doc, encoding)
                    responses.append((status, body, seen[0][2]))
            assert len(wire) == 1
            records.append(normalize(wire[0]))
        assert records[0] == records[1], name
        assert responses[0] == responses[1], name
        results.append({'case': name, 'wire_equal_except_monotonic_times': True,
                        'request_and_response_bytes_equal': True,
                        'normalized_wire_sha256': hashlib.sha256(json.dumps(records[0], sort_keys=True).encode()).hexdigest()})
    result = {'offline_only': True, 'native_inference_runs': 0,
              'before_driver_sha256': hashlib.sha256(old_source).hexdigest(),
              'candidate_driver_sha256': hashlib.sha256(DRIVER.read_bytes()).hexdigest(),
              'results': results}
    (OUT / 'normal-observer-equivalence.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
