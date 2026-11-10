# Workspaces

Discover paths and setup from T3/project configuration. Reuse an appropriate
checkout when its branch and local state are safe; worktrees provide isolation
when needed, not a requirement per ticket. Use T3-managed worktree creation so
the thread is bound to the correct checkout. Verify actual path, branch/base,
instructions, skills, and spec/ticket access in the worker workspace before edits.
Uncommitted main-checkout context may need provisioning through project setup.

Workspaces can share mutable state: linked scratch/docs, artifact caches,
installed snapshots, ports, or databases. Serialize conflicting writers or isolate
the resource. Workers write their own result notes; the orchestrator alone updates
the ledger and ticket lifecycle state. Supply context pointers that resolve from
every destination project, including sibling repositories.
