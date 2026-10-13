#!/usr/bin/env python3
"""Internal runner result adapter. Logs remain the source for controller adjudication."""
import argparse
import json
import math
import re
import shlex
import sys
from pathlib import Path

DISPLAY_LIMIT = 12000
DIAGNOSTIC_LIMIT = 20


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


def finite_json_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("JSON number exceeds finite float range")
    return number


def validate_event_text(event):
    # JSON escapes can decode to lone surrogates, which cannot be UTF-8 output.
    pending = [event]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            pending.extend(value.keys())
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
        elif isinstance(value, str):
            value.encode("utf-8")


def reported_tokens(lines):
    """Only standalone proof lines outside fenced examples constitute reports."""
    fence = None
    html = None
    for number, raw in enumerate(lines, 1):
        if raw.startswith("    ") or raw.startswith("\t"):
            continue
        line = raw.strip()
        marker = re.match(r"^(`{3,}|~{3,})", line)
        if fence:
            if marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= fence[1] and not line[marker.end():].strip():
                fence = None
            continue
        if html:
            if re.search(r"</" + html + r"\s*>", line, re.I):
                html = None
            continue
        tag = re.match(r"<(pre|code)(?:\s|>)", line, re.I)
        if tag:
            name = tag.group(1).lower()
            if not re.search(r"</" + name + r"\s*>", line, re.I):
                html = name
            continue
        if marker:
            current = marker.group(1)
            fence = (current[0], len(current))
            continue
        if len(line) >= 2 and line[0] == line[-1] and line[0] in "`\"'":
            line = line[1:-1].strip()
        match = re.fullmatch(r"CANARY\s*[:=]\s*(.+)", line)
        if not match:
            continue
        token = match.group(1).strip().rstrip("。.,;；，")
        if len(token) >= 2 and token[0] == token[-1] and token[0] in "`\"'":
            token = token[1:-1]
        yield number, token


def contains_tool_syntax(text):
    if re.search(r'<tool_(?:call|result)>|"tool_calls"|"function_call"\s*:|'
                 r'"type"\s*:\s*"(?:tool_use|tool_call|tool_result|function_call)"|'
                 r'"name"\s*:\s*"[^"\n]+"\s*,\s*"(?:arguments|input)"\s*:', text):
        return True
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        stripped = "\n".join(stripped.splitlines()[1:-1])
    try:
        data = json.loads(stripped)
    except (ValueError, RecursionError):
        return False
    pending = [data]
    while pending:
        value = pending.pop()
        if isinstance(value, list):
            pending.extend(value)
        elif isinstance(value, dict):
            if isinstance(value.get("type"), str) and value["type"] in {"tool_use", "tool_call", "tool_result", "function_call"}:
                return True
            if any(key in value for key in ("tool_call", "tool_calls", "tool_use")):
                return True
            if "name" in value and ("arguments" in value or "input" in value):
                return True
            pending.extend(value.values())
    return False


def validate_canary_inputs(canary_file, expected_file):
    for value in (canary_file, expected_file):
        if not Path(value).is_file():
            raise ValueError(f"canary input is not a regular file: {value}")
    with Path(canary_file).open("rb") as stream:
        if not stream.read(1):
            raise ValueError(f"canary input is empty: {canary_file}")
    token = Path(expected_file).read_text(encoding="utf-8").strip()
    if not token or re.search(r"\s", token):
        raise ValueError("invalid canary expected token")


class Collection:
    def __init__(self, args):
        self.args = args
        self.errors, self.anomalies, self.warnings = [], [], []
        self.counts = dict(errors=0, anomalies=0, warnings=0)
        self.final = ""
        self.final_line = None
        self.terminal = None
        self.session_ids = set()
        self.usage = None
        self.runtime_metrics = {}
        self.events = self.tools = 0
        self.pending = {}
        self.read_visible = False
        self.token = ""
        self.canary_status = "not_run"
        self.artifacts = []
        self.stream = "collection"
        self.text_truncated = False
        # Adapter-local execution proof is independent of parser/check errors.
        self.execution_valid = True
        self.identity_valid = True
        self.final_valid = self.terminal_valid = False
        self.output_frames = 0
        self.thread_starts = self.turn_starts = 0
        self.thread_start_line = self.turn_start_line = None
        self.root_inits = 0
        self.root_work_seen = False
        self.claude_calls = set()

    def note(self, kind, message, line=None, path=None, proof_line=None):
        self.counts[kind] += 1
        target = getattr(self, kind)
        text = str(message)
        self.text_truncated |= len(text) > 2000
        if len(target) < DIAGNOSTIC_LIMIT:
            target.append({"stream": self.stream, "line": line, "message": text[:2000], "message_chars": len(text), "truncated": len(text) > 2000, "path": path, "proof_line": proof_line})

    def mentions_canary(self, value):
        if isinstance(value, dict):
            return any(self.mentions_canary(v) for v in value.values())
        if isinstance(value, list):
            return any(self.mentions_canary(v) for v in value)
        if not isinstance(value, str):
            return False
        if self.args.canary_file in value:
            return True
        try:
            return any(token.startswith("/") and Path(token).resolve() == Path(self.args.canary_file).resolve()
                       for token in shlex.split(value))
        except (ValueError, OSError):
            return False

    def tool(self, command, output):
        self.tools += 1
        # This locates candidate evidence, not a semantic proof that a command read a file.
        if self.token and self.mentions_canary(command) and self.token in str(output):
            self.read_visible = True

    def session_identity(self, value):
        if isinstance(value, str) and value.strip():
            self.session_ids.add(value)

    def proof_error(self, message, line):
        self.execution_valid = False
        self.note("errors", message, line)

    def terminal_metrics(self, event):
        # Streaming updates are not totals. Keep only one unambiguous terminal.
        if self.terminal == "conflicting":
            self.usage, self.runtime_metrics = None, {}
            return
        self.usage = event.get("usage") if isinstance(event.get("usage"), dict) else None
        if self.args.runtime == "claude":
            for key in ("duration_ms", "duration_api_ms", "total_cost_usd"):
                value = event.get(key)
                if type(value) in (int, float) and value >= 0 and (type(value) is int or math.isfinite(value)):
                    self.runtime_metrics[key] = value
            if isinstance(event.get("modelUsage"), dict):
                self.runtime_metrics["modelUsage"] = event["modelUsage"]

    def codex(self, event, line):
        kind = event.get("type")
        item = event.get("item")
        diagnostic = (kind == "error" or
                      (kind == "item.completed" and isinstance(item, dict)
                       and item.get("type") == "error"))
        if kind == "thread.started":
            self.thread_starts += 1
            identity = event.get("thread_id")
            valid = (set(event) == {"type", "thread_id"}
                     and isinstance(identity, str) and bool(identity.strip()))
            if not valid:
                self.identity_valid = False
            self.session_identity(identity)
            if self.thread_starts != 1 or self.output_frames != 1 or not valid:
                self.proof_error("invalid thread start identity, shape or order", line)
            self.thread_start_line = line
        elif kind == "turn.started":
            self.turn_starts += 1
            if (self.thread_starts != 1 or self.turn_starts != 1
                    or self.thread_start_line is None or set(event) != {"type"}):
                self.proof_error("invalid turn start shape or order", line)
            self.turn_start_line = line
        else:
            if self.thread_starts != 1 or (self.turn_starts != 1 and not diagnostic):
                self.proof_error("event outside started turn", line)
            if kind in {"turn.completed", "turn.failed"}:
                valid = (set(event) <= {"type", "usage"} if kind == "turn.completed" else
                         set(event) <= {"type", "error", "usage"}
                         and isinstance(event.get("error"), dict)
                         and isinstance(event["error"].get("message"), str))
                self.terminal_valid = valid and kind == "turn.completed"
                if self.terminal is not None:
                    self.proof_error("multiple turn terminals", line)
                    self.terminal = "conflicting"
                    self.terminal_valid = False
                else:
                    self.terminal = kind
                self.terminal_metrics(event)
                if not valid:
                    self.proof_error("invalid turn terminal shape", line)
                if kind == "turn.failed":
                    self.proof_error(event, line)
            elif kind == "error":
                if not isinstance(event.get("message"), str):
                    self.note("errors", "invalid error diagnostic message", line)
                else:
                    self.note("anomalies", event, line)
            elif kind in {"item.started", "item.completed", "item.updated"}:
                if not isinstance(item, dict):
                    self.note("errors", "invalid item", line)
                    return
                item_kind = item.get("type")
                if kind == "item.started" and item_kind in {"command_execution", "mcp_tool_call", "file_change"}:
                    self.pending[item.get("id", str(line))] = line
                if kind != "item.completed":
                    if item.get("status") in {"failed", "error"} or item.get("error"):
                        self.note("anomalies", item, line)
                    return
                if isinstance(item.get("id"), str):
                    self.pending.pop(item["id"], None)
                if item_kind == "agent_message":
                    identity = item.get("id")
                    self.final_valid = (set(event) == {"type", "item"}
                                        and set(item) == {"id", "type", "text"}
                                        and isinstance(identity, str) and bool(identity.strip())
                                        and isinstance(item.get("text"), str)
                                        and bool(item["text"].strip()))
                    if isinstance(item.get("text"), str):
                        self.final = item["text"]
                        self.final_line = line
                    if not self.final_valid:
                        self.proof_error("invalid or empty completed agent message", line)
                elif item_kind in {"command_execution", "mcp_tool_call", "file_change"}:
                    self.tool(item.get("command", item.get("arguments", "")), item.get("aggregated_output", item.get("result", "")))
                    if item.get("status") == "failed" or item.get("error") or item.get("exit_code") not in (None, 0):
                        self.note("anomalies", item, line)
                elif item_kind == "error":
                    identity = item.get("id")
                    if (not isinstance(identity, str) or not identity.strip()
                            or not isinstance(item.get("message"), str)):
                        self.note("errors", "invalid error item diagnostic", line)
                    else:
                        self.note("anomalies", event, line)
                elif item.get("status") in {"failed", "error"} or item.get("error"):
                    self.note("anomalies", item, line)
            elif isinstance(kind, str) and kind.endswith(".failed"):
                self.note("anomalies", event, line)

    def claude_result_valid(self, event):
        # Only the authoritative result carries execution completion metadata.
        if (event.get("subtype") != "success" or event.get("is_error") is not False
                or not isinstance(event.get("result"), str) or not event["result"].strip()):
            return False
        if "stop_reason" in event and event["stop_reason"] is not None:
            if event["stop_reason"] not in ("end_turn", "stop_sequence"):
                return False
        if "terminal_reason" in event and event["terminal_reason"] != "completed":
            return False
        if "api_error_status" in event and event["api_error_status"] is not None:
            return False
        if "errors" in event and (not isinstance(event["errors"], list) or event["errors"]):
            return False
        return "deferred_tool_use" not in event

    def claude(self, event, line):
        kind = event.get("type")
        if kind == "result" and self.terminal is not None:
            self.proof_error("multiple result terminals", line)
            self.terminal = "conflicting"
            self.terminal_valid = False
            self.terminal_metrics(event)
            return  # Preserve the first terminal's final and execution identity.
        parent = event.get("parent_tool_use_id")
        parent_valid = parent is None or (isinstance(parent, str) and bool(parent.strip()))
        if not parent_valid:
            self.proof_error("invalid parent tool identity", line)
            return
        root = parent is None
        if "session_id" in event:
            identity = event["session_id"]
            if not isinstance(identity, str) or not identity.strip():
                if root:
                    self.identity_valid = False
                self.proof_error("invalid runtime session identifier", line)
            elif root:
                self.session_identity(identity)
        if not root and not any(
                identity == parent for _, identity in self.claude_calls):
            self.proof_error("nested frame without recorded parent call", line)
        if kind == "result":
            # Parented results are unsupported, never substitute for a root result.
            valid = root and self.claude_result_valid(event)
            self.terminal_valid = valid
            self.terminal = "success" if valid else "failed"
            self.terminal_metrics(event)
            self.final_valid = root and isinstance(event.get("result"), str) and bool(event["result"].strip())
            if self.final_valid:
                self.final = event["result"]
                self.final_line = line
            if not valid:
                self.proof_error("invalid or unsuccessful result terminal: " + str(event), line)
        elif kind == "system" and event.get("subtype") == "init":
            if root:
                self.root_inits += 1
                if self.root_inits != 1 or self.root_work_seen:
                    self.proof_error("duplicate or late root init", line)
        elif kind in {"assistant", "user"}:
            if root:
                self.root_work_seen = True
            message = event.get("message")
            if not isinstance(message, dict) or not isinstance(message.get("content"), list):
                self.note("errors", "invalid message content", line)
                return
            if kind == "assistant" and "error" in event:
                self.note("anomalies", event, line)
            text = []
            for block in message["content"]:
                if not isinstance(block, dict) or not isinstance(block.get("type"), str):
                    self.note("errors", "invalid content block", line)
                elif block.get("type") == "text":
                    if not isinstance(block.get("text"), str):
                        self.note("errors", "invalid text block", line)
                    else:
                        text.append(block["text"])
                elif block.get("type") == "tool_use":
                    identity = block.get("id")
                    name = block.get("name")
                    if (not isinstance(identity, str) or not identity.strip()
                            or not isinstance(name, str) or not name.strip()
                            or not isinstance(block.get("input"), dict)):
                        self.note("errors", "invalid tool call", line)
                        continue
                    key = (parent, identity)
                    if key in self.claude_calls:
                        self.note("errors", "duplicate tool identity in parent scope", line)
                    else:
                        self.claude_calls.add(key)
                        self.pending[key] = block["input"]
                elif block.get("type") == "tool_result":
                    identity = block.get("tool_use_id")
                    if (not isinstance(identity, str) or not identity.strip()
                            or ("is_error" in block and type(block["is_error"]) is not bool)):
                        self.note("errors", "invalid tool result identity or error flag", line)
                        continue
                    key = (parent, identity)
                    command = self.pending.pop(key, None)
                    if command is None:
                        self.note("errors", "tool result without matching call in parent scope", line)
                    self.tool(command, block.get("content", ""))
                    if block.get("is_error") is True:
                        self.note("anomalies", block, line)
            joined = "".join(text)
            if kind == "assistant" and root and joined:
                self.final = joined
                self.final_line = line
        elif kind == "error" or (kind == "system" and event.get("subtype") == "api_retry"):
            self.note("anomalies", event, line)

    def collect(self):
        a = self.args
        if a.canary_expected:
            try:
                self.token = Path(a.canary_expected).read_text().strip()
                if not self.token or re.search(r"\s", self.token):
                    raise ValueError("invalid canary expected token")
            except (OSError, ValueError, UnicodeError) as exc:
                self.note("errors", exc)
                self.canary_status = "unknown"
        self.stream = "output"
        try:
            with open(a.output, encoding="utf-8") as stream:
                for line, raw in enumerate(stream, 1):
                    if not raw.strip():
                        continue
                    self.output_frames += 1
                    try:
                        event = json.loads(raw, object_pairs_hook=strict_object, parse_constant=invalid_constant, parse_float=finite_json_float)
                        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
                            raise ValueError("expected an event object with type")
                        validate_event_text(event)
                        self.events += 1
                        if self.terminal is not None:
                            if event["type"] == "rate_limit_event":
                                continue  # Trailing metadata cannot supply proof, identity or totals.
                            self.proof_error("event after runtime terminal", line)
                            if event["type"] not in {"turn.completed", "turn.failed", "result"}:
                                continue
                        (self.codex if a.runtime == "codex" else self.claude)(event, line)
                    except (ValueError, TypeError, AttributeError, RecursionError) as exc:
                        self.note("errors", f"invalid event: {exc}", line)
        except (OSError, UnicodeError) as exc:
            self.note("errors", exc)
        if self.terminal not in {"turn.completed", "success"}:
            self.note("errors", "missing successful runtime terminal")
        if not self.final_valid:
            self.note("errors", "missing valid complete final answer")
        if a.runtime == "codex" and (self.thread_starts != 1 or self.turn_starts != 1):
            self.proof_error("missing unique execution starts", None)
        if self.pending:
            self.note("anomalies", f"{len(self.pending)} tool calls without completion")
        if a.last_message:
            try:
                saved = Path(a.last_message).read_text()
                if saved.strip() != self.final.strip():
                    self.note("errors", "last-message differs from event final answer")
            except (OSError, UnicodeError) as exc:
                self.note("errors", exc)
        proof_count = mismatches = 0
        def check_proofs(lines, source, path, event_line=None):
            nonlocal proof_count, mismatches
            for proof_line, value in reported_tokens(lines):
                proof_count += 1
                if self.token and value != self.token:
                    mismatches += 1
                    self.stream = source
                    self.note("errors", "canary proof does not match expected token",
                              line=event_line if source == "output" else proof_line,
                              path=str(path), proof_line=proof_line)
        check_proofs(self.final.splitlines(), "output", a.output, self.final_line)
        self.stream = "artifact"
        for path in a.artifact:
            target = Path(path)
            exists = target.exists()
            regular = target.is_file() and not target.is_symlink()
            self.artifacts.append({"path": str(target.absolute()), "exists": exists, "regular_file": regular})
            if not exists:
                self.note("errors", f"required artifact missing: {target}")
            elif not regular:
                self.note("errors", f"required artifact is not a regular file: {target}")
            else:
                try:
                    logs = (a.output, a.stderr, a.last_message)
                    if target.stat().st_nlink != 1 or any(
                            value and Path(value).exists() and target.samefile(value) for value in logs):
                        self.note("errors", f"required artifact is hard-linked or aliases a runner log: {target}")
                        continue
                    with target.open(encoding="utf-8") as stream:
                        check_proofs(stream, "artifact", target)
                except UnicodeError:
                    pass  # Binary artifacts still undergo existence checks.
                except OSError as exc:
                    self.note("errors", exc)
        if self.token:
            self.canary_status = "match" if proof_count and not mismatches else "mismatch"
            self.stream = "collection"
            if not proof_count:
                self.note("errors", "missing standalone canary report")
            if not self.read_visible:
                self.note("anomalies", "canary read evidence not visible; inspect logs and required evidence")
        if self.tools == 0:
            if self.token:
                self.note("anomalies", "no tool results visible; required evidence needs independent verification")
            if contains_tool_syntax(self.final):
                self.stream = "output"
                self.note("anomalies", "tool-like text without recorded tool results; verify task intent and execution",
                          line=self.final_line, path=a.output)
        self.stream = "stderr"
        try:
            with open(a.stderr, encoding="utf-8") as stream:
                for line, raw in enumerate(stream, 1):
                    if raw.strip():
                        benign = a.runtime == "claude" and raw.startswith("[claude-code:unrecognized_model]")
                        self.note("warnings" if benign else "anomalies", raw.strip(), line)
        except (OSError, UnicodeError) as exc:
            self.note("errors", exc)
        if a.exit_code != 0:
            self.note("errors", f"runtime process exited {a.exit_code}")
        if a.runner_exit_code != 0 and a.runner_exit_code != a.exit_code:
            self.note("errors", f"runner postprocessing failed: {a.runner_exit_code}")
        if len(self.session_ids) > 1:
            self.stream = "output"
            self.identity_valid = False
            self.proof_error("conflicting runtime session identifiers; session_id unavailable", None)
        validation = "rejected" if self.counts["errors"] else "needs_review" if self.counts["anomalies"] else "passed"
        completed = (a.exit_code == 0 and a.runner_exit_code == 0 and self.execution_valid
                     and self.identity_valid and self.terminal_valid and self.final_valid)
        return dict(schema_version=1, source="subagent_report", runtime=a.runtime, provider=a.provider,
                    runtime_exit_code=a.exit_code, runner_exit_code=a.runner_exit_code or (1 if validation == "rejected" else 0),
                    agent_status="completed" if completed else "failed",
                    validation_status=validation, result_status="not_assessed", final_answer=self.final[:DISPLAY_LIMIT],
                    final_answer_truncated=len(self.final) > DISPLAY_LIMIT, final_answer_chars=len(self.final),
                    wall_clock_seconds=elapsed_seconds(a.wall_clock_seconds), usage=self.usage, runtime_metrics=self.runtime_metrics,
                    session_id=next(iter(self.session_ids)) if self.identity_valid and len(self.session_ids) == 1 else None,
                    terminal=self.terminal, tool_evidence_scope="recorded_events_only", tool_results=self.tools, events=self.events,
                    canary_status=self.canary_status, canary_read_candidate=self.read_visible,
                    errors=self.errors, anomalies=self.anomalies, warnings=self.warnings,
                    diagnostic_counts=self.counts, diagnostics_truncated=self.text_truncated or any(v > DIAGNOSTIC_LIMIT for v in self.counts.values()),
                    artifacts=self.artifacts, logs=dict(output=a.output, stderr=a.stderr, last_message=a.last_message))


def elapsed_seconds(value):
    try:
        seconds = float(value)
        return seconds if math.isfinite(seconds) and seconds >= 0 else None
    except (ValueError, TypeError, OverflowError):
        return None


def main():
    if sys.argv[1:2] == ["--validate-canary-inputs"]:
        check = argparse.ArgumentParser(description="Internal canary setup validation")
        check.add_argument("--validate-canary-inputs", action="store_true")
        check.add_argument("--canary-file", required=True)
        check.add_argument("--canary-expected", required=True)
        args = check.parse_args()
        try:
            validate_canary_inputs(args.canary_file, args.canary_expected)
        except (OSError, ValueError, UnicodeError) as exc:
            check.error(str(exc))
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", required=True, choices=("codex", "claude"))
    parser.add_argument("--provider", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--stderr", required=True)
    parser.add_argument("--exit-code", required=True, type=int)
    parser.add_argument("--runner-exit-code", required=True, type=int)
    parser.add_argument("--wall-clock-seconds")
    parser.add_argument("--last-message")
    parser.add_argument("--canary-file")
    parser.add_argument("--canary-expected")
    parser.add_argument("--artifact", action="append", default=[])
    args = parser.parse_args()
    if bool(args.canary_file) != bool(args.canary_expected):
        parser.error("canary-file and canary-expected must be supplied together")
    report = Collection(args).collect()
    print(json.dumps(report, ensure_ascii=False, allow_nan=False))
    return 1 if report["validation_status"] == "rejected" else 0


if __name__ == "__main__":
    raise SystemExit(main())
