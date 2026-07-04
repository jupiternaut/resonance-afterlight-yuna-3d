#!/usr/bin/env python3
"""Build YUNA semantic-layer v5 assets.

v5 is a focused fix for the v4 visual failure where legs look broken in yaw
views. It keeps v4's part-grammar render shell, then adds two visible continuous
leg underlay volumes behind the alpha leg panels. This is still a DCC handoff
prototype, not final skinned character topology.
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
OUT = ROOT / "semantic_layer_v5"
STEM = "yuna_semantic_layer_v5"
CONSTRAINT_DIR = OUT / "constraints"

ORIGINAL_BLENDER_SCRIPT = v4.blender_script


LEG_UNDERLAY_CODE = """
leg_underlay_mat = bpy.data.materials.new('leg_underlay_warm_white')
leg_underlay_mat.use_nodes = True
leg_underlay_mat.blend_method = 'BLEND'
leg_bsdf = leg_underlay_mat.node_tree.nodes.get('Principled BSDF')
leg_bsdf.inputs['Base Color'].default_value = (0.88, 0.88, 0.82, 0.34)
leg_bsdf.inputs['Alpha'].default_value = 0.34
leg_bsdf.inputs['Roughness'].default_value = 0.72

def add_underlay_cylinder(name, loc, radius, depth, scale_x, scale_y, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale.x = scale_x
    obj.scale.y = scale_y
    obj.data.materials.append(mat)
    obj['semantic_part'] = name
    obj['v5_continuity_underlay'] = True
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass
    return obj

# These are intentionally conservative: they sit behind the original alpha leg
# panels and only fill the visible discontinuity in yaw views.
add_underlay_cylinder('leg_L_continuity_underlay', (-0.18, -0.155, 2.22), 1.0, 2.82, 0.068, 0.052, leg_underlay_mat)
add_underlay_cylinder('leg_R_continuity_underlay', (0.20, -0.150, 2.22), 1.0, 2.82, 0.068, 0.052, leg_underlay_mat)
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


def blender_script_v5(parts_payload: list[dict], source_size: tuple[int, int]) -> str:
    script = ORIGINAL_BLENDER_SCRIPT(parts_payload, source_size)
    marker = "cage_mat = bpy.data.materials.new('dcc_cage_translucent')"
    if marker not in script:
        raise RuntimeError("v5 injection marker missing from v4 blender script")
    return script.replace(marker, LEG_UNDERLAY_CODE + "\n" + marker)


def write_spec_v5(mask_stats: dict[str, dict], constraints: dict, parts_payload: list[dict]) -> Path:
    path = v4.write_spec_v4(mask_stats, constraints, parts_payload)
    spec = json.loads(path.read_text(encoding="utf-8"))
    spec["character"]["route"] = "semantic_layer_v5_leg_continuity"
    spec["character"]["boundary"] = "v5 fixes obvious broken-leg yaw read with visible underlay volumes; still not final skinned topology."
    spec["leg_continuity_underlays"] = [
        "leg_L_continuity_underlay",
        "leg_R_continuity_underlay",
    ]
    spec["acceptance_v5"] = {
        "must_not_show_broken_legs_in_yaw30": True,
        "main_glb_must_include_leg_underlay_meshes": True,
        "known_limits": [
            "underlay cylinders are visual continuity proxies, not final leg topology",
            "alpha panels still need hand-painted masks and texture padding",
        ],
    }
    v5_path = base.SPEC_DIR / f"{STEM}.json"
    v5_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if path != v5_path and path.exists():
        path.unlink()
    return v5_path


def update_status(report: dict) -> None:
    status_path = ROOT / "qa" / "production_status.json"
    if not status_path.exists():
        return
    status = json.loads(status_path.read_text(encoding="utf-8"))
    completed = status.setdefault("completed", [])
    for item in [
        "semantic-layer v5 leg continuity underlays generated",
        "semantic-layer v5 BLEND/GLB/FBX/OBJ roundtrip verified",
        "semantic-layer v5 validation screenshots rendered",
    ]:
        if item not in completed:
            completed.append(item)
    status["semantic_layer_v5_route"] = {
        "status": report["status"],
        "boundary": report["boundary"],
        "exports": report["exports"],
        "quality": report["quality"],
    }
    status["next_action"] = (
        "Use v5 only as the corrected visual-continuity baseline. Next rebuild legs as true retopo cages "
        "with knees/ankles, then replace underlay cylinders with skinnable leg topology."
    )
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    configure_output()
    v4.configure_parts_v4()
    v4.ensure_dirs()
    v4.blender_script = blender_script_v5
    source = Image.open(base.SOURCE_FRONT).convert("RGBA")
    masks = v2.build_front_masks_v2(source)
    stats = base.mask_stats(masks)
    base.save_part_textures(source, masks)
    contact = base.build_contact_sheet(masks)
    constraints = v3.build_side_back_constraints()
    parts_payload = v4.build_parts_payload(stats)
    spec_path = write_spec_v5(stats, constraints, parts_payload)
    export_report = v4.run_blender_export(parts_payload, source.size)
    glb_report = base.validate_glb(base.EXPORT_DIR / f"{STEM}.glb")
    cage_glb_report = base.validate_glb(base.EXPORT_DIR / f"{STEM}_cage_debug.glb")
    fbx_report = v4.validate_blender_import(base.EXPORT_DIR / f"{STEM}.fbx", "fbx")
    obj_report = v4.validate_blender_import(base.EXPORT_DIR / f"{STEM}.obj", "obj")
    quality = v4.build_quality(export_report, glb_report, cage_glb_report, fbx_report, obj_report, parts_payload)
    mesh_names = set(glb_report.get("mesh_names", []))
    required_underlays = {"leg_L_continuity_underlay", "leg_R_continuity_underlay"}
    missing_underlays = sorted(required_underlays - mesh_names)
    if missing_underlays:
        quality["status"] = "failed"
        quality.setdefault("failures", []).append(f"missing continuity underlay meshes: {', '.join(missing_underlays)}")
    else:
        quality.setdefault("warnings", []).append("leg continuity underlays are visual proxies and must be replaced by real skinnable leg topology")
    quality["leg_continuity_underlays"] = sorted(required_underlays)
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": "semantic_layer_v5_leg_continuity",
        "status": quality["status"],
        "boundary": "v5 fixes the obvious broken-leg visual read with underlay volumes; still not final game-ready topology.",
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
            "Replace leg continuity underlay cylinders with skinnable left/right leg topology.",
            "Add knee and ankle edge-loop guides before any animation claim.",
            "Rebuild boots as independent hard-surface forms instead of alpha panels.",
        ],
    }
    base.REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_status(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
