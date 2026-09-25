"""Recovery checks for cross-provider Codex reasoning history."""

from __future__ import annotations

import json
import importlib.util
import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/repair-codex-reasoning-history.py"
SPEC = importlib.util.spec_from_file_location("repair_reasoning", SCRIPT)
assert SPEC and SPEC.loader
repair_reasoning = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repair_reasoning)


def row(kind: str, payload: dict) -> str:
    return json.dumps({"type": kind, "payload": payload}, separators=(",", ":")) + "\n"


class RepairReasoningHistoryTests(unittest.TestCase):
    def test_drops_reasoning_only_for_selected_model(self) -> None:
        original = (
            row("turn_context", {"model": "gpt-6-sol"})
            + row("response_item", {"type": "reasoning", "encrypted_content": "openai-secret", "content": None})
            + row("turn_context", {"model": "kimi-k3"})
            + row("response_item", {"type": "reasoning", "encrypted_content": "kimi-secret", "content": None, "summary": [{"type": "summary_text", "text": "summary"}]})
        ).encode()
        fixed, count = repair_reasoning.repair_lines(original, frozenset({"kimi-k3"}))
        self.assertEqual(count, 1)
        lines = fixed.splitlines()
        self.assertEqual(lines[1], original.splitlines()[1])
        self.assertEqual(lines[2], original.splitlines()[2])
        self.assertEqual(len(lines), 3)

    def test_reports_unmatched_model_and_rejects_invalid_context(self) -> None:
        original = row("turn_context", {"model": "kimi-k3"}) + row("response_item", {"type": "reasoning", "encrypted_content": "opaque"})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout-sample.jsonl"
            path.write_text(original)
            result = subprocess.run([sys.executable, str(SCRIPT), str(path), "--drop-reasoning-model", "kimi"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn("warning: no reasoning items matched", result.stderr)
            path.write_text(row("turn_context", {"model": {"unexpected": "object"}}) + original)
            bad = subprocess.run([sys.executable, str(SCRIPT), str(path), "--apply"], capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)
            self.assertIn("invalid model in turn_context at line 1", bad.stderr)
            self.assertNotIn("Traceback", bad.stderr)

    def test_consecutive_repairs_make_distinct_backups(self) -> None:
        original = (
            row("turn_context", {"model": "mimo-v2.6-pro"})
            + row("response_item", {"type": "reasoning", "content": [{"type": "reasoning_text", "text": "x"}]})
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout-sample.jsonl"
            path.write_text(original)
            path.chmod(0o600)
            first = subprocess.run([sys.executable, str(SCRIPT), str(path), "--apply"], capture_output=True, text=True)
            second = subprocess.run([sys.executable, str(SCRIPT), str(path), "--drop-reasoning-model", "mimo-v2.6-pro", "--apply"], capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(len(list(Path(tmp).glob("*.backup-*"))), 2)

    def test_backup_mode_ignores_restrictive_umask(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "backup"
            previous = os.umask(0o777)
            try:
                repair_reasoning.write_backup(path, b"private", 0o600)
            finally:
                os.umask(previous)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_repairs_only_reasoning_text_and_preserves_backup(self) -> None:
        original = (
            row("session_meta", {"id": "sample"})
            + row("response_item", {"type": "reasoning", "content": [{"type": "reasoning_text", "text": "private"}], "summary": []})
            + row("response_item", {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "answer"}]})
            + row("response_item", {"type": "reasoning", "content": None, "summary": []})
        ).encode()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout-sample.jsonl"
            path.write_bytes(original)
            path.chmod(0o600)
            dry = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
            self.assertEqual(dry.returncode, 0, dry.stderr)
            self.assertIn("affected reasoning items: 1", dry.stdout)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(Path(tmp).glob("*.backup-*")), [])

            applied = subprocess.run([sys.executable, str(SCRIPT), str(path), "--apply"], capture_output=True, text=True)
            self.assertEqual(applied.returncode, 0, applied.stderr)
            backup, = Path(tmp).glob("*.backup-*")
            self.assertEqual(backup.read_bytes(), original)
            self.assertEqual(backup.stat().st_mode & 0o777, 0o600)
            fixed = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertIsNone(fixed[1]["payload"]["content"])
            self.assertEqual(fixed[2]["payload"]["content"][0]["text"], "answer")
            self.assertEqual(fixed[3]["payload"]["content"], None)
            again = subprocess.run([sys.executable, str(SCRIPT), str(path), "--apply"], capture_output=True, text=True)
            self.assertEqual(again.returncode, 0, again.stderr)
            self.assertIn("affected reasoning items: 0", again.stdout)
            self.assertEqual(len(list(Path(tmp).glob("*.backup-*"))), 1)

    def test_rejects_unsupported_reasoning_and_invalid_json_without_writes(self) -> None:
        for original in [
            row("response_item", {"type": "reasoning", "content": [{"type": "other", "text": "x"}]}).encode(),
            b"{broken\n",
        ]:
            with self.subTest(original=original), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "rollout-sample.jsonl"
                path.write_bytes(original)
                bad = subprocess.run([sys.executable, str(SCRIPT), str(path), "--apply"], capture_output=True, text=True)
                self.assertNotEqual(bad.returncode, 0)
                self.assertEqual(path.read_bytes(), original)
                self.assertEqual(list(Path(tmp).glob("*.backup-*")), [])

    def test_preserves_blank_lines_and_carriage_return_endings(self) -> None:
        target = row("response_item", {"type": "reasoning", "content": [{"type": "reasoning_text", "text": "x"}]}).rstrip("\n")
        untouched = row("response_item", {"type": "message", "role": "user", "content": []}).rstrip("\n")
        original = (target + "\r\r" + untouched + "\r").encode()
        fixed, count = repair_reasoning.repair_lines(original)
        self.assertEqual(count, 1)
        self.assertEqual(fixed.split(b"\r")[1], b"")
        self.assertEqual(fixed.split(b"\r")[2], untouched.encode())
        self.assertIsNone(json.loads(fixed.split(b"\r")[0])["payload"]["content"])

    def test_aborts_if_rollout_changes_during_backup(self) -> None:
        original = row("response_item", {"type": "reasoning", "content": [{"type": "reasoning_text", "text": "x"}]}).encode()
        appended = row("response_item", {"type": "message", "role": "user", "content": []}).encode()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout-sample.jsonl"
            path.write_bytes(original)
            real_write_backup = repair_reasoning.write_backup

            def append_during_backup(backup: Path, data: bytes, mode: int) -> None:
                real_write_backup(backup, data, mode)
                with path.open("ab") as out:
                    out.write(appended)

            with mock.patch.object(repair_reasoning, "write_backup", side_effect=append_during_backup), mock.patch.object(sys, "argv", [str(SCRIPT), str(path), "--apply"]), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as exit_context:
                    repair_reasoning.main()
            self.assertEqual(exit_context.exception.code, 2)
            self.assertEqual(path.read_bytes(), original + appended)
            self.assertEqual(next(Path(tmp).glob("*.backup-*")).read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
