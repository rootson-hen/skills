# Resource stewardship

Before resource-heavy concurrency, discover the repository's build/test controls,
host capacity, and shared bottlenecks. Bound **aggregate load** across workers,
including nested tools, test forks, and long-lived daemons; a per-command limit
alone does not bound the run. Prefer repository-native controls and scheduling.
Serialize conflicting writers or isolate their shared services and artifacts;
serialize other work only where capacity requires it.

Pass the relevant limits and resource ownership to affected workers, recording
what a later session needs to resume. Adjust the affected workload proportionately
to observed contention. Defer heavy work when capacity is unsafe or unavailable,
while independent lightweight work continues. Intervene only in owned resources.

Monitor when a capacity concern or external gate warrants it, using existing
telemetry and the harness's wait/notification contract. Interrupt the orchestrator
for an actionable change, failure, or decision; keep routine samples in local
telemetry. Give a temporary monitor an owner and stop condition.

Only when a repository explicitly selects the bundled Cargo adapter, read
[Cargo adapter](cargo-adapter.md) for its specialized command and host policy.
