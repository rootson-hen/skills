# Workspaces

Resolve checkout paths and setup from T3/project configuration. Reuse a safe
checkout or create a T3-managed worktree when isolation is needed. Before work,
verify the actual branch/base, repository instructions, required skills, and
Spec/issue/context access from that workspace.

Use the checkout's committed instruction tree unless repository/user instructions
identify a different governing version. If that version or required supporting
context is unavailable in the workspace, follow
[Missing worker context](context-provisioning.md) before dispatch.

Workspaces may still share mutable services or artifacts. For conflicting writers
or resource-heavy concurrency, apply [Resource stewardship](resources.md).
