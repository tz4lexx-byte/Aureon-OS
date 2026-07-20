"""Tests for the no-write Aureon phase-control foundation."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "system" / "desktop" / "overlays" / "usr" / "libexec" / "aureon" / "aureonctl"
CATALOG = ROOT / "packaging" / "aureon-control-plane.json"


def load_control_module():
    name = "aureon_control_plane_under_test"
    loader = importlib.machinery.SourceFileLoader(name, str(CONTROL))
    spec = importlib.util.spec_from_loader(name, loader)
    if spec is None:
        raise RuntimeError("Unable to load the Aureon control plane")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


class AureonControlPlaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.control = load_control_module()

    def invoke(self, arguments):
        output = io.StringIO()
        status = self.control.main(arguments, output=output)
        return status, json.loads(output.getvalue())

    def test_every_master_phase_has_a_declared_state(self):
        status, report = self.invoke(["status"])

        self.assertEqual(status, 0)
        self.assertEqual(set(report["phases"]), {str(number) for number in range(33)})
        self.assertTrue(report["all_actions_are_plan_or_diagnostic_only"])

    def test_authority_contract_blocks_dangerous_operations(self):
        status, report = self.invoke(["authority"])

        self.assertEqual(status, 0)
        actions = report["actions"]
        self.assertEqual(actions["driver.install-proprietary"]["authority"], "C")
        self.assertEqual(actions["firmware.update"]["authority"], "C")
        self.assertFalse(actions["firmware.update"]["reversible"])
        self.assertEqual(actions["installer.partition-or-format"]["authority"], "D")
        self.assertEqual(actions["diagnostics.export"]["authority"], "D")

    def test_policy_sources_validate_without_writing(self):
        status, report = self.invoke(["validate"])

        self.assertEqual(status, 0)
        self.assertEqual(report["result"]["state"], "passed")
        self.assertEqual(report["result"]["errors"], [])

    def test_session_plans_never_execute_programs_or_access_devices(self):
        with mock.patch.object(self.control, "_safe_command", side_effect=AssertionError("unexpected inspection")):
            gaming_status, gaming = self.invoke(["gaming", "plan", "--game", "Example Game"])
            streaming_status, streaming = self.invoke(["streaming", "plan", "--encoder", "vaapi"])
            resource_status, resource = self.invoke(["resource", "plan", "--mode", "gaming"])

        self.assertEqual((gaming_status, streaming_status, resource_status), (0, 0, 0))
        self.assertEqual(gaming["result"]["state"], "plan-only")
        self.assertIn("launch a game", gaming["result"]["does_not"])
        self.assertIn("access microphone", streaming["result"]["does_not"])
        self.assertEqual(resource["result"]["state"], "plan-only")

    def test_installer_and_update_stay_plan_only(self):
        for command in ("update", "recovery", "installer"):
            status, report = self.invoke([command, "plan"])
            self.assertEqual(status, 0)
            self.assertIn(report["result"]["state"], {"plan-only", "manual-only"})

    def test_catalog_covers_all_phases_and_has_valid_authority_levels(self):
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.assertEqual([phase["id"] for phase in catalog["phases"]], list(range(33)))
        self.assertTrue(all(action["authority"] in {"A", "B", "C", "D"} for action in catalog["actions"].values()))
        self.assertEqual(catalog["privacy"]["telemetry"], "disabled")
        self.assertEqual(catalog["privacy"]["persistent_hardware_identifier"], "forbidden")

    def test_control_plane_contains_no_mutating_or_network_client_calls(self):
        source = CONTROL.read_text(encoding="utf-8").lower()
        forbidden = ("os.remove", "unlink(", "rmtree", "mkdir(", "write_text", "write_bytes", "shell=true", "curl", "wget")
        found = [token for token in forbidden if token in source]
        self.assertEqual(found, [], msg="Unexpected mutating/network capability: {0}".format(found))

    def test_desktop_image_installs_only_local_control_plane_helpers(self):
        containerfile = (ROOT / "system" / "desktop" / "Containerfile").read_text(encoding="utf-8")
        profile = json.loads((ROOT / "packaging" / "desktop-profile.json").read_text(encoding="utf-8"))
        self.assertIn("aureonctl", containerfile)
        self.assertIn("pciutils", containerfile)
        self.assertIn("usbutils", containerfile)
        for package in profile["core_packages"] + profile["diagnostic_packages"]:
            self.assertIn(package, containerfile)
        self.assertTrue(profile["package_resolution"]["lock_required_for_release"])
        self.assertNotIn("steam", containerfile.lower())
        self.assertNotIn("obs-studio", containerfile.lower())

    def test_named_phase_commands_are_safe_wrappers_around_the_control_plane(self):
        helpers = ("aureon-hardware", "aureon-driver", "aureon-resource", "aureon-integrity", "aureon-integrityctl")
        helper_root = CONTROL.parent
        for helper in helpers:
            source = (helper_root / helper).read_text(encoding="utf-8")
            self.assertIn("exec /usr/bin/aureonctl", source)
            self.assertNotIn("sudo", source)
            self.assertNotIn("curl", source)


if __name__ == "__main__":
    unittest.main()
