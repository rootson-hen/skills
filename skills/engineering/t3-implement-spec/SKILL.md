---
name: t3-implement-spec
description: "Run implement-spec through T3 project-bound workers with a configuration-aware resume checkpoint."
disable-model-invocation: true
---

# T3 implement-spec

Read the installed sibling [`implement-spec`](../implement-spec/SKILL.md) directly
as the universal workflow, not as a separate invocation. This wrapper supplies its
T3 execution adaptations. If the dependency is missing, request its installation.

Accept spec/ticket pointers and optional provider, model, and supported settings
for implementer, reviewer, explorer, or merger in ordinary language. The current
session remains the orchestrator, with one active orchestrator per Spec.

## 1. Reconcile

Read the spec, tickets, and owning repositories' instructions, following their
configuration pointers to the issue tracker and any ledger policy. Account for
every ticket's dependencies, completion criterion, repository, and existing evidence.
If no tracker is configured, tell the user to run `/setup-matt-pocock-skills`.

Resolve or resume the authoritative checkpoint using
[Persistence](references/persistence.md), then reconcile its contents using the
[Ledger contract](references/ledger.md) before scheduling work.

## 2. Bind

Resolve role selections using [Resolve agents](references/agents.md).
Map each ticket to its owning T3 project and a safe
[workspace](references/workspaces.md). Before resource-heavy concurrency or shared
writes, apply [Resource stewardship](references/resources.md).

For source changes, keep an integration destination **per repository**. Continue
feature branches/PRs identified by the spec; create integration branches only
where needed. Establish each repository's fixed review base and scope from
user/repository instructions; ask when undefined or ambiguous. Verify the base
resolves and record both. Include pre-existing feature work belonging to the spec,
not just this run's changes.

## 3. Dispatch the frontier

Follow `implement-spec`'s frontier loop with one fresh implementation context per
ticket. Dispatch only when dependencies and workspace/resource ownership permit
it, using the [worker lifecycle](references/workers.md).
Link each worker so the user can enter its thread and answer questions.

Every role owns its skill's internal process and subagents. Report a blocker if the
chosen worker cannot execute the required skill.

## 4. Reconcile results

A completed T3 run is a **result**, not proof that its ticket is done. Validate its
receipt using [validation evidence](../implement-spec/references/validation-evidence.md),
check criterion coverage and owned background-process completion, then perform the applicable
[integration or local-only handoff](references/workers.md#integration-and-local-only-work),
and persist the outcome before recomputing the frontier.

Before a human merge/release gate, complete the applicable repository review and
PR-readiness work; whole-graph completion must not block that prerequisite.
Continue independent ready work. When unfinished tickets remain but no executable
frontier exists, hand back the checkpoint pointer, blocker reasons, next
actions/owners, and worker links. Resume by reconciling the same run.

## 5. Close

Apply `implement-spec`'s final review and resolution per repository, reusing a
completed review only while its inputs match. Handle fixes through the
[worker lifecycle](references/workers.md#worker-lifecycle). Close only when every
ticket's completion criterion is evidenced.

Retain worker threads for inspection. Clean up only disposable workspaces whose
work and local-only artifacts are accounted for, under T3/repository permissions.
Persist the final checkpoint and report branches/PRs, validation, and retained artifacts.
