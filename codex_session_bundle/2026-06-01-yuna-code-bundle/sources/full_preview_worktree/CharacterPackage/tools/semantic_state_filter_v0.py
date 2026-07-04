#!/usr/bin/env python3
"""Read-only semantic state filter for YUNA semantic_layer_v8.

This script maps the current v8 asset state into the Bounded Semantic Geometry
Filter parameter space and writes a v9 candidate spec. It does not modify v8
and it does not generate GLB/FBX/OBJ files.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from semantic_filter.filter import filter_part
from semantic_filter.observations import build_observations, detect_constraints, load_json, normalize_part_states
from semantic_filter.report import build_candidate_spec, decision_markdown, write_json
from semantic_filter.state import FilterReport


CHARACTER_PACKAGE = Path(__file__).resolve().parents[1]
REPO_ROOT = CHARACTER_PACKAGE.parent
DEFAULT_SPEC = CHARACTER_PACKAGE / "semantic_layer_v8" / "specs" / "yuna_semantic_layer_v8.json"
DEFAULT_REPORT = CHARACTER_PACKAGE / "semantic_layer_v8" / "validation_report.json"
DEFAULT_OUTPUT = CHARACTER_PACKAGE / "semantic_layer_v9_candidate"
FORMULA = (
    "theta_next = ProjectToConstraints((1-alpha)*theta "
    "+ alpha*RobustFuse(front_obs, side_obs, back_obs, validation_obs, prior))"
)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a read-only v9 candidate spec from semantic_layer_v8.")
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--validation-report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--alpha", type=float, default=0.65)
    return parser.parse_args()


def build_filter_report(spec_path: Path, validation_report_path: Path, output_dir: Path, alpha: float = 0.65) -> FilterReport:
    spec = load_json(spec_path)
    validation_report = load_json(validation_report_path)
    constraints = detect_constraints(spec)
    states = normalize_part_states(spec, validation_report)
    observations = build_observations(spec, validation_report, states)
    observations_by_part = {}
    for observation in observations:
        observations_by_part.setdefault(observation.part_id, []).append(observation)

    decisions = [
        filter_part(
            state,
            observations_by_part.get(state.id, []),
            constraints,
            alpha=alpha,
        )
        for state in states
    ]

    output_paths = {
        "candidate_spec": display_path(output_dir / "specs" / "yuna_semantic_layer_v9_candidate.json"),
        "filter_report": display_path(output_dir / "filter_report.json"),
        "filter_decisions": display_path(output_dir / "filter_decisions.md"),
    }

    return FilterReport(
        route="semantic_state_filter_v0_on_v8",
        input_route=validation_report.get("route") or spec.get("character", {}).get("route"),
        formula=FORMULA,
        applicability={
            "status": "applicable",
            "reason": (
                "v8 exposes semantic parts, generator types, side/back soft constraints, "
                "validation reports, roundtrip status, and beauty/debug visibility split."
            ),
        },
        constraints=constraints,
        global_decisions=[
            {
                "decision": "do_not_modify_v8",
                "reason": "v8 is the current visual-review baseline and must remain reproducible.",
            },
            {
                "decision": "generate_v9_candidate_spec_only",
                "reason": "the first formula pass plans upgrades instead of rebuilding geometry.",
            },
            {
                "decision": "keep_beauty_until_replacement_validated",
                "reason": "candidate generators must pass screenshot/roundtrip validation before replacing v8 beauty meshes.",
            },
        ],
        part_states=states,
        observations=observations,
        part_decisions=decisions,
        output_paths=output_paths,
    )


def write_outputs(report: FilterReport, output_dir: Path) -> dict[str, Path]:
    candidate_path = output_dir / "specs" / "yuna_semantic_layer_v9_candidate.json"
    report_path = output_dir / "filter_report.json"
    decisions_path = output_dir / "filter_decisions.md"
    write_json(candidate_path, build_candidate_spec(report))
    write_json(report_path, report.to_dict())
    decisions_path.parent.mkdir(parents=True, exist_ok=True)
    decisions_path.write_text(decision_markdown(report.part_decisions), encoding="utf-8")
    return {
        "candidate_spec": candidate_path,
        "filter_report": report_path,
        "filter_decisions": decisions_path,
    }


def main() -> None:
    args = parse_args()
    report = build_filter_report(args.spec, args.validation_report, args.output_dir, alpha=args.alpha)
    paths = write_outputs(report, args.output_dir)
    for label, path in paths.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
