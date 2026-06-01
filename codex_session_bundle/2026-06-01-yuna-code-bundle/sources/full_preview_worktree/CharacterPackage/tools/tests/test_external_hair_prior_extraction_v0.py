from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CharacterPackage" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from external_hair_prior_extraction_v0 import default_paths  # noqa: E402


DATASET_DIR = REPO_ROOT / "CharacterPackage" / "external_hair_dataset"
PRIOR_LIBRARY = DATASET_DIR / "priors" / "external_hair_prior_library_v0.json"
EXTRACTION_REPORT = DATASET_DIR / "reports" / "external_hair_prior_extraction_v0_report.json"


class ExternalHairPriorExtractionV0Tests(unittest.TestCase):
    def load_library(self) -> dict:
        return json.loads(PRIOR_LIBRARY.read_text(encoding="utf-8"))

    def load_report(self) -> dict:
        return json.loads(EXTRACTION_REPORT.read_text(encoding="utf-8"))

    def test_prior_library_schema_validates_required_contract(self) -> None:
        library = self.load_library()

        self.assertEqual(library["library_version"], "external_hair_prior_library_v0.1")
        self.assertEqual(library["status"], "prior_library_generated")
        self.assertEqual(library["external_asset_usage"], "prior_only")
        self.assertFalse(library["replace_in_beauty_glb"])
        self.assertFalse(library["generated_yuna_hair"])
        self.assertTrue(library["cloth_seam_surface_blocked"])
        self.assertFalse(library["direct_copy_allowed"])
        self.assertEqual(len(library["sources"]), 2)
        self.assertIn("combined_prior_summary", library)

    def test_each_source_has_representation_type_and_required_hint_groups(self) -> None:
        library = self.load_library()
        required_hint_groups = {
            "scalp_anchor_hints",
            "primary_curve_hints",
            "width_profile_hints",
            "taper_profile_hints",
            "depth_group_hints",
            "silhouette_mass_hints",
            "card_topology_hints",
            "suitability_for_yuna",
        }

        for source in library["sources"]:
            self.assertIn(source["representation_type"], {"particle_hair", "curve_hair", "hair_cards", "ribbon_surfaces", "solid_sculpt_hair"})
            self.assertTrue(required_hint_groups.issubset(source))
            self.assertTrue(source["source_probe_paths"]["front"].startswith("CharacterPackage/"))
            self.assertTrue(source["source_probe_paths"]["report"].endswith("hair_reference_prior_report.json"))

    def test_no_source_can_be_marked_direct_copy_allowed(self) -> None:
        library = self.load_library()

        for source in library["sources"]:
            self.assertFalse(source["direct_copy_allowed"])
            self.assertTrue(source["do_not_copy_shape_directly"])
            self.assertFalse(source["contains_external_geometry"])
            self.assertFalse(source["contains_external_texture"])
            self.assertIn("direct_yuna_geometry_import", source["forbidden_downstream_use"])
            self.assertIn("v8_beauty_replacement", source["forbidden_downstream_use"])

    def test_at_least_one_useful_prior_hint_exists(self) -> None:
        library = self.load_library()
        useful_count = 0
        for source in library["sources"]:
            useful_count += len(source["scalp_anchor_hints"])
            useful_count += len(source["primary_curve_hints"])
            useful_count += len(source["width_profile_hints"]["samples_top_to_tip"])
        useful_count += len(library["combined_prior_summary"]["useful_prior_patterns"])
        useful_count += len(library["combined_prior_summary"]["recommended_yuna_curve_bundle_hints"])

        self.assertGreater(useful_count, 0)
        self.assertTrue(library["combined_prior_summary"]["next_goal_recommendation"])
        self.assertFalse(library["combined_prior_summary"]["direct_copy_allowed"])
        self.assertFalse(library["combined_prior_summary"]["ready_for_cloth_seam_surface"])

    def test_extraction_report_records_guards_and_outputs(self) -> None:
        report = self.load_report()

        self.assertEqual(report["status"], "prior_extraction_generated")
        self.assertEqual(report["source_count"], 2)
        self.assertGreater(report["useful_prior_hint_count"], 0)
        self.assertFalse(report["guards"]["replace_in_beauty_glb"])
        self.assertFalse(report["guards"]["direct_copy_allowed"])
        self.assertFalse(report["guards"]["generated_yuna_hair"])
        self.assertFalse(report["guards"]["ready_for_cloth_seam_surface"])
        self.assertFalse(report["guards"]["source_geometry_copied"])
        self.assertFalse(report["guards"]["source_texture_copied"])
        self.assertEqual(report["output_prior_library"], "CharacterPackage/external_hair_dataset/priors/external_hair_prior_library_v0.json")

    def test_default_paths_point_to_prior_outputs(self) -> None:
        paths = default_paths(REPO_ROOT)

        self.assertEqual(paths.prior_library_path, PRIOR_LIBRARY)
        self.assertEqual(paths.extraction_report_path, EXTRACTION_REPORT)

    def test_v8_unchanged(self) -> None:
        completed = subprocess.run(
            ["git", "diff", "--name-only", "--", "CharacterPackage/semantic_layer_v8"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertEqual(completed.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
