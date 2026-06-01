from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CHARACTER_PACKAGE = REPO_ROOT / "CharacterPackage"
TOOLS_DIR = CHARACTER_PACKAGE / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from separate_hair_debug_beauty_and_add_style_gate_v1 import (  # noqa: E402
    BEAUTY_OUTPUTS,
    DEBUG_OUTPUTS,
    STYLE_TARGET_PATH,
)


class HairStyleGateV1Tests(unittest.TestCase):
    def test_style_target_exists_and_defines_yuna_direction(self) -> None:
        self.assertTrue(STYLE_TARGET_PATH.exists())
        data = json.loads(STYLE_TARGET_PATH.read_text(encoding="utf-8"))
        self.assertEqual(data["id"], "yuna_cinematic_sci_fi_heroine_v0")
        self.assertEqual(data["direction"]["summary"], "premium cinematic sci-fi heroine")
        palette = data["palette"]
        for key in ("graphite_black", "pearl_white", "gunmetal", "cyan_accent"):
            self.assertIn(key, palette)
        requirements = data["hair_requirements"]
        for key in (
            "large_coherent_back_hair_mass",
            "soft_curved_bangs",
            "left_right_side_drape",
            "scalp_anchored_flow",
            "transparent_tapered_tips",
            "no_barcode_strips",
            "no_straight_guide_bars",
            "no_fragmented_shards",
            "no_copied_commercial_character_design",
        ):
            self.assertIs(requirements[key], True)

    def test_debug_and_beauty_outputs_are_split(self) -> None:
        for _name, (_source, target) in DEBUG_OUTPUTS.items():
            self.assertTrue(target.exists(), target)
            self.assertGreater(target.stat().st_size, 0)
            self.assertIn("debug", target.name)
        for _name, (_source, target) in BEAUTY_OUTPUTS.items():
            self.assertTrue(target.exists(), target)
            self.assertGreater(target.stat().st_size, 0)
            self.assertIn("beauty", target.name)
            self.assertNotIn("debug", target.name)
        contact_sheet = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "curve_bundle_candidate_v1" / "validation_ci" / "beauty_contact_sheet.png"
        self.assertTrue(contact_sheet.exists())
        self.assertGreater(contact_sheet.stat().st_size, 0)

    def test_reports_include_style_gate_fields_and_keep_replacement_blocked(self) -> None:
        report_path = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "curve_bundle_candidate_v1" / "validation_report.json"
        ci_path = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "curve_bundle_candidate_v1" / "validation_ci" / "validation_ci_report.json"
        for path in (report_path, ci_path):
            data = json.loads(path.read_text(encoding="utf-8"))
            style_gate = data["style_gate"]
            self.assertEqual(style_gate["style_target"], "CharacterPackage/style_targets/yuna_cinematic_sci_fi_heroine_v0.json")
            self.assertIs(style_gate["debug_guides_hidden_in_beauty"], True)
            self.assertIs(style_gate["beauty_render_exists"], True)
            self.assertIs(style_gate["guide_leak_into_beauty"], False)
            self.assertIn(
                style_gate["style_target_status"],
                {
                    "failed_debug_leak_into_beauty",
                    "style_gate_failed_manual_review_required",
                    "beauty_candidate_manual_review_required",
                },
            )
            self.assertIs(style_gate["candidate_beauty_manual_review_required"], True)
            self.assertIs(style_gate["replace_in_beauty_glb"], False)
            self.assertIs(style_gate["ready_for_cloth_seam_surface"], False)

    def test_candidate_contract_exposes_style_gate_fields(self) -> None:
        report_path = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "curve_bundle_candidate_v1" / "validation_report.json"
        data = json.loads(report_path.read_text(encoding="utf-8"))
        validation = data["validation"]
        for field in (
            "style_target",
            "debug_guides_hidden_in_beauty",
            "beauty_render_exists",
            "guide_leak_into_beauty",
            "style_target_status",
            "reads_as_hair",
            "front_hair_silhouette_quality",
            "yaw30_hair_likeness",
            "side_hair_likeness",
            "candidate_beauty_manual_review_required",
        ):
            self.assertIn(field, validation)
        self.assertIs(validation["replace_in_beauty_glb"], False)
        self.assertIs(validation["ready_for_cloth_seam_surface"], False)

    def test_v8_diff_is_empty(self) -> None:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--", "CharacterPackage/semantic_layer_v8"],
            cwd=str(REPO_ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
