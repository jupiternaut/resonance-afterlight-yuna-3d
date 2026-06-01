#!/usr/bin/env python3
"""Build the preview-only YUNA full-character assembly scene."""

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
ROUTE_DIR = CHARACTER_PACKAGE / "semantic_layer_v10_full_preview"
EXPORTS_DIR = ROUTE_DIR / "exports"
VALIDATION_DIR = ROUTE_DIR / "validation_ci"
MANIFEST_PATH = ROUTE_DIR / "full_preview_asset_manifest.json"
REPORT_PATH = ROUTE_DIR / "validation_report.json"
VALIDATION_CI_REPORT = VALIDATION_DIR / "validation_ci_report.json"
HANDOFF_PATH = ROUTE_DIR / "FULL_PREVIEW_HANDOFF.md"
CHATGPT_HANDOFF_PATH = CHARACTER_PACKAGE / "semantic_layer_v9_candidate" / "CHATGPT_HANDOFF.md"
WORKER_REPORT_PATH = VALIDATION_DIR / "blender_worker_report.json"
BLENDER_LOG_PATH = VALIDATION_DIR / "blender_full_preview.log"
BLEND_PATH = EXPORTS_DIR / "yuna_full_character_preview_v0.blend"
GLB_PATH = EXPORTS_DIR / "yuna_full_character_preview_v0.glb"

ROUTE = "yuna_full_character_preview_v0"
SOURCE_BRANCH = "feature/authored-hair-ribbons-v0"
BASE_COMMIT = "d933c6f"
FORMULA = "PreviewScene = AssembleUnderConstraints(v8_baseline, candidate_hair, candidate_cloth, weapon, boots, debug_cage)"

COLLECTIONS = (
    "baseline_v8",
    "candidate_hair_unaccepted",
    "candidate_cloth_unaccepted",
    "weapon",
    "body_visual",
    "debug_cage_hidden",
    "review_cameras",
    "lights",
)

SCREENSHOTS = (
    "front_baseline",
    "front_candidate_overlay",
    "yaw15",
    "yaw30",
    "side",
    "back",
    "wire",
    "exploded",
)

REVIEW_CHECKLIST = [
    "front identity readable?",
    "full silhouette coherent?",
    "candidate hair helps or hurts?",
    "cloth helps or hurts?",
    "weapon scale acceptable?",
    "boots/legs acceptable?",
    "top priority to fix?",
]


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
    return data if isinstance(data, dict) else {}


def file_record(path: Path, *, role: str, collection: str | None = None, required: bool = False, reason: str | None = None) -> dict[str, Any]:
    exists = path.exists()
    record: dict[str, Any] = {
        "role": role,
        "path": display_path(path),
        "exists": exists,
        "available": exists,
        "required": required,
        "bytes": path.stat().st_size if exists else 0,
    }
    if collection is not None:
        record["collection"] = collection
    if not exists or reason:
        record["reason"] = reason or "file_not_found_on_source_branch"
    return record


def unavailable_record(role: str, path: Path, reason: str, *, collection: str | None = None) -> dict[str, Any]:
    return file_record(path, role=role, collection=collection, required=False, reason=reason)


def git_diff_names(path: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--", path],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return [f"git_diff_failed:{result.stderr.strip()}"]
    return [line for line in result.stdout.splitlines() if line.strip()]


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


def make_review_checklist() -> list[dict[str, str]]:
    return [{"question": question, "status": "pending_manual_visual_review"} for question in REVIEW_CHECKLIST]


def build_asset_manifest() -> dict[str, Any]:
    cloth_route = CHARACTER_PACKAGE / "semantic_layer_v9_cloth"
    cloth_candidate_glb = cloth_route / "exports" / "yuna_semantic_layer_v9_cloth.glb"
    cloth_missing_reason = "semantic_layer_v9_cloth route is not present on source branch; cloth remains blocked and unaccepted"
    assets = {
        "v8_beauty_glb": file_record(
            CHARACTER_PACKAGE / "semantic_layer_v8" / "exports" / "yuna_semantic_layer_v8.glb",
            role="immutable_v8_baseline_beauty",
            collection="baseline_v8",
            required=True,
        ),
        "v8_cage_debug_glb": file_record(
            CHARACTER_PACKAGE / "semantic_layer_v8" / "exports" / "yuna_semantic_layer_v8_cage_debug.glb",
            role="debug_cage_hidden_by_default",
            collection="debug_cage_hidden",
            required=False,
        ),
        "candidate_hair_glb": file_record(
            CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "curve_bundle_candidate_v1" / "exports" / "yuna_curve_bundle_hair_v1.glb",
            role="candidate_hair_unaccepted_curve_bundle_v1",
            collection="candidate_hair_unaccepted",
            required=False,
        ),
        "candidate_hair_report": file_record(
            CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "curve_bundle_candidate_v1" / "validation_report.json",
            role="candidate_hair_unaccepted_report",
            required=False,
        ),
        "weapon_candidate_glb": file_record(
            CHARACTER_PACKAGE / "semantic_layer_v9_weapon" / "exports" / "yuna_semantic_layer_v9_weapon.glb",
            role="weapon_candidate_context",
            collection="weapon",
            required=False,
        ),
        "weapon_candidate_report": file_record(
            CHARACTER_PACKAGE / "semantic_layer_v9_weapon" / "validation_report.json",
            role="weapon_candidate_report",
            required=False,
        ),
        "boots_candidate_glb": file_record(
            CHARACTER_PACKAGE / "semantic_layer_v9_boot" / "exports" / "yuna_semantic_layer_v9_boot.glb",
            role="boots_candidate_context",
            collection="body_visual",
            required=False,
        ),
        "boots_candidate_report": file_record(
            CHARACTER_PACKAGE / "semantic_layer_v9_boot" / "validation_report.json",
            role="boots_candidate_report",
            required=False,
        ),
        "legs_candidate_glb": file_record(
            CHARACTER_PACKAGE / "semantic_layer_v9_leg" / "exports" / "yuna_semantic_layer_v9_leg.glb",
            role="legs_candidate_context",
            collection="body_visual",
            required=False,
        ),
        "legs_candidate_report": file_record(
            CHARACTER_PACKAGE / "semantic_layer_v9_leg" / "validation_report.json",
            role="legs_candidate_report",
            required=False,
        ),
        "cloth_candidate_glb": unavailable_record(
            "candidate_cloth_unaccepted_missing",
            cloth_candidate_glb,
            cloth_missing_reason,
            collection="candidate_cloth_unaccepted",
        ),
    }

    texture_dir = CHARACTER_PACKAGE / "semantic_layer_v8" / "textures"
    mask_dir = CHARACTER_PACKAGE / "semantic_layer_v8" / "masks" / "front"
    cloth_panel_names = ("cape_left", "cape_right", "jacket_outer", "skirt_front", "torso_inner")
    boots_legs_panel_names = ("boots", "legs", "leg_L_visual_panel", "leg_R_visual_panel")
    debug_image_names = (
        "yuna_semantic_layer_v8_cage_wire.png",
        "yuna_semantic_layer_v8_exploded.png",
        "yuna_semantic_layer_v8_side_cage.png",
    )

    panels = {
        "cloth_cape_skirt_jacket_panels": [
            file_record(texture_dir / f"{name}.png", role=f"v8_texture_panel_{name}", required=False)
            for name in cloth_panel_names
        ]
        + [
            file_record(mask_dir / f"{name}.png", role=f"v8_front_mask_{name}", required=False)
            for name in cloth_panel_names
        ],
        "boots_legs_visual_panels": [
            file_record(texture_dir / f"{name}.png", role=f"v8_texture_panel_{name}", required=False)
            for name in boots_legs_panel_names
        ]
        + [
            file_record(mask_dir / f"{name}.png", role=f"v8_front_mask_{name}", required=False)
            for name in ("boots", "legs")
        ],
        "debug_cage_assets": [
            assets["v8_cage_debug_glb"],
            *[
                file_record(CHARACTER_PACKAGE / "semantic_layer_v8" / "validation" / name, role=f"v8_debug_validation_{name}", required=False)
                for name in debug_image_names
            ],
        ],
    }

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": ROUTE,
        "formula": FORMULA,
        "preview_only": True,
        "replace_in_beauty_glb": False,
        "hair_accepted": False,
        "cloth_accepted": False,
        "ready_for_cloth_seam_surface": False,
        "manual_visual_review_required": True,
        "source_branch": SOURCE_BRANCH,
        "base_commit": BASE_COMMIT,
        "scene_collections": [
            {
                "name": name,
                "default_visible": name not in {"debug_cage_hidden", "candidate_cloth_unaccepted"},
                "toggleable": name in {"candidate_hair_unaccepted", "candidate_cloth_unaccepted", "weapon", "body_visual", "debug_cage_hidden"},
            }
            for name in COLLECTIONS
        ],
        "assets": assets,
        "panels": panels,
        "unavailable": [
            record
            for record in [assets["cloth_candidate_glb"], *panels["cloth_cape_skirt_jacket_panels"], *panels["boots_legs_visual_panels"], *panels["debug_cage_assets"]]
            if not record["available"]
        ],
        "constraints": {
            "semantic_layer_v8": "read_only",
            "semantic_layer_v9_hair": "read_only",
            "debug_cage": "hidden_by_default",
            "candidate_hair": "unaccepted_toggleable_context",
            "candidate_cloth": "unaccepted_unavailable_on_source_branch",
            "beauty_replacement": "forbidden",
            "production_topology_claim": "forbidden",
        },
    }
    write_json(MANIFEST_PATH, manifest)
    return manifest


def script_argv(argv: list[str] | None = None) -> list[str]:
    if argv is not None:
        return argv
    raw = sys.argv[1:]
    if "--" in raw:
        return raw[raw.index("--") + 1 :]
    return raw


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the YUNA full-character preview scene.")
    parser.add_argument("--blender", default=None)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--resolution-x", type=int, default=1400)
    parser.add_argument("--resolution-y", type=int, default=1800)
    return parser.parse_args(script_argv(argv))


def tail_lines(text: str, count: int = 80) -> list[str]:
    return [line.replace(str(REPO_ROOT), ".") for line in text.splitlines()[-count:]]


def screenshot_records() -> dict[str, dict[str, Any]]:
    records = {
        name: file_record(VALIDATION_DIR / f"{name}.png", role=f"full_preview_screenshot_{name}", required=True)
        for name in SCREENSHOTS
    }
    records["contact_sheet"] = file_record(VALIDATION_DIR / "contact_sheet.png", role="full_preview_contact_sheet", required=True)
    return records


def output_records() -> dict[str, dict[str, Any]]:
    return {
        "blend": file_record(BLEND_PATH, role="full_preview_blender_scene", required=True),
        "glb": file_record(GLB_PATH, role="full_preview_glb_export_if_possible", required=False),
    }


def create_contact_sheet() -> dict[str, Any]:
    from PIL import Image, ImageDraw

    existing = [(name, VALIDATION_DIR / f"{name}.png") for name in SCREENSHOTS if (VALIDATION_DIR / f"{name}.png").exists()]
    if not existing:
        return {"status": "skipped_with_reason", "reason": "no_screenshots_available", "path": display_path(VALIDATION_DIR / "contact_sheet.png"), "exists": False}

    thumb_w, thumb_h = 360, 460
    label_h = 34
    cols = 3
    rows = (len(existing) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), (235, 235, 232))
    draw = ImageDraw.Draw(sheet)
    for index, (name, path) in enumerate(existing):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (index % cols) * thumb_w + (thumb_w - image.width) // 2
        y = (index // cols) * (thumb_h + label_h) + label_h
        draw.text(((index % cols) * thumb_w + 10, (index // cols) * (thumb_h + label_h) + 8), name, fill=(20, 20, 20))
        sheet.paste(image, (x, y))

    path = VALIDATION_DIR / "contact_sheet.png"
    sheet.save(path)
    return file_record(path, role="full_preview_contact_sheet", required=True)


def run_blender(args: argparse.Namespace, manifest: dict[str, Any]) -> dict[str, Any]:
    blender = find_blender(args.blender)
    if blender is None:
        return {
            "status": "skipped_with_reason",
            "reason": "blender_not_found",
            "blender": None,
            "exit_code": 0,
            "log": None,
            "log_tail": [],
        }

    cmd = [
        blender,
        "--background",
        "--python",
        str(Path(__file__).resolve()),
        "--",
        "--worker",
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
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    BLENDER_LOG_PATH.write_text(result.stdout, encoding="utf-8")
    worker_report = load_json(WORKER_REPORT_PATH)
    return {
        "status": worker_report.get("status", "failed") if result.returncode == 0 else "failed",
        "reason": worker_report.get("reason"),
        "blender": blender,
        "exit_code": result.returncode,
        "log": display_path(BLENDER_LOG_PATH),
        "log_tail": tail_lines(result.stdout),
        "worker_report": worker_report,
        "manifest_route": manifest.get("route"),
    }


def write_reports(manifest: dict[str, Any], blender_result: dict[str, Any], contact_sheet: dict[str, Any]) -> dict[str, Any]:
    screenshots = screenshot_records()
    screenshots["contact_sheet"] = contact_sheet if contact_sheet.get("exists") else screenshots["contact_sheet"]
    missing_screenshots = [name for name, record in screenshots.items() if name != "contact_sheet" and (not record["exists"] or record["bytes"] <= 0)]
    v8_diff = git_diff_names("CharacterPackage/semantic_layer_v8")
    v9_hair_diff = git_diff_names("CharacterPackage/semantic_layer_v9_hair")
    if blender_result["status"] == "skipped_with_reason":
        status = "skipped_with_reason"
    elif blender_result["exit_code"] != 0:
        status = "failed"
    elif missing_screenshots:
        status = "generated_with_warnings"
    else:
        status = "preview_generated_manual_review_required"

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": ROUTE,
        "status": status,
        "formula": FORMULA,
        "preview_only": True,
        "replace_in_beauty_glb": False,
        "hair_accepted": False,
        "cloth_accepted": False,
        "ready_for_cloth_seam_surface": False,
        "v8_unchanged": v8_diff == [],
        "v9_hair_unchanged": v9_hair_diff == [],
        "manual_visual_review_required": True,
        "source_branch": SOURCE_BRANCH,
        "base_commit": BASE_COMMIT,
        "boundary": "Preview-only context scene. It does not accept hair or cloth, replace v8 beauty, unblock cloth_seam_surface, or claim final production topology.",
        "asset_manifest": file_record(MANIFEST_PATH, role="full_preview_asset_manifest", required=True),
        "outputs": output_records(),
        "screenshots": screenshots,
        "quality": {
            "missing_screenshots": missing_screenshots,
            "manual_visual_review_status": "pending",
            "visual_sanity_status": "manual_review_required",
            "known_limits": [
                "curve_bundle_candidate_v1 hair remains unaccepted until manual visual review passes",
                "cloth candidate route is unavailable on this source branch; v8 cloth panels are context only",
                "v10 preview scene is an assembly review artifact, not a beauty replacement",
            ],
        },
        "collections": manifest["scene_collections"],
        "review_checklist": make_review_checklist(),
        "unavailable_assets": manifest["unavailable"],
        "git_diff_checks": {
            "CharacterPackage/semantic_layer_v8": v8_diff,
            "CharacterPackage/semantic_layer_v9_hair": v9_hair_diff,
        },
        "blender": blender_result,
    }
    write_json(REPORT_PATH, report)
    write_json(
        VALIDATION_CI_REPORT,
        {
            "created_at": report["created_at"],
            "route": ROUTE,
            "status": status,
            "preview_only": True,
            "replace_in_beauty_glb": False,
            "hair_accepted": False,
            "cloth_accepted": False,
            "ready_for_cloth_seam_surface": False,
            "v8_unchanged": report["v8_unchanged"],
            "v9_hair_unchanged": report["v9_hair_unchanged"],
            "manual_visual_review_required": True,
            "screenshots": screenshots,
            "outputs": report["outputs"],
            "missing_screenshots": missing_screenshots,
        },
    )
    return report


def write_handoff(report: dict[str, Any]) -> None:
    generated_files = [
        "CharacterPackage/semantic_layer_v10_full_preview/full_preview_asset_manifest.json",
        "CharacterPackage/semantic_layer_v10_full_preview/exports/yuna_full_character_preview_v0.blend",
        "CharacterPackage/semantic_layer_v10_full_preview/exports/yuna_full_character_preview_v0.glb",
        "CharacterPackage/semantic_layer_v10_full_preview/validation_report.json",
        "CharacterPackage/semantic_layer_v10_full_preview/validation_ci/validation_ci_report.json",
        "CharacterPackage/semantic_layer_v10_full_preview/validation_ci/front_baseline.png",
        "CharacterPackage/semantic_layer_v10_full_preview/validation_ci/front_candidate_overlay.png",
        "CharacterPackage/semantic_layer_v10_full_preview/validation_ci/yaw15.png",
        "CharacterPackage/semantic_layer_v10_full_preview/validation_ci/yaw30.png",
        "CharacterPackage/semantic_layer_v10_full_preview/validation_ci/side.png",
        "CharacterPackage/semantic_layer_v10_full_preview/validation_ci/back.png",
        "CharacterPackage/semantic_layer_v10_full_preview/validation_ci/wire.png",
        "CharacterPackage/semantic_layer_v10_full_preview/validation_ci/exploded.png",
        "CharacterPackage/semantic_layer_v10_full_preview/validation_ci/contact_sheet.png",
        "CharacterPackage/semantic_layer_v10_full_preview/FULL_PREVIEW_HANDOFF.md",
    ]
    existing_files = [
        path
        for path in generated_files
        if (REPO_ROOT / path).exists()
    ]
    missing_screenshots = report.get("quality", {}).get("missing_screenshots", [])
    handoff = f"""# COPY_TO_CHATGPT_HANDOFF

项目：`jupiternaut/resonance-afterlight-yuna-3d`

分支：`feature/yuna-full-character-preview-v0`

源分支：`{SOURCE_BRANCH}`

基线提交：`{BASE_COMMIT}`

本轮目标：实现 `yuna_full_character_preview_v0`，创建只用于整体轮廓审查的 v10 full-character preview 场景。该场景把 v8 baseline、未接受的 curve-bundle hair candidate、weapon、boots/legs body visual、debug cage 组装到同一个 Blender 审查文件中；cloth candidate 在当前源分支不可用，只记录 v8 cape/skirt/jacket panels 作为上下文。

公式阶段：
`{FORMULA}`

本轮结论：
- route status: `{report["status"]}`
- `preview_only=true`
- `replace_in_beauty_glb=false`
- `hair_accepted=false`
- `cloth_accepted=false`
- `ready_for_cloth_seam_surface=false`
- `manual_visual_review_required=true`
- `CharacterPackage/semantic_layer_v8` 未修改：`{report["v8_unchanged"]}`
- `CharacterPackage/semantic_layer_v9_hair` 未修改：`{report["v9_hair_unchanged"]}`
- 这不是最终生产拓扑，也不是 beauty GLB 替换。

生成/更新文件：
{chr(10).join(f"- `{path}`" for path in existing_files)}

缺失/不可用：
- cloth candidate: `semantic_layer_v9_cloth` 在当前源分支不存在；cloth 仍保持 blocked/unaccepted。
- missing screenshots: `{missing_screenshots}`

审查清单：
{chr(10).join(f"- {item}" for item in REVIEW_CHECKLIST)}

验证命令：
- `python3 CharacterPackage/tools/build_yuna_full_character_preview_v0.py`
- `python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v`
- `python3 -m compileall CharacterPackage/tools`
- `git diff --name-only -- CharacterPackage/semantic_layer_v8`
- `git diff --name-only -- CharacterPackage/semantic_layer_v9_hair`

验证结果：
- build: `{report["status"]}`
- unittest: `pending_final_run`
- compileall: `pending_final_run`
- v8 diff: `{report["git_diff_checks"]["CharacterPackage/semantic_layer_v8"]}`
- v9_hair diff: `{report["git_diff_checks"]["CharacterPackage/semantic_layer_v9_hair"]}`

视觉/人工复核结论：
- 当前只生成 full-character preview 审查包；必须人工查看 screenshots/contact sheet 后再判断 hair/cloth/weapon/boots/body 哪个优先修。
- hair candidate 仍是 unaccepted。
- cloth candidate 不存在且未接受。

当前阻塞：
- `manual_visual_review_yuna_full_character_preview_v0`

推荐下一条 Codex Goal：

```text
/goal Manual-review yuna_full_character_preview_v0.

Read:
- CharacterPackage/semantic_layer_v10_full_preview/validation_report.json
- CharacterPackage/semantic_layer_v10_full_preview/full_preview_asset_manifest.json
- CharacterPackage/semantic_layer_v10_full_preview/validation_ci/contact_sheet.png
- CharacterPackage/semantic_layer_v10_full_preview/validation_ci/front_baseline.png
- CharacterPackage/semantic_layer_v10_full_preview/validation_ci/front_candidate_overlay.png
- CharacterPackage/semantic_layer_v10_full_preview/validation_ci/yaw30.png
- CharacterPackage/semantic_layer_v10_full_preview/validation_ci/side.png
- CharacterPackage/semantic_layer_v10_full_preview/validation_ci/back.png

Decide only review priority:
- front identity readable?
- full silhouette coherent?
- candidate hair helps or hurts?
- cloth helps or hurts?
- weapon scale acceptable?
- boots/legs acceptable?
- top priority to fix?

Keep semantic_layer_v8 unchanged.
Keep semantic_layer_v9_hair unchanged.
Keep replace_in_beauty_glb=false.
Keep preview_only=true.
Do not proceed to cloth_seam_surface.
Do not call this final production topology.
```
"""
    HANDOFF_PATH.parent.mkdir(parents=True, exist_ok=True)
    HANDOFF_PATH.write_text(handoff, encoding="utf-8")
    CHATGPT_HANDOFF_PATH.write_text(handoff, encoding="utf-8")


def write_skipped_outputs(manifest: dict[str, Any], reason: str) -> dict[str, Any]:
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    skipped = {
        "status": "skipped_with_reason",
        "reason": reason,
        "blender": None,
        "exit_code": 0,
        "log": None,
        "log_tail": [],
        "manifest_route": manifest.get("route"),
    }
    contact_sheet = {"status": "skipped_with_reason", "reason": reason, "path": display_path(VALIDATION_DIR / "contact_sheet.png"), "exists": False, "bytes": 0}
    report = write_reports(manifest, skipped, contact_sheet)
    write_handoff(report)
    return report


def worker_main(args: argparse.Namespace) -> int:
    import math

    import bpy
    from mathutils import Vector

    manifest = load_json(MANIFEST_PATH)
    missing_required = [
        record["path"]
        for record in manifest.get("assets", {}).values()
        if isinstance(record, dict) and record.get("required") and not record.get("exists")
    ]
    if missing_required:
        write_json(
            WORKER_REPORT_PATH,
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "route": ROUTE,
                "status": "failed",
                "reason": "missing_required_assets",
                "missing_required": missing_required,
            },
        )
        return 1

    for directory in (EXPORTS_DIR, VALIDATION_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    root_collection = bpy.context.scene.collection
    collections: dict[str, Any] = {}
    for name in COLLECTIONS:
        collection = bpy.data.collections.new(name)
        root_collection.children.link(collection)
        collection["preview_only"] = True
        collection["replace_in_beauty_glb"] = False
        collection["toggleable"] = name in {"candidate_hair_unaccepted", "candidate_cloth_unaccepted", "weapon", "body_visual", "debug_cage_hidden"}
        collections[name] = collection

    def move_to_collection(obj: Any, collection_name: str) -> None:
        target = collections[collection_name]
        for collection in list(obj.users_collection):
            collection.objects.unlink(obj)
        target.objects.link(obj)

    def set_collection_hidden(collection_name: str, hidden: bool) -> None:
        collection = collections[collection_name]
        collection.hide_viewport = hidden
        collection.hide_render = hidden
        for obj in collection.objects:
            obj.hide_viewport = hidden
            obj.hide_render = hidden

    def import_glb(record: dict[str, Any], collection_name: str, source_label: str) -> list[Any]:
        if not record.get("exists"):
            return []
        path = REPO_ROOT / record["path"]
        before = set(bpy.context.scene.objects)
        bpy.ops.import_scene.gltf(filepath=str(path))
        objects = [obj for obj in bpy.context.scene.objects if obj not in before]
        for obj in objects:
            move_to_collection(obj, collection_name)
            obj["preview_route"] = ROUTE
            obj["preview_source"] = source_label
            obj["candidate_only"] = collection_name in {"candidate_hair_unaccepted", "candidate_cloth_unaccepted", "weapon", "body_visual"}
            if obj["candidate_only"]:
                obj["accepted"] = False
            obj["replace_in_beauty_glb"] = False
            obj["preview_only"] = True
        return objects

    assets = manifest["assets"]
    baseline_objects = import_glb(assets["v8_beauty_glb"], "baseline_v8", "v8_baseline")
    debug_objects = import_glb(assets["v8_cage_debug_glb"], "debug_cage_hidden", "v8_debug_cage")
    hair_objects = import_glb(assets["candidate_hair_glb"], "candidate_hair_unaccepted", "curve_bundle_candidate_v1_unaccepted")
    weapon_objects = import_glb(assets["weapon_candidate_glb"], "weapon", "weapon_candidate_context")
    boot_objects = import_glb(assets["boots_candidate_glb"], "body_visual", "boots_candidate_context")
    leg_objects = import_glb(assets["legs_candidate_glb"], "body_visual", "legs_candidate_context")
    cloth_objects = import_glb(assets["cloth_candidate_glb"], "candidate_cloth_unaccepted", "cloth_candidate_unavailable")

    for collection_name in COLLECTIONS:
        set_collection_hidden(collection_name, collection_name in {"debug_cage_hidden", "candidate_cloth_unaccepted"})

    visible_review_objects = baseline_objects + hair_objects + weapon_objects + boot_objects + leg_objects + cloth_objects
    mesh_objects = [obj for obj in visible_review_objects if obj.type == "MESH"]
    if not mesh_objects:
        write_json(
            WORKER_REPORT_PATH,
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "route": ROUTE,
                "status": "failed",
                "reason": "no_mesh_objects_imported",
            },
        )
        return 1

    def bounds(objects: list[Any]) -> tuple[Vector, Vector]:
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

    min_corner, max_corner = bounds(mesh_objects)
    center = (min_corner + max_corner) * 0.5
    width = max(max_corner.x - min_corner.x, 0.1)
    height = max(max_corner.z - min_corner.z, 0.1)
    depth = max(max_corner.y - min_corner.y, 0.1)
    distance = max(width, height, depth) * 2.8 + 1.5
    aspect = args.resolution_x / args.resolution_y
    ortho_scale = max(height * 1.12, width / aspect * 1.12, 2.2)

    light_data = bpy.data.lights.new("full_preview_key_softbox", type="AREA")
    light_data.energy = 650
    light_data.size = max(width, height, 1.0)
    light = bpy.data.objects.new("full_preview_key_softbox", light_data)
    light.location = (center.x, center.y - distance * 0.55, center.z + height * 0.6)
    collections["lights"].objects.link(light)

    fill_data = bpy.data.lights.new("full_preview_fill_softbox", type="AREA")
    fill_data.energy = 220
    fill_data.size = max(width, height, 1.0)
    fill = bpy.data.objects.new("full_preview_fill_softbox", fill_data)
    fill.location = (center.x + width, center.y + distance * 0.35, center.z + height * 0.4)
    collections["lights"].objects.link(fill)

    def add_camera(name: str, yaw_deg: float) -> Any:
        yaw = math.radians(yaw_deg)
        loc = Vector((center.x + math.sin(yaw) * distance, center.y - math.cos(yaw) * distance, center.z))
        cam_data = bpy.data.cameras.new(name)
        cam = bpy.data.objects.new(name, cam_data)
        cam.location = loc
        direction = center - cam.location
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho_scale
        cam["preview_route"] = ROUTE
        collections["review_cameras"].objects.link(cam)
        return cam

    cameras = {
        "front": add_camera("Camera_FullPreview_Front", 0),
        "yaw15": add_camera("Camera_FullPreview_Yaw15", 15),
        "yaw30": add_camera("Camera_FullPreview_Yaw30", 30),
        "side": add_camera("Camera_FullPreview_Side", 90),
        "back": add_camera("Camera_FullPreview_Back", 180),
        "wire": add_camera("Camera_FullPreview_Wire", 30),
        "exploded": add_camera("Camera_FullPreview_Exploded", 30),
    }

    try:
        bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        bpy.context.scene.render.engine = "BLENDER_EEVEE"
    bpy.context.scene.render.resolution_x = args.resolution_x
    bpy.context.scene.render.resolution_y = args.resolution_y
    bpy.context.scene.world.color = (0.72, 0.72, 0.70)

    def set_review_visibility(mode: str) -> None:
        show_candidates = mode != "baseline"
        set_collection_hidden("baseline_v8", False)
        set_collection_hidden("candidate_hair_unaccepted", not show_candidates)
        set_collection_hidden("candidate_cloth_unaccepted", True if not cloth_objects else not show_candidates)
        set_collection_hidden("weapon", not show_candidates)
        set_collection_hidden("body_visual", not show_candidates)
        set_collection_hidden("debug_cage_hidden", True)
        set_collection_hidden("review_cameras", False)
        set_collection_hidden("lights", False)

    def render(name: str, mode: str, camera_key: str) -> Path:
        set_review_visibility(mode)
        path = VALIDATION_DIR / f"{name}.png"
        bpy.context.scene.camera = cameras[camera_key]
        bpy.context.scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        return path

    rendered: dict[str, Path] = {
        "front_baseline": render("front_baseline", "baseline", "front"),
        "front_candidate_overlay": render("front_candidate_overlay", "overlay", "front"),
        "yaw15": render("yaw15", "overlay", "yaw15"),
        "yaw30": render("yaw30", "overlay", "yaw30"),
        "side": render("side", "overlay", "side"),
        "back": render("back", "overlay", "back"),
    }

    wire_mat = bpy.data.materials.new("full_preview_wire_overlay_black")
    wire_mat.diffuse_color = (0.02, 0.02, 0.02, 1.0)
    wire_mods: list[tuple[Any, Any]] = []
    set_review_visibility("overlay")
    for obj in [item for item in visible_review_objects if item.type == "MESH"]:
        obj.data.materials.append(wire_mat)
        modifier = obj.modifiers.new("full_preview_wire_overlay", "WIREFRAME")
        modifier.thickness = 0.006
        modifier.use_replace = False
        try:
            modifier.material_offset = len(obj.data.materials) - 1
        except Exception:
            pass
        wire_mods.append((obj, modifier))
    rendered["wire"] = render("wire", "overlay", "wire")
    for obj, modifier in wire_mods:
        obj.modifiers.remove(modifier)

    candidate_groups = [
        (hair_objects, Vector((-0.28, -0.08, 0.0))),
        (weapon_objects, Vector((0.34, 0.08, 0.0))),
        (boot_objects + leg_objects, Vector((0.18, 0.0, -0.02))),
        (cloth_objects, Vector((-0.16, 0.10, 0.0))),
    ]
    original_locations = {obj.name: obj.location.copy() for group, _offset in candidate_groups for obj in group}
    for group, offset in candidate_groups:
        for obj in group:
            obj.location += offset
    rendered["exploded"] = render("exploded", "overlay", "exploded")
    for group, _offset in candidate_groups:
        for obj in group:
            obj.location = original_locations[obj.name]

    set_collection_hidden("baseline_v8", False)
    set_collection_hidden("candidate_hair_unaccepted", False)
    set_collection_hidden("candidate_cloth_unaccepted", True if not cloth_objects else False)
    set_collection_hidden("weapon", False)
    set_collection_hidden("body_visual", False)
    set_collection_hidden("debug_cage_hidden", True)
    set_collection_hidden("review_cameras", False)
    set_collection_hidden("lights", False)

    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))

    glb_export: dict[str, Any]
    try:
        for obj in bpy.context.scene.objects:
            obj.select_set(False)
        for obj in bpy.context.scene.objects:
            if obj.type in {"MESH", "EMPTY"} and not obj.hide_render and not obj.hide_get():
                obj.select_set(True)
        bpy.ops.export_scene.gltf(filepath=str(GLB_PATH), export_format="GLB", use_selection=True)
        glb_export = file_record(GLB_PATH, role="full_preview_glb_export_if_possible", required=False)
    except Exception as exc:
        glb_export = {
            "role": "full_preview_glb_export_if_possible",
            "path": display_path(GLB_PATH),
            "exists": GLB_PATH.exists(),
            "available": GLB_PATH.exists(),
            "bytes": GLB_PATH.stat().st_size if GLB_PATH.exists() else 0,
            "status": "skipped_with_reason",
            "reason": f"glb_export_failed:{exc}",
        }

    rendered_records = {
        name: file_record(path, role=f"full_preview_screenshot_{name}", required=True)
        for name, path in rendered.items()
    }
    missing = [name for name, record in rendered_records.items() if not record["exists"] or record["bytes"] <= 0]
    imported_counts = {
        "baseline_v8": len(baseline_objects),
        "candidate_hair_unaccepted": len(hair_objects),
        "candidate_cloth_unaccepted": len(cloth_objects),
        "weapon": len(weapon_objects),
        "body_visual": len(boot_objects) + len(leg_objects),
        "debug_cage_hidden": len(debug_objects),
    }
    write_json(
        WORKER_REPORT_PATH,
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "route": ROUTE,
            "status": "passed_with_warnings" if missing else "preview_scene_generated",
            "preview_only": True,
            "replace_in_beauty_glb": False,
            "hair_accepted": False,
            "cloth_accepted": False,
            "ready_for_cloth_seam_surface": False,
            "manual_visual_review_required": True,
            "collections": list(COLLECTIONS),
            "imported_counts": imported_counts,
            "screenshots": rendered_records,
            "outputs": {
                "blend": file_record(BLEND_PATH, role="full_preview_blender_scene", required=True),
                "glb": glb_export,
            },
            "missing_screenshots": missing,
            "camera": {
                "center": [round(center.x, 6), round(center.y, 6), round(center.z, 6)],
                "ortho_scale": round(ortho_scale, 6),
                "distance": round(distance, 6),
            },
        },
    )
    return 0 if not missing else 1


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.worker:
        return worker_main(args)

    manifest = build_asset_manifest()
    blender = find_blender(args.blender)
    if blender is None:
        report = write_skipped_outputs(manifest, "blender_not_found")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    blender_result = run_blender(args, manifest)
    contact_sheet = create_contact_sheet()
    report = write_reports(manifest, blender_result, contact_sheet)
    write_handoff(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] in {"preview_generated_manual_review_required", "generated_with_warnings"} else 1


if __name__ == "__main__":
    sys.exit(main())
