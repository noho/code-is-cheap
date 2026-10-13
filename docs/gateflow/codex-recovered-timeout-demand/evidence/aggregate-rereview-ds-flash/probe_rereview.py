"""Independent aggregate re-review probe (ds-flash). Synthetic events only; no business input."""
import json, os, subprocess
from pathlib import Path

CURRENT = Path('/Users/leo/workspace/code-is-cheap/scripts/agent-run-result.py')
BEFORE = Path(os.environ['BEFORE_SNAPSHOT'])
WORK = Path(os.environ['WORK_DIR']); WORK.mkdir(parents=True, exist_ok=True)
CANARY = WORK/'canary.txt'; CANARY.write_text('fresh-12345678')
EXPECTED = WORK/'expected.txt'; EXPECTED.write_text('fresh-12345678')
GOODART = WORK/'artifact.md'; GOODART.write_text('report body\nCANARY=fresh-12345678\n')

def assistant(text, **f): return {'type':'assistant','message':{'content':[{'type':'text','text':text}]},**f}
def init(): return {'type':'system','subtype':'init'}
def result(value, **f):
    e = {'type':'result','subtype':'success','is_error':False,'result':value}; e.update(f); return e
def codex(text='done'): return [{'type':'thread.started','thread_id':'t'},{'type':'turn.started'},
    {'type':'item.completed','item':{'id':'m','type':'agent_message','text':text}},{'type':'turn.completed','usage':{}}]

CASES = [
 ('c1-blank-result-cannot-be-rescued-by-canary-match-and-valid-artifact',
  dict(runtime='claude', events=[init(), assistant('partial root\nCANARY=fresh-12345678'), result('')],
       canary=True, artifact='good', last_message='partial root\nCANARY=fresh-12345678')),
 ('c2-blank-result-with-canary-mismatch-and-valid-artifact',
  dict(runtime='claude', events=[init(), assistant('partial root\nCANARY=wrong'), result('')],
       canary=True, artifact='good', last_message='partial root\nCANARY=wrong')),
 ('c3-duplicate-result-late-text-never-displays-over-retained-partial',
  dict(runtime='claude', events=[init(), assistant('partial root'), result(''), result('late authoritative')],
       canary=False, artifact=None, last_message=None)),
 ('c4-postterminal-assistant-cannot-overwrite-retained-partial',
  dict(runtime='claude', events=[init(), assistant('partial root'), result(''), assistant('overwrite')],
       canary=False, artifact=None, last_message=None)),
 ('c5-nested-result-text-never-supplies-root-display',
  dict(runtime='claude', events=[init(), assistant('partial root'),
        assistant('', **{'message':{'content':[{'type':'tool_use','id':'p','name':'Bash','input':{}}]}}),
        {'type':'result','subtype':'success','is_error':False,'result':'child-final','parent_tool_use_id':'p'},
        result('')], canary=False, artifact=None, last_message=None)),
 ('c6-whitespace-partial-then-blank-result-retained',
  dict(runtime='claude', events=[init(), assistant('   '), result('  ')],
       canary=False, artifact=None, last_message=None)),
 ('c7-normal-nonblank-claude-unchanged',
  dict(runtime='claude', events=[init(), assistant('partial root'), result('authoritative')],
       canary=False, artifact=None, last_message=None)),
 ('c8-codex-blank-latest-message-unchanged',
  dict(runtime='codex', events=[codex('earlier'), {'type':'item.completed','item':{'id':'last','type':'agent_message','text':'  '}}],
       canary=False, artifact=None, last_message=None)),
 ('c9-codex-normal-unchanged',
  dict(runtime='codex', events=codex('done'), canary=False, artifact=None, last_message=None)),
]

def run_case(source, name, spec):
    d = WORK/Path(source).stem/name; d.mkdir(parents=True, exist_ok=True)
    out = d/'events.jsonl'; err = d/'stderr.log'
    out.write_text(''.join(json.dumps(e)+'\n' for e in spec['events'])); err.write_text('')
    argv = ['python3','-B',str(source),'--runtime',spec['runtime'],'--provider','synthetic',
            '--output',str(out),'--stderr',str(err),'--exit-code','0','--runner-exit-code','0']
    if spec['canary']:
        argv += ['--canary-file',str(CANARY),'--canary-expected',str(EXPECTED)]
    if spec['artifact']=='good':
        argv += ['--artifact',str(GOODART)]
    if spec['last_message'] is not None:
        lm = d/'last.txt'; lm.write_text(spec['last_message']); argv += ['--last-message',str(lm)]
    r = subprocess.run(argv, capture_output=True, text=True)
    rep = json.loads(r.stdout)
    (d/'report.json').write_text(r.stdout)
    msgs = [e['message'] for e in rep['errors']]
    return {'exit':r.returncode,'validation':rep['validation_status'],'agent_status':rep['agent_status'],
            'terminal':rep['terminal'],'display':rep['final_answer'],'chars':rep['final_answer_chars'],
            'canary':rep['canary_status'],'not_assessed':rep['result_status']=='not_assessed','errors':msgs}

def has(msgs, frag): return any(frag in m for m in msgs)

def check(name, cur):
    if name.startswith('c1'):
        return (cur['exit']==1 and cur['validation']=='rejected' and cur['agent_status']=='failed'
                and cur['terminal']=='failed' and cur['display']=='partial root\nCANARY=fresh-12345678'
                and cur['canary']=='match' and has(cur['errors'],'missing valid complete final answer')
                and not has(cur['errors'],'required artifact missing') and not has(cur['errors'],'last-message differs'))
    if name.startswith('c2'):
        return (cur['exit']==1 and cur['validation']=='rejected' and cur['canary']=='mismatch'
                and cur['display']=='partial root\nCANARY=wrong'
                and has(cur['errors'],'canary proof does not match') and has(cur['errors'],'missing valid complete final answer')
                and not has(cur['errors'],'required artifact missing'))
    if name.startswith('c3'):
        return (cur['exit']==1 and cur['validation']=='rejected' and cur['terminal']=='conflicting'
                and cur['display']=='partial root' and 'late authoritative' not in cur['display']
                and has(cur['errors'],'multiple result terminals'))
    if name.startswith('c4'):
        return (cur['exit']==1 and cur['validation']=='rejected' and cur['display']=='partial root'
                and has(cur['errors'],'event after runtime terminal'))
    if name.startswith('c5'):
        return (cur['exit']==1 and cur['validation']=='rejected' and cur['display']=='partial root'
                and 'child-final' not in cur['display'])
    if name.startswith('c6'):
        return (cur['exit']==1 and cur['validation']=='rejected' and cur['display']=='   ' and cur['chars']==3)
    if name.startswith('c7'):
        return (cur['exit']==0 and cur['validation']=='passed' and cur['agent_status']=='completed'
                and cur['terminal']=='success' and cur['display']=='authoritative' and cur['not_assessed'])
    if name.startswith('c8'):
        return cur['exit']==1 and cur['validation']=='rejected' and cur['agent_status']=='failed'
    if name.startswith('c9'):
        return cur['exit']==0 and cur['validation']=='passed' and cur['display']=='done'
    raise SystemExit('unknown case '+name)

results = {'current':{}, 'before':{}}
for source, label in ((CURRENT,'current'),(BEFORE,'before')):
    for name, spec in CASES:
        res = run_case(source, name, spec)
        ok = check(name, res)
        results[label][name] = {'ok':ok, **res}
        print(f"{label:8s} {name[:55]:58s} ok={ok} exit={res['exit']} val={res['validation']} disp={res['display']!r}")
        assert ok or label=='before', (label, name, res)

# differential: which cases changed between before and current
diff = {}
for name,_ in CASES:
    a, b = results['before'][name], results['current'][name]
    if (a['exit'],a['validation'],a['display'],a['chars'],a['terminal'],a['canary']) != (b['exit'],b['validation'],b['display'],b['chars'],b['terminal'],b['canary']):
        diff[name] = {'before':{k:a[k] for k in ('exit','validation','display','chars','terminal')},
                      'current':{k:b[k] for k in ('exit','validation','display','chars','terminal')}}
print('DIFFERENTIAL:', json.dumps(diff, indent=1))
(WORK/'probe-results.json').write_text(json.dumps({'results':results,'differential':diff}, indent=1)+'\n')
print('ALL CHECKS PASSED')
