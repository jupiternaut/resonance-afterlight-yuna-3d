from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CharacterPackage" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from semantic_actuators.state import ActuatorPaths  # noqa: E402
from semantic_actuators.validation_contract import validate_weapon_candidate_report  # noqa: E402
from semantic_actuators.weapon_hardsurface_ortho import (  # noqa: E402
    ACTUATOR_NAME,
    alpha_profile,
    build_weapon_mesh,
    run_weapon_hardsurface_ortho,
    write_obj,
)


CHARACTER_PACKAGE = REPO_ROOT / "CharacterPackage"
WEAPON_TEXTURE = CHARACTER_PACKAGE / "semantic_layer_v8" / "textures" / "weapon.png"


class WeaponHardSurfaceActuatorTests(unittest.TestCase):
    def test_alpha_profile_uses_visible_weapon_texture(self) -> None:
        bbox, profile = alpha_profile(WEAPON_TEXTURE, sections=12)

        self.assertEqual(len(profile), 12)
        self.assertGreater(bbox[2] - bbox[0], 10)
        self.assertGreater(bbox[3] - bbox[1], 10)
        self.assertTrue(all(left <= right for _, left, right in profile))

    def test_weapon_mesh_has_thickness_bevel_uvs_and_side_faces(self) -> None:
        mesh = build_weapon_mesh(WEAPON_TEXTURE, target_height=2.0, thickness=0.2, bevel=0.04)
        summary = mesh.to_summary()

        self.assertGreater(summary["vertices"], 0)
        self.assertGreater(summary["faces"], 0)
        self.assertEqual(summary["vertices"], len(mesh.uvs))
        self.assertGreater(summary["material_face_counts"]["textured"], 0)
        self.assertGreater(summary["material_face_counts"]["side"], 0)
        self.assertEqual(summary["thickness"], 0.2)
        self.assertEqual(summary["bevel"], 0.04)

    def test_obj_writer_creates_obj_and_mtl(self) -> None:
        mesh = build_weapon_mesh(WEAPON_TEXTURE, target_height=1.0)
        with tempfile.TemporaryDirectory() as tmp:
            obj_path = Path(tmp) / "weapon.obj"
            mtl_path = write_obj(obj_path, mesh, WEAPON_TEXTURE)

            self.assertTrue(obj_path.exists())
            self.assertTrue(mtl_path.exists())
            text = obj_path.read_text(encoding="utf-8")
            self.assertIn("o weapon_hardsurface_ortho_v0", text)
            self.assertIn("usemtl weapon_front_texture", text)
            self.assertIn("usemtl weapon_side_material", text)

    def test_contract_validator_rejects_missing_requirements(self) -> None:
        errors = validate_weapon_candidate_report(
            {
                "actuator": ACTUATOR_NAME,
                "part_id": "weapon",
                "status": "generated_with_warnings",
                "mesh_summary": {"vertices": 1, "faces": 1},
                "validation": {
                    "independent_object": True,
                    "has_thickness": False,
                    "has_bevel_proxy": True,
                    "has_hand_socket_metadata": True,
                },
            }
        )
        self.assertIn("weapon candidate must have thickness", errors)

    def test_actuator_can_write_report_to_temp_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "semantic_layer_v9_weapon"
            paths = ActuatorPaths(
                repo_root=REPO_ROOT,
                character_package=CHARACTER_PACKAGE,
                output_dir=out,
                spec_path=out / "specs" / "yuna_semantic_layer_v9_weapon.json",
                obj_path=out / "exports" / "yuna_semantic_layer_v9_weapon.obj",
                glb_path=out / "exports" / "yuna_semantic_layer_v9_weapon.glb",
                report_path=out / "validation_report.json",
            )
            result = run_weapon_hardsurface_ortho(paths)

            self.assertNotEqual(result.status, "failed")
            self.assertTrue(paths.spec_path.exists())
            self.assertTrue(paths.obj_path.exists())
            self.assertTrue(paths.report_path.exists())
            report = json.loads(paths.report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["route"], "semantic_layer_v9_weapon_hardsurface_ortho_v0")
            self.assertEqual(report["part_id"], "weapon")
            self.assertEqual(report["actuator"], ACTUATOR_NAME)
            self.assertFalse(report["validation"]["replace_in_beauty_glb"])


if __name__ == "__main__":
    unittest.main()
