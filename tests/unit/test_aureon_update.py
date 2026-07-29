"""Contracts for the interactive post-install updater."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OVERLAY = ROOT / "system" / "desktop" / "overlays"
UPDATER = OVERLAY / "usr" / "libexec" / "aureon" / "aureon-update"
LAUNCHER = OVERLAY / "usr" / "share" / "applications" / "org.aureon.Update.desktop"
WORKFLOW = ROOT / ".github" / "workflows" / "publish-aureon-update.yml"


class AureonUpdateTests(unittest.TestCase):
    def test_updater_is_valid_shell_and_uses_atomic_system_updates(self):
        source = UPDATER.read_text()

        subprocess.run(["bash", "-n", str(UPDATER)], check=True)
        self.assertIn("bootc upgrade --check", source)
        self.assertIn("bootc upgrade", source)
        self.assertIn("bootc rollback", source)
        self.assertIn("flatpak update --system", source)
        self.assertIn("flatpak uninstall --system --unused", source)

    def test_updater_never_forces_a_reboot(self):
        source = UPDATER.read_text()

        self.assertNotIn("systemctl reboot", source)
        self.assertNotIn("shutdown ", source)
        self.assertIn("No se reiniciará automáticamente.", source)

    def test_desktop_launcher_uses_polkit_and_holds_visible_progress(self):
        source = LAUNCHER.read_text()

        self.assertIn("Name=Actualizar Aureon", source)
        self.assertIn(
            "Exec=konsole --hold -e pkexec /usr/libexec/aureon/aureon-update apply",
            source,
        )

    def test_update_publication_is_explicit_and_targets_the_configured_ghcr_package(self):
        source = WORKFLOW.read_text()

        self.assertIn("workflow_dispatch:", source)
        self.assertNotIn("schedule:", source)
        self.assertIn("packages: write", source)
        self.assertIn("ghcr.io/${{ github.repository_owner }}/aureon-os:", source)
        self.assertIn("buildah push", source)
        self.assertIn("cancel-in-progress: false", source)
        self.assertNotIn("actions/checkout@v", source)


if __name__ == "__main__":
    unittest.main()
