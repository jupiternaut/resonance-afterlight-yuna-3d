from __future__ import annotations

import json
import sys
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CharacterPackage" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import build_hair_target_schema_v1 as schema  # noqa: E402


CHARACTER_PACKAGE = REPO_ROOT / "CharacterPackage"
HAIR_DESIGN_SCHEMA_PATH = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "hair_design_schema_v1.json"


class HairTargetSchemaV1Tests(unittest.TestCase):
    def test_builds_three_layer_schema_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = schema.build_report(Path(tmp), update_reports=False)

            self.assertEqual(report["route"], "build_hair_target_schema_v1")
            self.assertTrue((Path(tmp) / "strict_hair_core_mask.png").exists())
            self.assertTrue((Path(tmp) / "soft_hair_silhouette_mask.png").exists())
            self.assertTrue((Path(tmp) / "forbidden_nonhair_zone_mask.png").exists())
            self.assertTrue((Path(tmp) / "candidate_vs_schema_overlay.png").exists())
            self.assertTrue((Path(tmp) / "schema_debug_contact_sheet.png").exists())
            self.assertTrue((Path(tmp) / "hair_target_schema_v1_report.json").exists())
            self.assertGreater(report["strict_core_area"], 0)
            self.assertGreater(report["soft_silhouette_area"], report["strict_core_area"])
            self.assertGreater(report["forbidden_zone_area"], 0)

    def test_current_candidate_is_evaluated_against_schema_not_raw_union_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = schema.build_report(Path(tmp), update_reports=False)

            self.assertIn(
                report["candidate_target_schema_status"],
                {
                    "schema_gate_passed_manual_review_required",
                    "schema_gate_passed_manual_review_failed_underfilled",
                    "failed_target_schema_alignment",
                    "schema_not_ready_for_rebuild",
                },
            )
            self.assertTrue(report["schema_ready_for_ribbon_rebuild"])
            self.assertFalse(report["ready_for_cloth_seam_surface"])
            self.assertLessEqual(report["core_body_overlap_ratio"], schema.SCHEMA_THRESHOLDS["core_body_overlap_ratio"])
            saved = json.loads((Path(tmp) / "hair_target_schema_v1_report.json").read_text(encoding="utf-8"))
            if report["candidate_target_schema_status"] == "schema_gate_passed_manual_review_required":
                self.assertLess(report["forbidden_candidate_leak_ratio"], schema.SCHEMA_THRESHOLDS["forbidden_candidate_leak_ratio"])
                self.assertGreaterEqual(report["candidate_soft_inside_ratio"], schema.SCHEMA_THRESHOLDS["candidate_soft_inside_ratio"])
                self.assertGreaterEqual(report["candidate_core_coverage_ratio"], schema.SCHEMA_THRESHOLDS["candidate_core_coverage_ratio"])
                self.assertEqual(saved["recommended_next"], "manual_review_authored_hair_ribbons_v0_quality")
            elif report["candidate_target_schema_status"] == "schema_gate_passed_manual_review_failed_underfilled":
                self.assertLess(report["forbidden_candidate_leak_ratio"], schema.SCHEMA_THRESHOLDS["forbidden_candidate_leak_ratio"])
                self.assertGreaterEqual(report["candidate_soft_inside_ratio"], schema.SCHEMA_THRESHOLDS["candidate_soft_inside_ratio"])
                self.assertGreaterEqual(report["candidate_core_coverage_ratio"], schema.SCHEMA_THRESHOLDS["candidate_core_coverage_ratio"])
                self.assertFalse(report["non_degenerate_hair_coverage_passed"])
                self.assertEqual(saved["recommended_next"], "build_art_directed_hair_ribbons_v1")
            else:
                self.assertGreater(report["forbidden_candidate_leak_ratio"], schema.SCHEMA_THRESHOLDS["forbidden_candidate_leak_ratio"])
                self.assertEqual(saved["recommended_next"], "fix_hair_ribbons_to_schema_v1")

    def test_current_candidate_fails_non_degenerate_underfilled_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = schema.build_report(Path(tmp), update_reports=False)

            self.assertEqual(report["candidate_target_schema_status"], "schema_gate_passed_manual_review_failed_underfilled")
            self.assertFalse(report["non_degenerate_hair_coverage_passed"])
            self.assertLess(report["candidate_visible_area_ratio"], schema.SCHEMA_THRESHOLDS["candidate_visible_area_ratio"])
            self.assertLess(report["soft_silhouette_coverage_ratio"], schema.SCHEMA_THRESHOLDS["soft_silhouette_coverage_ratio"])
            self.assertLess(report["bangs_presence_ratio"], schema.SCHEMA_THRESHOLDS["bangs_presence_ratio"])
            self.assertGreater(report["component_count"], schema.SCHEMA_THRESHOLDS["component_count_max"])
            self.assertIn("per_group_visible_pixel_count", report)
            self.assertIn("per_group_soft_inside_ratio", report)
            self.assertIn("candidate passes leak/alignment metrics by becoming too sparse", report["non_degenerate_hair_coverage_reason"])

    def test_hair_design_schema_v1_defines_required_design_contract(self) -> None:
        design = json.loads(HAIR_DESIGN_SCHEMA_PATH.read_text(encoding="utf-8"))

        self.assertEqual(design["schema"], "hair_design_schema_v1")
        self.assertIn("bangs_primary", design["required_primary_groups"])
        self.assertIn("side_hair_left_primary", design["required_primary_groups"])
        self.assertIn("side_hair_right_primary", design["required_primary_groups"])
        self.assertIn("back_hair_mass", design["required_primary_groups"])
        self.assertIn("secondary_strands", design)
        self.assertIn("flyaway_strands", design)
        self.assertGreaterEqual(len(design["scalp_anchor_points"]), 4)
        self.assertGreaterEqual(len(design["depth_groups"]), 3)
        self.assertTrue(design["forbidden_face_occlusion_zones"])
        self.assertIn("allowed_silhouette_expansion", design)
        self.assertEqual(design["blocked_route"], "cloth_seam_surface")

    def test_schema_report_records_estimated_sources_and_confidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = schema.build_report(Path(tmp), update_reports=False)

            layers = report["layers"]
            self.assertTrue(layers["strict_hair_core"]["estimated"])
            self.assertTrue(layers["soft_hair_silhouette"]["estimated"])
            self.assertTrue(layers["forbidden_nonhair_zone"]["estimated"])
            self.assertIn("confidence_score", layers["strict_hair_core"])
            self.assertIn("v8 front hair masks", layers["strict_hair_core"]["source"])
            self.assertIn("v8 face mask", layers["forbidden_nonhair_zone"]["source"])

    def test_schema_report_records_visible_mass_and_manual_review_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = schema.build_report(Path(tmp), update_reports=False)

            for field in (
                "candidate_front_visible_hair_mass",
                "primary_group_presence_passed",
                "yaw30_hair_readability",
                "side_hair_readability",
                "manual_visual_review_status",
            ):
                self.assertIn(field, report)
            if report["candidate_target_schema_status"] == "failed_target_schema_alignment":
                self.assertEqual(report["manual_visual_review_status"], "blocked_by_target_schema_alignment")
            elif report["candidate_front_visible_hair_mass"]:
                self.assertIn(
                    report["manual_visual_review_status"],
                    {"pending_user_review_visible_mass_refined", "failed_visible_mass_readability_gate"},
                )

    def test_temp_run_does_not_change_v8_inputs(self) -> None:
        watched = [
            CHARACTER_PACKAGE / "semantic_layer_v8" / "specs" / "yuna_semantic_layer_v8.json",
            *(CHARACTER_PACKAGE / "semantic_layer_v8" / "masks" / "front" / f"{part_id}.png" for part_id in schema.HAIR_PART_IDS),
        ]
        before = {path: sha256(path.read_bytes()).hexdigest() for path in watched}
        with tempfile.TemporaryDirectory() as tmp:
            schema.build_report(Path(tmp), update_reports=False)
        after = {path: sha256(path.read_bytes()).hexdigest() for path in watched}

        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
