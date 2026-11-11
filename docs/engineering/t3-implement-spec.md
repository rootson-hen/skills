## What it does

`t3-implement-spec` adapts [implement-spec](https://aihero.dev/skills-implement-spec)'s
task graph to T3 project-bound workers. One active orchestrator owns each Spec;
a worker's completed run is evidence to reconcile, not ticket acceptance. Exact-source validation receipts and finished owned background commands are checked before integration.

Its ledger is a **resume checkpoint**, not a transcript. It keeps current
dispatches, evidence, retained resources, and next actions in the location selected
through repository configuration.

## When to reach for it

You invoke this by typing `/t3-implement-spec`; the
[agent](https://www.aihero.dev/ai-coding-dictionary/agent) will not reach for it on
its own. Pass a Spec pointer and optional role selections.

- Use it for T3 project binding, cross-repository coordination, or session recovery.
- Use [implement-spec](https://aihero.dev/skills-implement-spec) without T3-specific
  execution bookkeeping.
- Use [implement](https://aihero.dev/skills-implement) to drive one ticket yourself.

## Prerequisites

T3 orchestration tools, the sibling `implement-spec`, and the skills required by
worker roles must be available. Repository tracker configuration is normally
established by [setup-matt-pocock-skills](https://aihero.dev/skills-setup-matt-pocock-skills).

## One checkpoint

Finished attempts shrink to outcome/evidence pointers. Uncertain dispatch identities,
exact review inputs, unmerged work, and unresolved artifact/resource obligations
remain available for recovery. Worker threads and logs carry the history.

- Explicit repository persistence policy wins, including local exceptions.
- Otherwise, local Markdown normally uses a file beside the Spec; suitable remote
  trackers use a mutable record on the Spec, such as an editable comment.
- An unsuitable backend requires an agreed fallback, not a second authority.

Existing ledgers stay in their home unless relocation is agreed and verified.
Machine-local artifact pointers remain machine-local, even in a remote checkpoint.

## Coordination, not a build system

Resource-heavy concurrency uses the target repository's controls and the host's
capacity. Limits account for all participating workers and nested tools rather than
one command in isolation. Contention calls for a proportionate adjustment, not a
universal single-build policy or a pause on independent lightweight work.

Ordinary worktrees use their committed instruction tree. Context unavailable at
the agreed version needs provisioning and verification in the worker's workspace. Follow-up
findings go through the orchestrator so each repair has one implementation owner. Blind discovery contexts receive requirements, not earlier dispositions; the checkpoint points to the separate findings ledger instead of copying it. Clean descendant fast-forwards can be verified by the parent, reserving merger workers for substantive reconciliation.
Monitoring is used when needed; routine telemetry does not merit an interruption.

## Common questions

**Does this require a particular language, host, or resource helper?**

No. It uses the repository's workflow, whether that is Maven, Gradle, another build
system, or non-build work. A bundled Cargo adapter remains available for repositories
that explicitly select it; its Python/POSIX requirements and host policies do not
apply to normal orchestration.

**Will each worker completion add a tracker comment?**

No. The orchestrator updates the checkpoint in place. Acceptance evidence remains
on the tickets; uncertain persistence pauses new dispatch until recovered.

## It's working if

- Resume finds one current next action and reconciles live workers before replacement.
- Finished work leaves compact pointers while recovery and cleanup obligations remain.
- Workers can read the governing context from their actual workspace.
- Resource limits fit the repository and aggregate workload; routine monitoring stays quiet.
- Follow-up findings produce one repair, rather than competing edits.

## Where it fits

This is the T3 execution alternative after [to-spec](https://aihero.dev/skills-to-spec)
and [to-tickets](https://aihero.dev/skills-to-tickets). It preserves
[implement-spec](https://aihero.dev/skills-implement-spec)'s task graph and adds worker
lifecycle and recovery bookkeeping. [ask-matt](https://aihero.dev/skills-ask-matt)
routes the surrounding flows.
