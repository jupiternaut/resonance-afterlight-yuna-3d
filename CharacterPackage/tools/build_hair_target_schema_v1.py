#!/usr/bin/env python3
"""Build the v1 three-layer hair target schema for future authored ribbons."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from run_blender_semantic_validation import (
    CHARACTER_PACKAGE,
    HAIR_CONTAMINANT_PARTS,
    HAIR_PART_IDS,
    REPO_ROOT,
    bool_matrix_to_image,
    count_intersection,
    count_mask_pixels,
    file_record,
    foreground_mask_from_render,
    load_json,
    source_mask_to_render_bool,
    union_source_masks,
    write_json,
)


OUT_DIR = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "target_schema_v1"
BASELINE_FRONT = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "validation_ci" / "yuna_semantic_layer_v9_hair_validation_baseline_front.png"
CANDIDATE_FRONT = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "validation_ci" / "yuna_semantic_layer_v9_hair_validation_candidate_front.png"
TARGET_REVIEW_REFINED = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "target_review" / "hair_target_mask_refined_component_priors.png"
VALIDATION_REPORT = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "validation_report.json"
VALIDATION_CI_REPORT = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "validation_ci" / "validation_ci_report.json"


SCHEMA_THRESHOLDS = {
    "core_body_overlap_ratio": 0.02,
    "soft_body_overlap_ratio": 0.20,
    "forbidden_candidate_leak_ratio": 0.10,
    "candidate_core_coverage_ratio": 0.10,
    "candidate_soft_inside_ratio": 0.70,
}


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def mask_pixel_count(mask: Image.Image) -> int:
    return sum(1 for value in mask.getdata() if value > 0)


def union_masks(masks: list[Image.Image]) -> Image.Image:
    if not masks:
        raise ValueError("Expected at least one mask")
    result = Image.new("L", masks[0].size, 0)
    for mask in masks:
        result = ImageChops.lighter(result, mask.convert("L"))
    return result.point(lambda value: 255 if value > 0 else 0)


def subtract_mask(source: Image.Image, blocker: Image.Image) -> Image.Image:
    return ImageChops.subtract(source.convert("L"), blocker.convert("L")).point(lambda value: 255 if value > 0 else 0)


def dilate(mask: Image.Image, radius: int) -> Image.Image:
    size = max(3, radius * 2 + 1)
    if size % 2 == 0:
        size += 1
    return mask.convert("L").filter(ImageFilter.MaxFilter(size)).point(lambda value: 255 if value > 0 else 0)


def overlap_ratio(target: Image.Image, overlap_mask: Image.Image) -> float:
    target_pixels = mask_pixel_count(target)
    overlap = ImageChops.multiply(target.convert("L"), overlap_mask.convert("L"))
    return mask_pixel_count(overlap) / max(target_pixels, 1)


def load_refined_component_target(raw_union: Image.Image) -> tuple[Image.Image, str, float]:
    if TARGET_REVIEW_REFINED.exists():
        refined = Image.open(TARGET_REVIEW_REFINED).convert("L").point(lambda value: 255 if value > 0 else 0)
        if refined.size == raw_union.size:
            return refined, display_path(TARGET_REVIEW_REFINED), 0.68
    return raw_union.copy(), "fallback:raw_hair_union", 0.35


def build_schema_masks() -> tuple[dict[str, Image.Image], dict[str, Any]]:
    raw_hair_union = union_source_masks(HAIR_PART_IDS).point(lambda value: 255 if value > 0 else 0)
    refined_target, refined_source, refined_confidence = load_refined_component_target(raw_hair_union)

    face_mask = union_source_masks(HAIR_CONTAMINANT_PARTS["face"])
    body_mask = union_source_masks(HAIR_CONTAMINANT_PARTS["body"])
    weapon_mask = union_source_masks(HAIR_CONTAMINANT_PARTS["weapon"])
    contaminant_union = union_masks([face_mask, body_mask, weapon_mask])

    forbidden_nonhair_zone = dilate(contaminant_union, 3)
    strict_seed = ImageChops.multiply(raw_hair_union, refined_target).point(lambda value: 255 if value > 0 else 0)
    strict_hair_core = subtract_mask(strict_seed, dilate(contaminant_union, 2))

    # The soft silhouette keeps hair-like refined components and cautious flyaway
    # expansion from the raw union, but still removes known non-hair zones. This
    # makes it a rebuild target, not proof that the current candidate is valid.
    raw_flyaway_allowance = subtract_mask(dilate(raw_hair_union, 2), forbidden_nonhair_zone)
    refined_expansion = subtract_mask(dilate(refined_target, 3), forbidden_nonhair_zone)
    soft_hair_silhouette = union_masks([strict_hair_core, raw_flyaway_allowance, refined_expansion])

    masks = {
        "raw_hair_union": raw_hair_union,
        "refined_component_target": refined_target,
        "strict_hair_core": strict_hair_core,
        "soft_hair_silhouette": soft_hair_silhouette,
        "forbidden_nonhair_zone": forbidden_nonhair_zone,
        "face": face_mask,
        "body": body_mask,
        "weapon": weapon_mask,
    }
    provenance = {
        "strict_hair_core": {
            "source": [
                "v8 front hair masks",
                refined_source,
                "face/body/weapon contaminant subtraction",
            ],
            "confidence": "medium",
            "confidence_score": round(min(0.82, refined_confidence + 0.12), 2),
            "estimated": True,
        },
        "soft_hair_silhouette": {
            "source": [
                "v8 front hair masks",
                refined_source,
                "dilated flyaway allowance",
                "forbidden nonhair subtraction",
            ],
            "confidence": "medium_low",
            "confidence_score": round(min(0.72, refined_confidence + 0.04), 2),
            "estimated": True,
        },
        "forbidden_nonhair_zone": {
            "source": [
                "v8 face mask",
                "v8 body/cloth/legs/boots masks",
                "v8 weapon mask",
            ],
            "confidence": "high",
            "confidence_score": 0.86,
            "estimated": True,
        },
    }
    return masks, provenance


def render_mask(mask: Image.Image, width: int, height: int) -> list[list[bool]]:
    return source_mask_to_render_bool(mask, width, height)


def schema_candidate_metrics(masks: dict[str, Image.Image]) -> dict[str, Any]:
    candidate_mask, width, height, candidate_pixels = foreground_mask_from_render(CANDIDATE_FRONT)
    strict_render = render_mask(masks["strict_hair_core"], width, height)
    soft_render = render_mask(masks["soft_hair_silhouette"], width, height)
    forbidden_render = render_mask(masks["forbidden_nonhair_zone"], width, height)

    strict_pixels = count_mask_pixels(strict_render, width, height)
    soft_pixels = count_mask_pixels(soft_render, width, height)
    forbidden_pixels = count_mask_pixels(forbidden_render, width, height)
    candidate_strict = count_intersection(candidate_mask, strict_render, width, height)
    candidate_soft = count_intersection(candidate_mask, soft_render, width, height)
    candidate_forbidden = count_intersection(candidate_mask, forbidden_render, width, height)

    core_body_overlap_ratio = overlap_ratio(masks["strict_hair_core"], masks["body"])
    soft_body_overlap_ratio = overlap_ratio(masks["soft_hair_silhouette"], masks["body"])
    forbidden_candidate_leak_ratio = candidate_forbidden / max(candidate_pixels, 1)
    candidate_core_coverage_ratio = candidate_strict / max(strict_pixels, 1)
    candidate_soft_inside_ratio = candidate_soft / max(candidate_pixels, 1)

    schema_ready = (
        mask_pixel_count(masks["strict_hair_core"]) > 1000
        and mask_pixel_count(masks["soft_hair_silhouette"]) > mask_pixel_count(masks["strict_hair_core"])
        and mask_pixel_count(masks["forbidden_nonhair_zone"]) > 1000
        and core_body_overlap_ratio <= SCHEMA_THRESHOLDS["core_body_overlap_ratio"]
        and soft_body_overlap_ratio <= SCHEMA_THRESHOLDS["soft_body_overlap_ratio"]
    )
    candidate_passes = (
        schema_ready
        and forbidden_candidate_leak_ratio <= SCHEMA_THRESHOLDS["forbidden_candidate_leak_ratio"]
        and candidate_core_coverage_ratio >= SCHEMA_THRESHOLDS["candidate_core_coverage_ratio"]
        and candidate_soft_inside_ratio >= SCHEMA_THRESHOLDS["candidate_soft_inside_ratio"]
    )

    if candidate_passes:
        candidate_status = "passed_target_schema_gate_manual_review_required"
    elif schema_ready:
        candidate_status = "failed_target_schema_alignment"
    else:
        candidate_status = "schema_not_ready_for_rebuild"

    return {
        "render_size": [width, height],
        "candidate_visible_pixel_count": candidate_pixels,
        "strict_core_render_pixel_count": strict_pixels,
        "soft_silhouette_render_pixel_count": soft_pixels,
        "forbidden_zone_render_pixel_count": forbidden_pixels,
        "strict_core_area": mask_pixel_count(masks["strict_hair_core"]),
        "soft_silhouette_area": mask_pixel_count(masks["soft_hair_silhouette"]),
        "forbidden_zone_area": mask_pixel_count(masks["forbidden_nonhair_zone"]),
        "core_body_overlap_ratio": round(core_body_overlap_ratio, 6),
        "soft_body_overlap_ratio": round(soft_body_overlap_ratio, 6),
        "forbidden_candidate_leak_ratio": round(forbidden_candidate_leak_ratio, 6),
        "candidate_core_coverage_ratio": round(candidate_core_coverage_ratio, 6),
        "candidate_soft_inside_ratio": round(candidate_soft_inside_ratio, 6),
        "candidate_target_schema_status": candidate_status,
        "schema_ready_for_ribbon_rebuild": schema_ready,
        "thresholds": SCHEMA_THRESHOLDS,
    }


def save_candidate_schema_overlay(masks: dict[str, Image.Image], output_path: Path) -> None:
    candidate_mask, width, height, _ = foreground_mask_from_render(CANDIDATE_FRONT)
    strict_render = render_mask(masks["strict_hair_core"], width, height)
    soft_render = render_mask(masks["soft_hair_silhouette"], width, height)
    forbidden_render = render_mask(masks["forbidden_nonhair_zone"], width, height)

    image = Image.new("RGBA", (width, height), (42, 42, 42, 255))
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            candidate = candidate_mask[y][x]
            strict = strict_render[y][x]
            soft = soft_render[y][x]
            forbidden = forbidden_render[y][x]
            if candidate and forbidden:
                pixels[x, y] = (255, 0, 0, 255)
            elif candidate and strict:
                pixels[x, y] = (255, 255, 255, 255)
            elif candidate and soft:
                pixels[x, y] = (255, 0, 190, 235)
            elif candidate:
                pixels[x, y] = (255, 128, 0, 230)
            elif strict:
                pixels[x, y] = (60, 255, 128, 210)
            elif soft:
                pixels[x, y] = (0, 220, 255, 170)
            elif forbidden:
                pixels[x, y] = (180, 28, 28, 145)
    image.save(output_path)


def source_mask_preview(mask: Image.Image, color: tuple[int, int, int, int], size: tuple[int, int]) -> Image.Image:
    resized = mask.resize(size, Image.Resampling.NEAREST)
    preview = Image.new("RGBA", size, (35, 35, 35, 255))
    overlay = Image.new("RGBA", size, (color[0], color[1], color[2], 0))
    overlay.putalpha(resized.point(lambda value: color[3] if value else 0))
    return Image.alpha_composite(preview, overlay)


def baseline_schema_overlay(masks: dict[str, Image.Image], size: tuple[int, int]) -> Image.Image:
    baseline = Image.open(BASELINE_FRONT).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
    width, height = baseline.size
    overlays = [
        (masks["forbidden_nonhair_zone"], (255, 24, 24, 88)),
        (masks["soft_hair_silhouette"], (0, 220, 255, 92)),
        (masks["strict_hair_core"], (60, 255, 128, 132)),
    ]
    result = baseline
    for source, color in overlays:
        rendered = bool_matrix_to_image(render_mask(source, width, height), width, height)
        overlay = Image.new("RGBA", (width, height), (color[0], color[1], color[2], 0))
        overlay.putalpha(rendered.point(lambda value: color[3] if value else 0))
        result = Image.alpha_composite(result, overlay)
    return result


def make_contact_sheet(masks: dict[str, Image.Image], candidate_overlay: Path, output_path: Path) -> None:
    tile = (420, 560)
    labels = [
        ("strict_hair_core", source_mask_preview(masks["strict_hair_core"], (60, 255, 128, 220), tile)),
        ("soft_hair_silhouette", source_mask_preview(masks["soft_hair_silhouette"], (0, 220, 255, 210), tile)),
        ("forbidden_nonhair_zone", source_mask_preview(masks["forbidden_nonhair_zone"], (255, 24, 24, 190), tile)),
        ("baseline_schema_overlay", baseline_schema_overlay(masks, tile)),
        ("candidate_vs_schema_overlay", Image.open(candidate_overlay).convert("RGBA").resize(tile, Image.Resampling.LANCZOS)),
        ("candidate_front", Image.open(CANDIDATE_FRONT).convert("RGBA").resize(tile, Image.Resampling.LANCZOS)),
    ]
    sheet = Image.new("RGBA", (tile[0] * 3, tile[1] * 2), (24, 24, 24, 255))
    draw = ImageDraw.Draw(sheet)
    for index, (label, image) in enumerate(labels):
        x = (index % 3) * tile[0]
        y = (index // 3) * tile[1]
        sheet.alpha_composite(image, (x, y))
        draw.rectangle((x, y, x + tile[0] - 1, y + 28), fill=(0, 0, 0, 185))
        draw.text((x + 8, y + 7), label, fill=(255, 255, 255, 255))
    sheet.save(output_path)


def update_json_reports(report: dict[str, Any]) -> None:
    summary = {
        "route": report["route"],
        "status": report["candidate_target_schema_status"],
        "strict_core_area": report["strict_core_area"],
        "soft_silhouette_area": report["soft_silhouette_area"],
        "forbidden_zone_area": report["forbidden_zone_area"],
        "core_body_overlap_ratio": report["core_body_overlap_ratio"],
        "soft_body_overlap_ratio": report["soft_body_overlap_ratio"],
        "forbidden_candidate_leak_ratio": report["forbidden_candidate_leak_ratio"],
        "candidate_core_coverage_ratio": report["candidate_core_coverage_ratio"],
        "candidate_soft_inside_ratio": report["candidate_soft_inside_ratio"],
        "candidate_target_schema_status": report["candidate_target_schema_status"],
        "schema_ready_for_ribbon_rebuild": report["schema_ready_for_ribbon_rebuild"],
        "ready_for_cloth_seam_surface": False,
        "recommended_next": report["recommended_next"],
        "artifacts": report["artifacts"],
    }

    if VALIDATION_REPORT.exists():
        validation_report = load_json(VALIDATION_REPORT)
        validation_report["status"] = report["candidate_target_schema_status"]
        validation = validation_report.setdefault("validation", {})
        validation["target_schema_v1"] = summary
        validation["candidate_target_schema_status"] = report["candidate_target_schema_status"]
        validation["schema_ready_for_ribbon_rebuild"] = report["schema_ready_for_ribbon_rebuild"]
        validation["ready_for_cloth_seam_surface"] = False
        validation["recommended_next"] = report["recommended_next"]
        validation["visual_sanity_status"] = report["candidate_target_schema_status"]
        validation["manual_visual_review"] = "blocked_by_target_schema"
        write_json(VALIDATION_REPORT, validation_report)

    if VALIDATION_CI_REPORT.exists():
        ci_report = load_json(VALIDATION_CI_REPORT)
        ci_report["status"] = report["candidate_target_schema_status"]
        ci_report.setdefault("quality", {})["target_schema_v1"] = summary
        ci_report.setdefault("candidate_contract", {})["target_schema_v1_status"] = report["candidate_target_schema_status"]
        ci_report.setdefault("candidate_contract", {})["visual_sanity_status"] = report["candidate_target_schema_status"]
        ci_report["ready_for_cloth_seam_surface"] = False
        write_json(VALIDATION_CI_REPORT, ci_report)


def build_report(output_dir: Path, *, update_reports: bool = True) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    masks, provenance = build_schema_masks()

    strict_path = output_dir / "strict_hair_core_mask.png"
    soft_path = output_dir / "soft_hair_silhouette_mask.png"
    forbidden_path = output_dir / "forbidden_nonhair_zone_mask.png"
    overlay_path = output_dir / "candidate_vs_schema_overlay.png"
    contact_sheet_path = output_dir / "schema_debug_contact_sheet.png"
    report_path = output_dir / "hair_target_schema_v1_report.json"

    masks["strict_hair_core"].save(strict_path)
    masks["soft_hair_silhouette"].save(soft_path)
    masks["forbidden_nonhair_zone"].save(forbidden_path)
    save_candidate_schema_overlay(masks, overlay_path)
    make_contact_sheet(masks, overlay_path, contact_sheet_path)

    metrics = schema_candidate_metrics(masks)
    recommended_next = (
        "fix_hair_ribbons_to_schema_v1"
        if metrics["schema_ready_for_ribbon_rebuild"]
        else "build_hair_target_schema_v1"
    )
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": "build_hair_target_schema_v1",
        "status": metrics["candidate_target_schema_status"],
        "boundary": "Target-schema generation only. Does not modify semantic_layer_v8, generate GLB, or unblock cloth.",
        "formula_binding": {
            "state": "theta_hair target masks and validation fields, not raw mesh vertices",
            "update": "ProjectToConstraints_hair(RobustFuse(strict_hair_core, soft_hair_silhouette, forbidden_nonhair_zone, front_identity, manual_visual_review))",
        },
        "layers": {
            "strict_hair_core": provenance["strict_hair_core"],
            "soft_hair_silhouette": provenance["soft_hair_silhouette"],
            "forbidden_nonhair_zone": provenance["forbidden_nonhair_zone"],
        },
        **metrics,
        "ready_for_cloth_seam_surface": False,
        "recommended_next": recommended_next,
        "artifacts": {
            "strict_hair_core_mask": file_record(strict_path),
            "soft_hair_silhouette_mask": file_record(soft_path),
            "forbidden_nonhair_zone_mask": file_record(forbidden_path),
            "candidate_vs_schema_overlay": file_record(overlay_path),
            "schema_debug_contact_sheet": file_record(contact_sheet_path),
            "report": file_record(report_path),
        },
    }
    write_json(report_path, report)
    report["artifacts"]["report"] = file_record(report_path)
    write_json(report_path, report)
    if update_reports:
        update_json_reports(report)
    return report


def main() -> int:
    report = build_report(OUT_DIR, update_reports=True)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
