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
        self.fake.write_text('''import os, sys, json
from pathlib import Path
args=sys.argv[1:]
for path, content in json.loads(os.environ.get('ARTIFACT_CONTENTS','{}')).items():
 Path(path).write_text(content)
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

    def run_agent(self, runtime, events, *args, exit_code=0, err='', final='done', runner_path=None):
        fixture = self.root / 'events'
        fixture.write_text('\n'.join(json.dumps(e) if isinstance(e, dict) else e for e in events)+'\n')
        env = self.env | {'FIXTURE': str(fixture), 'RUNTIME_EXIT': str(exit_code), 'ERR': err, 'FINAL': final}
        result = subprocess.run([str(runner_path or ROOT/f'scripts/{runtime}-agent-run'), '--provider', 'mimo' if runtime=='codex' else 'ds-flash', '--cwd', str(ROOT), '--prompt', 'bounded test', *args], env=env, capture_output=True, text=True)
        return result

    def codex(self, text='done'):
        return [{'type':'thread.started','thread_id':'test'}, {'type':'turn.started'}, {'type':'item.completed','item':{'id':'m','type':'agent_message','text':text}}, {'type':'turn.completed','usage':{}}]

    def claude(self, text='done'):
        return [{'type':'system','subtype':'init','model':'fixture'}, {'type':'result','subtype':'success','is_error':False,'result':text}]

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

    def test_bare_tool_objects_without_execution_are_rejected(self):
        for runtime in ('codex','claude'):
            for claim in ({'type':'tool_use','id':'fake','name':'Bash','input':{'command':'cat proof'}},
                          {'name':'exec_command','arguments':{'cmd':'cat proof'}}):
                result=self.run_agent(runtime,getattr(self,runtime)(json.dumps(claim)))
                self.assertEqual(result.returncode,1)
                self.assertEqual(json.loads(result.stdout)['validation_status'],'rejected')

    def test_wrapped_tool_claims_are_rejected_but_ordinary_json_types_are_data(self):
        tool=json.dumps({'type':'tool_use','name':'Bash','input':{'command':'cat proof'}})
        for runtime in ('codex','claude'):
            for text in ('Called '+tool+' just now', '~~~json\n'+tool+'\n~~~', '```json\n'+tool+'\n```\nDone.'):
                result=self.run_agent(runtime,getattr(self,runtime)(text))
                self.assertEqual(result.returncode,1)
                self.assertEqual(json.loads(result.stdout)['validation_status'],'rejected')
            for text in (json.dumps({'type':['a','b'],'answer':'done'}),'['*600+'0'+']'*600):
                result=self.run_agent(runtime,getattr(self,runtime)(text))
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(json.loads(result.stdout)['validation_status'],'passed')

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
