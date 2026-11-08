# Suggested CLAUDE.md rules

Rules to paste into your own `CLAUDE.md` (the global `~/.claude/CLAUDE.md`, or a project's). Each
section stands on its own, so take only the ones you want.

## Explanations without repetition

Before justifying an implementation in comments or documentation, check whether the explanation
already exists in the files related to the change. Don't search widely for a simple comment.

- Repeating a short justification is fine. A long explanation lives in one place, and the others
  keep the context needed to understand the code and point to it.
- Decisions that affect the whole project (architecture, security, conventions) belong in the
  relevant documentation. Justifications of specific mechanisms stay next to the implementation.
- History of decisions only appears when it helps to understand or maintain the current behavior.

When changing a behavior, update in the same commit the related explanations and references that no
longer match the implementation.
