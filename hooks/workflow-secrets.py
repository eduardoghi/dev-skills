#!/usr/bin/env python3
"""PostToolUse hook that runs bin/workflow-secrets on a GitHub Actions workflow Claude just wrote.

Reads the event from standard input and acts only on `.yml` and `.yaml` files under
`.github/workflows/`. A finding goes back to Claude with exit code 2, so it fixes the step in the
same turn. Without PyYAML the check can't run, and the hook says so and lets the edit through.
"""
import importlib.machinery
import importlib.util
import json
import os
import sys
from pathlib import PurePath

TOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", "workflow-secrets")


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    path = (event.get("tool_input") or {}).get("file_path") or ""
    parts = PurePath(path).parts
    in_workflows = len(parts) >= 3 and parts[-3:-1] == (".github", "workflows")
    if not in_workflows or not path.endswith((".yml", ".yaml")):
        return 0
    try:
        import yaml
    except ImportError:
        print("workflow-secrets: PyYAML isn't installed, the workflow wasn't checked", file=sys.stderr)
        return 0
    loader = importlib.machinery.SourceFileLoader("workflow_secrets", TOOL)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    try:
        findings = module.check(path)
    except (OSError, yaml.YAMLError) as error:
        print(f"workflow-secrets: {path} couldn't be checked ({error})", file=sys.stderr)
        return 0
    if not findings:
        return 0
    print(
        "These steps run third-party code with a secret in their environment. Move the install or "
        "build to an earlier step without the secret.",
        file=sys.stderr,
    )
    for finding in findings:
        print(f"  {finding}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
