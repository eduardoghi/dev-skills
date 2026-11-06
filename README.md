# dev-skills

Claude Code plugin with checks for mistakes that keep slipping through reviews of code written
with AI help. Each check runs as a hook while Claude Code edits files, and what it finds goes back
to Claude in the same turn.

## Install

```text
/plugin marketplace add eduardoghi/dev-skills
/plugin install dev-skills@dev-skills
```

The hooks need Python 3 and PyYAML.

## Checks

- `workflow-secrets` runs when Claude writes a file under `.github/workflows/`. It reports each
  step that installs packages, builds or runs a downloaded script while a secret is in its
  environment, from the step, the job or the workflow. Those commands run code from outside the
  repository, which can read the secret. The check is also a standalone script,
  `bin/workflow-secrets FILE...`, that exits with 1 when it finds something, so it can run in CI.

## Tests

```sh
python3 -m unittest discover -s tests
```
