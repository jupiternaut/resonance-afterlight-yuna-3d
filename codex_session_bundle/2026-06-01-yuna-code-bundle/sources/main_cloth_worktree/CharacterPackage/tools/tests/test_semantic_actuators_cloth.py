from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CharacterPackage" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from semantic_actuators.cloth_seam_surface import (  # noqa: E402
    ACTUATOR_NAME,
    REVIEW_VARIANT_CONFIGS,
    TARGET_PART_IDS,
    build_cloth_panels,
    combined_seam_metadata,
    combine_gate_metrics,
    run_cloth_review_pack,
    run_cloth_seam_surface,
    write_cloth_purity_assets,
    write_obj,
    write_side_volume_diagnostic,
)
from semantic_actuators.state import ActuatorPaths  # noqa: E402
from semantic_actuators.validation_contract import validate_cloth_candidate_report  # noqa: E402


CHARACTER_PACKAGE = REPO_ROOT / "CharacterPackage"


class ClothSeamSurfaceActuatorTests(unittest.TestCase):
    def test_target_masks_and_textures_exist(self) -> None:
        for part_id in TARGET_PART_IDS:
            self.assertTrue((CHARACTER_PACKAGE / "semantic_layer_v8" / "masks" / "front" / f"{part_id}.png").exists())
            self.assertTrue((CHARACTER_PACKAGE / "semantic_layer_v8" / "textures" / f"{part_id}.png").exists())

    def test_cloth_panels_have_requested_parts_and_quad_surfaces(self) -> None:
        panels = build_cloth_panels(CHARACTER_PACKAGE)

        self.assertEqual([panel.source_part_id for panel in panels], list(TARGET_PART_IDS))
        self.assertTrue(all(panel.mesh.faces for panel in panels))
        self.assertTrue(all(len(face) == 4 for panel in panels for face in panel.mesh.faces))
        self.assertTrue(all(len(panel.mesh.uvs) == len(panel.mesh.vertices) for panel in panels))
        self.assertTrue(all(panel.mesh.thickness > 0 for panel in panels))
        self.assertTrue(all(any(material == 1 for material in panel.mesh.face_materials) for panel in panels))

    def test_seam_metadata_includes_required_handoff_routes(self) -> None:
        seams = combined_seam_metadata(build_cloth_panels(CHARACTER_PACKAGE))

        self.assertIn("left", seams["shoulder_anchors"])
        self.assertIn("right", seams["shoulder_anchors"])
        self.assertTrue(seams["cape_roots"]["left"])
        self.assertTrue(seams["cape_roots"]["right"])
        self.assertTrue(seams["skirt_waist_seam"])
        self.assertEqual(set(seams["lower_cloth_edge"]), set(TARGET_PART_IDS))

    def test_obj_writer_creates_panel_objects_and_seam_guides(self) -> None:
        panels = build_cloth_panels(CHARACTER_PACKAGE)
        seams = combined_seam_metadata(panels)
        with tempfile.TemporaryDirectory() as tmp:
            obj_path = Path(tmp) / "cloth.obj"
            mtl_path = write_obj(obj_path, panels, seams)

            self.assertTrue(obj_path.exists())
            self.assertTrue(mtl_path.exists())
            text = obj_path.read_text(encoding="utf-8")
            self.assertIn("o jacket_outer_cloth_seam_surface_v0", text)
            self.assertIn("o cape_left_cloth_seam_surface_v0", text)
            self.assertIn("o cape_right_cloth_seam_surface_v0", text)
            self.assertIn("o skirt_front_cloth_seam_surface_v0", text)
            self.assertIn("o cloth_shoulder_anchor_line", text)
            self.assertIn("o cloth_skirt_waist_seam", text)
            self.assertIn("usemtl cloth_solidify_edge_material", text)

    def test_purity_and_side_volume_reports_write_required_assets(self) -> None:
        panels = build_cloth_panels(CHARACTER_PACKAGE)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "semantic_layer_v9_cloth"
            paths = ActuatorPaths(
                repo_root=REPO_ROOT,
                character_package=CHARACTER_PACKAGE,
                output_dir=out,
                spec_path=out / "specs" / "yuna_semantic_layer_v9_cloth.json",
                obj_path=out / "exports" / "yuna_semantic_layer_v9_cloth.obj",
                glb_path=out / "exports" / "yuna_semantic_layer_v9_cloth.glb",
                report_path=out / "validation_report.json",
            )
            purity = write_cloth_purity_assets(paths, panels)
            side_volume = write_side_volume_diagnostic(paths, panels)
            seams = combined_seam_metadata(panels)
            metrics = combine_gate_metrics(purity, side_volume, seams)

            self.assertTrue((out / "validation_ci" / "cloth_target_mask_union.png").exists())
            self.assertTrue((out / "validation_ci" / "cloth_forbidden_noncloth_zone.png").exists())
            self.assertTrue((out / "validation_ci" / "cloth_candidate_vs_target_overlay.png").exists())
            self.assertTrue((out / "validation_ci" / "cloth_purity_report.json").exists())
            self.assertTrue((out / "validation_ci" / "cloth_side_volume_debug.png").exists())
            self.assertTrue((out / "validation_ci" / "cloth_depth_span_report.json").exists())
            self.assertIn("cloth_mask_purity_ratio", metrics)
            self.assertTrue(metrics["cloth_side_volume_present"])
            self.assertTrue(metrics["cloth_edge_thickness_present"])
            self.assertTrue(metrics["cloth_body_attachment_valid"])
            self.assertGreaterEqual(metrics["seam_count"], 4)
            self.assertGreaterEqual(metrics["anchor_count"], 10)

    def test_contract_validator_rejects_unblocked_integration_claim(self) -> None:
        errors = validate_cloth_candidate_report(
            {
                "actuator": ACTUATOR_NAME,
                "part_id": "cloth",
                "status": "generated_with_warnings",
                "mesh_summary": {
                    "vertices": 1,
                    "faces": 1,
                    "component_count": 4,
                    "target_parts": list(TARGET_PART_IDS),
                    "quad_faces_only": True,
                },
                "validation": {
                    "independent_objects": True,
                    "has_cloth_surfaces": True,
                    "has_shoulder_anchors": True,
                    "has_cape_roots": True,
                    "has_skirt_waist_seam": True,
                    "has_lower_cloth_edge": True,
                    "side_back_are_soft_constraints": True,
                    "replace_in_beauty_glb": False,
                    "v8_beauty_replaced": False,
                    "candidate_only": True,
                    "dcc_handoff_only": True,
                    "production_cloth_topology": False,
                    "ready_for_cloth_integration": True,
                    "hair_route_still_blocks_cloth_integration": False,
                    "overlay_front_is_acceptance_gate": False,
                    "cloth_mask_purity_ratio": 1.0,
                    "non_cloth_texture_leak_ratio": 0.0,
                    "cloth_side_volume_present": True,
                    "cloth_edge_thickness_present": True,
                    "cloth_panel_curvature_score": 0.08,
                    "cloth_drape_depth_span": 0.12,
                    "cloth_body_attachment_valid": True,
                    "seam_count": 8,
                    "anchor_count": 19,
                    "silhouette_readability_front": 0.88,
                    "yaw30_cloth_readability": 0.65,
                    "side_volume_readability": 0.58,
                    "material_alpha_stability": 1.0,
                    "cloth_front_visual_candidate_status": "manual_review_required",
                    "cloth_dcc_handoff_status": "manual_review_required_candidate_only_hair_blocked",
                },
            }
        )

        self.assertIn("cloth candidate must not mark cloth integration unblocked", errors)
        self.assertIn("cloth candidate must preserve the hair-route integration blocker", errors)

    def test_actuator_can_write_cloth_report_to_temp_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch(
            "semantic_actuators.cloth_seam_surface.blender_export_glb",
            return_value={"status": "skipped_with_reason", "reason": "test_blender_skip", "glb_exists": False},
        ), mock.patch(
            "semantic_actuators.cloth_seam_surface.run_blender_validation_ci",
            return_value={"status": "skipped_with_reason", "reason": "test_blender_skip", "screenshots": {}},
        ):
            out = Path(tmp) / "semantic_layer_v9_cloth"
            paths = ActuatorPaths(
                repo_root=REPO_ROOT,
                character_package=CHARACTER_PACKAGE,
                output_dir=out,
                spec_path=out / "specs" / "yuna_semantic_layer_v9_cloth.json",
                obj_path=out / "exports" / "yuna_semantic_layer_v9_cloth.obj",
                glb_path=out / "exports" / "yuna_semantic_layer_v9_cloth.glb",
                report_path=out / "validation_report.json",
            )
            result = run_cloth_seam_surface(paths)

            self.assertNotEqual(result.status, "failed")
            self.assertTrue(paths.spec_path.exists())
            self.assertTrue(paths.obj_path.exists())
            self.assertTrue(paths.obj_path.with_suffix(".mtl").exists())
            self.assertTrue(paths.report_path.exists())
            report = json.loads(paths.report_path.read_text(encoding="utf-8"))
            spec = json.loads(paths.spec_path.read_text(encoding="utf-8"))
            self.assertEqual(report["route"], "semantic_layer_v9_cloth_seam_surface_v0")
            self.assertEqual(report["part_id"], "cloth")
            self.assertEqual(report["actuator"], ACTUATOR_NAME)
            self.assertEqual(report["status"], "manual_review_required")
            self.assertEqual(report["mesh_summary"]["component_count"], 4)
            self.assertFalse(report["validation"]["replace_in_beauty_glb"])
            self.assertFalse(report["validation"]["ready_for_cloth_integration"])
            self.assertTrue(report["validation"]["hair_route_still_blocks_cloth_integration"])
            self.assertGreaterEqual(report["validation"]["cloth_mask_purity_ratio"], 0.90)
            self.assertLessEqual(report["validation"]["non_cloth_texture_leak_ratio"], 0.035)
            self.assertTrue(report["validation"]["cloth_side_volume_present"])
            self.assertTrue(report["validation"]["cloth_edge_thickness_present"])
            self.assertTrue(report["validation"]["cloth_body_attachment_valid"])
            self.assertGreaterEqual(report["validation"]["seam_count"], 4)
            self.assertGreaterEqual(report["validation"]["anchor_count"], 10)
            self.assertIn("yaw30_cloth_readability", report["validation"])
            self.assertIn("side_volume_readability", report["validation"])
            self.assertIn("material_alpha_stability", report["validation"])
            self.assertIn("cloth_volume_and_purity_gate_v1", report["validation"]["validation_ci"])
            self.assertTrue(report["seams"]["cape_roots"]["left"])
            self.assertTrue(report["seams"]["solidify"]["cape_left"]["has_front_back_depth_separation"])
            self.assertFalse(spec["part"]["replace_in_beauty_glb"])
            self.assertTrue(spec["part"]["candidate_only"])

    def test_review_pack_writes_three_variant_contract_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch(
            "semantic_actuators.cloth_seam_surface.blender_export_glb",
            return_value={"status": "skipped_with_reason", "reason": "test_blender_skip", "glb_exists": False},
        ), mock.patch(
            "semantic_actuators.cloth_seam_surface.run_blender_validation_ci",
            return_value={"status": "skipped_with_reason", "reason": "test_blender_skip", "screenshots": {}},
        ):
            repo_root = Path(tmp)
            character_package = repo_root / "CharacterPackage"
            character_package.mkdir()
            (character_package / "semantic_layer_v8").symlink_to(
                CHARACTER_PACKAGE / "semantic_layer_v8",
                target_is_directory=True,
            )

            comparison = run_cloth_review_pack(repo_root, character_package)
            variants_dir = character_package / "semantic_layer_v9_cloth" / "variants"

            self.assertEqual(comparison["status"], "manual_review_required")
            self.assertEqual(comparison["round_count"], len(REVIEW_VARIANT_CONFIGS))
            self.assertFalse(comparison["replace_in_beauty_glb"])
            self.assertFalse(comparison["cloth_integration_ready"])
            self.assertEqual(len(comparison["variants"]), 3)
            self.assertTrue((variants_dir / "cloth_iteration_log.md").exists())
            self.assertTrue((variants_dir / "cloth_variants_contact_sheet.png").exists())
            self.assertTrue((variants_dir / "cloth_variants_comparison_report.json").exists())
            self.assertTrue((variants_dir / "manual_review_cloth_v1.md").exists())
            self.assertIn(comparison["recommended_variant"], {config.name for config in REVIEW_VARIANT_CONFIGS})
            for config in REVIEW_VARIANT_CONFIGS:
                report_path = variants_dir / config.name / "validation_report.json"
                ci_path = variants_dir / config.name / "validation_ci" / "validation_ci_report.json"
                self.assertTrue(report_path.exists())
                self.assertTrue(ci_path.exists())
                report = json.loads(report_path.read_text(encoding="utf-8"))
                self.assertEqual(report["route"], "cloth_seam_surface_v1_review_pack")
                self.assertEqual(report["variant"], config.name)
                self.assertEqual(report["status"], "manual_review_required")
                self.assertFalse(report["validation"]["replace_in_beauty_glb"])
                self.assertFalse(report["validation"]["ready_for_cloth_integration"])


if __name__ == "__main__":
    unittest.main()
