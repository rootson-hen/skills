---
name: t3-implement
description: "Implement a spec sequentially with one persistent T3 implementer and final blind review."
disable-model-invocation: true
---

# T3 implement

Read the installed sibling [`implement`](../implement/SKILL.md) directly as the
base workflow, not as a separate invocation. This adapter changes execution
ownership: one persistent implementer builds the whole scope; the current thread
orchestrates its final review and acceptance. Read only the named shared T3
references below, not `t3-implement-spec`'s frontier workflow. If either sibling
skill is missing, request its installation before dispatch.

Accept a spec, tickets, or agreed plan and optional implementer/reviewer provider,
model and supported settings in ordinary language. This pilot uses one owning
repository. For a multi-repository spec, agree a bounded repository scope or tell
the user to use `/t3-implement-spec` instead.

## 1. Reconcile the scope

Read the complete requirements and ticket discussions, repository instructions,
and their tracker/configuration pointers. State referenced tickets' titles. A
supplied file or agreed plan needs no tracker; tracker-backed work needs its
configured workflow. Tell the user to run `/setup-matt-pocock-skills` if needed.
Account for every ticket, dependency, completion criterion and existing change.

Resolve one authoritative checkpoint using
[Persistence](../t3-implement-spec/references/persistence.md) and the
[Ledger contract](../t3-implement-spec/references/ledger.md). For file/plan inputs,
use their owning repository's persistence policy and agree a checkpoint location
if none exists. Resume the same run and reconcile live execution before replacing
an implementer or taking over another orchestrator's scope.

Agree the public test seams and validation plan through `implement`'s validation
contract. Separate implementation prerequisites from delivery gates. A green
slice may support later work only when repository/tracker policy permits it;
review, human approval, installation or release prerequisites remain gates.
Keep blocked work blocked and tracker completion truthful. Surface a policy
conflict before dispatch rather than assuming final-only review overrides it.

## 2. Bind one implementer

Resolve role selections through
[Resolve agents](../t3-implement-spec/references/agents.md). Unspecified roles
inherit this thread's selection. Use live T3 capabilities and the harness's
delegation rules; report unavailable selections or required capabilities.

Choose one safe working checkout and feature branch through
[Workspaces](../t3-implement-spec/references/workspaces.md). Reuse it across all
tickets; create a T3-managed worktree only when isolation is needed. Preserve
existing work and verify the actual path, branch, base and required context.
Pin the repository's review base and complete scope, including existing feature
work belonging to this spec; ask when the base or scope is ambiguous.

Persist dispatch intent, then start one implementer with a **fresh context
window**, not a fork of this conversation. Supply the whole scope by original
spec/ticket pointers, the ordered dependencies, agreed seams, governing context,
checkout, fixed review base and resource limits. Link the returned worker thread
and save its task/run/workspace identities in the checkpoint.

## 3. Continue through tracer bullets

The implementer reads `implement` as its base, calls the Skill tool with `tdd`,
and owns exploration, implementation and debugging for the whole scope. Work
sequentially in dependency order, one red-green **tracer bullet** at a time at the
agreed public seams. Prefer a runnable end-to-end path when it provides a tight,
meaningful feedback loop. Keep focused checks running throughout, and preserve
slice/ticket evidence, remaining criteria and artifact pointers for recovery.
Use [Resource stewardship](../t3-implement-spec/references/resources.md) for heavy
commands or shared services, including this single worker's test forks/daemons.

Ticket boundaries are progress checkpoints, not fresh dispatches. Continue in
the same worker and checkout, with no implementation subagents or parallel
writers. The implementer may make authorized interim commits for recovery and
review visibility; commit hooks and repository-required checks still apply.
The orchestrator owns the authoritative checkpoint and tracker closure. Delegate
any ticket claim/evidence writes explicitly, with one writer per record.

Follow the task's returned wait/notification instructions. Resume the existing
worker for clarification, remaining tickets and repairs using the harness's
supported continuation mechanism. Keep updates to deltas and evidence pointers;
the orchestrator checks coverage and gates rather than repeating exploration or
rerunning every green cycle. Hand back questions and external gates with the
checkpoint and worker link; continue only work that is independently permitted.

Before compaction or interruption, preserve the current slice, source state,
evidence and owned-process state. A persistent thread can compact; it is not an
unlimited context window. Replace it only when continuation is unavailable or
the user changes the execution choice, after reconciling partial work and
stopping superseded owned execution. Retain the same run and checkout when safe.

## 4. Review the whole scope

The implementer returns when the whole agreed implementation scope and required
validation are ready, or identifies exact blockers. Require `implement`'s
exact-source validation receipt, criterion coverage and final owned-command exits;
a completed turn with tests still running is unfinished.

The orchestrator owns `implement`'s final `code-review` call once per repository
scope, normally after all implementation, not once per ticket. Brief the
implementer to return before that call so it is not duplicated. Use the pinned
base and a source snapshot including all changes. Preserve `code-review`'s fresh,
independent blind Standards and Spec discovery; reviewers receive original
requirements and standards, not implementation reports or prior dispositions.
They review directly, with no further delegation.

Adjudicate findings using `implement`'s findings policy. Return required repairs
to the **same implementer**, retaining sole implementation ownership, then verify
the changed surface, impact and fresh applicable validation. Use fresh contexts
for independent repair re-checks; repeat full blind discovery only for changed
invariants. A repository-required earlier review gates its affected work and
does not justify routine per-ticket review or bypassing the final uncovered scope.

## 5. Accept and close

Have the same implementer call the Skill tool with `commit` for final local
changes after required repairs. If the final snapshot changes, refresh applicable
validation and review coverage before acceptance. Account for every criterion,
exact accepted source, owned process and retained artifact. Verify changes already
in the destination rather than manufacturing a merge; reconcile and revalidate
any actual integration before claiming delivery.

Only the orchestrator resolves tracker-backed tickets/specs, according to their
configured acceptance and merge/release rules, with read-back. File/plan inputs
need no manufactured tracker items. Pushes, PRs and merges follow user/repository
authority; this wrapper grants none. Retain the worker thread and required local
evidence, clean up only accounted-for disposable workspaces, and persist the
final checkpoint. Report commits/branches/PRs, validation, review dispositions,
unresolved gates and the checkpoint pointer separately.
