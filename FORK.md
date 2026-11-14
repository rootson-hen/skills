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

The initial audit compared 28 installed skills from `mattpocock/skills` with the
per-skill Git trees recorded in `~/.agents/.skill-lock.json`: 81 files, including
53 supporting files. Only `grilling/SKILL.md` was customized. Its final paragraph
now requires an agreed summary and an immediate stop, without modifying project
files; the user invokes a downstream skill to continue. No files were added or
removed, and no supporting files were customized.

Differences from a newer upstream release alone are not customizations. In
particular, the installed `resolving-merge-conflicts` folder matches its recorded
historical tree but is absent at v1.3.1. It is not copied into this release-based
fork as a personal customization.

## Refinement decisions

One entry per merge cluster, with the reasoning and the session evidence it
rested on, so the next upstream collision can re-decide with context rather
than from zero.

**2026-11-14, upstream `5863806` (unreleased tip, explicit exception):**

- `implement-spec` step 4 (implementer startup): took upstream verbatim (fresh
  subagent per ticket, reset onto integration branch). No incident anywhere
  supports the fork's preserve-and-report line (T3 threads, Claude transcripts
  and the Bob store were searched; the only reset episode, Bob 2026-10-23,
  fired correctly on an empty worktree), and the commit that added it
  (`362a307`) records no rationale. The protection survives in
  `t3-implement-spec`'s references, where real usage runs. Step 7 (final
  review): kept the fork's adjudicated review, folding in upstream's "single
  fresh implementer subagent" as repair owner; upstream's own docs still
  describe the four-hour fix-loop as unresolved. Evidence: t3-implement-spec
  runs jira-cli HEN-5/23/80 and ekmf specs, 2026-11-10 to 13.
- `implement`: kept the fork's pinned-base review paragraph (upstream's
  one-liner walks into the empty-diff problem their own shared FAQ documents),
  adopting upstream's "call the Skill tool with" verb form. Evidence:
  code-review's 34 invocations, including the ekmf DB2-alpha reviews at a
  pinned merge-base, 2026-11-10 to 12.
- `code-review`: kept the fork throughout (findings ledger, blind discovery,
  tracker resolution via `AGENTS.md`/`CLAUDE.md` configuration pointers; a
  2026-11-10 T3 finding showed the fixed tracker-config path assumption
  failing) and added upstream's explicit fresh-context-window sentence.
- `grilling`: kept the fork verbatim. The hard stop is this fork's founding
  refinement; upstream's doc ending ("before it acts on what you agreed")
  would contradict the auto-merged `SKILL.md`.
- `retro`: kept the fork verbatim. The doc was written 2026-11-13 (`0387bc8`)
  for the decision-ready skill that auto-merged unchanged; upstream's doc
  describes their simpler skill.
- `ask-matt`, `prototype`: kept the fork. The conflicted additions document
  fork-only skills (`commit`, `t3-implement-spec`) that survive the merge.
- `setup-matt-pocock-skills`: blended. Kept pointer-following and
  preserve-exceptions semantics; took upstream's existing-section check and
  the legacy `CONTEXT.md` migration.
- Post-merge coherence pass: nine fresh reviewers, one per skill changed on
  both sides (the eight above plus `tdd`, whose supporting files the fork had
  converted to Java while upstream changed its `SKILL.md`). Twelve fixes
  applied, all small: stale bug claims and counts in `ask-matt` and `tdd`
  docs, the tdd Java example, the setup label-creation contradiction (docs
  said labels are never created; the merged skill creates them), setup's
  undocumented `CONTEXT.md` migration and hardcoded template paths, a
  private-workspace clause removed from `retro` docs, and wording alignments
  in `code-review` and `implement-spec`. Known and left alone: fork docs link
  fork-only skills to `aihero.dev/skills-<name>` URLs that upstream does not
  publish; that is a pre-existing fork-wide convention, not a merge
  regression.
