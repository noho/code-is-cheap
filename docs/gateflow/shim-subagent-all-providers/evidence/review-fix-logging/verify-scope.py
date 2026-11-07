"""Verify the entry preservation boundary and diagnostic-only helper delta."""
import ast
import difflib
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
BASELINE = 'a6246a4bc810125437992791aedcc8f2aa4c072f55e2bcf3691562feecd8e1e6'
HELPER = 'codex-agent/bin/codex-auto-review-shim'
ALLOWED = {HELPER, 'README.md', 'README.zh.md',
           'tests/test_shim_native_namespace.py', 'tests/test_shim_native_evidence.py'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


entry = json.loads((OUT/'entry-manifest.json').read_text())
changed = {name: {'before': digest, 'after': sha(ROOT/name) if (ROOT/name).is_file() else None}
           for name, digest in entry.items() if not (ROOT/name).is_file() or sha(ROOT/name)!=digest}
assert set(changed)==ALLOWED, changed
names = set(subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],
                                   cwd=ROOT).decode().split('\0'))-{''}
added = sorted(names-set(entry))
prefix = str(OUT.relative_to(ROOT))+'/'
concurrent = json.loads((OUT/'concurrent-controller-additions.json').read_text())
assert all(sha(ROOT/name)==digest for name,digest in concurrent.items())
receipt = json.loads((ROOT/'docs/gateflow/shim-subagent-all-providers/controller-candidate-source.json').read_text())
for record in receipt['files']:
    assert entry[record['file']]==record['sha256']
    assert hashlib.sha256(gzip.decompress((ROOT/record['snapshot']).read_bytes())).hexdigest()==record['sha256']
assert all(name.startswith(prefix) or name==
           'docs/gateflow/shim-subagent-all-providers/review-logging-fix-validation.md' or name in concurrent
           for name in added), added

old = gzip.decompress((OUT/'before-codex-auto-review-shim.gz').read_bytes())
assert hashlib.sha256(old).hexdigest()==entry[HELPER]==BASELINE
snapshot = ROOT/'docs/gateflow/shim-subagent-all-providers/evidence/mimo-flash/namespace-scenario-a-attempt-4'/(BASELINE+'.source.gz')
assert gzip.decompress(snapshot.read_bytes())==old
new = (ROOT/HELPER).read_bytes()
trees = [ast.parse(source) for source in (old,new)]
handlers = [next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Handler') for tree in trees]
methods = [{n.name:ast.dump(n) for n in handler.body if isinstance(n,ast.FunctionDef)} for handler in handlers]
assert methods[0].keys()==methods[1].keys()
changed_methods = [name for name in methods[0] if methods[0][name]!=methods[1][name]]
assert changed_methods==['_summary','_handle'], changed_methods
spec = importlib.util.spec_from_file_location('logging_contracts', ROOT/'tests/test_shim_native_namespace.py')
tests = importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
assert len({tests.LoggingContracts.without_request_diagnostics(handler) for handler in handlers})==1
for tree, handler in zip(trees,handlers):
    tree.body.remove(handler)
assert ast.dump(trees[0])==ast.dump(trees[1])

def diagnostics(handler):
    method = next(n for n in handler.body if isinstance(n,ast.FunctionDef) and n.name=='_handle')
    start = next(i for i,n in enumerate(method.body) if isinstance(n,ast.Assign) and
                 any(isinstance(t,ast.Name) and t.id=='warn' for t in n.targets))
    return ast.dump(ast.Module(body=method.body[start:start+3], type_ignores=[]))

assert diagnostics(handlers[0])==diagnostics(handlers[1])
diff = ''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),
                                  fromfile='a6246-baseline/'+HELPER,tofile='logging-fix/'+HELPER))
(OUT/'helper-v-a6246.diff').write_text(diff)
all_diff = ''
for name in sorted(ALLOWED):
    before = gzip.decompress((OUT/('before-'+Path(name).name+'.gz')).read_bytes()).decode()
    all_diff += ''.join(difflib.unified_diff(before.splitlines(True),(ROOT/name).read_text().splitlines(True),
                                           fromfile='entry/'+name,tofile='logging-fix/'+name))
(OUT/'all-authored-changes.diff').write_text(all_diff)

spec = importlib.util.spec_from_file_location('offline_logging_auditor',
    ROOT/'docs/gateflow/shim-subagent-delivery/audit-native-evidence.py')
auditor = importlib.util.module_from_spec(spec); spec.loader.exec_module(auditor)
audit_results = {}
for attempt in (3,4):
    directory = ROOT/'docs/gateflow/shim-subagent-all-providers/evidence/mimo-flash'/f'namespace-scenario-a-attempt-{attempt}'
    result = auditor.audit_directory(directory,scenario='a')
    wire = json.loads((directory/'wire.json').read_text())
    summary = json.loads((directory/'summary.json').read_text())
    audit_results[f'A{attempt}'] = {
        'directory':str(directory.relative_to(ROOT)), 'passed':result['passed'],
        'coverage':result['coverage'], 'checks':result['checks'],
        'auditor_sha256':result['auditor_sha256'], 'input_sha256':result['input_sha256'],
        'capture_helper_sha256':summary['source_hashes_at_launch'][HELPER],
        'requests':len(wire), 'active_maps':sum(bool(w['native_request_stage']['map']) for w in wire),
        'parent_receipts_verified':len(result['details'].get('declared_case_native_waits_fresh_completion_order',{}).get('v2_receipts',[]))
            if isinstance(result['details'].get('declared_case_native_waits_fresh_completion_order'),dict) else 0,
        'namespace_additions':sum(a['namespace_added_count'] for w in wire for a in w['outbound_attempts'])}
assert audit_results['A4']['passed'] and not audit_results['A3']['passed']
(OUT/'actual-a4-a3-current-audits.json').write_text(json.dumps(audit_results,indent=2)+'\n')

prior = json.loads((ROOT/'docs/gateflow/shim-subagent-all-providers/evidence/location-offline/offline-validation.json').read_text())
reused = []
for record in prior['reused_mandatory_checks']:
    source = 'tests/'+record['pattern']
    assert sha(ROOT/source)==entry[source]
    assert sha(ROOT/record['log'])==record['sha256']==entry[record['log']]
    assert record['exit']==0
    reused.append({'source':source, 'source_sha256':entry[source], 'tests':record['tests'],
                   'log':record['log'], 'log_sha256':record['sha256'], 'archived_exit':record['exit']})
assert sum(record['tests'] for record in reused)==90
(OUT/'unchanged-path-90-reuse.json').write_text(json.dumps({
    'checks':reused, 'count':90, 'new_execution':False,
    'applicability':'Entry sources and archived passing logs match exact hashes. All helper module definitions except diagnostic _summary and relocation of the unchanged standard log block are AST-identical to a6246; affected handler paths were actually rerun. Prior native/configuration/source applicability limits remain in force.'},indent=2)+'\n')

result = {
    'baseline_helper_sha256':BASELINE, 'final_helper_sha256':hashlib.sha256(new).hexdigest(),
    'A4_baseline_snapshot_identical':True, 'entry_file_count':len(entry),
    'changed_existing_files':changed, 'new_files':[name for name in added if name not in concurrent],
    'concurrent_controller_preservation_additions_unchanged':concurrent,
    'all_other_entry_files_unchanged':True, 'unchanged_existing_file_count':len(entry)-len(changed),
    'changed_handler_methods':changed_methods, 'standard_log_AST_unchanged':True,
    'handler_nonlogging_AST_unchanged':True, 'all_other_module_AST_unchanged':True,
    'unchanged_handler_methods':[name for name in methods[0] if name not in changed_methods],
    'native_source_applicability':'Old captures remain attributed to their exact launch helper. Only diagnostics change from a6246; all transforms, relay, routes/auth/model/guardian/retry control flow and module globals match after removing the unchanged standard diagnostic block and its summary owner.',
    'prior_90_check_reuse':'All nonlogging implementation/configuration files unchanged vs entry; prior 90-check applicability remains bounded by the archived manifests and settings, not current provider availability.',
    'no_new_provider_inference':True}
(OUT/'validation-scope.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='new_files'},indent=2))
