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

            self.assertEqual(sanity["visual_sanity_status"], "failed_hair_mask_projection")
            self.assertGreaterEqual(sanity["outside_hair_mask_ratio"], 0.10)
            self.assertFalse(sanity["candidate_is_hair_only"])

    def test_hair_visual_sanity_separates_projection_from_candidate_geometry_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            candidate_path = tmp_path / "candidate.png"
            baseline_path = tmp_path / "baseline.png"
            candidate = Image.new("RGB", (20, 20), (184, 184, 184))
            baseline = Image.new("RGB", (20, 20), (184, 184, 184))
            for x in range(14, 19):
                for y in range(14, 19):
                    candidate.putpixel((x, y), (220, 220, 220))
            for x in range(1, 8):
                for y in range(1, 8):
                    baseline.putpixel((x, y), (220, 220, 220))
            candidate.save(candidate_path)
            baseline.save(baseline_path)
            hair_mask = [[1 <= x < 8 and 1 <= y < 8 for x in range(20)] for y in range(20)]

            with mock.patch(
                "run_blender_semantic_validation.evaluate_render_framing",
                return_value={"framing_valid": True, "reason": "synthetic valid frame"},
            ), mock.patch(
                "run_blender_semantic_validation.load_hair_union_mask",
                return_value=hair_mask,
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
                    candidate_path,
                    baseline_path,
                    baseline_path,
                    tmp_path,
                    "synthetic",
                )

            self.assertEqual(sanity["visual_sanity_status"], "failed_candidate_geometry_alignment")
            self.assertTrue(sanity["hair_union_projection_valid"])
            self.assertFalse(sanity["candidate_geometry_alignment_valid"])
            self.assertTrue((tmp_path / "synthetic_validation_v8_hair_union_mask_projected_on_baseline.png").exists())
            self.assertTrue((tmp_path / "synthetic_validation_candidate_visible_mask.png").exists())
            self.assertTrue((tmp_path / "synthetic_validation_candidate_mask_vs_hair_union_overlay.png").exists())
            self.assertTrue((tmp_path / "synthetic_validation_candidate_bbox_vs_hair_union_bbox.png").exists())
            self.assertTrue((tmp_path / "coordinate_mapping_debug.json").exists())

    def test_hair_visual_sanity_rejects_dirty_clean_target_even_when_raw_alignment_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            candidate_path = tmp_path / "candidate.png"
            baseline_path = tmp_path / "baseline.png"
            image = Image.new("RGB", (20, 20), (184, 184, 184))
            for x in range(2, 10):
                for y in range(2, 10):
                    image.putpixel((x, y), (220, 220, 220))
            image.save(candidate_path)
            baseline = Image.new("RGB", (20, 20), (184, 184, 184))
            for x in range(1, 19):
                for y in range(1, 19):
                    baseline.putpixel((x, y), (220, 220, 220))
            baseline.save(baseline_path)
            hair_mask = [[1 <= x < 19 and 1 <= y < 19 for x in range(20)] for y in range(20)]

            with mock.patch(
                "run_blender_semantic_validation.evaluate_render_framing",
                return_value={"framing_valid": True, "reason": "synthetic valid frame"},
            ), mock.patch(
                "run_blender_semantic_validation.load_hair_union_mask",
                return_value=hair_mask,
            ), mock.patch(
                "run_blender_semantic_validation.write_hair_target_cleaning_debug",
                return_value={
                    "hair_union_target_is_clean": False,
                    "hair_union_body_overlap_ratio": 0.80,
                    "hair_union_face_overlap_ratio": 0.04,
                    "hair_union_weapon_overlap_ratio": 0.02,
                    "clean_hair_mask_iou": 0.0,
                    "clean_outside_hair_mask_ratio": 1.0,
                    "clean_candidate_is_hair_only": False,
                    "hair_target_cleaning_report": {"exists": True, "path": "synthetic.json", "bytes": 1},
                    "artifacts": {},
                },
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
                    candidate_path,
                    baseline_path,
                    baseline_path,
                    tmp_path,
                    "synthetic",
                )

            self.assertEqual(sanity["visual_sanity_status"], "failed_clean_hair_mask_alignment")
            self.assertEqual(sanity["coordinate_alignment_gate"], "weak_pass")
            self.assertTrue(sanity["raw_candidate_is_hair_only"])
            self.assertFalse(sanity["candidate_is_hair_only"])
            self.assertFalse(sanity["hair_union_target_is_clean"])
            self.assertEqual(sanity["hair_target_quality"], "dirty_or_overbroad")


if __name__ == "__main__":
    unittest.main()
