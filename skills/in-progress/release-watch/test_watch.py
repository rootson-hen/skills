import importlib.util
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("watch", Path(__file__).with_name("watch.py"))
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


class WatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "state.json"
        self.identity = {"release_id": "synthetic", "run_id": "run-1", "sha": "a" * 40}
        self.creator = {"environment_id": "env", "project_id": "project", "thread_id": "creator"}
        w.initialize(self.path, self.identity, self.creator, ["/usr/bin/false"], now=0)

    def tick(self, status="pending", now=1, **kwargs):
        return w.tick(self.path, now=now, observation={"status": status, **kwargs})

    def test_pending_has_no_events_and_restart_preserves_identity(self):
        self.tick(progress="one")
        state = self.tick(now=100, progress="one")
        self.assertEqual(state["outbox"], [])
        self.assertEqual(state["identity"], self.identity)
        with self.assertRaises(ValueError):
            w.initialize(self.path, self.identity, self.creator, ["/usr/bin/false"])

    def test_terminal_deduplicated_and_retried_until_agent_ack(self):
        receipt = {"projectId": "project", "boundThreadId": "creator", "scheduledTaskId": "task", "webhookUrl": "https://example.invalid/token"}
        w.bind_callback(self.path, receipt)
        calls = []
        def deliver(state, event):
            # Delivery must see its durable event before sending.
            self.assertEqual(json.loads(self.path.read_text())["outbox"][0]["event_id"], event["event_id"])
            calls.append(event["event_id"])
            return "accepted-unacknowledged"
        state = self.tick("succeeded")
        event = state["outbox"][0]["event_id"]
        w.tick(self.path, now=10, delivery=deliver)
        w.tick(self.path, now=20, delivery=deliver)
        w.tick(self.path, now=311, delivery=deliver)
        self.assertEqual(calls, [event, event])
        w.tick(self.path, now=1811, delivery=deliver)
        self.assertEqual(json.loads(self.path.read_text())["outbox"][0]["generation"], 1)
        self.assertNotIn("example.invalid", self.path.read_text())
        w.acknowledge(self.path, event, self.creator)
        w.acknowledge(self.path, event, self.creator)
        self.assertEqual(self.tick("succeeded", now=700)["outbox"], [])

    def test_wrong_callback_thread_project_and_missing_tunnel_rejected(self):
        for receipt in [{"projectId": "project", "boundThreadId": "wrong", "webhookUrl": "https://example.invalid", "scheduledTaskId": "t"},
                        {"projectId": "wrong", "boundThreadId": "creator", "webhookUrl": "https://example.invalid", "scheduledTaskId": "t"},
                        {"projectId": "project", "boundThreadId": "creator", "scheduledTaskId": "t"}]:
            with self.assertRaises(ValueError):
                w.bind_callback(self.path, receipt)

    def test_faults_never_success_and_fault_deduplication(self):
        for now in [1, 2]:
            self.assertEqual(self.tick("fault", now, fault="network")["outbox"], [])
        state = self.tick("fault", 3, fault="network")
        self.assertEqual(state["outbox"][0]["kind"], "fault:network")
        self.assertEqual(len(self.tick("fault", 4, fault="network")["outbox"]), 1)
        self.assertEqual(state["status"], "pending")
        self.assertEqual(self.tick("pending", 5, progress="ok")["outbox"][-1]["kind"], "recovered")

    def test_no_progress_does_not_expire_before_absolute_lifetime(self):
        self.tick(progress="same")
        self.assertEqual(self.tick(now=6 * 3600 - 1, progress="same")["outbox"], [])

    def test_overnight_wake_checks_success_before_expiring_and_cleans(self):
        calls = []
        with patch.object(w, "observe", side_effect=lambda state: calls.append("checked") or {"status": "succeeded"}):
            state = w.tick(self.path, now=12 * 3600)
        self.assertEqual(calls, ["checked"])
        self.assertEqual(state["status"], "succeeded")
        self.assertEqual([e["kind"] for e in state["outbox"]], ["succeeded"])
        self.assertTrue(state["closed"])
        self.assertEqual(state["cleanup"], "no-job")

    def test_expiry_checks_once_then_closes_without_deleting_pending_event(self):
        state = self.tick(now=7 * 3600)
        self.assertEqual(state["status"], "expired")
        self.assertEqual(state["outbox"][-1]["kind"], "expired")
        self.assertTrue(state["closed"])
        with patch.object(w, "observe", side_effect=AssertionError("closed watch checked again")):
            w.tick(self.path, now=8 * 3600)
        self.assertEqual(len(w.load(self.path)["outbox"]), 1)

    def test_lifetime_extensions_and_long_lifetime_permission(self):
        w.extend(self.path, 2 * 86400, now=100)
        self.assertEqual(w.load(self.path)["expires_at"], 2 * 86400)
        with self.assertRaisesRegex(ValueError, "user approval"):
            w.extend(self.path, 8 * 86400, now=100)
        approval = {"lifetime_seconds": 8 * 86400, "user_message": "Approve this eight-day fixture watch"}
        w.extend(self.path, 8 * 86400, approval, now=100)
        self.assertEqual(w.load(self.path)["lifetime_approval"], approval)

    def test_provider_identity_accepts_numeric_pr_ids(self):
        path = Path(self.tmp.name) / "pr.json"
        state = w.initialize(path, {"pr": 123, "app_id": 42, "sha": "a" * 40}, self.creator, ["/usr/bin/false"])
        self.assertEqual(state["identity"]["pr"], 123)

    def test_cleanup_removes_only_own_plist_and_unloads(self):
        home = Path(self.tmp.name) / "home"
        wrapper = Path(self.tmp.name) / "wrapper"
        wrapper.write_text("#!/bin/sh\nexit 0\n")
        wrapper.chmod(0o700)
        w.bind_callback(self.path, {"projectId": "project", "boundThreadId": "creator", "scheduledTaskId": "task", "webhookUrl": "https://example.invalid/token"})
        calls = []
        def run(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, b"", b"")
        w.install(self.path, wrapper, run=run, home=home)
        state = w.load(self.path)
        plist = Path(state["launchd"]["plist"])
        other = plist.with_name("unrelated.plist")
        other.write_text("unrelated")
        self.assertTrue(plist.exists())
        w.tick(self.path, now=7 * 3600, observation={"status": "pending"},
               cleanup=lambda path, state: w.cleanup_launchd(path, state, run, home))
        self.assertFalse(plist.exists())
        self.assertEqual(other.read_text(), "unrelated")
        self.assertEqual(calls[-1][1], "bootout")
        self.assertEqual(w.load(self.path)["cleanup"], "removed")

    def test_expiry_attempts_delivery_then_removes_job_even_if_offline(self):
        w.bind_callback(self.path, {"projectId": "project", "boundThreadId": "creator", "scheduledTaskId": "task", "webhookUrl": "https://example.invalid/token"})
        order = []
        def delivery(state, event):
            order.append("delivered:" + event["kind"])
            return "delivery-failed"
        def cleanup(path, state):
            order.append("cleanup")
            state["cleanup"] = "removed"
            w.save(path, state)
        state = w.tick(self.path, now=7 * 3600, observation={"status": "pending"}, delivery=delivery, cleanup=cleanup)
        self.assertEqual(order, ["delivered:expired", "cleanup"])
        self.assertTrue(state["closed"])
        self.assertEqual(state["outbox"][0]["delivery"], "delivery-failed")

    def test_legacy_state_adopts_only_exact_owned_plist_for_cleanup(self):
        state = w.load(self.path)
        state["schema_version"] = 1
        state["stall_seconds"] = 21600
        for key in ["expires_at", "lifetime_seconds", "launchd", "closed", "cleanup"]:
            state.pop(key)
        w.save(self.path, state)
        home = Path(self.tmp.name) / "home"
        plist = home / "Library/LaunchAgents" / (w.label_for(self.path) + ".plist")
        plist.parent.mkdir(parents=True)
        plist.write_bytes(w.launchd_plist("/fixture/wrapper", str(self.path)))
        run = lambda argv, **kwargs: subprocess.CompletedProcess(argv, 0, b"", b"")
        w.tick(self.path, now=7 * 3600, observation={"status": "pending"},
               cleanup=lambda path, state: w.cleanup_launchd(path, state, run, home))
        self.assertFalse(plist.exists())
        self.assertEqual(w.load(self.path)["cleanup"], "removed")

    def test_changed_plist_is_never_removed(self):
        state = w.load(self.path)
        home = Path(self.tmp.name) / "home"
        plist = home / "Library/LaunchAgents" / (w.label_for(self.path) + ".plist")
        plist.parent.mkdir(parents=True)
        plist.write_bytes(b"changed")
        state["launchd"] = {"label": w.label_for(self.path), "plist": str(plist), "uid": w.os.getuid(), "sha256": "old"}
        with self.assertRaisesRegex(ValueError, "changed"):
            w.cleanup_launchd(self.path, state, home=home)
        self.assertTrue(plist.exists())

    def test_adapter_rejects_wrong_identity_unknown_auth_and_invalid_output(self):
        state = json.loads(self.path.read_text())
        for payload, expected in [({"schema_version": 1, "identity": {}, "status": "succeeded"}, "identity"),
                                  ({"schema_version": 1, "identity": self.identity, "status": "new-state"}, "unknown-status"),
                                  ({"schema_version": 1, "identity": self.identity, "status": "fault", "fault": "auth"}, "auth")]:
            with patch.object(w.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps(payload), "secret")):
                self.assertEqual(w.observe(state), {"status": "fault", "fault": expected})
        with patch.object(w.subprocess, "run", side_effect=subprocess.TimeoutExpired([], 90)):
            self.assertEqual(w.observe(state)["fault"], "timeout")

    def test_calendar_output_is_unarmed_and_secret_free(self):
        value = plistlib.loads(w.launchd_plist("/opt/private-wrapper", "/private/state.json"))
        self.assertEqual(value["StartCalendarInterval"], [{"Minute": m} for m in range(0, 60, 5)])
        self.assertNotIn("EnvironmentVariables", value)
        self.assertNotIn("KeepAlive", value)

    def test_wrong_injected_callback_url_never_sends(self):
        w.bind_callback(self.path, {"projectId": "project", "boundThreadId": "creator", "scheduledTaskId": "task", "webhookUrl": "https://example.invalid/right"})
        state = self.tick("succeeded")
        with patch.dict(w.os.environ, {"RELEASE_CALLBACK_URL": "https://example.invalid/wrong"}):
            self.assertEqual(w.deliver_event(state, state["outbox"][0]), "callback-owner-mismatch")

    def test_mismatched_ack_rejected(self):
        state = self.tick("failed")
        with self.assertRaises(ValueError):
            w.acknowledge(self.path, state["outbox"][0]["event_id"], {**self.creator, "thread_id": "other"})


if __name__ == "__main__":
    unittest.main()
