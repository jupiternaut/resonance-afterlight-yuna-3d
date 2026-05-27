from __future__ import annotations

import json
import sys
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path
from unittest import mock

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CharacterPackage" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from semantic_actuators.authored_hair_ribbons import (  # noqa: E402
    ACTUATOR_NAME,
    HAIR_PART_IDS,
    alpha_bbox,
    blender_export_glb,
    build_hair_ribbons,
    build_schema_constrained_group_masks,
    load_hair_sources,
    mask_components,
    run_authored_hair_ribbons,
    write_obj,
)
from semantic_actuators.state import ActuatorPaths  # noqa: E402
from semantic_actuators.validation_contract import validate_hair_candidate_report  # noqa: E402


CHARACTER_PACKAGE = REPO_ROOT / "CharacterPackage"


class AuthoredHairRibbonsActuatorTests(unittest.TestCase):
    def test_four_hair_masks_and_textures_exist(self) -> None:
        for part_id in HAIR_PART_IDS:
            self.assertTrue((CHARACTER_PACKAGE / "semantic_layer_v8" / "masks" / "front" / f"{part_id}.png").exists())
            self.assertTrue((CHARACTER_PACKAGE / "semantic_layer_v8" / "textures" / f"{part_id}.png").exists())

    def test_alpha_bbox_extracts_visible_bounds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "alpha.png"
            image = Image.new("RGBA", (6, 5), (0, 0, 0, 0))
            for x in range(2, 5):
                for y in range(1, 4):
                    image.putpixel((x, y), (255, 255, 255, 255))
            image.save(image_path)

            self.assertEqual(alpha_bbox(image_path), (2, 1, 5, 4))

    def test_load_hair_sources_uses_v8_textures(self) -> None:
        sources = load_hair_sources(CHARACTER_PACKAGE)

        self.assertEqual([source.part_id for source in sources], list(HAIR_PART_IDS))
        self.assertTrue(all(source.mask_path.exists() for source in sources))
        self.assertTrue(all(source.texture_path.exists() for source in sources))
        self.assertTrue(all(source.bbox[2] > source.bbox[0] for source in sources))
        self.assertTrue(all(source.ribbon_count > 0 for source in sources))
        self.assertFalse(any(source.schema_constrained for source in sources))

    def test_schema_group_masks_constrain_hair_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            schema_paths = build_schema_constrained_group_masks(CHARACTER_PACKAGE, Path(tmp) / "group_masks")
            sources = load_hair_sources(CHARACTER_PACKAGE, schema_mask_paths=schema_paths)
            original_sources = {source.part_id: source for source in load_hair_sources(CHARACTER_PACKAGE)}

            self.assertEqual(set(schema_paths), set(HAIR_PART_IDS))
            for source in sources:
                self.assertTrue(source.schema_constrained)
                self.assertTrue(source.mask_path.exists())
                self.assertIn("schema_v1", source.mask_path.name)
                original = original_sources[source.part_id]
                self.assertLess(source.width, original.width)
                self.assertLess(source.depth_spread, original.depth_spread)

    def test_hair_ribbons_have_groups_depths_uvs_and_faces(self) -> None:
        ribbons = build_hair_ribbons(CHARACTER_PACKAGE)

        self.assertGreaterEqual(len(ribbons), 24)
        self.assertGreaterEqual(len({ribbon.depth_group for ribbon in ribbons}), 3)
        self.assertEqual({ribbon.group_id for ribbon in ribbons}, {"hair_back", "hair_side_left", "hair_side_right", "hair_bangs"})
        self.assertTrue(all(len(ribbon.mesh.vertices) == len(ribbon.mesh.uvs) for ribbon in ribbons))
        self.assertTrue(all(len(ribbon.mesh.faces) > 0 for ribbon in ribbons))
        self.assertTrue(all(ribbon.mesh.thickness > 0 for ribbon in ribbons))

    def test_hair_ribbons_use_v8_world_vertical_scale(self) -> None:
        ribbons = build_hair_ribbons(CHARACTER_PACKAGE)
        z_values = [vertex[2] for ribbon in ribbons for vertex in ribbon.mesh.vertices]

        self.assertGreater(max(z_values), 5.5)
        self.assertGreater(min(z_values), 1.8)

    def test_hair_ribbons_are_built_from_local_mask_components(self) -> None:
        ribbons = build_hair_ribbons(CHARACTER_PACKAGE)
        back_components = mask_components(CHARACTER_PACKAGE / "semantic_layer_v8" / "masks" / "front" / "back_hair.png")
        back_component_bboxes = {component.bbox for component in back_components}
        back_ribbon_bboxes = {ribbon.bbox for ribbon in ribbons if ribbon.source_part_id == "back_hair"}

        self.assertTrue(back_ribbon_bboxes)
        self.assertTrue(back_ribbon_bboxes.issubset(back_component_bboxes))

    def test_obj_writer_creates_named_ribbon_objects_and_materials(self) -> None:
        ribbons = build_hair_ribbons(CHARACTER_PACKAGE)
        with tempfile.TemporaryDirectory() as tmp:
            obj_path = Path(tmp) / "hair.obj"
            mtl_path = write_obj(obj_path, ribbons)

            self.assertTrue(obj_path.exists())
            self.assertTrue(mtl_path.exists())
            text = obj_path.read_text(encoding="utf-8")
            self.assertIn("o hair_back_ribbon_01", text)
            self.assertIn("o hair_side_left_ribbon_01", text)
            self.assertIn("o hair_side_right_ribbon_01", text)
            self.assertIn("o hair_bangs_ribbon_01", text)
            self.assertIn("usemtl hair_back_front_texture", text)
            self.assertIn("usemtl hair_ribbon_side_material", text)

    def test_contract_validator_rejects_missing_depth_groups_and_hooks(self) -> None:
        errors = validate_hair_candidate_report(
            {
                "actuator": ACTUATOR_NAME,
                "part_id": "hair",
                "status": "generated_with_warnings",
                "mesh_summary": {"vertices": 1, "faces": 1, "group_count": 4, "ribbon_count": 30, "depth_group_count": 1},
                "validation": {
                    "independent_objects": True,
                    "has_ribbon_meshes": True,
                    "has_depth_groups": False,
                    "has_spring_hook_metadata": False,
                    "side_back_are_soft_constraints": True,
                    "replace_in_beauty_glb": False,
                },
            }
        )
        self.assertIn("hair candidate should preserve at least three depth groups", errors)
        self.assertIn("hair candidate must expose multiple depth groups", errors)
        self.assertIn("hair candidate must include spring hook metadata", errors)

    def test_contract_validator_rejects_missing_visual_sanity_fields(self) -> None:
        errors = validate_hair_candidate_report(
            {
                "actuator": ACTUATOR_NAME,
                "part_id": "hair",
                "status": "generated_with_warnings",
                "mesh_summary": {"vertices": 1, "faces": 1, "group_count": 4, "ribbon_count": 30, "depth_group_count": 4},
                "validation": {
                    "independent_objects": True,
                    "has_ribbon_meshes": True,
                    "has_depth_groups": True,
                    "has_spring_hook_metadata": True,
                    "side_back_are_soft_constraints": True,
                    "replace_in_beauty_glb": False,
                },
            }
        )

        self.assertIn("hair candidate missing visual sanity field: alpha_material_valid", errors)
        self.assertIn("hair candidate missing visual sanity field: visual_sanity_status", errors)

    def test_blender_unavailable_reports_explicit_skip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch("semantic_actuators.authored_hair_ribbons.find_blender", return_value=None):
            glb_path = Path(tmp) / "hair.glb"

            result = blender_export_glb(glb_path, [], REPO_ROOT)

            self.assertEqual(result["status"], "skipped_with_reason")
            self.assertEqual(result["reason"], "blender_not_found")
            self.assertFalse(result["glb_exists"])

    def test_actuator_temp_output_does_not_change_v8_inputs(self) -> None:
        watched = [
            CHARACTER_PACKAGE / "semantic_layer_v8" / "specs" / "yuna_semantic_layer_v8.json",
            *(CHARACTER_PACKAGE / "semantic_layer_v8" / "masks" / "front" / f"{part_id}.png" for part_id in HAIR_PART_IDS),
            *(CHARACTER_PACKAGE / "semantic_layer_v8" / "textures" / f"{part_id}.png" for part_id in HAIR_PART_IDS),
        ]
        before = {path: sha256(path.read_bytes()).hexdigest() for path in watched}
        with tempfile.TemporaryDirectory() as tmp, mock.patch(
            "semantic_actuators.authored_hair_ribbons.blender_export_glb",
            return_value={"status": "skipped_with_reason", "reason": "test_blender_skip", "glb_exists": False},
        ):
            out = Path(tmp) / "semantic_layer_v9_hair"
            paths = ActuatorPaths(
                repo_root=REPO_ROOT,
                character_package=CHARACTER_PACKAGE,
                output_dir=out,
                spec_path=out / "specs" / "yuna_semantic_layer_v9_hair.json",
                obj_path=out / "exports" / "yuna_semantic_layer_v9_hair.obj",
                glb_path=out / "exports" / "yuna_semantic_layer_v9_hair.glb",
                report_path=out / "validation_report.json",
            )

            run_authored_hair_ribbons(paths)

        after = {path: sha256(path.read_bytes()).hexdigest() for path in watched}
        self.assertEqual(after, before)

    def test_actuator_can_write_hair_report_to_temp_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch(
            "semantic_actuators.authored_hair_ribbons.blender_export_glb",
            return_value={"status": "skipped_with_reason", "reason": "test_blender_skip", "glb_exists": False},
        ):
            out = Path(tmp) / "semantic_layer_v9_hair"
            paths = ActuatorPaths(
                repo_root=REPO_ROOT,
                character_package=CHARACTER_PACKAGE,
                output_dir=out,
                spec_path=out / "specs" / "yuna_semantic_layer_v9_hair.json",
                obj_path=out / "exports" / "yuna_semantic_layer_v9_hair.obj",
                glb_path=out / "exports" / "yuna_semantic_layer_v9_hair.glb",
                report_path=out / "validation_report.json",
            )
            result = run_authored_hair_ribbons(paths)

            self.assertNotEqual(result.status, "failed")
            self.assertTrue(paths.spec_path.exists())
            self.assertTrue(paths.obj_path.exists())
            self.assertTrue(paths.obj_path.with_suffix(".mtl").exists())
            self.assertTrue(paths.report_path.exists())
            report = json.loads(paths.report_path.read_text(encoding="utf-8"))
            spec = json.loads(paths.spec_path.read_text(encoding="utf-8"))
            self.assertEqual(report["route"], "semantic_layer_v9_authored_hair_ribbons_v0")
            self.assertEqual(report["part_id"], "hair")
            self.assertEqual(report["actuator"], ACTUATOR_NAME)
            self.assertFalse(report["validation"]["replace_in_beauty_glb"])
            self.assertTrue(report["validation"]["side_back_are_soft_constraints"])
            self.assertEqual(report["validation"]["visual_sanity_status"], "failed_hair_mask_alignment")
            self.assertEqual(report["validation"]["manual_visual_review"], "failed")
            self.assertFalse(report["validation"]["ready_for_cloth_seam_surface"])
            self.assertLess(report["validation"]["non_hair_occlusion_ratio"], 0.10)
            self.assertFalse(spec["part"]["replace_in_beauty_glb"])


if __name__ == "__main__":
    unittest.main()
