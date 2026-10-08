#!/usr/bin/env python3
"""Resolve private default/override connections; sync never writes user data."""

import argparse
import copy
import json
import os
from pathlib import Path
import stat
from urllib.parse import urlsplit

FIELDS = {"base_url", "upstream_model", "api_key"}


def user_path():
    return Path.home() / ".config/agent-tools/endpoints.json"


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def read_json(text):
    return json.loads(text, object_pairs_hook=unique_object)


def validate_url(url):
    if not isinstance(url, str) or not url:
        raise ValueError("empty or invalid base URL")
    parts = urlsplit(url)
    if (
        parts.scheme not in {"http", "https"}
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
        or any(c.isspace() for c in url)
    ):
        raise ValueError("invalid base URL")
    parts.port


def validate_document(doc, known=None):
    if (
        not isinstance(doc, dict)
        or "default" not in doc
        or set(doc) - {"default", "override"}
    ):
        raise ValueError("expected default and optional override objects")
    for section in ["default", "override"]:
        providers = doc.get(section, {})
        if not isinstance(providers, dict):
            raise ValueError("invalid configuration section")
        for provider, runtimes in providers.items():
            if not isinstance(runtimes, dict) or not runtimes:
                raise ValueError("invalid provider settings")
            for runtime, value in runtimes.items():
                if runtime not in {"codex", "claude"} or (
                    known is not None and runtime not in known.get(provider, {})
                ):
                    raise ValueError("unknown provider/runtime")
                if not isinstance(value, dict) or set(value) != FIELDS:
                    raise ValueError(
                        "connection requires base_url, upstream_model and api_key together"
                    )
                validate_url(value["base_url"])
                model, key = value["upstream_model"], value["api_key"]
                if (
                    not isinstance(model, str)
                    or not model
                    or any(c.isspace() or c in '"\\' for c in model)
                ):
                    raise ValueError("invalid upstream model")
                if not isinstance(key, str) or any(c in key for c in "\r\n\0"):
                    raise ValueError("invalid API key")
                if section == "override" and provider != "local" and not key.strip():
                    raise ValueError("cloud override requires its own API key")
                if provider == "local" and runtime == "codex" and key:
                    raise ValueError(
                        "direct local Codex connection does not support an API key"
                    )


def factory_document():
    path = Path(__file__).with_name("agent-endpoints.defaults.json")
    if not path.exists():
        path = Path(__file__).resolve().parents[1] / "config/endpoints.example.json"
    doc = read_json(path.read_text())
    validate_document(doc)
    if doc.get("override") or not doc["default"]:
        raise ValueError("invalid project defaults")
    if any(
        value["api_key"] and provider != "local"
        for provider, runtimes in doc["default"].items()
        for value in runtimes.values()
    ):
        raise ValueError("project defaults cannot contain credentials")
    return doc


def load_endpoints():
    """Return one effective snapshot, replacing whole runtime connections."""
    try:
        factory = factory_document()
        path = user_path()
        try:
            info = path.lstat()
        except FileNotFoundError:
            local = {"default": {}, "override": {}}
        else:
            if (
                not stat.S_ISREG(info.st_mode)
                or stat.S_IMODE(info.st_mode) != 0o600
                or info.st_uid != os.getuid()
            ):
                raise ValueError(
                    "private file must be an owned regular file with mode 600"
                )
            local = read_json(path.read_text())
        validate_document(local, factory["default"])
        result = copy.deepcopy(factory["default"])
        for section in ["default", "override"]:
            for provider, runtimes in local.get(section, {}).items():
                result[provider].update(copy.deepcopy(runtimes))
        return result
    except (OSError, ValueError, TypeError):
        raise ValueError(
            "Cannot load private connection settings; check JSON schema, mode 600 and project defaults"
        ) from None


def connection(provider, runtime, doc=None, require_key=False):
    doc = load_endpoints() if doc is None else doc
    try:
        result = dict(doc[provider][runtime])
    except KeyError:
        raise ValueError("unknown provider/runtime") from None
    if require_key and provider != "local" and not result["api_key"].strip():
        raise ValueError(
            "Selected connection has no API key; fill its api_key in endpoints.json"
        )
    if runtime == "codex":
        result["base_url"] = result["base_url"].rstrip("/")
    return result


def endpoint(provider, runtime, doc=None):
    return connection(provider, runtime, doc)["base_url"]


def initialize():
    path = user_path()
    if path.exists() or path.is_symlink():
        load_endpoints()
        return
    data = (json.dumps(factory_document(), indent=2) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)


class FullAccessConflict(ValueError):
    pass


def launch_claude(provider, args, compact_window, max_context, api_timeout, full_access=False):
    if full_access:
        for arg in args:
            if arg == "--":
                break
            if arg == "--restricted" or arg.split("=", 1)[0] in {"--settings", "--permission-mode"}:
                raise FullAccessConflict("--full-access conflicts with custom settings/permission mode/restricted mode")
    value = connection(provider, "claude", require_key=True)
    model = value["upstream_model"]
    settings = {
        "ANTHROPIC_BASE_URL": value["base_url"],
        "ANTHROPIC_MODEL": model,
        **{
            name: model
            for name in [
                "ANTHROPIC_SMALL_FAST_MODEL",
                "ANTHROPIC_DEFAULT_SONNET_MODEL",
                "ANTHROPIC_DEFAULT_OPUS_MODEL",
                "ANTHROPIC_DEFAULT_HAIKU_MODEL",
                "ANTHROPIC_DEFAULT_FABLE_MODEL",
                "CLAUDE_CODE_SUBAGENT_MODEL",
            ]
        },
        "CLAUDE_CODE_SUBAGENT_MODEL_FORCE": "1",
        "CLAUDE_CODE_ENABLE_TODO_TOOLS": "1",
        "CLAUDE_CODE_DISABLE_AUTO_TITLE": "1",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "CLAUDE_CODE_DISABLE_SESSIONMETADATA": "1",
        "CLAUDE_CODE_DISABLE_QUOTA_CHECK": "1",
        "DISABLE_NON_ESSENTIAL_MODEL_CALLS": "1",
        "CLAUDE_CODE_EFFORT_LEVEL": "max",
        "CLAUDE_CODE_AUTO_COMPACT_WINDOW": compact_window,
    }
    if max_context:
        settings["CLAUDE_CODE_MAX_CONTEXT_TOKENS"] = max_context
    if api_timeout:
        settings["API_TIMEOUT_MS"] = api_timeout
    # The installed helper is also directly callable: enforce the same
    # credential boundary as the shell launcher before adding selected auth.
    credential_parts = (
        "KEY",
        "TOKEN",
        "SECRET",
        "PASSWORD",
        "CREDENTIAL",
        "AUTHORIZATION",
    )
    env = {
        name: content
        for name, content in os.environ.items()
        if not any(part in name.upper() for part in credential_parts)
        and name.upper() not in {"ANTHROPIC_CUSTOM_HEADERS", "SSH_AUTH_SOCK"}
    }
    env["ANTHROPIC_AUTH_TOKEN"] = value["api_key"]
    document = {"env": settings}
    if full_access:
        document.update(sandbox={"enabled": False}, skipDangerousModePermissionPrompt=True)
        args = ["--permission-mode", "bypassPermissions", *args]
    os.execvpe("claude", ["claude", "--settings", json.dumps(document), *args], env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider")
    parser.add_argument("--runtime", choices=["claude", "codex"])
    parser.add_argument(
        "--field", choices=["base_url", "upstream_model"], default="base_url"
    )
    for flag in ["check", "require-key", "initialize"]:
        parser.add_argument("--" + flag, action="store_true")
    parser.add_argument("--launch-claude")
    parser.add_argument("--full-access", action="store_true")
    parser.add_argument("--compact-window", default="786432")
    parser.add_argument("--max-context", default="")
    parser.add_argument("--api-timeout", default="")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if args.initialize:
            initialize()
        elif args.launch_claude:
            launch_claude(
                args.launch_claude,
                args.args[1:] if args.args[:1] == ["--"] else args.args,
                args.compact_window,
                args.max_context,
                args.api_timeout,
                args.full_access,
            )
        elif args.check and not args.provider:
            load_endpoints()
        else:
            if not args.provider or not args.runtime:
                parser.error("--provider and --runtime are required")
            value = connection(
                args.provider, args.runtime, require_key=args.require_key
            )
            if not args.check:
                print(value[args.field])
    except FullAccessConflict as error:
        parser.exit(2, str(error) + "\n")
    except (OSError, ValueError, KeyError, TypeError):
        parser.exit(
            1,
            "Cannot use connection settings; check JSON fields, mode 600 and selected api_key.\n",
        )


if __name__ == "__main__":
    main()
