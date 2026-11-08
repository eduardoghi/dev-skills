#!/usr/bin/env python3
"""PostToolUse hook that runs bin/stale-paths on a file Claude just wrote.

Reads the event from standard input. A path the file's comments or text name and that does not
exist goes back to Claude with exit code 2, so it fixes the reference in the same turn. A file
outside a git repository, or of a kind the check doesn't read, is let through untouched.
"""
import importlib.machinery
import importlib.util
import json
import os
import sys

TOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", "stale-paths")


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    path = (event.get("tool_input") or {}).get("file_path") or ""
    if not path or not os.path.isfile(path):
        return 0
    loader = importlib.machinery.SourceFileLoader("stale_paths", TOOL)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    try:
        findings = module.check(path)
    except (OSError, UnicodeDecodeError):
        return 0
    if not findings:
        return 0
    print(
        "These paths are named in the file but don't exist. Point them at where the file is now, "
        "or drop the reference. A path to a file you are about to create can be left as it is.",
        file=sys.stderr,
    )
    for finding in findings:
        print(f"  {finding}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
