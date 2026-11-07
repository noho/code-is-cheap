"""Provider-boundary contracts; no model or private credentials required."""
import copy
import gzip
import http.client
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('delivery_shim', str(ROOT / 'codex-agent/bin/codex-auto-review-shim'))
spec = importlib.util.spec_from_loader(loader.name, loader)
shim = importlib.util.module_from_spec(spec)
loader.exec_module(shim)


def agent(kind='NEW_TASK', text='  中文\n\t🧪  '):
    return {'type': 'agent_message', 'id': 'amsg_native', 'author': '/root/a',
            'recipient': '/root/b', 'internal_chat_message_metadata_passthrough': {'source': 'native', 'sequence': 7},
            'content': [{'type': 'input_text', 'text': f'Message Type: {kind}\nPayload:\n'},
                        {'type': 'encrypted_content', 'encrypted_content': text},
                        {'type': 'input_text', 'text': ''}]}


def encode(doc):
    return json.dumps(doc, ensure_ascii=False).encode()


class DeliveryTests(unittest.TestCase):
    def test_known_envelopes_preserve_content_routing_metadata_order_and_others(self):
        untouched = [{'type': 'message', 'role': 'developer', 'id': 'msg_x', 'content': 'unchanged'},
                     {'type': 'reasoning', 'encrypted_content': 'OPAQUE'},
                     {'type': 'function_call', 'arguments': '{"encrypted_content":"DO NOT TOUCH"}'}]
        for kind in ('NEW_TASK', 'MESSAGE', 'FINAL_ANSWER'):
            with self.subTest(kind=kind):
                a = agent(kind)
                # A second task represents history + followup, preserving order.
                doc = {'model': 'original', 'stream': True, 'metadata': {'x': 1}, 'input': [untouched[0], a, *untouched[1:], agent(text='FOLLOWUP')]}
                original = copy.deepcopy(doc)
                out, n = shim.fix_agent_messages(encode(doc))
                fixed = json.loads(out)
                self.assertEqual(n, 2)
                self.assertEqual(doc, original)
                self.assertEqual({k: v for k, v in fixed.items() if k != 'input'}, {k: v for k, v in doc.items() if k != 'input'})
                self.assertEqual([fixed['input'][i] for i in (0, 2, 3)], untouched)
                msg = fixed['input'][1]
                self.assertEqual(set(msg), {'type', 'role', 'content'})
                self.assertEqual(msg['role'], 'user')
                metadata = json.loads(msg['content'][0]['text'].split(': ', 1)[1])
                self.assertEqual(metadata, {k: v for k, v in a.items() if k not in ('type', 'content')})
                self.assertEqual([p['text'] for p in msg['content'][1:]], [a['content'][0]['text'], '  中文\n\t🧪  ', ''])
                self.assertEqual(fixed['input'][4]['content'][2]['text'], 'FOLLOWUP')

    def test_no_targets_byte_noop_and_opaque_reasoning_untouched(self):
        for body in (b'not json', b'[]', b'{ "input": "text" }', b'{ "input": [{"type":"reasoning","encrypted_content":"OPAQUE"}] }'):
            self.assertEqual(shim.fix_agent_messages(body), (body, 0))

    def test_body_only_plaintext_and_empty_strings_are_not_lost(self):
        for kind, key in (('input_text', 'text'), ('encrypted_content', 'encrypted_content')):
            for text in ('', ' \t\n', '独立任务 🧪'):
                item = agent(); item['content'] = [{'type': kind, key: text}]
                out, n = shim.fix_agent_messages(encode({'input': [item]}))
                self.assertEqual(n, 1)
                self.assertEqual(json.loads(out)['input'][0]['content'][1], {'type': 'input_text', 'text': text})

    def test_unknown_invalid_shapes_reject_whole_request_sanitized(self):
        invalids = [None, {}, [], '', [None], [{'type': 'image', 'secret': 'SECRET'}],
                    [{'type': 'input_text', 'text': 1}], [{'type': ['SECRET']}],
                    [{'type': 'encrypted_content', 'encrypted_content': {}}],
                    [{'type': 'input_text', 'text': 'SECRET', 'future': True}]]
        for content in invalids:
            bad = agent(); bad['content'] = content
            with self.subTest(content=content), self.assertRaisesRegex(ValueError, r'^Invalid agent_message at input\[1\]$'):
                shim.fix_agent_messages(encode({'input': [agent(), bad]}))
        for key in ('author', 'recipient'):
            for value in (None, '', [], 1):
                bad = agent(); bad[key] = value
                with self.assertRaises(ValueError):
                    shim.fix_agent_messages(encode({'input': [bad]}))

    def handle(self, doc, encoding='', enabled=True, responses=None):
        # Execute the production Handler._handle with real urllib Request and
        # byte streams; intercept only the external network boundary.
        plain = encode(doc)
        body = {'gzip': gzip.compress, 'deflate': zlib.compress}.get(encoding, lambda b: b)(plain)
        h = Mock(spec=shim.Handler)
        h.route = {'port': 1, 'endpoint_id': 'ds-flash', 'request_prefix': '/v1',
                   'from': 'codex-auto-review', 'to': 'deepseek-flash', 'agent_message_fix': enabled,
                   'id_fix': True, 'json_fmt_fix': True, 'drop_tools_item': True}
        h.headers = {'Content-Length': str(len(body)), 'Content-Encoding': encoding,
                     'Authorization': 'WRONG', 'X-Api-Key': 'WRONG', 'Api-Key': 'WRONG'}
        h.rfile, h.wfile = io.BytesIO(body), io.BytesIO()
        h.command, h.path, h._summary = 'POST', '/v1/responses', shim.Handler._summary
        if responses is None:
            r = Mock(status=200, headers={'Content-Type': 'text/event-stream'})
            r.read.return_value = b'event: response.completed\n'
            r.read1.side_effect = [b'event: response.', b'completed\n', b'']
            responses = [r]
        connection = {'base_url': 'https://example.invalid/v1', 'upstream_model': 'upstream/model', 'api_key': 'FAKE_MANAGED'}
        with patch.object(shim, 'endpoint_module') as endpoint, patch.object(shim, 'upstream_open', side_effect=responses) as opening:
            endpoint.return_value.connection.return_value = connection
            shim.Handler._handle(h)
            endpoint.return_value.connection.assert_called_once_with('ds-flash', 'codex', require_key=True)
        return h, opening, responses, body

    def test_handler_encoding_model_credentials_stream_and_other_transforms(self):
        for encoding in ('', 'identity', 'gzip', 'deflate'):
            with self.subTest(encoding=encoding):
                doc = {'model': 'deepseek-flash', 'stream': True, 'input': [agent(), {'type': 'additional_tools'}],
                       'text': {'format': {'type': 'json_schema', 'schema': {}}}}
                h, opening, responses, _ = self.handle(doc, encoding)
                req = opening.call_args.args[0]
                raw = {'gzip': gzip.decompress, 'deflate': zlib.decompress}.get(encoding, lambda b: b)(req.data)
                out = json.loads(raw)
                self.assertEqual(out['model'], 'upstream/model')
                self.assertTrue(out['stream'])
                self.assertEqual(len(out['input']), 1)
                self.assertEqual(out['input'][0]['role'], 'user')
                self.assertEqual(out['text']['format'], {'type': 'json_object'})
                self.assertEqual(req.full_url, 'https://example.invalid/v1/responses')
                self.assertEqual(req.get_header('Authorization'), 'Bearer FAKE_MANAGED')
                self.assertIsNone(req.get_header('X-api-key'))
                self.assertIsNone(req.get_header('Api-key'))
                self.assertIsNone(req.get_header('Content-length'))
                self.assertEqual(req.get_header('Content-encoding'), encoding)
                responses[0].read.assert_not_called()
                self.assertEqual(responses[0].read1.call_count, 3)
                self.assertEqual(h.wfile.getvalue(), b'event: response.completed\n')
                h._dump.assert_not_called()

    def test_handler_invalid_rejected_before_any_upstream_or_dump(self):
        for encoding in ('identity', 'gzip', 'deflate'):
            bad = agent(); bad['content'].append({'type': 'SECRET_FUTURE', 'text': 'SECRET_BODY'})
            h, opening, _, _ = self.handle({'input': [agent(), bad]}, encoding)
            opening.assert_not_called()
            h.send_error.assert_called_once_with(400, 'Invalid agent_message at input[1]')
            h._dump.assert_not_called()
            self.assertNotIn('SECRET', str(h._log.call_args_list))

    def test_handler_disabled_noop(self):
        # Invalid agent content also remains untouched on disabled routes.
        bad = agent(); bad['content'] = [{'type': 'FUTURE'}]
        doc = {'model': 'unmapped-model', 'input': [bad]}
        h, opening, _, body = self.handle(doc, enabled=False)
        self.assertEqual(opening.call_args.args[0].data, body)
        h.send_error.assert_not_called()

    def test_handler_invalid_unicode_is_sanitized_before_model_swap(self):
        bad = agent(text='\ud800')
        # JSON's escaped surrogate is accepted by json.loads but cannot be
        # represented as UTF-8. This must fail as a client error, not disconnect.
        doc = {'model': 'deepseek-flash', 'input': [bad]}
        with patch(__name__ + '.encode', lambda d: json.dumps(d).encode()):
            h, opening, _, _ = self.handle(doc)
        opening.assert_not_called()
        h.send_error.assert_called_once_with(400, 'Invalid agent_message Unicode')

    def test_guardian_original_identity_buffer_retry_and_adapter(self):
        responses = []
        for payload in (b'event: response.created\n', b'event: response.completed\n'):
            r = Mock(status=200, headers={}); r.read.return_value = payload
            responses.append(r)
        h, opening, _, _ = self.handle({'model': 'codex-auto-review', 'input': [agent()]}, responses=responses)
        self.assertEqual(opening.call_count, 2)
        for r in responses:
            r.read.assert_called_once(); r.read1.assert_not_called()
        out = json.loads(opening.call_args.args[0].data)
        self.assertEqual(out['model'], 'upstream/model')
        self.assertEqual(out['input'][0]['role'], 'user')
        self.assertEqual(h.wfile.getvalue(), b'event: response.completed\n')

    def test_route_flag_explicit_default_off_ds_only(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'routes.json'
            path.write_text(json.dumps({'agent_message_fix': True, 'routes': [
                {'port': 1, 'to': 'a', 'upstream': 'http://localhost'},
                {'port': 2, 'to': 'b', 'upstream': 'http://localhost', 'agent_message_fix': True}]}))
            with patch.dict(os.environ, {'SHIM_ROUTES': str(path)}):
                self.assertEqual([r['agent_message_fix'] for r in shim.load_routes()], [False, True])
        routes = json.loads((ROOT / 'codex-agent/shim-routes.json').read_text())['routes']
        self.assertEqual([r['endpoint_id'] for r in routes if r.get('agent_message_fix')], ['ds-flash'])

    def test_actual_http_handler_framing_compression_and_sanitized_400(self):
        requests = []

        def upstream(req, timeout):
            requests.append(req)
            response = Mock(status=200, headers={'Content-Type': 'text/event-stream'})
            response.read1.side_effect = [b'event: response.completed\n\n', b'']
            return response

        route = {'listen': '127.0.0.1:0', 'endpoint_id': 'ds-flash', 'request_prefix': '/v1',
                 'from': 'codex-auto-review', 'to': 'deepseek-flash', 'agent_message_fix': True}
        with patch.object(shim, 'endpoint_module') as endpoint, patch.object(shim, 'upstream_open', side_effect=upstream), patch.object(shim.Handler, '_log'), patch.object(shim.Handler, '_dump') as dump:
            endpoint.return_value.connection.return_value = {'base_url': 'https://example.invalid/v1', 'upstream_model': 'remote/model', 'api_key': 'FAKE_MANAGED'}
            server = shim._make_server(route)
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                for encoding in ('identity', 'gzip', 'deflate'):
                    raw = encode({'model': 'deepseek-flash', 'stream': True, 'input': [agent()]})
                    body = shim.ENCODERS.get(encoding, lambda b: b)(raw)
                    client = http.client.HTTPConnection(*server.server_address, timeout=3)
                    client.request('POST', '/v1/responses', body, {'Content-Encoding': encoding, 'Authorization': 'WRONG'})
                    response = client.getresponse()
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.read(), b'event: response.completed\n\n')
                    client.close()
                    out = json.loads(shim.DECODERS.get(encoding, lambda b: b)(requests[-1].data))
                    self.assertEqual(out['model'], 'remote/model')
                    self.assertEqual(out['input'][0]['role'], 'user')
                    self.assertEqual(requests[-1].get_header('Authorization'), 'Bearer FAKE_MANAGED')
                client = http.client.HTTPConnection(*server.server_address, timeout=3)
                bad = agent(); bad['content'].append({'type': 'SECRET_VARIANT', 'text': 'SECRET_BODY'})
                client.request('POST', '/v1/responses', encode({'input': [agent(), bad]}))
                response = client.getresponse()
                self.assertEqual(response.status, 400)
                self.assertNotIn(b'SECRET', response.read())
                self.assertEqual(len(requests), 3)
                client.close()
                dump.assert_not_called()
            finally:
                server.shutdown(); server.server_close(); thread.join()


if __name__ == '__main__':
    unittest.main()
