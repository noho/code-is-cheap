"""Exercise the public runners with deterministic runtime streams, no model requests."""
import importlib.util
import json
import math
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SERVER_RETRY_CASES = ((2, '4324720a-d6d1-4f28-ab30-43742ac44125'),
                      (3, '0e6e96e9-f41d-457f-8df2-0d8d4d366d47'))


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

    def run_collector(self, events, *args, native=0, precollection=0, err=''):
        output=self.root/'collector.jsonl';stderr=self.root/'collector.stderr'
        output.write_text('\n'.join(json.dumps(e) if isinstance(e,dict) else e for e in events)+'\n')
        stderr.write_text(err)
        return subprocess.run(['python3','-B',str(ROOT/'scripts/agent-run-result.py'),
            '--runtime','codex','--provider','mimo','--output',str(output),'--stderr',str(stderr),
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

    def assert_connection_result(self, result, events, recovered, status=None, reason=None, notices=None, expected_exit=None):
        report=json.loads(result.stdout)
        self.assert_report_contract(report)
        exit_code=(0 if recovered else 1) if expected_exit is None else expected_exit
        self.assertEqual(result.returncode,exit_code,result.stderr)
        self.assertEqual(report['runner_exit_code'],exit_code)
        self.assertEqual(report['validation_status'],status or ('passed' if recovered else 'rejected'))
        category='warnings' if recovered else 'errors'
        supported=[self.connection_notice(i) for i in range(1,6)] if notices is None else notices
        if notices is not None:
            self.assertTrue(notices)
            self.assertEqual([e for e in events if isinstance(e,dict) and e in supported],notices)
            failure_reason={'start':'start multiplicity, shape or initial frame order',
                'terminal':'terminal identity or shape','final':'final shape or order',
                'other collector':'other collector validation errors',
                'native or postprocessing':'native or postprocessing nonzero'}.get(reason,reason)
            if not recovered:self.assertIsNotNone(failure_reason)
            prefix=('Recovered Codex connection notice: ' if recovered else
                    f'Codex connection notice recovery not proven ({failure_reason}): ')
            self.assertEqual(sum(d['message'].startswith(prefix) for d in report[category]),len(notices))
            self.assertEqual(report['diagnostic_counts']['warnings'],len(notices) if recovered else 0)
        for line,event in enumerate(events,1):
            if isinstance(event,dict) and event in supported:
                matches=[d for d in report[category] if d['line']==line and event['message'] in d['message']]
                self.assertEqual(len(matches),1,(line,report[category]))
                self.assertEqual(matches[0]['stream'],'output')
                self.assertIn('Recovered Codex connection notice:' if recovered else 'recovery not proven',matches[0]['message'])
                if reason:self.assertIn(reason,matches[0]['message'])
                if notices is not None:self.assert_output_diagnostic(matches[0],prefix+str(event),line)
        if not recovered:
            self.assertFalse(any('Recovered Codex connection notice:' in d['message'] for d in report['warnings']))
        return report

    def assert_output_diagnostic(self, diagnostic, message, line):
        self.assertEqual(diagnostic, {'stream':'output','line':line,'message':message,
            'message_chars':len(message),'truncated':False,'path':None,'proof_line':None})

    def test_codex_server_retry_recovered_connection_notice(self):
        historical=[self.server_retry_notice(*case) for case in SERVER_RETRY_CASES]
        mixed=[historical[0],self.connection_notice(5),historical[1],historical[0]]
        cases=[('case10-pair',historical,False,False),
               ('case10-first',[historical[0]],False,False),
               ('case10-second',[historical[1]],False,False),('mixed-repeated',mixed,False,False)]
        cases += [(f'ascii-attempt-{i}',[self.server_retry_notice(i)],False,False) for i in range(1,6)]
        cases += [(f'startup-{startup}-tool-{tool}',historical,startup,tool)
                  for startup,tool in ((True,False),(False,True),(True,True))]
        for name,notices,startup,tool in cases:
            with self.subTest(name=name):
                events=self.recovered_codex('OK',startup=startup,notices=notices)
                failed_tool={'type':'item.completed','item':{'id':'failed-tool','type':'command_execution',
                    'command':'rg no-match','exit_code':1,'status':'completed','aggregated_output':''}}
                if tool:events.insert(-2,failed_tool)
                usage={'input_tokens':123,'cached_input_tokens':0,'output_tokens':7}
                events[-1]['usage']=usage
                last=self.root/f'{name}.last.md';stderr='fixture stderr\n' if tool else ''
                result=self.run_agent('codex',events,'--last-message',str(last),final='OK',err=stderr)
                report=self.assert_connection_result(result,events,True,
                    'needs_review' if startup or tool else 'passed',notices=notices)
                self.assertEqual(report['diagnostic_counts'],{'errors':0,'anomalies':int(startup)+2*int(tool),'warnings':len(notices)})
                self.assertEqual(report['errors'],[])
                self.assertEqual((report['runtime_exit_code'],report['agent_status'],report['terminal']),(0,'completed','turn.completed'))
                self.assertEqual((report['final_answer'],report['final_answer_chars'],report['final_answer_truncated']),('OK',2,False))
                self.assertEqual(report['session_id'],'test')
                self.assertEqual(report['usage'],usage)
                self.assertEqual((report['events'],report['tool_results']),(len(events),int(tool)))
                self.assertEqual(report['runtime_metrics'],{})
                self.assertFalse(report['diagnostics_truncated'])
                self.assertEqual(Path(report['logs']['output']).read_text(),'\n'.join(json.dumps(e) for e in events)+'\n')
                self.assertEqual(Path(report['logs']['stderr']).read_text(),stderr)
                self.assertEqual(Path(report['logs']['last_message']).read_text(),'OK')
                if startup:self.assert_output_diagnostic(report['anomalies'][0],str(events[1]['item']),2)
                if tool:self.assert_output_diagnostic(report['anomalies'][int(startup)],str(failed_tool['item']),len(events)-2)

    def test_codex_server_retry_notice_lookalikes_rejected(self):
        event=self.server_retry_notice();message=event['message']
        request_id='01234567-89ab-cdef-0123-456789abcdef'
        messages=[('prefix','x '+message),('suffix',message+' x'),('leading-space',' '+message),
            ('trailing-space',message+' '),('trailing-newline',message+'\n'),
            ('internal-newline',message.replace(' You can','\nYou can')),('case',message.lower()),
            ('wording',message.replace('An error occurred','A server error occurred')),
            ('url',message.replace('help.openai.com','help.example.com')),
            ('url-dot',message.replace('help.openai.com','helpXopenai.com')),
            ('punctuation',message.replace('persists.','persists!')),
            ('spacing',message.replace('You can','You  can')),('closing-paren',message[:-1]),
            ('unknown','unrelated failure'),('nonstring',42),('null',None),('list',[]),('dict',{})]
        messages += [(f'attempt-{attempt}',message.replace('1/5',f'{attempt}/5'))
                     for attempt in ('0','6','01','１','١')]
        messages += [(f'budget-{budget}',message.replace('1/5',f'1/{budget}')) for budget in ('6','05','５')]
        messages += [(f'uuid-{name}',message.replace(request_id,value)) for name,value in [
            ('missing',''),('uppercase',request_id.upper()),('nonhex',request_id.replace('a','g')),
            ('unicode-hex',request_id.replace('a','ａ')),('short-first',request_id[1:]),
            ('long-last',request_id+'f'),('short-middle',request_id.replace('89ab','89a')),
            ('missing-hyphen',request_id.replace('-','',1)),('wrong-hyphen',request_id.replace('-','_',1)),
            ('braces','{'+request_id+'}')]]
        cases=[(name,{'type':'error','message':value}) for name,value in messages]
        cases.append(('missing-message',{'type':'error'}))
        cases += [(f'extra-{key}',event | {key:None}) for key in ('code','metadata','status','error')]
        for name,unknown in cases:
            with self.subTest(name=name):
                events=self.codex();events.insert(2,unknown)
                result=self.run_collector(events);report=json.loads(result.stdout)
                self.assert_report_contract(report)
                self.assertEqual((result.returncode,report['runner_exit_code'],report['runtime_exit_code']),(1,1,0),result.stderr)
                self.assertEqual((report['validation_status'],report['agent_status']),('rejected','completed'))
                self.assertEqual(report['diagnostic_counts'],{'errors':1,'anomalies':0,'warnings':0})
                self.assertEqual(report['warnings'],[])
                self.assert_output_diagnostic(report['errors'][0],str(unknown),3)
        notices=[self.server_retry_notice(*case) for case in SERVER_RETRY_CASES]
        events=self.recovered_codex(notices=notices);unknown={'type':'error','message':'unrelated failure'}
        events.insert(-2,unknown)
        report=self.assert_connection_result(self.run_agent('codex',events),events,False,
            reason='other collector',notices=notices)
        self.assertEqual(report['diagnostic_counts'],{'errors':3,'anomalies':0,'warnings':0})
        self.assert_output_diagnostic(report['errors'][0],str(unknown),5)

    def test_codex_server_retry_notice_recovery_fences(self):
        notice=self.server_retry_notice(*SERVER_RETRY_CASES[0]);notices=[notice]
        cases=[]
        for name,index in (('thread',0),('turn',1)):
            events=self.recovered_codex(notices=notices);events.pop(index)
            cases.append((f'missing-{name}',events,notices,'start'))
            events=self.recovered_codex(notices=notices);events.insert(2,events[index].copy())
            cases.append((f'duplicate-{name}',events,notices,'start'))
            events=self.recovered_codex(notices=notices);events[index]['metadata']=None
            cases.append((f'malformed-{name}',events,notices,'start'))
        for identity in ('',None,42):
            events=self.recovered_codex(notices=notices);events[0]['thread_id']=identity
            cases.append((f'thread-id-{identity}',events,notices,'start'))
        mutations=[('reversed-starts',lambda e:e.insert(0,e.pop(1)),'start'),
            ('notice-before-turn',lambda e:e.insert(1,e.pop(2)),'start'),
            ('unknown-startup',lambda e:e.insert(1,{'type':'item.completed','item':{
                'id':'unknown','type':'error','message':'unknown warning'}}),'start')]
        # Build the multiple-startup case directly; both messages stay anomalies.
        events=self.recovered_codex(notices=notices);events[1:1]=[self.startup_diagnostic(),self.startup_diagnostic()]
        cases.append(('multiple-startup',events,notices,'start'))
        mutations += [('missing-final',lambda e:e.pop(-2),'final'),
            ('blank-final',lambda e:e[-2]['item'].update(text='  '),'final'),
            ('nonstring-final',lambda e:e[-2]['item'].update(text=None),'final'),
            ('malformed-final-envelope',lambda e:e[-2].update(item=[]),'final'),
            ('malformed-final-item',lambda e:e[-2]['item'].update(metadata=None),'final'),
            ('missing-final-id',lambda e:e[-2]['item'].pop('id'),'final'),
            ('final-before-notice',lambda e:e.insert(2,e.pop(-2)),'final'),
            ('missing-terminal',lambda e:e.pop(-1),'terminal'),
            ('failed-terminal',lambda e:e[-1].update(type='turn.failed'),'terminal'),
            ('duplicate-terminal',lambda e:e.append(e[-1].copy()),'terminal'),
            ('conflicting-terminal',lambda e:e.insert(-1,{'type':'turn.failed','error':'failed'}),'terminal'),
            ('malformed-terminal',lambda e:e[-1].update(metadata=None),'terminal'),
            ('final-after-terminal',lambda e:e.append(e.pop(-2)),'final'),
            ('event-after-terminal',lambda e:e.append({'type':'future.event'}),'other collector')]
        for name,mutate,reason in mutations:
            events=self.recovered_codex(notices=notices);mutate(events);cases.append((name,events,notices,reason))
        for name,index in (('notice-after-terminal',None),('final-before-last-notice',-1)):
            later=self.server_retry_notice(*SERVER_RETRY_CASES[1])
            events=self.recovered_codex(notices=notices)
            if index is None:events.append(later)
            else:events.insert(index,later)
            cases.append((name,events,[notice,later],'final'))
        for raw in ('not-json','{"type":"future.event","type":"other"}',
                    '{"type":"future.event","value":NaN}', '[]'):
            events=self.recovered_codex(notices=notices);events.insert(-2,raw)
            cases.append(('malformed-json-'+raw,events,notices,'other collector'))
        for name,events,expected,reason in cases:
            with self.subTest(name=name):
                report=self.assert_connection_result(self.run_collector(events),events,False,reason=reason,notices=expected)
                self.assertEqual(report['runtime_exit_code'],0)
                self.assertEqual(report['warnings'],[])
                self.assertEqual(report['diagnostic_counts']['errors'],len(report['errors']))
        historical=[self.server_retry_notice(*case) for case in SERVER_RETRY_CASES]
        events=self.recovered_codex(notices=historical)[:-2]
        report=self.assert_connection_result(self.run_collector(events),events,False,reason='terminal',notices=historical)
        self.assertEqual(report['diagnostic_counts'],{'errors':4,'anomalies':0,'warnings':0})
        events=self.claude();events.insert(1,notice)
        result=self.run_agent('claude',events);report=json.loads(result.stdout)
        self.assert_report_contract(report)
        self.assertEqual((result.returncode,report['runner_exit_code']),(1,1),result.stderr)
        self.assertEqual(report['validation_status'],'rejected')
        self.assertEqual(report['diagnostic_counts'],{'errors':1,'anomalies':0,'warnings':0})
        self.assert_output_diagnostic(report['errors'][0],str(notice),2)
        events=self.recovered_codex(notices=historical)
        for exit_code in (0,7):
            with self.subTest(detail_exit=exit_code):
                result=self.run_agent('codex',events,'--detail',exit_code=exit_code,err='raw stderr\n')
                self.assertEqual(result.returncode,exit_code,result.stderr)
                self.assertEqual(result.stdout,'\n'.join(json.dumps(e) for e in events)+'\n')
                self.assertEqual(result.stderr,'raw stderr\n')
                self.assertNotIn('validation_status',result.stdout)
                self.assertNotIn('Recovered Codex connection notice:',result.stdout)

    def test_codex_server_retry_notice_keeps_selected_checks(self):
        original=self.root
        for startup in (False,True):
            with self.subTest(startup=startup):
                self.root=original/f'server-selected-{startup}';self.root.mkdir()
                try:self.assert_codex_connection_selected_checks(startup,notices=[self.server_retry_notice()])
                finally:self.root=original

    def test_codex_server_retry_notice_keeps_process_failures(self):
        original=self.root
        for startup in (False,True):
            with self.subTest(startup=startup):
                self.root=original/f'server-process-{startup}';self.root.mkdir()
                try:self.assert_codex_connection_process_failures(startup,notices=[self.server_retry_notice()])
                finally:self.root=original

    def test_codex_startup_diagnostic_recovery_and_controls(self):
        evidence=ROOT/'docs/gateflow/codex-recovery-startup-diagnostics/evidence'
        controls=[('startup-warning-recovered.jsonl','needs_review',6,1,1,4),
                  ('adjacent-starts-recovered.jsonl','passed',5,0,1,3),
                  ('startup-warning-no-retry.jsonl','needs_review',5,1,0,None)]
        for name,status,count,anomalies,warnings,notice_line in controls:
            with self.subTest(control=name):
                raw=(evidence/name).read_text()
                events=[json.loads(line) for line in raw.splitlines()]
                result=self.run_collector(events,'--wall-clock-seconds','2698.161843')
                report=self.assert_connection_result(result,events,True,status)
                self.assertEqual(report['runtime_exit_code'],0)
                self.assertEqual((report['agent_status'],report['terminal']),('completed','turn.completed'))
                self.assertEqual(report['diagnostic_counts'],{'errors':0,'anomalies':anomalies,'warnings':warnings})
                self.assertEqual(report['errors'],[])
                self.assertEqual(report['events'],count)
                self.assertEqual((report['final_answer'],report['final_answer_chars'],report['final_answer_truncated']),('OK',2,False))
                self.assertEqual(report['session_id'],'synthetic-thread')
                self.assertEqual(report['tool_results'],0)
                self.assertEqual(report['runtime_metrics'],{})
                self.assertEqual(report['canary_status'],'not_run')
                self.assertEqual(report['artifacts'],[])
                self.assertFalse(report['diagnostics_truncated'])
                self.assertEqual(report['usage'],events[-1]['usage'])
                self.assertEqual(report['wall_clock_seconds'],2698.161843)
                self.assertEqual(Path(report['logs']['output']).read_text(),raw)
                self.assertEqual(Path(report['logs']['stderr']).read_text(),'')
                if anomalies:self.assert_output_diagnostic(report['anomalies'][0],str(events[1]['item']),2)
                if warnings:self.assert_output_diagnostic(report['warnings'][0],
                    'Recovered Codex connection notice: '+str(events[notice_line-1]),notice_line)

        events=self.recovered_codex(text='OK',startup=True)
        tool={'type':'item.completed','item':{'id':'tool','type':'command_execution',
            'command':'rg no-match','exit_code':1,'status':'completed','aggregated_output':''}}
        events.insert(3,tool)
        last=self.root/'combined.last.md'
        result=self.run_agent('codex',events,'--last-message',str(last),exit_code=0,err='',final='OK')
        report=self.assert_connection_result(result,events,True,'needs_review')
        self.assertEqual(last.read_text(),'OK')
        self.assertEqual(Path(report['logs']['last_message']),last.resolve())
        self.assertEqual((report['runtime_exit_code'],report['agent_status'],report['terminal']),(0,'completed','turn.completed'))
        self.assertEqual(report['diagnostic_counts'],{'errors':0,'anomalies':2,'warnings':1})
        self.assertEqual(report['errors'],[])
        self.assertEqual((report['events'],report['tool_results']),(7,1))
        for diagnostic,event,line in zip(report['anomalies'],[events[1],tool],[2,4]):
            self.assert_output_diagnostic(diagnostic,str(event['item']),line)
        self.assert_output_diagnostic(report['warnings'][0],'Recovered Codex connection notice: '+str(events[4]),5)
        self.assertEqual((report['final_answer'],report['final_answer_chars'],report['final_answer_truncated']),('OK',2,False))
        self.assertEqual(report['usage'],events[-1]['usage'])
        self.assertEqual(Path(report['logs']['output']).read_text(),'\n'.join(json.dumps(e) for e in events)+'\n')
        self.assertEqual(Path(report['logs']['stderr']).read_text(),'')

        paths=['/tmp/synthetic-codex/config.toml','/home/synthetic/.codex/config.toml',
               '/Users/synthetic/.codex/agent-homes/profile_1/config.toml','/a/config.toml',
               '/.../.profile-2_3/config.toml']
        identities=['startup-warning','other-id','  nonblank  ','0','告警']
        for index,(path,identity) in enumerate(zip(paths,identities)):
            for attempts in [(i,) for i in range(1,6)]+[(1,2,5)]:
                with self.subTest(path=path,identity=identity,attempts=attempts):
                    events=self.recovered_codex('OK',attempts,startup=True)
                    events[1]=self.startup_diagnostic(path,identity)
                    usage={'input_tokens':12345678,'cached_input_tokens':0,'output_tokens':7}
                    events[-1]['usage']=usage
                    last=self.root/f'variation-{index}-{attempts}.last.md'
                    report=self.assert_connection_result(self.run_agent('codex',events,
                        '--last-message',str(last),final='OK'),events,True,'needs_review')
                    self.assertEqual(report['diagnostic_counts'],{'errors':0,'anomalies':1,'warnings':len(attempts)})
                    self.assert_output_diagnostic(report['anomalies'][0],str(events[1]['item']),2)
                    self.assertEqual([d['line'] for d in report['warnings']],list(range(4,4+len(attempts))))
                    self.assertEqual((report['final_answer'],report['final_answer_chars'],report['final_answer_truncated']),('OK',2,False))
                    self.assertEqual(report['usage'],usage)
                    self.assertEqual(report['runtime_exit_code'],0)
                    self.assertTrue(math.isfinite(report['wall_clock_seconds']))
                    self.assertGreaterEqual(report['wall_clock_seconds'],0)
                    self.assertEqual(Path(report['logs']['output']).read_text(),'\n'.join(json.dumps(e) for e in events)+'\n')
                    self.assertEqual(Path(report['logs']['stderr']).read_text(),'')
                    self.assertEqual(Path(report['logs']['last_message']).read_text(),'OK')

    def test_codex_startup_diagnostic_lookalikes_do_not_bridge_gap(self):
        message=self.startup_diagnostic()['item']['message']
        messages=[('prefix','x '+message),('suffix',message+' x'),('leading-space',' '+message),
            ('trailing-space',message+' '),('newline',message+'\n'),('case',message.lower()),
            ('feature','other_feature'),('feature-list',message.replace('skip_host_skill_discovery','skip_host_skill_discovery, other')),
            ('feature-suffix',message.replace('skip_host_skill_discovery','skip_host_skill_discovery_extra')),
            ('feature-other',message.replace('skip_host_skill_discovery','other_feature')),
            ('explanation-omitted',message.replace('Under-development features are incomplete and may behave unpredictably. ','')),
            ('suppression-omitted',message.split(' To suppress')[0]),
            ('punctuation',message.replace('discovery.','discovery!')),
            ('setting',message.replace(' = true',' = false')),('spacing',message.replace(' in /',' in  /')),
            ('nonstring',42),('null',None),('list',[])]
        cases=[]
        for name,value in messages:
            event=self.startup_diagnostic();event['item']['message']=value;cases.append((name,event))
        for field in ('message','id','type'):
            event=self.startup_diagnostic();event['item'].pop(field);cases.append(('missing-item-'+field,event))
        for identity in ('','  ','\t\n',None,42,[],{}):
            event=self.startup_diagnostic(identity=identity);cases.append((f'id-{identity!r}',event))
        cases += [('missing-item',{'type':'item.completed'}),('null-item',{'type':'item.completed','item':None}),
                  ('list-item',{'type':'item.completed','item':[]}),('top-error',{'type':'error','message':message})]
        for kind in ('item.started','item.updated'):
            event=self.startup_diagnostic();event['type']=kind;cases.append((kind,event))
        for kind in ('agent_message','command_execution','unknown'):
            event=self.startup_diagnostic();event['item']['type']=kind;cases.append(('item-'+kind,event))
        for target in ('envelope','item'):
            for key in ('metadata','status','error','code'):
                for value in ('fixture',None):
                    event=self.startup_diagnostic();(event if target=='envelope' else event['item'])[key]=value
                    cases.append((f'{target}-extra-{key}-{value}',event))
        paths=['tmp/a/config.toml','~/a/config.toml','/config.toml','/a//config.toml','//a/config.toml',
            '/a/./config.toml','/a/../config.toml','/./a/config.toml','/../a/config.toml',
            '/a b/config.toml','/a\tb/config.toml','/a\nb/config.toml','/`a`/config.toml',
            '/"a"/config.toml',"/'a'/config.toml",'/中文/config.toml',r'C:\a\config.toml',
            r'/a\b/config.toml','https://example/a/config.toml','/a/other.toml','/a/Config.toml',
            '/a/config.TOML','/a/config.toml.bak','/a/config.toml/']
        cases += [('path-'+path,self.startup_diagnostic(path)) for path in paths]
        for name,value in [('missing-period',message[:-1]),('double-period',message+'.'),
                           ('unknown-text','Unknown warning in /a/config.toml.')]:
            event=self.startup_diagnostic();event['item']['message']=value;cases.append((name,event))
        for name,event in cases:
            with self.subTest(name=name):
                events=self.recovered_codex();events.insert(1,event)
                self.assert_connection_result(self.run_collector(events),events,False,
                    reason='start multiplicity, shape or initial frame order')
        unsupported=self.startup_diagnostic('/config.toml')
        events=self.codex();events.insert(1,unsupported)
        result=self.run_agent('codex',events);report=json.loads(result.stdout)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(report['validation_status'],'needs_review')
        self.assertEqual(report['diagnostic_counts'],{'errors':0,'anomalies':1,'warnings':0})
        self.assert_output_diagnostic(report['anomalies'][0],str(unsupported['item']),2)
        events=self.codex();events.insert(1,{'type':'error','message':message})
        result=self.run_agent('codex',events);report=json.loads(result.stdout)
        self.assertEqual(result.returncode,1,result.stderr)
        self.assertEqual(report['diagnostic_counts'],{'errors':1,'anomalies':0,'warnings':0})

    def test_codex_startup_diagnostic_gap_order_and_count(self):
        frames=[{'type':'future.nonproof'},{'type':'future.failed','message':'failure'},
            {'type':'rate_limit_event'},self.codex('premature')[2],
            {'type':'item.completed','item':{'id':'metadata','type':'error','message':'Model metadata for fixture not found'}},
            {'type':'item.completed','item':{'id':'unknown','type':'error','message':'unknown warning'}},
            {'type':'error','message':'unknown error'},self.connection_notice(2)]
        for kind in ('command_execution','mcp_tool_call','file_change'):
            for phase in ('item.started','item.completed'):
                frames.append({'type':phase,'item':{'id':'gap-tool','type':kind,'status':'completed'}})
        for frame in frames:
            for gap in ([frame],[frame,self.startup_diagnostic()],[self.startup_diagnostic(),frame]):
                with self.subTest(gap=gap):
                    events=self.recovered_codex();events[1:1]=gap
                    self.assert_connection_result(self.run_collector(events),events,False,reason='start multiplicity')
        for count in (0,1,2,25):
            for distinct in (False,True):
                with self.subTest(count=count,distinct=distinct):
                    gap=[self.startup_diagnostic(f'/tmp/profile_{i}/config.toml',f'warning-{i}')
                         if distinct else self.startup_diagnostic() for i in range(count)]
                    events=self.recovered_codex();events[1:1]=gap
                    accepted=count in (0,1)
                    report=self.assert_connection_result(self.run_collector(events),events,accepted,
                        status=('needs_review' if count else 'passed') if accepted else None,
                        reason=None if accepted else 'start multiplicity')
                    self.assertEqual(report['diagnostic_counts'],{'errors':int(not accepted),'anomalies':count,'warnings':int(accepted)})
                    self.assertEqual(len(report['anomalies']),min(count,20))
                    self.assertEqual(report['diagnostics_truncated'],count>20)
        cases=[]
        events=self.recovered_codex(startup=True);events.insert(0,self.startup_diagnostic())
        cases.append(('before-thread',events))
        for index,kind in [(0,'thread'),(2,'turn')]:
            events=self.recovered_codex(startup=True);events.pop(index);cases.append(('missing-'+kind,events))
            for place in (1,3,-2):
                events=self.recovered_codex(startup=True);events.insert(place,events[index].copy())
                cases.append((f'duplicate-{kind}-{place}',events))
            for field in ('metadata','status','error'):
                events=self.recovered_codex(startup=True);events[index][field]=None;cases.append((f'malformed-{kind}-{field}',events))
        for identity in (None,42,[],{},'','  '):
            events=self.recovered_codex(startup=True);events[0]['thread_id']=identity;cases.append((f'thread-id-{identity!r}',events))
        events=self.recovered_codex(startup=True);events[0].pop('thread_id');cases.append(('thread-id-missing',events))
        events=self.recovered_codex(startup=True);events[0],events[2]=events[2],events[0];cases.append(('reversed',events))
        for name,events in cases:
            with self.subTest(name=name):
                self.assert_connection_result(self.run_collector(events),events,False,reason='start multiplicity')
        for startup in (False,True):
            events=self.recovered_codex(startup=startup);events.insert(-2,self.startup_diagnostic())
            report=self.assert_connection_result(self.run_collector(events),events,True,'needs_review')
            self.assertEqual(report['diagnostic_counts']['anomalies'],1+int(startup))
        events=self.recovered_codex(startup=True);events.append(self.startup_diagnostic())
        report=self.assert_connection_result(self.run_collector(events),events,False,reason='other collector')
        self.assertTrue(any(d['message']=='event after runtime terminal' for d in report['errors']))
        events=self.recovered_codex(startup=True);events.insert(0,'');events.insert(2,'  ');events.insert(4,'\t')
        report=self.assert_connection_result(self.run_collector(events),events,True,'needs_review')
        self.assertEqual(report['events'],6)
        self.assert_output_diagnostic(report['anomalies'][0],str(self.startup_diagnostic()['item']),4)
        self.assertEqual(report['warnings'][0]['line'],7)
        corrupt=['not-json','{"type":"future.event","type":"other"}',
            '{"type":"future.event","value":NaN}','{"type":"future.event","value":Infinity}',
            '{"type":"future.event","value":1e400}',json.dumps({'type':'future.event','value':'\ud800'}),'[]']
        for raw in corrupt:
            for position in (1,2):
                with self.subTest(raw=raw,position=position):
                    events=self.recovered_codex(startup=True);events.insert(position,raw)
                    report=self.assert_connection_result(self.run_collector(events),events,False,reason='other collector')
                    errors=[d for d in report['errors'] if d['message'].startswith('invalid event:')]
                    self.assertEqual(len(errors),1)
                    self.assertEqual((errors[0]['stream'],errors[0]['line']),('output',position+1))
                    self.assertEqual(report['events'],6)
                    self.assertEqual(report['diagnostic_counts'],{'errors':2,'anomalies':1,'warnings':0})

    def test_codex_startup_diagnostic_keeps_recovery_fences(self):
        cases=[]
        for message in ('unknown failure',self.connection_notice()['message'].replace('stream closed','socket closed')):
            events=self.recovered_codex(startup=True);events.insert(-2,{'type':'error','message':message})
            cases.append(('unknown-error-'+message,events,'other collector'))
        for name,mutate,reason in [
            ('missing-terminal',lambda e:e.pop(-1),'terminal'),
            ('failed-terminal',lambda e:e[-1].update(type='turn.failed'),'terminal'),
            ('duplicate-terminal',lambda e:e.append(e[-1].copy()),'terminal'),
            ('conflicting-terminal',lambda e:e.insert(-1,{'type':'turn.failed','error':'failed'}),'terminal'),
            ('missing-final',lambda e:e.pop(-2),'final'),
            ('final-before-notice',lambda e:e.insert(3,e.pop(-2)),'final'),
            ('final-after-terminal',lambda e:e.append(e.pop(-2)),'final'),
            ('notice-after-terminal',lambda e:e.append(self.connection_notice(2)),'final')]:
            events=self.recovered_codex(startup=True);mutate(events);cases.append((name,events,reason))
        for target in ('terminal','final-envelope','final-item'):
            for key in ('metadata','status','error','code'):
                events=self.recovered_codex(startup=True)
                obj=events[-1] if target=='terminal' else events[-2] if target=='final-envelope' else events[-2]['item']
                obj[key]=None;cases.append((target+'-extra-'+key,events,'terminal' if target=='terminal' else 'final'))
        for field in ('id','text'):
            for value in ('','  ',None,42,[],{}):
                events=self.recovered_codex(startup=True);events[-2]['item'][field]=value
                cases.append((f'final-{field}-{value!r}',events,'final'))
            events=self.recovered_codex(startup=True);events[-2]['item'].pop(field);cases.append(('final-missing-'+field,events,'final'))
        for name,events,reason in cases:
            with self.subTest(name=name):
                self.assert_connection_result(self.run_collector(events),events,False,reason=reason)
        # An unsupported disconnect stays fatal even without any supported notice.
        events=self.recovered_codex(startup=True);events[3]['message']='stream disconnected before completion'
        result=self.run_collector(events);report=json.loads(result.stdout)
        self.assertEqual(result.returncode,1,result.stderr)
        self.assertEqual(report['validation_status'],'rejected')
        self.assertEqual(report['diagnostic_counts'],{'errors':1,'anomalies':1,'warnings':0})
        self.assert_output_diagnostic(report['errors'][0],str(events[3]),4)
        # No terminal/final after an exact retry cannot establish recovery.
        events=self.recovered_codex(startup=True)[:4]
        self.assert_connection_result(self.run_collector(events),events,False,reason='terminal')
        last=self.root/'mismatch.last.md';last.write_text('stale')
        events=self.recovered_codex(startup=True)
        report=self.assert_connection_result(self.run_collector(events,'--last-message',str(last)),events,False,reason='other collector')
        self.assertTrue(any('last-message differs' in d['message'] for d in report['errors']))
        for usage in ('omitted',None,42,[],{'input_tokens':0,'label':'fixture'}):
            with self.subTest(usage=usage):
                events=self.recovered_codex(startup=True)
                if usage=='omitted':events[-1].pop('usage')
                else:events[-1]['usage']=usage
                events.append({'type':'rate_limit_event','metadata':'allowed trailing event'})
                report=self.assert_connection_result(self.run_collector(events),events,True,'needs_review')
                self.assertEqual(report['usage'],usage if isinstance(usage,dict) else None)

    def test_codex_recovered_connection_notice(self):
        cases=[(f'attempt-{i}',self.recovered_codex(attempts=(i,)),'passed','') for i in range(1,6)]
        cases.append(('multiple-notices',self.recovered_codex(attempts=(1,2,5)),'passed',''))
        earlier=self.recovered_codex();earlier[2:2]=[self.codex('earlier one')[2],self.codex('earlier two')[2]]
        cases.append(('earlier-messages',earlier,'passed',''))
        anomaly=self.recovered_codex();anomaly.insert(-2,{'type':'item.completed','item':{
            'id':'tool','type':'command_execution','command':'fixture','exit_code':1,'aggregated_output':'no match'}})
        cases.append(('tool-and-stderr-anomalies',anomaly,'needs_review','fixture stderr\n'))
        other=self.recovered_codex();other.insert(3,{'type':'future.nonproof','metadata':{},'status':'new'})
        cases.append(('post-start-nonproof-kind',other,'passed',''))
        other=self.recovered_codex();other.insert(3,{'type':'future.failed','message':'fixture anomaly'})
        cases.append(('baseline-failed-kind-anomaly',other,'needs_review',''))
        for name,events,status,stderr in cases:
            with self.subTest(name=name):
                usage={'input_tokens':123,'cached_input_tokens':0,'output_tokens':7,'reasoning_output_tokens':2}
                events[-1]['usage']=usage
                result=self.run_agent('codex',events,'--last-message',str(self.root/f'{name}.last.md'),err=stderr)
                report=self.assert_connection_result(result,events,True,status)
                self.assertEqual(report['diagnostic_counts']['errors'],0)
                self.assertEqual(report['diagnostic_counts']['warnings'],sum(e.get('type')=='error' for e in events))
                self.assertEqual(report['agent_status'],'completed')
                self.assertEqual(report['runtime_exit_code'],0)
                self.assertEqual(report['terminal'],'turn.completed')
                self.assertEqual(report['final_answer'],'done')
                self.assertEqual(report['final_answer_chars'],4)
                self.assertFalse(report['final_answer_truncated'])
                self.assertEqual(report['usage'],usage)
                self.assertEqual(report['runtime_metrics'],{})
                self.assertEqual(report['session_id'],'test')
                self.assertEqual(report['events'],len(events))
                self.assertGreaterEqual(report['wall_clock_seconds'],0)
                self.assertEqual(Path(report['logs']['output']).read_text(),'\n'.join(json.dumps(e) for e in events)+'\n')
                self.assertEqual(Path(report['logs']['stderr']).read_text(),stderr)
                self.assertEqual(Path(report['logs']['last_message']).read_text(),'done')
                if name=='tool-and-stderr-anomalies':
                    self.assertEqual(report['tool_results'],1)
                    self.assertEqual(report['diagnostic_counts']['anomalies'],2)

    def test_codex_connection_notice_lookalikes_rejected(self):
        message=self.connection_notice()['message']
        messages=[('prefix','x '+message),('suffix',message+' x'),('newline',message+'\n'),
            ('leading-space',' '+message),('case',message.lower()),
            ('transport',message.replace('stream closed','socket closed')),
            ('budget',message.replace('1/5','1/6')),('attempt-zero',message.replace('1/5','0/5')),
            ('attempt-six',message.replace('1/5','6/5')),('attempt-wide',message.replace('1/5','01/5')),
            ('unicode-digit',message.replace('1/5','１/5')),
            ('nonstring',42),('null',None),('array',[])]
        cases=[(name,{'type':'error','message':value}) for name,value in messages]+[('missing',{'type':'error'})]
        cases += [(f'notice-extra-field-{key}',self.connection_notice() | {key:'fixture'})
                  for key in ('code','metadata','status','error')]
        for name,event in cases:
            with self.subTest(name=name):
                events=self.codex();events.insert(2,event)
                result=self.run_agent('codex',events);report=json.loads(result.stdout)
                self.assertEqual(result.returncode,1,result.stderr)
                self.assertEqual(report['validation_status'],'rejected')
                self.assertEqual(report['diagnostic_counts'],{'errors':1,'anomalies':0,'warnings':0})
                self.assertEqual(report['errors'][0]['line'],3)
                self.assertEqual(report['errors'][0]['message'],str(event))
        for count in (1,25):
            with self.subTest(name=f'arbitrary-after-{count}-candidates'):
                events=self.recovered_codex(attempts=(1,)*count)
                events.insert(-2,{'type':'error','message':'unrelated failure'})
                result=self.run_agent('codex',events);report=json.loads(result.stdout)
                self.assertEqual(result.returncode,1,result.stderr)
                self.assertEqual(report['diagnostic_counts']['errors'],count+1)
                self.assertEqual(report['diagnostic_counts']['warnings'],0)
                self.assertTrue(any('unrelated failure' in d['message'] for d in report['errors']))
                self.assertTrue(any('other collector validation errors' in d['message'] for d in report['errors']))

    def test_codex_connection_notice_supported_shape_fence(self):
        cases=[]
        for name,index in [('thread-start',0),('turn-start',1),('terminal',-1),('final-envelope',-2),('final-item',-2)]:
            for field in ('metadata','status','error'):
                events=self.recovered_codex()
                target=events[index]['item'] if name=='final-item' else events[index]
                target[field]='fixture'
                cases.append((f'{name}-extra-field-{field}',events))
        events=self.recovered_codex();events.insert(0,{'type':'rate_limit_event'})
        cases.append(('preamble-before-thread-start',events))
        events=self.recovered_codex();events.insert(1,self.codex('earlier')[2])
        cases.append(('item-between-starts',events))
        for name,events in cases:
            with self.subTest(name=name):
                reason='start' if name.startswith(('thread','turn','preamble','item-between')) else 'terminal' if name.startswith('terminal') else 'final'
                report=self.assert_connection_result(self.run_agent('codex',events),events,False,reason=reason)
                control=[e for e in events if e != self.connection_notice()]
                result=self.run_agent('codex',control);ordinary=json.loads(result.stdout)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(ordinary['validation_status'],'passed')
                for key in ('final_answer','final_answer_chars','session_id','usage','terminal'):
                    self.assertEqual(ordinary[key],report[key])
                self.assertEqual(ordinary['diagnostic_counts'],{'errors':0,'anomalies':0,'warnings':0})

    def test_codex_connection_notice_mixed_order_rejected(self):
        events=self.recovered_codex();events.insert(-1,self.connection_notice(2))
        report=self.assert_connection_result(self.run_agent('codex',events),events,False,reason='final')
        self.assertEqual(report['agent_status'],'completed')
        self.assertEqual(report['diagnostic_counts'],{'errors':2,'anomalies':0,'warnings':0})
        self.assertEqual([d['line'] for d in report['errors']],[3,5])

    def test_codex_connection_notice_requires_same_execution_completion(self):
        cases=[]
        for name,index in [('thread',0),('turn',1)]:
            events=self.recovered_codex();events.pop(index)
            cases.append((f'missing-{name}-start',events,'start'))
            for duplicate in ([self.codex()[index], self.codex()[index] | {'metadata':'invalid'}]
                              + ([{'type':'thread.started'}, {'type':'thread.started','thread_id':'other'}]
                                 if name=='thread' else [])):
                events=self.recovered_codex();events.insert(2,duplicate)
                cases.append((f'duplicate-{name}-{duplicate}',events,'start'))
        events=self.recovered_codex();events[0].pop('thread_id')
        cases.append(('missing-thread-identity',events,'start'))
        for identity in (None,42,[],{},'', '  '):
            events=self.recovered_codex();events[0]['thread_id']=identity
            cases.append((f'invalid-thread-identity-{identity}',events,'start'))
        events=self.recovered_codex();events[0],events[1]=events[1],events[0]
        cases.append(('starts-reversed',events,'start'))
        events=self.recovered_codex();events.insert(0,{'type':'orphan.fixture'})
        cases.append(('orphan-prefix',events,'start'))
        events=self.recovered_codex();events.insert(1,events.pop(2))
        cases.append(('notice-before-turn',events,'start'))
        events=self.recovered_codex();events[2],events[3]=events[3],events[2]
        cases.append(('final-only-before-notice',events,'final'))
        events=self.recovered_codex();events.pop(-2)
        cases.append(('missing-final',events,'final'))
        for text in ('', '  ',None,42,[]):
            events=self.recovered_codex();events[-2]['item']['text']=text
            cases.append((f'invalid-final-text-{text}',events,'final'))
        for identity in (None,42,[],{},'', '  '):
            events=self.recovered_codex();events[-2]['item']['id']=identity
            cases.append((f'invalid-final-id-{identity}',events,'final'))
        for name,mutation in [('missing-id',lambda e:e[-2]['item'].pop('id')),
                              ('unknown-final-kind',lambda e:e[-2]['item'].update(type='unknown_message')),
                              ('invalid-final-envelope',lambda e:e[-2].update(item=[]))]:
            events=self.recovered_codex();mutation(events);cases.append((name,events,'final'))
        cases.append(('missing-terminal',self.recovered_codex()[:-1],'terminal'))
        events=self.recovered_codex();events[-1]['type']='turn.failed'
        cases.append(('failed-terminal',events,'terminal'))
        events=self.recovered_codex();events.append(events[-1].copy())
        cases.append(('duplicate-terminal',events,'terminal'))
        events=self.recovered_codex();events.insert(-1,{'type':'turn.failed','error':'failed'})
        cases.append(('conflicting-terminal',events,'terminal'))
        events=self.recovered_codex();events[-2],events[-1]=events[-1],events[-2]
        cases.append(('final-after-terminal',events,'final'))
        events=self.recovered_codex();events.append(self.connection_notice(2))
        cases.append(('notice-after-terminal',events,'final'))
        events=self.recovered_codex();events.append({'type':'future.event'})
        cases.append(('event-after-terminal',events,'other collector'))
        corrupt=['not-json','{"type":"future.event","type":"other"}',
                 '{"type":"future.event","value":NaN}', '{"type":"future.event","value":Infinity}',
                 '{"type":"future.event","value":1e400}',
                 json.dumps({'type':'future.event','value':'\ud800'}), '[]']
        for index,raw in enumerate(corrupt):
            events=self.recovered_codex();events.insert(-2,raw)
            cases.append((f'malformed-event-{index}',events,'other collector'))
        for name,events,reason in cases:
            with self.subTest(name=name):
                self.assert_connection_result(self.run_agent('codex',events),events,False,reason=reason)
        # Strict text parsing rejects these rows before start proof bookkeeping.
        for kind,field in [('thread.started','thread_id'),('turn.started','metadata')]:
            raw=json.dumps({'type':kind,field:'\ud800'})
            for position,index,line in [('before-final',-2,4),('after-final',-1,5)]:
                with self.subTest(name=f'parser-rejected-duplicate-{kind}-{position}'):
                    events=self.recovered_codex();events.insert(index,raw)
                    report=self.assert_connection_result(self.run_agent('codex',events),events,
                        False,reason='other collector validation errors')
                    parser_errors=[d for d in report['errors'] if d['message'].startswith('invalid event:')]
                    self.assertEqual(len(parser_errors),1,report['errors'])
                    self.assertEqual((parser_errors[0]['stream'],parser_errors[0]['line']),('output',line))
                    self.assertIn('surrogates not allowed',parser_errors[0]['message'])
                    self.assertEqual(report['diagnostic_counts'],{'errors':2,'anomalies':0,'warnings':0})
                    self.assertEqual(report['events'],5)
                    self.assertEqual(report['runtime_exit_code'],0)
                    self.assertEqual(report['agent_status'],'completed')
                    self.assertEqual(report['terminal'],'turn.completed')
                    self.assertEqual(report['final_answer'],'done')
        for usage in ('omitted',None,42,[],{'input_tokens':0,'label':'fixture'}):
            with self.subTest(name=f'usage-not-proof-{usage}'):
                events=self.recovered_codex()
                if usage=='omitted':events[-1].pop('usage')
                else:events[-1]['usage']=usage
                events.append({'type':'rate_limit_event','metadata':'allowed trailing event'})
                report=self.assert_connection_result(self.run_agent('codex',events),events,True)
                self.assertEqual(report['usage'],usage if isinstance(usage,dict) else None)
        events=self.recovered_codex();events.insert(0,'');events.insert(2,'  ')
        self.assert_connection_result(self.run_agent('codex',events),events,True)

    def test_codex_connection_notice_keeps_selected_checks(self):
        self.assert_codex_connection_selected_checks(startup=False)

    def test_codex_startup_diagnostic_keeps_selected_checks(self):
        self.assert_codex_connection_selected_checks(startup=True)

    def assert_codex_connection_selected_checks(self, startup, notices=None):
        artifact=self.root/'new-review.md'
        self.env['ARTIFACT_CONTENTS']=json.dumps({str(artifact):'CANARY=fresh-12345678\n'})
        events=self.recovered_codex(startup=startup,notices=notices);events.insert(-2,{'type':'item.completed','item':{
            'id':'read','type':'command_execution','command':f'cat {self.canary}',
            'exit_code':0,'aggregated_output':self.canary.read_text()}})
        result=self.run_agent('codex',events,'--artifact',str(artifact),
            '--canary-file',str(self.canary),'--canary-expected',str(self.expected),
            '--last-message',str(self.root/'matching-last.md'))
        report=self.assert_connection_result(result,events,True,'needs_review' if startup else 'passed',notices=notices)
        self.assertEqual(report['canary_status'],'match')
        self.assertTrue(report['canary_read_candidate'])
        self.assertEqual(report['artifacts'],[{'path':str(artifact.resolve()),'exists':True,'regular_file':True}])
        self.assertEqual(report['tool_results'],1)
        self.assertEqual(report['runtime_exit_code'],0)
        self.assertEqual(report['diagnostic_counts'],{'errors':0,'anomalies':int(startup),'warnings':1})
        if startup:self.assert_output_diagnostic(report['anomalies'][0],str(events[1]['item']),2)
        self.env.pop('ARTIFACT_CONTENTS')
        for name,text in [('mismatch','CANARY=wrong'),('missing-proof','done')]:
            with self.subTest(name=name):
                bad=self.recovered_codex(text,startup=startup,notices=notices)
                result=self.run_agent('codex',bad,'--canary-file',str(self.canary),
                    '--canary-expected',str(self.expected),final=text)
                report=self.assert_connection_result(result,bad,False,reason='other collector',notices=notices)
                self.assertEqual(report['canary_status'],'mismatch')
                self.assertTrue(any('canary proof does not match' in d['message'] if name=='mismatch'
                    else 'missing standalone canary' in d['message'] for d in report['errors']))
        unreadable=self.root/'unreadable-expected';unreadable.write_text('fresh-12345678');unreadable.chmod(0)
        try:
            for path in (self.root/'missing-expected',unreadable):
                with self.subTest(name=f'expected-{path.name}'):
                    result=self.run_collector(events,'--canary-file',str(self.canary),'--canary-expected',str(path))
                    report=self.assert_connection_result(result,events,False,reason='other collector',notices=notices)
                    self.assertEqual(report['canary_status'],'unknown')
        finally:unreadable.chmod(0o600)
        for name,options in [('missing-artifact',['--artifact',str(self.root/'missing-artifact')]),
                             ('directory-artifact',['--artifact',str(self.root)]),
                             ('log-alias',['--artifact',str(self.root/'collector.jsonl')]),
                             ('missing-last',['--last-message',str(self.root/'missing-last')])]:
            with self.subTest(name=name):
                report=self.assert_connection_result(self.run_collector(events,*options),events,False,reason='other collector',notices=notices)
                self.assertGreater(report['diagnostic_counts']['errors'],1)
        result=self.run_agent('codex',events,'--last-message',str(self.root/'stale-last.md'),final='stale')
        report=self.assert_connection_result(result,events,False,reason='other collector',notices=notices)
        self.assertTrue(any('last-message differs' in d['message'] for d in report['errors']))
        output=self.root/'hard-link-output';linked=self.root/'hard-link-artifact'
        self.env['ARTIFACT_LINKS']=json.dumps({str(linked):str(output)})
        result=self.run_agent('codex',events,'--output',str(output),'--artifact',str(linked))
        report=self.assert_connection_result(result,events,False,reason='other collector',notices=notices)
        self.assertTrue(any('hard-linked or aliases' in d['message'] for d in report['errors']))
        self.env.pop('ARTIFACT_LINKS')
        capture=self.root/'prelaunch-capture';self.env['CAPTURE_ARGS']=str(capture)
        for options in (['--canary-file',str(self.canary),'--canary-expected',str(self.root/'missing-expected')],
                        ['--artifact',str(artifact)]):
            with self.subTest(name=f'prelaunch-{options[0]}'):
                result=self.run_agent('codex',events,*options)
                self.assertEqual(result.returncode,2,result.stderr)
                self.assertFalse(capture.exists())

    def test_codex_connection_notice_keeps_process_failures(self):
        self.assert_codex_connection_process_failures(startup=False)

    def test_codex_startup_diagnostic_keeps_process_failures(self):
        self.assert_codex_connection_process_failures(startup=True)

    def assert_codex_connection_process_failures(self, startup, notices=None):
        events=self.recovered_codex(startup=startup,notices=notices)
        result=self.run_agent('codex',events,exit_code=7);report=json.loads(result.stdout)
        self.assertEqual(result.returncode,7,result.stderr)
        self.assertEqual(report['runtime_exit_code'],7)
        self.assertEqual(report['runner_exit_code'],7)
        self.assertEqual(report['agent_status'],'failed')
        self.assertEqual(report['validation_status'],'rejected')
        self.assertEqual(report['diagnostic_counts']['warnings'],0)
        self.assertEqual(report['diagnostic_counts']['anomalies'],int(startup))
        self.assertTrue(any('native or postprocessing nonzero' in d['message'] for d in report['errors']))
        if notices is not None:
            self.assert_connection_result(result,events,False,reason='native or postprocessing',
                notices=notices,expected_exit=7)
        for mode,phrase in [('missing','did not produce'),('raced','destination now exists'),('unwritable','cannot save')]:
            with self.subTest(name=mode):
                parent=self.root/f'recovered-{mode}';parent.mkdir();last=parent/'last.md'
                key={'missing':'SKIP_LAST_MESSAGE','raced':'OCCUPY_LAST_MESSAGE','unwritable':'BREAK_LAST_PARENT'}[mode]
                self.env[key]='1' if mode=='missing' else str(last if mode=='raced' else parent)
                try:
                    result=self.run_agent('codex',events,'--last-message',str(last))
                    report=self.assert_connection_result(result,events,False,reason='native or postprocessing',notices=notices)
                    self.assertEqual(report['runtime_exit_code'],0)
                    self.assertEqual(report['agent_status'],'failed')
                    self.assertIn(phrase,Path(report['logs']['stderr']).read_text())
                    self.assertTrue(any('runner postprocessing failed' in d['message'] for d in report['errors']))
                finally:self.env.pop(key)
        result=self.run_collector(events,native=0,precollection=1)
        report=self.assert_connection_result(result,events,False,reason='native or postprocessing',notices=notices)
        self.assertEqual(report['agent_status'],'failed')
        self.assertEqual(report['runtime_exit_code'],0)
        self.assertEqual(report['runner_exit_code'],1)

    def test_codex_connection_notice_diagnostic_bounds(self):
        self.assert_codex_connection_diagnostic_bounds(startup=False)

    def test_codex_startup_diagnostic_diagnostic_bounds(self):
        self.assert_codex_connection_diagnostic_bounds(startup=True)

    def assert_codex_connection_diagnostic_bounds(self, startup):
        cases=[('unsaturated-success-25',0,True,False),('unsaturated-failure-25',0,False,True),
            ('saturated-success-20-old-25-notices',20,True,False),
            ('saturated-failure-20-old-25-notices',20,False,False),
            ('overflowed-failure-23-old-25-notices',23,False,False),
            ('one-slot-success-19-old-25-notices',19,True,False)]
        for name,old_count,recovered,early_final in cases:
            with self.subTest(name=name):
                old=[{'type':'item.completed','item':{'id':f'old-{i}','type':'error',
                        'message':f'Model metadata for fixture not found old-{i}'}} if recovered else
                     {'type':'error','message':f'old-error-{i}'} for i in range(old_count)]
                notices=[self.connection_notice((i%5)+1) for i in range(25)]
                events=self.codex()[:2]+old+([self.codex()[2]] if early_final else [])+notices
                events+=([self.codex()[-1]] if early_final else self.codex()[2:])
                if startup:events.insert(1,self.startup_diagnostic())
                result=self.run_agent('codex',events);report=json.loads(result.stdout)
                category='warnings' if recovered else 'errors'
                self.assertEqual(result.returncode,0 if recovered else 1,result.stderr)
                self.assertEqual(report['validation_status'],('needs_review' if startup else 'passed') if recovered else 'rejected')
                self.assertEqual(report['runner_exit_code'],0 if recovered else 1)
                self.assertEqual(report['runtime_exit_code'],0)
                self.assertEqual(report['diagnostic_counts'],{
                    'errors':0 if recovered else old_count+25,'anomalies':int(startup),
                    'warnings':old_count+25 if recovered else 0})
                self.assertEqual(len(report[category]),20)
                self.assertTrue(report['diagnostics_truncated'])
                first_line=3+int(startup)+old_count+int(early_final)
                displayed_old=min(old_count,19)
                self.assertEqual([d['line'] for d in report[category][:displayed_old]],list(range(3+int(startup),3+int(startup)+displayed_old)))
                if startup:self.assert_output_diagnostic(report['anomalies'][0],str(events[1]['item']),2)
                first=report[category][displayed_old]
                self.assertEqual((first['stream'],first['line']),('output',first_line))
                self.assertIn(notices[0]['message'],first['message'])
                if old_count>=19:
                    self.assertEqual([d['message'] for d in report[category][:19]],
                        [str(e['item'] if recovered else e) for e in old[:19]])
                for diagnostic in report[category]:
                    self.assertEqual(set(diagnostic),{'stream','line','message','message_chars','truncated','path','proof_line'})
                    self.assertLessEqual(len(diagnostic['message']),2000)
                    self.assertEqual(diagnostic['message_chars'],len(diagnostic['message']))
                    self.assertFalse(diagnostic['truncated'])
        with self.subTest(name='last-candidate-beyond-retention'):
            events=self.recovered_codex(attempts=(1,)*20,startup=startup);events[-1:-1]=[self.connection_notice(2)]*5
            result=self.run_agent('codex',events);report=json.loads(result.stdout)
            self.assertEqual(result.returncode,1,result.stderr)
            self.assertEqual(report['runner_exit_code'],1)
            self.assertEqual(report['diagnostic_counts'],{'errors':25,'anomalies':int(startup),'warnings':0})
            self.assertEqual(report['validation_status'],'rejected')
            self.assertTrue(all('final shape or order' in d['message'] for d in report['errors']))
        spec=importlib.util.spec_from_file_location('agent_result',ROOT/'scripts/agent-run-result.py')
        adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
        for recovered in (True,False):
            with self.subTest(name=f'evicted-long-diagnostic-keeps-text-truncation-{recovered}'):
                output=self.root/'direct.jsonl';stderr=self.root/'direct.stderr'
                output.write_text('\n'.join(json.dumps(e) for e in self.recovered_codex(startup=startup))+'\n');stderr.write_text('')
                args=SimpleNamespace(runtime='codex',provider='mimo',output=str(output),stderr=str(stderr),
                    last_message=None,canary_file=None,canary_expected=None,artifact=[],exit_code=0,
                    runner_exit_code=0,wall_clock_seconds=None)
                collector=adapter.Collection(args);category='warnings' if recovered else 'errors'
                for i in range(19):collector.note(category,f'old-{i}')
                collector.note(category,'x'*2501)
                last=getattr(collector,category)[-1]
                self.assertEqual((len(last['message']),last['message_chars'],last['truncated']),(2000,2501,True))
                report=collector.collect()
                self.assertTrue(collector.text_truncated)
                self.assertTrue(report['diagnostics_truncated'])
                self.assertEqual(report['diagnostic_counts'][category],21)
                self.assertEqual(len(report[category]),20)
                self.assertEqual([d['message'] for d in report[category][:19]],[f'old-{i}' for i in range(19)])
                self.assertIn(self.connection_notice()['message'],report[category][-1]['message'])
                self.assertEqual(report[category][-1]['line'],3+int(startup))
                self.assertEqual(report['validation_status'],('needs_review' if startup else 'passed') if recovered else 'rejected')
                self.assertEqual(collector.stream,'stderr')

    def test_claude_connection_error_stays_fatal(self):
        for error in (False,True):
            with self.subTest(error=error):
                events=self.claude()
                if error:events.insert(1,self.connection_notice())
                result=self.run_agent('claude',events);report=json.loads(result.stdout)
                self.assert_report_contract(report)
                self.assertEqual(result.returncode,int(error),result.stderr)
                self.assertEqual(report['validation_status'],'rejected' if error else 'passed')
                self.assertEqual(report['final_answer'],'done')
                self.assertEqual(report['agent_status'],'completed')
                self.assertEqual(report['diagnostic_counts'],{'errors':int(error),'anomalies':0,'warnings':0})
                if error:self.assertEqual(report['errors'][0]['message'],str(self.connection_notice()))

    def test_agent_run_report_contract(self):
        anomaly=self.recovered_codex();anomaly.insert(-2,{'type':'item.completed','item':{
            'id':'c','type':'command_execution','command':'fixture','exit_code':1}})
        mixed=self.recovered_codex();mixed.insert(-1,self.connection_notice(2))
        claude_error=self.claude();claude_error.insert(1,self.connection_notice())
        for name,runtime,events,status in [
            ('clean-recovery','codex',self.recovered_codex(),'passed'),
            ('anomaly-recovery','codex',anomaly,'needs_review'),
            ('proof-failure','codex',mixed,'rejected'),
            ('ordinary-codex','codex',self.codex(),'passed'),
            ('ordinary-claude','claude',self.claude(),'passed'),
            ('claude-error','claude',claude_error,'rejected')]:
            with self.subTest(name=name):
                result=self.run_agent(runtime,events);report=json.loads(result.stdout)
                self.assert_report_contract(report)
                self.assertEqual(report['runtime'],runtime)
                self.assertEqual(report['provider'],'mimo' if runtime=='codex' else 'ds-flash')
                self.assertEqual(report['validation_status'],status)
                self.assertEqual(result.returncode,int(status=='rejected'),result.stderr)

    def test_codex_connection_notice_detail_preserves_raw_stream(self):
        events=self.recovered_codex()
        for exit_code in (0,7):
            with self.subTest(exit_code=exit_code):
                result=self.run_agent('codex',events,'--detail','--artifact',str(self.root/'absent-artifact'),
                    '--canary-file',str(self.root/'absent-canary'),'--canary-expected',str(self.root/'absent-expected'),
                    exit_code=exit_code,err='fixture stderr\n')
                self.assertEqual(result.returncode,exit_code,result.stderr)
                self.assertEqual(result.stdout,'\n'.join(json.dumps(e) for e in events)+'\n')
                self.assertEqual(result.stderr,'fixture stderr\n')
                self.assertNotIn('validation_status',result.stdout)
                self.assertNotIn('Recovered Codex connection notice:',result.stdout)
        output=self.root/'detail-recovered.jsonl';stderr=self.root/'detail-recovered.stderr'
        result=self.run_agent('codex',events,'--detail','--output',str(output),'--stderr',str(stderr),err='raw stderr\n')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout,'');self.assertEqual(result.stderr,'')
        self.assertEqual(output.read_text(),'\n'.join(json.dumps(e) for e in events)+'\n')
        self.assertEqual(stderr.read_text(),'raw stderr\n')

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
                self.assertEqual(report['validation_status'],'passed')
            events=getattr(self,runtime)()
            if runtime=='codex':events.insert(1,{'type':'thread.started','thread_id':'other'})
            else:
                events[0]['session_id']='first';events[-1]['session_id']='other'
            result=self.run_agent(runtime,events);report=json.loads(result.stdout)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIsNone(report['session_id'])
            self.assertEqual(report['validation_status'],'needs_review')
            self.assertTrue(any('conflicting runtime session' in a['message'] for a in report['anomalies']))

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
            if runtime=='codex':events[-1]['type']='turn.failed'
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
