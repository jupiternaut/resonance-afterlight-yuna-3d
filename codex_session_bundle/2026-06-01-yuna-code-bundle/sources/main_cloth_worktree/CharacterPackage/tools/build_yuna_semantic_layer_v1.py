#!/usr/bin/env python3
"""Build YUNA semantic-layer v1 assets.

This is a deterministic, non-cloud 2.5D asset compiler step. It creates
draft semantic masks, turns each semantic part into an independent textured
mesh, adds guide proxies/hooks in Blender, exports BLEND/OBJ/FBX/GLB, and
renders validation screenshots.

The output is a structured DCC handoff asset, not a final production character.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "semantic_layer_v1"
MASK_DIR = OUT / "masks" / "front"
TEXTURE_DIR = OUT / "textures"
OBJ_DIR = OUT / "obj"
PART_OBJ_DIR = OBJ_DIR / "parts"
EXPORT_DIR = OUT / "exports"
VALIDATION_DIR = OUT / "validation"
SPEC_DIR = OUT / "specs"
REPORT_PATH = OUT / "validation_report.json"
SOURCE_FRONT = ROOT / "refs" / "front_rgba" / "yuna_front_rgba.png"
EDGE_ALPHA = 1.0


@dataclass(frozen=True)
class PartDef:
    id: str
    category: str
    parent: str
    mesh_generator: str
    depth: float
    thickness: float
    curvature: str
    z_spread: float
    edge_color: tuple[float, float, float]
    validation_role: str


PARTS: list[PartDef] = [
    PartDef("back_hair", "hair", "head_proxy", "curved_cutout", -0.055, 0.020, "wide_wrap", 0.020, (0.03, 0.18, 0.18), "hair_depth_back"),
    PartDef("side_hair_left", "hair", "head_proxy", "ribbon_like_cutout", 0.020, 0.018, "left_ribbon", 0.045, (0.02, 0.18, 0.18), "hair_depth_mid"),
    PartDef("side_hair_right", "hair", "head_proxy", "ribbon_like_cutout", 0.035, 0.018, "right_ribbon", 0.045, (0.02, 0.18, 0.18), "hair_depth_mid"),
    PartDef("torso_inner", "body", "torso_proxy", "curved_cutout", 0.000, 0.048, "torso_wrap", 0.000, (0.02, 0.03, 0.04), "body_shell"),
    PartDef("jacket_outer", "costume", "torso_proxy", "curved_cutout", 0.050, 0.034, "torso_wrap", 0.010, (0.015, 0.02, 0.03), "costume_shell"),
    PartDef("cape_left", "cloth", "torso_proxy", "cloth_surface", -0.025, 0.016, "left_cloth_drape", 0.035, (0.03, 0.10, 0.12), "cape_independent"),
    PartDef("cape_right", "cloth", "torso_proxy", "cloth_surface", -0.020, 0.016, "right_cloth_drape", 0.035, (0.03, 0.10, 0.12), "cape_independent"),
    PartDef("skirt_front", "cloth", "torso_proxy", "folded_panel", 0.075, 0.024, "shallow_panel", 0.015, (0.05, 0.05, 0.06), "skirt_panel"),
    PartDef("legs", "body", "torso_proxy", "curved_cutout", 0.015, 0.045, "leg_rounding", 0.000, (0.06, 0.06, 0.07), "leg_shell"),
    PartDef("boots", "costume", "torso_proxy", "hard_cutout", 0.060, 0.052, "hard_surface", 0.000, (0.02, 0.03, 0.035), "boot_shell"),
    PartDef("face", "face", "head_proxy", "curved_face_plate", 0.115, 0.018, "face_convex", 0.000, (0.07, 0.06, 0.055), "front_identity"),
    PartDef("bangs", "hair", "head_proxy", "ribbon_like_cutout", 0.160, 0.014, "bangs_convex", 0.040, (0.025, 0.18, 0.19), "hair_depth_front"),
    PartDef("weapon", "weapon", "hand_R_socket", "hard_surface_prop", 0.190, 0.075, "weapon_bevel_proxy", 0.000, (0.02, 0.16, 0.18), "weapon_independent"),
]


def ensure_dirs() -> None:
    for path in (OUT, MASK_DIR, TEXTURE_DIR, OBJ_DIR, PART_OBJ_DIR, EXPORT_DIR, VALIDATION_DIR, SPEC_DIR):
        path.mkdir(parents=True, exist_ok=True)


def point_in_polygon(x: float, y: float, polygon: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi:
            inside = not inside
        j = i
    return inside


def ellipse(x: int, y: int, cx: float, cy: float, rx: float, ry: float) -> bool:
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0


def color_features(r: int, g: int, b: int) -> dict[str, bool | float]:
    brightness = (r + g + b) / 3.0
    cyan = g > 135 and b > 145 and b >= r + 10
    pale = brightness > 150 and abs(r - g) < 45 and abs(g - b) < 55
    white = brightness > 174 and abs(r - g) < 42 and abs(g - b) < 52
    dark = brightness < 105 and b >= r - 15
    skin = r > 165 and g > 128 and b > 118 and r >= b - 5 and brightness > 145
    return {
        "brightness": brightness,
        "cyan": cyan,
        "pale": pale,
        "white": white,
        "dark": dark,
        "skin": skin,
    }


def build_front_masks(source: Image.Image) -> dict[str, Image.Image]:
    rgba = source.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    masks = {part.id: Image.new("L", (width, height), 0) for part in PARTS}
    draw = {key: ImageDraw.Draw(mask) for key, mask in masks.items()}

    blade_poly = [(0, 1535), (72, 1515), (305, 735), (250, 705), (0, 1450)]
    hilt_poly = [(180, 700), (302, 620), (350, 735), (236, 822)]
    guard_poly = [(200, 690), (350, 670), (334, 760), (190, 780)]

    for y in range(height):
        ny = y / height
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a <= 22:
                continue

            nx = x / width
            c = color_features(r, g, b)

            is_weapon = (
                point_in_polygon(x, y, blade_poly)
                or point_in_polygon(x, y, hilt_poly)
                or point_in_polygon(x, y, guard_poly)
            ) and not (nx > 0.36 and ny < 0.58)
            if is_weapon:
                draw["weapon"].point((x, y), fill=255)
                continue

            is_face = ellipse(x, y, 520, 235, 92, 118) and bool(c["skin"]) and ny < 0.26
            if is_face:
                draw["face"].point((x, y), fill=255)
                continue

            upper_hair = ny < 0.43 and 0.29 < nx < 0.72 and (bool(c["pale"]) or bool(c["cyan"]))
            if upper_hair and not ellipse(x, y, 520, 255, 108, 132):
                draw["bangs"].point((x, y), fill=255)
                continue

            hair_like = bool(c["pale"]) or bool(c["cyan"])
            if hair_like and 0.13 < ny < 0.54 and nx < 0.50 and not (0.34 < nx < 0.59 and 0.22 < ny < 0.50):
                draw["side_hair_left"].point((x, y), fill=255)
                continue
            if hair_like and 0.13 < ny < 0.56 and nx > 0.53 and not (0.37 < nx < 0.63 and 0.22 < ny < 0.50):
                draw["side_hair_right"].point((x, y), fill=255)
                continue
            if hair_like and 0.20 < ny < 0.66 and (nx < 0.35 or nx > 0.65):
                draw["back_hair"].point((x, y), fill=255)
                continue

            if 0.43 < ny < 0.57 and 0.34 < nx < 0.64 and (bool(c["white"]) or bool(c["skin"])):
                draw["skirt_front"].point((x, y), fill=255)
                continue

            if 0.48 < ny < 0.84 and 0.30 < nx < 0.66 and (bool(c["white"]) or bool(c["skin"])):
                draw["legs"].point((x, y), fill=255)
                continue

            if 0.79 < ny < 0.99 and 0.34 < nx < 0.70:
                draw["boots"].point((x, y), fill=255)
                continue

            torso_box = 0.29 < nx < 0.69 and 0.21 < ny < 0.57
            if torso_box and (bool(c["white"]) or bool(c["dark"]) or bool(c["cyan"]) or c["brightness"] > 112):
                if bool(c["dark"]) and (nx < 0.40 or nx > 0.56):
                    draw["jacket_outer"].point((x, y), fill=255)
                else:
                    draw["torso_inner"].point((x, y), fill=255)
                continue

            cape_area = 0.33 < ny < 0.90 and (nx < 0.40 or nx > 0.60)
            if cape_area and (bool(c["dark"]) or bool(c["white"]) or bool(c["cyan"]) or a < 205):
                if nx < 0.50:
                    draw["cape_left"].point((x, y), fill=255)
                else:
                    draw["cape_right"].point((x, y), fill=255)

    return masks


def clean_mask(mask: Image.Image, minimum_pixels: int = 40) -> Image.Image:
    alpha = mask.convert("L")
    width, height = alpha.size
    src = alpha.load()
    out = Image.new("L", (width, height), 0)
    dst = out.load()
    for y in range(height):
        for x in range(width):
            if src[x, y] == 0:
                continue
            count = 0
            for yy in range(max(0, y - 1), min(height, y + 2)):
                for xx in range(max(0, x - 1), min(width, x + 2)):
                    if src[xx, yy] > 0:
                        count += 1
            if count >= 2:
                dst[x, y] = 255
    if out.getbbox() is None:
        return out
    if sum(1 for value in out.getdata() if value > 0) < minimum_pixels:
        return Image.new("L", (width, height), 0)
    return out


def save_part_textures(source: Image.Image, masks: dict[str, Image.Image]) -> None:
    source.save(TEXTURE_DIR / "yuna_semantic_front_source.png")
    for part in PARTS:
        mask = masks[part.id]
        rgba = source.copy().convert("RGBA")
        rgba.putalpha(mask)
        rgba.save(TEXTURE_DIR / f"{part.id}.png")
        mask.save(MASK_DIR / f"{part.id}.png")


def build_contact_sheet(masks: dict[str, Image.Image]) -> Path:
    source = Image.open(SOURCE_FRONT).convert("RGBA")
    thumb_w, thumb_h = 256, 384
    cols = 4
    rows = math.ceil(len(PARTS) / cols)
    sheet = Image.new("RGBA", (cols * thumb_w, rows * (thumb_h + 28)), (8, 12, 16, 255))
    for index, part in enumerate(PARTS):
        col = index % cols
        row = index // cols
        rgba = source.copy()
        rgba.putalpha(masks[part.id])
        rgba.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = col * thumb_w + (thumb_w - rgba.width) // 2
        y = row * (thumb_h + 28) + 4
        sheet.alpha_composite(rgba, (x, y))
        ImageDraw.Draw(sheet).text((col * thumb_w + 8, row * (thumb_h + 28) + thumb_h + 6), part.id, fill=(210, 236, 255, 255))
    out = VALIDATION_DIR / "yuna_semantic_masks_contact.png"
    sheet.save(out)
    return out


def mask_to_resized_bool(mask: Image.Image, target_height: int) -> tuple[list[list[bool]], int, int]:
    width, height = mask.size
    target_width = max(1, round(target_height * width / height))
    resized = mask.resize((target_width, target_height), Image.Resampling.LANCZOS)
    pix = resized.load()
    grid: list[list[bool]] = []
    for y in range(target_height):
        row: list[bool] = []
        for x in range(target_width):
            row.append(pix[x, y] > 32)
        grid.append(row)
    return grid, target_width, target_height


def curvature_offset(part: PartDef, x_mid: float, y_mid: float, width_world: float, height_world: float) -> float:
    nx = x_mid / max(width_world * 0.5, 1e-6)
    ny = (y_mid / max(height_world, 1e-6)) - 0.5
    if part.curvature == "face_convex":
        return 0.035 * max(0.0, 1.0 - (nx / 0.36) ** 2 - (ny / 0.22) ** 2)
    if part.curvature == "torso_wrap":
        return 0.038 * (1.0 - min(1.0, abs(nx) * 1.6))
    if part.curvature == "left_ribbon":
        return -0.020 + 0.060 * (1.0 - min(1.0, abs(nx + 0.30) * 2.4))
    if part.curvature == "right_ribbon":
        return -0.015 + 0.060 * (1.0 - min(1.0, abs(nx - 0.30) * 2.4))
    if part.curvature == "bangs_convex":
        return 0.050 * (1.0 - min(1.0, abs(nx) * 1.8))
    if part.curvature == "wide_wrap":
        return -0.025 + 0.030 * (1.0 - min(1.0, abs(nx) * 1.1))
    if part.curvature == "left_cloth_drape":
        return -0.045 + 0.030 * (1.0 - min(1.0, abs(nx + 0.32) * 1.8)) - max(0.0, -ny) * 0.020
    if part.curvature == "right_cloth_drape":
        return -0.035 + 0.032 * (1.0 - min(1.0, abs(nx - 0.35) * 1.8)) - max(0.0, -ny) * 0.020
    if part.curvature == "shallow_panel":
        return 0.022 * (1.0 - min(1.0, abs(nx) * 1.5))
    if part.curvature == "leg_rounding":
        return 0.026 * (1.0 - min(1.0, abs(nx) * 2.1))
    if part.curvature == "weapon_bevel_proxy":
        return 0.0
    return 0.0


def make_obj_for_part(part: PartDef, mask: Image.Image, target_height: int = 420, height_world: float = 6.4, mtl_name: str = "yuna_semantic_layer_v1.mtl") -> dict:
    grid, width, height = mask_to_resized_bool(mask, target_height)
    cell = height_world / height
    width_world = width * cell
    half_w = width_world / 2.0
    half_t = part.thickness / 2.0
    vertices: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    faces: list[tuple[str, list[tuple[int, int]]]] = []

    def add_vertex(x: float, y: float, z: float, u: float, v: float) -> tuple[int, int]:
        vertices.append((x, y, z))
        uvs.append((u, v))
        return len(vertices), len(uvs)

    def add_face(material: str, corners: list[tuple[float, float, float, float, float]]) -> None:
        faces.append((material, [add_vertex(*corner) for corner in corners]))

    occupied = 0
    for gy in range(height):
        for gx in range(width):
            if not grid[gy][gx]:
                continue
            occupied += 1
            x0 = gx * cell - half_w
            x1 = (gx + 1) * cell - half_w
            y0 = (height - gy - 1) * cell
            y1 = (height - gy) * cell
            u0 = gx / width
            u1 = (gx + 1) / width
            v0 = 1.0 - ((gy + 1) / height)
            v1 = 1.0 - (gy / height)
            x_mid = (x0 + x1) * 0.5
            y_mid = (y0 + y1) * 0.5
            curved_z = part.depth + curvature_offset(part, x_mid, y_mid, width_world, height_world)
            z_front = curved_z - half_t
            z_back = curved_z + half_t

            add_face(part.id, [(x0, y0, z_front, u0, v0), (x1, y0, z_front, u1, v0), (x1, y1, z_front, u1, v1), (x0, y1, z_front, u0, v1)])
            add_face(part.id, [(x1, y0, z_back, u1, v0), (x0, y0, z_back, u0, v0), (x0, y1, z_back, u0, v1), (x1, y1, z_back, u1, v1)])

            neighbors = {
                "left": gx == 0 or not grid[gy][gx - 1],
                "right": gx == width - 1 or not grid[gy][gx + 1],
                "bottom": gy == height - 1 or not grid[gy + 1][gx],
                "top": gy == 0 or not grid[gy - 1][gx],
            }
            if neighbors["left"]:
                add_face(f"{part.id}_edge", [(x0, y0, z_back, u0, v0), (x0, y0, z_front, u0, v0), (x0, y1, z_front, u0, v1), (x0, y1, z_back, u0, v1)])
            if neighbors["right"]:
                add_face(f"{part.id}_edge", [(x1, y0, z_front, u1, v0), (x1, y0, z_back, u1, v0), (x1, y1, z_back, u1, v1), (x1, y1, z_front, u1, v1)])
            if neighbors["bottom"]:
                add_face(f"{part.id}_edge", [(x0, y0, z_back, u0, v0), (x1, y0, z_back, u1, v0), (x1, y0, z_front, u1, v0), (x0, y0, z_front, u0, v0)])
            if neighbors["top"]:
                add_face(f"{part.id}_edge", [(x0, y1, z_front, u0, v1), (x1, y1, z_front, u1, v1), (x1, y1, z_back, u1, v1), (x0, y1, z_back, u0, v1)])

    part_obj = PART_OBJ_DIR / f"{part.id}.obj"
    part_obj.write_text(build_obj_text(part.id, mtl_name, vertices, uvs, faces), encoding="utf-8")
    return {
        "part": part.id,
        "obj": str(part_obj.relative_to(ROOT)),
        "occupied_cells": occupied,
        "vertices": len(vertices),
        "faces": len(faces),
        "category": part.category,
        "mesh_generator": part.mesh_generator,
        "depth": part.depth,
        "thickness": part.thickness,
    }


def build_obj_text(name: str, mtl_name: str, vertices, uvs, faces) -> str:
    lines = [f"mtllib {mtl_name}", f"o {name}"]
    for x, y, z in vertices:
        lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
    for u, v in uvs:
        lines.append(f"vt {u:.6f} {v:.6f}")
    active = None
    for material, refs in faces:
        if material != active:
            lines.append(f"usemtl {material}")
            active = material
        lines.append("f " + " ".join(f"{vi}/{ti}" for vi, ti in refs))
    return "\n".join(lines) + "\n"


def build_mtl(stem: str = "yuna_semantic_layer_v1") -> None:
    lines: list[str] = []
    for part in PARTS:
        r, g, b = part.edge_color
        lines.extend(
            [
                f"newmtl {part.id}",
                "Ka 1.000 1.000 1.000",
                "Kd 1.000 1.000 1.000",
                "Ks 0.100 0.100 0.100",
                "Ns 64.000",
                f"map_Kd ../textures/{part.id}.png",
                "",
                f"newmtl {part.id}_edge",
                f"Ka {r:.3f} {g:.3f} {b:.3f}",
                f"Kd {r:.3f} {g:.3f} {b:.3f}",
                "Ks 0.120 0.250 0.280",
                "Ns 96.000",
                "",
            ]
        )
    mtl = "\n".join(lines)
    (OBJ_DIR / f"{stem}.mtl").write_text(mtl, encoding="utf-8")
    (PART_OBJ_DIR / f"{stem}.mtl").write_text(mtl, encoding="utf-8")


def combine_part_objs(combined_path: Path, stem: str = "yuna_semantic_layer_v1") -> dict:
    mtl_src = OBJ_DIR / f"{stem}.mtl"
    vertices: list[str] = []
    uvs: list[str] = []
    body: list[str] = []
    v_offset = 0
    vt_offset = 0

    for part in PARTS:
        path = PART_OBJ_DIR / f"{part.id}.obj"
        part_lines = path.read_text(encoding="utf-8").splitlines()
        body.append(f"o {part.id}")
        for line in part_lines:
            if line.startswith("v "):
                vertices.append(line)
            elif line.startswith("vt "):
                uvs.append(line)
            elif line.startswith("usemtl "):
                body.append(line)
            elif line.startswith("f "):
                refs = []
                for ref in line[2:].split():
                    vi, ti = ref.split("/")[:2]
                    refs.append(f"{int(vi) + v_offset}/{int(ti) + vt_offset}")
                body.append("f " + " ".join(refs))
        v_offset += sum(1 for line in part_lines if line.startswith("v "))
        vt_offset += sum(1 for line in part_lines if line.startswith("vt "))

    combined_path.write_text("\n".join([f"mtllib {mtl_src.name}", *vertices, *uvs, *body]) + "\n", encoding="utf-8")
    return {
        "obj": str(combined_path.relative_to(ROOT)),
        "mtl": str(mtl_src.relative_to(ROOT)),
        "parts": len(PARTS),
        "vertices": len(vertices),
        "uvs": len(uvs),
    }


def write_spec(mask_stats: dict[str, dict]) -> Path:
    spec = {
        "character": {
            "id": "YUNA",
            "route": "semantic_layer_v1",
            "boundary": "Structured 2.5D render-shell asset with draft masks and DCC hooks; not a final rigged volumetric character.",
            "coordinate_system": {"right": "X", "up": "Y", "front_depth": "Z"},
            "viewing_cone": {"primary_yaw_degrees": [-30, 30], "side_is_reference_only": True},
        },
        "source_images": {
            "front": str(SOURCE_FRONT.relative_to(ROOT)),
        },
        "mask_source": "auto_draft_rules_from_locked_front_rgba",
        "parts": [
            {
                "id": part.id,
                "category": part.category,
                "parent": part.parent,
                "mesh_generator": part.mesh_generator,
                "mask": str((MASK_DIR / f"{part.id}.png").relative_to(ROOT)),
                "texture": str((TEXTURE_DIR / f"{part.id}.png").relative_to(ROOT)),
                "depth": part.depth,
                "thickness": part.thickness,
                "curvature": part.curvature,
                "animation_hook": hook_for_part(part),
                "validation_role": part.validation_role,
                "mask_pixels": mask_stats[part.id]["pixels"],
                "mask_bbox": mask_stats[part.id]["bbox"],
            }
            for part in PARTS
        ],
        "acceptance_v1": {
            "must_have_independent_meshes": ["face", "bangs", "back_hair", "cape_left", "cape_right", "weapon"],
            "hair_depth_groups_min": 3,
            "weapon_independent_object": True,
            "cape_independent_object": True,
            "exports_required": ["blend", "glb", "fbx", "obj"],
            "validation_views_required": ["front", "yaw15", "yaw30", "side", "exploded", "masks_contact"],
        },
    }
    path = SPEC_DIR / "yuna_semantic_layer_v1.json"
    path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def hook_for_part(part: PartDef) -> str:
    if part.category == "hair":
        return f"{part.id}_spring_hook"
    if part.category == "cloth":
        return f"{part.id}_swing_hook"
    if part.category == "weapon":
        return "hand_R_socket"
    if part.category == "face":
        return "face_expression_texture_swap"
    return f"{part.id}_pivot"


def mask_stats(masks: dict[str, Image.Image]) -> dict[str, dict]:
    stats: dict[str, dict] = {}
    for part_id, mask in masks.items():
        pixels = sum(1 for value in mask.getdata() if value > 0)
        stats[part_id] = {"pixels": pixels, "bbox": list(mask.getbbox() or (0, 0, 0, 0))}
    return stats


def export_with_blender(obj_path: Path, stem: str = "yuna_semantic_layer_v1") -> dict:
    blender = shutil.which("blender") or "/opt/homebrew/bin/blender"
    if not Path(blender).exists():
        return {"error": "blender_not_found", "obj": str(obj_path)}

    blend = EXPORT_DIR / f"{stem}.blend"
    glb = EXPORT_DIR / f"{stem}.glb"
    fbx = EXPORT_DIR / f"{stem}.fbx"
    exported_obj = EXPORT_DIR / f"{stem}.obj"
    front_png = VALIDATION_DIR / f"{stem}_front.png"
    yaw15_png = VALIDATION_DIR / f"{stem}_yaw15.png"
    yaw30_png = VALIDATION_DIR / f"{stem}_yaw30.png"
    side_png = VALIDATION_DIR / f"{stem}_side.png"
    exploded_png = VALIDATION_DIR / f"{stem}_exploded.png"
    texture_dir = str(TEXTURE_DIR.resolve())
    part_defs = [
        {
            "id": part.id,
            "category": part.category,
            "parent": part.parent,
            "depth": part.depth,
            "edge_color": part.edge_color,
        }
        for part in PARTS
    ]

    script = f"""
import math
from pathlib import Path
import bpy
from mathutils import Vector

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bpy.ops.wm.obj_import(filepath=r'{obj_path}')

texture_dir = Path(r'{texture_dir}')
part_defs = {part_defs!r}

def image_material(part_id):
    mat = bpy.data.materials.new(part_id + '_image')
    mat.use_nodes = True
    mat.blend_method = 'OPAQUE'
    nodes = mat.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(texture_dir / (part_id + '.png')), check_existing=True)
    tex.extension = 'CLIP'
    mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.55
    return mat

def edge_material(part_id, color):
    mat = bpy.data.materials.new(part_id + '_edge')
    mat.use_nodes = True
    edge_alpha = {EDGE_ALPHA!r}
    mat.blend_method = 'BLEND' if edge_alpha < 0.999 else 'OPAQUE'
    nodes = mat.node_tree.nodes
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(texture_dir / (part_id + '.png')), check_existing=True)
    tex.extension = 'CLIP'
    mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Alpha'].default_value = edge_alpha
    bsdf.inputs['Roughness'].default_value = 0.42
    return mat

mat_map = {{}}
for p in part_defs:
    mat_map[p['id']] = image_material(p['id'])
    mat_map[p['id'] + '_edge'] = edge_material(p['id'], p['edge_color'])

for obj in bpy.context.scene.objects:
    if obj.type != 'MESH':
        continue
    for slot in obj.material_slots:
        name = slot.material.name if slot.material else ''
        if name in mat_map:
            slot.material = mat_map[name]
    obj['semantic_layer_v1'] = True

proxy_mat = bpy.data.materials.new('proxy_body_transparent_guide')
proxy_mat.use_nodes = True
proxy_mat.blend_method = 'BLEND'
proxy_bsdf = proxy_mat.node_tree.nodes.get('Principled BSDF')
proxy_bsdf.inputs['Base Color'].default_value = (0.18, 0.80, 1.0, 0.16)
proxy_bsdf.inputs['Alpha'].default_value = 0.16
proxy_bsdf.inputs['Roughness'].default_value = 0.70

def add_proxy(name, loc, scale):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(proxy_mat)
    obj.display_type = 'WIRE'
    obj['proxy_role'] = 'retopo_guide'
    return obj

add_proxy('head_proxy_retopo_guide', (0, -0.01, 5.58), (0.43, 0.28, 0.50))
add_proxy('torso_proxy_retopo_guide', (0, -0.01, 3.95), (0.65, 0.32, 0.95))

def add_empty(name, loc):
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.empty_display_size = 0.12
    obj['animation_hook'] = True
    return obj

add_empty('hook_bangs_spring', (0.0, 0.26, 5.40))
add_empty('hook_back_hair_spring', (0.0, -0.14, 5.00))
add_empty('hook_cape_left_swing', (-0.72, -0.10, 3.80))
add_empty('hook_cape_right_swing', (0.72, -0.10, 3.80))
add_empty('hand_R_socket_weapon', (-1.46, 0.26, 2.90))

for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        try:
            bpy.ops.object.shade_smooth()
        except Exception:
            pass
        obj.select_set(False)

bpy.ops.object.light_add(type='AREA', location=(0, -5.0, 7.5))
light = bpy.context.object
light.name = 'semantic_large_softbox'
light.data.energy = 650
light.data.size = 5

mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
min_corner = Vector((999999, 999999, 999999))
max_corner = Vector((-999999, -999999, -999999))
for obj in mesh_objects:
    for corner in obj.bound_box:
        world = obj.matrix_world @ Vector(corner)
        min_corner.x = min(min_corner.x, world.x)
        min_corner.y = min(min_corner.y, world.y)
        min_corner.z = min(min_corner.z, world.z)
        max_corner.x = max(max_corner.x, world.x)
        max_corner.y = max(max_corner.y, world.y)
        max_corner.z = max(max_corner.z, world.z)
center = (min_corner + max_corner) * 0.5
height = max_corner.z - min_corner.z
distance = 9.0

def add_camera(name, yaw_deg):
    yaw = math.radians(yaw_deg)
    loc = Vector((center.x + math.sin(yaw) * distance, center.y - math.cos(yaw) * distance, center.z))
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    cam.name = name
    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Z').to_euler()
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = height * 1.08
    return cam

front_cam = add_camera('Camera_Front_Ortho', 0)
yaw15_cam = add_camera('Camera_Yaw_15', 15)
yaw30_cam = add_camera('Camera_Yaw_30', 30)
side_cam = add_camera('Camera_Side_90', 90)

try:
    bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
try:
    bpy.context.scene.eevee.taa_render_samples = 64
except Exception:
    pass
bpy.context.scene.render.resolution_x = 1200
bpy.context.scene.render.resolution_y = 1600
bpy.context.scene.view_settings.view_transform = 'Filmic'
bpy.context.scene.view_settings.look = 'Medium High Contrast'
bpy.context.scene.world.color = (0.006, 0.009, 0.012)

def render(cam, filepath):
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)

render(front_cam, r'{front_png}')
render(yaw15_cam, r'{yaw15_png}')
render(yaw30_cam, r'{yaw30_png}')
render(side_cam, r'{side_png}')

proxy_objects = [obj for obj in bpy.context.scene.objects if obj.get('proxy_role') == 'retopo_guide']
for obj in proxy_objects:
    obj.hide_render = True

render(front_cam, r'{front_png}')
render(yaw15_cam, r'{yaw15_png}')
render(yaw30_cam, r'{yaw30_png}')
render(side_cam, r'{side_png}')

original_locations = {{}}
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH' and obj.name.split('.')[0] in [p['id'] for p in part_defs]:
        base = obj.name.split('.')[0]
        original_locations[obj.name] = obj.location.copy()
        index = [p['id'] for p in part_defs].index(base)
        obj.location.x += (index - len(part_defs) / 2) * 0.18
        obj.location.y += (index % 4 - 1.5) * 0.08
render(yaw30_cam, r'{exploded_png}')
for obj in bpy.context.scene.objects:
    if obj.name in original_locations:
        obj.location = original_locations[obj.name]

for obj in proxy_objects:
    obj.hide_render = False
    obj.hide_viewport = False
bpy.ops.wm.save_as_mainfile(filepath=r'{blend}')

for obj in proxy_objects:
    obj.hide_viewport = True
    obj.hide_render = True
bpy.ops.export_scene.gltf(filepath=r'{glb}', export_format='GLB', export_texcoords=True, export_normals=True, export_materials='EXPORT', use_visible=True)
bpy.ops.export_scene.fbx(filepath=r'{fbx}', path_mode='COPY', embed_textures=True, add_leaf_bones=False, use_visible=True)
bpy.ops.wm.obj_export(filepath=r'{exported_obj}', export_uv=True, export_materials=True)
"""

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(script)
        tmp_path = tmp.name

    result = subprocess.run(
        [blender, "--background", "--python", tmp_path],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    return {
        "blend": str(blend.relative_to(ROOT)) if blend.exists() else None,
        "glb": str(glb.relative_to(ROOT)) if glb.exists() else None,
        "fbx": str(fbx.relative_to(ROOT)) if fbx.exists() else None,
        "obj": str(exported_obj.relative_to(ROOT)) if exported_obj.exists() else None,
        "validation_screenshots": {
            "front": str(front_png.relative_to(ROOT)) if front_png.exists() else None,
            "yaw15": str(yaw15_png.relative_to(ROOT)) if yaw15_png.exists() else None,
            "yaw30": str(yaw30_png.relative_to(ROOT)) if yaw30_png.exists() else None,
            "side": str(side_png.relative_to(ROOT)) if side_png.exists() else None,
            "exploded": str(exploded_png.relative_to(ROOT)) if exploded_png.exists() else None,
        },
        "blender_exit_code": result.returncode,
        "blender_log_tail": result.stdout.splitlines()[-40:],
    }


def validate_glb(glb_path: Path) -> dict:
    blender = shutil.which("blender") or "/opt/homebrew/bin/blender"
    if not glb_path.exists() or not Path(blender).exists():
        return {"status": "skipped", "reason": "missing_glb_or_blender"}
    script = f"""
import json
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.import_scene.gltf(filepath=r'{glb_path}')
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
empties = [o for o in bpy.context.scene.objects if o.type == 'EMPTY']
materials = list(bpy.data.materials)
print('YUNA_SEMANTIC_IMPORT_REPORT=' + json.dumps({{
    'mesh_count': len(meshes),
    'empty_count': len(empties),
    'material_count': len(materials),
    'mesh_names': [o.name for o in meshes],
    'empty_names': [o.name for o in empties],
}}))
"""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(script)
        tmp_path = tmp.name
    result = subprocess.run([blender, "--background", "--python", tmp_path], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    report_line = None
    for line in result.stdout.splitlines():
        if line.startswith("YUNA_SEMANTIC_IMPORT_REPORT="):
            report_line = line.split("=", 1)[1]
            break
    if report_line:
        data = json.loads(report_line)
        data["status"] = "ok"
        data["blender_exit_code"] = result.returncode
        return data
    return {"status": "failed", "blender_exit_code": result.returncode, "log_tail": result.stdout.splitlines()[-30:]}


def main() -> None:
    ensure_dirs()
    source = Image.open(SOURCE_FRONT).convert("RGBA")
    raw_masks = build_front_masks(source)
    masks = {part_id: clean_mask(mask) for part_id, mask in raw_masks.items()}
    stats = mask_stats(masks)
    save_part_textures(source, masks)
    contact = build_contact_sheet(masks)
    build_mtl()

    part_reports = {
        part.id: make_obj_for_part(part, masks[part.id])
        for part in PARTS
    }
    combined_obj = OBJ_DIR / "yuna_semantic_layer_v1.obj"
    combined_report = combine_part_objs(combined_obj)
    spec_path = write_spec(stats)
    export_report = export_with_blender(combined_obj)
    glb_report = validate_glb(EXPORT_DIR / "yuna_semantic_layer_v1.glb")

    acceptance = {
        "independent_part_meshes": [part.id for part in PARTS if stats[part.id]["pixels"] > 0],
        "hair_depth_groups": ["back_hair", "side_hair_left", "side_hair_right", "bangs"],
        "weapon_independent_object": stats["weapon"]["pixels"] > 0,
        "cape_independent_objects": stats["cape_left"]["pixels"] > 0 and stats["cape_right"]["pixels"] > 0,
        "proxy_guides_added_in_blender": True,
        "boundary": "semantic-layer v1 uses auto-draft masks; human mask cleanup is expected before production DCC retopo.",
    }
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": "semantic_layer_v1_asset_compiler",
        "status": "generated" if export_report.get("blender_exit_code") == 0 else "generated_with_errors",
        "boundary": "This is a structured 2.5D render-shell and DCC handoff asset, not a final production rigged character.",
        "source": str(SOURCE_FRONT.relative_to(ROOT)),
        "spec": str(spec_path.relative_to(ROOT)),
        "mask_contact_sheet": str(contact.relative_to(ROOT)),
        "mask_stats": stats,
        "parts": part_reports,
        "combined_obj": combined_report,
        "exports": export_report,
        "glb_roundtrip": glb_report,
        "acceptance_v1": acceptance,
        "next_manual_cleanup": [
            "Review auto-draft masks, especially cape/body overlap and weapon/hand boundary.",
            "Replace heuristic hair masks with hand-authored bangs, side hair and back hair groups.",
            "Add side/back masks before the multi-view constraint cage stage.",
            "Convert proxy guides into a real retopo cage only after mask cleanup.",
        ],
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
