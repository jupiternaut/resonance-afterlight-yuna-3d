from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CharacterPackage" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from semantic_actuators.leg_quad_loop_retopo_proxy import (  # noqa: E402
    ACTUATOR_NAME,
    RADIAL_SEGMENTS,
    RING_COUNT,
    alpha_bbox,
    build_leg_components,
    run_leg_quad_loop_retopo_proxy,
    write_obj,
)
from semantic_actuators.state import ActuatorPaths  # noqa: E402
from semantic_actuators.validation_contract import validate_leg_candidate_report  # noqa: E402


CHARACTER_PACKAGE = REPO_ROOT / "CharacterPackage"
LEG_L_TEXTURE = CHARACTER_PACKAGE / "semantic_layer_v8" / "textures" / "leg_L_visual_panel.png"
LEG_R_TEXTURE = CHARACTER_PACKAGE / "semantic_layer_v8" / "textures" / "leg_R_visual_panel.png"


class LegQuadLoopRetopoProxyTests(unittest.TestCase):
    def test_alpha_bbox_finds_leg_visual_panels(self) -> None:
        self.assertIsNotNone(alpha_bbox(LEG_L_TEXTURE))
        self.assertIsNotNone(alpha_bbox(LEG_R_TEXTURE))

    def test_leg_components_have_quad_loop_mesh_data(self) -> None:
        components = build_leg_components(CHARACTER_PACKAGE)

        self.assertEqual(len(components), 2)
        self.assertTrue(all(component.mesh.section_count == RING_COUNT for component in components))
        self.assertTrue(all(len(component.mesh.faces) == (RING_COUNT - 1) * RADIAL_SEGMENTS for component in components))
        self.assertTrue(all(len(component.mesh.uvs) == len(component.mesh.vertices) for component in components))
        self.assertTrue(all({"knee", "ankle"}.issubset(component.loop_rings) for component in components))

    def test_obj_writer_creates_left_and_right_leg_objects(self) -> None:
        components = build_leg_components(CHARACTER_PACKAGE)
        with tempfile.TemporaryDirectory() as tmp:
            obj_path = Path(tmp) / "legs.obj"
            mtl_path = write_obj(obj_path, components)

            self.assertTrue(obj_path.exists())
            self.assertTrue(mtl_path.exists())
            text = obj_path.read_text(encoding="utf-8")
            self.assertIn("o leg_L_retopo_proxy_candidate", text)
            self.assertIn("o leg_R_retopo_proxy_candidate", text)
            self.assertIn("usemtl leg_L_front_texture", text)
            self.assertIn("usemtl leg_R_front_texture", text)

    def test_contract_validator_rejects_missing_loop_metadata(self) -> None:
        errors = validate_leg_candidate_report(
            {
                "actuator": ACTUATOR_NAME,
                "part_id": "legs",
                "status": "generated_with_warnings",
                "mesh_summary": {
                    "vertices": 1,
                    "faces": 1,
                    "component_count": 2,
                    "ring_count": RING_COUNT,
                    "radial_segments": RADIAL_SEGMENTS,
                    "quad_faces_only": True,
                },
                "validation": {
                    "independent_objects": True,
                    "has_quad_loop_topology": True,
                    "has_knee_ankle_loop_metadata": False,
                    "replace_in_beauty_glb": False,
                },
            }
        )
        self.assertIn("leg candidate must include knee/ankle loop metadata", errors)

    def test_actuator_can_write_leg_report_to_temp_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "semantic_layer_v9_leg"
            paths = ActuatorPaths(
                repo_root=REPO_ROOT,
                character_package=CHARACTER_PACKAGE,
                output_dir=out,
                spec_path=out / "specs" / "yuna_semantic_layer_v9_leg.json",
                obj_path=out / "exports" / "yuna_semantic_layer_v9_leg.obj",
                glb_path=out / "exports" / "yuna_semantic_layer_v9_leg.glb",
                report_path=out / "validation_report.json",
            )
            result = run_leg_quad_loop_retopo_proxy(paths)

            self.assertNotEqual(result.status, "failed")
            self.assertTrue(paths.spec_path.exists())
            self.assertTrue(paths.obj_path.exists())
            self.assertTrue(paths.report_path.exists())
            report = json.loads(paths.report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["route"], "semantic_layer_v9_leg_quad_loop_retopo_proxy_v0")
            self.assertEqual(report["part_id"], "legs")
            self.assertEqual(report["actuator"], ACTUATOR_NAME)
            self.assertFalse(report["validation"]["replace_in_beauty_glb"])
            self.assertEqual(report["validation"]["deformation_test_status"], "not_run_requires_skinning_stage")


if __name__ == "__main__":
    unittest.main()
