## What it does

`t3-implement-spec` runs the task-graph workflow from
[implement-spec](https://aihero.dev/skills-implement-spec) through T3 project-bound
workers. One active orchestrator owns each Spec, including across session and
machine handoffs. A worker finishing is evidence to reconcile, not proof that its
ticket is accepted.

Its ledger is a **resume checkpoint**, not a transcript. It keeps one current
snapshot of dispatches, evidence, retained resources, and next actions, in the
location selected through repository configuration.

## When to reach for it

You invoke this by typing `/t3-implement-spec`; the
[agent](https://www.aihero.dev/ai-coding-dictionary/agent) will not reach for it on
its own. Pass a Spec pointer and optional implementer/reviewer role selections.

- Use it when T3 workers need project binding, cross-repository coordination, or
  recovery across sessions.
- Use [implement-spec](https://aihero.dev/skills-implement-spec) for the universal
  workflow without T3-specific execution bookkeeping.
- Use [implement](https://aihero.dev/skills-implement) to drive one ticket yourself.

## Prerequisites

T3 orchestration tools and the sibling `implement-spec` skill must be available.
The repository needs a configured issue tracker, normally established by
[setup-matt-pocock-skills](https://aihero.dev/skills-setup-matt-pocock-skills).
Workers also need the skills required by their assigned roles.

## One checkpoint, not competing histories

The checkpoint retains identities needed to recover uncertain dispatches, exact
review inputs, unmerged work, and resource/artifact ownership. Completed attempts
shrink to outcome and evidence pointers once their recovery obligations are met.
Worker threads and logs carry the execution narrative.

Persistence follows the repository's instruction-file pointers, including custom
paths and explicit local exceptions:

- Local Markdown normally uses a checkpoint file beside the Spec.
- Jira and GitHub normally use one identifiable, editable comment on the Spec.
- An unsuitable or unavailable backend requires an agreed fallback before dispatch.

Existing runs stay in their existing home unless relocation is explicitly agreed
and verified. Local probes, logs, and worktrees can remain local; putting their
paths in a remote comment does not make them available on another machine.

## Bind before fan-out

Workers receive one verified governing instruction snapshot and an aggregate
resource policy before they start. Approved committed instructions are preferred;
approved uncommitted instructions require a coherent read-only snapshot, checked
from the actual worker workspace. Mutable main-checkout paths alone are not enough.

The included Cargo guard serializes cooperating builds across worktrees and bounds
compiler jobs. On a configured Mac, warning pressure throttles rather than halts
work; critical pressure or sustained rapid swap growth defers new builds while
lightweight work continues. Machine-local budgets are configurable, not universal
host assumptions. Quiet telemetry writes routine samples to files and emits events
only when the resource policy changes or sampling fails.

Follow-up findings return to the orchestrator, which assigns or resumes one
implementation owner. A reviewer or merger telling a peer about a defect does not
dispatch a second fix.

## Common questions

**Does moving the skill into this fork make it tracker-aware?**

Packaging alone does not. The wrapper resolves repository persistence policy and
checks the available tooling, permissions, capacity, and visibility before using
it. Setup records that policy without embedding T3 worker identities in generic
tracker configuration.

**Will every completed worker add another tracker comment?**

No. The orchestrator updates the same checkpoint record in place and reads it back.
Ticket acceptance evidence remains on the tickets. If persistence becomes
uncertain, new dispatch pauses until the checkpoint is recovered.

## It's working if

- A replacement session finds one current next-action section and reconciles live
  workers before launching replacements.
- Finished work leaves compact evidence pointers, while unresolved recovery and
  cleanup obligations remain visible.
- The checkpoint lives where repository policy says it does, without a silent
  second authoritative copy.
- Handoff names blockers, owners, retained machine-local artifacts, and worker links.
- Concurrent workers use a shared build slot and verified instruction identity.
- Warning pressure reduces compilation without a blanket pause, and unchanged
  healthy telemetry does not wake the orchestrator.
- Each follow-up defect has one implementation owner, without parallel duplicate fixes.

## Where it fits

This is the T3 execution alternative at the implementation step after
[to-spec](https://aihero.dev/skills-to-spec) and
[to-tickets](https://aihero.dev/skills-to-tickets). It preserves
[implement-spec](https://aihero.dev/skills-implement-spec)'s task graph while adding
worker lifecycle and recovery bookkeeping. [ask-matt](https://aihero.dev/skills-ask-matt)
routes the surrounding flows.
