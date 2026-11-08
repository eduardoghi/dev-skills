# dev-skills

Claude Code plugin with checks for mistakes that keep slipping through reviews of code written
with AI help. Each check runs as a hook while Claude Code edits files, and what it finds goes back
to Claude in the same turn.

## Install

```text
/plugin marketplace add eduardoghi/dev-skills
/plugin install dev-skills@dev-skills
```

The hooks need Python 3, and `workflow-secrets` also needs PyYAML.

## Checks

- `workflow-secrets` runs when Claude writes a file under `.github/workflows/`. It reports each
  step that installs packages, builds or runs a downloaded script while a secret is in its
  environment, from the step, the job or the workflow. Those commands run code from outside the
  repository, which can read the secret. The check is also a standalone script,
  `bin/workflow-secrets FILE...`, that exits with 1 when it finds something, so it can run in CI.

- `stale-paths` runs when Claude writes any file in a git repository. It reports each repository
  path that a comment (in source) or the text (in Markdown, outside fenced blocks) names and that
  doesn't exist, the reference a moved or renamed file leaves behind. A short path given from a
  nested source root counts when a file of the repository ends with it, and a word whose folders
  the repository doesn't have is not taken for a path. A line that names a removed file on purpose
  carries `stale-paths: ignore`. Also a standalone script, `bin/stale-paths FILE...`, that exits
  with 1 when it finds something.

## Skills

- `qt-pitfalls` holds mistakes in QML that compile and pass qmllint but fail on screen, such as
  JavaScript the QML engine lacks or a popup sized by the list inside it. Its `paths` field makes
  Claude Code load it only when working on `.qml` files, so other projects pay only for its name
  and one line.

- `rust-pitfalls` and `cpp-pitfalls` hold mistakes that compile and fail only on an edge or at exit,
  such as `then_some` evaluating its value before the check, an early return that leaves a lock
  held, and worker threads racing the cleanup of a driver when the process ends. Each loads only for
  files of its language.

## Suggested CLAUDE.md rules

`examples/claude-md-rules.md` holds rules that are not checks, to paste into your own `CLAUDE.md`,
where Claude reads them in every session. It has one now, which keeps Claude from writing the same
justification in several comments and docs, the copies that drift apart when the code changes.

## Tests

```sh
python3 -m unittest discover -s tests
```
