#!/usr/bin/env python3
"""Build deterministic image-constructed YUNA GLB/FBX/OBJ assets.

This deliberately avoids cloud image-to-3D services. It turns existing PNG
references into textured relief meshes by carving the alpha mask into geometry.
The result is a 2.5D/DCC reference asset, not a final animated character mesh.
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

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "image_constructed"
OBJ_DIR = OUT / "obj"
EXPORT_DIR = OUT / "exports"
TEXTURE_DIR = OUT / "textures"
QA_DIR = ROOT / "qa" / "turntable"
REPORT = ROOT / "qa" / "yuna_image_constructed_report.json"


@dataclass(frozen=True)
class SourceImage:
    key: str
    source: Path
    texture_name: str
    target_height: int


SOURCES = [
    SourceImage(
        "front",
        ROOT / "refs" / "front_rgba" / "yuna_front_rgba.png",
        "yuna_image_constructed_front.png",
        320,
    ),
    SourceImage(
        "side",
        ROOT / "refs" / "ai_turnarounds" / "cutouts" / "yuna_left_side.png",
        "yuna_image_constructed_side.png",
        260,
    ),
    SourceImage(
        "back",
        ROOT / "refs" / "ai_turnarounds" / "cutouts" / "yuna_back.png",
        "yuna_image_constructed_back.png",
        260,
    ),
]


def ensure_dirs() -> None:
    for path in (OUT, OBJ_DIR, EXPORT_DIR, TEXTURE_DIR, QA_DIR):
        path.mkdir(parents=True, exist_ok=True)


def copy_texture(src: Path, texture_name: str) -> Path:
    dst = TEXTURE_DIR / texture_name
    shutil.copy2(src, dst)
    return dst


def load_mask(src: Path, target_height: int, alpha_threshold: int = 24) -> tuple[Image.Image, list[list[bool]]]:
    image = Image.open(src).convert("RGBA")
    aspect = image.width / image.height
    target_width = max(1, round(target_height * aspect))
    resized = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    alpha = resized.getchannel("A")
    mask: list[list[bool]] = []
    for y in range(target_height):
        row = []
        for x in range(target_width):
            row.append(alpha.getpixel((x, y)) > alpha_threshold)
        mask.append(row)
    return resized, mask


def generate_relief_obj(
    src: SourceImage,
    obj_path: Path,
    texture_rel_path: str,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
    z_rotation_deg: float = 0.0,
    height_world: float = 6.0,
    thickness: float = 0.12,
) -> dict:
    resized, mask = load_mask(src.source, src.target_height)
    width, height = resized.size
    cell = height_world / height
    width_world = width * cell
    half_w = width_world / 2
    half_t = thickness / 2
    rot = math.radians(z_rotation_deg)
    cos_r = math.cos(rot)
    sin_r = math.sin(rot)

    vertices: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    faces: list[tuple[str, list[tuple[int, int]]]] = []

    def transform(x: float, y: float, z: float) -> tuple[float, float, float]:
        rx = x * cos_r - y * sin_r
        ry = x * sin_r + y * cos_r
        # Wavefront OBJ is conventionally Y-up. Store image height in Y and
        # relief thickness in Z so Blender/FBX/GLB imports stand upright.
        return (rx + offset_x, z, ry + offset_y)

    def add_vertex(x: float, y: float, z: float, u: float, v: float) -> tuple[int, int]:
        vertices.append(transform(x, y, z))
        uvs.append((u, v))
        return (len(vertices), len(uvs))

    def add_face(material: str, corners: list[tuple[float, float, float, float, float]]) -> None:
        face_refs = [add_vertex(*corner) for corner in corners]
        faces.append((material, face_refs))

    occupied = 0
    for gy in range(height):
        for gx in range(width):
            if not mask[gy][gx]:
                continue
            occupied += 1
            x0 = gx * cell - half_w
            x1 = (gx + 1) * cell - half_w
            z0 = (height - gy - 1) * cell
            z1 = (height - gy) * cell
            u0 = gx / width
            u1 = (gx + 1) / width
            v0 = 1.0 - ((gy + 1) / height)
            v1 = 1.0 - (gy / height)

            add_face(
                "image",
                [
                    (x0, -half_t, z0, u0, v0),
                    (x1, -half_t, z0, u1, v0),
                    (x1, -half_t, z1, u1, v1),
                    (x0, -half_t, z1, u0, v1),
                ],
            )
            add_face(
                "image",
                [
                    (x1, half_t, z0, u1, v0),
                    (x0, half_t, z0, u0, v0),
                    (x0, half_t, z1, u0, v1),
                    (x1, half_t, z1, u1, v1),
                ],
            )

            neighbors = {
                "left": gx == 0 or not mask[gy][gx - 1],
                "right": gx == width - 1 or not mask[gy][gx + 1],
                "bottom": gy == height - 1 or not mask[gy + 1][gx],
                "top": gy == 0 or not mask[gy - 1][gx],
            }
            if neighbors["left"]:
                add_face("edge", [(x0, half_t, z0, u0, v0), (x0, -half_t, z0, u0, v0), (x0, -half_t, z1, u0, v1), (x0, half_t, z1, u0, v1)])
            if neighbors["right"]:
                add_face("edge", [(x1, -half_t, z0, u1, v0), (x1, half_t, z0, u1, v0), (x1, half_t, z1, u1, v1), (x1, -half_t, z1, u1, v1)])
            if neighbors["bottom"]:
                add_face("edge", [(x0, half_t, z0, u0, v0), (x1, half_t, z0, u1, v0), (x1, -half_t, z0, u1, v0), (x0, -half_t, z0, u0, v0)])
            if neighbors["top"]:
                add_face("edge", [(x0, -half_t, z1, u0, v1), (x1, -half_t, z1, u1, v1), (x1, half_t, z1, u1, v1), (x0, half_t, z1, u0, v1)])

    mtl_name = obj_path.with_suffix(".mtl").name
    obj_path.write_text(
        build_obj_text(obj_path.stem, mtl_name, vertices, uvs, faces),
        encoding="utf-8",
    )
    obj_path.with_suffix(".mtl").write_text(build_mtl_text(texture_rel_path), encoding="utf-8")
    return {
        "key": src.key,
        "obj": str(obj_path.relative_to(ROOT)),
        "mtl": str(obj_path.with_suffix(".mtl").relative_to(ROOT)),
        "texture": texture_rel_path,
        "source": str(src.source.relative_to(ROOT)),
        "resampled_size": [width, height],
        "occupied_cells": occupied,
        "vertices": len(vertices),
        "faces": len(faces),
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


def build_mtl_text(texture_rel_path: str) -> str:
    return "\n".join(
        [
            "newmtl image",
            "Ka 1.000 1.000 1.000",
            "Kd 1.000 1.000 1.000",
            "Ks 0.100 0.100 0.100",
            "Ns 64.000",
            "d 1.000",
            f"map_Kd {texture_rel_path}",
            "",
            "newmtl edge",
            "Ka 0.020 0.040 0.050",
            "Kd 0.030 0.100 0.120",
            "Ks 0.200 0.450 0.500",
            "Ns 96.000",
            "d 1.000",
            "",
        ]
    )


def combine_objs(obj_paths: list[Path], combined_path: Path) -> dict:
    vertices: list[str] = []
    uvs: list[str] = []
    face_lines: list[str] = []
    mtllibs: list[str] = []
    v_offset = 0
    vt_offset = 0

    for index, path in enumerate(obj_paths):
        material_prefix = f"view{index}_"
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("mtllib "):
                src_mtl = path.with_suffix(".mtl")
                dst_mtl = combined_path.with_name(f"{path.stem}.mtl")
                if src_mtl != dst_mtl:
                    shutil.copy2(src_mtl, dst_mtl)
                mtllibs.append(dst_mtl.name)
            elif line.startswith("v "):
                vertices.append(line)
            elif line.startswith("vt "):
                uvs.append(line)
            elif line.startswith("usemtl "):
                face_lines.append(line)
            elif line.startswith("f "):
                refs = []
                for ref in line[2:].split():
                    vi, ti = ref.split("/")[:2]
                    refs.append(f"{int(vi) + v_offset}/{int(ti) + vt_offset}")
                face_lines.append("f " + " ".join(refs))
            elif line.startswith("o "):
                face_lines.append(f"o {material_prefix}{line[2:]}")
        v_offset += sum(1 for l in path.read_text(encoding="utf-8").splitlines() if l.startswith("v "))
        vt_offset += sum(1 for l in path.read_text(encoding="utf-8").splitlines() if l.startswith("vt "))

    combined_path.write_text(
        "\n".join([*(f"mtllib {name}" for name in mtllibs), *vertices, *uvs, *face_lines]) + "\n",
        encoding="utf-8",
    )
    return {
        "obj": str(combined_path.relative_to(ROOT)),
        "mtl_files": [str(combined_path.with_name(name).relative_to(ROOT)) for name in mtllibs],
        "views": len(obj_paths),
    }


def export_with_blender(obj_path: Path, stem: str) -> dict:
    blender = shutil.which("blender") or "/opt/homebrew/bin/blender"
    if not Path(blender).exists():
        return {"error": "blender_not_found", "obj": str(obj_path)}

    glb = EXPORT_DIR / f"{stem}.glb"
    fbx = EXPORT_DIR / f"{stem}.fbx"
    preview = QA_DIR / f"{stem}_preview.png"
    blend = OUT / f"{stem}.blend"
    ortho_scale = 14.0 if "turnaround" in stem else 8.4
    texture_map = {
        "front": str((TEXTURE_DIR / "yuna_image_constructed_front.png").resolve()),
        "side": str((TEXTURE_DIR / "yuna_image_constructed_side.png").resolve()),
        "back": str((TEXTURE_DIR / "yuna_image_constructed_back.png").resolve()),
    }

    script = f"""
import bpy
from pathlib import Path
from mathutils import Vector

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

obj_path = r'{obj_path}'
bpy.ops.wm.obj_import(filepath=obj_path)

texture_map = {texture_map!r}

def build_image_material(name, image_path):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.blend_method = 'OPAQUE'
    nodes = mat.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(image_path, check_existing=True)
    mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.5
    return mat

def build_edge_material():
    mat = bpy.data.materials.new('constructed_dark_edge')
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (0.02, 0.10, 0.12, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.38
    return mat

front_mat = build_image_material('constructed_front_image', texture_map['front'])
side_mat = build_image_material('constructed_side_image', texture_map['side'])
back_mat = build_image_material('constructed_back_image', texture_map['back'])
edge_mat = build_edge_material()

for obj in bpy.context.scene.objects:
    if obj.type != 'MESH':
        continue
    image_mat = front_mat
    lower_name = obj.name.lower()
    if 'side' in lower_name or 'view1' in lower_name:
        image_mat = side_mat
    elif 'back' in lower_name or 'view2' in lower_name:
        image_mat = back_mat
    for index, slot in enumerate(obj.material_slots):
        old_name = slot.material.name.lower() if slot.material else ''
        if 'edge' in old_name:
            slot.material = edge_mat
        else:
            slot.material = image_mat

for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        try:
            bpy.ops.object.shade_smooth()
        except Exception:
            pass
        obj.select_set(False)

for mat in bpy.data.materials:
    mat.use_nodes = True
    mat.blend_method = 'BLEND'
    mat.use_screen_refraction = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        try:
            bsdf.inputs['Roughness'].default_value = 0.45
            bsdf.inputs['Metallic'].default_value = 0.0
        except Exception:
            pass

bpy.ops.object.light_add(type='AREA', location=(0, -5, 7))
light = bpy.context.object
light.name = 'large_softbox'
light.data.energy = 600
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

bpy.ops.object.camera_add(location=(center.x, center.y - 10, center.z))
camera = bpy.context.object
bpy.context.scene.camera = camera
direction = center - camera.location
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
camera.data.lens = 55
camera.data.type = 'ORTHO'
camera.data.ortho_scale = {ortho_scale}

try:
    bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
try:
    bpy.context.scene.eevee.taa_render_samples = 64
except Exception:
    pass
bpy.context.scene.render.resolution_x = 1440
bpy.context.scene.render.resolution_y = 900
bpy.context.scene.view_settings.view_transform = 'Filmic'
bpy.context.scene.view_settings.look = 'Medium High Contrast'
bpy.context.scene.world.color = (0.008, 0.012, 0.016)

bpy.ops.wm.save_as_mainfile(filepath=r'{blend}')
bpy.ops.export_scene.gltf(filepath=r'{glb}', export_format='GLB', export_texcoords=True, export_normals=True, export_materials='EXPORT')
bpy.ops.export_scene.fbx(filepath=r'{fbx}', path_mode='COPY', embed_textures=True, add_leaf_bones=False)
bpy.context.scene.render.filepath = r'{preview}'
bpy.ops.render.render(write_still=True)
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
        "obj": str(obj_path.relative_to(ROOT)),
        "blend": str(blend.relative_to(ROOT)) if blend.exists() else None,
        "glb": str(glb.relative_to(ROOT)) if glb.exists() else None,
        "fbx": str(fbx.relative_to(ROOT)) if fbx.exists() else None,
        "preview": str(preview.relative_to(ROOT)) if preview.exists() else None,
        "blender_exit_code": result.returncode,
        "blender_log_tail": result.stdout.splitlines()[-25:],
    }


def main() -> None:
    ensure_dirs()

    texture_paths = {
        src.key: copy_texture(src.source, src.texture_name)
        for src in SOURCES
    }

    front_obj = OBJ_DIR / "yuna_image_constructed_front_relief.obj"
    front_report = generate_relief_obj(
        SOURCES[0],
        front_obj,
        f"../textures/{texture_paths['front'].name}",
        height_world=6.0,
        thickness=0.14,
    )

    view_objs = []
    view_reports = []
    offsets = {"front": -4.7, "side": 0.0, "back": 4.7}
    for src in SOURCES:
        obj_path = OBJ_DIR / f"yuna_image_constructed_{src.key}_view.obj"
        report = generate_relief_obj(
            src,
            obj_path,
            f"../textures/{texture_paths[src.key].name}",
            offset_x=offsets[src.key],
            height_world=5.4,
            thickness=0.08,
        )
        view_objs.append(obj_path)
        view_reports.append(report)

    combined_obj = OBJ_DIR / "yuna_image_constructed_turnaround.obj"
    combined_report = combine_objs(view_objs, combined_obj)

    front_export = export_with_blender(front_obj, "yuna_image_constructed_front_relief")
    turnaround_export = export_with_blender(combined_obj, "yuna_image_constructed_turnaround")

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": "deterministic_png_alpha_to_textured_relief_mesh",
        "status": "image_constructed_exports_generated",
        "boundary": "These are 2.5D relief/reference assets built from image alpha and texture data, not full volumetric animation-ready character meshes.",
        "front_relief": front_report,
        "turnaround_views": view_reports,
        "combined_turnaround": combined_report,
        "exports": {
            "front_relief": front_export,
            "turnaround": turnaround_export,
        },
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
