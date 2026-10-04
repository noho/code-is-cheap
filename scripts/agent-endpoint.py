#!/usr/bin/env python3
"""Read user-owned upstream URLs; never write them during synchronization."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit


def validate_document(doc, allow_empty=False):
    if not isinstance(doc, dict):
        raise ValueError("expected a provider object")
    for provider, runtimes in doc.items():
        if not isinstance(runtimes, dict):
            raise ValueError("invalid provider settings")
        for runtime, url in runtimes.items():
            if runtime not in {"claude", "codex"} or not isinstance(url, str):
                raise ValueError("invalid endpoint settings")
            if not url:
                if allow_empty:  # An unset local field inherits the default.
                    continue
                raise ValueError("empty project default URL")
            parts = urlsplit(url)
            if (parts.scheme not in {"http", "https"} or not parts.hostname
                    or parts.username is not None or parts.password is not None
                    or parts.query or parts.fragment or any(c.isspace() for c in url)):
                raise ValueError("invalid endpoint URL")
            parts.port


def load_endpoints():
    path = Path.home() / ".config/agent-tools/endpoints.json"
    defaults_path = Path(__file__).with_name("agent-endpoints.defaults.json")
    if not defaults_path.exists():
        defaults_path = Path(__file__).resolve().parents[1] / "config/endpoints.example.json"
    try:
        defaults = json.loads(defaults_path.read_text())
        # Missing local config is normal; malformed existing config fails closed.
        try:
            local_text = path.read_text()
        except FileNotFoundError:
            local_text = "{}"
        local = json.loads(local_text)
        validate_document(defaults)
        validate_document(local, allow_empty=True)
        result = {provider: dict(runtimes) for provider, runtimes in defaults.items()}
        for provider, runtimes in local.items():
            for runtime, url in runtimes.items():
                if url:
                    result.setdefault(provider, {})[runtime] = url
        return result
    except (OSError, ValueError):
        # Suppress parser exception chains as they can echo malformed URL data.
        raise ValueError(f"Cannot load endpoint settings; check {path} or reinstall default resources") from None


def endpoint(provider, runtime, doc=None):
    doc = load_endpoints() if doc is None else doc
    try:
        url = doc[provider][runtime]
        if not url:
            raise ValueError(f"Missing default endpoint: {provider}/{runtime}")
        return url.rstrip("/") if runtime == "codex" else url
    except KeyError as exc:
        raise ValueError(f"Missing endpoint: {provider}/{runtime}") from exc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider")
    parser.add_argument("--runtime", choices=["claude", "codex"])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        doc = load_endpoints()
        if not args.check:
            if not args.provider or not args.runtime:
                parser.error("--provider and --runtime are required")
            print(endpoint(args.provider, args.runtime, doc))
    except ValueError as exc:
        parser.exit(1, f"{exc}\n")
