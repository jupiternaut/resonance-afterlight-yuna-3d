from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from PIL import Image


SCRIPT_NAME = "external_hair_intake_probe_v0"
DATASET_ID = "external_hair_dataset_pilot_v0"
PROBE_STATUS = "probe_generated"
BLOCKED_STATUS = "blocked_waiting_for_open_template_source"
ALLOWED_RECOMMENDATIONS = {
    "open_template_source",
    "reference_report_only",
    "local_study_only",
    "pending",
    "do_not_use",
}
OPEN_LICENSE_CONFIDENCE = {"high", "medium-high"}
SELECTED_SOURCE_IDS = ("opengameart_ponytail_female", "opengameart_long_male")
SOURCE_FILE_URLS = {
    "opengameart_ponytail_female": "https://opengameart.org/sites/default/files/female_hair_ponytail2.blend",
    "opengameart_long_male": "https://opengameart.org/sites/default/files/long_flat_hair.blend",
}


@dataclass(frozen=True)
class ProbePaths:
    repo_root: Path
    dataset_dir: Path
    manifest_path: Path
    triage_path: Path
    pilot_report_path: Path
    probes_dir: Path
    summary_report_path: Path


def repo_root_from_file() -> Path:
    return Path(__file__).resolve().parents[2]


def default_paths(repo_root: Path) -> ProbePaths:
    dataset_dir = repo_root / "CharacterPackage" / "external_hair_dataset"
    probes_dir = dataset_dir / "probes"
    return ProbePaths(
        repo_root=repo_root,
        dataset_dir=dataset_dir,
        manifest_path=dataset_dir / "assets_manifest.json",
        triage_path=dataset_dir / "SOURCE_TRIAGE.md",
        pilot_report_path=dataset_dir / "external_hair_dataset_pilot_v0_report.json",
        probes_dir=probes_dir,
        summary_report_path=probes_dir / "external_hair_intake_probe_v0_report.json",
    )


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def validate_manifest_source_policy(source: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    recommendation = source.get("recommendation")
    license_confidence = source.get("license_confidence")
    if recommendation not in ALLOWED_RECOMMENDATIONS:
        errors.append(f"{source.get('source_id', '<unknown>')}: invalid recommendation {recommendation!r}")
    if recommendation == "do_not_use":
        errors.append(f"{source.get('source_id', '<unknown>')}: do_not_use source cannot be selected")
    if recommendation == "open_template_source" and license_confidence not in OPEN_LICENSE_CONFIDENCE:
        errors.append(
            f"{source.get('source_id', '<unknown>')}: open_template_source requires high or medium-high license confidence"
        )
    if source.get("external_asset_usage") != "prior_only":
        errors.append(f"{source.get('source_id', '<unknown>')}: external_asset_usage must be prior_only")
    if source.get("replace_in_beauty_glb") is not False:
        errors.append(f"{source.get('source_id', '<unknown>')}: replace_in_beauty_glb must be false")
    return errors


def select_sources(manifest: dict[str, Any], limit: int = 2) -> list[dict[str, Any]]:
    sources_by_id = {source["source_id"]: source for source in manifest.get("sources", [])}
    selected: list[dict[str, Any]] = []
    for source_id in SELECTED_SOURCE_IDS:
        source = sources_by_id.get(source_id)
        if not source:
            continue
        if validate_manifest_source_policy(source):
            continue
        if source.get("recommendation") == "open_template_source":
            selected.append(source)
        if len(selected) >= limit:
            return selected

    if len(selected) < limit:
        for source in manifest.get("sources", []):
            if source.get("source_id") in {item["source_id"] for item in selected}:
                continue
            if validate_manifest_source_policy(source):
                continue
            if source.get("recommendation") == "open_template_source":
                selected.append(source)
            if len(selected) >= limit:
                break

    if len(selected) < limit:
        for source in manifest.get("sources", []):
            if source.get("source_id") in {item["source_id"] for item in selected}:
                continue
            if source.get("recommendation") == "reference_report_only":
                selected.append(source)
            if len(selected) >= limit:
                break

    return selected[:limit]


def fetch_url_bytes(url: str, max_bytes: int = 5_000_000) -> tuple[bytes, dict[str, Any]]:
    request = Request(url, headers={"User-Agent": "YUNA-external-hair-intake-probe/0.1"})
    with urlopen(request, timeout=60) as response:
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > max_bytes:
            raise ValueError(f"remote file too large for probe: {content_length} bytes")
        data = response.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError(f"download exceeded max_bytes={max_bytes}")
        return data, {
            "content_length": int(content_length) if content_length else len(data),
            "content_type": response.headers.get("Content-Type"),
            "final_url": response.geturl(),
        }


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def find_blender() -> str | None:
    return shutil.which("blender")


def blender_probe_script() -> str:
    return r'''
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
out_dir = Path(args[0])
out_dir.mkdir(parents=True, exist_ok=True)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE"
scene.render.resolution_x = 768
scene.render.resolution_y = 768
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.image_settings.color_depth = "8"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "Medium High Contrast"
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1

objects = [obj for obj in scene.objects if obj.type in {"MESH", "CURVE", "SURFACE", "FONT", "META"}]
mesh_objects = [obj for obj in objects if obj.type == "MESH"]
curve_objects = [obj for obj in objects if obj.type == "CURVE"]
particle_system_count = sum(len(obj.particle_systems) for obj in scene.objects)

if not objects:
    raise RuntimeError("no renderable mesh/curve objects found")

depsgraph = bpy.context.evaluated_depsgraph_get()
corners = []
for obj in objects:
    eval_obj = obj.evaluated_get(depsgraph)
    for corner in eval_obj.bound_box:
        corners.append(eval_obj.matrix_world @ Vector(corner))
if not corners:
    raise RuntimeError("no bounding box corners found")

min_corner = Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
max_corner = Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
center = (min_corner + max_corner) * 0.5
span = max(max_corner.x - min_corner.x, max_corner.y - min_corner.y, max_corner.z - min_corner.z, 0.1)

for obj in objects:
    obj.select_set(True)
bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")

light_data = bpy.data.lights.new("probe_area_light", type="AREA")
light_data.energy = 450
light_data.size = span * 2.5
light = bpy.data.objects.new("probe_area_light", light_data)
bpy.context.collection.objects.link(light)
light.location = center + Vector((0, -span * 2.2, span * 2.0))

camera_data = bpy.data.cameras.new("probe_camera")
camera_data.type = "ORTHO"
camera_data.ortho_scale = span * 1.25
camera = bpy.data.objects.new("probe_camera", camera_data)
bpy.context.collection.objects.link(camera)
scene.camera = camera

def look_at(obj, target):
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

def set_camera(angle_deg):
    angle = math.radians(angle_deg)
    radius = span * 2.4
    camera.location = center + Vector((math.sin(angle) * radius, -math.cos(angle) * radius, span * 0.08))
    look_at(camera, center)

def render_png(name):
    scene.render.filepath = str(out_dir / name)
    bpy.ops.render.render(write_still=True)

set_camera(0)
render_png("front.png")
set_camera(30)
render_png("yaw30.png")
set_camera(90)
render_png("side.png")

wire_mat = bpy.data.materials.new("probe_wire_black")
wire_mat.diffuse_color = (0.02, 0.02, 0.02, 1.0)
for obj in mesh_objects:
    obj.data.materials.clear()
    obj.data.materials.append(wire_mat)
    modifier = obj.modifiers.new("probe_wireframe", "WIREFRAME")
    modifier.thickness = span * 0.003
    modifier.use_even_offset = True
set_camera(0)
render_png("wire.png")

mesh_vertices = 0
mesh_faces = 0
for obj in mesh_objects:
    mesh_vertices += len(obj.data.vertices)
    mesh_faces += len(obj.data.polygons)

has_alpha_material = False
for mat in bpy.data.materials:
    if mat.blend_method not in {"OPAQUE", ""}:
        has_alpha_material = True
    if mat.use_nodes:
        for node in mat.node_tree.nodes:
            if getattr(node, "type", "") == "TEX_IMAGE" and getattr(node, "image", None):
                if node.image.depth in {32, 64, 128}:
                    has_alpha_material = True

if particle_system_count:
    representation = "particle_hair"
elif curve_objects:
    representation = "curve_hair"
elif has_alpha_material:
    representation = "hair_cards"
elif mesh_objects and mesh_faces <= 1200:
    representation = "ribbon_surfaces"
else:
    representation = "solid_sculpt_hair"

summary = {
    "object_count": len(objects),
    "mesh_object_count": len(mesh_objects),
    "curve_object_count": len(curve_objects),
    "particle_system_count": particle_system_count,
    "mesh_vertices": mesh_vertices,
    "mesh_faces": mesh_faces,
    "has_alpha_material": has_alpha_material,
    "classification": representation,
    "classification_confidence": "medium" if mesh_objects or curve_objects else "low",
    "bounds": {
        "min": [min_corner.x, min_corner.y, min_corner.z],
        "max": [max_corner.x, max_corner.y, max_corner.z],
        "span": span,
    },
}
(out_dir / "blender_probe_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
'''


def run_blender_probe(blend_path: Path, probe_dir: Path) -> dict[str, Any]:
    blender = find_blender()
    if not blender:
        return {
            "status": "skipped",
            "skipped_with_reason": "blender_unavailable",
            "outputs": {},
        }

    with tempfile.TemporaryDirectory() as tmp:
        script_path = Path(tmp) / "probe_render.py"
        script_path.write_text(blender_probe_script(), encoding="utf-8")
        command = [
            blender,
            "--background",
            "--disable-autoexec",
            str(blend_path),
            "--python",
            str(script_path),
            "--",
            str(probe_dir),
        ]
        completed = subprocess.run(command, cwd=probe_dir, text=True, capture_output=True, timeout=180)
        if completed.returncode != 0:
            return {
                "status": "skipped",
                "skipped_with_reason": "blender_probe_failed",
                "returncode": completed.returncode,
                "stderr_tail": completed.stderr[-2000:],
                "stdout_tail": completed.stdout[-2000:],
                "outputs": {},
            }

    outputs = {name: name for name in ("front.png", "yaw30.png", "side.png", "wire.png")}
    alpha_path = probe_dir / "alpha.png"
    if (probe_dir / "front.png").exists():
        create_alpha_preview(probe_dir / "front.png", alpha_path)
        outputs["alpha.png"] = "alpha.png"
    summary_path = probe_dir / "blender_probe_summary.json"
    summary = read_json(summary_path) if summary_path.exists() else {}
    return {
        "status": "rendered",
        "skipped_with_reason": None,
        "outputs": outputs,
        "blender_summary": summary,
    }


def create_alpha_preview(front_path: Path, alpha_path: Path) -> None:
    image = Image.open(front_path).convert("RGBA")
    alpha = image.getchannel("A")
    alpha.save(alpha_path)


def make_selection_record(source: dict[str, Any]) -> dict[str, Any]:
    source_id = source["source_id"]
    return {
        "source_id": source_id,
        "source_name": source["source_name"],
        "source_url": source["source_url"],
        "why_selected": (
            "Selected from manifest/SOURCE_TRIAGE because it is a high-confidence open_template_source, "
            "small enough for a minimal probe, and useful for YUNA hair priors."
        ),
        "intended_usage_role": source["possible_usage_role"],
        "binary_download_allowed": source["can_commit_binary_to_repo"] in {
            "yes_after_license_snapshot",
            "yes_selected_cc0_files_after_review",
            "partial_selected_small_files_only",
        },
        "binary_download_policy": source["can_commit_binary_to_repo"],
        "renders_can_be_committed": source["can_commit_renders"] in {"yes", "yes_selected_cc0_files"},
        "renders_policy": source["can_commit_renders"],
        "curve_template_extraction_allowed": source["can_extract_curve_templates"] not in {"no_texture_only", "pending"},
        "curve_template_policy": source["can_extract_curve_templates"],
        "recommendation": source["recommendation"],
        "license_confidence": source["license_confidence"],
        "source_file_url": SOURCE_FILE_URLS.get(source_id),
    }


def write_license_snapshot(probe_dir: Path, source: dict[str, Any], selection: dict[str, Any]) -> None:
    text = "\n".join(
        [
            f"source_id: {source['source_id']}",
            f"source_name: {source['source_name']}",
            f"source_url: {source['source_url']}",
            f"source_file_url: {selection.get('source_file_url')}",
            f"claimed_license: {source['claimed_license']}",
            f"license_confidence: {source['license_confidence']}",
            f"recommendation: {source['recommendation']}",
            "snapshot_note: This text snapshot records manifest/source-triage evidence only; it is not legal advice.",
            "",
        ]
    )
    (probe_dir / "source_license_snapshot.txt").write_text(text, encoding="utf-8")


def build_prior_report(
    source: dict[str, Any],
    selection: dict[str, Any],
    download: dict[str, Any],
    blender_result: dict[str, Any],
) -> dict[str, Any]:
    blender_summary = blender_result.get("blender_summary") or {}
    classification = blender_summary.get("classification", "classification_deferred")
    outputs = {
        "front": "front.png" if (blender_result.get("outputs") or {}).get("front.png") else None,
        "yaw30": "yaw30.png" if (blender_result.get("outputs") or {}).get("yaw30.png") else None,
        "side": "side.png" if (blender_result.get("outputs") or {}).get("side.png") else None,
        "wire": "wire.png" if (blender_result.get("outputs") or {}).get("wire.png") else None,
        "alpha": "alpha.png" if (blender_result.get("outputs") or {}).get("alpha.png") else None,
    }
    return {
        "report_version": "hair_reference_prior_report_v0.1",
        "generated_at": now_iso(),
        "source_id": source["source_id"],
        "source_name": source["source_name"],
        "source_url": source["source_url"],
        "source_file_url": selection.get("source_file_url"),
        "status": "probe_generated" if blender_result.get("status") == "rendered" else "probe_skipped_with_reason",
        "selection": selection,
        "download": download,
        "representation_classification": classification,
        "classification_confidence": blender_summary.get("classification_confidence", "low"),
        "probe_outputs": outputs,
        "prior_only": true_false(True),
        "replace_in_beauty_glb": False,
        "ready_for_yuna_replacement": False,
        "ready_for_cloth_seam_surface": False,
        "third_party_binary_committed": False,
        "source_binary_committed": False,
        "derived_prior_candidates": {
            "scalp_anchors": "candidate_from_bounds_and_centerlines_only_after_manual_review",
            "primary_curves": "candidate_from_rendered silhouette and mesh centerlines, not copied geometry",
            "width_profiles": "candidate_from normalized mesh/card span statistics",
            "taper_profiles": "pending_curve_or_mesh_analysis",
            "depth_groups": "candidate_from yaw30/side visual layers",
            "negative_examples": "use if source fails hair readability or import quality",
        },
        "blender_probe": blender_result,
        "limitations": [
            "This report is a reference-prior probe only.",
            "No source geometry or texture is imported into YUNA.",
            "No candidate is accepted without manual visual review.",
        ],
    }


def true_false(value: bool) -> bool:
    return value


def probe_source(source: dict[str, Any], paths: ProbePaths) -> dict[str, Any]:
    selection = make_selection_record(source)
    probe_dir = paths.probes_dir / source["source_id"]
    probe_dir.mkdir(parents=True, exist_ok=True)
    write_license_snapshot(probe_dir, source, selection)

    source_file_url = selection.get("source_file_url")
    if not source_file_url or not selection["binary_download_allowed"]:
        report = {
            "report_version": "hair_reference_prior_report_v0.1",
            "generated_at": now_iso(),
            "source_id": source["source_id"],
            "status": "blocked_waiting_for_open_template_source",
            "selection": selection,
            "blocked_reason": "no safe source_file_url or binary download not allowed by manifest policy",
            "prior_only": True,
            "replace_in_beauty_glb": False,
            "ready_for_cloth_seam_surface": False,
        }
        write_json(probe_dir / "hair_reference_prior_report.json", report)
        return report

    try:
        data, response_meta = fetch_url_bytes(source_file_url)
    except (ValueError, URLError, TimeoutError) as exc:
        report = {
            "report_version": "hair_reference_prior_report_v0.1",
            "generated_at": now_iso(),
            "source_id": source["source_id"],
            "status": "probe_skipped_with_reason",
            "selection": selection,
            "skipped_with_reason": f"download_failed: {exc}",
            "prior_only": True,
            "replace_in_beauty_glb": False,
            "ready_for_cloth_seam_surface": False,
        }
        write_json(probe_dir / "hair_reference_prior_report.json", report)
        return report

    download_meta = {
        "status": "downloaded_to_temporary_file_only",
        "source_binary_committed": False,
        "url": source_file_url,
        "sha256": sha256_bytes(data),
        "size_bytes": len(data),
        "response": response_meta,
    }
    with tempfile.TemporaryDirectory(prefix=f"{source['source_id']}_") as tmp:
        blend_path = Path(tmp) / Path(source_file_url).name
        blend_path.write_bytes(data)
        blender_result = run_blender_probe(blend_path, probe_dir)

    report = build_prior_report(source, selection, download_meta, blender_result)
    write_json(probe_dir / "hair_reference_prior_report.json", report)
    return report


def run_probe(paths: ProbePaths, limit: int = 2) -> dict[str, Any]:
    manifest = read_json(paths.manifest_path)
    selected = select_sources(manifest, limit=limit)
    paths.probes_dir.mkdir(parents=True, exist_ok=True)
    (paths.probes_dir / ".gitignore").write_text(
        "\n".join(
            [
                "# Do not commit raw third-party source payloads from intake probes.",
                "*.blend",
                "*.fbx",
                "*.glb",
                "*.gltf",
                "*.obj",
                "*.zip",
                "*.rar",
                "*.7z",
                "__source_downloads__/",
                "",
            ]
        ),
        encoding="utf-8",
    )

    source_reports: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for source in selected:
        report = probe_source(source, paths)
        source_reports.append(report)
        if report.get("status") != PROBE_STATUS:
            blocked.append({"source_id": source["source_id"], "status": report.get("status"), "reason": report.get("skipped_with_reason") or report.get("blocked_reason")})

    status = PROBE_STATUS if any(report.get("status") == PROBE_STATUS for report in source_reports) else BLOCKED_STATUS
    summary = {
        "report_version": "external_hair_intake_probe_v0_report_v0.1",
        "generated_at": now_iso(),
        "status": status,
        "dataset_id": DATASET_ID,
        "selected_source_ids": [source["source_id"] for source in selected],
        "selection_count": len(selected),
        "successful_probe_count": sum(1 for report in source_reports if report.get("status") == PROBE_STATUS),
        "blocked_count": len(blocked),
        "source_reports": [
            {
                "source_id": report.get("source_id"),
                "status": report.get("status"),
                "representation_classification": report.get("representation_classification"),
                "report_path": f"CharacterPackage/external_hair_dataset/probes/{report.get('source_id')}/hair_reference_prior_report.json",
            }
            for report in source_reports
        ],
        "blocked_sources": blocked,
        "guards": {
            "v8_immutable": True,
            "replace_in_beauty_glb": False,
            "external_asset_usage": "prior_only",
            "third_party_binary_committed": False,
            "generated_yuna_hair": False,
            "ready_for_cloth_seam_surface": False,
        },
    }
    write_json(paths.summary_report_path, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run external hair intake probe v0.")
    parser.add_argument("--repo-root", type=Path, default=repo_root_from_file())
    parser.add_argument("--limit", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = default_paths(args.repo_root.resolve())
    summary = run_probe(paths, limit=args.limit)
    print(json.dumps({"status": summary["status"], "selected_source_ids": summary["selected_source_ids"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
