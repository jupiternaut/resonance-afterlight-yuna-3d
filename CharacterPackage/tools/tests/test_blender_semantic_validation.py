from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CharacterPackage" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from run_blender_semantic_validation import (  # noqa: E402
    DEFAULT_BASELINE_GLB,
    DEFAULT_CAGE_GLB,
    DEFAULT_CANDIDATE_GLB,
    display_path,
    file_record,
    parse_args,
)


class BlenderSemanticValidationTests(unittest.TestCase):
    def test_default_candidate_inputs_exist_after_weapon_build(self) -> None:
        self.assertTrue(DEFAULT_BASELINE_GLB.exists())
        self.assertTrue(DEFAULT_CAGE_GLB.exists())
        self.assertTrue(DEFAULT_CANDIDATE_GLB.exists())

    def test_parse_help_works(self) -> None:
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "run_blender_semantic_validation.py"), "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Validate a semantic candidate GLB", result.stdout)

    def test_parse_args_supports_custom_candidate(self) -> None:
        args = parse_args(["--candidate-glb", "custom.glb"])
        self.assertEqual(args.candidate_glb, Path("custom.glb"))

    def test_file_record_and_display_path(self) -> None:
        record = file_record(DEFAULT_CANDIDATE_GLB)

        self.assertTrue(record["exists"])
        self.assertGreater(record["bytes"], 0)
        self.assertEqual(
            display_path(DEFAULT_CANDIDATE_GLB),
            "CharacterPackage/semantic_layer_v9_weapon/exports/yuna_semantic_layer_v9_weapon.glb",
        )


if __name__ == "__main__":
    unittest.main()
