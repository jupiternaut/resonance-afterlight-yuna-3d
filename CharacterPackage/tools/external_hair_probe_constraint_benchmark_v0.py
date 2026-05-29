#!/usr/bin/env python3
"""Benchmark YUNA hair constraints against an external pink-hair probe.

The Sketchfab probe is used as a positive-control prior sample. It is not a
YUNA hair replacement and never writes into the semantic-layer hair route.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from build_hair_target_schema_v1 import SCHEMA_THRESHOLDS


CHARACTER_PACKAGE = Path(__file__).resolve().parents[1]
REPO_ROOT = CHARACTER_PACKAGE.parent
SOURCE_DIR = CHARACTER_PACKAGE / "external_hair_dataset" / "sketchfab_gorgeous_japanese_fight"
PROBE_GLB = SOURCE_DIR / "extracted" / "pink_hair_segment_probe.glb"
SOURCE_VIEW_DIR = SOURCE_DIR / "analysis" / "pink_hair_segmentation_probe"
DEFAULT_OUTPUT_DIR = SOURCE_DIR / "benchmarks" / "constraint_benchmark_v0"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "external_hair_probe_constraint_benchmark_v0_report.json"

SOURCE_VIEWS = {
    "front": SOURCE_VIEW_DIR / "candidate_only_front.png",
    "yaw30": SOURCE_VIEW_DIR / "candidate_only_yaw30.png",
    "side": SOURCE_VIEW_DIR / "candidate_only_side.png",
    "wire": SOURCE_VIEW_DIR / "wire_front.png",
}

BENCHMARK_THRESHOLDS = {
    "candidate_visible_area_ratio": SCHEMA_THRESHOLDS["candidate_visible_area_ratio"],
    "candidate_core_coverage_ratio": SCHEMA_THRESHOLDS["candidate_core_coverage_ratio"],
    "candidate_soft_inside_ratio": SCHEMA_THRESHOLDS["candidate_soft_inside_ratio"],
    "forbidden_candidate_leak_ratio": SCHEMA_THRESHOLDS["forbidden_candidate_leak_ratio"],
    "component_count_max": SCHEMA_THRESHOLDS["component_count_max"],
    "yaw30_visible_ratio_to_front": SCHEMA_THRESHOLDS["yaw30_visible_ratio_to_front"],
    "side_view_visible_ratio_to_front": SCHEMA_THRESHOLDS["side_view_visible_ratio_to_front"],
    "flow_continuity": 0.36,
    "scalp_anchor_continuity": SCHEMA_THRESHOLDS["scalp_anchor_continuity"],
}


@dataclass(frozen=True)
class BenchmarkPaths:
    source_dir: Path
    probe_glb: Path
    output_dir: Path
    report_path: Path


def default_paths(repo_root: Path = REPO_ROOT) -> BenchmarkPaths:
    character_package = repo_root / "CharacterPackage"
    source_dir = character_package / "external_hair_dataset" / "sketchfab_gorgeous_japanese_fight"
    output_dir = source_dir / "benchmarks" / "constraint_benchmark_v0"
    return BenchmarkPaths(
        source_dir=source_dir,
        probe_glb=source_dir / "extracted" / "pink_hair_segment_probe.glb",
        output_dir=output_dir,
        report_path=output_dir / "external_hair_probe_constraint_benchmark_v0_report.json",
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


def _binary(mask: Image.Image) -> Image.Image:
    return mask.convert("L").point(lambda value: 255 if value > 0 else 0)


def mask_pixel_count(mask: Image.Image) -> int:
    return _binary(mask).histogram()[255]


def foreground_mask_from_render(image_path: Path) -> Image.Image:
    """Extract foreground using corner-background differencing."""

    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    pixels = image.load()
    samples = [
        pixels[0, 0],
        pixels[width - 1, 0],
        pixels[0, height - 1],
        pixels[width - 1, height - 1],
    ]
    background = tuple(sum(sample[index] for sample in samples) / len(samples) for index in range(3))
    output = Image.new("L", (width, height), 0)
    out = output.load()
    for y in range(height):
        for x in range(width):
            rgb = pixels[x, y]
            visible = sum(abs(rgb[index] - background[index]) for index in range(3)) > 28
            if visible:
                out[x, y] = 255
    return output


def bbox(mask: Image.Image) -> tuple[int, int, int, int] | None:
    return mask.convert("L").point(lambda value: 255 if value > 0 else 0).getbbox()


def dilate(mask: Image.Image, radius: int) -> Image.Image:
    size = radius * 2 + 1
    return _binary(mask).filter(ImageFilter.MaxFilter(max(3, size)))


def erode(mask: Image.Image, radius: int) -> Image.Image:
    size = radius * 2 + 1
    return _binary(mask).filter(ImageFilter.MinFilter(max(3, size)))


def intersect(a: Image.Image, b: Image.Image) -> Image.Image:
    return ImageChops.multiply(_binary(a), _binary(b)).point(lambda value: 255 if value > 0 else 0)


def subtract(a: Image.Image, b: Image.Image) -> Image.Image:
    return ImageChops.subtract(_binary(a), _binary(b)).point(lambda value: 255 if value > 0 else 0)


def invert(mask: Image.Image) -> Image.Image:
    return ImageChops.invert(_binary(mask))


def connected_components(mask: Image.Image, *, min_area: int = 24) -> tuple[int, int, float]:
    binary = _binary(mask)
    width, height = binary.size
    pixels = binary.load()
    seen: set[tuple[int, int]] = set()
    components = 0
    largest_area = 0
    total_area = 0
    for y in range(height):
        for x in range(width):
            if pixels[x, y] <= 0 or (x, y) in seen:
                continue
            queue = [(x, y)]
            seen.add((x, y))
            area = 0
            for current_x, current_y in queue:
                area += 1
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
            total_area += area
            largest_area = max(largest_area, area)
            if area >= min_area:
                components += 1
    largest_ratio = largest_area / max(total_area, 1)
    return components, largest_area, largest_ratio


def flow_continuity(mask: Image.Image) -> float:
    box = bbox(mask)
    if box is None:
        return 0.0
    x0, y0, x1, y1 = box
    binary = _binary(mask)
    width = max(x1 - x0, 1)
    height = max(y1 - y0, 1)
    pixels = binary.load()
    occupied_rows = 0
    occupied_cols = 0
    for y in range(y0, y1):
        if any(pixels[x, y] > 0 for x in range(x0, x1)):
            occupied_rows += 1
    for x in range(x0, x1):
        if any(pixels[x, y] > 0 for y in range(y0, y1)):
            occupied_cols += 1
    components, _, largest_ratio = connected_components(binary, min_area=24)
    row_ratio = occupied_rows / height
    col_ratio = occupied_cols / width
    fragmentation_penalty = min(components / 64, 1.0) * 0.35
    return max(0.0, min(1.0, (0.45 * row_ratio) + (0.30 * col_ratio) + (0.25 * largest_ratio) - fragmentation_penalty))


def scalp_anchor_continuity(mask: Image.Image) -> float:
    box = bbox(mask)
    if box is None:
        return 0.0
    x0, y0, x1, y1 = box
    anchor_height = max(round((y1 - y0) * 0.18), 1)
    binary = _binary(mask)
    pixels = binary.load()
    columns = 0
    for x in range(x0, x1):
        if any(pixels[x, y] > 0 for y in range(y0, min(y1, y0 + anchor_height))):
            columns += 1
    return columns / max(x1 - x0, 1)


def make_schema_from_positive(alpha: Image.Image) -> dict[str, Image.Image]:
    soft = dilate(alpha, 8)
    strict_seed = erode(alpha, 2)
    strict = strict_seed if mask_pixel_count(strict_seed) > 200 else _binary(alpha)
    forbidden = invert(dilate(soft, 10))
    return {
        "strict_core": _binary(strict),
        "soft_silhouette": _binary(soft),
        "forbidden_zone": _binary(forbidden),
    }


def resize_center(mask: Image.Image, scale: float) -> Image.Image:
    binary = _binary(mask)
    width, height = binary.size
    box = bbox(binary)
    if box is None:
        return Image.new("L", binary.size, 0)
    cropped = binary.crop(box)
    target_size = (
        max(1, round(cropped.width * scale)),
        max(1, round(cropped.height * scale)),
    )
    resized = cropped.resize(target_size, Image.Resampling.NEAREST)
    result = Image.new("L", binary.size, 0)
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    result.paste(resized, (cx - target_size[0] // 2, cy - target_size[1] // 2))
    return _binary(result)


def shift_mask(mask: Image.Image, dx: int, dy: int) -> Image.Image:
    result = Image.new("L", mask.size, 0)
    result.paste(_binary(mask), (dx, dy))
    return _binary(result)


def fragment_mask(mask: Image.Image) -> Image.Image:
    binary = _binary(mask)
    width, height = binary.size
    result = Image.new("L", binary.size, 0)
    source = binary.load()
    out = result.load()
    tile = 22
    for y in range(height):
        for x in range(width):
            if source[x, y] <= 0:
                continue
            if ((x // tile) + (y // tile)) % 3 == 0:
                out[x, y] = 255
    return _binary(result)


def barcode_mask(mask: Image.Image) -> Image.Image:
    box = bbox(mask)
    result = Image.new("L", mask.size, 0)
    if box is None:
        return result
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(result)
    stripe_width = max(2, (x1 - x0) // 90)
    gap = stripe_width
    x = x0
    while x < x1:
        draw.rectangle((x, y0, min(x + stripe_width, x1), y1), fill=255)
        x += stripe_width + gap
    return intersect(result, dilate(mask, 2))


def nonhair_component_mask(mask: Image.Image) -> Image.Image:
    binary = _binary(mask)
    result = binary.copy()
    width, height = binary.size
    draw = ImageDraw.Draw(result)
    rect_width = max(40, width // 9)
    rect_height = max(40, height // 10)
    draw.rectangle(
        (
            width - rect_width - 32,
            height - rect_height - 32,
            width - 32,
            height - 32,
        ),
        fill=255,
    )
    return _binary(result)


def create_negative_controls(front: Image.Image, yaw30: Image.Image, side: Image.Image) -> dict[str, dict[str, Image.Image]]:
    width, height = front.size
    shift_x = round(width * 0.24)
    shift_y = round(height * 0.12)
    return {
        "shrunken_probe": {
            "front": resize_center(front, 0.20),
            "yaw30": resize_center(yaw30, 0.20),
            "side": resize_center(side, 0.20),
        },
        "shifted_probe": {
            "front": shift_mask(front, shift_x, shift_y),
            "yaw30": shift_mask(yaw30, shift_x, shift_y),
            "side": shift_mask(side, shift_x, shift_y),
        },
        "fragmented_probe": {
            "front": fragment_mask(front),
            "yaw30": fragment_mask(yaw30),
            "side": fragment_mask(side),
        },
        "barcode_strip_probe": {
            "front": barcode_mask(front),
            "yaw30": barcode_mask(yaw30),
            "side": barcode_mask(side),
        },
        "nonhair_component_probe": {
            "front": nonhair_component_mask(front),
            "yaw30": nonhair_component_mask(yaw30),
            "side": nonhair_component_mask(side),
        },
    }


def save_mask(mask: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _binary(mask).save(path)


def save_mask_preview(mask: Image.Image, path: Path, color: tuple[int, int, int] = (225, 96, 176)) -> None:
    binary = _binary(mask)
    image = Image.new("RGB", binary.size, (36, 36, 36))
    overlay = Image.new("RGBA", binary.size, (*color, 0))
    overlay.putalpha(binary)
    Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB").save(path)


def evaluate_constraints(
    *,
    name: str,
    front: Image.Image,
    yaw30: Image.Image,
    side: Image.Image,
    schema: dict[str, Image.Image],
) -> dict[str, Any]:
    front = _binary(front)
    yaw30 = _binary(yaw30)
    side = _binary(side)
    candidate_pixels = mask_pixel_count(front)
    width, height = front.size
    total_pixels = max(width * height, 1)
    strict_pixels = max(mask_pixel_count(schema["strict_core"]), 1)
    soft_pixels = max(mask_pixel_count(schema["soft_silhouette"]), 1)
    candidate_core = mask_pixel_count(intersect(front, schema["strict_core"]))
    candidate_soft = mask_pixel_count(intersect(front, schema["soft_silhouette"]))
    candidate_forbidden = mask_pixel_count(intersect(front, schema["forbidden_zone"]))
    components, largest_component_area, largest_component_ratio = connected_components(front)
    yaw30_pixels = mask_pixel_count(yaw30)
    side_pixels = mask_pixel_count(side)
    metrics = {
        "candidate_visible_pixel_count": candidate_pixels,
        "candidate_visible_area_ratio": round(candidate_pixels / total_pixels, 6),
        "candidate_core_coverage_ratio": round(candidate_core / strict_pixels, 6),
        "candidate_soft_inside_ratio": round(candidate_soft / max(candidate_pixels, 1), 6),
        "soft_silhouette_coverage_ratio": round(candidate_soft / soft_pixels, 6),
        "forbidden_candidate_leak_ratio": round(candidate_forbidden / max(candidate_pixels, 1), 6),
        "component_count": components,
        "largest_component_area": largest_component_area,
        "largest_component_ratio": round(largest_component_ratio, 6),
        "yaw30_visible_ratio_to_front": round(yaw30_pixels / max(candidate_pixels, 1), 6),
        "side_view_visible_ratio_to_front": round(side_pixels / max(candidate_pixels, 1), 6),
        "flow_continuity": round(flow_continuity(front), 6),
        "scalp_anchor_continuity": round(scalp_anchor_continuity(front), 6),
    }
    gates = {
        "visible_mass": metrics["candidate_visible_area_ratio"] >= BENCHMARK_THRESHOLDS["candidate_visible_area_ratio"],
        "core_coverage": metrics["candidate_core_coverage_ratio"] >= BENCHMARK_THRESHOLDS["candidate_core_coverage_ratio"],
        "soft_inside": metrics["candidate_soft_inside_ratio"] >= BENCHMARK_THRESHOLDS["candidate_soft_inside_ratio"],
        "forbidden_leak": metrics["forbidden_candidate_leak_ratio"] <= BENCHMARK_THRESHOLDS["forbidden_candidate_leak_ratio"],
        "component_count": metrics["component_count"] <= BENCHMARK_THRESHOLDS["component_count_max"],
        "yaw30_readability": metrics["yaw30_visible_ratio_to_front"] >= BENCHMARK_THRESHOLDS["yaw30_visible_ratio_to_front"],
        "side_readability": metrics["side_view_visible_ratio_to_front"] >= BENCHMARK_THRESHOLDS["side_view_visible_ratio_to_front"],
        "flow_continuity": metrics["flow_continuity"] >= BENCHMARK_THRESHOLDS["flow_continuity"],
        "scalp_anchor_continuity": metrics["scalp_anchor_continuity"] >= BENCHMARK_THRESHOLDS["scalp_anchor_continuity"],
    }
    failed_gates = [gate for gate, passed in gates.items() if not passed]
    return {
        "name": name,
        "status": "passed" if not failed_gates else "failed",
        "expected_role": "positive_control" if name == "positive_probe" else "negative_control",
        "metrics": metrics,
        "gates": gates,
        "failed_gates": failed_gates,
    }


def copy_source_views(output_dir: Path) -> dict[str, dict[str, Any]]:
    views_dir = output_dir / "views"
    views_dir.mkdir(parents=True, exist_ok=True)
    records: dict[str, dict[str, Any]] = {}
    for name, source in SOURCE_VIEWS.items():
        target = views_dir / f"positive_{name}.png"
        if source.exists():
            shutil.copy2(source, target)
            records[name] = {
                "status": "consumed_existing_render",
                "source": display_path(source),
                **file_record(target),
            }
        else:
            records[name] = {
                "status": "skipped_with_reason",
                "skipped_with_reason": f"source view missing: {display_path(source)}",
                "source": display_path(source),
                **file_record(target),
            }
    for optional in ("depth", "normal"):
        records[optional] = {
            "status": "skipped_with_reason",
            "skipped_with_reason": f"{optional} view is not available for the committed extracted probe",
        }
    return records


def make_contact_sheet(output_dir: Path, positive: dict[str, Image.Image], controls: dict[str, dict[str, Image.Image]]) -> Path:
    tile = (260, 340)
    rows = [("positive_probe", positive["front"])]
    rows.extend((name, data["front"]) for name, data in controls.items())
    sheet = Image.new("RGB", (tile[0] * 3, tile[1] * len(rows)), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    schema_labels = ["front/alpha", "yaw30/alpha", "side/alpha"]
    for row_index, (name, front_mask) in enumerate(rows):
        data = positive if name == "positive_probe" else controls[name]
        for column_index, key in enumerate(("front", "yaw30", "side")):
            preview = Image.new("RGB", data[key].size, (34, 34, 34))
            overlay = Image.new("RGBA", data[key].size, (225, 96, 176, 0))
            overlay.putalpha(_binary(data[key]))
            rendered = Image.alpha_composite(preview.convert("RGBA"), overlay).convert("RGB")
            rendered = rendered.resize(tile, Image.Resampling.LANCZOS)
            x = column_index * tile[0]
            y = row_index * tile[1]
            sheet.paste(rendered, (x, y))
            draw.rectangle((x, y, x + tile[0] - 1, y + 28), fill=(0, 0, 0))
            label = name if column_index == 0 else schema_labels[column_index]
            draw.text((x + 8, y + 8), label, fill=(255, 255, 255))
    output = output_dir / "external_hair_probe_constraint_benchmark_contact_sheet.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    return output


def build_blocked_report(paths: BenchmarkPaths, reason: str) -> dict[str, Any]:
    report = {
        "route": "external_hair_probe_constraint_benchmark_v0",
        "status": "blocked",
        "blocked_with_reason": reason,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_probe": file_record(paths.probe_glb),
        "positive_probe_status": "blocked",
        "negative_control_results": {},
        "constraint_false_positive_risk": "unknown",
        "constraint_false_negative_risk": "unknown",
        "constraints_too_strict": None,
        "constraints_too_weak": None,
        "recommended_constraint_updates": ["Provide the extracted pink hair probe and committed source renders, then rerun benchmark."],
        "usable_as_yuna_prior": False,
        "guards": {
            "external_asset_usage": "positive_control_prior_only",
            "generated_yuna_hair": False,
            "replace_in_beauty_glb": False,
            "ready_for_cloth_seam_surface": False,
            "semantic_layer_v8_modified": False,
        },
    }
    write_json(paths.report_path, report)
    return report


def build_report(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    report_path: Path | None = None,
) -> dict[str, Any]:
    paths = default_paths(REPO_ROOT)
    if output_dir != DEFAULT_OUTPUT_DIR:
        paths = BenchmarkPaths(paths.source_dir, paths.probe_glb, output_dir, report_path or output_dir / DEFAULT_REPORT.name)
    else:
        paths = BenchmarkPaths(paths.source_dir, paths.probe_glb, output_dir, report_path or DEFAULT_REPORT)
    output_dir = paths.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if not paths.probe_glb.exists():
        return build_blocked_report(paths, f"positive probe missing: {display_path(paths.probe_glb)}")
    missing_views = [name for name, source in SOURCE_VIEWS.items() if not source.exists()]
    if missing_views:
        return build_blocked_report(paths, f"required source views missing: {missing_views}")

    view_records = copy_source_views(output_dir)
    views_dir = output_dir / "views"
    front = foreground_mask_from_render(views_dir / "positive_front.png")
    yaw30 = foreground_mask_from_render(views_dir / "positive_yaw30.png")
    side = foreground_mask_from_render(views_dir / "positive_side.png")
    wire = foreground_mask_from_render(views_dir / "positive_wire.png")
    positive_masks = {"front": front, "yaw30": yaw30, "side": side, "wire": wire}
    schema = make_schema_from_positive(front)

    mask_dir = output_dir / "masks"
    for name, mask in {
        "positive_alpha": front,
        "positive_yaw30_alpha": yaw30,
        "positive_side_alpha": side,
        "positive_wire_alpha": wire,
        "strict_core": schema["strict_core"],
        "soft_silhouette": schema["soft_silhouette"],
        "forbidden_zone": schema["forbidden_zone"],
    }.items():
        save_mask(mask, mask_dir / f"{name}.png")

    controls = create_negative_controls(front, yaw30, side)
    controls_dir = output_dir / "negative_controls"
    negative_results: dict[str, Any] = {}
    for name, data in controls.items():
        control_dir = controls_dir / name
        for view_name, mask in data.items():
            save_mask(mask, control_dir / f"{view_name}_alpha.png")
            save_mask_preview(mask, control_dir / f"{view_name}_preview.png")
        result = evaluate_constraints(name=name, front=data["front"], yaw30=data["yaw30"], side=data["side"], schema=schema)
        result["expected_to_fail"] = True
        result["failed_as_expected"] = result["status"] == "failed"
        result["artifacts"] = {
            "front_alpha": file_record(control_dir / "front_alpha.png"),
            "yaw30_alpha": file_record(control_dir / "yaw30_alpha.png"),
            "side_alpha": file_record(control_dir / "side_alpha.png"),
        }
        negative_results[name] = result

    positive_result = evaluate_constraints(
        name="positive_probe",
        front=front,
        yaw30=yaw30,
        side=side,
        schema=schema,
    )
    positive_passed = positive_result["status"] == "passed"
    negative_failures = [result["status"] == "failed" for result in negative_results.values()]
    all_negatives_failed = all(negative_failures)
    any_negative_passed = any(not failed for failed in negative_failures)
    constraints_too_strict = not positive_passed and all_negatives_failed
    constraints_too_weak = positive_passed and any_negative_passed
    if positive_passed and all_negatives_failed:
        benchmark_status = "constraint_benchmark_passed_for_external_probe"
        false_positive_risk = "low"
        false_negative_risk = "low"
    elif positive_passed and any_negative_passed:
        benchmark_status = "constraint_benchmark_failed_negatives_too_weak"
        false_positive_risk = "high"
        false_negative_risk = "low"
    elif not positive_passed and all_negatives_failed:
        benchmark_status = "constraint_benchmark_failed_positive_too_strict_or_mapping_issue"
        false_positive_risk = "low"
        false_negative_risk = "high"
    else:
        benchmark_status = "constraint_benchmark_inconclusive"
        false_positive_risk = "medium"
        false_negative_risk = "high"

    recommendations: list[str] = []
    if constraints_too_strict:
        recommendations.append("Positive control failed: inspect target construction, yaw/side thresholds, and flow/scalp continuity before tightening YUNA constraints.")
    if constraints_too_weak:
        recommendations.append("At least one negative control passed: add stricter negative-control gates before accepting future YUNA hair candidates.")
    if positive_passed and all_negatives_failed:
        recommendations.append("Constraint set is useful as a smoke gate for external hair priors, but it is not a visual acceptance gate for YUNA.")
    recommendations.append("Keep external probe as prior_only; do not copy this geometry into YUNA or unblock cloth from this benchmark alone.")

    contact_sheet = make_contact_sheet(output_dir, positive_masks, controls)
    report = {
        "route": "external_hair_probe_constraint_benchmark_v0",
        "status": benchmark_status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "formula_stage": "theta_p_next = ProjectToConstraints_p((1-alpha)*theta_p + alpha*RobustFuse(observations, prior_p))",
        "purpose": "Use the approved extracted pink hair probe as a positive-control prior sample to test hair constraint reasonableness.",
        "source_probe": file_record(paths.probe_glb),
        "source_model": {
            "name": "Sketchfab Gorgeous japanese Fight",
            "usage": "positive_control_external_hair_prior_only",
            "not_yuna_replacement": True,
        },
        "views": view_records,
        "constraint_model": {
            "type": "external_probe_normalized_target_schema",
            "reason": "External probe does not share YUNA coordinate space; target masks are derived from the probe foreground itself.",
            "thresholds": BENCHMARK_THRESHOLDS,
            "depth_view": view_records["depth"],
            "normal_view": view_records["normal"],
        },
        "positive_probe_status": positive_result["status"],
        "positive_probe_result": positive_result,
        "negative_control_results": negative_results,
        "negative_controls_generated": bool(negative_results),
        "negative_controls_skipped_with_reason": None,
        "constraint_false_positive_risk": false_positive_risk,
        "constraint_false_negative_risk": false_negative_risk,
        "constraints_too_strict": constraints_too_strict,
        "constraints_too_weak": constraints_too_weak,
        "recommended_constraint_updates": recommendations,
        "usable_as_yuna_prior": positive_passed,
        "usable_as_yuna_prior_reason": (
            "External probe passed normalized smoke constraints; usable only as a visual/flow prior, not as replacement geometry."
            if positive_passed
            else "External probe did not pass normalized smoke constraints; use only for manual study until constraints/mapping are reviewed."
        ),
        "guards": {
            "external_asset_usage": "positive_control_prior_only",
            "generated_yuna_hair": False,
            "replace_in_beauty_glb": False,
            "ready_for_cloth_seam_surface": False,
            "semantic_layer_v8_modified": False,
            "external_probe_is_final_yuna_hair": False,
        },
        "artifacts": {
            "report": file_record(paths.report_path),
            "contact_sheet": file_record(contact_sheet),
            "positive_alpha": file_record(mask_dir / "positive_alpha.png"),
            "strict_core": file_record(mask_dir / "strict_core.png"),
            "soft_silhouette": file_record(mask_dir / "soft_silhouette.png"),
            "forbidden_zone": file_record(mask_dir / "forbidden_zone.png"),
            "negative_controls_dir": display_path(controls_dir),
        },
    }
    write_json(paths.report_path, report)
    report["artifacts"]["report"] = file_record(paths.report_path)
    write_json(paths.report_path, report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark hair constraints on an external pink-hair probe.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(args.output_dir, report_path=args.report)
    print(json.dumps({
        "status": report["status"],
        "positive_probe_status": report["positive_probe_status"],
        "constraints_too_strict": report["constraints_too_strict"],
        "constraints_too_weak": report["constraints_too_weak"],
        "report": report["artifacts"]["report"]["path"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
