from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DATASET_DIR = REPO_ROOT / "CharacterPackage" / "external_hair_dataset"
V8_DIR = REPO_ROOT / "CharacterPackage" / "semantic_layer_v8"


RECOMMENDATIONS = {
    "local_study_only",
    "reference_report_only",
    "open_template_source",
    "do_not_use",
    "pending",
}

LICENSE_CONFIDENCE = {"high", "medium-high", "medium", "medium-low", "low", "unknown"}

FORBIDDEN_BINARY_EXTENSIONS = {
    ".blend",
    ".fbx",
    ".glb",
    ".gltf",
    ".obj",
    ".zip",
    ".rar",
    ".7z",
    ".tif",
    ".tiff",
    ".exr",
    ".mp4",
    ".mov",
}

APPROVED_BINARY_PREFIXES = {
    DATASET_DIR / "sketchfab_gorgeous_japanese_fight" / "source" / "gorgeous_japanese_fight.glb",
    DATASET_DIR / "sketchfab_gorgeous_japanese_fight" / "extracted" / "pink_hair_segment_probe.glb",
    DATASET_DIR / "sketchfab_gorgeous_japanese_fight" / "extracted" / "pink_hair_segment_probe.obj",
    DATASET_DIR / "sketchfab_gorgeous_japanese_fight" / "extracted" / "pink_hair_segment_probe.blend",
}


class ExternalHairDatasetPilotTests(unittest.TestCase):
    def load_manifest(self) -> dict:
        return json.loads((DATASET_DIR / "assets_manifest.json").read_text(encoding="utf-8"))

    def load_report(self) -> dict:
        return json.loads((DATASET_DIR / "external_hair_dataset_pilot_v0_report.json").read_text(encoding="utf-8"))

    def test_required_pilot_files_exist(self) -> None:
        required = [
            DATASET_DIR / "README.md",
            DATASET_DIR / "SOURCE_TRIAGE.md",
            DATASET_DIR / "assets_manifest.schema.json",
            DATASET_DIR / "assets_manifest.json",
            DATASET_DIR / "external_hair_dataset_pilot_v0_report.json",
            DATASET_DIR / "subagent_reports" / "source_scout_report.md",
            DATASET_DIR / "subagent_reports" / "dataset_schema_plan.md",
            DATASET_DIR / "subagent_reports" / "intake_pipeline_plan.md",
            DATASET_DIR / "subagent_reports" / "hair_prior_plan.md",
            DATASET_DIR / "subagent_reports" / "test_contract_plan.md",
        ]

        for path in required:
            self.assertTrue(path.exists(), f"missing required pilot file: {path}")

    def test_manifest_is_prior_only_and_has_sources(self) -> None:
        manifest = self.load_manifest()

        self.assertEqual(manifest["schema_version"], "external_hair_dataset_manifest_v0.1")
        self.assertEqual(manifest["dataset_id"], "external_hair_dataset_pilot_v0")
        self.assertTrue(manifest["project_guards"]["v8_immutable"])
        self.assertFalse(manifest["project_guards"]["replace_in_beauty_glb"])
        self.assertEqual(manifest["project_guards"]["external_asset_usage"], "prior_only")
        self.assertFalse(manifest["project_guards"]["large_binaries_committed"])
        self.assertTrue(manifest["project_guards"]["cloth_seam_surface_blocked"])
        self.assertGreaterEqual(len(manifest["sources"]), 5)

    def test_sources_use_closed_recommendations_and_conservative_permissions(self) -> None:
        manifest = self.load_manifest()

        source_ids: set[str] = set()
        for source in manifest["sources"]:
            self.assertNotIn(source["source_id"], source_ids)
            source_ids.add(source["source_id"])
            self.assertIn(source["recommendation"], RECOMMENDATIONS)
            self.assertIn(source["license_confidence"], LICENSE_CONFIDENCE)
            self.assertEqual(source["external_asset_usage"], "prior_only")
            self.assertFalse(source["replace_in_beauty_glb"])
            self.assertEqual(source["download_status"], "not_downloaded")
            self.assertEqual(source["validation_status"]["status"], "skipped")
            self.assertTrue(source["validation_status"]["skipped_with_reason"])
            self.assertNotEqual(source["can_commit_binary_to_repo"], "yes_unrestricted")

        open_sources = [source for source in manifest["sources"] if source["recommendation"] == "open_template_source"]
        self.assertGreaterEqual(len(open_sources), 5)
        for source in open_sources:
            self.assertIn(source["license_confidence"], {"high", "medium-high"})

    def test_only_approved_external_binary_payloads_are_present(self) -> None:
        offenders = [
            path
            for path in DATASET_DIR.rglob("*")
            if path.is_file()
            and path.suffix.lower() in FORBIDDEN_BINARY_EXTENSIONS
            and path not in APPROVED_BINARY_PREFIXES
        ]

        self.assertEqual(offenders, [])

        sketchfab_dir = DATASET_DIR / "sketchfab_gorgeous_japanese_fight"
        for path in APPROVED_BINARY_PREFIXES:
            self.assertTrue(path.exists(), f"missing approved binary payload: {path}")
        self.assertTrue((sketchfab_dir / "ATTRIBUTION.md").exists())
        self.assertTrue((sketchfab_dir / "README.md").exists())
        self.assertTrue((sketchfab_dir / "source" / "source_page_snapshot.html").exists())
        self.assertTrue((sketchfab_dir / "analysis" / "hair_prior_analysis.md").exists())

    def test_readme_and_triage_state_blocked_behavior(self) -> None:
        readme = (DATASET_DIR / "README.md").read_text(encoding="utf-8")
        triage = (DATASET_DIR / "SOURCE_TRIAGE.md").read_text(encoding="utf-8")

        for text in (readme, triage):
            self.assertIn("replace_in_beauty_glb", text)
            self.assertIn("prior", text.lower())
            self.assertNotIn("production-ready replacement", text.lower())

        self.assertIn("cloth_seam_surface", readme)
        self.assertIn("not_downloaded", json.dumps(self.load_manifest()))

    def test_pilot_report_is_metadata_only_and_cloth_blocked(self) -> None:
        report = self.load_report()

        self.assertEqual(report["status"], "metadata_scaffold_generated")
        self.assertFalse(report["summary"]["downloaded_binaries"])
        self.assertFalse(report["summary"]["generated_assets"])
        self.assertFalse(report["summary"]["large_binaries_committed"])
        self.assertEqual(report["summary"]["external_asset_usage"], "prior_only")
        self.assertFalse(report["summary"]["replace_in_beauty_glb"])
        self.assertFalse(report["summary"]["ready_for_cloth_seam_surface"])
        self.assertIn("skipped_with_reason", report["pilot_gate"])

    def test_v8_baseline_directory_still_exists(self) -> None:
        self.assertTrue(V8_DIR.exists())
        self.assertTrue((V8_DIR / "specs" / "yuna_semantic_layer_v8.json").exists())


if __name__ == "__main__":
    unittest.main()
