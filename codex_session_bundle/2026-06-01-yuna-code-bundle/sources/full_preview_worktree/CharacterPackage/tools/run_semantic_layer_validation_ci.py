#!/usr/bin/env python3
"""Repeatable Blender screenshot validation for semantic-layer assets.

Default target is semantic_layer_v8. This script imports the existing beauty GLB
and cage-debug GLB, renders fixed validation screenshots, and writes a CI-style
JSON report. It does not rebuild geometry or modify v8 source exports.
"""

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
DEFAULT_ROUTE_DIR = CHARACTER_PACKAGE / "semantic_layer_v8"
DEFAULT_MAIN_GLB = DEFAULT_ROUTE_DIR / "exports" / "yuna_semantic_layer_v8.glb"
DEFAULT_CAGE_GLB = DEFAULT_ROUTE_DIR / "exports" / "yuna_semantic_layer_v8_cage_debug.glb"
DEFAULT_SOURCE_REPORT = DEFAULT_ROUTE_DIR / "validation_report.json"
DEFAULT_OUTPUT_DIR = DEFAULT_ROUTE_DIR / "validation_ci"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "validation_ci_report.json"
SCREENSHOT_KEYS = ("front", "yaw15", "yaw30", "side_cage", "cage_wire", "exploded")


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def source_split_checks(source_report_path: Path) -> dict[str, Any]:
    source_report = load_json(source_report_path)
    quality = source_report.get("quality", {})
    main_names = set(source_report.get("glb_roundtrip", {}).get("mesh_names", []))
    cage_names = set(source_report.get("cage_glb_roundtrip", {}).get("mesh_names", []))
    required_main = set(quality.get("v8_required_main_meshes", [])) or {
        "leg_L_visual_panel",
        "leg_R_visual_panel",
        "boots",
    }
    debug_only = set(quality.get("v8_debug_only_meshes", [])) or {
        "leg_L_retopo_proxy",
        "leg_R_retopo_proxy",
        "boot_L_hardsurface_proxy",
        "boot_R_hardsurface_proxy",
        "leg_L_thigh_strap_proxy",
        "leg_R_thigh_strap_proxy",
        "leg_L_knee_loop_proxy",
        "leg_R_knee_loop_proxy",
    }
    missing_main = sorted(required_main - main_names)
    leaked_debug = sorted(debug_only & main_names)
    missing_cage = sorted(debug_only - cage_names)
    return {
        "source_report": display_path(source_report_path),
        "source_status": source_report.get("status"),
        "required_main_meshes": sorted(required_main),
        "debug_only_meshes": sorted(debug_only),
        "missing_main_meshes": missing_main,
        "debug_guides_leaked_to_beauty": leaked_debug,
        "debug_guides_missing_from_cage": missing_cage,
        "passed": not missing_main and not leaked_debug and not missing_cage,
    }


def tail_lines(text: str, count: int = 80) -> list[str]:
    return text.splitlines()[-count:]


def script_argv(argv: list[str] | None = None) -> list[str] | None:
    if argv is not None:
        return argv
    raw = sys.argv[1:]
    if "--" in raw:
        return raw[raw.index("--") + 1 :]
    return raw


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Blender validation screenshots for a semantic-layer GLB route.")
    parser.add_argument("--main-glb", type=Path, default=DEFAULT_MAIN_GLB)
    parser.add_argument("--cage-glb", type=Path, default=DEFAULT_CAGE_GLB)
    parser.add_argument("--source-report", type=Path, default=DEFAULT_SOURCE_REPORT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--blender", default=None)
    parser.add_argument("--resolution-x", type=int, default=1200)
    parser.add_argument("--resolution-y", type=int, default=1600)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args(script_argv(argv))


def run_wrapper(args: argparse.Namespace) -> int:
    blender = find_blender(args.blender)
    if blender is None:
        write_json(
            args.report,
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "route": "semantic_layer_validation_ci_v0",
                "status": "failed",
                "error": "blender_not_found",
            },
        )
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        blender,
        "--background",
        "--python",
        str(Path(__file__).resolve()),
        "--",
        "--worker",
        "--main-glb",
        str(args.main_glb),
        "--cage-glb",
        str(args.cage_glb),
        "--source-report",
        str(args.source_report),
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
    log_path = args.output_dir / "blender_validation_ci.log"
    log_path.write_text(result.stdout, encoding="utf-8")

    report = load_json(args.report) if args.report.exists() else {}
    if not report:
        report = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "route": "semantic_layer_validation_ci_v0",
            "status": "failed",
            "error": "worker_did_not_write_report",
        }
    report["wrapper"] = {
        "blender": blender,
        "exit_code": result.returncode,
        "log": display_path(log_path),
        "log_tail": tail_lines(result.stdout),
    }
    if result.returncode != 0:
        report["status"] = "failed"
    write_json(args.report, report)
    return result.returncode


def worker_main(args: argparse.Namespace) -> int:
    import math

    import bpy
    from mathutils import Vector

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for path in (args.main_glb, args.cage_glb):
        if not path.exists():
            write_json(
                args.report,
                {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "route": "semantic_layer_validation_ci_v0",
                    "status": "failed",
                    "error": f"missing_input:{path}",
                },
            )
            return 1

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    bpy.ops.import_scene.gltf(filepath=str(args.main_glb))
    beauty_objects = [obj for obj in bpy.context.scene.objects]
    for obj in beauty_objects:
        obj["ci_source"] = "beauty"

    before_cage = {obj.name for obj in bpy.context.scene.objects}
    bpy.ops.import_scene.gltf(filepath=str(args.cage_glb))
    cage_objects = [obj for obj in bpy.context.scene.objects if obj.name not in before_cage]
    for obj in cage_objects:
        obj["ci_source"] = "cage"

    beauty_meshes = [obj for obj in beauty_objects if obj.type == "MESH"]
    cage_meshes = [obj for obj in cage_objects if obj.type == "MESH"]
    all_meshes = beauty_meshes + cage_meshes

    def set_render_group(beauty_visible: bool, cage_visible: bool) -> None:
        for obj in beauty_objects:
            obj.hide_viewport = not beauty_visible
            obj.hide_render = not beauty_visible
        for obj in cage_objects:
            obj.hide_viewport = not cage_visible
            obj.hide_render = not cage_visible

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

    min_corner, max_corner = bounds(beauty_meshes or all_meshes)
    center = (min_corner + max_corner) * 0.5
    width = max(max_corner.x - min_corner.x, 0.1)
    height = max(max_corner.z - min_corner.z, 0.1)
    depth = max(max_corner.y - min_corner.y, 0.1)
    distance = max(width, height, depth) * 2.2 + 4.0
    aspect = args.resolution_x / args.resolution_y
    ortho_scale = max(height * 1.08, width / aspect * 1.08)

    bpy.ops.object.light_add(type="AREA", location=(center.x, center.y - distance * 0.5, center.z + height * 0.7))
    light = bpy.context.object
    light.name = "validation_ci_softbox"
    light.data.energy = 650
    light.data.size = max(width, height) * 0.8

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
        "front": add_camera("Camera_CI_Front_Ortho", 0),
        "yaw15": add_camera("Camera_CI_Yaw_15", 15),
        "yaw30": add_camera("Camera_CI_Yaw_30", 30),
        "side_cage": add_camera("Camera_CI_Side_90", 90),
        "cage_wire": add_camera("Camera_CI_Cage_Wire", 30),
        "exploded": add_camera("Camera_CI_Exploded", 30),
    }

    try:
        bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        bpy.context.scene.render.engine = "BLENDER_EEVEE"
    try:
        bpy.context.scene.eevee.taa_render_samples = 64
    except Exception:
        pass
    bpy.context.scene.render.resolution_x = args.resolution_x
    bpy.context.scene.render.resolution_y = args.resolution_y
    bpy.context.scene.view_settings.view_transform = "Filmic"
    bpy.context.scene.view_settings.look = "Medium High Contrast"
    bpy.context.scene.world.color = (0.03, 0.03, 0.03)

    def render(key: str, beauty_visible: bool, cage_visible: bool) -> Path:
        set_render_group(beauty_visible, cage_visible)
        filepath = args.output_dir / f"yuna_semantic_layer_v8_ci_{key}.png"
        bpy.context.scene.camera = cameras[key]
        bpy.context.scene.render.filepath = str(filepath)
        bpy.ops.render.render(write_still=True)
        return filepath

    screenshot_paths = {
        "front": render("front", True, False),
        "yaw15": render("yaw15", True, False),
        "yaw30": render("yaw30", True, False),
        "side_cage": render("side_cage", True, True),
        "cage_wire": render("cage_wire", False, True),
    }

    original_locations = {obj.name: obj.location.copy() for obj in beauty_meshes}
    for index, obj in enumerate(beauty_meshes):
        obj.location.x += (index - len(beauty_meshes) / 2) * 0.14
        obj.location.y += ((index % 5) - 2) * 0.10
    screenshot_paths["exploded"] = render("exploded", True, False)
    for obj in beauty_meshes:
        obj.location = original_locations[obj.name]

    split_checks = source_split_checks(args.source_report)
    screenshot_records = {key: file_record(path) for key, path in screenshot_paths.items()}
    missing_screenshots = [key for key, value in screenshot_records.items() if not value["exists"] or value["bytes"] <= 0]
    passed = not missing_screenshots and split_checks["passed"]
    source_report = load_json(args.source_report)
    inherited_warnings = source_report.get("quality", {}).get("warnings", [])

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": "semantic_layer_validation_ci_v0",
        "input_route": source_report.get("route"),
        "status": "passed_with_warnings" if passed else "failed",
        "boundary": "Screenshot validation only. This does not generate mesh or certify production topology.",
        "inputs": {
            "main_glb": file_record(args.main_glb),
            "cage_glb": file_record(args.cage_glb),
            "source_report": file_record(args.source_report),
        },
        "screenshots": screenshot_records,
        "inventory": {
            "beauty_mesh_count": len(beauty_meshes),
            "cage_mesh_count": len(cage_meshes),
            "beauty_mesh_names": [obj.name for obj in beauty_meshes],
            "cage_mesh_names": [obj.name for obj in cage_meshes],
        },
        "split_checks": split_checks,
        "quality": {
            "missing_screenshots": missing_screenshots,
            "inherited_warnings": inherited_warnings,
            "next_required_step": "Run v9 actuator only after candidate output passes these screenshot gates.",
        },
    }
    write_json(args.report, report)
    return 0 if passed else 1


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.worker:
        return worker_main(args)
    return run_wrapper(args)


if __name__ == "__main__":
    sys.exit(main())
