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

from semantic_actuators.curve_bundle_hair_candidate_v1 import (  # noqa: E402
    ACTUATOR_NAME,
    PRIMARY_GROUPS,
    build_curve_bundle_hair,
    run_curve_bundle_hair_candidate_v1,
)
from semantic_actuators.state import ActuatorPaths  # noqa: E402
from semantic_actuators.validation_contract import validate_hair_candidate_report  # noqa: E402


CHARACTER_PACKAGE = REPO_ROOT / "CharacterPackage"


class CurveBundleHairCandidateV1Tests(unittest.TestCase):
    def test_builds_curve_ribbons_from_primary_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ribbons, records, design_summary = build_curve_bundle_hair(CHARACTER_PACKAGE, Path(tmp))

        self.assertGreaterEqual(len(ribbons), 24)
        self.assertTrue(set(PRIMARY_GROUPS).issubset({ribbon.group_id for ribbon in ribbons}))
        self.assertGreaterEqual(len({ribbon.depth_group for ribbon in ribbons}), 3)
        self.assertTrue(all(ribbon.primitive_intent for ribbon in ribbons))
        self.assertTrue(all(ribbon.mesh.vertices for ribbon in ribbons))
        self.assertTrue(all(len(ribbon.mesh.vertices) == len(ribbon.mesh.uvs) for ribbon in ribbons))
        self.assertTrue(all(record.primitive_intent.get("anchor_point") for record in records if record.role == "primary"))
        self.assertFalse(design_summary["replace_in_beauty_glb"])
        self.assertFalse(design_summary["ready_for_cloth_seam_surface"])

    def test_curve_ribbons_preserve_curve_bundle_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ribbons, _records, _summary = build_curve_bundle_hair(CHARACTER_PACKAGE, Path(tmp))

        primary = [ribbon for ribbon in ribbons if ribbon.group_id in set(PRIMARY_GROUPS)]
        self.assertTrue(primary)
        for ribbon in primary[:8]:
            intent = ribbon.primitive_intent or {}
            self.assertEqual(intent["primitive_type"], "primary_curve_bundle_component_ribbon")
            self.assertIn("source_curve_path", intent)
            self.assertIn("generated_curve_path", intent)
            self.assertIn("width_profile", intent)
            self.assertIn("taper_profile", intent)
            self.assertIn("depth_group", intent)
            self.assertEqual(intent["scalp_anchor_metadata"]["copy_external_geometry"], False)

    def test_temp_actuator_writes_report_without_touching_v8(self) -> None:
        watched = [
            CHARACTER_PACKAGE / "semantic_layer_v8" / "specs" / "yuna_semantic_layer_v8.json",
            CHARACTER_PACKAGE / "semantic_layer_v8" / "exports" / "yuna_semantic_layer_v8.glb",
        ]
        before = {path: sha256(path.read_bytes()).hexdigest() for path in watched}
        with tempfile.TemporaryDirectory() as tmp, mock.patch(
            "semantic_actuators.curve_bundle_hair_candidate_v1.blender_export_glb",
            return_value={"status": "skipped_with_reason", "reason": "test_blender_skip", "glb_exists": False},
        ):
            out = Path(tmp) / "curve_bundle_candidate_v1"
            paths = ActuatorPaths(
                repo_root=REPO_ROOT,
                character_package=CHARACTER_PACKAGE,
                output_dir=out,
                spec_path=out / "specs" / "yuna_curve_bundle_hair_v1.json",
                obj_path=out / "exports" / "yuna_curve_bundle_hair_v1.obj",
                glb_path=out / "exports" / "yuna_curve_bundle_hair_v1.glb",
                report_path=out / "validation_report.json",
            )
            result = run_curve_bundle_hair_candidate_v1(paths)

            self.assertTrue(paths.obj_path.exists())
            self.assertTrue(paths.obj_path.with_suffix(".mtl").exists())
            self.assertTrue(paths.report_path.exists())
            report = json.loads(paths.report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["actuator"], ACTUATOR_NAME)
            self.assertEqual(report["part_id"], "hair")
            self.assertFalse(report["validation"]["replace_in_beauty_glb"])
            self.assertFalse(report["validation"]["ready_for_cloth_seam_surface"])
            self.assertEqual(result.part_id, "hair")

        after = {path: sha256(path.read_bytes()).hexdigest() for path in watched}
        self.assertEqual(after, before)

    def test_contract_accepts_curve_bundle_candidate_statuses(self) -> None:
        report = {
            "actuator": ACTUATOR_NAME,
            "part_id": "hair",
            "status": "curve_bundle_candidate_failed_visual_review",
            "mesh_summary": {"vertices": 12, "faces": 6, "group_count": 4, "ribbon_count": 24, "depth_group_count": 4},
            "validation": {
                "independent_objects": True,
                "has_ribbon_meshes": True,
                "has_depth_groups": True,
                "has_spring_hook_metadata": True,
                "side_back_are_soft_constraints": True,
                "replace_in_beauty_glb": False,
                "alpha_material_valid": True,
                "black_alpha_leak_ratio": 0.0,
                "candidate_black_pixel_ratio": 0.0,
                "face_occlusion_ratio": 0.0,
                "non_hair_occlusion_ratio": 0.0,
                "hair_mask_iou": 0.0,
                "outside_hair_mask_ratio": 0.0,
                "candidate_is_hair_only": False,
                "raw_candidate_is_hair_only": False,
                "hair_union_body_overlap_ratio": 1.0,
                "hair_union_face_overlap_ratio": 1.0,
                "hair_union_weapon_overlap_ratio": 1.0,
                "hair_union_target_is_clean": False,
                "hair_target_quality": "target_schema_v1_curve_bundle_gate",
                "clean_hair_mask_iou": 0.1,
                "clean_outside_hair_mask_ratio": 0.0,
                "clean_candidate_is_hair_only": True,
                "hair_union_projection_valid": False,
                "candidate_geometry_alignment_valid": False,
                "clean_candidate_geometry_alignment_valid": False,
                "coordinate_alignment_gate": "target_schema_v1_source_space_checked",
                "coordinate_mapping_status": "target_schema_v1_source_space_checked",
                "alignment_failure_reason": "synthetic visual failure",
                "baseline_framing_valid": False,
                "overlay_alignment_valid": False,
                "visual_sanity_status": "curve_bundle_candidate_failed_visual_review",
                "visual_sanity_reason": "synthetic visual failure",
            },
        }

        self.assertEqual(validate_hair_candidate_report(report), [])


if __name__ == "__main__":
    unittest.main()
