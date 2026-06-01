from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CHARACTER_PACKAGE = REPO_ROOT / "CharacterPackage"
HAIR_DIR = CHARACTER_PACKAGE / "semantic_layer_v9_hair"
PRIORS_DIR = CHARACTER_PACKAGE / "external_hair_dataset" / "priors"

PRIOR_SCHEMA = PRIORS_DIR / "external_hair_prior_schema_v1.json"
CURVE_BUNDLE = HAIR_DIR / "primary_curve_bundle_v1.json"
CURVE_REPORT = HAIR_DIR / "primary_curve_bundle_v1_report.json"
PINK_SEGMENTATION_REPORT = (
    CHARACTER_PACKAGE
    / "external_hair_dataset"
    / "sketchfab_gorgeous_japanese_fight"
    / "analysis"
    / "pink_hair_segmentation_probe"
    / "pink_hair_segmentation_report.json"
)
POSITIVE_BENCHMARK_REPORT = (
    CHARACTER_PACKAGE
    / "external_hair_dataset"
    / "sketchfab_gorgeous_japanese_fight"
    / "benchmarks"
    / "constraint_benchmark_v0"
    / "external_hair_probe_constraint_benchmark_v0_report.json"
)

PRIMARY_GROUPS = {
    "bangs_primary",
    "side_hair_left_primary",
    "side_hair_right_primary",
    "back_hair_mass",
}


class PrimaryCurveBundleV1Tests(unittest.TestCase):
    def load_bundle(self) -> dict:
        self.assertTrue(CURVE_BUNDLE.exists(), f"missing curve bundle: {CURVE_BUNDLE}")
        return json.loads(CURVE_BUNDLE.read_text(encoding="utf-8"))

    def load_prior_schema(self) -> dict:
        self.assertTrue(PRIOR_SCHEMA.exists(), f"missing prior schema: {PRIOR_SCHEMA}")
        return json.loads(PRIOR_SCHEMA.read_text(encoding="utf-8"))

    def load_report(self) -> dict:
        self.assertTrue(CURVE_REPORT.exists(), f"missing curve bundle report: {CURVE_REPORT}")
        return json.loads(CURVE_REPORT.read_text(encoding="utf-8"))

    def test_external_prior_schema_has_required_pattern_families(self) -> None:
        prior = self.load_prior_schema()

        self.assertEqual(prior["schema"], "external_hair_prior_schema_v1")
        self.assertTrue(prior["do_not_copy_shape_directly"])
        self.assertFalse(prior["direct_copy_allowed"])
        for key in (
            "scalp_anchor_patterns",
            "flow_arc_patterns",
            "width_profile_patterns",
            "taper_profile_patterns",
            "visible_mass_patterns",
            "depth_group_patterns",
            "negative_failure_patterns",
        ):
            self.assertIn(key, prior)
            self.assertTrue(prior[key], key)

    def test_external_prior_schema_explicitly_uses_positive_pink_probe_as_prior_only(self) -> None:
        prior = self.load_prior_schema()

        self.assertIn("positive_pink_hair_probe_benchmark", prior)
        benchmark = prior["positive_pink_hair_probe_benchmark"]
        self.assertEqual(benchmark["usage_role"], "positive_control_prior_only")
        self.assertTrue(benchmark["not_a_shape_source"])
        self.assertEqual(benchmark["positive_probe_status"], "passed")
        self.assertIn("positive_metrics", benchmark)
        self.assertGreater(benchmark["positive_metrics"]["candidate_visible_area_ratio"], 0.0)
        self.assertIn("do not copy mesh vertices, topology, UV islands", " ".join(benchmark["transfer_policy"]))
        self.assertEqual(
            prior["source_inputs"]["positive_pink_hair_segmentation_probe"],
            str(PINK_SEGMENTATION_REPORT.relative_to(REPO_ROOT)),
        )
        self.assertEqual(
            prior["source_inputs"]["constraint_benchmark_v0"],
            str(POSITIVE_BENCHMARK_REPORT.relative_to(REPO_ROOT)),
        )

    def test_all_required_primary_groups_exist(self) -> None:
        bundle = self.load_bundle()

        self.assertEqual(set(bundle["primary_curves"]), PRIMARY_GROUPS)
        for group_id in PRIMARY_GROUPS:
            self.assertIn(group_id, bundle)
            self.assertEqual(bundle[group_id]["id"], group_id)

    def test_each_primary_curve_has_anchor_points_width_taper_and_depth_policy(self) -> None:
        bundle = self.load_bundle()

        for group_id in PRIMARY_GROUPS:
            curve = bundle["primary_curves"][group_id]
            self.assertTrue(curve["scalp_anchor"], group_id)
            self.assertGreaterEqual(len(curve["curve_points"]), 3, group_id)
            self.assertTrue(curve["width_profile"], group_id)
            self.assertTrue(curve["taper_profile"], group_id)
            self.assertTrue(curve["depth_group"], group_id)
            self.assertIn("allowed_soft_silhouette_region", curve, group_id)
            self.assertIn("forbidden_zone_policy", curve, group_id)
            self.assertIn("source_prior_reference", curve, group_id)
            self.assertIn("positive_pink_hair_probe_benchmark", curve["source_prior_reference"], group_id)
            self.assertIn("positive_pink_hair_segmentation_probe", curve["source_prior_reference"], group_id)
            self.assertEqual(curve["source_prior_reference"]["usage_role"], "prior_only", group_id)
            self.assertFalse(curve["source_prior_reference"]["copy_external_geometry"], group_id)
            self.assertIn("mesh vertices", curve["source_prior_reference"]["forbidden_transfer"], group_id)
            self.assertTrue(curve["manual_review_required"], group_id)
            self.assertIn(curve["confidence"], {"low", "medium_low", "medium", "medium_high", "high"})

    def test_secondary_and_flyaway_strands_are_planning_curves_not_geometry(self) -> None:
        bundle = self.load_bundle()

        self.assertTrue(bundle["secondary_strands"])
        self.assertTrue(bundle["flyaway_strands"])
        for strand in [*bundle["secondary_strands"], *bundle["flyaway_strands"]]:
            self.assertGreaterEqual(len(strand["curve_points"]), 3)
            self.assertTrue(strand["manual_review_required"])
            self.assertIn("source_prior_reference", strand)

    def test_no_direct_copy_or_yuna_glb_generation_is_allowed(self) -> None:
        bundle = self.load_bundle()
        report = self.load_report()

        self.assertFalse(bundle["direct_copy_allowed"])
        self.assertTrue(bundle["do_not_copy_shape_directly"])
        self.assertFalse(bundle["replace_in_beauty_glb"])
        self.assertFalse(bundle["ready_for_cloth_seam_surface"])
        self.assertTrue(bundle["manual_review_required"])
        self.assertFalse(report["guards"]["generated_yuna_hair_glb"])
        self.assertFalse(report["guards"]["direct_copy_allowed"])
        self.assertTrue(report["guards"]["do_not_copy_shape_directly"])
        self.assertEqual(report["recommended_next"], "manual_review_primary_curve_bundle_v1_before_generation")
        self.assertEqual(report["positive_pink_hair_probe_benchmark"]["positive_probe_status"], "passed")
        self.assertTrue(report["positive_pink_hair_probe_benchmark"]["not_a_shape_source"])

    def test_visual_planning_artifacts_exist_or_are_reported(self) -> None:
        report = self.load_report()

        artifacts = report["visual_planning_artifacts"]
        for key in ("front_overlay", "yaw30_plan", "contact_sheet"):
            self.assertIn(key, artifacts)
            self.assertTrue(REPO_ROOT.joinpath(artifacts[key]["path"]).exists(), key)

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
