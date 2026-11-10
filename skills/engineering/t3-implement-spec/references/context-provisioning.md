# Missing worker context

For instructions or supporting docs unavailable at the agreed version in a
worktree or destination machine, use the project's setup/provisioning mechanism. Commit
only the instruction changes explicitly approved for publication; otherwise provide
a stable read-only copy or accessible reference without overwriting worker edits.

Preserve the context's relative links and resolve any conflict with checkout
instructions before work. Verify from the actual worker workspace that the agreed
version and its targets are accessible. If copying mutable local docs, capture a
coherent version and record enough identity to detect changes; use content hashes
when paths or commit IDs cannot identify it. A machine-local path is not a transfer.

Record the provisioned entry point and version in the checkpoint. If that context
changes, rebind affected workers before they continue under different instructions.
