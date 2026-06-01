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

from semantic_actuators.hair_silhouette_mass_v1 import (  # noqa: E402
    ACTUATOR_NAME,
    CONFIG,
    STATUS_MANUAL_REVIEW,
    build_hair_silhouette_mass,
    run_hair_silhouette_mass_v1,
)
from semantic_actuators.state import ActuatorPaths  # noqa: E402


CHARACTER_PACKAGE = REPO_ROOT / "CharacterPackage"


class HairSilhouetteMassV1Tests(unittest.TestCase):
    def test_builds_primary_mass_sheets_before_secondary_strands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ribbons, records, design_summary = build_hair_silhouette_mass(CHARACTER_PACKAGE, Path(tmp))

        self.assertGreaterEqual(len(records), 4)
        self.assertGreaterEqual(len(ribbons), 20)
        self.assertGreaterEqual(len({ribbon.depth_group for ribbon in ribbons}), 3)
        self.assertGreaterEqual(design_summary["primary_mass_coverage_ratio"], 0.35)
        self.assertTrue(design_summary["flow_continuity_passed"])
        self.assertEqual(sum(1 for ribbon in ribbons if ribbon.group_id == "secondary_strands"), CONFIG.secondary_strand_count)
        self.assertEqual(sum(1 for ribbon in ribbons if ribbon.group_id == "flyaway_strands"), CONFIG.flyaway_strand_count)
        self.assertGreaterEqual(sum(1 for ribbon in ribbons if "_sheet_" in ribbon.id), 4)

    def test_temp_run_writes_candidate_report_and_keeps_replacement_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch(
            "semantic_actuators.hair_silhouette_mass_v1.blender_export_glb",
            return_value={"status": "skipped_with_reason", "reason": "test_blender_skip", "glb_exists": False},
        ):
            out = Path(tmp) / "silhouette_mass_v1"
            paths = ActuatorPaths(
                repo_root=REPO_ROOT,
                character_package=CHARACTER_PACKAGE,
                output_dir=out,
                spec_path=out / "specs" / "hair_silhouette_mass_v1.json",
                obj_path=out / "exports" / "hair_silhouette_mass_v1.obj",
                glb_path=out / "exports" / "hair_silhouette_mass_v1.glb",
                report_path=out / "validation_report.json",
            )
            result = run_hair_silhouette_mass_v1(paths)

            self.assertEqual(result.actuator, ACTUATOR_NAME)
            self.assertEqual(result.status, STATUS_MANUAL_REVIEW)
            self.assertTrue(paths.report_path.exists())
            self.assertTrue(paths.obj_path.exists())
            report = json.loads(paths.report_path.read_text(encoding="utf-8"))
            self.assertFalse(report["validation"]["replace_in_beauty_glb"])
            self.assertFalse(report["validation"]["ready_for_cloth_seam_surface"])
            self.assertGreaterEqual(report["validation"]["primary_mass_coverage_ratio"], 0.35)
            self.assertIn("primary_mass_sheet_count", report["mesh_summary"])

    def test_temp_run_keeps_v8_unchanged(self) -> None:
        watched = [
            CHARACTER_PACKAGE / "semantic_layer_v8" / "specs" / "yuna_semantic_layer_v8.json",
            *(CHARACTER_PACKAGE / "semantic_layer_v8" / "masks" / "front" / f"{part_id}.png" for part_id in ("back_hair", "side_hair_left", "side_hair_right", "bangs")),
        ]
        before = {path: sha256(path.read_bytes()).hexdigest() for path in watched}
        with tempfile.TemporaryDirectory() as tmp, mock.patch(
            "semantic_actuators.hair_silhouette_mass_v1.blender_export_glb",
            return_value={"status": "skipped_with_reason", "reason": "test_blender_skip", "glb_exists": False},
        ):
            out = Path(tmp) / "silhouette_mass_v1"
            paths = ActuatorPaths(
                repo_root=REPO_ROOT,
                character_package=CHARACTER_PACKAGE,
                output_dir=out,
                spec_path=out / "specs" / "hair_silhouette_mass_v1.json",
                obj_path=out / "exports" / "hair_silhouette_mass_v1.obj",
                glb_path=out / "exports" / "hair_silhouette_mass_v1.glb",
                report_path=out / "validation_report.json",
            )
            run_hair_silhouette_mass_v1(paths)

        after = {path: sha256(path.read_bytes()).hexdigest() for path in watched}
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
