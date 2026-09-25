"""The launchd shim must use Python from the destination machine."""

import os
import json
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import unittest


SERVICE = Path(__file__).resolve().parents[1] / "codex-agent/bin/codex-auto-review-shim-service"


class ShimServiceTests(unittest.TestCase):
    def test_print_plist_uses_available_python(self):
        with tempfile.TemporaryDirectory() as temp:
            home, bin_dir, env = self._fixture(Path(temp))
            result = subprocess.run(
                [str(SERVICE), "print-plist"], env=env, capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"<string>{self._python_executable(bin_dir)}</string>", result.stdout)
            self.assertNotIn("/opt/homebrew/bin/python3", result.stdout)
            self.assertFalse((home / "Library/LaunchAgents").exists())

    def test_install_replaces_loaded_plist_from_another_machine(self):
        with tempfile.TemporaryDirectory() as temp:
            home, bin_dir, env = self._fixture(Path(temp))
            (home / "loaded").touch()
            plist = home / "Library/LaunchAgents/com.leo.codex-auto-review-shim.plist"
            plist.parent.mkdir(parents=True)
            plist.write_text("<string>/old-machine/python3</string>\n")
            result = subprocess.run(
                [str(SERVICE), "install"], env=env, capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"<string>{self._python_executable(bin_dir)}</string>", plist.read_text())
            self.assertNotIn("/old-machine/python3", plist.read_text())
            self.assertEqual((home / "events").read_text().splitlines(), ["bootout", "bootstrap"])

    def test_install_detects_every_configured_port_before_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            home, _, env = self._fixture(Path(temp))
            env["CONFLICT_PORT"] = "8794"
            result = subprocess.run(
                [str(SERVICE), "install"], env=env, capture_output=True, text=True
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("8794", result.stderr)
            self.assertFalse((home / "events").exists())
            self.assertFalse((home / "Library/LaunchAgents/com.leo.codex-auto-review-shim.plist").exists())

    def test_failed_reinstall_restores_previous_plist_and_service(self):
        with tempfile.TemporaryDirectory() as temp:
            home, _, env = self._fixture(Path(temp))
            (home / "loaded").touch()
            (home / "fail_bootstrap_once").touch()
            plist = home / "Library/LaunchAgents/com.leo.codex-auto-review-shim.plist"
            plist.parent.mkdir(parents=True)
            plist.write_text("old plist\n")
            result = subprocess.run(
                [str(SERVICE), "install"], env=env, capture_output=True, text=True
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(plist.read_text(), "old plist\n")
            self.assertTrue((home / "loaded").exists())
            self.assertEqual((home / "events").read_text().splitlines(),
                             ["bootout", "bootstrap_failed", "bootout", "bootstrap"])

    def test_conflict_after_bootout_restores_previous_service(self):
        with tempfile.TemporaryDirectory() as temp:
            home, _, env = self._fixture(Path(temp))
            (home / "loaded").touch()
            env["CONFLICT_PORT"] = "8794"
            plist = home / "Library/LaunchAgents/com.leo.codex-auto-review-shim.plist"
            plist.parent.mkdir(parents=True)
            plist.write_text("old plist\n")
            result = subprocess.run(
                [str(SERVICE), "install"], env=env, capture_output=True, text=True
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("8794", result.stderr)
            self.assertEqual(plist.read_text(), "old plist\n")
            self.assertTrue((home / "loaded").exists())
            self.assertEqual((home / "events").read_text().splitlines(), ["bootout", "bootout", "bootstrap"])

    def test_missing_listeners_fail_and_roll_back(self):
        with tempfile.TemporaryDirectory() as temp:
            home, _, env = self._fixture(Path(temp))
            (home / "loaded").touch()
            env["NO_LISTEN"] = "1"
            plist = home / "Library/LaunchAgents/com.leo.codex-auto-review-shim.plist"
            plist.parent.mkdir(parents=True)
            plist.write_text("old plist\n")
            result = subprocess.run(
                [str(SERVICE), "install"], env=env, capture_output=True, text=True
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("未在所有路由端口启动", result.stderr)
            self.assertEqual(plist.read_text(), "old plist\n")
            self.assertTrue((home / "loaded").exists())

    def test_plist_escapes_home_path(self):
        with tempfile.TemporaryDirectory() as temp:
            home, _, env = self._fixture(Path(temp), home_name="destination & home")
            result = subprocess.run(
                [str(SERVICE), "install"], env=env, capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            plist = home / "Library/LaunchAgents/com.leo.codex-auto-review-shim.plist"
            with plist.open("rb") as stream:
                data = plistlib.load(stream)
            self.assertEqual(data["ProgramArguments"][1], str(home / ".codex-agent/bin/codex-auto-review-shim"))
            self.assertIn("&amp;", plist.read_text())

    def test_optimized_python_does_not_admit_old_system_python(self):
        system_python = Path("/usr/bin/python3")
        if not system_python.exists():
            self.skipTest("no macOS system Python")
        version = json.loads(subprocess.check_output(
            [str(system_python), "-c", "import json,sys; print(json.dumps(sys.version_info[:2]))"],
            text=True,
        ))
        if tuple(version) >= (3, 11):
            self.skipTest("system Python is already 3.11+")
        with tempfile.TemporaryDirectory() as temp:
            _, bin_dir, env = self._fixture(Path(temp))
            (bin_dir / "python3").unlink()
            (bin_dir / "python3").symlink_to(system_python)
            env["PYTHONOPTIMIZE"] = "1"
            result = subprocess.run(
                [str(SERVICE), "print-plist"], env=env, capture_output=True, text=True
            )
            if result.returncode == 0:
                selected = plistlib.loads(result.stdout.encode())["ProgramArguments"][0]
                selected_version = json.loads(subprocess.check_output(
                    [selected, "-c", "import json,sys; print(json.dumps(sys.version_info[:2]))"],
                    text=True,
                ))
                self.assertGreaterEqual(tuple(selected_version), (3, 11))
            else:
                self.assertIn("找不到可用的 Python 3.11+", result.stderr)

    @staticmethod
    def _python_executable(bin_dir):
        return subprocess.check_output(
            [str(bin_dir / "python3"), "-I", "-S", "-c", "import os,sys;print(os.path.abspath(sys.executable))"],
            text=True,
        ).strip()

    @staticmethod
    def _fixture(root, home_name="destination home"):
        home = root / home_name
        bin_dir = root / "bin"
        bin_dir.mkdir()
        (bin_dir / "python3").symlink_to(sys.executable)
        for name, body in {
            "launchctl": """#!/bin/sh
case "$1" in
  print) test -f "$HOME/loaded" ;;
  bootout) rm "$HOME/loaded"; echo bootout >> "$HOME/events" ;;
  bootstrap)
    if [ -f "$HOME/fail_bootstrap_once" ]; then
      rm "$HOME/fail_bootstrap_once"
      echo bootstrap_failed >> "$HOME/events"
      exit 1
    fi
    touch "$HOME/loaded"; echo bootstrap >> "$HOME/events" ;;
esac
""",
            "lsof": """#!/bin/sh
for arg in "$@"; do
  if [ "$arg" = "-iTCP:$CONFLICT_PORT" ]; then exit 0; fi
done
if [ "$NO_LISTEN" = "1" ]; then exit 1; fi
test -f "$HOME/loaded"
""",
            "sleep": "#!/bin/sh\nexit 0\n",
        }.items():
            path = bin_dir / name
            path.write_text(body)
            path.chmod(0o755)
        shim = home / ".codex-agent/bin/codex-auto-review-shim"
        shim.parent.mkdir(parents=True)
        shim.write_text("#!/bin/sh\n")
        shim.chmod(0o755)
        (home / ".codex-agent/shim-routes.json").write_text(
            '{"routes":[{"port":8788},{"port":8794}]}\n'
        )
        env = os.environ | {"HOME": str(home), "PATH": f"{bin_dir}:/usr/bin:/bin"}
        return home, bin_dir, env


if __name__ == "__main__":
    unittest.main()
