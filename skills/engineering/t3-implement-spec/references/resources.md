# Resource stewardship

## Bind before fan-out

Budget shared machine resources before launching workers, including review workers
that run builds. Discover host capacity, repository/build conventions, and competing
work. Record the aggregate build slot, compiler-job budgets, priority, lock/config
identity, telemetry owner, and defer/recovery criteria in the checkpoint. Supply
the same policy to every build-capable worker across worktrees and repositories.
Verify it in the actual worker workspace before its first build. Independent
machines need independent budgets; one checkout lock is not an aggregate budget.

Use a process-safe shared lock for cooperating builds. A per-process jobs limit
alone does not bound parallel workers. Serialize or isolate other shared writers
(databases, ports, auth sessions, generated artifacts) by ownership. Warning
pressure reduces build parallelism; it is not a blanket pause. Critical pressure
or sustained rapid swap growth may defer **new builds** while lightweight edits,
research, and reconciliation continue. Reassess on policy transitions, not every
sample. Never kill unrelated processes or delete a live lock to free a slot.

## Cargo guard

For POSIX hosts with Python 3, the maintained command is:

```sh
python3 -I <installed-t3-implement-spec>/scripts/cargo-resource-guard.py <cargo args>
```

The guard holds one advisory `flock` across Cargo invocations, preserves arguments
(including `--locked` and arguments after `--`), sets `CARGO_BUILD_JOBS`, and lowers
CPU priority. All cooperating workers must use the same absolute lock path. Cargo
job flags and inline `--config` before `--` are rejected because they can override
the budget. Guard a real build/test/check command, not a `cargo run` application or
an alias that starts detached build work. Builds outside the guard remain outside
its protection. Repository tooling can expose it as an explicit optional override;
standalone checks must retain their own bounds without installed skills.

Select machine-local JSON with `T3_CARGO_GUARD_CONFIG`. Paths must be absolute;
commands are argv arrays, never shell strings. Example **macOS policy**, to review
against host capacity rather than apply universally:

```json
{
  "lock_path": "/absolute/shared-state/cargo.lock",
  "state_path": "/absolute/shared-state/resource-state.json",
  "state_max_age_seconds": 120,
  "jobs": {"normal": 3, "warning": 2, "unknown": 1},
  "nice_increment": 10
}
```

Without config, the POSIX fallback uses one per-user lock in
`~/.cache/t3-implement-spec/cargo.lock`, budgets 3/2/1, nice +10, and no sampler state.
The native pressure probe is macOS-specific; other hosts use the unknown budget
unless `pressure_command` supplies `1` (normal), `2` (warning), or `4` (critical).
A configured probe supplements macOS readings and cannot weaken native critical
pressure. Optional `cargo_command` is an argv prefix (default `["cargo"]`).
Unknown keys, invalid budgets, and unreadable explicit config fail closed.

A configured state's missing, malformed, future, or stale reading lowers jobs to
the unknown budget, still honoring independently observed critical pressure.
Fresh critical state or `sustained_swap_growth: true` defers new builds. With no
state configured, swap-based deferral is unavailable; configure the sampler before
fan-out when the resource policy requires it. Readings are checked after acquiring
the slot; a running build is not dynamically resized or killed on a pressure change.

Exit status: **75** means deferred, **2** is invalid invocation/config or launch
failure, otherwise Cargo's exit status (signals map to `128 + signal`). A deferred
check is not a passing check. Retry on recovery, not in a tight model-driven loop.
SIGINT/SIGTERM target only the guard's own Cargo process group; the guard waits for
its child before releasing the slot. Cargo inherits the lock descriptor so an
unexpectedly killed wrapper does not immediately free a still-running Cargo slot.
After abnormal interruption, reconcile Cargo/descendant state before new builds;
a detached descendant is not guaranteed to retain the advisory lock.

## Quiet telemetry

Use `scripts/resource-watch.py --help` for the sampler command. It writes JSONL
samples to `--log` and atomically replaces `--state`, whose path must match the guard
config. One owner writes each state/log pair. The native sampler reads macOS
pressure/swap; other hosts supply `--sample-command-json` with a JSON-emitting argv
array (`timestamp` Unix seconds, `pressure` normal/warning/critical/unknown,
`swap_used_mib`). The default 30-second cadence flags swap growth of at least
512 MiB per 30 seconds for three consecutive intervals; thresholds are configurable.

Detector history and the effective notification policy survive bounded sampler
restarts through `--state` when the next timestamp is increasing and within
`--history-max-age` (default 120 seconds), with unchanged detector settings. Longer
gaps reset detection; stale state cannot establish continuous growth. Reuse the
same state path across bounded runs.

Initial normal state and unchanged samples are silent. Stdout emits JSON events
only on policy changes (throttle, defer, recover, unknown readings) or sampler
failure. Telemetry belongs in files, not checkpoint heartbeats. A harness event
bridge should wake the orchestrator only for these actionable events; stdout alone
does not guarantee a live wakeup. When background tools notify only on exit, use
a bounded sampler run and inspect its events, or an available event-aware wait.
Follow the current harness's returned wait/notification instructions; do not add
polling loops or scheduled model wakeups around tracked background work.

Start monitoring only while needed, retain its task/owner and stop condition, and
stop it through its owner at handback. If the harness requires a background wait,
register that wait before ending the turn. Healthy output must not wake the model.
No global hooks, CI configuration, or perpetual monitor is installed by this skill.
