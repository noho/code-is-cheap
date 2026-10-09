"""Transport tests: no model calls or srt installation needed."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('node'), 'optional envelope needs Node')
class LaunchTests(unittest.TestCase):
    def run_node(self, source, inputs):
        result = subprocess.run(['node', '--input-type=module', '-e',
            "import {decodeArgv,fileBackedArgv,compactDenyRules,validateRuntime} from " + json.dumps((ROOT/'scripts/agent-sandbox-launch.mjs').as_uri()) + ";\n"
            "import fs from 'node:fs';\nconst input=JSON.parse(fs.readFileSync(0,'utf8'));\n" + source],
            input=json.dumps(inputs), capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_decode_quoting_preserves_literal_arguments_and_rejects_operators(self):
        result = self.run_node("""
const good=input.good.map(([text,expected])=>JSON.stringify(decodeArgv(text))===JSON.stringify(expected));
const bad=input.bad.map(text=>{try{decodeArgv(text);return false;}catch{return true;}});
console.log(JSON.stringify({good,bad}));
""", dict(good=[
            ["env A=b '/path with space' ''", ['env','A=b','/path with space','']],
            ["'a'\"'\"'b' '$HOME $(touch /not-executed); ! [*]'", ["a'b",'$HOME $(touch /not-executed); ! [*]']],
            ["'Unicode 雪\nline'", ['Unicode 雪\nline']],
        ], bad=['env x;echo bad', 'env $HOME', 'env `id`', 'env a|b', "env 'unterminated", 'env  a', 'env a ']))
        self.assertTrue(all(result['good']) and all(result['bad']),result)

    def test_runtime_validation_is_nonspawning_and_rejects_incomplete_installations(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); (p/'dist/utils').mkdir(parents=True); (p/'dist/sandbox').mkdir()
            marker=p/'must-not-run'
            cli=p/'dist/cli.js'; cli.write_text(f"require('fs').writeFileSync({json.dumps(str(marker))},'bad')")
            quote=p/'dist/utils/shell-quote.js'; quote.write_text('export const quote = () => "";')
            (p/'dist/sandbox/macos-sandbox-utils.js').write_text('// fixture')
            pkg=p/'package.json'
            doc=dict(name='@anthropic-ai/sandbox-runtime',version='0.0.79',bin=dict(srt='dist/cli.js'))
            pkg.write_text(json.dumps(doc))
            result=self.run_node('console.log(JSON.stringify(validateRuntime(input)));',str(cli))
            self.assertEqual(result['cli'],str(cli.resolve()))
            self.assertFalse(marker.exists())
            for alteration in ('version','bin','missing-module','standalone'):
                changed=dict(doc)
                if alteration=='version': changed['version']='0.0.80'
                if alteration=='bin': changed['bin']=dict(srt='dist/other.js')
                if alteration=='missing-module': quote.unlink()
                pkg.write_text(json.dumps(changed))
                candidate=str(cli) if alteration!='standalone' else str(p/'standalone')
                if alteration=='standalone': Path(candidate).write_text('#!/bin/sh\necho 0.0.79\n')
                result=self.run_node('try{validateRuntime(input);console.log(JSON.stringify(false));}catch(e){console.log(JSON.stringify(e.message));}',candidate)
                self.assertIn('reinstall with install-agent-sandbox.sh',result)

    def test_large_profile_is_byte_preserved_and_no_long_spawn_argument_remains(self):
        with tempfile.TemporaryDirectory() as directory:
            profile_path = str(Path(directory)/'seatbelt.sb')
            profile = '(version 1)\n; ' + "雪 ' quote ! $() [x]\n" * 70000
            result = self.run_node("""
const quote=args=>args.map(s=>s===''?"''":/^[A-Za-z0-9_./:@+,-][A-Za-z0-9_./:=@+,-]*$/.test(s)?s:"'"+s.replace(/'/g,`'"'"'`)+"'").join(' ');
const expected=quote(['/bin/echo',"literal ! ' $HOME"]);
const original=['env','-u','EXAMPLE','PROXY_VALUE=literal $()','/usr/bin/sandbox-exec','-p',input.profile,'/bin/bash','-c',expected];
const result=fileBackedArgv(quote(original),input.path,expected,quote);
const bytes=fs.readFileSync(input.path);
let duplicateRejected=false;try{fileBackedArgv(quote(original),input.path,expected,quote);}catch{duplicateRejected=true;}
console.log(JSON.stringify({argv:result.argv,equal:bytes.equals(Buffer.from(input.profile)),bytes:result.profileBytes,maxArgBytes:Math.max(...result.argv.map(s=>Buffer.byteLength(s))),mode:fs.statSync(input.path).mode&0o777,duplicateRejected,profileSha256:result.profileSha256,sourceSha256:result.sourceSha256}));
""", dict(path=profile_path,profile=profile))
            self.assertTrue(result['equal'] and result['duplicateRejected'])
            self.assertGreater(result['bytes'],1048576)
            self.assertLess(result['maxArgBytes'],1024)
            self.assertEqual(result['mode'],0o400)
            self.assertEqual(result['profileSha256'],hashlib.sha256(profile.encode()).hexdigest())
            self.assertEqual(result['sourceSha256'],result['profileSha256'])
            self.assertIn('-f',result['argv'])
            self.assertNotIn('-p',result['argv'])

    def test_unexpected_launch_layout_fails_without_creating_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_node("""
const quote=args=>args.map(s=>s===''?"''":/^[A-Za-z0-9_./:@+,-][A-Za-z0-9_./:=@+,-]*$/.test(s)?s:"'"+s.replace(/'/g,`'"'"'`)+"'").join(' ');
const base=['env','X=y','/usr/bin/sandbox-exec','-p','(version 1) (allow default)','/bin/bash','-c','expected'];
const cases=[['/bin/echo','no sandbox'],base.with(0,'other-env'),base.with(1,'another-command'),base.with(3,'-f'),base.with(7,'different'),base.with(4,'no-version')];
const rejected=cases.map((argv,i)=>{const p=input.dir+'/'+i+'.sb';try{fileBackedArgv(quote(argv),p,'expected',quote);return false;}catch{return !fs.existsSync(p);}});
let noncanonical=false;try{fileBackedArgv("'env' "+quote(base.slice(1)),input.dir+'/extra.sb','expected',quote);}catch{noncanonical=true;}
console.log(JSON.stringify({rejected,noncanonical}));
""", dict(dir=directory))
            self.assertTrue(all(result['rejected']) and result['noncanonical'],result)

    def test_compaction_preserves_exact_path_regions_and_other_rules(self):
        paths = ['/synthetic/dir/' + x for x in (
            ['name-'+str(i) for i in range(150)] +
            ["quote'雪", 'dot.*[x](y)|z', 'newline\nname', 'back\\slash', 'dollar$end'])]
        filters = '\n'.join('  (subpath '+json.dumps(p,ensure_ascii=False)+')' for p in paths)
        untouched = '(allow file-write* (subpath "/synthetic"))\n(deny file-read* (require-all (subpath "/nested") (literal "/nested/one")))\n'
        profile = untouched+'(deny file-read*\n'+filters+'\n  (with message "test"))\n'
        result = self.run_node('console.log(JSON.stringify({profile:compactDenyRules(input)}));',profile)['profile']
        self.assertTrue(result.startswith(untouched))
        regexes = []
        remaining = []
        import re
        for line in result[len(untouched):].splitlines():
            if line.startswith('  (regex '):
                text = line[len('  (regex '):-1]
                self.assertLessEqual(len(text.encode())-2,900)
                regexes.append(re.compile(json.loads(text)))
            elif line.startswith('  (subpath '):
                remaining.append(json.loads(line[len('  (subpath '):-1]))
        def matches(p):
            return any(r.fullmatch(p) for r in regexes) or any(p==x or p.startswith(x+'/') for x in remaining)
        for p in paths:
            for value in (p,p+'/child',p+'/child\nline',p+'/deep/leaf'):
                self.assertTrue(matches(value),value)
            for value in (p+'extra',p+'\n',p.replace('/synthetic/','/different/',1)):
                self.assertFalse(matches(value),value)

    @unittest.skipUnless(platform.system() == 'Darwin' and os.getenv('AGENT_SANDBOX_KERNEL_TESTS') == '1',
                         'explicit native Seatbelt test opt-in')
    def test_native_original_and_compacted_policies_have_identical_access(self):
        # Compare kernel behavior, including regex metacharacters, descendants,
        # newline names, case aliases, writes, renames and near-miss siblings.
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            p = Path(directory)
            names = ['item-'+str(i) for i in range(140)] + ["quote'雪",'dot.*[x](y)|z','line\nname','back\\slash','dollar$end']
            paths = []
            for name in names:
                d = p/name; d.mkdir(); (d/'child\nline').write_text('denied')
                (p/(name+'extra')).write_text('allowed')
                paths.append(str(d))
            filters = '\n'.join('  (subpath '+json.dumps(x,ensure_ascii=False)+')' for x in paths)
            pins = '\n'.join('  (literal '+json.dumps(x,ensure_ascii=False)+')' for x in paths)
            rules = ''.join('(deny '+op+'\n'+body+'\n  (with message "test"))\n'
                            for op,body in [('file-read*',filters),('file-write*',filters),
                                            ('file-write-unlink',pins),('file-write-unlink file-write-create',pins)])
            original = '(version 1)\n(allow default)\n'+rules
            compacted = self.run_node('console.log(JSON.stringify(compactDenyRules(input)));',original)
            self.assertNotEqual(original,compacted)
            probe = p/'probe.py'
            probe.write_text('''import json,os,sys
from pathlib import Path
paths=json.loads(Path(sys.argv[1]).read_text()); r=[]
for value in paths:
 p=Path(value)
 for path in (p/'child\\nline',Path(value+'extra'),Path(value+'\\n'),Path(value.upper())/'child\\nline'):
  try: path.read_text(); r.append('read')
  except OSError as e: r.append(type(e).__name__)
 try: (p/'new').write_text('x'); r.append('write')
 except OSError as e: r.append(type(e).__name__)
 try: os.rename(p,str(p)+'-moved'); r.append('rename')
 except OSError as e: r.append(type(e).__name__)
print(json.dumps(r))
''')
            listing=p/'paths.json'; listing.write_text(json.dumps(paths))
            results=[]
            for i,policy in enumerate((original,compacted)):
                profile=p/f'{i}.sb'; profile.write_text(policy)
                r=subprocess.run(['/usr/bin/sandbox-exec','-f',str(profile),shutil.which('python3'),str(probe),str(listing)],capture_output=True,text=True,timeout=30)
                self.assertEqual(r.returncode,0,r.stderr)
                results.append(json.loads(r.stdout))
            self.assertEqual(*results)
            for i in range(0,len(results[0]),6):
                self.assertEqual(results[0][i],'PermissionError')
                self.assertEqual(results[0][i+1],'read')
                self.assertEqual(results[0][i+4:i+6],['PermissionError','PermissionError'])


if __name__ == '__main__':
    unittest.main()
