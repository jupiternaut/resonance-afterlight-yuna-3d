from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CharacterPackage" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from run_blender_semantic_validation import (  # noqa: E402
    DEFAULT_BASELINE_GLB,
    DEFAULT_CAGE_GLB,
    DEFAULT_CANDIDATE_GLB,
    display_path,
    evaluate_black_pixel_sanity,
    file_record,
    hair_visual_sanity_from_reports,
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

    def test_visual_sanity_rejects_large_black_candidate_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "black_leak.png"
            image = Image.new("RGB", (100, 100), (184, 184, 184))
            for x in range(20, 80):
                for y in range(20, 80):
                    image.putpixel((x, y), (0, 0, 0))
            image.save(image_path)

            metrics = evaluate_black_pixel_sanity(image_path)

            self.assertGreaterEqual(metrics["candidate_black_pixel_ratio"], 0.05)
            self.assertGreaterEqual(metrics["black_alpha_leak_ratio"], 0.02)

    def test_hair_visual_sanity_rejects_face_and_non_hair_occlusion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "clean.png"
            Image.new("RGB", (20, 20), (184, 184, 184)).save(image_path)

            sanity = hair_visual_sanity_from_reports(
                {},
                {
                    "validation": {
                        "alpha_material_valid": True,
                        "face_occlusion_ratio": 0.40,
                        "non_hair_occlusion_ratio": 0.30,
                    }
                },
                image_path,
            )

            self.assertIn(sanity["visual_sanity_status"], {"failed_visual_sanity", "failed_validation_framing"})
            self.assertIn("face", sanity["visual_sanity_reason"])
            self.assertIn("non-hair", sanity["visual_sanity_reason"])

    def test_hair_visual_sanity_rejects_candidate_outside_hair_mask(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "candidate.png"
            image = Image.new("RGB", (20, 20), (184, 184, 184))
            for x in range(4, 16):
                for y in range(4, 16):
                    image.putpixel((x, y), (220, 220, 220))
            image.save(image_path)

            with mock.patch(
                "run_blender_semantic_validation.evaluate_render_framing",
                return_value={"framing_valid": True, "reason": "synthetic valid frame"},
            ), mock.patch(
                "run_blender_semantic_validation.load_hair_union_mask",
                return_value=[[False for _ in range(20)] for _ in range(20)],
            ):
                sanity = hair_visual_sanity_from_reports(
                    {},
                    {
                        "validation": {
                            "alpha_material_valid": True,
                            "face_occlusion_ratio": 0.0,
                            "non_hair_occlusion_ratio": 0.0,
                        }
                    },
                    image_path,
                    image_path,
                    image_path,
                )

            self.assertEqual(sanity["visual_sanity_status"], "failed_hair_mask_alignment")
            self.assertGreaterEqual(sanity["outside_hair_mask_ratio"], 0.10)
            self.assertFalse(sanity["candidate_is_hair_only"])


if __name__ == "__main__":
    unittest.main()
