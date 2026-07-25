"""Unit and structural tests for Aureon System Overview."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
OVERLAY = ROOT / "system" / "desktop" / "overlays"
CONTROL = OVERLAY / "usr" / "libexec" / "aureon" / "aureonctl"
PLASMOID = OVERLAY / "usr" / "share" / "plasma" / "plasmoids" / "org.aureon.systemoverview"
QML = PLASMOID / "contents" / "ui" / "main.qml"
LAYOUT = (
    OVERLAY
    / "usr"
    / "share"
    / "plasma"
    / "look-and-feel"
    / "org.aureon.desktop"
    / "contents"
    / "layouts"
    / "org.kde.plasma.desktop-layout.js"
)
LAYOUT_PROBE = OVERLAY / "usr" / "libexec" / "aureon" / "aureon-plasma-layout-ready"


def load_control_module():
    name = "aureon_overview_control_under_test"
    loader = importlib.machinery.SourceFileLoader(name, str(CONTROL))
    spec = importlib.util.spec_from_loader(name, loader)
    if spec is None:
        raise RuntimeError("Unable to load aureonctl")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


def load_layout_probe():
    name = "aureon_plasma_layout_probe_under_test"
    loader = importlib.machinery.SourceFileLoader(name, str(LAYOUT_PROBE))
    spec = importlib.util.spec_from_loader(name, loader)
    if spec is None:
        raise RuntimeError("Unable to load Plasma layout probe")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


class AureonSystemOverviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.control = load_control_module()
        cls.layout_probe = load_layout_probe()

    def report(self, files=None, *, cpu=8, storage=None, kernel="6.12.0", architecture="x86_64"):
        fixtures = files or {
            "/etc/os-release": 'NAME="Aureon OS"\nVERSION="2.0 Preview"\n',
            "/proc/meminfo": "MemTotal:       16777216 kB\n",
            "/proc/uptime": "93784.25 100.00\n",
        }
        storage = storage or SimpleNamespace(f_frsize=4096, f_blocks=8_388_608, f_bavail=3_145_728)

        def read_fixture(path, _limit=131_072):
            return fixtures.get(str(path))

        with (
            mock.patch.object(self.control, "_safe_read", side_effect=read_fixture),
            mock.patch.object(self.control.os, "cpu_count", return_value=cpu),
            mock.patch.object(self.control.os, "statvfs", return_value=storage),
            mock.patch.object(self.control.platform, "release", return_value=kernel),
            mock.patch.object(self.control.platform, "machine", return_value=architecture),
        ):
            return self.control._overview_report()

    def test_complete_data_is_formatted_and_healthy(self):
        report = self.report()
        self.assertEqual(
            report["values"],
            {
                "system_name": "Aureon OS",
                "system_version": "2.0 Preview",
                "kernel_version": "6.12.0",
                "architecture": "x86_64",
                "logical_cpus": "8",
                "memory_total": "16.0 GiB",
                "storage_total": "32.0 GiB",
                "storage_available": "12.0 GiB",
                "uptime": "26h 3m",
            },
        )
        self.assertEqual(report["state"], "Healthy")

    def test_partial_data_has_consistent_unknown_values(self):
        report = self.report(files={"/etc/os-release": "VERSION_ID=2\n"})
        self.assertEqual(report["values"]["system_version"], "2")
        self.assertEqual(report["values"]["memory_total"], "Unavailable")
        self.assertEqual(report["values"]["uptime"], "Unavailable")
        self.assertEqual(report["state"], "Limited data")

    def test_unknown_cpu_kernel_and_architecture_are_safe(self):
        report = self.report(cpu=None, kernel="", architecture="")
        self.assertEqual(report["values"]["logical_cpus"], "Unavailable")
        self.assertEqual(report["values"]["kernel_version"], "Unavailable")
        self.assertEqual(report["values"]["architecture"], "Unavailable")

    def test_memory_and_storage_use_mib_for_smaller_values(self):
        files = {
            "/etc/os-release": "VERSION=2\n",
            "/proc/meminfo": "MemTotal:       524288 kB\n",
            "/proc/uptime": "60 0\n",
        }
        storage = SimpleNamespace(f_frsize=4096, f_blocks=131_072, f_bavail=65_536)
        report = self.report(files, storage=storage)
        self.assertEqual(report["values"]["memory_total"], "512.0 MiB")
        self.assertEqual(report["values"]["storage_total"], "512.0 MiB")
        self.assertEqual(report["values"]["storage_available"], "256.0 MiB")

    def test_uptime_formats_minutes_and_hours_deterministically(self):
        self.assertEqual(self.control._human_uptime(3599), "59m")
        self.assertEqual(self.control._human_uptime(3600), "1h 0m")
        self.assertEqual(self.control._human_uptime(7380), "2h 3m")

    def test_provider_read_and_storage_errors_become_unavailable(self):
        with (
            mock.patch.object(self.control, "_safe_read", return_value=None),
            mock.patch.object(self.control.os, "cpu_count", return_value=None),
            mock.patch.object(self.control.os, "statvfs", side_effect=OSError("denied")),
            mock.patch.object(self.control.platform, "release", return_value=""),
            mock.patch.object(self.control.platform, "machine", return_value=""),
        ):
            report = self.control._overview_report()
        self.assertEqual(report["state"], "Unavailable")
        self.assertTrue(all(value == "Unavailable" for key, value in report["values"].items() if key != "system_name"))

    def test_invalid_provider_text_is_ignored(self):
        report = self.report(
            files={
                "/etc/os-release": "not valid",
                "/proc/meminfo": "MemTotal: many kB",
                "/proc/uptime": "not-a-number",
            }
        )
        self.assertEqual(report["values"]["system_version"], "Unavailable")
        self.assertEqual(report["values"]["memory_total"], "Unavailable")
        self.assertEqual(report["values"]["uptime"], "Unavailable")

    def test_overview_contract_is_read_only_and_non_sensitive(self):
        with mock.patch.object(self.control, "_safe_command", side_effect=AssertionError("must not execute commands")):
            report = self.report()
        serialized = json.dumps(report).lower()
        self.assertFalse(report["writes_performed"])
        for key in ("hostname", "username", "token", "password", "serial", "machine_id", "hardware_id"):
            self.assertNotIn(key, serialized)

    def test_cli_entry_point_emits_the_overview_contract(self):
        output = io.StringIO()
        expected = {"state": "Healthy", "values": {"system_name": "Aureon OS"}}
        with mock.patch.object(self.control, "_overview_report", return_value=expected):
            status = self.control.main(["overview"], output=output)
        payload = json.loads(output.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(payload["command"], "overview")
        self.assertEqual(payload["result"], expected)
        self.assertFalse(payload["data_sent"])

    def test_plasma_entry_point_and_async_failure_states_are_present(self):
        metadata = json.loads((PLASMOID / "metadata.json").read_text(encoding="utf-8"))
        qml = QML.read_text(encoding="utf-8")
        layout = LAYOUT.read_text(encoding="utf-8")
        self.assertEqual(metadata["KPlugin"]["Name"], "Aureon System Overview")
        self.assertIn('panel.addWidget("org.aureon.systemoverview")', layout)
        self.assertIn('engine: "executable"', qml)
        self.assertIn('connectedSources: ["/usr/bin/aureonctl overview"]', qml)
        self.assertIn('i18n("Loading…")', qml)
        self.assertGreaterEqual(qml.count('i18n("Unavailable")'), 3)
        self.assertIn("JSON.parse", qml)
        self.assertIn("Accessible.name", qml)
        self.assertIn("ScrollView", qml)

    def test_plasma_6_layout_explicitly_creates_the_complete_bottom_panel(self):
        layout = LAYOUT.read_text(encoding="utf-8")
        plugins = (
            "org.kde.plasma.kickoff",
            "org.kde.plasma.icontasks",
            "org.kde.plasma.systemtray",
            "org.aureon.systemoverview",
            "org.kde.plasma.digitalclock",
        )
        self.assertIn("new Panel", layout)
        self.assertIn('panel.location = "bottom"', layout)
        for plugin in plugins:
            self.assertEqual(layout.count(f'panel.addWidget("{plugin}")'), 1)
        self.assertLess(layout.index("org.kde.plasma.systemtray"), layout.index("org.aureon.systemoverview"))
        self.assertLess(layout.index("org.aureon.systemoverview"), layout.index("org.kde.plasma.digitalclock"))

    def test_widget_failure_is_isolated_after_panel_creation(self):
        layout = LAYOUT.read_text(encoding="utf-8")
        overview = layout.index('panel.addWidget("org.aureon.systemoverview")')
        self.assertLess(layout.index("new Panel"), overview)
        self.assertLess(layout.index("try {"), overview)
        self.assertLess(overview, layout.index("catch (error)"))
        self.assertLess(layout.index("catch (error)"), layout.index("org.kde.plasma.digitalclock"))

    def test_persisted_profile_requires_one_complete_bottom_panel(self):
        appletsrc = """\
[Containments][1]
plugin=org.kde.plasma.folder
[Containments][2]
plugin=org.kde.panel
location=4
[Containments][2][Applets][10]
plugin=org.kde.plasma.kickoff
[Containments][2][Applets][11]
plugin=org.kde.plasma.icontasks
[Containments][2][Applets][12]
plugin=org.kde.plasma.systemtray
[Containments][2][Applets][13]
plugin=org.aureon.systemoverview
[Containments][2][Applets][14]
plugin=org.kde.plasma.digitalclock
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plasma-org.kde.plasma.desktop-appletsrc"
            path.write_text(appletsrc, encoding="utf-8")
            first = self.layout_probe.inspect(path)
            second = self.layout_probe.inspect(path)
        self.assertEqual(first, second)
        self.assertEqual(first["state"], "valid")
        self.assertEqual(first["panel_count"], 1)
        self.assertEqual(first["valid_panel_count"], 1)

    def test_wallpaper_only_or_incomplete_panel_is_not_ready(self):
        fixtures = (
            "[Containments][1]\nplugin=org.kde.plasma.folder\n",
            "[Containments][2]\nplugin=org.kde.panel\nlocation=3\n",
            "[Containments][2]\nplugin=org.kde.panel\nlocation=4\n",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plasma-org.kde.plasma.desktop-appletsrc"
            for fixture in fixtures:
                path.write_text(fixture, encoding="utf-8")
                self.assertEqual(self.layout_probe.inspect(path)["state"], "invalid")


if __name__ == "__main__":
    unittest.main()
