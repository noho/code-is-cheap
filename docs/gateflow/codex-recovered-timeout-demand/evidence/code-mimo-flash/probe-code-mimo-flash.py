#!/usr/bin/env python3
"""Focused reviewer probes for S-1 slice code review (mimo-flash, synthetic only).

Each probe records name, exact command class, exit code and selected report fields.
No business data, no provider requests, no network.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
COLLECTOR = ROOT / "scripts" / "agent-run-result.py"
results = []


def collector(events, runtime="codex", native=0, precollection=0, err="", tmp=None):
    tmp = tmp or Path(tempfile.mkdtemp(prefix="mimo-probe-"))
    output, stderr = tmp / "output.jsonl", tmp / "stderr.log"
    output.write_text("\n".join(json.dumps(e) if isinstance(e, dict) else e for e in events) + "\n")
    stderr.write_text(err)
    argv = [sys.executable, "-B", str(COLLECTOR), "--runtime", runtime,
            "--provider", "synthetic", "--output", str(output), "--stderr", str(stderr),
            "--exit-code", str(native), "--runner-exit-code", str(precollection)]
    proc = subprocess.run(argv, capture_output=True, text=True)
    report = json.loads(proc.stdout) if proc.stdout.strip() else None
    return argv, proc, report


def codex_stream():
    return [{"type": "thread.started", "thread_id": "probe"},
            {"type": "turn.started"},
            {"type": "item.completed", "item": {"id": "m", "type": "agent_message", "text": "done"}},
            {"type": "turn.completed", "usage": {}}]


def record(name, argv, proc, report, checks):
    entry = {
        "name": name,
        "command": argv,
        "exit": proc.returncode,
        "stderr": proc.stderr[:500],
        "report": None if report is None else {
            "validation_status": report["validation_status"],
            "agent_status": report["agent_status"],
            "result_status": report["result_status"],
            "runner_exit_code": report["runner_exit_code"],
            "runtime_exit_code": report["runtime_exit_code"],
            "terminal": report["terminal"],
            "session_id": report["session_id"],
            "final_answer": report["final_answer"],
            "diagnostic_counts": report["diagnostic_counts"],
            "error_messages": [e["message"][:120] for e in report["errors"]],
            "anomaly_lines": [a["line"] for a in report["anomalies"]],
        } if report else None,
        "checks": checks,
    }
    results.append(entry)
    ok = all(checks.values())
    print(("PASS " if ok else "FAIL ") + name + " -> exit=" + str(proc.returncode)
          + " " + json.dumps(entry["report"], ensure_ascii=False)[:400])
    return ok


# P1: garbage preamble line before thread.started (nonblank first frame is not thread.started)
argv, proc, rep = collector(["not-json", *codex_stream()])
record("P1-preamble-garbage-before-thread-start", argv, proc, rep, {
    "exit_nonzero": proc.returncode != 0,
    "rejected": rep["validation_status"] == "rejected",
    "failed": rep["agent_status"] == "failed",
    "start_order_error": any("start" in m for m in [e["message"] for e in rep["errors"]]),
})

# P2: rate_limit_event mid-turn (after turn.started, before final) is inert metadata
stream = codex_stream()
stream.insert(2, {"type": "rate_limit_event", "session_id": "x", "usage": {"tokens": 9}})
argv, proc, rep = collector(stream)
record("P2-midturn-rate-limit-inert", argv, proc, rep, {
    "exit_zero": proc.returncode == 0,
    "passed": rep["validation_status"] == "passed",
    "completed": rep["agent_status"] == "completed",
    "final_ok": rep["final_answer"] == "done",
})

# P3: native and precollection both nonzero and equal -> single native note, exact code preserved
argv, proc, rep = collector(codex_stream(), native=7, precollection=7)
record("P3-equal-nonzero-native-and-postprocessing", argv, proc, rep, {
    "exit_nonzero": proc.returncode != 0,
    "rejected": rep["validation_status"] == "rejected",
    "failed": rep["agent_status"] == "failed",
    "runner_code_preserved": rep["runner_exit_code"] == 7,
    "native_code_preserved": rep["runtime_exit_code"] == 7,
    "no_duplicate_runner_note": sum("postprocessing" in e["message"] for e in rep["errors"]) == 0,
})

# P4: Claude success-labeled content_filter through the PUBLIC claude runner end to end
with tempfile.TemporaryDirectory(prefix="mimo-e2e-") as tmp:
    tmp = Path(tmp)
    fixture = tmp / "events.jsonl"
    fixture.write_text("\n".join(json.dumps(e) for e in [
        {"type": "system", "subtype": "init", "model": "synthetic"},
        {"type": "result", "subtype": "success", "is_error": False, "result": "done",
         "stop_reason": "content_filter", "terminal_reason": "completed"}]) + "\n")
    tools = tmp / "tools.zsh"
    tools.write_text(f"ds-flash_claude() {{ cat '{fixture}'; }}\n")
    env = os.environ | {"AGENT_TOOLS_FILE": str(tools), "TMPDIR": str(tmp),
                        "PATH": f"{tmp}:{os.environ['PATH']}"}
    (tmp / "claude").write_text("#!/bin/sh\nexit 99\n")
    (tmp / "claude").chmod(0o755)
    argv = [str(ROOT / "scripts" / "claude-agent-run"), "--provider", "ds-flash",
            "--cwd", str(tmp), "--prompt", "synthetic probe"]
    proc = subprocess.run(argv, capture_output=True, text=True, env=env, cwd=str(ROOT))
    rep = json.loads(proc.stdout) if proc.stdout.strip().startswith("{") else None
    entry = {
        "name": "P4-public-runner-success-content-filter-rejects",
        "command": argv,
        "exit": proc.returncode,
        "stderr": proc.stderr[:500],
        "report": None if rep is None else {
            "validation_status": rep["validation_status"],
            "agent_status": rep["agent_status"],
            "result_status": rep["result_status"],
            "terminal": rep["terminal"],
            "final_answer": rep["final_answer"],
            "diagnostic_counts": rep["diagnostic_counts"],
        },
        "checks": {
            "exit_nonzero": proc.returncode == 1,
            "rejected": rep is not None and rep["validation_status"] == "rejected",
            "failed": rep is not None and rep["agent_status"] == "failed",
            "failed_terminal": rep is not None and rep["terminal"] == "failed",
            "not_assessed": rep is not None and rep["result_status"] == "not_assessed",
            "text_retained": rep is not None and rep["final_answer"] == "done",
        },
    }
    results.append(entry)
    ok = all(entry["checks"].values())
    print(("PASS " if ok else "FAIL ") + entry["name"] + " -> exit=" + str(proc.returncode)
          + " " + json.dumps(entry["report"], ensure_ascii=False)[:400])

# P5: post-terminal rate_limit is skipped, a later diagnostic still fences the stream
stream = codex_stream()
stream.append({"type": "rate_limit_event", "session_id": "later"})
stream.append({"type": "error", "message": "after terminal"})
argv, proc, rep = collector(stream)
record("P5-trailing-rate-limit-then-diagnostic-fences", argv, proc, rep, {
    "exit_nonzero": proc.returncode != 0,
    "rejected": rep["validation_status"] == "rejected",
    "final_preserved": rep["final_answer"] == "done",
    "fence_error": any("after runtime terminal" in e["message"] for e in rep["errors"]),
})

# P6: explicit null parent_tool_use_id on a root result denotes root (plan compatibility rule)
events = [{"type": "result", "subtype": "success", "is_error": False, "result": "done",
           "parent_tool_use_id": None}]
argv, proc, rep = collector(events, runtime="claude")
record("P6-explicit-null-parent-is-root", argv, proc, rep, {
    "exit_zero": proc.returncode == 0,
    "passed": rep["validation_status"] == "passed",
    "completed": rep["agent_status"] == "completed",
})

# P7: pre-turn structural diagnostic (nonstring message) stays a hard error, not an anomaly
stream = [{"type": "thread.started", "thread_id": "probe"},
          {"type": "error", "message": 42},
          {"type": "turn.started"},
          {"type": "item.completed", "item": {"id": "m", "type": "agent_message", "text": "done"}},
          {"type": "turn.completed", "usage": {}}]
argv, proc, rep = collector(stream)
record("P7-preturn-nonstring-diagnostic-hard-error", argv, proc, rep, {
    "exit_nonzero": proc.returncode != 0,
    "rejected": rep["validation_status"] == "rejected",
    "is_error_not_anomaly": rep["diagnostic_counts"]["errors"] >= 1
                            and rep["diagnostic_counts"]["anomalies"] == 0,
})

passed = sum(1 for r in results if all(r["checks"].values()))
summary = {"total": len(results), "passed": passed, "failed": len(results) - passed,
           "results": results}
out = Path(__file__).with_name("probe-results.json")
out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
print(json.dumps({"total": len(results), "passed": passed, "failed": len(results) - passed}))
sys.exit(0 if passed == len(results) else 1)
