---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec, tickets or agreed plan.

If the user passes a ticket reference, fetch it from the issue tracker and state its title before starting. If the reference is ambiguous, ask.

Call the Skill tool with "tdd" where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full required test scope once at the end. Agree and validate the evidence using the sibling [validation-evidence contract](../implement-spec/references/validation-evidence.md), rather than a second receipt format. Own background commands through final exits and cleanup; unfinished execution is not completion.

Once implemented, call the Skill tool with "code-review" against a pinned base and a source snapshot that actually includes the changes. Its normal HEAD diff requires an interim commit; use the repository's authorized commit workflow, or agree an explicit uncommitted-input review scope instead of reviewing an empty diff. Keep independent blind discovery and reconcile afterward using [the findings policy](../code-review/references/findings.md). Repair required findings, record optional/accepted/deferred decisions, and verify changed surface and impact. Full blind re-review needs changed invariants, not cosmetic churn.

Call the Skill tool with "commit" for the final local commit. Report accepted validation evidence and unresolved scope separately from tracker closure; this skill does not itself close the ticket.
