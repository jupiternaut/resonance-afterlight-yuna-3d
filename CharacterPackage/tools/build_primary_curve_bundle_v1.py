#!/usr/bin/env python3
"""Build YUNA primary hair curve bundle v1 from external priors.

This planner writes curve parameters and visual planning overlays only. It does
not generate hair geometry, GLB, or replacement assets.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


CHARACTER_PACKAGE = Path(__file__).resolve().parents[1]
REPO_ROOT = CHARACTER_PACKAGE.parent
HAIR_DIR = CHARACTER_PACKAGE / "semantic_layer_v9_hair"
TARGET_SCHEMA_DIR = HAIR_DIR / "target_schema_v1"
PRIORS_DIR = CHARACTER_PACKAGE / "external_hair_dataset" / "priors"
SKETCHFAB_BENCHMARK_DIR = (
    CHARACTER_PACKAGE
    / "external_hair_dataset"
    / "sketchfab_gorgeous_japanese_fight"
    / "benchmarks"
    / "constraint_benchmark_v0"
)

DESIGN_SCHEMA = HAIR_DIR / "hair_design_schema_v1.json"
TARGET_SCHEMA_REPORT = TARGET_SCHEMA_DIR / "hair_target_schema_v1_report.json"
EXTERNAL_PRIOR_LIBRARY = PRIORS_DIR / "external_hair_prior_library_v0.json"
BENCHMARK_REPORT = SKETCHFAB_BENCHMARK_DIR / "external_hair_probe_constraint_benchmark_v0_report.json"
BASELINE_FRONT = HAIR_DIR / "validation_ci" / "yuna_semantic_layer_v9_hair_validation_baseline_front.png"

EXTERNAL_PRIOR_SCHEMA_V1 = PRIORS_DIR / "external_hair_prior_schema_v1.json"
PRIMARY_CURVE_BUNDLE = HAIR_DIR / "primary_curve_bundle_v1.json"
PRIMARY_CURVE_REPORT = HAIR_DIR / "primary_curve_bundle_v1_report.json"
FRONT_OVERLAY = HAIR_DIR / "primary_curve_bundle_v1_front_overlay.png"
YAW30_PLAN = HAIR_DIR / "primary_curve_bundle_v1_yaw30_plan.png"
CONTACT_SHEET = HAIR_DIR / "primary_curve_bundle_v1_contact_sheet.png"

GROUP_MASKS = {
    "bangs_primary": TARGET_SCHEMA_DIR / "group_masks" / "bangs_schema_v1_mask.png",
    "side_hair_left_primary": TARGET_SCHEMA_DIR / "group_masks" / "side_hair_left_schema_v1_mask.png",
    "side_hair_right_primary": TARGET_SCHEMA_DIR / "group_masks" / "side_hair_right_schema_v1_mask.png",
    "back_hair_mass": TARGET_SCHEMA_DIR / "group_masks" / "back_hair_schema_v1_mask.png",
}
GROUP_SOURCE_PARTS = {
    "bangs_primary": "bangs",
    "side_hair_left_primary": "side_hair_left",
    "side_hair_right_primary": "side_hair_right",
    "back_hair_mass": "back_hair",
}
ANCHOR_BY_GROUP = {
    "bangs_primary": "scalp_front_center",
    "side_hair_left_primary": "scalp_left_temple",
    "side_hair_right_primary": "scalp_right_temple",
    "back_hair_mass": "scalp_crown",
}
DEPTH_BY_GROUP = {
    "bangs_primary": "front_bangs",
    "side_hair_left_primary": "side_ribbons",
    "side_hair_right_primary": "side_ribbons",
    "back_hair_mass": "back_mass",
}
CURVE_FRACTIONS = {
    "bangs_primary": [(0.50, 0.05), (0.48, 0.28), (0.44, 0.58), (0.40, 0.93)],
    "side_hair_left_primary": [(0.72, 0.04), (0.54, 0.34), (0.34, 0.68), (0.18, 0.96)],
    "side_hair_right_primary": [(0.26, 0.04), (0.44, 0.35), (0.64, 0.70), (0.80, 0.96)],
    "back_hair_mass": [(0.50, 0.05), (0.54, 0.34), (0.51, 0.66), (0.47, 0.95)],
}
COLORS = {
    "bangs_primary": (255, 245, 170),
    "side_hair_left_primary": (95, 230, 255),
    "side_hair_right_primary": (150, 245, 255),
    "back_hair_mass": (255, 150, 225),
}


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": display_path(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
    }


def binary_mask(path: Path) -> Image.Image:
    return Image.open(path).convert("L").point(lambda value: 255 if value > 0 else 0)


def mask_area(mask: Image.Image) -> int:
    return mask.convert("L").point(lambda value: 255 if value > 0 else 0).histogram()[255]


def normalized_point(point: tuple[float, float]) -> list[float]:
    return [round(point[0], 6), round(point[1], 6)]


def curve_points_from_bbox(group_id: str, box: tuple[int, int, int, int], size: tuple[int, int]) -> list[dict[str, Any]]:
    x0, y0, x1, y1 = box
    width = max(x1 - x0, 1)
    height = max(y1 - y0, 1)
    image_width, image_height = size
    points: list[dict[str, Any]] = []
    for index, (fx, fy) in enumerate(CURVE_FRACTIONS[group_id]):
        px = x0 + (width * fx)
        py = y0 + (height * fy)
        points.append(
            {
                "t": round(index / max(len(CURVE_FRACTIONS[group_id]) - 1, 1), 3),
                "xy": normalized_point((px / image_width, py / image_height)),
                "pixel_xy": [round(px), round(py)],
            }
        )
    return points


def width_profile_for_group(group_id: str) -> list[dict[str, float]]:
    if group_id == "back_hair_mass":
        samples = [(0.0, 0.34), (0.28, 0.88), (0.62, 0.68), (0.86, 0.34), (1.0, 0.12)]
    elif group_id.startswith("side_hair"):
        samples = [(0.0, 0.24), (0.32, 0.58), (0.66, 0.44), (1.0, 0.10)]
    else:
        samples = [(0.0, 0.28), (0.36, 0.44), (0.72, 0.30), (1.0, 0.08)]
    return [{"t": t, "width_ratio": width} for t, width in samples]


def taper_profile_for_group(group_id: str) -> dict[str, Any]:
    return {
        "family": "root_full_mid_mass_tip_taper",
        "samples": [
            {"t": 0.0, "taper": 0.88},
            {"t": 0.35, "taper": 1.0},
            {"t": 0.70, "taper": 0.55},
            {"t": 1.0, "taper": 0.12},
        ],
        "source": "external prior width/taper ratios plus YUNA target-schema group bbox",
        "copy_source_curve": False,
    }


def build_external_prior_schema(
    design: dict[str, Any],
    prior_library: dict[str, Any],
    benchmark: dict[str, Any],
) -> dict[str, Any]:
    combined = prior_library.get("combined_prior_summary", {})
    negative_patterns = []
    for name, result in benchmark.get("negative_control_results", {}).items():
        negative_patterns.append(
            {
                "control": name,
                "failed_gates": result.get("failed_gates", []),
                "lesson": f"Reject {name.replace('_', ' ')} when building YUNA primary curves.",
            }
        )
    positive = benchmark.get("positive_probe_result", {}).get("metrics", {})
    return {
        "schema": "external_hair_prior_schema_v1",
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "prior_schema_generated",
        "external_asset_usage": "prior_only",
        "do_not_copy_shape_directly": True,
        "direct_copy_allowed": False,
        "replace_in_beauty_glb": False,
        "generated_yuna_hair": False,
        "ready_for_cloth_seam_surface": False,
        "source_inputs": {
            "external_prior_library_v0": display_path(EXTERNAL_PRIOR_LIBRARY),
            "constraint_benchmark_v0": display_path(BENCHMARK_REPORT),
            "hair_design_schema_v1": display_path(DESIGN_SCHEMA),
        },
        "scalp_anchor_patterns": [
            {
                "anchor_id": item["id"],
                "semantic_location": item.get("semantic_location", ""),
                "confidence": item.get("confidence", "estimated"),
                "use_as": "YUNA anchor name and semantic region only",
            }
            for item in design.get("scalp_anchor_points", [])
        ],
        "flow_arc_patterns": [
            *combined.get("recommended_yuna_curve_bundle_hints", []),
            {
                "bundle_id": "pink_probe_compact_bob_mass",
                "informed_by": ["sketchfab_gorgeous_japanese_fight_pink_hair_probe"],
                "intended_yuna_group": "bangs_side_back_balance",
                "parameter_hint": "Use as mass/readability positive-control only; do not copy bob silhouette.",
            },
        ],
        "width_profile_patterns": {
            "source": "external prior ratios plus pink probe visible-mass benchmark",
            "positive_probe_visible_area_ratio": positive.get("candidate_visible_area_ratio"),
            "positive_probe_soft_silhouette_coverage_ratio": positive.get("soft_silhouette_coverage_ratio"),
            "recommended_use": "relative width envelopes for YUNA curves, not copied outlines",
        },
        "taper_profile_patterns": {
            "family": "full root and mid mass with narrow tapered tips",
            "negative_controls": ["shrunken_probe", "barcode_strip_probe"],
            "recommended_use": "preserve enough visible mass while avoiding barcode/slat fragmentation",
        },
        "visible_mass_patterns": {
            "positive_probe_component_count": positive.get("component_count"),
            "positive_probe_flow_continuity": positive.get("flow_continuity"),
            "positive_probe_scalp_anchor_continuity": positive.get("scalp_anchor_continuity"),
            "benchmark_status": benchmark.get("status"),
        },
        "depth_group_patterns": {
            "front_bangs": "front identity group; keep around face without broad opaque occlusion",
            "side_ribbons": "mid-depth side-fall curves; preserve left/right silhouette",
            "back_mass": "rear mass; use crown anchor and visible volume, not a flat wall",
            "flyaways": "thin distributed accents after primary groups pass",
            "side_back_are_soft_constraints": True,
        },
        "negative_failure_patterns": negative_patterns,
        "unsafe_or_style_mismatched_patterns": combined.get("unsafe_or_style_mismatched_patterns", []),
    }


def build_primary_curve(group_id: str, design: dict[str, Any]) -> dict[str, Any]:
    mask_path = GROUP_MASKS[group_id]
    mask = binary_mask(mask_path)
    box = mask.getbbox()
    if box is None:
        raise ValueError(f"Missing non-empty group mask for {group_id}: {mask_path}")
    points = curve_points_from_bbox(group_id, box, mask.size)
    required = design["required_primary_groups"][group_id]
    return {
        "id": group_id,
        "source_part": GROUP_SOURCE_PARTS[group_id],
        "role": required["role"],
        "scalp_anchor": ANCHOR_BY_GROUP[group_id],
        "curve_points": points,
        "coordinate_space": "target_schema_source_mask_normalized_xy",
        "width_profile": width_profile_for_group(group_id),
        "taper_profile": taper_profile_for_group(group_id),
        "depth_group": DEPTH_BY_GROUP[group_id],
        "allowed_soft_silhouette_region": {
            "source": "hair_target_schema_v1.soft_hair_silhouette",
            "group_mask": display_path(mask_path),
            "policy": "curve envelope must remain in soft silhouette unless explicitly marked as a flyaway",
        },
        "forbidden_zone_policy": {
            "source": "hair_target_schema_v1.forbidden_nonhair_zone",
            "policy": "do not place primary curves through face/body/weapon forbidden zones",
            "leak_threshold": 0.10,
        },
        "source_prior_reference": {
            "external_prior_schema_v1": display_path(EXTERNAL_PRIOR_SCHEMA_V1),
            "constraint_benchmark_v0": display_path(BENCHMARK_REPORT),
            "hair_design_schema_v1": display_path(DESIGN_SCHEMA),
            "direct_copy_allowed": False,
        },
        "confidence": "medium",
        "manual_review_required": True,
        "source_mask_bbox": list(box),
        "source_mask_area": mask_area(mask),
    }


def make_secondary_strands(primary_curves: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    strands = []
    for index, group_id in enumerate(("back_hair_mass", "side_hair_left_primary", "side_hair_right_primary", "bangs_primary")):
        curve = primary_curves[group_id]
        points = curve["curve_points"]
        strands.append(
            {
                "id": f"secondary_{index + 1}_{group_id}",
                "parent_primary": group_id,
                "scalp_anchor": curve["scalp_anchor"],
                "curve_points": points,
                "width_profile": [{"t": item["t"], "width_ratio": round(item["width_ratio"] * 0.45, 4)} for item in curve["width_profile"]],
                "taper_profile": curve["taper_profile"],
                "depth_group": "flyaways" if group_id == "bangs_primary" else curve["depth_group"],
                "allowed_soft_silhouette_region": curve["allowed_soft_silhouette_region"],
                "forbidden_zone_policy": curve["forbidden_zone_policy"],
                "source_prior_reference": curve["source_prior_reference"],
                "confidence": "medium_low",
                "manual_review_required": True,
            }
        )
    return strands


def make_flyaway_strands(primary_curves: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    flyaways = []
    for index, group_id in enumerate(("bangs_primary", "side_hair_left_primary", "side_hair_right_primary", "back_hair_mass")):
        curve = primary_curves[group_id]
        points = curve["curve_points"][:]
        # A tiny deterministic offset marks this as a planning hint, not copied
        # or generated geometry.
        offset = (-0.006 if "left" in group_id else 0.006, -0.004)
        shifted = []
        for point in points:
            x, y = point["xy"]
            shifted.append({"t": point["t"], "xy": normalized_point((max(0.0, min(1.0, x + offset[0])), max(0.0, min(1.0, y + offset[1]))))})
        flyaways.append(
            {
                "id": f"flyaway_{index + 1}_{group_id}",
                "parent_primary": group_id,
                "scalp_anchor": curve["scalp_anchor"],
                "curve_points": shifted,
                "width_profile": [{"t": 0.0, "width_ratio": 0.10}, {"t": 1.0, "width_ratio": 0.02}],
                "taper_profile": {"family": "thin_wisp_taper", "copy_source_curve": False},
                "depth_group": "flyaways",
                "allowed_soft_silhouette_region": {
                    "source": "hair_design_schema_v1.allowed_silhouette_expansion",
                    "maximum_px": 18,
                },
                "forbidden_zone_policy": curve["forbidden_zone_policy"],
                "source_prior_reference": curve["source_prior_reference"],
                "confidence": "low",
                "manual_review_required": True,
            }
        )
    return flyaways


def build_curve_bundle(design: dict[str, Any], external_prior_schema: dict[str, Any]) -> dict[str, Any]:
    primary_curves = {group_id: build_primary_curve(group_id, design) for group_id in GROUP_MASKS}
    secondary = make_secondary_strands(primary_curves)
    flyaways = make_flyaway_strands(primary_curves)
    return {
        "schema": "primary_curve_bundle_v1",
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "primary_curve_bundle_generated_planning_only",
        "boundary": "Curve planner only. Does not generate YUNA hair geometry, GLB, or beauty replacement.",
        "formula_stage": "theta_hair_curves = ProjectToConstraints_hair(RobustFuse(external_prior, hair_design_schema_v1, target_schema_v1))",
        "direct_copy_allowed": False,
        "do_not_copy_shape_directly": True,
        "replace_in_beauty_glb": False,
        "ready_for_cloth_seam_surface": False,
        "manual_review_required": True,
        "source_inputs": {
            "external_hair_prior_schema_v1": display_path(EXTERNAL_PRIOR_SCHEMA_V1),
            "hair_design_schema_v1": display_path(DESIGN_SCHEMA),
            "target_schema_v1_report": display_path(TARGET_SCHEMA_REPORT),
            "constraint_benchmark_v0": display_path(BENCHMARK_REPORT),
        },
        "primary_curves": primary_curves,
        "bangs_primary": primary_curves["bangs_primary"],
        "side_hair_left_primary": primary_curves["side_hair_left_primary"],
        "side_hair_right_primary": primary_curves["side_hair_right_primary"],
        "back_hair_mass": primary_curves["back_hair_mass"],
        "secondary_strands": secondary,
        "flyaway_strands": flyaways,
        "external_prior_summary": {
            "status": external_prior_schema["status"],
            "do_not_copy_shape_directly": external_prior_schema["do_not_copy_shape_directly"],
            "usable_patterns": [
                "scalp anchor semantics",
                "visible mass and flow continuity thresholds",
                "width/taper ratio families",
                "negative-control failure lessons",
            ],
        },
    }


def curve_pixels(curve: dict[str, Any], size: tuple[int, int]) -> list[tuple[int, int]]:
    width, height = size
    return [(round(point["xy"][0] * width), round(point["xy"][1] * height)) for point in curve["curve_points"]]


def draw_curves(base: Image.Image, bundle: dict[str, Any], *, yaw30: bool = False) -> Image.Image:
    image = base.convert("RGBA")
    draw = ImageDraw.Draw(image)
    width, height = image.size
    for group_id in GROUP_MASKS:
        curve = bundle["primary_curves"][group_id]
        points = curve_pixels(curve, image.size)
        if yaw30:
            depth_offset = {
                "front_bangs": 42,
                "side_ribbons": -18 if "left" in group_id else 28,
                "back_mass": -58,
            }.get(curve["depth_group"], 0)
            points = [(max(0, min(width, x + depth_offset)), y) for x, y in points]
        color = COLORS[group_id]
        line_width = 9 if group_id == "back_hair_mass" else 7
        draw.line(points, fill=(*color, 235), width=line_width, joint="curve")
        root = points[0]
        draw.ellipse((root[0] - 8, root[1] - 8, root[0] + 8, root[1] + 8), fill=(255, 255, 255, 255), outline=(*color, 255), width=3)
        draw.text((root[0] + 10, root[1] - 14), group_id, fill=(255, 255, 255, 255))
    return image


def make_front_overlay(bundle: dict[str, Any]) -> Image.Image:
    soft = binary_mask(TARGET_SCHEMA_DIR / "soft_hair_silhouette_mask.png")
    strict = binary_mask(TARGET_SCHEMA_DIR / "strict_hair_core_mask.png")
    if BASELINE_FRONT.exists():
        base = Image.open(BASELINE_FRONT).convert("RGBA").resize(soft.size, Image.Resampling.LANCZOS)
    else:
        base = Image.new("RGBA", soft.size, (30, 30, 30, 255))
    for mask, color in ((soft, (0, 210, 255, 70)), (strict, (80, 255, 120, 95))):
        overlay = Image.new("RGBA", soft.size, (color[0], color[1], color[2], 0))
        overlay.putalpha(mask.point(lambda value: color[3] if value else 0))
        base = Image.alpha_composite(base, overlay)
    return draw_curves(base, bundle)


def make_yaw30_plan(bundle: dict[str, Any]) -> Image.Image:
    soft = binary_mask(TARGET_SCHEMA_DIR / "soft_hair_silhouette_mask.png")
    base = Image.new("RGBA", soft.size, (31, 31, 34, 255))
    overlay = Image.new("RGBA", soft.size, (0, 160, 255, 0))
    overlay.putalpha(soft.point(lambda value: 56 if value else 0))
    base = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(base)
    draw.text((24, 24), "yaw30 planning view: depth offsets are soft hints, not locked side truth", fill=(255, 255, 255, 255))
    return draw_curves(base, bundle, yaw30=True)


def make_contact_sheet(front: Image.Image, yaw30: Image.Image) -> Image.Image:
    schema_debug = TARGET_SCHEMA_DIR / "schema_debug_contact_sheet.png"
    benchmark_sheet = SKETCHFAB_BENCHMARK_DIR / "external_hair_probe_constraint_benchmark_contact_sheet.png"
    tile = (480, 720)
    panels = [
        ("front curve overlay", front.resize(tile, Image.Resampling.LANCZOS)),
        ("yaw30 curve plan", yaw30.resize(tile, Image.Resampling.LANCZOS)),
    ]
    for label, path in (("target schema debug", schema_debug), ("external benchmark", benchmark_sheet)):
        if path.exists():
            panels.append((label, Image.open(path).convert("RGBA").resize(tile, Image.Resampling.LANCZOS)))
    sheet = Image.new("RGBA", (tile[0] * 2, tile[1] * 2), (24, 24, 24, 255))
    draw = ImageDraw.Draw(sheet)
    for index, (label, image) in enumerate(panels[:4]):
        x = (index % 2) * tile[0]
        y = (index // 2) * tile[1]
        sheet.alpha_composite(image, (x, y))
        draw.rectangle((x, y, x + tile[0] - 1, y + 30), fill=(0, 0, 0, 190))
        draw.text((x + 8, y + 8), label, fill=(255, 255, 255, 255))
    return sheet


def build_report() -> dict[str, Any]:
    design = load_json(DESIGN_SCHEMA)
    target_report = load_json(TARGET_SCHEMA_REPORT)
    prior_library = load_json(EXTERNAL_PRIOR_LIBRARY)
    benchmark = load_json(BENCHMARK_REPORT)
    external_prior_schema = build_external_prior_schema(design, prior_library, benchmark)
    bundle = build_curve_bundle(design, external_prior_schema)

    write_json(EXTERNAL_PRIOR_SCHEMA_V1, external_prior_schema)
    write_json(PRIMARY_CURVE_BUNDLE, bundle)

    front = make_front_overlay(bundle)
    yaw30 = make_yaw30_plan(bundle)
    front.save(FRONT_OVERLAY)
    yaw30.save(YAW30_PLAN)
    make_contact_sheet(front, yaw30).save(CONTACT_SHEET)

    primary_curves = bundle["primary_curves"]
    report = {
        "route": "external_prior_to_yuna_primary_curve_bundle_v1",
        "status": "primary_curve_bundle_generated_planning_only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "boundary": "No YUNA hair GLB generated; no v8 replacement; external shape is not copied.",
        "formula_stage": bundle["formula_stage"],
        "primary_group_count": len(primary_curves),
        "secondary_strand_count": len(bundle["secondary_strands"]),
        "flyaway_strand_count": len(bundle["flyaway_strands"]),
        "primary_groups": sorted(primary_curves),
        "primary_curve_point_counts": {
            group_id: len(curve["curve_points"]) for group_id, curve in primary_curves.items()
        },
        "target_schema_status": target_report.get("status"),
        "external_benchmark_status": benchmark.get("status"),
        "positive_probe_status": benchmark.get("positive_probe_status"),
        "negative_control_count": len(benchmark.get("negative_control_results", {})),
        "guards": {
            "semantic_layer_v8_modified": False,
            "replace_in_beauty_glb": False,
            "generated_yuna_hair_glb": False,
            "direct_copy_allowed": False,
            "do_not_copy_shape_directly": True,
            "ready_for_cloth_seam_surface": False,
            "manual_review_required": True,
        },
        "visual_planning_artifacts": {
            "front_overlay": file_record(FRONT_OVERLAY),
            "yaw30_plan": file_record(YAW30_PLAN),
            "contact_sheet": file_record(CONTACT_SHEET),
        },
        "outputs": {
            "external_hair_prior_schema_v1": file_record(EXTERNAL_PRIOR_SCHEMA_V1),
            "primary_curve_bundle_v1": file_record(PRIMARY_CURVE_BUNDLE),
            "primary_curve_bundle_v1_report": file_record(PRIMARY_CURVE_REPORT),
        },
        "recommended_next": "build_hair_ribbons_from_primary_curve_bundle_v1",
    }
    write_json(PRIMARY_CURVE_REPORT, report)
    report["outputs"]["primary_curve_bundle_v1_report"] = file_record(PRIMARY_CURVE_REPORT)
    write_json(PRIMARY_CURVE_REPORT, report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build YUNA primary curve bundle v1 from external priors.")
    return parser.parse_args()


def main() -> None:
    parse_args()
    report = build_report()
    print(json.dumps({
        "status": report["status"],
        "primary_groups": report["primary_groups"],
        "recommended_next": report["recommended_next"],
        "report": report["outputs"]["primary_curve_bundle_v1_report"]["path"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
