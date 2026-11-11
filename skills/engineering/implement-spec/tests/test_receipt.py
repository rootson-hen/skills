import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check-receipt.py"
spec = importlib.util.spec_from_file_location("receipt", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.root = self.base / "repo"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Test")
        (self.root / "test.txt").write_text("source")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        identity = m.source_identity(self.root, "example/repo")
        self.plan = {"schema_version": 1, "plan_id": "test-plan", "source": identity,
                     "dependencies": {"source_digest": identity["digest"], "artifacts": []},
                     "jobs": [{"id": "test", "argv": ["test-command"], "test_reruns": 3,
                               "allowed_skips": [], "expected_suites": [{"name": "Suite", "min_tests": 1}]}]}
        self.report = self.base / "TEST-Suite.xml"
        self.report.write_text('<testsuite name="Suite" tests="1" failures="0" errors="0" skipped="0"><testcase classname="Suite" name="works"/></testsuite>')
        (self.base / "command.log").write_text("ok")
        self.receipt = {"schema_version": 1, "kind": "validation-receipt", "run_id": "run-1", "plan_sha256": m.canonical(self.plan),
                        "finalized": True, "owned_processes_finished": True, "active_jobs": [],
                        "source_before": identity, "source_after": identity,
                        "dependencies_before": self.plan["dependencies"], "dependencies_after": self.plan["dependencies"],
                        "jobs": [{"id": "test", "argv": ["test-command"], "state": "finished", "exit_code": 0, "test_reruns": 3,
                                  "owned_processes_finished": True, "started_ns": 1, "finished_ns": 3,
                                  "log": {"path": "command.log", "sha256": m.digest(self.base / "command.log")}, "reports": []}]}
        self.refresh()

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.root), *args], check=True, stdout=subprocess.DEVNULL)

    def refresh(self):
        self.receipt["jobs"][0]["reports"] = [{"path": self.report.name, "sha256": m.digest(self.report), "fresh": True,
                                               "mtime_ns": 2, "suites": m.parse_report(self.report)}]
        self.receipt["plan_sha256"] = m.canonical(self.plan)

    def accept(self, **kwargs):
        return m.check(self.plan, self.receipt, self.base, **kwargs)

    def test_accepts_exact_evidence(self):
        self.assertEqual(self.accept()["classification"], "first-attempt-green")

    def test_rejects_unfinished_and_wrong_identity(self):
        for field, value in (("finalized", False), ("active_jobs", ["pending"]), ("owned_processes_finished", False), ("plan_sha256", "wrong")):
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.receipt)
                receipt[field] = value
                with self.assertRaises(m.Invalid):
                    m.check(self.plan, receipt, self.base)

    def test_rejects_changed_tracked_or_untracked_source(self):
        (self.root / "new-test.txt").write_text("new")
        with self.assertRaises(m.Invalid):
            self.accept()
        (self.root / "new-test.txt").unlink()
        (self.root / "test.txt").write_text("changed")
        with self.assertRaises(m.Invalid):
            self.accept()

    def test_ignored_inputs_and_symlink_targets_are_fingerprinted(self):
        (self.root / ".gitignore").write_text("fixture\n")
        (self.root / "fixture").write_text("one")
        (self.root / "link").symlink_to("fixture")
        first = m.source_identity(self.root, "example/repo", ["fixture"])
        (self.root / "fixture").write_text("two")
        self.assertNotEqual(first, m.source_identity(self.root, "example/repo", ["fixture"]))

    def test_rejects_exit_even_when_xml_green(self):
        self.receipt["jobs"][0]["exit_code"] = 1
        with self.assertRaises(m.Invalid):
            self.accept()

    def test_rejects_xml_failure_even_when_exit_green(self):
        self.report.write_text('<testsuite name="Suite" tests="1" failures="1"><testcase name="works"><failure/></testcase></testsuite>')
        self.refresh()
        with self.assertRaises(m.Invalid):
            self.accept()

    def test_all_retry_tags_are_not_first_attempt_green(self):
        for tag in ("flakyFailure", "rerunFailure", "flakyError", "rerunError"):
            with self.subTest(tag=tag):
                self.report.write_text(f'<testsuite name="Suite" tests="1"><testcase name="works"><{tag}/></testcase></testsuite>')
                self.refresh()
                with self.assertRaises(m.Invalid):
                    self.accept()
                self.assertEqual(self.accept(allow_retries=True)["classification"], "recovered-after-retries")

    def test_only_named_allowed_skips(self):
        self.report.write_text('<testsuite name="Suite" tests="2" skipped="1"><testcase classname="Suite" name="works"/><testcase classname="Suite" name="db2only"><skipped/></testcase></testsuite>')
        self.refresh()
        with self.assertRaises(m.Invalid):
            self.accept()
        self.plan["jobs"][0]["allowed_skips"] = ["Suite#db2only"]
        self.refresh()
        self.assertTrue(self.accept()["accepted"])

    def test_zero_wrong_stale_missing_tampered_reports_rejected(self):
        for mutation in (lambda r: r["jobs"][0].update(reports=[]),
                         lambda r: r["jobs"][0]["reports"][0].update(fresh=False),
                         lambda r: r["jobs"][0]["reports"][0].update(mtime_ns=0),
                         lambda r: r["jobs"][0]["reports"][0].update(sha256="wrong"),
                         lambda r: r["jobs"][0].update(argv=["other"]),
                         lambda r: r["jobs"][0].update(id="unexpected")):
            receipt = copy.deepcopy(self.receipt)
            mutation(receipt)
            with self.assertRaises(m.Invalid):
                m.check(self.plan, receipt, self.base)
        self.report.write_text('<testsuite name="Other" tests="0"/>')
        self.refresh()
        with self.assertRaises(m.Invalid):
            self.accept()

    def test_dependencies_change_is_rejected(self):
        jar = self.base / "dependency.jar"
        jar.write_text("old")
        self.plan["dependencies"]["artifacts"] = [{"path": str(jar), "sha256": m.digest(jar)}]
        self.refresh()
        jar.write_text("new")
        with self.assertRaises(m.Invalid):
            self.accept()

    def test_malformed_plan_and_xml(self):
        self.plan["jobs"][0]["expected_suites"][0]["min_tests"] = 0
        with self.assertRaises(m.Invalid):
            m.validate_plan(self.plan)
        self.report.write_text('<!DOCTYPE x [<!ENTITY x "value">]><testsuite/>')
        with self.assertRaises(m.Invalid):
            m.parse_report(self.report)

    def test_cli_rejects_missing_receipt(self):
        result = subprocess.run(["python3", "-I", str(SCRIPT), "check", "--plan", "/missing", "--receipt", "/missing"], capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)["accepted"])


if __name__ == "__main__":
    unittest.main()
