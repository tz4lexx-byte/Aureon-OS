"""Structural tests for Aureon's local, vector-based Liquid Glass theme."""

from __future__ import annotations

import configparser
import importlib.machinery
import importlib.util
import io
import json
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OVERLAY = ROOT / "system" / "desktop" / "overlays"
CONTROL = OVERLAY / "usr" / "libexec" / "aureon" / "aureonctl"


def load_control_module():
    name = "aureon_liquid_glass_control_under_test"
    loader = importlib.machinery.SourceFileLoader(name, str(CONTROL))
    spec = importlib.util.spec_from_loader(name, loader)
    if spec is None:
        raise RuntimeError("Unable to load the Aureon control plane")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


class LiquidGlassThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.control = load_control_module()
        cls.theme_root = OVERLAY / "usr" / "share" / "plasma" / "desktoptheme" / "AureonLiquidGlass"
        cls.wallpaper = OVERLAY / "usr" / "share" / "wallpapers" / "AureonLiquidGlass" / "contents" / "images" / "1920x1080.svg"

    def invoke(self, arguments):
        output = io.StringIO()
        status = self.control.main(arguments, output=output)
        return status, json.loads(output.getvalue())

    def test_profile_catalog_offers_carbon_by_default_and_liquid_glass(self):
        catalog = json.loads((ROOT / "packaging" / "appearance-profiles.json").read_text(encoding="utf-8"))
        authority = json.loads((ROOT / "packaging" / "aureon-control-plane.json").read_text(encoding="utf-8"))

        self.assertEqual(catalog["default_style"], "carbon")
        self.assertEqual(set(catalog["styles"]), {"carbon", "liquid-glass"})
        self.assertEqual(catalog["styles"]["carbon"]["color_scheme"], "AureonCarbon")
        self.assertEqual(catalog["styles"]["liquid-glass"]["color_scheme"], "AureonLiquidGlass")
        self.assertEqual(catalog["default_profile"], "off")
        self.assertEqual(set(catalog["profiles"]), {"off", "lite", "balanced", "ultra"})
        self.assertEqual(authority["actions"]["desktop.apply-appearance"]["authority"], "A")
        self.assertTrue(authority["actions"]["desktop.apply-appearance"]["reversible"])

    def test_appearance_plan_is_local_and_does_not_apply_settings(self):
        status, report = self.invoke(["appearance", "plan", "--profile", "balanced"])

        self.assertEqual(status, 0)
        result = report["result"]
        self.assertEqual(result["state"], "plan-only")
        self.assertEqual(result["theme"], "AureonLiquidGlass")
        self.assertIn("download assets", result["does_not"])
        self.assertIn("override a user choice after initial setup", result["does_not"])

    def test_color_schemes_are_installed_and_default_configs_select_carbon(self):
        colors = OVERLAY / "usr" / "share" / "color-schemes" / "AureonLiquidGlass.colors"
        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str
        parser.read_string(colors.read_text(encoding="utf-8"))

        self.assertEqual(parser["General"]["Name"], "Aureon Liquid Glass")
        self.assertIn("Colors:Window", parser)
        self.assertIn("Colors:Selection", parser)
        self.assertEqual(parser["Colors:Window"]["BackgroundNormal"], "22,32,57")
        carbon = configparser.ConfigParser(interpolation=None)
        carbon.optionxform = str
        carbon.read_string(
            (OVERLAY / "usr" / "share" / "color-schemes" / "AureonCarbon.colors").read_text(encoding="utf-8")
        )
        self.assertEqual(carbon["General"]["Name"], "Aureon Carbon")
        self.assertIn("ColorScheme=AureonCarbon", (OVERLAY / "etc" / "skel" / ".config" / "kdeglobals").read_text(encoding="utf-8"))
        self.assertIn("name=AureonCarbon", (OVERLAY / "etc" / "skel" / ".config" / "plasmarc").read_text(encoding="utf-8"))

    def test_theme_metadata_and_vector_assets_are_local_and_valid_xml(self):
        metadata = json.loads((self.theme_root / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["KPlugin"]["Id"], "AureonLiquidGlass")
        self.assertEqual(metadata["KPlugin"]["License"], "GPL-3.0-or-later")
        look_and_feel = json.loads(
            (OVERLAY / "usr" / "share" / "plasma" / "look-and-feel" / "org.aureon.desktop" / "metadata.json").read_text(encoding="utf-8")
        )
        self.assertEqual(look_and_feel["KPackageStructure"], "Plasma/LookAndFeel")

        for asset in (self.theme_root / "widgets" / "panel-background.svg", self.wallpaper):
            root = ET.fromstring(asset.read_text(encoding="utf-8"))
            self.assertEqual(root.tag.rsplit("}", 1)[-1], "svg")
            source = asset.read_text(encoding="utf-8").lower().replace("http://www.w3.org/2000/svg", "")
            self.assertNotIn("http://", source)
            self.assertNotIn("https://", source)
            self.assertNotIn("<script", source)
            self.assertNotIn("<image", source)

    def test_panel_and_kwin_keep_the_glass_effect_bounded(self):
        layout = (OVERLAY / "usr" / "share" / "plasma" / "look-and-feel" / "org.aureon.desktop" / "contents" / "layouts" / "org.kde.plasma.desktop-layout.js").read_text(encoding="utf-8")
        kwin = (OVERLAY / "etc" / "skel" / ".config" / "kwinrc").read_text(encoding="utf-8")

        self.assertIn('panel.opacity = "translucent"', layout)
        self.assertIn('panel.lengthMode = "fill"', layout)
        self.assertIn('panel.hiding = "none"', layout)
        self.assertIn("panel.floating = false", layout)
        self.assertIn("blurEnabled=true", kwin)
        self.assertIn("contrastEnabled=true", kwin)
        self.assertIn("BlurStrength=6", kwin)

    def test_one_time_wallpaper_helper_never_uses_network_or_host_paths(self):
        helper = OVERLAY / "usr" / "libexec" / "aureon" / "aureon-apply-appearance"
        readiness = OVERLAY / "usr" / "libexec" / "aureon" / "aureon-session-ready"
        helper_source = helper.read_text(encoding="utf-8").lower()

        self.assertIn("aureon-apply-appearance", readiness.read_text(encoding="utf-8"))
        self.assertIn("plasma-apply-wallpaperimage", helper_source)
        self.assertIn("plasma-apply-lookandfeel --apply org.aureon.desktop --resetlayout", helper_source)
        self.assertIn("carbon-v2-sharp-wallpaper-applied", helper_source)
        self.assertIn("/usr/share/wallpapers/aureoncarbon/", helper_source)
        self.assertIn('writeconfig("fillmode",2)', helper_source)
        self.assertIn('writeconfig("blur",false)', helper_source)
        for forbidden in ("curl", "wget", "sudo", "physicaldrive", "/mnt/c", "rm -rf"):
            self.assertNotIn(forbidden, helper_source)

    def test_container_marks_the_appearance_helper_executable(self):
        containerfile = (ROOT / "system" / "desktop" / "Containerfile").read_text(encoding="utf-8")
        self.assertIn("aureon-apply-appearance", containerfile)


if __name__ == "__main__":
    unittest.main()
