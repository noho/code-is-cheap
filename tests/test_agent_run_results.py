"""Exercise the public runners with deterministic runtime streams, no model requests."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
class RunnerResults(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
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
        tools.write_text(f'''mimo_codex() {{ python3 '{self.fake}' "$@"; }}
ds-flash_claude() {{ python3 '{self.fake}' "$@"; }}
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

    def run_collector(self, events, *args, runtime="codex", native=0, precollection=0, err=""):
        output=self.root/'collector.jsonl';stderr=self.root/'collector.stderr'
        output.write_text('\n'.join(json.dumps(e) if isinstance(e,dict) else e for e in events)+'\n')
        stderr.write_text(err)
        return subprocess.run(['python3','-B',str(ROOT/'scripts/agent-run-result.py'),
            '--runtime',runtime,'--provider','mimo' if runtime=='codex' else 'ds-flash','--output',str(output),'--stderr',str(stderr),
            '--exit-code',str(native),'--runner-exit-code',str(precollection),*args],
            capture_output=True,text=True)

    def assert_report_contract(self, report):
        self.assertEqual(set(report), {
            'schema_version','source','runtime','provider','runtime_exit_code','runner_exit_code',
            'agent_status','validation_status','result_status','final_answer','final_answer_truncated',
            'final_answer_chars','wall_clock_seconds','usage','runtime_metrics','session_id','terminal',
            'tool_evidence_scope','tool_results','events','canary_status','canary_read_candidate',
            'errors','anomalies','warnings','diagnostic_counts','diagnostics_truncated','artifacts','logs'})
        for key,value in {'schema_version':1,'source':'subagent_report','result_status':'not_assessed',
                          'tool_evidence_scope':'recorded_events_only'}.items():
            self.assertEqual(report[key],value)

    def assert_completion(self, result, status='passed', agent='completed', exit_code=None, runner_code=None):
        report=json.loads(result.stdout)
        self.assert_report_contract(report)
        expected=(1 if status=='rejected' else 0) if exit_code is None else exit_code
        self.assertEqual(result.returncode,expected,result.stderr)
        self.assertEqual(report['runner_exit_code'],expected if runner_code is None else runner_code)
        self.assertEqual(report['validation_status'],status)
        self.assertEqual(report['agent_status'],agent)
        return report

    def assert_output_diagnostic(self, diagnostic, message, line):
        self.assertEqual(diagnostic, {'stream':'output','line':line,'message':message,
            'message_chars':len(message),'truncated':False,'path':None,'proof_line':None})

    def assistant(self, blocks, **fields):
        return {'type':'assistant','message':{'content':blocks},**fields}

    def tool_call(self, identity, **fields):
        return self.assistant([{'type':'tool_use','id':identity,'name':'Bash','input':{}}],**fields)

    def tool_result(self, identity, **fields):
        return {'type':'user','message':{'content':[{'type':'tool_result','tool_use_id':identity,
            'content':'synthetic output','is_error':False}]},**fields}

    def test_novel_diagnostics_recover_without_text_inventory(self):
        messages=['novel upstream diagnostic Ω\nsecond line','',self.connection_notice(29)['message'],
                  self.server_retry_notice(9,'ABC-new-request')['message'],'socket changed; demand timed out']
        for runtime in ('codex','claude'):
            for message in messages:
                with self.subTest(runtime=runtime,message=message):
                    events=getattr(self,runtime)();notice={'type':'error','message':message,'future':{'extra':True}}
                    events.insert(-1,notice)
                    report=self.assert_completion(self.run_agent(runtime,events),'needs_review')
                    self.assertEqual(report['diagnostic_counts'],dict(errors=0,anomalies=1,warnings=0))
                    self.assert_output_diagnostic(report['anomalies'][0],str(notice),len(events)-1)
                    self.assertEqual(Path(report['logs']['output']).read_text(),
                        '\n'.join(json.dumps(e) for e in events)+'\n')
            events=getattr(self,runtime)();events[-1:-1]=[{'type':'error','message':m} for m in messages]
            report=self.assert_completion(self.run_agent(runtime,events,err='synthetic stderr\n'),'needs_review')
            self.assertEqual(report['diagnostic_counts']['anomalies'],len(messages)+1)

    def test_codex_startup_diagnostics_any_count_and_ancillary_shape(self):
        for count in (0,1,4,25):
            events=self.codex();events[1:1]=[
                {'type':'error','message':f'unknown startup {i}','extra':None} if i%2 else
                {'type':'item.completed','extra':False,'item':{'type':'error','id':f'd{i}',
                 'message':'new startup path or feature','metadata':[]}} for i in range(count)]
            report=self.assert_completion(self.run_collector(events),'needs_review' if count else 'passed')
            self.assertEqual(report['diagnostic_counts']['anomalies'],count)
            self.assertEqual(len(report['anomalies']),min(count,20))
            for i,d in enumerate(report['anomalies']):self.assert_output_diagnostic(d,str(events[i+1]),i+2)
        events=self.codex();events.insert(-1,{'type':'error','message':'after final'})
        self.assert_completion(self.run_collector(events),'needs_review')

    def test_codex_start_and_final_fences_apply_with_or_without_diagnostics(self):
        mutations={
            'missing-thread':lambda e:e.pop(0), 'missing-turn':lambda e:e.pop(1),
            'reversed':lambda e:e.__setitem__(slice(0,2),[e[1],e[0]]),
            'duplicate-thread':lambda e:e.insert(1,e[0].copy()),
            'different-thread':lambda e:e.insert(1,{'type':'thread.started','thread_id':'other'}),
            'duplicate-turn':lambda e:e.insert(2,{'type':'turn.started'}),
            'thread-extra':lambda e:e[0].update(status='completed'),
            'turn-extra':lambda e:e[1].update(usage={}),
            'missing-final':lambda e:e.pop(2),
            'blank-final':lambda e:e[2]['item'].update(text='  '),
            'nonstring-final':lambda e:e[2]['item'].update(text=[]),
            'missing-id':lambda e:e[2]['item'].pop('id'),
            'missing-text':lambda e:e[2]['item'].pop('text'),
            'blank-id':lambda e:e[2]['item'].update(id='  '),
            'wrong-id':lambda e:e[2]['item'].update(id=[]),
            'item-extra':lambda e:e[2]['item'].update(status='completed'),
            'envelope-extra':lambda e:e[2].update(metadata={}),
            'terminal-extra':lambda e:e[-1].update(stop_reason='completed'),
            'missing-terminal':lambda e:e.pop(),
            'duplicate-terminal':lambda e:e.append(e[-1].copy()),
            'failed-then-success':lambda e:e.insert(-1,{'type':'turn.failed','error':{'message':'failed'}}),
            'malformed-failed':lambda e:e.insert(-1,{'type':'turn.failed','error':'failed'}),
            'concatenated':lambda e:e.extend(self.codex()),
            'final-before-turn':lambda e:e.__setitem__(slice(1,3),[e[2],e[1]]),
            'final-after-terminal':lambda e:e.append(e[2].copy()),
        }
        for name,mutate in mutations.items():
            for diagnostic in (False,True):
                with self.subTest(name=name,diagnostic=diagnostic):
                    events=self.codex();mutate(events)
                    if diagnostic:events.insert(2,{'type':'error','message':'novel diagnostic'})
                    report=self.assert_completion(self.run_collector(events),'rejected','failed')
                    self.assertGreater(report['diagnostic_counts']['errors'],0)
                    if diagnostic:self.assertEqual(report['diagnostic_counts']['anomalies'],1)
        for frame in [self.codex()[2],{'type':'unknown'},{'type':'rate_limit_event'},
                      {'type':'item.started','item':{'type':'command_execution','id':'c'}}]:
            events=self.codex();events.insert(1,frame)
            self.assert_completion(self.run_collector(events),'rejected','failed')

    def test_codex_latest_message_owns_final_and_prose_is_unassessed(self):
        for text in ('new final','I cannot answer this request.','The answer seems incomplete.'):
            events=self.codex('earlier');events.insert(-1,{'type':'item.completed',
                'item':{'type':'agent_message','id':'last','text':text}})
            report=self.assert_completion(self.run_collector(events))
            self.assertEqual(report['final_answer'],text)
        for value in ('',None,42):
            events=self.codex('earlier');events.insert(-1,{'type':'item.completed',
                'item':{'type':'agent_message','id':'last','text':value}})
            self.assert_completion(self.run_collector(events),'rejected','failed')
        events=self.codex();events.insert(2,{'type':'item.completed','item':{'type':'agent_message','text':'bad'}})
        self.assert_completion(self.run_collector(events),'rejected','failed')

    def test_required_codex_diagnostics_remain_structural_errors(self):
        frames=[{'type':'error'},*[{'type':'error','message':v} for v in (None,42,[],{})],
                {'type':'item.completed','item':[]},
                {'type':'item.completed','item':{'type':'error','message':'missing id'}},
                {'type':'item.completed','item':{'type':'error','id':'','message':'bad id'}},
                {'type':'item.completed','item':{'type':'error','id':'e','message':42}}]
        for frame in frames:
            with self.subTest(frame=frame):
                events=self.codex();events.insert(2,frame)
                report=self.assert_completion(self.run_collector(events),'rejected')
                self.assertEqual(report['errors'][0]['line'],3)

    def test_claude_supported_native_completion_reasons(self):
        # Synthetic equivalents of saved CLI end_turn/stop_sequence protocol evidence.
        for reason in (None,'end_turn','stop_sequence'):
            for diagnostic in (False,True):
                events=self.claude();events[-1].update(stop_reason=reason,terminal_reason='completed',api_error_status=None)
                if diagnostic:events.insert(1,{'type':'error','message':'unknown recovered diagnostic'})
                report=self.assert_completion(self.run_agent('claude',events),'needs_review' if diagnostic else 'passed')
                self.assertEqual(report['terminal'],'success')
        self.assert_completion(self.run_collector(self.claude()[1:],runtime='claude'))

    def test_claude_native_negative_and_malformed_completion_overrides_success(self):
        reasons=['blocking_limit','rapid_refill_breaker','prompt_too_long','image_error','model_error',
                 'aborted_streaming','aborted_tools','stop_hook_prevented','hook_stopped','tool_deferred','max_turns']
        fields=[('terminal_reason',v) for v in reasons+[None,'','new-reason',0,False,[],{}]]
        fields += [('stop_reason',v) for v in ['content_filter','max_tokens','refusal','model_context_window_exceeded',
                   'tool_use','pause_turn','unknown','',False,42,[],{}]]
        fields += [('api_error_status',v) for v in (400,0,True,'500',[],{},1.2)]
        fields += [('errors',v) for v in (['native error'],[42],None,{},'error',False)]
        fields += [('deferred_tool_use',v) for v in (None,{},[],False,'tool')]
        fields += [('is_error',v) for v in (True,None,0,'false')]
        fields += [('subtype',v) for v in ('error','',None,[],{})]
        for normal in ('end_turn','stop_sequence'):
            for field,value in fields:
                with self.subTest(normal=normal,field=field,value=value):
                    events=self.claude();events[-1].update(stop_reason=normal,terminal_reason='completed')
                    events[-1][field]=value
                    events.insert(1,{'type':'error','message':'recovered intermediate'})
                    report=self.assert_completion(self.run_collector(events,runtime='claude'),'rejected','failed')
                    self.assertEqual(report['terminal'],'failed')
                    self.assertEqual(report['diagnostic_counts']['anomalies'],1)
        for field in ('is_error','subtype'):
            events=self.claude();events[-1].pop(field)
            self.assert_completion(self.run_collector(events,runtime='claude'),'rejected','failed')
        events=self.claude();events[-1]['errors']=[]
        self.assert_completion(self.run_collector(events,runtime='claude'))

    def test_claude_nonproof_diagnostics_accept_any_json_payload(self):
        values=[None,'','new-code',False,42,[],{'future':['novel']}]
        for value in values:
            frames=[{'type':'error','message':value,'ancillary':value},
                    self.assistant([{'type':'text','text':'intermediate'}],error=value),
                    {'type':'system','subtype':'api_retry','attempt':value,'max_retries':value,
                     'retry_delay_ms':value,'error_status':value,'error':value}]
            for frame in frames:
                with self.subTest(frame=frame):
                    events=self.claude();events.insert(1,frame)
                    report=self.assert_completion(self.run_collector(events,runtime='claude'),'needs_review')
                    self.assertEqual(report['final_answer'],'done')
                    self.assertEqual(report['diagnostic_counts'],dict(errors=0,anomalies=1,warnings=0))
                    self.assert_output_diagnostic(report['anomalies'][0],str(frame),2)
        for frame in ({'type':'error'},{'type':'system','subtype':'api_retry'}):
            events=self.claude();events.insert(1,frame)
            self.assert_completion(self.run_collector(events,runtime='claude'),'needs_review')
        events=self.claude();events.insert(1,self.assistant([],message_unused=True))
        self.assert_completion(self.run_collector(events,runtime='claude'))
        for reason in ('tool_use','max_tokens','refusal'):
            intermediate=self.assistant([{'type':'text','text':'intermediate API message'}],error='max_output_tokens')
            intermediate['message']['stop_reason']=reason
            events=self.claude();events.insert(1,intermediate)
            self.assert_completion(self.run_collector(events,runtime='claude'),'needs_review')

    def test_claude_result_owns_final_without_assistant_fallback(self):
        prior=self.assistant([{'type':'text','text':'partial root'}])
        for value in ('authoritative','', '  ', None,42,[]):
            events=self.claude();events.insert(1,prior);events[-1]['result']=value
            valid=isinstance(value,str) and bool(value.strip())
            report=self.assert_completion(self.run_collector(events,runtime='claude'),
                'passed' if valid else 'rejected','completed' if valid else 'failed')
            self.assertEqual(report['final_answer'],value if isinstance(value,str) else 'partial root')
        events=self.claude();events.insert(1,prior);events[-1].pop('result')
        self.assert_completion(self.run_collector(events,runtime='claude'),'rejected','failed')
        events=[prior]
        report=self.assert_completion(self.run_collector(events,runtime='claude'),'rejected','failed')
        self.assertEqual(report['final_answer'],'partial root')

    def test_claude_root_identity_init_order_and_diagnostic_identity(self):
        frames=[self.assistant([]),{'type':'user','message':{'content':[]}},
                {'type':'system','subtype':'api_retry'},{'type':'error'}]
        for frame in frames:
            for identity in ('root','other',None,42,'',[],{}):
                with self.subTest(frame=frame,identity=identity):
                    events=self.claude();events[0]['session_id']='root';events[-1]['session_id']='root'
                    events.insert(1,frame | {'session_id':identity})
                    valid=identity=='root';status=('needs_review' if frame['type'] in ('error','system') else 'passed')
                    report=self.assert_completion(self.run_collector(events,runtime='claude'),
                        status if valid else 'rejected','completed' if valid else 'failed')
                    self.assertEqual(report['session_id'],'root' if valid else None)
        for events in [self.claude()[:1]*2+self.claude()[1:],
                       [self.assistant([])]+self.claude()]:
            self.assert_completion(self.run_collector(events,runtime='claude'),'rejected','failed')
        events=self.claude();events[-1]['session_id']='only-result'
        report=self.assert_completion(self.run_collector(events,runtime='claude'))
        self.assertEqual(report['session_id'],'only-result')

    def test_claude_nested_ownership_and_scoped_tool_pairing(self):
        events=self.claude();events[0]['session_id']='root';events[-1]['session_id']='root'
        events[1:1]=[self.tool_call('parent',session_id='root'),self.tool_call('same',session_id='root'),
            self.tool_call('same',parent_tool_use_id='parent',session_id='child'),
            self.assistant([{'type':'text','text':'child text'}],parent_tool_use_id='parent',session_id='child'),
            {'type':'system','subtype':'api_retry','parent_tool_use_id':'parent','session_id':'child'},
            self.tool_result('same',parent_tool_use_id='parent',session_id='child'),
            self.tool_result('same',session_id='root'),self.tool_result('parent',session_id='root')]
        report=self.assert_completion(self.run_collector(events,runtime='claude'),'needs_review')
        self.assertEqual((report['session_id'],report['final_answer'],report['tool_results']),('root','done',3))
        events[6]['message']['content'][0]['is_error']=True
        events.insert(6,{'type':'error','parent_tool_use_id':'parent','session_id':'child','message':None})
        report=self.assert_completion(self.run_collector(events,runtime='claude'),'needs_review')
        self.assertEqual(report['diagnostic_counts']['anomalies'],3)
        self.assertEqual(report['session_id'],'root')
        # A root result cannot consume a child call with the same ID, or vice versa.
        for caller_parent,result_parent in [('parent',None),(None,'parent')]:
            events=self.claude();events[1:1]=[self.tool_call('parent'),self.tool_call('t',parent_tool_use_id=caller_parent),
                self.tool_result('t',parent_tool_use_id=result_parent)]
            report=self.assert_completion(self.run_collector(events,runtime='claude'),'rejected')
            self.assertTrue(any('parent scope' in d['message'] for d in report['errors']))
            self.assertTrue(any('without completion' in d['message'] for d in report['anomalies']))
        for parent in ('missing',42,'',[],{}):
            events=self.claude();events.insert(1,self.assistant([],parent_tool_use_id=parent))
            self.assert_completion(self.run_collector(events,runtime='claude'),'rejected','failed')
        for parent in ('parent',42,False,'',[],{}):
            events=self.claude();events.insert(1,self.tool_call('parent'));events[-1]['parent_tool_use_id']=parent
            self.assert_completion(self.run_collector(events,runtime='claude'),'rejected','failed')
        events=[self.tool_call('parent'),self.assistant([{'type':'text','text':'child only'}],parent_tool_use_id='parent')]
        report=self.assert_completion(self.run_collector(events,runtime='claude'),'rejected','failed')
        self.assertEqual(report['final_answer'],'')

    def test_claude_core_message_tool_shapes_remain_strict(self):
        frames=[{'type':'assistant'},self.assistant([],message=None),self.assistant([None]),self.assistant([{}]),
                self.assistant([{'type':[]}]),
                self.assistant([{'type':'text','text':42}]),
                self.assistant([{'type':'tool_use','id':[],'name':'Bash','input':{}}]),
                self.assistant([{'type':'tool_use','id':'t','name':42,'input':{}}]),
                self.assistant([{'type':'tool_use','id':'t','name':'Bash','input':[]}]),
                self.assistant([{'type':'tool_result','tool_use_id':42}]),
                self.assistant([{'type':'tool_result','tool_use_id':'t','is_error':1}]),
                self.tool_call('t'),self.tool_result('missing')]
        for frame in frames:
            events=self.claude();events.insert(1,frame)
            if frame==self.tool_call('t'):events.insert(2,frame)
            self.assert_completion(self.run_collector(events,runtime='claude'),'rejected')

    def test_terminal_order_and_trailing_metadata_cannot_change_proof(self):
        for runtime in ('codex','claude'):
            events=getattr(self,runtime)();events[-1]['usage']={'tokens':1}
            events.append({'type':'rate_limit_event','session_id':'other','usage':{'tokens':99},'result':'fake'})
            report=self.assert_completion(self.run_collector(events,runtime=runtime))
            self.assertEqual(report['usage'],{'tokens':1});self.assertEqual(report['final_answer'],'done')
            if runtime=='claude':
                events=self.claude('first');events.append(self.claude('overwrite')[-1] | {'session_id':'other'})
                report=self.assert_completion(self.run_collector(events,runtime=runtime),'rejected','failed')
                self.assertEqual(report['final_answer'],'first')
                self.assertIsNone(report['session_id'])
            for frame in [{'type':'error','message':'trailing'}, {'type':'unknown'},
                          self.assistant([{'type':'text','text':'overwrite'}]),getattr(self,runtime)()[0]]:
                with self.subTest(runtime=runtime,frame=frame):
                    events=getattr(self,runtime)()+[frame]
                    report=self.assert_completion(self.run_collector(events,runtime=runtime),'rejected','failed')
                    self.assertEqual(report['final_answer'],'done')
            for terminal in (getattr(self,runtime)()[-1],
                {'type':'turn.failed','error':{'message':'failed'}} if runtime=='codex' else
                {'type':'result','subtype':'error','is_error':True,'result':'partial'}):
                events=getattr(self,runtime)();events.insert(-1,terminal)
                report=self.assert_completion(self.run_collector(events,runtime=runtime),'rejected','failed')
                self.assertEqual(report['terminal'],'conflicting')
            events=getattr(self,runtime)()+['{"type":"rate_limit_event","x":NaN}']
            self.assert_completion(self.run_collector(events,runtime=runtime),'rejected')

    def test_parsing_damage_and_validation_do_not_erase_observed_completion(self):
        invalid=['not-json','[]','{}','{"type":42}', '{"type":"unknown","x":1,"x":2}',
                 '{"type":"unknown","x":Infinity}', '{"type":"unknown","x":1e400}',
                 '{"type":"unknown","x":"\\ud800"}', '{"type":"unknown","\\ud800":1}']
        for runtime in ('codex','claude'):
            for raw in invalid:
                events=getattr(self,runtime)();events.insert(-1,raw)
                report=self.assert_completion(self.run_collector(events,runtime=runtime),'rejected')
                self.assertEqual(report['errors'][0]['line'],len(events)-1)
                self.assertEqual(report['final_answer'],'done')
            # Invalid UTF-8 is a read failure; keep a serializable rejected report.
            output=self.root/'bad-utf8';output.write_bytes(b'\xff\n');stderr=self.root/'empty-stderr';stderr.write_text('')
            result=subprocess.run(['python3','-B',str(ROOT/'scripts/agent-run-result.py'),
                '--runtime',runtime,'--provider','synthetic','--output',str(output),'--stderr',str(stderr),
                '--exit-code','0','--runner-exit-code','0'],capture_output=True,text=True)
            self.assert_completion(result,'rejected','failed')

    def test_diagnostic_bounds_are_preserved_even_when_call_rejects(self):
        for runtime in ('codex','claude'):
            for failed in (False,True):
                events=getattr(self,runtime)();events[-1:-1]=[
                    {'type':'error','message':('Ω'*2500 if i==0 else f'unknown {i}')} for i in range(25)]
                if failed:events.pop()
                report=self.assert_completion(self.run_collector(events,runtime=runtime),
                    'rejected' if failed else 'needs_review','failed' if failed else 'completed')
                self.assertEqual(report['diagnostic_counts']['anomalies'],25)
                self.assertEqual(len(report['anomalies']),20);self.assertTrue(report['diagnostics_truncated'])
                self.assertTrue(report['anomalies'][0]['truncated'])
                for i,d in enumerate(report['anomalies']):
                    self.assertEqual(d['line'],len(getattr(self,runtime)())+i)
                    self.assertEqual(d['message_chars'],len(str(events[d['line']-1])))
                self.assertIn('unknown 24',Path(report['logs']['output']).read_text())

    def test_recovered_diagnostics_keep_selected_checks_for_both_runtimes(self):
        for runtime in ('codex','claude'):
            artifact=self.root/f'{runtime}-artifact';self.env['ARTIFACT_CONTENTS']=json.dumps({str(artifact):'CANARY=fresh-12345678\n'})
            events=getattr(self,runtime)();events.insert(-1,{'type':'error','message':'unknown recovered'})
            if runtime=='codex':
                events.insert(2,{'type':'item.completed','item':{'id':'read','type':'command_execution',
                    'command':f'cat {self.canary}','exit_code':0,'aggregated_output':self.canary.read_text()}})
            else:
                call=self.tool_call('read');call['message']['content'][0]['input']={'command':f'cat {self.canary}'}
                result=self.tool_result('read');result['message']['content'][0]['content']=self.canary.read_text()
                events[1:1]=[call,result]
            report=self.assert_completion(self.run_agent(runtime,events,'--artifact',str(artifact),
                '--canary-file',str(self.canary),'--canary-expected',str(self.expected)),'needs_review')
            self.assertTrue(report['canary_read_candidate']);self.assertEqual(report['canary_status'],'match')
            self.env.pop('ARTIFACT_CONTENTS')
            for text in ('CANARY=wrong','done'):
                bad=getattr(self,runtime)(text);bad.insert(-1,{'type':'error','message':'unknown'})
                self.assert_completion(self.run_agent(runtime,bad,'--canary-file',str(self.canary),
                    '--canary-expected',str(self.expected),final=text),'rejected')
            unreadable=self.root/f'{runtime}-unreadable';unreadable.write_text('token');unreadable.chmod(0)
            try:
                for expected in (self.root/'missing-expected',unreadable):
                    report=self.assert_completion(self.run_collector(events,'--canary-file',str(self.canary),
                        '--canary-expected',str(expected),runtime=runtime),'rejected')
                    self.assertEqual(report['canary_status'],'unknown')
            finally:unreadable.chmod(0o600)
            for args in [('--artifact',str(self.root/'missing')),('--artifact',str(self.root)),
                         ('--artifact',str(self.root/'collector.jsonl')),('--last-message',str(self.root/'missing-last'))]:
                self.assert_completion(self.run_collector(events,*args,runtime=runtime),'rejected')
            saved=self.root/f'{runtime}-stale-last';saved.write_text('stale')
            self.assert_completion(self.run_collector(events,'--last-message',str(saved),runtime=runtime),'rejected')

    def test_recovered_diagnostics_detail_keeps_raw_and_bypasses_checks(self):
        for runtime in ('codex','claude'):
            events=getattr(self,runtime)();events.insert(-1,{'type':'error','message':'new diagnostic'})
            raw='\n'.join(json.dumps(e) for e in events)+'\n'
            for code in (0,7):
                for redirected in (False,True):
                    output=self.root/f'{runtime}-detail-{code}';artifact=self.root/'missing-detail-artifact'
                    options=['--detail','--artifact',str(artifact),'--canary-file',str(self.canary),
                             '--canary-expected',str(self.expected)]
                    if redirected:options += ['--output',str(output)]
                    result=self.run_agent(runtime,events,*options,exit_code=code,err='detail diagnostic\n')
                    self.assertEqual(result.returncode,code)
                    self.assertEqual(result.stderr,'detail diagnostic\n')
                    self.assertEqual(result.stdout,'' if redirected else raw)
                    if redirected:self.assertEqual(output.read_text(),raw)

    def test_recovered_diagnostics_keep_native_and_postprocessing_failures(self):
        for runtime in ('codex','claude'):
            events=getattr(self,runtime)();events.insert(-1,{'type':'error','message':'unknown recovered'})
            report=self.assert_completion(self.run_agent(runtime,events,exit_code=7),'rejected','failed',7)
            self.assertEqual(report['runtime_exit_code'],7);self.assertEqual(report['diagnostic_counts']['anomalies'],1)
            self.assert_completion(self.run_collector(events,runtime=runtime,precollection=3),
                'rejected','failed',runner_code=3)
        for mode,phrase in [('missing','did not produce'),('raced','destination now exists'),('unwritable','cannot save')]:
            parent=self.root/f'zero-{mode}';parent.mkdir();last=parent/'last'
            key={'missing':'SKIP_LAST_MESSAGE','raced':'OCCUPY_LAST_MESSAGE','unwritable':'BREAK_LAST_PARENT'}[mode]
            self.env[key]='1' if mode=='missing' else str(last if mode=='raced' else parent)
            try:
                events=self.recovered_codex(notices=[{'type':'error','message':'unknown recovered'}])
                report=self.assert_completion(self.run_agent('codex',events,'--last-message',str(last)),'rejected','failed')
                self.assertEqual(report['runtime_exit_code'],0)
                self.assertIn(phrase,Path(report['logs']['stderr']).read_text())
            finally:self.env.pop(key)

    def test_invalid_canary_setup_never_invokes_runtime(self):
        capture=self.root/'capture';self.env['CAPTURE_ARGS']=str(capture)
        empty=self.root/'empty';empty.write_text('')
        whitespace=self.root/'whitespace';whitespace.write_text('bad token')
        unreadable=self.root/'unreadable';unreadable.write_text('unreadable');unreadable.chmod(0)
        missing=self.root/'missing'
        cases=[(missing,self.expected),(self.canary,missing),(self.root,self.expected),
               (self.canary,self.root),(empty,self.expected),(self.canary,empty),
               (self.canary,whitespace),(unreadable,self.expected),(self.canary,unreadable)]
        try:
            for runtime in ('codex','claude'):
                for canary,expected in cases:
                    result=self.run_agent(runtime,getattr(self,runtime)(),
                        '--canary-file',str(canary),'--canary-expected',str(expected))
                    self.assertEqual(result.returncode,2,result.stderr)
                    self.assertIn('invalid canary setup; runtime was not started',result.stderr)
                    self.assertFalse(capture.exists())
        finally:unreadable.chmod(0o600)

    def test_runtime_created_artifact_hard_links_are_rejected(self):
        original=self.root/'existing-source';original.write_text('existing content')
        for runtime in ('codex','claude'):
            for source_kind in ('output','stderr','existing'):
                output=self.root/f'{runtime}-{source_kind}.jsonl'
                stderr=self.root/f'{runtime}-{source_kind}.stderr'
                artifact=self.root/f'{runtime}-{source_kind}.artifact'
                source={'output':output,'stderr':stderr,'existing':original}[source_kind]
                self.env['ARTIFACT_LINKS']=json.dumps({str(artifact):str(source)})
                result=self.run_agent(runtime,getattr(self,runtime)(),
                    '--output',str(output),'--stderr',str(stderr),'--artifact',str(artifact))
                report=json.loads(result.stdout)
                self.assertEqual(result.returncode,1,result.stderr)
                self.assertEqual(report['runtime_exit_code'],0)
                self.assertEqual(report['validation_status'],'rejected')
                self.assertTrue(any('hard-linked or aliases a runner log' in e['message'] for e in report['errors']))
            self.env.pop('ARTIFACT_LINKS')

    def test_dash_destinations_require_detail_before_launch(self):
        capture=self.root/'capture';self.env['CAPTURE_ARGS']=str(capture)
        for runtime in ('codex','claude'):
            options=['--output','--stderr']+(['--last-message'] if runtime=='codex' else [])
            for option in options:
                result=self.run_agent(runtime,getattr(self,runtime)(),option,'-')
                self.assertEqual(result.returncode,2,result.stderr)
                self.assertIn(f'{option} - requires --detail',result.stderr)
                self.assertFalse(capture.exists())
                raw=self.run_agent(runtime,getattr(self,runtime)(),'--detail',option,'-')
                self.assertEqual(raw.returncode,0,raw.stderr)
                self.assertEqual(json.loads(raw.stdout.splitlines()[-1])['type'],
                                 'turn.completed' if runtime=='codex' else 'result')
                capture.unlink()

    def test_persist_and_resume_return_native_session_identity(self):
        capture=self.root/'capture';self.env['CAPTURE_ARGS']=str(capture)
        for runtime in ('codex','claude'):
            sid='native-session-id'
            events=getattr(self,runtime)()
            if runtime=='codex':events[0]['thread_id']=sid
            else:
                events[0]['session_id']=sid;events[-1]['session_id']=sid
            first=json.loads(self.run_agent(runtime,events,'--persist').stdout)
            self.assertEqual(first['session_id'],sid)
            args=json.loads(capture.read_text())
            self.assertNotIn('--ephemeral' if runtime=='codex' else '--no-session-persistence',args)
            resumed=self.run_agent(runtime,events,'--resume',first['session_id'])
            self.assertEqual(resumed.returncode,0,resumed.stderr)
            self.assertEqual(json.loads(resumed.stdout)['session_id'],sid)
            args=json.loads(capture.read_text())
            self.assertIn(sid,args)
            self.assertIn('resume' if runtime=='codex' else '--resume',args)

    def test_session_identity_missing_invalid_or_conflicting_stays_unavailable(self):
        for runtime in ('codex','claude'):
            for value in (None,42,[],{},'', '  '):
                events=getattr(self,runtime)()
                if runtime=='codex':events[0]['thread_id']=value
                else:
                    events[0]['session_id']=value;events[-1]['session_id']=value
                report=json.loads(self.run_agent(runtime,events).stdout)
                self.assertIsNone(report['session_id'])
                self.assertEqual(report['validation_status'],'rejected')
                self.assertEqual(report['agent_status'],'failed')
            events=getattr(self,runtime)()
            if runtime=='codex':events.insert(1,{'type':'thread.started','thread_id':'other'})
            else:
                events[0]['session_id']='first';events[-1]['session_id']='other'
            result=self.run_agent(runtime,events);report=json.loads(result.stdout)
            self.assertEqual(result.returncode,1,result.stderr)
            self.assertIsNone(report['session_id'])
            self.assertEqual(report['validation_status'],'rejected')
            self.assertEqual(report['agent_status'],'failed')
            self.assertTrue(any('conflicting runtime session' in a['message'] for a in report['errors']))

    def test_defaults_return_one_result_and_retain_private_raw_logs(self):
        for runtime in ('codex','claude'):
            result = self.run_agent(runtime, getattr(self,runtime)())
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['final_answer'], 'done')
            self.assertEqual(report['agent_status'], 'completed')
            self.assertEqual(report['validation_status'], 'passed')
            self.assertEqual(report['result_status'], 'not_assessed')
            for path in (report['logs']['output'],report['logs']['stderr']):
                self.assertEqual(Path(path).stat().st_mode & 0o777, 0o600)
            self.assertIn('type', Path(report['logs']['output']).read_text())

    def test_minimal_call_routes_and_generated_claude_identity(self):
        capture=self.root/'captured';self.env['CAPTURE_ARGS']=str(capture)
        for runtime in ('codex','claude'):
            result=self.run_agent(runtime,getattr(self,runtime)())
            self.assertEqual(result.returncode,0,result.stderr)
            args=json.loads(capture.read_text())
            if runtime=='claude':
                self.assertIn('--no-session-persistence',args)
                self.assertIn('--name',args)
                self.assertRegex(args[args.index('--name')+1],r'^ds-flash-[0-9a-f]{8}$')
            else:
                self.assertIn('--ephemeral',args)
            self.assertEqual(json.loads(result.stdout)['canary_status'],'not_run')

    def test_whitespace_prompts_and_directory_files_fail_before_runtime(self):
        capture=self.root/'captured';self.env['CAPTURE_ARGS']=str(capture)
        directory=self.root/'prompt-dir';directory.mkdir()
        blank=self.root/'blank';blank.write_text(' \t\r\n\v\f')
        for runtime in ('codex','claude'):
            for args,stdin in ((['--prompt',' \t\n'],None),(['--prompt','\u3000'],None),(['--prompt','\u00a0'],None),(['--prompt-file',str(blank)],None),
                               (['--prompt-file',str(directory)],None),([' \t\n'],None),([], ' \t\n')):
                result=subprocess.run([str(ROOT/f'scripts/{runtime}-agent-run'),'--provider',
                    'mimo' if runtime=='codex' else 'ds-flash','--cwd',str(ROOT),*args],
                    env=self.env,input=stdin,capture_output=True,text=True)
                self.assertEqual(result.returncode,2,result.stderr)
                self.assertFalse(capture.exists())

    def test_relative_runner_path_survives_workspace_change(self):
        workspace=self.root/'other-workspace';workspace.mkdir()
        for runtime in ('codex','claude'):
            result=self.run_agent(runtime,getattr(self,runtime)(),
                runner_path=Path('scripts')/f'{runtime}-agent-run',workdir=workspace)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['validation_status'],'passed')

    def test_overflow_numbers_never_escape_as_nonstandard_json(self):
        for runtime in ('codex','claude'):
            for number in ('1e400','-1e400'):
                for field in ('usage','modelUsage'):
                    events=getattr(self,runtime)()[:-1]
                    terminal=('{"type":"turn.completed",' if runtime=='codex' else
                        '{"type":"result","subtype":"success","is_error":false,"result":"done",')
                    events.append(terminal+'"'+field+'":{"nested":{"tokens":'+number+'}}}')
                    result=self.run_agent(runtime,events)
                    report=json.loads(result.stdout,parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
                    self.assertEqual(result.returncode,1,result.stderr)
                    self.assertEqual(report['validation_status'],'rejected')
                    self.assertIsNone(report['usage'])
                    self.assertEqual(report['runtime_metrics'],{})
                    self.assertTrue(any('finite float' in x['message'] for x in report['errors']))

    def test_lone_surrogates_reject_with_a_report_and_valid_unicode_survives(self):
        for runtime in ('codex','claude'):
            for field in ('final','usage','modelUsage','key'):
                events=getattr(self,runtime)('bad \ud800' if field=='final' else 'done')
                if field!='final':
                    events[-1]['usage' if field=='key' else field]=({'\ud800':0} if field=='key' else {'nested':['\ud800']})
                result=self.run_agent(runtime,events)
                self.assertEqual(result.returncode,1,result.stderr)
                self.assertNotIn('Traceback',result.stderr)
                report=json.loads(result.stdout)
                self.assertEqual(report['validation_status'],'rejected')
                self.assertTrue(any('surrogates not allowed' in e['message'] for e in report['errors']))
            events=getattr(self,runtime)('正常 😀')
            events[-1]['usage']={'label':'正常 😀','zero':0}
            result=self.run_agent(runtime,events)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(result.stdout)
            self.assertEqual(report['final_answer'],'正常 😀')
            self.assertEqual(report['usage'],events[-1]['usage'])

    def test_terminal_statistics_are_verbatim_and_wall_clock_measured(self):
        self.env['RUNTIME_DELAY']='0.15'
        for runtime in ('codex','claude'):
            events=getattr(self,runtime)()
            usage=({'input_tokens':123,'cached_input_tokens':0,'cache_write_input_tokens':45,
                    'output_tokens':67,'reasoning_output_tokens':8} if runtime=='codex' else
                   {'input_tokens':123,'cache_read_input_tokens':0,'cache_creation_input_tokens':45,
                    'output_tokens':67,'output_tokens_details':{'thinking_tokens':0}})
            events[-1]['usage']=usage
            if runtime=='claude':
                events.insert(1,{'type':'assistant','message':{'usage':{'input_tokens':999},'content':[]}})
                events.insert(1,{'type':'assistant','message':{'usage':{'input_tokens':999},'content':[]}})
                events[-1].update(duration_ms=0,duration_api_ms=12,total_cost_usd=0,
                    modelUsage={'fixture':{'inputTokens':123,'cacheReadInputTokens':0}})
            report=json.loads(self.run_agent(runtime,events).stdout)
            self.assertEqual(report['usage'],usage)
            self.assertGreaterEqual(report['wall_clock_seconds'],0.15)
            self.assertLess(report['wall_clock_seconds'],10)
            self.assertEqual(report['runtime_metrics'],
                {} if runtime=='codex' else {k:events[-1][k] for k in ('duration_ms','duration_api_ms','total_cost_usd','modelUsage')})

    def test_missing_malformed_failed_and_conflicting_terminal_metrics(self):
        for runtime in ('codex','claude'):
            for usage in (None,'42',42,[],{'nested':{'zero':0},'reported_string':'2'}):
                events=getattr(self,runtime)();events[-1]['usage']=usage
                report=json.loads(self.run_agent(runtime,events).stdout)
                self.assertEqual(report['usage'],usage if isinstance(usage,dict) else None)
            events=getattr(self,runtime)();events[-1]['usage']={'input_tokens':7}
            if runtime=='codex':events[-1].update(type='turn.failed',error={'message':'synthetic failure'})
            else:events[-1].update(subtype='error',is_error=True,duration_ms=5)
            report=json.loads(self.run_agent(runtime,events,exit_code=3).stdout)
            self.assertEqual(report['usage'],{'input_tokens':7})
            self.assertEqual(report['validation_status'],'rejected')
            events=getattr(self,runtime)();events[-1]['usage']={'input_tokens':7}
            for bad in (events[:-1], events+[events[-1]]):
                report=json.loads(self.run_agent(runtime,bad).stdout)
                self.assertIsNone(report['usage'])
                self.assertEqual(report['runtime_metrics'],{})
                self.assertEqual(report['validation_status'],'rejected')
        events=self.claude();events[-1].update(duration_ms='1',duration_api_ms=-2,total_cost_usd=True,modelUsage=[])
        report=json.loads(self.run_agent('claude',events).stdout)
        self.assertEqual(report['runtime_metrics'],{})

    def test_invalid_or_absent_elapsed_is_unavailable_without_rejection(self):
        output=self.root/'adapter.jsonl';output.write_text('\n'.join(json.dumps(e) for e in self.codex())+'\n')
        err=self.root/'adapter.stderr';err.write_text('')
        argv=['python3',str(ROOT/'scripts/agent-run-result.py'),'--runtime','codex','--provider','mimo',
              '--output',str(output),'--stderr',str(err),'--exit-code','0','--runner-exit-code','0']
        for value in (None,'not-a-time','-1','NaN','inf','0','1.25'):
            args=argv+([] if value is None else ['--wall-clock-seconds='+value])
            result=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['wall_clock_seconds'],float(value) if value in ('0','1.25') else None)

    def test_sync_installs_self_contained_result_adapter(self):
        installed=self.root/'installed'
        env=self.env | {'AGENT_RUN_BIN_DIR':str(installed), 'AGENT_TOOLS_TARGET':str(self.root/'installed-tools.zsh')}
        setup=subprocess.run(['bash',str(ROOT/'scripts/sync-agent-tools.sh')],env=env,capture_output=True,text=True)
        self.assertEqual(setup.returncode,0,setup.stderr)
        self.assertTrue((installed/'agent-run-result.py').is_file())
        for runtime in ('codex','claude'):
            result=self.run_agent(runtime,getattr(self,runtime)(),runner_path=installed/f'{runtime}-agent-run')
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['final_answer'],'done')

    def test_explicit_output_is_raw_but_stdout_is_summary(self):
        output = self.root/'raw.jsonl'
        result = self.run_agent('codex', self.codex(), '--output', str(output))
        self.assertEqual(json.loads(result.stdout)['final_answer'], 'done')
        self.assertIn('turn.completed', output.read_text())

    def test_detail_preserves_raw_stdout_and_redirection(self):
        for runtime in ('codex','claude'):
            events=getattr(self,runtime)()
            result=self.run_agent(runtime,events,'--detail',err='diagnostic\n')
            self.assertEqual(result.returncode,0)
            self.assertIn('"type"',result.stdout)
            self.assertNotIn('validation_status',result.stdout)
            self.assertIn('diagnostic',result.stderr)
        output=self.root/'detail.json'
        result=self.run_agent('claude',self.claude(),'--detail','--output',str(output))
        self.assertEqual(result.stdout,'')
        self.assertIn('result',output.read_text())
        events=self.recovered_codex('OK',startup=True)
        raw='\n'.join(json.dumps(e) for e in events)+'\n'
        for exit_code in (0,7):
            with self.subTest(startup_detail_exit=exit_code):
                result=self.run_agent('codex',events,'--detail',exit_code=exit_code,err='diagnostic\n')
                self.assertEqual(result.returncode,exit_code)
                self.assertEqual(result.stdout,raw)
                self.assertEqual(result.stderr,'diagnostic\n')
                output=self.root/f'startup-detail-{exit_code}.jsonl'
                result=self.run_agent('codex',events,'--detail','--output',str(output),exit_code=exit_code,err='diagnostic\n')
                self.assertEqual(result.returncode,exit_code)
                self.assertEqual(result.stdout,'')
                self.assertEqual(output.read_text(),raw)
                self.assertEqual(result.stderr,'diagnostic\n')

    def test_nonzero_process_preserves_partial_answer(self):
        result=self.run_agent('codex',self.codex('partial'),'--last-message',str(self.root/'last.md'),exit_code=7,final='partial')
        report=json.loads(result.stdout)
        self.assertEqual(result.returncode,7)
        self.assertEqual(report['runtime_exit_code'],7)
        self.assertEqual(report['agent_status'],'failed')
        self.assertEqual(report['final_answer'],'partial')
        self.assertEqual(report['validation_status'],'rejected')

    def test_tool_failures_need_adjudication_not_process_rejection(self):
        codex=self.codex(); codex.insert(2,{'type':'item.completed','item':{'id':'c','type':'command_execution','command':'rg no-match','exit_code':1,'status':'completed','aggregated_output':''}})
        claude=self.claude();claude[1:1]=[{'type':'assistant','message':{'content':[{'type':'tool_use','id':'t','name':'Bash','input':{'command':'rg no-match'}}]}},{'type':'user','message':{'content':[{'type':'tool_result','tool_use_id':'t','is_error':True,'content':'no matches'}]}}]
        for runtime,events in [('codex',codex),('claude',claude)]:
            result=self.run_agent(runtime,events)
            report=json.loads(result.stdout)
            self.assertEqual(result.returncode,0)
            self.assertEqual(report['validation_status'],'needs_review')
            self.assertEqual(report['agent_status'],'completed')
            self.assertEqual(report['tool_results'],1)
            self.assertTrue(report['anomalies'])

    def test_corrupt_missing_or_duplicate_terminal_rejected(self):
        fixtures=[self.codex()[:-1],self.codex()+['not-json'], self.codex()+[{'type':'turn.completed'}],['{"type":"turn.completed","type":"turn.failed"}'],['{"type":"turn.completed","x":NaN}'],[{'type':'turn.failed','error':{'message':'failed'}}]]
        for events in fixtures:
            result=self.run_agent('codex',events)
            self.assertEqual(result.returncode,1,result.stderr)
            self.assertEqual(json.loads(result.stdout)['validation_status'],'rejected')

    def test_canary_report_in_artifact_and_actual_tool_output(self):
        artifact=self.root/'review.md';self.env['ARTIFACT_CONTENTS']=json.dumps({str(artifact):'CANARY=fresh-12345678\n'})
        events=self.codex();events.insert(2,{'type':'item.completed','item':{'id':'c','type':'command_execution','command':f'cat {self.canary}','exit_code':0,'status':'completed','aggregated_output':self.canary.read_text()}})
        result=self.run_agent('codex',events,'--artifact',str(artifact),'--canary-file',str(self.canary),'--canary-expected',str(self.expected))
        report=json.loads(result.stdout)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(report['canary_status'],'match')
        self.assertTrue(report['canary_read_candidate'])
        self.assertEqual(report['validation_status'],'passed')

    def test_claimed_canary_without_tool_evidence_needs_review(self):
        result=self.run_agent('claude',self.claude('CANARY=fresh-12345678'),'--canary-file',str(self.canary),'--canary-expected',str(self.expected))
        report=json.loads(result.stdout)
        self.assertEqual(result.returncode,0)
        self.assertEqual(report['validation_status'],'needs_review')
        self.assertFalse(report['canary_read_candidate'])

    def test_canary_examples_are_not_reports_and_markdown_wrappers_are_safe(self):
        artifact=self.root/'review.md'
        self.env['ARTIFACT_CONTENTS']=json.dumps({str(artifact):
            'CANARY=fresh-12345678\nAn example: `CANARY=wrong`\n```text\nCANARY=old\n```\n'})
        result=self.run_agent('claude',self.claude('The example `CANARY=wrong` is invalid.'),
            '--artifact',str(artifact),'--canary-file',str(self.canary),'--canary-expected',str(self.expected))
        self.assertEqual(json.loads(result.stdout)['canary_status'],'match')
        for text in ('CANARY=`fresh-12345678`','`CANARY=fresh-12345678`','CANARY=fresh-12345678。'):
            result=self.run_agent('claude',self.claude(text),'--canary-file',str(self.canary),'--canary-expected',str(self.expected))
            self.assertEqual(json.loads(result.stdout)['canary_status'],'match',text)
        for text in ('CANARY=fresh-12345678-extra','CANARY=wrong','CANARY=fresh-12345678\nCANARY=wrong'):
            result=self.run_agent('claude',self.claude(text),'--canary-file',str(self.canary),'--canary-expected',str(self.expected))
            self.assertEqual(json.loads(result.stdout)['canary_status'],'mismatch',text)

    def test_artifacts_must_be_new_regular_files_and_not_log_aliases(self):
        stale=self.root/'stale.md';stale.write_text('old')
        directory=self.root/'existing-directory';directory.mkdir()
        alias=self.root/'alias.md';alias.symlink_to(stale)
        for path in (stale,directory,alias):
            result=self.run_agent('codex',self.codex(),'--artifact',str(path))
            self.assertEqual(result.returncode,2)
        log=self.root/'raw-log'
        result=self.run_agent('codex',self.codex(),'--output',str(log),'--artifact',str(log))
        self.assertEqual(result.returncode,2)

    def test_unrecognized_failed_item_and_incomplete_calls_require_adjudication(self):
        for event in ({'type':'item.started','item':{'id':'w','type':'web_search','status':'failed','error':'unavailable'}},
                      {'type':'item.updated','item':{'id':'w','type':'web_search','status':'failed','error':'unavailable'}},
                      {'type':'item.completed','item':{'id':'w','type':'web_search','status':'failed','error':'unavailable'}},
                      {'type':'item.started','item':{'id':'c','type':'command_execution','command':'cat missing','status':'in_progress'}}):
            events=self.codex();events.insert(2,event)
            result=self.run_agent('codex',events)
            report=json.loads(result.stdout)
            self.assertEqual(result.returncode,0)
            self.assertEqual(report['validation_status'],'needs_review')
            self.assertEqual(report['tool_evidence_scope'],'recorded_events_only')

    def test_long_single_diagnostic_marks_truncation_and_source(self):
        result=self.run_agent('codex',self.codex(),err='x'*2500+'\n')
        report=json.loads(result.stdout)
        self.assertTrue(report['diagnostics_truncated'])
        self.assertTrue(report['anomalies'][0]['truncated'])
        self.assertEqual(report['anomalies'][0]['stream'],'stderr')

    def test_failed_terminal_cannot_revert_to_success(self):
        events=self.codex();events.insert(-1,{'type':'turn.failed','error':{'message':'failure'}})
        result=self.run_agent('codex',events)
        report=json.loads(result.stdout)
        self.assertEqual(result.returncode,1)
        self.assertEqual(report['terminal'],'conflicting')
        self.assertEqual(report['agent_status'],'failed')

    def test_indented_nested_fences_and_html_examples_do_not_contaminate_proof(self):
        for example in ('    CANARY=wrong','        CANARY=wrong','\tCANARY=wrong',
                        '````text\n```\nCANARY=wrong\n```\n````', '<pre>\nCANARY=wrong\n</pre>',
                        '```text\n<pre>\n```\nCANARY=fresh-12345678'):
            for runtime in ('codex','claude'):
                result=self.run_agent(runtime,getattr(self,runtime)('CANARY=fresh-12345678\n'+example),
                    '--canary-file',str(self.canary),'--canary-expected',str(self.expected))
                self.assertEqual(json.loads(result.stdout)['canary_status'],'match',example)

    def test_canary_mismatch_locates_final_event_and_artifact_proof(self):
        result=self.run_agent('codex',self.codex('CANARY=wrong'),'--canary-file',str(self.canary),'--canary-expected',str(self.expected))
        error=json.loads(result.stdout)['errors'][0]
        self.assertEqual((error['stream'],error['line'],error['proof_line']),('output',3,1))
        good=self.root/'good.md';bad=self.root/'bad.md'
        self.env['ARTIFACT_CONTENTS']=json.dumps({str(good):'CANARY=fresh-12345678\n',str(bad):'intro\nCANARY=wrong\n'})
        result=self.run_agent('claude',self.claude(),'--artifact',str(good),'--artifact',str(bad),
            '--canary-file',str(self.canary),'--canary-expected',str(self.expected))
        error=json.loads(result.stdout)['errors'][0]
        self.assertEqual((error['stream'],error['line'],error['proof_line']),('artifact',2,2))
        self.assertEqual(Path(error['path']),bad.resolve())

    def test_wrong_canary_and_missing_artifact_reject(self):
        result=self.run_agent('codex',self.codex('CANARY=wrong'),'--canary-file',str(self.canary),'--canary-expected',str(self.expected),'--artifact',str(self.root/'missing.md'))
        report=json.loads(result.stdout)
        self.assertEqual(result.returncode,1)
        self.assertEqual(report['agent_status'],'completed')
        self.assertEqual(report['canary_status'],'mismatch')
        self.assertEqual(report['validation_status'],'rejected')

    def test_benign_diagnostics_and_other_stderr(self):
        result=self.run_agent('claude',self.claude(),err='[claude-code:unrecognized_model] {}\n')
        report=json.loads(result.stdout)
        self.assertEqual(report['validation_status'],'passed')
        self.assertEqual(len(report['warnings']),1)
        result=self.run_agent('codex',self.codex(),err='unrecognized_model: actual failure\n')
        self.assertEqual(json.loads(result.stdout)['validation_status'],'needs_review')

    def test_long_final_and_diagnostics_are_explicitly_truncated(self):
        result=self.run_agent('codex',self.codex('x'*15000),err='warning\n'*30)
        report=json.loads(result.stdout)
        self.assertEqual(len(report['final_answer']),12000)
        self.assertTrue(report['final_answer_truncated'])
        self.assertEqual(report['final_answer_chars'],15000)
        self.assertEqual(report['diagnostic_counts']['anomalies'],30)
        self.assertTrue(report['diagnostics_truncated'])
        self.assertIn('x'*15000,Path(report['logs']['output']).read_text())

    def test_bare_tool_objects_without_execution_need_task_judgment(self):
        for runtime in ('codex','claude'):
            for claim in ({'type':'tool_use','id':'fake','name':'Bash','input':{'command':'cat proof'}},
                          {'name':'exec_command','arguments':{'cmd':'cat proof'}}):
                result=self.run_agent(runtime,getattr(self,runtime)(json.dumps(claim)))
                self.assertEqual(result.returncode,0)
                self.assertEqual(json.loads(result.stdout)['validation_status'],'needs_review')

    def test_tool_syntax_is_ambiguous_but_ordinary_json_types_are_data(self):
        tool=json.dumps({'type':'tool_use','name':'Bash','input':{'command':'cat proof'}})
        for runtime in ('codex','claude'):
            for text in ('Called '+tool+' just now', '~~~json\n'+tool+'\n~~~', '```json\n'+tool+'\n```\nDone.'):
                result=self.run_agent(runtime,getattr(self,runtime)(text))
                self.assertEqual(result.returncode,0)
                self.assertEqual(json.loads(result.stdout)['validation_status'],'needs_review')
            for text in (json.dumps({'type':['a','b'],'answer':'done'}),'['*600+'0'+']'*600):
                result=self.run_agent(runtime,getattr(self,runtime)(text))
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(json.loads(result.stdout)['validation_status'],'passed')

    def test_legitimate_tool_example_is_delivered_and_cannot_replace_canary(self):
        text='示例：\n```json\n{"type":"tool_call","name":"read","input":{}}\n```'
        for runtime in ('codex','claude'):
            result=self.run_agent(runtime,getattr(self,runtime)(text),
                prompt='Give a tool-call JSON example; do not execute any tool.')
            report=json.loads(result.stdout)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(report['agent_status'],'completed')
            self.assertEqual(report['final_answer'],text)
            self.assertEqual(report['validation_status'],'needs_review')
            self.assertEqual(report['errors'],[])
            self.assertEqual(report['anomalies'][0]['stream'],'output')
            self.assertIsNotNone(report['anomalies'][0]['line'])
            result=self.run_agent(runtime,getattr(self,runtime)(text),
                '--canary-file',str(self.canary),'--canary-expected',str(self.expected))
            self.assertEqual(result.returncode,1)
            self.assertEqual(json.loads(result.stdout)['canary_status'],'mismatch')

    def test_runner_postprocessing_errors_and_original_runtime_code_are_retained(self):
        for mode, phrase in (('missing','did not produce'),('raced','destination now exists'),('unwritable','cannot save')):
            parent=self.root/mode;parent.mkdir();last=parent/'last.md'
            if mode=='missing':self.env['SKIP_LAST_MESSAGE']='1'
            elif mode=='raced':self.env['OCCUPY_LAST_MESSAGE']=str(last)
            else:self.env['BREAK_LAST_PARENT']=str(parent)
            result=self.run_agent('codex',self.codex(),'--last-message',str(last),exit_code=7)
            report=json.loads(result.stdout)
            self.assertEqual(result.returncode,7)
            self.assertEqual(report['runtime_exit_code'],7)
            self.assertIn(phrase,Path(report['logs']['stderr']).read_text())
            if mode!='missing':
                self.assertIn('final message retained at',Path(report['logs']['stderr']).read_text())
                self.assertEqual(Path(report['logs']['last_message']).read_text(),'done')
            for key in ('SKIP_LAST_MESSAGE','OCCUPY_LAST_MESSAGE','BREAK_LAST_PARENT'):self.env.pop(key,None)

    def test_stale_final_file_rejected(self):
        result=self.run_agent('codex',self.codex(),'--last-message',str(self.root/'last.md'),final='stale')
        self.assertEqual(result.returncode,1)
        self.assertIn('differs',json.loads(result.stdout)['errors'][0]['message'])

    def test_unsupported_collection_format_fails_before_model(self):
        for runtime in ('codex','claude'):
            result=self.run_agent(runtime,[], '--output-format','text')
            self.assertEqual(result.returncode,2)
            self.assertIn('requires --detail',result.stderr)


if __name__=='__main__': unittest.main()
