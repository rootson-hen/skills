# Ledger contract

The ledger is a **resume checkpoint**, not an execution transcript. Maintain one
current snapshot and one **Next actions** section, replacing their contents as
state changes. Keep requirements and ticket acceptance in the tracker; point to
them and use its lifecycle vocabulary separately from worker execution state.

## Checkpoint contents

- **Run:** stable run ID/marker, Spec/ticket pointers, checkpoint location,
  orchestrator link, last reconciled time, resolved role selections,
  repositories/T3 projects, integration destinations, fixed review bases/scopes,
  plus any separately provisioned context or shared-resource controls.
- **Dispatches:** one row per active or recovery-relevant attempt: ticket/role,
  resolved agent, unique client request ID, thread link/ID, run/task IDs,
  machine/project, actual checkout/worktree, branch/base, execution state.
  Mark unknown launch results as uncertain, not absent or failed.
- **Evidence and retained state:** result/validation pointers, exact source and
  integration commit identities, unmerged or superseded work still needed,
  review verdict and exact inputs, retained artifacts, shared-resource/auth
  ownership, and release/cleanup conditions. Record machine-local paths with
  their machine/workspace; a remote pointer does not make them portable. Keep
  credentials in the credential store, not the checkpoint.
- **Next actions:** current frontier or blocker/gate, next action and owner,
  and any required intervention. Replace superseded actions in the same section.

A review's identity includes repository, fixed base SHA and scope, reviewed head
SHA, and any separately reviewed uncommitted/artifact inputs. Record validation
commands and observed outcomes by pointer. Reuse evidence only while its relevant
inputs match; a branch name alone is not an input identity.

## Updates and compaction

Persist dispatch intent **before launch**, then returned identities before further
dispatch. Update the affected records after intervention, result, integration,
resource-policy change, and handback; read back the saved checkpoint. If persistence
fails or the write outcome is uncertain, pause new dispatch and recover the saved
state before proceeding. Running workers can still require intervention.

Compress terminal attempts to outcome/evidence pointers once their work is
accounted for. Keep identities and artifacts needed for uncertain-launch recovery,
unmerged work, review reuse, dependent validation, or safe cleanup until those
obligations are resolved. Put detailed history in worker threads/logs, indexed only
when still useful. Remove superseded statuses and resource policies from the
current snapshot rather than appending another "current" section. Resource
heartbeats and tool-event narration belong outside the checkpoint.

## Resume and handoff

Confirm the recorded orchestrator has stopped dispatching before a replacement
takes ownership. Ask if ownership is uncertain; a timestamp or revision counter is
not a lock. Preserve the run ID across session/machine handoff, updating its owner.

Reconcile recorded attempts with live T3 threads/runs, branches/local changes,
artifacts/resources, ticket evidence, and external gates before scheduling new
work. Recover uncertain dispatches by their client request/thread/task identities
before replacement; a timeout alone proves neither failure nor absence. Preserve
recorded role choices unless explicitly overridden; surface inherited-agent changes
caused by a new orchestrator before launching workers.

Worker completion is not ticket acceptance. Require evidence of actual integration,
local-only handoff, or human merge/release events as applicable. Refresh the single
Next actions section from the reconciled state before handing back its pointer.
