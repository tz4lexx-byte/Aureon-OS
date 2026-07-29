"""Unit tests for the isolated Aureon desktop-preview launcher."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import json
import errno
import stat
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = REPOSITORY_ROOT / "tools" / "aureon-desktop-preview"


def load_tool_module():
    """Load the extensionless desktop launcher without executing its CLI."""

    name = "aureon_desktop_preview_under_test"
    loader = importlib.machinery.SourceFileLoader(name, str(TOOL_PATH))
    spec = importlib.util.spec_from_loader(name, loader)
    if spec is None:
        raise RuntimeError("Unable to load desktop preview launcher")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


class DesktopPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool_module()

    def invoke(self, arguments):
        output = io.StringIO()
        status = self.tool.main(arguments, output=output)
        return status, output.getvalue()

    def test_dry_run_is_deterministic_and_never_creates_artifacts(self):
        build_id = "desktop-unit-" + uuid.uuid4().hex[:10]
        paths = self.tool.preview_paths(build_id)
        self.assertFalse(paths.build_root.exists())
        self.assertFalse(paths.image_root.exists())
        self.assertFalse(paths.work_root.exists())

        first_status, first_output = self.invoke(["--build-id", build_id, "--dry-run"])
        second_status, second_output = self.invoke(["--build-id", build_id, "--dry-run"])
        plan = json.loads(first_output)

        self.assertEqual(first_status, 0)
        self.assertEqual(second_status, 0)
        self.assertEqual(first_output, second_output)
        self.assertEqual(plan["command"], "desktop-preview")
        self.assertTrue(plan["execution"]["allow_build_network_required"])
        self.assertEqual(plan["execution"]["guest_network"], "qemu-user-nat-no-inbound-forwarding")
        self.assertEqual(plan["execution"]["video_adapter"], "virtio")
        self.assertEqual(plan["execution"]["gtk_backend"], "x11")
        self.assertEqual(plan["execution"]["requested_display"]["width"], 1920)
        self.assertEqual(plan["execution"]["requested_display"]["height"], 1080)
        self.assertFalse(paths.build_root.exists())
        self.assertFalse(paths.image_root.exists())
        self.assertFalse(paths.work_root.exists())

    def test_source_digest_excludes_local_python_cache_artifacts(self):
        records, _ = self.tool._source_digest(REPOSITORY_ROOT)
        paths = [record["path"] for record in records]

        self.assertIn("system/desktop/.containerignore", paths)
        self.assertFalse(any("__pycache__" in path or path.endswith((".pyc", ".pyo")) for path in paths))
        ignore = (REPOSITORY_ROOT / "system" / "desktop" / ".containerignore").read_text(encoding="utf-8")
        self.assertIn("**/__pycache__/**", ignore)
        self.assertIn("**/*.pyc", ignore)

    def test_package_inventory_is_sorted_deduplicated_and_hashed(self):
        inventory = self.tool._package_inventory(
            "plasma-workspace-0:6.4.5-1.fc42.x86_64\n"
            "bash-0:5.2.37-1.fc42.x86_64\n"
            "plasma-workspace-0:6.4.5-1.fc42.x86_64\n"
        )

        self.assertEqual(inventory["count"], 2)
        self.assertEqual(
            inventory["packages"],
            ["bash-0:5.2.37-1.fc42.x86_64", "plasma-workspace-0:6.4.5-1.fc42.x86_64"],
        )
        self.assertRegex(inventory["digest"], r"^[0-9a-f]{64}$")

    def test_package_inventory_normalizes_rpm_missing_epoch(self):
        inventory = self.tool._package_inventory(
            "plasma-workspace\t(none)\t6.4.5\t1.fc42\tx86_64\n"
            "bash\t2\t5.2.37\t1.fc42\tx86_64\n"
            "gpg-pubkey\t(none)\t18b8e74c\t62f5cdd3\t(none)\n"
        )

        self.assertEqual(
            inventory["packages"],
            [
                "bash-2:5.2.37-1.fc42.x86_64",
                "gpg-pubkey-0:18b8e74c-62f5cdd3.none",
                "plasma-workspace-0:6.4.5-1.fc42.x86_64",
            ],
        )

    def test_guest_evidence_is_decoded_from_the_serial_contract(self):
        report = {"schema": "aureon.control-plane-report", "version": 1, "result": {"state": "passed"}}
        encoded = self.tool.base64.b64encode(json.dumps(report).encode("utf-8")).decode("ascii")
        with tempfile.TemporaryDirectory() as directory:
            serial = Path(directory) / "serial.log"
            serial.write_text(
                "display_requested=1920x1080@60\n"
                "display_state=observed-1920x1080@60\n"
                "AUREON_EVIDENCE core=" + encoded + "\nAUREON_DESKTOP_READY\n",
                encoding="utf-8",
            )
            evidence = self.tool._extract_guest_evidence(serial)
            state = self.tool._extract_guest_session_state(serial)

        self.assertEqual(evidence["core"], report)
        self.assertEqual(state["display_requested"], "1920x1080@60")
        self.assertEqual(state["display_state"], "observed-1920x1080@60")

    def test_guest_evidence_recovers_from_interleaved_serial_chunks(self):
        report = {
            "schema": "aureon.control-plane-report",
            "version": 1,
            "result": {"state": "passed", "details": "x" * 900},
        }
        encoded = self.tool.base64.b64encode(json.dumps(report).encode("utf-8")).decode("ascii")
        chunks = [encoded[offset : offset + 512] for offset in range(0, len(encoded), 512)]
        lines = []
        for index, chunk in enumerate(chunks, start=1):
            line = (
                f"[  83.0] aureon-wait-desktop-ready[1017]: "
                f"AUREON_EVIDENCE_CHUNK name=services index={index:04d} "
                f"total={len(chunks):04d} data={chunk}"
            )
            lines.extend((line, "[  83.0] audit: interleaved", line))
        with tempfile.TemporaryDirectory() as directory:
            serial = Path(directory) / "serial.log"
            serial.write_text("\n".join(lines) + "\n", encoding="utf-8")
            evidence = self.tool._extract_guest_evidence(serial)

        self.assertEqual(evidence["services"], report)

    def test_execute_requires_explicit_network_acknowledgement_before_preflight(self):
        with mock.patch.object(
            self.tool,
            "execute",
            side_effect=AssertionError("the runner must not be called"),
        ):
            status, output = self.invoke(["--build-id", "desktop-safe", "--execute"])

        self.assertEqual(status, 4)
        self.assertIn("--allow-build-network", output)

    def test_preview_paths_use_only_the_fixed_virtual_artifact_topology(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            paths = self.tool.preview_paths("demo", root)

        self.assertEqual(paths.build_root, root / "build" / "desktop-demo")
        self.assertEqual(paths.image_root, root / "images" / "desktop-demo")
        self.assertEqual(paths.work_root, root / "work" / "qemu-desktop" / "demo")
        self.assertEqual(paths.disk.suffix, ".qcow2")

    def test_existing_preview_uses_a_new_session_overlay_below_its_virtual_work_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            paths = self.tool.existing_session_paths("demo", "resume-01", root)

        self.assertEqual(paths.session_root, root / "work" / "qemu-desktop" / "demo" / "sessions" / "resume-01")
        self.assertEqual(paths.overlay.name, "desktop-overlay.qcow2")
        self.assertEqual(paths.serial_log.parent, paths.session_root)

    def test_existing_preview_dry_run_needs_no_build_network_or_new_image(self):
        build_id = "existing-unit-" + uuid.uuid4().hex[:10]
        status, output = self.invoke(["--run-existing", "--build-id", build_id, "--session-id", "resume-01"])
        plan = json.loads(output)

        self.assertEqual(status, 0)
        self.assertEqual(plan["command"], "desktop-preview --run-existing")
        self.assertEqual(plan["execution"]["build_network"], "not used")
        self.assertTrue(plan["safety"]["base_qcow2_reused_read_only"])
        self.assertTrue(plan["safety"]["writes_limited_to_new_session_overlay"])

    def test_existing_preview_execute_does_not_require_build_network_acknowledgement(self):
        build_id = "existing-execute-" + uuid.uuid4().hex[:10]
        with mock.patch.object(self.tool, "run_existing_preview", return_value={"status": "passed"}) as runner:
            status, output = self.invoke(
                ["--run-existing", "--build-id", build_id, "--session-id", "resume-01", "--execute"]
            )

        self.assertEqual(status, 0)
        self.assertEqual(json.loads(output)["status"], "passed")
        runner.assert_called_once()

    def test_existing_preview_rejects_unneeded_build_network_acknowledgement(self):
        status, output = self.invoke(
            ["--run-existing", "--build-id", "existing-network", "--execute", "--allow-build-network"]
        )

        self.assertEqual(status, 4)
        self.assertIn("never uses build networking", output)

    def test_qemu_gui_command_keeps_the_guest_offline_and_uses_only_virtual_devices(self):
        paths = self.tool.preview_paths("desktop-command")
        command = self.tool.qemu_command(paths, "/usr/bin/qemu-system-x86_64", "tcg")
        joined = " ".join(command)
        portable_joined = joined.replace("\\", "/")

        self.assertIn("-display gtk,gl=off,zoom-to-fit=on,full-screen=on,show-tabs=off", joined)
        self.assertIn("-device virtio-vga,edid=on,xres=1920,yres=1080,max_outputs=1", joined)
        self.assertIn("-device usb-kbd,bus=xhci.0", joined)
        self.assertIn("-nic user,model=virtio-net-pci", joined)
        self.assertNotIn("hostfwd=", joined)
        self.assertIn("-qmp unix:/run/aureon-desktop-preview/", portable_joined)
        self.assertNotIn("tcp:", joined)
        self.assertIn("readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd", portable_joined)
        self.assertIn(str(paths.overlay), joined)
        self.assertNotIn("-virtfs", joined)
        self.assertNotIn("PhysicalDrive", joined)
        self.assertNotIn("/dev/sd", joined)

    def test_virtio_video_is_explicit_and_advertises_full_hd(self):
        paths = self.tool.preview_paths("desktop-virtio-command")
        command = self.tool.qemu_command(paths, "/usr/bin/qemu-system-x86_64", "tcg", "virtio")
        joined = " ".join(command)

        self.assertIn("-device virtio-vga,edid=on,xres=1920,yres=1080,max_outputs=1", joined)
        self.assertIn("-nic user,model=virtio-net-pci", joined)
        self.assertNotIn("hostfwd=", joined)

    def test_existing_preview_plan_records_full_hd_compatibility_video(self):
        status, output = self.invoke(
            ["--run-existing", "--build-id", "existing-full-hd", "--session-id", "full-hd-01", "--video", "std"]
        )
        plan = json.loads(output)

        self.assertEqual(status, 0)
        self.assertEqual(plan["execution"]["video_adapter"], "std")
        self.assertEqual(plan["execution"]["gtk_backend"], "x11")
        self.assertEqual(plan["execution"]["requested_display"], {"height": 1080, "refresh_hz": 60, "scale": 1.0, "width": 1920})

    def test_wayland_frontend_choice_is_preserved_in_existing_plan(self):
        status, output = self.invoke(
            ["--run-existing", "--build-id", "existing-wayland", "--session-id", "wayland-01", "--gtk-backend", "wayland"]
        )
        plan = json.loads(output)

        self.assertEqual(status, 0)
        self.assertEqual(plan["execution"]["gtk_backend"], "wayland")

    def test_gui_environment_selects_the_requested_gdk_backend(self):
        with mock.patch.dict(
            self.tool.os.environ,
            {"DISPLAY": ":0", "WAYLAND_DISPLAY": "wayland-0", "XDG_RUNTIME_DIR": "/run/user/1000"},
            clear=True,
        ):
            environment = self.tool._gui_environment("/home/pc", "x11")

        self.assertEqual(environment["GDK_BACKEND"], "x11")
        self.assertEqual(environment["DISPLAY"], ":0")

    def test_existing_preview_root_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            (root / "build").mkdir(parents=True)
            (root / "images").mkdir()
            paths = self.tool.preview_paths("demo", root)
            paths.image_root.mkdir()

            with self.assertRaisesRegex(self.tool.PreviewError, "refusing to overwrite"):
                self.tool._require_unused_roots(paths, root)

    def test_phase_zero_containerfile_remains_separate_from_desktop_profile(self):
        phase_zero = (REPOSITORY_ROOT / "system" / "Containerfile").read_text(encoding="utf-8")
        desktop = (REPOSITORY_ROOT / "system" / "desktop" / "Containerfile").read_text(encoding="utf-8")

        self.assertIn("aureon-phase0-shutdown.service", phase_zero)
        self.assertNotIn("aureon-phase0-shutdown.service", desktop)
        greetd = (REPOSITORY_ROOT / "system" / "desktop" / "overlays" / "etc" / "greetd" / "config.toml").read_text(encoding="utf-8")
        launcher = (REPOSITORY_ROOT / "system" / "desktop" / "overlays" / "usr" / "libexec" / "aureon" / "aureon-plasma-session").read_text(encoding="utf-8")
        self.assertIn("aureon-plasma-session", greetd)
        self.assertNotIn("dbus-run-session", greetd)
        self.assertIn("plasma-dbus-run-session-if-needed", launcher)
        self.assertIn("startplasma-wayland", launcher)
        self.assertIn("KWIN_COMPOSE=Q", launcher)
        self.assertIn("QT_QUICK_BACKEND=software", launcher)

    def test_ppm_framebuffer_inspection_detects_visible_content(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "framebuffer.ppm"
            pixels = bytes((index * 17) % 256 for index in range(4 * 3 * 3))
            image.write_bytes(b"P6\n4 3\n255\n" + pixels)

            evidence = self.tool._inspect_ppm(image)

        self.assertEqual((evidence["width"], evidence["height"]), (4, 3))
        self.assertTrue(evidence["visually_non_uniform"])
        self.assertRegex(evidence["sha256"], r"^[0-9a-f]{64}$")

    def test_ppm_framebuffer_inspection_flags_a_solid_surface(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "framebuffer.ppm"
            image.write_bytes(b"P6\n4 3\n255\n" + bytes([80, 80, 80]) * 12)

            evidence = self.tool._inspect_ppm(image)

        self.assertFalse(evidence["visually_non_uniform"])

    def test_qmp_framebuffer_capture_retries_a_transient_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "framebuffer.ppm"
            visible = {
                "sha256": "a" * 64,
                "width": 1920,
                "height": 1080,
                "visually_non_uniform": True,
            }
            with mock.patch.object(
                self.tool,
                "_qmp_screendump",
                side_effect=[self.tool.PreviewError("temporary QMP failure"), visible],
            ) as capture, mock.patch.object(self.tool.time, "sleep"):
                details, error = self.tool._capture_qmp_with_retries(Path("/run/qmp.sock"), output)

        self.assertIsNone(error)
        self.assertEqual(details["path"], "framebuffer.ppm")
        self.assertEqual(capture.call_count, 2)

    def test_qmp_runtime_parent_mode_is_normalized_after_mkdir(self):
        source = (REPOSITORY_ROOT / "tools" / "aureon-desktop-preview").read_text(encoding="utf-8")

        self.assertIn("os.chmod(QMP_RUNTIME_ROOT, 0o755)", source)

    def test_kvm_device_access_uses_the_unprivileged_qemu_identity(self):
        device = mock.Mock()
        device.stat.return_value = SimpleNamespace(st_mode=stat.S_IFCHR | 0o660, st_uid=0, st_gid=108)
        identity = (1000, 1000, "pc", "/home/pc", (1000,))

        self.assertFalse(self.tool._identity_can_access_device(device, identity))
        self.assertTrue(self.tool._identity_can_access_device(device, (1000, 1000, "pc", "/home/pc", (1000, 108))))

    def test_transient_drvfs_serial_read_error_does_not_abort_the_vm(self):
        """QEMU keeps running when WSL briefly reports ENODATA on its log."""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = self.tool.preview_paths("drvfs-read", root)
            paths.work_root.mkdir(parents=True)
            paths.serial_log.write_text("", encoding="utf-8")

            process = mock.Mock()
            process.poll.side_effect = [None, 0]
            process.wait.return_value = 0

            with mock.patch.object(self.tool.subprocess, "Popen", return_value=process), mock.patch.object(
                Path, "read_text", side_effect=OSError(errno.ENODATA, "No data available")
            ), mock.patch.object(self.tool.time, "sleep"):
                result = self.tool._run_interactive_qemu(
                    ("qemu",), paths, {}, 60, None
                )

            self.assertEqual(result["returncode"], 0)
            self.assertIsNone(result["desktop_ready_after_seconds"])


if __name__ == "__main__":
    unittest.main()
