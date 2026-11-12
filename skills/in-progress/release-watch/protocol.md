# Checker protocol v1, watcher state v2

Each tick invokes literal absolute checker argv once, sends identity JSON on stdin
and expects one JSON object on stdout, exit 0, within 90 seconds:

```json
{"schema_version":1,"identity":{"job_id":"example","run_id":"exact-run","pr":123},"status":"pending","progress":{"stage":"build"}}
```

Identity is provider-defined JSON, including numeric IDs. The adapter verifies
all expected identity fields against the provider and echoes it exactly. Include
repository, full SHA and exact run/analysis identity where relevant. Credentials
belong to secure environment injection, never identity, argv, source or state.

Checker statuses: `pending`, `succeeded`, `failed`, `cancelled`, `fault`. Fault
codes: `auth`, `network`, `unknown-status`, `identity`, `contract`, `timeout`.
Unknown states and API/auth errors are never success. Bound each API call and
whole checker. Read exact-run APIs, not recent-run ordering. Output sanitized
codes, not provider bodies or secrets; stderr is not persisted. `progress` is
optional non-secret actual progress, not poll time. It does not extend lifetime.
Terminal semantics belong to the checker: e.g. analysis-ready can be succeeded
without a passing quality gate. The creator rechecks full results on wake.

## Lifetime and events

Default total lifetime is 21600 seconds from creation. Agent-selected values up
to 604800 need no extra permission; longer lifetimes require real user approval
for that duration. `extend` updates total lifetime, not added time per tick.
No no-progress kill/warning exists. State v1 upgrades to a six-hour lifetime while
preserving identity/outbox; old indefinite watches therefore become bounded.

Each wake checks once before expiry, including after an overnight sleep. A terminal
job result wins over expiry. If still pending or faulted at/after expiry, record
`expired`, attempt notification, close and remove the owned LaunchAgent. This does
not cancel or kill the external job. Terminal acknowledgment also closes early.
No agent processing is required for local LaunchAgent expiry cleanup.

Event kinds: checker terminal statuses, `expired`, `fault:<code>` and `recovered`.
Auth/identity/unknown status surface immediately; other faults after three ticks.
An active fault is deduplicated until recovery. Events are atomically fsynced
before transport. Process locks serialize ticks, acknowledgment and cleanup.

Until expiry, retry unacknowledged events every five minutes, at most four per
tick. Durable event ID stays the same; transport `delivery_id` adds a generation,
advanced after 30 minutes without agent ack to permit another T3 wake. HTTP 2xx
means accepted, not handled. The creator saves handled result/blocker before ack.
At expiry **stop background retries even if delivery/ack failed**; retain events
on disk for manual resume. This bounded lifetime deliberately takes precedence
over indefinite delivery. Repeated callbacks must not repeat calling-workflow
side effects; use that workflow's persistent action ledger.

Creator matching and local hashes prevent accidental misrouting, not hostile
processes that can modify the same user's files. Cleanup validates exact label,
path, UID and original plist hash before touching a launch job. The T3 webhook
task is disabled/deleted by the creator through T3 tools, not by an invented local
API. No check is performed while the laptop is asleep or powered off.
