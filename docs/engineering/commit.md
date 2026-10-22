## What it does

`commit` creates a local Git commit for the requested work. It inspects the current branch, staged changes, and other changes, then includes only work belonging to the task. It commits on the current branch and reports the commit hash and message. It never pushes.

Before writing the message, it reads `docs/agents/commit-messages.md` from the target repository root if that file exists. It follows that format and other applicable repository requirements. Normal Git hooks stay enabled: a failed check needs a fix, not a bypass.

## When to reach for it

Use `/commit` when the work is ready for a local commit. The agent can also invoke it: [implement](https://aihero.dev/skills-implement) uses it after review, and [prototype](https://aihero.dev/skills-prototype) uses it to preserve a prototype on a throwaway branch.

Keep repository-specific commit rules in `docs/agents/commit-messages.md`. [setup-matt-pocock-skills](https://aihero.dev/skills-setup-matt-pocock-skills) can help create it after you confirm the requirements and draft. The commit step reads it directly, with no policy pointer needed in `AGENTS.md` or `CLAUDE.md`.

## Common questions

**Will implement see a commit policy that used to live only in Orca?**

Not unless the policy is available in the target repository. Put the requirements in `docs/agents/commit-messages.md`; implement now calls this skill after review, and this skill reads that file before committing. It does not rely on an Orca-only instruction being in context.

**What if the repository has no commit-messages file?**

It uses a concise Conventional Commit title in imperative mood and adds a body only when useful. Other applicable repository requirements still apply.

**Will it invent Jira references, time values, or workflow actions?**

No. It omits issue references, worklogs, and transitions unless explicitly required. If a required value is missing, or requirements conflict or remain unclear, it asks rather than guessing.

**Will it include unrelated changes or skip failing hooks?**

No. It includes only changes belonging to the requested work and keeps normal Git hooks enabled. Validation failures must be corrected rather than bypassed.

**Does it push or choose a different branch?**

Neither. It commits on the current branch and stops after reporting the hash and message. Publishing the commit is a separate step.

## It's working if

The commit contains only the requested work, its message follows the repository's policy or the documented fallback, and normal hooks passed. You have a commit hash and message, the branch is unchanged, and nothing was pushed.
