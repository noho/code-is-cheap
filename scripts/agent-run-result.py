#!/usr/bin/env python3
"""Internal runner result adapter. Logs remain the source for controller adjudication."""
import argparse
import json
import math
import re
import shlex
import sys
from pathlib import Path

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
        self.diagnostics = []
        self.final = None
        self.final_line = None
        self.terminals = []
        self.session_ids = {}
        self.invalid_identity = False
        self.starts = {"thread.started": 0, "turn.started": 0}
        self.pending = {}
        self.read_visible = False
        self.token = None
        self.artifacts = []

    def note(self, message, line=None, path=None):
        self.diagnostics.append({"message": str(message), "path": path, "line": line})

    def native_diagnostic(self, value, line):
        # Free text is opaque. Never recognize, classify, trim or rewrite it.
        if isinstance(value, str):
            self.note(value, line, self.args.output)
        elif isinstance(value, list):
            for part in value:
                self.native_diagnostic(part, line)
        elif isinstance(value, dict) and "message" in value:
            self.native_diagnostic(value["message"], line)
        elif value is not None:
            self.note(json.dumps(value, ensure_ascii=False), line, self.args.output)

    def event_diagnostics(self, event, line):
        for key in ("message", "error", "errors", "warning", "warnings"):
            if key in event:
                self.native_diagnostic(event[key], line)

    def identity(self, event, key, line):
        if key not in event:
            return
        value = event[key]
        if isinstance(value, str) and value.strip():
            self.session_ids[value] = line
        else:
            self.invalid_identity = True
            self.note("invalid runtime session identifier", line, self.args.output)

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
        # Candidate evidence only; this does not prove a read or task correctness.
        if self.token and self.mentions_canary(command) and self.token in str(output):
            self.read_visible = True

    def set_final(self, value, line):
        self.final = value if isinstance(value, str) else None
        self.final_line = line
        if self.final is None:
            self.note("native final is missing or nontext", line, self.args.output)
        elif not self.final.strip():
            self.note("native final is empty or whitespace-only", line, self.args.output)

    def codex(self, event, line):
        kind, item = event["type"], event.get("item")
        if kind in self.starts:
            self.starts[kind] += 1
            if self.starts[kind] > 1:
                self.note("multiple " + kind + " events", line, self.args.output)
            if kind == "thread.started":
                self.identity(event, "thread_id", line)
            elif not self.starts["thread.started"]:
                self.note("turn start precedes thread start", line, self.args.output)
        elif kind in {"turn.completed", "turn.failed"}:
            self.terminals.append((event, line))
            if kind == "turn.failed":
                self.note("native turn.failed event", line, self.args.output)
            self.event_diagnostics(event, line)
        elif kind in {"error", "warning"}:
            self.event_diagnostics(event, line)
            if "message" not in event:
                self.note(kind + " event has no message", line, self.args.output)
        elif kind in {"item.started", "item.completed", "item.updated"}:
            if not isinstance(item, dict):
                self.note("invalid item", line, self.args.output)
                return
            item_kind, identity = item.get("type"), item.get("id")
            if kind == "item.started" and item_kind in {"command_execution", "mcp_tool_call", "file_change"}:
                self.pending[identity if isinstance(identity, str) else str(line)] = (None, line)
            if kind == "item.completed":
                if isinstance(identity, str):
                    self.pending.pop(identity, None)
                if item_kind == "agent_message":
                    self.set_final(item.get("text"), line)
                elif item_kind in {"command_execution", "mcp_tool_call", "file_change"}:
                    self.tool(item.get("command", item.get("arguments", "")), item.get("aggregated_output", item.get("result", "")))
            if item_kind == "error":
                self.event_diagnostics(item, line)
                if "message" not in item:
                    self.note("error item has no message", line, self.args.output)
            elif item.get("status") in {"failed", "error"} or item.get("exit_code") not in (None, 0) or item.get("error"):
                self.note(f"native item {item_kind!r}: status={item.get('status')!r}, exit_code={item.get('exit_code')!r}", line, self.args.output)
                if "error" in item:
                    self.native_diagnostic(item["error"], line)
        elif kind.endswith(".failed"):
            self.note("native event " + kind, line, self.args.output)
            self.event_diagnostics(event, line)

    def claude(self, event, line):
        kind = event["type"]
        parent = event.get("parent_tool_use_id")
        if parent is not None and (not isinstance(parent, str) or not parent.strip()):
            self.note("invalid parent tool identity", line, self.args.output)
            return
        root = parent is None
        if root:
            self.identity(event, "session_id", line)
        if kind == "result":
            if root:
                self.terminals.append((event, line))
                self.set_final(event.get("result"), line)
                # Metadata is an observation, never a prerequisite for final text.
                for key, normal in (("is_error", (False,)), ("subtype", ("success",)),
                                    ("stop_reason", (None, "end_turn", "stop_sequence")),
                                    ("terminal_reason", ("completed",)), ("api_error_status", (None,))):
                    if key in event and (event[key] not in normal or
                                         (key == "is_error" and type(event[key]) is not bool)):
                        self.note(f"native result {key}={event[key]!r}", line, self.args.output)
                if "deferred_tool_use" in event:
                    self.note("native result contains deferred_tool_use", line, self.args.output)
                self.event_diagnostics(event, line)
            else:
                self.note("nested result is not a root final", line, self.args.output)
        elif kind in {"assistant", "user"}:
            if "error" in event:
                self.native_diagnostic(event["error"], line)
            message = event.get("message")
            if not isinstance(message, dict) or not isinstance(message.get("content"), list):
                self.note("invalid message content", line, self.args.output)
                return
            for block in message["content"]:
                if not isinstance(block, dict):
                    self.note("invalid content block", line, self.args.output)
                    continue
                if block.get("type") == "tool_use":
                    identity = block.get("id")
                    if not isinstance(identity, str) or not identity.strip():
                        self.note("invalid tool call identity", line, self.args.output)
                        continue
                    key = (parent, identity)
                    if key in self.pending:
                        self.note("duplicate tool identity in parent scope", line, self.args.output)
                    self.pending[key] = (block.get("input"), line)
                elif block.get("type") == "tool_result":
                    identity = block.get("tool_use_id")
                    if not isinstance(identity, str) or not identity.strip():
                        self.note("invalid tool result identity", line, self.args.output)
                        continue
                    key = (parent, identity)
                    if key not in self.pending:
                        self.note("tool result without matching call in parent scope", line, self.args.output)
                    command, _ = self.pending.pop(key, (None, None))
                    self.tool(command, block.get("content", ""))
                    if block.get("is_error") is True:
                        self.note(f"native tool result is_error=true (tool_use_id={identity!r})", line, self.args.output)
        elif kind in {"error", "warning"} or (kind == "system" and event.get("subtype") in {"api_retry", "warning"}):
            self.event_diagnostics(event, line)

    def read_events(self):
        try:
            with open(self.args.output, "rb") as stream:
                for line, raw in enumerate(stream, 1):
                    if not raw.strip():
                        continue
                    try:
                        event = json.loads(raw.decode("utf-8"), object_pairs_hook=strict_object,
                                           parse_constant=invalid_constant, parse_float=finite_json_float)
                        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
                            raise ValueError("expected an event object with type")
                        validate_event_text(event)
                        (self.codex if self.args.runtime == "codex" else self.claude)(event, line)
                    except (ValueError, UnicodeError, TypeError, AttributeError, RecursionError) as exc:
                        self.note(f"invalid event: {exc}", line, self.args.output)
        except OSError as exc:
            self.note(exc, path=self.args.output)

    def collect(self):
        a = self.args
        if a.canary_expected:
            try:
                self.token = Path(a.canary_expected).read_text(encoding="utf-8").strip()
                if not self.token or re.search(r"\s", self.token):
                    self.token = None
                    raise ValueError("invalid canary expected token")
            except (OSError, ValueError, UnicodeError) as exc:
                self.note(exc, path=a.canary_expected)
        self.read_events()
        if len(self.terminals) != 1:
            self.note("missing runtime terminal" if not self.terminals else "multiple runtime terminals",
                      self.terminals[-1][1] if self.terminals else None, a.output)
            if a.runtime == "claude":
                self.final, self.final_line = None, None
        if self.final_line is None:
            self.note("native final unavailable", path=a.output)
        if a.runtime == "codex":
            for kind, count in self.starts.items():
                if not count:
                    self.note("missing " + kind + " event", path=a.output)
        for _, line in self.pending.values():
            self.note("tool call without completion", line, a.output)
        if a.last_message:
            try:
                with open(a.last_message, encoding="utf-8", newline="") as stream:
                    saved = stream.read()
                if saved != self.final:
                    self.note("last-message differs from event final answer", path=a.last_message)
            except (OSError, UnicodeError) as exc:
                self.note(exc, path=a.last_message)
        proofs = []

        def check_proofs(lines, path, event_line=None):
            for proof_line, value in reported_tokens(lines):
                proofs.append(value)
                if self.token and value != self.token:
                    self.note(f"canary proof does not match expected token (proof line {proof_line})",
                              event_line if event_line is not None else proof_line, str(path))

        if a.canary_file:
            check_proofs((self.final or "").splitlines(), a.output, self.final_line)
        for path in a.artifact:
            target = Path(path)
            try:
                exists = target.exists()
                regular = target.is_file() and not target.is_symlink()
                self.artifacts.append({"path": str(target.absolute()), "exists": exists, "regular_file": regular})
                if not exists:
                    self.note("artifact missing", path=path)
                elif not regular:
                    self.note("artifact is not a regular file", path=path)
                elif target.stat().st_nlink != 1 or any(
                        value and Path(value).exists() and target.samefile(value)
                        for value in (a.output, a.stderr, a.last_message)):
                    self.note("artifact is hard-linked or aliases a runner log", path=path)
                elif a.canary_file:
                    try:
                        with target.open(encoding="utf-8") as stream:
                            check_proofs(stream, target)
                    except UnicodeError as exc:
                        self.note(f"artifact is not UTF-8 text; canary proof not inspected: {exc}", path=path)
            except OSError as exc:
                self.note(exc, path=path)
        canary = None
        if a.canary_file:
            canary = dict(proof_observed=bool(proofs),
                          proof_matches_expected=all(value == self.token for value in proofs) if proofs and self.token else None,
                          read_candidate_observed=self.read_visible)
            if not proofs:
                self.note("no standalone canary proof observed", path=a.output)
            if not self.read_visible:
                self.note("canary read candidate not observed", path=a.output)
        try:
            with open(a.stderr, "rb") as stream:
                for line, raw in enumerate(stream, 1):
                    try:
                        # Include exact whitespace/newlines, including empty warning text.
                        self.note(raw.decode("utf-8"), line, a.stderr)
                    except UnicodeError as exc:
                        self.note(exc, line, a.stderr)
        except OSError as exc:
            self.note(exc, path=a.stderr)
        if len(self.session_ids) > 1:
            self.note("conflicting runtime session identifiers", max(self.session_ids.values()), a.output)
        session = next(iter(self.session_ids)) if not self.invalid_identity and len(self.session_ids) == 1 else None
        if session is None and len(self.session_ids) <= 1 and not self.invalid_identity:
            self.note("runtime session identifier unavailable", path=a.output)
        terminal, usage, metrics = None, None, {}
        if len(self.terminals) == 1:
            event, _ = self.terminals[0]
            terminal = event["type"] if a.runtime == "codex" else event.get("subtype")
            if not isinstance(terminal, str):
                terminal = None
                self.note("native terminal subtype unavailable", self.terminals[0][1], a.output)
            usage = event.get("usage") if isinstance(event.get("usage"), dict) else None
            if a.runtime == "claude":
                for key in ("duration_ms", "duration_api_ms", "total_cost_usd"):
                    value = event.get(key)
                    if type(value) in (int, float) and value >= 0 and (type(value) is int or math.isfinite(value)):
                        metrics[key] = value
                if isinstance(event.get("modelUsage"), dict):
                    metrics["modelUsage"] = event["modelUsage"]
        return dict(schema_version=2, source="subagent_report", runtime=a.runtime, provider=a.provider,
                    runtime_exit_code=a.exit_code, final_answer=self.final,
                    session_id=session, terminal=terminal,
                    wall_clock_seconds=elapsed_seconds(a.wall_clock_seconds), usage=usage, runtime_metrics=metrics,
                    logs=dict(output=a.output, stderr=a.stderr, last_message=a.last_message),
                    diagnostics=self.diagnostics, checks=dict(artifacts=self.artifacts, canary=canary))


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
    parser.add_argument("--wall-clock-seconds")
    parser.add_argument("--last-message")
    parser.add_argument("--canary-file")
    parser.add_argument("--canary-expected")
    parser.add_argument("--artifact", action="append", default=[])
    args = parser.parse_args()
    if bool(args.canary_file) != bool(args.canary_expected):
        parser.error("canary-file and canary-expected must be supplied together")
    report = Collection(args).collect()
    # Exception diagnostics can contain lone surrogates from malformed JSON keys.
    # Escape at delivery so UTF-8 JSON preserves every decoded string verbatim.
    print(json.dumps(report, ensure_ascii=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
