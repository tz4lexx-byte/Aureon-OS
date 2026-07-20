"""Unit tests for the isolated Aureon desktop-preview launcher."""

from __future__ import annotations

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
        self.assertEqual(plan["execution"]["guest_network"], "disabled")
        self.assertFalse(paths.build_root.exists())
        self.assertFalse(paths.image_root.exists())
        self.assertFalse(paths.work_root.exists())

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

    def test_qemu_gui_command_keeps_the_guest_offline_and_uses_only_virtual_devices(self):
        paths = self.tool.preview_paths("desktop-command")
        command = self.tool.qemu_command(paths, "/usr/bin/qemu-system-x86_64", "tcg")
        joined = " ".join(command)
        portable_joined = joined.replace("\\", "/")

        self.assertIn("-display gtk,gl=off", joined)
        self.assertIn("-device virtio-vga", joined)
        self.assertIn("-device usb-kbd,bus=xhci.0", joined)
        self.assertIn("-nic none", joined)
        self.assertIn("readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd", portable_joined)
        self.assertIn(str(paths.overlay), joined)
        self.assertNotIn("-virtfs", joined)
        self.assertNotIn("PhysicalDrive", joined)
        self.assertNotIn("/dev/sd", joined)

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
        self.assertIn("startplasma-wayland", (REPOSITORY_ROOT / "system" / "desktop" / "overlays" / "etc" / "greetd" / "config.toml").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
