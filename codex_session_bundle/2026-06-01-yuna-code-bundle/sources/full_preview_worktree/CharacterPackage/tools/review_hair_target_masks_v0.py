#!/usr/bin/env python3
"""Review and refine v8 hair target masks for v9 hair candidate validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw

from run_blender_semantic_validation import (
    CHARACTER_PACKAGE,
    HAIR_CONTAMINANT_PARTS,
    HAIR_PART_IDS,
    REPO_ROOT,
    VISUAL_SANITY_THRESHOLDS,
    bool_matrix_to_image,
    count_intersection,
    count_mask_pixels,
    file_record,
    foreground_bbox,
    foreground_mask_from_render,
    source_mask_to_render_bool,
    union_source_masks,
)


OUT_DIR = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "target_review"
BASELINE_FRONT = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "validation_ci" / "yuna_semantic_layer_v9_hair_validation_baseline_front.png"
CANDIDATE_FRONT = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "validation_ci" / "yuna_semantic_layer_v9_hair_validation_candidate_front.png"


@dataclass(frozen=True)
class MaskComponent:
    part_id: str
    area: int
    bbox: tuple[int, int, int, int]
    points: tuple[tuple[int, int], ...]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def mask_components(part_id: str, mask: Image.Image, *, min_area: int = 120) -> list[MaskComponent]:
    pixels = mask.load()
    width, height = mask.size
    seen: set[tuple[int, int]] = set()
    components: list[MaskComponent] = []
    for y in range(height):
        for x in range(width):
            if pixels[x, y] <= 0 or (x, y) in seen:
                continue
            queue = [(x, y)]
            seen.add((x, y))
            points: list[tuple[int, int]] = []
            for current_x, current_y in queue:
                points.append((current_x, current_y))
                for next_x, next_y in (
                    (current_x + 1, current_y),
                    (current_x - 1, current_y),
                    (current_x, current_y + 1),
                    (current_x, current_y - 1),
                ):
                    if not (0 <= next_x < width and 0 <= next_y < height):
                        continue
                    if pixels[next_x, next_y] <= 0 or (next_x, next_y) in seen:
                        continue
                    seen.add((next_x, next_y))
                    queue.append((next_x, next_y))
            if len(points) >= min_area:
                xs = [point[0] for point in points]
                ys = [point[1] for point in points]
                components.append(
                    MaskComponent(
                        part_id=part_id,
                        area=len(points),
                        bbox=(min(xs), min(ys), max(xs) + 1, max(ys) + 1),
                        points=tuple(points),
                    )
                )
    components.sort(key=lambda item: item.area, reverse=True)
    return components


def component_is_hair_like(component: MaskComponent) -> bool:
    x0, y0, x1, y1 = component.bbox
    center_x = (x0 + x1) * 0.5
    part_id = component.part_id
    if part_id == "bangs":
        return y0 < 400 and y1 < 450 and 340 < center_x < 740
    if part_id == "side_hair_left":
        return x1 < 525 and y0 < 780 and y1 < 860
    if part_id == "side_hair_right":
        return x0 > 520 and y0 < 780 and y1 < 900
    if part_id == "back_hair":
        central_lower_body = 340 <= center_x <= 700 and y0 > 740
        side_or_upper_hair = (x0 < 330 and y0 > 450) or x1 > 700 or y0 < 660
        return y0 < 1050 and side_or_upper_hair and not central_lower_body
    return False


def refined_component_target(raw_hair_masks: dict[str, Image.Image]) -> tuple[Image.Image, list[dict[str, Any]]]:
    first = next(iter(raw_hair_masks.values()))
    target = Image.new("L", first.size, 0)
    target_pixels = target.load()
    component_records: list[dict[str, Any]] = []
    for part_id, mask in raw_hair_masks.items():
        for component in mask_components(part_id, mask):
            keep = component_is_hair_like(component)
            component_records.append(
                {
                    "part_id": part_id,
                    "area": component.area,
                    "bbox": list(component.bbox),
                    "kept": keep,
                    "reason": "component_prior_v0" if keep else "outside_component_prior_v0",
                }
            )
            if keep:
                for x, y in component.points:
                    target_pixels[x, y] = 255
    return target, component_records


def count_pixels(mask: Image.Image) -> int:
    return sum(1 for value in mask.getdata() if value > 0)


def overlap_ratio(target: Image.Image, contaminant: Image.Image) -> float:
    overlap = ImageChops.multiply(target, contaminant)
    return count_pixels(overlap) / max(count_pixels(target), 1)


def candidate_alignment(candidate_front: Path, target: Image.Image) -> dict[str, Any]:
    candidate_mask, width, height, candidate_pixels = foreground_mask_from_render(candidate_front)
    target_mask = source_mask_to_render_bool(target, width, height)
    intersection = count_intersection(candidate_mask, target_mask, width, height)
    target_pixels = count_mask_pixels(target_mask, width, height)
    union = 0
    outside = 0
    for y in range(height):
        for x in range(width):
            candidate = candidate_mask[y][x]
            target_pixel = target_mask[y][x]
            if candidate or target_pixel:
                union += 1
            if candidate and not target_pixel:
                outside += 1
    iou = intersection / max(union, 1)
    outside_ratio = outside / max(candidate_pixels, 1)
    return {
        "iou": round(iou, 6),
        "outside_ratio": round(outside_ratio, 6),
        "candidate_visible_pixel_count": candidate_pixels,
        "target_pixel_count": target_pixels,
        "candidate_bbox": list(foreground_bbox(candidate_mask, width, height)) if foreground_bbox(candidate_mask, width, height) else None,
        "target_bbox": list(foreground_bbox(target_mask, width, height)) if foreground_bbox(target_mask, width, height) else None,
        "candidate_is_inside_target": outside_ratio < VISUAL_SANITY_THRESHOLDS["clean_outside_hair_mask_ratio"]
        and iou >= VISUAL_SANITY_THRESHOLDS["clean_hair_mask_iou"],
    }


def save_overlay(base_image_path: Path, target: Image.Image, output_path: Path, color: tuple[int, int, int, int]) -> None:
    base = Image.open(base_image_path).convert("RGBA")
    target_bool = source_mask_to_render_bool(target, base.width, base.height)
    target_image = bool_matrix_to_image(target_bool, base.width, base.height)
    overlay = Image.new("RGBA", (base.width, base.height), (color[0], color[1], color[2], 0))
    overlay.putalpha(target_image.point(lambda value: color[3] if value else 0))
    Image.alpha_composite(base, overlay).save(output_path)


def save_candidate_target_overlay(candidate_front: Path, target: Image.Image, output_path: Path) -> None:
    candidate_mask, width, height, _ = foreground_mask_from_render(candidate_front)
    target_mask = source_mask_to_render_bool(target, width, height)
    overlay = Image.new("RGBA", (width, height), (48, 48, 48, 255))
    pixels = overlay.load()
    for y in range(height):
        for x in range(width):
            candidate = candidate_mask[y][x]
            target_pixel = target_mask[y][x]
            if candidate and target_pixel:
                pixels[x, y] = (255, 255, 255, 255)
            elif target_pixel:
                pixels[x, y] = (0, 220, 255, 220)
            elif candidate:
                pixels[x, y] = (255, 0, 180, 220)
    overlay.save(output_path)


def run() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_hair_masks = {part_id: union_source_masks((part_id,)) for part_id in HAIR_PART_IDS}
    raw_union = union_source_masks(HAIR_PART_IDS)
    contaminants = {name: union_source_masks(parts) for name, parts in HAIR_CONTAMINANT_PARTS.items()}
    strict_clean = raw_union.copy()
    for mask in contaminants.values():
        strict_clean = ImageChops.subtract(strict_clean, mask)
    refined, components = refined_component_target(raw_hair_masks)

    raw_path = OUT_DIR / "hair_target_mask_raw_union.png"
    strict_path = OUT_DIR / "hair_target_mask_strict_clean.png"
    refined_path = OUT_DIR / "hair_target_mask_refined_component_priors.png"
    raw_overlay_path = OUT_DIR / "hair_target_raw_union_overlay.png"
    strict_overlay_path = OUT_DIR / "hair_target_strict_clean_overlay.png"
    refined_overlay_path = OUT_DIR / "hair_target_refined_component_overlay.png"
    candidate_refined_overlay_path = OUT_DIR / "candidate_vs_refined_hair_target_overlay.png"
    report_path = OUT_DIR / "hair_target_review_report.json"

    raw_union.save(raw_path)
    strict_clean.save(strict_path)
    refined.save(refined_path)
    save_overlay(BASELINE_FRONT, raw_union, raw_overlay_path, (255, 32, 32, 118))
    save_overlay(BASELINE_FRONT, strict_clean, strict_overlay_path, (0, 220, 255, 128))
    save_overlay(BASELINE_FRONT, refined, refined_overlay_path, (0, 220, 255, 128))
    save_candidate_target_overlay(CANDIDATE_FRONT, refined, candidate_refined_overlay_path)

    def target_report(target: Image.Image) -> dict[str, Any]:
        return {
            "pixel_count": count_pixels(target),
            "face_overlap_ratio": round(overlap_ratio(target, contaminants["face"]), 6),
            "body_overlap_ratio": round(overlap_ratio(target, contaminants["body"]), 6),
            "weapon_overlap_ratio": round(overlap_ratio(target, contaminants["weapon"]), 6),
            "candidate_alignment": candidate_alignment(CANDIDATE_FRONT, target),
        }

    kept_components = [component for component in components if component["kept"]]
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": "review_and_refine_hair_target_masks_v0",
        "status": "target_review_generated",
        "boundary": "Target review only. Does not modify semantic_layer_v8, does not generate new GLB, and does not unblock cloth.",
        "hair_parts": list(HAIR_PART_IDS),
        "raw_union": target_report(raw_union),
        "strict_clean": target_report(strict_clean),
        "refined_component_priors": target_report(refined),
        "component_selection": {
            "method": "component_prior_v0",
            "component_count": len(components),
            "kept_component_count": len(kept_components),
            "kept_component_area": sum(int(item["area"]) for item in kept_components),
            "components": components,
        },
        "artifacts": {
            "raw_union_mask": file_record(raw_path),
            "strict_clean_mask": file_record(strict_path),
            "refined_component_priors_mask": file_record(refined_path),
            "raw_union_overlay": file_record(raw_overlay_path),
            "strict_clean_overlay": file_record(strict_overlay_path),
            "refined_component_overlay": file_record(refined_overlay_path),
            "candidate_vs_refined_target_overlay": file_record(candidate_refined_overlay_path),
        },
        "decision": {
            "ready_for_cloth_seam_surface": False,
            "recommended_next": "fix_authored_hair_ribbons_v0_to_refined_target",
            "reason": "The refined target is cleaner than the raw union, but the current candidate must be explicitly rebuilt/evaluated against it before any cloth actuator starts.",
        },
    }
    write_json(report_path, report)
    report["artifacts"]["review_report"] = file_record(report_path)
    write_json(report_path, report)
    return report


def main() -> int:
    report = run()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
