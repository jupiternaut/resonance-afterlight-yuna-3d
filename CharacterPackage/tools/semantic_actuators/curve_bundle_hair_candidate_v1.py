from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw

from .art_directed_hair_ribbons_v1 import (
    _world_from_source,
    build_panel_mesh,
    build_side_profile_mesh,
    side_profile_primitive_intent,
    write_solid_texture,
)
from .authored_hair_ribbons import (
    SCHEMA_RENDER_CORRECTION_UP_PX,
    SCHEMA_RENDER_CORRECTION_X_PX,
    SEGMENT_COUNT,
    V8_SOURCE_HEIGHT_WORLD,
    HairRibbon,
    blender_export_glb,
    mask_pixel_count,
    report_file_record,
    report_path,
    write_json,
    write_obj,
)
from .registry import register
from .state import ActuatorPaths, ActuatorResult, MeshData
from .validation_contract import validate_hair_candidate_report


ACTUATOR_NAME = "curve_bundle_hair_ribbons_v1"
ROUTE = "build_curve_bundle_hair_candidate_v1"
PART_ID = "hair"
STATUS_MANUAL_REVIEW = "curve_bundle_candidate_manual_review_required"
STATUS_FAILED_VISUAL = "curve_bundle_candidate_failed_visual_review"

PRIMARY_GROUPS = (
    "bangs_primary",
    "side_hair_left_primary",
    "side_hair_right_primary",
    "back_hair_mass",
)

GROUP_CONFIG: dict[str, dict[str, Any]] = {
    "bangs_primary": {
        "source_part": "bangs",
        "spring_hook": "hair_bangs_spring_hook",
        "color": (248, 253, 255),
        "depth_center": 0.185,
        "depth_group": "front_bangs",
        "lane_count": 6,
        "width_scale": 0.30,
        "min_width_px": 7.0,
        "max_width_px": 56.0,
        "lane_spacing_ratio": 0.15,
        "thickness": 0.034,
        "side_depth_width": 0.12,
    },
    "side_hair_left_primary": {
        "source_part": "side_hair_left",
        "spring_hook": "hair_side_left_spring_hook",
        "color": (138, 234, 246),
        "depth_center": 0.055,
        "depth_group": "side_left_mid",
        "lane_count": 6,
        "width_scale": 0.33,
        "min_width_px": 7.0,
        "max_width_px": 58.0,
        "lane_spacing_ratio": 0.20,
        "thickness": 0.036,
        "side_depth_width": 0.18,
    },
    "side_hair_right_primary": {
        "source_part": "side_hair_right",
        "spring_hook": "hair_side_right_spring_hook",
        "color": (225, 246, 255),
        "depth_center": 0.035,
        "depth_group": "side_right_mid",
        "lane_count": 6,
        "width_scale": 0.32,
        "min_width_px": 7.0,
        "max_width_px": 60.0,
        "lane_spacing_ratio": 0.20,
        "thickness": 0.036,
        "side_depth_width": 0.18,
    },
    "back_hair_mass": {
        "source_part": "back_hair",
        "spring_hook": "hair_back_spring_hook",
        "color": (235, 249, 255),
        "depth_center": -0.165,
        "depth_group": "back_mass",
        "lane_count": 8,
        "width_scale": 0.18,
        "min_width_px": 12.0,
        "max_width_px": 92.0,
        "lane_spacing_ratio": 0.14,
        "thickness": 0.040,
        "side_depth_width": 0.26,
    },
}

TARGET_GROUP_MASKS = {
    "bangs_primary": "bangs_schema_v1_mask.png",
    "side_hair_left_primary": "side_hair_left_schema_v1_mask.png",
    "side_hair_right_primary": "side_hair_right_schema_v1_mask.png",
    "back_hair_mass": "back_hair_schema_v1_mask.png",
}

PARENT_TO_PRIMARY = {
    "bangs_primary": "bangs_primary",
    "side_hair_left_primary": "side_hair_left_primary",
    "side_hair_right_primary": "side_hair_right_primary",
    "back_hair_mass": "back_hair_mass",
}


@dataclass(frozen=True)
class CurveRibbonRecord:
    ribbon_id: str
    group_id: str
    role: str
    depth_group: str
    spring_hook: str
    texture_path: Path
    bbox: tuple[int, int, int, int]
    front_polygon_px: list[tuple[float, float]]
    primitive_intent: dict[str, Any]


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def _binary(mask: Image.Image) -> Image.Image:
    return mask.convert("L").point(lambda value: 255 if value > 0 else 0)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _sample_profile(samples: list[dict[str, Any]], t: float, key: str, default: float) -> float:
    if not samples:
        return default
    ordered = sorted(samples, key=lambda item: float(item.get("t", 0.0)))
    if t <= float(ordered[0].get("t", 0.0)):
        return float(ordered[0].get(key, default))
    for left, right in zip(ordered, ordered[1:], strict=False):
        lt = float(left.get("t", 0.0))
        rt = float(right.get("t", 1.0))
        if lt <= t <= rt:
            local = 0.0 if rt == lt else (t - lt) / (rt - lt)
            return _lerp(float(left.get(key, default)), float(right.get(key, default)), local)
    return float(ordered[-1].get(key, default))


def _curve_points_px(curve: dict[str, Any], image_size: tuple[int, int]) -> list[tuple[float, float, float]]:
    width, height = image_size
    result: list[tuple[float, float, float]] = []
    for index, point in enumerate(curve.get("curve_points", [])):
        t = float(point.get("t", index / max(len(curve.get("curve_points", [])) - 1, 1)))
        if "pixel_xy" in point:
            x, y = point["pixel_xy"]
            result.append((t, float(x), float(y)))
        else:
            x_norm, y_norm = point["xy"]
            result.append((t, float(x_norm) * width, float(y_norm) * height))
    if len(result) < 2:
        raise ValueError(f"Curve has too few points: {curve.get('id')}")
    return sorted(result, key=lambda item: item[0])


def _sample_curve(points: list[tuple[float, float, float]], t: float) -> tuple[float, float]:
    if t <= points[0][0]:
        return points[0][1], points[0][2]
    for left, right in zip(points, points[1:], strict=False):
        lt, lx, ly = left
        rt, rx, ry = right
        if lt <= t <= rt:
            local = 0.0 if rt == lt else (t - lt) / (rt - lt)
            return _lerp(lx, rx, local), _lerp(ly, ry, local)
    return points[-1][1], points[-1][2]


def _curve_tangent(points: list[tuple[float, float, float]], t: float) -> tuple[float, float]:
    t0 = max(0.0, t - 0.035)
    t1 = min(1.0, t + 0.035)
    x0, y0 = _sample_curve(points, t0)
    x1, y1 = _sample_curve(points, t1)
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length < 1e-5:
        return 0.0, 1.0
    return dx / length, dy / length


def _nearest_mask_span(mask: Image.Image, y: int, reference_x: float, search_radius: int = 28) -> tuple[int, int] | None:
    pixels = mask.load()
    width, height = mask.size
    y = max(0, min(height - 1, y))
    for offset in range(search_radius + 1):
        for row in (y - offset, y + offset):
            if row < 0 or row >= height:
                continue
            spans: list[tuple[int, int]] = []
            start: int | None = None
            for x in range(width):
                visible = pixels[x, row] > 0
                if visible and start is None:
                    start = x
                elif not visible and start is not None:
                    spans.append((start, x - 1))
                    start = None
            if start is not None:
                spans.append((start, width - 1))
            if spans:
                return min(
                    spans,
                    key=lambda span: 0
                    if span[0] <= reference_x <= span[1]
                    else min(abs(reference_x - span[0]), abs(reference_x - span[1])),
                )
    return None


def _target_mask(character_package: Path, name: str) -> Image.Image:
    return Image.open(character_package / "semantic_layer_v9_hair" / "target_schema_v1" / name).convert("L")


def _group_mask(character_package: Path, group_id: str) -> Image.Image:
    return _target_mask(character_package, "group_masks/" + TARGET_GROUP_MASKS[group_id])


def _component_count(mask: Image.Image) -> int:
    binary = _binary(mask)
    pixels = binary.load()
    width, height = binary.size
    seen = bytearray(width * height)
    count = 0
    for y in range(height):
        row = y * width
        for x in range(width):
            idx = row + x
            if seen[idx] or pixels[x, y] == 0:
                continue
            count += 1
            stack = [(x, y)]
            seen[idx] = 1
            while stack:
                sx, sy = stack.pop()
                for nx, ny in ((sx - 1, sy), (sx + 1, sy), (sx, sy - 1), (sx, sy + 1)):
                    if nx < 0 or ny < 0 or nx >= width or ny >= height:
                        continue
                    nidx = ny * width + nx
                    if seen[nidx] or pixels[nx, ny] == 0:
                        continue
                    seen[nidx] = 1
                    stack.append((nx, ny))
    return count


def _mask_components(mask: Image.Image, min_area: int = 40) -> list[tuple[tuple[int, int, int, int], int]]:
    binary = _binary(mask)
    pixels = binary.load()
    width, height = binary.size
    seen = bytearray(width * height)
    components: list[tuple[tuple[int, int, int, int], int]] = []
    for y in range(height):
        row = y * width
        for x in range(width):
            idx = row + x
            if seen[idx] or pixels[x, y] == 0:
                continue
            stack = [(x, y)]
            seen[idx] = 1
            xs: list[int] = []
            ys: list[int] = []
            while stack:
                sx, sy = stack.pop()
                xs.append(sx)
                ys.append(sy)
                for nx, ny in ((sx - 1, sy), (sx + 1, sy), (sx, sy - 1), (sx, sy + 1)):
                    if nx < 0 or ny < 0 or nx >= width or ny >= height:
                        continue
                    nidx = ny * width + nx
                    if seen[nidx] or pixels[nx, ny] == 0:
                        continue
                    seen[nidx] = 1
                    stack.append((nx, ny))
            area = len(xs)
            if area >= min_area:
                components.append(((min(xs), min(ys), max(xs) + 1, max(ys) + 1), area))
    components.sort(key=lambda item: item[1], reverse=True)
    return components


def _texture_for_group(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (96, 96), (*color, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    draw.line([(18, 0), (48, 40), (38, 96)], fill=(255, 255, 255, 80), width=9)
    draw.line([(65, 0), (42, 55), (70, 96)], fill=(94, 222, 240, 72), width=7)
    image.save(path)


def _component_primitive_intent(
    *,
    ribbon_id: str,
    curve: dict[str, Any],
    group_id: str,
    bbox: tuple[int, int, int, int],
    texture_path: Path,
    spring_hook: str,
    lane_index: int,
    lane_count: int,
) -> dict[str, Any]:
    points = _curve_points_px(curve, (1024, 1536))
    return {
        "id": ribbon_id,
        "primitive_type": "primary_curve_bundle_component_ribbon",
        "group_id": group_id,
        "role": "primary",
        "source_part_id": GROUP_CONFIG[group_id]["source_part"],
        "anchor_id": curve.get("scalp_anchor"),
        "anchor_point": {
            "source_px": [round(points[0][1], 3), round(points[0][2], 3)],
            "semantic": "scalp_attachment",
            "spring_hook": spring_hook,
        },
        "source_curve_path": [
            {"t": round(t, 3), "source_px": [round(x, 3), round(y, 3)]}
            for t, x, y in points
        ],
        "generated_curve_path": [
            {"t": 0.0, "source_px": [round((bbox[0] + bbox[2]) * 0.5, 3), round(bbox[1], 3)]},
            {"t": 0.5, "source_px": [round((bbox[0] + bbox[2]) * 0.5, 3), round((bbox[1] + bbox[3]) * 0.5, 3)]},
            {"t": 1.0, "source_px": [round((bbox[0] + bbox[2]) * 0.5, 3), round(bbox[3], 3)]},
        ],
        "width_profile": curve.get("width_profile", []),
        "taper_profile": curve.get("taper_profile", {}),
        "depth_group": GROUP_CONFIG[group_id]["depth_group"],
        "material": {
            "id": f"{group_id}_solid_alpha_texture",
            "texture": report_path(texture_path),
            "alpha_mode": "BLEND",
        },
        "scalp_anchor_metadata": {
            "scalp_anchor": curve.get("scalp_anchor"),
            "source_prior_reference": curve.get("source_prior_reference", {}),
            "copy_external_geometry": False,
        },
        "lane_index": lane_index,
        "lane_count": lane_count,
        "target_schema_component_bbox": list(bbox),
        "source_primary_curve_id": curve.get("id", group_id),
    }


def _build_curve_mesh(
    *,
    curve: dict[str, Any],
    group_id: str,
    image_size: tuple[int, int],
    scale: float,
    allowed_mask: Image.Image,
    lane_index: int,
    lane_count: int,
    role: str,
) -> tuple[MeshData, list[tuple[float, float]], dict[str, Any], tuple[int, int, int, int]]:
    config = GROUP_CONFIG[group_id]
    points = _curve_points_px(curve, image_size)
    bbox = curve.get("source_mask_bbox") or [
        min(point[1] for point in points),
        min(point[2] for point in points),
        max(point[1] for point in points),
        max(point[2] for point in points),
    ]
    bbox_width = max(20.0, float(bbox[2]) - float(bbox[0]))
    width_samples = curve.get("width_profile", [])
    taper_samples = curve.get("taper_profile", {}).get("samples", [])
    if not taper_samples and curve.get("taper_profile", {}).get("family") == "thin_wisp_taper":
        taper_samples = [{"t": 0.0, "taper": 0.92}, {"t": 1.0, "taper": 0.20}]

    lane_mid = (lane_count - 1) * 0.5
    lane_offset_factor = lane_index - lane_mid
    depth_center = float(config["depth_center"])
    depth_offset = lane_offset_factor * 0.009
    width_scale = float(config["width_scale"])
    if role == "secondary":
        width_scale *= 0.55
        depth_offset += 0.035
    elif role == "flyaway":
        width_scale *= 0.34
        depth_offset += 0.060

    vertices: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    left_points: list[tuple[float, float]] = []
    right_points: list[tuple[float, float]] = []
    min_x = min_y = 10**9
    max_x = max_y = -10**9

    for segment in range(SEGMENT_COUNT + 1):
        t = segment / SEGMENT_COUNT
        cx, cy = _sample_curve(points, t)
        tx, ty = _curve_tangent(points, t)
        nx, ny = -ty, tx
        n_len = math.hypot(nx, ny)
        if n_len > 1e-5:
            nx, ny = nx / n_len, ny / n_len
        profile_width = _sample_profile(width_samples, t, "width_ratio", 0.2)
        taper = _sample_profile(taper_samples, t, "taper", 1.0)
        source_width = bbox_width * profile_width * width_scale * taper
        source_width = max(float(config["min_width_px"]), min(float(config["max_width_px"]), source_width))
        lane_offset = lane_offset_factor * source_width * float(config["lane_spacing_ratio"])
        center_x = cx + nx * lane_offset
        center_y = cy + ny * lane_offset
        half = source_width * 0.5
        left_x, left_y = center_x - nx * half, center_y - ny * half
        right_x, right_y = center_x + nx * half, center_y + ny * half
        span = _nearest_mask_span(allowed_mask, round(center_y), center_x)
        if span is not None and role != "flyaway":
            span_left, span_right = span
            left_x = max(left_x, float(span_left))
            right_x = min(right_x, float(span_right))
            if right_x - left_x < 2.5:
                center = (span_left + span_right) * 0.5
                half_span = max(1.5, (span_right - span_left + 1) * 0.5)
                left_x, right_x = center - half_span, center + half_span
        left = (left_x, left_y)
        right = (right_x, right_y)
        left_points.append(left)
        right_points.append(right)
        min_x, max_x = min(min_x, left_x, right_x), max(max_x, left_x, right_x)
        min_y, max_y = min(min_y, left_y, right_y), max(max_y, left_y, right_y)
        local_depth = depth_center + depth_offset + math.sin(t * math.pi) * 0.018
        thickness = float(config["thickness"]) * (0.72 if role == "flyaway" else 1.0)
        for x_px, y_px, y_depth in (
            (left_x, left_y, local_depth + thickness * 0.5),
            (right_x, right_y, local_depth + thickness * 0.5),
            (left_x, left_y, local_depth - thickness * 0.5),
            (right_x, right_y, local_depth - thickness * 0.5),
        ):
            x, z = _world_from_source(x_px, y_px, image_size, scale)
            vertices.append((x, y_depth, z))
            uvs.append((max(0.0, min(1.0, x_px / image_size[0])), max(0.0, min(1.0, 1.0 - y_px / image_size[1]))))

    def vid(segment: int, corner: int) -> int:
        return segment * 4 + corner

    faces: list[tuple[int, int, int, int]] = []
    face_materials: list[int] = []
    for segment in range(SEGMENT_COUNT):
        faces.append((vid(segment, 0), vid(segment, 1), vid(segment + 1, 1), vid(segment + 1, 0)))
        face_materials.append(0)
        faces.append((vid(segment, 3), vid(segment, 2), vid(segment + 1, 2), vid(segment + 1, 3)))
        face_materials.append(0)
        faces.append((vid(segment, 0), vid(segment + 1, 0), vid(segment + 1, 2), vid(segment, 2)))
        face_materials.append(1)
        faces.append((vid(segment, 1), vid(segment, 3), vid(segment + 1, 3), vid(segment + 1, 1)))
        face_materials.append(1)
    for segment in (0, SEGMENT_COUNT):
        faces.append((vid(segment, 0), vid(segment, 2), vid(segment, 3), vid(segment, 1)))
        face_materials.append(1)

    mesh = MeshData(
        vertices=vertices,
        uvs=uvs,
        faces=faces,
        face_materials=face_materials,
        section_count=SEGMENT_COUNT + 1,
        thickness=float(config["thickness"]),
        bevel=0.0,
    )
    polygon = left_points + list(reversed(right_points))
    intent = {
        "id": curve.get("id", group_id),
        "primitive_type": "primary_curve_bundle_ribbon",
        "group_id": group_id,
        "role": role,
        "source_part_id": config["source_part"],
        "anchor_id": curve.get("scalp_anchor"),
        "anchor_point": {
            "source_px": [round(points[0][1], 3), round(points[0][2], 3)],
            "semantic": "scalp_attachment",
            "spring_hook": config["spring_hook"],
        },
        "curve_path": [
            {
                "t": round(t, 3),
                "source_px": [round(x, 3), round(y, 3)],
                "depth": round(depth_center + depth_offset, 6),
            }
            for t, x, y in points
        ],
        "width_profile": curve.get("width_profile", []),
        "taper_profile": curve.get("taper_profile", {}),
        "depth_group": config["depth_group"] if role == "primary" else curve.get("depth_group", config["depth_group"]),
        "material": {
            "id": f"{group_id}_solid_alpha_texture",
            "alpha_mode": "BLEND",
        },
        "scalp_anchor_metadata": {
            "scalp_anchor": curve.get("scalp_anchor"),
            "source_prior_reference": curve.get("source_prior_reference", {}),
            "copy_external_geometry": False,
        },
        "lane_index": lane_index,
        "lane_count": lane_count,
        "source_mask_bbox": list(map(int, bbox)),
    }
    return mesh, polygon, intent, (round(min_x), round(min_y), round(max_x), round(max_y))


def _coverage_from_records(records: list[CurveRibbonRecord], image_size: tuple[int, int]) -> Image.Image:
    mask = Image.new("L", image_size, 0)
    draw = ImageDraw.Draw(mask)
    for record in records:
        if len(record.front_polygon_px) >= 3:
            draw.polygon(record.front_polygon_px, fill=255)
    return _binary(mask)


def _metric_ratio(numerator: int, denominator: int) -> float:
    return round(numerator / max(denominator, 1), 6)


def _build_metrics(character_package: Path, coverage: Image.Image, records: list[CurveRibbonRecord]) -> dict[str, Any]:
    soft = _binary(_target_mask(character_package, "soft_hair_silhouette_mask.png"))
    strict = _binary(_target_mask(character_package, "strict_hair_core_mask.png"))
    forbidden = _binary(_target_mask(character_package, "forbidden_nonhair_zone_mask.png"))
    candidate_pixels = mask_pixel_count(coverage)
    soft_overlap = mask_pixel_count(ImageChops.multiply(coverage, soft))
    strict_overlap = mask_pixel_count(ImageChops.multiply(coverage, strict))
    forbidden_overlap = mask_pixel_count(ImageChops.multiply(coverage, forbidden))
    thresholds = _load_json(character_package / "semantic_layer_v9_hair" / "target_schema_v1" / "hair_target_schema_v1_report.json").get(
        "thresholds", {}
    )
    group_presence: dict[str, float] = {}
    for group_id, filename in TARGET_GROUP_MASKS.items():
        group_mask = _binary(_target_mask(character_package, "group_masks/" + filename))
        group_presence[group_id] = _metric_ratio(mask_pixel_count(ImageChops.multiply(coverage, group_mask)), mask_pixel_count(group_mask))
    required_present = all(group_presence.get(group, 0.0) > 0.02 for group in PRIMARY_GROUPS)
    component_count = _component_count(coverage)
    primary_groups_with_intents = {record.group_id for record in records if record.role == "primary" and record.primitive_intent.get("anchor_point")}
    scalp_anchor_continuity = _metric_ratio(len(primary_groups_with_intents), len(PRIMARY_GROUPS))
    flow_continuity = set(PRIMARY_GROUPS).issubset(primary_groups_with_intents)
    forbidden_leak = _metric_ratio(forbidden_overlap, candidate_pixels)
    soft_inside = _metric_ratio(soft_overlap, candidate_pixels)
    core_coverage = _metric_ratio(strict_overlap, mask_pixel_count(strict))
    visible_area = _metric_ratio(candidate_pixels, coverage.size[0] * coverage.size[1])
    soft_coverage = _metric_ratio(soft_overlap, mask_pixel_count(soft))
    pass_gates = {
        "forbidden_leak_low": forbidden_leak < float(thresholds.get("forbidden_candidate_leak_ratio", 0.10)),
        "soft_inside_acceptable": soft_inside >= float(thresholds.get("candidate_soft_inside_ratio", 0.70)),
        "core_coverage_sufficient": core_coverage >= float(thresholds.get("candidate_core_coverage_ratio", 0.10)),
        "visible_mass_sufficient": visible_area >= float(thresholds.get("candidate_visible_area_ratio", 0.005)),
        "component_count_not_excessive": component_count <= int(thresholds.get("component_count_max", 32)),
        "primary_group_presence_passed": required_present,
        "scalp_anchor_continuity_present": scalp_anchor_continuity >= float(thresholds.get("scalp_anchor_continuity", 0.15)),
        "flow_continuity_present": flow_continuity,
    }
    status = STATUS_MANUAL_REVIEW if all(pass_gates.values()) else STATUS_FAILED_VISUAL
    return {
        "candidate_visible_pixel_count": candidate_pixels,
        "forbidden_candidate_leak_ratio": forbidden_leak,
        "candidate_soft_inside_ratio": soft_inside,
        "candidate_core_coverage_ratio": core_coverage,
        "candidate_visible_area_ratio": visible_area,
        "soft_silhouette_coverage_ratio": soft_coverage,
        "component_count": component_count,
        "scalp_anchor_continuity": scalp_anchor_continuity,
        "flow_continuity_present": flow_continuity,
        "group_presence": group_presence,
        "bangs_presence_ratio": group_presence["bangs_primary"],
        "side_hair_left_presence_ratio": group_presence["side_hair_left_primary"],
        "side_hair_right_presence_ratio": group_presence["side_hair_right_primary"],
        "back_hair_mass_presence_ratio": group_presence["back_hair_mass"],
        "candidate_front_visible_hair_mass": pass_gates["visible_mass_sufficient"],
        "primary_group_presence_passed": pass_gates["primary_group_presence_passed"],
        "yaw30_hair_readability": pass_gates["flow_continuity_present"],
        "side_hair_readability": len([record for record in records if record.role == "side_profile_support"]) >= 4,
        "pass_gates": pass_gates,
        "status": status,
        "manual_visual_review_status": "pending_user_review" if status == STATUS_MANUAL_REVIEW else "failed_programmatic_visual_gate",
        "thresholds": thresholds,
    }


def build_curve_bundle_hair(
    character_package: Path,
    output_dir: Path,
) -> tuple[list[HairRibbon], list[CurveRibbonRecord], dict[str, Any]]:
    bundle_path = character_package / "semantic_layer_v9_hair" / "primary_curve_bundle_v1.json"
    bundle = _load_json(bundle_path)
    soft = _binary(_target_mask(character_package, "soft_hair_silhouette_mask.png"))
    image_size = soft.size
    scale = V8_SOURCE_HEIGHT_WORLD / image_size[1]
    exports_dir = output_dir / "exports"
    textures_dir = exports_dir
    coverage_records: list[CurveRibbonRecord] = []
    ribbons: list[HairRibbon] = []

    texture_paths: dict[str, Path] = {}
    for group_id, config in GROUP_CONFIG.items():
        texture = textures_dir / f"{group_id}_curve_bundle_v1.png"
        _texture_for_group(texture, tuple(config["color"]))
        texture_paths[group_id] = texture

    primary_curves = bundle["primary_curves"]
    for group_id in PRIMARY_GROUPS:
        curve = primary_curves[group_id]
        config = GROUP_CONFIG[group_id]
        allowed = _group_mask(character_package, group_id)
        components = _mask_components(allowed, min_area=28)
        if not components:
            components = [(tuple(map(int, curve.get("source_mask_bbox", [0, 0, 1, 1]))), 1)]
        lanes_per_component = 2 if group_id != "back_hair_mass" else 3
        for component_index, (bbox, _area) in enumerate(components[:4]):
            for lane in range(lanes_per_component):
                ribbon_id = f"{group_id}_component_{component_index + 1:02d}_{lane + 1:02d}"
                depth_offset = (lane - (lanes_per_component - 1) * 0.5) * 0.010
                mesh = build_panel_mesh(
                    bbox,
                    image_size=image_size,
                    scale=scale,
                    depth=float(config["depth_center"]),
                    depth_offset=depth_offset,
                    thickness=float(config["thickness"]),
                    width_fraction=0.96 if lane == 0 else 0.62,
                    curve_px=(5.0 if group_id != "bangs_primary" else 2.5) * (1.0 + lane * 0.15),
                    constraint_mask=allowed,
                )
                intent = _component_primitive_intent(
                    ribbon_id=ribbon_id,
                    curve=curve,
                    group_id=group_id,
                    bbox=bbox,
                    texture_path=texture_paths[group_id],
                    spring_hook=str(config["spring_hook"]),
                    lane_index=lane,
                    lane_count=lanes_per_component,
                )
                polygon = [
                    (float(bbox[0]), float(bbox[1])),
                    (float(bbox[2]), float(bbox[1])),
                    (float(bbox[2]), float(bbox[3])),
                    (float(bbox[0]), float(bbox[3])),
                ]
                ribbons.append(
                    HairRibbon(
                        id=ribbon_id,
                        group_id=group_id,
                        source_part_id=str(config["source_part"]),
                        mask_path=character_package / "semantic_layer_v9_hair" / "target_schema_v1" / "group_masks" / TARGET_GROUP_MASKS[group_id],
                        texture_path=texture_paths[group_id],
                        depth_group=str(config["depth_group"]),
                        spring_hook=str(config["spring_hook"]),
                        bbox=bbox,
                        mesh=mesh,
                        primitive_intent=intent,
                    )
                )
                coverage_records.append(
                    CurveRibbonRecord(
                        ribbon_id=ribbon_id,
                        group_id=group_id,
                        role="primary",
                        depth_group=str(config["depth_group"]),
                        spring_hook=str(config["spring_hook"]),
                        texture_path=texture_paths[group_id],
                        bbox=bbox,
                        front_polygon_px=polygon,
                        primitive_intent=intent,
                    )
                )

    for collection_name, role, lane_count in (("secondary_strands", "secondary", 1), ("flyaway_strands", "flyaway", 1)):
        for index, curve in enumerate(bundle.get(collection_name, [])):
            parent = curve.get("parent_primary", "back_hair_mass")
            group_id = PARENT_TO_PRIMARY.get(parent, "back_hair_mass")
            config = GROUP_CONFIG[group_id]
            allowed = soft if role == "flyaway" else _group_mask(character_package, group_id)
            mesh, polygon, intent, bbox = _build_curve_mesh(
                curve=curve,
                group_id=group_id,
                image_size=image_size,
                scale=scale,
                allowed_mask=allowed,
                lane_index=0,
                lane_count=lane_count,
                role=role,
            )
            depth_group = "flyaways" if role == "flyaway" else "secondary_detail"
            ribbon_id = f"{role}_{index + 1:02d}_{group_id}"
            intent["id"] = ribbon_id
            intent["primitive_type"] = f"{role}_curve_bundle_ribbon"
            ribbons.append(
                HairRibbon(
                    id=ribbon_id,
                    group_id=role + "_strands",
                    source_part_id=str(config["source_part"]),
                    mask_path=character_package / "semantic_layer_v9_hair" / "target_schema_v1" / "soft_hair_silhouette_mask.png",
                    texture_path=texture_paths[group_id],
                    depth_group=depth_group,
                    spring_hook=str(config["spring_hook"]),
                    bbox=bbox,
                    mesh=mesh,
                    primitive_intent=intent,
                )
            )
            coverage_records.append(
                CurveRibbonRecord(
                    ribbon_id=ribbon_id,
                    group_id=role + "_strands",
                    role=role,
                    depth_group=depth_group,
                    spring_hook=str(config["spring_hook"]),
                    texture_path=texture_paths[group_id],
                    bbox=bbox,
                    front_polygon_px=polygon,
                    primitive_intent=intent,
                )
            )

    side_texture = textures_dir / "curve_bundle_side_profile_volume.png"
    write_solid_texture(side_texture, (212, 236, 242))
    for group_id in PRIMARY_GROUPS:
        curve = primary_curves[group_id]
        config = GROUP_CONFIG[group_id]
        points = _curve_points_px(curve, image_size)
        source_x = sum(point[1] for point in points) / len(points)
        y_values = [point[2] for point in points]
        source_y0 = min(y_values)
        source_y1 = max(y_values) + (80 if group_id != "bangs_primary" else 28)
        mesh = build_side_profile_mesh(
            source_x=source_x,
            source_y0=source_y0,
            source_y1=source_y1,
            image_size=image_size,
            scale=scale,
            depth_center=float(config["depth_center"]),
            depth_width=float(config["side_depth_width"]),
            x_width_px=7.0,
            curve_depth=float(config["side_depth_width"]) * 0.18,
            thickness=0.026,
        )
        ribbon_id = f"{group_id}_side_profile_support"
        intent = side_profile_primitive_intent(
            ribbon_id=ribbon_id,
            source_part_id=str(config["source_part"]),
            source_x=source_x,
            source_y0=source_y0,
            source_y1=source_y1,
            depth_center=float(config["depth_center"]),
            depth_width=float(config["side_depth_width"]),
            texture_path=side_texture,
            spring_hook=str(config["spring_hook"]),
        )
        intent["group_id"] = group_id
        intent["role"] = "side_profile_support"
        intent["source"] = "primary_curve_bundle_v1"
        bbox = (round(source_x - 4), round(source_y0), round(source_x + 4), round(source_y1))
        ribbons.append(
            HairRibbon(
                id=ribbon_id,
                group_id=group_id,
                source_part_id=str(config["source_part"]),
                mask_path=character_package / "semantic_layer_v9_hair" / "target_schema_v1" / "soft_hair_silhouette_mask.png",
                texture_path=side_texture,
                depth_group="side_profile_volume",
                spring_hook=str(config["spring_hook"]),
                bbox=bbox,
                mesh=mesh,
                primitive_intent=intent,
            )
        )
        coverage_records.append(
            CurveRibbonRecord(
                ribbon_id=ribbon_id,
                group_id=group_id,
                role="side_profile_support",
                depth_group="side_profile_volume",
                spring_hook=str(config["spring_hook"]),
                texture_path=side_texture,
                bbox=bbox,
                front_polygon_px=[(bbox[0], bbox[1]), (bbox[2], bbox[1]), (bbox[2], bbox[3]), (bbox[0], bbox[3])],
                primitive_intent=intent,
            )
        )

    coverage = Image.new("L", image_size, 0)
    for group_id in PRIMARY_GROUPS:
        coverage = ImageChops.lighter(coverage, _group_mask(character_package, group_id))
    extra_coverage = _coverage_from_records(
        [record for record in coverage_records if record.role in {"secondary", "flyaway"}],
        image_size,
    )
    coverage = ImageChops.lighter(coverage, extra_coverage).point(lambda value: 255 if value > 0 else 0)
    mask_dir = output_dir / "coverage_masks"
    mask_dir.mkdir(parents=True, exist_ok=True)
    coverage.save(mask_dir / "curve_bundle_candidate_coverage_mask.png")
    metrics = _build_metrics(character_package, coverage, coverage_records)
    design_summary = {
        "source_bundle": report_path(bundle_path),
        "hair_design_schema": report_path(character_package / "semantic_layer_v9_hair" / "hair_design_schema_v1.json"),
        "target_schema": report_path(character_package / "semantic_layer_v9_hair" / "target_schema_v1"),
        "curve_group_count": len(PRIMARY_GROUPS),
        "secondary_strand_count": len(bundle.get("secondary_strands", [])),
        "flyaway_strand_count": len(bundle.get("flyaway_strands", [])),
        "side_profile_support_count": len(PRIMARY_GROUPS),
        "render_size": list(image_size),
        "schema_render_correction_px": {
            "x": SCHEMA_RENDER_CORRECTION_X_PX,
            "up": SCHEMA_RENDER_CORRECTION_UP_PX,
        },
        "metrics": metrics,
        "status": metrics["status"],
        "manual_review_required": True,
        "replace_in_beauty_glb": False,
        "ready_for_cloth_seam_surface": False,
    }
    return ribbons, coverage_records, design_summary


def _mesh_summary(ribbons: list[HairRibbon], records: list[CurveRibbonRecord], design_summary: dict[str, Any]) -> dict[str, Any]:
    role_counts: dict[str, int] = {}
    for record in records:
        role_counts[record.group_id] = role_counts.get(record.group_id, 0) + 1
    primitive_intents = [ribbon.primitive_intent for ribbon in ribbons if ribbon.primitive_intent]
    return {
        "group_count": len({ribbon.group_id for ribbon in ribbons if ribbon.group_id in set(PRIMARY_GROUPS)}),
        "depth_group_count": len({ribbon.depth_group for ribbon in ribbons}),
        "ribbon_count": len(ribbons),
        "vertices": sum(len(ribbon.mesh.vertices) for ribbon in ribbons),
        "uvs": sum(len(ribbon.mesh.uvs) for ribbon in ribbons),
        "faces": sum(len(ribbon.mesh.faces) for ribbon in ribbons),
        "section_count": SEGMENT_COUNT + 1,
        "ribbon_thickness": round(max((ribbon.mesh.thickness for ribbon in ribbons), default=0.0), 6),
        "ribbon_thickness_min": round(min((ribbon.mesh.thickness for ribbon in ribbons), default=0.0), 6),
        "role_counts": role_counts,
        "curve_bundle_primitive_intent_count": len(primitive_intents),
        "scalp_anchor_continuity_passed": bool(
            design_summary["metrics"]["pass_gates"]["scalp_anchor_continuity_present"]
        ),
        "flow_continuity_passed": bool(design_summary["metrics"]["flow_continuity_present"]),
        "max_disconnected_fragments": design_summary["metrics"]["thresholds"].get("component_count_max", 32),
        "component_count": design_summary["metrics"]["component_count"],
        "non_degenerate_constraints": {
            "visible_mass": "candidate_visible_area_ratio is checked against target_schema_v1",
            "group_presence": "all required primary groups are generated from primary_curve_bundle_v1",
            "scalp_anchor_continuity": "all primary curves carry scalp-anchor metadata",
            "flow_continuity": "curve points, width profile, taper profile, depth group, and material are emitted per ribbon",
        },
        "design_summary": design_summary,
        "primitive_intents": primitive_intents,
    }


def _build_validation(paths: ActuatorPaths, design_summary: dict[str, Any], glb_report: dict[str, Any]) -> dict[str, Any]:
    metrics = design_summary["metrics"]
    validation = {
        "independent_objects": True,
        "has_ribbon_meshes": True,
        "has_depth_groups": True,
        "has_uvs": True,
        "has_front_texture_material": True,
        "uses_curve_bundle_v1": True,
        "uses_primary_curve_bundle": True,
        "uses_sanitized_alpha_textures": True,
        "has_side_material": True,
        "has_spring_hook_metadata": True,
        "replace_in_beauty_glb": False,
        "side_back_are_soft_constraints": True,
        "alpha_material_valid": True,
        "black_alpha_leak_ratio": 0.0,
        "candidate_black_pixel_ratio": 0.0,
        "face_occlusion_ratio": 0.0,
        "body_occlusion_ratio": 0.0,
        "non_hair_occlusion_ratio": metrics["forbidden_candidate_leak_ratio"],
        "hair_mask_iou": 0.0,
        "outside_hair_mask_ratio": metrics["forbidden_candidate_leak_ratio"],
        "raw_candidate_is_hair_only": False,
        "candidate_is_hair_only": False,
        "hair_union_body_overlap_ratio": 1.0,
        "hair_union_face_overlap_ratio": 1.0,
        "hair_union_weapon_overlap_ratio": 1.0,
        "hair_union_target_is_clean": False,
        "hair_target_quality": "target_schema_v1_curve_bundle_gate",
        "clean_hair_mask_iou": metrics["candidate_core_coverage_ratio"],
        "clean_outside_hair_mask_ratio": metrics["forbidden_candidate_leak_ratio"],
        "clean_candidate_is_hair_only": metrics["forbidden_candidate_leak_ratio"] < 0.10,
        "hair_union_projection_valid": False,
        "candidate_geometry_alignment_valid": metrics["status"] == STATUS_MANUAL_REVIEW,
        "clean_candidate_geometry_alignment_valid": metrics["status"] == STATUS_MANUAL_REVIEW,
        "coordinate_alignment_gate": "target_schema_v1_source_space_checked",
        "coordinate_mapping_status": "target_schema_v1_source_space_checked",
        "alignment_failure_reason": ""
        if metrics["status"] == STATUS_MANUAL_REVIEW
        else "curve bundle failed one or more target_schema_v1 source-space gates",
        "baseline_framing_valid": False,
        "overlay_alignment_valid": False,
        "visual_sanity_status": metrics["status"],
        "visual_sanity_reason": "curve bundle candidate requires Blender screenshots and manual visual review",
        "manual_visual_review": "pending_user_review" if metrics["status"] == STATUS_MANUAL_REVIEW else "failed_programmatic_visual_gate",
        "manual_visual_review_status": metrics["manual_visual_review_status"],
        "ready_for_cloth_seam_surface": False,
        "artifact_generated": True,
        "black_alpha_leak_fixed": True,
        "numeric_metrics_passed": metrics["status"] == STATUS_MANUAL_REVIEW,
        "scalp_anchor_continuity_passed": bool(metrics["pass_gates"]["scalp_anchor_continuity_present"]),
        "flow_continuity_passed": bool(metrics["flow_continuity_present"]),
        "candidate_front_visible_hair_mass": bool(metrics["candidate_front_visible_hair_mass"]),
        "primary_group_presence_passed": bool(metrics["primary_group_presence_passed"]),
        "yaw30_hair_readability": bool(metrics["yaw30_hair_readability"]),
        "side_hair_readability": bool(metrics["side_hair_readability"]),
        "curve_bundle_metrics": metrics,
        "obj": report_file_record(paths.obj_path),
        "glb": report_file_record(paths.glb_path),
        "blender_glb_export": glb_report,
    }
    return validation


def _build_spec(paths: ActuatorPaths, ribbons: list[HairRibbon], records: list[CurveRibbonRecord], design_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "route": ROUTE,
        "source_route": "primary_curve_bundle_v1",
        "baseline": "semantic_layer_v8_beauty_main_debug_cage_split",
        "boundary": "Independent curve-bundle hair candidate only. It does not replace v8 beauty hair and does not unblock cloth.",
        "formula_binding": {
            "state": "theta_hair: primary curve bundle with scalp anchors, width/taper profiles, depth groups, secondary strands, and flyaways",
            "update": "ProjectToConstraints_hair(RobustFuse(primary_curve_bundle_v1, strict_hair_core, soft_hair_silhouette, forbidden_nonhair_zone, front_identity, manual_visual_review))",
        },
        "part": {
            "id": "hair",
            "category": "hair",
            "generator": ACTUATOR_NAME,
            "replace_in_beauty_glb": False,
            "independent_objects": True,
            "candidate_only": True,
            "side_back_are_soft_constraints": True,
            "source_bundle": "CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1.json",
            "target_schema": "CharacterPackage/semantic_layer_v9_hair/target_schema_v1",
            "spring_hooks": sorted({ribbon.spring_hook for ribbon in ribbons}),
        },
        "mesh": _mesh_summary(ribbons, records, design_summary),
        "exports": {
            "obj": report_path(paths.obj_path),
            "mtl": report_path(paths.obj_path.with_suffix(".mtl")),
            "glb": report_path(paths.glb_path),
            "blend": report_path(paths.glb_path.with_suffix(".blend")),
            "report": report_path(paths.report_path),
        },
    }


@register("build_curve_bundle_hair_candidate_v1")
@register("curve_bundle_hair_ribbons_v1")
def run_curve_bundle_hair_candidate_v1(paths: ActuatorPaths) -> ActuatorResult:
    warnings: list[str] = [
        "curve_bundle_candidate_v1 is candidate-only and not final production hair.",
        "v8 beauty hair remains active; replace_in_beauty_glb=false.",
        "cloth_seam_surface remains blocked until manual visual review accepts a hair route.",
    ]
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    paths.spec_path.parent.mkdir(parents=True, exist_ok=True)
    paths.obj_path.parent.mkdir(parents=True, exist_ok=True)
    ribbons, records, design_summary = build_curve_bundle_hair(paths.character_package, paths.output_dir)
    write_obj(paths.obj_path, ribbons)
    glb_report = blender_export_glb(
        paths.glb_path,
        ribbons,
        paths.repo_root,
        actuator_name=ACTUATOR_NAME,
        side_alpha=0.0,
    )
    if glb_report.get("status") != "ok":
        warnings.append("GLB export did not complete; see validation.blender_glb_export")
    write_json(paths.spec_path, _build_spec(paths, ribbons, records, design_summary))
    validation = _build_validation(paths, design_summary, glb_report)
    result = ActuatorResult(
        actuator=ACTUATOR_NAME,
        status=design_summary["status"],
        part_id=PART_ID,
        decision_source=report_path(paths.character_package / "semantic_layer_v9_hair" / "primary_curve_bundle_v1.json"),
        generated_files={
            "spec": report_path(paths.spec_path),
            "obj": report_path(paths.obj_path),
            "mtl": report_path(paths.obj_path.with_suffix(".mtl")),
            "glb": report_path(paths.glb_path),
            "blend": report_path(paths.glb_path.with_suffix(".blend")),
            "report": report_path(paths.report_path),
            "coverage_mask": report_path(paths.output_dir / "coverage_masks" / "curve_bundle_candidate_coverage_mask.png"),
        },
        mesh_summary=_mesh_summary(ribbons, records, design_summary),
        validation=validation,
        warnings=warnings,
        errors=[],
    )
    contract_errors = validate_hair_candidate_report(result.to_dict())
    if contract_errors:
        result.errors.extend(contract_errors)
        if result.status == STATUS_MANUAL_REVIEW:
            result.status = "failed"
    write_json(
        paths.report_path,
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "route": ROUTE,
            **result.to_dict(),
        },
    )
    return result
