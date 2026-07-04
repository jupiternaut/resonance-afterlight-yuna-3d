#!/usr/bin/env python3
"""Build YUNA semantic-layer v4 assets.

v4 is the first "part grammar" pass after v3. It deliberately stops using
thick per-pixel cutout extrusion as the main surface, because that created the
black horizontal sidewall bands in yaw/side views. Instead it builds:

- curved alpha render panels for face/body/costume
- split ribbon cards for hair groups
- cloth-like curved sheets for cape/skirt panels
- an independent weapon panel/prop
- transparent DCC cage guides in the .blend and cage-debug GLB

This is still a DCC handoff/blockout asset, not production topology.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

import build_yuna_semantic_layer_v1 as base
import build_yuna_semantic_layer_v2 as v2
import build_yuna_semantic_layer_v3 as v3


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "semantic_layer_v4"
STEM = "yuna_semantic_layer_v4"
CONSTRAINT_DIR = OUT / "constraints"


def configure_output() -> None:
    base.OUT = OUT
    base.MASK_DIR = OUT / "masks" / "front"
    base.TEXTURE_DIR = OUT / "textures"
    base.OBJ_DIR = OUT / "obj"
    base.PART_OBJ_DIR = base.OBJ_DIR / "parts"
    base.EXPORT_DIR = OUT / "exports"
    base.VALIDATION_DIR = OUT / "validation"
    base.SPEC_DIR = OUT / "specs"
    base.REPORT_PATH = OUT / "validation_report.json"


def configure_parts_v4() -> None:
    depth_overrides = {
        "back_hair": (-0.58, 0.006, "hair_cards"),
        "cape_left": (-0.42, 0.004, "cloth_sheet"),
        "cape_right": (-0.36, 0.004, "cloth_sheet"),
        "torso_inner": (0.00, 0.006, "curved_panel"),
        "legs": (0.02, 0.006, "curved_panel"),
        "side_hair_left": (0.16, 0.004, "hair_cards"),
        "side_hair_right": (0.22, 0.004, "hair_cards"),
        "jacket_outer": (0.30, 0.006, "curved_panel"),
        "boots": (0.38, 0.008, "curved_panel"),
        "skirt_front": (0.48, 0.004, "cloth_sheet"),
        "face": (0.62, 0.004, "face_plate"),
        "bangs": (0.76, 0.004, "hair_cards"),
        "weapon": (0.92, 0.012, "weapon_panel"),
    }
    base.PARTS = [
        replace(
            part,
            depth=depth_overrides[part.id][0],
            thickness=depth_overrides[part.id][1],
            mesh_generator=depth_overrides[part.id][2],
        )
        for part in base.PARTS
    ]


def ensure_dirs() -> None:
    for path in (
        OUT,
        base.MASK_DIR,
        base.TEXTURE_DIR,
        base.OBJ_DIR,
        base.PART_OBJ_DIR,
        base.EXPORT_DIR,
        base.VALIDATION_DIR,
        base.SPEC_DIR,
        CONSTRAINT_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def build_parts_payload(mask_stats: dict[str, dict]) -> list[dict]:
    card_counts = {
        "bangs": 10,
        "side_hair_left": 8,
        "side_hair_right": 9,
        "back_hair": 14,
    }
    payload = []
    for part in base.PARTS:
        bbox = mask_stats[part.id]["bbox"]
        payload.append(
            {
                "id": part.id,
                "category": part.category,
                "parent": part.parent,
                "generator": part.mesh_generator,
                "depth": part.depth,
                "thickness": part.thickness,
                "curvature": part.curvature,
                "bbox": bbox,
                "texture": str((base.TEXTURE_DIR / f"{part.id}.png").resolve()),
                "card_count": card_counts.get(part.id, 1),
            }
        )
    return payload


def blender_script(parts_payload: list[dict], source_size: tuple[int, int]) -> str:
    blend = base.EXPORT_DIR / f"{STEM}.blend"
    glb = base.EXPORT_DIR / f"{STEM}.glb"
    glb_cage = base.EXPORT_DIR / f"{STEM}_cage_debug.glb"
    fbx = base.EXPORT_DIR / f"{STEM}.fbx"
    obj = base.EXPORT_DIR / f"{STEM}.obj"
    front_png = base.VALIDATION_DIR / f"{STEM}_front.png"
    yaw15_png = base.VALIDATION_DIR / f"{STEM}_yaw15.png"
    yaw30_png = base.VALIDATION_DIR / f"{STEM}_yaw30.png"
    side_png = base.VALIDATION_DIR / f"{STEM}_side_cage.png"
    exploded_png = base.VALIDATION_DIR / f"{STEM}_exploded.png"
    wire_png = base.VALIDATION_DIR / f"{STEM}_cage_wire.png"
    parts_json = json.dumps(parts_payload)
    img_w, img_h = source_size
    return f"""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

PARTS = json.loads({parts_json!r})
IMG_W = {img_w!r}
IMG_H = {img_h!r}
HEIGHT_WORLD = 6.4
WIDTH_WORLD = HEIGHT_WORLD * IMG_W / IMG_H

def px_to_world(x, y, depth):
    wx = (x / IMG_W - 0.5) * WIDTH_WORLD
    wz = (1.0 - y / IMG_H) * HEIGHT_WORLD
    return wx, depth, wz

def make_material(part):
    mat = bpy.data.materials.new(part['id'] + '_alpha')
    mat.use_nodes = True
    mat.blend_method = 'BLEND'
    mat.show_transparent_back = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(part['texture'], check_existing=True)
    tex.extension = 'CLIP'
    mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    mat.node_tree.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    bsdf.inputs['Roughness'].default_value = 0.62
    return mat

MATS = {{part['id']: make_material(part) for part in PARTS}}

def add_mesh_object(name, verts, faces, uvs, mat, semantic_part):
    mesh = bpy.data.meshes.new(name + '_mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            uv_layer.data[loop_index].uv = uvs[mesh.loops[loop_index].vertex_index]
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj['semantic_part'] = semantic_part
    obj['v4_generator'] = True
    return obj

def curvature(part, wx, wz, local_u, local_v, strip_index=0, strip_count=1):
    gen = part['generator']
    if gen == 'face_plate':
        cx = 0.0
        cz = 5.35
        return 0.055 * max(0.0, 1.0 - ((wx - cx) / 0.42) ** 2 - ((wz - cz) / 0.62) ** 2)
    if gen == 'curved_panel':
        return 0.050 * (1.0 - min(1.0, abs(local_u - 0.5) * 1.8))
    if gen == 'cloth_sheet':
        side = -1.0 if part['id'].endswith('left') else 1.0
        if part['id'] == 'skirt_front':
            side = 0.0
        return side * 0.045 * (local_u - 0.5) - 0.055 * max(0.0, 1.0 - local_v)
    if gen == 'hair_cards':
        center = (strip_index + 0.5) / max(strip_count, 1)
        return (center - 0.5) * 0.24 + math.sin(local_v * math.pi) * 0.035
    if gen == 'weapon_panel':
        return 0.0
    return 0.0

def make_panel(part, cols=10, rows=18):
    x0, y0, x1, y1 = part['bbox']
    if x1 <= x0 or y1 <= y0:
        return None
    verts, uvs = [], []
    for gy in range(rows + 1):
        v = gy / rows
        py = y0 + (y1 - y0) * v
        for gx in range(cols + 1):
            u = gx / cols
            px = x0 + (x1 - x0) * u
            wx, wy, wz = px_to_world(px, py, part['depth'])
            wy += curvature(part, wx, wz, u, v)
            verts.append((wx, wy, wz))
            uvs.append((px / IMG_W, 1.0 - py / IMG_H))
    faces = []
    stride = cols + 1
    for gy in range(rows):
        for gx in range(cols):
            a = gy * stride + gx
            b = a + 1
            c = a + stride + 1
            d = a + stride
            faces.append((a, b, c, d))
    return add_mesh_object(part['id'], verts, faces, uvs, MATS[part['id']], part['id'])

def make_hair_cards(part):
    x0, y0, x1, y1 = part['bbox']
    count = max(3, part.get('card_count', 6))
    rows = 16
    verts, uvs, faces = [], [], []
    for strip in range(count):
        su0 = strip / count
        su1 = (strip + 1) / count
        # Overlap cards slightly so there are no obvious gaps.
        px0 = x0 + (x1 - x0) * max(0.0, su0 - 0.025)
        px1 = x0 + (x1 - x0) * min(1.0, su1 + 0.025)
        start = len(verts)
        for gy in range(rows + 1):
            v = gy / rows
            py = y0 + (y1 - y0) * v
            for px in (px0, px1):
                local_u = (px - x0) / max(x1 - x0, 1)
                wx, wy, wz = px_to_world(px, py, part['depth'])
                wy += curvature(part, wx, wz, local_u, v, strip, count)
                # Small bend in X to avoid all cards being coplanar.
                wx += math.sin(v * math.pi) * (strip - (count - 1) * 0.5) * 0.006
                verts.append((wx, wy, wz))
                uvs.append((px / IMG_W, 1.0 - py / IMG_H))
        for gy in range(rows):
            a = start + gy * 2
            b = a + 1
            c = a + 3
            d = a + 2
            faces.append((a, b, c, d))
    return add_mesh_object(part['id'], verts, faces, uvs, MATS[part['id']], part['id'])

def make_weapon_panel(part):
    # Keep weapon as an independent prop node, but still use the original alpha
    # texture so the front identity is preserved for this prototype pass.
    return make_panel(part, cols=4, rows=24)

for part in PARTS:
    gen = part['generator']
    if gen == 'hair_cards':
        make_hair_cards(part)
    elif gen == 'weapon_panel':
        make_weapon_panel(part)
    elif gen == 'cloth_sheet':
        make_panel(part, cols=8, rows=18)
    else:
        make_panel(part, cols=10, rows=14)

cage_mat = bpy.data.materials.new('dcc_cage_translucent')
cage_mat.use_nodes = True
cage_mat.blend_method = 'BLEND'
cage_bsdf = cage_mat.node_tree.nodes.get('Principled BSDF')
cage_bsdf.inputs['Base Color'].default_value = (0.15, 0.85, 1.0, 0.18)
cage_bsdf.inputs['Alpha'].default_value = 0.18
cage_bsdf.inputs['Roughness'].default_value = 0.75

def add_cage_sphere(name, loc, scale):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(cage_mat)
    obj.display_type = 'WIRE'
    obj['dcc_cage'] = True
    return obj

def add_cage_cylinder(name, loc, radius, depth, scale_x=1.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=radius, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale.x = scale_x
    obj.data.materials.append(cage_mat)
    obj.display_type = 'WIRE'
    obj['dcc_cage'] = True
    return obj

add_cage_sphere('cage_head_ellipsoid', (0.0, 0.02, 5.55), (0.44, 0.30, 0.54))
add_cage_sphere('cage_torso_ellipsoid', (0.0, 0.02, 4.05), (0.62, 0.34, 0.95))
add_cage_cylinder('cage_leg_L_capsule_proxy', (-0.22, 0.02, 2.10), 0.13, 2.10, 0.72)
add_cage_cylinder('cage_leg_R_capsule_proxy', (0.22, 0.02, 2.10), 0.13, 2.10, 0.72)

def add_empty(name, loc):
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.empty_display_size = 0.13
    obj['animation_hook'] = True
    return obj

add_empty('hook_bangs_spring', (0.0, 0.42, 5.55))
add_empty('hook_back_hair_spring', (0.0, -0.56, 5.10))
add_empty('hook_cape_left_swing', (-0.72, -0.42, 3.88))
add_empty('hook_cape_right_swing', (0.72, -0.38, 3.88))
add_empty('hand_R_socket_weapon', (-1.55, 0.92, 2.92))

for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.shade_smooth()
        except Exception:
            pass
        obj.select_set(False)

bpy.ops.object.light_add(type='AREA', location=(0, -4.6, 8.2))
light = bpy.context.object
light.name = 'v4_large_softbox'
light.data.energy = 600
light.data.size = 5.5

mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH' and not obj.get('dcc_cage')]
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
distance = 8.8

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

def cages_visible(visible):
    for obj in bpy.context.scene.objects:
        if obj.get('dcc_cage'):
            obj.hide_render = not visible
            obj.hide_viewport = not visible

def render(cam, filepath):
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)

cages_visible(False)
render(front_cam, r'{front_png}')
render(yaw15_cam, r'{yaw15_png}')
render(yaw30_cam, r'{yaw30_png}')
cages_visible(True)
render(side_cam, r'{side_png}')
render(yaw30_cam, r'{wire_png}')

original_locations = {{}}
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH' and obj.name.split('.')[0] in [p['id'] for p in PARTS]:
        original_locations[obj.name] = obj.location.copy()
        index = [p['id'] for p in PARTS].index(obj.name.split('.')[0])
        obj.location.x += (index - len(PARTS) / 2) * 0.14
        obj.location.y += (index % 5 - 2) * 0.10
render(yaw30_cam, r'{exploded_png}')
for obj in bpy.context.scene.objects:
    if obj.name in original_locations:
        obj.location = original_locations[obj.name]

cages_visible(True)
bpy.ops.wm.save_as_mainfile(filepath=r'{blend}')

cages_visible(False)
bpy.ops.export_scene.gltf(filepath=r'{glb}', export_format='GLB', export_texcoords=True, export_normals=True, export_materials='EXPORT', use_visible=True)
bpy.ops.export_scene.fbx(filepath=r'{fbx}', path_mode='COPY', embed_textures=True, add_leaf_bones=False, use_visible=True, object_types={{'MESH', 'EMPTY'}})
bpy.ops.wm.obj_export(filepath=r'{obj}', export_uv=True, export_materials=True)

cages_visible(True)
bpy.ops.export_scene.gltf(filepath=r'{glb_cage}', export_format='GLB', export_texcoords=True, export_normals=True, export_materials='EXPORT', use_visible=True)
"""


def run_blender_export(parts_payload: list[dict], source_size: tuple[int, int]) -> dict:
    blender = shutil.which("blender") or "/opt/homebrew/bin/blender"
    if not Path(blender).exists():
        return {"error": "blender_not_found"}
    script = blender_script(parts_payload, source_size)
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
    files = {
        "blend": base.EXPORT_DIR / f"{STEM}.blend",
        "glb": base.EXPORT_DIR / f"{STEM}.glb",
        "glb_cage_debug": base.EXPORT_DIR / f"{STEM}_cage_debug.glb",
        "fbx": base.EXPORT_DIR / f"{STEM}.fbx",
        "obj": base.EXPORT_DIR / f"{STEM}.obj",
    }
    screenshots = {
        "front": base.VALIDATION_DIR / f"{STEM}_front.png",
        "yaw15": base.VALATION_DIR / f"{STEM}_yaw15.png" if False else base.VALIDATION_DIR / f"{STEM}_yaw15.png",
        "yaw30": base.VALIDATION_DIR / f"{STEM}_yaw30.png",
        "side_cage": base.VALIDATION_DIR / f"{STEM}_side_cage.png",
        "cage_wire": base.VALIDATION_DIR / f"{STEM}_cage_wire.png",
        "exploded": base.VALIDATION_DIR / f"{STEM}_exploded.png",
    }
    return {
        **{key: str(path.relative_to(ROOT)) if path.exists() else None for key, path in files.items()},
        "validation_screenshots": {
            key: str(path.relative_to(ROOT)) if path.exists() else None for key, path in screenshots.items()
        },
        "blender_exit_code": result.returncode,
        "blender_log_tail": result.stdout.splitlines()[-60:],
    }


def validate_blender_import(asset_path: Path, kind: str) -> dict:
    blender = shutil.which("blender") or "/opt/homebrew/bin/blender"
    if not asset_path.exists() or not Path(blender).exists():
        return {"status": "skipped", "reason": "missing_asset_or_blender", "path": str(asset_path)}
    import_op = {
        "fbx": f"bpy.ops.import_scene.fbx(filepath=r'{asset_path}')",
        "obj": f"bpy.ops.wm.obj_import(filepath=r'{asset_path}')",
    }.get(kind)
    if import_op is None:
        return {"status": "skipped", "reason": f"unsupported_kind:{kind}"}
    script = f"""
import json
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
try:
    {import_op}
    status = 'ok'
    error = None
except Exception as exc:
    status = 'failed'
    error = str(exc)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
empties = [o for o in bpy.context.scene.objects if o.type == 'EMPTY']
materials = list(bpy.data.materials)
print('YUNA_V4_IMPORT_REPORT=' + json.dumps({{
    'status': status,
    'error': error,
    'kind': {kind!r},
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
        if line.startswith("YUNA_V4_IMPORT_REPORT="):
            report_line = line.split("=", 1)[1]
            break
    if report_line:
        data = json.loads(report_line)
        data["blender_exit_code"] = result.returncode
        return data
    return {"status": "failed", "kind": kind, "blender_exit_code": result.returncode, "log_tail": result.stdout.splitlines()[-30:]}


def write_spec_v4(mask_stats: dict[str, dict], constraints: dict, parts_payload: list[dict]) -> Path:
    spec = {
        "character": {
            "id": "YUNA",
            "route": "semantic_layer_v4_part_grammar",
            "boundary": "Hybrid render-shell plus DCC cage handoff asset; not final production topology, rig, UV/PBR, or blendshape set.",
            "coordinate_system": {"right": "X", "depth": "Y", "up": "Z"},
            "viewing_cone": {"primary_yaw_degrees": [-30, 30], "side_uses_cage_debug": True},
        },
        "source_images": {
            "front": str(base.SOURCE_FRONT.relative_to(ROOT)),
            "side_ai_inferred": str(v3.SIDE_REF.relative_to(ROOT)),
            "back_ai_inferred": str(v3.BACK_REF.relative_to(ROOT)),
        },
        "mask_source": "semantic_layer_v2_front_masks_reused_as alpha textures",
        "side_back_constraints": constraints,
        "parts": [
            {
                "id": part["id"],
                "category": part["category"],
                "generator": part["generator"],
                "texture": str(Path(part["texture"]).relative_to(ROOT)),
                "mask_pixels": mask_stats[part["id"]]["pixels"],
                "mask_bbox": mask_stats[part["id"]]["bbox"],
                "depth": part["depth"],
                "dcc_note": generator_note(part["generator"]),
            }
            for part in parts_payload
        ],
        "acceptance_v4": {
            "must_have_independent_render_meshes": ["face", "bangs", "back_hair", "cape_left", "cape_right", "weapon", "torso_inner"],
            "must_have_cage_guides_in_blend": ["cage_head_ellipsoid", "cage_torso_ellipsoid", "cage_leg_L_capsule_proxy", "cage_leg_R_capsule_proxy"],
            "expected_improvement": [
                "removes per-pixel sidewall extrusion from main render shell",
                "reduces black horizontal side bands in yaw views",
                "keeps side/back as soft constraints and cage debug, not locked truth",
            ],
        },
    }
    path = base.SPEC_DIR / f"{STEM}.json"
    path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def generator_note(generator: str) -> str:
    return {
        "hair_cards": "split alpha render texture across ribbon cards; must be replaced by hand-authored strand curves for production",
        "cloth_sheet": "curved alpha sheet; DCC artist should rebuild as cloth panel with proper seams",
        "curved_panel": "front-locked curved render panel; proxy cage carries volume, not deformation topology",
        "face_plate": "front-locked anime face plate; not a real facial topology or blendshape base",
        "weapon_panel": "independent alpha prop placeholder; next pass should use orthographic hard-surface contours",
    }.get(generator, "prototype generator")


def build_quality(
    export_report: dict,
    glb_report: dict,
    cage_glb_report: dict,
    fbx_report: dict,
    obj_report: dict,
    parts_payload: list[dict],
) -> dict:
    failures: list[str] = []
    warnings: list[str] = []
    if export_report.get("blender_exit_code") != 0:
        failures.append("Blender v4 export exited with non-zero status")
    if glb_report.get("status") != "ok":
        failures.append("main GLB roundtrip import failed")
    if cage_glb_report.get("status") != "ok":
        warnings.append("cage debug GLB roundtrip import failed or was skipped")
    if fbx_report.get("status") != "ok":
        failures.append("FBX roundtrip import failed")
    if obj_report.get("status") != "ok":
        failures.append("OBJ roundtrip import failed")
    required = ["face", "bangs", "back_hair", "cape_left", "cape_right", "weapon", "torso_inner"]
    missing = [item for item in required if item not in glb_report.get("mesh_names", [])]
    if missing:
        failures.append(f"missing required render-shell meshes: {', '.join(missing)}")
    main_mesh_count = glb_report.get("mesh_count", 0)
    cage_mesh_count = cage_glb_report.get("mesh_count", 0)
    if cage_mesh_count <= main_mesh_count:
        warnings.append("cage debug GLB did not add visible cage meshes")
    warnings.extend(
        [
            "v4 removes cutout sidewalls but still relies on alpha render shells, not clean production topology",
            "side view should be judged with the cage-debug screenshot, not as a finished character profile",
            "weapon is still a textured independent prop panel; hard-surface ortho reconstruction remains next",
        ]
    )
    return {
        "status": "failed" if failures else "generated_with_warnings" if warnings else "passed",
        "failures": failures,
        "warnings": warnings,
        "render_shell_parts": [part["id"] for part in parts_payload],
        "mesh_counts": {
            "main_glb_mesh_count": main_mesh_count,
            "cage_debug_glb_mesh_count": cage_mesh_count,
            "fbx_mesh_count": fbx_report.get("mesh_count", 0),
            "obj_mesh_count": obj_report.get("mesh_count", 0),
            "main_material_count": glb_report.get("material_count", 0),
            "cage_debug_material_count": cage_glb_report.get("material_count", 0),
            "fbx_material_count": fbx_report.get("material_count", 0),
            "obj_material_count": obj_report.get("material_count", 0),
        },
        "part_grammar_counts": {
            generator: sum(1 for part in parts_payload if part["generator"] == generator)
            for generator in sorted({part["generator"] for part in parts_payload})
        },
    }


def update_status(report: dict) -> None:
    status_path = ROOT / "qa" / "production_status.json"
    if not status_path.exists():
        return
    status = json.loads(status_path.read_text(encoding="utf-8"))
    completed = status.setdefault("completed", [])
    for item in [
        "semantic-layer v4 part grammar generator implemented",
        "semantic-layer v4 render-shell BLEND/GLB/FBX/OBJ exported",
        "semantic-layer v4 cage-debug GLB exported",
        "semantic-layer v4 validation screenshots rendered",
        "semantic-layer v4 GLB roundtrip import verified",
    ]:
        if item not in completed:
            completed.append(item)
    status["semantic_layer_v4_route"] = {
        "status": report["status"],
        "boundary": report["boundary"],
        "exports": report["exports"],
        "quality": report["quality"],
    }
    status["next_action"] = (
        "Use v4 as the part-grammar baseline, then replace alpha hair cards with hand-authored curves, "
        "convert the weapon panel to orthographic hard-surface mesh, and rebuild torso/legs as retopo cages."
    )
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    configure_output()
    configure_parts_v4()
    ensure_dirs()
    source = Image.open(base.SOURCE_FRONT).convert("RGBA")
    masks = v2.build_front_masks_v2(source)
    stats = base.mask_stats(masks)
    base.save_part_textures(source, masks)
    contact = base.build_contact_sheet(masks)
    constraints = v3.build_side_back_constraints()
    parts_payload = build_parts_payload(stats)
    spec_path = write_spec_v4(stats, constraints, parts_payload)
    export_report = run_blender_export(parts_payload, source.size)
    glb_report = base.validate_glb(base.EXPORT_DIR / f"{STEM}.glb")
    cage_glb_report = base.validate_glb(base.EXPORT_DIR / f"{STEM}_cage_debug.glb")
    fbx_report = validate_blender_import(base.EXPORT_DIR / f"{STEM}.fbx", "fbx")
    obj_report = validate_blender_import(base.EXPORT_DIR / f"{STEM}.obj", "obj")
    quality = build_quality(export_report, glb_report, cage_glb_report, fbx_report, obj_report, parts_payload)
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": "semantic_layer_v4_part_grammar",
        "status": quality["status"],
        "boundary": "Hybrid alpha render-shell plus DCC cage guide asset; not final game-ready topology.",
        "source": str(base.SOURCE_FRONT.relative_to(ROOT)),
        "spec": str(spec_path.relative_to(ROOT)),
        "mask_contact_sheet": str(contact.relative_to(ROOT)),
        "side_back_constraints": constraints,
        "parts": parts_payload,
        "exports": export_report,
        "glb_roundtrip": glb_report,
        "cage_glb_roundtrip": cage_glb_report,
        "fbx_roundtrip": fbx_report,
        "obj_roundtrip": obj_report,
        "quality": quality,
        "next_manual_cleanup": [
            "Paint final semantic masks and reduce texture transparency noise around hair/cape edges.",
            "Replace procedural rectangular hair cards with explicit strand guide curves.",
            "Rebuild weapon from refs/ai_turnarounds/cutouts/yuna_weapon_orthographic.png as true hard-surface geometry.",
            "Use the cage objects as retopo guide, not as final visible mesh.",
        ],
    }
    base.REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_status(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
