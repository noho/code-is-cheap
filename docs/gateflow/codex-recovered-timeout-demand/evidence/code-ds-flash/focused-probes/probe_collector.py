#!/usr/bin/env python3
"""ds-flash independent focused probes for slice code review S-1.

Synthetic JSONL fixtures only; no model/provider requests, no business data.
Runs the current working-tree collector directly and records per-case
exit/report evidence next to this script.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/Users/leo/workspace/code-is-cheap")
COLLECTOR = ROOT / "scripts/agent-run-result.py"
HERE = Path(__file__).resolve().parent


def claude_init(session="s"):
    return {"type": "system", "subtype": "init", "model": "synthetic", "session_id": session}


def claude_result(**fields):
    event = {"type": "result", "subtype": "success", "is_error": False, "result": "answer"}
    event.update(fields)
    return event


def codex_ok(text="done"):
    return [
        {"type": "thread.started", "thread_id": "t1"},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {"id": "m", "type": "agent_message", "text": text}},
        {"type": "turn.completed", "usage": {"input_tokens": 1}},
    ]


CASES = [
    # (name, runtime, events, expected exit, expected fields)
    ("claude_content_filter_rejects", "claude",
     [claude_init(), claude_result(stop_reason="content_filter", terminal_reason="completed")],
     1, {"validation_status": "rejected", "agent_status": "failed", "terminal": "failed"}),
    ("claude_end_turn_accepts", "claude",
     [claude_init(), claude_result(stop_reason="end_turn", terminal_reason="completed", api_error_status=None)],
     0, {"validation_status": "passed", "agent_status": "completed", "terminal": "success"}),
    ("claude_stop_sequence_accepts", "claude",
     [claude_init(), claude_result(stop_reason="stop_sequence", terminal_reason="completed")],
     0, {"validation_status": "passed", "agent_status": "completed"}),
    ("claude_null_absent_metadata_accepts", "claude",
     [claude_init(), claude_result(stop_reason=None)],
     0, {"validation_status": "passed", "agent_status": "completed"}),
    ("claude_duplicate_results_conflict", "claude",
     [claude_init(), claude_result(result="first"), claude_result(result="second")],
     1, {"validation_status": "rejected", "terminal": "conflicting", "final_answer": "first"}),
    ("claude_trailing_rate_limit_ignored", "claude",
     [claude_init(), claude_result(usage={"input_tokens": 5}),
      {"type": "rate_limit_event", "session_id": "other", "usage": {"input_tokens": 99}, "result": "fake"}],
     0, {"validation_status": "passed", "final_answer": "answer", "usage": {"input_tokens": 5}}),
    ("claude_is_error_true_rejects", "claude",
     [claude_init(), claude_result(is_error=True, stop_reason="end_turn")],
     1, {"validation_status": "rejected", "agent_status": "failed"}),
    ("claude_missing_result_keeps_partial", "claude",
     [claude_init(),
      {"type": "assistant", "message": {"content": [{"type": "text", "text": "partial"}]}, "session_id": "s"},
      {"type": "result", "subtype": "success", "is_error": False, "session_id": "s"}],
     1, {"validation_status": "rejected", "agent_status": "failed", "final_answer": "partial"}),
    ("claude_real_296_frame_mix_accepts", "claude",
     [claude_init(),
      {"type": "system", "subtype": "session_title_changed", "title": "x", "session_id": "s"},
      {"type": "system", "subtype": "ui_invalidate", "event": "ui.render", "session_id": "s"},
      {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "tool1", "name": "Bash",
        "input": {"command": "cat canary"}}], "stop_reason": None}, "parent_tool_use_id": None, "session_id": "s"},
      {"type": "system", "subtype": "permission_denied", "tool_name": "Bash", "tool_use_id": "tool1", "session_id": "s"},
      {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ALLOW_CANARY", "is_error": True,
        "tool_use_id": "tool1"}]}, "parent_tool_use_id": None, "session_id": "s"},
      {"type": "assistant", "message": {"content": [{"type": "text", "text": "Probe complete"}],
        "stop_reason": None}, "parent_tool_use_id": None, "session_id": "s"},
      claude_result(stop_reason="end_turn", terminal_reason="completed", api_error_status=None,
                    session_id="s", permission_denials=[{"tool_name": "Bash"}])],
     0, {"validation_status": "needs_review", "agent_status": "completed",
         "session_id": "s", "terminal": "success"}),
    ("claude_nested_task_pairing_accepts", "claude",
     [claude_init(),
      {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "task1", "name": "Task",
        "input": {"prompt": "x"}}]}, "parent_tool_use_id": None, "session_id": "s"},
      {"type": "assistant", "message": {"content": [{"type": "text", "text": "child"}]},
       "parent_tool_use_id": "task1", "session_id": "child"},
      {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "task1",
        "content": "ok", "is_error": False}]}, "parent_tool_use_id": None, "session_id": "s"},
      claude_result(stop_reason="end_turn", session_id="s")],
     0, {"validation_status": "passed", "agent_status": "completed", "final_answer": "answer"}),
    ("claude_nested_without_parent_rejects", "claude",
     [claude_init(),
      {"type": "assistant", "message": {"content": [{"type": "text", "text": "child"}]},
       "parent_tool_use_id": "task1", "session_id": "s"},
      claude_result(stop_reason="end_turn", session_id="s")],
     1, {"validation_status": "rejected", "agent_status": "failed"}),
    ("claude_errors_list_nonempty_rejects", "claude",
     [claude_init(), claude_result(stop_reason="end_turn", errors=["native error"])],
     1, {"validation_status": "rejected", "agent_status": "failed", "terminal": "failed"}),
    ("codex_novel_diagnostics_recover", "codex",
     [{"type": "thread.started", "thread_id": "t1"},
      {"type": "error", "message": "Reconnecting... 29/5 (novel upstream wording Ω)"},
      {"type": "turn.started"},
      {"type": "item.completed", "item": {"id": "d1", "type": "error", "message": "socket changed; demand timed out"}},
      {"type": "item.completed", "item": {"id": "m", "type": "agent_message", "text": "done"}},
      {"type": "error", "message": "after final novel diagnostic"},
      {"type": "turn.completed", "usage": {"input_tokens": 2}}],
     0, {"validation_status": "needs_review", "agent_status": "completed",
         "terminal": "turn.completed", "diagnostic_anomalies": 3}),
    ("codex_failed_then_completed_conflict", "codex",
     [{"type": "thread.started", "thread_id": "t1"}, {"type": "turn.started"},
      {"type": "item.completed", "item": {"id": "m", "type": "agent_message", "text": "done"}},
      {"type": "turn.failed", "error": {"message": "failed"}},
      {"type": "turn.completed", "usage": {}}],
     1, {"validation_status": "rejected", "terminal": "conflicting", "agent_status": "failed"}),
    ("codex_post_terminal_diagnostic_rejects", "codex",
     codex_ok() + [{"type": "error", "message": "trailing diagnostic payload probe"}],
     1, {"validation_status": "rejected", "agent_status": "failed", "final_answer": "done"}),
    ("codex_item_extra_field_rejects", "codex",
     [{"type": "thread.started", "thread_id": "t1"}, {"type": "turn.started"},
      {"type": "item.completed", "item": {"id": "m", "type": "agent_message", "text": "done",
                                          "status": "completed"}},
      {"type": "turn.completed", "usage": {}}],
     1, {"validation_status": "rejected", "agent_status": "failed"}),
    ("codex_missing_thread_id_rejects", "codex",
     [{"type": "thread.started"}, {"type": "turn.started"},
      {"type": "item.completed", "item": {"id": "m", "type": "agent_message", "text": "done"}},
      {"type": "turn.completed", "usage": {}}],
     1, {"validation_status": "rejected", "agent_status": "failed", "session_id": None}),
    ("codex_diagnostic_between_final_and_terminal_accepts", "codex",
     [{"type": "thread.started", "thread_id": "t1"}, {"type": "turn.started"},
      {"type": "item.completed", "item": {"id": "m", "type": "agent_message", "text": "done"}},
      {"type": "error", "message": "diagnostic after final before terminal"},
      {"type": "turn.completed", "usage": {}}],
     0, {"validation_status": "needs_review", "agent_status": "completed"}),
]


def run_case(name, runtime, events):
    case_dir = HERE / "cases" / name
    case_dir.mkdir(parents=True, exist_ok=True)
    output = case_dir / "events.jsonl"
    stderr = case_dir / "stderr.log"
    output.write_text("\n".join(json.dumps(e) for e in events) + "\n")
    stderr.write_text("")
    argv = [sys.executable, "-B", str(COLLECTOR), "--runtime", runtime, "--provider", "synthetic",
            "--output", str(output), "--stderr", str(stderr),
            "--exit-code", "0", "--runner-exit-code", "0"]
    result = subprocess.run(argv, capture_output=True, text=True)
    report = json.loads(result.stdout) if result.stdout.strip() else None
    (case_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    (case_dir / "meta.json").write_text(json.dumps({"argv": argv, "exit": result.returncode,
                                                    "stderr": result.stderr}, indent=2))
    return result.returncode, report


def extract(report, expected):
    out = {}
    for key in ("validation_status", "agent_status", "terminal", "final_answer", "session_id",
                "usage", "diagnostic_counts"):
        if key in expected:
            out[key] = report.get(key)
    if "diagnostic_anomalies" in expected:
        out["diagnostic_anomalies"] = report.get("diagnostic_counts", {}).get("anomalies")
    # Observation fields recorded regardless of expectation.
    out["errors_first"] = [d["message"][:120] for d in report.get("errors", [])[:2]]
    out["anomalies_first"] = [d["message"][:120] for d in report.get("anomalies", [])[:3]]
    out["anomaly_payload_retained"] = any("trailing diagnostic payload probe" in d["message"]
                                          for d in report.get("anomalies", []))
    return out


def main():
    results = []
    failures = 0
    for name, runtime, events, expected_exit, expected in CASES:
        exit_code, report = run_case(name, runtime, events)
        observed = extract(report, expected) if report else {}
        ok = exit_code == expected_exit and all(observed.get(k) == v for k, v in expected.items())
        if not ok:
            failures += 1
        results.append({"case": name, "runtime": runtime, "expected_exit": expected_exit,
                        "actual_exit": exit_code, "expected": expected, "observed": observed,
                        "pass": ok})
        print(f"{'PASS' if ok else 'FAIL'} {name}: exit={exit_code} {observed}")
    summary = {"collector": str(COLLECTOR),
               "collector_sha256": __import__("hashlib").sha256(COLLECTOR.read_bytes()).hexdigest(),
               "cases": len(CASES), "passed": len(CASES) - failures, "failed": failures,
               "results": results}
    (HERE / "results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n{len(CASES) - failures}/{len(CASES)} focused probes passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
