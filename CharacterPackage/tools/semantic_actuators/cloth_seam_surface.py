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

from PIL import Image

from .registry import register
from .state import ActuatorPaths, ActuatorResult, MeshData
from .validation_contract import file_record, validate_cloth_candidate_report


ACTUATOR_NAME = "cloth_seam_surface_v0"
PART_ID = "cloth"
TARGET_PART_IDS = ("jacket_outer", "cape_left", "cape_right", "skirt_front")
ROUTE = "semantic_layer_v9_cloth_seam_surface_v0"
ROWS = 22
COLS = 8
HEIGHT_WORLD = 6.4


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


def cloth_curvature(part_id: str, base_depth: float, u: float, v: float) -> float:
    if part_id == "jacket_outer":
        return base_depth + 0.045 * (1.0 - min(1.0, abs(u - 0.5) * 1.9))
    if part_id == "cape_left":
        return base_depth - 0.045 * (u - 0.5) - 0.040 * max(0.0, 1.0 - v)
    if part_id == "cape_right":
        return base_depth + 0.045 * (u - 0.5) - 0.040 * max(0.0, 1.0 - v)
    if part_id == "skirt_front":
        return base_depth - 0.045 * max(0.0, 1.0 - v) + 0.015 * math.sin(u * math.pi)
    return base_depth


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
) -> MeshData:
    image = Image.open(mask_path).convert("RGBA")
    alpha = image.getchannel("A")
    image_size = image.size
    x0, y0, x1, y1 = bbox
    vertices: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    face_materials: list[int] = []

    for row in range(ROWS + 1):
        v = row / ROWS
        py = round(y0 + (y1 - y0 - 1) * v)
        left, right = row_alpha_span(alpha, bbox, py)
        span = max(right - left, 1)
        for col in range(COLS + 1):
            u = col / COLS
            px = left + span * u
            wx, _, wz = px_to_world(px, py, cloth_curvature(part_id, depth, u, v), image_size)
            vertices.append((wx, cloth_curvature(part_id, depth, u, v), wz))
            uvs.append((max(0.0, min(1.0, px / image_size[0])), 1.0 - py / image_size[1]))

    stride = COLS + 1
    for row in range(ROWS):
        for col in range(COLS):
            a = row * stride + col
            faces.append((a, a + 1, a + stride + 1, a + stride))
            face_materials.append(0)

    return MeshData(
        vertices=vertices,
        uvs=uvs,
        faces=faces,
        face_materials=face_materials,
        section_count=ROWS + 1,
        thickness=0.0,
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
) -> dict[str, Any]:
    x0, y0, x1, y1 = bbox
    px = x0 + (x1 - x0) * u
    py = y0 + (y1 - y0) * v
    world = px_to_world(px, py, cloth_curvature(part_id, depth, u, v), image_size)
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
) -> list[dict[str, Any]]:
    return [seam_point(part_id, bbox, depth, image_size, u, v, label) for u, v, label in points]


def build_panel_seam_metadata(
    part_id: str,
    bbox: tuple[int, int, int, int],
    depth: float,
    image_size: tuple[int, int],
) -> dict[str, Any]:
    lower_points = seam_line(
        part_id,
        bbox,
        depth,
        image_size,
        [(0.04, 0.98, "lower_left"), (0.50, 0.995, "lower_mid"), (0.96, 0.98, "lower_right")],
    )
    metadata: dict[str, Any] = {
        "part_id": part_id,
        "lower_cloth_edge": lower_points,
    }
    if part_id == "jacket_outer":
        metadata["shoulder_anchors"] = {
            "left": seam_point(part_id, bbox, depth, image_size, 0.24, 0.05, "shoulder_anchor_left"),
            "right": seam_point(part_id, bbox, depth, image_size, 0.76, 0.05, "shoulder_anchor_right"),
        }
    elif part_id == "cape_left":
        metadata["cape_root"] = seam_line(
            part_id,
            bbox,
            depth,
            image_size,
            [(0.78, 0.02, "cape_left_root_shoulder"), (0.62, 0.10, "cape_left_root_falloff")],
        )
    elif part_id == "cape_right":
        metadata["cape_root"] = seam_line(
            part_id,
            bbox,
            depth,
            image_size,
            [(0.20, 0.02, "cape_right_root_shoulder"), (0.36, 0.10, "cape_right_root_falloff")],
        )
    elif part_id == "skirt_front":
        metadata["skirt_waist_seam"] = seam_line(
            part_id,
            bbox,
            depth,
            image_size,
            [(0.08, 0.04, "waist_left"), (0.50, 0.02, "waist_mid"), (0.92, 0.04, "waist_right")],
        )
    return metadata


def build_cloth_panels(character_package: Path) -> list[ClothPanel]:
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
        panels.append(
            ClothPanel(
                id=f"{part_id}_cloth_seam_surface_v0",
                source_part_id=part_id,
                category=str(source.get("category", "cloth")),
                generator=str(source.get("generator", "unknown")),
                texture_path=texture_path,
                mask_path=mask_path,
                bbox=bbox_tuple,
                depth=depth,
                mesh=build_cloth_mesh(part_id, texture_path, mask_path, bbox_tuple, depth),
                seam_metadata=build_panel_seam_metadata(part_id, bbox_tuple, depth, image_size),
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
        lines.append(f"usemtl {panel.source_part_id}_front_texture")
        for face in panel.mesh.faces:
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
        ]
    )
    mtl_path.write_text("\n".join(material_lines) + "\n", encoding="utf-8")
    return mtl_path


def blender_export_glb(glb_path: Path, panels: list[ClothPanel], seam_metadata: dict[str, Any], repo_root: Path) -> dict[str, Any]:
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
            "seam_metadata": panel.seam_metadata,
        }
        for panel in panels
    ]
    payload_json = json.dumps(payload)
    seam_json = json.dumps(seam_metadata)
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
    obj['semantic_part'] = item['source_part_id']
    obj['actuator'] = 'cloth_seam_surface_v0'
    obj['candidate_only'] = True
    obj['dcc_handoff_only'] = True
    obj['replace_in_beauty_glb'] = False
    obj['production_cloth_topology'] = False
    obj['seam_metadata'] = json.dumps(item['seam_metadata'])

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
    half_width = 0.008
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


def build_spec(paths: ActuatorPaths, panels: list[ClothPanel], seam_metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "route": ROUTE,
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
        "exports": {
            "obj": display_path(paths.obj_path, paths.repo_root),
            "glb": display_path(paths.glb_path, paths.repo_root),
            "blend": display_path(paths.glb_path.with_suffix(".blend"), paths.repo_root),
            "report": display_path(paths.report_path, paths.repo_root),
        },
    }


@register("cloth_seam_surface_v0")
def run_cloth_seam_surface(paths: ActuatorPaths) -> ActuatorResult:
    warnings: list[str] = [
        "cloth_seam_surface_v0 is a candidate DCC handoff route, not production cloth topology.",
        "v8 beauty cloth remains active; replace_in_beauty_glb=false.",
        "hair route still blocks cloth integration; this route does not mark cloth unblocked.",
    ]
    errors: list[str] = []
    try:
        panels = build_cloth_panels(paths.character_package)
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
        write_json(paths.report_path, {"created_at": datetime.now(timezone.utc).isoformat(), "route": ROUTE, **result.to_dict()})
        return result

    paths.output_dir.mkdir(parents=True, exist_ok=True)
    paths.spec_path.parent.mkdir(parents=True, exist_ok=True)
    paths.obj_path.parent.mkdir(parents=True, exist_ok=True)
    prepare_output_textures(paths, panels)
    seam_metadata = combined_seam_metadata(panels)
    write_obj(paths.obj_path, panels, seam_metadata)
    glb_report = blender_export_glb(paths.glb_path, panels, seam_metadata, paths.repo_root)
    if glb_report.get("status") != "ok":
        warnings.append("GLB/BLEND/screenshots are skipped or incomplete; see validation.blender_glb_export and validation.validation_ci.")

    generated_files = {
        "spec": display_path(paths.spec_path, paths.repo_root),
        "obj": display_path(paths.obj_path, paths.repo_root),
        "mtl": display_path(paths.obj_path.with_suffix(".mtl"), paths.repo_root),
        "glb": display_path(paths.glb_path, paths.repo_root),
        "blend": display_path(paths.glb_path.with_suffix(".blend"), paths.repo_root),
        "report": display_path(paths.report_path, paths.repo_root),
        "validation_ci_report": display_path(paths.output_dir / "validation_ci" / "validation_ci_report.json", paths.repo_root),
    }
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
        "obj": file_record(paths.obj_path),
        "glb": file_record(paths.glb_path),
        "blender_glb_export": glb_report,
    }

    result = ActuatorResult(
        actuator=ACTUATOR_NAME,
        status="generated_with_warnings",
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

    write_json(paths.spec_path, build_spec(paths, panels, seam_metadata))
    write_json(paths.report_path, {"created_at": datetime.now(timezone.utc).isoformat(), "route": ROUTE, "seams": seam_metadata, **result.to_dict()})

    validation_ci = run_blender_validation_ci(paths)
    result.validation["validation_ci"] = {
        "status": validation_ci.get("status"),
        "report": display_path(paths.output_dir / "validation_ci" / "validation_ci_report.json", paths.repo_root),
        "screenshot_count": len(validation_ci.get("screenshots", {})),
    }
    write_json(paths.report_path, {"created_at": datetime.now(timezone.utc).isoformat(), "route": ROUTE, "seams": seam_metadata, **result.to_dict()})
    return result
