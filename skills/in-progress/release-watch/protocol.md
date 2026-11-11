# Checker protocol, version 1

`watch.py` invokes an absolute argv once per tick, with identity JSON on stdin.
The adapter returns one JSON object on stdout, exit 0, within 90 seconds:

```json
{"schema_version":1,"identity":{"release_id":"example","run_id":"exact-run","sha":"full-sha"},"status":"pending","progress":{"stage":"build"}}
```

Identity must exactly echo the persisted input after verifying it against the
provider response. The real identity fields belong to the adapter: include
repository, branch, full SHA, pipeline/run and release invocation identity as
needed. A response missing an identity dimension is a fault, not a match.

Statuses: `pending`, `succeeded`, `failed`, `cancelled`, `fault`. Faults have a
`fault` code: `auth`, `network`, `unknown-status`, `identity`, `contract`, `timeout`
or `stalled`. Never put provider error bodies, URLs with tokens, auth headers or
credentials in stdout/stderr. The watcher ignores adapter stderr entirely rather
than recording potentially secret diagnostics.

`progress` is a small, non-secret structure that changes only on actual provider
progress. Do not include the poll time, or time-stall detection cannot work. An
adapter may also return evidence fields. The watcher retains only a progress hash
and terminal state, not evidence or credentials. The agent recollects evidence on
wake; a successful build is not artifact or deployment readiness.

Bound each HTTP call and overall execution. Treat unknown states and API/schema
errors as faults, never success. Use exact run endpoints rather than recent-run
ordering. A status checker must make no repository, registry or deployment writes.

## Events

Outbox event fields: `event_id`, `kind`, `created_at`, `attempts`, `last_attempt`,
plus non-secret delivery result. Kinds are terminal statuses, `fault:<code>` and
`recovered`. Auth, identity, unknown status and stalls surface immediately; other
faults surface after three ticks. The active fault is deduplicated until recovery.
The default no-progress threshold is six hours, configurable through the Python
initializer for a provider's expected duration.

Observation/outbox are atomically saved and fsynced before delivery. A process lock
serializes ticks and acknowledgments. Delivery retries the same event ID at most
once per five minutes, at most four events per tick. `delivery_id` combines event
ID with a transport generation: after 30 minutes without agent ack, including
unknown HTTP outcomes, a new generation permits re-wake despite server replay
dedupe. Retries inside that interval share a transport key. HTTP acceptance never removes the event. The responsible agent explicitly acknowledges after persisting its
handled outcome. A crash before/after a request is therefore safe for at-least-once
delivery; the release action ledger must provide idempotent effects.

Local creator-ID comparison prevents accidental cross-thread acknowledgment; it
is not an authentication boundary against a process that can edit private files.
