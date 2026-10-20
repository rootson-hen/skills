# Personal fork

This is a public fork of [mattpocock/skills](https://github.com/mattpocock/skills).
It keeps the full upstream structure and MIT license. Changes here are personal
refinements, not proposed upstream defaults.

## Branches and remotes

- `origin`: `https://github.com/rootson-hen/skills.git`
- `upstream`: `https://github.com/mattpocock/skills.git`
- `personal`: the customized branch and this fork's default branch.
- `main`: the upstream branch as copied when the fork was created; not the
  customized branch and not required for updates.

The initial baseline is upstream **v1.3.1**. After an update, the merge commit
records the new release baseline.

## Make a customization

Keep each meaningful refinement in a small, focused commit. Explain the need it
serves, not just the wording that changed. Keep related skill documentation and
any required changeset in the same commit; follow `AGENTS.md`.

Use Git history as the change ledger. Do not rebase, squash, or force-push
published customization history. To inspect changes since a release:

```sh
git log --first-parent --oneline personal
git log --oneline v1.3.1..personal --not upstream/main
git diff v1.3.1 personal -- skills/
```

Substitute the most recently merged upstream release for `v1.3.1` after updates.

## Adopt an upstream release

Use tagged releases by default. Fetching discovers updates without changing
`personal` or any installed skills. Review and merge explicitly.

Start with a clean working tree:

```sh
git switch personal
git status --short
git fetch upstream --tags
```

Choose a release from [upstream releases](https://github.com/mattpocock/skills/releases).
For example, when adopting `v1.4.0` from `v1.3.1` (replace both tags with the actual
releases):

```sh
git log --oneline v1.3.1..v1.4.0
git diff --stat v1.3.1 v1.4.0
git merge --no-ff --no-commit v1.4.0
```

Resolve conflicts, then review the staged changes and each affected personal
customization. A conflict-free merge does not prove that the skill still serves
its intended purpose. Keep, adapt, or explicitly retire refinements based on that
purpose. Check affected docs and run the repository's relevant validation.

```sh
git diff --cached
git diff --check
git commit -m "merge: adopt upstream v1.4.0"
git push origin personal
```

Use `git merge --abort` to abandon an in-progress update. Adaptations made later
should be separate focused commits that explain why the customization changed.
Take unreleased upstream changes only as an explicit exception.

## Installation is separate

This repository does not prescribe an agent, installation directory, or deployment
method. Editing or updating this checkout does not install its contents. The
upstream README's installation examples still refer to upstream, not this fork.

The initial setup leaves `~/.agents`, `~/.bob/skills`, and existing symlinks
untouched. Agent-specific installation remains a separate decision.

## Initial customization audit

The initial audit compares installed skills from `mattpocock/skills` with the
per-skill Git trees recorded in `~/.agents/.skill-lock.json`, including supporting
files. Differences from a newer upstream release alone are not customizations.
The audit's verified result is recorded in the initial customization commit.
