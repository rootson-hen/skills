# Workers

## Worker lifecycle

Use live tool schemas for API mechanics; the coordination contract is:

1. **Persist intent.** Save and read back ticket/role, resolved agent, project,
   workspace choice, and a unique client request ID in the authoritative checkpoint
   before launch. Follow the [ledger contract](ledger.md) if persistence is uncertain.
2. **Launch.** Use delegation when it supports the required project binding;
   otherwise create a project-bound peer thread. Record returned thread link/ID,
   run ID, actual workspace, and delegation task ID if any; save and read back the
   checkpoint before further dispatch. Brief the worker with
   ticket/spec, relevant notes/commits, workspace/base, role constraints, and
   expected result, primarily through context pointers.
3. **Observe.** Follow delegated work's returned `next` instructions. For peers,
   use T3's thread wait operation and read the relevant run's complete response;
   peer threads need not send child-task completion notifications. Associate
   feedback with its run: queued follow-ups can outlive the first completed turn.
4. **Handle intervention.** Inspect actual thread/pending-request state; permission
   requests are distinct from text questions. Use the existing worker for ordinary
   clarification and record each new run. Reviews and independent re-checks use
   fresh contexts, under the harness's dispatch rules.
5. **Capture evidence.** Obtain the worker's actual workspace/branch, work performed,
   commit or retained-artifact pointers, commands with observed results, unmet
   criteria, and human actions. Research returns accessible notes; review returns
   `code-review`'s output. Record failures, interruptions, and question-blocked runs
   as unfinished. A wait timeout alone is not failure. Before retry/replacement,
   reconcile partial changes and stop superseded execution through its T3 owner.

## Integration and local-only work

For isolated source branches, verify repository/base and integrate through
`implement-spec`'s merger role. With a reused checkout, work may already be at the
integration destination: verify the exact diff/commit and tests instead of
manufacturing a merge.

Preserve ticket-required local-only validation state and hand its exact workspace
and artifacts to dependents. Verify uncommitted changes and their validation
separately: `code-review`'s HEAD diff does not cover them. Non-code work needs
neither a merge commit nor a manufactured commit to enter that review.
