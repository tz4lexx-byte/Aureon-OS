"""Deterministic tests for the Phase 1 smoke measurement harness."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPOSITORY_ROOT / "tools" / "aureon-dev"
BASELINE_PATH = REPOSITORY_ROOT / "docs/testing/phase0-review-20260724t164040z.json"


def load_cli_module():
    module_name = "aureon_dev_measurement_under_test"
    loader = importlib.machinery.SourceFileLoader(module_name, str(CLI_PATH))
    spec = importlib.util.spec_from_loader(module_name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    loader.exec_module(module)
    return module


class MeasureSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cli = load_cli_module()

    def invoke(self, arguments):
        output = io.StringIO()
        status = self.cli.main(arguments, stdout=output)
        return status, output.getvalue()

    def result(self, build_id, readiness, duration, overlay_size, status="passed"):
        return {
            "acceleration": "kvm",
            "artifacts": {"overlay": {"size_bytes": overlay_size}},
            "build_id": build_id,
            "readiness_after_seconds": readiness,
            "status": status,
            "wall_duration_seconds": duration,
        }

    def test_run_id_uses_test_smoke_validation(self):
        self.assertEqual(
            self.cli.measurement_build_ids("phase1.baseline", 1),
            ("phase1.baseline-r01",),
        )
        for invalid in ("Upper", "../escape", "has space"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(self.cli.PlanValidationError):
                    self.cli.measurement_build_ids(invalid, 1)

    def test_runs_are_bounded_integers(self):
        for valid in (1, 3, 20):
            self.assertEqual(self.cli.validate_measurement_runs(valid), valid)
        for invalid in (0, 21, True, 1.5):
            with self.subTest(invalid=invalid):
                with self.assertRaises(self.cli.PlanValidationError):
                    self.cli.validate_measurement_runs(invalid)

    def test_build_ids_are_unique_and_deterministic(self):
        expected = ("phase1-baseline-r01", "phase1-baseline-r02", "phase1-baseline-r03")
        self.assertEqual(self.cli.measurement_build_ids("phase1-baseline", 3), expected)
        self.assertEqual(self.cli.measurement_build_ids("phase1-baseline", 3), expected)
        with self.assertRaisesRegex(
            self.cli.PlanValidationError, "required '-rNN' suffix.*within 63 characters"
        ):
            self.cli.measurement_build_ids("a" * 60, 3)

    def test_dry_run_is_reproducible_and_performs_no_writes_or_commands(self):
        target = REPOSITORY_ROOT / "work/measurements/phase1-unit-no-write"
        before = target.exists()
        arguments = [
            "measure-smoke",
            "--run-id",
            "phase1-unit-no-write",
            "--runs",
            "3",
            "--baseline",
            str(BASELINE_PATH.relative_to(REPOSITORY_ROOT)),
            "--dry-run",
        ]
        with mock.patch.object(
            self.cli.subprocess, "run", side_effect=AssertionError("must not invoke a command")
        ), mock.patch.object(
            self.cli.subprocess, "Popen", side_effect=AssertionError("must not invoke QEMU")
        ):
            first = self.invoke(arguments)
            second = self.invoke(arguments)
        self.assertEqual(first, second)
        self.assertEqual(first[0], 0)
        self.assertFalse(json.loads(first[1])["execution"]["writes"])
        self.assertEqual(target.exists(), before)

    def test_loads_phase_zero_baseline(self):
        baseline, path = self.cli.load_measurement_baseline(BASELINE_PATH)
        self.assertEqual(path, "docs/testing/phase0-review-20260724t164040z.json")
        self.assertEqual(baseline["readiness_after_seconds"], 63.733)
        self.assertEqual(baseline["wall_duration_seconds"], 75.488)

    def test_aggregates_three_results_and_statistics(self):
        baseline = {"readiness_after_seconds": 10.0, "wall_duration_seconds": 20.0}
        results = [
            self.result("sample-r01", 8.0, 18.0, 100),
            self.result("sample-r02", 10.0, 20.0, 200),
            self.result("sample-r03", 12.0, 28.0, 300),
        ]
        measurement = self.cli.aggregate_measurement(
            "sample", 3, "docs/testing/baseline.json", baseline, results
        )
        summary = measurement["summary"]
        self.assertEqual(
            (summary["requested"], summary["completed"], summary["passed"], summary["failed"]),
            (3, 3, 3, 0),
        )
        self.assertEqual(
            summary["duration_seconds"],
            {"minimum": 18.0, "maximum": 28.0, "mean": 22.0, "median": 20.0},
        )
        self.assertEqual(
            summary["readiness_seconds"],
            {"minimum": 8.0, "maximum": 12.0, "mean": 10.0, "median": 10.0},
        )
        self.assertEqual(summary["overlay_size_bytes"]["median"], 200.0)
        self.assertEqual(summary["variation_percent_from_baseline"]["readiness_mean"], 0.0)
        self.assertEqual(summary["variation_percent_from_baseline"]["wall_duration_mean"], 10.0)
        self.assertEqual(summary["status"], "passed")

    def test_failed_run_sets_overall_failed(self):
        baseline = {"readiness_after_seconds": 10.0, "wall_duration_seconds": 20.0}
        results = [
            self.result("sample-r01", 10.0, 20.0, 100),
            self.result("sample-r02", None, None, 120, status="failed"),
        ]
        measurement = self.cli.aggregate_measurement(
            "sample", 2, "docs/testing/baseline.json", baseline, results
        )
        self.assertEqual(measurement["summary"]["failed"], 1)
        self.assertEqual(measurement["summary"]["status"], "failed")

    def test_json_is_sorted_reproducible_and_newline_terminated(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            self.cli._write_json_once(path, {"z": 1, "a": 2})
            self.assertEqual(path.read_bytes(), b'{\n  "a": 2,\n  "z": 1\n}\n')

    def test_rejects_private_absolute_paths(self):
        for value in ({"path": "/home/alice/private"}, {"path": r"C:\Users\alice\private"}):
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    self.cli.PlanValidationError, "absolute private path"
                ):
                    self.cli._reject_private_absolute_paths(value)

    def test_plan_preserves_isolation_policies(self):
        plan = self.cli.create_measurement_plan(
            "phase1-isolation", 3, BASELINE_PATH
        )
        constraints = plan["constraints"]
        self.assertEqual(constraints["guest_network"], "none")
        self.assertFalse(constraints["host_directories_mounted_in_guest"])
        self.assertFalse(constraints["physical_block_devices_accessed"])
        self.assertFalse(constraints["windows_install_or_boot_changes"])
        self.assertIn("copy-on-write", constraints["base_storage_mode"])
        self.assertEqual(constraints["privilege_escalation"], "never")

    def test_execute_without_privileges_fails_before_writing_or_running(self):
        plan = self.cli.create_measurement_plan(
            "phase1-unprivileged", 1, BASELINE_PATH
        )
        baseline, path = self.cli.load_measurement_baseline(BASELINE_PATH)
        with mock.patch.object(self.cli.os, "geteuid", return_value=1000), mock.patch.object(
            self.cli, "execute_smoke_plan", side_effect=AssertionError("must not execute")
        ), mock.patch.object(
            self.cli.Path, "mkdir", side_effect=AssertionError("must not write")
        ):
            with self.assertRaisesRegex(
                self.cli.SmokeRunnerError, "automatic privilege elevation"
            ):
                self.cli.execute_measurement(plan, baseline, path)


if __name__ == "__main__":
    unittest.main()
