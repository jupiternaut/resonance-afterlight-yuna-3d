#!/usr/bin/env python3
"""Build manual-review variants for the art-directed v1 hair ribbon route."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from build_hair_target_schema_v1 import build_report as build_target_schema_report
from semantic_actuators.art_directed_hair_ribbons_v1 import (
    HAIR_REVIEW_VARIANTS,
    HairVariantConfig,
    run_art_directed_hair_ribbons_variant,
)
from semantic_actuators.state import ActuatorPaths


CHARACTER_PACKAGE = Path(__file__).resolve().parents[1]
REPO_ROOT = CHARACTER_PACKAGE.parent
OUT = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "art_directed_v1_variants"
VARIANT_NAMES = ("balanced", "fuller", "silhouette")
COMPARISON_REPORT = OUT / "hair_variants_comparison_report.json"
CONTACT_SHEET = OUT / "hair_variants_contact_sheet.png"
MANUAL_REVIEW = OUT / "manual_review_hair_v1.md"

METRIC_KEYS = (
    "forbidden_candidate_leak_ratio",
    "candidate_soft_inside_ratio",
    "candidate_core_coverage_ratio",
    "candidate_visible_area_ratio",
    "soft_silhouette_coverage_ratio",
    "bangs_presence_ratio",
    "side_hair_left_presence_ratio",
    "side_hair_right_presence_ratio",
    "back_hair_mass_presence_ratio",
    "component_count",
    "scalp_anchor_continuity",
    "candidate_front_visible_hair_mass",
    "primary_group_presence_passed",
    "yaw30_hair_readability",
    "side_hair_readability",
)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": display_path(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
    }


def run_step(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        args,
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {
        "args": [str(item) for item in args],
        "exit_code": result.returncode,
        "log_tail": result.stdout.splitlines()[-60:],
    }


def variant_paths(variant_name: str) -> tuple[Path, str, ActuatorPaths]:
    variant_dir = OUT / variant_name
    stem = f"yuna_semantic_layer_v9_hair_art_directed_v1_{variant_name}"
    return (
        variant_dir,
        stem,
        ActuatorPaths(
            repo_root=REPO_ROOT,
            character_package=CHARACTER_PACKAGE,
            output_dir=variant_dir,
            spec_path=variant_dir / "specs" / f"{stem}.json",
            obj_path=variant_dir / "exports" / f"{stem}.obj",
            glb_path=variant_dir / "exports" / f"{stem}.glb",
            report_path=variant_dir / "validation_report.json",
        ),
    )


def run_blender_validation(paths: ActuatorPaths, variant_dir: Path) -> tuple[dict[str, Any], Path]:
    validation_dir = variant_dir / "validation_ci"
    validation_report = validation_dir / "validation_ci_report.json"
    step = run_step(
        [
            sys.executable,
            str(CHARACTER_PACKAGE / "tools" / "run_blender_semantic_validation.py"),
            "--candidate-glb",
            str(paths.glb_path),
            "--candidate-report",
            str(paths.report_path),
            "--output-dir",
            str(validation_dir),
            "--report",
            str(validation_report),
        ]
    )
    candidate_front = validation_dir / f"{paths.glb_path.stem}_validation_candidate_front.png"
    return step, candidate_front


def evaluate_target_schema(paths: ActuatorPaths, variant_dir: Path, candidate_front: Path) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if not candidate_front.exists():
        return {
            "args": [],
            "exit_code": 0,
            "skipped_with_reason": "candidate_front_render_missing",
        }, None

    schema_dir = variant_dir / "target_schema_v1_eval"
    report = build_target_schema_report(
        schema_dir,
        update_reports=True,
        candidate_front=candidate_front,
        candidate_route_label=f"art_directed_hair_ribbons_v1_{variant_dir.name}",
        validation_report_path=paths.report_path,
        validation_ci_report_path=variant_dir / "validation_ci" / "validation_ci_report.json",
    )
    return {
        "args": [
            "build_hair_target_schema_v1.build_report",
            "--output-dir",
            display_path(schema_dir),
            "--candidate-front",
            display_path(candidate_front),
        ],
        "exit_code": 0,
        "log_tail": [
            f"candidate_target_schema_status={report['candidate_target_schema_status']}",
            f"forbidden_candidate_leak_ratio={report['forbidden_candidate_leak_ratio']}",
        ],
    }, report


def compact_variant_summary(
    variant_name: str,
    config: HairVariantConfig,
    paths: ActuatorPaths,
    actuator_result: dict[str, Any],
    blender_step: dict[str, Any],
    schema_step: dict[str, Any],
    schema_report: dict[str, Any] | None,
) -> dict[str, Any]:
    metrics = {key: schema_report.get(key) for key in METRIC_KEYS} if schema_report else {}
    validation = actuator_result.get("validation", {})
    return {
        "variant": variant_name,
        "review_intent": config.review_intent,
        "status": schema_report.get("candidate_route_status") if schema_report else actuator_result.get("status"),
        "candidate_target_schema_status": schema_report.get("candidate_target_schema_status") if schema_report else None,
        "manual_visual_review_status": schema_report.get("manual_visual_review_status") if schema_report else "blocked_by_missing_schema_eval",
        "replace_in_beauty_glb": bool(validation.get("replace_in_beauty_glb", False)),
        "ready_for_cloth_seam_surface": False,
        "metrics": metrics,
        "mesh_summary": actuator_result.get("mesh_summary", {}),
        "exports": {
            "spec": file_record(paths.spec_path),
            "obj": file_record(paths.obj_path),
            "mtl": file_record(paths.obj_path.with_suffix(".mtl")),
            "glb": file_record(paths.glb_path),
            "blend": file_record(paths.glb_path.with_suffix(".blend")),
            "validation_report": file_record(paths.report_path),
            "validation_ci_report": file_record(paths.output_dir / "validation_ci" / "validation_ci_report.json"),
        },
        "screenshots": screenshot_records(paths),
        "steps": {
            "blender_validation": blender_step,
            "target_schema_eval": schema_step,
        },
        "acceptance_boundary": "manual-review candidate only; not accepted and not production hair",
    }


def screenshot_records(paths: ActuatorPaths) -> dict[str, dict[str, Any]]:
    validation_dir = paths.output_dir / "validation_ci"
    stem = paths.glb_path.stem
    mapping = {
        "candidate_front": validation_dir / f"{stem}_validation_candidate_front.png",
        "overlay_front": validation_dir / f"{stem}_validation_overlay_front.png",
        "yaw15": validation_dir / f"{stem}_validation_yaw15.png",
        "yaw30": validation_dir / f"{stem}_validation_yaw30.png",
        "side": validation_dir / f"{stem}_validation_side.png",
        "wire": validation_dir / f"{stem}_validation_wire.png",
        "exploded": validation_dir / f"{stem}_validation_exploded.png",
    }
    return {name: file_record(path) for name, path in mapping.items()}


def score_variant(summary: dict[str, Any]) -> float:
    metrics = summary.get("metrics", {})
    if not metrics:
        return -999.0
    leak = float(metrics.get("forbidden_candidate_leak_ratio") or 1.0)
    soft = float(metrics.get("candidate_soft_inside_ratio") or 0.0)
    core = float(metrics.get("candidate_core_coverage_ratio") or 0.0)
    visible = float(metrics.get("candidate_visible_area_ratio") or 0.0)
    coverage = float(metrics.get("soft_silhouette_coverage_ratio") or 0.0)
    readability_bonus = 0.1 if metrics.get("yaw30_hair_readability") else 0.0
    readability_bonus += 0.1 if metrics.get("side_hair_readability") else 0.0
    readability_bonus += 0.1 if metrics.get("candidate_front_visible_hair_mass") else -0.25
    readability_bonus += 0.1 if metrics.get("primary_group_presence_passed") else -0.25
    leak_penalty = max(0.0, leak - 0.10) * 4.0
    return soft + core + coverage + min(visible * 40.0, 0.6) + readability_bonus - leak_penalty


def choose_recommended_variant(summaries: list[dict[str, Any]]) -> str | None:
    if not summaries:
        return None
    return max(summaries, key=score_variant)["variant"]


def make_contact_sheet(summaries: list[dict[str, Any]], output_path: Path) -> None:
    tile = (360, 480)
    rows = [
        ("candidate_front", "candidate front"),
        ("overlay_front", "overlay front"),
        ("yaw30", "yaw30"),
        ("side", "side"),
    ]
    columns = summaries
    sheet = Image.new("RGBA", (tile[0] * len(columns), tile[1] * len(rows)), (24, 24, 24, 255))
    draw = ImageDraw.Draw(sheet)
    for col, summary in enumerate(columns):
        for row, (key, label) in enumerate(rows):
            record = summary["screenshots"][key]
            x = col * tile[0]
            y = row * tile[1]
            if record["exists"]:
                image = Image.open(REPO_ROOT / record["path"]).convert("RGBA").resize(tile, Image.Resampling.LANCZOS)
            else:
                image = Image.new("RGBA", tile, (50, 50, 50, 255))
                ImageDraw.Draw(image).text((16, 220), "missing", fill=(255, 128, 128, 255))
            sheet.alpha_composite(image, (x, y))
            draw.rectangle((x, y, x + tile[0] - 1, y + 36), fill=(0, 0, 0, 190))
            draw.text((x + 8, y + 9), f"{summary['variant']} / {label}", fill=(255, 255, 255, 255))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def write_manual_review(summaries: list[dict[str, Any]], recommended_variant: str | None) -> None:
    lines = [
        "# Manual Review: Hair V1 Variants",
        "",
        "This pack is for human visual review only. No variant replaces v8 beauty hair, no variant unblocks cloth, and no variant is production-ready hair.",
        "",
        "Current caution: candidate-only renders may still read as sparse fragments. The recommendation below is only the first variant to inspect, not an acceptance decision.",
        "",
        f"Recommended first review target: `{recommended_variant or 'none'}`.",
        "",
        "| Variant | Status | Manual gate | Leak | Soft inside | Core coverage | Visible area | Soft coverage | Front mass | Yaw30 | Side | Review note |",
        "|---|---|---|---:|---:|---:|---:|---:|---|---|---|---|",
    ]
    for summary in summaries:
        metrics = summary["metrics"]
        lines.append(
            "| {variant} | {status} | {manual_gate} | {leak} | {soft} | {core} | {visible} | {coverage} | {front_mass} | {yaw} | {side} | manual review required |".format(
                variant=summary["variant"],
                status=summary.get("status"),
                manual_gate=summary.get("manual_visual_review_status"),
                leak=metrics.get("forbidden_candidate_leak_ratio"),
                soft=metrics.get("candidate_soft_inside_ratio"),
                core=metrics.get("candidate_core_coverage_ratio"),
                visible=metrics.get("candidate_visible_area_ratio"),
                coverage=metrics.get("soft_silhouette_coverage_ratio"),
                front_mass=metrics.get("candidate_front_visible_hair_mass"),
                yaw=metrics.get("yaw30_hair_readability"),
                side=metrics.get("side_hair_readability"),
            )
        )
    lines.extend(
        [
            "",
            "## Review Instructions",
            "",
            "1. Start with `hair_variants_contact_sheet.png`.",
            "2. Check candidate-only front first; it must read as hair without relying on v8 overlay.",
            "3. Check yaw30 and side for broken slice-wall artifacts.",
            "4. Reject any variant that looks like shredded body/cloth texture, even if numeric gates pass.",
            "5. Keep `cloth_seam_surface` blocked until a human accepts a hair variant or requests another hair refinement pass.",
        ]
    )
    MANUAL_REVIEW.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_variant(variant_name: str) -> dict[str, Any]:
    config = HAIR_REVIEW_VARIANTS[variant_name]
    variant_dir, _, paths = variant_paths(variant_name)
    result = run_art_directed_hair_ribbons_variant(paths, config)
    blender_step, candidate_front = run_blender_validation(paths, variant_dir)
    schema_step, schema_report = evaluate_target_schema(paths, variant_dir, candidate_front)
    return compact_variant_summary(
        variant_name,
        config,
        paths,
        result.to_dict(),
        blender_step,
        schema_step,
        schema_report,
    )


def build_pack(variant_names: tuple[str, ...] = VARIANT_NAMES) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    summaries = [build_variant(name) for name in variant_names]
    generated_count = sum(1 for item in summaries if item["exports"]["obj"]["exists"])
    recommended_variant = choose_recommended_variant(summaries)
    make_contact_sheet(summaries, CONTACT_SHEET)
    write_manual_review(summaries, recommended_variant)
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": "build_art_directed_hair_ribbons_v1_variants",
        "status": "manual_review_pack_generated" if generated_count >= 2 else "failed_insufficient_variants_generated",
        "boundary": "Human visual review pack only; does not replace v8 beauty and does not unblock cloth.",
        "formula_binding": {
            "state": "theta_hair variant parameters under strict/soft/forbidden target schema",
            "update": "ProjectToConstraints_hair(RobustFuse(variant_design, strict_hair_core, soft_hair_silhouette, forbidden_nonhair_zone, front_identity, manual_visual_review))",
        },
        "variant_count": len(summaries),
        "generated_variant_count": generated_count,
        "recommended_first_human_review_variant": recommended_variant,
        "replace_in_beauty_glb": False,
        "ready_for_cloth_seam_surface": False,
        "manual_review_warning": (
            "This pack is evidence for human review only. Candidate-only renders may still look sparse or fragmented; "
            "the recommended variant is a first review target, not an accepted replacement."
        ),
        "variant_summaries": summaries,
        "artifacts": {
            "comparison_report": file_record(COMPARISON_REPORT),
            "contact_sheet": file_record(CONTACT_SHEET),
            "manual_review": file_record(MANUAL_REVIEW),
        },
    }
    write_json(COMPARISON_REPORT, report)
    report["artifacts"]["comparison_report"] = file_record(COMPARISON_REPORT)
    write_json(COMPARISON_REPORT, report)
    if generated_count < 2:
        failure = OUT / "failure_report.md"
        failure.write_text(
            "# Hair V1 Variant Pack Failure\n\n"
            f"Only {generated_count} variants generated. Keep cloth blocked.\n",
            encoding="utf-8",
        )
    return report


def main() -> int:
    report = build_pack()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["generated_variant_count"] >= 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
