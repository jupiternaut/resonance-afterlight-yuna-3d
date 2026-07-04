#!/usr/bin/env python3
"""Build YUNA semantic-layer v3 assets.

v3 keeps the v2 front-mask ownership, then pushes the asset toward the
side/back-constrained route:

- wider part depth bands so side view is no longer a near-flat line
- softer edge colors to reduce black sidewall noise
- lower mesh sampling density for a more practical DCC handoff
- side/back alpha reference constraints recorded in the report

This is still a structured 2.5D render-shell asset, not final production
topology or a fully volumetric rigged character.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw

import build_yuna_semantic_layer_v1 as base
import build_yuna_semantic_layer_v2 as v2


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "semantic_layer_v3"
SIDE_REF = ROOT / "refs" / "ai_turnarounds" / "cutouts" / "yuna_left_side.png"
BACK_REF = ROOT / "refs" / "ai_turnarounds" / "cutouts" / "yuna_back.png"
CONSTRAINT_DIR = OUT / "constraints"
STEM = "yuna_semantic_layer_v3"


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
    base.EDGE_ALPHA = 0.08


def configure_parts_v3() -> None:
    edge = {
        "hair": (0.32, 0.62, 0.66),
        "body": (0.50, 0.52, 0.55),
        "costume": (0.28, 0.32, 0.38),
        "cloth": (0.30, 0.48, 0.55),
        "face": (0.68, 0.66, 0.62),
        "weapon": (0.18, 0.68, 0.72),
    }
    depth_overrides = {
        "back_hair": (-0.42, 0.060),
        "cape_left": (-0.27, 0.040),
        "cape_right": (-0.23, 0.040),
        "torso_inner": (0.00, 0.180),
        "legs": (0.03, 0.140),
        "side_hair_left": (0.16, 0.045),
        "side_hair_right": (0.20, 0.045),
        "jacket_outer": (0.30, 0.075),
        "boots": (0.41, 0.120),
        "skirt_front": (0.54, 0.075),
        "face": (0.68, 0.045),
        "bangs": (0.80, 0.035),
        "weapon": (0.96, 0.120),
    }
    base.PARTS = [
        replace(
            part,
            depth=depth_overrides[part.id][0],
            thickness=depth_overrides[part.id][1],
            edge_color=edge[part.category],
        )
        for part in base.PARTS
    ]


def ensure_dirs() -> None:
    base.ensure_dirs()
    CONSTRAINT_DIR.mkdir(parents=True, exist_ok=True)


def alpha_metrics(path: Path) -> dict:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    bbox = alpha.getbbox() or (0, 0, 0, 0)
    pixels = sum(1 for value in alpha.getdata() if value > 10)
    bands = []
    for top_ratio, bottom_ratio in [(0.05, 0.20), (0.20, 0.38), (0.38, 0.58), (0.58, 0.78), (0.78, 0.95)]:
        top = int(image.height * top_ratio)
        bottom = int(image.height * bottom_ratio)
        crop = alpha.crop((0, top, image.width, bottom))
        band_bbox = crop.getbbox()
        if band_bbox:
            width = band_bbox[2] - band_bbox[0]
        else:
            width = 0
        bands.append({"y": [round(top_ratio, 2), round(bottom_ratio, 2)], "alpha_width_px": width, "width_ratio": round(width / image.width, 4)})
    return {
        "path": str(path.relative_to(ROOT)),
        "size": list(image.size),
        "alpha_bbox": list(bbox),
        "alpha_pixels": pixels,
        "alpha_coverage": round(pixels / (image.width * image.height), 4),
        "vertical_bands": bands,
    }


def save_alpha_constraint(path: Path, out_name: str) -> Path:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    out = Image.new("RGBA", image.size, (0, 0, 0, 0))
    px = out.load()
    ap = alpha.load()
    for y in range(image.height):
        for x in range(image.width):
            if ap[x, y] > 10:
                px[x, y] = (95, 220, 240, 210)
    out_path = CONSTRAINT_DIR / out_name
    out.save(out_path)
    return out_path


def build_reference_contact() -> Path:
    refs = [
        ("front", base.SOURCE_FRONT),
        ("side_ai_inferred", SIDE_REF),
        ("back_ai_inferred", BACK_REF),
    ]
    thumb_w, thumb_h = 320, 480
    pad = 32
    canvas = Image.new("RGB", (thumb_w * len(refs) + pad * (len(refs) + 1), thumb_h + 72), (8, 12, 16))
    draw = ImageDraw.Draw(canvas)
    for index, (label, path) in enumerate(refs):
        image = Image.open(path).convert("RGBA")
        image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = pad + index * (thumb_w + pad) + (thumb_w - image.width) // 2
        y = pad + (thumb_h - image.height) // 2
        canvas.paste(Image.new("RGB", image.size, (26, 31, 36)), (x, y))
        canvas.paste(image, (x, y), image)
        draw.text((pad + index * (thumb_w + pad), thumb_h + 42), label, fill=(210, 235, 240))
    out_path = base.VALIDATION_DIR / "yuna_semantic_layer_v3_reference_constraints.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    return out_path


def build_side_back_constraints() -> dict:
    side_alpha = save_alpha_constraint(SIDE_REF, "side_alpha_constraint.png")
    back_alpha = save_alpha_constraint(BACK_REF, "back_alpha_constraint.png")
    contact = build_reference_contact()
    return {
        "policy": "side/back are ai_inferred modeling constraints, not locked geometry truth",
        "side": alpha_metrics(SIDE_REF),
        "back": alpha_metrics(BACK_REF),
        "saved_alpha_constraints": {
            "side": str(side_alpha.relative_to(ROOT)),
            "back": str(back_alpha.relative_to(ROOT)),
        },
        "reference_contact_sheet": str(contact.relative_to(ROOT)),
    }


def write_spec_v3(mask_stats: dict[str, dict], constraints: dict) -> Path:
    spec_path = base.write_spec(mask_stats)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spec["character"]["route"] = "semantic_layer_v3"
    spec["character"]["boundary"] = "Structured 2.5D render-shell asset with expanded depth bands and side/back constraint metadata; not final rigged volumetric topology."
    spec["mask_source"] = "semantic_layer_v2_front_masks_reused_with_v3_depth_bands"
    spec["side_back_constraints"] = constraints
    spec["acceptance_v3"] = {
        "must_have_independent_meshes": ["face", "bangs", "back_hair", "cape_left", "cape_right", "weapon", "torso_inner"],
        "target_z_to_height_ratio_min": 0.10,
        "max_overlap_warning_count": 8,
        "max_overlap_warning_value": 0.015,
        "dcc_face_budget": 120000,
        "runtime_face_budget": 80000,
        "known_limits": [
            "side/back references are AI-inferred and only constrain depth/volume plausibility",
            "front masks remain coarse and require hand-painted cleanup",
            "hair groups are still cutout surfaces, not final spline hair cards",
            "this route improves side thickness but can increase stage-layer feeling in yaw views",
        ],
    }
    v3_spec_path = base.SPEC_DIR / "yuna_semantic_layer_v3.json"
    v3_spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if spec_path != v3_spec_path and spec_path.exists():
        spec_path.unlink()
    return v3_spec_path


def build_quality_report(part_reports: dict[str, dict], mask_stats: dict[str, dict], export_report: dict, glb_report: dict) -> dict:
    failures: list[str] = []
    warnings: list[str] = []
    required_parts = ["face", "bangs", "back_hair", "cape_left", "cape_right", "weapon", "torso_inner"]
    missing = [part_id for part_id in required_parts if part_id not in glb_report.get("mesh_names", [])]
    zero_masks = [part_id for part_id, stats in mask_stats.items() if stats.get("pixels", 0) <= 0]
    if missing:
        failures.append(f"missing required mesh nodes: {', '.join(missing)}")
    if zero_masks:
        failures.append(f"zero-pixel masks: {', '.join(zero_masks)}")
    if export_report.get("blender_exit_code") != 0:
        failures.append("Blender export exited with a non-zero status")
    if glb_report.get("status") != "ok":
        failures.append("GLB roundtrip import failed")

    intervals = []
    for part in base.PARTS:
        intervals.append(
            {
                "part": part.id,
                "z_min": round(part.depth - part.thickness * 0.5, 4),
                "z_max": round(part.depth + part.thickness * 0.5, 4),
            }
        )
    z_min = min(item["z_min"] for item in intervals)
    z_max = max(item["z_max"] for item in intervals)
    z_span = round(z_max - z_min, 4)
    z_to_height_ratio = round(z_span / 6.4, 4)
    if z_to_height_ratio < 0.07:
        failures.append(f"depth span is below hard minimum: z_span/body_height={z_to_height_ratio}")
    elif z_to_height_ratio < 0.10:
        warnings.append(f"depth span is below pass target: z_span/body_height={z_to_height_ratio}")

    allowed = {
        tuple(sorted(pair))
        for pair in [
            ("torso_inner", "legs"),
            ("legs", "boots"),
            ("side_hair_left", "side_hair_right"),
            ("cape_left", "cape_right"),
        ]
    }
    overlaps = []
    unallowed = []
    ordered = sorted(intervals, key=lambda item: item["z_min"])
    for left_index, left in enumerate(ordered):
        for right in ordered[left_index + 1 :]:
            if left["z_max"] <= right["z_min"]:
                break
            item = {"a": left["part"], "b": right["part"], "overlap": round(left["z_max"] - right["z_min"], 4)}
            overlaps.append(item)
            if tuple(sorted((left["part"], right["part"]))) not in allowed:
                unallowed.append(item)
    max_unallowed_overlap = max((item["overlap"] for item in unallowed), default=0.0)
    if len(unallowed) > 8 or max_unallowed_overlap > 0.015:
        failures.append(f"depth interval overlap exceeds v3 threshold: count={len(unallowed)}, max={max_unallowed_overlap}")
    elif unallowed:
        warnings.append(f"{len(unallowed)} unallowed depth interval overlaps remain; max={max_unallowed_overlap}")

    total_faces = sum(report.get("faces", 0) for report in part_reports.values())
    if total_faces > 120000:
        failures.append(f"mesh exceeds v3 hard budget: {total_faces} faces")
    elif total_faces > 80000:
        warnings.append(f"mesh is above runtime budget: {total_faces} faces")

    warnings.extend(
        [
            "visual review still required: v3 widens side depth, but is not a true volumetric body",
            "front masks are inherited from v2 and still need hand-painted cleanup",
        ]
    )
    status = "failed" if failures else "generated_with_warnings" if warnings else "passed"
    return {
        "status": status,
        "failures": failures,
        "warnings": warnings,
        "depth": {
            "z_min": z_min,
            "z_max": z_max,
            "z_span": z_span,
            "z_to_height_ratio": z_to_height_ratio,
            "intervals": intervals,
            "overlaps": overlaps,
            "unallowed_overlaps": unallowed,
        },
        "mesh_budget": {
            "total_faces": total_faces,
            "runtime_face_budget": 80000,
            "dcc_face_budget": 120000,
            "over_runtime_budget": total_faces > 80000,
            "over_dcc_budget": total_faces > 120000,
        },
    }


def main() -> None:
    configure_output()
    configure_parts_v3()
    ensure_dirs()
    source = Image.open(base.SOURCE_FRONT).convert("RGBA")
    masks = v2.build_front_masks_v2(source)
    stats = base.mask_stats(masks)
    base.save_part_textures(source, masks)
    contact = base.build_contact_sheet(masks)
    constraints = build_side_back_constraints()
    base.build_mtl(stem=STEM)

    part_reports = {
        part.id: base.make_obj_for_part(part, masks[part.id], target_height=290, mtl_name=f"{STEM}.mtl")
        for part in base.PARTS
    }
    combined_obj = base.OBJ_DIR / f"{STEM}.obj"
    combined_report = base.combine_part_objs(combined_obj, stem=STEM)
    spec_path = write_spec_v3(stats, constraints)
    export_report = base.export_with_blender(combined_obj, stem=STEM)
    glb_report = base.validate_glb(base.EXPORT_DIR / f"{STEM}.glb")
    quality = build_quality_report(part_reports, stats, export_report, glb_report)

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": "semantic_layer_v3_side_back_constraint_compiler",
        "status": quality["status"],
        "boundary": "Structured 2.5D render-shell and DCC handoff asset; not final production topology.",
        "source": str(base.SOURCE_FRONT.relative_to(ROOT)),
        "spec": str(spec_path.relative_to(ROOT)),
        "mask_contact_sheet": str(contact.relative_to(ROOT)),
        "side_back_constraints": constraints,
        "quality": quality,
        "mask_stats": stats,
        "parts": part_reports,
        "combined_obj": combined_report,
        "exports": export_report,
        "glb_roundtrip": glb_report,
        "next_manual_cleanup": [
            "Paint final semantic masks over face/bangs and torso/cape boundaries.",
            "Replace cutout hair groups with explicit strand curves/cards.",
            "Use side/back constraints to author per-part cage meshes instead of just widened depth bands.",
            "Add a Three.js v2/v3 comparison viewer before judging the route visually.",
        ],
    }
    base.REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
