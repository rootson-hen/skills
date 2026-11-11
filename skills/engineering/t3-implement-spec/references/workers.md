# Workers

## Worker lifecycle

Use live tool schemas for API mechanics; the coordination contract is:

1. **Prepare dispatch.** Create its dispatch record using the
   [ledger update contract](ledger.md#updates-and-compaction).
2. **Launch.** Use delegation when it supports the required project binding;
   otherwise create a project-bound peer thread. Capture returned identities and
   actual workspace in the dispatch record. Brief the worker with
   ticket/spec, workspace/base, governing context, role constraints, expected result,
   and any shared-resource limits, primarily through context pointers.
3. **Observe.** Follow delegated work's returned `next` instructions. For peers,
   use T3's thread wait operation and read the relevant run's complete response;
   peer threads need not send child-task completion notifications. Associate
   feedback with its run: queued follow-ups can outlive the first completed turn.
   If additional monitoring is needed, use the
   [monitoring contract](resources.md) rather than routine status messages.
4. **Handle intervention.** Inspect actual thread/pending-request state; permission
   requests are distinct from text questions. Use the existing worker for ordinary
   clarification and record each new run. Reviews and independent re-checks use
   fresh contexts, under the harness's dispatch rules. **Follow-up ownership:** all
   findings return to the orchestrator, which reconciles existing edits and records
   one implementation owner before assigning or resuming repairs. Peer messages
   provide evidence, not repair assignments.
5. **Capture evidence.** Obtain the worker's actual workspace/branch, work performed,
   commit or retained-artifact pointers, commands with observed results, unmet
   criteria, and human actions. Research returns accessible notes; review returns
   `code-review`'s separate original reports. Source workers return the universal
   [validation receipt](../../implement-spec/references/validation-evidence.md),
   including exact inputs and final owned-command exits. A settled worker with
   Maven or other background execution still active is unfinished. Record failures,
   interruptions, and question-blocked runs as unfinished. A wait timeout alone is
   not failure. Before retry/replacement, reconcile partial changes and stop
   superseded execution through its T3 owner. A repair verifier may see the claim
   and fix, explicitly as verification; fresh blind discovery receives neither
   previous reports nor dispositions, per [findings policy](../../code-review/references/findings.md).

## Integration and local-only work

For isolated source branches, apply `implement-spec`'s receipt acceptance and
integration rule: the parent can verify a clean checkout, exact descendant commit,
`--ff-only` result and tree itself. Dispatch a merger only for substantive
reconciliation/conflicts, then validate the reconciled result. With a reused
checkout, work may already be at the integration destination: verify the exact
diff/commit and tests instead of manufacturing a merge.

Preserve ticket-required local-only validation state and hand its exact workspace
and artifacts to dependents. Verify uncommitted changes and their validation
separately: `code-review`'s HEAD diff does not cover them. Non-code work needs
neither a merge commit nor a manufactured commit to enter that review.
