"""Exercise URL switching and installation with isolated homes and local mocks."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('endpoint_shim', str(ROOT / 'codex-agent/bin/codex-auto-review-shim'))
spec = importlib.util.spec_from_loader(loader.name, loader)
shim = importlib.util.module_from_spec(spec)
loader.exec_module(shim)


class EndpointTests(unittest.TestCase):
    def test_switch_gateway_path_without_sync_or_restart(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {'HOME': temp}):
            local = Path(temp) / '.config/agent-tools/endpoints.json'
            local.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / 'config/endpoints.example.json', local)
            with patch.dict(os.environ, {'SHIM_ROUTES': str(ROOT / 'codex-agent/shim-routes.json')}):
                routes = shim.load_routes()
            deepseek = routes[0]
            self.assertEqual(shim.route_url(deepseek, '/v1/responses'), 'https://api.deepseek.com/v1/responses')
            doc = json.loads(local.read_text())
            doc['ds-flash'] = {'codex': 'https://gateway.example/custom/v1/', 'claude': 'https://gateway.example/anthropic'}
            local.write_text(json.dumps(doc))
            self.assertEqual(shim.route_url(deepseek, '/v1/responses?stream=true'), 'https://gateway.example/custom/v1/responses?stream=true')
            bin_dir = Path(temp) / 'custom tools/bin'
            bin_dir.mkdir(parents=True)
            shutil.copyfile(ROOT / 'scripts/agent-endpoint.py', bin_dir / 'agent-endpoint.py')
            (bin_dir / 'agent-endpoint.py').chmod(0o755)
            shutil.copyfile(ROOT / 'config/endpoints.example.json', bin_dir / 'agent-endpoints.defaults.json')
            result = subprocess.run(['zsh', '-c', 'source "$1"; _claude_agent_base_url ds-flash', '_', str(ROOT / 'scripts/agent-tools.zsh')], env=os.environ | {'PATH': f'{bin_dir}:{os.environ["PATH"]}'}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), 'https://gateway.example/anthropic')
            with self.assertRaises(ValueError):
                shim.route_url(deepseek, '/wrong/responses')
            local.write_text('{broken')
            with self.assertRaises(ValueError):
                shim.route_url(deepseek, '/v1/responses')

    def test_missing_files_and_partial_overrides_use_defaults_without_writes(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {'HOME': temp}):
            local = Path(temp) / '.config/agent-tools/endpoints.json'
            with patch.dict(os.environ, {'SHIM_ROUTES': str(ROOT / 'codex-agent/shim-routes.json')}):
                routes = shim.load_routes()
            self.assertFalse(local.exists())
            self.assertEqual(shim.route_url(routes[0], '/v1/responses'), 'https://api.deepseek.com/v1/responses')
            local.parent.mkdir(parents=True)
            local.write_text('{"ds-flash":{"codex":"https://custom.example/v1","claude":""}}')
            before = local.read_bytes()
            module = shim.endpoint_module()
            self.assertEqual(module.endpoint('ds-flash', 'claude'), 'https://api.deepseek.com/anthropic')
            self.assertEqual(module.endpoint('kimi', 'codex'), 'https://api.kimi.com/coding/v1')
            self.assertEqual(shim.route_url(routes[0], '/v1/responses'), 'https://custom.example/v1/responses')
            self.assertEqual(local.read_bytes(), before)

    def test_manual_skill_sync_reuses_installed_validator_environment(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            interpreter = home / '.local/share/code-is-cheap-installer/venv/bin/python'
            interpreter.parent.mkdir(parents=True)
            marker = home / 'validator-used'
            # The chosen private interpreter records use, then executes Python.
            import shlex
            interpreter.write_text('#!/bin/sh\necho used >> ' + shlex.quote(str(marker)) + '\nexec ' + shlex.quote(sys.executable) + ' "$@"\n')
            interpreter.chmod(0o755)
            env = os.environ | {'HOME': str(home)}
            for name in ['SKILL_VALIDATOR_PYTHON', 'PYTHON', 'SKILL_VALIDATOR']:
                env.pop(name, None)
            result = subprocess.run(['bash', str(ROOT / 'scripts/validate-skills.sh')], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(marker.exists())

    def test_claude_never_starts_when_helper_or_local_config_is_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            bins = home / 'bin'
            bins.mkdir()
            marker = home / 'claude-called'
            import shlex
            stub = bins / 'claude'
            stub.write_text('#!/bin/sh\ntouch ' + shlex.quote(str(marker)) + '\n')
            stub.chmod(0o755)
            (bins / 'python3').symlink_to(sys.executable)
            # These launch tests isolate PATH; do not depend on Apple's jq.
            jq = bins / 'jq'
            jq.write_text("#!/bin/sh\nprintf '{}\\n'\n")
            jq.chmod(0o755)
            keys = home / '.config/zsh/agent-tools.local.zsh'
            keys.parent.mkdir(parents=True)
            keys.write_text('export DEEPSEEK_API_KEY="fake-key"\n')
            env = os.environ | {'HOME': str(home), 'PATH': f'{bins}:/usr/bin:/bin'}
            command = ['zsh', '-c', 'source "$1"; ds-flash_claude -p ping', '_', str(ROOT / 'scripts/agent-tools.zsh')]
            missing = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertFalse(marker.exists())
            shutil.copyfile(ROOT / 'scripts/agent-endpoint.py', bins / 'agent-endpoint.py')
            (bins / 'agent-endpoint.py').chmod(0o755)
            shutil.copyfile(ROOT / 'config/endpoints.example.json', bins / 'agent-endpoints.defaults.json')
            local = home / '.config/agent-tools/endpoints.json'
            local.parent.mkdir(parents=True)
            local.write_text('{broken')
            broken = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertNotEqual(broken.returncode, 0)
            self.assertFalse(marker.exists())
            local.unlink()
            healthy = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertEqual(healthy.returncode, 0, healthy.stderr)
            self.assertTrue(marker.exists())
            marker.unlink()
            defaults = bins / 'agent-endpoints.defaults.json'
            doc = json.loads(defaults.read_text())
            doc['ds-flash']['claude'] = ''
            defaults.write_text(json.dumps(doc))
            empty_default = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertNotEqual(empty_default.returncode, 0)
            self.assertFalse(marker.exists())

    def test_shim_configuration_errors_have_safe_diagnostics(self):
        from unittest.mock import Mock
        import io
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {'HOME': temp}):
            local = Path(temp) / '.config/agent-tools/endpoints.json'
            local.parent.mkdir(parents=True)
            local.write_text('{broken')
            handler = Mock(spec=shim.Handler)
            handler.route = {'endpoint_id': 'ds-flash', 'upstream': 'https://unused.example', 'request_prefix': '/v1'}
            handler.headers = {}
            handler.rfile = io.BytesIO()
            handler.path = '/v1/responses'
            shim.Handler._handle(handler)
            self.assertEqual(handler.send_error.call_args.args[0], 503)
            self.assertIn('endpoint error:', handler._log.call_args.args[0])
            routes = Path(temp) / 'routes.json'
            shutil.copyfile(ROOT / 'codex-agent/shim-routes.json', routes)
            result = subprocess.run([sys.executable, str(ROOT / 'codex-agent/bin/codex-auto-review-shim'), '--routes'], env=os.environ | {'SHIM_ROUTES': str(routes)}, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('Traceback', result.stderr)
            local.write_text('{"ds-flash":{"codex":"https://secret-route.example/custom/v1"}}')
            result = subprocess.run([sys.executable, str(ROOT / 'codex-agent/bin/codex-auto-review-shim'), '--routes'], env=os.environ | {'SHIM_ROUTES': str(routes)}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('endpoint:ds-flash', result.stdout)
            self.assertNotIn('secret-route.example', result.stdout)

    def test_url_helper_sees_no_keys_and_claude_gets_only_canonical_token(self):
        import shlex
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            bins = home / 'bin'
            bins.mkdir()
            helper_log = home / 'helper-env.json'
            claude_log = home / 'claude-env.json'
            # Use a Python URL helper stub, matching the launcher's invocation.
            helper = bins / 'agent-endpoint.py'
            helper.write_text('import os,json\nfrom pathlib import Path\nPath(' + repr(str(helper_log)) + ').write_text(json.dumps({k:v for k,v in os.environ.items() if k.endswith(("KEY","TOKEN"))}))\nprint("https://gateway.example/anthropic")\n')
            helper.chmod(0o755)
            stub = bins / 'claude'
            stub.write_text('#!/bin/sh\nexec ' + shlex.quote(sys.executable) + ' -c ' + shlex.quote('import os,json; from pathlib import Path; Path(' + repr(str(claude_log)) + ').write_text(json.dumps({k:v for k,v in os.environ.items() if k.endswith(("KEY","TOKEN"))}))') + '\n')
            stub.chmod(0o755)
            (bins / 'python3').symlink_to(sys.executable)
            # These launch tests isolate PATH; do not depend on Apple's jq.
            jq = bins / 'jq'
            jq.write_text("#!/bin/sh\nprintf '{}\\n'\n")
            jq.chmod(0o755)
            env = os.environ | {'HOME': str(home), 'PATH': f'{bins}:/usr/bin:/bin', 'DEEPSEEK_API_KEY': 'fake-key', 'OTHER_API_KEY': 'unrelated', 'ANTHROPIC_AUTH_TOKEN': 'unrelated-token'}
            result = subprocess.run(['zsh', '-c', 'source "$1"; ds-flash_claude -p ping', '_', str(ROOT / 'scripts/agent-tools.zsh')], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(helper_log.read_text()), {})
            self.assertEqual(json.loads(claude_log.read_text()), {'ANTHROPIC_AUTH_TOKEN': 'fake-key'})

    def test_local_health_uses_the_selected_runtime_endpoint(self):
        import shlex
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            bins = home / 'bin'
            bins.mkdir()
            marker = home / 'health-url'
            shutil.copy2(ROOT / 'scripts/agent-endpoint.py', bins / 'agent-endpoint.py')
            shutil.copyfile(ROOT / 'config/endpoints.example.json', bins / 'agent-endpoints.defaults.json')
            curl = bins / 'curl'
            curl.write_text('#!/bin/sh\nfor arg in "$@"; do last="$arg"; done\nprintf "%s" "$last" > ' + shlex.quote(str(marker)) + '\n')
            curl.chmod(0o755)
            local = home / '.config/agent-tools/endpoints.json'
            local.parent.mkdir(parents=True)
            local.write_text('{"local":{"claude":"http://127.0.0.1:8090","codex":"http://127.0.0.1:8091/v1"}}')
            env = os.environ | {'HOME': str(home), 'PATH': f'{bins}:{os.environ["PATH"]}'}
            for runtime, expected in [('claude','http://127.0.0.1:8090/health'), ('codex','http://127.0.0.1:8091/health')]:
                result = subprocess.run(['zsh', '-c', 'source "$1"; _local_agent_require_service "$2"', '_', str(ROOT / 'scripts/agent-tools.zsh'), runtime], env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(marker.read_text(), expected)

    def test_malformed_route_shapes_exit_without_traceback(self):
        for doc in [[], {'routes':42}, {'routes':[42]}, {'routes':['bad']}, {'routes':[None]}]:
            with self.subTest(doc=doc), tempfile.TemporaryDirectory() as temp:
                routes = Path(temp) / 'routes.json'
                routes.write_text(json.dumps(doc))
                result = subprocess.run([sys.executable, str(ROOT / 'codex-agent/bin/codex-auto-review-shim'), '--routes'], env=os.environ | {'HOME':temp, 'SHIM_ROUTES': str(routes)}, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('Traceback', result.stderr)
                self.assertEqual(len(result.stderr.strip().splitlines()), 1)

    def test_invalid_urls_never_echo_sensitive_values(self):
        for url in ['https://user:SENSITIVE_SENTINEL_7e61@example.com/v1', 'https://example.com/v1?key=SENSITIVE_SENTINEL_7e61', 'file:///tmp/SENSITIVE_SENTINEL_7e61', 'https://example.com:SENSITIVE_SENTINEL_7e61/v1']:
            with self.subTest(url=url), tempfile.TemporaryDirectory() as temp:
                local = Path(temp) / '.config/agent-tools/endpoints.json'
                local.parent.mkdir(parents=True)
                local.write_text(json.dumps({'ds-flash': {'codex': url}}))
                result = subprocess.run([sys.executable, str(ROOT / 'scripts/agent-endpoint.py'), '--check'], env=os.environ | {'HOME': temp}, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('SENSITIVE_SENTINEL_7e61', result.stderr)


@unittest.skipUnless(sys.platform == 'darwin' and shutil.which('codex'), 'macOS and Codex required')
class InstallTests(unittest.TestCase):
    def test_downloaded_bootstrap_reinstall_and_sync_preserve_local_state(self):
        # Use the installed Codex only to read its bundled catalog, never a model API.
        with tempfile.TemporaryDirectory() as codex_home:
            catalog = subprocess.check_output(['codex', 'debug', 'models'], env=os.environ | {'CODEX_HOME': codex_home}, text=True)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / 'home with spaces'
            home.mkdir()
            bins = root / 'bin'
            bins.mkdir()
            catalog_file = root / 'catalog.json'
            catalog_file.write_text(catalog)
            downloaded = root / 'downloaded.sh'
            shutil.copyfile(ROOT / 'install.sh', downloaded)
            scripts = {
                'codex': '#!/bin/sh\ncat "$TEST_CATALOG"\n',
                'claude': '#!/bin/sh\nexit 0\n',
                'launchctl': '#!/bin/sh\nexit 1\n',
                'uv': '''#!/bin/sh
if [ "$1" = venv ]; then
  for arg in "$@"; do target="$arg"; done
  mkdir -p "$target/bin"
  ln -sf "$TEST_PYTHON" "$target/bin/python"
fi
exit 0
''',
                'git': '''#!/bin/sh
if [ "$1" = clone ]; then
  for arg in "$@"; do target="$arg"; done
  "$TEST_PYTHON" - "$TEST_REPO" "$target" <<'PY'
import sys,shutil
from pathlib import Path
shutil.copytree(sys.argv[1], sys.argv[2], ignore=shutil.ignore_patterns('.git','__pycache__'))
(Path(sys.argv[2]) / '.git').mkdir()
PY
elif [ "$3" = remote ]; then
  echo https://github.com/noho/code-is-cheap.git
elif [ "$3" = branch ]; then
  echo main
elif [ "$3" = pull ]; then
  echo pull >> "$HOME/git-events"
fi
''',
            }
            for name, body in scripts.items():
                file = bins / name
                file.write_text(body)
                file.chmod(0o755)
            env = os.environ | {'HOME': str(home), 'PATH': f'{bins}:{os.environ["PATH"]}', 'TEST_CATALOG': str(catalog_file), 'TEST_PYTHON': sys.executable, 'TEST_REPO': str(ROOT)}
            command = ['bash', str(downloaded), '--no-service']
            first = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            endpoint = home / '.config/agent-tools/endpoints.json'
            keys = home / '.config/zsh/agent-tools.local.zsh'
            self.assertEqual(endpoint.stat().st_mode & 0o777, 0o600)
            doc = json.loads(endpoint.read_text())
            doc['ds-flash']['codex'] = 'https://custom.example/opencode/v1'
            endpoint.write_text(json.dumps(doc))
            keys.write_text('# user key setting\nexport DEEPSEEK_API_KEY="fake-key"\n')
            config = home / '.codex/config.toml'
            config.write_text(config.read_text() + '\n[projects."/local"]\ntrust_level="trusted"\n')
            before = endpoint.read_bytes(), keys.read_bytes(), (home / '.zshrc').read_bytes()
            second = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(before, (endpoint.read_bytes(), keys.read_bytes(), (home / '.zshrc').read_bytes()))
            self.assertIn('trust_level="trusted"', config.read_text())
            self.assertEqual((home / 'git-events').read_text(), 'pull\n')
            self.assertTrue((home / '.local/bin/codex-agent-run').is_file())
            self.assertTrue((home / '.claude/skills/sub-agents/SKILL.md').is_file())
            self.assertTrue((home / '.codex/gpt-6-sol.config.toml').is_file())
            endpoint.unlink()
            direct = subprocess.run(['bash', str(home / '.local/share/code-is-cheap/scripts/sync-codex-agent.sh')], env=env, capture_output=True, text=True)
            self.assertEqual(direct.returncode, 0, direct.stderr)
            self.assertFalse(endpoint.exists())
            self.assertEqual(keys.read_bytes(), before[1])
