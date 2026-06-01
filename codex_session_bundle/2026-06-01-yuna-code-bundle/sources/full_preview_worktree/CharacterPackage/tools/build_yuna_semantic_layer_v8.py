#!/usr/bin/env python3
"""Build YUNA semantic-layer v8 assets.

v8 keeps the v7 split-leg visual pass, but moves the generated leg/boot volume
guides out of the beauty/main export. Those guides are useful for DCC repair,
but they read as broken gray blocks in front/yaw renders, so they belong only
in the cage-debug GLB and Blender handoff scene.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

import build_yuna_semantic_layer_v7 as v7


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "semantic_layer_v8"
STEM = "yuna_semantic_layer_v8"
CONSTRAINT_DIR = OUT / "constraints"


def configure_output() -> None:
    v7.OUT = OUT
    v7.STEM = STEM
    v7.CONSTRAINT_DIR = CONSTRAINT_DIR
    v7.v4.OUT = OUT
    v7.v4.STEM = STEM
    v7.v4.CONSTRAINT_DIR = CONSTRAINT_DIR
    v7.v3.OUT = OUT
    v7.v3.CONSTRAINT_DIR = CONSTRAINT_DIR
    v7.base.OUT = OUT
    v7.base.MASK_DIR = OUT / "masks" / "front"
    v7.base.TEXTURE_DIR = OUT / "textures"
    v7.base.OBJ_DIR = OUT / "obj"
    v7.base.PART_OBJ_DIR = v7.base.OBJ_DIR / "parts"
    v7.base.EXPORT_DIR = OUT / "exports"
    v7.base.VALIDATION_DIR = OUT / "validation"
    v7.base.SPEC_DIR = OUT / "specs"
    v7.base.REPORT_PATH = OUT / "validation_report.json"


def patch_v7_template_for_v8() -> None:
    template = v7.LEG_CLEANUP_CODE_TEMPLATE
    template = template.replace(
        "leg_R_mat = make_alpha_texture_material('leg_R_visual_alpha', r'__LEG_R_TEX__', 1.0)",
        (
            "leg_R_mat = make_alpha_texture_material('leg_R_visual_alpha', r'__LEG_R_TEX__', 1.0)\n"
            "for _leg_mat in (leg_L_mat, leg_R_mat):\n"
            "    _leg_mat.blend_method = 'CLIP'\n"
            "    _leg_mat.alpha_threshold = 0.45\n"
            "    _leg_mat.show_transparent_back = False"
        ),
    )
    template = template.replace(
        "obj['v7_rear_leg_volume'] = True\n    return obj",
        "obj['v7_rear_leg_volume'] = True\n    obj['dcc_cage'] = True\n    return obj",
    )
    template = template.replace(
        "obj['v7_boot_rear_proxy'] = True\n    return obj",
        "obj['v7_boot_rear_proxy'] = True\n    obj['dcc_cage'] = True\n    return obj",
    )
    v7.LEG_CLEANUP_CODE_TEMPLATE = template


def write_spec_v8(mask_stats: dict[str, dict], constraints: dict, parts_payload: list[dict]) -> Path:
    path = v7.write_spec_v7(mask_stats, constraints, parts_payload)
    spec = json.loads(path.read_text(encoding="utf-8"))
    spec["character"]["route"] = "semantic_layer_v8_beauty_main_debug_cage_split"
    spec["character"]["boundary"] = (
        "v8 keeps visible split leg panels in the main GLB and moves leg/boot "
        "volume guides to the cage-debug GLB. It is still a 2.5D DCC handoff, "
        "not final skinned topology."
    )
    spec["v8_visibility_split"] = {
        "main_visible_meshes": ["leg_L_visual_panel", "leg_R_visual_panel", "boots"],
        "debug_only_guides": [
            "leg_L_retopo_proxy",
            "leg_R_retopo_proxy",
            "boot_L_hardsurface_proxy",
            "boot_R_hardsurface_proxy",
            "leg_L_thigh_strap_proxy",
            "leg_R_thigh_strap_proxy",
            "leg_L_knee_loop_proxy",
            "leg_R_knee_loop_proxy",
        ],
        "reason": "Volume guides caused gray-block leg artifacts in beauty renders.",
    }
    spec_path = v7.base.SPEC_DIR / f"{STEM}.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if path != spec_path and path.exists():
        path.unlink()
    return spec_path


def update_status(report: dict) -> None:
    status_path = ROOT / "qa" / "production_status.json"
    if not status_path.exists():
        return
    status = json.loads(status_path.read_text(encoding="utf-8"))
    completed = status.setdefault("completed", [])
    for item in [
        "semantic-layer v8 beauty/debug visibility split generated",
        "semantic-layer v8 BLEND/GLB/FBX/OBJ roundtrip verified",
        "semantic-layer v8 validation screenshots rendered",
    ]:
        if item not in completed:
            completed.append(item)
    status["semantic_layer_v8_route"] = {
        "status": report["status"],
        "boundary": report["boundary"],
        "exports": report["exports"],
        "quality": report["quality"],
    }
    status["next_action"] = (
        "Use v8 for visual review. Use v8 cage-debug GLB/BLEND for DCC leg retopo, "
        "boot cleanup, and knee/ankle skinning work."
    )
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    configure_output()
    patch_v7_template_for_v8()
    v7.v4.configure_parts_v4()
    v7.v4.ensure_dirs()

    source = Image.open(v7.base.SOURCE_FRONT).convert("RGBA")
    masks = v7.v2.build_front_masks_v2(source)
    stats = v7.base.mask_stats(masks)
    v7.base.save_part_textures(source, masks)
    leg_l_tex, leg_r_tex = v7.prepare_leg_textures(source)
    contact = v7.base.build_contact_sheet(masks)
    constraints = v7.v3.build_side_back_constraints()
    parts_payload = v7.v4.build_parts_payload(stats)
    spec_path = write_spec_v8(stats, constraints, parts_payload)

    v7.v4.blender_script = lambda payload, size: v7.blender_script_v7(payload, size, leg_l_tex, leg_r_tex)
    export_report = v7.v4.run_blender_export(parts_payload, source.size)
    glb_report = v7.base.validate_glb(v7.base.EXPORT_DIR / f"{STEM}.glb")
    cage_glb_report = v7.base.validate_glb(v7.base.EXPORT_DIR / f"{STEM}_cage_debug.glb")
    fbx_report = v7.v4.validate_blender_import(v7.base.EXPORT_DIR / f"{STEM}.fbx", "fbx")
    obj_report = v7.v4.validate_blender_import(v7.base.EXPORT_DIR / f"{STEM}.obj", "obj")
    quality = v7.v4.build_quality(export_report, glb_report, cage_glb_report, fbx_report, obj_report, parts_payload)

    mesh_names = set(glb_report.get("mesh_names", []))
    cage_mesh_names = set(cage_glb_report.get("mesh_names", []))
    empty_names = set(glb_report.get("empty_names", []))
    required_main = {"leg_L_visual_panel", "leg_R_visual_panel", "boots"}
    debug_only = {
        "leg_L_retopo_proxy",
        "leg_R_retopo_proxy",
        "boot_L_hardsurface_proxy",
        "boot_R_hardsurface_proxy",
        "leg_L_thigh_strap_proxy",
        "leg_R_thigh_strap_proxy",
        "leg_L_knee_loop_proxy",
        "leg_R_knee_loop_proxy",
    }
    required_hooks = {"hook_knee_L", "hook_knee_R", "hook_ankle_L", "hook_ankle_R"}
    failures = quality.setdefault("failures", [])
    missing_main = sorted(required_main - mesh_names)
    leaked_debug = sorted(debug_only & mesh_names)
    missing_cage = sorted(debug_only - cage_mesh_names)
    missing_hooks = sorted(required_hooks - empty_names)
    if missing_main:
        quality["status"] = "failed"
        failures.append(f"missing v8 beauty leg meshes: {', '.join(missing_main)}")
    if leaked_debug:
        quality["status"] = "failed"
        failures.append(f"debug leg/boot guide meshes leaked into main GLB: {', '.join(leaked_debug)}")
    if missing_cage:
        quality["status"] = "failed"
        failures.append(f"debug leg/boot guide meshes missing from cage GLB: {', '.join(missing_cage)}")
    if missing_hooks:
        quality["status"] = "failed"
        failures.append(f"missing knee/ankle hooks: {', '.join(missing_hooks)}")
    quality.setdefault("warnings", []).append(
        "v8 removes gray leg guide blocks from beauty renders; real skinned legs still require DCC retopo"
    )
    quality["v8_required_main_meshes"] = sorted(required_main)
    quality["v8_debug_only_meshes"] = sorted(debug_only)

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": "semantic_layer_v8_beauty_main_debug_cage_split",
        "status": quality["status"],
        "boundary": "Beauty GLB contains split leg visual panels only; debug GLB contains DCC leg/boot guides.",
        "source": str(v7.base.SOURCE_FRONT.relative_to(ROOT)),
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
            "Use cage-debug leg volumes only as side/depth guides.",
            "Rebuild boots from orthographic shoe silhouettes with bevels.",
        ],
    }
    v7.base.REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_status(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
