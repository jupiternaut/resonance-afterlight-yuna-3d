from __future__ import annotations

import json
import sys
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path
from unittest import mock

from PIL import Image, ImageChops


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CharacterPackage" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from semantic_actuators.curve_bundle_hair_repair_v1 import (  # noqa: E402
    REPAIR_ATTEMPTS,
    build_repaired_curve_bundle_hair,
    run_repaired_curve_bundle_hair_candidate_v1,
    schema_score,
)
from semantic_actuators.curve_bundle_hair_candidate_v1 import _binary, _target_mask  # noqa: E402
from semantic_actuators.state import ActuatorPaths  # noqa: E402
from semantic_actuators.validation_contract import validate_hair_candidate_report  # noqa: E402


CHARACTER_PACKAGE = REPO_ROOT / "CharacterPackage"


def _mask_pixels(mask) -> int:
    return sum(1 for value in mask.convert("L").getdata() if value > 0)


class CurveBundleHairRepairV1Tests(unittest.TestCase):
    def test_repaired_masks_improve_source_space_soft_and_forbidden_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ribbons, records, design_summary = build_repaired_curve_bundle_hair(
                CHARACTER_PACKAGE,
                Path(tmp),
                REPAIR_ATTEMPTS[0],
            )

        metrics = design_summary["metrics"]
        self.assertGreaterEqual(len(ribbons), 24)
        self.assertTrue(records)
        self.assertLess(metrics["forbidden_candidate_leak_ratio"], 0.10)
        self.assertGreaterEqual(metrics["candidate_soft_inside_ratio"], 0.70)
        self.assertGreaterEqual(metrics["candidate_core_coverage_ratio"], 0.10)
        self.assertTrue(metrics["candidate_front_visible_hair_mass"])
        self.assertTrue(metrics["primary_group_presence_passed"])

    def test_repaired_coverage_stays_outside_forbidden_mask(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            build_repaired_curve_bundle_hair(CHARACTER_PACKAGE, out, REPAIR_ATTEMPTS[0])
            coverage = _binary(Image.open(out / "coverage_masks" / "curve_bundle_candidate_repair_attempt_01_coverage_mask.png"))

        forbidden = _binary(_target_mask(CHARACTER_PACKAGE, "forbidden_nonhair_zone_mask.png"))
        overlap = ImageChops.multiply(coverage, forbidden)
        self.assertEqual(_mask_pixels(overlap), 0)

    def test_temp_repair_actuator_writes_report_without_touching_v8(self) -> None:
        watched = [
            CHARACTER_PACKAGE / "semantic_layer_v8" / "specs" / "yuna_semantic_layer_v8.json",
            CHARACTER_PACKAGE / "semantic_layer_v8" / "exports" / "yuna_semantic_layer_v8.glb",
        ]
        before = {path: sha256(path.read_bytes()).hexdigest() for path in watched}
        with tempfile.TemporaryDirectory() as tmp, mock.patch(
            "semantic_actuators.curve_bundle_hair_repair_v1.blender_export_glb",
            return_value={"status": "skipped_with_reason", "reason": "test_blender_skip", "glb_exists": False},
        ):
            out = Path(tmp) / "repair_attempt"
            paths = ActuatorPaths(
                repo_root=REPO_ROOT,
                character_package=CHARACTER_PACKAGE,
                output_dir=out,
                spec_path=out / "specs" / "repair.json",
                obj_path=out / "exports" / "repair.obj",
                glb_path=out / "exports" / "repair.glb",
                report_path=out / "validation_report.json",
            )
            result = run_repaired_curve_bundle_hair_candidate_v1(paths, REPAIR_ATTEMPTS[0])

            self.assertTrue(paths.obj_path.exists())
            self.assertTrue(paths.report_path.exists())
            report = json.loads(paths.report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["part_id"], "hair")
            self.assertFalse(report["validation"]["replace_in_beauty_glb"])
            self.assertFalse(report["validation"]["ready_for_cloth_seam_surface"])
            self.assertEqual(validate_hair_candidate_report(report), [])
            self.assertEqual(result.part_id, "hair")

        after = {path: sha256(path.read_bytes()).hexdigest() for path in watched}
        self.assertEqual(after, before)

    def test_schema_score_penalizes_forbidden_leak_and_fragmentation(self) -> None:
        clean = {
            "candidate_soft_inside_ratio": 0.8,
            "candidate_core_coverage_ratio": 0.2,
            "candidate_visible_area_ratio": 0.02,
            "forbidden_candidate_leak_ratio": 0.02,
            "component_count": 8,
        }
        leaky = {**clean, "forbidden_candidate_leak_ratio": 0.5, "component_count": 40}
        self.assertGreater(schema_score(clean), schema_score(leaky))


if __name__ == "__main__":
    unittest.main()
