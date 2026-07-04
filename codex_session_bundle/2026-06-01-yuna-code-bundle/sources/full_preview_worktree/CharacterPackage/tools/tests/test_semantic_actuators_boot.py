from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CharacterPackage" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from semantic_actuators.boot_hardsurface_ortho import (  # noqa: E402
    ACTUATOR_NAME,
    alpha_components,
    build_boot_components,
    run_boot_hardsurface_ortho,
    write_obj,
)
from semantic_actuators.state import ActuatorPaths  # noqa: E402
from semantic_actuators.validation_contract import validate_boot_candidate_report  # noqa: E402


CHARACTER_PACKAGE = REPO_ROOT / "CharacterPackage"
BOOT_TEXTURE = CHARACTER_PACKAGE / "semantic_layer_v8" / "textures" / "boots.png"


class BootHardSurfaceActuatorTests(unittest.TestCase):
    def test_alpha_components_finds_boot_shapes(self) -> None:
        components = alpha_components(BOOT_TEXTURE)

        self.assertGreaterEqual(len(components), 2)
        self.assertTrue(all(area >= 500 for area, _ in components))

    def test_boot_components_have_mesh_data(self) -> None:
        components = build_boot_components(BOOT_TEXTURE)
        summary_vertices = sum(len(component.mesh.vertices) for component in components)
        summary_faces = sum(len(component.mesh.faces) for component in components)

        self.assertGreaterEqual(len(components), 2)
        self.assertGreater(summary_vertices, 0)
        self.assertGreater(summary_faces, 0)
        self.assertTrue(all(component.mesh.thickness > 0 for component in components))
        self.assertTrue(all(component.mesh.bevel > 0 for component in components))

    def test_obj_writer_creates_boot_objects(self) -> None:
        components = build_boot_components(BOOT_TEXTURE)
        with tempfile.TemporaryDirectory() as tmp:
            obj_path = Path(tmp) / "boots.obj"
            mtl_path = write_obj(obj_path, components, BOOT_TEXTURE)

            self.assertTrue(obj_path.exists())
            self.assertTrue(mtl_path.exists())
            text = obj_path.read_text(encoding="utf-8")
            self.assertIn("o boot_component_01", text)
            self.assertIn("usemtl boot_front_texture", text)
            self.assertIn("usemtl boot_side_material", text)

    def test_contract_validator_rejects_missing_requirements(self) -> None:
        errors = validate_boot_candidate_report(
            {
                "actuator": ACTUATOR_NAME,
                "part_id": "boots",
                "status": "generated_with_warnings",
                "mesh_summary": {"vertices": 1, "faces": 1, "component_count": 1},
                "validation": {
                    "independent_objects": True,
                    "has_thickness": True,
                    "has_bevel_proxy": True,
                    "has_foot_socket_metadata": True,
                },
            }
        )
        self.assertIn("boot candidate should contain at least two visible components", errors)

    def test_actuator_can_write_boot_report_to_temp_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "semantic_layer_v9_boot"
            paths = ActuatorPaths(
                repo_root=REPO_ROOT,
                character_package=CHARACTER_PACKAGE,
                output_dir=out,
                spec_path=out / "specs" / "yuna_semantic_layer_v9_boot.json",
                obj_path=out / "exports" / "yuna_semantic_layer_v9_boot.obj",
                glb_path=out / "exports" / "yuna_semantic_layer_v9_boot.glb",
                report_path=out / "validation_report.json",
            )
            result = run_boot_hardsurface_ortho(paths)

            self.assertNotEqual(result.status, "failed")
            self.assertTrue(paths.spec_path.exists())
            self.assertTrue(paths.obj_path.exists())
            self.assertTrue(paths.report_path.exists())
            report = json.loads(paths.report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["route"], "semantic_layer_v9_boot_hardsurface_ortho_v0")
            self.assertEqual(report["part_id"], "boots")
            self.assertEqual(report["actuator"], ACTUATOR_NAME)
            self.assertFalse(report["validation"]["replace_in_beauty_glb"])


if __name__ == "__main__":
    unittest.main()
