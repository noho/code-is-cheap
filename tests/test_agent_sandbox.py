"""Boundary tests. Kernel tests are opt-in and must run outside the parent sandbox.
AGENT_SANDBOX_KERNEL_TESTS=1 SRT_TEST_BIN=/path/to/srt python3 -m unittest discover -s tests -p test_agent_sandbox.py
"""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest
import unittest.mock

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('agent_sandbox', str(ROOT/'scripts/agent-sandbox'))
spec = importlib.util.spec_from_loader(loader.name, loader)
sandbox = importlib.util.module_from_spec(spec)
loader.exec_module(sandbox)


class SetupTests(unittest.TestCase):
    def test_invalid_entries_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/'denies.json'
            for doc in ([], {}, ['relative'], ['/no-such-agent-sandbox-path']):
                p.write_text(json.dumps(doc))
                with self.assertRaises(ValueError):
                    sandbox.load_denies(p)

    def test_symlink_canonicalization(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p/'secret').write_text('secret')
            (p/'alias').symlink_to(p/'secret')
            (p/'list').write_text(json.dumps([str(p/'alias')]))
            denies = sandbox.load_denies(p/'list')
            self.assertTrue(sandbox.is_denied(p/'secret', denies))
            self.assertTrue(sandbox.is_denied(p/'alias', denies))

    def test_preexisting_hardlink_is_explicitly_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p/'secret').write_text('secret')
            os.link(p/'secret',p/'other-name')
            (p/'list').write_text(json.dumps([str(p/'secret')]))
            with self.assertRaisesRegex(ValueError,'hardlinked'):
                sandbox.load_denies(p/'list')

    def test_raw_native_options_cannot_change_policy(self):
        cwd = Path.cwd()
        with unittest.mock.patch.object(shutil, 'which', return_value='/bin/codex-agent-run'):
            for option in ('--', '--persist', '--resume', '--sandbox', '--config'):
                with self.assertRaises(ValueError):
                    sandbox.parse_runner(['codex-agent-run', '--provider', 'mimo', option], cwd)


@unittest.skipUnless(platform.system() == 'Darwin' and os.getenv('AGENT_SANDBOX_KERNEL_TESTS') == '1',
                     'requires macOS and explicit outer-sandbox test opt-in')
class KernelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='agent-sandbox-tests.')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        p = self.root
        for name in ('home/.codex', 'home/.config/agent-tools', 'bin', 'work/denied', 'work/.git', 'sinks'):
            (p/name).mkdir(parents=True)
        (p/'work/allowed').write_text('ALLOW_INPUT')
        (p/'work/denied/report').write_text('FORBIDDEN_BUSINESS_MARKER')
        (p/'work/history.jsonl').write_text('FORBIDDEN_HISTORY_MARKER')
        (p/'work/alias').symlink_to(p/'work/denied/report')
        (p/'work/dir-alias').symlink_to(p/'work/denied', target_is_directory=True)
        (p/'denies.json').write_text(json.dumps([str(p/'work/denied'), str(p/'work/history.jsonl')]))
        config = 'sandbox_mode = "workspace-write"\nmodel = "test"\nmodel_provider = "mock"\n[model_providers.mock]\nname = "mock"\nbase_url = "https://example.com/v1"\nwire_api = "responses"\nrequires_openai_auth = false\n'
        (p/'home/.codex/config.toml').write_text(config)
        (p/'home/.codex/mimo.config.toml').write_text('')
        endpoint = json.loads((ROOT/'config/endpoints.example.json').read_text())
        endpoint['default']['mimo']['codex']['api_key'] = 'synthetic-test-key'
        ep = p/'home/.config/agent-tools/endpoints.json'
        ep.write_text(json.dumps(endpoint)); ep.chmod(0o600)
        runner = p/'bin/codex-agent-run'
        runner.write_text('#!/usr/bin/env python3\n'+r'''
import json, os, subprocess, sys
from pathlib import Path
p = Path(os.environ['TEST_ROOT'])
r = {}
def read(name, path):
    try: r[name] = Path(path).read_text()
    except OSError as e: r[name] = type(e).__name__
def write(name, path):
    try: Path(path).write_text('write'); r[name] = 'allowed'
    except OSError as e: r[name] = type(e).__name__
read('allowed', p/'work/allowed')
for name, path in [('direct',p/'work/denied/report'), ('symlink',p/'work/alias'),
 ('dir_alias',p/'work/dir-alias/report'), ('dotdot',p/'work/../work/denied/report'),
 ('history',p/'work/history.jsonl'), ('data_alias','/System/Volumes/Data'+str(p/'work/denied/report')), ('tmp_alias',str(p/'work/denied/report').replace('/private/tmp/','/tmp/'))]:
    read(name,path)
s = subprocess.run(['rg','--no-ignore','-n','FORBIDDEN_',str(p/'work')], capture_output=True,text=True)
r['recursive_stdout'] = s.stdout
r['recursive_code'] = s.returncode
nested = subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default)','/bin/cat',str(p/'work/denied/report')], capture_output=True,text=True)
r['nested_stdout'] = nested.stdout
r['nested_code'] = nested.returncode
try:
    os.link(p/'work/denied/report',p/'work/hardlink')
    read('hardlink',p/'work/hardlink')
except OSError as e: r['hardlink'] = type(e).__name__
write('cwd_write',p/'work/new-output')
write('protected_write',p/'work/.git/evil')
write('outside_write',p/'outside')
write('sink_neighbor',p/'sinks/unrequested')
write('sink_write',p/'sinks/result')
print(json.dumps(r))
''')
        runner.chmod(0o755)
        srt = os.getenv('SRT_TEST_BIN') or shutil.which('srt')
        if not srt: self.fail('SRT_TEST_BIN or srt required for kernel tests')
        (p/'bin/srt').symlink_to(srt)
        self.env = {**os.environ, 'HOME':str(p/'home'), 'PATH':str(p/'bin')+':'+os.environ['PATH'],
                    'TEST_ROOT':str(p), 'AGENT_TOOLS_FILE':str(ROOT/'scripts/agent-tools.zsh')}

    def launch(self):
        p = self.root
        return subprocess.run([str(ROOT/'scripts/agent-sandbox'),'--cwd',str(p/'work'),
            '--deny-list',str(p/'denies.json'),'--','codex-agent-run','--provider','mimo',
            '--prompt','test','--output',str(p/'sinks/result')],env=self.env,capture_output=True,text=True,timeout=45)

    def test_kernel_boundary_and_write_preservation(self):
        result = self.launch()
        self.assertEqual(result.returncode,0,result.stderr)
        r = json.loads(result.stdout)
        self.assertEqual(r['allowed'],'ALLOW_INPUT')
        for name in ('direct','symlink','dir_alias','dotdot','history','data_alias','tmp_alias','hardlink'):
            self.assertEqual(r[name],'PermissionError',r)
        self.assertNotIn('FORBIDDEN_',r['recursive_stdout'])
        self.assertNotEqual(r['nested_code'],0)
        self.assertNotIn('FORBIDDEN_',r['nested_stdout'])
        self.assertEqual(r['cwd_write'],'allowed')
        self.assertEqual(r['sink_write'],'allowed')
        for name in ('protected_write','outside_write','sink_neighbor'):
            self.assertEqual(r[name],'PermissionError',r)

    def test_read_only_does_not_gain_cwd_writes(self):
        config = self.root/'home/.codex/config.toml'
        config.write_text(config.read_text().replace('workspace-write','read-only'))
        result = self.launch()
        self.assertEqual(result.returncode,0,result.stderr)
        r = json.loads(result.stdout)
        self.assertEqual(r['cwd_write'],'PermissionError',r)
        self.assertEqual(r['sink_write'],'allowed')

    def test_unsupported_policy_fails_before_runner(self):
        config = self.root/'home/.codex/config.toml'
        config.write_text(config.read_text()+'\n[permissions.test]\n')
        result = self.launch()
        self.assertNotEqual(result.returncode,0)
        self.assertIn('cannot preserve custom', result.stderr)
        self.assertFalse((self.root/'sinks/result').exists())



class FullAccessTests(unittest.TestCase):
    def test_opt_in_flags_and_default_launches(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            (p/'bin').mkdir(); (p/'.codex').mkdir()
            (p/'.codex/gpt-6-sol.config.toml').write_text('')
            doc = json.loads((ROOT/'config/endpoints.example.json').read_text())
            doc['default']['mimo']['claude']['api_key'] = 'synthetic-key'
            ep = p/'.config/agent-tools/endpoints.json'; ep.parent.mkdir(parents=True)
            ep.write_text(json.dumps(doc)); ep.chmod(0o600)
            for name in ('codex','claude'):
                native = p/'bin'/name
                native.write_text('#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n'); native.chmod(0o755)
            (p/'bin/agent-endpoint.py').symlink_to(ROOT/'scripts/agent-endpoint.py')
            env = {**os.environ, 'HOME':str(p),'PATH':str(p/'bin')+':'+os.environ['PATH'],
                   'AGENT_TOOLS_FILE':str(ROOT/'scripts/agent-tools.zsh')}
            for runtime,provider in (('codex','gpt-6-sol'),('claude','mimo')):
                for full in (False,True):
                    cmd = [str(ROOT/f'scripts/{runtime}-agent-run'),'--provider',provider,'--cwd',str(p),'--prompt','literal --full-access']
                    if full: cmd.append('--full-access')
                    done = subprocess.run(cmd,env=env,capture_output=True,text=True)
                    self.assertEqual(done.returncode,0,done.stderr)
                    args = json.loads(done.stdout)
                    if runtime == 'claude': self.assertEqual(args[-1],'literal --full-access')
                    if runtime == 'codex':
                        self.assertEqual('--dangerously-bypass-approvals-and-sandbox' in args,full)
                    else:
                        settings = json.loads(args[args.index('--settings')+1])
                        self.assertEqual('--permission-mode' in args,full)
                        if full:
                            self.assertEqual(args[args.index('--permission-mode')+1],'bypassPermissions')
                            self.assertEqual(settings['sandbox'],{'enabled':False})
                        else: self.assertNotIn('sandbox',settings)
                conflict = [str(ROOT/f'scripts/{runtime}-agent-run'),'--provider',provider,'--cwd',str(p),'--prompt','test','--full-access']
                conflict += ['--sandbox','read-only'] if runtime == 'codex' else ['--permission-mode','auto']
                done = subprocess.run(conflict,env=env,capture_output=True,text=True)
                self.assertNotEqual(done.returncode,0)
                self.assertIn('conflicts',done.stderr)

if __name__ == '__main__': unittest.main()
