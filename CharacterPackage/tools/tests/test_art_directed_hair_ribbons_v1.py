from __future__ import annotations

import json
import sys
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CharacterPackage" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from semantic_actuators.art_directed_hair_ribbons_v1 import (  # noqa: E402
    ACTUATOR_NAME,
    ART_DIRECTED_STATUS,
    HAIR_REVIEW_VARIANTS,
    build_art_directed_hair_ribbons,
    mesh_summary,
    run_art_directed_hair_ribbons_variant,
    run_art_directed_hair_ribbons_v1,
)
from semantic_actuators.state import ActuatorPaths  # noqa: E402


CHARACTER_PACKAGE = REPO_ROOT / "CharacterPackage"


class ArtDirectedHairRibbonsV1Tests(unittest.TestCase):
    def test_review_variants_define_three_manual_review_modes(self) -> None:
        self.assertEqual({"balanced", "fuller", "silhouette"}, set(HAIR_REVIEW_VARIANTS))
        self.assertEqual(HAIR_REVIEW_VARIANTS["balanced"].secondary_strand_count, 10)
        self.assertGreater(HAIR_REVIEW_VARIANTS["fuller"].secondary_strand_count, HAIR_REVIEW_VARIANTS["balanced"].secondary_strand_count)
        self.assertLess(HAIR_REVIEW_VARIANTS["silhouette"].flyaway_strand_count, HAIR_REVIEW_VARIANTS["balanced"].flyaway_strand_count)

    def test_v1_builds_design_groups_secondary_flyaways_and_depths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ribbons, records, design_summary = build_art_directed_hair_ribbons(CHARACTER_PACKAGE, Path(tmp))

        self.assertGreaterEqual(len(ribbons), 20)
        self.assertLessEqual(len(ribbons), 32)
        self.assertGreaterEqual(len({ribbon.depth_group for ribbon in ribbons}), 3)
        self.assertEqual(
            {"bangs_primary", "side_hair_left_primary", "side_hair_right_primary", "back_hair_mass"}.issubset(
                {ribbon.group_id for ribbon in ribbons}
            ),
            True,
        )
        self.assertEqual(sum(1 for ribbon in ribbons if ribbon.group_id == "secondary_strands"), 10)
        self.assertEqual(sum(1 for ribbon in ribbons if ribbon.group_id == "flyaway_strands"), 4)
        self.assertGreaterEqual(len(design_summary["scalp_anchor_points"]), 4)
        self.assertEqual(len(records), 4)

    def test_fuller_variant_temp_run_writes_report_and_keeps_replacement_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch(
            "semantic_actuators.art_directed_hair_ribbons_v1.blender_export_glb",
            return_value={"status": "skipped_with_reason", "reason": "test_blender_skip", "glb_exists": False},
        ):
            out = Path(tmp) / "art_directed_v1_fuller"
            paths = ActuatorPaths(
                repo_root=REPO_ROOT,
                character_package=CHARACTER_PACKAGE,
                output_dir=out,
                spec_path=out / "specs" / "hair_v1_fuller.json",
                obj_path=out / "exports" / "hair_v1_fuller.obj",
                glb_path=out / "exports" / "hair_v1_fuller.glb",
                report_path=out / "validation_report.json",
            )
            result = run_art_directed_hair_ribbons_variant(paths, HAIR_REVIEW_VARIANTS["fuller"])

            self.assertEqual(result.status, ART_DIRECTED_STATUS)
            report = json.loads(paths.report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["variant"], "fuller")
            self.assertFalse(report["validation"]["replace_in_beauty_glb"])
            self.assertFalse(report["validation"]["ready_for_cloth_seam_surface"])
            self.assertEqual(report["mesh_summary"]["design_summary"]["variant"]["name"], "fuller")
            self.assertTrue(paths.obj_path.exists())

    def test_v1_records_primitive_intents_for_art_directed_strands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ribbons, records, design_summary = build_art_directed_hair_ribbons(CHARACTER_PACKAGE, Path(tmp))
            summary = mesh_summary(ribbons, records, design_summary)

        self.assertEqual(summary["art_directed_primitive_intent_count"], len(ribbons))
        self.assertTrue(summary["flow_continuity_passed"])
        self.assertTrue(summary["scalp_anchor_continuity_passed"])
        required_groups = {"bangs_primary", "side_hair_left_primary", "side_hair_right_primary", "back_hair_mass"}
        intent_by_group = {item["group_id"]: item for item in summary["primitive_intents"]}
        self.assertTrue(required_groups.issubset(intent_by_group))
        for group in required_groups:
            intent = intent_by_group[group]
            self.assertIn("anchor_point", intent)
            self.assertGreaterEqual(len(intent["curve_path"]), 4)
            self.assertGreaterEqual(len(intent["width_profile"]), 3)
            self.assertIn("taper", intent)
            self.assertIn("depth_group", intent)
            self.assertIn("material", intent)
            self.assertEqual(intent["material"]["alpha_mode"], "BLEND")

    def test_v1_temp_run_writes_report_and_keeps_v8_unchanged(self) -> None:
        watched = [
            CHARACTER_PACKAGE / "semantic_layer_v8" / "specs" / "yuna_semantic_layer_v8.json",
            *(CHARACTER_PACKAGE / "semantic_layer_v8" / "masks" / "front" / f"{part_id}.png" for part_id in ("back_hair", "side_hair_left", "side_hair_right", "bangs")),
        ]
        before = {path: sha256(path.read_bytes()).hexdigest() for path in watched}
        with tempfile.TemporaryDirectory() as tmp, mock.patch(
            "semantic_actuators.art_directed_hair_ribbons_v1.blender_export_glb",
            return_value={"status": "skipped_with_reason", "reason": "test_blender_skip", "glb_exists": False},
        ):
            out = Path(tmp) / "art_directed_v1"
            paths = ActuatorPaths(
                repo_root=REPO_ROOT,
                character_package=CHARACTER_PACKAGE,
                output_dir=out,
                spec_path=out / "specs" / "hair_v1.json",
                obj_path=out / "exports" / "hair_v1.obj",
                glb_path=out / "exports" / "hair_v1.glb",
                report_path=out / "validation_report.json",
            )
            result = run_art_directed_hair_ribbons_v1(paths)

            self.assertEqual(result.actuator, ACTUATOR_NAME)
            self.assertEqual(result.status, ART_DIRECTED_STATUS)
            self.assertTrue(paths.report_path.exists())
            report = json.loads(paths.report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["route"], "build_art_directed_hair_ribbons_v1")
            self.assertEqual(report["status"], ART_DIRECTED_STATUS)
            self.assertFalse(report["validation"]["replace_in_beauty_glb"])
            self.assertEqual(report["validation"]["manual_visual_review"], "pending_user_review")
            self.assertFalse(report["validation"]["ready_for_cloth_seam_surface"])
            self.assertIn("hair_design_schema_v1.json", report["decision_source"])
            self.assertIn("design_summary", report["mesh_summary"])
            self.assertGreater(report["mesh_summary"]["art_directed_primitive_intent_count"], 0)
            self.assertTrue(report["mesh_summary"]["flow_continuity_passed"])

        after = {path: sha256(path.read_bytes()).hexdigest() for path in watched}
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
