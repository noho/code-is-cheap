"""Exercise the public runners with deterministic runtime streams, no model requests."""
import json
import os
import shutil
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
class RunnerResults(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        for name in ('claude', 'codex'):
            p = self.bin / name
            p.write_text('#!/bin/sh\nexit 99\n')
            p.chmod(0o755)
        self.fake = self.root / 'fake.py'
        self.fake.write_text('''import os, sys, json, time
from pathlib import Path
args=sys.argv[1:]
if os.environ.get('CAPTURE_PROMPT'): Path(os.environ['CAPTURE_PROMPT']).write_bytes(sys.stdin.buffer.read())
if os.environ.get('CAPTURE_ARGS'): Path(os.environ['CAPTURE_ARGS']).write_text(json.dumps(args))
time.sleep(float(os.environ.get('RUNTIME_DELAY','0')))
for path, content in json.loads(os.environ.get('ARTIFACT_CONTENTS','{}')).items():
 Path(path).write_text(content)
for path, source in json.loads(os.environ.get('ARTIFACT_LINKS','{}')).items():
 os.link(source,path)
if '--output-last-message' in args and not os.environ.get('SKIP_LAST_MESSAGE'):
 Path(args[args.index('--output-last-message')+1]).write_text(os.environ['FINAL'])
if os.environ.get('OCCUPY_LAST_MESSAGE'):
 Path(os.environ['OCCUPY_LAST_MESSAGE']).write_text('raced destination')
if os.environ.get('BREAK_LAST_PARENT'):
 parent=Path(os.environ['BREAK_LAST_PARENT']);parent.rename(str(parent)+'.moved');parent.write_text('not a directory')
print(Path(os.environ['FIXTURE']).read_text(), end='')
print(os.environ.get('ERR', ''), end='', file=sys.stderr)
sys.exit(int(os.environ.get('RUNTIME_EXIT', '0')))
''')
        tools = self.root / 'tools.zsh'
        tools.write_text(f'''_agent_tools_runner_contract() {{ print -r -- pre-exec-error-v1; }}
mimo_codex() {{ exec python3 '{ROOT / 'scripts/agent-endpoint.py'}' --exec-native -- python3 '{self.fake}' "$@"; }}
ds-flash_claude() {{ exec python3 '{ROOT / 'scripts/agent-endpoint.py'}' --exec-native -- python3 '{self.fake}' "$@"; }}
''')
        self.env = os.environ | {'PATH': f'{self.bin}:{os.environ["PATH"]}', 'TMPDIR': str(self.root), 'AGENT_TOOLS_FILE': str(tools), 'FINAL': 'done'}
        self.canary = self.root / 'proof.txt'
        self.canary.write_text('fresh-12345678')
        self.expected = self.root / 'expected.txt'
        self.expected.write_text('fresh-12345678')

    def run_agent(self, runtime, events, *args, exit_code=0, err='', final='done', runner_path=None, workdir=None, prompt="bounded test"):
        fixture = self.root / 'events'
        fixture.write_text('\n'.join(json.dumps(e) if isinstance(e, dict) else e for e in events)+'\n')
        env = self.env | {'FIXTURE': str(fixture), 'RUNTIME_EXIT': str(exit_code), 'ERR': err, 'FINAL': final}
        result = subprocess.run([str(runner_path or ROOT/f'scripts/{runtime}-agent-run'), '--provider', 'mimo' if runtime=='codex' else 'ds-flash', '--cwd', str(workdir or ROOT), '--prompt', prompt, *args], env=env, capture_output=True, text=True)
        return result

    def codex(self, text='done'):
        return [{'type':'thread.started','thread_id':'test'}, {'type':'turn.started'}, {'type':'item.completed','item':{'id':'m','type':'agent_message','text':text}}, {'type':'turn.completed','usage':{}}]

    def claude(self, text='done'):
        return [{'type':'system','subtype':'init','model':'fixture'}, {'type':'result','subtype':'success','is_error':False,'result':text}]

    def connection_notice(self, attempt=1):
        return {'type':'error','message':f'Reconnecting... {attempt}/5 (stream disconnected before completion: stream closed before response.completed)'}

    def server_retry_notice(self, attempt=1, request_id='01234567-89ab-cdef-0123-456789abcdef'):
        return {'type':'error','message':
            f'Reconnecting... {attempt}/5 (stream disconnected before completion: '
            'An error occurred while processing your request. You can retry your request, '
            'or contact us through our help center at help.openai.com if the error persists. '
            f'Please include the request ID {request_id} in your message.)'}

    def startup_diagnostic(self, path='/tmp/synthetic-codex/config.toml', identity='startup-warning'):
        return {'type':'item.completed','item':{'id':identity,'type':'error','message':
            'Under-development features enabled: skip_host_skill_discovery. '
            'Under-development features are incomplete and may behave unpredictably. '
            'To suppress this warning, set `suppress_unstable_features_warning = true` in '+path+'.'}}

    def recovered_codex(self, text='done', attempts=(1,), startup=False, notices=None):
        events=self.codex(text)
        events[2:2]=[self.connection_notice(attempt) for attempt in attempts] if notices is None else notices
        if startup:events.insert(1,self.startup_diagnostic())
        return events

    def run_collector(self, events, *args, runtime="codex", native=0, err=""):
        output=self.root/'collector.jsonl';stderr=self.root/'collector.stderr'
        output.write_text('\n'.join(json.dumps(e) if isinstance(e,dict) else e for e in events)+'\n')
        stderr.write_text(err)
        return subprocess.run(['python3','-B',str(ROOT/'scripts/agent-run-result.py'),
            '--runtime',runtime,'--provider','mimo' if runtime=='codex' else 'ds-flash','--output',str(output),'--stderr',str(stderr),
            '--exit-code',str(native),*args],
            capture_output=True,text=True)

    def assert_report(self, result, native=0, outer=None, final='done'):
        self.assertEqual(result.returncode, native if outer is None else outer, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(set(report), {
            'schema_version', 'source', 'runtime', 'provider', 'runtime_exit_code', 'final_answer',
            'session_id', 'terminal', 'wall_clock_seconds', 'usage', 'runtime_metrics', 'logs',
            'diagnostics', 'checks'})
        self.assertEqual(report['schema_version'], 2)
        self.assertEqual(report['source'], 'subagent_report')
        self.assertEqual(report['runtime_exit_code'], native)
        self.assertEqual(report['final_answer'], final)
        self.assertEqual(set(report['checks']), {'artifacts', 'canary'})
        for diagnostic in report['diagnostics']:
            self.assertEqual(set(diagnostic), {'message', 'path', 'line'})
        return report

    def observation(self, report, text):
        return next(d for d in report['diagnostics'] if text in d['message'])

    def test_native_codes_and_explanatory_final_are_caller_owned(self):
        finals = ['Python import failed: ModuleNotFoundError; no report was written.',
                  'Missing input. I cannot proceed.', 'Blocked by environment.', 'Incomplete skeleton only.']
        for runtime in ('codex', 'claude'):
            for native in (0, 1, 2, 7, 126, 127):
                for final in finals:
                    missing = self.root / 'absent-report'
                    report = self.assert_report(self.run_agent(runtime, getattr(self, runtime)(final),
                        '--artifact', str(missing), exit_code=native), native=native, final=final)
                    self.assertEqual(report['checks']['artifacts'], [dict(path=str(missing), exists=False, regular_file=False)])
                    self.assertEqual(self.observation(report, 'artifact missing')['path'], str(missing))
                # Even damaged sources and no final cannot alter a known native code.
                self.assert_report(self.run_agent(runtime, ['{bad'], exit_code=native), native=native, final=None)

    def test_full_final_unicode_and_whitespace_round_trips_every_entry(self):
        text = ' \n\t' + ('你好 Ω 😀\tline\r\n' * 1500) + '\n \t\r\n'
        self.assertGreater(len(text), 12000)
        for runtime in ('codex', 'claude'):
            events = getattr(self, runtime)(text)
            self.assert_report(self.run_collector(events, runtime=runtime), final=text)
            last = self.root / 'full-last-message'
            options = ['--last-message', str(last)] if runtime == 'codex' else []
            report = self.assert_report(self.run_agent(runtime, events, *options, final=text), final=text)
            if runtime == 'codex':
                self.assertEqual(last.read_bytes(), text.encode())
                self.assertFalse(any('differs' in d['message'] for d in report['diagnostics']))
            self.assertIn(text, [json.loads(line).get('result', json.loads(line).get('item', {}).get('text'))
                                 for line in Path(report['logs']['output']).read_text().splitlines()])

    def test_warning_wording_is_opaque_in_identical_envelopes(self):
        texts = [self.connection_notice()['message'], '[claude-code:unrecognized_model] {"model":"new"}',
                 'arbitrary diagnostic Ω\n\tsecond line  ', '', '  SSE recovered? NEVER classify me\t', 'x' * 2500]
        for runtime in ('codex', 'claude'):
            for native in (0, 7):
                for envelope in ('error', 'warning', 'stderr', 'item' if runtime == 'codex' else 'retry'):
                    for text in texts:
                        events = getattr(self, runtime)()
                        err = ''
                        if envelope in ('error', 'warning'): events.insert(-1, dict(type=envelope, message=text, future=[]))
                        elif envelope == 'item': events.insert(1, dict(type='item.completed', item=dict(type='error', id='e', message=text)))
                        elif envelope == 'retry': events.insert(1, dict(type='system', subtype='api_retry', message=text))
                        else: err = text + '\n'
                        report = self.assert_report(self.run_agent(runtime, events, exit_code=native, err=err), native=native)
                        path = report['logs']['stderr' if envelope == 'stderr' else 'output']
                        diagnostics = [d for d in report['diagnostics'] if d['path'] == path]
                        if envelope == 'stderr':
                            self.assertEqual(''.join(d['message'] for d in diagnostics), err)
                            self.assertEqual([d['line'] for d in diagnostics], list(range(1, len(err.splitlines()) + 1)))
                        else:
                            self.assertIn(dict(message=text, path=path, line=len(events)-1 if envelope in ('error','warning') else 2), diagnostics)

    def test_diagnostics_have_no_count_or_text_cap(self):
        for runtime in ('codex', 'claude'):
            messages = [('arbitrary ' + str(n) + 'x' * 2100 + '\n') for n in range(30)]
            report = self.assert_report(self.run_agent(runtime, getattr(self, runtime)(), err=''.join(messages)))
            self.assertEqual([d['message'] for d in report['diagnostics'] if d['path'] == report['logs']['stderr']], messages)

    def test_claude_root_result_only_with_intermediate_assistant_present(self):
        assistant = {'type':'assistant', 'message':{'content':[{'type':'text','text':'INTERMEDIATE MUST NOT BECOME FINAL'}]}}
        nested = {'type':'result', 'parent_tool_use_id':'child', 'subtype':'success', 'result':'NESTED NOT FINAL'}
        cases = [([], None), ([nested], None), ([dict(type='result', result='')], ''),
                 ([dict(type='result', result='   \n')], '   \n'),
                 ([dict(type='result')], None), ([dict(type='result', result=None)], None),
                 ([dict(type='result', result=42)], None), ([dict(type='result', result=[])], None),
                 ([dict(type='result', result='a'), dict(type='result', result='b')], None),
                 ([nested, dict(type='result', subtype='success', result='ROOT')], 'ROOT')]
        for tail, expected in cases:
            events = [assistant, *tail]
            for entry in ('collector', 'runner'):
                result = self.run_collector(events, runtime='claude') if entry == 'collector' else self.run_agent('claude', events)
                report = self.assert_report(result, final=expected)
                self.assertIn('INTERMEDIATE MUST NOT BECOME FINAL', Path(report['logs']['output']).read_text())
                if expected is None: self.assertTrue(report['diagnostics'])

    def test_codex_latest_completed_message_and_ancillary_fields(self):
        for value in ('new', '', '  ', None, 42, []):
            events = self.codex('earlier')
            events.insert(-1, dict(type='item.completed', metadata={}, item=dict(type='agent_message', text=value, future=True)))
            self.assert_report(self.run_agent('codex', events), final=value if isinstance(value, str) else None)
        events = self.codex(); events[0]['extra']=[]; events[1]['future']=True
        events[2]['item']['extra']='fine'; events[-1]['future']={}
        self.assert_report(self.run_collector(events))

    def test_structured_negative_terminal_metadata_is_only_observed(self):
        fields = [('subtype','error'), ('is_error',True), ('stop_reason','max_tokens'),
                  ('terminal_reason','hook_stopped'), ('api_error_status',500), ('errors',['original error Ω']),
                  ('deferred_tool_use',{})]
        for key, value in fields:
            events = self.claude(); events[-1][key]=value
            report = self.assert_report(self.run_agent('claude', events))
            self.assertTrue(report['diagnostics'])
        events = self.codex(); events[-1].update(type='turn.failed',error={'message':'native explanation'})
        report = self.assert_report(self.run_agent('codex', events))
        self.assertEqual(report['terminal'], 'turn.failed')
        self.assertEqual(self.observation(report, 'native explanation')['line'], 4)

    def test_protocol_damage_does_not_erase_attributable_final(self):
        for runtime in ('codex', 'claude'):
            for damage in ('{bad', '{"type":"error","message":"one","message":"two"}',
                           '{"type":"error","message":"\\ud800"}', '{"type":"error","number":1e400}', '[]'):
                events = getattr(self, runtime)(); events.insert(1, damage)
                report = self.assert_report(self.run_agent(runtime, events))
                diagnostic = self.observation(report, 'invalid event')
                self.assertEqual((diagnostic['path'],diagnostic['line']), (report['logs']['output'],2))
            events = getattr(self, runtime)()[:-1]
            self.assert_report(self.run_agent(runtime, events), final='done' if runtime=='codex' else None)
            events = getattr(self, runtime)(); events.append(events[-1].copy())
            report = self.assert_report(self.run_agent(runtime, events), final='done' if runtime=='codex' else None)
            self.assertIsNone(report['terminal']); self.assertIsNone(report['usage'])
            self.assertEqual(report['runtime_metrics'], {})

    def test_collector_unreadable_missing_and_binary_sources_are_observations(self):
        for mode in ('missing', 'directory', 'permission', 'binary'):
            output = self.root/'bad-source'; stderr = self.root/'bad-stderr'
            stderr.write_text('')
            if mode == 'directory': output.mkdir()
            elif mode == 'permission': output.write_text(''); output.chmod(0)
            elif mode == 'binary':
                output.write_bytes(b'\xff\n' + b'\n'.join(json.dumps(e).encode() for e in self.codex()))
            result = subprocess.run([sys.executable, str(ROOT/'scripts/agent-run-result.py'), '--runtime','codex',
                '--provider','mimo','--output',str(output),'--stderr',str(stderr),'--exit-code','0'], capture_output=True,text=True)
            report = self.assert_report(result, final='done' if mode=='binary' else None)
            self.assertTrue(report['diagnostics'])
            if mode == 'directory': output.rmdir()
            elif output.exists(): output.chmod(0o600); output.unlink()

    def test_identity_absence_invalid_conflicts_and_nested_scope(self):
        for runtime in ('codex','claude'):
            for value in (None,42,[],{},'', '  '):
                events=getattr(self,runtime)()
                if runtime=='codex': events[0]['thread_id']=value
                else: events[0]['session_id']=value; events[-1]['session_id']=value
                self.assertIsNone(self.assert_report(self.run_agent(runtime,events))['session_id'])
            events=getattr(self,runtime)()
            if runtime=='codex': events.insert(1,{'type':'thread.started','thread_id':'other'})
            else: events[0]['session_id']='one';events[-1]['session_id']='two'
            report=self.assert_report(self.run_agent(runtime,events));self.assertIsNone(report['session_id'])
            self.observation(report,'conflicting runtime session')
        events=self.claude();events[-1]['session_id']='root'
        events.insert(1,dict(type='assistant',parent_tool_use_id='child',session_id='nested',message={'content':[]}))
        self.assertEqual(self.assert_report(self.run_agent('claude',events))['session_id'],'root')

    def test_tool_errors_incomplete_and_scoped_pairing_are_factual(self):
        codex=self.codex();codex.insert(2,dict(type='item.completed',item=dict(id='c',type='command_execution',
            command='cat missing',status='failed',exit_code=2,aggregated_output='HUGE TRANSCRIPT'*1000)))
        claude=self.claude();claude[1:1]=[
            {'type':'assistant','message':{'content':[dict(type='tool_use',id='c',name='Read',input={'path':'missing'})]}},
            {'type':'user','message':{'content':[dict(type='tool_result',tool_use_id='c',is_error=True,content='HUGE TRANSCRIPT'*1000)]}}]
        for runtime,events in [('codex',codex),('claude',claude)]:
            report=self.assert_report(self.run_agent(runtime,events))
            self.assertTrue(report['diagnostics']);self.assertNotIn('HUGE TRANSCRIPT',json.dumps(report['diagnostics']))
        events=self.claude(); events.insert(1,{'type':'assistant','message':{'content':[dict(type='tool_use',id='c',input={})]}})
        events.insert(2,{'type':'user','parent_tool_use_id':'nested','message':{'content':[dict(type='tool_result',tool_use_id='c')]}})
        report=self.assert_report(self.run_agent('claude',events));self.observation(report,'without matching call');self.observation(report,'without completion')

    def test_tool_like_final_text_receives_no_semantic_diagnostic(self):
        for runtime in ('codex','claude'):
            baseline=self.assert_report(self.run_agent(runtime,getattr(self,runtime)()))['diagnostics']
            for text in ('<tool_call>pretend</tool_call>', '{"type":"tool_use","name":"Bash","input":{}}',
                         '```json\n{"function_call":{}}\n```', 'I could not perform any work.'):
                report=self.assert_report(self.run_agent(runtime,getattr(self,runtime)(text)),final=text)
                # Log paths vary across invocations; message/location behavior is unchanged.
                self.assertEqual([(d['message'],d['line']) for d in report['diagnostics']],[(d['message'],d['line']) for d in baseline])

    def test_checks_canary_artifacts_and_proof_offsets(self):
        for runtime in ('codex','claude'):
            path=self.root/f'{runtime}.artifact'
            self.env['ARTIFACT_CONTENTS']=json.dumps({str(path):'intro\nCANARY=wrong\n'})
            text='intro\n\nCANARY=wrong'
            report=self.assert_report(self.run_agent(runtime,getattr(self,runtime)(text),'--artifact',str(path),
                '--canary-file',str(self.canary),'--canary-expected',str(self.expected)),final=text)
            self.assertEqual(report['checks']['canary'],dict(proof_observed=True,proof_matches_expected=False,read_candidate_observed=False))
            mismatches=[d for d in report['diagnostics'] if 'does not match' in d['message']]
            self.assertEqual(mismatches[0],dict(message='canary proof does not match expected token (proof line 3)',
                path=report['logs']['output'],line=3 if runtime=='codex' else 2))
            self.assertEqual(mismatches[1],dict(message='canary proof does not match expected token (proof line 2)',path=str(path),line=2))
            self.assertEqual(report['checks']['artifacts'],[dict(path=str(path),exists=True,regular_file=True)])
        self.env.pop('ARTIFACT_CONTENTS')
        events=self.codex('CANARY=fresh-12345678');events.insert(2,dict(type='item.completed',item=dict(type='command_execution',id='c',
            command=f'cat {self.canary}',aggregated_output=self.canary.read_text(),exit_code=0)))
        report=self.assert_report(self.run_agent('codex',events,'--canary-file',str(self.canary),'--canary-expected',str(self.expected)), final='CANARY=fresh-12345678')
        self.assertEqual(report['checks']['canary'],dict(proof_observed=True,proof_matches_expected=True,read_candidate_observed=True))

    def test_canary_examples_and_unavailable_expected_are_not_verdicts(self):
        for example in ('    CANARY=wrong','\tCANARY=wrong','```text\nCANARY=wrong\n```',
                        '````text\n```\nCANARY=wrong\n```\n````','<pre>\nCANARY=wrong\n</pre>',
                        'An example: `CANARY=wrong`'):
            text='CANARY=`fresh-12345678`\n'+example
            report=self.assert_report(self.run_collector(self.codex(text),'--canary-file',str(self.canary),
                '--canary-expected',str(self.expected)),final=text)
            self.assertTrue(report['checks']['canary']['proof_matches_expected'])
        self.expected.unlink()
        report=self.assert_report(self.run_collector(self.codex('CANARY=x'),'--canary-file',str(self.canary),
            '--canary-expected',str(self.expected)),final='CANARY=x')
        self.assertIsNone(report['checks']['canary']['proof_matches_expected'])

    def test_runtime_created_artifact_hardlinks_are_only_observed(self):
        original=self.root/'original';original.write_text('old')
        for runtime in ('codex','claude'):
            for source_kind in ('output','stderr','existing'):
                output=self.root/f'{runtime}-{source_kind}.out';stderr=self.root/f'{runtime}-{source_kind}.err'
                artifact=self.root/f'{runtime}-{source_kind}.artifact'
                self.env['ARTIFACT_LINKS']=json.dumps({str(artifact):str({'output':output,'stderr':stderr,'existing':original}[source_kind])})
                report=self.assert_report(self.run_agent(runtime,getattr(self,runtime)(),'--output',str(output),'--stderr',str(stderr),'--artifact',str(artifact)))
                self.observation(report,'hard-linked or aliases')

    def test_auxiliary_missing_raced_unwritable_and_stale_preserve_native(self):
        for detail in (False,True):
            for native in (0,7):
                for mode,phrase in [('missing','did not produce'),('raced','destination now exists'),('unwritable','cannot save'),('stale','differs')]:
                    parent=self.root/f'{detail}-{native}-{mode}';parent.mkdir();last=parent/'last'
                    if mode=='missing':self.env['SKIP_LAST_MESSAGE']='1'
                    elif mode=='raced':self.env['OCCUPY_LAST_MESSAGE']=str(last)
                    elif mode=='unwritable':self.env['BREAK_LAST_PARENT']=str(parent)
                    result=self.run_agent('codex',self.codex(),'--last-message',str(last),*(['--detail'] if detail else []),exit_code=native,final='stale' if mode=='stale' else 'done')
                    self.assertEqual(result.returncode,native,result.stderr)
                    if not detail:
                        report=self.assert_report(result,native=native)
                        diagnostics=''.join(d['message'] for d in report['diagnostics']);self.assertIn(phrase,diagnostics)
                        if mode in ('raced','unwritable'):
                            self.assertEqual(Path(report['logs']['last_message']).read_text(),'done')
                    elif mode!='stale':self.assertIn(phrase,result.stderr)
                    if mode=='raced':self.assertEqual(last.read_text(),'raced destination')
                    for key in ('SKIP_LAST_MESSAGE','OCCUPY_LAST_MESSAGE','BREAK_LAST_PARENT'):self.env.pop(key,None)

    def test_auxiliary_cleanup_failure_keeps_copy_source_and_exit(self):
        rm=self.bin/'rm';rm.write_text('#!/bin/sh\nexit 1\n');rm.chmod(0o755)
        for detail in (False,True):
            for native in (0,7):
                last=self.root/f'cleanup-{detail}-{native}'
                result=self.run_agent('codex',self.codex(),'--last-message',str(last),*(['--detail'] if detail else []),exit_code=native)
                self.assertEqual(result.returncode,native,result.stderr);self.assertEqual(last.read_text(),'done')
                stderr=result.stderr if detail else Path(json.loads(result.stdout)['logs']['stderr']).read_text()
                self.assertIn('cannot remove temporary',stderr);self.assertIn('retained at',stderr)
                retained=stderr.split('final message retained at: ')[-1].splitlines()[0]
                self.assertEqual(Path(retained).read_text(),'done')

    def test_collector_execution_serialization_and_primary_write_failures(self):
        for runtime in ('codex','claude'):
            for mode,program in [('crash','raise RuntimeError("injected crash")'),
                                 ('serialize','import json; print(json.dumps(object()))'),
                                 ('write','import os; os.close(1); print("unwritable")')]:
                staged=self.root/f'{runtime}-{mode}';staged.mkdir()
                shutil.copy2(ROOT/f'scripts/{runtime}-agent-run',staged/f'{runtime}-agent-run')
                (staged/'agent-run-result.py').write_text(program+'\n')
                for native in (0,7):
                    result=self.run_agent(runtime,getattr(self,runtime)(),runner_path=staged/f'{runtime}-agent-run',exit_code=native)
                    self.assertEqual(result.returncode,native or 1,result.stderr)
                    self.assertIn('primary result delivery failed',result.stderr)
                    self.assertIn(f'known native exit={native}',result.stderr)
                    self.assertIn('output=',result.stderr);self.assertIn('stderr=',result.stderr)
            # Adapter existed during setup, then disappeared before collection.
            staged=self.root/f'{runtime}-missing-collector';staged.mkdir()
            shutil.copy2(ROOT/f'scripts/{runtime}-agent-run',staged/f'{runtime}-agent-run')
            adapter=staged/'agent-run-result.py';adapter.write_text('')
            original=self.fake.read_text();self.fake.write_text(original.replace('args=sys.argv[1:]',f'Path({str(adapter)!r}).unlink()\nargs=sys.argv[1:]'))
            result=self.run_agent(runtime,getattr(self,runtime)(),runner_path=staged/f'{runtime}-agent-run')
            self.assertEqual(result.returncode,1);self.assertIn('known native exit=0',result.stderr)
            self.fake.write_text(original)

    def test_large_prompt_pipeline_uses_native_component_and_preserves_bytes(self):
        prompt=('large prompt Ω\n' * 60000)+'\n\t  \n'
        prompt_path=self.root/'large-prompt';prompt_path.write_text(prompt)
        for native in (0,7):
            fixture=self.root/'events';fixture.write_text('\n'.join(json.dumps(e) for e in self.codex())+'\n')
            env=self.env|{'FIXTURE':str(fixture),'RUNTIME_EXIT':str(native)}
            command=[str(ROOT/'scripts/codex-agent-run'),'--provider','mimo','--cwd',str(ROOT)]
            # Fake exits without reading stdin, causing the producer to encounter SIGPIPE.
            self.assert_report(subprocess.run(command+['--prompt-file',str(prompt_path)],env=env,capture_output=True,text=True),native=native)
            capture=self.root/'prompt-bytes';env['CAPTURE_PROMPT']=str(capture)
            self.assert_report(subprocess.run(command,env=env,input=prompt,capture_output=True,text=True),native=native)
            self.assertEqual(capture.read_bytes(),prompt.encode())

    def test_invalid_setup_never_calls_runtime(self):
        capture=self.root/'called';self.env['CAPTURE_ARGS']=str(capture)
        empty=self.root/'empty';empty.write_text('')
        bad=self.root/'bad';bad.write_text('bad token')
        for runtime in ('codex','claude'):
            for c,e in [(self.root/'missing',self.expected),(self.canary,self.root),(empty,self.expected),(self.canary,bad)]:
                result=self.run_agent(runtime,getattr(self,runtime)(),'--canary-file',str(c),'--canary-expected',str(e))
                self.assertEqual(result.returncode,2);self.assertFalse(capture.exists())
            for option in ('--output','--stderr',*(['--last-message'] if runtime=='codex' else [])):
                result=self.run_agent(runtime,getattr(self,runtime)(),option,'-')
                self.assertEqual(result.returncode,2);self.assertFalse(capture.exists())
            result=self.run_agent(runtime,[],'--output-format','text')
            self.assertEqual(result.returncode,2);self.assertFalse(capture.exists())
            for prompt in (' \t\n','\u3000','\u00a0'):
                self.assertEqual(self.run_agent(runtime,[],prompt=prompt).returncode,2);self.assertFalse(capture.exists())

    def test_destinations_are_new_distinct_private_and_not_symlinks(self):
        existing=self.root/'existing';existing.write_text('old')
        directory=self.root/'directory';directory.mkdir()
        alias=self.root/'alias';alias.symlink_to(existing)
        for runtime in ('codex','claude'):
            for option in ('--output','--stderr','--artifact',*(['--last-message'] if runtime=='codex' else [])):
                for path in (existing,directory,alias):
                    self.assertEqual(self.run_agent(runtime,getattr(self,runtime)(),option,str(path)).returncode,2)
            fresh=self.root/'same'
            self.assertEqual(self.run_agent(runtime,[],'--output',str(fresh),'--stderr',str(fresh)).returncode,2)
            self.assertEqual(self.run_agent(runtime,[],'--output',str(fresh),'--artifact',str(fresh)).returncode,2)
            report=self.assert_report(self.run_agent(runtime,getattr(self,runtime)()))
            for path in (report['logs']['output'],report['logs']['stderr']):self.assertEqual(Path(path).stat().st_mode&0o777,0o600)
            self.assertIsNone(report['checks']['canary']);self.assertIsNone(report['logs']['last_message'])
        self.assertEqual(existing.read_text(),'old')

    def test_detail_is_raw_and_bypasses_checks(self):
        for runtime in ('codex','claude'):
            events=getattr(self,runtime)();raw='\n'.join(json.dumps(e) for e in events)+'\n'
            for native in (0,7):
                result=self.run_agent(runtime,events,'--detail','--artifact',str(self.root/'missing'),exit_code=native,err='opaque\n')
                self.assertEqual(result.returncode,native);self.assertEqual(result.stdout,raw);self.assertEqual(result.stderr,'opaque\n')
            path=self.root/f'{runtime}-detail'
            result=self.run_agent(runtime,events,'--detail','--output',str(path))
            self.assertEqual(result.stdout,'');self.assertEqual(path.read_text(),raw)

    def test_persist_resume_defaults_and_relative_runner_paths(self):
        capture=self.root/'args';self.env['CAPTURE_ARGS']=str(capture)
        workspace=self.root/'work';workspace.mkdir()
        for runtime in ('codex','claude'):
            events=getattr(self,runtime)();sid='native-id'
            if runtime=='codex':events[0]['thread_id']=sid
            else:events[0]['session_id']=sid;events[-1]['session_id']=sid
            report=self.assert_report(self.run_agent(runtime,events,runner_path=Path('scripts')/f'{runtime}-agent-run',workdir=workspace))
            self.assertEqual(report['session_id'],sid)
            args=json.loads(capture.read_text());self.assertIn('--ephemeral' if runtime=='codex' else '--no-session-persistence',args)
            if runtime=='claude':self.assertRegex(args[args.index('--name')+1],r'^ds-flash-[0-9a-f]{8}$')
            for option in (['--persist'],['--resume',sid]):
                self.assert_report(self.run_agent(runtime,events,*option))
                args=json.loads(capture.read_text());self.assertNotIn('--ephemeral' if runtime=='codex' else '--no-session-persistence',args)

    def test_terminal_metrics_are_actual_unique_totals(self):
        self.env['RUNTIME_DELAY']='0.05'
        for runtime in ('codex','claude'):
            events=getattr(self,runtime)();usage={'input_tokens':123,'zero':0,'nested':{'reported_string':'2'}}
            events[-1]['usage']=usage
            if runtime=='claude':
                events.insert(1,{'type':'assistant','message':{'content':[],'usage':{'input_tokens':999}}})
                events[-1].update(duration_ms=0,duration_api_ms=12,total_cost_usd=0,modelUsage={'m':{'inputTokens':123}})
            report=self.assert_report(self.run_agent(runtime,events));self.assertEqual(report['usage'],usage)
            self.assertGreaterEqual(report['wall_clock_seconds'],0.05)
            self.assertEqual(report['runtime_metrics'],{} if runtime=='codex' else {k:events[-1][k] for k in ('duration_ms','duration_api_ms','total_cost_usd','modelUsage')})
            for native in (0,7):
                events[-1].update(type='turn.failed',error={'message':'native'}) if runtime=='codex' else events[-1].update(subtype='error',is_error=True)
                self.assertEqual(self.assert_report(self.run_agent(runtime,events,exit_code=native),native=native)['usage'],usage)
            for usage in (None,42,[], '42'):
                events[-1]['usage']=usage
                self.assertIsNone(self.assert_report(self.run_collector(events,runtime=runtime))['usage'])
        for value in (None,'not-a-time','-1','NaN','inf','0','1.25'):
            report=self.assert_report(self.run_collector(self.codex(),*([] if value is None else ['--wall-clock-seconds='+value])))
            self.assertEqual(report['wall_clock_seconds'],float(value) if value in ('0','1.25') else None)

    def test_staged_install_keeps_adapter_and_launch_helper_self_contained(self):
        installed=self.root/'installed'
        env=self.env|{'AGENT_RUN_BIN_DIR':str(installed),'AGENT_TOOLS_TARGET':str(self.root/'installed-tools.zsh')}
        setup=subprocess.run(['bash',str(ROOT/'scripts/sync-agent-tools.sh')],env=env,capture_output=True,text=True)
        self.assertEqual(setup.returncode,0,setup.stderr)
        for runtime in ('codex','claude'):
            self.assert_report(self.run_agent(runtime,getattr(self,runtime)(),runner_path=installed/f'{runtime}-agent-run'))


if __name__=='__main__': unittest.main()
