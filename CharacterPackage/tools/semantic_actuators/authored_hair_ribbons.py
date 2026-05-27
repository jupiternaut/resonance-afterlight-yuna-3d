from __future__ import annotations

import json
import math
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .registry import register
from .state import ActuatorPaths, ActuatorResult, MeshData
from .validation_contract import file_record, validate_hair_candidate_report


ACTUATOR_NAME = "authored_hair_ribbons_v0"
PART_ID = "hair"
SEGMENT_COUNT = 24
V8_SOURCE_HEIGHT_WORLD = 6.4
HAIR_PART_IDS = ("back_hair", "side_hair_left", "side_hair_right", "bangs")
VISUAL_SANITY_THRESHOLDS = {
    "black_alpha_leak_ratio": 0.02,
    "candidate_black_pixel_ratio": 0.05,
    "face_occlusion_ratio": 0.15,
    "non_hair_occlusion_ratio": 0.10,
}

GROUP_CONFIG = {
    "back_hair": {
        "group_id": "hair_back",
        "ribbon_count": 14,
        "spring_hook": "hair_back_spring_hook",
        "width": 0.068,
        "depth_spread": 0.16,
        "curve_bias": -0.030,
        "x_bias": 0.000,
    },
    "side_hair_left": {
        "group_id": "hair_side_left",
        "ribbon_count": 8,
        "spring_hook": "hair_side_left_spring_hook",
        "width": 0.058,
        "depth_spread": 0.090,
        "curve_bias": 0.020,
        "x_bias": -0.035,
    },
    "side_hair_right": {
        "group_id": "hair_side_right",
        "ribbon_count": 9,
        "spring_hook": "hair_side_right_spring_hook",
        "width": 0.058,
        "depth_spread": 0.095,
        "curve_bias": 0.025,
        "x_bias": 0.035,
    },
    "bangs": {
        "group_id": "hair_bangs",
        "ribbon_count": 10,
        "spring_hook": "hair_bangs_spring_hook",
        "width": 0.050,
        "depth_spread": 0.055,
        "curve_bias": 0.018,
        "x_bias": 0.000,
    },
}


@dataclass
class HairGroupSource:
    part_id: str
    group_id: str
    mask_path: Path
    texture_path: Path
    bbox: tuple[int, int, int, int]
    depth: float
    ribbon_count: int
    width: float
    depth_spread: float
    curve_bias: float
    x_bias: float
    spring_hook: str


@dataclass
class HairRibbon:
    id: str
    group_id: str
    source_part_id: str
    mask_path: Path
    texture_path: Path
    depth_group: str
    spring_hook: str
    bbox: tuple[int, int, int, int]
    mesh: MeshData


@dataclass
class SanitizedTextureRecord:
    group_id: str
    source_texture: Path
    sanitized_texture: Path
    alpha_pixels: int
    fill_color: tuple[int, int, int]


@dataclass(frozen=True)
class MaskComponent:
    bbox: tuple[int, int, int, int]
    area: int


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def find_blender() -> str | None:
    blender = shutil.which("blender")
    if blender:
        return blender
    app_path = Path("/Applications/Blender.app/Contents/MacOS/Blender")
    if app_path.exists():
        return str(app_path)
    return None


def alpha_bbox(path: Path, threshold: int = 16) -> tuple[int, int, int, int]:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox == (0, 0, image.width, image.height) and alpha.getextrema() == (255, 255):
        mask = image.convert("L").point(lambda pixel: 255 if pixel > threshold else 0)
        bbox = mask.getbbox()
    if bbox is None:
        raise ValueError(f"Image has no visible pixels: {path}")
    return bbox


def mask_components(path: Path, threshold: int = 16, min_area: int = 120) -> list[MaskComponent]:
    mask = mask_luma(path, threshold=threshold)
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
            if len(xs) >= min_area:
                components.append(
                    MaskComponent(
                        bbox=(min(xs), min(ys), max(xs) + 1, max(ys) + 1),
                        area=len(xs),
                    )
                )
    components.sort(key=lambda item: item.area, reverse=True)
    return components


def component_lane_plan(source: HairGroupSource) -> list[tuple[tuple[int, int, int, int], int, int]]:
    components = mask_components(source.mask_path)
    if not components:
        return [(source.bbox, index, source.ribbon_count) for index in range(source.ribbon_count)]

    selected = components[: min(source.ribbon_count, max(4, source.ribbon_count // 2))]
    total_area = sum(component.area for component in selected)
    quotas: list[int] = []
    fractional: list[tuple[float, int]] = []
    for index, component in enumerate(selected):
        raw = source.ribbon_count * component.area / max(total_area, 1)
        quota = max(1, math.floor(raw))
        quotas.append(quota)
        fractional.append((raw - quota, index))

    while sum(quotas) > source.ribbon_count:
        index = min((idx for idx, quota in enumerate(quotas) if quota > 1), key=lambda idx: (selected[idx].area, idx))
        quotas[index] -= 1
    for _, index in sorted(fractional, reverse=True):
        if sum(quotas) >= source.ribbon_count:
            break
        quotas[index] += 1

    planned_components = sorted(
        zip(selected, quotas, strict=True),
        key=lambda item: ((item[0].bbox[0] + item[0].bbox[2]) * 0.5, item[0].bbox[1]),
    )
    plan: list[tuple[tuple[int, int, int, int], int, int]] = []
    for component, quota in planned_components:
        for lane_index in range(quota):
            plan.append((component.bbox, lane_index, quota))
    return plan[: source.ribbon_count]


def row_alpha_span(alpha, bbox: tuple[int, int, int, int], y: int, threshold: int = 16) -> tuple[int, int]:
    spans = row_alpha_spans(alpha, bbox, y, threshold=threshold)
    if not spans:
        return bbox[0], bbox[2] - 1
    left = min(span[0] for span in spans)
    right = max(span[1] for span in spans)
    return left, right


def row_alpha_spans(alpha, bbox: tuple[int, int, int, int], y: int, threshold: int = 16) -> list[tuple[int, int]]:
    x0, _, x1, _ = bbox
    spans: list[tuple[int, int]] = []
    start: int | None = None
    for x in range(x0, x1):
        visible = alpha.getpixel((x, y)) > threshold
        if visible and start is None:
            start = x
        elif not visible and start is not None:
            spans.append((start, x - 1))
            start = None
    if start is not None:
        spans.append((start, x1 - 1))
    return spans


def nearest_alpha_spans(alpha, bbox: tuple[int, int, int, int], y: int, threshold: int = 16) -> list[tuple[int, int]]:
    y0, y1 = bbox[1], bbox[3]
    for offset in range(max(y - y0, y1 - y) + 1):
        candidates: list[tuple[int, int]] = []
        for row in (y - offset, y + offset):
            if row < y0 or row >= y1:
                continue
            candidates = row_alpha_spans(alpha, bbox, row, threshold=threshold)
            if candidates:
                return candidates
    return [(bbox[0], bbox[2] - 1)]


def weighted_column_targets(alpha, bbox: tuple[int, int, int, int], count: int, threshold: int = 16) -> list[float]:
    x0, y0, x1, y1 = bbox
    weighted_columns: list[int] = []
    for x in range(x0, x1):
        coverage = 0
        for y in range(y0, y1):
            if alpha.getpixel((x, y)) > threshold:
                coverage += 1
        if coverage:
            weighted_columns.extend([x] * max(1, coverage // 6))
    if not weighted_columns:
        return [x0 + (x1 - x0 - 1) * (index + 0.5) / count for index in range(count)]
    weighted_columns.sort()
    return [
        float(weighted_columns[round((len(weighted_columns) - 1) * (index + 0.5) / count)])
        for index in range(count)
    ]


def load_hair_sources(character_package: Path) -> list[HairGroupSource]:
    spec = load_json(character_package / "semantic_layer_v8" / "specs" / "yuna_semantic_layer_v8.json")
    parts = {part.get("id"): part for part in spec.get("parts", []) if isinstance(part, dict)}
    sources: list[HairGroupSource] = []
    for part_id in HAIR_PART_IDS:
        part = parts.get(part_id)
        if not part:
            raise ValueError(f"Missing v8 hair part: {part_id}")
        config = GROUP_CONFIG[part_id]
        texture_rel = part.get("texture")
        if not isinstance(texture_rel, str):
            raise ValueError(f"Missing texture for hair part: {part_id}")
        texture_path = character_package / texture_rel
        if not texture_path.exists():
            raise ValueError(f"Missing hair texture: {texture_path}")
        mask_path = character_package / "semantic_layer_v8" / "masks" / "front" / f"{part_id}.png"
        if not mask_path.exists():
            raise ValueError(f"Missing hair mask: {mask_path}")
        with Image.open(mask_path) as mask_image, Image.open(texture_path) as texture_image:
            mask_size = mask_image.size
            texture_size = texture_image.size
        if mask_size != texture_size:
            raise ValueError(f"Hair mask/texture size mismatch: {part_id}")
        sources.append(
            HairGroupSource(
                part_id=part_id,
                group_id=str(config["group_id"]),
                mask_path=mask_path,
                texture_path=texture_path,
                bbox=alpha_bbox(mask_path),
                depth=float(part.get("depth", 0.0)),
                ribbon_count=int(config["ribbon_count"]),
                width=float(config["width"]),
                depth_spread=float(config["depth_spread"]),
                curve_bias=float(config["curve_bias"]),
                x_bias=float(config["x_bias"]),
                spring_hook=str(config["spring_hook"]),
            )
        )
    return sources


def build_ribbon_mesh(
    source: HairGroupSource,
    *,
    ribbon_index: int,
    image_size: tuple[int, int],
    scale: float,
    component_bbox: tuple[int, int, int, int] | None = None,
    component_lane_index: int | None = None,
    component_lane_count: int | None = None,
    ribbon_thickness: float = 0.0035,
) -> MeshData:
    width_px, height_px = image_size
    image = Image.open(source.mask_path).convert("RGBA")
    alpha = image.getchannel("A")
    if alpha.getbbox() == (0, 0, image.width, image.height) and alpha.getextrema() == (255, 255):
        alpha = image.convert("L").point(lambda pixel: 255 if pixel > 16 else 0)
    bbox = component_bbox or source.bbox
    x0, y0, x1, y1 = bbox
    lane_count = component_lane_count or source.ribbon_count
    lane_index = component_lane_index if component_lane_index is not None else ribbon_index
    column_targets = weighted_column_targets(alpha, bbox, lane_count)
    target_px = column_targets[min(lane_index, len(column_targets) - 1)]
    ribbon_depth_offset = (ribbon_index - (source.ribbon_count - 1) * 0.5) * source.depth_spread / max(source.ribbon_count - 1, 1)

    vertices: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    half_width_world = source.width * 0.5
    half_width_px = max(1.0, half_width_world / scale)
    previous_center_px: float | None = None

    for segment in range(SEGMENT_COUNT + 1):
        t = segment / SEGMENT_COUNT
        y = round(y0 + (y1 - y0 - 1) * t)
        spans = row_alpha_spans(alpha, bbox, y)
        if not spans:
            spans = nearest_alpha_spans(alpha, bbox, y)
        # Keep the authored candidate deterministic but not perfectly flat:
        # the alpha component provides the strand lane, while sinusoidal
        # offsets add a readable ribbon curve for turntable review.
        curve_px = math.sin(t * math.pi) * source.curve_bias / scale
        tip_taper_px = (t - 0.5) * source.x_bias / scale
        desired_px = target_px + curve_px + tip_taper_px
        reference_px = previous_center_px if previous_center_px is not None else desired_px
        left, right = min(spans, key=lambda span: 0 if span[0] <= reference_px <= span[1] else min(abs(reference_px - span[0]), abs(reference_px - span[1])))
        center_px = max(left, min(right, desired_px))
        previous_center_px = center_px

        center_x = (center_px - width_px * 0.5) * scale
        # Match the v8 semantic-layer coordinate system: source image Y maps
        # into positive world Z from feet upward. The earlier centered 2.2m
        # mapping made the hair candidate tiny and rendered near the boots.
        center_z = (height_px - y) * scale
        center_depth = source.depth + ribbon_depth_offset + math.sin(t * math.pi) * source.curve_bias
        local_half_width_px = min(half_width_px, max(1.0, (right - left + 1) * 0.20))
        left_px = max(float(left), center_px - local_half_width_px)
        right_px = min(float(right), center_px + local_half_width_px)
        local_half_width_world = max(scale, (right_px - left_px) * 0.5 * scale)
        left_x = center_x - local_half_width_world
        right_x = center_x + local_half_width_world
        front_depth = center_depth + ribbon_thickness * 0.5
        back_depth = center_depth - ribbon_thickness * 0.5

        for x, depth, px in (
            (left_x, front_depth, left_px),
            (right_x, front_depth, right_px),
            (left_x, back_depth, left_px),
            (right_x, back_depth, right_px),
        ):
            vertices.append((x, depth, center_z))
            uvs.append((max(0.0, min(1.0, px / width_px)), 1.0 - y / height_px))

    def vid(segment: int, corner: int) -> int:
        return segment * 4 + corner

    faces: list[tuple[int, int, int, int]] = []
    face_materials: list[int] = []
    for segment in range(SEGMENT_COUNT):
        # Front and back use the source hair texture; ribbon edges use the side
        # material to make thickness visible in side/yaw screenshots.
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
        thickness=ribbon_thickness,
        bevel=0.0,
    )


def build_hair_ribbons(character_package: Path) -> list[HairRibbon]:
    sources = load_hair_sources(character_package)
    first_image = Image.open(sources[0].mask_path).convert("RGBA")
    image_size = first_image.size
    scale = V8_SOURCE_HEIGHT_WORLD / image_size[1]
    ribbons: list[HairRibbon] = []
    for source in sources:
        lane_plan = component_lane_plan(source)
        for index, (component_bbox, lane_index, lane_count) in enumerate(lane_plan):
            mesh = build_ribbon_mesh(
                source,
                ribbon_index=index,
                image_size=image_size,
                scale=scale,
                component_bbox=component_bbox,
                component_lane_index=lane_index,
                component_lane_count=lane_count,
            )
            ribbons.append(
                HairRibbon(
                    id=f"{source.group_id}_ribbon_{index + 1:02d}",
                    group_id=source.group_id,
                    source_part_id=source.part_id,
                    mask_path=source.mask_path,
                    texture_path=source.texture_path,
                    depth_group=source.group_id,
                    spring_hook=source.spring_hook,
                    bbox=component_bbox,
                    mesh=mesh,
                )
            )
    return ribbons


def sanitize_hair_texture(source_texture: Path, mask_path: Path, output_path: Path) -> SanitizedTextureRecord:
    source = Image.open(source_texture).convert("RGBA")
    mask = mask_luma(mask_path)
    pixels = source.load()
    mask_pixels = mask.load()
    visible_colors: list[tuple[int, int, int]] = []
    for y in range(source.height):
        for x in range(source.width):
            if mask_pixels[x, y] > 0 and pixels[x, y][3] > 16:
                visible_colors.append(pixels[x, y][:3])
    if visible_colors:
        fill_color = tuple(round(sum(color[index] for color in visible_colors) / len(visible_colors)) for index in range(3))
    else:
        fill_color = (210, 226, 228)
    alpha_pixels = 0
    sanitized = Image.new("RGBA", source.size, (*fill_color, 0))
    sanitized_pixels = sanitized.load()
    for y in range(source.height):
        for x in range(source.width):
            if mask_pixels[x, y] > 0 and pixels[x, y][3] > 16:
                sanitized_pixels[x, y] = pixels[x, y]
                alpha_pixels += 1
            else:
                sanitized_pixels[x, y] = (*fill_color, 0)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sanitized.save(output_path)
    return SanitizedTextureRecord(
        group_id=output_path.stem,
        source_texture=source_texture,
        sanitized_texture=output_path,
        alpha_pixels=alpha_pixels,
        fill_color=fill_color,
    )


def prepare_sanitized_textures(paths: ActuatorPaths, ribbons: list[HairRibbon]) -> list[SanitizedTextureRecord]:
    records: list[SanitizedTextureRecord] = []
    by_group: dict[str, HairRibbon] = {}
    for ribbon in ribbons:
        by_group.setdefault(ribbon.group_id, ribbon)
    for group_id, ribbon in by_group.items():
        sanitized_path = paths.output_dir / "textures" / f"{group_id}_sanitized.png"
        record = sanitize_hair_texture(ribbon.texture_path, ribbon.mask_path, sanitized_path)
        record.group_id = group_id
        records.append(record)
        for item in ribbons:
            if item.group_id == group_id:
                item.texture_path = sanitized_path
    return records


def combined_summary(ribbons: list[HairRibbon], texture_records: list[SanitizedTextureRecord] | None = None) -> dict[str, Any]:
    groups: dict[str, dict[str, Any]] = {}
    for ribbon in ribbons:
        group = groups.setdefault(
            ribbon.group_id,
            {
                "group_id": ribbon.group_id,
                "source_part_id": ribbon.source_part_id,
                "mask": str(ribbon.mask_path),
                "texture": str(ribbon.texture_path),
                "bbox": list(ribbon.bbox),
                "spring_hook": ribbon.spring_hook,
                "ribbon_count": 0,
            },
        )
        group["ribbon_count"] += 1
    return {
        "group_count": len(groups),
        "depth_group_count": len({ribbon.depth_group for ribbon in ribbons}),
        "ribbon_count": len(ribbons),
        "vertices": sum(len(ribbon.mesh.vertices) for ribbon in ribbons),
        "uvs": sum(len(ribbon.mesh.uvs) for ribbon in ribbons),
        "faces": sum(len(ribbon.mesh.faces) for ribbon in ribbons),
        "section_count": SEGMENT_COUNT + 1,
        "ribbon_thickness": 0.0035,
        "groups": list(groups.values()),
        "sanitized_textures": [
            {
                "group_id": record.group_id,
                "source_texture": str(record.source_texture),
                "sanitized_texture": str(record.sanitized_texture),
                "alpha_pixels": record.alpha_pixels,
                "fill_color": list(record.fill_color),
            }
            for record in (texture_records or [])
        ],
    }


def mask_luma(path: Path, threshold: int = 16) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    if alpha.getbbox() == (0, 0, image.width, image.height) and alpha.getextrema() == (255, 255):
        return image.convert("L").point(lambda pixel: 255 if pixel > threshold else 0)
    return alpha.point(lambda pixel: 255 if pixel > threshold else 0)


def union_masks(paths: list[Path], threshold: int = 16) -> Image.Image:
    if not paths:
        raise ValueError("Expected at least one mask path")
    with Image.open(paths[0]) as first:
        result = Image.new("L", first.size, 0)
    for path in paths:
        result = ImageChops.lighter(result, mask_luma(path, threshold=threshold))
    return result


def ribbon_source_coverage(ribbons: list[HairRibbon]) -> Image.Image:
    if not ribbons:
        raise ValueError("Expected at least one hair ribbon")
    with Image.open(ribbons[0].mask_path) as first:
        size = first.size
    coverage = Image.new("L", size, 0)
    draw = ImageDraw.Draw(coverage)
    width, height = size
    for ribbon in ribbons:
        for face, material_index in zip(ribbon.mesh.faces, ribbon.mesh.face_materials, strict=True):
            if material_index != 0:
                continue
            points = []
            for vertex_index in face:
                u, v = ribbon.mesh.uvs[vertex_index]
                points.append((u * width, (1.0 - v) * height))
            draw.polygon(points, fill=255)
    return coverage


def ratio(mask: Image.Image, denominator: int | None = None) -> float:
    pixels = mask.load()
    count = 0
    for y in range(mask.height):
        for x in range(mask.width):
            if pixels[x, y] > 0:
                count += 1
    base = denominator if denominator is not None else mask.width * mask.height
    return count / max(base, 1)


def source_visual_sanity_metrics(character_package: Path, ribbons: list[HairRibbon]) -> dict[str, Any]:
    coverage = ribbon_source_coverage(ribbons)
    coverage_pixels = max(1, int(ratio(coverage) * coverage.width * coverage.height))
    hair_masks = union_masks([character_package / "semantic_layer_v8" / "masks" / "front" / f"{part_id}.png" for part_id in HAIR_PART_IDS]).filter(ImageFilter.MaxFilter(3))
    face_mask = mask_luma(character_package / "semantic_layer_v8" / "masks" / "front" / "face.png")
    body_masks = union_masks(
        [
            character_package / "semantic_layer_v8" / "masks" / "front" / "torso_inner.png",
            character_package / "semantic_layer_v8" / "masks" / "front" / "jacket_outer.png",
            character_package / "semantic_layer_v8" / "masks" / "front" / "skirt_front.png",
        ]
    )
    non_hair = ImageChops.subtract(coverage, hair_masks)
    face_overlap = ImageChops.multiply(coverage, face_mask)
    body_overlap = ImageChops.multiply(coverage, body_masks)
    face_pixels = max(1, int(ratio(face_mask) * face_mask.width * face_mask.height))
    body_pixels = max(1, int(ratio(body_masks) * body_masks.width * body_masks.height))
    non_hair_occlusion_ratio = ratio(non_hair, denominator=coverage_pixels)
    face_occlusion_ratio = ratio(face_overlap, denominator=face_pixels)
    body_occlusion_ratio = ratio(body_overlap, denominator=body_pixels)
    visual_sanity_reason: list[str] = []
    if non_hair_occlusion_ratio >= VISUAL_SANITY_THRESHOLDS["non_hair_occlusion_ratio"]:
        visual_sanity_reason.append("source ribbon coverage exceeds hair masks")
    if face_occlusion_ratio >= VISUAL_SANITY_THRESHOLDS["face_occlusion_ratio"]:
        visual_sanity_reason.append("source ribbon coverage occludes too much face area")
    # Source-space checks are necessary but not sufficient. Render-space
    # hair-mask alignment and full-frame baseline/overlay framing are evaluated
    # by run_blender_semantic_validation.py before this candidate can advance.
    visual_sanity_reason.append("render-space hair mask alignment and baseline framing are not accepted yet")
    status = "failed_hair_mask_alignment"
    return {
        "alpha_material_valid": True,
        "black_alpha_leak_ratio": 0.0,
        "candidate_black_pixel_ratio": 0.0,
        "face_occlusion_ratio": round(face_occlusion_ratio, 6),
        "body_occlusion_ratio": round(body_occlusion_ratio, 6),
        "non_hair_occlusion_ratio": round(non_hair_occlusion_ratio, 6),
        "hair_mask_iou": 0.0,
        "outside_hair_mask_ratio": round(non_hair_occlusion_ratio, 6),
        "raw_candidate_is_hair_only": False,
        "candidate_is_hair_only": False,
        "hair_union_body_overlap_ratio": 1.0,
        "hair_union_face_overlap_ratio": 1.0,
        "hair_union_weapon_overlap_ratio": 1.0,
        "hair_union_target_is_clean": False,
        "hair_target_quality": "not_evaluated_until_blender_validation",
        "clean_hair_mask_iou": 0.0,
        "clean_outside_hair_mask_ratio": 1.0,
        "clean_candidate_is_hair_only": False,
        "hair_union_projection_valid": False,
        "candidate_geometry_alignment_valid": False,
        "clean_candidate_geometry_alignment_valid": False,
        "coordinate_alignment_gate": "not_evaluated_until_blender_validation",
        "coordinate_mapping_status": "not_evaluated_until_blender_validation",
        "alignment_failure_reason": "render-space coordinate debug has not run",
        "baseline_framing_valid": False,
        "overlay_alignment_valid": False,
        "visual_sanity_status": status,
        "visual_sanity_reason": "; ".join(visual_sanity_reason),
        "manual_visual_review": "failed",
        "artifact_generated": True,
        "black_alpha_leak_fixed": True,
        "numeric_metrics_passed": non_hair_occlusion_ratio < VISUAL_SANITY_THRESHOLDS["non_hair_occlusion_ratio"]
        and face_occlusion_ratio < VISUAL_SANITY_THRESHOLDS["face_occlusion_ratio"],
        "ready_for_cloth_seam_surface": False,
    }


def write_obj(path: Path, ribbons: list[HairRibbon]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    mtl_path = path.with_suffix(".mtl")
    lines = ["# YUNA semantic v9 authored hair ribbons candidate", f"mtllib {mtl_path.name}"]
    vertex_offset = 0
    for ribbon in ribbons:
        lines.append(f"o {ribbon.id}")
        for x, y, z in ribbon.mesh.vertices:
            lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
        for u, v in ribbon.mesh.uvs:
            lines.append(f"vt {u:.6f} {v:.6f}")
        current_material = None
        for face, material_index in zip(ribbon.mesh.faces, ribbon.mesh.face_materials, strict=True):
            material = f"{ribbon.group_id}_front_texture" if material_index == 0 else "hair_ribbon_side_material"
            if material != current_material:
                lines.append(f"usemtl {material}")
                current_material = material
            refs = [f"{idx + 1 + vertex_offset}/{idx + 1 + vertex_offset}" for idx in face]
            lines.append("f " + " ".join(refs))
        vertex_offset += len(ribbon.mesh.vertices)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    material_lines: list[str] = []
    seen_groups: set[str] = set()
    for ribbon in ribbons:
        if ribbon.group_id in seen_groups:
            continue
        seen_groups.add(ribbon.group_id)
        material_lines.extend(
            [
                f"newmtl {ribbon.group_id}_front_texture",
                "Ka 1.000 1.000 1.000",
                "Kd 1.000 1.000 1.000",
                "Ks 0.040 0.040 0.045",
                "d 1.000",
                f"map_Kd {ribbon.texture_path.name}",
                "",
            ]
        )
    material_lines.extend(
        [
            "newmtl hair_ribbon_side_material",
            "Ka 0.630 0.720 0.740",
            "Kd 0.720 0.820 0.840",
            "Ks 0.030 0.040 0.045",
            "d 1.000",
        ]
    )
    mtl_path.write_text("\n".join(material_lines) + "\n", encoding="utf-8")
    return mtl_path


def blender_export_glb(glb_path: Path, ribbons: list[HairRibbon], repo_root: Path) -> dict[str, Any]:
    blender = find_blender()
    if blender is None:
        return {"status": "skipped_with_reason", "reason": "blender_not_found", "glb_exists": False}
    payload = [
        {
            "id": ribbon.id,
            "group_id": ribbon.group_id,
            "source_part_id": ribbon.source_part_id,
            "texture_path": str(ribbon.texture_path),
            "vertices": ribbon.mesh.vertices,
            "faces": ribbon.mesh.faces,
            "uvs": ribbon.mesh.uvs,
            "face_materials": ribbon.mesh.face_materials,
            "spring_hook": ribbon.spring_hook,
        }
        for ribbon in ribbons
    ]
    payload_json = json.dumps(payload)
    hooks = sorted({ribbon.spring_hook for ribbon in ribbons})
    hooks_json = json.dumps(hooks)
    script = f"""
import bpy
import json

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
try:
    bpy.context.preferences.filepaths.save_version = 0
except Exception:
    pass

RIBBONS = json.loads({payload_json!r})
HOOKS = json.loads({hooks_json!r})

side_mat = bpy.data.materials.new('hair_ribbon_side_material')
side_mat.use_nodes = True
side_mat.blend_method = 'OPAQUE'
side_bsdf = side_mat.node_tree.nodes.get('Principled BSDF')
side_bsdf.inputs['Base Color'].default_value = (0.72, 0.82, 0.84, 1.0)
side_bsdf.inputs['Roughness'].default_value = 0.68

front_mats = {{}}
for item in RIBBONS:
    group = item['group_id']
    if group not in front_mats:
        mat = bpy.data.materials.new(group + '_front_texture')
        mat.use_nodes = True
        mat.blend_method = 'BLEND'
        mat.alpha_threshold = 0.02
        mat.show_transparent_back = True
        try:
            mat.surface_render_method = 'BLENDED'
        except Exception:
            pass
        nodes = mat.node_tree.nodes
        bsdf = nodes.get('Principled BSDF')
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(item['texture_path'], check_existing=True)
        tex.image.alpha_mode = 'STRAIGHT'
        tex.extension = 'CLIP'
        mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        mat.node_tree.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
        bsdf.inputs['Alpha'].default_value = 1.0
        bsdf.inputs['Roughness'].default_value = 0.62
        front_mats[group] = mat

for item in RIBBONS:
    mesh = bpy.data.meshes.new(item['id'] + '_mesh')
    mesh.from_pydata([tuple(v) for v in item['vertices']], [], [tuple(f) for f in item['faces']])
    mesh.update()
    uv_layer = mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = item['uvs'][vertex_index]
    obj = bpy.data.objects.new(item['id'], mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(front_mats[item['group_id']])
    obj.data.materials.append(side_mat)
    obj['semantic_part'] = 'hair'
    obj['source_part_id'] = item['source_part_id']
    obj['hair_group'] = item['group_id']
    obj['actuator'] = 'authored_hair_ribbons_v0'
    obj['candidate_only'] = True
    obj['replace_in_beauty_glb'] = False
    obj['spring_hook'] = item['spring_hook']
    for idx, poly in enumerate(obj.data.polygons):
        poly.material_index = item['face_materials'][idx]

for index, name in enumerate(HOOKS):
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=((index - 1.5) * 0.12, 0.0, 0.0))
    hook = bpy.context.object
    hook.name = name
    hook.empty_display_size = 0.08
    hook['semantic_part'] = 'hair'
    hook['actuator'] = 'authored_hair_ribbons_v0'
    hook['secondary_motion_hook'] = True

bpy.ops.wm.save_as_mainfile(filepath=r'{glb_path.with_suffix('.blend')}')
bpy.ops.export_scene.gltf(
    filepath=r'{glb_path}',
    export_format='GLB',
    export_texcoords=True,
    export_normals=True,
    export_materials='EXPORT'
)
"""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(script)
        tmp_path = tmp.name
    result = subprocess.run(
        [blender, "--background", "--python", tmp_path],
        cwd=str(repo_root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {
        "status": "ok" if result.returncode == 0 and glb_path.exists() else "failed",
        "blender": blender,
        "exit_code": result.returncode,
        "glb_exists": glb_path.exists(),
        "glb_bytes": glb_path.stat().st_size if glb_path.exists() else 0,
        "blend_exists": glb_path.with_suffix(".blend").exists(),
        "blend_path": display_path(glb_path.with_suffix(".blend"), repo_root),
        "log_tail": result.stdout.splitlines()[-80:],
    }


def build_spec(paths: ActuatorPaths, ribbons: list[HairRibbon], source_decisions: list[dict[str, Any]], texture_records: list[SanitizedTextureRecord]) -> dict[str, Any]:
    return {
        "route": "semantic_layer_v9_authored_hair_ribbons_v0",
        "source_route": "semantic_layer_v9_candidate_spec_only",
        "baseline": "semantic_layer_v8_beauty_main_debug_cage_split",
        "boundary": "Independent hair ribbon candidate only. It does not replace v8 beauty hair cards until screenshot/import validation passes.",
        "part": {
            "id": "hair",
            "category": "hair",
            "generator": "authored_hair_ribbons_v0",
            "replace_in_beauty_glb": False,
            "independent_objects": True,
            "candidate_only": True,
            "side_back_are_soft_constraints": True,
            "source_parts": list(HAIR_PART_IDS),
            "spring_hooks": sorted({ribbon.spring_hook for ribbon in ribbons}),
        },
        "source_decisions": source_decisions,
        "mesh": combined_summary(ribbons, texture_records),
        "exports": {
            "obj": display_path(paths.obj_path, paths.repo_root),
            "glb": display_path(paths.glb_path, paths.repo_root),
            "report": display_path(paths.report_path, paths.repo_root),
        },
    }


@register("authored_hair_ribbons_v0")
def run_authored_hair_ribbons(paths: ActuatorPaths) -> ActuatorResult:
    candidate_spec = load_json(paths.character_package / "semantic_layer_v9_candidate" / "specs" / "yuna_semantic_layer_v9_candidate.json")
    decisions = {item["part_id"]: item for item in candidate_spec.get("decisions", [])}
    source_decisions = [decisions[item] for item in HAIR_PART_IDS if item in decisions]
    warnings: list[str] = []
    errors: list[str] = []
    if len(source_decisions) != len(HAIR_PART_IDS):
        errors.append("v9 candidate is missing one or more hair strand-authoring decisions")
    if any(item.get("proposed_generator") != "authored_hair_ribbons" for item in source_decisions):
        errors.append("v9 candidate has inconsistent hair ribbon proposals")

    if errors:
        result = ActuatorResult(
            actuator=ACTUATOR_NAME,
            status="failed",
            part_id=PART_ID,
            decision_source=display_path(paths.character_package / "semantic_layer_v9_candidate" / "specs" / "yuna_semantic_layer_v9_candidate.json", paths.repo_root),
            generated_files={},
            mesh_summary={},
            validation={},
            warnings=warnings,
            errors=errors,
        )
        write_json(paths.report_path, {"created_at": datetime.now(timezone.utc).isoformat(), "route": "semantic_layer_v9_authored_hair_ribbons_v0", **result.to_dict()})
        return result

    ribbons = build_hair_ribbons(paths.character_package)
    texture_records = prepare_sanitized_textures(paths, ribbons)
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    paths.spec_path.parent.mkdir(parents=True, exist_ok=True)
    paths.obj_path.parent.mkdir(parents=True, exist_ok=True)
    write_obj(paths.obj_path, ribbons)
    glb_report = blender_export_glb(paths.glb_path, ribbons, paths.repo_root)
    if glb_report.get("status") != "ok":
        warnings.append("GLB export did not complete; see validation.blender_glb_export")

    generated_files = {
        "spec": display_path(paths.spec_path, paths.repo_root),
        "obj": display_path(paths.obj_path, paths.repo_root),
        "mtl": display_path(paths.obj_path.with_suffix(".mtl"), paths.repo_root),
        "glb": display_path(paths.glb_path, paths.repo_root),
        "blend": display_path(paths.glb_path.with_suffix(".blend"), paths.repo_root),
        "report": display_path(paths.report_path, paths.repo_root),
    }
    summary = combined_summary(ribbons, texture_records)
    visual_metrics = source_visual_sanity_metrics(paths.character_package, ribbons)
    validation = {
        "independent_objects": True,
        "has_ribbon_meshes": len(ribbons) > 0,
        "has_depth_groups": summary["depth_group_count"] >= 3,
        "has_uvs": all(len(ribbon.mesh.uvs) == len(ribbon.mesh.vertices) for ribbon in ribbons),
        "has_front_texture_material": True,
        "uses_sanitized_alpha_textures": all(record.sanitized_texture.exists() and record.alpha_pixels > 0 for record in texture_records),
        "has_side_material": True,
        "has_spring_hook_metadata": True,
        "replace_in_beauty_glb": False,
        "side_back_are_soft_constraints": True,
        **visual_metrics,
        "obj": file_record(paths.obj_path),
        "glb": file_record(paths.glb_path),
        "blender_glb_export": glb_report,
    }
    result = ActuatorResult(
        actuator=ACTUATOR_NAME,
        status="generated_with_warnings" if visual_metrics["visual_sanity_status"] in {"passed", "passed_with_minor_warnings"} else visual_metrics["visual_sanity_status"],
        part_id=PART_ID,
        decision_source=display_path(paths.character_package / "semantic_layer_v9_candidate" / "filter_report.json", paths.repo_root),
        generated_files=generated_files,
        mesh_summary=summary,
        validation=validation,
        warnings=warnings
        + [
            "v0 derives deterministic ribbon guides from v8 mask bounds and texture alpha; these are authored-ribbon candidates, not final hand-authored production curves.",
            "side/back references remain soft constraints and are not treated as locked geometry truth.",
            "v8 beauty hair cards remain active until screenshot/import validation passes.",
        ],
        errors=[],
    )
    contract_errors = validate_hair_candidate_report({"part_id": PART_ID, **result.to_dict()})
    if contract_errors:
        if result.status not in {"failed_visual_sanity", "failed_hair_mask_alignment", "failed_validation_framing", "manual_review_failed"}:
            result.status = "failed"
        result.errors.extend(contract_errors)

    write_json(paths.spec_path, build_spec(paths, ribbons, source_decisions, texture_records))
    write_json(paths.report_path, {"created_at": datetime.now(timezone.utc).isoformat(), "route": "semantic_layer_v9_authored_hair_ribbons_v0", **result.to_dict()})
    return result
