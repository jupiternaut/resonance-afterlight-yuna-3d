from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CharacterPackage" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import review_hair_target_masks_v0 as review  # noqa: E402


class HairTargetReviewTests(unittest.TestCase):
    def test_component_prior_keeps_plausible_hair_component(self) -> None:
        kept = review.MaskComponent("bangs", 100, (420, 60, 560, 180), tuple())
        rejected = review.MaskComponent("bangs", 100, (420, 600, 560, 720), tuple())

        self.assertTrue(review.component_is_hair_like(kept))
        self.assertFalse(review.component_is_hair_like(rejected))

    def test_candidate_alignment_reports_outside_ratio(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            candidate = Image.new("RGB", (20, 20), (184, 184, 184))
            for x in range(2, 8):
                for y in range(2, 8):
                    candidate.putpixel((x, y), (220, 220, 220))
            candidate_path = tmp_path / "candidate.png"
            candidate.save(candidate_path)
            target = Image.new("L", (20, 20), 0)
            for x in range(2, 8):
                for y in range(2, 8):
                    target.putpixel((x, y), 255)

            metrics = review.candidate_alignment(candidate_path, target)

            self.assertTrue(metrics["candidate_is_inside_target"])
            self.assertEqual(metrics["outside_ratio"], 0.0)

    def test_run_writes_review_report_without_touching_v8(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(review, "OUT_DIR", Path(tmp)):
            report = review.run()

            report_path = Path(tmp) / "hair_target_review_report.json"
            self.assertTrue(report_path.exists())
            saved = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["route"], "review_and_refine_hair_target_masks_v0")
            self.assertFalse(saved["decision"]["ready_for_cloth_seam_surface"])
            self.assertTrue((Path(tmp) / "hair_target_mask_raw_union.png").exists())
            self.assertTrue((Path(tmp) / "hair_target_mask_strict_clean.png").exists())
            self.assertTrue((Path(tmp) / "hair_target_mask_refined_component_priors.png").exists())
            self.assertGreaterEqual(report["component_selection"]["kept_component_count"], 1)


if __name__ == "__main__":
    unittest.main()
