# Optional Cargo adapter

Use only when the repository explicitly selects this adapter instead of its own
resource controls. It remains bundled for existing command consumers; it is not a
prerequisite for T3 orchestration. The adapter requires a POSIX host with Python 3
and `flock` support.

```sh
python3 -I <installed-t3-implement-spec>/scripts/cargo-resource-guard.py <cargo args>
```

## Contract

The guard serializes cooperating invocations on one shared lock, sets
`CARGO_BUILD_JOBS`, and lowers CPU priority. It preserves Cargo arguments, including
`--locked` and arguments after `--`. Cargo job flags and inline `--config` before
`--` are rejected because they can override the budget. Use it for build/test/check,
not applications or aliases that detach work. All participating processes must
use the same absolute lock path; unguarded processes remain outside its protection.

`T3_CARGO_GUARD_CONFIG` selects machine-local JSON. This **macOS example** must be
reviewed against the host, not adopted as a workflow default:

```json
{
  "lock_path": "/absolute/shared-state/cargo.lock",
  "state_path": "/absolute/shared-state/resource-state.json",
  "state_max_age_seconds": 120,
  "jobs": {"normal": 3, "warning": 2, "unknown": 1},
  "nice_increment": 10
}
```

Without config, this adapter uses `~/.cache/t3-implement-spec/cargo.lock`, budgets
3/2/1, nice +10, and no sampler state. Its native pressure probe is macOS-specific;
other hosts use the unknown budget unless `pressure_command` supplies `1` (normal),
`2` (warning), or `4` (critical). A configured probe cannot weaken native macOS
critical pressure. Optional `cargo_command` is an argv prefix, default `["cargo"]`.
Paths must be absolute and commands argv arrays. Invalid/unreadable explicit config
or unknown keys fail closed.

With `state_path` configured, missing/malformed/future/stale state uses the unknown
budget while honoring independently observed critical pressure. Fresh critical
state or `sustained_swap_growth: true` returns **75** without launching Cargo.
Without sampler state, swap-based deferral is unavailable. Readings are checked
when the slot is acquired; running builds are not dynamically resized or killed.

Exit **2** is invalid invocation/config or launch failure; other statuses pass
through from Cargo, with signals mapped to `128 + signal`. Exit **75** is deferred,
not passed. SIGINT/SIGTERM target the guard's own Cargo process group and it waits
for its child before releasing the slot. Cargo inherits the lock descriptor; after
abnormal interruption reconcile descendants, since detached descendants may not
retain it. Keep the lock file in place while participants may hold or wait on it.

## Optional sampler

Only if the adapter's host policy needs swap/pressure telemetry, use
`scripts/resource-watch.py --help`. `--log` receives JSONL samples; `--state` is
atomically replaced and must match the guard config. Assign one writer per pair.
The native sampler reads macOS pressure/swap. Other hosts need
`--sample-command-json`, an argv array producing `timestamp` (Unix seconds),
`pressure` (normal/warning/critical/unknown), and `swap_used_mib`.

The adapter's configurable defaults sample every 30 seconds and flag at least
512 MiB of swap growth per 30 seconds for three consecutive intervals. Bounded
restarts reuse history at the same state path when settings match and timestamps
advance within `--history-max-age` (120 seconds by default); longer gaps reset it.

Initial normal state and unchanged effective policy are silent. Stdout JSON events
report throttle/defer/recover/unknown transitions or sampler failure. An event-aware
harness bridge can use those events; stdout alone does not guarantee live wakeup.
For exit-only notifications, inspect bounded-run events using the harness's wait
contract. This adapter installs no monitor or hooks automatically.

## Validation

```sh
python3 -I -B -m unittest discover -s <installed-t3-implement-spec>/tests -v
```

Tests simulate pressure and Cargo processes; they do not stress the host.
