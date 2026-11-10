#!/usr/bin/env python3
"""Serialize cooperating Cargo commands and bound jobs using machine-local policy."""
import fcntl
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

DEFERRED = 75


def load_config():
    path = os.environ.get("T3_CARGO_GUARD_CONFIG")
    raw = json.loads(Path(path).read_text()) if path else {}
    allowed = {"lock_path", "state_path", "state_max_age_seconds", "jobs",
               "nice_increment", "pressure_command", "cargo_command"}
    if not isinstance(raw, dict) or raw.keys() - allowed:
        raise ValueError("config must be an object with documented keys only")
    config = {
        "lock_path": str(Path.home() / ".cache" / "t3-implement-spec" / "cargo.lock"),
        "state_path": None, "state_max_age_seconds": 120,
        "jobs": {"normal": 3, "warning": 2, "unknown": 1},
        "nice_increment": 10, "pressure_command": None, "cargo_command": ["cargo"],
    }
    config.update(raw)
    for key in ("lock_path", "state_path"):
        value = config[key]
        if value is None and key == "state_path":
            continue
        if not isinstance(value, str) or not Path(value).is_absolute():
            raise ValueError(f"{key} must be an absolute path")
    jobs = config["jobs"]
    if (not isinstance(jobs, dict) or set(jobs) != {"normal", "warning", "unknown"}
            or any(type(n) is not int or n < 1 for n in jobs.values())
            or not jobs["unknown"] <= jobs["warning"] <= jobs["normal"]):
        raise ValueError("jobs must be positive integer normal >= warning >= unknown budgets")
    if type(config["nice_increment"]) is not int or not 0 <= config["nice_increment"] <= 19:
        raise ValueError("nice_increment must be an integer from 0 to 19")
    age = config["state_max_age_seconds"]
    if type(age) not in (int, float) or not math.isfinite(age) or age <= 0:
        raise ValueError("state_max_age_seconds must be positive and finite")
    for key in ("pressure_command", "cargo_command"):
        cmd = config[key]
        if cmd is None and key == "pressure_command":
            continue
        if not isinstance(cmd, list) or not cmd or any(not isinstance(x, str) or not x for x in cmd):
            raise ValueError(f"{key} must be a nonempty argv array")
    return config


def pressure_level(command):
    if command is None:
        if sys.platform != "darwin":
            return "unknown"
        command = ["/usr/sbin/sysctl", "-n", "kern.memorystatus_vm_pressure_level"]
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=5, check=False)
        return {"1": "normal", "2": "warning", "4": "critical"}.get(
            result.stdout.strip() if result.returncode == 0 else "", "unknown")
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"


def saved_state(path, max_age):
    if path is None:
        return None
    try:
        state = json.loads(Path(path).read_text())
        timestamp = state["timestamp"]
        if type(timestamp) not in (int, float) or not math.isfinite(timestamp):
            return None
        if not 0 <= time.time() - timestamp <= max_age:
            return None
        if (state["pressure"] not in ("normal", "warning", "critical", "unknown")
                or type(state["sustained_swap_growth"]) is not bool):
            return None
        return state
    except (OSError, ValueError, KeyError, TypeError):
        return None


def run_cargo(config, args, jobs, lock_fd):
    env = os.environ.copy()
    env["CARGO_BUILD_JOBS"] = str(jobs)
    child = None
    interrupted = None

    def forward(signum, _frame):
        nonlocal interrupted
        interrupted = signum
        if child is not None:
            try:
                os.killpg(child.pid, signum)
            except ProcessLookupError:
                pass

    previous = {sig: signal.signal(sig, forward) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        os.nice(config["nice_increment"])
        if interrupted:
            return 128 + interrupted
        child = subprocess.Popen(config["cargo_command"] + args, env=env,
                                 start_new_session=True, pass_fds=(lock_fd,))
        if interrupted:
            forward(interrupted, None)
        status = child.wait()
        return 128 + interrupted if interrupted else (status if status >= 0 else 128 - status)
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def has_jobs_option(arg):
    if arg == "--jobs" or arg.startswith("--jobs="):
        return True
    if not arg.startswith("-") or arg.startswith("--"):
        return False
    for option in arg[1:]:
        if option == "j":
            return True
        if option in "pFZC":
            # These short options consume the remaining text as a value.
            return False
    return False


def main(args):
    if not args or args == ["--help"]:
        print("Usage: python3 -I cargo-resource-guard.py <cargo args>\n"
              "Optional T3_CARGO_GUARD_CONFIG selects a machine-local JSON policy.\n"
              "Exit 75: deferred; 2: invalid invocation/config; otherwise Cargo status.")
        return 0 if args else 2
    cargo_options = args[:args.index("--")] if "--" in args else args
    if any(has_jobs_option(a) for a in cargo_options):
        raise ValueError("omit Cargo job flags; the guard owns compiler parallelism")
    if any(a == "--config" or a.startswith("--config=") for a in cargo_options):
        raise ValueError("Cargo --config can override jobs; use repository config plus the guard budget")
    config = load_config()
    lock_path = Path(config["lock_path"])
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    # Never unlink the lock: waiting processes must agree on the same inode.
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(lock_path, flags, 0o600)
    try:
        with os.fdopen(fd, "a+") as lock:
            print("Cargo guard: waiting for aggregate build slot", file=sys.stderr, flush=True)
            fcntl.flock(lock, fcntl.LOCK_EX)
            pressure = pressure_level(config["pressure_command"])
            native_pressure = pressure_level(None) if config["pressure_command"] else pressure
            state = saved_state(config["state_path"], config["state_max_age_seconds"])
            if "critical" in (pressure, native_pressure) or (state and (state["pressure"] == "critical"
                                                       or state["sustained_swap_growth"])):
                print("Cargo guard: new build deferred by critical pressure or sustained swap growth",
                      file=sys.stderr, flush=True)
                return DEFERRED
            # A configured but unavailable sampler cannot authorize the normal budget.
            if config["state_path"] and state is None:
                pressure = "unknown"
                print("Cargo guard: stale/unreadable state; using unknown budget", file=sys.stderr)
            levels = [pressure] + ([state["pressure"]] if state else [])
            if sys.platform == "darwin":
                levels.append(native_pressure)
            jobs = min(config["jobs"][p] for p in levels)
            print(f"Cargo guard: acquired slot; max {jobs} jobs; nice +{config['nice_increment']}",
                  file=sys.stderr, flush=True)
            return run_cargo(config, args, jobs, lock.fileno())
    except BaseException:
        # fdopen owns the descriptor after entry; no separate close/unlink here.
        raise


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(130)
    except (OSError, ValueError, TypeError) as error:
        print(f"Cargo guard: {error}", file=sys.stderr)
        sys.exit(2)
