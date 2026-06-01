#!/usr/bin/env python3
"""Build the curve-bundle v1 YUNA hair candidate."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from semantic_actuators.curve_bundle_hair_candidate_v1 import (
    ACTUATOR_NAME,
    run_curve_bundle_hair_candidate_v1,
)
from semantic_actuators.authored_hair_ribbons import write_json
from semantic_actuators.state import ActuatorPaths


CHARACTER_PACKAGE = Path(__file__).resolve().parents[1]
REPO_ROOT = CHARACTER_PACKAGE.parent
OUT = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "curve_bundle_candidate_v1"
STEM = "yuna_curve_bundle_hair_v1"
VALIDATION_DIR = OUT / "validation_ci"
VALIDATION_CI_REPORT = VALIDATION_DIR / "validation_ci_report.json"
TARGET_SCHEMA_EVAL_DIR = OUT / "target_schema_v1_eval"

SCREENSHOT_ALIASES = {
    "candidate_front": "candidate_front.png",
    "overlay_front": "overlay_front.png",
    "yaw30": "yaw30.png",
    "side": "side.png",
    "wire": "wire.png",
    "exploded": "exploded.png",
}


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
        "log_tail": result.stdout.splitlines()[-60:],
    }


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def alias_screenshots(paths: ActuatorPaths) -> dict[str, dict[str, object]]:
    aliases: dict[str, dict[str, object]] = {}
    for key, alias_name in SCREENSHOT_ALIASES.items():
        source = VALIDATION_DIR / f"{paths.glb_path.stem}_validation_{key}.png"
        target = VALIDATION_DIR / alias_name
        if source.exists():
            shutil.copyfile(source, target)
        aliases[key] = {
            "source": str(source.relative_to(REPO_ROOT)) if source.exists() else str(source),
            "path": str(target.relative_to(REPO_ROOT)),
            "exists": target.exists(),
            "bytes": target.stat().st_size if target.exists() else 0,
        }
    return aliases


def write_skipped_validation(reason: str) -> None:
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    write_json(
        VALIDATION_CI_REPORT,
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "route": "blender_semantic_validation_v0",
            "status": "skipped_with_reason",
            "reason": reason,
            "ready_for_cloth_seam_surface": False,
        },
    )


def finalize_failure_semantics(report_path: Path, ci_report_path: Path) -> None:
    """Keep target-schema failure details but expose the route status requested by the goal."""

    report = load_json(report_path)
    validation = report.setdefault("validation", {})
    target_status = validation.get("candidate_target_schema_status") or report.get("status")
    if target_status == "failed_target_schema_alignment":
        report["target_schema_status"] = target_status
        report["status"] = "curve_bundle_candidate_failed_visual_review"
        validation["visual_sanity_status"] = "curve_bundle_candidate_failed_visual_review"
        validation["visual_sanity_reason"] = (
            "curve bundle asset generated, but target_schema_v1 alignment failed; "
            "candidate remains blocked from cloth and beauty replacement"
        )
        validation["manual_visual_review_status"] = "blocked_by_target_schema_alignment"
        validation["manual_visual_review"] = "failed_programmatic_visual_gate"
        validation["ready_for_cloth_seam_surface"] = False
        report["ready_for_cloth_seam_surface"] = False
        write_json(report_path, report)

    ci_report = load_json(ci_report_path)
    if ci_report:
        ci_report["ready_for_cloth_seam_surface"] = False
        if target_status == "failed_target_schema_alignment":
            ci_report["target_schema_status"] = target_status
            ci_report["status"] = "curve_bundle_candidate_failed_visual_review"
            ci_report.setdefault("candidate_contract", {})["visual_sanity_status"] = "curve_bundle_candidate_failed_visual_review"
            ci_report.setdefault("quality", {}).setdefault("visual_sanity", {})[
                "visual_sanity_status"
            ] = "curve_bundle_candidate_failed_visual_review"
        write_json(ci_report_path, ci_report)


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
    result = run_curve_bundle_hair_candidate_v1(paths)
    validation_step: dict[str, object]
    schema_step: dict[str, object]
    if paths.glb_path.exists():
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
        aliases = alias_screenshots(paths)
        ci_report = load_json(VALIDATION_CI_REPORT)
        ci_report["screenshot_aliases"] = aliases
        ci_report["ready_for_cloth_seam_surface"] = False
        write_json(VALIDATION_CI_REPORT, ci_report)
        candidate_front = VALIDATION_DIR / f"{paths.glb_path.stem}_validation_candidate_front.png"
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
                    ACTUATOR_NAME,
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
    else:
        write_skipped_validation("candidate_glb_missing_or_blender_export_skipped")
        validation_step = {
            "args": [],
            "exit_code": 0,
            "skipped_with_reason": "candidate_glb_missing_or_blender_export_skipped",
        }
        schema_step = {
            "args": [],
            "exit_code": 0,
            "skipped_with_reason": "candidate_front_render_missing",
        }
    finalize_failure_semantics(paths.report_path, VALIDATION_CI_REPORT)
    print(
        json.dumps(
            {
                "actuator": result.to_dict(),
                "blender_validation": validation_step,
                "target_schema_eval": schema_step,
                "output_dir": str(OUT.relative_to(REPO_ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result.status != "failed" else 1


if __name__ == "__main__":
    sys.exit(main())
