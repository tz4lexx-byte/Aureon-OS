"""Structural contracts for honest Plasma and Full HD preview readiness."""

from __future__ import annotations

import json
import importlib.machinery
import importlib.util
import shutil
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OVERLAY = ROOT / "system" / "desktop" / "overlays"
SESSION_PROBE = OVERLAY / "usr" / "libexec" / "aureon" / "aureon-session-ready"
SYSTEM_PROBE = OVERLAY / "usr" / "libexec" / "aureon" / "aureon-wait-desktop-ready"
READY_SERVICE = OVERLAY / "usr" / "lib" / "systemd" / "system" / "aureon-desktop-ready.service"
PLASMA_LAUNCHER = OVERLAY / "usr" / "libexec" / "aureon" / "aureon-plasma-session"
DISPLAY_PROBE = OVERLAY / "usr" / "libexec" / "aureon" / "aureon-display"
LAYOUT_PROBE = OVERLAY / "usr" / "libexec" / "aureon" / "aureon-plasma-layout-ready"
READINESS_AUTOSTART = OVERLAY / "etc" / "xdg" / "autostart" / "aureon-session-ready.desktop"


def load_display_probe():
    name = "aureon_display_probe_under_test"
    loader = importlib.machinery.SourceFileLoader(name, str(DISPLAY_PROBE))
    spec = importlib.util.spec_from_loader(name, loader)
    if spec is None:
        raise RuntimeError("Unable to load display probe")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


class DesktopReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.display_probe = load_display_probe()

    def test_probe_scripts_have_valid_shell_syntax(self):
        bash = shutil.which("bash")
        if bash is None:
            self.skipTest("bash syntax validation runs inside the Ubuntu WSL builder")
        for script in (SESSION_PROBE, SYSTEM_PROBE, PLASMA_LAUNCHER):
            result = subprocess.run(
                [bash, "-n", str(script)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_launcher_starts_readiness_independently_of_xdg_autostart(self):
        launcher = PLASMA_LAUNCHER.read_text(encoding="utf-8")
        probe_start = launcher.index("/usr/libexec/aureon/aureon-session-ready &")
        plasma_start = launcher.index("/usr/bin/startplasma-wayland")

        self.assertLess(probe_start, plasma_start)
        self.assertIn("session-probe.lock", SESSION_PROBE.read_text(encoding="utf-8"))

    def test_ready_marker_requires_responsive_kwin_and_plasma(self):
        session = SESSION_PROBE.read_text(encoding="utf-8")
        bridge = SYSTEM_PROBE.read_text(encoding="utf-8")
        service = READY_SERVICE.read_text(encoding="utf-8")

        self.assertIn("pgrep", session)
        self.assertIn("kwin_wayland", session)
        self.assertIn("plasmashell", session)
        self.assertIn("org.freedesktop.DBus.Peer.Ping", session)
        self.assertIn("aureon-plasma-layout-ready", session)
        self.assertTrue(LAYOUT_PROBE.is_file())
        self.assertNotIn("AUREON_DESKTOP_READY", session)
        self.assertIn("session-ready", bridge)
        self.assertIn("AUREON_EVIDENCE", bridge)
        for report in ("baseline", "core", "services"):
            self.assertIn("aureonctl " + (report if report == "baseline" else report + " doctor"), session)
        self.assertIn("AUREON_DESKTOP_READY", bridge)
        self.assertIn("ExecStart=/usr/libexec/aureon/aureon-wait-desktop-ready", service)
        self.assertIn("TimeoutStartSec=300", service)
        self.assertNotIn("ExecStart=/usr/bin/echo", service)
        self.assertIn("probe_state=failed", bridge)
        self.assertIn("AUREON_DESKTOP_DIAGNOSTICS_BEGIN", bridge)
        self.assertIn("aureon-session-ready", READINESS_AUTOSTART.read_text(encoding="utf-8"))

    def test_full_hd_is_requested_and_runtime_observation_is_required(self):
        profile = json.loads((ROOT / "packaging" / "display-profile.json").read_text(encoding="utf-8"))
        request = profile["preview_request"]
        wallpaper = OVERLAY / "usr" / "share" / "wallpapers" / "AureonLiquidGlass" / "contents" / "images" / "1920x1080.svg"
        svg = ET.fromstring(wallpaper.read_text(encoding="utf-8"))

        self.assertEqual((request["width"], request["height"], request["refresh_hz"]), (1920, 1080, 60))
        self.assertTrue(profile["policy"]["runtime_observation_required_before_claiming_full_hd"])
        self.assertEqual(svg.attrib["width"], "1920")
        self.assertEqual(svg.attrib["height"], "1080")
        self.assertEqual(svg.attrib["viewBox"], "0 0 1920 1080")
        self.assertIn("kscreen-doctor", SESSION_PROBE.read_text(encoding="utf-8"))
        self.assertNotIn("video=", (OVERLAY / "usr" / "lib" / "bootc" / "kargs.d" / "20-aureon-desktop-serial.toml").read_text(encoding="utf-8"))

    def test_display_probe_selects_and_observes_exact_full_hd_at_sixty_hz(self):
        payload = {
            "outputs": [
                {
                    "connected": True,
                    "enabled": True,
                    "priority": 1,
                    "id": 1,
                    "name": "Virtual-1",
                    "currentModeId": "7",
                    "scale": 1.0,
                    "modes": [
                        {"id": "6", "size": {"width": 1280, "height": 720}, "refreshRate": 60.0},
                        {"id": "7", "size": {"width": 1920, "height": 1080}, "refreshRate": 59.94},
                    ],
                }
            ]
        }

        result = self.display_probe.inspect(payload)

        self.assertEqual(result["state"], "observed-1920x1080@60")
        self.assertEqual((result["output_id"], result["mode_id"]), ("1", "7"))

    def test_display_probe_rejects_available_but_inactive_full_hd(self):
        payload = {
            "outputs": [
                {
                    "connected": True,
                    "enabled": True,
                    "id": 1,
                    "name": "Virtual-1",
                    "currentModeId": "6",
                    "scale": 1.0,
                    "modes": [
                        {"id": "6", "size": {"width": 1280, "height": 720}, "refreshRate": 60.0},
                        {"id": "7", "size": {"width": 1920, "height": 1080}, "refreshRate": 60.0},
                    ],
                }
            ]
        }

        self.assertEqual(self.display_probe.inspect(payload)["state"], "mode-available-not-active")


if __name__ == "__main__":
    unittest.main()
