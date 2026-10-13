"""Independent mimo-flash focused synthetic re-review probe for DS-A1 at current source.

Runs the current collector directly against generated synthetic event streams only.
No business originals, no other-agent raw logs, no model/runtime requests, no runner.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path("/Users/leo/workspace/code-is-cheap")
COLLECTOR = REPO / "scripts" / "agent-run-result.py"
HERE = Path(__file__).resolve().parent


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def init_event():
    return {"type": "system", "subtype": "init", "model": "fixture"}


def assistant(text, **fields):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}, **fields}


def tool_call(identity, **fields):
    return {"type": "assistant",
            "message": {"content": [{"type": "tool_use", "id": identity, "name": "Bash", "input": {}}]},
            **fields}


def tool_result(identity, **fields):
    return {"type": "user",
            "message": {"content": [{"type": "tool_result", "tool_use_id": identity,
                                     "content": "synthetic output", "is_error": False}]},
            **fields}


def result_event(text, **fields):
    event = {"type": "result", "subtype": "success", "is_error": False}
    event.update(fields)
    if "result" not in event:
        event["result"] = text
    return event


def claude_ok(text):
    return result_event(text, stop_reason="end_turn", terminal_reason="completed")


def run(events, *extra, runtime="claude", exit_code=0, runner_exit_code=0, root=None, err=""):
    output = root / "collector.jsonl"
    stderr = root / "collector.stderr"
    output.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    stderr.write_text(err, encoding="utf-8")
    argv = [sys.executable, "-B", str(COLLECTOR),
            "--runtime", runtime, "--provider", "mimo" if runtime == "codex" else "ds-flash",
            "--output", str(output), "--stderr", str(stderr),
            "--exit-code", str(exit_code), "--runner-exit-code", str(runner_exit_code), *extra]
    started = time.time()
    proc = subprocess.run(argv, capture_output=True, text=True)
    report = json.loads(proc.stdout)
    return {"argv": argv, "returncode": proc.returncode, "stderr": proc.stderr,
            "wall_seconds": round(time.time() - started, 3), "report": report}


def error_messages(report):
    return [d["message"] for d in report["errors"]]


CASES = []


def case(name):
    def wrap(fn):
        CASES.append((name, fn))
        return fn
    return wrap


@case("blank_result_keeps_partial_rejects")
def _(ctx):
    events = [init_event(), assistant("partial root"), claude_ok("")]
    r = run(events, root=ctx["root"])
    rep = r["report"]
    assert r["returncode"] == 1 and rep["runner_exit_code"] == 1
    assert rep["validation_status"] == "rejected" and rep["agent_status"] == "failed"
    assert rep["result_status"] == "not_assessed" and rep["terminal"] == "failed"
    assert rep["final_answer"] == "partial root" and rep["final_answer_chars"] == 12
    msgs = error_messages(rep)
    assert any("missing valid complete final answer" in m for m in msgs), msgs
    assert any("invalid or unsuccessful result terminal" in m for m in msgs), msgs
    return r


@case("whitespace_result_keeps_partial_rejects")
def _(ctx):
    events = [init_event(), assistant("partial root"), claude_ok("  ")]
    r = run(events, root=ctx["root"])
    rep = r["report"]
    assert r["returncode"] == 1 and rep["validation_status"] == "rejected"
    assert rep["agent_status"] == "failed" and rep["terminal"] == "failed"
    assert rep["final_answer"] == "partial root" and rep["final_answer_chars"] == 12
    assert any("missing valid complete final answer" in m for m in error_messages(rep))
    return r


@case("missing_result_key_keeps_partial_rejects")
def _(ctx):
    events = [init_event(), assistant("partial root"), {"type": "result", "subtype": "success",
                                                        "is_error": False, "stop_reason": "end_turn",
                                                        "terminal_reason": "completed"}]
    r = run(events, root=ctx["root"])
    rep = r["report"]
    assert r["returncode"] == 1 and rep["validation_status"] == "rejected"
    assert rep["final_answer"] == "partial root" and rep["final_answer_chars"] == 12
    assert rep["agent_status"] == "failed" and rep["result_status"] == "not_assessed"
    return r


@case("null_result_keeps_partial_rejects")
def _(ctx):
    events = [init_event(), assistant("partial root"),
              result_event(None, stop_reason="end_turn", terminal_reason="completed")]
    r = run(events, root=ctx["root"])
    rep = r["report"]
    assert r["returncode"] == 1 and rep["validation_status"] == "rejected"
    assert rep["final_answer"] == "partial root" and rep["final_answer_chars"] == 12
    return r


@case("number_result_keeps_partial_rejects")
def _(ctx):
    events = [init_event(), assistant("partial root"),
              {"type": "result", "subtype": "success", "is_error": False, "result": 42,
               "stop_reason": "end_turn", "terminal_reason": "completed"}]
    r = run(events, root=ctx["root"])
    rep = r["report"]
    assert r["returncode"] == 1 and rep["validation_status"] == "rejected"
    assert rep["final_answer"] == "partial root" and rep["final_answer_chars"] == 12
    assert rep["agent_status"] == "failed" and rep["terminal"] == "failed"
    return r


@case("blank_no_prior_empty_display_rejects")
def _(ctx):
    events = [init_event(), claude_ok("")]
    r = run(events, root=ctx["root"])
    rep = r["report"]
    assert r["returncode"] == 1 and rep["validation_status"] == "rejected"
    assert rep["agent_status"] == "failed" and rep["result_status"] == "not_assessed"
    assert rep["final_answer"] == "" and rep["final_answer_chars"] == 0
    assert any("missing valid complete final answer" in m for m in error_messages(rep))
    return r


@case("missing_result_no_prior_empty_display_rejects")
def _(ctx):
    events = [init_event(), {"type": "result", "subtype": "success", "is_error": False,
                             "stop_reason": "end_turn", "terminal_reason": "completed"}]
    r = run(events, root=ctx["root"])
    rep = r["report"]
    assert r["returncode"] == 1 and rep["validation_status"] == "rejected"
    assert rep["final_answer"] == "" and rep["final_answer_chars"] == 0
    assert rep["agent_status"] == "failed"
    return r


@case("nested_text_never_supplies_root_display_blank")
def _(ctx):
    events = [init_event(),
              tool_call("parent"),
              assistant("child text", parent_tool_use_id="parent"),
              tool_result("parent"),
              claude_ok("")]
    r = run(events, root=ctx["root"])
    rep = r["report"]
    assert r["returncode"] == 1 and rep["validation_status"] == "rejected"
    assert rep["final_answer"] == "" and rep["final_answer_chars"] == 0
    assert rep["agent_status"] == "failed" and rep["terminal"] == "failed"
    return r


@case("nested_text_never_supplies_root_display_missing")
def _(ctx):
    events = [init_event(),
              tool_call("parent"),
              assistant("child text", parent_tool_use_id="parent"),
              tool_result("parent"),
              {"type": "result", "subtype": "success", "is_error": False,
               "stop_reason": "end_turn", "terminal_reason": "completed"}]
    r = run(events, root=ctx["root"])
    rep = r["report"]
    assert r["returncode"] == 1 and rep["validation_status"] == "rejected"
    assert rep["final_answer"] == "" and rep["final_answer_chars"] == 0
    return r


@case("native_negative_nonempty_result_displayed_yet_rejected")
def _(ctx):
    events = [init_event(), assistant("partial root"),
              result_event("authoritative", stop_reason="max_tokens", terminal_reason="completed")]
    r = run(events, root=ctx["root"])
    rep = r["report"]
    assert r["returncode"] == 1 and rep["validation_status"] == "rejected"
    assert rep["agent_status"] == "failed" and rep["terminal"] == "failed"
    assert rep["result_status"] == "not_assessed"
    assert rep["final_answer"] == "authoritative" and rep["final_answer_chars"] == 13
    msgs = error_messages(rep)
    assert any("invalid or unsuccessful result terminal" in m for m in msgs), msgs
    assert not any("missing valid complete final answer" in m for m in msgs), msgs
    return r


@case("normal_nonblank_claude_unchanged_passed")
def _(ctx):
    events = [init_event(), assistant("partial root"), claude_ok("authoritative final")]
    r = run(events, root=ctx["root"])
    rep = r["report"]
    assert r["returncode"] == 0 and rep["validation_status"] == "passed"
    assert rep["agent_status"] == "completed" and rep["terminal"] == "success"
    assert rep["final_answer"] == "authoritative final"
    assert rep["errors"] == [] and rep["result_status"] == "not_assessed"
    return r


@case("duplicate_result_first_terminal_final_retained")
def _(ctx):
    events = [init_event(), assistant("partial root"), claude_ok("done first"), claude_ok("")]
    r = run(events, root=ctx["root"])
    rep = r["report"]
    assert r["returncode"] == 1 and rep["validation_status"] == "rejected"
    assert rep["agent_status"] == "failed"
    assert rep["final_answer"] == "done first" and rep["final_answer_chars"] == 10
    msgs = error_messages(rep)
    assert any("multiple result terminals" in m for m in msgs), msgs
    assert any("event after runtime terminal" in m for m in msgs), msgs
    return r


@case("postterminal_trailing_assistant_cannot_change_final")
def _(ctx):
    events = [init_event(), claude_ok("done first"), assistant("late text")]
    r = run(events, root=ctx["root"])
    rep = r["report"]
    assert r["returncode"] == 1 and rep["validation_status"] == "rejected"
    assert rep["agent_status"] == "failed"
    assert rep["final_answer"] == "done first"
    assert any("event after runtime terminal" in m for m in error_messages(rep))
    return r


@case("blank_partial_wrong_canary_mismatch_at_retained_line")
def _(ctx):
    partial = "partial root\nCANARY=wrong-token"
    events = [init_event(), assistant(partial), claude_ok("")]
    r = run(events, "--canary-file", str(ctx["canary_file"]),
            "--canary-expected", str(ctx["canary_expected"]),
            "--artifact", str(ctx["root"] / "missing-artifact"),
            root=ctx["root"])
    rep = r["report"]
    assert r["returncode"] == 1 and rep["validation_status"] == "rejected"
    assert rep["final_answer"] == partial and rep["final_answer_chars"] == len(partial)
    assert rep["canary_status"] == "mismatch"
    canary = next(d for d in rep["errors"] if "canary proof does not match" in d["message"])
    assert canary["stream"] == "output" and canary["line"] == 2 and canary["proof_line"] == 2, canary
    assert any("required artifact missing" in m for m in error_messages(rep))
    assert any("missing valid complete final answer" in m for m in error_messages(rep))
    return r


@case("blank_partial_matching_canary_still_rejected")
def _(ctx):
    partial = "partial root\nCANARY=fresh-12345678"
    events = [init_event(), assistant(partial), claude_ok("")]
    r = run(events, "--canary-file", str(ctx["canary_file"]),
            "--canary-expected", str(ctx["canary_expected"]),
            root=ctx["root"])
    rep = r["report"]
    assert r["returncode"] == 1 and rep["validation_status"] == "rejected"
    assert rep["agent_status"] == "failed"
    assert rep["final_answer"] == partial
    assert rep["canary_status"] == "match"
    assert not any("canary proof does not match" in m for m in error_messages(rep))
    assert any("missing valid complete final answer" in m for m in error_messages(rep))
    return r


@case("codex_normal_stream_unchanged_passed")
def _(ctx):
    events = [{"type": "thread.started", "thread_id": "probe"},
              {"type": "turn.started"},
              {"type": "item.completed", "item": {"id": "m", "type": "agent_message", "text": "done"}},
              {"type": "turn.completed", "usage": {}}]
    r = run(events, runtime="codex", root=ctx["root"])
    rep = r["report"]
    assert r["returncode"] == 0 and rep["validation_status"] == "passed"
    assert rep["agent_status"] == "completed" and rep["final_answer"] == "done"
    assert rep["result_status"] == "not_assessed" and rep["errors"] == []
    return r


def main():
    collector_hash = sha256(COLLECTOR)
    results = {
        "probe": "aggregate-rereview-mimo-flash DS-A1 focused synthetic",
        "collector_path": str(COLLECTOR),
        "collector_sha256": collector_hash,
        "python": sys.version.split()[0],
        "cases": [],
        "totals": {"cases": 0, "passed": 0, "failed": 0, "assertions_failed": 0},
    }
    failures = []
    with tempfile.TemporaryDirectory(prefix="mimo-rereview-") as tmp:
        root = Path(tmp)
        canary_file = root / "proof.txt"
        canary_file.write_text("fresh-12345678", encoding="utf-8")
        canary_expected = root / "expected.txt"
        canary_expected.write_text("fresh-12345678", encoding="utf-8")
        ctx = {"root": root, "canary_file": canary_file, "canary_expected": canary_expected}
        for name, fn in CASES:
            results["totals"]["cases"] += 1
            started = time.time()
            try:
                r = fn(ctx)
                entry = {"name": name, "status": "pass",
                         "returncode": r["returncode"],
                         "validation_status": r["report"]["validation_status"],
                         "agent_status": r["report"]["agent_status"],
                         "result_status": r["report"]["result_status"],
                         "terminal": r["report"]["terminal"],
                         "final_answer": r["report"]["final_answer"],
                         "final_answer_chars": r["report"]["final_answer_chars"],
                         "canary_status": r["report"]["canary_status"],
                         "diagnostic_counts": r["report"]["diagnostic_counts"],
                         "error_messages": error_messages(r["report"]),
                         "wall_seconds": round(time.time() - started, 3)}
                results["totals"]["passed"] += 1
            except AssertionError as exc:
                entry = {"name": name, "status": "fail", "assertion": str(exc)}
                results["totals"]["failed"] += 1
                results["totals"]["assertions_failed"] += 1
                failures.append((name, str(exc)))
            results["cases"].append(entry)
    results["all_pass"] = results["totals"]["failed"] == 0
    out = HERE / "results.json"
    out.write_text(json.dumps(results, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"collector_sha256={collector_hash}")
    print(f"cases={results['totals']['cases']} passed={results['totals']['passed']} "
          f"failed={results['totals']['failed']}")
    for name, msg in failures:
        print(f"FAIL {name}: {msg}")
    return 0 if results["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
