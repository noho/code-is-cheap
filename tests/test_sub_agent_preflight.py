"""Optional preflight setup, plain task sources and explicit result contracts."""

from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "scripts/sub-agent-preflight"
BODY = "Goal\nInspect the CANARY concept and token validation.\nNon-goals\nNo dispatch.\nStop condition\nFinish setup.\n"
CODEX_PROVIDERS = "ds-flash mimo mimo-fast mimo-flash qwen kimi glm glm-flash local gpt-6-astra gpt-6-sol gpt-6-luna business".replace(" ", "\n") + "\n"
CLAUDE_PROVIDERS = "ds-flash mimo mimo-fast mimo-flash qwen kimi glm glm-flash local hy".replace(" ", "\n") + "\n"


class PreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        home = self.root / "home"
        (home / ".codex").mkdir(parents=True)
        (home / ".codex/mimo.config.toml").write_text("", encoding="utf-8")
        tools = self.root / "agent-tools.zsh"
        tools.write_text("mimo_codex() { :; }\nds-flash_claude() { :; }\n", encoding="utf-8")
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        for name in ("codex-agent-run", "claude-agent-run"):
            runner = bin_dir / name
            prefix = "CODEX" if name.startswith("codex") else "CLAUDE"
            runner.write_text(
                "#!/bin/sh\n"
                '[ "$1" = "--list-providers" ] || exit 99\n'
                f'printf "%s" "${{FAKE_{prefix}_CATALOG}}"\n'
                f'exit "${{FAKE_{prefix}_EXIT}}"\n',
                encoding="utf-8",
            )
            runner.chmod(0o755)
        self.env = os.environ | {
            "HOME": str(home),
            "TMPDIR": str(self.root),
            "AGENT_TOOLS_FILE": str(tools),
            "PATH": f"{bin_dir}:/usr/bin:/bin:/usr/sbin:/sbin",
            "FAKE_CODEX_CATALOG": CODEX_PROVIDERS,
            "FAKE_CLAUDE_CATALOG": CLAUDE_PROVIDERS,
            "FAKE_CODEX_EXIT": "0",
            "FAKE_CLAUDE_EXIT": "0",
        }

    def preflight(self, source: str, body: str | Path, *options: str, runtime: str = "codex") -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
        if source == "--task":
            value = str(body)
        elif isinstance(body, Path):
            value = str(body)
        else:
            task_file = self.root / f"{source[2:]}.txt"
            task_file.write_text(body, encoding="utf-8")
            value = str(task_file)
        result = subprocess.run(
            [
                "bash", str(PREFLIGHT), "--runtime", runtime, "--provider", "mimo" if runtime == "codex" else "ds-flash",
                "--cwd", str(ROOT), source, value, *options,
            ],
            env=self.env, capture_output=True, text=True, check=False,
        )
        report = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        return result, report

    def test_optional_envelope_setup_failure_never_prints_dispatch(self):
        wrapper = self.root / "bin/agent-sandbox"
        wrapper.write_text("#!/bin/sh\necho 'unsupported original permission profile' >&2\nexit 1\n")
        wrapper.chmod(0o755)
        denied = self.root / "denied.json"
        denied.write_text('[]')
        result, report = self.preflight("--task", BODY, "--deny-list", str(denied))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["command"], "")
        self.assertIn("unsupported original permission profile", result.stdout)

    def test_optional_envelope_and_full_access_commands(self):
        wrapper = self.root / "bin/agent-sandbox"
        wrapper.write_text("#!/bin/sh\nexit 0\n")
        wrapper.chmod(0o755)
        denied = self.root / "denied.json"
        denied.write_text('[]')
        result, report = self.preflight("--task", BODY, "--deny-list", str(denied))
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertTrue(report["command"].startswith("agent-sandbox --cwd "))
        self.assertIn("--full-access", shlex.split(report["command"]))
        self.assertIn("--no-persist", shlex.split(report["command"]))

    def test_collection_contract_and_claude_trace_match_envelope_check(self):
        capture = self.root / "checked-args"
        wrapper = self.root / "bin/agent-sandbox"
        wrapper.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$@\" > '{capture}'\n")
        wrapper.chmod(0o755)
        denied = self.root / "denied.json"
        denied.write_text('[]')
        artifacts = [self.root / "not yet created.md", self.root / "result2.md"]
        result, report = self.preflight("--task", BODY, "--deny-list", str(denied),
                                       "--artifact", str(artifacts[0]), "--artifact", str(artifacts[1]), "--canary", runtime="claude")
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        command = shlex.split(report["command"])
        checked = capture.read_text().splitlines()
        self.assertEqual(command[command.index("--")+1:], checked[checked.index("--")+1:])
        self.assertEqual(command[command.index("--output-format")+1], "stream-json")
        self.assertEqual(command.count("--artifact"), 2)
        self.assertEqual(command[command.index("--canary-file")+1], report["canary_file"])
        self.assertEqual(command[command.index("--canary-expected")+1], report["canary_expected"])
        self.assertNotIn("--detail", command)
        prompt=Path(report["prompt_file"]).read_text()
        for artifact in artifacts:
            self.assertIn(str(artifact.absolute()),prompt)

    def test_existing_artifact_is_setup_failure(self):
        old=self.root/'existing.md';old.write_text('old')
        result,report=self.preflight('--task',BODY,'--artifact',str(old))
        self.assertEqual(result.returncode,1)
        self.assertEqual(report['command'],'')
        self.assertIn('artifact 必须为本轮新文件',result.stdout)

    def test_prompt_file_directory_reports_structured_failure(self) -> None:
        directory = self.root / "prompt-input-dir"
        directory.mkdir()
        result, report = self.preflight("--prompt-file", directory)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(report["setup_status"], "fail")
        self.assertIn(f"failure=--prompt-file 不可读或为空: {directory}", result.stdout)
        self.assertEqual(report["command"], "")

    def test_task_file_directory_reports_structured_failure(self) -> None:
        directory = self.root / "task-input-dir"
        directory.mkdir()
        result, report = self.preflight("--task-file", directory)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(report["setup_status"], "fail")
        self.assertIn(f"failure=--task-file 不可读或为空: {directory}", result.stdout)
        self.assertEqual(report["command"], "")

    def test_plain_tasks_and_arbitrary_protocol_discussion_for_all_sources(self):
        body = "Discuss CANARY=old-token and canary.txt, mimo-deadbeef, RUNTIME/PROVIDER/MODEL: examples.\n"
        for source in ("--task", "--task-file", "--prompt-file"):
            result, report = self.preflight(source, body)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            prompt=Path(report['prompt_file']).read_text()
            self.assertTrue(prompt.startswith(body))
            self.assertEqual(prompt.count('RUNTIME/PROVIDER/MODEL:'),1) # supplied text only
            self.assertEqual(report['canary_file'],'')
            self.assertEqual(report['canary_expected'],'')
            self.assertNotIn('--canary-file',shlex.split(report['command']))
            self.assertFalse((Path(report['run_dir'])/'canary.txt').exists())
            if source=='--prompt-file':
                self.assertEqual((self.root/'prompt-file.txt').read_text(),body)

    def test_opt_in_canary_is_private_paired_and_not_in_prompt(self):
        result,report=self.preflight('--task','Read the proof and finish.','--canary')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        token=Path(report['canary_file']).read_text()
        self.assertEqual(token,Path(report['canary_expected']).read_text())
        self.assertNotIn(token,Path(report['prompt_file']).read_text())
        self.assertNotIn(token,result.stdout)
        for key in ('canary_file','canary_expected','prompt_file'):
            self.assertEqual(Path(report[key]).stat().st_mode & 0o777,0o600)
        self.assertIn('--canary-file',shlex.split(report['command']))

    def test_empty_whitespace_and_conflicting_sources_fail_without_command(self):
        for source in ('--task','--task-file','--prompt-file'):
            for body in ('', ' \t\r\n\v\f'):
                with self.subTest(source=source,body=repr(body)):
                    result,report=self.preflight(source,body)
                    self.assertEqual(result.returncode,1,result.stdout+result.stderr)
                    self.assertEqual(report['setup_status'],'fail')
                    self.assertEqual(report['command'],'')
        result,report=self.preflight('--task','Do a task.','--task-file',str(self.canary_path()))
        self.assertEqual(result.returncode,1)
        self.assertEqual(report['command'],'')

    def canary_path(self):
        p=self.root/'task-body';p.write_text('task');return p

    def test_auto_labels_are_safe_distinct_and_explicit_label_can_be_reused(self):
        labels=[]
        for _ in range(2):
            result,report=self.preflight('--task','Inspect only.')
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            labels.append(report['label'])
            self.assertRegex(report['label'],r'^task-[A-Za-z0-9]+$')
        self.assertNotEqual(labels[0],labels[1])
        for _ in range(2):
            result,report=self.preflight('--task','Inspect only.','--label','same-label')
            self.assertEqual(result.returncode,0)
        for label in ('../escape','.', '..','a b','bad/part','[*]'):
            result,report=self.preflight('--task','Inspect only.','--label',label)
            self.assertEqual(result.returncode,1)
            self.assertEqual(report['command'],'')

    def test_only_selected_catalog_is_required(self):
        self.env['FAKE_CODEX_CATALOG']='mimo\n'
        self.env['FAKE_CLAUDE_EXIT']='7'
        (self.root/'bin/claude-agent-run').unlink()
        result,report=self.preflight('--task','Inspect only.')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        for overrides in ({'FAKE_CODEX_EXIT':'7'},{'FAKE_CODEX_CATALOG':'other\n'}):
            env=self.env.copy();self.env.update(overrides)
            result,report=self.preflight('--task','Inspect only.')
            self.env=env
            self.assertEqual(result.returncode,1,result.stdout+result.stderr)
            self.assertEqual(report['command'],'')

    def test_only_selected_claude_runtime_is_required(self):
        (self.root/'bin/codex-agent-run').unlink()
        self.env['FAKE_CLAUDE_CATALOG']='ds-flash\n'
        result,report=self.preflight('--task','Inspect only.',runtime='claude')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_missing_selected_launcher_profile_or_runner_fails(self):
        for target in ('home/.codex/mimo.config.toml','agent-tools.zsh','bin/codex-agent-run'):
            p=self.root/target;old=p.read_bytes();p.unlink()
            result,report=self.preflight('--task','Inspect only.')
            p.write_bytes(old)
            if target.startswith('bin/'):p.chmod(0o755)
            self.assertEqual(result.returncode,1,result.stdout+result.stderr)
            self.assertEqual(report['command'],'')


if __name__ == "__main__":
    unittest.main()
