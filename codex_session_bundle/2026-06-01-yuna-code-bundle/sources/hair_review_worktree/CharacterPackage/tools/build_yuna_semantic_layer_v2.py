#!/usr/bin/env python3
"""Build YUNA semantic-layer v2 assets.

v2 keeps the v1 export chain but replaces the first draft color-threshold masks
with explicit art-directed region masks. The goal is better front readability
and cleaner part ownership before side/back constraint work.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

import build_yuna_semantic_layer_v1 as base


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "semantic_layer_v2"


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


def poly_mask(size: tuple[int, int], points: list[tuple[int, int]], blur: float = 0.0) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    if blur:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    return mask


def ellipse_mask(size: tuple[int, int], box: tuple[int, int, int, int], blur: float = 0.0) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).ellipse(box, fill=255)
    if blur:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    return mask


def rect_mask(size: tuple[int, int], box: tuple[int, int, int, int]) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rectangle(box, fill=255)
    return mask


def intersect_alpha(region: Image.Image, alpha: Image.Image) -> Image.Image:
    out = Image.new("L", region.size, 0)
    rp = region.load()
    ap = alpha.load()
    op = out.load()
    width, height = region.size
    for y in range(height):
        for x in range(width):
            if rp[x, y] > 18 and ap[x, y] > 22:
                op[x, y] = 255
    return out


def intersect_alpha_where(region: Image.Image, rgba: Image.Image, predicate) -> Image.Image:
    out = Image.new("L", region.size, 0)
    rp = region.load()
    px = rgba.load()
    op = out.load()
    width, height = region.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = px[x, y]
            if rp[x, y] > 18 and a > 22 and predicate(r, g, b, a):
                op[x, y] = 255
    return out


def is_hair_color(r: int, g: int, b: int, _a: int) -> bool:
    brightness = (r + g + b) / 3
    pale = brightness > 142 and abs(r - g) < 58 and abs(g - b) < 70
    cyan = g > 122 and b > 132 and b >= r + 6
    return pale or cyan


def is_inner_costume_color(r: int, g: int, b: int, _a: int) -> bool:
    brightness = (r + g + b) / 3
    white = brightness > 150 and abs(r - g) < 55 and abs(g - b) < 68
    skin = r > 152 and g > 110 and b > 105 and r >= b - 8 and brightness > 130
    cyan_core = g > 128 and b > 140 and b >= r + 10
    return white or skin or cyan_core


def is_jacket_color(r: int, g: int, b: int, _a: int) -> bool:
    brightness = (r + g + b) / 3
    dark_cloth = brightness < 132 and b >= r - 28
    gold_line = r > 110 and g > 90 and b < 95 and brightness > 75
    cyan_trim = g > 120 and b > 135 and r < 115
    return dark_cloth or gold_line or cyan_trim


def is_cape_color(r: int, g: int, b: int, a: int) -> bool:
    brightness = (r + g + b) / 3
    translucent = a < 230
    dark = brightness < 132 and b >= r - 30
    pale = brightness > 138 and abs(r - g) < 60 and abs(g - b) < 78
    cyan = g > 118 and b > 132 and b >= r + 5
    return translucent or dark or pale or cyan


def subtract_many(mask: Image.Image, blockers: list[Image.Image]) -> Image.Image:
    out = mask.copy().convert("L")
    op = out.load()
    blocker_pixels = [blocker.load() for blocker in blockers]
    width, height = out.size
    for y in range(height):
        for x in range(width):
            if op[x, y] and any(bp[x, y] > 0 for bp in blocker_pixels):
                op[x, y] = 0
    return out


def union_many(size: tuple[int, int], masks: list[Image.Image]) -> Image.Image:
    out = Image.new("L", size, 0)
    op = out.load()
    loaded = [mask.load() for mask in masks]
    width, height = size
    for y in range(height):
        for x in range(width):
            if any(mp[x, y] > 0 for mp in loaded):
                op[x, y] = 255
    return out


def build_front_masks_v2(source: Image.Image) -> dict[str, Image.Image]:
    rgba = source.convert("RGBA")
    size = rgba.size
    alpha = rgba.getchannel("A")

    # Hand-authored coarse regions in the locked 1024x1536 front image space.
    weapon_region = union_many(
        size,
        [
            poly_mask(size, [(0, 1505), (48, 1512), (306, 708), (278, 682), (0, 1435)]),
            poly_mask(size, [(178, 700), (316, 607), (368, 716), (232, 818)]),
            poly_mask(size, [(198, 668), (350, 650), (342, 765), (194, 790)]),
        ],
    )
    face_region = ellipse_mask(size, (415, 82, 635, 360), 1.0)
    head_hair_region = union_many(
        size,
        [
            ellipse_mask(size, (370, 40, 675, 362), 1.0),
            poly_mask(size, [(338, 200), (432, 86), (605, 80), (720, 248), (664, 430), (410, 438)]),
        ],
    )
    bangs_region = subtract_many(head_hair_region, [face_region])
    side_left_region = poly_mask(size, [(130, 195), (392, 150), (520, 396), (405, 795), (126, 830), (70, 520)])
    side_right_region = poly_mask(size, [(565, 130), (895, 225), (1015, 545), (990, 875), (642, 840), (540, 410)])
    back_hair_region = poly_mask(size, [(110, 505), (1000, 475), (1008, 1018), (118, 1035)])
    torso_region = poly_mask(size, [(318, 302), (694, 302), (738, 838), (322, 888), (254, 575)])
    skirt_region = poly_mask(size, [(340, 640), (670, 640), (694, 905), (354, 900)])
    legs_region = poly_mask(size, [(308, 812), (704, 812), (716, 1330), (318, 1330)])
    boots_region = poly_mask(size, [(330, 1195), (732, 1195), (760, 1530), (322, 1530)])
    cape_left_region = poly_mask(size, [(8, 500), (420, 470), (442, 1368), (122, 1400), (12, 980)])
    cape_right_region = poly_mask(size, [(602, 430), (1016, 485), (1018, 1388), (662, 1405), (585, 742)])
    jacket_region = poly_mask(size, [(278, 290), (748, 300), (832, 868), (618, 1025), (248, 895), (220, 535)])

    masks = {
        "weapon": intersect_alpha(weapon_region, alpha),
        "face": intersect_alpha(face_region, alpha),
        "bangs": intersect_alpha_where(bangs_region, rgba, is_hair_color),
        "side_hair_left": intersect_alpha_where(side_left_region, rgba, is_hair_color),
        "side_hair_right": intersect_alpha_where(side_right_region, rgba, is_hair_color),
        "back_hair": intersect_alpha_where(back_hair_region, rgba, is_hair_color),
        "torso_inner": intersect_alpha_where(torso_region, rgba, is_inner_costume_color),
        "jacket_outer": intersect_alpha_where(jacket_region, rgba, is_jacket_color),
        "cape_left": intersect_alpha_where(cape_left_region, rgba, is_cape_color),
        "cape_right": intersect_alpha_where(cape_right_region, rgba, is_cape_color),
        "skirt_front": intersect_alpha(skirt_region, alpha),
        "legs": intersect_alpha(legs_region, alpha),
        "boots": intersect_alpha(boots_region, alpha),
    }

    # Enforce clear front ownership for critical overlaps.
    masks["face"] = subtract_many(masks["face"], [masks["bangs"]])
    masks["torso_inner"] = subtract_many(masks["torso_inner"], [masks["skirt_front"]])
    masks["legs"] = subtract_many(masks["legs"], [masks["skirt_front"], masks["boots"]])
    masks["cape_left"] = subtract_many(masks["cape_left"], [masks["weapon"]])
    masks["back_hair"] = subtract_many(masks["back_hair"], [masks["torso_inner"], masks["jacket_outer"], masks["face"], masks["bangs"]])

    return {part.id: base.clean_mask(masks[part.id]) for part in base.PARTS}


def write_spec_v2(mask_stats: dict[str, dict]) -> Path:
    spec_path = base.write_spec(mask_stats)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spec["character"]["route"] = "semantic_layer_v2"
    spec["character"]["boundary"] = "Structured 2.5D render-shell asset with art-directed coarse masks and DCC hooks; not a final rigged volumetric character."
    spec["mask_source"] = "art_directed_front_region_masks_v2"
    spec["acceptance_v2"] = {
        "improves_over_v1": [
            "coarser but more complete face/head/body ownership",
            "weapon remains independent",
            "cape remains independent",
            "render-shell default GLB excludes proxy guide spheres",
        ],
        "known_limits": [
            "masks are still coarse polygons, not hand-painted production masks",
            "side/back masks are not yet used",
            "hair cards are still cutout surfaces, not true spline hair cards",
        ],
    }
    v2_spec_path = base.SPEC_DIR / "yuna_semantic_layer_v2.json"
    v2_spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if spec_path != v2_spec_path and spec_path.exists():
        spec_path.unlink()
    return v2_spec_path


def build_quality_report(
    mask_stats: dict[str, dict],
    part_reports: dict[str, dict],
    export_report: dict,
    glb_report: dict,
) -> dict:
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
    if z_to_height_ratio < 0.08:
        warnings.append(f"depth span is still shallow: z_span/body_height={z_to_height_ratio}")

    overlaps = []
    ordered = sorted(intervals, key=lambda item: item["z_min"])
    for left_index, left in enumerate(ordered):
        for right in ordered[left_index + 1 :]:
            if left["z_max"] <= right["z_min"]:
                break
            overlaps.append({"a": left["part"], "b": right["part"], "overlap": round(left["z_max"] - right["z_min"], 4)})
    if overlaps:
        warnings.append(f"{len(overlaps)} depth interval overlaps remain; yaw views may show black edge bands/z-order noise")

    total_faces = sum(report.get("faces", 0) for report in part_reports.values())
    if total_faces > 80000:
        warnings.append(f"mesh is too dense for runtime handoff without decimation: {total_faces} faces")

    warnings.extend(
        [
            "visual review: front likeness is improved over v1, but yaw30 still shows dark sidewall/edge artifacts",
            "visual review: side validation still reads as a shallow layered shell, not a volumetric character",
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
            "overlaps_sample": overlaps[:20],
            "overlap_count": len(overlaps),
        },
        "mesh_budget": {
            "total_faces": total_faces,
            "runtime_face_budget": 80000,
            "over_budget": total_faces > 80000,
        },
    }


def main() -> None:
    configure_output()
    base.ensure_dirs()
    source = Image.open(base.SOURCE_FRONT).convert("RGBA")
    masks = build_front_masks_v2(source)
    stats = base.mask_stats(masks)
    base.save_part_textures(source, masks)
    contact = base.build_contact_sheet(masks)
    stem = "yuna_semantic_layer_v2"
    base.build_mtl(stem=stem)

    part_reports = {part.id: base.make_obj_for_part(part, masks[part.id], mtl_name=f"{stem}.mtl") for part in base.PARTS}
    combined_obj = base.OBJ_DIR / "yuna_semantic_layer_v2.obj"
    combined_report = base.combine_part_objs(combined_obj, stem=stem)
    spec_path = write_spec_v2(stats)
    export_report = base.export_with_blender(combined_obj, stem=stem)
    glb_report = base.validate_glb(base.EXPORT_DIR / "yuna_semantic_layer_v2.glb")
    quality = build_quality_report(stats, part_reports, export_report, glb_report)

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": "semantic_layer_v2_asset_compiler",
        "status": quality["status"],
        "boundary": "Structured 2.5D render-shell and DCC handoff asset; not final production topology.",
        "source": str(base.SOURCE_FRONT.relative_to(ROOT)),
        "spec": str(spec_path.relative_to(ROOT)),
        "mask_contact_sheet": str(contact.relative_to(ROOT)),
        "quality": quality,
        "mask_stats": stats,
        "parts": part_reports,
        "combined_obj": combined_report,
        "exports": export_report,
        "glb_roundtrip": glb_report,
        "next_manual_cleanup": [
            "Paint final semantic masks over face/bangs and torso/cape boundaries.",
            "Replace cutout hair groups with explicit strand curves/cards.",
            "Add side/back masks and run per-part constraint cages.",
            "Build a real Three.js review viewer for v1/v2 side-by-side comparison.",
        ],
    }
    base.REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
