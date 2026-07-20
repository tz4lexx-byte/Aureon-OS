from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "system"
    / "desktop"
    / "overlays"
    / "usr"
    / "libexec"
    / "aureon"
    / "aureon-baseline"
)


class AureonBaselineTests(unittest.TestCase):
    maxDiff = None

    def test_script_exists(self) -> None:
        self.assertTrue(SCRIPT.is_file(), f"No existe: {SCRIPT}")

    def test_bash_syntax(self) -> None:
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"Error de sintaxis Bash:\n{result.stderr}",
        )

    def test_report_contract(self) -> None:
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=(
                f"El medidor terminó con código {result.returncode}.\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            ),
        )

        expected_keys = {
            "report_format",
            "timestamp_utc",
            "os_pretty_name",
            "kernel",
            "architecture",
            "uptime_seconds",
            "memory_total_mib",
            "memory_available_mib",
            "memory_used_estimated_mib",
            "process_count",
            "running_services",
            "failed_units",
            "root_used_mib",
            "root_available_mib",
            "cgroup_mode",
            "ntsync_device",
            "ntsync_module",
            "selinux",
            "vulkaninfo",
        }

        found_keys = {
            line.split("=", 1)[0]
            for line in result.stdout.splitlines()
            if "=" in line and not line.startswith((" ", "\t"))
        }

        missing = sorted(expected_keys - found_keys)

        self.assertFalse(
            missing,
            msg=f"Faltan campos obligatorios: {missing}\n\n{result.stdout}",
        )

        self.assertIn(
            "report_format=aureon-baseline-v1",
            result.stdout,
        )
        self.assertIn("[top_memory_processes]", result.stdout)
        self.assertIn("[failed_units]", result.stdout)

    def test_no_network_transmission_commands(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8").lower()

        forbidden = (
            "curl",
            "wget",
            "nc",
            "netcat",
            "socat",
            "ssh",
        )

        detected = [
            command
            for command in forbidden
            if re.search(rf"\b{re.escape(command)}\b", source)
        ]

        self.assertEqual(
            detected,
            [],
            msg=(
                "El medidor contiene comandos de red no permitidos: "
                f"{detected}"
            ),
        )

        self.assertNotRegex(
            source,
            r"https?://",
            msg="El medidor contiene una dirección HTTP o HTTPS.",
        )
if __name__ == "__main__":
    unittest.main()
