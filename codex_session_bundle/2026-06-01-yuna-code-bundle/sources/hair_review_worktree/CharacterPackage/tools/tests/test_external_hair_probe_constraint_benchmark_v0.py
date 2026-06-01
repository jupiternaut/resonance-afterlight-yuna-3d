from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CharacterPackage" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from external_hair_probe_constraint_benchmark_v0 import default_paths  # noqa: E402


DATASET_DIR = REPO_ROOT / "CharacterPackage" / "external_hair_dataset" / "sketchfab_gorgeous_japanese_fight"
BENCHMARK_DIR = DATASET_DIR / "benchmarks" / "constraint_benchmark_v0"
REPORT_PATH = BENCHMARK_DIR / "external_hair_probe_constraint_benchmark_v0_report.json"
PROBE_GLB = DATASET_DIR / "extracted" / "pink_hair_segment_probe.glb"


class ExternalHairProbeConstraintBenchmarkV0Tests(unittest.TestCase):
    def load_report(self) -> dict:
        self.assertTrue(REPORT_PATH.exists(), f"missing benchmark report: {REPORT_PATH}")
        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    def test_benchmark_report_schema_validates_required_fields(self) -> None:
        report = self.load_report()

        required = {
            "route",
            "status",
            "source_probe",
            "views",
            "positive_probe_status",
            "negative_control_results",
            "constraint_false_positive_risk",
            "constraint_false_negative_risk",
            "constraints_too_strict",
            "constraints_too_weak",
            "recommended_constraint_updates",
            "usable_as_yuna_prior",
            "guards",
        }
        self.assertTrue(required.issubset(report))
        self.assertEqual(report["route"], "external_hair_probe_constraint_benchmark_v0")
        self.assertIn(
            report["status"],
            {
                "blocked",
                "constraint_benchmark_passed_for_external_probe",
                "constraint_benchmark_failed_negatives_too_weak",
                "constraint_benchmark_failed_positive_too_strict_or_mapping_issue",
                "constraint_benchmark_inconclusive",
            },
        )
        self.assertIsInstance(report["negative_control_results"], dict)
        self.assertIsInstance(report["recommended_constraint_updates"], list)

    def test_positive_probe_exists_or_report_is_blocked(self) -> None:
        report = self.load_report()

        if PROBE_GLB.exists():
            self.assertNotEqual(report["status"], "blocked")
            self.assertTrue(report["source_probe"]["exists"])
            self.assertIn(report["positive_probe_status"], {"passed", "failed"})
            self.assertIn("positive_probe_result", report)
        else:
            self.assertEqual(report["status"], "blocked")
            self.assertTrue(report.get("blocked_with_reason"))

    def test_negative_controls_generated_or_explicitly_skipped(self) -> None:
        report = self.load_report()

        if report["status"] == "blocked":
            self.assertTrue(report.get("negative_controls_skipped_with_reason") or report.get("blocked_with_reason"))
            return

        expected_controls = {
            "shrunken_probe",
            "shifted_probe",
            "fragmented_probe",
            "barcode_strip_probe",
            "nonhair_component_probe",
        }
        self.assertEqual(set(report["negative_control_results"]), expected_controls)
        for name, result in report["negative_control_results"].items():
            self.assertTrue(result["expected_to_fail"], name)
            self.assertIn(result["status"], {"passed", "failed"}, name)
            self.assertIn("metrics", result, name)
            self.assertIn("failed_gates", result, name)
            for record in result["artifacts"].values():
                self.assertTrue(REPO_ROOT.joinpath(record["path"]).exists(), record["path"])

    def test_probe_views_include_consumed_renders_and_optional_skips(self) -> None:
        report = self.load_report()
        if report["status"] == "blocked":
            return

        for view in ("front", "yaw30", "side", "wire"):
            self.assertEqual(report["views"][view]["status"], "consumed_existing_render")
            self.assertTrue(REPO_ROOT.joinpath(report["views"][view]["path"]).exists())
        for optional in ("depth", "normal"):
            self.assertEqual(report["views"][optional]["status"], "skipped_with_reason")
            self.assertTrue(report["views"][optional]["skipped_with_reason"])

    def test_report_guards_no_yuna_hair_and_cloth_blocked(self) -> None:
        report = self.load_report()
        guards = report["guards"]

        self.assertEqual(guards["external_asset_usage"], "positive_control_prior_only")
        self.assertFalse(guards["generated_yuna_hair"])
        self.assertFalse(guards["replace_in_beauty_glb"])
        self.assertFalse(guards["ready_for_cloth_seam_surface"])
        self.assertFalse(guards["external_probe_is_final_yuna_hair"])
        self.assertNotIn("semantic_layer_v9_hair", json.dumps(report["artifacts"]))

    def test_default_paths_point_to_benchmark_outputs(self) -> None:
        paths = default_paths(REPO_ROOT)

        self.assertEqual(paths.probe_glb, PROBE_GLB)
        self.assertEqual(paths.output_dir, BENCHMARK_DIR)
        self.assertEqual(paths.report_path, REPORT_PATH)

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
