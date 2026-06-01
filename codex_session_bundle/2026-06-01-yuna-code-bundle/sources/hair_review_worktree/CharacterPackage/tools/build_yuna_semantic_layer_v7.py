#!/usr/bin/env python3
"""Build YUNA semantic-layer v7 assets.

v7 focuses on the visual failure left in v6: the legs are no longer broken, but
the original combined `legs` alpha panel and visible proxy volumes read as large
rectangles. This pass replaces that with left/right leg visual panels plus
subtle rear volumes. It is still a 2.5D DCC handoff asset, not final rigged
character topology.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw

import build_yuna_semantic_layer_v1 as base
import build_yuna_semantic_layer_v2 as v2
import build_yuna_semantic_layer_v3 as v3
import build_yuna_semantic_layer_v4 as v4


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "semantic_layer_v7"
STEM = "yuna_semantic_layer_v7"
CONSTRAINT_DIR = OUT / "constraints"

ORIGINAL_BLENDER_SCRIPT = v4.blender_script


LEG_CLEANUP_CODE_TEMPLATE = r"""
# v7: replace the combined legs rectangle with separate left/right visual leg
# panels and keep continuous rear volumes as subtle depth support.
old_legs = bpy.data.objects.get('legs')
if old_legs is not None:
    bpy.data.objects.remove(old_legs, do_unlink=True)

def make_plain_material(name, color, alpha=1.0, blend=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    if blend:
        mat.blend_method = 'BLEND'
        mat.show_transparent_back = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Alpha'].default_value = alpha
    bsdf.inputs['Roughness'].default_value = 0.70
    return mat

def make_alpha_texture_material(name, texture_path, alpha=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.blend_method = 'BLEND'
    mat.show_transparent_back = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(texture_path, check_existing=True)
    tex.extension = 'CLIP'
    mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    mat.node_tree.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    bsdf.inputs['Alpha'].default_value = alpha
    bsdf.inputs['Roughness'].default_value = 0.68
    return mat

leg_L_mat = make_alpha_texture_material('leg_L_visual_alpha', r'__LEG_L_TEX__', 1.0)
leg_R_mat = make_alpha_texture_material('leg_R_visual_alpha', r'__LEG_R_TEX__', 1.0)
leg_volume_L_mat = make_plain_material('leg_L_rear_volume_subtle', (0.74, 0.74, 0.68, 0.075), 0.075, True)
leg_volume_R_mat = make_plain_material('leg_R_rear_volume_subtle', (0.40, 0.41, 0.39, 0.065), 0.065, True)
boot_proxy_mat = make_plain_material('boot_rear_shadow_volume_subtle', (0.018, 0.026, 0.030, 0.025), 0.025, True)
guide_mat = make_plain_material('leg_debug_loop_hidden_in_main', (0.020, 0.025, 0.028, 0.42), 0.42, True)

def uv_from_world(wx, wz):
    return (max(0.0, min(1.0, wx / WIDTH_WORLD + 0.5)), max(0.0, min(1.0, wz / HEIGHT_WORLD)))

def make_leg_visual_panel(name, side, mat, x_center_top, x_center_bottom, z_top, z_bottom, width_top, width_bottom, y_depth):
    rows = 22
    cols = 3
    verts, uvs, faces = [], [], []
    for gy in range(rows + 1):
        t = gy / rows
        z = z_top + (z_bottom - z_top) * t
        x_center = x_center_top + (x_center_bottom - x_center_top) * t + math.sin(t * math.pi) * side * 0.025
        width = width_top + (width_bottom - width_top) * t
        for gx in range(cols + 1):
            u = gx / cols
            x = x_center + (u - 0.5) * width
            # Gentle front-facing curvature without turning into a cylinder.
            y = y_depth + 0.018 * (1.0 - abs(u - 0.5) * 2.0)
            verts.append((x, y, z))
            uvs.append(uv_from_world(x, z))
    stride = cols + 1
    for gy in range(rows):
        for gx in range(cols):
            a = gy * stride + gx
            faces.append((a, a + 1, a + stride + 1, a + stride))
    obj = add_mesh_object(name, verts, faces, uvs, mat, name)
    obj['v7_leg_visual_panel'] = True
    return obj

def make_limb_volume(name, side, mat):
    rings = 14
    segs = 18
    z_top = 3.22
    z_bottom = 1.02
    x_top = -0.19 if side < 0 else 0.23
    x_bottom = -0.30 if side < 0 else 0.40
    y_center = -0.06
    verts, uvs, faces = [], [], []
    for i in range(rings + 1):
        t = i / rings
        z = z_top + (z_bottom - z_top) * t
        x_center = x_top + (x_bottom - x_top) * t + math.sin(t * math.pi) * side * 0.025
        if t < 0.34:
            rx = 0.132 - 0.022 * (t / 0.34)
            ry = 0.055 - 0.010 * (t / 0.34)
        elif t < 0.56:
            rx = 0.096 + 0.018 * ((t - 0.34) / 0.22)
            ry = 0.040 + 0.010 * ((t - 0.34) / 0.22)
        else:
            rx = 0.114 - 0.040 * ((t - 0.56) / 0.44)
            ry = 0.050 - 0.020 * ((t - 0.56) / 0.44)
        for j in range(segs):
            angle = 2.0 * math.pi * j / segs
            px = x_center + rx * math.cos(angle)
            py = y_center + ry * math.sin(angle)
            verts.append((px, py, z))
            uvs.append(uv_from_world(px, z))
    for i in range(rings):
        for j in range(segs):
            a = i * segs + j
            b = i * segs + ((j + 1) % segs)
            c = (i + 1) * segs + ((j + 1) % segs)
            d = (i + 1) * segs + j
            faces.append((a, b, c, d))
    obj = add_mesh_object(name, verts, faces, uvs, mat, name)
    obj['v7_rear_leg_volume'] = True
    return obj

def make_boot_proxy(name, side):
    rings = 7
    segs = 14
    z_top = 0.86
    z_bottom = 0.38
    x_top = -0.30 if side < 0 else 0.40
    x_bottom = -0.34 if side < 0 else 0.45
    y_center = 0.16
    verts, uvs, faces = [], [], []
    for i in range(rings + 1):
        t = i / rings
        z = z_top + (z_bottom - z_top) * t
        x_center = x_top + (x_bottom - x_top) * t
        rx = 0.055 + 0.010 * t
        ry = 0.036 + 0.010 * t
        for j in range(segs):
            angle = 2.0 * math.pi * j / segs
            px = x_center + rx * math.cos(angle)
            py = y_center + ry * math.sin(angle)
            verts.append((px, py, z))
            uvs.append(uv_from_world(px, z))
    for i in range(rings):
        for j in range(segs):
            a = i * segs + j
            b = i * segs + ((j + 1) % segs)
            c = (i + 1) * segs + ((j + 1) % segs)
            d = (i + 1) * segs + j
            faces.append((a, b, c, d))
    obj = add_mesh_object(name, verts, faces, uvs, boot_proxy_mat, name)
    obj['v7_boot_rear_proxy'] = True
    return obj

def add_leg_band(name, side, z, radius_x, radius_y):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.014, major_segments=48, minor_segments=6, location=((-0.20 if side < 0 else 0.23), -0.08, z))
    obj = bpy.context.object
    obj.name = name
    obj.scale.x = radius_x
    obj.scale.y = radius_y
    obj.data.materials.append(guide_mat)
    obj['v7_leg_debug_loop'] = True
    obj['dcc_cage'] = True
    return obj

make_leg_visual_panel('leg_L_visual_panel', -1, leg_L_mat, -0.20, -0.31, 3.20, 0.98, 0.29, 0.15, 0.32)
make_leg_visual_panel('leg_R_visual_panel', 1, leg_R_mat, 0.23, 0.40, 3.20, 0.98, 0.27, 0.14, 0.30)
make_limb_volume('leg_L_retopo_proxy', -1, leg_volume_L_mat)
make_limb_volume('leg_R_retopo_proxy', 1, leg_volume_R_mat)
make_boot_proxy('boot_L_hardsurface_proxy', -1)
make_boot_proxy('boot_R_hardsurface_proxy', 1)
add_leg_band('leg_L_thigh_strap_proxy', -1, 2.98, 0.126, 0.070)
add_leg_band('leg_R_thigh_strap_proxy', 1, 2.98, 0.126, 0.070)
add_leg_band('leg_L_knee_loop_proxy', -1, 2.28, 0.100, 0.055)
add_leg_band('leg_R_knee_loop_proxy', 1, 2.28, 0.100, 0.055)
"""


HOOK_CODE = """
add_empty('hook_knee_L', (-0.24, -0.10, 2.28))
add_empty('hook_knee_R', (0.31, -0.10, 2.28))
add_empty('hook_ankle_L', (-0.31, -0.10, 1.02))
add_empty('hook_ankle_R', (0.40, -0.10, 1.02))
"""


def configure_output() -> None:
    v4.OUT = OUT
    v4.STEM = STEM
    v4.CONSTRAINT_DIR = CONSTRAINT_DIR
    v3.OUT = OUT
    v3.CONSTRAINT_DIR = CONSTRAINT_DIR
    base.OUT = OUT
    base.MASK_DIR = OUT / "masks" / "front"
    base.TEXTURE_DIR = OUT / "textures"
    base.OBJ_DIR = OUT / "obj"
    base.PART_OBJ_DIR = base.OBJ_DIR / "parts"
    base.EXPORT_DIR = OUT / "exports"
    base.VALIDATION_DIR = OUT / "validation"
    base.SPEC_DIR = OUT / "specs"
    base.REPORT_PATH = OUT / "validation_report.json"


def make_leg_texture(source: Image.Image, name: str, points: list[tuple[int, int]]) -> Path:
    size = source.size
    rgba = source.copy().convert("RGBA")
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    alpha = source.getchannel("A")
    out_alpha = Image.new("L", size, 0)
    mp = mask.load()
    ap = alpha.load()
    op = out_alpha.load()
    for y in range(size[1]):
        for x in range(size[0]):
            r, g, b, _a = rgba.getpixel((x, y))
            brightness = (r + g + b) / 3
            pale_leg = brightness > 132 and abs(r - g) < 70 and abs(g - b) < 85
            skin_hint = r > 145 and g > 104 and b > 95 and brightness > 118
            if mp[x, y] > 0 and ap[x, y] > 22 and (pale_leg or skin_hint):
                op[x, y] = 255
    rgba.putalpha(out_alpha)
    path = base.TEXTURE_DIR / f"{name}.png"
    rgba.save(path)
    return path


def prepare_leg_textures(source: Image.Image) -> tuple[Path, Path]:
    left = make_leg_texture(
        source,
        "leg_L_visual_panel",
        [(322, 764), (512, 760), (520, 1268), (358, 1300), (292, 1042)],
    )
    right = make_leg_texture(
        source,
        "leg_R_visual_panel",
        [(500, 760), (706, 800), (712, 1292), (520, 1306), (472, 1000)],
    )
    return left, right


def blender_script_v7(parts_payload: list[dict], source_size: tuple[int, int], leg_l_tex: Path, leg_r_tex: Path) -> str:
    script = ORIGINAL_BLENDER_SCRIPT(parts_payload, source_size)
    cage_marker = "cage_mat = bpy.data.materials.new('dcc_cage_translucent')"
    hook_marker = "add_empty('hand_R_socket_weapon', (-1.55, 0.92, 2.92))"
    if cage_marker not in script:
        raise RuntimeError("v7 cage injection marker missing from v4 blender script")
    if hook_marker not in script:
        raise RuntimeError("v7 hook injection marker missing from v4 blender script")
    leg_code = (
        LEG_CLEANUP_CODE_TEMPLATE
        .replace("__LEG_L_TEX__", str(leg_l_tex.resolve()))
        .replace("__LEG_R_TEX__", str(leg_r_tex.resolve()))
    )
    script = script.replace(cage_marker, leg_code + "\n" + cage_marker)
    script = script.replace(hook_marker, hook_marker + "\n" + HOOK_CODE)
    return script


def write_spec_v7(mask_stats: dict[str, dict], constraints: dict, parts_payload: list[dict]) -> Path:
    path = v4.write_spec_v4(mask_stats, constraints, parts_payload)
    spec = json.loads(path.read_text(encoding="utf-8"))
    spec["character"]["route"] = "semantic_layer_v7_split_leg_visuals"
    spec["character"]["boundary"] = (
        "v7 splits the visible leg treatment into left/right panels with subtle rear volumes. "
        "It is a cleaner 2.5D DCC handoff, not final skinned topology."
    )
    spec["v7_leg_cleanup"] = {
        "removed_flat_parts": ["legs"],
        "visual_leg_panels": ["leg_L_visual_panel", "leg_R_visual_panel"],
        "rear_volume_guides": ["leg_L_retopo_proxy", "leg_R_retopo_proxy"],
        "boot_rear_proxies": ["boot_L_hardsurface_proxy", "boot_R_hardsurface_proxy"],
        "debug_only_loops": [
            "leg_L_thigh_strap_proxy",
            "leg_R_thigh_strap_proxy",
            "leg_L_knee_loop_proxy",
            "leg_R_knee_loop_proxy",
        ],
    }
    spec["acceptance_v7"] = {
        "must_include_split_leg_visual_panels": True,
        "must_keep_original_boot_panel": True,
        "must_hide_debug_leg_loops_from_main_glb": True,
        "known_limits": [
            "leg panels are still 2.5D projected surfaces",
            "rear volumes are subtle continuity guides, not deformation-ready legs",
            "no real UV unwrap or skin weights yet",
        ],
    }
    v7_path = base.SPEC_DIR / f"{STEM}.json"
    v7_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if path != v7_path and path.exists():
        path.unlink()
    return v7_path


def update_status(report: dict) -> None:
    status_path = ROOT / "qa" / "production_status.json"
    if not status_path.exists():
        return
    status = json.loads(status_path.read_text(encoding="utf-8"))
    completed = status.setdefault("completed", [])
    for item in [
        "semantic-layer v7 split leg visual panels generated",
        "semantic-layer v7 BLEND/GLB/FBX/OBJ roundtrip verified",
        "semantic-layer v7 validation screenshots rendered",
    ]:
        if item not in completed:
            completed.append(item)
    status["semantic_layer_v7_route"] = {
        "status": report["status"],
        "boundary": report["boundary"],
        "exports": report["exports"],
        "quality": report["quality"],
    }
    status["next_action"] = (
        "Use v7 as the current best 2.5D visual baseline. Next hand-retopo the split leg panels into "
        "true quads, clean boot geometry, then skin and pose-test knees/ankles."
    )
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    configure_output()
    v4.configure_parts_v4()
    v4.ensure_dirs()
    source = Image.open(base.SOURCE_FRONT).convert("RGBA")
    masks = v2.build_front_masks_v2(source)
    stats = base.mask_stats(masks)
    base.save_part_textures(source, masks)
    leg_l_tex, leg_r_tex = prepare_leg_textures(source)
    contact = base.build_contact_sheet(masks)
    constraints = v3.build_side_back_constraints()
    parts_payload = v4.build_parts_payload(stats)
    spec_path = write_spec_v7(stats, constraints, parts_payload)
    v4.blender_script = lambda payload, size: blender_script_v7(payload, size, leg_l_tex, leg_r_tex)
    export_report = v4.run_blender_export(parts_payload, source.size)
    glb_report = base.validate_glb(base.EXPORT_DIR / f"{STEM}.glb")
    cage_glb_report = base.validate_glb(base.EXPORT_DIR / f"{STEM}_cage_debug.glb")
    fbx_report = v4.validate_blender_import(base.EXPORT_DIR / f"{STEM}.fbx", "fbx")
    obj_report = v4.validate_blender_import(base.EXPORT_DIR / f"{STEM}.obj", "obj")
    quality = v4.build_quality(export_report, glb_report, cage_glb_report, fbx_report, obj_report, parts_payload)

    mesh_names = set(glb_report.get("mesh_names", []))
    cage_mesh_names = set(cage_glb_report.get("mesh_names", []))
    empty_names = set(glb_report.get("empty_names", []))
    required_main = {
        "leg_L_visual_panel",
        "leg_R_visual_panel",
        "leg_L_retopo_proxy",
        "leg_R_retopo_proxy",
        "boot_L_hardsurface_proxy",
        "boot_R_hardsurface_proxy",
    }
    forbidden_main = {"leg_L_thigh_strap_proxy", "leg_R_thigh_strap_proxy", "leg_L_knee_loop_proxy", "leg_R_knee_loop_proxy"}
    required_cage = forbidden_main
    required_hooks = {"hook_knee_L", "hook_knee_R", "hook_ankle_L", "hook_ankle_R"}
    failures = quality.setdefault("failures", [])
    missing_main = sorted(required_main - mesh_names)
    leaked_debug = sorted(forbidden_main & mesh_names)
    missing_cage = sorted(required_cage - cage_mesh_names)
    missing_hooks = sorted(required_hooks - empty_names)
    if missing_main:
        quality["status"] = "failed"
        failures.append(f"missing v7 main leg meshes: {', '.join(missing_main)}")
    if leaked_debug:
        quality["status"] = "failed"
        failures.append(f"debug leg guide meshes leaked into main GLB: {', '.join(leaked_debug)}")
    if missing_cage:
        quality["status"] = "failed"
        failures.append(f"debug leg guide meshes missing from cage GLB: {', '.join(missing_cage)}")
    if missing_hooks:
        quality["status"] = "failed"
        failures.append(f"missing knee/ankle hooks: {', '.join(missing_hooks)}")
    quality.setdefault("warnings", []).append("v7 is the current best 2.5D leg visual pass, not final skinned leg topology")
    quality["v7_required_main_meshes"] = sorted(required_main)
    quality["v7_debug_only_meshes"] = sorted(forbidden_main)

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": "semantic_layer_v7_split_leg_visuals",
        "status": quality["status"],
        "boundary": "Split leg visual panels plus subtle rear volume baseline; not final game-ready skinned legs.",
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
            "Hand-retopo split leg visual panels into continuous quad loops.",
            "Replace rear volume guides with skinned thigh/shin/calf geometry.",
            "Clean boot mesh from orthographic shoe silhouette instead of rough rear proxies.",
        ],
    }
    base.REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_status(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
