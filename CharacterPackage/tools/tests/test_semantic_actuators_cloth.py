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
    TARGET_PART_IDS,
    build_cloth_panels,
    combined_seam_metadata,
    run_cloth_seam_surface,
    write_obj,
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
            self.assertEqual(report["mesh_summary"]["component_count"], 4)
            self.assertFalse(report["validation"]["replace_in_beauty_glb"])
            self.assertFalse(report["validation"]["ready_for_cloth_integration"])
            self.assertTrue(report["validation"]["hair_route_still_blocks_cloth_integration"])
            self.assertTrue(report["seams"]["cape_roots"]["left"])
            self.assertFalse(spec["part"]["replace_in_beauty_glb"])
            self.assertTrue(spec["part"]["candidate_only"])


if __name__ == "__main__":
    unittest.main()
