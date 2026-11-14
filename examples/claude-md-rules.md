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

## Where heavy files go

Before proposing a folder for a tool environment, model weights, a cache or other data read on every
run, check what kind of drive each candidate is, not only how much space it has free. On Windows,
`Get-PhysicalDisk` gives the media type and `Get-Partition` maps drive letters to disks.

- Prefer an SSD for what is read often, and leave a large HDD for archives such as finished renders.
- Package managers that hardlink from a cache, such as uv and pnpm, only do it within one volume, so
  an environment on the cache's volume avoids a second copy of large packages.
- Name the media type in the recommendation, so a wrong guess is easy to catch.
