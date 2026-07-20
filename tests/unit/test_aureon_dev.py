"""Unit tests for the safe Aureon development CLI scaffold."""

from __future__ import annotations

import dataclasses
import importlib.machinery
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPOSITORY_ROOT / "tools" / "aureon-dev"


def load_cli_module():
    """Load the extensionless Python entry point as an importable test module."""

    module_name = "aureon_dev_under_test"
    loader = importlib.machinery.SourceFileLoader(module_name, str(CLI_PATH))
    spec = importlib.util.spec_from_loader(module_name, loader)
    if spec is None:
        raise RuntimeError("Unable to load tools/aureon-dev for testing")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    loader.exec_module(module)
    return module


class AureonDevTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cli = load_cli_module()

    def invoke(self, arguments):
        output = io.StringIO()
        status = self.cli.main(arguments, stdout=output)
        return status, output.getvalue()

    def ready_checks(self):
        return (
            self.cli.PreflightCheck("Python >= 3.10", self.cli.FOUND, "test runtime"),
            self.cli.PreflightCheck("Git", self.cli.FOUND, "test git"),
            self.cli.PreflightCheck("Linux builder", self.cli.FOUND, "test Linux"),
            self.cli.PreflightCheck("QEMU system emulator", self.cli.FOUND, "test qemu"),
            self.cli.PreflightCheck("QEMU image tool", self.cli.FOUND, "test qemu-img"),
            self.cli.PreflightCheck("OCI builder (Podman or Docker)", self.cli.FOUND, "test builder"),
            self.cli.PreflightCheck("OVMF firmware", self.cli.FOUND, "test firmware"),
        )

    def test_default_workspace_is_the_canonical_checkout(self):
        args = self.cli.build_parser().parse_args(["doctor"])

        self.assertEqual(args.workspace, self.cli.REPOSITORY_ROOT)
        self.assertEqual(self.cli.REPOSITORY_ROOT, REPOSITORY_ROOT.resolve())

    def test_workspace_outside_checkout_is_rejected(self):
        status, report = self.invoke(["--workspace", str(self.cli.REPOSITORY_ROOT.parent), "doctor"])

        self.assertEqual(status, self.cli.WORKSPACE_REJECTED_EXIT_CODE)
        self.assertIn("rejected --workspace", report)
        self.assertIn("outside canonical checkout", report)

    def test_workspace_that_resolves_outside_checkout_is_rejected(self):
        escaping_path = self.cli.REPOSITORY_ROOT / ".."
        status, report = self.invoke(["--workspace", str(escaping_path), "doctor"])

        self.assertEqual(status, self.cli.WORKSPACE_REJECTED_EXIT_CODE)
        self.assertIn("outside canonical checkout", report)

    def test_doctor_never_creates_paths(self):
        unique_scope = self.cli.REPOSITORY_ROOT / "work" / ("doctor-no-write-" + uuid.uuid4().hex)
        before = {path: path.exists() for _, path in self.cli.expected_paths(self.cli.REPOSITORY_ROOT)}
        self.assertFalse(unique_scope.exists())

        report = io.StringIO()
        status = self.cli.run_doctor(unique_scope, report, checks=self.ready_checks())

        after = {path: path.exists() for _, path in self.cli.expected_paths(self.cli.REPOSITORY_ROOT)}
        self.assertEqual(status, 0)
        self.assertFalse(unique_scope.exists())
        self.assertEqual(before, after)
        self.assertIn("Mode: read-only", report.getvalue())
        self.assertIn("Readiness: READY", report.getvalue())

    def test_doctor_is_not_ready_when_phase_zero_dependencies_are_missing(self):
        checks = self.cli.collect_preflight_checks(
            host_system="Linux",
            which=lambda candidate: None,
            version_info=(3, 10, 0),
            ovmf_paths=(),
        )
        report = io.StringIO()

        status = self.cli.run_doctor(self.cli.REPOSITORY_ROOT, report, checks=checks)
        rendered = report.getvalue()

        self.assertEqual(status, self.cli.PREFLIGHT_NOT_READY_EXIT_CODE)
        self.assertIn("Readiness: NOT READY", rendered)
        self.assertIn("[not found] Git", rendered)
        self.assertIn("[not found] QEMU system emulator", rendered)
        self.assertIn("[not found] OCI builder (Podman or Docker)", rendered)
        self.assertIn("[not found] OVMF firmware", rendered)

    def test_phase_zero_preflight_covers_all_required_capabilities(self):
        checks = self.cli.collect_preflight_checks(
            host_system="Linux",
            which=lambda candidate: None,
            version_info=(3, 10, 0),
            ovmf_paths=(),
        )
        names = {check.name for check in checks}

        self.assertEqual(
            names,
            {
                "Python >= 3.10",
                "Git",
                "Linux builder",
                "QEMU system emulator",
                "QEMU image tool",
                "OCI builder (Podman or Docker)",
                "OVMF firmware",
            },
        )

    def test_default_ovmf_paths_include_current_ubuntu_firmware(self):
        candidates = self.cli.default_ovmf_paths(environ={}, operating_system="posix")

        self.assertIn(Path("/usr/share/OVMF/OVMF_CODE_4M.fd"), candidates)

    def test_expected_paths_follow_the_phase_zero_topology(self):
        paths = dict(self.cli.expected_paths(self.cli.REPOSITORY_ROOT))

        self.assertEqual(paths["Build artifacts"], self.cli.REPOSITORY_ROOT / "build")
        self.assertEqual(paths["Bootable images"], self.cli.REPOSITORY_ROOT / "images")
        self.assertEqual(paths["QEMU work directory"], self.cli.REPOSITORY_ROOT / "work" / "qemu")
        self.assertNotIn("logs", " ".join(str(path) for path in paths.values()))

    def test_first_executable_uses_the_first_available_candidate(self):
        found = self.cli.first_executable(
            ("missing", "available"),
            which=lambda candidate: "/fake/available" if candidate == "available" else None,
        )

        self.assertEqual(found, "/fake/available")

    def test_reserved_commands_fail_closed_without_creating_workspace_files(self):
        before = {path: path.exists() for _, path in self.cli.expected_paths(self.cli.REPOSITORY_ROOT)}
        for command in self.cli.PENDING_COMMANDS:
            status, report = self.invoke([command])

            self.assertEqual(status, self.cli.NOT_IMPLEMENTED_EXIT_CODE, command)
            self.assertIn("not implemented yet", report)
            self.assertIn("No files, images, snapshots", report)
        after = {path: path.exists() for _, path in self.cli.expected_paths(self.cli.REPOSITORY_ROOT)}
        self.assertEqual(before, after)

    def test_smoke_dry_run_is_deterministic_and_never_creates_artifacts(self):
        build_id = "unit-smoke-" + uuid.uuid4().hex[:12]
        paths = self.cli.smoke_paths(build_id)
        self.assertFalse(paths.build_root.exists())
        self.assertFalse(paths.image_root.exists())
        self.assertFalse(paths.work_root.exists())

        first_status, first_report = self.invoke(["test-smoke", "--build-id", build_id])
        second_status, second_report = self.invoke(["test-smoke", "--build-id", build_id])
        plan = json.loads(first_report)

        self.assertEqual(first_status, 0)
        self.assertEqual(second_status, 0)
        self.assertEqual(first_report, second_report)
        self.assertEqual(plan["command"], "test-smoke")
        self.assertEqual(plan["execution"]["mode"], "dry-run")
        self.assertFalse(plan["execution"]["writes"])
        self.assertEqual(plan["constraints"]["guest_network"], "disabled")
        self.assertFalse(paths.build_root.exists())
        self.assertFalse(paths.image_root.exists())
        self.assertFalse(paths.work_root.exists())

    def test_smoke_execute_requires_a_new_explicit_build_id_before_preflight(self):
        with mock.patch.object(
            self.cli,
            "execute_smoke_plan",
            side_effect=AssertionError("runner must not be called"),
        ):
            status, report = self.invoke(["test-smoke", "--execute"])

        self.assertEqual(status, self.cli.UNSAFE_INPUT_EXIT_CODE)
        self.assertIn("explicit unused --build-id", report)

    def test_smoke_output_roots_never_overwrite_an_existing_build(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            (root / "build").mkdir(parents=True)
            (root / "images").mkdir()
            (root / "work" / "qemu").mkdir(parents=True)
            paths = self.cli.smoke_paths("safe-smoke", root)
            paths.build_root.mkdir()

            with self.assertRaisesRegex(self.cli.PlanValidationError, "refusing to overwrite"):
                self.cli.require_unused_smoke_output_roots(paths, root)

            self.assertFalse(paths.image_root.exists())
            self.assertFalse(paths.work_root.exists())

    def test_smoke_allows_a_clean_checkout_without_ignored_work_parents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            (root / "build").mkdir(parents=True)
            (root / "images").mkdir()
            paths = self.cli.smoke_paths("safe-smoke", root)

            self.cli.require_unused_smoke_output_roots(paths, root)

            self.assertFalse((root / "work").exists())
            self.assertFalse(paths.work_root.exists())

    def test_smoke_rejects_a_caller_substituting_an_external_artifact_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            (root / "build").mkdir(parents=True)
            (root / "images").mkdir()
            paths = self.cli.smoke_paths("safe-smoke", root)
            unsafe = dataclasses.replace(paths, qemu_log=Path(directory) / "outside.log")

            with self.assertRaisesRegex(self.cli.PlanValidationError, "fixed build-ID topology"):
                self.cli.require_unused_smoke_output_roots(unsafe, root)

    def test_smoke_preflight_rejects_non_linux_before_any_command(self):
        with mock.patch.object(self.cli.platform, "system", return_value="Windows"), mock.patch.object(
            self.cli.subprocess,
            "run",
            side_effect=AssertionError("no command may run"),
        ):
            with self.assertRaisesRegex(self.cli.SmokeRunnerError, "only inside Linux/WSL"):
                self.cli.collect_smoke_runner_preflight()

    def test_serial_assertions_require_one_marker_and_clean_poweroff(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "serial.log"
            log.write_text(
                "kernel console=ttyS0,115200n8\n"
                "AUREON_PHASE0_READY\n"
                "systemd-shutdown[1]: Powering off.\n"
                "reboot: Power down\n",
                encoding="utf-8",
            )

            assertions = self.cli._read_serial_assertions(log, "tcg")

        self.assertEqual(assertions["readiness_line"], 2)
        self.assertEqual(assertions["poweroff_line"], 3)
        self.assertEqual(assertions["clean_guest_shutdown_line"], 4)

    def test_build_dry_run_prints_a_versioned_deterministic_manifest_without_writes(self):
        planned_build = self.cli.REPOSITORY_ROOT / "build" / "unit-plan"
        self.assertFalse(planned_build.exists())

        first_status, first_report = self.invoke(["build", "--build-id", "unit-plan"])
        second_status, second_report = self.invoke(["build", "--build-id", "unit-plan"])
        manifest = json.loads(first_report)

        self.assertEqual(first_status, 0)
        self.assertEqual(second_status, 0)
        self.assertEqual(first_report, second_report)
        self.assertFalse(planned_build.exists())
        self.assertEqual(manifest["schema"], self.cli.MANIFEST_SCHEMA)
        self.assertEqual(manifest["version"], self.cli.MANIFEST_VERSION)
        self.assertEqual(manifest["command"], "build")
        self.assertEqual(manifest["execution"]["mode"], "dry-run")
        self.assertFalse(manifest["execution"]["writes"])
        self.assertEqual(manifest["paths"]["manifest"], "build/unit-plan/manifest.json")
        self.assertEqual(manifest["paths"]["oci_layout"], "build/unit-plan/oci")
        self.assertRegex(manifest["inputs"]["digest"], r"^[0-9a-f]{64}$")

    def test_image_plan_accepts_only_an_in_tree_qcow2_target(self):
        planned_image = self.cli.REPOSITORY_ROOT / "images" / "unit-image"
        self.assertFalse(planned_image.exists())

        status, report = self.invoke(
            [
                "image",
                "--build-id",
                "unit-image",
                "--disk",
                "images/unit-image/custom.qcow2",
            ]
        )
        manifest = json.loads(report)

        self.assertEqual(status, 0)
        self.assertFalse(planned_image.exists())
        self.assertEqual(manifest["paths"]["disk"], "images/unit-image/custom.qcow2")

    def test_plan_rejects_invalid_build_ids_and_external_paths(self):
        bad_id_status, bad_id_report = self.invoke(["build", "--build-id", "../escape"])
        external_status, external_report = self.invoke(
            ["build", "--build-id", "safe", "--manifest", str(self.cli.REPOSITORY_ROOT.parent / "x.json")]
        )

        self.assertEqual(bad_id_status, self.cli.UNSAFE_INPUT_EXIT_CODE)
        self.assertIn("invalid build id", bad_id_report)
        self.assertEqual(external_status, self.cli.UNSAFE_INPUT_EXIT_CODE)
        self.assertIn("outside canonical checkout", external_report)

    def test_plan_rejects_windows_reserved_ids_and_path_components(self):
        aliases = (
            "con",
            "nul.txt",
            "aux",
            "prn.log",
            "com1",
            "com9.img",
            "lpt1",
            "lpt9.qcow2",
        )
        for build_id in aliases:
            with self.subTest(build_id=build_id):
                with self.assertRaisesRegex(self.cli.PlanValidationError, "Windows-reserved"):
                    self.cli.validate_build_id(build_id)

        for build_id in ("safe.", "safe "):
            with self.subTest(build_id=build_id):
                with self.assertRaisesRegex(self.cli.PlanValidationError, "must not end"):
                    self.cli.validate_build_id(build_id)

        self.assertTrue(self.cli.is_windows_reserved_name("CON.txt"))
        for disk in ("images/safe/con.qcow2", r"images\safe\lpt9.qcow2"):
            with self.subTest(disk=disk):
                status, report = self.invoke(["image", "--build-id", "safe", "--disk", disk])

                self.assertEqual(status, self.cli.UNSAFE_INPUT_EXIT_CODE)
                self.assertIn("Windows-reserved device name", report)
                self.assertNotIn("No files", report)

        status, report = self.invoke(
            ["build", "--build-id", "safe", "--manifest", "build/safe/nul.json"]
        )
        self.assertEqual(status, self.cli.UNSAFE_INPUT_EXIT_CODE)
        self.assertIn("Windows-reserved device name", report)

    def test_image_plan_rejects_physical_disks_and_non_qcow2_paths(self):
        physical_status, physical_report = self.invoke(
            ["image", "--build-id", "safe", "--disk", r"\\.\PhysicalDrive0"]
        )
        extension_status, extension_report = self.invoke(
            ["image", "--build-id", "safe", "--disk", "images/safe/aureon-base.raw"]
        )

        self.assertEqual(physical_status, self.cli.UNSAFE_INPUT_EXIT_CODE)
        self.assertIn("physical disk", physical_report)
        self.assertEqual(extension_status, self.cli.UNSAFE_INPUT_EXIT_CODE)
        self.assertIn(".qcow2", extension_report)

    def test_declared_input_hash_is_independent_of_declared_root_order(self):
        first_records, first_digest = self.cli.declared_input_records()
        second_records, second_digest = self.cli.declared_input_records(
            input_paths=tuple(reversed(self.cli.DECLARED_INPUTS))
        )

        self.assertEqual(first_records, second_records)
        self.assertEqual(first_digest, second_digest)

    def test_declared_inputs_do_not_follow_or_hash_child_links_outside_the_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            declared = root / "declared"
            declared.mkdir(parents=True)
            external = Path(directory) / "outside.txt"
            external.write_text("must never be hashed", encoding="utf-8")
            link = declared / "external-link"
            try:
                link.symlink_to(external)
            except (NotImplementedError, OSError) as error:
                self.skipTest("symlink creation is unavailable in this test environment: {0}".format(error))

            with mock.patch.object(
                self.cli.hashlib, "sha256", side_effect=AssertionError("declared input was hashed")
            ):
                with self.assertRaisesRegex(self.cli.PlanValidationError, "resolves outside canonical checkout"):
                    self.cli.declared_input_records(root, input_paths=("declared",))

    def test_image_validates_every_destination_before_hashing_declared_inputs(self):
        with mock.patch.object(
            self.cli,
            "declared_input_records",
            side_effect=AssertionError("declared inputs must not be hashed"),
        ):
            with self.assertRaisesRegex(self.cli.PlanValidationError, "qcow2"):
                self.cli.create_dry_run_manifest(
                    "image", "safe", disk_path="images/safe/aureon-base.raw"
                )

    def test_execute_mode_fails_closed_after_validation(self):
        with mock.patch.object(
            self.cli,
            "declared_input_records",
            side_effect=AssertionError("--execute must not hash declared inputs"),
        ):
            status, report = self.invoke(["image", "--build-id", "safe", "--execute"])

        self.assertEqual(status, self.cli.NOT_IMPLEMENTED_EXIT_CODE)
        self.assertIn("fails closed", report)
        self.assertIn("not implemented or verified", report)
        self.assertIn("before hashing declared inputs", report)

    def test_windows_wsl_check_uses_only_the_systemroot_executable(self):
        commands = []

        def query(command):
            commands.append(command)
            if command[1] == "--status":
                return self.cli.WslQueryResult(returncode=0)
            return self.cli.WslQueryResult(returncode=0, stdout="Ubuntu-24.04\n")

        check = self.cli.linux_builder_check(
            host_system="Windows",
            which=lambda candidate: (_ for _ in ()).throw(AssertionError("PATH must not be used")),
            wsl_query=query,
            environ={"SystemRoot": r"C:\Windows"},
            path_is_file=lambda path: True,
        )

        self.assertEqual(check.state, self.cli.FOUND)
        self.assertEqual(len(commands), 2)
        self.assertEqual(
            str(commands[0][0]).replace("/", "\\").casefold(),
            r"c:\windows\system32\wsl.exe",
        )

    def test_windows_wsl_check_marks_an_untrusted_location_unverified_without_querying(self):
        check = self.cli.linux_builder_check(
            host_system="Windows",
            wsl_query=lambda command: (_ for _ in ()).throw(AssertionError("WSL must not run")),
            environ={"SystemRoot": r"\\server\share"},
            path_is_file=lambda path: True,
        )

        self.assertEqual(check.state, self.cli.NOT_VERIFIED)
        self.assertIn("UNC or remote", check.detail)

    def test_windows_doctor_inspects_the_actual_wsl_guest_toolchain(self):
        commands = []

        def query(command):
            commands.append(command)
            if command[1] == "--status":
                return self.cli.WslQueryResult(returncode=0)
            if command[1] == "--list":
                return self.cli.WslQueryResult(returncode=0, stdout="Ubuntu-24.04\n")
            executable = command[4]
            outputs = {
                "/usr/bin/uname": "x86_64\n",
                "/usr/bin/python3": "Python 3.12.0\n",
                "/usr/bin/podman": "podman version 4.9.3\n",
                "/usr/bin/qemu-system-x86_64": "QEMU emulator version 8.2\n",
                "/usr/bin/qemu-img": "qemu-img version 8.2\n",
                "/usr/bin/test": "",
            }
            return self.cli.WslQueryResult(returncode=0, stdout=outputs[executable])

        checks = self.cli.collect_preflight_checks(
            host_system="Windows",
            which=lambda candidate: r"C:\Program Files\Git\cmd\git.exe" if candidate == "git" else None,
            version_info=(3, 12, 0),
            wsl_query=query,
            environ={"SystemRoot": r"C:\Windows"},
            path_is_file=lambda path: True,
        )
        by_name = {check.name: check for check in checks}

        self.assertTrue(self.cli.readiness(checks), checks)
        self.assertEqual(by_name["WSL guest architecture"].state, self.cli.FOUND)
        self.assertEqual(by_name["WSL Podman"].state, self.cli.FOUND)
        self.assertEqual(by_name["WSL OVMF firmware"].state, self.cli.FOUND)
        self.assertIn("WSL KVM acceleration (optional)", by_name)
        self.assertNotIn("QEMU system emulator", by_name)
        guest_commands = [command for command in commands if "--distribution" in command]
        self.assertTrue(guest_commands)
        for command in guest_commands:
            self.assertEqual(command[1:4], ("--distribution", "Ubuntu-24.04", "--exec"))
            self.assertNotIn("sudo", command)
            self.assertNotIn("--install", command)
            self.assertNotIn("--mount", command)

    def test_windows_doctor_does_not_probe_a_missing_target_distribution(self):
        commands = []

        def query(command):
            commands.append(command)
            if command[1] == "--status":
                return self.cli.WslQueryResult(returncode=0)
            return self.cli.WslQueryResult(returncode=0, stdout="Ubuntu\n")

        checks = self.cli.collect_wsl_guest_checks(
            wsl_query=query,
            environ={"SystemRoot": r"C:\Windows"},
            path_is_file=lambda path: True,
        )

        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0].state, self.cli.NOT_VERIFIED)
        self.assertIn("Ubuntu-24.04", checks[0].detail)
        self.assertFalse(any("--distribution" in command for command in commands))

    def test_optional_wsl_kvm_absence_does_not_block_functional_readiness(self):
        def query(command):
            if command[1] == "--status":
                return self.cli.WslQueryResult(returncode=0)
            if command[1] == "--list":
                return self.cli.WslQueryResult(returncode=0, stdout="Ubuntu-24.04\n")
            if command[-1] == "/dev/kvm":
                return self.cli.WslQueryResult(returncode=1)
            executable = command[4]
            outputs = {
                "/usr/bin/uname": "x86_64\n",
                "/usr/bin/python3": "Python 3.12.0\n",
                "/usr/bin/podman": "podman version 4.9.3\n",
                "/usr/bin/qemu-system-x86_64": "QEMU emulator version 8.2\n",
                "/usr/bin/qemu-img": "qemu-img version 8.2\n",
                "/usr/bin/test": "",
            }
            return self.cli.WslQueryResult(returncode=0, stdout=outputs[executable])

        checks = self.cli.collect_wsl_guest_checks(
            wsl_query=query,
            environ={"SystemRoot": r"C:\Windows"},
            path_is_file=lambda path: True,
        )
        kvm = next(check for check in checks if check.name == "WSL KVM acceleration (optional)")

        self.assertEqual(kvm.state, self.cli.NOT_FOUND)
        self.assertFalse(kvm.required)
        self.assertTrue(self.cli.readiness(checks))

    def test_ovmf_environment_rejects_unc_and_remote_paths(self):
        unc = r"\\server\share\OVMF_CODE.fd"
        candidates = self.cli.default_ovmf_paths(
            environ={"AUREON_OVMF_CODE": unc}, operating_system="posix"
        )
        check = self.cli.ovmf_check(environ={"AUREON_OVMF_CODE": unc})

        self.assertNotIn(Path(unc), candidates)
        self.assertEqual(check.state, self.cli.NOT_VERIFIED)
        self.assertIn("UNC and remote", check.detail)
        self.assertTrue(self.cli.is_remote_or_unc_path("smb://firmware/OVMF_CODE.fd"))

    def test_help_lists_doctor_and_every_reserved_contract(self):
        help_text = self.cli.build_parser().format_help()

        self.assertIn("doctor", help_text)
        self.assertIn("build", help_text)
        self.assertIn("image", help_text)
        for command in self.cli.PENDING_COMMANDS:
            self.assertIn(command, help_text)


if __name__ == "__main__":
    unittest.main()
