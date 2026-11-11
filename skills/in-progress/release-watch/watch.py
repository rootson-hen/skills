#!/usr/bin/env python3
"""Bounded, token-free release observation with a durable acknowledged outbox.

Adapters consume identity JSON on stdin and return the contract in protocol.md.
No shell, branch mutation, scheduler installation, or callback creation occurs here.
"""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

TERMINAL = {"succeeded", "failed", "cancelled"}
FAULTS = {"auth", "network", "unknown-status", "identity", "contract", "timeout", "stalled"}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".state-")
    try:
        with os.fdopen(fd, "w") as out:
            json.dump(value, out, sort_keys=True, indent=2)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def locked(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(str(path) + ".lock", os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(fd, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def initialize(path, identity, creator, checker, now=None, stall_seconds=21600):
    if not isinstance(identity, dict) or not identity or not all(isinstance(v, str) and v for v in identity.values()):
        raise ValueError("identity must be a nonempty string-valued object without credentials")
    if set(creator) != {"environment_id", "project_id", "thread_id"} or not all(creator.values()):
        raise ValueError("creator environment/project/thread IDs are required")
    if not checker or not Path(checker[0]).is_absolute():
        raise ValueError("checker executable must be absolute")
    if stall_seconds < 300:
        raise ValueError("stall threshold must be at least 300 seconds")
    with locked(path):
        if Path(path).exists():
            raise ValueError("state already exists; resume it instead")
        now = time.time() if now is None else now
        state = dict(schema_version=1, identity=identity, creator=creator, checker=checker,
                     created_at=now, progressed_at=now, stall_seconds=stall_seconds,
                     progress=None, status="pending", faults=0, active_fault=None,
                     outbox=[], acknowledged=[], callback=None)
        save(path, state)
    return state


def bind_callback(path, receipt):
    """Accept only a task receipt bound to this release's creator, never retarget."""
    with locked(path):
        state = json.loads(Path(path).read_text())
        if receipt.get("boundThreadId") != state["creator"]["thread_id"] or receipt.get("projectId") != state["creator"]["project_id"]:
            raise ValueError("callback is not bound to the release creator and project")
        if not receipt.get("scheduledTaskId") or not receipt.get("webhookUrl") or receipt.get("blockedByPolicy"):
            raise ValueError("callback unavailable: check T3 Connect and policy; do not fabricate a URL")
        # URL is a bearer credential. Keep it in the scheduler's credential injection,
        # not in this ledger or the task receipt copied into it.
        state["callback"] = {"task_id": receipt["scheduledTaskId"], "thread_id": receipt["boundThreadId"],
                             "url_fingerprint": fingerprint(receipt["webhookUrl"])}
        save(path, state)


def observe(state):
    try:
        result = subprocess.run(state["checker"], input=json.dumps(state["identity"]), text=True,
                                capture_output=True, timeout=90, check=False)
        value = json.loads(result.stdout)
        if result.returncode or value.get("schema_version") != 1:
            return {"status": "fault", "fault": "contract"}
        if value.get("identity") != state["identity"]:
            return {"status": "fault", "fault": "identity"}
        status = value.get("status")
        if status == "fault" and value.get("fault") in FAULTS:
            return {"status": status, "fault": value["fault"]}
        if status not in TERMINAL | {"pending"}:
            return {"status": "fault", "fault": "unknown-status"}
        return {"status": status, "progress": fingerprint(value.get("progress"))}
    except subprocess.TimeoutExpired:
        return {"status": "fault", "fault": "timeout"}
    except (OSError, ValueError, TypeError, AttributeError):
        return {"status": "fault", "fault": "contract"}


def enqueue(state, kind, now):
    event_id = fingerprint([state["identity"], kind, now])
    state["outbox"].append({"event_id": event_id, "kind": kind, "created_at": now,
                            "attempts": 0, "last_attempt": None, "generation": 0,
                            "accepted_at": None})


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def deliver_event(state, event):
    url = os.environ.get("RELEASE_CALLBACK_URL", "")
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        return "callback-unavailable"
    if not state.get("callback") or fingerprint(url) != state["callback"].get("url_fingerprint"):
        return "callback-owner-mismatch"
    body = json.dumps({"schema_version": 1, "event_id": event["event_id"],
                       "delivery_id": event["event_id"] + ":" + str(event["generation"]),
                       "kind": event["kind"], "identity": state["identity"],
                       "creator": state["creator"]}, sort_keys=True).encode()
    headers = {"Content-Type": "application/json", "X-Release-Event": event["event_id"]}
    secret = os.environ.get("RELEASE_CALLBACK_SECRET")
    if secret:
        import hmac
        headers["X-Release-Signature"] = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    try:
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=15) as response:
            return "accepted-unacknowledged" if 200 <= response.status < 300 else "delivery-failed"
    except (OSError, ValueError):
        return "delivery-failed"


def tick(path, now=None, observation=None, delivery=None):
    now = time.time() if now is None else now
    with locked(path):
        state = json.loads(Path(path).read_text())
        if state["status"] not in TERMINAL:
            value = observe(state) if observation is None else observation
            status = value["status"]
            fault = value.get("fault")
            if status == "pending":
                if value.get("progress") != state["progress"]:
                    state["progress"], state["progressed_at"] = value.get("progress"), now
                if now - state["progressed_at"] >= state["stall_seconds"]:
                    status, fault = "fault", "stalled"
            if status == "fault":
                state["faults"] += 1
                fault = fault if fault in FAULTS else "contract"
                if (state["faults"] >= 3 or fault in {"auth", "identity", "unknown-status", "stalled"}) and state["active_fault"] != fault:
                    enqueue(state, "fault:" + fault, now)
                    state["active_fault"] = fault
            else:
                if state["active_fault"] and status == "pending":
                    enqueue(state, "recovered", now)
                state["faults"], state["active_fault"] = 0, None
                state["status"] = status
                if status in TERMINAL:
                    enqueue(state, status, now)
            # Persist observation and outbox BEFORE attempting delivery.
            save(path, state)
        if delivery and state["callback"]:
            for event in state["outbox"][:4]:
                if event["last_attempt"] is not None and now - event["last_attempt"] < 300:
                    continue
                # A missing agent ack, even with an unknown HTTP outcome, gets
                # a new transport key after 30 minutes. Keep the durable event
                # identity stable so repeated wakes cannot repeat release effects.
                origin = event.get("generation_started_at", now)
                if now - origin >= 1800:
                    event["generation"] += 1
                    event["accepted_at"] = None
                    event["generation_started_at"] = now
                event.setdefault("generation_started_at", now)
                event["attempts"] += 1
                event["last_attempt"] = now
                save(path, state)
                event["delivery"] = delivery(state, event)
                if event["delivery"] == "accepted-unacknowledged" and event["accepted_at"] is None:
                    event["accepted_at"] = now
                save(path, state)
        return state


def acknowledge(path, event_id, creator):
    with locked(path):
        state = json.loads(Path(path).read_text())
        if creator != state["creator"]:
            raise ValueError("acknowledgment must come from the recorded creator context")
        if event_id in state["acknowledged"]:
            return
        if not any(e["event_id"] == event_id for e in state["outbox"]):
            raise ValueError("unknown event")
        state["outbox"] = [e for e in state["outbox"] if e["event_id"] != event_id]
        state["acknowledged"].append(event_id)
        save(path, state)


def launchd_plist(wrapper, state_path):
    if not Path(wrapper).is_absolute() or not Path(state_path).is_absolute():
        raise ValueError("absolute wrapper and state paths required")
    return plistlib.dumps({"Label": "local.release-watch." + fingerprint(str(state_path))[:16],
                          "ProgramArguments": [str(wrapper), str(state_path)],
                          "StartCalendarInterval": [{"Minute": minute} for minute in range(0, 60, 5)],
                          "RunAtLoad": True, "ProcessType": "Background"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["init", "tick", "status", "ack", "bind", "plist"])
    parser.add_argument("state", type=Path)
    parser.add_argument("--identity", type=Path)
    parser.add_argument("--creator", type=Path)
    parser.add_argument("--checker", nargs=argparse.REMAINDER, help="Absolute checker argv; place this option last.")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--event-id")
    parser.add_argument("--wrapper")
    parser.add_argument("--deliver", action="store_true")
    args = parser.parse_args()
    if args.command == "init":
        if not args.identity or not args.creator or not args.checker:
            parser.error("init requires --identity, --creator and --checker")
        if any(args.state.resolve().is_relative_to(root.resolve()) for root in [Path(tempfile.gettempdir()), Path("/tmp"), Path("/var/tmp")]):
            parser.error("use persistent private state, not a temporary directory")
        initialize(args.state, json.loads(args.identity.read_text()), json.loads(args.creator.read_text()), args.checker)
    elif args.command == "tick":
        state = tick(args.state, delivery=deliver_event if args.deliver else None)
        print(json.dumps({"status": state["status"], "fault": state["active_fault"], "unacknowledged": len(state["outbox"])}))
    elif args.command == "ack":
        if not args.creator or not args.event_id:
            parser.error("ack requires --creator and --event-id")
        acknowledge(args.state, args.event_id, json.loads(args.creator.read_text()))
    elif args.command == "bind":
        if not args.receipt:
            parser.error("bind requires a private --receipt file")
        bind_callback(args.state, json.loads(args.receipt.read_text()))
    elif args.command == "plist":
        if not args.wrapper:
            parser.error("plist requires --wrapper")
        sys.stdout.buffer.write(launchd_plist(args.wrapper, args.state))
    else:
        print(args.state.read_text())


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        print("release-watch: invalid state/configuration; inspect local inputs (credentials redacted)", file=sys.stderr)
        sys.exit(1)
