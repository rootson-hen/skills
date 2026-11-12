#!/usr/bin/env python3
"""T3/macOS job watcher: bounded checks, durable events and self-cleaning lifetime.

Checker protocol remains v1. State v2 adds an absolute lifetime (six hours by
default); no no-progress timeout. Installation never occurs on init or tick.
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
import urllib.parse
import urllib.request

DEFAULT_LIFETIME = 6 * 3600
MAX_UNAPPROVED_LIFETIME = 7 * 86400
TERMINAL = {"succeeded", "failed", "cancelled", "expired"}
FAULTS = {"auth", "network", "unknown-status", "identity", "contract", "timeout"}


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


def validate_lifetime(seconds, approval=None):
    if not isinstance(seconds, int) or isinstance(seconds, bool) or seconds < 300:
        raise ValueError("lifetime must be at least 300 seconds")
    if seconds > MAX_UNAPPROVED_LIFETIME:
        if not isinstance(approval, dict) or approval.get("lifetime_seconds") != seconds or not isinstance(approval.get("user_message"), str) or not approval["user_message"].strip():
            raise ValueError("more than seven days requires explicit user approval for that lifetime")


def initialize(path, identity, creator, checker, now=None, lifetime_seconds=DEFAULT_LIFETIME, approval=None):
    # Identity is provider-defined JSON, e.g. Sonar app/PR IDs are integers.
    if not isinstance(identity, dict) or not identity:
        raise ValueError("nonempty identity object required; credentials belong in environment")
    json.dumps(identity, allow_nan=False)
    if set(creator) != {"environment_id", "project_id", "thread_id"} or not all(isinstance(v, str) and v for v in creator.values()):
        raise ValueError("creator environment/project/thread IDs are required")
    if not checker or not all(isinstance(v, str) for v in checker) or not Path(checker[0]).is_absolute():
        raise ValueError("checker executable must be absolute")
    validate_lifetime(lifetime_seconds, approval)
    with locked(path):
        if Path(path).exists():
            raise ValueError("state already exists; resume it instead")
        now = time.time() if now is None else now
        state = dict(schema_version=2, identity=identity, creator=creator, checker=checker,
                     created_at=now, lifetime_seconds=lifetime_seconds, expires_at=now + lifetime_seconds,
                     lifetime_approval=approval, progress=None, status="pending", faults=0,
                     active_fault=None, outbox=[], acknowledged=[], callback=None, launchd=None,
                     closed=False, cleanup=None)
        save(path, state)
    return state


def load(path):
    state = json.loads(Path(path).read_text())
    if state.get("schema_version") == 1:
        # Upgrade old ledgers without following a new run or dropping the outbox.
        state.update(schema_version=2, lifetime_seconds=DEFAULT_LIFETIME,
                     expires_at=state["created_at"] + DEFAULT_LIFETIME,
                     lifetime_approval=None, launchd=None, closed=False, cleanup=None)
        state.pop("stall_seconds", None)
        state.pop("progressed_at", None)
    if state.get("schema_version") != 2:
        raise ValueError("unsupported state schema")
    return state


def extend(path, lifetime_seconds, approval=None, now=None):
    """Set total wall-clock lifetime from creation, not additional time per tick."""
    validate_lifetime(lifetime_seconds, approval)
    with locked(path):
        state = load(path)
        if state["closed"]:
            raise ValueError("closed watch: start an explicit new watch instead")
        now = time.time() if now is None else now
        if state["created_at"] + lifetime_seconds <= now:
            raise ValueError("new expiry is already in the past")
        state.update(lifetime_seconds=lifetime_seconds, expires_at=state["created_at"] + lifetime_seconds,
                     lifetime_approval=approval)
        save(path, state)


def bind_callback(path, receipt):
    with locked(path):
        state = load(path)
        if receipt.get("boundThreadId") != state["creator"]["thread_id"] or receipt.get("projectId") != state["creator"]["project_id"]:
            raise ValueError("callback is not bound to the job creator and project")
        if not receipt.get("scheduledTaskId") or not receipt.get("webhookUrl") or receipt.get("blockedByPolicy"):
            raise ValueError("callback unavailable: check T3 Connect and policy")
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
        if status not in {"succeeded", "failed", "cancelled", "pending"}:
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


def label_for(state_path):
    return "local.release-watch." + fingerprint(str(Path(state_path).resolve()))[:16]


def launchd_plist(wrapper, state_path):
    if not Path(wrapper).is_absolute() or not Path(state_path).is_absolute():
        raise ValueError("absolute wrapper and state paths required")
    return plistlib.dumps({"Label": label_for(state_path), "ProgramArguments": [str(wrapper), str(state_path)],
                          "StartCalendarInterval": [{"Minute": m} for m in range(0, 60, 5)],
                          "RunAtLoad": True, "ProcessType": "Background"})


def install(path, wrapper, run=subprocess.run, home=None):
    """Explicit activation only. Tick never installs or loads a job."""
    path = Path(path).resolve()
    home = Path.home() if home is None else Path(home)
    wrapper = Path(wrapper)
    if not wrapper.is_absolute() or not wrapper.is_file() or not os.access(wrapper, os.X_OK):
        raise ValueError("absolute executable wrapper required")
    with locked(path):
        state = load(path)
        if state["closed"] or not state["callback"]:
            raise ValueError("bind a creator-owned callback on an open watch before activation")
        label = label_for(path)
        plist = home / "Library/LaunchAgents" / (label + ".plist")
        if plist.exists() or plist.is_symlink() or state["launchd"]:
            raise ValueError("job already registered or destination occupied; inspect instead of replacing")
        plist.parent.mkdir(parents=True, exist_ok=True)
        raw = launchd_plist(wrapper, path)
        with plist.open("xb") as output:
            output.write(raw)
        state["launchd"] = {"label": label, "plist": str(plist), "sha256": hashlib.sha256(raw).hexdigest(),
                            "uid": os.getuid(), "status": "bootstrap-intent"}
        save(path, state)
        result = run(["/bin/launchctl", "bootstrap", "gui/" + str(os.getuid()), str(plist)],
                     capture_output=True, timeout=15, check=False)
        state["launchd"]["status"] = "loaded" if result.returncode == 0 else "bootstrap-failed"
        save(path, state)
        if result.returncode:
            raise ValueError("launchd activation failed; inspect sanitized job state")


def cleanup_launchd(path, state, run=subprocess.run, home=None):
    """Remove only this watch's validated plist, then unload as the last action.

    launchctl bootout can terminate this very process. Save all state first.
    An interrupted bootout is represented honestly as an intent, not confirmed.
    """
    job = state.get("launchd")
    home = Path.home() if home is None else Path(home)
    expected = home / "Library/LaunchAgents" / (label_for(path) + ".plist")
    if not job and expected.exists() and not expected.is_symlink():
        # Earlier generated plists predate explicit registration. Adopt only the
        # exact deterministic label and state argv, never scan unrelated agents.
        raw = expected.read_bytes()
        prior = plistlib.loads(raw)
        if prior.get("Label") != label_for(path) or len(prior.get("ProgramArguments", [])) != 2 or Path(prior["ProgramArguments"][1]).resolve() != Path(path).resolve():
            raise ValueError("legacy job identity mismatch; inspect rather than removing")
        job = {"label": label_for(path), "plist": str(expected), "uid": os.getuid(),
               "sha256": hashlib.sha256(raw).hexdigest(), "status": "legacy-adopted"}
        state["launchd"] = job
        save(path, state)
    if not job:
        state["cleanup"] = "no-job"
        save(path, state)
        return
    plist = Path(job["plist"])
    if job["label"] != label_for(path) or plist != expected or job["uid"] != os.getuid() or plist.is_symlink():
        raise ValueError("cleanup ownership mismatch; leave unrelated job intact")
    if plist.exists():
        raw = plist.read_bytes()
        if hashlib.sha256(raw).hexdigest() != job["sha256"] or plistlib.loads(raw).get("Label") != job["label"]:
            raise ValueError("job configuration changed; leave it intact for inspection")
        plist.unlink()
    state["cleanup"] = "bootout-intent"
    save(path, state)
    target = "gui/" + str(job["uid"]) + "/" + job["label"]
    result = run(["/bin/launchctl", "bootout", target], capture_output=True, timeout=15, check=False)
    if result.returncode:
        probe = run(["/bin/launchctl", "print", target], capture_output=True, timeout=10, check=False)
        state["cleanup"] = "failed-job-still-loaded" if probe.returncode == 0 else "removed"
    else:
        state["cleanup"] = "removed"
    save(path, state)


def tick(path, now=None, observation=None, delivery=None, cleanup=cleanup_launchd):
    now = time.time() if now is None else now
    with locked(path):
        state = load(path)
        if not state["closed"] and state["status"] not in TERMINAL:
            # Even after an overnight sleep past expiry, query once BEFORE expiry.
            value = observe(state) if observation is None else observation
            status, fault = value["status"], value.get("fault")
            if status == "fault":
                state["faults"] += 1
                fault = fault if fault in FAULTS else "contract"
                if (state["faults"] >= 3 or fault in {"auth", "identity", "unknown-status"}) and state["active_fault"] != fault:
                    enqueue(state, "fault:" + fault, now)
                    state["active_fault"] = fault
            else:
                if state["active_fault"] and status == "pending":
                    enqueue(state, "recovered", now)
                state["faults"], state["active_fault"] = 0, None
                state["status"], state["progress"] = status, value.get("progress")
                if status in TERMINAL:
                    enqueue(state, status, now)
            if now >= state["expires_at"] and state["status"] not in TERMINAL:
                state["status"] = "expired"
                enqueue(state, "expired", now)
            save(path, state)
        deadline = now >= state["expires_at"]
        # An activated watch owes its creator one final notification attempt,
        # even if a credential-failure wrapper omitted routine delivery flags.
        if deadline and not state["closed"] and state["callback"] and state["launchd"] and delivery is None:
            delivery = deliver_event
        if delivery and state["callback"] and not state["closed"]:
            # Final outcome must not be starved behind old unacknowledged faults.
            events = sorted(state["outbox"], key=lambda e: e["kind"] not in TERMINAL)
            for event in events[:4]:
                if not deadline and event["last_attempt"] is not None and now - event["last_attempt"] < 300:
                    continue
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
        if deadline or (state["status"] in TERMINAL and not state["outbox"]):
            state["closed"] = True
            save(path, state)
        if state["closed"] and state["cleanup"] not in {"removed", "no-job"}:
            cleanup(path, state)
        return state


def acknowledge(path, event_id, creator, cleanup=cleanup_launchd):
    with locked(path):
        state = load(path)
        if creator != state["creator"]:
            raise ValueError("acknowledgment must come from the recorded creator context")
        if event_id not in state["acknowledged"]:
            if not any(e["event_id"] == event_id for e in state["outbox"]):
                raise ValueError("unknown event")
            state["outbox"] = [e for e in state["outbox"] if e["event_id"] != event_id]
            state["acknowledged"].append(event_id)
        if state["status"] in TERMINAL and not state["outbox"]:
            state["closed"] = True
        save(path, state)
        if state["closed"] and state["cleanup"] not in {"removed", "no-job"}:
            cleanup(path, state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["init", "extend", "tick", "status", "ack", "bind", "plist", "install", "cleanup"])
    parser.add_argument("state", type=Path)
    parser.add_argument("--identity", type=Path)
    parser.add_argument("--creator", type=Path)
    parser.add_argument("--lifetime-seconds", type=int, default=DEFAULT_LIFETIME)
    parser.add_argument("--approval-file", type=Path, help="Private record of actual user approval for lifetimes over seven days")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--event-id")
    parser.add_argument("--wrapper")
    parser.add_argument("--deliver", action="store_true")
    parser.add_argument("--monitoring-fault", choices=sorted(FAULTS), help="Credential wrapper failure; record a fault and still enforce expiry")
    parser.add_argument("--checker", nargs=argparse.REMAINDER, help="Absolute checker argv; put this option last")
    args = parser.parse_args()
    approval = json.loads(args.approval_file.read_text()) if args.approval_file else None
    if args.command == "init":
        if not args.identity or not args.creator or not args.checker:
            parser.error("init requires --identity, --creator and --checker")
        if any(args.state.resolve().is_relative_to(root.resolve()) for root in [Path(tempfile.gettempdir()), Path("/tmp"), Path("/var/tmp")]):
            parser.error("use persistent private state, not a temporary directory")
        initialize(args.state, json.loads(args.identity.read_text()), json.loads(args.creator.read_text()),
                   args.checker, lifetime_seconds=args.lifetime_seconds, approval=approval)
    elif args.command == "extend":
        extend(args.state, args.lifetime_seconds, approval)
    elif args.command == "tick":
        observation = {"status": "fault", "fault": args.monitoring_fault} if args.monitoring_fault else None
        state = tick(args.state, observation=observation, delivery=deliver_event if args.deliver else None)
        print(json.dumps({k: state[k] for k in ["status", "active_fault", "expires_at", "closed", "cleanup"]} | {"unacknowledged": len(state["outbox"])}))
    elif args.command == "ack":
        if not args.creator or not args.event_id:
            parser.error("ack requires --creator and --event-id")
        acknowledge(args.state, args.event_id, json.loads(args.creator.read_text()))
    elif args.command == "bind":
        if not args.receipt:
            parser.error("bind requires a private --receipt file")
        bind_callback(args.state, json.loads(args.receipt.read_text()))
    elif args.command in {"plist", "install"}:
        if not args.wrapper:
            parser.error("absolute --wrapper required")
        if args.command == "plist":
            sys.stdout.buffer.write(launchd_plist(args.wrapper, args.state))
        else:
            install(args.state, args.wrapper)
    elif args.command == "cleanup":
        with locked(args.state):
            state = load(args.state)
            if not state["closed"]:
                raise ValueError("only closed watches can be cleaned up")
            cleanup_launchd(args.state, state)
    else:
        print(json.dumps(load(args.state), indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        print("job watch: operation failed; inspect private state/configuration (credentials redacted)", file=sys.stderr)
        sys.exit(1)
