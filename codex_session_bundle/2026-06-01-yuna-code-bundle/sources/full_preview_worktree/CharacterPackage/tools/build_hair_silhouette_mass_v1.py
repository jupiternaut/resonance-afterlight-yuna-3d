#!/usr/bin/env python3
"""Build the silhouette-mass-first v1 hair candidate."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from build_hair_target_schema_v1 import build_report as build_target_schema_report
from semantic_actuators.hair_silhouette_mass_v1 import (
    ROUTE,
    STATUS_FAILED_READABILITY,
    STATUS_MANUAL_REVIEW,
    run_hair_silhouette_mass_v1,
)
from semantic_actuators.state import ActuatorPaths


CHARACTER_PACKAGE = Path(__file__).resolve().parents[1]
REPO_ROOT = CHARACTER_PACKAGE.parent
OUT = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "silhouette_mass_v1"
STEM = "yuna_semantic_layer_v9_hair_silhouette_mass_v1"
VALIDATION_DIR = OUT / "validation_ci"
VALIDATION_CI_REPORT = VALIDATION_DIR / "validation_ci_report.json"
TARGET_SCHEMA_EVAL_DIR = OUT / "target_schema_v1_eval"
CONTACT_SHEET = OUT / "silhouette_mass_v1_contact_sheet.png"
HANDOFF = CHARACTER_PACKAGE / "semantic_layer_v9_candidate" / "CHATGPT_HANDOFF.md"
PROJECT_STATE = CHARACTER_PACKAGE / "semantic_layer_v9_candidate" / "PROJECT_STATE.md"
BACKLOG = CHARACTER_PACKAGE / "semantic_layer_v9_candidate" / "backlog_v10.md"

REQUIRED_THRESHOLDS = {
    "primary_mass_coverage_ratio": 0.35,
    "candidate_visible_area_ratio": 0.014,
    "soft_silhouette_coverage_ratio": 0.55,
    "back_hair_mass_presence_ratio": 0.25,
    "side_hair_left_presence_ratio": 0.20,
    "side_hair_right_presence_ratio": 0.20,
    "bangs_presence_ratio": 0.15,
    "forbidden_candidate_leak_ratio": 0.10,
}


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


def run_step(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        args,
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {
        "args": [str(item) for item in args],
        "exit_code": result.returncode,
        "log_tail": result.stdout.splitlines()[-80:],
    }


def route_paths() -> ActuatorPaths:
    return ActuatorPaths(
        repo_root=REPO_ROOT,
        character_package=CHARACTER_PACKAGE,
        output_dir=OUT,
        spec_path=OUT / "specs" / f"{STEM}.json",
        obj_path=OUT / "exports" / f"{STEM}.obj",
        glb_path=OUT / "exports" / f"{STEM}.glb",
        report_path=OUT / "validation_report.json",
    )


def screenshot_records(paths: ActuatorPaths) -> dict[str, dict[str, Any]]:
    mapping = {
        "candidate_front": VALIDATION_DIR / f"{paths.glb_path.stem}_validation_candidate_front.png",
        "overlay_front": VALIDATION_DIR / f"{paths.glb_path.stem}_validation_overlay_front.png",
        "yaw15": VALIDATION_DIR / f"{paths.glb_path.stem}_validation_yaw15.png",
        "yaw30": VALIDATION_DIR / f"{paths.glb_path.stem}_validation_yaw30.png",
        "side": VALIDATION_DIR / f"{paths.glb_path.stem}_validation_side.png",
        "wire": VALIDATION_DIR / f"{paths.glb_path.stem}_validation_wire.png",
        "exploded": VALIDATION_DIR / f"{paths.glb_path.stem}_validation_exploded.png",
    }
    return {name: file_record(path) for name, path in mapping.items()}


def evaluate_required_gates(actuator_report: dict[str, Any], schema_report: dict[str, Any] | None) -> dict[str, Any]:
    mesh_summary = actuator_report.get("mesh_summary", {})
    design_summary = mesh_summary.get("design_summary", {})
    primary_mass_coverage = float(design_summary.get("primary_mass_coverage_ratio") or 0.0)
    if not schema_report:
        return {
            "status": STATUS_FAILED_READABILITY,
            "candidate_front_hair_readability": False,
            "yaw30_hair_readability": False,
            "side_hair_volume_present": False,
            "primary_mass_coverage_ratio": round(primary_mass_coverage, 6),
            "reason": "target schema report missing",
        }

    side_visible_ratio = float(schema_report.get("side_visible_ratio_to_front") or 0.0)
    side_edge_readable = bool(schema_report.get("side_view_hair_edge_readability"))
    side_hair_volume_present = side_edge_readable and side_visible_ratio >= 0.18
    candidate_visible_area_ratio = float(schema_report.get("candidate_visible_area_ratio") or 0.0)
    soft_silhouette_coverage_ratio = float(schema_report.get("soft_silhouette_coverage_ratio") or 0.0)
    candidate_front_hair_readability = (
        bool(schema_report.get("candidate_front_visible_hair_mass"))
        and primary_mass_coverage >= REQUIRED_THRESHOLDS["primary_mass_coverage_ratio"]
        and candidate_visible_area_ratio >= REQUIRED_THRESHOLDS["candidate_visible_area_ratio"]
        and soft_silhouette_coverage_ratio >= REQUIRED_THRESHOLDS["soft_silhouette_coverage_ratio"]
    )
    gates = {
        "candidate_front_hair_readability": candidate_front_hair_readability,
        "yaw30_hair_readability": bool(schema_report.get("yaw30_hair_readability")),
        "side_hair_volume_present": side_hair_volume_present,
        "primary_mass_coverage_ratio": round(primary_mass_coverage, 6),
        "back_hair_mass_presence_ratio": schema_report.get("back_hair_mass_presence_ratio"),
        "side_hair_left_presence_ratio": schema_report.get("side_hair_left_presence_ratio"),
        "side_hair_right_presence_ratio": schema_report.get("side_hair_right_presence_ratio"),
        "bangs_presence_ratio": schema_report.get("bangs_presence_ratio"),
        "forbidden_candidate_leak_ratio": schema_report.get("forbidden_candidate_leak_ratio"),
        "candidate_soft_inside_ratio": schema_report.get("candidate_soft_inside_ratio"),
        "candidate_core_coverage_ratio": schema_report.get("candidate_core_coverage_ratio"),
        "candidate_visible_area_ratio": schema_report.get("candidate_visible_area_ratio"),
        "soft_silhouette_coverage_ratio": schema_report.get("soft_silhouette_coverage_ratio"),
        "side_visible_ratio_to_front": schema_report.get("side_visible_ratio_to_front"),
        "candidate_front_hair_readability_reason": (
            "candidate-only front has enough visible area and soft silhouette coverage"
            if candidate_front_hair_readability
            else "candidate-only front is still too sparse or fragmented for silhouette-mass review"
        ),
    }
    pass_required = (
        gates["candidate_front_hair_readability"]
        and gates["yaw30_hair_readability"]
        and gates["side_hair_volume_present"]
        and float(gates["back_hair_mass_presence_ratio"] or 0.0) >= REQUIRED_THRESHOLDS["back_hair_mass_presence_ratio"]
        and float(gates["side_hair_left_presence_ratio"] or 0.0) >= REQUIRED_THRESHOLDS["side_hair_left_presence_ratio"]
        and float(gates["side_hair_right_presence_ratio"] or 0.0) >= REQUIRED_THRESHOLDS["side_hair_right_presence_ratio"]
        and float(gates["bangs_presence_ratio"] or 0.0) >= REQUIRED_THRESHOLDS["bangs_presence_ratio"]
        and float(gates["forbidden_candidate_leak_ratio"] or 1.0) < REQUIRED_THRESHOLDS["forbidden_candidate_leak_ratio"]
    )
    gates["status"] = STATUS_MANUAL_REVIEW if pass_required else STATUS_FAILED_READABILITY
    gates["manual_visual_review_status"] = "pending_user_review" if pass_required else "failed_required_visible_mass_gate"
    gates["ready_for_cloth_seam_surface"] = False
    gates["replace_in_beauty_glb"] = False
    gates["reason"] = (
        "candidate-only front/yaw/side meet silhouette-mass review gates; still not accepted without human review"
        if pass_required
        else "one or more silhouette-mass gates failed; keep cloth blocked"
    )
    return gates


def patch_reports(paths: ActuatorPaths, gates: dict[str, Any], schema_report: dict[str, Any] | None) -> None:
    validation_report = load_json(paths.report_path)
    validation_report["status"] = gates["status"]
    validation = validation_report.setdefault("validation", {})
    validation.update(gates)
    validation["visual_sanity_status"] = gates["status"]
    validation["visual_sanity_reason"] = gates["reason"]
    validation["manual_visual_review"] = "required" if gates["status"] == STATUS_MANUAL_REVIEW else "failed"
    validation["ready_for_cloth_seam_surface"] = False
    validation["target_schema_v1"] = schema_report or {}
    write_json(paths.report_path, validation_report)

    ci_report = load_json(VALIDATION_CI_REPORT)
    if ci_report:
        ci_report["status"] = gates["status"]
        ci_report["ready_for_cloth_seam_surface"] = False
        ci_report.setdefault("candidate_contract", {}).update(
            {
                "visual_sanity_status": gates["status"],
                "manual_visual_review": validation["manual_visual_review"],
                "ready_for_cloth_seam_surface": False,
                "replace_in_beauty_glb": False,
                "candidate_front_hair_readability": gates["candidate_front_hair_readability"],
                "yaw30_hair_readability": gates["yaw30_hair_readability"],
                "side_hair_volume_present": gates["side_hair_volume_present"],
            }
        )
        ci_report.setdefault("quality", {})["silhouette_mass_v1"] = gates
        write_json(VALIDATION_CI_REPORT, ci_report)


def make_contact_sheet(paths: ActuatorPaths) -> None:
    tile = (360, 480)
    rows = [
        ("candidate_front", "new silhouette mass"),
        ("overlay_front", "new overlay"),
        ("yaw30", "new yaw30"),
        ("side", "new side"),
    ]
    previous = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "art_directed_v1_variants" / "hair_variants_contact_sheet.png"
    sheet_width = tile[0] * 2
    sheet_height = tile[1] * len(rows)
    sheet = Image.new("RGBA", (sheet_width, sheet_height), (24, 24, 24, 255))
    draw = ImageDraw.Draw(sheet)
    if previous.exists():
        previous_img = Image.open(previous).convert("RGBA").resize((tile[0], sheet_height), Image.Resampling.LANCZOS)
        sheet.alpha_composite(previous_img, (0, 0))
        draw.rectangle((0, 0, tile[0] - 1, 36), fill=(0, 0, 0, 190))
        draw.text((8, 9), "art_directed_v1 variants", fill=(255, 255, 255, 255))
    screenshots = screenshot_records(paths)
    for row, (key, label) in enumerate(rows):
        record = screenshots[key]
        x = tile[0]
        y = row * tile[1]
        if record["exists"]:
            image = Image.open(REPO_ROOT / record["path"]).convert("RGBA").resize(tile, Image.Resampling.LANCZOS)
        else:
            image = Image.new("RGBA", tile, (50, 50, 50, 255))
            ImageDraw.Draw(image).text((16, 220), "missing", fill=(255, 128, 128, 255))
        sheet.alpha_composite(image, (x, y))
        draw.rectangle((x, y, x + tile[0] - 1, y + 36), fill=(0, 0, 0, 190))
        draw.text((x + 8, y + 9), label, fill=(255, 255, 255, 255))
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)


def update_markdown_state(gates: dict[str, Any]) -> None:
    note = f"""

## Hair Silhouette Mass v1

- Route: `hair_silhouette_mass_v1`
- Status: `{gates['status']}`
- `replace_in_beauty_glb=false`
- `ready_for_cloth_seam_surface=false`
- `primary_mass_coverage_ratio={gates.get('primary_mass_coverage_ratio')}`
- `forbidden_candidate_leak_ratio={gates.get('forbidden_candidate_leak_ratio')}`
- `candidate_front_hair_readability={gates.get('candidate_front_hair_readability')}`
- `yaw30_hair_readability={gates.get('yaw30_hair_readability')}`
- `side_hair_volume_present={gates.get('side_hair_volume_present')}`
- Boundary: candidate review asset only; not accepted as production hair.
"""
    for path in (PROJECT_STATE, BACKLOG):
        if path.exists():
            text = path.read_text(encoding="utf-8")
            marker = "## Hair Silhouette Mass v1"
            if marker in text:
                text = text[: text.index(marker)].rstrip() + note
            else:
                text = text.rstrip() + note
            path.write_text(text + "\n", encoding="utf-8")


def write_handoff(paths: ActuatorPaths, gates: dict[str, Any], steps: dict[str, Any]) -> None:
    handoff = f"""COPY_TO_CHATGPT_HANDOFF
项目：jupiternaut/resonance-afterlight-yuna-3d
分支：待最终 git status 确认
提交：待最终 commit 确认
本轮目标：生成 `hair_silhouette_mass_v1`，用主发块优先路线解决 art_directed_v1 candidate-only 稀疏问题。
本轮结论：`{gates['status']}`；仍需人工视觉复核，不应推进 `cloth_seam_surface`。
核心状态：
- v8 unchanged: 待最终 v8 diff check
- replace_in_beauty_glb: false
- ready_for_cloth_seam_surface: false
- visual_sanity_status: {gates['status']}
- manual_review: {gates.get('manual_visual_review_status')}
关键指标：
- primary_mass_coverage_ratio: {gates.get('primary_mass_coverage_ratio')}
- forbidden_candidate_leak_ratio: {gates.get('forbidden_candidate_leak_ratio')}
- candidate_soft_inside_ratio: {gates.get('candidate_soft_inside_ratio')}
- candidate_core_coverage_ratio: {gates.get('candidate_core_coverage_ratio')}
- back_hair_mass_presence_ratio: {gates.get('back_hair_mass_presence_ratio')}
- side_hair_left_presence_ratio: {gates.get('side_hair_left_presence_ratio')}
- side_hair_right_presence_ratio: {gates.get('side_hair_right_presence_ratio')}
- bangs_presence_ratio: {gates.get('bangs_presence_ratio')}
- candidate_front_hair_readability: {gates.get('candidate_front_hair_readability')}
- yaw30_hair_readability: {gates.get('yaw30_hair_readability')}
- side_hair_volume_present: {gates.get('side_hair_volume_present')}
生成/更新文件：
- {display_path(paths.spec_path)}
- {display_path(paths.obj_path)}
- {display_path(paths.obj_path.with_suffix('.mtl'))}
- {display_path(paths.glb_path)}
- {display_path(paths.report_path)}
- {display_path(VALIDATION_CI_REPORT)}
- {display_path(CONTACT_SHEET)}
- {display_path(TARGET_SCHEMA_EVAL_DIR / 'hair_target_schema_v1_report.json')}
验证命令：
- build: {steps.get('build', {}).get('status', 'ok')}
- blender_validation_exit: {steps.get('blender_validation', {}).get('exit_code')}
- target_schema_eval_exit: {steps.get('target_schema_eval', {}).get('exit_code')}
当前阻塞：hair route 仍是候选/复核对象；未人工接受前不允许替换 v8 beauty，也不允许推进 cloth。
推荐下一步 Codex goal：
/goal Manual-review `hair_silhouette_mass_v1` screenshots and, only if human review accepts candidate-only front/yaw/side, plan the next hair cleanup; otherwise mark failed and keep cloth blocked.
"""
    HANDOFF.parent.mkdir(parents=True, exist_ok=True)
    HANDOFF.write_text(handoff, encoding="utf-8")


def main() -> int:
    paths = route_paths()
    result = run_hair_silhouette_mass_v1(paths)
    validation_step = run_step(
        [
            sys.executable,
            str(CHARACTER_PACKAGE / "tools" / "run_blender_semantic_validation.py"),
            "--candidate-glb",
            str(paths.glb_path),
            "--candidate-report",
            str(paths.report_path),
            "--output-dir",
            str(VALIDATION_DIR),
            "--report",
            str(VALIDATION_CI_REPORT),
        ]
    )
    candidate_front = VALIDATION_DIR / f"{paths.glb_path.stem}_validation_candidate_front.png"
    schema_step: dict[str, Any]
    schema_report: dict[str, Any] | None = None
    if candidate_front.exists():
        schema_report = build_target_schema_report(
            TARGET_SCHEMA_EVAL_DIR,
            update_reports=True,
            candidate_front=candidate_front,
            candidate_route_label=ACTUATOR_LABEL,
            validation_report_path=paths.report_path,
            validation_ci_report_path=VALIDATION_CI_REPORT,
        )
        schema_step = {
            "args": [
                "build_hair_target_schema_v1.build_report",
                "--output-dir",
                display_path(TARGET_SCHEMA_EVAL_DIR),
            ],
            "exit_code": 0,
            "log_tail": [
                f"candidate_target_schema_status={schema_report['candidate_target_schema_status']}",
                f"forbidden_candidate_leak_ratio={schema_report['forbidden_candidate_leak_ratio']}",
            ],
        }
    else:
        schema_step = {
            "args": [],
            "exit_code": 0,
            "skipped_with_reason": "candidate_front_render_missing",
        }
    gates = evaluate_required_gates(load_json(paths.report_path), schema_report)
    patch_reports(paths, gates, schema_report)
    make_contact_sheet(paths)
    update_markdown_state(gates)
    steps = {
        "build": result.to_dict(),
        "blender_validation": validation_step,
        "target_schema_eval": schema_step,
    }
    write_handoff(paths, gates, steps)
    run_report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": ROUTE,
        "status": gates["status"],
        "boundary": "Manual-review candidate route only; does not replace v8 beauty and does not unblock cloth.",
        "gates": gates,
        "generated_files": {
            "contact_sheet": file_record(CONTACT_SHEET),
            "chatgpt_handoff": file_record(HANDOFF),
            "screenshots": screenshot_records(paths),
        },
        "steps": steps,
    }
    write_json(OUT / "silhouette_mass_v1_run_report.json", run_report)
    print(json.dumps(run_report, ensure_ascii=False, indent=2))
    return 0


ACTUATOR_LABEL = "hair_silhouette_mass_v1"


if __name__ == "__main__":
    raise SystemExit(main())
