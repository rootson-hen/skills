# Checkpoint configuration

Record orchestration persistence with the tracker workflow, or link to an existing
ledger policy from it. Make it reachable through the repository instruction files;
consumers follow pointers, not a required heading or filename. Preserve an explicit
policy unless the user requests a change.

The policy specifies the checkpoint home, discovery/update mechanism, writer and
reader visibility constraints, and any deliberate local exception. Keep worker IDs,
models, and run-specific state in the consuming orchestration skill's checkpoint.

## Recommended defaults

- **Local Markdown:** `orchestration.md` beside the Spec, under the configured
  scratch/ignore convention. Agree a location when the convention is absent.
- **Jira or GitHub:** one identifiable, editable comment on the Spec issue/Epic
  per run. Keep requirements in the Spec and acceptance evidence on the tickets.
- **GitLab:** one editable note on the Spec issue per run, when supported.
- **Other:** a suitable mutable record attached to the Spec, if supported;
  otherwise agree one explicit location.

For remote records, verify available CLI/API/MCP discovery, exact-record read,
creation and update, permissions, visibility, and capacity. Inspect available
schemas/help and read-only access; configuration setup does not create a test
comment or change an active run. Document limitations or unverified capabilities
for the orchestrator to resolve before dispatch. An exposed REST operation does
not imply an available MCP tool.

## Consumer rules to record

- One active orchestrator per Spec owns writes. The run has a stable marker,
  record ID and durable URL/path so later sessions can rediscover it.
- Update one authoritative checkpoint in place and read back writes. After an
  uncertain creation, discover by marker before retrying. A revision is not a lock.
- Explicit repository policy wins. For older configs without a ledger policy,
  prefer suitable persistence in the configured tracker after capability checks.
- If the chosen backend is unsuitable or unavailable, explain why and agree one
  fallback before new dispatch; never silently keep a second authoritative ledger.
- Resume an existing run in its existing home. Moving it requires explicit
  agreement, reconciliation, a verified new checkpoint, and a superseded pointer
  from the old one. Setup alone neither relocates nor edits active ledgers.
- Local execution artifacts may remain local. Identify machine-bound pointers and
  keep enough recovery state in the checkpoint for the intended handoff. Publish
  only metadata appropriate for its audience, never credentials.

Use these as prose instructions, not a new database schema or a requirement to
install tooling. Show the policy in the setup draft before writing it.
