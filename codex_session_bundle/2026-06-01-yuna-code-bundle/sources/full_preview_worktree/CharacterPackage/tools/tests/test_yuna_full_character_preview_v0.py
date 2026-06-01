from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CharacterPackage" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import build_yuna_full_character_preview_v0 as preview  # noqa: E402


class YunaFullCharacterPreviewV0Tests(unittest.TestCase):
    def test_manifest_and_report_exist_with_guardrails(self) -> None:
        self.assertTrue(preview.MANIFEST_PATH.exists())
        self.assertTrue(preview.REPORT_PATH.exists())

        manifest = json.loads(preview.MANIFEST_PATH.read_text(encoding="utf-8"))
        report = json.loads(preview.REPORT_PATH.read_text(encoding="utf-8"))

        for data in (manifest, report):
            self.assertTrue(data["preview_only"])
            self.assertFalse(data["replace_in_beauty_glb"])
            self.assertFalse(data["hair_accepted"])
            self.assertFalse(data["cloth_accepted"])
            self.assertFalse(data["ready_for_cloth_seam_surface"])
            self.assertTrue(data["manual_visual_review_required"])
            self.assertEqual(data["source_branch"], preview.SOURCE_BRANCH)
            self.assertEqual(data["base_commit"], preview.BASE_COMMIT)

        self.assertTrue(report["v8_unchanged"])
        self.assertTrue(report["v9_hair_unchanged"])
        self.assertEqual(manifest["assets"]["v8_beauty_glb"]["collection"], "baseline_v8")
        self.assertEqual(manifest["assets"]["candidate_hair_glb"]["collection"], "candidate_hair_unaccepted")
        self.assertFalse(manifest["assets"]["cloth_candidate_glb"]["available"])

    def test_required_collections_are_declared(self) -> None:
        manifest = json.loads(preview.MANIFEST_PATH.read_text(encoding="utf-8"))
        declared = {item["name"] for item in manifest["scene_collections"]}

        self.assertEqual(set(preview.COLLECTIONS), declared)
        self.assertTrue(next(item for item in manifest["scene_collections"] if item["name"] == "baseline_v8")["default_visible"])
        self.assertFalse(next(item for item in manifest["scene_collections"] if item["name"] == "debug_cage_hidden")["default_visible"])
        self.assertFalse(next(item for item in manifest["scene_collections"] if item["name"] == "candidate_cloth_unaccepted")["default_visible"])

    def test_screenshots_or_explicit_skip_exist(self) -> None:
        report = json.loads(preview.REPORT_PATH.read_text(encoding="utf-8"))
        if report["status"] == "skipped_with_reason":
            self.assertIn("reason", report["blender"])
            return

        for name in [*preview.SCREENSHOTS, "contact_sheet"]:
            with self.subTest(name=name):
                record = report["screenshots"][name]
                self.assertTrue(record["exists"])
                self.assertGreater(record["bytes"], 0)

    def test_immutable_routes_have_empty_git_diff(self) -> None:
        for path in ("CharacterPackage/semantic_layer_v8", "CharacterPackage/semantic_layer_v9_hair"):
            with self.subTest(path=path):
                result = subprocess.run(
                    ["git", "diff", "--name-only", "--", path],
                    cwd=str(REPO_ROOT),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
