"""Black-box backup tests: fake HOMEs, packages and CLIs; no live operations."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ('agent-run-result.py', 'agent-sandbox', 'agent-sandbox-launch.mjs',
         'install-agent-sandbox.sh')
NODE = shutil.which('node')
RSYNC = shutil.which('rsync')


@unittest.skipUnless(NODE and RSYNC and shutil.which('zsh'), 'Node, rsync and zsh required')
class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='agent-backup-tests.', dir='/private/tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.log = self.root / 'calls.jsonl'
        self.script = self.root / 'usb/agents-backup-restore.sh'
        self.script.parent.mkdir()
        shutil.copy2(ROOT / 'scripts/backup/agents-backup-restore.sh', self.script)
        self.function = self.root / 'backupsysfiles.zsh'
        shutil.copy2(ROOT / 'scripts/backup/backupsysfiles.zsh', self.function)
        self.bin.joinpath('python3').symlink_to(sys.executable)
        self.bin.joinpath('rsync').symlink_to(RSYNC)
        self.stub('node', f'''#!/bin/bash
if [[ "${{TEST_OLD_NODE:-}}" == 1 && "$1" == -e ]]; then exit 1; fi
exec {NODE} "$@"
''')
        for name in ('brew', 'curl', 'uv', 'npm', 'claude', 'codex', 'tmux',
                     'tmux-cli', 'jq', 'crontab'):
            self.stub(name, '#!' + sys.executable + '\n' + r'''
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
with open(os.environ['TEST_LOG'], 'a') as stream:
    stream.write(json.dumps([name, *sys.argv[1:]]) + '\n')
if name in ('curl', 'uv'):
    sys.exit(98)  # Network/real package installation must never be reached.
if name == 'npm':
    if os.environ.get('NPM_FAIL') == '1':
        print('npm ERR! fixture installation failure', file=sys.stderr)
        sys.exit(42)
    args = sys.argv[1:]
    prefix = pathlib.Path(args[args.index('--prefix') + 1])
    root = prefix / 'node_modules/@anthropic-ai/sandbox-runtime'
    (root / 'dist/utils').mkdir(parents=True)
    (root / 'dist/sandbox').mkdir()
    version = '0.0.80' if os.environ.get('NPM_LAYOUT') == 'version' else '0.0.79'
    doc = dict(name='@anthropic-ai/sandbox-runtime', version=version,
               bin=dict(srt='dist/cli.js'))
    if os.environ.get('NPM_LAYOUT') == 'bin': doc['bin']['srt'] = 'dist/other.js'
    (root / 'package.json').write_text(json.dumps(doc))
    (root / 'dist/cli.js').write_text('throw Error("fixture SRT must not execute");')
    (root / 'dist/sandbox/macos-sandbox-utils.js').write_text('// fixture')
    if os.environ.get('NPM_LAYOUT') != 'module':
        (root / 'dist/utils/shell-quote.js').write_text('// fixture')
    (prefix / 'node_modules/.bin').mkdir()
    (prefix / 'node_modules/.bin/srt').symlink_to(root / 'dist/cli.js')
elif name == 'brew' and sys.argv[1:] == ['--prefix']:
    print(os.environ['TEST_BIN'])
else:
    print('fixture-cli-1.0')
''')
        self.source = self.make_home('source', helpers=True)

    def stub(self, name, text):
        path = self.bin / name
        path.write_text(text)
        path.chmod(0o755)

    def write(self, home, relative, text, mode=0o600):
        path = home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        path.chmod(mode)
        return path

    def make_home(self, name, helpers=False):
        home = self.root / name
        home.mkdir()
        for relative in ('.claude', '.codex', '.codex-agent'):
            (home / relative).mkdir()
        for relative in ('.zshrc', '.claude.json', '.config/zsh/agent-tools.zsh',
                         '.config/zsh/agent-tools.local.zsh', '.tmux.conf'):
            self.write(home, relative, '# fixture ' + str(home) + '\n')
        for name in ('claude-agent-run', 'codex-agent-run', 'agent-run-result.py'):
            self.write(home, '.local/bin/' + name, '#!/bin/sh\nexit 98\n', 0o640)
        if helpers:
            for name in TOOLS[1:]:
                shutil.copy2(ROOT / 'scripts' / name, home / '.local/bin' / name)
                (home / '.local/bin' / name).chmod(0o640)
        for relative in ('.codex/config.toml', '.codex/other.config.toml',
                         '.codex-agent/gpt/config.toml',
                         '.codex-agent/app-data/app/home/config.toml'):
            self.write(home, relative,
                       f'model_catalog_json = "{home}/.codex-agent/.catalog/vendor/full.json"\n')
        self.write(home, '.claude/settings.json', json.dumps({'path': str(home) + '/fixture'}))
        for relative in ('.codex-agent/.catalog/vendor/full.json',
                         '.codex-agent/.catalog/vendor/.hidden', '.codex/.catalog/nested/model.json'):
            self.write(home, relative, 'catalog fixture\n')
        for relative in ('.codex/sessions/run/session.jsonl', '.claude/projects/session.jsonl',
                         '.codex-agent/gpt/sessions/session.jsonl'):
            self.write(home, relative, 'synthetic session\n')
        self.write(home, '.codex/auth.json', '{"api_key":"FAKE_TEST_KEY"}\n')
        self.write(home, '.config/agent-tools/endpoints.json', '{"endpoint":"https://fixture.invalid"}\n')
        self.write(home, '.local/bin/agent-endpoints.defaults.json', '{}\n')
        self.write(home, '.codex/node_modules/local-sdk/module.js', '// excluded fixture')
        (home / '.codex-agent/catalog-link').symlink_to(home / '.codex-agent/.catalog')
        return home

    def package(self, home, version='0.0.79'):
        root = home / '.local/share/agent-sandbox/node_modules/@anthropic-ai/sandbox-runtime'
        self.write(home, str(root.relative_to(home) / 'package.json'), json.dumps(dict(
            name='@anthropic-ai/sandbox-runtime', version=version, bin=dict(srt='dist/cli.js'))))
        for name in ('dist/cli.js', 'dist/utils/shell-quote.js', 'dist/sandbox/macos-sandbox-utils.js'):
            self.write(home, str(root.relative_to(home) / name), 'throw Error("must not execute");')
        (home / '.local/bin').mkdir(parents=True, exist_ok=True)
        (home / '.local/bin/srt').symlink_to(root / 'dist/cli.js')
        return root

    def env(self, home, **extra):
        # Deliberately do not inherit personal credentials/configuration variables.
        return dict(HOME=str(home), PATH=str(self.bin) + ':/usr/bin:/bin:/usr/sbin:/sbin',
                    TMPDIR=str(self.root), TEST_LOG=str(self.log), TEST_BIN=str(self.bin),
                    LC_ALL='C', **extra)

    def run_script(self, home, *args, expected=0, **extra):
        result = subprocess.run(['/bin/bash', str(self.script), *args], env=self.env(home, **extra),
                                cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def backup(self):
        self.run_script(self.source, 'backup')

    def manifest(self):
        return dict(line.split('=', 1) for line in
                    (self.script.parent / 'payload/manifest.txt').read_text().splitlines())

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def assert_no_install(self):
        self.assertFalse([call for call in self.calls() if call[0] in ('npm', 'curl', 'uv') or
                          call[:2] == ['brew', 'install']], self.calls())

    def target(self, name='target'):
        home = self.root / ('target-' + name)
        home.mkdir()
        return home

    def test_four_tools_restore_modes_rollback_catalog_home_and_private_data(self):
        self.package(self.source)
        self.backup()
        with tarfile.open(self.script.parent / 'payload/agent-home.tar') as archive:
            names = archive.getnames()
        self.assertFalse(any('node_modules' in name or name == '.local/bin/srt' for name in names))
        self.assertEqual(self.manifest()['sandbox_runtime_version'], '0.0.79')
        target = self.target()
        for tool in TOOLS:
            self.write(target, '.local/bin/' + tool, 'old ' + tool, 0o711)
        self.write(target, '.codex/old.txt', 'previous directory')
        result = self.run_script(target, 'restore', '--yes')
        rollbacks = list((target / '.agent-restore-backups').iterdir())
        self.assertEqual(len(rollbacks), 1)
        for tool in TOOLS:
            self.assertEqual((target / '.local/bin' / tool).stat().st_mode & 0o777, 0o755)
            old = rollbacks[0] / '.local/bin' / tool
            self.assertEqual(old.read_text(), 'old ' + tool)
            self.assertEqual(old.stat().st_mode & 0o777, 0o711)
        self.assertEqual((rollbacks[0] / '.codex/old.txt').read_text(), 'previous directory')
        for relative in ('.codex-agent/.catalog/vendor/full.json',
                         '.codex-agent/.catalog/vendor/.hidden', '.codex/.catalog/nested/model.json',
                         '.codex/sessions/run/session.jsonl', '.claude/projects/session.jsonl',
                         '.codex-agent/gpt/sessions/session.jsonl', '.codex/auth.json',
                         '.config/agent-tools/endpoints.json'):
            self.assertEqual((target / relative).read_bytes(), (self.source / relative).read_bytes())
        for relative in ('.codex/config.toml', '.codex/other.config.toml',
                         '.codex-agent/gpt/config.toml', '.codex-agent/app-data/app/home/config.toml',
                         '.zshrc', '.claude/settings.json'):
            self.assertNotIn(str(self.source), (target / relative).read_text())
            self.assertIn(str(target), (target / relative).read_text())
        self.assertEqual(os.readlink(target / '.codex-agent/catalog-link'), str(target / '.codex-agent/.catalog'))
        for relative in ('.zshrc', '.claude.json', '.config/zsh/agent-tools.zsh',
                         '.config/agent-tools/endpoints.json'):
            self.assertEqual((target / relative).stat().st_mode & 0o777, 0o600)
        self.assertIn('Install optional SRT:', result.stderr)
        self.assertFalse((target / '.local/bin/srt').exists())
        self.assert_no_install()

    def test_missing_collector_rejects_backup_and_archive_before_target_changes(self):
        collector = self.source / '.local/bin/agent-run-result.py'
        original = collector.read_bytes()
        collector.unlink()
        self.run_script(self.source, 'backup', expected=1)
        original_path = self.root / 'collector-original'
        original_path.write_bytes(original)
        collector.symlink_to(original_path)
        self.run_script(self.source, 'backup', expected=1)
        collector.unlink()
        collector.write_bytes(original)
        self.backup()
        archive = self.script.parent / 'payload/agent-home.tar'
        edited = self.root / 'edited.tar'
        with tarfile.open(archive) as src, tarfile.open(edited, 'w') as dst:
            for member in src:
                if member.name != '.local/bin/agent-run-result.py':
                    dst.addfile(member, src.extractfile(member) if member.isfile() else None)
        edited.replace(archive)
        (archive.parent / 'SHA256SUMS').write_text(hashlib.sha256(archive.read_bytes()).hexdigest() +
                                                 '  agent-home.tar\n')
        target = self.target()
        self.write(target, '.zshrc', '# target sentinel')
        self.write(target, '.local/bin/agent-run-result.py', '# target collector sentinel')
        before = sorted(path.relative_to(target) for path in target.rglob('*'))
        result = self.run_script(target, 'restore', '--yes', expected=1)
        self.assertIn('archive predates the required runner collector', result.stderr)
        self.assertIn('cannot restore a complete current runner', result.stderr)
        self.assertIn('On the source, install current agent tools with ./scripts/sync-agent-tools.sh', result.stderr)
        self.assertIn('if the collector is missing', result.stderr)
        self.assertIn('bash agents-backup-restore.sh backup', result.stderr)
        self.assertIn('bash agents-backup-restore.sh verify', result.stderr)
        self.assertIn('Verify the regenerated backup before migration', result.stderr)
        self.assertIn('If the source is unavailable, verify remains usable', result.stderr)
        self.assertIn('retain this archive for separate manual data recovery', result.stderr)
        self.assertIn('does not automatically restore a working runner', result.stderr)
        self.assertIn('Archive structure: OK', self.run_script(target, 'verify').stdout)
        self.assertEqual(sorted(path.relative_to(target) for path in target.rglob('*')), before)
        self.assertEqual((target / '.zshrc').read_text(), '# target sentinel')
        self.assertEqual((target / '.local/bin/agent-run-result.py').read_text(), '# target collector sentinel')
        self.assertFalse((target / '.agent-restore-backups').exists())

    def test_no_source_srt_and_optional_helpers_does_not_install_even_with_flag(self):
        for tool in TOOLS[1:]:
            (self.source / '.local/bin' / tool).unlink()
        self.backup()
        self.assertEqual(self.manifest()['sandbox_runtime_installed'], 'false')
        target = self.target()
        result = self.run_script(target, 'restore', '--yes', '--install-deps')
        self.assertNotIn('Install optional SRT:', result.stderr)
        self.assertTrue((target / '.local/bin/agent-run-result.py').is_file())
        self.assertFalse(any((target / '.local/bin' / name).exists() for name in TOOLS[1:]))
        self.assert_no_install()

    def test_archive_nonregular_collector_rejected_before_rollback(self):
        self.backup()
        archive = self.script.parent / 'payload/agent-home.tar'
        original = self.root / 'original.tar'
        shutil.copy2(archive, original)
        for kind in (tarfile.SYMTYPE, tarfile.DIRTYPE):
            with self.subTest(kind=kind):
                with tarfile.open(original) as src, tarfile.open(archive, 'w') as dst:
                    for member in src:
                        if member.name == '.local/bin/agent-run-result.py':
                            member.type = kind
                            member.size = 0
                            member.linkname = str(self.source / '.local/bin/agent-run-result.py') if kind == tarfile.SYMTYPE else ''
                        dst.addfile(member, src.extractfile(member) if member.isfile() else None)
                (archive.parent / 'SHA256SUMS').write_text(hashlib.sha256(archive.read_bytes()).hexdigest() +
                                                         '  agent-home.tar\n')
                target = self.target(kind.decode())
                self.run_script(target, 'restore', '--yes', expected=1)
                self.assertFalse((target / '.agent-restore-backups').exists())

    def test_install_uses_archived_installer_fixed_pin_and_target_directories(self):
        self.package(self.source, '0.0.80')
        self.backup()
        self.assertEqual(self.manifest()['sandbox_runtime_version'], '0.0.80')
        target = self.target()
        result = self.run_script(target, 'restore', '--yes', '--install-deps',
                                 AGENT_SANDBOX_INSTALL_DIR=str(self.root / 'wrong-sdk'),
                                 AGENT_RUN_BIN_DIR=str(self.root / 'wrong-bin'))
        self.assertIn('validated Node package 0.0.79', result.stdout)
        self.assertEqual([call for call in self.calls() if call[0] == 'npm'], [[
            'npm', 'install', '--prefix', str(target / '.local/share/agent-sandbox'),
            '--omit=dev', '--ignore-scripts', '@anthropic-ai/sandbox-runtime@0.0.79']])
        self.assertTrue((target / '.local/bin/srt').resolve().is_file())
        self.assertNotIn(str(self.source), os.readlink(target / '.local/bin/srt'))
        self.assertFalse((self.root / 'wrong-sdk').exists())

    def test_target_layout_version_modules_node_and_npm_are_checked_offline(self):
        self.package(self.source)
        self.backup()
        for case in ('valid', 'version', 'bin', 'module', 'standalone', 'node', 'npm'):
            with self.subTest(case=case):
                target = self.target(case)
                pkg = self.package(target)
                if case in ('version', 'bin'):
                    doc = json.loads((pkg / 'package.json').read_text())
                    if case == 'version': doc['version'] = '0.0.80'
                    else: doc['bin']['srt'] = 'dist/other.js'
                    (pkg / 'package.json').write_text(json.dumps(doc))
                if case == 'module': (pkg / 'dist/utils/shell-quote.js').unlink()
                if case == 'standalone':
                    (target / '.local/bin/srt').unlink()
                    self.write(target, '.local/bin/srt', '#!/bin/sh\nexit 98\n', 0o755)
                if case == 'npm': (self.bin / 'npm').unlink()
                result = self.run_script(target, 'restore', '--yes', TEST_OLD_NODE='1' if case == 'node' else '0')
                if case == 'valid':
                    self.assertIn('validated Node package 0.0.79', result.stdout)
                    self.assertNotIn('Install optional SRT:', result.stderr)
                else:
                    self.assertIn('Install optional SRT:', result.stderr)
        self.assert_no_install()

    def test_install_rejects_invalid_post_install_package_and_old_node(self):
        self.package(self.source)
        self.backup()
        for case in ('version', 'bin', 'module', 'node', 'npm'):
            with self.subTest(case=case):
                target = self.target(case)
                self.write(target, '.zshrc', '# previous target files')
                if case == 'npm': (self.bin / 'npm').unlink()
                result = self.run_script(target, 'restore', '--yes', '--install-deps', expected=1,
                                         NPM_LAYOUT=case, TEST_OLD_NODE='1' if case == 'node' else '0')
                self.assertIn('validation' if case in ('version', 'bin', 'module') else 'Install Node >=22.12', result.stderr)
                self.assertIn('Environment files were restored, but optional SRT dependencies are not ready', result.stderr)
                rollbacks = list((target / '.agent-restore-backups').iterdir())
                self.assertEqual(len(rollbacks), 1)
                self.assertIn('Previous files are in: ' + str(rollbacks[0]), result.stderr)
                self.assertEqual((rollbacks[0] / '.zshrc').read_text(), '# previous target files')
                self.assertIn(str(target), (target / '.zshrc').read_text())
                self.assertNotIn('Restore complete', result.stdout)
                self.assertNotIn('validated Node package', result.stdout)
        self.assertEqual(len([call for call in self.calls() if call[0] == 'npm']), 3)

    def test_npm_installer_failure_reports_restored_files_and_retained_previous_files(self):
        self.package(self.source)
        self.backup()
        target = self.target()
        self.write(target, '.zshrc', '# previous target files')
        self.write(target, '.local/bin/install-agent-sandbox.sh', '# previous installer')
        result = self.run_script(target, 'restore', '--yes', '--install-deps', expected=1, NPM_FAIL='1')
        self.assertIn('npm ERR! fixture installation failure', result.stderr)
        self.assertIn('Optional SRT installer failed: ' + str(target / '.local/bin/install-agent-sandbox.sh'), result.stderr)
        self.assertIn('Environment files were restored, but optional SRT dependencies are not ready', result.stderr)
        rollbacks = list((target / '.agent-restore-backups').iterdir())
        self.assertEqual(len(rollbacks), 1)
        self.assertIn('Previous files are in: ' + str(rollbacks[0]), result.stderr)
        self.assertEqual((rollbacks[0] / '.zshrc').read_text(), '# previous target files')
        self.assertEqual((rollbacks[0] / '.local/bin/install-agent-sandbox.sh').read_text(), '# previous installer')
        self.assertIn(str(target), (target / '.zshrc').read_text())
        self.assertEqual((target / '.local/bin/install-agent-sandbox.sh').read_bytes(),
                         (self.source / '.local/bin/install-agent-sandbox.sh').read_bytes())
        self.assertNotIn('Restore complete', result.stdout)
        self.assertNotIn('validated Node package', result.stdout)
        self.assertFalse((target / '.local/bin/srt').exists())
        self.assertEqual(len([call for call in self.calls() if call[0] == 'npm']), 1)

    def test_source_srt_missing_installer_reports_concrete_missing_helper(self):
        self.package(self.source)
        (self.source / '.local/bin/install-agent-sandbox.sh').unlink()
        self.backup()
        target = self.target()
        marker = self.root / 'unarchived-installer-ran'
        self.write(target, '.local/bin/install-agent-sandbox.sh', '#!/bin/bash\ntouch ' + str(marker) + '\n', 0o755)
        result = self.run_script(target, 'restore', '--yes', '--install-deps', expected=1)
        self.assertIn('Archived install-agent-sandbox.sh is missing', result.stderr)
        self.assertFalse(marker.exists())
        self.assert_no_install()

    def run_function(self, expected=0):
        # Stub legacy external copies so the function never reads a live USB or /etc file.
        code = '''source "$1"
function cp() {
  if [[ "$1" == /etc/auto_resources || "$1" == /Volumes/LEO/Agents/agents-backup-restore.sh ]]; then
    print -r -- 'external copy fixture' > "$2"
  else
    /bin/cp "$@"
  fi
}
backupsysfiles
'''
        result = subprocess.run(['/bin/zsh', '-f', '-c', code, 'test', str(self.function)],
                                env=self.env(self.source), cwd=self.root,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return self.source / 'Documents/_8ssh'

    def test_backupsysfiles_helpers_optional_cleanup_metadata_and_catalog(self):
        self.package(self.source)
        for tool in TOOLS: (self.source / '.local/bin' / tool).chmod(0o755)
        self.write(self.source, 'Documents/_8ssh/.codex/node_modules/stale-sdk/module.js', '// stale SDK')
        self.write(self.source, 'Documents/_8ssh/.codex/sessions/stale/session.jsonl', 'retained session')
        backup = self.run_function()
        for tool in TOOLS:
            self.assertEqual((backup / tool).read_bytes(), (self.source / '.local/bin' / tool).read_bytes())
            self.assertEqual((backup / tool).stat().st_mode & 0o777, 0o755)
        self.assertIn('sandbox_runtime_version=0.0.79', (backup / 'agent-sandbox-runtime.txt').read_text())
        self.assertFalse((backup / 'srt').exists())
        self.assertFalse((backup / '.codex/node_modules').exists())
        self.assertEqual((backup / '.codex/sessions/stale/session.jsonl').read_text(), 'retained session')
        self.assertTrue((backup / 'codex-agent/.catalog/vendor/.hidden').is_file())
        self.assertTrue((backup / '.codex/.catalog/nested/model.json').is_file())
        self.assertTrue((backup / '.codex/sessions/run/session.jsonl').is_file())
        self.assertFalse((backup / 'claude/projects').exists())
        self.assertFalse((backup / 'codex-agent/gpt/sessions').exists())
        for tool in TOOLS[1:]: (self.source / '.local/bin' / tool).unlink()
        (self.source / '.local/bin/srt').unlink()
        self.run_function()
        self.assertTrue((backup / 'agent-run-result.py').is_file())
        self.assertFalse(any((backup / tool).exists() for tool in TOOLS[1:]))
        self.assertIn('sandbox_runtime_installed=false', (backup / 'agent-sandbox-runtime.txt').read_text())
        self.assert_no_install()

    def test_backupsysfiles_missing_collector_fails(self):
        (self.source / '.local/bin/agent-run-result.py').unlink()
        self.run_function(expected=1)


if __name__ == '__main__':
    unittest.main()
