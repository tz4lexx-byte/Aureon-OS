"""Static safety checks for the intentionally gated Phase 0 bootc recipe."""

from __future__ import annotations

import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTAINERFILE = REPOSITORY_ROOT / "system" / "Containerfile"
MANIFEST = REPOSITORY_ROOT / "packaging" / "phase0-image-manifest.template.yaml"
READINESS_UNIT = (
    REPOSITORY_ROOT
    / "system"
    / "overlays"
    / "usr"
    / "lib"
    / "systemd"
    / "system"
    / "aureon-phase0-ready.service"
)
SHUTDOWN_UNIT = (
    REPOSITORY_ROOT
    / "system"
    / "overlays"
    / "usr"
    / "lib"
    / "systemd"
    / "system"
    / "aureon-phase0-shutdown.service"
)
SERIAL_KARGS = (
    REPOSITORY_ROOT
    / "system"
    / "overlays"
    / "usr"
    / "lib"
    / "bootc"
    / "kargs.d"
    / "20-aureon-phase0-serial.toml"
)
NESTED_CONTAINERS_CONFIG = REPOSITORY_ROOT / "packaging" / "phase0-containers.conf"
NESTED_STORAGE_CONFIG = REPOSITORY_ROOT / "packaging" / "phase0-container-storage.conf"


class PhaseZeroRecipeTests(unittest.TestCase):
    def test_recipe_uses_reviewed_immutable_inputs_with_an_explicit_gate(self):
        containerfile = CONTAINERFILE.read_text(encoding="utf-8")
        manifest = MANIFEST.read_text(encoding="utf-8")

        base_reference = (
            "quay.io/fedora/fedora-bootc@sha256:"
            "86cd97f1e7962e30f52f35ae1c0719299df4f681492b133ea4bcdb74d154fb92"
        )
        builder_reference = (
            "ghcr.io/osbuild/image-builder-cli@sha256:"
            "700368cfa3e78b25fb4fe02a87cedf1a5bc0cb142d7287c8c6fff72fd09228f5"
        )
        self.assertIn("FROM " + base_reference, containerfile)
        self.assertFalse(
            any(line.lstrip().upper().startswith("ARG ") for line in containerfile.splitlines())
        )
        self.assertIn("enabled: true", manifest)
        self.assertIn(base_reference, manifest)
        self.assertIn(builder_reference, manifest)

    def test_overlay_has_explicit_guest_side_permissions(self):
        containerfile = CONTAINERFILE.read_text(encoding="utf-8")

        self.assertIn("chmod 0755 /usr/lib/aureon /usr/lib/bootc /usr/lib/bootc/kargs.d", containerfile)
        self.assertIn("chmod 0644 /usr/lib/aureon/phase0-release", containerfile)
        self.assertIn("/usr/lib/bootc/kargs.d/20-aureon-phase0-serial.toml", containerfile)
        self.assertIn("/usr/lib/systemd/system/aureon-phase0-ready.service", containerfile)
        self.assertIn("/usr/lib/systemd/system/aureon-phase0-shutdown.service", containerfile)

    def test_readiness_unit_is_vm_only_and_hardened(self):
        unit = READINESS_UNIT.read_text(encoding="utf-8")

        self.assertIn("ConditionVirtualization=vm", unit)
        self.assertIn("ExecStart=/usr/bin/echo AUREON_PHASE0_READY", unit)
        self.assertIn("PrivateNetwork=yes", unit)
        self.assertIn("ProtectSystem=strict", unit)
        self.assertIn("NoNewPrivileges=yes", unit)
        self.assertIn("UMask=0077", unit)

    def test_shutdown_unit_requests_poweroff_only_after_readiness(self):
        unit = SHUTDOWN_UNIT.read_text(encoding="utf-8")

        self.assertIn("ConditionVirtualization=vm", unit)
        self.assertIn("Requires=aureon-phase0-ready.service", unit)
        self.assertIn("After=aureon-phase0-ready.service", unit)
        self.assertIn("ExecStart=/usr/bin/systemctl --no-block poweroff", unit)
        self.assertIn("PrivateNetwork=yes", unit)
        self.assertIn("ProtectSystem=strict", unit)

    def test_serial_kernel_arguments_are_declared_for_headless_smoke(self):
        kargs = SERIAL_KARGS.read_text(encoding="utf-8")

        self.assertIn('"console=tty0"', kargs)
        self.assertIn('"console=ttyS0,115200n8"', kargs)

    def test_nested_builder_configuration_uses_dedicated_storage_and_no_network(self):
        containers_config = NESTED_CONTAINERS_CONFIG.read_text(encoding="utf-8")
        storage_config = NESTED_STORAGE_CONFIG.read_text(encoding="utf-8")

        self.assertIn('netns = "none"', containers_config)
        self.assertIn("no_hosts = true", containers_config)
        self.assertIn('graphroot = "/var/lib/aureon-phase0-podman/storage"', storage_config)
        self.assertIn('runroot = "/run/aureon-phase0-podman"', storage_config)


if __name__ == "__main__":
    unittest.main()
