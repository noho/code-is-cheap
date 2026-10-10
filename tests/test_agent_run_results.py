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
        self.fake.write_text('''import os, sys
from pathlib import Path
args=sys.argv[1:]
if '--output-last-message' in args:
 Path(args[args.index('--output-last-message')+1]).write_text(os.environ['FINAL'])
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
        artifact=self.root/'review.md';artifact.write_text('CANARY=fresh-12345678\n')
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
