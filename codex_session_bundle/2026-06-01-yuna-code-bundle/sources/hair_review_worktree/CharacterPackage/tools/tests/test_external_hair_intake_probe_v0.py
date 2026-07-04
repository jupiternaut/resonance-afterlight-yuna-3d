from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CharacterPackage" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from external_hair_intake_probe_v0 import (  # noqa: E402
    default_paths,
    select_sources,
    validate_manifest_source_policy,
)


DATASET_DIR = REPO_ROOT / "CharacterPackage" / "external_hair_dataset"


class ExternalHairIntakeProbeV0Tests(unittest.TestCase):
    def load_manifest(self) -> dict:
        return json.loads((DATASET_DIR / "assets_manifest.json").read_text(encoding="utf-8"))

    def load_summary(self) -> dict:
        return json.loads(
            (DATASET_DIR / "probes" / "external_hair_intake_probe_v0_report.json").read_text(encoding="utf-8")
        )

    def test_selected_sources_exist_in_manifest_and_are_not_do_not_use(self) -> None:
        manifest = self.load_manifest()
        source_ids = {source["source_id"] for source in manifest["sources"]}
        selected = select_sources(manifest, limit=2)

        self.assertGreaterEqual(len(selected), 1)
        self.assertLessEqual(len(selected), 2)
        for source in selected:
            self.assertIn(source["source_id"], source_ids)
            self.assertNotEqual(source["recommendation"], "do_not_use")
            self.assertEqual(source["external_asset_usage"], "prior_only")
            self.assertFalse(source["replace_in_beauty_glb"])

    def test_unknown_license_cannot_be_open_template_source(self) -> None:
        bad_source = {
            "source_id": "bad_unknown_license",
            "recommendation": "open_template_source",
            "license_confidence": "unknown",
            "external_asset_usage": "prior_only",
            "replace_in_beauty_glb": False,
        }

        errors = validate_manifest_source_policy(bad_source)

        self.assertTrue(any("open_template_source requires" in error for error in errors))

    def test_do_not_use_source_cannot_be_selected_by_policy(self) -> None:
        bad_source = {
            "source_id": "blocked_source",
            "recommendation": "do_not_use",
            "license_confidence": "high",
            "external_asset_usage": "prior_only",
            "replace_in_beauty_glb": False,
        }

        errors = validate_manifest_source_policy(bad_source)

        self.assertTrue(any("do_not_use source cannot be selected" in error for error in errors))

    def test_probe_summary_exists_or_reports_explicit_block(self) -> None:
        summary_path = DATASET_DIR / "probes" / "external_hair_intake_probe_v0_report.json"

        self.assertTrue(summary_path.exists())
        summary = self.load_summary()
        self.assertIn(summary["status"], {"probe_generated", "blocked_waiting_for_open_template_source"})
        self.assertFalse(summary["guards"]["replace_in_beauty_glb"])
        self.assertEqual(summary["guards"]["external_asset_usage"], "prior_only")
        self.assertFalse(summary["guards"]["third_party_binary_committed"])
        self.assertFalse(summary["guards"]["generated_yuna_hair"])
        self.assertFalse(summary["guards"]["ready_for_cloth_seam_surface"])

    def test_successful_probe_reports_have_images_and_no_source_binary(self) -> None:
        summary = self.load_summary()
        if summary["status"] == "blocked_waiting_for_open_template_source":
            self.assertGreater(summary["blocked_count"], 0)
            return

        for source_report in summary["source_reports"]:
            report_path = REPO_ROOT / source_report["report_path"]
            self.assertTrue(report_path.exists())
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "probe_generated")
            self.assertTrue(report["selection"]["binary_download_allowed"])
            self.assertTrue(report["selection"]["renders_can_be_committed"])
            self.assertFalse(report["source_binary_committed"])
            self.assertFalse(report["third_party_binary_committed"])
            self.assertFalse(report["replace_in_beauty_glb"])
            self.assertFalse(report["ready_for_cloth_seam_surface"])
            self.assertIn(
                report["representation_classification"],
                {"particle_hair", "curve_hair", "hair_cards", "ribbon_surfaces", "solid_sculpt_hair"},
            )
            probe_dir = report_path.parent
            for name in ("front.png", "yaw30.png", "side.png", "wire.png", "alpha.png"):
                self.assertTrue((probe_dir / name).exists(), f"missing {name} for {report['source_id']}")

            forbidden_payloads = list(probe_dir.glob("*.blend")) + list(probe_dir.glob("*.zip"))
            self.assertEqual(forbidden_payloads, [])

    def test_default_paths_point_to_probe_summary(self) -> None:
        paths = default_paths(REPO_ROOT)

        self.assertEqual(paths.summary_report_path, DATASET_DIR / "probes" / "external_hair_intake_probe_v0_report.json")


if __name__ == "__main__":
    unittest.main()
