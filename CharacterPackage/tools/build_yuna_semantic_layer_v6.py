#!/usr/bin/env python3
"""Build YUNA semantic-layer v6 assets.

v6 replaces the v5 "leg continuity underlay" cylinders with explicit continuous
left/right leg topology proxies and independent boot proxies. This is still a
DCC handoff asset, but it removes the most visible broken-leg failure in yaw
views and gives later retopology/rigging a cleaner target than transparent
underlay tubes.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

import build_yuna_semantic_layer_v1 as base
import build_yuna_semantic_layer_v2 as v2
import build_yuna_semantic_layer_v3 as v3
import build_yuna_semantic_layer_v4 as v4


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "semantic_layer_v6"
STEM = "yuna_semantic_layer_v6"
CONSTRAINT_DIR = OUT / "constraints"

ORIGINAL_BLENDER_SCRIPT = v4.blender_script


LEG_RETOPO_CODE_TEMPLATE = r"""
# v6 keeps the original leg/boot alpha panels as the visual source of truth and
# adds continuous topology proxies behind them. That avoids the v5 broken-leg
# read without replacing the design with crude procedural cylinders.

def make_plain_material(name, color, alpha=1.0, blend=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    if blend:
        mat.blend_method = 'BLEND'
        mat.show_transparent_back = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Alpha'].default_value = alpha
    bsdf.inputs['Roughness'].default_value = 0.68
    return mat

leg_volume_mat = make_plain_material('leg_volume_warm_white_stocking', (0.76, 0.76, 0.70, 0.30), 0.30, True)
leg_rear_mat = make_plain_material('leg_rear_dim_stocking', (0.36, 0.37, 0.36, 0.22), 0.22, True)
boot_proxy_mat = make_plain_material('boot_proxy_shadow_volume', (0.018, 0.026, 0.030, 0.10), 0.10, True)
strap_proxy_mat = make_plain_material('leg_strap_proxy_black', (0.020, 0.025, 0.028, 0.42), 0.42, True)

def uv_from_world(wx, wz):
    u = max(0.0, min(1.0, wx / WIDTH_WORLD + 0.5))
    v = max(0.0, min(1.0, wz / HEIGHT_WORLD))
    return (u, v)

def make_limb_volume(name, side, mat):
    # Continuous superellipse-like rings with intentional knee and ankle taper.
    # side -1 = image-left leg, +1 = image-right leg.
    rings = 18
    segs = 24
    z_top = 3.28
    z_bottom = 0.98
    x_top = -0.20 if side < 0 else 0.23
    x_bottom = -0.31 if side < 0 else 0.40
    y_center = 0.105
    verts = []
    uvs = []
    faces = []

    def radius_profile(t):
        # t 0 top, 1 bottom. Wider thigh, pinched knee, calf, slim ankle.
        if t < 0.34:
            k = t / 0.34
            rx = 0.155 - 0.030 * k
            ry = 0.070 - 0.014 * k
        elif t < 0.56:
            k = (t - 0.34) / 0.22
            rx = 0.105 + 0.020 * k
            ry = 0.052 + 0.012 * k
        else:
            k = (t - 0.56) / 0.44
            rx = 0.125 - 0.046 * k
            ry = 0.062 - 0.024 * k
        return max(rx, 0.055), max(ry, 0.045)

    for i in range(rings + 1):
        t = i / rings
        z = z_top + (z_bottom - z_top) * t
        bend = math.sin(t * math.pi) * (0.030 * side)
        x_center = x_top + (x_bottom - x_top) * t + bend
        rx, ry = radius_profile(t)
        for j in range(segs):
            angle = 2.0 * math.pi * j / segs
            # Slight superellipse bias without adding a dependency.
            ca = math.cos(angle)
            sa = math.sin(angle)
            px = x_center + rx * math.copysign(abs(ca) ** 0.72, ca)
            py = y_center + ry * math.copysign(abs(sa) ** 0.72, sa)
            verts.append((px, py, z))
            uvs.append(uv_from_world(px, z))

    for i in range(rings):
        for j in range(segs):
            a = i * segs + j
            b = i * segs + ((j + 1) % segs)
            c = (i + 1) * segs + ((j + 1) % segs)
            d = (i + 1) * segs + j
            faces.append((a, b, c, d))

    # Cap top and bottom so this imports as a solid proxy, not a paper tube.
    top_center = len(verts)
    verts.append((x_top, y_center, z_top))
    uvs.append(uv_from_world(x_top, z_top))
    bottom_center = len(verts)
    verts.append((x_bottom, y_center, z_bottom))
    uvs.append(uv_from_world(x_bottom, z_bottom))
    for j in range(segs):
        faces.append((top_center, j, (j + 1) % segs))
        a = rings * segs + j
        b = rings * segs + ((j + 1) % segs)
        faces.append((bottom_center, b, a))

    obj = add_mesh_object(name, verts, faces, uvs, mat, name)
    obj['v6_retopo_proxy'] = True
    obj['semantic_category'] = 'continuous_leg'
    return obj

def make_boot_proxy(name, side):
    rings = 8
    segs = 18
    z_top = 0.90
    z_bottom = 0.38
    x_top = -0.31 if side < 0 else 0.40
    x_bottom = -0.34 if side < 0 else 0.45
    y_center = 0.26
    verts = []
    uvs = []
    faces = []
    for i in range(rings + 1):
        t = i / rings
        z = z_top + (z_bottom - z_top) * t
        x_center = x_top + (x_bottom - x_top) * t
        rx = 0.060 + 0.010 * t
        ry = 0.040 + 0.014 * t
        for j in range(segs):
            angle = 2.0 * math.pi * j / segs
            ca = math.cos(angle)
            sa = math.sin(angle)
            toe_push = -0.035 * max(0.0, t - 0.55) if sa < -0.2 else 0.0
            px = x_center + rx * math.copysign(abs(ca) ** 0.75, ca)
            py = y_center + toe_push + ry * math.copysign(abs(sa) ** 0.75, sa)
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
    obj['v6_hardsurface_proxy'] = True
    obj['semantic_category'] = 'boot'
    return obj

def add_leg_band(name, side, z, radius_x, radius_y):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.018, major_segments=48, minor_segments=6, location=(( -0.20 if side < 0 else 0.23), -0.11, z))
    obj = bpy.context.object
    obj.name = name
    obj.scale.x = radius_x
    obj.scale.y = radius_y
    obj.data.materials.append(strap_proxy_mat)
    obj['v6_leg_band'] = True
    obj['dcc_cage'] = True
    return obj

leg_L = make_limb_volume('leg_L_retopo_proxy', -1, leg_volume_mat)
leg_R = make_limb_volume('leg_R_retopo_proxy', 1, leg_rear_mat)
boot_L = make_boot_proxy('boot_L_hardsurface_proxy', -1)
boot_R = make_boot_proxy('boot_R_hardsurface_proxy', 1)

add_leg_band('leg_L_thigh_strap_proxy', -1, 2.98, 0.135, 0.095)
add_leg_band('leg_R_thigh_strap_proxy', 1, 2.98, 0.135, 0.095)
add_leg_band('leg_L_knee_loop_proxy', -1, 2.28, 0.110, 0.082)
add_leg_band('leg_R_knee_loop_proxy', 1, 2.28, 0.110, 0.082)
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


def blender_script_v6(parts_payload: list[dict], source_size: tuple[int, int]) -> str:
    script = ORIGINAL_BLENDER_SCRIPT(parts_payload, source_size)
    cage_marker = "cage_mat = bpy.data.materials.new('dcc_cage_translucent')"
    hook_marker = "add_empty('hand_R_socket_weapon', (-1.55, 0.92, 2.92))"
    if cage_marker not in script:
        raise RuntimeError("v6 cage injection marker missing from v4 blender script")
    if hook_marker not in script:
        raise RuntimeError("v6 hook injection marker missing from v4 blender script")
    leg_code = LEG_RETOPO_CODE_TEMPLATE.replace(
        "__FRONT_TEXTURE__",
        str((base.TEXTURE_DIR / "yuna_semantic_front_source.png").resolve()),
    )
    script = script.replace(cage_marker, leg_code + "\n" + cage_marker)
    script = script.replace(hook_marker, hook_marker + "\n" + HOOK_CODE)
    return script


def write_spec_v6(mask_stats: dict[str, dict], constraints: dict, parts_payload: list[dict]) -> Path:
    path = v4.write_spec_v4(mask_stats, constraints, parts_payload)
    spec = json.loads(path.read_text(encoding="utf-8"))
    spec["character"]["route"] = "semantic_layer_v6_leg_retopo_proxy"
    spec["character"]["boundary"] = (
        "v6 replaces broken leg alpha panels and v5 underlay cylinders with continuous leg/boot topology proxies; "
        "still not final skinned production topology."
    )
    spec["v6_visible_replacements"] = {
        "removed_flat_parts": ["legs", "boots"],
        "continuous_leg_proxies": ["leg_L_retopo_proxy", "leg_R_retopo_proxy"],
        "boot_proxies": ["boot_L_hardsurface_proxy", "boot_R_hardsurface_proxy"],
        "leg_guides": [
            "leg_L_thigh_strap_proxy",
            "leg_R_thigh_strap_proxy",
            "leg_L_knee_loop_proxy",
            "leg_R_knee_loop_proxy",
        ],
    }
    spec["acceptance_v6"] = {
        "must_include_continuous_leg_meshes": True,
        "must_not_include_v5_underlay_meshes": True,
        "must_include_knee_and_ankle_hooks": True,
        "known_limits": [
            "leg material is front-projected and still needs hand UV/PBR cleanup",
            "boot forms are simple hard-surface proxies, not final shoes",
            "no real skin weights or deformation tests yet",
        ],
    }
    v6_path = base.SPEC_DIR / f"{STEM}.json"
    v6_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if path != v6_path and path.exists():
        path.unlink()
    return v6_path


def update_status(report: dict) -> None:
    status_path = ROOT / "qa" / "production_status.json"
    if not status_path.exists():
        return
    status = json.loads(status_path.read_text(encoding="utf-8"))
    completed = status.setdefault("completed", [])
    for item in [
        "semantic-layer v6 continuous leg topology proxies generated",
        "semantic-layer v6 BLEND/GLB/FBX/OBJ roundtrip verified",
        "semantic-layer v6 validation screenshots rendered",
    ]:
        if item not in completed:
            completed.append(item)
    status["semantic_layer_v6_route"] = {
        "status": report["status"],
        "boundary": report["boundary"],
        "exports": report["exports"],
        "quality": report["quality"],
    }
    status["next_action"] = (
        "Use v6 as the corrected leg-volume baseline. Next replace proxy legs with hand-retopo leg loops, "
        "clean front-projected UVs, and add actual skin weights before any animation claim."
    )
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    configure_output()
    v4.configure_parts_v4()
    v4.ensure_dirs()
    v4.blender_script = blender_script_v6
    source = Image.open(base.SOURCE_FRONT).convert("RGBA")
    masks = v2.build_front_masks_v2(source)
    stats = base.mask_stats(masks)
    base.save_part_textures(source, masks)
    contact = base.build_contact_sheet(masks)
    constraints = v3.build_side_back_constraints()
    parts_payload = v4.build_parts_payload(stats)
    spec_path = write_spec_v6(stats, constraints, parts_payload)
    export_report = v4.run_blender_export(parts_payload, source.size)
    glb_report = base.validate_glb(base.EXPORT_DIR / f"{STEM}.glb")
    cage_glb_report = base.validate_glb(base.EXPORT_DIR / f"{STEM}_cage_debug.glb")
    fbx_report = v4.validate_blender_import(base.EXPORT_DIR / f"{STEM}.fbx", "fbx")
    obj_report = v4.validate_blender_import(base.EXPORT_DIR / f"{STEM}.obj", "obj")
    quality = v4.build_quality(export_report, glb_report, cage_glb_report, fbx_report, obj_report, parts_payload)

    mesh_names = set(glb_report.get("mesh_names", []))
    empty_names = set(glb_report.get("empty_names", []))
    required_meshes = {
        "leg_L_retopo_proxy",
        "leg_R_retopo_proxy",
        "boot_L_hardsurface_proxy",
        "boot_R_hardsurface_proxy",
    }
    forbidden_meshes = {"leg_L_continuity_underlay", "leg_R_continuity_underlay"}
    required_hooks = {"hook_knee_L", "hook_knee_R", "hook_ankle_L", "hook_ankle_R"}
    missing_required = sorted(required_meshes - mesh_names)
    leaked_forbidden = sorted(forbidden_meshes & mesh_names)
    missing_hooks = sorted(required_hooks - empty_names)
    if missing_required:
        quality["status"] = "failed"
        quality.setdefault("failures", []).append(f"missing v6 leg/boot proxy meshes: {', '.join(missing_required)}")
    if leaked_forbidden:
        quality["status"] = "failed"
        quality.setdefault("failures", []).append(f"v5 underlay meshes leaked into v6: {', '.join(leaked_forbidden)}")
    if missing_hooks:
        quality["status"] = "failed"
        quality.setdefault("failures", []).append(f"missing v6 knee/ankle hooks: {', '.join(missing_hooks)}")
    quality.setdefault("warnings", []).append("v6 leg proxies are continuous DCC retopo guides, not final skinned animation topology")
    quality["v6_required_meshes"] = sorted(required_meshes)
    quality["v6_required_hooks"] = sorted(required_hooks)

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": "semantic_layer_v6_leg_retopo_proxy",
        "status": quality["status"],
        "boundary": "Continuous leg/boot topology proxy baseline; not final game-ready skinned legs.",
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
            "Retopo the leg proxies into clean quad loops around hip, knee and ankle.",
            "Reproject or repaint stocking/boot UVs instead of relying on front planar texture sampling.",
            "Add armature bones and skin weights, then pose-test knees and ankles.",
        ],
    }
    base.REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_status(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
