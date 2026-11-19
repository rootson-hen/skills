---
name: t3-implement
description: "Implement a spec sequentially with one persistent T3 implementer and final blind review."
disable-model-invocation: true
---

# T3 implement

Read the installed sibling [`implement`](../implement/SKILL.md) as the base
workflow, not a separate invocation. Keep its TDD, validation and review policy;
change only execution ownership as follows.

## T3 coordination

Accept spec/ticket/plan pointers and optional implementer/reviewer selections.
This pilot owns one repository; agree a bounded scope for multi-repository work.
Read repository instructions and requirements, reconcile dependencies and existing
work, and pin the complete review scope and base.

Use `t3-implement-spec`'s shared contracts, not its frontier workflow:
[agents](../t3-implement-spec/references/agents.md),
[workspaces](../t3-implement-spec/references/workspaces.md),
[persistence](../t3-implement-spec/references/persistence.md),
[ledger](../t3-implement-spec/references/ledger.md),
[workers](../t3-implement-spec/references/workers.md) and
[resources](../t3-implement-spec/references/resources.md).
Request missing dependencies before dispatch. File/plan inputs need no tracker;
agree a checkpoint home if repository policy supplies none.

## Persistent implementation

Start **one fresh-context implementer** with the whole scope, base workflow and
agreed seams. Link their thread; retain that worker and checkout across tickets,
questions, compaction and repairs. Work sequentially through red-green **tracer
bullets**, preferably end-to-end when feedback is tight, with no implementation
subagents. Ticket boundaries checkpoint progress rather than reset context.
Use shared recovery rules before any necessary replacement.

The implementer returns before the base workflow's final `code-review` call.
The parent owns that call over the whole scope with fresh blind reviewers, then
returns required repairs and the final `commit` step to the **same implementer**.
The parent owns the checkpoint and tracker closure; delegate claim/evidence writes
explicitly. Preserve repository delivery gates, including required earlier review:
green implementation is not automatically Done. Accept and close through repository
policy, with read-back, and report the checkpoint, evidence and remaining gates.
