"""Safety and structure tests for the Aureon USB builder."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "aureon-build-usb"


def load_tool():
    name = "aureon_build_usb_under_test"
    loader = importlib.machinery.SourceFileLoader(name, str(TOOL))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


class UsbBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool()

    def test_plan_is_read_only_and_never_accepts_a_disk(self):
        identifier = "usb-unit-" + uuid.uuid4().hex[:8]
        output = self.tool.paths(identifier)
        payload = self.tool.plan(identifier, self.tool.default_update_image_ref())

        self.assertFalse(output["build"].exists())
        self.assertFalse(output["image"].exists())
        self.assertFalse(payload["installer_safety"]["automatic_disk_selection"])
        self.assertFalse(payload["installer_safety"]["automatic_partitioning"])
        self.assertFalse(payload["installer_safety"]["physical_drive_argument_accepted"])
        self.assertFalse(payload["installer_resources"]["live_root_heavy_workspace"])
        self.assertEqual(
            payload["installer_resources"]["bootc_workspace"],
            "target-filesystem:/var/tmp/aureon-bootc-install",
        )
        self.assertTrue(payload["installer_resources"]["workspace_removed_after_install"])
        self.assertTrue(payload["update_channel"]["configured"])
        self.assertEqual(
            payload["update_channel"]["image_ref"],
            "ghcr.io/tz4lexx-byte/aureon-os:stable",
        )
        self.assertTrue(payload["update_channel"]["flatpak_updates"])

    def test_update_channel_requires_a_remote_tagged_oci_reference(self):
        reference = "ghcr.io/example/aureon:stable"

        self.assertEqual(self.tool.update_image_ref(reference), reference)
        with self.assertRaises(Exception):
            self.tool.update_image_ref("localhost/aureon:stable")
        with self.assertRaises(Exception):
            self.tool.update_image_ref("ghcr.io/example/aureon@sha256:deadbeef")

        payload = self.tool.plan("usb-update-plan", reference)
        self.assertTrue(payload["update_channel"]["configured"])
        self.assertEqual(payload["update_channel"]["image_ref"], reference)

    def test_repository_update_channel_is_public_and_never_forces_reboot(self):
        channel = json.loads(
            (ROOT / "packaging" / "update-channel.json").read_text()
        )

        self.assertEqual(
            channel["stable_image"],
            "ghcr.io/tz4lexx-byte/aureon-os:stable",
        )
        self.assertEqual(
            channel["source_repository"],
            "https://github.com/tz4lexx-byte/Aureon-OS",
        )
        self.assertEqual(channel["visibility"], "public")
        self.assertFalse(channel["automatic_reboot"])

    def test_installer_has_live_install_and_basic_graphics_entries(self):
        config = (ROOT / "system/installer/overlays/usr/lib/image-builder/bootc/iso.yaml").read_text()

        self.assertIn("Probar Aureon sin instalar", config)
        self.assertIn("Instalar Aureon (modo texto)", config)
        self.assertIn("inst.text", config)
        self.assertIn("nomodeset", config)
        self.assertEqual(config.count("enforcing=0"), 3)

    def test_installer_initramfs_includes_seccomp_runtime(self):
        containerfile = (ROOT / "system/installer/Containerfile").read_text()

        self.assertIn("readlink -f /usr/lib64/libseccomp.so.2", containerfile)
        self.assertIn('--install "/usr/lib64/libseccomp.so.2 ${seccomp}"', containerfile)

    def test_kickstart_never_selects_or_erases_a_disk(self):
        kickstart = (
            ROOT / "system/installer/overlays/usr/share/anaconda/interactive-defaults.ks"
        ).read_text().lower()

        for forbidden in ("clearpart", "autopart", "ignoredisk", "zerombr"):
            active_lines = [
                line for line in kickstart.splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
            self.assertFalse(any(forbidden in line for line in active_lines))
        self.assertIn("text", kickstart)
        self.assertIn("bootc --source-imgref containers-storage:", kickstart)
        self.assertIn("--target-imgref @@aureon_target_ref@@", kickstart)
        self.assertIn("network --hostname=aureon --no-activate", kickstart)
        self.assertNotIn("--activate", kickstart)

    def test_installer_bootc_wrapper_uses_target_storage_and_reports_activity(self):
        wrapper = ROOT / "system/installer/overlays/usr/local/bin/bootc"
        content = wrapper.read_text()

        self.assertIn('workspace="${target}/var/tmp/aureon-bootc-install"', content)
        self.assertIn('export TMPDIR="${workspace}"', content)
        self.assertIn("bootc activo:", content)
        self.assertIn("sleep 5", content)
        self.assertIn('rm -rf --one-file-system "${workspace}"', content)
        subprocess.run(["bash", "-n", str(wrapper)], check=True)

    def test_live_only_services_and_network_permissions_are_scoped_to_installer(self):
        bootupd_dropin = (
            ROOT
            / "system/installer/overlays/usr/lib/systemd/system"
            / "bootloader-update.service.d/20-aureon-live.conf"
        ).read_text()
        live_network = (
            ROOT
            / "system/installer/overlays/etc/polkit-1/rules.d"
            / "49-aureon-live-network.rules"
        ).read_text()
        anaconda_dropin = (
            ROOT
            / "system/installer/overlays/usr/lib/systemd/system"
            / "anaconda.service.d/20-aureon-installer.conf"
        ).read_text()

        self.assertIn("ConditionPathExists=!/run/initramfs/live", bootupd_dropin)
        self.assertIn('subject.user == "aureon"', live_network)
        self.assertIn("org.freedesktop.NetworkManager.", live_network)
        self.assertIn("/usr/local/bin", anaconda_dropin)
        self.assertFalse(
            (
                ROOT
                / "system/desktop/overlays/etc/polkit-1/rules.d"
                / "49-aureon-live-network.rules"
            ).exists()
        )

    def test_profile_declares_steam_and_obs(self):
        profile = json.loads((ROOT / "packaging/desktop-profile.json").read_text())
        apps = {item["app_id"] for item in profile["preinstalled_flatpaks"]}
        self.assertEqual(apps, {"com.valvesoftware.Steam", "com.obsproject.Studio"})


if __name__ == "__main__":
    unittest.main()
