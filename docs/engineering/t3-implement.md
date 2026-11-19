## What it does

`t3-implement` adapts [implement](https://aihero.dev/skills-implement) for a whole
[spec](https://www.aihero.dev/ai-coding-dictionary/spec) in T3. One persistent
[implementer subagent](https://www.aihero.dev/ai-coding-dictionary/subagent) works
through the scope sequentially in one checkout, retaining what it learns between
[tickets](https://www.aihero.dev/ai-coding-dictionary/ticket). The parent thread
manages authority, recovery and final acceptance.

Small feedback loops do not require short-lived implementation contexts. This
workflow preserves tracer-bullet TDD while moving independent blind review to the
end of the complete implementation scope, except where repository policy requires
an earlier gate. It is a personal pilot, not a replacement for `t3-implement-spec`.

## When to reach for it

You invoke this by typing `/t3-implement`, and the agent won't reach for it on its
own. Pass a spec, tickets or an agreed plan, with optional implementer/reviewer
model selections and supported settings.

| You want | Use |
| --- | --- |
| Sequential implementation with retained context and T3 recovery | `/t3-implement` |
| Fresh ticket workers, parallel implementation or cross-repository orchestration | `/t3-implement-spec` |
| Implementation directly in the current thread without a T3 manager | [implement](https://aihero.dev/skills-implement) |

## Prerequisites

T3 delegation and continuation tools must be available. Install both `implement`
and `t3-implement-spec` alongside this adapter: the former supplies the base
workflow, and the latter owns the shared T3 coordination references. Its parallel
scheduler is not run.

The pilot has one owning repository, an agreed review base, public test seams and
one resumable checkpoint. Tracker-backed work follows the repository's configured
tracker; a supplied file or agreed plan can run without creating tracker items.
Required delivery gates still apply.

## Tracer bullets, persistent ownership

The implementer starts with a fresh
[context window](https://www.aihero.dev/ai-coding-dictionary/context-window) and
receives the whole scope. They drive [tdd](https://aihero.dev/skills-tdd) one public
behavior at a time, observing a meaningful red test and then making it green
before moving on. End-to-end paths are preferred when they provide useful, tight
feedback; a test's value comes from behavior it detects, not its label.

Ticket completion is not a reason to discard the implementer's understanding or
create another worktree. The same worker owns exploration, debugging and later
repairs. The parent keeps a compact checkpoint and evidence pointers instead of
rebuilding the implementation story at every handoff.

The parent owns the final [code-review](https://aihero.dev/skills-code-review)
phase, with separate fresh blind Standards and Spec reviewers over the complete
pinned scope. Required repairs go back to the original implementer. Implementation
and review therefore have different context lifetimes without duplicating review.

## Common questions

**Does this remove TDD or build everything before testing?**

No. Slice size and context lifetime are separate choices. Focused checks continue
throughout the work, with full required validation at acceptance boundaries.
Repository hooks and required checks remain enabled.

**Can every review wait until the end?**

Only where repository policy permits it. If a dependent ticket requires an earlier
reviewed or released prerequisite, the workflow respects that gate or asks for an
explicit policy decision. It does not mark unaccepted work Done to unblock itself.

**Will the implementer keep one unlimited context window?**

No. The thread persists, but its history can compact. Progress, partial source,
validation and owned-process state are preserved for recovery. A replacement is a
recovery decision, not the normal next-ticket step.

**Is one implementer proven cheaper or better?**

Not yet. Sequential work avoids per-ticket startup and merge coordination but gives
up implementation parallelism and accumulates context. Compare cost per accepted
spec, feedback time, review repairs and missed requirements on real runs before
promoting this pilot to a default. Model selections are explicit, not inferred
from a provider name.

## It's working if

- Subsequent tickets continue in the original implementer's thread and checkout.
- Each tracer bullet produces visible red-green feedback through a public seam.
- Final review covers the complete spec, with no implementation report supplied
  to the blind reviewers.
- Review repairs return to the original implementer rather than another fresh
  implementation worker.
- Interruptions resume from the same checkpoint without duplicate work, and
  unfinished validation remains visibly unfinished.

## Where it fits

`t3-implement` is the sequential T3 build step after
[to-tickets](https://aihero.dev/skills-to-tickets), or a standalone execution adapter
for an agreed plan. It wraps `implement` while `t3-implement-spec` retains the
fresh-per-ticket orchestration route. Both preserve independent final review and
repository acceptance rules.

[ask-matt](https://aihero.dev/skills-ask-matt) is the router over the whole set.
