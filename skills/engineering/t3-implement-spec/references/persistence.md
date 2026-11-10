# Persistence

## Resolve before dispatch

Follow the owning repository's `AGENTS.md` / `CLAUDE.md` configuration pointers,
including custom paths and headings, to its tracker and explicit ledger policy.
For a multi-repository Spec, resolve one checkpoint home from the Spec's owning
configuration; ask about conflicting policies rather than making a ledger per repo.

Look for an existing run via the supplied checkpoint pointer, Spec records/comments,
and configured or previously recorded local locations. Enumerate all relevant
comment pages when discovering by marker. Resume the same run; ask when multiple
records compete for authority. A changed default is not permission to relocate an
existing ledger.

Explicit policy wins, including a deliberate local exception. For a new run with
no ledger policy, prefer suitable persistence in the configured tracker:

- **Local Markdown:** `orchestration.md` beside the Spec under its configured
  scratch/ignore convention. Verify Git exclusion before committing nearby work;
  agree a location when no convention exists.
- **Jira or GitHub:** one identifiable, editable checkpoint comment on the Spec
  issue/Epic, separate from its requirements and ordinary ticket evidence.
- **Other trackers:** use their supported mutable record attached to the Spec;
  agree a backend when no suitable convention can be established.

Verify the available CLI/API/MCP can discover, read, create, and update the exact
record, with adequate capacity, writer permissions, and appropriate reader
visibility. REST support alone does not establish MCP capability or permission.
Check visibility of execution metadata and pointer targets before publishing;
respect repository/harness authorization for external writes. Do not publish
secrets or sensitive local details to a broader audience.

If the backend is unsuitable, unavailable, or cannot preserve recovery-critical
state, explain the limitation and agree one fallback before dispatch. If an
existing ledger needs relocation, first reconcile and agree the move, write and
read back the new checkpoint, then mark the old record superseded with a pointer.
Continue only once a single authority is clear; an interrupted move requires
reconciliation, not another ledger.

## Mutable-record protocol

Choose a stable run ID on creation and persist a visible marker such as
`orchestration-run: <run-id>`, the Spec pointer, and orchestrator link in the record.
Keep it across resumes. Capture the returned record ID and durable URL/path;
include that pointer in orchestrator handbacks. The Spec comment's marker makes
it discoverable even when its returned ID was lost.

Read the record before updating and target its exact ID/path. The orchestrator is
the only writer; workers return results to it. Update the same checkpoint rather
than posting one comment per event. Read back to verify the saved marker and
contents. If creation/update times out, rediscover/read before retrying; never
blindly create a replacement. Unexpected edits or owner changes require
reconciliation, not overwrite. Revision counters do not provide atomic ownership.

Keep ticket acceptance evidence on the tickets. Local logs, probes, worktrees, and
resource telemetry may remain local supporting artifacts, not a second current
checkpoint. Store enough recovery-critical state in the authoritative checkpoint
for the intended handoff; inaccessible pointers alone are insufficient.
