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
    if result.returncode != 0:
        report["status"] = "failed"
    write_json(args.report, report)
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

    def set_group_visibility(group: str) -> None:
        for obj in baseline_objects:
            visible = group == "baseline"
            obj.hide_viewport = not visible
            obj.hide_render = not visible
        for obj in cage_objects:
            visible = group == "cage"
            obj.hide_viewport = not visible
            obj.hide_render = not visible
        for obj in candidate_objects:
            visible = group in {"candidate", "candidate_wire", "candidate_exploded"}
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
    bpy.context.scene.world.color = (0.03, 0.03, 0.03)

    def render(key: str, group: str) -> Path:
        set_group_visibility(group)
        path = args.output_dir / f"yuna_semantic_layer_v9_weapon_validation_{key}.png"
        bpy.context.scene.camera = cameras[key]
        bpy.context.scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        return path

    screenshot_paths = {
        "front": render("front", "candidate"),
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
    has_socket = any(obj.name.startswith("hand_R_socket") for obj in candidate_empties)
    candidate_names = [obj.name for obj in candidate_meshes]
    status = "passed_with_warnings" if not missing_screenshots and candidate_meshes and has_socket else "failed"

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
            "has_independent_weapon_mesh": any("weapon_hardsurface_ortho_v0" in name for name in candidate_names),
            "has_hand_R_socket": has_socket,
            "replace_in_beauty_glb": candidate_report.get("validation", {}).get("replace_in_beauty_glb"),
        },
        "quality": {
            "missing_screenshots": missing_screenshots,
            "known_limits": [
                "weapon candidate is an actuator proxy, not final DCC hard-surface art",
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
