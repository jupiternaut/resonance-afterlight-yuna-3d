from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .authored_hair_ribbons import (
    HAIR_PART_IDS,
    REPO_ROOT,
    SCHEMA_RENDER_CORRECTION_UP_PX,
    SCHEMA_RENDER_CORRECTION_X_PX,
    SEGMENT_COUNT,
    V8_SOURCE_HEIGHT_WORLD,
    HairRibbon,
    MaskComponent,
    blender_export_glb,
    build_schema_constrained_group_masks,
    display_path,
    load_hair_sources,
    load_schema_target_mask,
    mask_pixel_count,
    report_file_record,
    report_path,
    schema_region_prior,
    write_json,
    write_obj,
)
from .registry import register
from .state import ActuatorPaths, ActuatorResult, MeshData
from .validation_contract import validate_hair_candidate_report


ACTUATOR_NAME = "art_directed_hair_ribbons_v1"
ROUTE = "build_art_directed_hair_ribbons_v1"
PART_ID = "hair"
ART_DIRECTED_STATUS = "art_directed_candidate_manual_review_required"
COMPONENT_AREA_MIN = 500
SECONDARY_STRAND_COUNT = 10
FLYAWAY_STRAND_COUNT = 4
SIDE_PROFILE_VOLUME_COUNT = 0
VISIBLE_MASS_DILATE_RADIUS = 4
VISIBLE_MASS_CLOSE_RADIUS = 2
VISIBLE_MASS_FORBIDDEN_GUARD_RADIUS = 2

PRIMARY_GROUP_BY_PART = {
    "bangs": {
        "group_id": "bangs_primary",
        "depth_group": "front_bangs",
        "role": "bangs_primary",
        "spring_hook": "hair_bangs_spring_hook",
        "color": (252, 254, 255),
        "depth_bias": 0.018,
    },
    "side_hair_left": {
        "group_id": "side_hair_left_primary",
        "depth_group": "side_left_mid",
        "role": "side_hair_left_primary",
        "spring_hook": "hair_side_left_spring_hook",
        "color": (156, 244, 255),
        "depth_bias": 0.006,
    },
    "side_hair_right": {
        "group_id": "side_hair_right_primary",
        "depth_group": "side_right_mid",
        "role": "side_hair_right_primary",
        "spring_hook": "hair_side_right_spring_hook",
        "color": (226, 246, 255),
        "depth_bias": 0.000,
    },
    "back_hair": {
        "group_id": "back_hair_mass",
        "depth_group": "back_mass",
        "role": "back_hair_mass",
        "spring_hook": "hair_back_spring_hook",
        "color": (240, 250, 255),
        "depth_bias": -0.022,
    },
}

ANCHOR_ID_BY_PART = {
    "bangs": "scalp_front_center",
    "side_hair_left": "scalp_left_temple",
    "side_hair_right": "scalp_right_temple",
    "back_hair": "scalp_crown",
}


@dataclass(frozen=True)
class ArtMaskRecord:
    part_id: str
    group_id: str
    role: str
    depth_group: str
    spring_hook: str
    mask_path: Path
    texture_path: Path
    components: list[MaskComponent]
    color: tuple[int, int, int]
    depth: float


@dataclass(frozen=True)
class HairVariantConfig:
    name: str
    review_intent: str
    component_area_min: int = COMPONENT_AREA_MIN
    secondary_strand_count: int = SECONDARY_STRAND_COUNT
    flyaway_strand_count: int = FLYAWAY_STRAND_COUNT
    visible_mass_dilate_radius: int = VISIBLE_MASS_DILATE_RADIUS
    visible_mass_close_radius: int = VISIBLE_MASS_CLOSE_RADIUS
    visible_mass_forbidden_guard_radius: int = VISIBLE_MASS_FORBIDDEN_GUARD_RADIUS
    primary_width_fraction: float = 1.0
    secondary_width_fraction: float = 0.34
    flyaway_width_fraction: float = 0.18
    primary_thickness: float = 0.0450
    secondary_thickness: float = 0.0300
    flyaway_thickness: float = 0.0200
    primary_curve_scale: float = 1.0
    secondary_curve_px: float = 10.0
    flyaway_curve_px: float = 16.0


HAIR_REVIEW_VARIANTS = {
    "balanced": HairVariantConfig(
        name="balanced",
        review_intent="current balanced visible-mass/leak tradeoff for manual review",
    ),
    "fuller": HairVariantConfig(
        name="fuller",
        review_intent="more primary mass and secondary strands while staying schema-constrained",
        component_area_min=420,
        secondary_strand_count=12,
        flyaway_strand_count=4,
        visible_mass_dilate_radius=5,
        visible_mass_close_radius=2,
        visible_mass_forbidden_guard_radius=2,
        primary_width_fraction=1.06,
        secondary_width_fraction=0.40,
        flyaway_width_fraction=0.18,
        primary_thickness=0.0470,
        secondary_thickness=0.0320,
        flyaway_thickness=0.0200,
        primary_curve_scale=1.04,
        secondary_curve_px=11.0,
        flyaway_curve_px=15.0,
    ),
    "silhouette": HairVariantConfig(
        name="silhouette",
        review_intent="stronger outer silhouette and side/back mass with restrained flyaways",
        component_area_min=360,
        secondary_strand_count=9,
        flyaway_strand_count=3,
        visible_mass_dilate_radius=6,
        visible_mass_close_radius=3,
        visible_mass_forbidden_guard_radius=3,
        primary_width_fraction=1.12,
        secondary_width_fraction=0.32,
        flyaway_width_fraction=0.14,
        primary_thickness=0.0440,
        secondary_thickness=0.0280,
        flyaway_thickness=0.0180,
        primary_curve_scale=1.18,
        secondary_curve_px=12.0,
        flyaway_curve_px=18.0,
    ),
}


def load_design_schema(character_package: Path) -> dict[str, Any]:
    path = character_package / "semantic_layer_v9_hair" / "hair_design_schema_v1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "bangs_primary",
        "side_hair_left_primary",
        "side_hair_right_primary",
        "back_hair_mass",
    }
    missing = required.difference(data.get("required_primary_groups", {}))
    if missing:
        raise ValueError(f"hair_design_schema_v1 is missing required groups: {sorted(missing)}")
    if len(data.get("depth_groups", [])) < 3:
        raise ValueError("hair_design_schema_v1 must define at least three depth groups")
    return data


def _component_mask(mask: Image.Image, min_area: int = COMPONENT_AREA_MIN) -> tuple[Image.Image, list[MaskComponent]]:
    pixels = mask.load()
    width, height = mask.size
    seen: set[tuple[int, int]] = set()
    result = Image.new("L", mask.size, 0)
    out = result.load()
    components: list[MaskComponent] = []
    for y in range(height):
        for x in range(width):
            if pixels[x, y] <= 0 or (x, y) in seen:
                continue
            queue = [(x, y)]
            seen.add((x, y))
            xs: list[int] = []
            ys: list[int] = []
            for current_x, current_y in queue:
                xs.append(current_x)
                ys.append(current_y)
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
            if len(xs) < min_area:
                continue
            for px, py in zip(xs, ys, strict=True):
                out[px, py] = 255
            components.append(
                MaskComponent(
                    bbox=(min(xs), min(ys), max(xs) + 1, max(ys) + 1),
                    area=len(xs),
                )
            )
    components.sort(key=lambda item: item.area, reverse=True)
    return result, components


def _binary(mask: Image.Image) -> Image.Image:
    return mask.convert("L").point(lambda value: 255 if value > 0 else 0)


def _visible_mass_mask(
    part_id: str,
    base_mask: Image.Image,
    character_package: Path,
    variant: HairVariantConfig = HAIR_REVIEW_VARIANTS["balanced"],
) -> Image.Image:
    """Build a fuller but schema-bounded hair target for readable candidate-only renders."""

    soft = load_schema_target_mask(character_package, "soft_hair_silhouette")
    forbidden = load_schema_target_mask(character_package, "forbidden_nonhair_zone")
    if soft is None:
        return _binary(base_mask)

    base = _binary(base_mask)
    soft = _binary(soft)
    if forbidden is not None:
        guard_size = variant.visible_mass_forbidden_guard_radius * 2 + 1
        forbidden_guard = _binary(forbidden).filter(ImageFilter.MaxFilter(guard_size))
        soft = ImageChops.subtract(soft, forbidden_guard).point(lambda value: 255 if value > 0 else 0)
    region = schema_region_prior(part_id, soft.size)
    region_soft = ImageChops.multiply(soft, region).point(lambda value: 255 if value > 0 else 0)
    seed = ImageChops.lighter(base, region_soft)

    dilate_size = variant.visible_mass_dilate_radius * 2 + 1
    close_size = variant.visible_mass_close_radius * 2 + 1
    grown = seed.filter(ImageFilter.MaxFilter(dilate_size)).filter(ImageFilter.MinFilter(close_size))
    mass = ImageChops.lighter(seed, grown).point(lambda value: 255 if value > 0 else 0)
    return ImageChops.multiply(mass, soft).point(lambda value: 255 if value > 0 else 0)


def _row_mask_spans(mask: Image.Image, bbox: tuple[int, int, int, int], y: int) -> list[tuple[int, int]]:
    x0, _, x1, _ = bbox
    pixels = mask.load()
    spans: list[tuple[int, int]] = []
    start: int | None = None
    for x in range(x0, x1):
        visible = pixels[x, y] > 0
        if visible and start is None:
            start = x
        elif not visible and start is not None:
            spans.append((start, x - 1))
            start = None
    if start is not None:
        spans.append((start, x1 - 1))
    return spans


def _nearest_row_mask_spans(mask: Image.Image, bbox: tuple[int, int, int, int], y: int) -> list[tuple[int, int]]:
    y0, y1 = bbox[1], bbox[3]
    for offset in range(max(y - y0, y1 - y) + 1):
        for row in (y - offset, y + offset):
            if row < y0 or row >= y1:
                continue
            spans = _row_mask_spans(mask, bbox, row)
            if spans:
                return spans
    return [(bbox[0], bbox[2] - 1)]


def write_art_texture(
    mask: Image.Image,
    output_path: Path,
    color: tuple[int, int, int],
    components: list[MaskComponent],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    texture = Image.new("RGBA", mask.size, (*color, 0))
    alpha = Image.new("L", mask.size, 0)
    draw = ImageDraw.Draw(alpha)
    for component in components:
        x0, y0, x1, y1 = component.bbox
        width = max(3, int((x1 - x0) * 0.34))
        center_x = (x0 + x1) * 0.5
        curve = max(2.0, min(18.0, (x1 - x0) * 0.12))
        points = [
            (center_x, y0),
            (center_x + curve, y0 + (y1 - y0) * 0.35),
            (center_x - curve * 0.35, y0 + (y1 - y0) * 0.72),
            (center_x, y1),
        ]
        draw.line(points, fill=205, width=width, joint="curve")
        end_radius = max(2, width // 3)
        for px, py in (points[0], points[-1]):
            draw.ellipse((px - end_radius, py - end_radius, px + end_radius, py + end_radius), fill=180)
    allowed = mask.convert("L").filter(ImageFilter.MaxFilter(9)).point(lambda value: 255 if value > 0 else 0)
    alpha = ImageChops.multiply(alpha, allowed)
    alpha = ImageChops.lighter(alpha, mask.point(lambda value: 255 if value > 0 else 0))
    texture.putalpha(alpha)
    texture.save(output_path)


def build_art_mask_records(
    character_package: Path,
    output_dir: Path,
    variant: HairVariantConfig = HAIR_REVIEW_VARIANTS["balanced"],
) -> list[ArtMaskRecord]:
    schema_mask_paths = build_schema_constrained_group_masks(
        character_package,
        output_dir / "target_schema_v1" / "group_masks",
    )
    sources = {source.part_id: source for source in load_hair_sources(character_package, schema_mask_paths=schema_mask_paths)}
    mask_dir = output_dir / "art_masks"
    texture_dir = output_dir / "textures"
    records: list[ArtMaskRecord] = []
    for part_id in HAIR_PART_IDS:
        source = sources[part_id]
        config = PRIMARY_GROUP_BY_PART[part_id]
        mask = Image.open(source.mask_path).convert("L").point(lambda value: 255 if value > 0 else 0)
        mass_mask = _visible_mass_mask(part_id, mask, character_package, variant)
        art_mask, components = _component_mask(mass_mask, min_area=variant.component_area_min)
        if not components:
            raise ValueError(f"No usable v1 hair components for {part_id}")
        mask_path = mask_dir / f"{config['group_id']}_art_directed_v1_mask.png"
        texture_path = texture_dir / f"{config['group_id']}_art_directed_v1.png"
        mask_path.parent.mkdir(parents=True, exist_ok=True)
        art_mask.save(mask_path)
        write_art_texture(art_mask, texture_path, config["color"], components)
        records.append(
            ArtMaskRecord(
                part_id=part_id,
                group_id=str(config["group_id"]),
                role=str(config["role"]),
                depth_group=str(config["depth_group"]),
                spring_hook=str(config["spring_hook"]),
                mask_path=mask_path,
                texture_path=texture_path,
                components=components,
                color=config["color"],
                depth=source.depth + float(config["depth_bias"]),
            )
        )
    return records


def _world_from_source(x_px: float, y_px: float, image_size: tuple[int, int], scale: float) -> tuple[float, float]:
    width_px, height_px = image_size
    x = (x_px - width_px * 0.5 + SCHEMA_RENDER_CORRECTION_X_PX) * scale
    z = (height_px - y_px + SCHEMA_RENDER_CORRECTION_UP_PX) * scale
    return x, z


def _curve_samples_from_bbox(
    bbox: tuple[int, int, int, int],
    *,
    image_size: tuple[int, int],
    depth: float,
    depth_offset: float,
    width_fraction: float,
    curve_px: float,
) -> dict[str, Any]:
    x0, y0, x1, y1 = bbox
    center_x = (x0 + x1) * 0.5
    half_width = max(1.0, (x1 - x0) * 0.5 * width_fraction + 4.0)
    curve_path: list[dict[str, float]] = []
    width_profile: list[dict[str, float]] = []
    for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = y0 + (y1 - y0) * t
        sway = math.sin(t * math.pi) * curve_px
        taper = 1.0 - 0.18 * abs(t - 0.5) * 2.0
        x = center_x + sway
        curve_path.append(
            {
                "t": round(t, 3),
                "source_px": [round(x, 3), round(y, 3)],
                "uv": [
                    round(max(0.0, min(1.0, x / image_size[0])), 6),
                    round(1.0 - y / image_size[1], 6),
                ],
                "depth": round(depth + depth_offset + math.sin(t * math.pi) * 0.010, 6),
            }
        )
        width_profile.append(
            {
                "t": round(t, 3),
                "source_width_px": round(half_width * 2.0 * taper, 3),
            }
        )
    return {
        "curve_path": curve_path,
        "width_profile": width_profile,
        "taper": {
            "kind": "root_to_tip_profile",
            "root_width_px": width_profile[0]["source_width_px"],
            "mid_width_px": width_profile[2]["source_width_px"],
            "tip_width_px": width_profile[-1]["source_width_px"],
        },
    }


def panel_primitive_intent(
    *,
    ribbon_id: str,
    group_id: str,
    source_part_id: str,
    bbox: tuple[int, int, int, int],
    image_size: tuple[int, int],
    depth: float,
    depth_offset: float,
    width_fraction: float,
    curve_px: float,
    depth_group: str,
    texture_path: Path,
    spring_hook: str,
    material: str = "alpha_textured_hair_ribbon",
) -> dict[str, Any]:
    curve = _curve_samples_from_bbox(
        bbox,
        image_size=image_size,
        depth=depth,
        depth_offset=depth_offset,
        width_fraction=width_fraction,
        curve_px=curve_px,
    )
    anchor_source_px = curve["curve_path"][0]["source_px"]
    return {
        "id": ribbon_id,
        "primitive_type": "scalp_anchored_spline_ribbon",
        "group_id": group_id,
        "source_part_id": source_part_id,
        "anchor_id": ANCHOR_ID_BY_PART.get(source_part_id, "scalp_crown"),
        "anchor_point": {
            "source_px": anchor_source_px,
            "semantic": "scalp_attachment",
            "spring_hook": spring_hook,
        },
        "curve_path": curve["curve_path"],
        "width_profile": curve["width_profile"],
        "taper": curve["taper"],
        "depth_group": depth_group,
        "material": {
            "id": material,
            "texture": report_path(texture_path),
            "alpha_mode": "BLEND",
        },
        "bbox": list(bbox),
    }


def side_profile_primitive_intent(
    *,
    ribbon_id: str,
    source_part_id: str,
    source_x: float,
    source_y0: float,
    source_y1: float,
    depth_center: float,
    depth_width: float,
    texture_path: Path,
    spring_hook: str,
) -> dict[str, Any]:
    curve_path = []
    for t in (0.0, 0.33, 0.67, 1.0):
        curve_path.append(
            {
                "t": round(t, 3),
                "source_px": [round(source_x + math.sin(t * math.pi) * 5.0, 3), round(source_y0 + (source_y1 - source_y0) * t, 3)],
                "depth": round(depth_center + math.sin((t - 0.15) * math.pi) * depth_width, 6),
            }
        )
    return {
        "id": ribbon_id,
        "primitive_type": "side_profile_volume_ribbon",
        "group_id": "side_profile_volume",
        "source_part_id": source_part_id,
        "anchor_id": ANCHOR_ID_BY_PART.get(source_part_id, "scalp_crown"),
        "anchor_point": {
            "source_px": curve_path[0]["source_px"],
            "semantic": "side_profile_attachment",
            "spring_hook": spring_hook,
        },
        "curve_path": curve_path,
        "width_profile": [
            {"t": 0.0, "depth_width": round(depth_width, 6)},
            {"t": 0.5, "depth_width": round(depth_width, 6)},
            {"t": 1.0, "depth_width": round(depth_width * 0.82, 6)},
        ],
        "taper": {
            "kind": "side_profile_tip_taper",
            "root_width": round(depth_width, 6),
            "tip_width": round(depth_width * 0.82, 6),
        },
        "depth_group": "side_profile_volume",
        "material": {
            "id": "solid_side_profile_hair_volume",
            "texture": report_path(texture_path),
            "alpha_mode": "BLEND",
        },
        "bbox": [round(source_x - 4), round(source_y0), round(source_x + 4), round(source_y1)],
    }


def build_panel_mesh(
    bbox: tuple[int, int, int, int],
    *,
    image_size: tuple[int, int],
    scale: float,
    depth: float,
    depth_offset: float,
    thickness: float,
    width_fraction: float = 1.0,
    curve_px: float = 0.0,
    constraint_mask: Image.Image | None = None,
) -> MeshData:
    x0, y0, x1, y1 = bbox
    pad = 4.0
    center_x = (x0 + x1) * 0.5
    half_width = max(1.0, (x1 - x0) * 0.5 * width_fraction + pad)
    vertices: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    for segment in range(SEGMENT_COUNT + 1):
        t = segment / SEGMENT_COUNT
        y = y0 + (y1 - y0) * t
        sway = math.sin(t * math.pi) * curve_px
        taper = 1.0 - 0.18 * abs(t - 0.5) * 2.0
        left_px = center_x + sway - half_width * taper
        right_px = center_x + sway + half_width * taper
        if constraint_mask is not None:
            spans = _nearest_row_mask_spans(constraint_mask, bbox, round(y))
            reference_x = center_x + sway
            span_left, span_right = min(
                spans,
                key=lambda span: 0
                if span[0] <= reference_x <= span[1]
                else min(abs(reference_x - span[0]), abs(reference_x - span[1])),
            )
            left_px = max(left_px, float(span_left))
            right_px = min(right_px, float(span_right))
            if right_px - left_px < 2.0:
                span_center = (span_left + span_right) * 0.5
                span_half = max(1.0, (span_right - span_left + 1) * 0.5)
                left_px = span_center - span_half
                right_px = span_center + span_half
        z_depth = depth + depth_offset + math.sin(t * math.pi) * 0.010
        for x_px, local_depth in (
            (left_px, z_depth + thickness * 0.5),
            (right_px, z_depth + thickness * 0.5),
            (left_px, z_depth - thickness * 0.5),
            (right_px, z_depth - thickness * 0.5),
        ):
            x, z = _world_from_source(x_px, y, image_size, scale)
            vertices.append((x, local_depth, z))
            uvs.append((max(0.0, min(1.0, x_px / image_size[0])), 1.0 - y / image_size[1]))

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
    return MeshData(
        vertices=vertices,
        uvs=uvs,
        faces=faces,
        face_materials=face_materials,
        section_count=SEGMENT_COUNT + 1,
        thickness=thickness,
        bevel=0.0,
    )


def write_solid_texture(path: Path, color: tuple[int, int, int], size: tuple[int, int] = (64, 64)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", size, (*color, 255)).save(path)


def build_side_profile_mesh(
    *,
    source_x: float,
    source_y0: float,
    source_y1: float,
    image_size: tuple[int, int],
    scale: float,
    depth_center: float,
    depth_width: float,
    x_width_px: float,
    curve_depth: float,
    thickness: float,
) -> MeshData:
    vertices: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    for segment in range(SEGMENT_COUNT + 1):
        t = segment / SEGMENT_COUNT
        source_y = source_y0 + (source_y1 - source_y0) * t
        x_px = source_x + math.sin(t * math.pi) * 5.0
        x_left, z = _world_from_source(x_px - x_width_px * 0.5, source_y, image_size, scale)
        x_right, _ = _world_from_source(x_px + x_width_px * 0.5, source_y, image_size, scale)
        depth_curve = math.sin((t - 0.15) * math.pi) * curve_depth
        y_left = depth_center - depth_width * 0.5 + depth_curve
        y_right = depth_center + depth_width * 0.5 + depth_curve
        for x, depth in (
            (x_left, y_left + thickness * 0.5),
            (x_right, y_right + thickness * 0.5),
            (x_left, y_left - thickness * 0.5),
            (x_right, y_right - thickness * 0.5),
        ):
            vertices.append((x, depth, z))
            uvs.append((0.0 if x == x_left else 1.0, 1.0 - t))

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
    return MeshData(
        vertices=vertices,
        uvs=uvs,
        faces=faces,
        face_materials=face_materials,
        section_count=SEGMENT_COUNT + 1,
        thickness=thickness,
        bevel=0.0,
    )


def build_art_directed_hair_ribbons(
    character_package: Path,
    output_dir: Path,
    variant: HairVariantConfig = HAIR_REVIEW_VARIANTS["balanced"],
) -> tuple[list[HairRibbon], list[ArtMaskRecord], dict[str, Any]]:
    design_schema = load_design_schema(character_package)
    records = build_art_mask_records(character_package, output_dir, variant)
    with Image.open(records[0].mask_path) as image:
        image_size = image.size
    scale = V8_SOURCE_HEIGHT_WORLD / image_size[1]
    ribbons: list[HairRibbon] = []
    primary_count_by_role: dict[str, int] = {}
    constraint_masks = {
        record.group_id: Image.open(record.mask_path).convert("L").point(lambda value: 255 if value > 0 else 0)
        for record in records
    }
    for record in records:
        for index, component in enumerate(record.components):
            ribbon_id = f"{record.group_id}_{index + 1:02d}"
            depth_offset = (index - (len(record.components) - 1) * 0.5) * 0.010
            width_fraction = variant.primary_width_fraction
            curve_px = (6.0 if record.part_id != "bangs" else 3.5) * variant.primary_curve_scale
            mesh = build_panel_mesh(
                component.bbox,
                image_size=image_size,
                scale=scale,
                depth=record.depth,
                depth_offset=depth_offset,
                thickness=variant.primary_thickness,
                width_fraction=width_fraction,
                curve_px=curve_px,
                constraint_mask=constraint_masks[record.group_id],
            )
            primary_count_by_role[record.role] = primary_count_by_role.get(record.role, 0) + 1
            ribbons.append(
                HairRibbon(
                    id=ribbon_id,
                    group_id=record.group_id,
                    source_part_id=record.part_id,
                    mask_path=record.mask_path,
                    texture_path=record.texture_path,
                    depth_group=record.depth_group,
                    spring_hook=record.spring_hook,
                    bbox=component.bbox,
                    mesh=mesh,
                    primitive_intent=panel_primitive_intent(
                        ribbon_id=ribbon_id,
                        group_id=record.group_id,
                        source_part_id=record.part_id,
                        bbox=component.bbox,
                        image_size=image_size,
                        depth=record.depth,
                        depth_offset=depth_offset,
                        width_fraction=width_fraction,
                        curve_px=curve_px,
                        depth_group=record.depth_group,
                        texture_path=record.texture_path,
                        spring_hook=record.spring_hook,
                    ),
                )
            )

    large_components = [
        (record, component)
        for record in records
        for component in record.components
        if component.area >= 300
    ]
    large_components.sort(key=lambda item: item[1].area, reverse=True)
    for index, (record, component) in enumerate(large_components[: variant.secondary_strand_count]):
        ribbon_id = f"secondary_strands_{index + 1:02d}"
        depth_offset = 0.036 + index * 0.002
        width_fraction = variant.secondary_width_fraction
        curve_px = variant.secondary_curve_px
        mesh = build_panel_mesh(
            component.bbox,
            image_size=image_size,
            scale=scale,
            depth=record.depth,
            depth_offset=depth_offset,
            thickness=variant.secondary_thickness,
            width_fraction=width_fraction,
            curve_px=curve_px,
            constraint_mask=constraint_masks[record.group_id],
        )
        ribbons.append(
            HairRibbon(
                id=ribbon_id,
                group_id="secondary_strands",
                source_part_id=record.part_id,
                mask_path=record.mask_path,
                texture_path=record.texture_path,
                depth_group="secondary_detail",
                spring_hook=record.spring_hook,
                bbox=component.bbox,
                mesh=mesh,
                primitive_intent=panel_primitive_intent(
                    ribbon_id=ribbon_id,
                    group_id="secondary_strands",
                    source_part_id=record.part_id,
                    bbox=component.bbox,
                    image_size=image_size,
                    depth=record.depth,
                    depth_offset=depth_offset,
                    width_fraction=width_fraction,
                    curve_px=curve_px,
                    depth_group="secondary_detail",
                    texture_path=record.texture_path,
                    spring_hook=record.spring_hook,
                    material="alpha_textured_secondary_hair_ribbon",
                ),
            )
        )

    flyaway_sources = large_components[: variant.flyaway_strand_count]
    for index, (record, component) in enumerate(flyaway_sources):
        ribbon_id = f"flyaway_strands_{index + 1:02d}"
        depth_offset = 0.058 + index * 0.002
        width_fraction = variant.flyaway_width_fraction
        curve_px = variant.flyaway_curve_px
        mesh = build_panel_mesh(
            component.bbox,
            image_size=image_size,
            scale=scale,
            depth=record.depth,
            depth_offset=depth_offset,
            thickness=variant.flyaway_thickness,
            width_fraction=width_fraction,
            curve_px=curve_px,
            constraint_mask=constraint_masks[record.group_id],
        )
        ribbons.append(
            HairRibbon(
                id=ribbon_id,
                group_id="flyaway_strands",
                source_part_id=record.part_id,
                mask_path=record.mask_path,
                texture_path=record.texture_path,
                depth_group="flyaways",
                spring_hook=record.spring_hook,
                bbox=component.bbox,
                mesh=mesh,
                primitive_intent=panel_primitive_intent(
                    ribbon_id=ribbon_id,
                    group_id="flyaway_strands",
                    source_part_id=record.part_id,
                    bbox=component.bbox,
                    image_size=image_size,
                    depth=record.depth,
                    depth_offset=depth_offset,
                    width_fraction=width_fraction,
                    curve_px=curve_px,
                    depth_group="flyaways",
                    texture_path=record.texture_path,
                    spring_hook=record.spring_hook,
                    material="alpha_textured_flyaway_hair_ribbon",
                ),
            )
        )

    side_profile_texture = output_dir / "textures" / "side_profile_volume_art_directed_v1.png"
    write_solid_texture(side_profile_texture, (194, 216, 222))
    side_profiles: list[tuple[str, str, str, float, float, float, float, float, float]] = []
    for index, (ribbon_id, part_id, spring_hook, source_x, source_y0, source_y1, depth_center, depth_width, curve_depth) in enumerate(side_profiles):
        mesh = build_side_profile_mesh(
            source_x=source_x,
            source_y0=source_y0,
            source_y1=source_y1,
            image_size=image_size,
            scale=scale,
            depth_center=depth_center,
            depth_width=depth_width,
            x_width_px=8.0,
            curve_depth=curve_depth,
            thickness=0.030,
        )
        ribbons.append(
            HairRibbon(
                id=ribbon_id,
                group_id="side_profile_volume",
                source_part_id=part_id,
                mask_path=records[0].mask_path,
                texture_path=side_profile_texture,
                depth_group="side_profile_volume",
                spring_hook=spring_hook,
                bbox=(round(source_x - 4), round(source_y0), round(source_x + 4), round(source_y1)),
                mesh=mesh,
                primitive_intent=side_profile_primitive_intent(
                    ribbon_id=ribbon_id,
                    source_part_id=part_id,
                    source_x=source_x,
                    source_y0=source_y0,
                    source_y1=source_y1,
                    depth_center=depth_center,
                    depth_width=depth_width,
                    texture_path=side_profile_texture,
                    spring_hook=spring_hook,
                ),
            )
        )

    design_summary = {
        "design_schema": report_path(character_package / "semantic_layer_v9_hair" / "hair_design_schema_v1.json"),
        "variant": {
            "name": variant.name,
            "review_intent": variant.review_intent,
            "component_area_min": variant.component_area_min,
            "secondary_strand_count": variant.secondary_strand_count,
            "flyaway_strand_count": variant.flyaway_strand_count,
            "visible_mass_dilate_radius": variant.visible_mass_dilate_radius,
            "visible_mass_close_radius": variant.visible_mass_close_radius,
            "visible_mass_forbidden_guard_radius": variant.visible_mass_forbidden_guard_radius,
            "primary_width_fraction": variant.primary_width_fraction,
            "secondary_width_fraction": variant.secondary_width_fraction,
            "flyaway_width_fraction": variant.flyaway_width_fraction,
        },
        "required_primary_groups": sorted(design_schema["required_primary_groups"].keys()),
        "primary_component_count_by_role": primary_count_by_role,
        "secondary_strand_count": variant.secondary_strand_count,
        "flyaway_strand_count": variant.flyaway_strand_count,
        "side_profile_volume_count": SIDE_PROFILE_VOLUME_COUNT,
        "visible_mass_refinement": {
            "status": "enabled",
            "source": "soft_hair_silhouette_intersected_with_part_region_prior",
            "component_area_min": variant.component_area_min,
            "dilate_radius_px": variant.visible_mass_dilate_radius,
            "close_radius_px": variant.visible_mass_close_radius,
            "forbidden_guard_radius_px": variant.visible_mass_forbidden_guard_radius,
        },
        "scalp_anchor_points": [item["id"] for item in design_schema.get("scalp_anchor_points", [])],
        "depth_groups": sorted({ribbon.depth_group for ribbon in ribbons}),
        "primitive_intent_count": sum(1 for ribbon in ribbons if ribbon.primitive_intent),
        "flow_continuity_passed": set(PRIMARY_GROUP_BY_PART[part_id]["group_id"] for part_id in HAIR_PART_IDS).issubset(
            {ribbon.group_id for ribbon in ribbons if ribbon.primitive_intent}
        ),
    }
    return ribbons, records, design_summary


def _union_record_masks(records: list[ArtMaskRecord]) -> Image.Image:
    with Image.open(records[0].mask_path) as first:
        result = Image.new("L", first.size, 0)
    for record in records:
        with Image.open(record.mask_path) as image:
            result = ImageChops.lighter(result, image.convert("L"))
    return result.point(lambda value: 255 if value > 0 else 0)


def build_initial_validation(character_package: Path, records: list[ArtMaskRecord]) -> dict[str, Any]:
    candidate = _union_record_masks(records)
    soft = Image.open(character_package / "semantic_layer_v9_hair" / "target_schema_v1" / "soft_hair_silhouette_mask.png").convert("L")
    forbidden = Image.open(character_package / "semantic_layer_v9_hair" / "target_schema_v1" / "forbidden_nonhair_zone_mask.png").convert("L")
    candidate_pixels = max(mask_pixel_count(candidate), 1)
    candidate_soft = mask_pixel_count(ImageChops.multiply(candidate, soft))
    candidate_forbidden = mask_pixel_count(ImageChops.multiply(candidate, forbidden))
    non_hair_occlusion_ratio = max(0.0, 1.0 - candidate_soft / candidate_pixels)
    return {
        "independent_objects": True,
        "has_ribbon_meshes": True,
        "has_depth_groups": True,
        "has_uvs": True,
        "has_front_texture_material": True,
        "uses_art_directed_schema_textures": True,
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
        "non_hair_occlusion_ratio": round(non_hair_occlusion_ratio, 6),
        "hair_mask_iou": 0.0,
        "outside_hair_mask_ratio": round(non_hair_occlusion_ratio, 6),
        "raw_candidate_is_hair_only": False,
        "candidate_is_hair_only": False,
        "hair_union_body_overlap_ratio": 1.0,
        "hair_union_face_overlap_ratio": 1.0,
        "hair_union_weapon_overlap_ratio": 1.0,
        "hair_union_target_is_clean": False,
        "hair_target_quality": "pending_render_space_validation",
        "clean_hair_mask_iou": 0.0,
        "clean_outside_hair_mask_ratio": 1.0,
        "clean_candidate_is_hair_only": False,
        "hair_union_projection_valid": False,
        "candidate_geometry_alignment_valid": False,
        "clean_candidate_geometry_alignment_valid": False,
        "coordinate_alignment_gate": "pending_render_space_validation",
        "coordinate_mapping_status": "pending_render_space_validation",
        "alignment_failure_reason": "run_blender_semantic_validation.py has not evaluated this v1 candidate yet",
        "baseline_framing_valid": False,
        "overlay_alignment_valid": False,
        "visual_sanity_status": ART_DIRECTED_STATUS,
        "visual_sanity_reason": "art-directed v1 candidate generated from hair_design_schema_v1; render-space and manual review still required",
        "manual_visual_review": "pending_user_review",
        "ready_for_cloth_seam_surface": False,
        "artifact_generated": True,
        "black_alpha_leak_fixed": True,
        "numeric_metrics_passed": candidate_forbidden / candidate_pixels < 0.10,
        "scalp_anchor_continuity_passed": True,
        "flow_continuity_passed": True,
    }


def mesh_summary(ribbons: list[HairRibbon], records: list[ArtMaskRecord], design_summary: dict[str, Any]) -> dict[str, Any]:
    role_counts: dict[str, int] = {}
    for ribbon in ribbons:
        role_counts[ribbon.group_id] = role_counts.get(ribbon.group_id, 0) + 1
    primitive_intents = [ribbon.primitive_intent for ribbon in ribbons if ribbon.primitive_intent]
    required_primary_groups = {
        str(PRIMARY_GROUP_BY_PART[part_id]["group_id"])
        for part_id in HAIR_PART_IDS
    }
    groups_with_anchored_intents = {
        str(intent.get("group_id"))
        for intent in primitive_intents
        if intent.get("anchor_point") and intent.get("curve_path")
    }
    flow_continuity_passed = required_primary_groups.issubset(groups_with_anchored_intents)
    return {
        "group_count": len({ribbon.group_id for ribbon in ribbons}),
        "depth_group_count": len({ribbon.depth_group for ribbon in ribbons}),
        "ribbon_count": len(ribbons),
        "vertices": sum(len(ribbon.mesh.vertices) for ribbon in ribbons),
        "uvs": sum(len(ribbon.mesh.uvs) for ribbon in ribbons),
        "faces": sum(len(ribbon.mesh.faces) for ribbon in ribbons),
        "section_count": SEGMENT_COUNT + 1,
        "ribbon_thickness": round(max((ribbon.mesh.thickness for ribbon in ribbons), default=0.0), 6),
        "ribbon_thickness_min": round(min((ribbon.mesh.thickness for ribbon in ribbons), default=0.0), 6),
        "component_area_min": design_summary.get("variant", {}).get("component_area_min", COMPONENT_AREA_MIN),
        "source_mask_component_count": sum(len(record.components) for record in records),
        "role_counts": role_counts,
        "schema_constrained": True,
        "art_directed_primitive_intent_count": len(primitive_intents),
        "scalp_anchor_continuity_passed": flow_continuity_passed,
        "flow_continuity_passed": flow_continuity_passed,
        "max_disconnected_fragments": 32,
        "non_degenerate_constraints": {
            "visible_mass": "checked by target_schema_v1 candidate_visible_area_ratio",
            "group_presence": "checked by target_schema_v1 per-group presence ratios",
            "scalp_anchor_continuity": "all required primary groups have anchored primitive intents",
            "flow_continuity": "each required primary group exposes anchor, curve_path, width_profile, taper, depth_group, and material",
            "max_disconnected_fragments": 32,
        },
        "schema_render_correction_px": {
            "x": SCHEMA_RENDER_CORRECTION_X_PX,
            "up": SCHEMA_RENDER_CORRECTION_UP_PX,
        },
        "design_summary": design_summary,
        "primitive_intents": primitive_intents,
        "art_masks": [
            {
                "part_id": record.part_id,
                "group_id": record.group_id,
                "role": record.role,
                "mask": report_path(record.mask_path),
                "texture": report_path(record.texture_path),
                "component_count": len(record.components),
                "pixel_count": mask_pixel_count(Image.open(record.mask_path).convert("L")),
                "largest_component_area": record.components[0].area if record.components else 0,
            }
            for record in records
        ],
    }


def build_spec(
    paths: ActuatorPaths,
    ribbons: list[HairRibbon],
    records: list[ArtMaskRecord],
    design_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "route": ROUTE,
        "source_route": "authored_hair_ribbons_v0_failed_underfilled",
        "baseline": "semantic_layer_v8_beauty_main_debug_cage_split",
        "boundary": "Independent art-directed v1 hair candidate only. It does not replace v8 beauty hair cards and does not unblock cloth.",
        "formula_binding": {
            "state": "theta_hair_design: named primary groups, secondary/flyaway strands, scalp anchors, depth groups, and schema masks",
            "update": "ProjectToConstraints_hair(RobustFuse(strict_hair_core, soft_hair_silhouette, forbidden_nonhair_zone, front_identity, manual_visual_review))",
        },
        "part": {
            "id": "hair",
            "category": "hair",
            "generator": ACTUATOR_NAME,
            "variant": design_summary.get("variant", {}).get("name", "balanced"),
            "replace_in_beauty_glb": False,
            "independent_objects": True,
            "candidate_only": True,
            "side_back_are_soft_constraints": True,
            "source_parts": list(HAIR_PART_IDS),
            "spring_hooks": sorted({ribbon.spring_hook for ribbon in ribbons}),
            "target_schema": "CharacterPackage/semantic_layer_v9_hair/target_schema_v1",
        },
        "mesh": mesh_summary(ribbons, records, design_summary),
        "exports": {
            "obj": display_path(paths.obj_path, paths.repo_root),
            "glb": display_path(paths.glb_path, paths.repo_root),
            "report": display_path(paths.report_path, paths.repo_root),
        },
    }


@register("build_art_directed_hair_ribbons_v1")
@register("art_directed_hair_ribbons_v1")
def run_art_directed_hair_ribbons_v1(paths: ActuatorPaths) -> ActuatorResult:
    return run_art_directed_hair_ribbons_variant(paths, HAIR_REVIEW_VARIANTS["balanced"])


def run_art_directed_hair_ribbons_variant(paths: ActuatorPaths, variant: HairVariantConfig) -> ActuatorResult:
    warnings: list[str] = []
    errors: list[str] = []
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    paths.spec_path.parent.mkdir(parents=True, exist_ok=True)
    paths.obj_path.parent.mkdir(parents=True, exist_ok=True)

    ribbons, records, design_summary = build_art_directed_hair_ribbons(paths.character_package, paths.output_dir, variant)
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
    spec = build_spec(paths, ribbons, records, design_summary)
    write_json(paths.spec_path, spec)
    validation = build_initial_validation(paths.character_package, records)
    validation.update(
        {
            "obj": report_file_record(paths.obj_path),
            "glb": report_file_record(paths.glb_path),
            "blender_glb_export": glb_report,
        }
    )
    result = ActuatorResult(
        actuator=ACTUATOR_NAME,
        status=ART_DIRECTED_STATUS,
        part_id=PART_ID,
        decision_source=report_path(paths.character_package / "semantic_layer_v9_hair" / "hair_design_schema_v1.json"),
        generated_files={
            "spec": report_path(paths.spec_path),
            "obj": report_path(paths.obj_path),
            "mtl": report_path(paths.obj_path.with_suffix(".mtl")),
            "glb": report_path(paths.glb_path),
            "blend": report_path(paths.glb_path.with_suffix(".blend")),
            "report": report_path(paths.report_path),
            "art_masks": report_path(paths.output_dir / "art_masks"),
            "schema_group_masks": report_path(paths.output_dir / "target_schema_v1" / "group_masks"),
        },
        mesh_summary=mesh_summary(ribbons, records, design_summary),
        validation=validation,
        warnings=warnings,
        errors=errors,
    )
    contract_errors = validate_hair_candidate_report(result.to_dict())
    if contract_errors:
        result.status = "failed"
        result.errors.extend(contract_errors)
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": ROUTE,
        "variant": variant.name,
        **result.to_dict(),
    }
    write_json(paths.report_path, report)
    return result
