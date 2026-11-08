"""Extra offline real-handler check: Kimi map sources stay top-only.
No native/model inference; only loopback fake upstream and actual helper observer.
"""
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'tests'))
import test_shim_native_namespace as harness

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
probe=load('bounded_probe',ROOT/'docs/gateflow/shim-subagent-delivery/native-probe.py')
audit=load('bounded_auditor',ROOT/'docs/gateflow/shim-subagent-delivery/audit-native-evidence.py')
module=probe.load('bounded_shim',ROOT/'codex-agent/bin/codex-auto-review-shim')
route={'to':'test','native_agent_request_flatten':True,'native_agent_response_restore':True,'agent_message_fix':True,'id_fix':False,'json_fmt_fix':False,'drop_tools_item':False}
wire,_,_=probe.install_observers(module,route)
original=module._make_server

def make_server(r):return original({**r,**route})
with patch.object(harness,'shim',module),patch.object(module,'_make_server',make_server):
    with harness.service(lambda h,b,n:harness.reply(h,harness.event()+b'data: {"type":"response.completed","response":{"output":[]}}\n\n')) as (port,seen):
        top=harness.request();top['input']=[{'type':'additional_tools','tools':[harness.group('collaboration','additional_only')]}]
        additional_only={'model':'test','input':top['input']}
        for doc in (top,additional_only):assert harness.call(port,doc)[0]==200
assert len(wire)==2
for record,expected in zip(wire,({'spawn_agent':'multi_agent_v1'},{})):
    stage=record['native_request_stage'];assert stage['map']==expected
    audit.audit_namespace_record({'route':route},record)
    assert stage['selected_descriptor_paths']==([['tools',0]] if expected else [])
    assert any(location['containing_item_type']=='additional_tools' for location in record['descriptor_locations'])
print(json.dumps({'passed':True,'real_handler_cases':2,'maps':[w['native_request_stage']['map'] for w in wire],'scope':'flatten=True additional native descriptors are location-proved but never selected/mapped/rewritten'},indent=2))
