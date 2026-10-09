"""Exercise private connections, model mapping and install with isolated homes."""

import copy
import gzip
import http.client
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest
import zlib
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader(
    "endpoint_shim", str(ROOT / "codex-agent/bin/codex-auto-review-shim")
)
spec = importlib.util.spec_from_loader(loader.name, loader)
shim = importlib.util.module_from_spec(spec)
loader.exec_module(shim)
FACTORY = json.loads((ROOT / "config/endpoints.example.json").read_text())
HELPER = ROOT / "scripts/agent-endpoint.py"


def fixture_env(**changes):
    # Reviews run under authenticated provider clients. Never copy those real
    # inherited credentials into fixture JSON or subprocess diagnostics.
    env = {
        k: v
        for k, v in os.environ.items()
        if not any(
            part in k.upper()
            for part in [
                "KEY",
                "TOKEN",
                "SECRET",
                "PASSWORD",
                "CREDENTIAL",
                "AUTHORIZATION",
            ]
        )
    }
    return env | changes


def private_doc(home, doc):
    path = Path(home) / ".config/agent-tools/endpoints.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc))
    path.chmod(0o600)
    return path


def conn(
    url="https://gateway.example/custom/v1", model="gateway/model", key="fake-json-key"
):
    return {"base_url": url, "upstream_model": model, "api_key": key}


def stage_helper(bins):
    bins.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HELPER, bins / HELPER.name)
    shutil.copyfile(
        ROOT / "config/endpoints.example.json", bins / "agent-endpoints.defaults.json"
    )
    (bins / "python3").symlink_to(sys.executable)


class EndpointTests(unittest.TestCase):
    def run_helper(self, home, *args):
        return subprocess.run(
            [sys.executable, str(HELPER), *args],
            env=fixture_env(HOME=str(home)),
            capture_output=True,
            text=True,
        )

    def test_whole_runtime_override_revert_and_single_snapshot(self):
        with (
            tempfile.TemporaryDirectory() as temp,
            patch.dict(os.environ, {"HOME": temp}),
        ):
            doc = copy.deepcopy(FACTORY)
            doc["default"]["ds-flash"]["codex"]["api_key"] = "factory-local-key"
            path = private_doc(temp, doc)
            before = shim.endpoint_module().load_endpoints()
            doc["override"] = {"ds-flash": {"codex": conn()}}
            path.write_text(json.dumps(doc))
            module = shim.endpoint_module()
            selected = module.connection("ds-flash", "codex", require_key=True)
            self.assertEqual(selected, conn())
            self.assertEqual(
                module.connection("ds-flash", "claude")["base_url"],
                FACTORY["default"]["ds-flash"]["claude"]["base_url"],
            )
            self.assertEqual(
                module.connection("mimo", "codex"), FACTORY["default"]["mimo"]["codex"]
            )
            route = {"endpoint_id": "ds-flash", "request_prefix": "/v1"}
            self.assertEqual(
                shim.route_url(route, "/v1/responses?stream=true"),
                "https://gateway.example/custom/v1/responses?stream=true",
            )
            doc["override"] = {}
            path.write_text(json.dumps(doc))
            self.assertEqual(
                module.connection("ds-flash", "codex"), before["ds-flash"]["codex"]
            )
            self.assertEqual(
                shim.route_url(route, "/v1/responses", selected),
                "https://gateway.example/custom/v1/responses",
            )
            with self.assertRaises(ValueError):
                shim.route_url(route, "/wrong/responses")

    def test_missing_file_uses_defaults_without_creating_or_loading_env_keys(self):
        with (
            tempfile.TemporaryDirectory() as temp,
            patch.dict(
                os.environ, {"HOME": temp, "DEEPSEEK_API_KEY": "inherited-secret"}
            ),
        ):
            module = shim.endpoint_module()
            self.assertEqual(
                module.endpoint("ds-flash", "claude"),
                FACTORY["default"]["ds-flash"]["claude"]["base_url"],
            )
            with self.assertRaises(ValueError):
                module.connection("ds-flash", "codex", require_key=True)
            self.assertFalse(
                (Path(temp) / ".config/agent-tools/endpoints.json").exists()
            )

    def test_invalid_config_and_partial_override_fail_closed_without_secret_echo(self):
        invalid = [
            [],
            {},
            {"defaut": {}},
            {
                "default": {},
                "override": {
                    "ds-flash": {"codex": {"base_url": "https://other.example/v1"}}
                },
            },
            {"default": {}, "override": {"ds-flash": {"codex": conn(key="")}}},
            {"default": {"unknown": {"codex": conn()}}},
            {"default": {}, "override": None},
        ]
        for doc in invalid:
            with self.subTest(doc=doc), tempfile.TemporaryDirectory() as temp:
                private_doc(temp, doc)
                result = self.run_helper(temp, "--check")
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("fake-json-key", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
        for url in [
            "https://user:SENSITIVE_SENTINEL@example.com/v1",
            "https://example.com/v1?key=SENSITIVE_SENTINEL",
            "file:///tmp/SENSITIVE_SENTINEL",
            "https://example.com:SENSITIVE_SENTINEL/v1",
        ]:
            with self.subTest(url=url), tempfile.TemporaryDirectory() as temp:
                private_doc(
                    temp,
                    {"default": {}, "override": {"ds-flash": {"codex": conn(url=url)}}},
                )
                result = self.run_helper(temp, "--check")
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("SENSITIVE_SENTINEL", result.stderr)

    def test_duplicate_fields_permissions_symlinks_and_factory_keys_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = private_doc(temp, FACTORY)
            path.write_text('{"default":{},"default":{}}')
            self.assertNotEqual(self.run_helper(temp, "--check").returncode, 0)
            path.write_text(json.dumps(FACTORY))
            for mode in [0o400, 0o700, 0o644, 0o600]:
                with self.subTest(mode=oct(mode)):
                    path.chmod(mode)
                    self.assertEqual(
                        self.run_helper(temp, "--check").returncode == 0, mode == 0o600
                    )
            real = path.with_name("real.json")
            path.rename(real)
            real.chmod(0o600)
            path.symlink_to(real)
            self.assertNotEqual(self.run_helper(temp, "--check").returncode, 0)
            path.unlink()
            bins = Path(temp) / "bin"
            stage_helper(bins)
            doc = copy.deepcopy(FACTORY)
            doc["default"]["ds-flash"]["codex"]["api_key"] = "BAD_FACTORY_KEY"
            (bins / "agent-endpoints.defaults.json").write_text(json.dumps(doc))
            result = subprocess.run(
                [sys.executable, str(bins / "agent-endpoint.py"), "--check"],
                env=os.environ | {"HOME": temp},
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("BAD_FACTORY_KEY", result.stderr)

    def test_initialization_is_exclusive_and_reinstall_never_overwrites_overrides(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_helper(temp, "--initialize")
            self.assertEqual(result.returncode, 0, result.stderr)
            path = Path(temp) / ".config/agent-tools/endpoints.json"
            doc = json.loads(path.read_text())
            self.assertEqual(doc, FACTORY)
            doc["override"] = {"ds-flash": {"codex": conn()}}
            path.write_text(json.dumps(doc))
            before = path.read_bytes()
            self.assertEqual(self.run_helper(temp, "--initialize").returncode, 0)
            self.assertEqual(path.read_bytes(), before)
            self.assertFalse(
                (Path(temp) / ".config/zsh/agent-tools.local.zsh").exists()
            )

    def test_claude_gets_one_connection_no_key_in_argv_and_clean_inherited_environment(
        self,
    ):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            bins = home / "bin"
            stage_helper(bins)
            helper_log = home / "helper-env.json"
            claude_log = home / "claude.json"
            wrapper = bins / "agent-endpoint.py"
            wrapper.write_text(
                "import os,json,sys\nfrom pathlib import Path\nPath("
                + repr(str(helper_log))
                + ').write_text(json.dumps({k:v for k,v in os.environ.items() if k.endswith(("KEY","TOKEN"))}))\nos.execv(sys.executable,[sys.executable,'
                + repr(str(HELPER))
                + ",*sys.argv[1:]])\n"
            )
            stub = bins / "claude"
            stub.write_text(
                "#!"
                + sys.executable
                + "\nimport os,json,sys\nfrom pathlib import Path\nPath("
                + repr(str(claude_log))
                + ').write_text(json.dumps({"keys":{k:v for k,v in os.environ.items() if k.endswith(("KEY","TOKEN"))},"argv":sys.argv[1:]}))\n'
            )
            stub.chmod(0o755)
            private_doc(
                home,
                {
                    "default": {},
                    "override": {
                        "ds-flash": {
                            "claude": conn(
                                url="https://gateway.example",
                                model="gateway/deepseek",
                                key="SELECTED_FAKE_KEY",
                            )
                        }
                    },
                },
            )
            env = os.environ | {
                "HOME": str(home),
                "PATH": str(bins) + ":/usr/bin:/bin",
                "DEEPSEEK_API_KEY": "old-inherited",
                "OTHER_API_KEY": "unrelated",
                "ANTHROPIC_AUTH_TOKEN": "old-token",
            }
            result = subprocess.run(
                [
                    "zsh",
                    "-f",
                    "-c",
                    'source "$1"; ds-flash_claude -p ping',
                    "_",
                    str(ROOT / "scripts/agent-tools.zsh"),
                ],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(helper_log.read_text()), {})
            captured = json.loads(claude_log.read_text())
            self.assertEqual(
                captured["keys"], {"ANTHROPIC_AUTH_TOKEN": "SELECTED_FAKE_KEY"}
            )
            self.assertNotIn("SELECTED_FAKE_KEY", json.dumps(captured["argv"]))
            settings = json.loads(captured["argv"][1])["env"]
            self.assertEqual(settings["ANTHROPIC_MODEL"], "gateway/deepseek")
            self.assertEqual(settings["ANTHROPIC_BASE_URL"], "https://gateway.example")
            self.assertEqual(settings["CLAUDE_CODE_SUBAGENT_MODEL"], "gateway/deepseek")
            self.assertEqual(captured["argv"][-2:], ["-p", "ping"])
            # The installed helper's direct CLI entry must enforce the same
            # auth boundary without relying on the zsh caller.
            env["ANTHROPIC_API_KEY"] = "OTHER_FAKE_AUTH"
            direct = subprocess.run(
                [
                    sys.executable,
                    str(HELPER),
                    "--launch-claude",
                    "ds-flash",
                    "--",
                    "-p",
                    "ping",
                ],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(direct.returncode, 0, direct.stderr)
            direct_capture = json.loads(claude_log.read_text())
            self.assertEqual(
                direct_capture["keys"], {"ANTHROPIC_AUTH_TOKEN": "SELECTED_FAKE_KEY"}
            )
            self.assertNotIn("SELECTED_FAKE_KEY", json.dumps(direct_capture["argv"]))

    def test_guardian_read_failures_retry_and_exhaust_as_controlled_gateway_error(self):
        with (
            tempfile.TemporaryDirectory() as temp,
            patch.dict(os.environ, {"HOME": temp}),
        ):
            private_doc(
                temp, {"default": {}, "override": {"ds-flash": {"codex": conn()}}}
            )
            for success in [True, False]:
                with self.subTest(success=success):
                    handler = Mock(spec=shim.Handler)
                    handler.route = {
                        "endpoint_id": "ds-flash",
                        "request_prefix": "/v1",
                        "from": "codex-auto-review",
                        "to": "deepseek-flash",
                        "port": 8788,
                    }
                    body = b'{"model":"codex-auto-review"}'
                    handler.headers = {"Content-Length": str(len(body))}
                    handler.rfile, handler.wfile = io.BytesIO(body), io.BytesIO()
                    handler.path, handler.command = "/v1/responses", "POST"
                    handler._summary = shim.Handler._summary
                    responses = [Mock(status=200, headers={}) for _ in range(3)]
                    for response in responses:
                        response.read.side_effect = http.client.IncompleteRead(
                            b"partial"
                        )
                    if success:
                        responses[-1].read.side_effect = None
                        responses[-1].read.return_value = b"event: response.completed\n"
                    with patch.object(
                        shim, "upstream_open", side_effect=responses
                    ) as opening:
                        shim.Handler._handle(handler)
                    self.assertEqual(opening.call_count, 3)
                    handler.send_response.assert_called_once_with(
                        200 if success else 502
                    )
                    for response in responses[: 2 if success else 3]:
                        response.close.assert_called_once()
                    self.assertEqual(
                        handler.wfile.getvalue(),
                        b"event: response.completed\n" if success else b"",
                    )

    def test_all_request_transforms_apply_before_restoring_gzip_and_deflate(self):
        with (
            tempfile.TemporaryDirectory() as temp,
            patch.dict(os.environ, {"HOME": temp}),
        ):
            private_doc(
                temp, {"default": {}, "override": {"ds-flash": {"codex": conn()}}}
            )
            original = {
                "model": "deepseek-flash",
                "input": [
                    {"id": "at_123", "type": "message"},
                    {"type": "additional_tools"},
                ],
                "text": {"format": {"type": "json_schema", "schema": {}}},
            }
            plain = json.dumps(original, separators=(",", ":")).encode()
            for codec, encode, decode in [
                ("", lambda x: x, lambda x: x),
                ("gzip", gzip.compress, gzip.decompress),
                ("deflate", zlib.compress, zlib.decompress),
            ]:
                with self.subTest(codec=codec):
                    body = encode(plain)
                    handler = Mock(spec=shim.Handler)
                    handler.route = {
                        "endpoint_id": "ds-flash",
                        "request_prefix": "/v1",
                        "from": "codex-auto-review",
                        "to": "deepseek-flash",
                        "port": 8788,
                        "id_fix": True,
                        "json_fmt_fix": True,
                        "drop_tools_item": True,
                    }
                    handler.headers = {
                        "Content-Length": str(len(body)),
                        "Content-Encoding": codec,
                    }
                    handler.rfile, handler.wfile = io.BytesIO(body), io.BytesIO()
                    handler.path, handler.command = "/v1/responses", "POST"
                    handler._summary = shim.Handler._summary
                    response = Mock(status=200, headers={})
                    response.read1.side_effect = [b"event: response.completed\n", b""]
                    with patch.object(
                        shim, "upstream_open", return_value=response
                    ) as opening:
                        shim.Handler._handle(handler)
                    request = opening.call_args.args[0]
                    result = json.loads(decode(request.data))
                    self.assertEqual(result["model"], "gateway/model")
                    self.assertEqual(
                        result["input"], [{"id": "msg_123", "type": "message"}]
                    )
                    self.assertEqual(result["text"]["format"], {"type": "json_object"})
                    self.assertEqual(request.get_header("Content-encoding"), codec)
                    response.read.assert_not_called()

    def test_claude_not_started_when_config_key_or_helper_is_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            bins = home / "bin"
            bins.mkdir()
            (bins / "python3").symlink_to(sys.executable)
            marker = home / "called"
            stub = bins / "claude"
            stub.write_text("#!/bin/sh\ntouch " + shlex.quote(str(marker)) + "\n")
            stub.chmod(0o755)
            env = os.environ | {"HOME": temp, "PATH": str(bins) + ":/usr/bin:/bin"}
            command = [
                "zsh",
                "-f",
                "-c",
                'source "$1"; ds-flash_claude -p ping',
                "_",
                str(ROOT / "scripts/agent-tools.zsh"),
            ]
            self.assertNotEqual(
                subprocess.run(command, env=env, capture_output=True).returncode, 0
            )
            self.assertFalse(marker.exists())
            shutil.copy2(HELPER, bins / HELPER.name)
            shutil.copyfile(
                ROOT / "config/endpoints.example.json",
                bins / "agent-endpoints.defaults.json",
            )
            self.assertNotEqual(
                subprocess.run(command, env=env, capture_output=True).returncode, 0
            )
            self.assertFalse(marker.exists())
            path = private_doc(
                home, {"default": {}, "override": {"ds-flash": {"claude": conn()}}}
            )
            healthy = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertEqual(healthy.returncode, 0, healthy.stderr)
            self.assertTrue(marker.exists())
            marker.unlink()
            path.write_text("{broken")
            self.assertNotEqual(
                subprocess.run(command, env=env, capture_output=True).returncode, 0
            )
            self.assertFalse(marker.exists())

    def test_codex_client_gets_no_cloud_key_but_selected_connection_is_required(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            bins = home / "bin"
            stage_helper(bins)
            capture = home / "codex.json"
            stub = bins / "codex"
            stub.write_text(
                "#!"
                + sys.executable
                + "\nimport os,json,sys\nfrom pathlib import Path\nPath("
                + repr(str(capture))
                + ').write_text(json.dumps({"keys":{k:v for k,v in os.environ.items() if k.endswith(("KEY","TOKEN"))},"argv":sys.argv[1:]}))\n'
            )
            stub.chmod(0o755)
            card = home / ".codex/ds-flash.config.toml"
            card.parent.mkdir()
            card.write_text('model="deepseek-flash"\n')
            private_doc(
                home, {"default": {}, "override": {"ds-flash": {"codex": conn()}}}
            )
            env = os.environ | {
                "HOME": temp,
                "PATH": str(bins) + ":" + os.environ["PATH"],
                "DEEPSEEK_API_KEY": "old-key",
            }
            command = [
                "zsh",
                "-f",
                "-c",
                'source "$1"; _codex_agent_require_shim() { return 0; }; ds-flash_codex exec ping',
                "_",
                str(ROOT / "scripts/agent-tools.zsh"),
            ]
            result = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            captured = json.loads(capture.read_text())
            self.assertEqual(captured["keys"], {})
            self.assertEqual(captured["argv"], ["exec", "-p", "ds-flash", "ping"])
            capture.unlink()
            private_doc(home, {"default": {}})
            self.assertNotEqual(
                subprocess.run(command, env=env, capture_output=True).returncode, 0
            )
            self.assertFalse(capture.exists())

    def test_shim_maps_normal_and_guardian_models_without_buffering_normal_requests(
        self,
    ):
        with (
            tempfile.TemporaryDirectory() as temp,
            patch.dict(os.environ, {"HOME": temp}),
        ):
            path = private_doc(
                temp, {"default": {}, "override": {"ds-flash": {"codex": conn()}}}
            )
            route = {
                "endpoint_id": "ds-flash",
                "request_prefix": "/v1",
                "from": "codex-auto-review",
                "to": "deepseek-flash",
                "port": 8788,
            }
            for model, guardian, complete in [
                ("deepseek-flash", False, True),
                ("codex-auto-review", True, True),
                ("deepseek-flash", False, False),
            ]:
                handler = Mock(spec=shim.Handler)
                handler.route = route
                body = json.dumps(
                    {"model": model, "input": [{"model": "deepseek-flash"}]}
                ).encode()
                handler.headers = {
                    "Content-Length": str(len(body)),
                    "Authorization": "Bearer WRONG_INHERITED",
                    "x-api-key": "WRONG_OTHER",
                }
                handler.rfile = io.BytesIO(body)
                handler.wfile = io.BytesIO()
                handler.path = "/v1/responses"
                handler.command = "POST"
                handler._summary = shim.Handler._summary
                response = Mock()
                response.status = 200
                response.headers = {}
                payload = (
                    b"event: response.completed\n"
                    if complete
                    else b"event: response.created\n"
                )
                response.read.return_value = payload
                response.read1.side_effect = [payload, b""]
                with patch.object(
                    shim, "upstream_open", return_value=response
                ) as opening:
                    shim.Handler._handle(handler)
                request = opening.call_args.args[0]
                self.assertEqual(
                    request.full_url, "https://gateway.example/custom/v1/responses"
                )
                self.assertEqual(
                    request.get_header("Authorization"), "Bearer fake-json-key"
                )
                self.assertIsNone(request.get_header("X-api-key"))
                doc = json.loads(request.data)
                self.assertEqual(doc["model"], "gateway/model")
                self.assertEqual(doc["input"][0]["model"], "deepseek-flash")
                if guardian:
                    response.read.assert_called_once()
                else:
                    response.read.assert_not_called()
                    self.assertEqual(response.read1.call_count, 2)
                self.assertNotIn("fake-json-key", str(handler._log.call_args_list))
                if complete:
                    handler._dump.assert_not_called()
                else:
                    self.assertEqual(handler._dump.call_count, 2)
                    self.assertEqual(
                        handler._dump.call_args_list[0].args[1], "nostream"
                    )
            path.write_text(
                json.dumps(
                    {
                        "default": {},
                        "override": {
                            "ds-flash": {
                                "codex": conn(
                                    url="https://new.example/v1",
                                    model="next/model",
                                    key="NEXT_FAKE_KEY",
                                )
                            }
                        },
                    }
                )
            )
            self.assertEqual(
                shim.endpoint_module().connection(
                    "ds-flash", "codex", require_key=True
                ),
                conn(
                    url="https://new.example/v1",
                    model="next/model",
                    key="NEXT_FAKE_KEY",
                ),
            )

    def test_shim_missing_key_or_bad_json_fails_before_upstream_and_logs_sanitized_error(
        self,
    ):
        with (
            tempfile.TemporaryDirectory() as temp,
            patch.dict(os.environ, {"HOME": temp}),
        ):
            for doc in [FACTORY, {"defaut": {"api_key": "SENSITIVE_SENTINEL"}}]:
                private_doc(temp, doc)
                handler = Mock(spec=shim.Handler)
                handler.route = {
                    "endpoint_id": "ds-flash",
                    "request_prefix": "/v1",
                    "from": "codex-auto-review",
                    "to": "deepseek-flash",
                }
                handler.headers = {}
                handler.rfile = io.BytesIO()
                handler.path = "/v1/responses"
                with patch.object(shim, "upstream_open") as opening:
                    shim.Handler._handle(handler)
                opening.assert_not_called()
                self.assertEqual(handler.send_error.call_args.args[0], 503)
                self.assertNotIn("SENSITIVE_SENTINEL", str(handler._log.call_args_list))

    def test_redirect_does_not_forward_gateway_key(self):
        received = []

        class Destination(BaseHTTPRequestHandler):
            def do_POST(self):
                received.append(self.headers.get("Authorization"))
                self.send_response(200)
                self.end_headers()

            def log_message(self, *args):
                pass

        target = ThreadingHTTPServer(("127.0.0.1", 0), Destination)

        class Redirect(BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(302)
                self.send_header(
                    "Location", f"http://127.0.0.1:{target.server_port}/responses"
                )
                self.end_headers()

            def log_message(self, *args):
                pass

        source = ThreadingHTTPServer(("127.0.0.1", 0), Redirect)
        threads = [
            threading.Thread(target=server.serve_forever, daemon=True)
            for server in [source, target]
        ]
        for thread in threads:
            thread.start()
        try:
            request = urllib.request.Request(
                f"http://127.0.0.1:{source.server_port}/responses",
                data=b"{}",
                headers={"Authorization": "Bearer FAKE_REDIRECT_KEY"},
            )
            with self.assertRaises(urllib.error.HTTPError) as caught:
                shim.upstream_open(request, timeout=2)
            self.assertEqual(caught.exception.code, 302)
            self.assertEqual(received, [])
        finally:
            for server in [source, target]:
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join()

    def test_local_codex_model_reaches_cli_and_app_composer(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            bins = home / "bin"
            stage_helper(bins)
            capture = home / "codex-args"
            stub = bins / "codex"
            stub.write_text(
                '#!/bin/sh\nprintf "%s\\n" "$@" > ' + shlex.quote(str(capture)) + "\n"
            )
            stub.chmod(0o755)
            curl = bins / "curl"
            curl.write_text("#!/bin/sh\nexit 0\n")
            curl.chmod(0o755)
            card = home / ".codex/local.config.toml"
            card.parent.mkdir()
            card.write_text('model="qwen3.8-27b-local"\nmodel_provider="local_llama"\n')
            doc = copy.deepcopy(FACTORY)
            doc["default"]["local"]["codex"]["upstream_model"] = "local/selected-model"
            private_doc(home, doc)
            env = fixture_env(HOME=temp, PATH=str(bins) + ":" + os.environ["PATH"])
            result = subprocess.run(
                [
                    "zsh",
                    "-f",
                    "-c",
                    'source "$1"; local_codex exec ping',
                    "_",
                    str(ROOT / "scripts/agent-tools.zsh"),
                ],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                capture.read_text().splitlines(),
                ["exec", "-c", 'model="local/selected-model"', "-p", "local", "ping"],
            )
            base = home / ".codex/config.toml"
            base.write_text('model="gpt-6-sol"\n')
            out = home / "app.toml"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/compose-codex-app-config.py"),
                    "--base",
                    str(base),
                    "--card",
                    str(card),
                    "--out",
                    str(out),
                    "--model",
                    "local/selected-model",
                ],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('model = "local/selected-model"', out.read_text())

    def test_manual_skill_sync_reuses_installed_validator_environment(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            interpreter = home / ".local/share/code-is-cheap-installer/venv/bin/python"
            interpreter.parent.mkdir(parents=True)
            marker = home / "validator-used"
            interpreter.write_text(
                "#!/bin/sh\necho used >> "
                + shlex.quote(str(marker))
                + "\nexec "
                + shlex.quote(sys.executable)
                + ' "$@"\n'
            )
            interpreter.chmod(0o755)
            env = os.environ | {"HOME": temp}
            for name in ["SKILL_VALIDATOR_PYTHON", "PYTHON", "SKILL_VALIDATOR"]:
                env.pop(name, None)
            result = subprocess.run(
                ["bash", str(ROOT / "scripts/validate-skills.sh")],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(marker.exists())

    def test_local_health_uses_the_selected_runtime_endpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            bins = home / "bin"
            stage_helper(bins)
            marker = home / "health-url"
            curl = bins / "curl"
            curl.write_text(
                '#!/bin/sh\nfor arg in "$@"; do last="$arg"; done\nprintf "%s" "$last" > '
                + shlex.quote(str(marker))
                + "\n"
            )
            curl.chmod(0o755)
            doc = copy.deepcopy(FACTORY)
            doc["default"]["local"]["claude"]["base_url"] = "http://127.0.0.1:8090"
            doc["default"]["local"]["codex"]["base_url"] = "http://127.0.0.1:8091/v1"
            private_doc(home, doc)
            env = os.environ | {
                "HOME": temp,
                "PATH": str(bins) + ":" + os.environ["PATH"],
            }
            for runtime, expected in [
                ("claude", "http://127.0.0.1:8090/health"),
                ("codex", "http://127.0.0.1:8091/health"),
            ]:
                result = subprocess.run(
                    [
                        "zsh",
                        "-f",
                        "-c",
                        'source "$1"; _local_agent_require_service "$2"',
                        "_",
                        str(ROOT / "scripts/agent-tools.zsh"),
                        runtime,
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(marker.read_text(), expected)

    def test_malformed_route_shapes_exit_without_traceback(self):
        for doc in [
            [],
            {"routes": 42},
            {"routes": [42]},
            {"routes": ["bad"]},
            {"routes": [None]},
        ]:
            with self.subTest(doc=doc), tempfile.TemporaryDirectory() as temp:
                routes = Path(temp) / "routes.json"
                routes.write_text(json.dumps(doc))
                result = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "codex-agent/bin/codex-auto-review-shim"),
                        "--routes",
                    ],
                    env=os.environ | {"HOME": temp, "SHIM_ROUTES": str(routes)},
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(len(result.stderr.strip().splitlines()), 1)


@unittest.skipUnless(
    sys.platform == "darwin" and shutil.which("codex"), "macOS and Codex required"
)
class InstallTests(unittest.TestCase):
    def test_downloaded_bootstrap_reinstall_and_sync_preserve_local_state(self):
        # Use the installed Codex only to read its bundled catalog, never a model API.
        with tempfile.TemporaryDirectory() as codex_home:
            catalog = subprocess.check_output(
                ["codex", "debug", "models"],
                env=os.environ | {"CODEX_HOME": codex_home},
                text=True,
            )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home with spaces"
            home.mkdir()
            bins = root / "bin"
            bins.mkdir()
            catalog_file = root / "catalog.json"
            catalog_file.write_text(catalog)
            downloaded = root / "downloaded.sh"
            shutil.copyfile(ROOT / "install.sh", downloaded)
            scripts = {
                "codex": '#!/bin/sh\ncat "$TEST_CATALOG"\n',
                "claude": "#!/bin/sh\nexit 0\n",
                "launchctl": "#!/bin/sh\nexit 1\n",
                "uv": """#!/bin/sh
if [ "$1" = venv ]; then
  for arg in "$@"; do target="$arg"; done
  mkdir -p "$target/bin"
  ln -sf "$TEST_PYTHON" "$target/bin/python"
fi
exit 0
""",
                "git": """#!/bin/sh
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
""",
            }
            for name, body in scripts.items():
                file = bins / name
                file.write_text(body)
                file.chmod(0o755)
            env = fixture_env(
                HOME=str(home),
                PATH=f"{bins}:{os.environ['PATH']}",
                TEST_CATALOG=str(catalog_file),
                TEST_PYTHON=sys.executable,
                TEST_REPO=str(ROOT),
            )
            command = ["bash", str(downloaded), "--no-service"]
            first = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            endpoint = home / ".config/agent-tools/endpoints.json"
            keys = home / ".config/zsh/agent-tools.local.zsh"
            self.assertEqual(endpoint.stat().st_mode & 0o777, 0o600)
            doc = json.loads(endpoint.read_text())
            doc["override"]["ds-flash"] = {
                "codex": {
                    "base_url": "https://custom.example/opencode/v1",
                    "upstream_model": "gateway/model",
                    "api_key": "fake-json-key",
                }
            }
            endpoint.write_text(json.dumps(doc))
            keys.write_text('# user key setting\nexport DEEPSEEK_API_KEY="fake-key"\n')
            config = home / ".codex/config.toml"
            config.write_text(
                config.read_text() + '\n[projects."/local"]\ntrust_level="trusted"\n'
            )
            before = (
                endpoint.read_bytes(),
                keys.read_bytes(),
                (home / ".zshrc").read_bytes(),
            )
            second = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(
                before,
                (
                    endpoint.read_bytes(),
                    keys.read_bytes(),
                    (home / ".zshrc").read_bytes(),
                ),
            )
            self.assertIn('trust_level="trusted"', config.read_text())
            self.assertEqual((home / "git-events").read_text(), "pull\n")
            self.assertTrue((home / ".local/bin/codex-agent-run").is_file())
            self.assertEqual((home / ".local/bin/agent-sandbox-launch.mjs").read_bytes(), (ROOT / "scripts/agent-sandbox-launch.mjs").read_bytes())
            self.assertTrue((home / ".claude/skills/sub-agents/SKILL.md").is_file())
            self.assertTrue((home / ".codex/gpt-6-sol.config.toml").is_file())
            endpoint.unlink()
            direct = subprocess.run(
                [
                    "bash",
                    str(
                        home / ".local/share/code-is-cheap/scripts/sync-codex-agent.sh"
                    ),
                ],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(direct.returncode, 0, direct.stderr)
            self.assertFalse(endpoint.exists())
            self.assertEqual(keys.read_bytes(), before[1])
