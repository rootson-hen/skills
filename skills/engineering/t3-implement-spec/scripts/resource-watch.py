#!/usr/bin/env python3
"""Write resource telemetry; emit notifications only when intervention changes."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time


def command_output(command):
    return subprocess.check_output(command, text=True, timeout=5).strip()


def sample_native():
    if sys.platform != "darwin":
        raise ValueError("supply --sample-command-json on platforms without the macOS sampler")
    try:
        level = command_output(["/usr/sbin/sysctl", "-n", "kern.memorystatus_vm_pressure_level"])
        pressure = {"1": "normal", "2": "warning", "4": "critical"}.get(level, "unknown")
    except (OSError, subprocess.SubprocessError):
        pressure = "unknown"
    swap = command_output(["/usr/sbin/sysctl", "-n", "vm.swapusage"])
    match = re.search(r"used\s*=\s*([\d.]+)M", swap)
    if not match:
        raise ValueError("could not parse swap usage")
    return {"timestamp": time.time(), "pressure": pressure, "swap_used_mib": float(match[1])}


def read_sample(command):
    value = json.loads(command_output(command)) if command else sample_native()
    if not isinstance(value, dict):
        raise ValueError("sample must be a JSON object")
    for key in ("timestamp", "swap_used_mib"):
        number = value[key]
        if type(number) not in (int, float) or not math.isfinite(number) or number < 0:
            raise ValueError(f"{key} must be a finite nonnegative number")
    if value["pressure"] not in ("normal", "warning", "critical", "unknown"):
        raise ValueError("invalid pressure level")
    return value


def atomic_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as output:
            json.dump(state, output)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def effective_policy(pressure, sustained):
    return "deferred" if pressure == "critical" or sustained else pressure


def restore_history(path, sample, max_age, detector):
    try:
        state = json.loads(path.read_text())
        elapsed = sample["timestamp"] - state["timestamp"]
        if not 0 < elapsed <= max_age or state["detector"] != detector:
            return None
        if (type(state["rapid_samples"]) is not int or state["rapid_samples"] < 0
                or type(state["swap_used_mib"]) not in (int, float)
                or not math.isfinite(state["swap_used_mib"]) or state["swap_used_mib"] < 0
                or type(state["sustained_swap_growth"]) is not bool
                or state["pressure"] not in ("normal", "warning", "critical", "unknown")):
            return None
        return state
    except (OSError, ValueError, TypeError, KeyError):
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--interval", type=float, default=30)
    parser.add_argument("--samples", type=int, help="stop after N samples; otherwise run until stopped")
    parser.add_argument("--sample-command-json", help="argv JSON; emits timestamp, pressure, swap_used_mib")
    parser.add_argument("--swap-growth-mib-per-second", type=float, default=512 / 30)
    parser.add_argument("--rapid-samples", type=int, default=3)
    parser.add_argument("--history-max-age", type=float, default=120,
                        help="maximum seconds between samples to reuse detector history")
    args = parser.parse_args()
    if (not math.isfinite(args.interval) or args.interval <= 0 or args.rapid_samples < 1
            or not math.isfinite(args.swap_growth_mib_per_second)
            or args.swap_growth_mib_per_second <= 0
            or not math.isfinite(args.history_max_age) or args.history_max_age <= 0
            or (args.samples is not None and args.samples < 1)):
        parser.error("interval, sample count, and swap thresholds must be positive and finite")
    command = json.loads(args.sample_command_json) if args.sample_command_json else None
    if command is not None and (not isinstance(command, list) or not command
                               or any(not isinstance(v, str) or not v for v in command)):
        parser.error("--sample-command-json must be a nonempty argv array")
    if args.state.resolve() == args.log.resolve():
        parser.error("state and telemetry log must be different paths")
    previous = None
    previous_policy = None
    rapid_samples = 0
    count = 0
    args.log.parent.mkdir(parents=True, exist_ok=True)
    while args.samples is None or count < args.samples:
        sample = read_sample(command)
        detector = {"rate": args.swap_growth_mib_per_second, "samples": args.rapid_samples}
        if count == 0:
            history = restore_history(args.state, sample, args.history_max_age, detector)
            if history:
                previous = history
                rapid_samples = history["rapid_samples"]
                previous_policy = effective_policy(history["pressure"], history["sustained_swap_growth"])
        rate = 0
        if previous is not None:
            elapsed = sample["timestamp"] - previous["timestamp"]
            if elapsed <= 0:
                raise ValueError("sample timestamps must increase")
            rate = max(0, sample["swap_used_mib"] - previous["swap_used_mib"]) / elapsed
        if previous is not None and sample["timestamp"] - previous["timestamp"] > args.history_max_age:
            rapid_samples = 0
            rate = 0
        rapid_samples = rapid_samples + 1 if rate >= args.swap_growth_mib_per_second else 0
        sustained = rapid_samples >= args.rapid_samples
        state = {"timestamp": sample["timestamp"], "pressure": sample["pressure"],
                 "sustained_swap_growth": sustained, "rapid_samples": rapid_samples,
                 "swap_used_mib": sample["swap_used_mib"], "detector": detector}
        atomic_state(args.state, state)
        telemetry = dict(sample, swap_growth_mib_per_second=rate, sustained_swap_growth=sustained)
        with args.log.open("a") as output:
            output.write(json.dumps(telemetry) + "\n")
        deferred = sample["pressure"] == "critical" or sustained
        policy = effective_policy(sample["pressure"], sustained)
        if policy != previous_policy and (previous_policy is not None or policy != "normal"):
            event = "builds_deferred" if deferred else (
                "builds_resumed" if previous_policy == "deferred" else "policy_changed")
            print(json.dumps(dict(state, event=event)), flush=True)
        previous = sample
        previous_policy = policy
        count += 1
        if args.samples is None or count < args.samples:
            time.sleep(args.interval)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({"event": "sampler_failed", "error": str(error)}), flush=True)
        sys.exit(1)
