"""Official snapshot assembly, native parsing and narrow sync recovery."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/patch-codex-model-catalog.py'
CARDS = ROOT / 'codex-agent/profiles'
SPEC = importlib.util.spec_from_file_location('patch_codex_model_catalog', SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
# Independent approved manifest data, with no dependency on Gateflow/Downloads.
HASHES = {
    'ds': 'd47876f3bca395fe2d9d3c7fc7312282a60da8a2479dd13b995cb8e0fe2695dd',
    'glm': '94cf9e8df540be39aa2948bf14ae665ec76699b1740d5344f499dd67fc71d1a3',
    'kimi': '61990fe840fe299eafc08460b16da5b53c720cc34ccd147e820265dd2f1f50d4',
    'mimo': '8834dc34d879b8489b7376a5a1788f0d1b696f8410fc2df3544ad38ab145601a',
    'qwen': '4bc94831cb66e43aaf4c375543f92883bfa1d3116a4065c5796c5de29e8a019c',
}
NATIVE = {'models': [
    {'slug': 'codex-auto-review', 'tool_mode': 'code_mode_only', 'use_responses_lite': True,
     'base_instructions': 'Synthetic guardian security', 'security_extension': {'keep': True}},
    {'slug': 'renamed-direct', 'base_instructions': 'Synthetic local instructions',
     'shell_type': 'unified_exec', 'use_responses_lite': False, 'experimental_supported_tools': [],
     'future_schema_field': {'enabled': True}},
]}


def fixture_env(root):
    return dict(HOME=str(root / 'home'), CODEX_SHARED_HOME=str(root / 'home/.codex'),
                CODEX_AGENT_TARGET=str(root / 'home/.codex-agent'),
                PATH=f"{root / 'bin'}:{os.environ['PATH']}",
                TMPDIR=str(root), NO_PROXY='127.0.0.1,localhost')


def stage_cards(home, cards=None):
    cards = cards or home
    cards.mkdir(parents=True, exist_ok=True)
    for path in CARDS.glob('*/config.toml'):
        (cards / f'{path.parent.name}.config.toml').write_text(
            path.read_text().replace('@HOME@/.codex', str(home)))


class SessionTemplateTests(unittest.TestCase):
    """The native direct-session donor is used only by local."""
    def setUp(self):
        module.warnings.clear()
        self.direct = copy.deepcopy(NATIVE['models'][1])

    def test_local_donor_can_be_renamed_and_is_deep_copied(self):
        for slug in ('gpt-5.5', 'future-direct-model'):
            donor = self.direct | {'slug': slug}
            catalog = {'models': [NATIVE['models'][0], donor]}
            session = module.session_entry(catalog, 'local-model', 1000000)
            self.assertEqual(session['base_instructions'], donor['base_instructions'])
            self.assertEqual(session['tool_mode'], 'direct')
            session['future_schema_field']['enabled'] = False
            self.assertTrue(donor['future_schema_field']['enabled'])

    def test_incompatible_local_donors_fail_closed(self):
        for changed in ({'tool_mode': 'code_mode_only'}, {'shell_type': 'default'},
                        {'use_responses_lite': True}, {'experimental_supported_tools': ['clock']},
                        {'base_instructions': ''}, {'slug': 'codex-auto-review'}):
            with self.subTest(changed=changed):
                self.assertIsNone(module.session_entry({'models': [self.direct | changed]}, 'local', 100))
        self.assertIsNone(module.session_entry({'models': [self.direct]}, self.direct['slug'], 100))


class OfficialAssemblyTests(unittest.TestCase):
    def setUp(self):
        module.warnings.clear()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        stage_cards(self.home)
        self.addCleanup(patch.stopall)
        patch.object(module, 'CATALOG_DIR', self.home / 'model-catalogs').start()

    def test_tracked_snapshots_and_all_eight_complete_mappings(self):
        self.assertEqual(module.SOURCE_HASHES, HASHES)
        with patch.object(module, 'session_entry', side_effect=AssertionError('cloud donor forbidden')):
            for profile, (family, donor_slug, selected_slug) in module.OFFICIAL.items():
                with self.subTest(profile=profile):
                    raw = (module.SOURCE_DIR / f'{family}-model-catalogs.json').read_bytes()
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), HASHES[family])
                    source = json.loads(raw)
                    output = module.assemble(NATIVE, profile, self.home)
                    extra = 2 if profile == 'glm-flash' else 1
                    self.assertEqual(output['models'][:-extra], source['models'])
                    self.assertEqual({k:v for k,v in output.items() if k != 'models'},
                                     {k:v for k,v in source.items() if k != 'models'})
                    selected = next(m for m in output['models'] if m['slug'] == selected_slug)
                    donor = next(m for m in source['models'] if m['slug'] == donor_slug)
                    if profile == 'glm-flash':
                        self.assertEqual({k:v for k,v in selected.items() if k not in ('slug','display_name','description')},
                                         {k:v for k,v in donor.items() if k not in ('slug','display_name','description')})
                        self.assertIn('derived', selected['display_name'])
                        self.assertIn('User-authorized', selected['description'])
                    else:
                        self.assertEqual(selected, donor)
                    guardian = output['models'][-1]
                    self.assertEqual({k:v for k,v in guardian.items() if k not in ('tool_mode','use_responses_lite')},
                                     {k:v for k,v in NATIVE['models'][0].items() if k not in ('tool_mode','use_responses_lite')})
                    self.assertEqual(guardian['tool_mode'], 'code_mode_only' if family == 'mimo' else 'direct')
                    self.assertEqual(guardian['use_responses_lite'], family == 'mimo')
                    if profile == 'qwen':
                        self.assertNotIn('max_context_window', selected)
                        self.assertEqual(selected['shell_type'], 'default')
                    if profile == 'kimi':
                        self.assertNotIn('kimi-k3', [m['slug'] for m in output['models']])
        self.assertEqual(module.warnings, [])

    def changed_source(self, family, change):
        source_dir = self.home / 'sources'
        source_dir.mkdir(exist_ok=True)
        doc = json.loads((module.SOURCE_DIR / f'{family}-model-catalogs.json').read_bytes())
        changed = change(doc)
        raw = json.dumps(changed).encode()
        (source_dir / f'{family}-model-catalogs.json').write_bytes(raw)
        patch.object(module, 'SOURCE_DIR', source_dir).start()
        patch.dict(module.SOURCE_HASHES, {family: hashlib.sha256(raw).hexdigest()}).start()
        return changed

    def test_unknown_nested_extension_preserves_copy_ownership(self):
        def change(doc):
            doc['future_root'] = {'metadata': [None, {'opaque': True}]}
            doc['models'][0]['future_nested'] = {'keep': ['x']}
            return doc
        source = self.changed_source('kimi', change)
        generated = module.assemble(NATIVE, 'kimi', self.home)
        self.assertEqual(generated['future_root'], source['future_root'])
        self.assertEqual(generated['models'][:-1], source['models'])
        generated['models'][0]['future_nested']['keep'].append('y')
        self.assertEqual(module.official_source('kimi'), source)

    def test_source_integrity_and_missing_file_errors(self):
        with patch.object(module, 'SOURCE_DIR', self.home):
            with self.assertRaisesRegex(ValueError, 'kimi:.*k3.*No such file'):
                module.assemble(NATIVE, 'kimi', self.home)
            (self.home / 'kimi-model-catalogs.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                module.assemble(NATIVE, 'kimi', self.home)

    def test_source_mapping_and_structure_failures(self):
        changes = [lambda d: [], lambda d: {'models': []}, lambda d: {'models': [3]},
                   lambda d: {'models': [{'id':'k3'}]}, lambda d: {'models': [{'slug':' '}]},
                   lambda d: {'models': [{'slug':'other'}]},
                   lambda d: {'models': [{'slug':'k3'}, {'slug':'k3'}]},
                   lambda d: {'models': [{'slug':'k3'}, {'slug':'codex-auto-review'}]}]
        for change in changes:
            with self.subTest(change=change):
                with patch.object(module, 'SOURCE_DIR', ROOT / 'codex-agent/catalog-sources'):
                    self.changed_source('kimi', change)
                    with self.assertRaises(ValueError): module.assemble(NATIVE, 'kimi', self.home)
                patch.stopall()
                patch.object(module, 'CATALOG_DIR', self.home / 'model-catalogs').start()

    def test_card_invariants_fail_without_overwriting_output(self):
        path = self.home / 'kimi.config.toml'
        original = path.read_text()
        for old, new in [('"k3"','"kimi-k3"'), ('"max"','"high"'),
                         ('1048576','1048577'), ('1048576','true'),
                         ('786432','786433'), ('786432','true'),
                         ('786432','0'), ('/model-catalogs/kimi.json','/wrong.json')]:
            with self.subTest(new=new):
                path.write_text(original.replace(old,new))
                with self.assertRaisesRegex(ValueError, 'kimi:.*selected slug k3'):
                    module.assemble(NATIVE, 'kimi', self.home)
        path.write_text(original)

    def test_selected_budget_and_tool_semantics(self):
        for delta in ({'tool_mode':'unknown'}, {'context_window':True},
                      {'context_window':None,'max_context_window':None},
                      {'max_context_window':1}, {'effective_context_window_percent':True},
                      {'effective_context_window_percent':70}):
            with self.subTest(delta=delta):
                with patch.object(module, 'official_source', return_value={'models':[{'slug':'k3','context_window':1048576} | delta]}):
                    with self.assertRaises(ValueError): module.assemble(NATIVE, 'kimi', self.home)

    def test_guardian_drift_is_not_replaced_by_session(self):
        for models in ([], NATIVE['models']*2,
                       [NATIVE['models'][0] | {'tool_mode':'direct'}],
                       [NATIVE['models'][0] | {'use_responses_lite':False}]):
            with self.subTest(models=models):
                with self.assertRaisesRegex(ValueError, 'native guardian'):
                    module.assemble({'models':models}, 'kimi', self.home)

    def test_dry_run_native_validation_no_output_writes(self):
        output = self.home / 'not-created'
        with patch.object(module, 'native_models', return_value={}) as parser:
            self.assertEqual(module.write_targets(NATIVE,['kimi','mimo','qwen'],True,self.home,output),3)
        self.assertEqual(parser.call_count,3)
        self.assertFalse(output.exists())


@unittest.skipUnless(shutil.which('codex'), 'native Codex parser prerequisite missing')
class NativeParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = module.run_codex_debug_models()

    def test_all_assembled_profiles_parse_and_local_fallback_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp); stage_cards(home)
            with patch.object(module,'CATALOG_DIR',home/'model-catalogs'):
                for profile in module.DEFAULT_PROFILES:
                    output = module.assemble(self.native,profile,home)
                    path = home / f'{profile}.json'; path.write_text(json.dumps(output))
                    parsed = module.native_models(path)
                    self.assertIn('models',parsed)
                    if profile == 'local':
                        self.assertEqual(output['models'][:-1], module.patch(copy.deepcopy(self.native))[0]['models'])

    def test_actual_nested_native_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            home=Path(temp); stage_cards(home)
            with patch.object(module,'CATALOG_DIR',home/'model-catalogs'):
                output=module.assemble(self.native,'kimi',home)
            output['models'][0]['truncation_policy']={'mode':'native-invalid-enum','limit':100}
            path=home/'native-malformed.json'; path.write_text(json.dumps(output))
            with self.assertRaisesRegex(ValueError,'native parser failed.*'):
                module.native_models(path)


class ConversionSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve(); self.repo=self.root/'repo'
        shutil.copytree(ROOT/'scripts',self.repo/'scripts',ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(ROOT/'codex-agent',self.repo/'codex-agent')
        shutil.copytree(ROOT/'config',self.repo/'config')
        self.home=self.root/'home/.codex'; self.home.mkdir(parents=True)
        (self.root/'bin').mkdir()
        self.env=fixture_env(self.root) | {'TEST_ROOT':str(self.root),'TEST_PYTHON':sys.executable}
        self.snapshot={}
        for name, raw in [('config.toml',b'model="gpt-6-sol"\n[projects."/synthetic"]\ntrust_level="trusted"\n'),
                          ('ds-flash.config.toml',b'previous card\n'), ('model-catalogs/ds-flash.json',b'previous catalog\n'),
                          ('glm.config.toml',b'older glm card\n')]:
            path=self.home/name; path.parent.mkdir(exist_ok=True); path.write_bytes(raw); path.chmod(0o640)
            self.snapshot[path]=(raw,0o640)
        native=self.root/'native.json'; native.write_text(json.dumps(NATIVE))
        self.env['TEST_NATIVE']=str(native)
        self.script('codex', '''import json,os,sys
from pathlib import Path
if '--bundled' in sys.argv:
    print(Path(os.environ['TEST_NATIVE']).read_text())
else:
    value=sys.argv[sys.argv.index('-c')+1].split('=',1)[1]
    path=Path(json.loads(value)); doc=json.loads(path.read_text())
    with open(Path(os.environ['TEST_ROOT'])/'parses','a') as f: f.write(path.name+'\\n')
    if any(m.get('truncation_policy',{}).get('mode')=='native-invalid-enum' for m in doc['models']):
        sys.exit('synthetic parser diagnostic: invalid truncation enum')
    assert doc['models'] and len({m['slug'] for m in doc['models']})==len(doc['models'])
    print(json.dumps(doc))
''')
        self.script('launchctl', '''import os,sys
from pathlib import Path
with open(Path(os.environ['TEST_ROOT'])/'launchctl','a') as f:f.write(' '.join(sys.argv[1:])+'\\n')
if sys.argv[1]=='print': sys.exit(0 if os.environ.get('TEST_SERVICE_LOADED')=='1' else 1)
if sys.argv[1]=='kickstart': sys.exit(int(os.environ.get('TEST_KICKSTART_EXIT','0')))
sys.exit(1)
''')

    def script(self,name,body):
        path=self.root/'bin'/name; path.write_text(f'#!{sys.executable}\n'+body); path.chmod(0o755)

    def run_sync(self):
        return subprocess.run(['bash',str(self.repo/'scripts/sync-codex-agent.sh')],env=self.env,capture_output=True,text=True)

    def assert_restored(self):
        for path,(raw,mode) in self.snapshot.items():
            self.assertEqual(path.read_bytes(),raw,str(path)); self.assertEqual(path.stat().st_mode & 0o777,mode)
        self.assertEqual({p for p in self.home.rglob('*') if p.is_file()},set(self.snapshot))

    def assert_conversion_current(self):
        with patch.object(module,'CATALOG_DIR',self.home/'model-catalogs'):
            for profile in module.DEFAULT_PROFILES:
                card=self.home/f'{profile}.config.toml'
                expected=(self.repo/f'codex-agent/profiles/{profile}/config.toml').read_text()
                self.assertEqual(card.read_text(),expected.replace('@HOME@/.codex',str(self.home)))
                catalog=self.home/f'model-catalogs/{profile}.json'
                self.assertEqual(json.loads(catalog.read_text()),module.assemble(NATIVE,profile,self.home))
                for path in (card,catalog): self.assertEqual(path.stat().st_mode & 0o777,0o600)
        base=tomllib.loads((self.home/'config.toml').read_text())
        registry=tomllib.loads((self.repo/'codex-agent/model-providers.toml').read_text())
        self.assertEqual(base['model_providers'],registry['model_providers'])
        original=tomllib.loads(self.snapshot[self.home/'config.toml'][0].decode())
        self.assertEqual({k:v for k,v in base.items() if k!='model_providers'},original)
        self.assertEqual((self.home/'config.toml').stat().st_mode & 0o777,0o640)
        self.assertEqual((self.root/'home/.codex-agent/shim-routes.json').read_bytes(),
                         (self.repo/'codex-agent/shim-routes.json').read_bytes())
        self.assertFalse(list(self.home.glob('.catalog-stage.*')))

    def assert_loaded_service_actions(self):
        service=f'gui/{os.getuid()}/com.leo.codex-auto-review-shim'
        self.assertEqual((self.root/'launchctl').read_text().splitlines(),
                         [f'print {service}',f'kickstart -k {service}'])

    def inject(self,name,n,after=False,always_after=False):
        real=shutil.which(name)
        self.script(name,f'''import os,sys,subprocess
from pathlib import Path
counter=Path(os.environ['TEST_ROOT'])/{name+'-counter'!r}
count=int(counter.read_text())+1 if counter.exists() else 1; counter.write_text(str(count))
fail=(count>={n} if {always_after!r} else count=={n})
if fail and not {after!r}: sys.exit(71)
r=subprocess.run([{real!r},*sys.argv[1:]])
if fail:sys.exit(72)
sys.exit(r.returncode)
''')

    def test_success_repeat_bytes_modes_and_no_service_actions(self):
        first=self.run_sync(); self.assertEqual(first.returncode,0,first.stderr)
        all_files={p:p.read_bytes() for p in self.home.rglob('*') if p.is_file()}
        second=self.run_sync(); self.assertEqual(second.returncode,0,second.stderr)
        self.assertEqual(all_files,{p:p.read_bytes() for p in self.home.rglob('*') if p.is_file()})
        self.assertEqual(len((self.root/'parses').read_text().splitlines()),18)
        self.assertTrue(all(p.stat().st_mode & 0o777==0o600 for p in self.home.glob('*.config.toml')))
        self.assertTrue(all(line.startswith('print ') for line in (self.root/'launchctl').read_text().splitlines()))
        for profile in module.OFFICIAL:
            card=tomllib.loads((self.home/f'{profile}.config.toml').read_text())
            models=json.loads(Path(card['model_catalog_json']).read_text())['models']
            self.assertEqual(len([m for m in models if m['slug']==card['model']]),1)
            self.assertEqual(card['model_reasoning_effort'],'max')

    def test_loaded_service_restart_failure_keeps_conversion_and_reports_failure(self):
        self.env.update(TEST_SERVICE_LOADED='1',TEST_KICKSTART_EXIT='77')
        done=self.run_sync()
        self.assertNotEqual(done.returncode,0)
        self.assertIn('ERROR: failed to restart launchd service: com.leo.codex-auto-review-shim',done.stderr)
        self.assertNotIn('Synced codex-agent cards',done.stdout)
        self.assertNotIn('restarted launchd service:',done.stdout)
        self.assertNotIn('conversion failed',done.stderr)
        self.assert_loaded_service_actions()
        self.assert_conversion_current()

    def test_loaded_service_restart_success_keeps_conversion_and_prints_success(self):
        self.env['TEST_SERVICE_LOADED']='1'
        done=self.run_sync()
        self.assertEqual(done.returncode,0,done.stderr)
        self.assertIn('restarted launchd service: com.leo.codex-auto-review-shim',done.stdout)
        self.assertIn(f'Synced codex-agent cards to {self.home}',done.stdout)
        self.assertEqual(done.stderr,'')
        self.assert_loaded_service_actions()
        self.assert_conversion_current()

    def test_stage_integrity_failure_untouched(self):
        (self.repo/'codex-agent/catalog-sources/kimi-model-catalogs.json').write_text('{}')
        done=self.run_sync(); self.assertNotEqual(done.returncode,0); self.assertIn('SHA-256',done.stderr); self.assert_restored()

    def test_native_stage_failure_untouched(self):
        native=json.loads((self.root/'native.json').read_text())
        native['models'][1]['truncation_policy']={'mode':'native-invalid-enum'}
        (self.root/'native.json').write_text(json.dumps(native))
        done=self.run_sync(); self.assertNotEqual(done.returncode,0); self.assertIn('synthetic parser diagnostic',done.stderr); self.assert_restored()

    def test_unowned_registry_failure_untouched(self):
        path=self.home/'config.toml'; raw=path.read_bytes()+b'\n[model_providers.kimi]\nname="user-owned"\n'
        path.write_bytes(raw); self.snapshot[path]=(raw,0o640)
        done=self.run_sync(); self.assertNotEqual(done.returncode,0); self.assert_restored()

    def test_first_catalog_replace_failure_rollback(self):
        self.inject('mv',1,after=True); done=self.run_sync(); self.assertNotEqual(done.returncode,0); self.assert_restored()

    def test_first_card_replace_failure_rollback(self):
        self.inject('mv',2,after=True); done=self.run_sync(); self.assertNotEqual(done.returncode,0); self.assert_restored()

    def test_later_pair_copy_failure_rollback(self):
        self.inject('install',4); done=self.run_sync(); self.assertNotEqual(done.returncode,0); self.assert_restored()

    def test_final_verification_failure_rollback(self):
        self.inject('cmp',1); done=self.run_sync(); self.assertNotEqual(done.returncode,0); self.assert_restored()

    def test_registry_update_then_failure_rollback(self):
        self.script('python3', '''import os,sys,subprocess
r=subprocess.run([os.environ['TEST_PYTHON'],*sys.argv[1:]])
sys.exit(73 if 'sync-codex-providers.py' in sys.argv[1] else r.returncode)
''')
        done=self.run_sync(); self.assertNotEqual(done.returncode,0); self.assert_restored()

    def test_absent_original_registry_and_pairs_are_removed_on_failure(self):
        path=self.home/'config.toml'; path.unlink(); self.snapshot.pop(path)
        self.inject('mv',4,after=True)
        done=self.run_sync(); self.assertNotEqual(done.returncode,0); self.assert_restored()

    @unittest.skipUnless(shutil.which('codex'), 'native parser prerequisite missing')
    def test_actual_native_rejection_before_registry_and_pair_mutation(self):
        native=module.run_codex_debug_models()
        guardian=next(m for m in native['models'] if m['slug']=='codex-auto-review')
        guardian['truncation_policy']={'mode':'native-invalid-enum','limit':100}
        (self.root/'native.json').write_text(json.dumps(native))
        real=shutil.which('codex')
        self.script('codex',f'''import json,os,sys,subprocess
from pathlib import Path
if '--bundled' in sys.argv:print(Path(os.environ['TEST_NATIVE']).read_text())
else:sys.exit(subprocess.run([{real!r},*sys.argv[1:]]).returncode)
''')
        done=self.run_sync(); self.assertNotEqual(done.returncode,0)
        self.assertIn('native parser failed',done.stderr)
        self.assertIn('native-invalid-enum',done.stderr)
        print('Actual native staged rejection (synthetic fixture):\n'+done.stderr)
        self.assert_restored()

    def test_backup_failure_before_mutation(self):
        self.inject('cp',1); done=self.run_sync(); self.assertNotEqual(done.returncode,0); self.assert_restored()

    def test_restore_failure_retains_backups_and_reports_error(self):
        self.inject('cmp',1); self.inject('cp',5,always_after=True)
        done=self.run_sync(); self.assertNotEqual(done.returncode,0); self.assertIn('rollback failed; backups retained',done.stderr)
        self.assertTrue(list(self.home.glob('.catalog-stage.*/backups/*')))
        self.assertNotIn('Synced codex-agent cards',done.stdout)


if __name__ == '__main__': unittest.main()
