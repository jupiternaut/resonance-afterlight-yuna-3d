from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CharacterPackage" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from semantic_filter.observations import (  # noqa: E402
    build_observations,
    detect_constraints,
    load_json,
    normalize_part_states,
)
from semantic_state_filter_v0 import build_filter_report, write_outputs  # noqa: E402


SPEC_PATH = REPO_ROOT / "CharacterPackage" / "semantic_layer_v8" / "specs" / "yuna_semantic_layer_v8.json"
VALIDATION_REPORT_PATH = REPO_ROOT / "CharacterPackage" / "semantic_layer_v8" / "validation_report.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SemanticStateFilterV0Tests(unittest.TestCase):
    def test_reads_v8_spec_and_validation_report(self) -> None:
        spec = load_json(SPEC_PATH)
        report = load_json(VALIDATION_REPORT_PATH)

        self.assertEqual(spec["character"]["route"], "semantic_layer_v8_beauty_main_debug_cage_split")
        self.assertEqual(report["route"], "semantic_layer_v8_beauty_main_debug_cage_split")
        self.assertEqual(report["status"], "generated_with_warnings")

    def test_normalizes_visibility_split_and_debug_guides(self) -> None:
        spec = load_json(SPEC_PATH)
        report = load_json(VALIDATION_REPORT_PATH)
        states = {state.id: state for state in normalize_part_states(spec, report)}

        self.assertIn("leg_L_visual_panel", states)
        self.assertIn("leg_R_visual_panel", states)
        self.assertIn("leg_L_retopo_proxy", states)
        self.assertTrue(states["leg_L_visual_panel"].visible_in_beauty)
        self.assertFalse(states["leg_L_retopo_proxy"].visible_in_beauty)
        self.assertTrue(states["leg_L_retopo_proxy"].visible_in_cage)
        self.assertTrue(states["leg_L_retopo_proxy"].debug_only)

    def test_side_back_are_soft_constraints(self) -> None:
        spec = load_json(SPEC_PATH)
        report = load_json(VALIDATION_REPORT_PATH)
        states = normalize_part_states(spec, report)
        constraints = detect_constraints(spec)
        observations = build_observations(spec, report, states)

        self.assertTrue(constraints.side_back_are_soft)
        side_obs = [obs for obs in observations if obs.source == "side"]
        back_obs = [obs for obs in observations if obs.source == "back"]
        self.assertTrue(side_obs)
        self.assertTrue(back_obs)
        self.assertTrue(all(obs.confidence < 1.0 for obs in side_obs + back_obs))
        self.assertTrue(all("soft inferred constraints" in " ".join(obs.warnings) for obs in side_obs + back_obs))

    def test_required_decisions_are_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_filter_report(SPEC_PATH, VALIDATION_REPORT_PATH, Path(tmp))
        decisions = {decision.part_id: decision for decision in report.part_decisions}

        self.assertEqual(decisions["weapon"].decision, "upgrade_required")
        self.assertEqual(decisions["weapon"].proposed_generator, "weapon_hardsurface_ortho")
        self.assertEqual(decisions["legs"].decision, "retopo_required")
        self.assertEqual(decisions["legs"].proposed_generator, "leg_quad_loop_retopo_proxy")
        self.assertEqual(decisions["boots"].decision, "upgrade_required")
        self.assertEqual(decisions["boots"].proposed_generator, "boot_hardsurface_ortho")
        self.assertEqual(decisions["leg_L_retopo_proxy"].decision, "keep_debug_only")
        self.assertFalse(decisions["leg_L_retopo_proxy"].visible_in_beauty)
        self.assertTrue(decisions["leg_L_retopo_proxy"].visible_in_cage)

    def test_writes_outputs_without_modifying_v8_inputs(self) -> None:
        spec_before = sha256(SPEC_PATH)
        report_before = sha256(VALIDATION_REPORT_PATH)

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "semantic_layer_v9_candidate"
            filter_report = build_filter_report(SPEC_PATH, VALIDATION_REPORT_PATH, output_dir)
            paths = write_outputs(filter_report, output_dir)

            self.assertTrue(paths["candidate_spec"].exists())
            self.assertTrue(paths["filter_report"].exists())
            self.assertTrue(paths["filter_decisions"].exists())

            candidate = json.loads(paths["candidate_spec"].read_text(encoding="utf-8"))
            self.assertEqual(candidate["route"], "semantic_layer_v9_candidate_spec_only")
            self.assertEqual(candidate["source_route"], "semantic_layer_v8_beauty_main_debug_cage_split")

        self.assertEqual(spec_before, sha256(SPEC_PATH))
        self.assertEqual(report_before, sha256(VALIDATION_REPORT_PATH))


if __name__ == "__main__":
    unittest.main()
