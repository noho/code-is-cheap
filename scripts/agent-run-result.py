#!/usr/bin/env python3
"""Internal runner result adapter. Logs remain the source for controller adjudication."""
import argparse
import json
import re
import shlex
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


def reported_tokens(lines):
    """Only standalone proof lines outside fenced examples constitute reports."""
    fence = None
    for raw in lines:
        line = raw.strip()
        marker = re.match(r"^(`{3,}|~{3,})", line)
        if marker:
            current = marker.group(1)
            if fence is None:
                fence = current[0]
            elif fence == current[0]:
                fence = None
            continue
        if fence:
            continue
        if len(line) >= 2 and line[0] == line[-1] and line[0] in "`\"'":
            line = line[1:-1].strip()
        match = re.fullmatch(r"CANARY\s*[:=]\s*(.+)", line)
        if not match:
            continue
        token = match.group(1).strip().rstrip("。.,;；，")
        if len(token) >= 2 and token[0] == token[-1] and token[0] in "`\"'":
            token = token[1:-1]
        yield token


def literal_tool_claim(text):
    if re.search(r"<tool_(?:call|result)>|\"tool_calls\"", text):
        return True
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        stripped = "\n".join(stripped.splitlines()[1:-1])
    try:
        data = json.loads(stripped)
    except ValueError:
        return False
    def contains(value):
        if isinstance(value, list):
            return any(contains(v) for v in value)
        if not isinstance(value, dict):
            return False
        if value.get("type") in {"tool_use", "tool_call", "tool_result", "function_call"}:
            return True
        if any(key in value for key in ("tool_call", "tool_calls", "tool_use")):
            return True
        if "name" in value and ("arguments" in value or "input" in value):
            return True
        return any(contains(v) for v in value.values())
    return contains(data)


class Collection:
    def __init__(self, args):
        self.args = args
        self.errors, self.anomalies, self.warnings = [], [], []
        self.counts = dict(errors=0, anomalies=0, warnings=0)
        self.final = ""
        self.terminal = None
        self.events = self.tools = 0
        self.pending = {}
        self.read_visible = False
        self.token = ""
        self.canary_status = "not_run"
        self.artifacts = []
        self.stream = "collection"
        self.text_truncated = False

    def note(self, kind, message, line=None):
        self.counts[kind] += 1
        target = getattr(self, kind)
        text = str(message)
        self.text_truncated |= len(text) > 2000
        if len(target) < DIAGNOSTIC_LIMIT:
            target.append({"stream": self.stream, "line": line, "message": text[:2000], "message_chars": len(text), "truncated": len(text) > 2000})

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

    def codex(self, event, line):
        kind = event.get("type")
        if kind in {"turn.completed", "turn.failed"}:
            if self.terminal is not None:
                self.note("errors", "multiple turn terminals", line)
                self.terminal = "conflicting"
            else:
                self.terminal = kind
            if kind == "turn.failed":
                self.note("errors", event, line)
        elif kind == "error":
            self.note("errors", event, line)
        elif kind in {"item.started", "item.completed", "item.updated"}:
            item = event.get("item")
            if not isinstance(item, dict):
                self.note("errors", "invalid item", line)
                return
            item_kind = item.get("type")
            if kind == "item.started" and item_kind in {"command_execution", "mcp_tool_call", "file_change"}:
                self.pending[item.get("id", str(line))] = line
            if kind != "item.completed":
                return
            self.pending.pop(item.get("id"), None)
            if item_kind == "agent_message":
                if not isinstance(item.get("text"), str):
                    self.note("errors", "invalid agent message", line)
                else:
                    self.final = item["text"]
            elif item_kind in {"command_execution", "mcp_tool_call", "file_change"}:
                self.tool(item.get("command", item.get("arguments", "")), item.get("aggregated_output", item.get("result", "")))
                if item.get("status") == "failed" or item.get("error") or item.get("exit_code") not in (None, 0):
                    self.note("anomalies", item, line)
            elif item_kind == "error":
                message = item.get("message", "")
                benign = isinstance(message, str) and (re.match(r"^Model metadata for \S+ not found", message) or "unrecognized_model" in message)
                self.note("warnings" if benign else "anomalies", item, line)
            elif item.get("status") in {"failed", "error"} or item.get("error"):
                self.note("anomalies", item, line)
        elif isinstance(kind, str) and kind.endswith(".failed"):
            self.note("anomalies", event, line)

    def claude(self, event, line):
        kind = event.get("type")
        if kind == "result":
            if self.terminal is not None:
                self.note("errors", "multiple result terminals", line)
                self.terminal = "conflicting"
            else:
                self.terminal = "success" if event.get("subtype") == "success" and event.get("is_error") is False else "failed"
            if self.terminal != "success":
                self.note("errors", event, line)
            if isinstance(event.get("result"), str):
                self.final = event["result"]
            else:
                self.note("errors", "missing text result", line)
        elif kind in {"assistant", "user"}:
            message = event.get("message", {})
            if not isinstance(message, dict) or not isinstance(message.get("content"), list):
                self.note("errors", "invalid message content", line)
                return
            if kind == "assistant":
                text = "".join(b.get("text", "") for b in message["content"]
                               if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str))
                if text:
                    self.final = text
            for block in message["content"]:
                if not isinstance(block, dict):
                    self.note("errors", "invalid content block", line)
                elif block.get("type") == "tool_use":
                    identity = block.get("id")
                    if not isinstance(identity, str) or identity in self.pending:
                        self.note("errors", "invalid or duplicate tool identity", line)
                    else:
                        self.pending[identity] = block.get("input", {})
                elif block.get("type") == "tool_result":
                    identity = block.get("tool_use_id")
                    command = self.pending.pop(identity, None)
                    if command is None:
                        self.note("errors", "tool result without matching call", line)
                    self.tool(command, block.get("content", ""))
                    if block.get("is_error") is True:
                        self.note("anomalies", block, line)
        elif kind == "error":
            self.note("errors", event, line)

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
                    try:
                        event = json.loads(raw, object_pairs_hook=strict_object, parse_constant=invalid_constant)
                        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
                            raise ValueError("expected an event object with type")
                        if self.terminal is not None and event["type"] not in {"rate_limit_event"}:
                            self.note("errors", "event after runtime terminal", line)
                        self.events += 1
                        (self.codex if a.runtime == "codex" else self.claude)(event, line)
                    except (ValueError, TypeError, AttributeError) as exc:
                        self.note("errors", f"invalid event: {exc}", line)
        except (OSError, UnicodeError) as exc:
            self.note("errors", exc)
        if self.terminal not in {"turn.completed", "success"}:
            self.note("errors", "missing successful runtime terminal")
        if not self.final.strip():
            self.note("errors", "missing final answer")
        if self.pending:
            self.note("anomalies", f"{len(self.pending)} tool calls without completion")
        if a.last_message:
            try:
                saved = Path(a.last_message).read_text()
                if saved.strip() != self.final.strip():
                    self.note("errors", "last-message differs from event final answer")
            except (OSError, UnicodeError) as exc:
                self.note("errors", exc)
        reported = list(reported_tokens(self.final.splitlines()))
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
                    with target.open(encoding="utf-8") as stream:
                        reported.extend(reported_tokens(stream))
                except UnicodeError:
                    pass  # Binary artifacts still undergo existence checks.
                except OSError as exc:
                    self.note("errors", exc)
        if self.token:
            self.canary_status = "match" if reported and all(value == self.token for value in reported) else "mismatch"
            if self.canary_status != "match":
                self.note("errors", "missing or mismatched canary report")
            if not self.read_visible:
                self.note("anomalies", "canary read evidence not visible; inspect logs and required evidence")
        if self.tools == 0:
            if self.token:
                self.note("anomalies", "no tool results visible; required evidence needs independent verification")
            if literal_tool_claim(self.final):
                self.note("errors", "literal tool syntax without tool execution evidence")
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
        validation = "rejected" if self.counts["errors"] else "needs_review" if self.counts["anomalies"] else "passed"
        return dict(schema_version=1, source="subagent_report", runtime=a.runtime, provider=a.provider,
                    runtime_exit_code=a.exit_code, runner_exit_code=a.runner_exit_code or (1 if validation == "rejected" else 0),
                    agent_status="completed" if a.runner_exit_code == 0 and self.terminal in {"success", "turn.completed"} else "failed",
                    validation_status=validation, result_status="not_assessed", final_answer=self.final[:DISPLAY_LIMIT],
                    final_answer_truncated=len(self.final) > DISPLAY_LIMIT, final_answer_chars=len(self.final),
                    terminal=self.terminal, tool_evidence_scope="recorded_events_only", tool_results=self.tools, events=self.events,
                    canary_status=self.canary_status, canary_read_candidate=self.read_visible,
                    errors=self.errors, anomalies=self.anomalies, warnings=self.warnings,
                    diagnostic_counts=self.counts, diagnostics_truncated=self.text_truncated or any(v > DIAGNOSTIC_LIMIT for v in self.counts.values()),
                    artifacts=self.artifacts, logs=dict(output=a.output, stderr=a.stderr, last_message=a.last_message))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", required=True, choices=("codex", "claude"))
    parser.add_argument("--provider", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--stderr", required=True)
    parser.add_argument("--exit-code", required=True, type=int)
    parser.add_argument("--runner-exit-code", required=True, type=int)
    parser.add_argument("--last-message")
    parser.add_argument("--canary-file")
    parser.add_argument("--canary-expected")
    parser.add_argument("--artifact", action="append", default=[])
    args = parser.parse_args()
    if bool(args.canary_file) != bool(args.canary_expected):
        parser.error("canary-file and canary-expected must be supplied together")
    report = Collection(args).collect()
    print(json.dumps(report, ensure_ascii=False))
    return 1 if report["validation_status"] == "rejected" else 0


if __name__ == "__main__":
    raise SystemExit(main())
