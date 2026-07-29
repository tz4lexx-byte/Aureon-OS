"""Structural contracts for honest Plasma and Full HD preview readiness."""

from __future__ import annotations

import json
import importlib.machinery
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OVERLAY = ROOT / "system" / "desktop" / "overlays"
SESSION_PROBE = OVERLAY / "usr" / "libexec" / "aureon" / "aureon-session-ready"
SYSTEM_PROBE = OVERLAY / "usr" / "libexec" / "aureon" / "aureon-wait-desktop-ready"
READY_SERVICE = OVERLAY / "usr" / "lib" / "systemd" / "system" / "aureon-desktop-ready.service"
READY_TMPFILES = OVERLAY / "usr" / "lib" / "tmpfiles.d" / "aureon-desktop-ready.conf"
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
        self.assertEqual(launcher.count("/usr/libexec/aureon/aureon-session-ready &"), 1)
        self.assertIn("probe_pid=$!", launcher)
        self.assertIn('kill -0 "$probe_pid"', launcher)
        self.assertIn("probe-exited-without-state", launcher)

    def test_probe_lock_is_owned_and_duplicate_cannot_remove_valid_lock(self):
        session = SESSION_PROBE.read_text(encoding="utf-8")

        self.assertIn('probe_lock="${state_dir}/session-probe.lock"', session)
        self.assertIn('probe_owner="${probe_lock}/pid"', session)
        duplicate = session.index('if ! mkdir "$probe_lock"')
        owner_write = session.index("printf '%s\\n' \"$$\" > \"$probe_owner\"")
        trap_install = session.index("trap cleanup_lock EXIT")
        self.assertLess(duplicate, owner_write)
        self.assertLess(owner_write, trap_install)
        self.assertNotIn("trap 'rmdir", session)
        self.assertIn("duplicate-probe owner_pid=", session)

    def test_state_publication_is_atomic_and_private(self):
        session = SESSION_PROBE.read_text(encoding="utf-8")

        self.assertIn('temporary_file="${state_dir}/session-state.$$"', session)
        self.assertIn('chmod 0600 "$temporary_file"', session)
        self.assertIn('mv -f "$temporary_file" "$state_file"', session)
        self.assertIn("state-write-failed", session)
        self.assertIn("state-publish-failed", session)

    def test_session_and_system_consumer_share_stable_private_runtime_directory(self):
        launcher = PLASMA_LAUNCHER.read_text(encoding="utf-8")
        session = SESSION_PROBE.read_text(encoding="utf-8")
        bridge = SYSTEM_PROBE.read_text(encoding="utf-8")
        service = READY_SERVICE.read_text(encoding="utf-8")

        state_default = "${AUREON_DESKTOP_STATE_DIR:-/run/aureon-desktop-ready}"
        for source in (launcher, session, bridge):
            self.assertIn(state_default, source)
        self.assertNotIn("/run/user/1000/aureon", bridge)
        self.assertIn("RuntimeDirectory=aureon-desktop-ready", service)
        self.assertIn("RuntimeDirectoryMode=0700", service)
        self.assertIn("User=aureon", service)
        self.assertIn("Group=aureon", service)
        self.assertEqual(
            READY_TMPFILES.read_text(encoding="utf-8").strip(),
            "d /run/aureon-desktop-ready 0700 aureon aureon -",
        )

    def test_consumer_reads_private_state_and_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)
            (state_dir / "session-state").write_text(
                "probe_state=passed\nfailure_reason=none\n", encoding="utf-8"
            )
            (state_dir / "session-ready").touch()
            for report in ("baseline", "core", "services"):
                (state_dir / f"{report}.json").write_text(
                    '{"status":"ready"}\n', encoding="utf-8"
                )
            os.chmod(state_dir, 0o700)
            environment = {
                **os.environ,
                "AUREON_DESKTOP_STATE_DIR": str(state_dir),
            }
            result = subprocess.run(
                ["/bin/sh", str(SYSTEM_PROBE)],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("probe_state=passed", result.stdout)
        self.assertIn("AUREON_DESKTOP_READY", result.stdout)

    def test_absent_probe_has_immediate_explicit_reason_when_state_directory_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "not-created"
            environment = {
                **os.environ,
                "AUREON_DESKTOP_STATE_DIR": str(missing),
            }
            first = subprocess.run(
                ["/bin/sh", str(SYSTEM_PROBE)],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            second = subprocess.run(
                ["/bin/sh", str(SYSTEM_PROBE)],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )

        self.assertEqual(first.returncode, 1)
        self.assertEqual(first.stderr, second.stderr)
        self.assertIn("reason=state-directory-missing", first.stderr)

    def test_ready_marker_requires_responsive_kwin_and_plasma(self):
        session = SESSION_PROBE.read_text(encoding="utf-8")
        bridge = SYSTEM_PROBE.read_text(encoding="utf-8")
        service = READY_SERVICE.read_text(encoding="utf-8")

        self.assertIn("pgrep", session)
        self.assertIn("kwin_wayland", session)
        self.assertIn("plasmashell", session)
        self.assertIn("org.freedesktop.DBus.Peer.Ping", session)
        self.assertIn("aureon-plasma-layout-ready", session)
        self.assertIn('fail_probe "plasma-panel-layout-invalid"', session)
        self.assertIn("panel-observation=", session)
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
        self.assertIn("reason=probe-state-missing", bridge)
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
