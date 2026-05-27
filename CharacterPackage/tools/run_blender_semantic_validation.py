#!/usr/bin/env python3
"""Generic Blender validation for semantic actuator candidates."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CHARACTER_PACKAGE = Path(__file__).resolve().parents[1]
REPO_ROOT = CHARACTER_PACKAGE.parent
DEFAULT_BASELINE_GLB = CHARACTER_PACKAGE / "semantic_layer_v8" / "exports" / "yuna_semantic_layer_v8.glb"
DEFAULT_CAGE_GLB = CHARACTER_PACKAGE / "semantic_layer_v8" / "exports" / "yuna_semantic_layer_v8_cage_debug.glb"
DEFAULT_CANDIDATE_GLB = CHARACTER_PACKAGE / "semantic_layer_v9_weapon" / "exports" / "yuna_semantic_layer_v9_weapon.glb"
DEFAULT_OUTPUT_DIR = CHARACTER_PACKAGE / "semantic_layer_v9_weapon" / "validation_ci"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "validation_ci_report.json"
VISUAL_SANITY_THRESHOLDS = {
    "black_alpha_leak_ratio": 0.02,
    "candidate_black_pixel_ratio": 0.05,
    "face_occlusion_ratio": 0.15,
    "non_hair_occlusion_ratio": 0.10,
    "outside_hair_mask_ratio": 0.10,
    "hair_mask_iou": 0.12,
}
HAIR_PART_IDS = ("back_hair", "side_hair_left", "side_hair_right", "bangs")
FULL_SOURCE_HEIGHT = 2.2


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": display_path(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
    }


def find_blender(explicit: str | None = None) -> str | None:
    if explicit:
        return explicit
    blender = shutil.which("blender")
    if blender:
        return blender
    app_path = Path("/Applications/Blender.app/Contents/MacOS/Blender")
    if app_path.exists():
        return str(app_path)
    return None


def script_argv(argv: list[str] | None = None) -> list[str] | None:
    if argv is not None:
        return argv
    raw = sys.argv[1:]
    if "--" in raw:
        return raw[raw.index("--") + 1 :]
    return raw


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a semantic candidate GLB in Blender.")
    parser.add_argument("--baseline-glb", type=Path, default=DEFAULT_BASELINE_GLB)
    parser.add_argument("--cage-glb", type=Path, default=DEFAULT_CAGE_GLB)
    parser.add_argument("--candidate-glb", type=Path, default=DEFAULT_CANDIDATE_GLB)
    parser.add_argument("--candidate-report", type=Path, default=CHARACTER_PACKAGE / "semantic_layer_v9_weapon" / "validation_report.json")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--blender", default=None)
    parser.add_argument("--resolution-x", type=int, default=1200)
    parser.add_argument("--resolution-y", type=int, default=1600)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args(script_argv(argv))


def tail_lines(text: str, count: int = 80) -> list[str]:
    return text.splitlines()[-count:]


def evaluate_black_pixel_sanity(image_path: Path) -> dict[str, float]:
    from PIL import Image

    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    pixels = image.load()
    corner_samples = [
        pixels[0, 0],
        pixels[width - 1, 0],
        pixels[0, height - 1],
        pixels[width - 1, height - 1],
    ]
    background = tuple(sum(sample[index] for sample in corner_samples) / len(corner_samples) for index in range(3))
    dark_pixels = 0
    foreground_pixels = 0
    dark_foreground_pixels = 0
    for y in range(height):
        for x in range(width):
            rgb = pixels[x, y]
            is_dark = max(rgb) < 64
            is_foreground = sum(abs(rgb[index] - background[index]) for index in range(3)) > 28
            if is_dark:
                dark_pixels += 1
            if is_foreground:
                foreground_pixels += 1
                if is_dark:
                    dark_foreground_pixels += 1
    total = max(width * height, 1)
    foreground_denominator = max(foreground_pixels, round(total * 0.05), 1)
    return {
        "candidate_black_pixel_ratio": round(dark_foreground_pixels / total, 6),
        "black_alpha_leak_ratio": round(dark_foreground_pixels / foreground_denominator, 6),
    }


def foreground_mask_from_render(image_path: Path) -> tuple[list[list[bool]], int, int, int]:
    from PIL import Image

    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    pixels = image.load()
    corner_samples = [
        pixels[0, 0],
        pixels[width - 1, 0],
        pixels[0, height - 1],
        pixels[width - 1, height - 1],
    ]
    background = tuple(sum(sample[index] for sample in corner_samples) / len(corner_samples) for index in range(3))
    mask: list[list[bool]] = []
    count = 0
    for y in range(height):
        row: list[bool] = []
        for x in range(width):
            rgb = pixels[x, y]
            visible = sum(abs(rgb[index] - background[index]) for index in range(3)) > 28
            row.append(visible)
            if visible:
                count += 1
        mask.append(row)
    return mask, width, height, count


def foreground_bbox(mask: list[list[bool]], width: int, height: int) -> tuple[int, int, int, int] | None:
    xs: list[int] = []
    ys: list[int] = []
    for y in range(height):
        for x in range(width):
            if mask[y][x]:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def evaluate_render_framing(image_path: Path) -> dict[str, Any]:
    mask, width, height, count = foreground_mask_from_render(image_path)
    bbox = foreground_bbox(mask, width, height)
    if bbox is None:
        return {
            "framing_valid": False,
            "foreground_ratio": 0.0,
            "bbox": None,
            "bbox_height_ratio": 0.0,
            "bbox_width_ratio": 0.0,
            "reason": "render has no visible foreground",
        }
    x0, y0, x1, y1 = bbox
    bbox_height_ratio = (y1 - y0) / max(height, 1)
    bbox_width_ratio = (x1 - x0) / max(width, 1)
    foreground_ratio = count / max(width * height, 1)
    top_band_visible = y0 < height * 0.30
    bottom_band_visible = y1 > height * 0.70
    framing_valid = bbox_height_ratio >= 0.55 and bbox_width_ratio >= 0.20 and foreground_ratio >= 0.02 and top_band_visible and bottom_band_visible
    reasons: list[str] = []
    if bbox_height_ratio < 0.55:
        reasons.append("foreground height is too small for full-frame baseline validation")
    if bbox_width_ratio < 0.20:
        reasons.append("foreground width is too small for full-frame baseline validation")
    if foreground_ratio < 0.02:
        reasons.append("foreground coverage is too small")
    if not top_band_visible:
        reasons.append("top of character is not visible")
    if not bottom_band_visible:
        reasons.append("bottom of character is not visible")
    return {
        "framing_valid": framing_valid,
        "foreground_ratio": round(foreground_ratio, 6),
        "bbox": [x0, y0, x1, y1],
        "bbox_height_ratio": round(bbox_height_ratio, 6),
        "bbox_width_ratio": round(bbox_width_ratio, 6),
        "reason": "; ".join(reasons) if reasons else "foreground spans a valid full-frame character range",
    }


def load_hair_union_mask(render_width: int, render_height: int) -> list[list[bool]]:
    from PIL import Image, ImageChops, ImageFilter

    mask_dir = CHARACTER_PACKAGE / "semantic_layer_v8" / "masks" / "front"
    result: Image.Image | None = None
    for part_id in HAIR_PART_IDS:
        source = Image.open(mask_dir / f"{part_id}.png").convert("RGBA")
        alpha = source.getchannel("A")
        if alpha.getbbox() == (0, 0, source.width, source.height) and alpha.getextrema() == (255, 255):
            current = source.convert("L").point(lambda value: 255 if value > 16 else 0)
        else:
            current = alpha.point(lambda value: 255 if value > 16 else 0)
        result = current if result is None else ImageChops.lighter(result, current)
    if result is None:
        raise ValueError("No hair masks available for validation")
    result = result.filter(ImageFilter.MaxFilter(5))
    source_width, source_height = result.size
    target_height = render_height
    target_width = round(source_width / source_height * target_height)
    if target_width > render_width:
        target_width = render_width
        target_height = round(source_height / source_width * target_width)
    resized = result.resize((target_width, target_height), Image.Resampling.NEAREST)
    canvas = Image.new("L", (render_width, render_height), 0)
    canvas.paste(resized, ((render_width - target_width) // 2, (render_height - target_height) // 2))
    return [[canvas.getpixel((x, y)) > 0 for x in range(render_width)] for y in range(render_height)]


def evaluate_hair_mask_alignment(candidate_front: Path) -> dict[str, Any]:
    candidate_mask, width, height, candidate_pixels = foreground_mask_from_render(candidate_front)
    hair_mask = load_hair_union_mask(width, height)
    intersection = 0
    union = 0
    outside = 0
    hair_pixels = 0
    for y in range(height):
        for x in range(width):
            candidate = candidate_mask[y][x]
            hair = hair_mask[y][x]
            if hair:
                hair_pixels += 1
            if candidate and hair:
                intersection += 1
            if candidate or hair:
                union += 1
            if candidate and not hair:
                outside += 1
    hair_mask_iou = intersection / max(union, 1)
    outside_hair_mask_ratio = outside / max(candidate_pixels, 1)
    candidate_is_hair_only = (
        candidate_pixels > 0
        and outside_hair_mask_ratio < VISUAL_SANITY_THRESHOLDS["outside_hair_mask_ratio"]
        and hair_mask_iou >= VISUAL_SANITY_THRESHOLDS["hair_mask_iou"]
    )
    return {
        "hair_mask_iou": round(hair_mask_iou, 6),
        "outside_hair_mask_ratio": round(outside_hair_mask_ratio, 6),
        "candidate_visible_pixel_count": candidate_pixels,
        "expected_hair_pixel_count": hair_pixels,
        "candidate_is_hair_only": candidate_is_hair_only,
    }


def hair_visual_sanity_from_reports(
    report: dict[str, Any],
    candidate_report: dict[str, Any],
    candidate_front: Path,
    baseline_front: Path | None = None,
    overlay_front: Path | None = None,
) -> dict[str, Any]:
    validation = candidate_report.get("validation", {})
    baseline_framing = evaluate_render_framing(baseline_front) if baseline_front and baseline_front.exists() else {"framing_valid": False, "reason": "baseline_front missing"}
    overlay_framing = evaluate_render_framing(overlay_front) if overlay_front and overlay_front.exists() else {"framing_valid": False, "reason": "overlay_front missing"}
    hair_alignment = evaluate_hair_mask_alignment(candidate_front)
    metrics = {
        "alpha_material_valid": bool(validation.get("alpha_material_valid")),
        "face_occlusion_ratio": float(validation.get("face_occlusion_ratio", 1.0)),
        "non_hair_occlusion_ratio": float(validation.get("non_hair_occlusion_ratio", 1.0)),
        "hair_mask_iou": hair_alignment["hair_mask_iou"],
        "outside_hair_mask_ratio": hair_alignment["outside_hair_mask_ratio"],
        "candidate_is_hair_only": hair_alignment["candidate_is_hair_only"],
        "candidate_visible_pixel_count": hair_alignment["candidate_visible_pixel_count"],
        "expected_hair_pixel_count": hair_alignment["expected_hair_pixel_count"],
        "baseline_framing_valid": bool(baseline_framing["framing_valid"]),
        "baseline_framing_reason": baseline_framing["reason"],
        "baseline_framing": baseline_framing,
        "overlay_alignment_valid": bool(overlay_framing["framing_valid"]) and bool(hair_alignment["candidate_is_hair_only"]),
        "overlay_alignment_reason": overlay_framing["reason"],
        "overlay_framing": overlay_framing,
        **evaluate_black_pixel_sanity(candidate_front),
    }
    reasons: list[str] = []
    status = "passed"
    if not metrics["alpha_material_valid"]:
        reasons.append("alpha material validation is missing or false")
    if metrics["black_alpha_leak_ratio"] >= VISUAL_SANITY_THRESHOLDS["black_alpha_leak_ratio"]:
        reasons.append("candidate front render has black alpha/background leakage")
    if metrics["candidate_black_pixel_ratio"] >= VISUAL_SANITY_THRESHOLDS["candidate_black_pixel_ratio"]:
        reasons.append("candidate front render has too many black pixels")
    if metrics["face_occlusion_ratio"] >= VISUAL_SANITY_THRESHOLDS["face_occlusion_ratio"]:
        reasons.append("candidate source coverage occludes too much face area")
    if metrics["non_hair_occlusion_ratio"] >= VISUAL_SANITY_THRESHOLDS["non_hair_occlusion_ratio"]:
        reasons.append("candidate source coverage exceeds non-hair threshold")
    if not metrics["baseline_framing_valid"]:
        reasons.append("baseline front render is not a valid full-frame baseline")
        status = "failed_validation_framing"
    elif not metrics["candidate_is_hair_only"]:
        reasons.append("candidate front render is not constrained to the v8 hair mask union")
        status = "failed_hair_mask_alignment"
    elif not metrics["overlay_alignment_valid"]:
        reasons.append("overlay front render is not valid for alignment review")
        status = "failed_hair_mask_alignment"
    elif reasons:
        status = "failed_visual_sanity"
    return {
        **metrics,
        "visual_sanity_status": status,
        "visual_sanity_reason": "; ".join(reasons) if reasons else "candidate front render, mask alignment, and source coverage pass hair visual sanity thresholds",
        "manual_visual_review": "failed" if status != "passed" else "pending",
        "ready_for_cloth_seam_surface": False,
        "artifact_generated": True,
        "black_alpha_leak_fixed": metrics["black_alpha_leak_ratio"] < VISUAL_SANITY_THRESHOLDS["black_alpha_leak_ratio"],
        "numeric_metrics_passed": not any(
            [
                metrics["black_alpha_leak_ratio"] >= VISUAL_SANITY_THRESHOLDS["black_alpha_leak_ratio"],
                metrics["candidate_black_pixel_ratio"] >= VISUAL_SANITY_THRESHOLDS["candidate_black_pixel_ratio"],
                metrics["face_occlusion_ratio"] >= VISUAL_SANITY_THRESHOLDS["face_occlusion_ratio"],
                metrics["non_hair_occlusion_ratio"] >= VISUAL_SANITY_THRESHOLDS["non_hair_occlusion_ratio"],
            ]
        ),
        "thresholds": VISUAL_SANITY_THRESHOLDS,
        "negative_fixture": "CharacterPackage/semantic_layer_v9_hair/negative_fixtures/yuna_semantic_layer_v9_hair_validation_front_failed_visual_fixture.png",
    }


def run_wrapper(args: argparse.Namespace) -> int:
    blender = find_blender(args.blender)
    if blender is None:
        write_json(
            args.report,
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "route": "blender_semantic_validation_v0",
                "status": "skipped_with_reason",
                "reason": "blender_not_found",
                "inputs": {
                    "baseline_glb": file_record(args.baseline_glb),
                    "cage_glb": file_record(args.cage_glb),
                    "candidate_glb": file_record(args.candidate_glb),
                },
            },
        )
        return 0

    args.output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        blender,
        "--background",
        "--python",
        str(Path(__file__).resolve()),
        "--",
        "--worker",
        "--baseline-glb",
        str(args.baseline_glb),
        "--cage-glb",
        str(args.cage_glb),
        "--candidate-glb",
        str(args.candidate_glb),
        "--candidate-report",
        str(args.candidate_report),
        "--output-dir",
        str(args.output_dir),
        "--report",
        str(args.report),
        "--resolution-x",
        str(args.resolution_x),
        "--resolution-y",
        str(args.resolution_y),
    ]
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    log_path = args.output_dir / "blender_semantic_validation.log"
    log_path.write_text(result.stdout, encoding="utf-8")
    report = load_json(args.report) if args.report.exists() else {}
    if not report:
        report = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "route": "blender_semantic_validation_v0",
            "status": "failed",
            "error": "worker_did_not_write_report",
        }
    report["wrapper"] = {
        "blender": blender,
        "exit_code": result.returncode,
        "log": display_path(log_path),
        "log_tail": tail_lines(result.stdout),
    }
    candidate_report = load_json(args.candidate_report)
    if candidate_report.get("part_id") == "hair" and report.get("screenshots", {}).get("candidate_front", {}).get("exists"):
        candidate_front = args.output_dir / f"{args.candidate_glb.stem}_validation_candidate_front.png"
        baseline_front = args.output_dir / f"{args.candidate_glb.stem}_validation_baseline_front.png"
        overlay_front = args.output_dir / f"{args.candidate_glb.stem}_validation_overlay_front.png"
        visual_sanity = hair_visual_sanity_from_reports(report, candidate_report, candidate_front, baseline_front, overlay_front)
        report.setdefault("quality", {})["visual_sanity"] = visual_sanity
        report.setdefault("candidate_contract", {})["visual_sanity_status"] = visual_sanity["visual_sanity_status"]
        if visual_sanity["visual_sanity_status"] != "passed":
            report["status"] = visual_sanity["visual_sanity_status"]
        candidate_report.setdefault("validation", {}).update(visual_sanity)
        if visual_sanity["visual_sanity_status"] != "passed":
            candidate_report["status"] = visual_sanity["visual_sanity_status"]
        write_json(args.candidate_report, candidate_report)
    if result.returncode != 0:
        report["status"] = "failed"
    write_json(args.report, report)
    if report.get("status") in {"failed_visual_sanity", "failed_hair_mask_alignment", "failed_validation_framing"}:
        return 1
    return result.returncode


def worker_main(args: argparse.Namespace) -> int:
    import math

    import bpy
    from mathutils import Vector

    missing = [path for path in (args.baseline_glb, args.cage_glb, args.candidate_glb) if not path.exists()]
    if missing:
        write_json(
            args.report,
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "route": "blender_semantic_validation_v0",
                "status": "failed",
                "error": "missing_input",
                "missing": [display_path(path) for path in missing],
            },
        )
        return 1

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    bpy.ops.import_scene.gltf(filepath=str(args.baseline_glb))
    baseline_objects = [obj for obj in bpy.context.scene.objects]
    for obj in baseline_objects:
        obj["validation_source"] = "baseline_v8"
    baseline_meshes = [obj for obj in baseline_objects if obj.type == "MESH"]

    before = {obj.name for obj in bpy.context.scene.objects}
    bpy.ops.import_scene.gltf(filepath=str(args.cage_glb))
    cage_objects = [obj for obj in bpy.context.scene.objects if obj.name not in before]
    for obj in cage_objects:
        obj["validation_source"] = "cage_v8"

    before = {obj.name for obj in bpy.context.scene.objects}
    bpy.ops.import_scene.gltf(filepath=str(args.candidate_glb))
    candidate_objects = [obj for obj in bpy.context.scene.objects if obj.name not in before]
    for obj in candidate_objects:
        obj["validation_source"] = "candidate"

    candidate_meshes = [obj for obj in candidate_objects if obj.type == "MESH"]
    candidate_empties = [obj for obj in candidate_objects if obj.type == "EMPTY"]
    candidate_report = load_json(args.candidate_report)
    candidate_part = candidate_report.get("part_id", "unknown")

    def set_group_visibility(group: str) -> None:
        for obj in baseline_objects:
            visible = group in {"baseline", "overlay"}
            obj.hide_viewport = not visible
            obj.hide_render = not visible
        for obj in cage_objects:
            visible = group == "cage"
            obj.hide_viewport = not visible
            obj.hide_render = not visible
        for obj in candidate_objects:
            visible = group in {"candidate", "candidate_wire", "candidate_exploded", "overlay"}
            obj.hide_viewport = not visible
            obj.hide_render = not visible

    def bounds(objects: list) -> tuple[Vector, Vector]:
        min_corner = Vector((999999.0, 999999.0, 999999.0))
        max_corner = Vector((-999999.0, -999999.0, -999999.0))
        for obj in objects:
            if obj.type != "MESH":
                continue
            for corner in obj.bound_box:
                world = obj.matrix_world @ Vector(corner)
                min_corner.x = min(min_corner.x, world.x)
                min_corner.y = min(min_corner.y, world.y)
                min_corner.z = min(min_corner.z, world.z)
                max_corner.x = max(max_corner.x, world.x)
                max_corner.y = max(max_corner.y, world.y)
                max_corner.z = max(max_corner.z, world.z)
        return min_corner, max_corner

    if candidate_part == "hair":
        # Hair candidate review must use the full v8 baseline frame. A
        # candidate-bounds camera can make baseline/overlay screenshots look
        # valid while only showing boots or another local body region.
        min_corner, max_corner = bounds(baseline_meshes)
        center = (min_corner + max_corner) * 0.5
        width = max(max_corner.x - min_corner.x, 0.1)
        height = max(max_corner.z - min_corner.z, 0.1)
        depth = max(max_corner.y - min_corner.y, 0.1)
        distance = max(width, height, depth) * 2.8 + 1.5
        aspect = args.resolution_x / args.resolution_y
        ortho_scale = max(height * 1.10, width / aspect * 1.10, FULL_SOURCE_HEIGHT)
    else:
        min_corner, max_corner = bounds(candidate_meshes)
        center = (min_corner + max_corner) * 0.5
        width = max(max_corner.x - min_corner.x, 0.1)
        height = max(max_corner.z - min_corner.z, 0.1)
        depth = max(max_corner.y - min_corner.y, 0.1)
        distance = max(width, height, depth) * 2.8 + 1.5
        aspect = args.resolution_x / args.resolution_y
        ortho_scale = max(height * 1.20, width / aspect * 1.20, 0.6)

    bpy.ops.object.light_add(type="AREA", location=(center.x, center.y - distance * 0.6, center.z + height))
    light = bpy.context.object
    light.name = "semantic_validation_softbox"
    light.data.energy = 450
    light.data.size = max(width, height, 1.0)

    def add_camera(name: str, yaw_deg: float):
        yaw = math.radians(yaw_deg)
        loc = Vector((center.x + math.sin(yaw) * distance, center.y - math.cos(yaw) * distance, center.z))
        bpy.ops.object.camera_add(location=loc)
        cam = bpy.context.object
        cam.name = name
        direction = center - cam.location
        cam.rotation_euler = direction.to_track_quat("-Z", "Z").to_euler()
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho_scale
        return cam

    cameras = {
        "front": add_camera("Camera_Candidate_Front", 0),
        "yaw15": add_camera("Camera_Candidate_Yaw15", 15),
        "yaw30": add_camera("Camera_Candidate_Yaw30", 30),
        "side": add_camera("Camera_Candidate_Side", 90),
        "wire": add_camera("Camera_Candidate_Wire", 30),
        "exploded": add_camera("Camera_Candidate_Exploded", 30),
    }

    try:
        bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        bpy.context.scene.render.engine = "BLENDER_EEVEE"
    bpy.context.scene.render.resolution_x = args.resolution_x
    bpy.context.scene.render.resolution_y = args.resolution_y
    bpy.context.scene.world.color = (0.72, 0.72, 0.72)

    screenshot_prefix = args.candidate_glb.stem

    def render(key: str, group: str, camera_key: str | None = None) -> Path:
        set_group_visibility(group)
        path = args.output_dir / f"{screenshot_prefix}_validation_{key}.png"
        bpy.context.scene.camera = cameras[camera_key or key]
        bpy.context.scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        return path

    screenshot_paths = {
        "front": render("front", "candidate"),
        "candidate_front": render("candidate_front", "candidate", "front"),
        "baseline_front": render("baseline_front", "baseline", "front"),
        "overlay_front": render("overlay_front", "overlay", "front"),
        "yaw15": render("yaw15", "candidate"),
        "yaw30": render("yaw30", "candidate"),
        "side": render("side", "candidate"),
    }

    for obj in candidate_meshes:
        obj.display_type = "WIRE"
    screenshot_paths["wire"] = render("wire", "candidate_wire")
    for obj in candidate_meshes:
        obj.display_type = "TEXTURED"

    original_locations = {obj.name: obj.location.copy() for obj in candidate_meshes}
    for index, obj in enumerate(candidate_meshes):
        obj.location.x += (index - len(candidate_meshes) / 2) * 0.20
        obj.location.y += ((index % 3) - 1) * 0.12
    screenshot_paths["exploded"] = render("exploded", "candidate_exploded")
    for obj in candidate_meshes:
        obj.location = original_locations[obj.name]

    screenshot_records = {
        key: file_record(path)
        for key, path in screenshot_paths.items()
    }
    missing_screenshots = [key for key, value in screenshot_records.items() if not value["exists"] or value["bytes"] <= 0]
    has_weapon_socket = any(obj.name.startswith("hand_R_socket") for obj in candidate_empties)
    has_foot_socket = any(obj.name.startswith("foot_L_socket") for obj in candidate_empties) and any(
        obj.name.startswith("foot_R_socket") for obj in candidate_empties
    )
    has_leg_loop_markers = all(
        any(obj.name.startswith(name) for obj in candidate_empties)
        for name in ("leg_L_knee_loop", "leg_L_ankle_loop", "leg_R_knee_loop", "leg_R_ankle_loop")
    )
    has_hair_spring_hooks = all(
        any(obj.name.startswith(name) for obj in candidate_empties)
        for name in ("hair_back_spring_hook", "hair_bangs_spring_hook", "hair_side_left_spring_hook", "hair_side_right_spring_hook")
    )
    has_hair_depth_groups = bool(candidate_report.get("validation", {}).get("has_depth_groups"))
    candidate_names = [obj.name for obj in candidate_meshes]
    if candidate_part == "weapon":
        contract_passed = any("weapon_hardsurface_ortho_v0" in name for name in candidate_names) and has_weapon_socket
    elif candidate_part == "boots":
        contract_passed = bool(candidate_meshes) and has_foot_socket
    elif candidate_part == "legs":
        contract_passed = bool(candidate_meshes) and has_leg_loop_markers
    elif candidate_part == "hair":
        contract_passed = bool(candidate_meshes) and has_hair_spring_hooks and has_hair_depth_groups
    else:
        contract_passed = bool(candidate_meshes)
    status = "passed_with_warnings" if not missing_screenshots and contract_passed else "failed"

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": "blender_semantic_validation_v0",
        "status": status,
        "boundary": "Candidate validation only. It does not replace v8 beauty GLB.",
        "inputs": {
            "baseline_glb": file_record(args.baseline_glb),
            "cage_glb": file_record(args.cage_glb),
            "candidate_glb": file_record(args.candidate_glb),
            "candidate_report": file_record(args.candidate_report),
        },
        "screenshots": screenshot_records,
        "inventory": {
            "baseline_object_count": len(baseline_objects),
            "cage_object_count": len(cage_objects),
            "candidate_mesh_count": len(candidate_meshes),
            "candidate_empty_count": len(candidate_empties),
            "candidate_mesh_names": candidate_names,
            "candidate_empty_names": [obj.name for obj in candidate_empties],
        },
        "candidate_contract": {
            "part_id": candidate_part,
            "has_independent_candidate_mesh": bool(candidate_meshes),
            "has_independent_weapon_mesh": any("weapon_hardsurface_ortho_v0" in name for name in candidate_names),
            "has_boot_candidate_meshes": bool(candidate_meshes) if candidate_part == "boots" else None,
            "has_leg_candidate_meshes": bool(candidate_meshes) if candidate_part == "legs" else None,
            "has_hair_candidate_meshes": bool(candidate_meshes) if candidate_part == "hair" else None,
            "has_hand_R_socket": has_weapon_socket,
            "has_foot_sockets": has_foot_socket,
            "has_leg_loop_markers": has_leg_loop_markers,
            "has_hair_spring_hooks": has_hair_spring_hooks,
            "has_hair_depth_groups": has_hair_depth_groups,
            "replace_in_beauty_glb": candidate_report.get("validation", {}).get("replace_in_beauty_glb"),
        },
        "quality": {
            "missing_screenshots": missing_screenshots,
            "known_limits": [
                f"{candidate_part} candidate is an actuator proxy, not final DCC asset",
                "v8 beauty GLB remains the active baseline until replacement validation is accepted",
            ],
        },
    }
    write_json(args.report, report)
    return 0 if status != "failed" else 1


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.worker:
        return worker_main(args)
    return run_wrapper(args)


if __name__ == "__main__":
    sys.exit(main())
