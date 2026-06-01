from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CharacterPackage" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from run_semantic_layer_validation_ci import (  # noqa: E402
    DEFAULT_CAGE_GLB,
    DEFAULT_MAIN_GLB,
    DEFAULT_SOURCE_REPORT,
    display_path,
    file_record,
    source_split_checks,
)


class SemanticLayerValidationCiTests(unittest.TestCase):
    def test_default_inputs_exist(self) -> None:
        self.assertTrue(DEFAULT_MAIN_GLB.exists())
        self.assertTrue(DEFAULT_CAGE_GLB.exists())
        self.assertTrue(DEFAULT_SOURCE_REPORT.exists())

    def test_source_split_checks_match_v8_contract(self) -> None:
        checks = source_split_checks(DEFAULT_SOURCE_REPORT)

        self.assertTrue(checks["passed"])
        self.assertEqual(checks["missing_main_meshes"], [])
        self.assertEqual(checks["debug_guides_leaked_to_beauty"], [])
        self.assertEqual(checks["debug_guides_missing_from_cage"], [])
        self.assertIn("leg_L_visual_panel", checks["required_main_meshes"])
        self.assertIn("leg_L_retopo_proxy", checks["debug_only_meshes"])

    def test_file_record_reports_existing_file(self) -> None:
        record = file_record(DEFAULT_MAIN_GLB)

        self.assertTrue(record["exists"])
        self.assertGreater(record["bytes"], 0)
        self.assertTrue(record["path"].endswith("yuna_semantic_layer_v8.glb"))

    def test_display_path_is_repo_relative_for_repo_files(self) -> None:
        self.assertEqual(
            display_path(DEFAULT_SOURCE_REPORT),
            "CharacterPackage/semantic_layer_v8/validation_report.json",
        )


if __name__ == "__main__":
    unittest.main()
