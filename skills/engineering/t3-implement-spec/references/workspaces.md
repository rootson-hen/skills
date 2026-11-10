# Workspaces

Discover paths and setup from T3/project configuration. Reuse an appropriate
checkout when its branch and local state are safe; worktrees provide isolation
when needed, not a requirement per ticket. Use T3-managed worktree creation so
the thread is bound to the correct checkout. Verify actual path, branch/base,
skills, Spec/issue access, instruction identity, and resource policy in the worker
workspace before edits or builds. Provisioning is complete only after this check,
not when a main-checkout path was placed in the brief.

## Governing instructions

Resolve the effective instruction tree and the documents it points to, including
approved uncommitted instructions in the coordinating checkout. Prefer a reviewed,
explicitly approved committed instruction snapshot before dispatch when committing
those paths is authorized. An implementation task is not authorization to commit
arbitrary dirty work. Record the governing commit and entry points in the checkpoint.

If the approved context must remain uncommitted, provision one coherent read-only
snapshot through project setup or a shared accessible location. Record a manifest
of relative paths and content hashes, snapshot location/identity, and its precedence
against the worker checkout's instructions. Check source hashes before and after
capture; retry or block on changes rather than accepting a mixed-time snapshot.
Preserve relative links and include their required targets. Give each worker a
resolvable entry point and verify the manifest from its actual workspace. For
another machine, transfer the approved snapshot or block; an absolute path alone
is not provisioning.

Keep snapshot files immutable for the run. Never overlay worker edits or copy dirty
source onto them. If checkout instructions conflict with the snapshot, reconcile
precedence before work. Instruction updates require a new approved snapshot and
explicit rebind of affected workers, not unnoticed changes through mutable symlinks.
Retain the original local files and any pending edits; cleanup only after their
ownership and preservation are accounted for.

## Shared state and handoff

Workspaces can share mutable state: linked scratch/docs, artifact caches,
installed snapshots, ports, databases, or auth sessions. Serialize conflicting
writers or isolate the resource under [Resource stewardship](resources.md).
Workers write their own result notes; the orchestrator alone updates the checkpoint
and issue lifecycle state. Supply context pointers that resolve from every
destination project, including sibling repositories.

All acceptance defects and follow-up findings return to the orchestrator. A peer
pointer or informational message is evidence, not authorization to launch repairs.
The orchestrator reconciles existing edits and assigns/resumes one implementation
owner before follow-up work; mergers and reviewers retain their assigned scope.
