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

    def test_reproducibility_reports_generated_inputs_as_excluded(self):
        status, report = self.invoke(["reproducibility"])

        self.assertEqual(status, 0)
        self.assertEqual(report["result"]["state"], "foundation-passed")
        self.assertTrue(report["result"]["base_image_pinned_by_digest"])
        self.assertTrue(report["result"]["generated_inputs_excluded"])
        self.assertFalse(report["result"]["writes_performed"])

    def test_core_doctor_detects_a_minimal_package_surface(self):
        required = {"state": "available", "installed": list(self.control.CORE_PACKAGES), "missing": []}
        prohibited = {"state": "available", "installed": [], "missing": list(self.control.PROHIBITED_AUTOMATIC_PACKAGES)}
        with mock.patch.object(self.control, "_query_rpm_packages", side_effect=(required, prohibited)):
            status, report = self.invoke(["core", "doctor"])

        self.assertEqual(status, 0)
        self.assertEqual(report["result"]["state"], "passed")
        self.assertEqual(report["result"]["required_missing"], [])
        self.assertEqual(report["result"]["optional_components_found_in_core"], [])

    def test_services_doctor_rejects_an_active_session_only_unit(self):
        unit_count = sum(len(group) for group in self.control.SESSION_ONLY_UNITS.values())
        active = {"state": "failed", "stdout": "active\n" + "inactive\n" * (unit_count - 1)}
        disabled = {"state": "failed", "stdout": "disabled\n" * unit_count}
        with mock.patch.object(self.control, "_safe_command", side_effect=(active, disabled)):
            status, report = self.invoke(["services", "doctor"])

        self.assertEqual(status, 0)
        self.assertEqual(report["result"]["state"], "failed")
        self.assertTrue(report["result"]["violations"])
        self.assertFalse(report["result"]["process_list_observed"])

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
        self.assertEqual(
            {phase["id"]: phase["state"] for phase in catalog["phases"]},
            self.control.PHASE_STATES,
        )

    def test_embedded_core_and_service_catalogues_match_reviewed_sources(self):
        profile = json.loads((ROOT / "packaging" / "desktop-profile.json").read_text(encoding="utf-8"))
        services = json.loads((ROOT / "packaging" / "service-classes.json").read_text(encoding="utf-8"))

        self.assertEqual(set(self.control.CORE_PACKAGES), set(profile["core_packages"]))
        self.assertEqual(
            {name: list(units) for name, units in self.control.SESSION_ONLY_UNITS.items()},
            services["runtime_audit_units"],
        )

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
        self.assertNotIn("dnf -y install steam", containerfile.lower())
        self.assertIn("com.valvesoftware.Steam", containerfile)
        self.assertNotIn("obs-studio", containerfile.lower())

    def test_named_phase_commands_are_safe_wrappers_around_the_control_plane(self):
        helpers = ("aureon-core", "aureon-services", "aureon-hardware", "aureon-driver", "aureon-resource", "aureon-integrity", "aureon-integrityctl")
        helper_root = CONTROL.parent
        for helper in helpers:
            source = (helper_root / helper).read_text(encoding="utf-8")
            self.assertIn("exec /usr/bin/aureonctl", source)
            self.assertNotIn("sudo", source)
            self.assertNotIn("curl", source)


if __name__ == "__main__":
    unittest.main()
