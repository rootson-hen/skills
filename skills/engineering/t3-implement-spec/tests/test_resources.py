"""Command-boundary tests with simulated OS readings and a fake Cargo process."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
GUARD = SCRIPTS / "cargo-resource-guard.py"
WATCH = SCRIPTS / "resource-watch.py"


class ResourceCommands(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pressure = self.root / "pressure"
        self.pressure.write_text("1")
        self.probe = self.root / "probe.py"
        self.probe.write_text("import pathlib,sys; print(pathlib.Path(sys.argv[1]).read_text())\n")
        self.cargo = self.root / "cargo.py"
        self.cargo.write_text(
            "import json,os,sys\n"
            "print(json.dumps({'args':sys.argv[1:], 'jobs':os.environ.get('CARGO_BUILD_JOBS'), "
            "'nice':os.getpriority(os.PRIO_PROCESS,0)}),flush=True)\n"
        )
        self.sample_origin = time.time() - 1000
        self.config = {
            "lock_path": str(self.root / "shared.lock"),
            "state_path": str(self.root / "state.json"),
            "pressure_command": [sys.executable, "-I", str(self.probe), str(self.pressure)],
            "cargo_command": [sys.executable, "-I", str(self.cargo)],
        }
        (self.root / "state.json").write_text(json.dumps({
            "timestamp": time.time(), "pressure": "normal", "sustained_swap_growth": False,
        }))
        self.native_pressure = self.root / "native-pressure"
        self.native_pressure.write_text("1")
        self.driver = self.root / "guard-driver.py"
        self.driver.write_text(
            "import pathlib,runpy,subprocess,sys\n"
            "from unittest.mock import patch\n"
            "guard,native=sys.argv[1:3]; sys.argv=[guard,*sys.argv[3:]]\n"
            "real_run=subprocess.run\n"
            "def run(cmd,*a,**kw):\n"
            "    if cmd==['/usr/sbin/sysctl','-n','kern.memorystatus_vm_pressure_level']:\n"
            "        return subprocess.CompletedProcess(cmd,0,pathlib.Path(native).read_text(),'')\n"
            "    return real_run(cmd,*a,**kw)\n"
            "with patch('subprocess.run',run), patch('sys.platform','darwin'):\n"
            "    runpy.run_path(guard,run_name='__main__')\n"
        )
        self.config_path = self.root / "config.json"
        self.env = dict(os.environ, T3_CARGO_GUARD_CONFIG=str(self.config_path), CARGO_BUILD_JOBS="99")

    def run_guard(self, *args):
        self.config_path.write_text(json.dumps(self.config))
        return subprocess.run([sys.executable, "-I", str(self.driver), str(GUARD), str(self.native_pressure), *args], env=self.env,
                              text=True, capture_output=True, timeout=10)

    def test_normal_pressure_bounds_jobs_lowers_priority_and_preserves_arguments(self):
        initial_nice = os.getpriority(os.PRIO_PROCESS, 0)
        result = self.run_guard("test", "--locked", "--", "--jobs=99")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "args": ["test", "--locked", "--", "--jobs=99"],
            "jobs": "3", "nice": min(19, initial_nice + 10),
        })

    def test_warning_throttles_unknown_limits_and_critical_defers(self):
        for level, jobs, status in (("2", "2", 0), ("?", "1", 0), ("4", None, 75)):
            with self.subTest(level=level):
                self.pressure.write_text(level)
                result = self.run_guard("check", "--locked")
                self.assertEqual(result.returncode, status, result.stderr)
                if jobs:
                    self.assertEqual(json.loads(result.stdout)["jobs"], jobs)
                else:
                    self.assertEqual(result.stdout, "")

    def test_stale_missing_malformed_and_future_state_use_unknown_budget(self):
        state = self.root / "state.json"
        samples = (None, "not json", json.dumps({"timestamp": time.time() - 300,
                   "pressure": "normal", "sustained_swap_growth": False}),
                   json.dumps({"timestamp": time.time() + 300, "pressure": "normal",
                               "sustained_swap_growth": False}))
        for sample in samples:
            with self.subTest(sample=sample):
                if state.exists(): state.unlink()
                if sample is not None: state.write_text(sample)
                result = self.run_guard("check")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["jobs"], "1")
        self.pressure.write_text("4")
        self.assertEqual(self.run_guard("check").returncode, 75)

    def test_fresh_critical_or_sustained_swap_state_defers_without_launch(self):
        for pressure, swap in (("critical", False), ("normal", True)):
            (self.root / "state.json").write_text(json.dumps({
                "timestamp": time.time(), "pressure": pressure, "sustained_swap_growth": swap,
            }))
            result = self.run_guard("test")
            self.assertEqual(result.returncode, 75, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_explicit_job_and_inline_config_overrides_are_rejected(self):
        for args in (("check", "--jobs", "99"), ("check", "-j99"), ("check", "-qj99"), ("check", "-qj", "99"),
                     ("check", "--jobs=0"), ("check", "--config=build.jobs=99")):
            with self.subTest(args=args):
                result = self.run_guard(*args)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")

    def test_non_job_short_option_values_preserve_arguments(self):
        args = ("check", "-pjson-client", "-Fjson", "-qpjobs")
        result = self.run_guard(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["args"], list(args))

    def test_configurable_budgets_cannot_disable_deferral(self):
        self.config["jobs"] = {"normal": 2, "warning": 1, "unknown": 1}
        self.assertEqual(json.loads(self.run_guard("check").stdout)["jobs"], "2")
        self.pressure.write_text("4")
        self.assertEqual(self.run_guard("check").returncode, 75)
        self.config["defer_on_critical"] = False
        self.assertEqual(self.run_guard("check").returncode, 2)

    def test_cargo_exit_and_signal_status_are_preserved(self):
        self.cargo.write_text("import sys; sys.exit(42)\n")
        self.assertEqual(self.run_guard("check").returncode, 42)
        self.cargo.write_text("import os,signal; os.kill(os.getpid(),signal.SIGTERM)\n")
        self.assertEqual(self.run_guard("check").returncode, 143)
        self.cargo.write_text("pass\n")
        self.assertEqual(self.run_guard("check").returncode, 0)

    def start_guard(self, cwd=None):
        self.config_path.write_text(json.dumps(self.config))
        proc = subprocess.Popen([sys.executable, "-I", str(self.driver), str(GUARD), str(self.native_pressure), "check"],
                                cwd=cwd, env=self.env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(lambda: self.cleanup_process(proc))
        return proc

    @staticmethod
    def cleanup_process(proc):
        if proc.poll() is None:
            proc.terminate()
        proc.communicate(timeout=5)

    def test_shared_lock_serializes_separate_worktrees_and_releases_after_signal(self):
        import signal
        self.cargo.write_text("import time; print('started',flush=True); time.sleep(20)\n")
        one_dir, two_dir = self.root / "one", self.root / "two"
        one_dir.mkdir(); two_dir.mkdir()
        first = self.start_guard(one_dir)
        self.assertEqual(first.stdout.readline().strip(), "started")
        second = self.start_guard(two_dir)
        self.assertIn("waiting", second.stderr.readline())
        import select
        self.assertEqual(select.select([second.stdout], [], [], 0.2)[0], [])
        first.send_signal(signal.SIGTERM)
        first.communicate(timeout=5)
        self.assertEqual(first.returncode, 143)
        self.assertEqual(second.stdout.readline().strip(), "started")
        second.send_signal(signal.SIGINT)
        second.communicate(timeout=5)
        self.assertEqual(second.returncode, 130)
        self.cargo.write_text("pass\n")
        self.assertEqual(self.run_guard("check").returncode, 0)

    def test_hard_killed_guard_does_not_release_running_child_slot(self):
        import select
        self.cargo.write_text("import time; print('started',flush=True); time.sleep(1)\n")
        first = self.start_guard()
        self.assertEqual(first.stdout.readline().strip(), "started")
        first.kill()
        second = self.start_guard()
        self.assertIn("waiting", second.stderr.readline())
        self.assertEqual(select.select([second.stdout], [], [], 0.2)[0], [])
        second.communicate(timeout=5)
        self.assertEqual(second.returncode, 0)
        first.communicate(timeout=5)

    def run_watch(self, samples, *extra):
        fixture = self.root / "samples.jsonl"
        fixture.write_text("".join(json.dumps(dict(s, timestamp=s["timestamp"] + self.sample_origin))
                                   + "\n" for s in samples))
        sampler = self.root / "sampler.py"
        sampler.write_text(
            "import pathlib,sys\n"
            "p=pathlib.Path(sys.argv[1]); rows=p.read_text().splitlines(); "
            "print(rows[0]); p.write_text('\\n'.join(rows[1:])+'\\n')\n"
        )
        command = [sys.executable, "-I", str(sampler), str(fixture)]
        return subprocess.run([sys.executable, "-I", str(WATCH),
            "--state", str(self.root / "state.json"), "--log", str(self.root / "telemetry.jsonl"),
            "--interval", "0.01", "--samples", str(len(samples)),
            "--sample-command-json", json.dumps(command), *extra], text=True,
            capture_output=True, timeout=10)

    def test_watch_is_quiet_for_initial_healthy_and_unchanged_warning(self):
        result = self.run_watch([
            {"timestamp": 100, "pressure": "normal", "swap_used_mib": 0},
            {"timestamp": 130, "pressure": "normal", "swap_used_mib": 0},
            {"timestamp": 160, "pressure": "warning", "swap_used_mib": 0},
            {"timestamp": 190, "pressure": "warning", "swap_used_mib": 0},
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        events = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual([e["event"] for e in events], ["policy_changed"])
        self.assertEqual(events[0]["pressure"], "warning")
        telemetry = (self.root / "telemetry.jsonl").read_text().splitlines()
        self.assertEqual(len(telemetry), 4)
        self.assertEqual(json.loads((self.root / "state.json").read_text())["pressure"], "warning")

    def test_swap_deferral_and_recovery_notify_only_on_policy_changes(self):
        result = self.run_watch([
            {"timestamp": 100 + 30*i, "pressure": "normal", "swap_used_mib": swap}
            for i, swap in enumerate((0, 512, 1024, 1536, 2048, 2048, 2048))
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([json.loads(s)["event"] for s in result.stdout.splitlines()],
                         ["builds_deferred", "builds_resumed"])
        state = json.loads((self.root / "state.json").read_text())
        self.assertFalse(state["sustained_swap_growth"])

    def test_first_critical_notifies_once_and_sampler_failure_is_actionable(self):
        result = self.run_watch([
            {"timestamp": 100, "pressure": "critical", "swap_used_mib": 0},
            {"timestamp": 130, "pressure": "critical", "swap_used_mib": 0},
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([json.loads(s)["event"] for s in result.stdout.splitlines()],
                         ["builds_deferred"])
        result = self.run_watch([{"timestamp": 100, "pressure": "invalid", "swap_used_mib": 0}])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["event"], "sampler_failed")

    def test_short_swap_spikes_and_slow_accumulation_do_not_defer(self):
        for values in ((0, 512, 512, 1024, 1024), (0, 100, 200, 300, 400)):
            (self.root / "state.json").unlink(missing_ok=True)
            result = self.run_watch([
                {"timestamp": 100 + 30*i, "pressure": "normal", "swap_used_mib": swap}
                for i, swap in enumerate(values)
            ])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_bounded_restarts_preserve_swap_history_and_notification_identity(self):
        first = self.run_watch([
            {"timestamp": 100 + 30*i, "pressure": "warning", "swap_used_mib": 512*i}
            for i in range(3)
        ])
        self.assertEqual([json.loads(s)["event"] for s in first.stdout.splitlines()], ["policy_changed"])
        second = self.run_watch([
            {"timestamp": 100 + 30*i, "pressure": "warning", "swap_used_mib": 512*i}
            for i in range(3, 6)
        ])
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual([json.loads(s)["event"] for s in second.stdout.splitlines()], ["builds_deferred"])
        self.assertTrue(json.loads((self.root / "state.json").read_text())["sustained_swap_growth"])
        third = self.run_watch([{"timestamp": 280, "pressure": "warning", "swap_used_mib": 3072}])
        self.assertEqual(third.stdout, "")

    def test_stale_or_corrupt_sampler_history_restarts_conservatively(self):
        self.run_watch([
            {"timestamp": 100 + 30*i, "pressure": "normal", "swap_used_mib": 512*i}
            for i in range(4)
        ])
        state_path = self.root / "state.json"
        self.assertTrue(json.loads(state_path.read_text())["sustained_swap_growth"])
        result = self.run_watch([{"timestamp": 400, "pressure": "normal", "swap_used_mib": 3584}])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(state_path.read_text())["sustained_swap_growth"])
        state_path.write_text("malformed")
        result = self.run_watch([{"timestamp": 430, "pressure": "normal", "swap_used_mib": 3584}])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_changed_detector_settings_reset_incompatible_history(self):
        self.run_watch([
            {"timestamp": 100 + 30*i, "pressure": "normal", "swap_used_mib": 512*i}
            for i in range(3)
        ])
        result = self.run_watch([{"timestamp": 190, "pressure": "normal", "swap_used_mib": 1536}],
                                "--rapid-samples", "5")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertFalse(json.loads((self.root / "state.json").read_text())["sustained_swap_growth"])

    def test_warning_restart_and_already_deferred_reason_changes_are_silent(self):
        self.run_watch([{"timestamp": 100, "pressure": "warning", "swap_used_mib": 0}])
        repeat = self.run_watch([{"timestamp": 130, "pressure": "warning", "swap_used_mib": 0}])
        self.assertEqual(repeat.stdout, "")
        (self.root / "state.json").unlink()
        result = self.run_watch([
            {"timestamp": 100 + 30*i, "pressure": "critical", "swap_used_mib": 512*i}
            for i in range(5)
        ])
        self.assertEqual([json.loads(s)["event"] for s in result.stdout.splitlines()], ["builds_deferred"])

    def test_configured_probe_cannot_weaken_native_critical_pressure(self):
        self.native_pressure.write_text("4")
        self.pressure.write_text("1")
        result = self.run_guard("check")
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_state_pressure_cannot_lower_live_pressure(self):
        (self.root / "state.json").write_text(json.dumps({
            "timestamp": time.time(), "pressure": "normal", "sustained_swap_growth": False,
        }))
        self.pressure.write_text("4")
        self.assertEqual(self.run_guard("check").returncode, 75)
        self.config["jobs"] = {"normal": 3, "warning": 0, "unknown": 1}
        self.assertEqual(self.run_guard("check").returncode, 2)


if __name__ == "__main__":
    unittest.main()
