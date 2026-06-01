#!/usr/bin/env python3
"""Build the art-directed v1 hair ribbon candidate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from semantic_actuators.art_directed_hair_ribbons_v1 import run_art_directed_hair_ribbons_v1
from semantic_actuators.state import ActuatorPaths


CHARACTER_PACKAGE = Path(__file__).resolve().parents[1]
REPO_ROOT = CHARACTER_PACKAGE.parent
OUT = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "art_directed_v1"
STEM = "yuna_semantic_layer_v9_hair_art_directed_v1"
VALIDATION_DIR = OUT / "validation_ci"
VALIDATION_CI_REPORT = VALIDATION_DIR / "validation_ci_report.json"
TARGET_SCHEMA_EVAL_DIR = OUT / "target_schema_v1_eval"


def run_step(args: list[str]) -> dict[str, object]:
    result = subprocess.run(
        args,
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {
        "args": args,
        "exit_code": result.returncode,
        "log_tail": result.stdout.splitlines()[-40:],
    }


def main() -> int:
    paths = ActuatorPaths(
        repo_root=REPO_ROOT,
        character_package=CHARACTER_PACKAGE,
        output_dir=OUT,
        spec_path=OUT / "specs" / f"{STEM}.json",
        obj_path=OUT / "exports" / f"{STEM}.obj",
        glb_path=OUT / "exports" / f"{STEM}.glb",
        report_path=OUT / "validation_report.json",
    )
    result = run_art_directed_hair_ribbons_v1(paths)
    validation_step = run_step(
        [
            sys.executable,
            str(CHARACTER_PACKAGE / "tools" / "run_blender_semantic_validation.py"),
            "--candidate-glb",
            str(paths.glb_path),
            "--candidate-report",
            str(paths.report_path),
            "--output-dir",
            str(VALIDATION_DIR),
            "--report",
            str(VALIDATION_CI_REPORT),
        ]
    )
    candidate_front = VALIDATION_DIR / f"{paths.glb_path.stem}_validation_candidate_front.png"
    schema_step: dict[str, object]
    if candidate_front.exists():
        schema_step = run_step(
            [
                sys.executable,
                str(CHARACTER_PACKAGE / "tools" / "build_hair_target_schema_v1.py"),
                "--output-dir",
                str(TARGET_SCHEMA_EVAL_DIR),
                "--candidate-front",
                str(candidate_front),
                "--candidate-route-label",
                "art_directed_hair_ribbons_v1",
                "--validation-report",
                str(paths.report_path),
                "--validation-ci-report",
                str(VALIDATION_CI_REPORT),
            ]
        )
    else:
        schema_step = {
            "args": [],
            "exit_code": 0,
            "skipped_with_reason": "candidate_front_render_missing",
        }
    print(
        json.dumps(
            {
                "actuator": result.to_dict(),
                "blender_validation": validation_step,
                "target_schema_eval": schema_step,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result.status != "failed" else 1


if __name__ == "__main__":
    sys.exit(main())
