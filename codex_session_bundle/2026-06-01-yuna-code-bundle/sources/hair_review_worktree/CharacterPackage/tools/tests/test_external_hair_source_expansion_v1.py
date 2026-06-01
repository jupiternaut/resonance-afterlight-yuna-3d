from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CharacterPackage" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from external_hair_source_expansion_v1 import default_paths  # noqa: E402


DATASET_DIR = REPO_ROOT / "CharacterPackage" / "external_hair_dataset"
REPORT_PATH = DATASET_DIR / "reports" / "external_hair_source_expansion_v1_report.json"
V8_DIR = REPO_ROOT / "CharacterPackage" / "semantic_layer_v8"


class ExternalHairSourceExpansionV1Tests(unittest.TestCase):
    def load_manifest(self) -> dict:
        return json.loads((DATASET_DIR / "assets_manifest.json").read_text(encoding="utf-8"))

    def load_report(self) -> dict:
        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    def test_report_exists_and_records_candidate_sources(self) -> None:
        report = self.load_report()

        self.assertEqual(report["status"], "source_expansion_generated")
        self.assertEqual(report["external_asset_usage"], "prior_only")
        self.assertFalse(report["replace_in_beauty_glb"])
        self.assertFalse(report["generated_yuna_hair"])
        self.assertTrue(report["cloth_seam_surface_blocked"])
        self.assertFalse(report["large_binaries_committed"])
        self.assertGreaterEqual(report["candidate_source_count"], 6)
        self.assertGreaterEqual(report["high_priority_source_count"], 2)

    def test_candidate_records_have_required_quality_fields(self) -> None:
        required = {
            "source_url",
            "source_name",
            "claimed_license",
            "license_confidence",
            "usage_role",
            "representation_type",
            "quality_score",
            "style_relevance_to_yuna",
            "has_bangs",
            "has_side_hair",
            "has_back_hair_mass",
            "has_scalp_anchor_structure",
            "has_hair_cards_or_curves",
            "can_extract_curve_templates",
            "can_commit_binary_to_repo",
            "notes",
        }
        report = self.load_report()

        for candidate in report["candidate_sources"]:
            self.assertTrue(required.issubset(candidate), f"missing fields for {candidate.get('source_id')}")
            self.assertGreaterEqual(candidate["quality_score"], 0)
            self.assertLessEqual(candidate["quality_score"], 1)
            self.assertGreaterEqual(candidate["style_relevance_to_yuna"], 0)
            self.assertLessEqual(candidate["style_relevance_to_yuna"], 1)
            self.assertEqual(candidate["recommendation"] == "do_not_use", False)

    def test_high_priority_sources_are_open_or_selected_material_sources(self) -> None:
        report = self.load_report()
        high_priority = report["high_priority_next_intake"]
        high_ids = {item["source_id"] for item in high_priority}

        self.assertIn("vroid_hairsample_female_cc0", high_ids)
        self.assertIn("vroid_hairsample_male_cc0", high_ids)
        self.assertIn("blendswap_curly_hair", high_ids)
        for item in high_priority:
            self.assertNotIn("no_", item["binary_policy"])

    def test_existing_probe_sources_are_retained_but_low_or_medium_quality(self) -> None:
        report = self.load_report()

        self.assertEqual(
            set(report["existing_probe_sources_retained"]),
            {"opengameart_ponytail_female", "opengameart_long_male"},
        )
        for quality in report["current_probe_quality_boundary"].values():
            self.assertIn(quality, {"low", "medium_low", "medium"})

    def test_method_references_are_not_binary_sources(self) -> None:
        report = self.load_report()
        methods = [candidate for candidate in report["candidate_sources"] if candidate["source_class"] == "method_reference"]

        self.assertGreaterEqual(len(methods), 2)
        for method in methods:
            self.assertEqual(method["recommendation"], "reference_report_only")
            self.assertFalse(method["can_commit_binary"])
            self.assertEqual(method["can_commit_binary_to_repo"], "no_method_reference_only")

    def test_manifest_annotations_match_report_and_keep_guards(self) -> None:
        manifest = self.load_manifest()
        report_ids = {candidate["source_id"] for candidate in self.load_report()["candidate_sources"]}
        annotated = {source["source_id"] for source in manifest["sources"] if "source_quality_v1" in source}

        self.assertTrue(report_ids.issubset(annotated))
        self.assertTrue(manifest["project_guards"]["v8_immutable"])
        self.assertFalse(manifest["project_guards"]["replace_in_beauty_glb"])
        self.assertEqual(manifest["project_guards"]["external_asset_usage"], "prior_only")
        self.assertFalse(manifest["project_guards"]["large_binaries_committed"])
        self.assertTrue(manifest["project_guards"]["cloth_seam_surface_blocked"])
        for source in manifest["sources"]:
            self.assertFalse(source["replace_in_beauty_glb"])
            self.assertEqual(source["external_asset_usage"], "prior_only")
            self.assertEqual(source["download_status"], "not_downloaded")
            self.assertEqual(source["validation_status"]["status"], "skipped")

    def test_text_reports_keep_cloth_blocked_and_external_sources_prior_only(self) -> None:
        triage = (DATASET_DIR / "SOURCE_TRIAGE.md").read_text(encoding="utf-8")
        readme = (DATASET_DIR / "README.md").read_text(encoding="utf-8")
        project_state = (REPO_ROOT / "CharacterPackage" / "semantic_layer_v9_candidate" / "PROJECT_STATE.md").read_text(
            encoding="utf-8"
        )

        for text in (triage, readme, project_state):
            self.assertIn("external_hair_source_expansion_v1", text)
            self.assertIn("prior", text.lower())
            self.assertIn("cloth", text.lower())
            self.assertNotIn("production-ready replacement", text.lower())

    def test_default_paths_point_to_expansion_report(self) -> None:
        paths = default_paths(REPO_ROOT)

        self.assertEqual(paths.expansion_report_path, REPORT_PATH)

    def test_v8_baseline_directory_still_exists(self) -> None:
        self.assertTrue(V8_DIR.exists())
        self.assertTrue((V8_DIR / "specs" / "yuna_semantic_layer_v8.json").exists())


if __name__ == "__main__":
    unittest.main()
