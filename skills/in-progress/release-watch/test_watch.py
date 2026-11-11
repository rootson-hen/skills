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
        w.initialize(self.path, self.identity, self.creator, ["/usr/bin/false"], now=0, stall_seconds=300)

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

    def test_stall_and_sleep_catch_up(self):
        self.tick(progress="same")
        self.assertEqual(self.tick(now=3600, progress="same")["outbox"][0]["kind"], "fault:stalled")
        self.assertEqual(self.tick("cancelled", now=3601)["outbox"][-1]["kind"], "cancelled")

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
