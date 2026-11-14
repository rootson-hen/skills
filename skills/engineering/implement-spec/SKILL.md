---
name: implement-spec
description: "Implement the result of /to-spec and /to-tickets in code."
disable-model-invocation: true
---

You have been provided a spec. This spec should have tickets associated with it, describing how to implement the spec.

The issue tracker should have been provided to you. If not, tell the user to run `/setup-matt-pocock-skills`.

The goal is the entire spec implemented on a single **integration branch**, with every ticket resolved the way the issue tracker closes work.

The tickets are not a list of steps. They are a **task graph** with blocking relationships between them. This means there is always a **frontier** of tickets which are ready to be grabbed.

Start every subagent with a fresh context window.

Communication to and from subagents should be sparse. Communicate primarily through **context pointers**: to the spec, tickets, research notes, and previous commits. Don't duplicate information already available via pointers.

**Implementer subagents** should be run in the background where possible for maximum concurrency.

## Steps

1. Read the spec and tickets to understand the task graph. Before execution, agree each ticket's validation plan using [validation evidence](references/validation-evidence.md), including source/dependency identity, expected suites and named skip policy. Use repository tooling to produce the receipt; worker completion alone is not acceptance.

2. (optional) Use an **exploration subagent** to conduct any exploration required by the tickets - relevant codebase files or external documentation. Ensure the exploration subagent can save files - it should save its markdown notes in a directory outside the repo, accessible by all future subagents. This lets **implementer subagents** focus on implementation rather than exploration.

3. Create the integration branch. If the issue tracker closes work through PRs, or the user asks for one, open a draft PR after the first merge in step 5 (a branch with no commits ahead of main can't open one), marked as closing the spec and tickets.

4. Use a fresh **implementer subagent** for each ticket, each in its own worktree on its own branch. Each implementer subagent:
   - confirms its worktree is based on the integration branch before starting, and resets onto it if not;
   - calls the Skill tool with `tdd` to build the ticket;
   - owns its background commands through their final exit and process cleanup, preserving unfinished state on interruption;
   - reconciles the integration tip into its branch when needed, then returns an exact-source validation receipt and retained-artifact pointers.

5. Once an **implementer subagent** completes, verify its [validation receipt](references/validation-evidence.md) and acceptance coverage before integration. For a clean integration checkout and a verified descendant of its current tip, the parent can run `git merge --ff-only <verified-commit>` and verify the resulting commit/tree itself. Use a **merger subagent** only for substantive reconciliation/conflicts, with revalidation of the reconciled result. Recheck identity at integration; a moving branch name is not the verified commit.

6. If this changes the **frontier** of available tickets, kick off more **implementer subagents** to work on the new tickets. This allows for maximum concurrency.

7. Once all tickets are complete, call the Skill tool with `code-review` on the pinned integration scope. Preserve blind Standards/Spec discovery, then adjudicate findings using its [findings policy](../code-review/references/findings.md). Assign required repairs to a single fresh **implementer subagent**; record optional, accepted and deferred claims with reasons. Verify repairs with targeted changed-surface/impact checks and fresh applicable validation evidence. Run full blind discovery again only when changed invariants justify it, not as a cosmetic clean-report loop.

8. If a draft PR exists, mark it ready for review. Otherwise, resolve each ticket the way the issue tracker closes work, and report the integration branch.

9. Clean up disposable **implementer subagent** worktrees only after acceptance, owned execution completion, integration and required local artifacts are accounted for. Retain blocked/unfinished evidence and report its owner.
