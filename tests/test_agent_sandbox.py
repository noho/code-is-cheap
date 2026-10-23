"""Boundary tests. Kernel tests are opt-in and must run outside the parent sandbox.
AGENT_SANDBOX_KERNEL_TESTS=1 SRT_TEST_BIN=/path/to/srt python3 -m unittest discover -s tests -p test_agent_sandbox.py
"""
import contextlib
import errno
import hashlib
import io
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import platform
import select
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
import unittest.mock

ROOT = Path(__file__).resolve().parents[1]
GPT_PROFILES = (
    ("gpt-6-astra", "gpt-6-astra", "high"),
    ("gpt-6-astra-x", "gpt-6-astra", "xhigh"),
    ("gpt-6-astra-max", "gpt-6-astra", "max"),
    ("gpt-6-sol", "gpt-6.1-sol", "high"),
    ("gpt-6-sol-x", "gpt-6.1-sol", "xhigh"),
    ("gpt-6-sol-max", "gpt-6.1-sol", "max"),
)
loader = importlib.machinery.SourceFileLoader('agent_sandbox', str(ROOT/'scripts/agent-sandbox'))
spec = importlib.util.spec_from_loader(loader.name, loader)
sandbox = importlib.util.module_from_spec(spec)
loader.exec_module(sandbox)


# Fixed public CA and genuine OpenSSL trustout AUX bytes; no private keys.
PUBLIC_CA = b"""-----BEGIN CERTIFICATE-----
MIIGFDCCA/ygAwIBAgIIU+w77vuySF8wDQYJKoZIhvcNAQEFBQAwUTELMAkGA1UE
BhMCRVMxQjBABgNVBAMMOUF1dG9yaWRhZCBkZSBDZXJ0aWZpY2FjaW9uIEZpcm1h
cHJvZmVzaW9uYWwgQ0lGIEE2MjYzNDA2ODAeFw0wOTA1MjAwODM4MTVaFw0zMDEy
MzEwODM4MTVaMFExCzAJBgNVBAYTAkVTMUIwQAYDVQQDDDlBdXRvcmlkYWQgZGUg
Q2VydGlmaWNhY2lvbiBGaXJtYXByb2Zlc2lvbmFsIENJRiBBNjI2MzQwNjgwggIi
MA0GCSqGSIb3DQEBAQUAA4ICDwAwggIKAoICAQDKlmuO6vj78aI14H9M2uDDUtd9
thDIAl6zQyrET2qyyhxdKJp4ERppWVevtSBC5IsP5t9bpgOSL/UR5GLXMnE42QQM
cas9UX4PB99jBVzpv5RvwSmCwLTaUbDBPLutN0pcyvFLNg4kq7/DhHf9qFD0sefG
L9ItWY16Ck6WaVICqjaY7Pz6FIMMNx/Jkjd/14Et5cS54D40/mf0PmbR0/RAz15i
NA9wBj4gGFrO93IbJWyTdBSTo3OxDqqHECNZXyAFGUftaI6SEspd/NYrspI8IM/h
X68gvqB2f3bl7BqGYTM+53u0P6APjqK5am+5hyZvQWyIplD9amML9ZMWGxmPsu2b
m8mQ9QEM3xk9Dz44I8kvjwzRAv4bVdZO0I08r0+k8/6vKtMFnXkIoctXMbScyJCy
Z/QYFpM6/EfY0XiWMR+6KwxfXZmtY4laJCB22N/9q06mIqqdXuYnin1oKaPnirja
EbsXLZmdEyRG98Xi2J+Of8ePdG1asuhy9azuJBCtLxTa/y2aRnFHvkLfuwHb9H/T
KI8xWVvTyQKmtFLKbpf7Q8UIJm+K9Lv9nyiqDdVF8xM6HdjAeI9BZzwelGSuewvF
6NkBiDkal4ZkQdU7hwxu+g/GvUgUvzlN1J5Bto+WHWOWk9mVBngxaJ43BjuAiUVh
OSPHG0SjFeUc+JIwuwIDAQABo4HvMIHsMBIGA1UdEwEB/wQIMAYBAf8CAQEwDgYD
VR0PAQH/BAQDAgEGMB0GA1UdDgQWBBRlzeurNR4APn7VdMActHNHDhpkLzCBpgYD
VR0gBIGeMIGbMIGYBgRVHSAAMIGPMC8GCCsGAQUFBwIBFiNodHRwOi8vd3d3LmZp
cm1hcHJvZmVzaW9uYWwuY29tL2NwczBcBggrBgEFBQcCAjBQHk4AUABhAHMAZQBv
ACAAZABlACAAbABhACAAQgBvAG4AYQBuAG8AdgBhACAANAA3ACAAQgBhAHIAYwBl
AGwAbwBuAGEAIAAwADgAMAAxADcwDQYJKoZIhvcNAQEFBQADggIBABd9oPm03cXF
661LJLWhAqvdpYhKsg9VSytXjDvlMd3+xDLx51tkljYyGOylMnfX40S2wBEqgLk9
am58m9Ot/MPWo+ZkKXzR4Tgegiv/J2Wv+xYVxC5xhOW1//qkR71kMrv2JYSiJ0L1
ILDCExARzRAVukKQKtJE4ZYm6zFIEv0q2skGz3QeqUvVhyj5eTSSPi5E6PaPT481
PyWzOdxjKpBrIF/EUhJOlywqrJ2X3kjyo2bbwtKDlaZmp54lD+kLM5FlClrD2VQS
3a/DTg4fJl4N3LON7NWBcN7STyQF82xO9UxJZo3R/9ILJUFI/lGExkKvgATP0H5k
SeTy36LssUzAKh3ntLFlosS88Zj0qnAHY7S42jtM+kAiMFsRpvAFDsYCA0irhpuF
3dvd6qJ2gHN99ZwExEWN57kci57q13XRcrHedUTnQn3iV2t93Jm8PYMo6oCTjcVM
ZcFwgbg4/EMxsvYDNEeyrPsiBsse3RdHHF9mudMaotoRsaS8I8nkvof/uZS2+F0g
StRf571oe2XyFR7SOqkt6dhrJKyXWERHrVkY8SFlcN7ONGCoQPHzPKTDKCOM/icz
Q0CgFzzr6juwcqajuUpLXhZI9LK8yIySxZ2frHI2vDSANGupi5LAuBft7HZT9SQB
jLMi6Et8Vcad+qMUu2WFbm5PEn4KPJ2V
-----END CERTIFICATE-----"""

PUBLIC_TRUSTED_CA = b"""-----BEGIN TRUSTED CERTIFICATE-----
MIIGFDCCA/ygAwIBAgIIU+w77vuySF8wDQYJKoZIhvcNAQEFBQAwUTELMAkGA1UE
BhMCRVMxQjBABgNVBAMMOUF1dG9yaWRhZCBkZSBDZXJ0aWZpY2FjaW9uIEZpcm1h
cHJvZmVzaW9uYWwgQ0lGIEE2MjYzNDA2ODAeFw0wOTA1MjAwODM4MTVaFw0zMDEy
MzEwODM4MTVaMFExCzAJBgNVBAYTAkVTMUIwQAYDVQQDDDlBdXRvcmlkYWQgZGUg
Q2VydGlmaWNhY2lvbiBGaXJtYXByb2Zlc2lvbmFsIENJRiBBNjI2MzQwNjgwggIi
MA0GCSqGSIb3DQEBAQUAA4ICDwAwggIKAoICAQDKlmuO6vj78aI14H9M2uDDUtd9
thDIAl6zQyrET2qyyhxdKJp4ERppWVevtSBC5IsP5t9bpgOSL/UR5GLXMnE42QQM
cas9UX4PB99jBVzpv5RvwSmCwLTaUbDBPLutN0pcyvFLNg4kq7/DhHf9qFD0sefG
L9ItWY16Ck6WaVICqjaY7Pz6FIMMNx/Jkjd/14Et5cS54D40/mf0PmbR0/RAz15i
NA9wBj4gGFrO93IbJWyTdBSTo3OxDqqHECNZXyAFGUftaI6SEspd/NYrspI8IM/h
X68gvqB2f3bl7BqGYTM+53u0P6APjqK5am+5hyZvQWyIplD9amML9ZMWGxmPsu2b
m8mQ9QEM3xk9Dz44I8kvjwzRAv4bVdZO0I08r0+k8/6vKtMFnXkIoctXMbScyJCy
Z/QYFpM6/EfY0XiWMR+6KwxfXZmtY4laJCB22N/9q06mIqqdXuYnin1oKaPnirja
EbsXLZmdEyRG98Xi2J+Of8ePdG1asuhy9azuJBCtLxTa/y2aRnFHvkLfuwHb9H/T
KI8xWVvTyQKmtFLKbpf7Q8UIJm+K9Lv9nyiqDdVF8xM6HdjAeI9BZzwelGSuewvF
6NkBiDkal4ZkQdU7hwxu+g/GvUgUvzlN1J5Bto+WHWOWk9mVBngxaJ43BjuAiUVh
OSPHG0SjFeUc+JIwuwIDAQABo4HvMIHsMBIGA1UdEwEB/wQIMAYBAf8CAQEwDgYD
VR0PAQH/BAQDAgEGMB0GA1UdDgQWBBRlzeurNR4APn7VdMActHNHDhpkLzCBpgYD
VR0gBIGeMIGbMIGYBgRVHSAAMIGPMC8GCCsGAQUFBwIBFiNodHRwOi8vd3d3LmZp
cm1hcHJvZmVzaW9uYWwuY29tL2NwczBcBggrBgEFBQcCAjBQHk4AUABhAHMAZQBv
ACAAZABlACAAbABhACAAQgBvAG4AYQBuAG8AdgBhACAANAA3ACAAQgBhAHIAYwBl
AGwAbwBuAGEAIAAwADgAMAAxADcwDQYJKoZIhvcNAQEFBQADggIBABd9oPm03cXF
661LJLWhAqvdpYhKsg9VSytXjDvlMd3+xDLx51tkljYyGOylMnfX40S2wBEqgLk9
am58m9Ot/MPWo+ZkKXzR4Tgegiv/J2Wv+xYVxC5xhOW1//qkR71kMrv2JYSiJ0L1
ILDCExARzRAVukKQKtJE4ZYm6zFIEv0q2skGz3QeqUvVhyj5eTSSPi5E6PaPT481
PyWzOdxjKpBrIF/EUhJOlywqrJ2X3kjyo2bbwtKDlaZmp54lD+kLM5FlClrD2VQS
3a/DTg4fJl4N3LON7NWBcN7STyQF82xO9UxJZo3R/9ILJUFI/lGExkKvgATP0H5k
SeTy36LssUzAKh3ntLFlosS88Zj0qnAHY7S42jtM+kAiMFsRpvAFDsYCA0irhpuF
3dvd6qJ2gHN99ZwExEWN57kci57q13XRcrHedUTnQn3iV2t93Jm8PYMo6oCTjcVM
ZcFwgbg4/EMxsvYDNEeyrPsiBsse3RdHHF9mudMaotoRsaS8I8nkvof/uZS2+F0g
StRf571oe2XyFR7SOqkt6dhrJKyXWERHrVkY8SFlcN7ONGCoQPHzPKTDKCOM/icz
Q0CgFzzr6juwcqajuUpLXhZI9LK8yIySxZ2frHI2vDSANGupi5LAuBft7HZT9SQB
jLMi6Et8Vcad+qMUu2WFbm5PEn4KPJ2VMAwwCgYIKwYBBQUHAwE=
-----END TRUSTED CERTIFICATE-----
"""

# Public CPython fixture: https://raw.githubusercontent.com/python/cpython/3.11/Lib/test/certdata/revocation.crl
PUBLIC_CRL = b"""-----BEGIN X509 CRL-----
MIICJjCBjwIBATANBgkqhkiG9w0BAQsFADBNMQswCQYDVQQGEwJYWTEmMCQGA1UE
CgwdUHl0aG9uIFNvZnR3YXJlIEZvdW5kYXRpb24gQ0ExFjAUBgNVBAMMDW91ci1j
YS1zZXJ2ZXIXDTIxMDMxNzA4NDgyMFoXDTQwMDUxNjA4NDgyMFqgDjAMMAoGA1Ud
FAQDAgEAMA0GCSqGSIb3DQEBCwUAA4IBgQCd2GrHb4zr2R8eK7YMHwlkgICxbWP1
4nuEi55yzUcmMcCZJ6ZQV3yYqTlAULGQ9qWAUdhsyH+yu3hRKFKHQv0DAdKKxgow
66YasAQQ99DskXOPxmRoIA7qtIWZbLtBwHQJWh+uUFlTdUXitGIX5Xie74xu5YIr
moa3QeuZyG5+gigSTUyst5T/J/cHfBzlAJLc2k3Ty4EPYXKHCVnrZWJbRmxq199l
A7S+eBb9qWXSYXCn6v+EZ76pUS3u/66kZ86PO3h9294BzdhxbCJ27dQXNHw6owe2
Iyiv0aWx+TNSGSf4yCqaYTH6RtEoviI3h/inVFHNGgjlMzdaGw/0I3bkB0rt2WSR
Vck37HnXvQvVEkgO/39C0WKZus6m4gmOgZcbJbXaR8uIR5Hmw3SEyGEPEIBu6tXV
BLJOSOSu2vVUH5GUIrpvK9FTySKYa+MGryoPasuqZNfwpaXK+ON2G6QsmcXPWZY0
Dry6t0w2geW6UYVGmb831i8ZP3JVVVwcwi0=
-----END X509 CRL-----
"""


# Deliberately invalid noncertificate payloads: setup must not parse these as CAs.
SYNTHETIC_NONCERTIFICATE_BLOCKS = tuple(
    b'-----BEGIN '+label+b'-----\n%%%not-certificate-data%%%\n-----END '+label+b'-----\n'
    for label in (b'CERTIFICATE REQUEST', b'NEW CERTIFICATE REQUEST',
                  b'TRUSTED CERTIFICATE REQUEST', b'CERTIFICATE CHAIN',
                  b'TRUSTED CERTIFICATE CHAIN', b'CERTIFICATE-REQUEST',
                  b'TRUSTED CERTIFICATE-REQUEST')
)
DECORATIVE_CERTIFICATE_COMMENTS = (
    b'# -----BEGIN CERTIFICATE-----\n# -----END CERTIFICATE-----\n'
    b' \t# -----BEGIN TRUSTED CERTIFICATE-----\n# -----END TRUSTED CERTIFICATE-----\n'
    b'decoration: -----BEGIN CERTIFICATE----- and -----END CERTIFICATE----- \xff\n'
)


def profile_fields(stderr):
    # The adapter emits before spawn; descendants can forge later duplicates.
    line=next(line for line in stderr.splitlines() if line.startswith('agent-sandbox: seatbelt_profile='))
    return dict(item.split('=',1) for item in line.split() if '=' in item)


def retain_kernel_evidence(name, result, policy_root=None):
    """Optional trusted-parent raw output and policy retention for synthetic tests."""
    destination=os.getenv('AGENT_SANDBOX_EVIDENCE_DIR')
    if not destination: return
    directory=Path(tempfile.mkdtemp(prefix=name.rsplit('.',1)[-1]+'-',dir=destination))
    (directory/'raw.json').write_text(json.dumps(dict(argv=result.args,exit=result.returncode,
        stdout=result.stdout,stderr=result.stderr),indent=2))
    if policy_root is None:
        line=next((line for line in result.stderr.splitlines() if line.startswith('agent-sandbox: state=')),None)
        if line: policy_root=Path(line.split('=',1)[1])
    if policy_root is not None:
        for name in ('boundary.json','srt.json','seatbelt.sb','seatbelt.source.sb',
                     'control-srt.json','control-seatbelt.sb','control-seatbelt.source.sb','materialization-probe.py'):
            source=policy_root/name
            if source.is_file(): shutil.copyfile(source,directory/name)
    if 'agent-sandbox: seatbelt_profile=' in result.stderr:
        (directory/'first-adapter-record.json').write_text(json.dumps(profile_fields(result.stderr),indent=2))


class SetupTests(unittest.TestCase):
    def test_later_child_hash_record_cannot_replace_adapter_record(self):
        stream=('agent-sandbox: seatbelt_profile=/first profile_sha256=original source_sha256=source file-backed\n'
                'read boundary verified; starting runner\n'
                'agent-sandbox: seatbelt_profile=/forged profile_sha256=forged source_sha256=forged file-backed\n')
        self.assertEqual(profile_fields(stream)['profile_sha256'],'original')
        self.assertEqual(profile_fields(stream)['source_sha256'],'source')

    def test_invalid_entries_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/'denies.json'
            for doc in ([], {}, ['relative'], ['/no-such-agent-sandbox-path']):
                p.write_text(json.dumps(doc))
                with self.assertRaises(ValueError):
                    sandbox.load_denies(p)

    def test_symlink_canonicalization(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p/'secret').write_text('secret')
            (p/'alias').symlink_to(p/'secret')
            (p/'list').write_text(json.dumps([str(p/'alias')]))
            denies, missing = sandbox.load_denies(p/'list')
            self.assertEqual(missing,{})
            self.assertTrue(sandbox.is_denied(p/'secret', denies))
            self.assertTrue(sandbox.is_denied(p/'alias', denies))

    def test_preexisting_hardlink_is_explicitly_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p/'secret').write_text('secret')
            os.link(p/'secret',p/'other-name')
            (p/'list').write_text(json.dumps([str(p/'secret')]))
            with self.assertRaisesRegex(ValueError,'hardlinked'):
                sandbox.load_denies(p/'list')

    def test_prepared_prompt_required(self):
        with unittest.mock.patch.object(shutil, 'which', return_value='/bin/codex-agent-run'):
            for extra in ([], ['--prompt-file','-'], ['--prompt','a','--prompt-file','x']):
                with self.assertRaises(ValueError):
                    sandbox.parse_runner(['codex-agent-run','--provider','mimo',*extra],Path.cwd())
            _,options,command = sandbox.parse_runner(['codex-agent-run','--provider','mimo','--thread-source','--prompt','--prompt','actual task'],Path.cwd())
            self.assertEqual(command[options['_prompt_index']+1],'actual task')

    def test_fifo_denial_is_rejected_without_open(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); os.mkfifo(p/'fifo'); (p/'list').write_text(json.dumps([str(p/'fifo')]))
            with self.assertRaisesRegex(ValueError,'regular file'):
                sandbox.load_denies(p/'list')

    def test_denied_directory_symlink_to_fifo_is_rejected_without_open(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory).resolve(); (p/'denied').mkdir(); os.mkfifo(p/'fifo')
            (p/'denied/pipe-link').symlink_to(p/'fifo')
            (p/'list').write_text(json.dumps([str(p/'denied')]))
            original_open = Path.open
            def guarded_open(path,*args,**kwargs):
                if path.resolve() == p/'fifo':
                    raise AssertionError('must not open a special-file target')
                return original_open(path,*args,**kwargs)
            with unittest.mock.patch.object(Path,'open',guarded_open):
                with self.assertRaisesRegex(ValueError,'regular file'):
                    sandbox.load_denies(p/'list')

    @unittest.skipUnless(platform.system() == 'Darwin','Seatbelt query requires macOS')
    def test_direct_internal_entry_cannot_fake_seatbelt_with_unix_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); secret=p/'secret'; secret.write_text('secret'); secret.chmod(0)
            probe=p/'probe'; probe.write_bytes(b'agent-sandbox-probe')
            runner=p/'codex-agent-run'; runner.write_text('#!/bin/sh\necho DIRECT_VERIFY_BYPASS\n'); runner.chmod(0o755)
            manifest=p/'boundary.json'; command=[str(runner)]
            manifest.write_text(json.dumps(dict(denies=[str(secret)],probe=str(probe),command=command)))
            result=subprocess.run([str(ROOT/'scripts/agent-sandbox'),'--verify',str(manifest),*command],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertNotIn('DIRECT_VERIFY_BYPASS',result.stdout)
            self.assertIn('effective Seatbelt policy',result.stderr)
            secret.chmod(0o600)

    def test_original_claude_parent_settings_remain_effective(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory).resolve(); cwd=p/'repo/sub'; cwd.mkdir(parents=True)
            settings=p/'repo/.claude/settings.json'; settings.parent.mkdir()
            settings.write_text(json.dumps(dict(sandbox=dict(filesystem=dict(denyWrite=[str(cwd/'blocked')])))))
            with unittest.mock.patch.dict(os.environ,HOME=str(p/'home'),CLAUDE_CONFIG_DIR=str(p/'custom')):
                roots,blocked=sandbox.write_boundary('claude','mimo',cwd,[])
                self.assertIn(str(cwd/'blocked'),blocked)
                settings.write_text(json.dumps(dict(sandbox=dict(filesystem=dict(denyWrite=['./blocked'])))))
                with self.assertRaisesRegex(ValueError,'relative'):
                    sandbox.write_boundary('claude','mimo',cwd,[])

    def test_collection_arguments_do_not_expand_outputs_or_write_boundary(self):
        cwd=Path.cwd()
        with unittest.mock.patch.object(shutil, 'which', return_value='/bin/codex-agent-run'):
            _,options,command=sandbox.parse_runner(['codex-agent-run','--provider','mimo','--prompt','task',
                '--canary-file','proof.txt','--canary-expected','expected.txt',
                '--artifact','review1.md','--artifact','review2.md'],cwd)
        self.assertEqual(command.count('--artifact'),2)
        self.assertEqual(options['--canary-file'],str(cwd/'proof.txt'))
        self.assertFalse({'--output','--stderr','--last-message'} & options.keys())

    def test_result_contract_rejects_denied_canary_and_unwritable_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();work=root/'work';work.mkdir()
            runner=root/'codex-agent-run';runner.write_text('stub')
            (root/'agent-run-result.py').write_text('stub')
            proof=root/'proof';proof.write_text('token')
            expected=root/'expected';expected.write_text('token')
            options={'--canary-file':str(proof),'--canary-expected':str(expected)}
            base=[str(runner)]
            sandbox.validate_result_contract(options | {"_artifacts":[str(work/'report.md')]},base,[str(work)],[],[])
            for path in (root/'outside.md',work/'denied/report.md',work/'.git/report.md'):
                with self.assertRaisesRegex(ValueError,'outside retained write roots|artifact is denied'):
                    sandbox.validate_result_contract(options | {"_artifacts":[str(path)]},base,[str(work)],
                        [str(work/'.git')],[str(work/'denied')])
            with unittest.mock.patch.object(shutil, 'which', return_value=str(runner)):
                _, literal, command = sandbox.parse_runner([str(runner),'--provider','mimo','--prompt','--detail',
                    '--artifact',str(root/'outside.md')],work)
                self.assertFalse(literal['_detail'])
                with self.assertRaisesRegex(ValueError,'outside retained write roots'):
                    sandbox.validate_result_contract(literal,command,[str(work)],[],[])
            for denied in (proof,expected):
                with self.assertRaisesRegex(ValueError,'required setup input is denied'):
                    sandbox.validate_result_contract(options,base,[str(work)],[],[str(denied)])

    def test_artifact_leaf_symlinks_are_rejected_before_canonicalization(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();work=root/'work';work.mkdir()
            existing=work/'existing';existing.write_text('old')
            for target in (work/'missing', root/'outside', existing):
                link=work/'artifact';link.symlink_to(target)
                with unittest.mock.patch.object(shutil,'which',return_value='/bin/codex-agent-run'):
                    with self.assertRaisesRegex(ValueError,'not a symlink'):
                        sandbox.parse_runner(['codex-agent-run','--provider','mimo','--prompt','task',
                            '--artifact',str(link)],work)
                link.unlink()

    def test_raw_native_options_cannot_change_policy(self):
        cwd = Path.cwd()
        with unittest.mock.patch.object(shutil, 'which', return_value='/bin/codex-agent-run'):
            for option in ('--', '--persist', '--resume', '--sandbox', '--config'):
                with self.assertRaises(ValueError):
                    sandbox.parse_runner(['codex-agent-run', '--provider', 'mimo', option], cwd)

    @unittest.skipUnless(platform.system() == 'Darwin' and shutil.which('node'), 'macOS/Node preflight')
    def test_preflight_rejects_standalone_srt_without_executing_it(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); (p/'bin').mkdir(); (p/'work').mkdir()
            (p/'secret').write_text('synthetic')
            (p/'denies.json').write_text(json.dumps([str(p/'secret')]))
            marker=p/'must-not-execute'
            srt=p/'bin/srt'; srt.write_text(f'#!/bin/sh\ntouch "{marker}"\necho 0.0.79\n'); srt.chmod(0o755)
            runner=p/'bin/codex-agent-run'; runner.write_text('#!/bin/sh\nexit 0\n'); runner.chmod(0o755)
            env={**os.environ,'PATH':str(p/'bin')+':'+os.environ['PATH'],
                 'AGENT_TOOLS_FILE':str(ROOT/'scripts/agent-tools.zsh')}
            result=subprocess.run([str(ROOT/'scripts/agent-sandbox'),'--check','--cwd',str(p/'work'),
                '--deny-list',str(p/'denies.json'),'--','codex-agent-run','--provider','mimo','--prompt','test'],
                env=env,capture_output=True,text=True,timeout=20)
            self.assertNotEqual(result.returncode,0)
            self.assertNotIn('setup_status=ok',result.stdout)
            self.assertIn('reinstall with install-agent-sandbox.sh',result.stderr)
            self.assertFalse(marker.exists())



class CodexCATests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='codex-ca-', dir='/private/tmp')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.cwd = self.root/'work'; self.cwd.mkdir()
        self.ca = self.cwd/'ca.pem'; self.ca.write_bytes(PUBLIC_CA)
        self.default = self.root/'default.pem'; self.default.write_bytes(PUBLIC_CA)
        self.default_patch = unittest.mock.patch.object(sandbox, 'DEFAULT_CODEX_CA_CERTIFICATE', str(self.default))
        self.default_patch.start(); self.addCleanup(self.default_patch.stop)

    def prepare(self, env, denies=(), route='https://example.com/v1'):
        sandbox.prepare_codex_ca(route, self.cwd, env, list(map(str, denies)))

    def rejected(self, env, prefix, *, denies=(), reason=None):
        before = dict(env)
        with self.assertRaises(ValueError) as caught:
            self.prepare(env, denies)
        text = str(caught.exception)
        self.assertTrue(text.startswith(prefix + ':'), text)
        self.assertIn('source=', text); self.assertIn('declared=', text)
        if reason: self.assertIn(reason, text)
        self.assertEqual(env, before)
        self.assertNotIn(PUBLIC_CA.splitlines()[1].decode(), text)
        return text

    def test_codex_priority_ignores_every_lower_input_and_parent(self):
        bad = self.root/'bad'; bad.write_bytes(b'not PEM')
        for lower in (self.root/'missing', bad, self.default):
            with self.subTest(lower=lower):
                parent = {'CODEX_CA_CERTIFICATE': 'ca.pem', 'SSL_CERT_FILE': str(lower)}
                env = dict(parent)
                original = os.open
                with unittest.mock.patch.object(os, 'open', wraps=original) as opened:
                    self.prepare(env, [lower])
                self.assertEqual([call.args[0] for call in opened.call_args_list], [self.ca])
                self.assertEqual(env, {**parent, 'CODEX_CA_CERTIFICATE': str(self.ca)})
                self.assertEqual(parent['CODEX_CA_CERTIFICATE'], 'ca.pem')

    def test_bad_selected_override_never_falls_through(self):
        bad = self.root/'invalid'; bad.write_bytes(b'not PEM')
        for key in ('CODEX_CA_CERTIFICATE', 'SSL_CERT_FILE'):
            for selected, denies, prefix in (
                (self.root/'absent', (), 'required Codex CA input missing'),
                (self.ca, (self.ca,), 'required Codex CA input is denied'),
                (bad, (), 'invalid Codex CA bundle')):
                with self.subTest(key=key, selected=selected):
                    env = {key: str(selected)}
                    if key == 'CODEX_CA_CERTIFICATE': env['SSL_CERT_FILE'] = str(self.default)
                    else: env['CODEX_CA_CERTIFICATE'] = ''
                    text = self.rejected(env, prefix, denies=denies)
                    self.assertIn('source='+repr(key), text)
                    self.assertIn(repr(str(selected)), text)

    def test_ssl_fallback_and_exact_empty_codex(self):
        for codex in (None, ''):
            env = {'SSL_CERT_FILE': 'ca.pem'}
            if codex is not None: env['CODEX_CA_CERTIFICATE'] = codex
            self.prepare(env)
            self.assertEqual(env['SSL_CERT_FILE'], str(self.ca))
            self.assertEqual(env.get('CODEX_CA_CERTIFICATE'), codex)

    def test_default_with_unset_and_empty_overrides(self):
        for codex in (None, ''):
            for ssl_value in (None, ''):
                with self.subTest(codex=codex, ssl=ssl_value):
                    env = {}
                    if codex is not None: env['CODEX_CA_CERTIFICATE'] = codex
                    if ssl_value is not None: env['SSL_CERT_FILE'] = ssl_value
                    self.prepare(env)
                    self.assertEqual(env['CODEX_CA_CERTIFICATE'], str(self.default))
                    self.assertEqual(env.get('SSL_CERT_FILE'), ssl_value)

    def test_default_failure_is_located(self):
        for kind in ('missing', 'denied', 'invalid'):
            with self.subTest(kind=kind):
                self.default.write_bytes(PUBLIC_CA)
                denies = ()
                if kind == 'missing': self.default.unlink()
                if kind == 'denied': denies = (self.default,)
                if kind == 'invalid': self.default.write_bytes(b'invalid')
                prefix = {'missing':'required Codex CA input missing', 'denied':'required Codex CA input is denied',
                          'invalid':'invalid Codex CA bundle'}[kind]
                text = self.rejected({}, prefix, denies=denies)
                self.assertIn("source='system-default'", text)
                self.assertIn(repr(str(self.default)), text)

    def test_selected_whitespace_is_literal_for_both_variables(self):
        for key in ('CODEX_CA_CERTIFICATE', 'SSL_CERT_FILE'):
            with self.subTest(key=key):
                path = self.cwd/'   '
                text = self.rejected({key: '   '}, 'required Codex CA input missing')
                self.assertIn("declared='   '", text)
                path.write_bytes(PUBLIC_CA)
                env = {key: '   '}; self.prepare(env)
                self.assertEqual(env[key], str(path))
                path.unlink()

    def test_relative_alias_and_literal_tilde_use_envelope_cwd(self):
        (self.cwd/'alias').symlink_to(self.ca)
        (self.cwd/'~').mkdir(); literal = self.cwd/'~/ca.pem'; literal.write_bytes(PUBLIC_CA)
        with unittest.mock.patch.object(Path, 'cwd', return_value=self.root/'different-caller-cwd'):
            for declared, expected in [('ca.pem', self.ca), ('alias', self.ca), ('~/ca.pem', literal)]:
                with self.subTest(declared=declared):
                    env = {'CODEX_CA_CERTIFICATE': declared}; self.prepare(env)
                    self.assertEqual(env['CODEX_CA_CERTIFICATE'], str(expected))

    def test_direct_alias_and_ancestor_denials_precede_open(self):
        (self.cwd/'alias').symlink_to(self.ca)
        for selected, denied in [('ca.pem', self.ca), ('alias', self.ca), ('alias', self.cwd)]:
            with self.subTest(selected=selected, denied=denied), \
                 unittest.mock.patch.object(os, 'open', side_effect=AssertionError('must not open denied CA')):
                text = self.rejected({'CODEX_CA_CERTIFICATE': selected}, 'required Codex CA input is denied', denies=[denied])
                self.assertIn('canonical='+repr(str(self.ca)), text)

    def test_existing_deny_expansion_covers_external_ca_target(self):
        denied = self.root/'denied'; denied.mkdir()
        (denied/'ca-link').symlink_to(self.ca)
        listing = self.root/'denies.json'; listing.write_text(json.dumps([str(denied)]))
        denies, _ = sandbox.load_denies(listing)
        with unittest.mock.patch.object(os, 'open', side_effect=AssertionError('must not open expanded deny')):
            self.rejected({'CODEX_CA_CERTIFICATE': str(self.ca)}, 'required Codex CA input is denied', denies=denies)

    def test_broken_cycle_and_nul_are_located(self):
        (self.cwd/'broken').symlink_to('absent')
        (self.cwd/'cycle').symlink_to('cycle')
        for selected, prefix, cause in [('broken','required Codex CA input missing','errno=2'),
                ('cycle','cannot read required Codex CA input','cause='),
                ('bad\0path','cannot read required Codex CA input','ValueError'),
                ('bad\ud800path','cannot read required Codex CA input','UnicodeEncodeError')]:
            with self.subTest(selected=selected):
                text = self.rejected({'CODEX_CA_CERTIFICATE': selected}, prefix)
                self.assertIn(cause, text); self.assertNotIn('canonical=', text)

    def test_special_files_and_alias_fail_before_open(self):
        os.mkfifo(self.cwd/'fifo'); (self.cwd/'fifo-alias').symlink_to('fifo')
        for selected in ('.', 'fifo', 'fifo-alias'):
            with self.subTest(selected=selected), \
                 unittest.mock.patch.object(os, 'open', side_effect=AssertionError('must not open special file')):
                self.rejected({'CODEX_CA_CERTIFICATE': selected}, 'required Codex CA input is not a regular file')

    def test_open_errors_remain_read_failures(self):
        for number in (errno.EACCES, errno.EPERM, errno.ELOOP):
            with self.subTest(errno=number), unittest.mock.patch.object(os, 'open', side_effect=OSError(number, 'fixture error')):
                text = self.rejected({'CODEX_CA_CERTIFICATE':'ca.pem'}, 'cannot read required Codex CA input')
                self.assertIn('errno='+str(number), text)

    def test_post_open_special_file_does_not_read_and_closes_fd(self):
        descriptors = []
        real_open = os.open
        def opened(*args):
            fd = real_open(*args); descriptors.append(fd); return fd
        fake = unittest.mock.Mock(st_mode=stat.S_IFIFO)
        with unittest.mock.patch.object(os, 'open', side_effect=opened) as opening, \
             unittest.mock.patch.object(os, 'fstat', return_value=fake), \
             unittest.mock.patch.object(os, 'fdopen', side_effect=AssertionError('must not read special file')):
            self.rejected({'CODEX_CA_CERTIFICATE':'ca.pem'}, 'required Codex CA input is not a regular file')
        self.assertEqual(opening.call_args.args[1], os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
        with self.assertRaises(OSError): os.fstat(descriptors[0])

    def test_read_failure_closes_fd(self):
        descriptors = []
        real_open, real_fdopen = os.open, os.fdopen
        def opened(*args):
            fd = real_open(*args); descriptors.append(fd); return fd
        def stream(fd, mode):
            owned = real_fdopen(fd, mode)
            failing = unittest.mock.MagicMock()
            failing.__enter__.return_value = failing
            failing.__exit__.side_effect = lambda *args: owned.close()
            failing.read.side_effect = PermissionError(errno.EPERM, 'read fixture')
            return failing
        with unittest.mock.patch.object(os, 'open', side_effect=opened), \
             unittest.mock.patch.object(os, 'fdopen', side_effect=stream):
            text = self.rejected({'CODEX_CA_CERTIFICATE':'ca.pem'}, 'cannot read required Codex CA input')
        self.assertIn('errno=1', text)
        with self.assertRaises(OSError): os.fstat(descriptors[0])

    def test_valid_ordinary_trusted_mixed_crl_and_comments_preserve_original(self):
        ordinary = PUBLIC_CA + b'\n'
        trusted = PUBLIC_TRUSTED_CA + b'\n'
        crl = PUBLIC_CRL + b'\n'
        bundles = [ordinary, ordinary*2, trusted, trusted*2, ordinary+trusted, trusted+ordinary]
        bundles += [crl+cert+crl+cert+crl for cert in (ordinary, trusted)]
        bundles += [b'# public non-ASCII comment \xff\n'+trusted+ordinary+b'\n# \xfe\n']
        for data in bundles:
            with self.subTest(size=len(data)):
                self.ca.write_bytes(data)
                env = {'CODEX_CA_CERTIFICATE':'ca.pem'}; self.prepare(env)
                self.assertEqual(env['CODEX_CA_CERTIFICATE'], str(self.ca))
                self.assertEqual(self.ca.read_bytes(), data)
        # AUX is genuine additional payload, not an ordinary certificate relabel.
        import base64
        def der(data): return base64.b64decode(b''.join(data.splitlines()[1:-1]))
        self.assertTrue(der(PUBLIC_TRUSTED_CA).startswith(der(PUBLIC_CA)))
        self.assertGreater(len(der(PUBLIC_TRUSTED_CA)), len(der(PUBLIC_CA)))

    def test_noncertificate_labels_around_ordinary_and_trusted_certificates(self):
        crl = PUBLIC_CRL + b'\n'
        for other in SYNTHETIC_NONCERTIFICATE_BLOCKS:
            for cert in (PUBLIC_CA+b'\n', PUBLIC_TRUSTED_CA+b'\n'):
                bundles = (other+cert, cert+other, crl+other+cert+crl+other+cert+crl)
                for position, data in enumerate(bundles):
                    with self.subTest(label=other.splitlines()[0], trusted=b'TRUSTED' in cert,
                                      position=position):
                        self.ca.write_bytes(data)
                        env = {'CODEX_CA_CERTIFICATE':'ca.pem'}; self.prepare(env)
                        self.assertEqual(env['CODEX_CA_CERTIFICATE'], str(self.ca))
                        self.assertEqual(self.ca.read_bytes(), data)
            data = other+PUBLIC_CA+b'\n'+crl+other+PUBLIC_TRUSTED_CA+b'\n'+other
            with self.subTest(label=other.splitlines()[0], mixed=True):
                self.ca.write_bytes(data)
                self.prepare({'CODEX_CA_CERTIFICATE':'ca.pem'})
                self.assertEqual(self.ca.read_bytes(), data)

    def test_decorative_certificate_comments_outside_blocks_are_ignored(self):
        comments = DECORATIVE_CERTIFICATE_COMMENTS
        for cert in (PUBLIC_CA+b'\n', PUBLIC_TRUSTED_CA+b'\n'):
            for data in (comments+cert, cert+comments,
                         comments+PUBLIC_CRL+b'\n'+cert+comments+cert+PUBLIC_CRL):
                with self.subTest(trusted=b'TRUSTED' in cert, size=len(data)):
                    self.ca.write_bytes(data)
                    self.prepare({'CODEX_CA_CERTIFICATE':'ca.pem'})
                    self.assertEqual(self.ca.read_bytes(), data)

    def test_noncertificate_text_inside_active_block_is_kept_for_validation(self):
        for cert in (PUBLIC_CA, PUBLIC_TRUSTED_CA):
            begin, payload = cert.split(b'\n', 1)
            for extra in (SYNTHETIC_NONCERTIFICATE_BLOCKS[0],
                          b'# -----BEGIN CERTIFICATE-----\n', b'unknown text \xff\n'):
                with self.subTest(trusted=b'TRUSTED' in begin, extra=extra.splitlines()[0]):
                    data = begin+b'\n'+extra+payload
                    self.ca.write_bytes(data)
                    if b'\xff' in extra:
                        self.rejected({'CODEX_CA_CERTIFICATE':'ca.pem'}, 'invalid Codex CA bundle',
                                      reason='UnicodeDecodeError')
                        continue
                    context = unittest.mock.Mock()
                    with unittest.mock.patch.object(sandbox.ssl, 'SSLContext', return_value=context):
                        self.prepare({'CODEX_CA_CERTIFICATE':'ca.pem'})
                    expected = data.decode().replace('TRUSTED CERTIFICATE', 'CERTIFICATE')
                    self.assertEqual(context.load_verify_locations.call_count, 1)
                    actual = context.load_verify_locations.call_args.kwargs['cadata']
                    self.assertEqual(hashlib.sha256(actual.encode()).hexdigest(),
                                     hashlib.sha256(expected.encode()).hexdigest())

    def test_validator_receives_individual_normalized_certificates_never_crls(self):
        context = unittest.mock.Mock()
        self.ca.write_bytes(PUBLIC_CRL+b'\n'+PUBLIC_TRUSTED_CA+b'\n'+PUBLIC_CA+b'\n'+PUBLIC_CRL)
        with unittest.mock.patch.object(sandbox.ssl, 'SSLContext', return_value=context) as contexts:
            self.prepare({'CODEX_CA_CERTIFICATE':'ca.pem'})
        self.assertEqual(contexts.call_count, 2)
        values = [call.kwargs['cadata'] for call in context.load_verify_locations.call_args_list]
        expected = [PUBLIC_TRUSTED_CA.decode().replace('TRUSTED CERTIFICATE','CERTIFICATE').rstrip('\n')+'\n',
                    PUBLIC_CA.decode().rstrip('\n')+'\n']
        self.assertEqual([hashlib.sha256(value.encode()).hexdigest() for value in values],
                         [hashlib.sha256(value.encode()).hexdigest() for value in expected])
        self.assertTrue(all('CRL' not in value and 'TRUSTED' not in value for value in values))

    def test_empty_nonpem_and_genuine_crl_only_fail(self):
        for data in (b'', b'not PEM', PUBLIC_CRL, DECORATIVE_CERTIFICATE_COMMENTS,
                     *SYNTHETIC_NONCERTIFICATE_BLOCKS,
                     PUBLIC_CRL+b'\n'+DECORATIVE_CERTIFICATE_COMMENTS+b''.join(SYNTHETIC_NONCERTIFICATE_BLOCKS)):
            with self.subTest(data_length=len(data)):
                self.ca.write_bytes(data)
                self.rejected({'CODEX_CA_CERTIFICATE':'ca.pem'}, 'invalid Codex CA bundle', reason='no certificate blocks')

    def test_malformed_delimiters_for_both_labels(self):
        for name in (b'CERTIFICATE', b'TRUSTED CERTIFICATE'):
            begin = b'-----BEGIN '+name+b'-----\n'
            end = b'-----END '+name+b'-----\n'
            other = b'TRUSTED CERTIFICATE' if name == b'CERTIFICATE' else b'CERTIFICATE'
            cases = [(begin+b'AAAA\n', 'incomplete '+name.decode()+' block'),
                     (begin[:-3]+b'\n', 'malformed '+name.decode()+' delimiter'),
                     (begin[5:], 'malformed '+name.decode()+' delimiter'),
                     (begin+b'AAAA\n'+end[:-3]+b'\n', 'malformed '+name.decode()+' delimiter'),
                     *[(marker, 'malformed '+name.decode()+' delimiter')
                       for edge in (b' ', b'\t', b'\v', b'\f')
                       for marker in (edge+begin, begin.rstrip(b'\n')+edge+b'\n',
                                      begin+b'AAAA\n'+edge+end,
                                      begin+b'AAAA\n'+end.rstrip(b'\n')+edge+b'\n')],
                     (begin.rstrip(b'\n')+b'junk\n', 'malformed '+name.decode()+' delimiter'),
                     (begin+b'AAAA\n'+end.rstrip(b'\n')+b'junk\n', 'malformed '+name.decode()+' delimiter'),
                     (end, 'orphan certificate END'), (begin+begin+end, 'nested certificate BEGIN'),
                     (begin+b'-----END '+other+b'-----\n', 'mismatched certificate labels')]
            for data, reason in cases:
                for surrounding in (b'', PUBLIC_CA+b'\n'+PUBLIC_CRL+b'\n'):
                    with self.subTest(label=name, reason=reason, companion=bool(surrounding)):
                        self.ca.write_bytes(surrounding+data)
                        self.rejected({'CODEX_CA_CERTIFICATE':'ca.pem'}, 'invalid Codex CA bundle', reason=reason)

    def test_invalid_payloads_and_every_companion_in_both_orders(self):
        for name in (b'CERTIFICATE', b'TRUSTED CERTIFICATE'):
            for payload in (b'%%%not-base64%%%', b'YWJjZA==', b'\xffNON_ASCII_PRIVATE_PAYLOAD'):
                bad = b'-----BEGIN '+name+b'-----\n'+payload+b'\n-----END '+name+b'-----\n'
                for good in (PUBLIC_CA+b'\n', PUBLIC_TRUSTED_CA+b'\n'):
                    for crl in (b'', PUBLIC_CRL+b'\n'):
                        for data in (bad+crl+good, good+crl+bad):
                            with self.subTest(label=name, payload=payload[:1], length=len(data)):
                                self.ca.write_bytes(data)
                                text = self.rejected({'CODEX_CA_CERTIFICATE':'ca.pem'}, 'invalid Codex CA bundle')
                                self.assertIn(name.decode(), text)
                                self.assertIn('UnicodeDecodeError' if b'\xff' in payload else 'SSLError', text)
                                self.assertNotIn('PRIVATE_PAYLOAD', text)

    def test_parser_error_detail_is_bounded(self):
        error = sandbox.ssl.SSLError(1, 'fixture parse failure')
        error.reason = 'R'*400 + 'PRIVATE_PAYLOAD'
        context = unittest.mock.Mock()
        context.load_verify_locations.side_effect = error
        with unittest.mock.patch.object(sandbox.ssl, 'SSLContext', return_value=context):
            text = self.rejected({'CODEX_CA_CERTIFICATE':'ca.pem'}, 'invalid Codex CA bundle')
        self.assertIn('certificate 1 CERTIFICATE: SSLError: '+'R'*256, text)
        self.assertNotIn('R'*257, text)
        self.assertNotIn('PRIVATE_PAYLOAD', text)

    def test_http_does_not_inspect_or_mutate_ca(self):
        env = {'CODEX_CA_CERTIFICATE':'bad\0path', 'SSL_CERT_FILE':'missing'}
        before = dict(env)
        with unittest.mock.patch.object(os, 'open', side_effect=AssertionError('no HTTP CA read')):
            self.prepare(env, route='http://example.com/v1')
        self.assertEqual(env, before)

    def run_main(self, env, *, check, runtime='codex', denies=(), route='https://example.com/v1', subscription=None):
        home = self.root/'home'; config = home/'.codex'; config.mkdir(parents=True, exist_ok=True)
        (config/'config.toml').write_text('model = "synthetic-model"\nmodel_provider = "mock"\n[model_providers.mock]\nname = "mock"\nbase_url = "'+route+'"\nrequires_openai_auth = false\n')
        (config/'gpt-6-sol.config.toml').write_text('')
        provider = subscription or 'gpt-6-sol'
        if subscription:
            (config/'config.toml').write_text('model = "gpt-6.1-sol"\nmodel_reasoning_effort = "medium"\nsandbox_mode = "workspace-write"\n')
            shutil.copyfile(ROOT/f'codex-agent/profiles/{provider}/config.toml', config/f'{provider}.config.toml')
            auth = config/'auth.json'
            auth.write_text('{"synthetic":"subscription-login"}\n'); auth.chmod(0o600)
        listing = self.root/'list.json'; listing.write_text(json.dumps(list(map(str, denies or [self.root/'secret']))))
        (self.root/'secret').write_text('synthetic denied input')
        runner = self.root/(runtime+'-agent-run'); runner.write_text('synthetic runner')
        node, srt = self.root/'node', self.root/'srt'
        node.write_text('synthetic node'); srt.write_text('synthetic srt')
        bin_paths = {'python3':sys.executable, 'node':str(node), 'srt':str(srt), runtime+'-agent-run':str(runner)}
        private_env = {'HOME':str(home), 'AGENT_TOOLS_FILE':str(ROOT/'scripts/agent-tools.zsh'), **env}
        before = dict(private_env)
        helper = unittest.mock.Mock()
        helper.user_path.return_value = self.root/'absent-endpoints.json'
        helper.connection.return_value = {'base_url':route}
        if subscription:
            helper.connection.side_effect = AssertionError('subscription must not query a gateway key')
        stdout, stderr = io.StringIO(), io.StringIO()
        original_mkdtemp = tempfile.mkdtemp
        argv = ['agent-sandbox', *(['--check'] if check else []), '--cwd',str(self.cwd), '--deny-list',str(listing),
                '--',str(runner),'--provider',provider,'--prompt','synthetic task','--detail',
                '--output',str(self.root/'sink/result')]
        with contextlib.ExitStack() as stack:
            stack.enter_context(unittest.mock.patch.object(sys,'argv',argv))
            stack.enter_context(unittest.mock.patch.object(os,'environ',private_env))
            stack.enter_context(unittest.mock.patch.object(platform,'system',return_value='Darwin'))
            stack.enter_context(unittest.mock.patch.object(shutil,'which',side_effect=lambda name:bin_paths.get(name, str(runner) if name == str(runner) else None)))
            stack.enter_context(unittest.mock.patch.object(sandbox,'connection_helper',return_value=helper))
            if not subscription:
                stack.enter_context(unittest.mock.patch.object(sandbox,'write_boundary',return_value=([str(self.cwd)],[str(self.cwd/'.git')])))
            stack.enter_context(unittest.mock.patch.object(subprocess,'run',return_value=subprocess.CompletedProcess([],0,sandbox.SRT_VERSION,'')))
            stack.enter_context(unittest.mock.patch.object(tempfile,'mkdtemp',side_effect=lambda suffix=None,prefix=None,dir=None:original_mkdtemp(suffix=suffix,prefix=prefix,dir=self.root)))
            stack.enter_context(unittest.mock.patch.object(os,'chdir'))
            stack.enter_context(unittest.mock.patch.object(os,'umask'))
            stack.enter_context(unittest.mock.patch.object(os,'dup2'))
            execute = stack.enter_context(unittest.mock.patch.object(os,'execvpe'))
            stack.enter_context(contextlib.redirect_stdout(stdout)); stack.enter_context(contextlib.redirect_stderr(stderr))
            try:
                sandbox.main()
            except ValueError as error:
                print('agent-sandbox: '+str(error), file=sys.stderr)
                code = 1
            else:
                code = 0
        self.assertEqual(private_env, before)
        if subscription:
            helper.connection.assert_not_called()
        return code, stdout.getvalue(), stderr.getvalue(), execute

    def test_subscription_check_and_launch_classification_and_staging(self):
        for provider, model, effort in GPT_PROFILES:
            for check in (True, False):
                with self.subTest(provider=provider, check=check):
                    code, out, err, execute = self.run_main({'CODEX_CA_CERTIFICATE':str(self.ca)},
                                                          check=check, subscription=provider)
                    self.assertEqual(code, 0, err)
                    if check:
                        self.assertEqual(out, 'setup_status=ok\n'); execute.assert_not_called()
                        continue
                    execute.assert_called_once()
                    child = execute.call_args.args[2]
                    home = Path(child['AGENT_SANDBOX_CODEX_HOME']); state = home.parent
                    config = sandbox.tomllib.loads((home/'config.toml').read_text())
                    self.assertEqual((config['model'], config['model_reasoning_effort']), (model, effort))
                    self.assertNotIn('model_provider', config)
                    self.assertEqual((home/f'{provider}.config.toml').read_text(), '')
                    self.assertEqual((home/'auth.json').read_bytes(), (self.root/'home/.codex/auth.json').read_bytes())
                    self.assertEqual((home/'auth.json').stat().st_mode & 0o777, 0o600)
                    self.assertEqual(state.stat().st_mode & 0o777, 0o700)
                    self.assertEqual(child['CODEX_CA_CERTIFICATE'], str(self.ca))
                    manifest = json.loads((state/'boundary.json').read_text())
                    command = manifest['command']
                    self.assertEqual(command[command.index('--provider')+1], provider)
                    settings = json.loads((state/'srt.json').read_text())
                    self.assertEqual(settings['network'], {'allowedDomains':['chatgpt.com:443', 'auth.openai.com:443',
                        'api.openai.com:443', 'chatgpt.com:443'], 'deniedDomains':[], 'strictAllowlist':True,
                        'allowLocalBinding':False, 'allowAllUnixSockets':False, 'allowUnixSockets':[]})
                    fs = settings['filesystem']
                    self.assertEqual(fs['allowRead'], [])
                    self.assertEqual(fs['denyRead'], [{'path':str(self.root/'secret'), 'literal':True}])
                    self.assertEqual(fs['allowWrite'], [{'path':str(path), 'literal':True}
                        for path in (state, self.cwd, self.root/'sink/result')])
                    for path in [self.cwd/name for name in ('.git', '.codex', '.agents', '.aws')] + [
                            home/'config.toml', home/f'{provider}.config.toml']:
                        self.assertIn({'path':str(path), 'literal':True}, fs['denyWrite'])
                    for key in ('allowAppleEvents', 'enableWeakerNestedSandbox', 'enableWeakerNetworkIsolation'):
                        self.assertIs(settings[key], False)

    def test_subscription_denied_selected_card_stops_check_and_launch(self):
        for provider, _, _ in GPT_PROFILES:
            card = self.root / f'home/.codex/{provider}.config.toml'
            for check in (True, False):
                with self.subTest(provider=provider, check=check):
                    code, out, err, execute = self.run_main({'CODEX_CA_CERTIFICATE':str(self.ca)}, check=check,
                        subscription=provider, denies=[card])
                    self.assertEqual(code, 1)
                    self.assertNotIn('setup_status=ok', out)
                    self.assertIn(str(card), err)
                    execute.assert_not_called()

    def test_check_and_launch_reject_same_ca_without_exec_or_success(self):
        bad = self.cwd/'bad'; bad.write_bytes(b'invalid')
        for path, denies, prefix in [(self.cwd/'missing', (), 'required Codex CA input missing'),
                (self.ca, [self.ca], 'required Codex CA input is denied'), (bad, (), 'invalid Codex CA bundle')]:
            diagnostics = []
            for check in (True, False):
                with self.subTest(path=path, check=check):
                    code, out, err, execute = self.run_main({'CODEX_CA_CERTIFICATE':str(path)}, check=check, denies=denies)
                    self.assertEqual(code, 1); self.assertEqual(out, '')
                    self.assertIn('agent-sandbox: '+prefix+':', err); self.assertIn(repr(str(path)), err)
                    self.assertNotIn('setup_status=ok', out); execute.assert_not_called()
                    diagnostics.append(err)
            self.assertEqual(diagnostics[0], diagnostics[1])

    def test_check_and_launch_share_selected_ca_and_unchanged_policy(self):
        code, out, err, execute = self.run_main({'CODEX_CA_CERTIFICATE':'ca.pem','SSL_CERT_FILE':'ignored'}, check=True)
        self.assertEqual((code,out,err), (0,'setup_status=ok\n','')); execute.assert_not_called()
        code, out, err, execute = self.run_main({'CODEX_CA_CERTIFICATE':'ca.pem','SSL_CERT_FILE':'ignored'}, check=False)
        self.assertEqual(code,0,err); execute.assert_called_once()
        child = execute.call_args.args[2]
        self.assertEqual(child['CODEX_CA_CERTIFICATE'],str(self.ca)); self.assertEqual(child['SSL_CERT_FILE'],'ignored')
        state = Path(child['AGENT_SANDBOX_CODEX_HOME']).parent
        settings = json.loads((state/'srt.json').read_text())
        self.assertEqual(settings['network'], {'allowedDomains':['example.com:443','auth.openai.com:443','api.openai.com:443','chatgpt.com:443'],
            'deniedDomains':[], 'strictAllowlist':True,'allowLocalBinding':False,'allowAllUnixSockets':False,'allowUnixSockets':[]})
        for key in ('allowAppleEvents','enableWeakerNestedSandbox','enableWeakerNetworkIsolation'):
            self.assertIs(settings[key],False)
        fs = settings['filesystem']; self.assertEqual(fs['allowRead'],[])
        self.assertEqual(fs['denyRead'],[{'path':str(self.root/'secret'),'literal':True}])
        self.assertEqual(fs['allowWrite'],[{'path':str(path),'literal':True} for path in (state,self.cwd,self.root/'sink/result')])
        expected_denies = [dict(path=str(self.root/'secret'), literal=True), '/tmp/claude', '/private/tmp/claude',
            str(self.root/'home/.npm/_logs'), str(self.root/'home/.claude/debug')]
        expected_denies += [dict(path=str(path),literal=True) for path in (self.cwd/'.git', state/'task.md',state/'seatbelt.sb',
            state/'seatbelt.source.sb',state/'codex/rules',state/'codex/config.toml',state/'codex/gpt-6-sol.config.toml')]
        self.assertEqual(fs['denyWrite'],expected_denies)
        manifest = json.loads((state/'boundary.json').read_text())
        command = manifest['command']
        self.assertEqual(command[command.index('--provider')+1],'gpt-6-sol')
        self.assertIn('--full-access',command); self.assertIn('--no-persist',command)
        config = sandbox.tomllib.loads((state/'codex/config.toml').read_text())
        self.assertEqual(config['model'],'synthetic-model'); self.assertEqual(config['model_provider'],'mock')
        self.assertEqual(config['model_providers']['mock']['base_url'],'https://example.com/v1')
        self.assertFalse(config['model_providers']['mock']['requires_openai_auth'])

    def test_main_claude_and_codex_http_preserve_ca_env_without_default_requirement(self):
        self.default.unlink()
        original = {'CODEX_CA_CERTIFICATE':'bad\0path','SSL_CERT_FILE':'absent'}
        for runtime, route in [('claude','https://example.com/v1'),('codex','http://example.com/v1')]:
            for check in (True,False):
                with self.subTest(runtime=runtime,check=check):
                    with unittest.mock.patch.object(os,'open',wraps=os.open) as opened:
                        code,out,err,execute = self.run_main(original, check=check, runtime=runtime, route=route)
                    self.assertEqual(code,0,err)
                    self.assertFalse(any(call.args[0] == self.default for call in opened.call_args_list))
                    if check: self.assertEqual(out,'setup_status=ok\n')
                    else:
                        child = execute.call_args.args[2]
                        self.assertEqual({key:child[key] for key in original},original)


class DanglingSetupTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='dangling-setup-', dir='/private/tmp')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.denied = self.root/'denied'; self.denied.mkdir()
        self.list = self.root/'list.json'
        self.list.write_text(json.dumps([str(self.denied)]))

    def load(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = sandbox.load_denies(self.list)
        return *result, stderr.getvalue()

    def assert_origin(self, text, link, raw, target=None, ancestor=None):
        for value in (str(self.denied), str(link), raw):
            self.assertIn(value, text)
        if target is not None: self.assertIn(str(target), text)
        if ancestor is not None: self.assertIn(str(ancestor), text)

    def test_missing_leaf_multiple_ancestors_absolute_relative_and_chain(self):
        anchor = self.root/'anchor'; anchor.mkdir()
        (anchor/'sentinel').write_text('readable before isolation')
        targets = [anchor/'leaf', anchor/'absent/deeper/leaf']
        links = [('absolute',str(targets[0])), ('relative','../anchor/absent/deeper/leaf'),
                 ('chain','relative')]
        for name, raw in links: (self.denied/name).symlink_to(raw)
        denies, missing, logs = self.load()
        self.assertEqual(set(missing), set(map(str, targets)))
        for target in targets:
            self.assertIn(str(target), denies); self.assertIn(str(anchor), denies)
            self.assertEqual(missing[str(target)]['ancestor'], str(anchor))
            self.assertEqual(missing[str(target)]['declared'], str(self.denied))
        for name, raw in links:
            self.assert_origin(logs, self.denied/name, raw)
        self.assertEqual(logs.count("target_state='missing'"),3)
        self.assertEqual(len(denies),4)

    def test_same_missing_target_keeps_first_origin_but_reports_each_link(self):
        anchor = self.root/'anchor'; anchor.mkdir()
        for name in ('one','two'): (self.denied/name).symlink_to('../anchor/absent')
        denies, missing, logs = self.load()
        first_link = logs.split("link=",1)[1].split(" raw_target=",1)[0].strip("'")
        self.assertEqual(missing[str(anchor/'absent')]['link'],first_link)
        self.assertEqual(denies.count(str(anchor)),1)
        self.assertEqual(denies.count(str(anchor/'absent')),1)
        self.assertEqual(logs.count("target_state='missing'"),2)

    def test_internal_target_and_revisited_ancestor_are_exact_and_terminate(self):
        (self.denied/'link').symlink_to('missing/leaf')
        denies, missing, logs = self.load()
        target=self.denied/'missing/leaf'
        self.assertEqual(set(denies),{str(self.denied),str(target)})
        self.assertEqual(missing[str(target)],dict(declared=str(self.denied),link=str(self.denied/'link'),
            raw_target='missing/leaf',ancestor=str(self.denied)))
        self.assertEqual(logs.count("target_state='missing'"),1)

    def test_strict_success_preserves_A_and_valid_file_directory_chains(self):
        (self.root/'plain').write_text('plain')
        good=self.root/'good'; good.mkdir(); (good/'data').write_text('good')
        external=self.root/'external'; external.mkdir()
        second=self.root/'second'; second.write_text('second')
        (external/'secondary').symlink_to(second)
        for name, raw in [('A','../plain/../good/data'),('dir',str(external)),('chain','A')]:
            (self.denied/name).symlink_to(raw)
        original=os.path.realpath
        def strict_only(path, *, strict=False):
            self.assertIs(strict,True)
            return original(path,strict=strict)
        with unittest.mock.patch.object(os.path,'realpath',side_effect=strict_only):
            denies, missing, logs=self.load()
        self.assertEqual(missing,{})
        self.assertEqual(logs,'')
        for target in (good/'data',external,second): self.assertIn(str(target),denies)

    def test_B_existing_reentry_is_reported_even_when_already_covered(self):
        (self.root/'anchor').mkdir(); other=self.root/'otherdir'; other.mkdir()
        (other/'config').write_text('config')
        self.list.write_text(json.dumps([str(other),str(self.denied)]))
        for name in ('one','two'):
            (self.denied/name).symlink_to('../anchor/missing/../../otherdir/config')
        denies, missing, logs=self.load()
        self.assertEqual(missing,{})
        self.assertTrue(sandbox.is_denied(other/'config',denies))
        self.assertEqual(logs.count("target_state='existing'"),2)
        self.assertEqual(logs.count("ancestor='not-applicable'"),2)
        for name in ('one','two'):
            self.assert_origin(logs,self.denied/name,'../anchor/missing/../../otherdir/config',other/'config')

    def test_B_directory_reentry_scans_secondary_targets_and_rejects_hardlinks(self):
        (self.root/'anchor').mkdir(); external=self.root/'external'; external.mkdir()
        (self.root/'dir-alias').symlink_to(external)
        second=self.root/'second'; second.write_text('second')
        (external/'secondary').symlink_to(second)
        raw='../anchor/missing/../../dir-alias'
        (self.denied/'B').symlink_to(raw)
        denies, missing, logs=self.load()
        self.assertEqual(missing,{})
        for target in (external,second): self.assertIn(str(target),denies)
        self.assert_origin(logs,self.denied/'B',raw,external)
        os.link(second,self.root/'second-hardlink')
        with self.assertRaisesRegex(ValueError,'hardlinked') as error: self.load()
        self.assert_origin(str(error.exception),external/'secondary',str(second),second)

    def test_C_missing_then_ENOTDIR_is_located_without_kernel_precedence_claim(self):
        (self.root/'anchor').mkdir(); (self.root/'plain').write_text('plain')
        raw='../anchor/missing/../../plain/child'; link=self.denied/'C'; link.symlink_to(raw)
        with self.assertRaises(ValueError) as error: self.load()
        text=str(error.exception)
        self.assert_origin(text,link,raw)
        self.assertIn('NotADirectoryError',text); self.assertIn('errno=20',text)
        self.assertIn(str(self.root/'plain/child'),text)

    def test_self_and_two_link_cycles_are_located(self):
        for two in (False,True):
            with self.subTest(two=two):
                link=self.denied/'loop'; link.symlink_to('other' if two else 'loop')
                if two: (self.denied/'other').symlink_to('loop')
                with self.assertRaises(ValueError) as error: self.load()
                text=str(error.exception)
                discovered=next(path for path in (link,self.denied/'other') if f'link={str(path)!r}' in text)
                self.assert_origin(text,discovered,os.readlink(discovered))
                link.unlink()
                if two: (self.denied/'other').unlink()

    def test_strict_non_ENOENT_errors_never_use_missing_aware(self):
        target=self.root/'target'; target.write_text('target')
        link=self.denied/'link'; link.symlink_to(target)
        original=Path.resolve
        errors=[OSError(errno.ELOOP,'cycle',str(link)),PermissionError(errno.EACCES,'denied',str(target)),
                NotADirectoryError(errno.ENOTDIR,'not directory',str(target)),OSError('no errno'),
                RuntimeError('cycle'),RecursionError('recursion')]
        for injected in errors:
            with self.subTest(error=repr(injected)):
                def resolve(path,*args,**kwargs):
                    if path==link: raise injected
                    return original(path,*args,**kwargs)
                with unittest.mock.patch.object(Path,'resolve',resolve), \
                     unittest.mock.patch.object(sandbox.os.path,'realpath',wraps=os.path.realpath) as realpath:
                    with self.assertRaises(ValueError) as error: self.load()
                self.assert_origin(str(error.exception),link,str(target))
                self.assertFalse(any(call.kwargs.get('strict') is os.path.ALLOW_MISSING for call in realpath.call_args_list))

    def test_missing_aware_non_ENOENT_errors_are_located(self):
        anchor=self.root/'anchor'; anchor.mkdir()
        link=self.denied/'link'; link.symlink_to('../anchor/absent')
        original=os.path.realpath
        for number in (errno.ELOOP,errno.EACCES,errno.ENOTDIR):
            with self.subTest(errno=number):
                def realpath(path,*,strict=False):
                    if strict is os.path.ALLOW_MISSING: raise OSError(number,'injected',str(anchor/'failure'))
                    return original(path,strict=strict)
                with unittest.mock.patch.object(os.path,'realpath',side_effect=realpath):
                    with self.assertRaises(ValueError) as error: self.load()
                self.assert_origin(str(error.exception),link,'../anchor/absent',anchor/'failure')
                self.assertIn(f'errno={number}',str(error.exception))

    def test_missing_then_real_cycle_is_not_swallowed(self):
        (self.root/'anchor').mkdir(); (self.root/'loop').symlink_to('loop')
        link=self.denied/'link'; raw='../anchor/absent/../../loop'; link.symlink_to(raw)
        with self.assertRaises(ValueError) as error: self.load()
        self.assert_origin(str(error.exception),link,raw)
        self.assertIn(f'errno={errno.ELOOP}',str(error.exception))

    def test_capability_failure_is_located_but_strict_success_still_works(self):
        anchor=self.root/'anchor'; anchor.mkdir()
        link=self.denied/'link'; link.symlink_to('../anchor/absent')
        original=os.path
        class WithoutAllowMissing:
            def __getattr__(self,name):
                if name=='ALLOW_MISSING': raise AttributeError(name)
                return getattr(original,name)
        with unittest.mock.patch.object(sandbox.os,'path',WithoutAllowMissing()):
            with self.assertRaises(ValueError) as error: self.load()
            self.assert_origin(str(error.exception),link,'../anchor/absent',anchor/'absent')
            self.assertIn('os.path.ALLOW_MISSING',str(error.exception))
            self.assertIn('errno=2',str(error.exception))
            link.unlink(); (anchor/'exists').write_text('existing'); link.symlink_to(anchor/'exists')
            denies, missing, logs=self.load()
            self.assertIn(str(anchor/'exists'),denies); self.assertEqual(missing,{})

    def test_readlink_and_target_lstat_errors_keep_context(self):
        target=self.root/'target'; target.write_text('target')
        link=self.denied/'link'; link.symlink_to(target)
        with unittest.mock.patch.object(os,'readlink',side_effect=PermissionError(errno.EACCES,'readlink',str(link))):
            with self.assertRaises(ValueError) as error: self.load()
        self.assertIn(str(link),str(error.exception)); self.assertIn('raw_target=None',str(error.exception))
        original=Path.lstat
        for number in (errno.EACCES,errno.ENOENT):
            with self.subTest(errno=number):
                def lstat(path,*args,**kwargs):
                    if path==target: raise OSError(number,'lstat',str(target))
                    return original(path,*args,**kwargs)
                with unittest.mock.patch.object(Path,'lstat',lstat):
                    with self.assertRaises(ValueError) as error: self.load()
                self.assert_origin(str(error.exception),link,str(target),target)
                self.assertIn(f'errno={number}',str(error.exception))

    def test_ancestor_cascade_preserves_origins_and_visited_termination(self):
        one=self.root/'anchor-one'; one.mkdir(); two=self.root/'anchor-two'; two.mkdir()
        (self.denied/'old-python').symlink_to('../anchor-one/absent/leaf')
        (one/'secondary').symlink_to('../anchor-two/absent/leaf')
        (two/'back').symlink_to(self.denied)
        denies, missing, logs=self.load()
        self.assertEqual(set(denies),set(map(str,(self.denied,one,one/'absent/leaf',two,two/'absent/leaf'))))
        for anchor,link,raw in [(one,self.denied/'old-python','../anchor-one/absent/leaf'),
                                (two,one/'secondary','../anchor-two/absent/leaf')]:
            self.assertEqual(missing[str(anchor/'absent/leaf')],dict(declared=str(self.denied),link=str(link),
                raw_target=raw,ancestor=str(anchor)))
            self.assert_origin(logs,link,raw,anchor/'absent/leaf',anchor)
        secondary=next(line for line in logs.splitlines() if str(one/'secondary') in line)
        self.assertIn(f'discovered_in={str(one)!r}',secondary)
        self.assertEqual(logs.count("target_state='missing'"),2)

    def test_root_ancestor_is_rejected_before_scan(self):
        raw='/agent-sandbox-nonexistent-'+self.root.name+'/leaf'
        link=self.denied/'root-link'; link.symlink_to(raw)
        with self.assertRaisesRegex(ValueError,'non-root') as error: self.load()
        self.assert_origin(str(error.exception),link,raw,raw,'/')

    def test_ancestor_listdir_walk_and_type_failures_do_not_move_up(self):
        anchor=self.root/'anchor'; anchor.mkdir(); link=self.denied/'link'; link.symlink_to('../anchor/absent')
        original_listdir=os.listdir; original_walk=os.walk; original_lstat=Path.lstat
        for operation in ('listdir','walk','type'):
            with self.subTest(operation=operation):
                def listdir(path):
                    if Path(path)==anchor: raise PermissionError(errno.EACCES,'listdir',str(anchor))
                    return original_listdir(path)
                def walk(path,**kwargs):
                    if Path(path)==anchor: kwargs['onerror'](PermissionError(errno.EACCES,'walk',str(anchor)))
                    return original_walk(path,**kwargs)
                def lstat(path,*args,**kwargs):
                    if path==anchor: return os.stat_result((stat.S_IFREG,0,0,1,0,0,0,0,0,0))
                    return original_lstat(path,*args,**kwargs)
                patch=(unittest.mock.patch.object(os,'listdir',listdir) if operation=='listdir' else
                       unittest.mock.patch.object(os,'walk',walk) if operation=='walk' else
                       unittest.mock.patch.object(Path,'lstat',lstat))
                with patch:
                    with self.assertRaises(ValueError) as error: self.load()
                self.assert_origin(str(error.exception),link,'../anchor/absent',anchor/'absent',anchor)

    def test_added_ancestor_preserves_hardlink_and_special_target_rejection(self):
        anchor=self.root/'anchor'; anchor.mkdir()
        (self.denied/'link').symlink_to('../anchor/absent')
        file=anchor/'file'; file.write_text('file'); os.link(file,self.root/'other-name')
        with self.assertRaisesRegex(ValueError,'hardlinked'): self.load()
        (self.root/'other-name').unlink(); file.unlink()
        fifo=self.root/'fifo'; os.mkfifo(fifo); (anchor/'pipe-link').symlink_to(fifo)
        with self.assertRaisesRegex(ValueError,'regular file'): self.load()

    def test_declared_missing_and_cycle_errors_include_original_declaration(self):
        declared=self.root/'absent-declared'; self.list.write_text(json.dumps([str(declared)]))
        with self.assertRaises(ValueError) as error: sandbox.load_denies(self.list)
        self.assertIn(str(declared),str(error.exception)); self.assertIn('errno=2',str(error.exception))
        declared.symlink_to(declared)
        with self.assertRaises(ValueError) as error: sandbox.load_denies(self.list)
        self.assertIn(str(declared),str(error.exception)); self.assertIn('RuntimeError',str(error.exception))

    def test_missing_target_is_not_preread_and_lstat_errors_are_not_absence(self):
        anchor=self.root/'anchor'; anchor.mkdir()
        target=anchor/'missing/leaf'; link=self.denied/'link'; link.symlink_to('../anchor/missing/leaf')
        original_open=Path.open; original_lstat=Path.lstat
        def no_missing_open(path,*args,**kwargs):
            if path==target: raise AssertionError('a missing target must not be pre-read')
            return original_open(path,*args,**kwargs)
        with unittest.mock.patch.object(Path,'open',no_missing_open):
            denies,missing,_=self.load()
        self.assertIn(str(target),denies);self.assertIn(str(target),missing)
        for failure in (target,anchor):
            with self.subTest(failure=failure):
                def lstat(path,*args,**kwargs):
                    if path==failure: raise PermissionError(errno.EACCES,'classification denied',str(path))
                    return original_lstat(path,*args,**kwargs)
                with unittest.mock.patch.object(Path,'lstat',lstat):
                    with self.assertRaises(ValueError) as error: self.load()
                self.assert_origin(str(error.exception),link,'../anchor/missing/leaf',failure)
                self.assertIn(f'errno={errno.EACCES}',str(error.exception))

    @unittest.skipUnless(platform.system()=='Darwin','macOS setup entry')
    def test_multi_link_required_input_conflict_has_each_origin_before_specific_path(self):
        p=self.root
        for name in ('safe-anchor','input-anchor','home/.codex','home/.config/agent-tools','bin','work'):
            (p/name).mkdir(parents=True)
        prompt=p/'input-anchor/task.md'; prompt.write_text('synthetic task')
        (p/'home/.codex/config.toml').write_text('sandbox_mode = "workspace-write"\n')
        (p/'home/.config/agent-tools/endpoints.json').write_text('{"synthetic_key":"fixture-only"}')
        marker=p/'must-not-start'
        for name in ('codex-agent-run','srt'):
            runner=p/'bin'/name; runner.write_text(f'#!/bin/sh\ntouch "{marker}"\n'); runner.chmod(0o755)
        for name,anchor in [('safe-link','safe-anchor'),('input-link','input-anchor')]:
            (self.denied/name).symlink_to('../'+anchor+'/absent/leaf')
        env={**os.environ,'HOME':str(p/'home'),'PATH':str(p/'bin')+':'+os.environ['PATH'],
             'AGENT_TOOLS_FILE':str(ROOT/'scripts/agent-tools.zsh')}
        for check in (True,False):
            with self.subTest(check=check):
                cmd=[str(ROOT/'scripts/agent-sandbox'),*(['--check'] if check else []),'--cwd',str(p/'work'),
                    '--deny-list',str(self.list),'--','codex-agent-run','--provider','mimo','--prompt-file',str(prompt)]
                result=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=20)
                self.assertEqual(result.returncode,1,result.stderr)
                lines=result.stderr.splitlines()
                self.assertEqual(sum('deny expansion' in line for line in lines),2)
                for name,anchor in [('safe-link','safe-anchor'),('input-link','input-anchor')]:
                    line=next(line for line in lines if str(self.denied/name) in line)
                    self.assert_origin(line,self.denied/name,'../'+anchor+'/absent/leaf',p/anchor/'absent/leaf',p/anchor)
                self.assertIn('required setup input is denied: '+str(prompt),lines[-1])
                self.assertFalse(marker.exists()); self.assertNotIn('agent-sandbox: state=',result.stderr)


class VerifyTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='dangling-verify-',dir='/private/tmp')
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve()
        self.ancestor=self.root/'anchor'; self.ancestor.mkdir()
        self.target=self.ancestor/'absent/leaf'
        self.probe=self.root/'probe'; self.probe.write_bytes(b'agent-sandbox-probe')
        self.command=[str(self.root/'codex-agent-run'),'--prompt-file','fixture']
        self.manifest=self.root/'boundary.json'
        self.source=dict(declared=str(self.root/'declared'),link=str(self.root/'declared/link'),
                         raw_target='../anchor/absent/leaf',ancestor=str(self.ancestor))
        # Deliberately list the missing target before its ancestor.
        self.doc=dict(denies=[str(self.target),str(self.ancestor)],probe=str(self.probe),command=self.command,
                      missing_targets={str(self.target):dict(self.source)})

    def run_verify(self, *, ancestor_query=True, target_query=True, ancestor_error=None,
                   target_error=None, ancestor_read=False, target_read=False, success=False):
        self.manifest.write_text(json.dumps(self.doc))
        events=[]
        original_open=open; original_listdir=os.listdir
        def query(path):
            events.append(('query',path))
            result=ancestor_query if path==str(self.ancestor) else target_query
            if isinstance(result,Exception): raise result
            return result
        def listdir(path):
            if Path(path)==self.ancestor:
                events.append(('read',str(path)))
                if ancestor_read: return original_listdir(path)
                raise ancestor_error or PermissionError(errno.EPERM,'fixture denial',str(path))
            return original_listdir(path)
        def denied_open(path,*args,**kwargs):
            if str(path)==str(self.target):
                events.append(('read',str(path)))
                if target_read: return io.BytesIO(b'read succeeded')
                raise target_error or FileNotFoundError(errno.ENOENT,'fixture absence',str(path))
            return original_open(path,*args,**kwargs)
        with unittest.mock.patch.object(sandbox,'kernel_denies_read',side_effect=query), \
             unittest.mock.patch.object(os,'listdir',side_effect=listdir), \
             unittest.mock.patch('builtins.open',side_effect=denied_open), \
             unittest.mock.patch.object(os,'execvpe') as execute, contextlib.redirect_stderr(io.StringIO()):
            if success:
                sandbox.verify_and_exec(self.manifest,self.command)
                execute.assert_called_once_with(self.command[0],self.command,os.environ)
                text=''
            else:
                with self.assertRaises((ValueError,OSError)) as error:
                    sandbox.verify_and_exec(self.manifest,self.command)
                execute.assert_not_called(); text=str(error.exception)
        return events,text

    def test_verified_ancestor_then_registered_ENOENT_then_allowed_probe_and_one_exec(self):
        events,_=self.run_verify(success=True)
        self.assertEqual(events,[('query',str(self.ancestor)),('read',str(self.ancestor)),
                                 ('query',str(self.target)),('read',str(self.target))])
        self.assertEqual(self.probe.read_bytes(),b'agent-sandbox-probe')
        self.run_verify(target_error=PermissionError(errno.EPERM,'denied'),success=True)

    def test_unregistered_ENOENT_and_existing_entry_disappearance_never_exec(self):
        self.doc.pop('missing_targets')
        events,text=self.run_verify()
        self.assertIn(str(self.target),text); self.assertIn('errno=2',text)
        self.assertEqual(events,[('query',str(self.target)),('read',str(self.target))])

    def test_ancestor_query_denial_is_not_enough_without_actual_PermissionError(self):
        for options in [dict(ancestor_query=False),dict(ancestor_query=ValueError('indeterminate query')),
                        dict(ancestor_query=OSError(errno.EIO,'query error')),dict(ancestor_read=True),
                        dict(ancestor_error=FileNotFoundError(errno.ENOENT,'deleted ancestor')),
                        dict(ancestor_error=OSError(errno.ENOTDIR,'changed ancestor')),
                        dict(ancestor_error=OSError(errno.ELOOP,'changed ancestor'))]:
            with self.subTest(options=options):
                events,text=self.run_verify(**options)
                self.assertNotIn(('query',str(self.target)),events)
                self.assertIn(str(self.ancestor),text)
                for value in self.source.values(): self.assertIn(value,text)

    def test_target_requires_query_and_only_PermissionError_or_registered_ENOENT(self):
        options=[dict(target_query=False),dict(target_query=ValueError('query indeterminate')),
                 dict(target_read=True)]
        options += [dict(target_error=OSError(number,'target error',str(self.target)))
                    for number in (errno.ENOTDIR,errno.ELOOP,errno.EIO)]
        for option in options:
            with self.subTest(option=option):
                _,text=self.run_verify(**option)
                for value in [str(self.target),*self.source.values()]: self.assertIn(value,text)

    def test_invalid_metadata_and_component_coverage_fail_before_query(self):
        import copy
        mutations=[lambda d: d.update(missing_targets=[]),
                   lambda d: d['missing_targets'].update({str(self.target):{}}),
                   lambda d: d['missing_targets'][str(self.target)].update(raw_target=None),
                   lambda d: d['missing_targets'][str(self.target)].update(ancestor=str(self.root/'anchor-other')),
                   lambda d: d['missing_targets'][str(self.target)].update(ancestor=str(self.target)),
                   lambda d: d['denies'].remove(str(self.ancestor)),
                   lambda d: d['denies'].remove(str(self.target)),
                   lambda d: d['missing_targets'].update({str(self.ancestor):dict(self.source)}),
                   lambda d: d['missing_targets'][str(self.target)].update(ancestor='//anchor'),
                   lambda d: d['missing_targets'][str(self.target)].update(ancestor=str(self.ancestor)+'/../anchor'),
                   lambda d: d['missing_targets'][str(self.target)].update(ancestor='/anchor\0'),
                   lambda d: d['missing_targets'].update({'//invalid/target':dict(self.source)}),
                   lambda d: d['missing_targets'].update({'/anchor/../target':dict(self.source)}),
                   lambda d: d['missing_targets'].update({'relative':dict(self.source)})]
        original=copy.deepcopy(self.doc)
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                self.doc=copy.deepcopy(original); mutate(self.doc)
                events,_=self.run_verify(); self.assertEqual(events,[])
        # A similarly spelled sibling is not in this ancestor's component subtree.
        self.target=self.root/'anchor-other/leaf'
        self.doc=copy.deepcopy(original)
        self.doc['denies']=[str(self.target),str(self.ancestor)]
        self.doc['missing_targets']={str(self.target):dict(self.source)}
        events,_=self.run_verify(); self.assertEqual(events,[])

    def test_allowed_probe_must_really_read_and_write_before_exec(self):
        self.probe.write_bytes(b'wrong content')
        self.run_verify()
        self.probe.write_bytes(b'agent-sandbox-probe')
        with unittest.mock.patch.object(Path,'write_bytes',side_effect=PermissionError(errno.EPERM,'probe write')):
            self.run_verify()
        with unittest.mock.patch.object(Path,'read_bytes',side_effect=PermissionError(errno.EPERM,'probe read')):
            self.run_verify()

    def test_no_missing_metadata_existing_boundary_still_requires_kernel_query(self):
        self.doc['denies']=[str(self.ancestor)]; self.doc.pop('missing_targets')
        self.run_verify(success=True)
        events,text=self.run_verify(ancestor_query=False)
        self.assertEqual(events,[('query',str(self.ancestor))]); self.assertIn('effective Seatbelt policy',text)


@unittest.skipUnless(platform.system() == 'Darwin' and os.getenv('AGENT_SANDBOX_KERNEL_TESTS') == '1',
                     'requires macOS and explicit outer-sandbox test opt-in')
class KernelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='agent-sandbox-tests.', dir='/private/tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        p = self.root
        for name in ('home/.codex', 'home/.config/agent-tools', 'bin', 'work/denied', 'work/.git', 'sinks'):
            (p/name).mkdir(parents=True)
        (p/'work/allowed').write_text('ALLOW_INPUT')
        (p/'work/denied/report').write_text('FORBIDDEN_BUSINESS_MARKER')
        (p/'work/history.jsonl').write_text('FORBIDDEN_HISTORY_MARKER')
        (p/'work/alias').symlink_to(p/'work/denied/report')
        (p/'work/dir-alias').symlink_to(p/'work/denied', target_is_directory=True)
        (p/'denies.json').write_text(json.dumps([str(p/'work/denied'), str(p/'work/history.jsonl')]))
        config = 'sandbox_mode = "workspace-write"\nmodel = "test"\nmodel_provider = "mock"\n[model_providers.mock]\nname = "mock"\nbase_url = "https://example.com/v1"\nwire_api = "responses"\nrequires_openai_auth = false\n'
        (p/'home/.codex/config.toml').write_text(config)
        (p/'home/.codex/mimo.config.toml').write_text('')
        endpoint = json.loads((ROOT/'config/endpoints.example.json').read_text())
        endpoint['default']['mimo']['codex']['api_key'] = 'synthetic-test-key'
        ep = p/'home/.config/agent-tools/endpoints.json'
        ep.write_text(json.dumps(endpoint)); ep.chmod(0o600)
        runner = p/'bin/codex-agent-run'
        runner.write_text('#!/usr/bin/env python3\n'+r'''
import json, os, subprocess, sys
from pathlib import Path
p = Path(os.environ['TEST_ROOT'])
r = {}
def read(name, path):
    try: r[name] = Path(path).read_text()
    except OSError as e: r[name] = type(e).__name__
def write(name, path):
    try: Path(path).write_text('write'); r[name] = 'allowed'
    except OSError as e: r[name] = type(e).__name__
read('allowed', p/'work/allowed')
for name, path in [('direct',p/'work/denied/report'), ('symlink',p/'work/alias'),
 ('dir_alias',p/'work/dir-alias/report'), ('dotdot',p/'work/../work/denied/report'),
 ('history',p/'work/history.jsonl'), ('data_alias','/System/Volumes/Data'+str(p/'work/denied/report')), ('tmp_alias',str(p/'work/denied/report').replace('/private/tmp/','/tmp/'))]:
    read(name,path)
case_alias = p/'work/DENIED/REPORT'
if os.environ['TEST_CASE_ALIAS_EXISTS'] == '1': read('case_alias',case_alias)
s = subprocess.run(['rg','--no-ignore','-n','FORBIDDEN_',str(p/'work')], capture_output=True,text=True)
r['recursive_stdout'] = s.stdout
r['recursive_code'] = s.returncode
nested = subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default)','/bin/cat',str(p/'work/denied/report')], capture_output=True,text=True)
r['nested_stdout'] = nested.stdout
r['nested_code'] = nested.returncode
try:
    os.link(p/'work/denied/report',p/'work/hardlink')
    read('hardlink',p/'work/hardlink')
except OSError as e: r['hardlink'] = type(e).__name__
write('cwd_write',p/'work/new-output')
write('protected_write',p/'work/.git/evil')
write('outside_write',p/'outside')
write('sink_neighbor',p/'sinks/unrequested')
write('sink_write',p/'sinks/result')
write('original_blocked_write',p/'work/original-blocked')
write('prompt_write',Path(sys.argv[sys.argv.index('--prompt-file')+1]))
write('profile_write',Path(os.environ.get('AGENT_SANDBOX_CODEX_HOME',os.environ.get('CLAUDE_CONFIG_DIR'))).parent/'seatbelt.sb')
heredoc = subprocess.run(['/bin/zsh','-lc','cat <<EOF\nALLOW_HEREDOC_MARKER\nEOF\n'],capture_output=True,text=True)
r['heredoc_code'], r['heredoc_stdout'], r['heredoc_stderr'] = heredoc.returncode, heredoc.stdout, heredoc.stderr
print(json.dumps(r))
''')
        runner.chmod(0o755)
        srt = os.getenv('SRT_TEST_BIN') or shutil.which('srt')
        if not srt: self.fail('SRT_TEST_BIN or srt required for kernel tests')
        (p/'bin/srt').symlink_to(srt)
        (p/'ca.pem').write_bytes(PUBLIC_CA)
        self.env = {**os.environ, 'CODEX_CA_CERTIFICATE':str(p/'ca.pem'), 'SSL_CERT_FILE':'', 'HOME':str(p/'home'), 'PATH':str(p/'bin')+':'+os.environ['PATH'],
                    'TEST_ROOT':str(p), 'TEST_CASE_ALIAS_EXISTS':str(int((p/'work/DENIED/REPORT').exists())),
                    'AGENT_TOOLS_FILE':str(ROOT/'scripts/agent-tools.zsh')}

    def launch(self):
        p = self.root
        result = subprocess.run([str(ROOT/'scripts/agent-sandbox'),'--cwd',str(p/'work'),
            '--deny-list',str(p/'denies.json'),'--','codex-agent-run','--provider','mimo',
            '--prompt','test','--detail','--output',str(p/'sinks/result')],env=self.env,capture_output=True,text=True,timeout=45)
        retain_kernel_evidence(self.id(),result)
        return result


    def test_codex_ca_reaches_native_cli(self):
        p = self.root
        runner = p/'bin/codex-agent-run'; runner.unlink()
        runner.symlink_to(ROOT/'scripts/codex-agent-run')
        native = p/'bin/codex'
        native.write_text('#!/usr/bin/env python3\n'+r'''
import hashlib, os
from pathlib import Path
selected = os.environ.get('CODEX_CA_CERTIFICATE') or os.environ.get('SSL_CERT_FILE')
assert selected == os.environ['TEST_CA_EXPECTED_PATH'], 'native CA path mismatch'
data = Path(selected).read_bytes()
assert data and hashlib.sha256(data).hexdigest() == os.environ['TEST_CA_EXPECTED_SHA256'], 'CA fixture changed or unreadable'
print('NATIVE_CA_PATH='+selected)
''')
        native.chmod(0o755)
        alias = p/'ca-alias.pem'; alias.symlink_to(p/'ca.pem')
        for name in ('default','ssl'):
            with self.subTest(source=name):
                env = dict(self.env)
                env.pop('CODEX_CA_CERTIFICATE',None); env.pop('SSL_CERT_FILE',None)
                if name == 'default':
                    # Runtime public OS bundle, never a historical fixed fixture/hash.
                    expected = Path(sandbox.DEFAULT_CODEX_CA_CERTIFICATE).resolve(strict=True)
                    data = expected.read_bytes()
                else:
                    env.update(CODEX_CA_CERTIFICATE='', SSL_CERT_FILE=str(alias))
                    expected = p/'ca.pem'
                    data = PUBLIC_CA
                self.assertTrue(data)
                env.update(TEST_CA_EXPECTED_PATH=str(expected), TEST_CA_EXPECTED_SHA256=hashlib.sha256(data).hexdigest())
                result = subprocess.run([str(ROOT/'scripts/agent-sandbox'),'--cwd',str(p/'work'),
                    '--deny-list',str(p/'denies.json'),'--','codex-agent-run','--provider','mimo',
                    '--prompt','test native CA environment','--detail','--output',str(p/'sinks'/('ca-'+name))],
                    env=env,capture_output=True,text=True,timeout=45)
                retain_kernel_evidence(self.id()+'.'+name,result)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual((p/'sinks'/('ca-'+name)).read_text(),'NATIVE_CA_PATH='+str(expected)+'\n')
                self.assertIn('read boundary verified; starting runner',result.stderr)
                self.assertLess(result.stderr.index('agent-sandbox: seatbelt_profile='),
                                result.stderr.index('read boundary verified; starting runner'))
                state = Path(next(line.split('=',1)[1] for line in result.stderr.splitlines()
                                  if line.startswith('agent-sandbox: state=')))
                fields = profile_fields(result.stderr)
                for file, key in (('seatbelt.sb','profile_sha256'),('seatbelt.source.sb','source_sha256')):
                    source = state/file
                    if not source.exists(): source = state/'seatbelt.sb'
                    profile_bytes = source.read_bytes()
                    self.assertEqual(hashlib.sha256(profile_bytes).hexdigest(),fields[key])
                    self.assertNotIn(b'com.apple.trustd.agent',profile_bytes)
                settings = json.loads((state/'srt.json').read_text())
                self.assertEqual(settings['network'],dict(allowedDomains=['example.com:443'],deniedDomains=[],
                    strictAllowlist=True,allowLocalBinding=False,allowAllUnixSockets=False,allowUnixSockets=[]))
                self.assertEqual(settings['filesystem']['denyRead'],[
                    dict(path=str(p/'work/denied'),literal=True),dict(path=str(p/'work/history.jsonl'),literal=True)])
                self.assertEqual(settings['filesystem']['allowRead'],[])
                self.assertEqual(settings['filesystem']['allowWrite'],[
                    dict(path=str(path),literal=True) for path in (state,p/'work',p/'sinks'/('ca-'+name))])
                fs = settings['filesystem']
                expected_denies = [dict(path=str(path),literal=True) for path in (p/'work/denied',p/'work/history.jsonl')]
                expected_denies += ['/tmp/claude','/private/tmp/claude',str(p/'home/.npm/_logs'),str(p/'home/.claude/debug')]
                expected_denies += [dict(path=str(path),literal=True) for path in (
                    p/'work/.git',p/'work/.codex',p/'work/.agents',p/'work/.aws',state/'task.md',state/'seatbelt.sb',
                    state/'seatbelt.source.sb',state/'codex/rules',state/'codex/config.toml',state/'codex/mimo.config.toml')]
                self.assertEqual(fs['denyWrite'],expected_denies)
                for key in ('allowAppleEvents','enableWeakerNestedSandbox','enableWeakerNetworkIsolation'):
                    self.assertIs(settings[key],False)

    def test_kernel_boundary_and_write_preservation(self):
        result = self.launch()
        self.assertEqual(result.returncode,0,result.stderr)
        r = json.loads(result.stdout)
        self.assertEqual(r['allowed'],'ALLOW_INPUT')
        for name in ('direct','symlink','dir_alias','dotdot','history','data_alias','tmp_alias','hardlink'):
            self.assertEqual(r[name],'PermissionError',r)

        if 'case_alias' in r: self.assertEqual(r['case_alias'],'PermissionError',r)
        self.assertNotIn('FORBIDDEN_',r['recursive_stdout'])
        self.assertNotEqual(r['nested_code'],0)
        self.assertNotIn('FORBIDDEN_',r['nested_stdout'])
        self.assertEqual(r['cwd_write'],'allowed')
        self.assertEqual(r['sink_write'],'allowed')
        self.assertEqual(r['heredoc_code'],0,r)
        self.assertEqual(r['heredoc_stdout'],'ALLOW_HEREDOC_MARKER\n',r)
        for name in ('protected_write','outside_write','sink_neighbor','prompt_write','profile_write'):
            self.assertEqual(r[name],'PermissionError',r)

    def test_dangling_targets_with_verified_ancestor_boundary(self):
        p=self.root
        anchor=p/'anchor'; anchor.mkdir(); (anchor/'sentinel').write_text('FORBIDDEN_ANCESTOR_MARKER')
        target=anchor/'missing-framework/Versions/old/bin/python'
        for name,raw in [('old-python',str(target)),('relative-python','../../anchor/missing-framework/Versions/old/bin/python'),
                         ('chain-python','relative-python')]:
            (p/'work/denied'/name).symlink_to(raw)
        external=p/'external'; (external/'nested').mkdir(parents=True)
        (external/'nested/data').write_text('FORBIDDEN_EXTERNAL_MARKER')
        secondary=p/'secondary'; secondary.write_text('FORBIDDEN_SECONDARY_MARKER')
        (external/'secondary-link').symlink_to(secondary)
        (p/'work/denied/external-link').symlink_to(external)
        valid=p/'valid-file'; valid.write_text('FORBIDDEN_VALID_TARGET_MARKER')
        (p/'work/denied/valid-link').symlink_to(valid)
        runner=p/'bin/codex-agent-run'
        extra=r'''
import ctypes
library=ctypes.CDLL('/usr/lib/libSystem.B.dylib',use_errno=True)
check=library.sandbox_check
check.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int];check.restype=ctypes.c_int
for name,path in [('ancestor',p/'anchor'),('sentinel',p/'anchor/sentinel'),('external',p/'external/nested/data')]:
    r[name+'_query']=check(os.getpid(),b'file-read-data',1,ctypes.c_char_p(os.fsencode(path)))
try: os.listdir(p/'anchor'); r['ancestor_listdir']='allowed'
except OSError as e: r['ancestor_listdir']=type(e).__name__
for name,path in [('sentinel_read',p/'anchor/sentinel'),('missing_direct',p/'anchor/missing-framework/Versions/old/bin/python'),
                  ('dangling_alias',p/'work/denied/old-python'),('external_direct',p/'external/nested/data'),
                  ('secondary_direct',p/'secondary'),('valid_direct',p/'valid-file')]: read(name,path)
write('ancestor_sentinel_write',p/'anchor/sentinel')
write('ancestor_create',p/'anchor/new-entry')
print('SYNTHETIC_DANGLING_RUNNER_STARTED',file=sys.stderr)
'''
        runner.write_text(runner.read_text().replace('print(json.dumps(r))',extra+'\nprint(json.dumps(r))'))
        result=self.launch()
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertLess(result.stderr.index('read boundary verified; starting runner'),
                        result.stderr.index('SYNTHETIC_DANGLING_RUNNER_STARTED'))
        state=Path(next(line.split('=',1)[1] for line in result.stderr.splitlines()
                        if line.startswith('agent-sandbox: state=')))
        manifest=json.loads((state/'boundary.json').read_text())
        for path in (p/'work/denied',p/'work/history.jsonl',target,anchor,external,secondary,valid):
            self.assertIn(str(path),manifest['denies'])
        self.assertEqual(set(manifest['missing_targets']),{str(target)})
        metadata=manifest['missing_targets'][str(target)]
        self.assertEqual(metadata['ancestor'],str(anchor)); self.assertEqual(metadata['declared'],str(p/'work/denied'))
        self.assertEqual(os.readlink(metadata['link']),metadata['raw_target'])
        self.assertEqual(result.stderr.count("target_state='missing'"),3)
        settings=json.loads((state/'srt.json').read_text())['filesystem']
        for key in ('denyRead','denyWrite'):
            for value in manifest['denies']: self.assertIn(dict(path=value,literal=True),settings[key])
        fields=profile_fields(result.stderr)
        for name,key in (('seatbelt.sb','profile_sha256'),('seatbelt.source.sb','source_sha256')):
            retained=state/name
            if not retained.exists():
                # No compaction: the launcher retains only the effective profile.
                self.assertEqual(fields['source_sha256'],fields['profile_sha256'])
                retained=state/'seatbelt.sb'
            self.assertEqual(hashlib.sha256(retained.read_bytes()).hexdigest(),fields[key])
            for value in manifest['denies']: self.assertIn(value,retained.read_text())
        r=json.loads(result.stdout)
        for name in ('ancestor_query','sentinel_query','external_query'): self.assertEqual(r[name],1,r)
        for name in ('ancestor_listdir','sentinel_read','dangling_alias','external_direct','secondary_direct','valid_direct',
                     'ancestor_sentinel_write','ancestor_create','direct','symlink','dir_alias','dotdot','history',
                     'data_alias','tmp_alias','hardlink','protected_write','outside_write','sink_neighbor','prompt_write','profile_write'):
            self.assertEqual(r[name],'PermissionError',r)
        self.assertIn(r['missing_direct'],('FileNotFoundError','PermissionError'),r)  # Never the boundary proof.
        self.assertEqual(r['allowed'],'ALLOW_INPUT'); self.assertEqual(r['cwd_write'],'allowed')
        self.assertEqual(r['sink_write'],'allowed'); self.assertNotIn('FORBIDDEN_',r['recursive_stdout'])
        self.assertNotEqual(r['nested_code'],0); self.assertNotIn('FORBIDDEN_',r['nested_stdout'])

    def missing_materialization_control(self, deny_ancestor):
        p=self.root
        anchor=p/'control-anchor'; anchor.mkdir(); (anchor/'sentinel').write_text('sentinel')
        probe=p/'materialization-probe.py'
        probe.write_text(r'''
import ctypes,json,os,sys
from pathlib import Path
p=Path(sys.argv[1]);anchor=p/'control-anchor';target=anchor/'missing/leaf'
lib=ctypes.CDLL('/usr/lib/libSystem.B.dylib',use_errno=True);check=lib.sandbox_check
check.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int];check.restype=ctypes.c_int
def snapshot():
    r={}
    for name,path,kind in [('ancestor',anchor,'dir'),('sentinel',anchor/'sentinel','file'),
                           ('missing_dir',target.parent,'dir'),('missing_file',target,'file')]:
        r[name+'_query']=check(os.getpid(),b'file-read-data',1,ctypes.c_char_p(os.fsencode(path)))
        try: r[name+'_read']=os.listdir(path) if kind=='dir' else path.read_text()
        except OSError as e: r[name+'_read']={'error':type(e).__name__,'errno':e.errno}
    r['allowed_read']=(p/'work/allowed').read_text()
    (p/'work/control-write').write_text('allowed write');r['allowed_write']='allowed'
    return r
print(json.dumps(snapshot()),flush=True)
if sys.stdin.readline()!='materialized\n': raise RuntimeError('missing fixture handshake')
print(json.dumps(snapshot()),flush=True)
''')
        settings=p/'control-srt.json'
        rules=[dict(path=str(anchor),literal=True)] if deny_ancestor else []
        settings.write_text(json.dumps(dict(filesystem=dict(denyRead=rules,allowRead=[],
            allowWrite=[dict(path=str(p/'work'),literal=True)],denyWrite=rules),
            network=dict(allowedDomains=[],deniedDomains=[],strictAllowlist=True,allowLocalBinding=False,
                         allowAllUnixSockets=False,allowUnixSockets=[]),allowAppleEvents=False,
            enableWeakerNestedSandbox=False,enableWeakerNetworkIsolation=False)))
        profile=p/'control-seatbelt.sb'
        cmd=[shutil.which('node'),str(ROOT/'scripts/agent-sandbox-launch.mjs'),str(p/'bin/srt'),str(profile),
             '--settings',str(settings),'--',sys.executable,str(probe),str(p)]
        deadline=time.monotonic()+45
        process=subprocess.Popen(cmd,env=self.env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            ready,_,_=select.select([process.stdout],[],[],max(0,deadline-time.monotonic()))
            self.assertTrue(ready,'materialization fixture handshake timed out')
            first=process.stdout.readline()
            self.assertTrue(first,'fixture did not reach pre-materialization snapshot')
            before=json.loads(first)
            target=anchor/'missing/leaf'; target.parent.mkdir();target.write_text('materialized fixture')
            stdout,stderr=process.communicate('materialized\n',timeout=max(.1,deadline-time.monotonic()))
            result=subprocess.CompletedProcess(cmd,process.returncode,first+stdout,stderr)
            retain_kernel_evidence(self.id(),result,policy_root=p)
            self.assertEqual(result.returncode,0,stderr)
            after=json.loads(stdout)
        finally:
            if process.poll() is None:
                process.kill();process.communicate(timeout=5)
        self.assertEqual(before['missing_file_query'],1)
        self.assertEqual(before['missing_file_read'],dict(error='FileNotFoundError',errno=errno.ENOENT))
        self.assertEqual(before['missing_dir_query'],1)
        self.assertEqual(before['missing_dir_read'],dict(error='FileNotFoundError',errno=errno.ENOENT))
        for result in (before,after):
            self.assertEqual(result['allowed_read'],'ALLOW_INPUT');self.assertEqual(result['allowed_write'],'allowed')
        fields=profile_fields(stderr)
        self.assertEqual(fields['profile_sha256'],hashlib.sha256(profile.read_bytes()).hexdigest())
        source=p/'seatbelt.source.sb'
        self.assertEqual(fields['source_sha256'],hashlib.sha256((source if source.exists() else profile).read_bytes()).hexdigest())
        if deny_ancestor:
            for snapshot in (before,after):
                for name in ('ancestor','sentinel'):
                    self.assertEqual(snapshot[name+'_query'],1)
                    self.assertEqual(snapshot[name+'_read']['error'],'PermissionError')
            for name in ('missing_dir','missing_file'):
                self.assertEqual(after[name+'_query'],1);self.assertEqual(after[name+'_read']['error'],'PermissionError')
            self.assertIn(str(anchor),profile.read_text())
        else:
            self.assertEqual(before['ancestor_query'],0);self.assertIsInstance(before['ancestor_read'],list)
            self.assertEqual(after['missing_file_query'],0);self.assertEqual(after['missing_file_read'],'materialized fixture')
            self.assertEqual(after['missing_dir_query'],0);self.assertEqual(after['missing_dir_read'],['leaf'])

    def test_missing_query_and_ENOENT_are_ambiguous_under_allow_default(self):
        self.missing_materialization_control(False)

    def test_verified_ancestor_policy_denies_after_fixture_materialization(self):
        self.missing_materialization_control(True)

    def test_profile_hardlink_changes_detected_by_prespawn_hashes(self):
        p=self.root
        entries=json.loads((p/'denies.json').read_text())
        for i in range(150):
            file=p/'work/mass'/f'item-{i:04d}'
            file.parent.mkdir(exist_ok=True); file.write_text('synthetic')
            entries.append(str(file))
        (p/'denies.json').write_text(json.dumps(entries))
        runner=p/'bin/codex-agent-run'
        extra="""
state=Path(os.environ['AGENT_SANDBOX_CODEX_HOME']).parent
for name in ('seatbelt.sb','seatbelt.source.sb'):
    alias=p/'work'/('alias-'+name)
    os.link(state/name,alias)
    alias.chmod(0o600)
    alias.write_text('SYNTHETIC_CHANGED_AFTER_LOAD')
from hashlib import sha256
forged=sha256(b'SYNTHETIC_CHANGED_AFTER_LOAD').hexdigest()
print(f'agent-sandbox: seatbelt_profile={state}/seatbelt.sb profile_sha256={forged} source_sha256={forged} file-backed',file=sys.stderr)
"""
        runner.write_text(runner.read_text().replace('print(json.dumps(r))',extra+'\nprint(json.dumps(r))'))
        result=self.launch()
        self.assertEqual(result.returncode,0,result.stderr)
        state=Path(result.stderr.split('state=',1)[1].splitlines()[0])
        fields=profile_fields(result.stderr)
        self.assertEqual(result.stderr.count('agent-sandbox: seatbelt_profile='),2)
        for name,key in (('seatbelt.sb','profile_sha256'),('seatbelt.source.sb','source_sha256')):
            self.assertEqual(len(fields[key]),64)
            self.assertNotEqual(hashlib.sha256((state/name).read_bytes()).hexdigest(),fields[key])
        # Retained bytes changed; the policy already loaded by the kernel did not.
        self.assertEqual(json.loads(result.stdout)['direct'],'PermissionError')

    def test_read_only_does_not_gain_cwd_writes(self):
        config = self.root/'home/.codex/config.toml'
        config.write_text(config.read_text().replace('workspace-write','read-only'))
        result = self.launch()
        self.assertEqual(result.returncode,0,result.stderr)
        r = json.loads(result.stdout)
        self.assertEqual(r['cwd_write'],'PermissionError',r)
        self.assertEqual(r['sink_write'],'allowed')
        self.assertEqual(r['heredoc_code'],0,r)

    def test_large_deny_list_verifies_every_entry_before_runner(self):
        p = self.root
        entries = json.loads((p/'denies.json').read_text())
        for i in range(4106):
            directory = p/'work/mass'/f'node-{i % 66:02d}-aaaa'
            directory.mkdir(parents=True, exist_ok=True)
            file = directory/f'item-{i:04d}-bbbbbbbbbb.txt'
            file.write_text('FORBIDDEN_MASS_MARKER')
            entries.append(str(file))
        (p/'denies.json').write_text(json.dumps(entries))
        result = subprocess.run([str(ROOT/'scripts/agent-sandbox'),'--cwd',str(p/'work'),
            '--deny-list',str(p/'denies.json'),'--','codex-agent-run','--provider','mimo',
            '--prompt','test','--detail','--output',str(p/'sinks/result')],
            env=self.env,capture_output=True,text=True,timeout=300)
        retain_kernel_evidence(self.id(),result)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('read boundary verified; starting runner',result.stderr)
        self.assertIn('file-backed',result.stderr)
        state = Path(result.stderr.split('state=',1)[1].splitlines()[0])
        manifest = json.loads((state/'boundary.json').read_text())
        self.assertEqual(len(manifest['denies']),4108)
        profile = state/'seatbelt.sb'
        self.assertGreater((state/'seatbelt.source.sb').stat().st_size,os.sysconf('SC_ARG_MAX'))
        self.assertLess(profile.stat().st_size,(state/'seatbelt.source.sb').stat().st_size)
        fields=profile_fields(result.stderr)
        for name,key in (('seatbelt.sb','profile_sha256'),('seatbelt.source.sb','source_sha256')):
            self.assertEqual(hashlib.sha256((state/name).read_bytes()).hexdigest(),fields[key])
        r = json.loads(result.stdout)
        self.assertEqual(r['allowed'],'ALLOW_INPUT')
        self.assertNotIn('FORBIDDEN_',r['recursive_stdout'])
        self.assertEqual(r['profile_write'],'PermissionError')
        self.assertEqual(r['outside_write'],'PermissionError')

    def test_claude_original_deny_write_wins_over_cwd(self):
        p = self.root
        settings = p/'home/.claude/settings.json'; settings.parent.mkdir()
        settings.write_text(json.dumps(dict(sandbox=dict(filesystem=dict(denyWrite=[str(p/'work/original-blocked')])))))
        endpoints = p/'home/.config/agent-tools/endpoints.json'
        doc = json.loads(endpoints.read_text())
        doc['default']['mimo']['claude']['api_key'] = 'synthetic-test-key'
        endpoints.write_text(json.dumps(doc))
        (p/'bin/claude-agent-run').symlink_to(p/'bin/codex-agent-run')
        check = subprocess.run([str(ROOT/'scripts/agent-sandbox'),'--check','--cwd',str(p/'work'),
            '--deny-list',str(p/'denies.json'),'--','claude-agent-run','--provider','mimo',
            '--prompt','test','--detail','--output',str(p/'work/original-blocked')],
            env=self.env,capture_output=True,text=True,timeout=45)
        self.assertNotEqual(check.returncode,0)
        self.assertIn('output conflicts with original write denial',check.stderr)
        result = subprocess.run([str(ROOT/'scripts/agent-sandbox'),'--cwd',str(p/'work'),
            '--deny-list',str(p/'denies.json'),'--','claude-agent-run','--provider','mimo',
            '--prompt','test','--detail','--instance','claude-write-boundary','--output',str(p/'sinks/result')],
            env=self.env,capture_output=True,text=True,timeout=45)
        retain_kernel_evidence(self.id(),result)
        self.assertEqual(result.returncode,0,result.stderr)
        r = json.loads(result.stdout)
        self.assertEqual(r['original_blocked_write'],'PermissionError',r)
        self.assertEqual(r['cwd_write'],'allowed',r)
        self.assertEqual(r['sink_write'],'allowed',r)
        self.assertEqual(r['outside_write'],'PermissionError',r)

    def test_unsupported_policy_fails_before_runner(self):
        config = self.root/'home/.codex/config.toml'
        config.write_text(config.read_text()+'\n[permissions.test]\n')
        result = self.launch()
        self.assertNotEqual(result.returncode,0)
        self.assertIn('cannot preserve custom', result.stderr)
        self.assertFalse((self.root/'sinks/result').exists())



class FullAccessTests(unittest.TestCase):
    def test_opt_in_flags_and_default_launches(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            (p/'bin').mkdir(); (p/'.codex').mkdir()
            (p/'.codex/gpt-6-sol.config.toml').write_text('')
            doc = json.loads((ROOT/'config/endpoints.example.json').read_text())
            doc['default']['mimo']['claude']['api_key'] = 'synthetic-key'
            ep = p/'.config/agent-tools/endpoints.json'; ep.parent.mkdir(parents=True)
            ep.write_text(json.dumps(doc)); ep.chmod(0o600)
            for name in ('codex','claude'):
                native = p/'bin'/name
                native.write_text('#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n'); native.chmod(0o755)
            (p/'bin/agent-endpoint.py').symlink_to(ROOT/'scripts/agent-endpoint.py')
            env = {**os.environ, 'HOME':str(p),'PATH':str(p/'bin')+':'+os.environ['PATH'],
                   'AGENT_TOOLS_FILE':str(ROOT/'scripts/agent-tools.zsh')}
            for runtime,provider in (('codex','gpt-6-sol'),('claude','mimo')):
                for full in (False,True):
                    cmd = [str(ROOT/f'scripts/{runtime}-agent-run'),'--provider',provider,'--cwd',str(p),'--prompt','literal --full-access','--detail']
                    if full: cmd.append('--full-access')
                    done = subprocess.run(cmd,env=env,capture_output=True,text=True)
                    self.assertEqual(done.returncode,0,done.stderr)
                    args = json.loads(done.stdout)
                    if runtime == 'claude': self.assertEqual(args[-1],'literal --full-access')
                    if runtime == 'codex':
                        self.assertEqual('--dangerously-bypass-approvals-and-sandbox' in args,full)
                    else:
                        settings = json.loads(args[args.index('--settings')+1])
                        self.assertEqual('--permission-mode' in args,full)
                        if full:
                            self.assertEqual(args[args.index('--permission-mode')+1],'bypassPermissions')
                            self.assertEqual(settings['sandbox'],{'enabled':False})
                        else: self.assertNotIn('sandbox',settings)
                conflict = [str(ROOT/f'scripts/{runtime}-agent-run'),'--provider',provider,'--cwd',str(p),'--prompt','test','--full-access']
                conflict += ['--sandbox','read-only'] if runtime == 'codex' else ['--permission-mode','auto']
                done = subprocess.run(conflict,env=env,capture_output=True,text=True)
                self.assertNotEqual(done.returncode,0)
                self.assertIn('conflicts',done.stderr)


    def test_direct_helper_full_access_conflicts(self):
        for extra in (['--permission-mode','auto'],['--settings','{}'],['--settings={}'],['--restricted']):
            done = subprocess.run([str(ROOT/'scripts/agent-endpoint.py'),'--full-access','--launch-claude','mimo','--',*extra],capture_output=True,text=True)
            self.assertEqual(done.returncode,2,done.stderr)
            self.assertEqual(done.stdout,'')
            self.assertIn('--full-access conflicts',done.stderr)

if __name__ == '__main__': unittest.main()
