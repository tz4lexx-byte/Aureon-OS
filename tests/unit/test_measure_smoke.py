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
            "--reuse-base",
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
        self.assertTrue(json.loads(first[1])["base_reuse_enabled"])
        self.assertEqual(target.exists(), before)

    def test_reuse_plan_has_one_shared_base_and_three_distinct_overlays(self):
        plan = self.cli.create_measurement_plan(
            "phase1-shared", 3, BASELINE_PATH, reuse_base=True
        )

        overlays = [run["overlay_path"] for run in plan["runs"]]
        backings = [run["overlay_backing_path"] for run in plan["runs"]]
        self.assertEqual(len(set(overlays)), 3)
        self.assertEqual(set(backings), {plan["shared_base_path"]})
        self.assertEqual(
            plan["shared_base_path"], "images/phase1-shared-r01/aureon-base.qcow2"
        )

    def test_reuse_plan_uses_only_relative_evidence_paths(self):
        plan = self.cli.create_measurement_plan(
            "phase1-relative", 3, BASELINE_PATH, reuse_base=True
        )

        self.cli._reject_private_absolute_paths(plan)
        self.assertFalse(Path(plan["shared_base_path"]).is_absolute())
        for run in plan["runs"]:
            self.assertFalse(Path(run["overlay_path"]).is_absolute())
            self.assertFalse(Path(run["overlay_backing_path"]).is_absolute())

    def test_shared_base_hash_change_is_rejected_immediately(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / "base.qcow2"
            base.write_bytes(b"immutable")
            expected = self.cli._sha256_file(base)
            self.assertEqual(self.cli.verify_shared_base_hash(base, expected), expected)
            base.write_bytes(b"changed")

            with self.assertRaisesRegex(self.cli.SmokeRunnerError, "hash changed"):
                self.cli.verify_shared_base_hash(base, expected)

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
            "phase1-isolation", 3, BASELINE_PATH, reuse_base=True
        )
        constraints = plan["constraints"]
        self.assertEqual(constraints["guest_network"], "none")
        self.assertFalse(constraints["host_directories_mounted_in_guest"])
        self.assertFalse(constraints["physical_block_devices_accessed"])
        self.assertFalse(constraints["windows_install_or_boot_changes"])
        self.assertIn("copy-on-write", constraints["base_storage_mode"])
        self.assertEqual(constraints["privilege_escalation"], "never")
        self.assertEqual(
            {run["overlay_backing_path"] for run in plan["runs"]},
            {plan["shared_base_path"]},
        )

    def test_execute_without_privileges_fails_before_writing_or_running(self):
        plan = self.cli.create_measurement_plan(
            "phase1-unprivileged", 1, BASELINE_PATH, reuse_base=True
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

    def test_measurement_json_reports_shared_base_contract(self):
        baseline = {"readiness_after_seconds": 10.0, "wall_duration_seconds": 20.0}
        backing = "images/sample-r01/aureon-base.qcow2"
        results = [
            {
                **self.result("sample-r01", 9.0, 19.0, 100),
                "overlay_backing_path": backing,
                "overlay_path": "work/qemu/sample-r01/smoke-overlay.qcow2",
            },
            {
                **self.result("sample-r02", 10.0, 20.0, 110),
                "overlay_backing_path": backing,
                "overlay_path": "work/qemu/sample-r02/smoke-overlay.qcow2",
            },
            {
                **self.result("sample-r03", 11.0, 21.0, 120),
                "overlay_backing_path": backing,
                "overlay_path": "work/qemu/sample-r03/smoke-overlay.qcow2",
            },
        ]
        measurement = self.cli.aggregate_measurement(
            "sample",
            3,
            "docs/testing/baseline.json",
            baseline,
            results,
            base_reuse_enabled=True,
            shared_base_path=backing,
            shared_base_sha256_before="abc",
            shared_base_sha256_after_each_run=["abc", "abc", "abc"],
        )

        self.assertTrue(measurement["base_reuse_enabled"])
        self.assertTrue(measurement["shared_base_unchanged"])
        self.assertTrue(measurement["base_images_identical_across_runs"])
        self.assertTrue(measurement["suitable_as_final_boot_regression_baseline"])
        self.assertEqual(
            measurement["shared_base_sha256_after_each_run"], ["abc", "abc", "abc"]
        )

    def test_failure_preserves_completed_run_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            baseline = {"readiness_after_seconds": 10.0, "wall_duration_seconds": 20.0}
            plan = {
                "base_reuse_enabled": True,
                "run_id": "partial",
                "runs": [
                    {
                        "build_id": "partial-r01",
                        "overlay_backing_path": "images/partial-r01/aureon-base.qcow2",
                    },
                    {
                        "build_id": "partial-r02",
                        "overlay_backing_path": "images/partial-r01/aureon-base.qcow2",
                    },
                    {
                        "build_id": "partial-r03",
                        "overlay_backing_path": "images/partial-r01/aureon-base.qcow2",
                    },
                ],
                "shared_base_path": "images/partial-r01/aureon-base.qcow2",
            }
            shared_base = root / plan["shared_base_path"]

            def execute(plan_value, paths, **kwargs):
                if plan_value["build_id"].endswith("r02"):
                    raise self.cli.SmokeRunnerError("simulated second-run failure")
                shared_base.parent.mkdir(parents=True, exist_ok=True)
                shared_base.write_bytes(b"base")
                return {"qcow2_sha256": self.cli._sha256_file(shared_base)}

            def record(build_id, paths, status, repository_root, error, backing):
                return {
                    "acceleration": None,
                    "artifacts": {"overlay": {"size_bytes": None}},
                    "build_id": build_id,
                    "overlay_backing_path": backing,
                    "overlay_path": self.cli.relative_repository_path(
                        paths.overlay, repository_root
                    ),
                    "readiness_after_seconds": None,
                    "status": status,
                    "wall_duration_seconds": None,
                }

            with mock.patch.object(self.cli.os, "geteuid", return_value=0), mock.patch.object(
                self.cli, "require_unused_smoke_output_roots"
            ), mock.patch.object(
                self.cli,
                "create_smoke_plan",
                side_effect=lambda build_id, repository_root: {
                    "build_id": build_id,
                    "command": "test-smoke",
                },
            ), mock.patch.object(
                self.cli, "execute_smoke_plan", side_effect=execute
            ), mock.patch.object(
                self.cli, "measurement_run_record", side_effect=record
            ):
                measurement = self.cli.execute_measurement(
                    plan, baseline, "docs/testing/baseline.json", root
                )

            runs = root / "work/measurements/partial/runs"
            self.assertTrue((runs / "r01.json").is_file())
            self.assertTrue((runs / "r02.json").is_file())
            self.assertFalse((runs / "r03.json").exists())
            self.assertEqual(measurement["summary"]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
