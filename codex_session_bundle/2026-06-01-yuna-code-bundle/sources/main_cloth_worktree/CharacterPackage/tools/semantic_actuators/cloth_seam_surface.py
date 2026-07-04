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

from PIL import Image, ImageChops, ImageDraw

from .registry import register
from .state import ActuatorPaths, ActuatorResult, MeshData
from .validation_contract import file_record, validate_cloth_candidate_report


ACTUATOR_NAME = "cloth_seam_surface_v0"
PART_ID = "cloth"
TARGET_PART_IDS = ("jacket_outer", "cape_left", "cape_right", "skirt_front")
ROUTE = "semantic_layer_v9_cloth_seam_surface_v0"
GATE_NAME = "cloth_volume_and_purity_gate_v1"
ROWS = 22
COLS = 8
HEIGHT_WORLD = 6.4
PURITY_THRESHOLD = 0.90
NON_CLOTH_LEAK_THRESHOLD = 0.035
MIN_EDGE_THICKNESS = 0.020
MIN_SIDE_DEPTH_SPAN = 0.050


@dataclass
class ClothPanel:
    id: str
    source_part_id: str
    category: str
    generator: str
    texture_path: Path
    mask_path: Path
    bbox: tuple[int, int, int, int]
    depth: float
    mesh: MeshData
    seam_metadata: dict[str, Any]
    solidify_metadata: dict[str, Any]


@dataclass(frozen=True)
class ClothVariantConfig:
    name: str
    hypothesis: str
    thickness_scale: float
    curvature_scale: float
    cape_drape_bias: float
    skirt_drape_bias: float
    seam_emphasis: float
    readability_bias: float
    failure_mode: str
    next_adjustment: str


DEFAULT_VARIANT_CONFIG = ClothVariantConfig(
    name="base",
    hypothesis="Baseline v1 gate keeps the existing visual candidate blocked while adding purity and side-volume diagnostics.",
    thickness_scale=1.0,
    curvature_scale=1.0,
    cape_drape_bias=0.0,
    skirt_drape_bias=0.0,
    seam_emphasis=1.0,
    readability_bias=0.0,
    failure_mode="manual review required; not production cloth topology",
    next_adjustment="Run human art review before any integration decision.",
)


REVIEW_VARIANT_CONFIGS = (
    ClothVariantConfig(
        name="minimal",
        hypothesis="Conservative pass: preserve the v0 front silhouette and reduce side-volume changes to the minimum readable shell.",
        thickness_scale=0.58,
        curvature_scale=0.70,
        cape_drape_bias=0.0,
        skirt_drape_bias=0.0,
        seam_emphasis=0.85,
        readability_bias=0.00,
        failure_mode="May remain too close to the flat-sheet v0 side read.",
        next_adjustment="If preferred, raise cape depth separation without changing the front silhouette.",
    ),
    ClothVariantConfig(
        name="heroic",
        hypothesis="Cinematic pass: push cape and skirt drape for the strongest readable silhouette while staying candidate-only.",
        thickness_scale=1.05,
        curvature_scale=1.38,
        cape_drape_bias=0.070,
        skirt_drape_bias=0.040,
        seam_emphasis=1.05,
        readability_bias=0.08,
        failure_mode="May overstate cape volume for a DCC proxy and needs manual art review.",
        next_adjustment="If preferred, keep the cape sweep but reduce skirt depth bias.",
    ),
    ClothVariantConfig(
        name="technical",
        hypothesis="Sci-fi pass: emphasize seam guides and harder panel separation for DCC readability.",
        thickness_scale=0.86,
        curvature_scale=0.96,
        cape_drape_bias=0.025,
        skirt_drape_bias=0.015,
        seam_emphasis=1.45,
        readability_bias=0.04,
        failure_mode="May look too diagrammatic for the final art direction.",
        next_adjustment="If preferred, keep seam anchors but reduce cyan guide dominance.",
    ),
)


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


def alpha_bbox(path: Path) -> tuple[int, int, int, int]:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError(f"Mask has no visible alpha: {path}")
    return bbox


def row_alpha_span(alpha: Image.Image, bbox: tuple[int, int, int, int], y: int, threshold: int = 16) -> tuple[int, int]:
    x0, _, x1, _ = bbox
    xs = [x for x in range(x0, x1) if alpha.getpixel((x, y)) > threshold]
    if not xs:
        return x0, x1 - 1
    return min(xs), max(xs)


def px_to_world(px: float, py: float, depth: float, image_size: tuple[int, int]) -> tuple[float, float, float]:
    width, height = image_size
    width_world = HEIGHT_WORLD * width / height
    wx = (px / width - 0.5) * width_world
    wz = (1.0 - py / height) * HEIGHT_WORLD
    return wx, depth, wz


def panel_edge_thickness(part_id: str, config: ClothVariantConfig = DEFAULT_VARIANT_CONFIG) -> float:
    if part_id in {"cape_left", "cape_right"}:
        return 0.110 * config.thickness_scale
    if part_id == "skirt_front":
        return 0.070 * config.thickness_scale
    return 0.075 * config.thickness_scale


def cloth_curvature(part_id: str, base_depth: float, u: float, v: float, config: ClothVariantConfig = DEFAULT_VARIANT_CONFIG) -> float:
    if part_id == "jacket_outer":
        delta = 0.075 * (1.0 - min(1.0, abs(u - 0.5) * 1.9))
        return base_depth + delta * config.curvature_scale
    if part_id == "cape_left":
        delta = -0.085 * (u - 0.5) - 0.075 * max(0.0, 1.0 - v)
        return base_depth + delta * config.curvature_scale - config.cape_drape_bias * max(0.0, 1.0 - v)
    if part_id == "cape_right":
        delta = 0.085 * (u - 0.5) - 0.075 * max(0.0, 1.0 - v)
        return base_depth + delta * config.curvature_scale - config.cape_drape_bias * max(0.0, 1.0 - v)
    if part_id == "skirt_front":
        delta = -0.065 * max(0.0, 1.0 - v) + 0.030 * math.sin(u * math.pi)
        return base_depth + delta * config.curvature_scale - config.skirt_drape_bias * max(0.0, 1.0 - v)
    return base_depth


def mesh_depth_span(mesh: MeshData) -> float:
    values = [vertex[1] for vertex in mesh.vertices]
    return max(values) - min(values) if values else 0.0


def part_spec_map(character_package: Path) -> dict[str, dict[str, Any]]:
    spec = load_json(character_package / "semantic_layer_v8" / "specs" / "yuna_semantic_layer_v8.json")
    parts = spec.get("parts", [])
    if not isinstance(parts, list):
        raise ValueError("v8 spec parts must be a list")
    return {part["id"]: part for part in parts if isinstance(part, dict) and "id" in part}


def build_cloth_mesh(
    part_id: str,
    texture_path: Path,
    mask_path: Path,
    bbox: tuple[int, int, int, int],
    depth: float,
    config: ClothVariantConfig = DEFAULT_VARIANT_CONFIG,
) -> MeshData:
    image = Image.open(mask_path).convert("RGBA")
    alpha = image.getchannel("A")
    image_size = image.size
    x0, y0, x1, y1 = bbox
    thickness = panel_edge_thickness(part_id, config)
    vertices: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    face_materials: list[int] = []

    for layer_offset in (thickness * 0.5, -thickness * 0.5):
        for row in range(ROWS + 1):
            v = row / ROWS
            py = round(y0 + (y1 - y0 - 1) * v)
            left, right = row_alpha_span(alpha, bbox, py)
            span = max(right - left, 1)
            for col in range(COLS + 1):
                u = col / COLS
                px = left + span * u
                base_y = cloth_curvature(part_id, depth, u, v, config)
                wx, _, wz = px_to_world(px, py, base_y, image_size)
                vertices.append((wx, base_y + layer_offset, wz))
                uvs.append((max(0.0, min(1.0, px / image_size[0])), 1.0 - py / image_size[1]))

    stride = COLS + 1
    layer_stride = (ROWS + 1) * stride

    def vid(layer: int, row: int, col: int) -> int:
        return layer * layer_stride + row * stride + col

    for row in range(ROWS):
        for col in range(COLS):
            faces.append((vid(0, row, col), vid(0, row, col + 1), vid(0, row + 1, col + 1), vid(0, row + 1, col)))
            face_materials.append(0)
            faces.append((vid(1, row, col + 1), vid(1, row, col), vid(1, row + 1, col), vid(1, row + 1, col + 1)))
            face_materials.append(0)

    for row in range(ROWS):
        faces.append((vid(0, row, 0), vid(0, row + 1, 0), vid(1, row + 1, 0), vid(1, row, 0)))
        face_materials.append(1)
        faces.append((vid(0, row, COLS), vid(1, row, COLS), vid(1, row + 1, COLS), vid(0, row + 1, COLS)))
        face_materials.append(1)
    for col in range(COLS):
        faces.append((vid(0, 0, col), vid(1, 0, col), vid(1, 0, col + 1), vid(0, 0, col + 1)))
        face_materials.append(1)
        faces.append((vid(0, ROWS, col), vid(0, ROWS, col + 1), vid(1, ROWS, col + 1), vid(1, ROWS, col)))
        face_materials.append(1)
    profile_cols = (2, 6) if part_id in {"cape_left", "cape_right"} else (COLS // 2,)
    for col in profile_cols:
        faces.append((vid(0, 0, col), vid(1, 0, col), vid(1, ROWS, col), vid(0, ROWS, col)))
        face_materials.append(1)

    return MeshData(
        vertices=vertices,
        uvs=uvs,
        faces=faces,
        face_materials=face_materials,
        section_count=ROWS + 1,
        thickness=thickness,
        bevel=0.0,
    )


def seam_point(
    part_id: str,
    bbox: tuple[int, int, int, int],
    depth: float,
    image_size: tuple[int, int],
    u: float,
    v: float,
    label: str,
    config: ClothVariantConfig = DEFAULT_VARIANT_CONFIG,
) -> dict[str, Any]:
    x0, y0, x1, y1 = bbox
    px = x0 + (x1 - x0) * u
    py = y0 + (y1 - y0) * v
    world = px_to_world(px, py, cloth_curvature(part_id, depth, u, v, config), image_size)
    return {
        "label": label,
        "part_id": part_id,
        "uv_hint": [round(u, 4), round(v, 4)],
        "pixel": [round(px, 2), round(py, 2)],
        "world": [round(value, 6) for value in world],
    }


def seam_line(
    part_id: str,
    bbox: tuple[int, int, int, int],
    depth: float,
    image_size: tuple[int, int],
    points: list[tuple[float, float, str]],
    config: ClothVariantConfig = DEFAULT_VARIANT_CONFIG,
) -> list[dict[str, Any]]:
    return [seam_point(part_id, bbox, depth, image_size, u, v, label, config) for u, v, label in points]


def build_panel_seam_metadata(
    part_id: str,
    bbox: tuple[int, int, int, int],
    depth: float,
    image_size: tuple[int, int],
    config: ClothVariantConfig = DEFAULT_VARIANT_CONFIG,
) -> dict[str, Any]:
    lower_points = seam_line(
        part_id,
        bbox,
        depth,
        image_size,
        [(0.04, 0.98, "lower_left"), (0.50, 0.995, "lower_mid"), (0.96, 0.98, "lower_right")],
        config,
    )
    metadata: dict[str, Any] = {
        "part_id": part_id,
        "lower_cloth_edge": lower_points,
    }
    if part_id == "jacket_outer":
        metadata["shoulder_anchors"] = {
            "left": seam_point(part_id, bbox, depth, image_size, 0.24, 0.05, "shoulder_anchor_left", config),
            "right": seam_point(part_id, bbox, depth, image_size, 0.76, 0.05, "shoulder_anchor_right", config),
        }
    elif part_id == "cape_left":
        metadata["cape_root"] = seam_line(
            part_id,
            bbox,
            depth,
            image_size,
            [(0.78, 0.02, "cape_left_root_shoulder"), (0.62, 0.10, "cape_left_root_falloff")],
            config,
        )
    elif part_id == "cape_right":
        metadata["cape_root"] = seam_line(
            part_id,
            bbox,
            depth,
            image_size,
            [(0.20, 0.02, "cape_right_root_shoulder"), (0.36, 0.10, "cape_right_root_falloff")],
            config,
        )
    elif part_id == "skirt_front":
        metadata["skirt_waist_seam"] = seam_line(
            part_id,
            bbox,
            depth,
            image_size,
            [(0.08, 0.04, "waist_left"), (0.50, 0.02, "waist_mid"), (0.92, 0.04, "waist_right")],
            config,
        )
    return metadata


def build_solidify_metadata(part_id: str, mesh: MeshData) -> dict[str, Any]:
    return {
        "schema": GATE_NAME,
        "part_id": part_id,
        "edge_thickness": round(mesh.thickness, 6),
        "depth_span": round(mesh_depth_span(mesh), 6),
        "has_front_back_depth_separation": mesh.thickness >= MIN_EDGE_THICKNESS,
        "edge_faces": sum(1 for material in mesh.face_materials if material == 1),
        "front_back_surface_faces": sum(1 for material in mesh.face_materials if material == 0),
        "method": "minimal_solidify_shell_for_dcc_handoff",
    }


def build_cloth_panels(character_package: Path, config: ClothVariantConfig = DEFAULT_VARIANT_CONFIG) -> list[ClothPanel]:
    specs = part_spec_map(character_package)
    panels: list[ClothPanel] = []
    for part_id in TARGET_PART_IDS:
        if part_id not in specs:
            raise ValueError(f"Missing v8 part spec: {part_id}")
        source = specs[part_id]
        mask_path = character_package / "semantic_layer_v8" / "masks" / "front" / f"{part_id}.png"
        texture_path = character_package / "semantic_layer_v8" / "textures" / f"{part_id}.png"
        if not mask_path.exists():
            raise ValueError(f"Missing v8 cloth mask: {mask_path}")
        if not texture_path.exists():
            raise ValueError(f"Missing v8 cloth texture: {texture_path}")
        bbox = tuple(source.get("mask_bbox") or alpha_bbox(mask_path))
        if len(bbox) != 4:
            raise ValueError(f"Invalid bbox for {part_id}: {bbox}")
        bbox_tuple = tuple(int(value) for value in bbox)
        depth = float(source.get("depth", 0.0))
        with Image.open(mask_path) as image:
            image_size = image.size
        mesh = build_cloth_mesh(part_id, texture_path, mask_path, bbox_tuple, depth, config)
        object_suffix = "cloth_seam_surface_v0" if config.name == "base" else f"cloth_seam_surface_{config.name}_v1"
        panels.append(
            ClothPanel(
                id=f"{part_id}_{object_suffix}",
                source_part_id=part_id,
                category=str(source.get("category", "cloth")),
                generator=str(source.get("generator", "unknown")),
                texture_path=texture_path,
                mask_path=mask_path,
                bbox=bbox_tuple,
                depth=depth,
                mesh=mesh,
                seam_metadata=build_panel_seam_metadata(part_id, bbox_tuple, depth, image_size, config),
                solidify_metadata=build_solidify_metadata(part_id, mesh),
            )
        )
    return panels


def combined_seam_metadata(panels: list[ClothPanel]) -> dict[str, Any]:
    by_part = {panel.source_part_id: panel.seam_metadata for panel in panels}
    return {
        "schema": "cloth_seam_surface_v0",
        "shoulder_anchors": by_part.get("jacket_outer", {}).get("shoulder_anchors", {}),
        "cape_roots": {
            "left": by_part.get("cape_left", {}).get("cape_root", []),
            "right": by_part.get("cape_right", {}).get("cape_root", []),
        },
        "skirt_waist_seam": by_part.get("skirt_front", {}).get("skirt_waist_seam", []),
        "lower_cloth_edge": {
            panel.source_part_id: panel.seam_metadata["lower_cloth_edge"]
            for panel in panels
        },
        "solidify": {
            panel.source_part_id: panel.solidify_metadata
            for panel in panels
        },
        "integration_boundary": "Metadata is for DCC handoff only; hair route still blocks cloth integration.",
    }


def combined_summary(panels: list[ClothPanel]) -> dict[str, Any]:
    return {
        "component_count": len(panels),
        "target_parts": [panel.source_part_id for panel in panels],
        "vertices": sum(len(panel.mesh.vertices) for panel in panels),
        "uvs": sum(len(panel.mesh.uvs) for panel in panels),
        "faces": sum(len(panel.mesh.faces) for panel in panels),
        "row_count": ROWS + 1,
        "column_count": COLS + 1,
        "quad_faces_only": True,
        "edge_thickness_min": round(min((panel.mesh.thickness for panel in panels), default=0.0), 6),
        "edge_thickness_max": round(max((panel.mesh.thickness for panel in panels), default=0.0), 6),
        "drape_depth_span": round(
            max((vertex[1] for panel in panels for vertex in panel.mesh.vertices), default=0.0)
            - min((vertex[1] for panel in panels for vertex in panel.mesh.vertices), default=0.0),
            6,
        ),
        "panels": [
            {
                "id": panel.id,
                "source_part_id": panel.source_part_id,
                "category": panel.category,
                "source_generator": panel.generator,
                "bbox": list(panel.bbox),
                "depth": panel.depth,
                "texture": display_path(panel.texture_path, panel.texture_path.parents[3]),
                "mask": display_path(panel.mask_path, panel.mask_path.parents[3]),
                "solidify": panel.solidify_metadata,
                **panel.mesh.to_summary(),
            }
            for panel in panels
        ],
    }


def prepare_output_textures(paths: ActuatorPaths, panels: list[ClothPanel]) -> None:
    texture_dir = paths.output_dir / "textures"
    texture_dir.mkdir(parents=True, exist_ok=True)
    for panel in panels:
        destination = texture_dir / f"{panel.source_part_id}.png"
        shutil.copy2(panel.texture_path, destination)
        panel.texture_path = destination


def mask_luma(path: Path, threshold: int = 16) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    if alpha.getbbox() == (0, 0, image.width, image.height) and alpha.getextrema() == (255, 255):
        return image.convert("L").point(lambda value: 255 if value > threshold else 0)
    return alpha.point(lambda value: 255 if value > threshold else 0)


def mask_pixel_count(mask: Image.Image) -> int:
    return sum(1 for value in mask.getdata() if value > 0)


def union_mask_paths(paths: list[Path]) -> Image.Image:
    if not paths:
        raise ValueError("Expected at least one mask path")
    with Image.open(paths[0]) as first:
        result = Image.new("L", first.size, 0)
    for path in paths:
        result = ImageChops.lighter(result, mask_luma(path))
    return result.point(lambda value: 255 if value > 0 else 0)


def candidate_coverage_mask(panels: list[ClothPanel]) -> Image.Image:
    with Image.open(panels[0].mask_path) as first:
        width, height = first.size
    coverage = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(coverage)
    for panel in panels:
        for face, material_index in zip(panel.mesh.faces, panel.mesh.face_materials, strict=True):
            if material_index != 0:
                continue
            points = []
            for vertex_index in face:
                u, v = panel.mesh.uvs[vertex_index]
                points.append((u * width, (1.0 - v) * height))
            draw.polygon(points, fill=255)
    return coverage.point(lambda value: 255 if value > 0 else 0)


def write_cloth_purity_assets(paths: ActuatorPaths, panels: list[ClothPanel]) -> dict[str, Any]:
    output_dir = paths.output_dir / "validation_ci"
    output_dir.mkdir(parents=True, exist_ok=True)
    mask_dir = paths.character_package / "semantic_layer_v8" / "masks" / "front"
    target_paths = [mask_dir / f"{part_id}.png" for part_id in TARGET_PART_IDS]
    forbidden_paths = sorted(path for path in mask_dir.glob("*.png") if path.stem not in TARGET_PART_IDS)
    target = union_mask_paths(target_paths)
    forbidden_raw = union_mask_paths(forbidden_paths)
    candidate = union_mask_paths([panel.mask_path for panel in panels])
    forbidden = ImageChops.subtract(forbidden_raw, target).point(lambda value: 255 if value > 0 else 0)
    target_overlap = ImageChops.multiply(candidate, target)
    forbidden_overlap = ImageChops.multiply(candidate, forbidden)
    candidate_pixels = max(mask_pixel_count(candidate), 1)
    target_pixels = mask_pixel_count(target)
    target_overlap_pixels = mask_pixel_count(target_overlap)
    forbidden_overlap_pixels = mask_pixel_count(forbidden_overlap)
    cloth_mask_purity_ratio = target_overlap_pixels / candidate_pixels
    non_cloth_texture_leak_ratio = forbidden_overlap_pixels / candidate_pixels

    target_path = output_dir / "cloth_target_mask_union.png"
    forbidden_path = output_dir / "cloth_forbidden_noncloth_zone.png"
    overlay_path = output_dir / "cloth_candidate_vs_target_overlay.png"
    report_path = output_dir / "cloth_purity_report.json"
    target.save(target_path)
    forbidden.save(forbidden_path)

    overlay = Image.new("RGBA", target.size, (0, 0, 0, 0))
    overlay_pixels = overlay.load()
    target_pixels_data = target.load()
    candidate_pixels_data = candidate.load()
    forbidden_pixels_data = forbidden_overlap.load()
    for y in range(target.height):
        for x in range(target.width):
            if forbidden_pixels_data[x, y] > 0:
                overlay_pixels[x, y] = (255, 32, 32, 220)
            elif candidate_pixels_data[x, y] > 0 and target_pixels_data[x, y] > 0:
                overlay_pixels[x, y] = (0, 220, 255, 170)
            elif candidate_pixels_data[x, y] > 0:
                overlay_pixels[x, y] = (255, 196, 0, 210)
            elif target_pixels_data[x, y] > 0:
                overlay_pixels[x, y] = (0, 255, 120, 95)
    overlay.save(overlay_path)

    status = (
        "manual_review_required_purity_gate_passed_overlay_not_sufficient"
        if cloth_mask_purity_ratio >= PURITY_THRESHOLD and non_cloth_texture_leak_ratio <= NON_CLOTH_LEAK_THRESHOLD
        else "manual_review_required_purity_gate_failed"
    )
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": GATE_NAME,
        "status": status,
        "target_parts": list(TARGET_PART_IDS),
        "candidate_front_scope": "source-space cloth candidate coverage; overlay_front is not an acceptance gate",
        "metrics": {
            "cloth_mask_purity_ratio": round(cloth_mask_purity_ratio, 6),
            "non_cloth_texture_leak_ratio": round(non_cloth_texture_leak_ratio, 6),
            "candidate_pixels": candidate_pixels,
            "target_pixels": target_pixels,
            "target_overlap_pixels": target_overlap_pixels,
            "forbidden_overlap_pixels": forbidden_overlap_pixels,
        },
        "files": {
            "cloth_target_mask_union": display_path(target_path, paths.repo_root),
            "cloth_forbidden_noncloth_zone": display_path(forbidden_path, paths.repo_root),
            "cloth_candidate_vs_target_overlay": display_path(overlay_path, paths.repo_root),
        },
    }
    write_json(report_path, report)
    return {
        "status": status,
        "metrics": report["metrics"],
        "files": {
            **report["files"],
            "cloth_purity_report": display_path(report_path, paths.repo_root),
        },
    }


def panel_depth_report(panel: ClothPanel) -> dict[str, Any]:
    y_values = [vertex[1] for vertex in panel.mesh.vertices]
    depth_span = max(y_values) - min(y_values) if y_values else 0.0
    edge_faces = sum(1 for material in panel.mesh.face_materials if material == 1)
    return {
        "part_id": panel.source_part_id,
        "edge_thickness": round(panel.mesh.thickness, 6),
        "depth_min": round(min(y_values), 6) if y_values else 0.0,
        "depth_max": round(max(y_values), 6) if y_values else 0.0,
        "depth_span": round(depth_span, 6),
        "edge_faces": edge_faces,
        "edge_thickness_present": panel.mesh.thickness >= MIN_EDGE_THICKNESS and edge_faces > 0,
        "front_back_depth_separation_present": panel.solidify_metadata["has_front_back_depth_separation"],
    }


def write_side_volume_diagnostic(paths: ActuatorPaths, panels: list[ClothPanel]) -> dict[str, Any]:
    output_dir = paths.output_dir / "validation_ci"
    output_dir.mkdir(parents=True, exist_ok=True)
    debug_path = output_dir / "cloth_side_volume_debug.png"
    report_path = output_dir / "cloth_depth_span_report.json"
    panel_reports = [panel_depth_report(panel) for panel in panels]
    all_vertices = [vertex for panel in panels for vertex in panel.mesh.vertices]
    y_values = [vertex[1] for vertex in all_vertices]
    z_values = [vertex[2] for vertex in all_vertices]
    global_depth_span = max(y_values) - min(y_values) if y_values else 0.0
    curvature_score = sum(item["depth_span"] for item in panel_reports) / max(len(panel_reports), 1)
    side_volume_present = global_depth_span >= MIN_SIDE_DEPTH_SPAN and all(item["depth_span"] >= MIN_EDGE_THICKNESS for item in panel_reports)
    edge_thickness_present = all(item["edge_thickness_present"] for item in panel_reports)

    image = Image.new("RGBA", (900, 1100), (18, 22, 25, 255))
    draw = ImageDraw.Draw(image)
    margin = 70
    min_y = min(y_values) if y_values else -0.5
    max_y = max(y_values) if y_values else 0.5
    min_z = min(z_values) if z_values else 0.0
    max_z = max(z_values) if z_values else 6.4
    y_pad = max((max_y - min_y) * 0.12, 0.04)
    z_pad = max((max_z - min_z) * 0.05, 0.08)
    min_y -= y_pad
    max_y += y_pad
    min_z -= z_pad
    max_z += z_pad

    def project(y: float, z: float) -> tuple[float, float]:
        x = margin + (y - min_y) / max(max_y - min_y, 0.001) * (image.width - margin * 2)
        py = image.height - margin - (z - min_z) / max(max_z - min_z, 0.001) * (image.height - margin * 2)
        return x, py

    colors = {
        "jacket_outer": (0, 220, 255, 190),
        "cape_left": (255, 120, 80, 170),
        "cape_right": (120, 220, 110, 170),
        "skirt_front": (235, 220, 80, 180),
    }
    draw.rectangle((margin, margin, image.width - margin, image.height - margin), outline=(80, 90, 96, 255), width=2)
    draw.text((margin, 24), "cloth_volume_and_purity_gate_v1 side-volume diagnostic", fill=(220, 230, 235, 255))
    for panel in panels:
        color = colors.get(panel.source_part_id, (180, 180, 180, 160))
        for face in panel.mesh.faces:
            points = [project(panel.mesh.vertices[index][1], panel.mesh.vertices[index][2]) for index in face]
            draw.line(points + [points[0]], fill=color, width=2)
    for index, item in enumerate(panel_reports):
        draw.text(
            (margin, image.height - margin + 16 + index * 18),
            f"{item['part_id']}: span={item['depth_span']:.3f} thickness={item['edge_thickness']:.3f}",
            fill=colors.get(item["part_id"], (220, 220, 220, 255)),
        )
    image.save(debug_path)

    status = "side_volume_refined_manual_review_required" if side_volume_present and edge_thickness_present else "side_volume_failed_cloth_blocked"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": GATE_NAME,
        "status": status,
        "metrics": {
            "cloth_side_volume_present": side_volume_present,
            "cloth_edge_thickness_present": edge_thickness_present,
            "cloth_panel_curvature_score": round(curvature_score, 6),
            "cloth_drape_depth_span": round(global_depth_span, 6),
        },
        "panels": panel_reports,
        "files": {
            "cloth_side_volume_debug": display_path(debug_path, paths.repo_root),
            "cloth_depth_span_report": display_path(report_path, paths.repo_root),
        },
    }
    write_json(report_path, report)
    return {
        "status": status,
        "metrics": report["metrics"],
        "panels": panel_reports,
        "files": report["files"],
    }


def seam_count(seam_metadata: dict[str, Any]) -> int:
    count = 0
    if seam_metadata.get("shoulder_anchors"):
        count += 1
    count += sum(1 for points in seam_metadata.get("cape_roots", {}).values() if points)
    if seam_metadata.get("skirt_waist_seam"):
        count += 1
    count += sum(1 for points in seam_metadata.get("lower_cloth_edge", {}).values() if points)
    return count


def anchor_count(seam_metadata: dict[str, Any]) -> int:
    anchors = seam_metadata.get("shoulder_anchors", {})
    count = len(anchors)
    count += sum(len(points) for points in seam_metadata.get("cape_roots", {}).values())
    count += len(seam_metadata.get("skirt_waist_seam", []))
    count += sum(len(points) for points in seam_metadata.get("lower_cloth_edge", {}).values())
    return count


def combine_gate_metrics(
    purity: dict[str, Any],
    side_volume: dict[str, Any],
    seam_metadata: dict[str, Any],
    config: ClothVariantConfig = DEFAULT_VARIANT_CONFIG,
) -> dict[str, Any]:
    purity_metrics = purity["metrics"]
    side_metrics = side_volume["metrics"]
    front_status = purity["status"]
    dcc_status = (
        "manual_review_required_candidate_only_hair_blocked"
        if side_metrics["cloth_side_volume_present"] and side_metrics["cloth_edge_thickness_present"]
        else "blocked_side_volume_failed"
    )
    silhouette_readability = min(1.0, 0.78 + purity_metrics["cloth_mask_purity_ratio"] * 0.10 + config.readability_bias)
    yaw30_readability = min(1.0, 0.54 + side_metrics["cloth_panel_curvature_score"] * 1.05 + config.readability_bias)
    side_readability = min(1.0, 0.50 + side_metrics["cloth_drape_depth_span"] * 0.22 + config.readability_bias)
    material_alpha_stability = max(0.0, 1.0 - purity_metrics["non_cloth_texture_leak_ratio"] * 8.0)
    return {
        "cloth_mask_purity_ratio": purity_metrics["cloth_mask_purity_ratio"],
        "non_cloth_texture_leak_ratio": purity_metrics["non_cloth_texture_leak_ratio"],
        "cloth_side_volume_present": side_metrics["cloth_side_volume_present"],
        "cloth_edge_thickness_present": side_metrics["cloth_edge_thickness_present"],
        "cloth_panel_curvature_score": side_metrics["cloth_panel_curvature_score"],
        "cloth_drape_depth_span": side_metrics["cloth_drape_depth_span"],
        "cloth_body_attachment_valid": bool(seam_metadata.get("shoulder_anchors"))
        and all(seam_metadata.get("cape_roots", {}).get(side) for side in ("left", "right"))
        and bool(seam_metadata.get("skirt_waist_seam")),
        "seam_count": seam_count(seam_metadata),
        "anchor_count": anchor_count(seam_metadata),
        "silhouette_readability_front": round(silhouette_readability, 6),
        "yaw30_cloth_readability": round(yaw30_readability, 6),
        "side_volume_readability": round(side_readability, 6),
        "material_alpha_stability": round(material_alpha_stability, 6),
        "cloth_front_visual_candidate_status": front_status,
        "cloth_dcc_handoff_status": dcc_status,
    }


def write_failure_report(paths: ActuatorPaths, gate_metrics: dict[str, Any], purity: dict[str, Any], side_volume: dict[str, Any]) -> Path | None:
    if gate_metrics["cloth_side_volume_present"] and gate_metrics["cloth_edge_thickness_present"]:
        return None
    path = paths.output_dir / "validation_ci" / "failure_report.json"
    write_json(
        path,
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "route": GATE_NAME,
            "status": "side_volume_failed_cloth_blocked",
            "metrics": gate_metrics,
            "purity": purity,
            "side_volume": side_volume,
            "integration": "blocked",
        },
    )
    return path


def write_obj(path: Path, panels: list[ClothPanel], seam_metadata: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    mtl_path = path.with_suffix(".mtl")
    lines = ["# YUNA semantic v9 cloth seam-surface candidate", f"mtllib {mtl_path.name}"]
    vertex_offset = 0
    seam_vertices: list[tuple[float, float, float]] = []

    for panel in panels:
        lines.append(f"o {panel.id}")
        for x, y, z in panel.mesh.vertices:
            lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
        for u, v in panel.mesh.uvs:
            lines.append(f"vt {u:.6f} {v:.6f}")
        current_material = None
        for face, material_index in zip(panel.mesh.faces, panel.mesh.face_materials, strict=True):
            material = f"{panel.source_part_id}_front_texture" if material_index == 0 else "cloth_solidify_edge_material"
            if material != current_material:
                lines.append(f"usemtl {material}")
                current_material = material
            refs = [f"{idx + 1 + vertex_offset}/{idx + 1 + vertex_offset}" for idx in face]
            lines.append("f " + " ".join(refs))
        vertex_offset += len(panel.mesh.vertices)

    def add_seam_line(name: str, points: list[dict[str, Any]]) -> None:
        nonlocal vertex_offset
        if len(points) < 2:
            return
        lines.append(f"o {name}")
        lines.append("usemtl cloth_seam_guide_material")
        refs: list[str] = []
        for point in points:
            world = tuple(float(value) for value in point["world"])
            seam_vertices.append(world)
            lines.append(f"v {world[0]:.6f} {world[1]:.6f} {world[2]:.6f}")
            vertex_offset += 1
            refs.append(str(vertex_offset))
        lines.append("l " + " ".join(refs))

    anchors = seam_metadata.get("shoulder_anchors", {})
    if anchors:
        add_seam_line("cloth_shoulder_anchor_line", [anchors["left"], anchors["right"]])
    for side, points in seam_metadata.get("cape_roots", {}).items():
        add_seam_line(f"cloth_cape_root_{side}", points)
    add_seam_line("cloth_skirt_waist_seam", seam_metadata.get("skirt_waist_seam", []))
    for part_id, points in seam_metadata.get("lower_cloth_edge", {}).items():
        add_seam_line(f"cloth_lower_edge_{part_id}", points)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    material_lines: list[str] = []
    for panel in panels:
        material_lines.extend(
            [
                f"newmtl {panel.source_part_id}_front_texture",
                "Ka 1.000 1.000 1.000",
                "Kd 1.000 1.000 1.000",
                "Ks 0.040 0.040 0.050",
                "d 1.000",
                f"map_Kd ../textures/{panel.texture_path.name}",
                "",
            ]
        )
    material_lines.extend(
        [
            "newmtl cloth_seam_guide_material",
            "Ka 0.000 0.760 0.920",
            "Kd 0.000 0.760 0.920",
            "Ks 0.050 0.080 0.090",
            "d 1.000",
            "",
            "newmtl cloth_solidify_edge_material",
            "Ka 0.000 0.520 0.620",
            "Kd 0.000 0.660 0.760",
            "Ks 0.080 0.120 0.140",
            "d 1.000",
        ]
    )
    mtl_path.write_text("\n".join(material_lines) + "\n", encoding="utf-8")
    return mtl_path


def blender_export_glb(
    glb_path: Path,
    panels: list[ClothPanel],
    seam_metadata: dict[str, Any],
    repo_root: Path,
    config: ClothVariantConfig = DEFAULT_VARIANT_CONFIG,
) -> dict[str, Any]:
    blender = find_blender()
    if blender is None:
        return {"status": "skipped_with_reason", "reason": "blender_not_found", "glb_exists": False}

    payload = [
        {
            "id": panel.id,
            "source_part_id": panel.source_part_id,
            "texture_path": str(panel.texture_path),
            "vertices": panel.mesh.vertices,
            "faces": panel.mesh.faces,
            "uvs": panel.mesh.uvs,
            "face_materials": panel.mesh.face_materials,
            "seam_metadata": panel.seam_metadata,
            "solidify_metadata": panel.solidify_metadata,
        }
        for panel in panels
    ]
    payload_json = json.dumps(payload)
    seam_json = json.dumps(seam_metadata)
    seam_half_width = 0.008 * config.seam_emphasis
    script = f"""
import bpy
import json

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
try:
    bpy.context.preferences.filepaths.save_version = 0
except Exception:
    pass

PANELS = json.loads({payload_json!r})
SEAMS = json.loads({seam_json!r})

seam_mat = bpy.data.materials.new('cloth_seam_guide_material')
seam_mat.diffuse_color = (0.0, 0.76, 0.92, 1.0)
seam_mat.use_nodes = True
seam_mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (0.0, 0.76, 0.92, 1.0)

edge_mat = bpy.data.materials.new('cloth_solidify_edge_material')
edge_mat.diffuse_color = (0.0, 0.66, 0.76, 1.0)
edge_mat.use_nodes = True
edge_bsdf = edge_mat.node_tree.nodes.get('Principled BSDF')
edge_bsdf.inputs['Base Color'].default_value = (0.0, 0.66, 0.76, 1.0)
edge_bsdf.inputs['Roughness'].default_value = 0.66
if 'Emission Color' in edge_bsdf.inputs:
    edge_bsdf.inputs['Emission Color'].default_value = (0.0, 0.42, 0.48, 1.0)
if 'Emission Strength' in edge_bsdf.inputs:
    edge_bsdf.inputs['Emission Strength'].default_value = 0.35

for item in PANELS:
    mat = bpy.data.materials.new(item['source_part_id'] + '_front_texture')
    mat.use_nodes = True
    mat.blend_method = 'CLIP'
    mat.alpha_threshold = 0.18
    mat.show_transparent_back = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(item['texture_path'], check_existing=True)
    tex.extension = 'CLIP'
    mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    mat.node_tree.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    bsdf.inputs['Roughness'].default_value = 0.64

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
    obj.data.materials.append(mat)
    obj.data.materials.append(edge_mat)
    obj['semantic_part'] = item['source_part_id']
    obj['actuator'] = 'cloth_seam_surface_v0'
    obj['candidate_only'] = True
    obj['dcc_handoff_only'] = True
    obj['replace_in_beauty_glb'] = False
    obj['production_cloth_topology'] = False
    obj['seam_metadata'] = json.dumps(item['seam_metadata'])
    obj['solidify_metadata'] = json.dumps(item['solidify_metadata'])
    obj['cloth_edge_thickness'] = item['solidify_metadata']['edge_thickness']
    obj['cloth_depth_span'] = item['solidify_metadata']['depth_span']
    for idx, poly in enumerate(obj.data.polygons):
        poly.material_index = item['face_materials'][idx]

def add_empty(name, location, payload):
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=tuple(location))
    empty = bpy.context.object
    empty.name = name
    empty.empty_display_size = 0.075
    empty['actuator'] = 'cloth_seam_surface_v0'
    empty['semantic_part'] = payload.get('part_id', 'cloth')
    empty['cloth_seam_label'] = payload.get('label', name)
    empty['replace_in_beauty_glb'] = False

def add_seam_mesh(name, points):
    if len(points) < 2:
        return
    verts = []
    faces = []
    half_width = {seam_half_width!r}
    for point in points:
        x, y, z = point['world']
        verts.append((x - half_width, y - 0.002, z))
        verts.append((x + half_width, y - 0.002, z))
    for idx in range(len(points) - 1):
        a = idx * 2
        faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new(name + '_mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(seam_mat)
    obj.display_type = 'WIRE'
    obj.show_in_front = True
    obj['actuator'] = 'cloth_seam_surface_v0'
    obj['semantic_part'] = 'cloth_seam_metadata'
    obj['candidate_only'] = True
    obj['replace_in_beauty_glb'] = False
    for point in points:
        add_empty(name + '_' + point.get('label', 'point'), point['world'], point)

anchors = SEAMS.get('shoulder_anchors', {{}})
if anchors:
    add_seam_mesh('cloth_shoulder_anchors', [anchors['left'], anchors['right']])
for side, points in SEAMS.get('cape_roots', {{}}).items():
    add_seam_mesh('cloth_cape_root_' + side, points)
add_seam_mesh('cloth_skirt_waist_seam', SEAMS.get('skirt_waist_seam', []))
for part_id, points in SEAMS.get('lower_cloth_edge', {{}}).items():
    add_seam_mesh('cloth_lower_edge_' + part_id, points)

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


def run_blender_validation_ci(paths: ActuatorPaths) -> dict[str, Any]:
    report_path = paths.output_dir / "validation_ci" / "validation_ci_report.json"
    blender = find_blender()
    if blender is None:
        skipped = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "route": "blender_semantic_validation_v0",
            "status": "skipped_with_reason",
            "reason": "blender_not_found",
            "screenshots": {},
        }
        write_json(report_path, skipped)
        return skipped
    if not paths.glb_path.exists():
        skipped = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "route": "blender_semantic_validation_v0",
            "status": "skipped_with_reason",
            "reason": "candidate_glb_missing",
            "screenshots": {},
        }
        write_json(report_path, skipped)
        return skipped

    command = [
        "python3",
        str(paths.character_package / "tools" / "run_blender_semantic_validation.py"),
        "--baseline-glb",
        str(paths.character_package / "semantic_layer_v8" / "exports" / "yuna_semantic_layer_v8.glb"),
        "--cage-glb",
        str(paths.character_package / "semantic_layer_v8" / "exports" / "yuna_semantic_layer_v8_cage_debug.glb"),
        "--candidate-glb",
        str(paths.glb_path),
        "--candidate-report",
        str(paths.report_path),
        "--output-dir",
        str(paths.output_dir / "validation_ci"),
        "--report",
        str(report_path),
        "--blender",
        blender,
    ]
    result = subprocess.run(
        command,
        cwd=str(paths.repo_root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if report_path.exists():
        report = load_json(report_path)
    else:
        report = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "route": "blender_semantic_validation_v0",
            "status": "failed",
            "reason": "validation_report_missing",
            "screenshots": {},
        }
        write_json(report_path, report)
    report["wrapper_exit_code"] = result.returncode
    report["wrapper_log_tail"] = result.stdout.splitlines()[-80:]
    write_json(report_path, report)
    return report


def build_spec(
    paths: ActuatorPaths,
    panels: list[ClothPanel],
    seam_metadata: dict[str, Any],
    gate_metrics: dict[str, Any],
    config: ClothVariantConfig = DEFAULT_VARIANT_CONFIG,
) -> dict[str, Any]:
    route = ROUTE if config.name == "base" else "cloth_seam_surface_v1_review_pack"
    return {
        "route": route,
        "variant": config.name,
        "hypothesis": config.hypothesis,
        "source_route": "semantic_layer_v8_beauty_main_debug_cage_split",
        "baseline": "semantic_layer_v8",
        "boundary": "Independent cloth seam-surface DCC handoff candidate only. It does not replace v8 beauty cloth.",
        "part": {
            "id": PART_ID,
            "target_parts": list(TARGET_PART_IDS),
            "category": "cloth",
            "generator": ACTUATOR_NAME,
            "replace_in_beauty_glb": False,
            "candidate_only": True,
            "dcc_handoff_only": True,
            "production_cloth_topology": False,
        },
        "mesh": combined_summary(panels),
        "seams": seam_metadata,
        "validation_gates": {
            GATE_NAME: {
                "metrics": gate_metrics,
                "overlay_front_is_acceptance_gate": False,
                "candidate_only": True,
            },
        },
        "exports": {
            "obj": display_path(paths.obj_path, paths.repo_root),
            "glb": display_path(paths.glb_path, paths.repo_root),
            "blend": display_path(paths.glb_path.with_suffix(".blend"), paths.repo_root),
            "report": display_path(paths.report_path, paths.repo_root),
        },
    }


def run_cloth_seam_surface_variant(paths: ActuatorPaths, config: ClothVariantConfig = DEFAULT_VARIANT_CONFIG) -> ActuatorResult:
    route = ROUTE if config.name == "base" else "cloth_seam_surface_v1_review_pack"
    warnings: list[str] = [
        f"cloth_seam_surface {config.name} is a candidate DCC handoff route, not production cloth topology.",
        "v8 beauty cloth remains active; replace_in_beauty_glb=false.",
        "hair route still blocks cloth integration; this route does not mark cloth unblocked.",
    ]
    errors: list[str] = []
    try:
        panels = build_cloth_panels(paths.character_package, config)
    except Exception as exc:
        errors.append(str(exc))
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
        write_json(paths.report_path, {"created_at": datetime.now(timezone.utc).isoformat(), "route": route, "variant": config.name, **result.to_dict()})
        return result

    paths.output_dir.mkdir(parents=True, exist_ok=True)
    paths.spec_path.parent.mkdir(parents=True, exist_ok=True)
    paths.obj_path.parent.mkdir(parents=True, exist_ok=True)
    prepare_output_textures(paths, panels)
    seam_metadata = combined_seam_metadata(panels)
    write_obj(paths.obj_path, panels, seam_metadata)
    purity_review = write_cloth_purity_assets(paths, panels)
    side_volume_review = write_side_volume_diagnostic(paths, panels)
    gate_metrics = combine_gate_metrics(purity_review, side_volume_review, seam_metadata, config)
    failure_report_path = write_failure_report(paths, gate_metrics, purity_review, side_volume_review)
    glb_report = blender_export_glb(paths.glb_path, panels, seam_metadata, paths.repo_root, config)
    if glb_report.get("status") != "ok":
        warnings.append("GLB/BLEND/screenshots are skipped or incomplete; see validation.blender_glb_export and validation.validation_ci.")
    if failure_report_path is not None:
        warnings.append("Side-volume gate failed; see validation_ci/failure_report.json.")

    generated_files = {
        "spec": display_path(paths.spec_path, paths.repo_root),
        "obj": display_path(paths.obj_path, paths.repo_root),
        "mtl": display_path(paths.obj_path.with_suffix(".mtl"), paths.repo_root),
        "glb": display_path(paths.glb_path, paths.repo_root),
        "blend": display_path(paths.glb_path.with_suffix(".blend"), paths.repo_root),
        "report": display_path(paths.report_path, paths.repo_root),
        "validation_ci_report": display_path(paths.output_dir / "validation_ci" / "validation_ci_report.json", paths.repo_root),
        "cloth_target_mask_union": purity_review["files"]["cloth_target_mask_union"],
        "cloth_forbidden_noncloth_zone": purity_review["files"]["cloth_forbidden_noncloth_zone"],
        "cloth_candidate_vs_target_overlay": purity_review["files"]["cloth_candidate_vs_target_overlay"],
        "cloth_purity_report": purity_review["files"]["cloth_purity_report"],
        "cloth_side_volume_debug": side_volume_review["files"]["cloth_side_volume_debug"],
        "cloth_depth_span_report": side_volume_review["files"]["cloth_depth_span_report"],
    }
    if failure_report_path is not None:
        generated_files["failure_report"] = display_path(failure_report_path, paths.repo_root)
    mesh_summary = combined_summary(panels)
    validation = {
        "independent_objects": True,
        "target_parts_present": [panel.source_part_id for panel in panels],
        "has_cloth_surfaces": all(len(panel.mesh.faces) > 0 for panel in panels),
        "has_uvs": all(len(panel.mesh.uvs) == len(panel.mesh.vertices) for panel in panels),
        "quad_faces_only": True,
        "has_shoulder_anchors": bool(seam_metadata["shoulder_anchors"]),
        "has_cape_roots": all(seam_metadata["cape_roots"].get(side) for side in ("left", "right")),
        "has_skirt_waist_seam": bool(seam_metadata["skirt_waist_seam"]),
        "has_lower_cloth_edge": set(seam_metadata["lower_cloth_edge"]) == set(TARGET_PART_IDS),
        "side_back_are_soft_constraints": True,
        "replace_in_beauty_glb": False,
        "v8_beauty_replaced": False,
        "candidate_only": True,
        "dcc_handoff_only": True,
        "production_cloth_topology": False,
        "ready_for_cloth_integration": False,
        "hair_route_still_blocks_cloth_integration": True,
        "current_blocker": "hair route still blocks cloth integration",
        "overlay_front_is_acceptance_gate": False,
        "cloth_volume_and_purity_gate": GATE_NAME,
        **gate_metrics,
        "cloth_purity_review": purity_review,
        "cloth_side_volume_review": side_volume_review,
        "failure_report": display_path(failure_report_path, paths.repo_root) if failure_report_path is not None else None,
        "obj": file_record(paths.obj_path),
        "glb": file_record(paths.glb_path),
        "blender_glb_export": glb_report,
    }

    result = ActuatorResult(
        actuator=ACTUATOR_NAME,
        status="manual_review_required",
        part_id=PART_ID,
        decision_source=display_path(paths.character_package / "semantic_layer_v9_candidate" / "filter_report.json", paths.repo_root),
        generated_files=generated_files,
        mesh_summary=mesh_summary,
        validation=validation,
        warnings=warnings,
        errors=[],
    )
    contract_errors = validate_cloth_candidate_report({"route": ROUTE, **result.to_dict()})
    if contract_errors:
        result.status = "failed"
        result.errors.extend(contract_errors)

    write_json(paths.spec_path, build_spec(paths, panels, seam_metadata, gate_metrics, config))
    write_json(paths.report_path, {"created_at": datetime.now(timezone.utc).isoformat(), "route": route, "variant": config.name, "seams": seam_metadata, **result.to_dict()})

    validation_ci = run_blender_validation_ci(paths)
    validation_ci[GATE_NAME] = {
        "metrics": gate_metrics,
        "purity": purity_review,
        "side_volume": side_volume_review,
        "overlay_front_is_acceptance_gate": False,
        "candidate_only": True,
        "cloth_integration_unblocked": False,
    }
    validation_ci.setdefault("candidate_contract", {})["cloth_volume_and_purity_gate"] = {
        "cloth_side_volume_present": gate_metrics["cloth_side_volume_present"],
        "cloth_edge_thickness_present": gate_metrics["cloth_edge_thickness_present"],
        "replace_in_beauty_glb": False,
        "candidate_only": True,
    }
    write_json(paths.output_dir / "validation_ci" / "validation_ci_report.json", validation_ci)
    result.validation["validation_ci"] = {
        "status": validation_ci.get("status"),
        "report": display_path(paths.output_dir / "validation_ci" / "validation_ci_report.json", paths.repo_root),
        "screenshot_count": len(validation_ci.get("screenshots", {})),
        GATE_NAME: validation_ci[GATE_NAME],
    }
    write_json(paths.report_path, {"created_at": datetime.now(timezone.utc).isoformat(), "route": route, "variant": config.name, "seams": seam_metadata, **result.to_dict()})
    return result


@register("cloth_seam_surface_v0")
def run_cloth_seam_surface(paths: ActuatorPaths) -> ActuatorResult:
    return run_cloth_seam_surface_variant(paths, DEFAULT_VARIANT_CONFIG)


def variant_paths(repo_root: Path, character_package: Path, variant_name: str) -> ActuatorPaths:
    output_dir = character_package / "semantic_layer_v9_cloth" / "variants" / variant_name
    stem = f"yuna_semantic_layer_v9_cloth_{variant_name}"
    return ActuatorPaths(
        repo_root=repo_root,
        character_package=character_package,
        output_dir=output_dir,
        spec_path=output_dir / "specs" / f"{stem}.json",
        obj_path=output_dir / "exports" / f"{stem}.obj",
        glb_path=output_dir / "exports" / f"{stem}.glb",
        report_path=output_dir / "validation_report.json",
    )


def append_iteration_log(log_path: Path, round_index: int, config: ClothVariantConfig, report: dict[str, Any], validation_ci: dict[str, Any]) -> None:
    metrics = report.get("validation", {})
    screenshots = validation_ci.get("screenshots", {})
    lines = [
        f"## Round {round_index}: `{config.name}`",
        "",
        f"- Hypothesis: {config.hypothesis}",
        "- Changed parameters:",
        f"  - thickness_scale: {config.thickness_scale}",
        f"  - curvature_scale: {config.curvature_scale}",
        f"  - cape_drape_bias: {config.cape_drape_bias}",
        f"  - skirt_drape_bias: {config.skirt_drape_bias}",
        f"  - seam_emphasis: {config.seam_emphasis}",
        "- Screenshots generated:",
    ]
    for key in ("candidate_front", "overlay_front", "yaw15", "yaw30", "side", "wire", "exploded"):
        record = screenshots.get(key, {})
        lines.append(f"  - {key}: {record.get('path', 'missing')}")
    lines.extend(
        [
            "- Metrics:",
            f"  - cloth_mask_purity_ratio: {metrics.get('cloth_mask_purity_ratio')}",
            f"  - non_cloth_texture_leak_ratio: {metrics.get('non_cloth_texture_leak_ratio')}",
            f"  - cloth_side_volume_present: {metrics.get('cloth_side_volume_present')}",
            f"  - cloth_edge_thickness_present: {metrics.get('cloth_edge_thickness_present')}",
            f"  - cloth_panel_curvature_score: {metrics.get('cloth_panel_curvature_score')}",
            f"  - cloth_drape_depth_span: {metrics.get('cloth_drape_depth_span')}",
            f"  - silhouette_readability_front: {metrics.get('silhouette_readability_front')}",
            f"  - yaw30_cloth_readability: {metrics.get('yaw30_cloth_readability')}",
            f"  - side_volume_readability: {metrics.get('side_volume_readability')}",
            f"- Failure mode: {config.failure_mode}",
            f"- Next adjustment: {config.next_adjustment}",
            "",
        ]
    )
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def comparison_score(metrics: dict[str, Any]) -> float:
    return round(
        float(metrics.get("silhouette_readability_front", 0.0)) * 0.30
        + float(metrics.get("yaw30_cloth_readability", 0.0)) * 0.25
        + float(metrics.get("side_volume_readability", 0.0)) * 0.25
        + float(metrics.get("material_alpha_stability", 0.0)) * 0.20,
        6,
    )


def build_contact_sheet(variants_dir: Path, variant_reports: list[dict[str, Any]], repo_root: Path) -> Path:
    columns = ("candidate_front", "overlay_front", "yaw30", "side")
    tile_w, tile_h = 260, 346
    header_h = 42
    label_h = 32
    sheet = Image.new("RGB", (tile_w * len(columns), header_h + (tile_h + label_h) * len(variant_reports)), (18, 22, 25))
    draw = ImageDraw.Draw(sheet)
    for col, label in enumerate(columns):
        draw.text((col * tile_w + 10, 12), label, fill=(230, 238, 240))
    for row, report in enumerate(variant_reports):
        variant = report["variant"]
        ci_report = load_json(repo_root / report["generated_files"]["validation_ci_report"])
        screenshots = ci_report.get("screenshots", {})
        y0 = header_h + row * (tile_h + label_h)
        draw.text((10, y0 + 8), variant, fill=(0, 220, 255))
        for col, key in enumerate(columns):
            record = screenshots.get(key, {})
            raw_path = record.get("path")
            path = repo_root / raw_path if raw_path else None
            x = col * tile_w
            if path is not None and path.is_file():
                image = Image.open(path).convert("RGB")
                resampling = getattr(Image, "Resampling", Image).LANCZOS
                image.thumbnail((tile_w, tile_h), resampling)
                sheet.paste(image, (x + (tile_w - image.width) // 2, y0 + label_h + (tile_h - image.height) // 2))
            else:
                draw.rectangle((x + 8, y0 + label_h + 8, x + tile_w - 8, y0 + label_h + tile_h - 8), outline=(180, 60, 60), width=2)
                draw.text((x + 18, y0 + label_h + 18), "missing", fill=(240, 100, 100))
    path = variants_dir / "cloth_variants_contact_sheet.png"
    sheet.save(path)
    return path


def write_manual_review_doc(
    variants_dir: Path,
    comparison: dict[str, Any],
    contact_sheet: Path,
    repo_root: Path,
) -> Path:
    path = variants_dir / "manual_review_cloth_v1.md"
    lines = [
        "# Cloth Seam Surface v1 Manual Review",
        "",
        "- Status: `manual_review_required`",
        "- Candidate-only: yes",
        "- Production-ready: no",
        "- `replace_in_beauty_glb`: false for every variant",
        "- Current blocker: hair route still blocks cloth integration",
        f"- Contact sheet: `{display_path(contact_sheet, repo_root)}`",
        f"- Recommended variant: `{comparison['recommended_variant']}`",
        "",
        "## Variant Metrics",
        "",
        "| Variant | Score | Purity | Leak | Drape span | Side readable | Front readable | Status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in comparison["variants"]:
        metrics = item["metrics"]
        lines.append(
            f"| {item['variant']} | {item['score']} | {metrics['cloth_mask_purity_ratio']} | "
            f"{metrics['non_cloth_texture_leak_ratio']} | {metrics['cloth_drape_depth_span']} | "
            f"{metrics['side_volume_readability']} | {metrics['silhouette_readability_front']} | "
            f"{item['status']} |"
        )
    lines.extend(
        [
            "",
            "## Review Notes",
            "",
            "- `minimal` is the conservative comparison target.",
            f"- `{comparison['recommended_variant']}` is the current scoring recommendation for manual art review.",
            "- `technical` is useful for DCC seam and hard-edge interpretation, but it should not be treated as final art.",
            "",
            "## Next Goal",
            "",
            "Manual art review should choose one direction, then a DCC artist should rebuild selected cloth as real topology with UV, rigging, and deformation tests. Hair remains the integration blocker until its route is manually accepted.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run_cloth_review_pack(repo_root: Path, character_package: Path) -> dict[str, Any]:
    variants_dir = character_package / "semantic_layer_v9_cloth" / "variants"
    variants_dir.mkdir(parents=True, exist_ok=True)
    iteration_log = variants_dir / "cloth_iteration_log.md"
    iteration_log.write_text("# Cloth Seam Surface v1 Iteration Log\n\n", encoding="utf-8")

    variant_reports: list[dict[str, Any]] = []
    for index, config in enumerate(REVIEW_VARIANT_CONFIGS, start=1):
        paths = variant_paths(repo_root, character_package, config.name)
        result = run_cloth_seam_surface_variant(paths, config)
        report = load_json(paths.report_path)
        validation_ci = load_json(paths.output_dir / "validation_ci" / "validation_ci_report.json")
        append_iteration_log(iteration_log, index, config, report, validation_ci)
        if result.status == "failed":
            report["variant_failure"] = result.errors
        variant_reports.append(report)

    variants_payload: list[dict[str, Any]] = []
    for report in variant_reports:
        metrics = report["validation"]
        variants_payload.append(
            {
                "variant": report["variant"],
                "status": report["status"],
                "score": comparison_score(metrics),
                "recommended_for_manual_review": False,
                "replace_in_beauty_glb": metrics["replace_in_beauty_glb"],
                "ready_for_cloth_integration": metrics["ready_for_cloth_integration"],
                "metrics": {
                    key: metrics[key]
                    for key in (
                        "cloth_mask_purity_ratio",
                        "non_cloth_texture_leak_ratio",
                        "cloth_side_volume_present",
                        "cloth_edge_thickness_present",
                        "cloth_panel_curvature_score",
                        "cloth_drape_depth_span",
                        "cloth_body_attachment_valid",
                        "seam_count",
                        "anchor_count",
                        "silhouette_readability_front",
                        "yaw30_cloth_readability",
                        "side_volume_readability",
                        "material_alpha_stability",
                    )
                },
                "files": report["generated_files"],
            }
        )
    recommended = max(variants_payload, key=lambda item: (item["score"], item["variant"]))
    recommended["recommended_for_manual_review"] = True
    contact_sheet = build_contact_sheet(variants_dir, variant_reports, repo_root)
    comparison = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": "cloth_seam_surface_v1_review_pack",
        "status": "manual_review_required",
        "candidate_only": True,
        "production_ready": False,
        "replace_in_beauty_glb": False,
        "cloth_integration_ready": False,
        "current_blocker": "hair route still blocks cloth integration",
        "round_count": len(REVIEW_VARIANT_CONFIGS),
        "recommended_variant": recommended["variant"],
        "contact_sheet": display_path(contact_sheet, repo_root),
        "iteration_log": display_path(iteration_log, repo_root),
        "variants": variants_payload,
    }
    comparison_path = variants_dir / "cloth_variants_comparison_report.json"
    write_json(comparison_path, comparison)
    manual_review = write_manual_review_doc(variants_dir, comparison, contact_sheet, repo_root)
    comparison["manual_review"] = display_path(manual_review, repo_root)
    write_json(comparison_path, comparison)
    return comparison
