#!/usr/bin/env python3
"""Separate hair debug imagery from beauty imagery and attach a style gate.

This pass does not rebuild geometry. It classifies the existing
curve_bundle_candidate_v1 renders into explicit debug and beauty outputs, then
records whether the beauty candidate satisfies the YUNA hair art direction.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


CHARACTER_PACKAGE = Path(__file__).resolve().parents[1]
REPO_ROOT = CHARACTER_PACKAGE.parent
STYLE_TARGET_PATH = CHARACTER_PACKAGE / "style_targets" / "yuna_cinematic_sci_fi_heroine_v0.json"
HAIR_ROUTE_DIR = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "curve_bundle_candidate_v1"
VALIDATION_DIR = HAIR_ROUTE_DIR / "validation_ci"
TARGET_SCHEMA_EVAL_DIR = HAIR_ROUTE_DIR / "target_schema_v1_eval"
VALIDATION_REPORT = HAIR_ROUTE_DIR / "validation_report.json"
VALIDATION_CI_REPORT = VALIDATION_DIR / "validation_ci_report.json"


DEBUG_OUTPUTS = {
    "debug_curve_overlay_front": (
        CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "primary_curve_bundle_v1_front_overlay.png",
        VALIDATION_DIR / "debug_curve_overlay_front.png",
    ),
    "debug_curve_overlay_yaw30": (
        CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "primary_curve_bundle_v1_yaw30_plan.png",
        VALIDATION_DIR / "debug_curve_overlay_yaw30.png",
    ),
    "debug_schema_overlay": (
        TARGET_SCHEMA_EVAL_DIR / "candidate_vs_schema_overlay.png",
        VALIDATION_DIR / "debug_schema_overlay.png",
    ),
}

BEAUTY_OUTPUTS = {
    "candidate_beauty_front": (VALIDATION_DIR / "candidate_front.png", VALIDATION_DIR / "candidate_beauty_front.png"),
    "overlay_beauty_front": (VALIDATION_DIR / "overlay_front.png", VALIDATION_DIR / "overlay_beauty_front.png"),
    "yaw30_beauty": (VALIDATION_DIR / "yaw30.png", VALIDATION_DIR / "yaw30_beauty.png"),
    "side_beauty": (VALIDATION_DIR / "side.png", VALIDATION_DIR / "side_beauty.png"),
}

GUIDE_NAME_TOKENS = (
    "debug",
    "guide",
    "bbox",
    "bounding",
    "schema",
    "curve_overlay",
    "construction",
    "anchor_box",
)


def display(path: Path) -> str:
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
        "path": display(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
    }


def style_target() -> dict[str, Any]:
    return {
        "id": "yuna_cinematic_sci_fi_heroine_v0",
        "version": 1,
        "created_for": "YUNA semantic v9 hair candidate style gate",
        "direction": {
            "summary": "premium cinematic sci-fi heroine",
            "intent": (
                "Hair should read as a coherent, elegant, scalp-anchored anime "
                "heroine silhouette suitable for later DCC hair authoring, not "
                "as a construction overlay or generic alpha-sliced technical demo."
            ),
            "not_final_production_hair": True,
        },
        "palette": {
            "graphite_black": "#101318",
            "pearl_white": "#F4F8FA",
            "gunmetal": "#4B5563",
            "cyan_accent": "#28DDEB",
            "notes": "Pearl/cyan hair accents are allowed, but debug-white guide bars are not beauty hair.",
        },
        "hair_requirements": {
            "large_coherent_back_hair_mass": True,
            "soft_curved_bangs": True,
            "left_right_side_drape": True,
            "scalp_anchored_flow": True,
            "limited_secondary_strands": True,
            "limited_flyaway_strands": True,
            "transparent_tapered_tips": True,
            "no_barcode_strips": True,
            "no_straight_guide_bars": True,
            "no_fragmented_shards": True,
            "no_copied_commercial_character_design": True,
        },
        "beauty_render_forbidden_content": [
            "curve guide lines",
            "anchor markers",
            "bounding boxes",
            "straight construction bars",
            "schema masks",
            "white debug material used as hair material",
        ],
        "external_prior_policy": {
            "external_assets_are_priors_not_replacements": True,
            "copying_commercial_character_design_is_forbidden": True,
        },
    }


def copy_outputs(mapping: dict[str, tuple[Path, Path]]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for name, (source, target) in mapping.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.exists():
            shutil.copyfile(source, target)
        records[name] = {
            "source": file_record(source),
            "output": file_record(target),
        }
    return records


def make_beauty_contact_sheet(records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    output = VALIDATION_DIR / "beauty_contact_sheet.png"
    image_paths = [Path(records[key]["output"]["path"]) for key in BEAUTY_OUTPUTS]
    resolved = [REPO_ROOT / path for path in image_paths]
    if not all(path.exists() for path in resolved):
        return {"path": display(output), "exists": False, "bytes": 0, "skipped_with_reason": "missing_beauty_input"}

    images = [Image.open(path).convert("RGB") for path in resolved]
    thumb_width = 600
    thumb_height = 800
    thumbs = []
    for image in images:
        image.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (thumb_width, thumb_height), (184, 184, 184))
        canvas.paste(image, ((thumb_width - image.width) // 2, (thumb_height - image.height) // 2))
        thumbs.append(canvas)
    sheet = Image.new("RGB", (thumb_width * 2, thumb_height * 2), (184, 184, 184))
    for index, thumb in enumerate(thumbs):
        x = (index % 2) * thumb_width
        y = (index // 2) * thumb_height
        sheet.paste(thumb, (x, y))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    return file_record(output)


def _candidate_mesh_debug_leaks(ci_report: dict[str, Any]) -> list[str]:
    inventory = ci_report.get("inventory", {})
    names = [str(name) for name in inventory.get("candidate_mesh_names", [])]
    leaks = []
    for name in names:
        lowered = name.lower()
        if any(token in lowered for token in GUIDE_NAME_TOKENS):
            leaks.append(name)
    return leaks


def build_style_gate(
    *,
    validation_report: dict[str, Any],
    validation_ci_report: dict[str, Any],
    debug_records: dict[str, dict[str, Any]],
    beauty_records: dict[str, dict[str, Any]],
    contact_sheet: dict[str, Any],
) -> dict[str, Any]:
    missing_beauty = [
        name for name, record in beauty_records.items()
        if not record["output"]["exists"] or int(record["output"]["bytes"]) <= 0
    ]
    debug_leak_names = _candidate_mesh_debug_leaks(validation_ci_report)
    guide_leak = bool(debug_leak_names)
    beauty_render_exists = not missing_beauty and bool(contact_sheet.get("exists"))
    debug_guides_hidden = beauty_render_exists and not guide_leak

    validation = validation_report.get("validation", {})
    schema_gate_passed = (
        validation_report.get("status") == "schema_gate_passed_manual_review_required"
        or validation.get("candidate_target_schema_status") == "schema_gate_passed_manual_review_required"
    )
    has_visible_mass = bool(validation.get("candidate_front_visible_hair_mass"))
    has_group_presence = bool(validation.get("primary_group_presence_passed"))
    yaw30_readable = bool(validation.get("yaw30_hair_readability"))
    side_readable = bool(validation.get("side_hair_readability"))

    # This pass intentionally does not auto-accept hair style quality. The
    # current candidate is guide-free as a beauty render, but remains too
    # construction-like for the requested cinematic heroine target.
    numeric_readability = bool(schema_gate_passed and has_visible_mass and has_group_presence and yaw30_readable and side_readable)
    reads_as_hair = False
    if guide_leak:
        status = "failed_debug_leak_into_beauty"
        reason = "beauty candidate includes debug/guide-like mesh names"
    elif not beauty_render_exists:
        status = "failed_debug_leak_into_beauty"
        reason = "one or more required beauty renders are missing"
    elif not numeric_readability:
        status = "style_gate_failed_manual_review_required"
        reason = "beauty render is guide-free, but current metrics do not prove hair readability"
    else:
        status = "style_gate_failed_manual_review_required"
        reason = (
            "beauty renders are separated from debug outputs and schema metrics pass, "
            "but the candidate remains construction-like and is not accepted against the cinematic sci-fi heroine style target"
        )

    # Keep an explicit style warning even when the programmatic style gate is
    # ready for human review.
    front_quality = "manual_review_required_coherent_mass_but_construction_like"
    yaw_quality = "manual_review_required_readable_but_not_final_hair"
    side_quality = "manual_review_required_readable_but_not_final_hair"

    return {
        "style_target": "CharacterPackage/style_targets/yuna_cinematic_sci_fi_heroine_v0.json",
        "style_target_id": "yuna_cinematic_sci_fi_heroine_v0",
        "style_target_status": status,
        "style_target_reason": reason,
        "debug_guides_hidden_in_beauty": debug_guides_hidden,
        "beauty_render_exists": beauty_render_exists,
        "guide_leak_into_beauty": guide_leak,
        "guide_leak_mesh_names": debug_leak_names,
        "reads_as_hair": reads_as_hair,
        "front_hair_silhouette_quality": front_quality,
        "yaw30_hair_likeness": yaw_quality,
        "side_hair_likeness": side_quality,
        "candidate_beauty_manual_review_required": True,
        "candidate_accepted": False,
        "replace_in_beauty_glb": False,
        "ready_for_cloth_seam_surface": False,
        "schema_gate_passed": schema_gate_passed,
        "numeric_readability": numeric_readability,
        "debug_outputs": debug_records,
        "beauty_outputs": beauty_records,
        "beauty_contact_sheet": contact_sheet,
        "failure_rules": {
            "debug_leak_status": "failed_debug_leak_into_beauty",
            "not_hair_like_status": "style_gate_failed_manual_review_required",
            "manual_review_status": "beauty_candidate_manual_review_required",
        },
    }


def apply_style_gate_to_report(report: dict[str, Any], style_gate: dict[str, Any]) -> dict[str, Any]:
    previous_status = report.get("status")
    report["schema_gate_status"] = previous_status
    report["status"] = style_gate["style_target_status"]
    report["style_gate"] = style_gate
    report["style_target"] = style_gate["style_target"]
    report["ready_for_cloth_seam_surface"] = False
    validation = report.setdefault("validation", {})
    validation.update({
        "style_target": style_gate["style_target"],
        "debug_guides_hidden_in_beauty": style_gate["debug_guides_hidden_in_beauty"],
        "beauty_render_exists": style_gate["beauty_render_exists"],
        "guide_leak_into_beauty": style_gate["guide_leak_into_beauty"],
        "style_target_status": style_gate["style_target_status"],
        "reads_as_hair": style_gate["reads_as_hair"],
        "front_hair_silhouette_quality": style_gate["front_hair_silhouette_quality"],
        "yaw30_hair_likeness": style_gate["yaw30_hair_likeness"],
        "side_hair_likeness": style_gate["side_hair_likeness"],
        "candidate_beauty_manual_review_required": True,
        "visual_sanity_status": style_gate["style_target_status"],
        "manual_visual_review_status": "pending_style_review",
        "replace_in_beauty_glb": False,
        "ready_for_cloth_seam_surface": False,
    })
    return report


def apply_style_gate_to_ci_report(report: dict[str, Any], style_gate: dict[str, Any]) -> dict[str, Any]:
    previous_status = report.get("status")
    report["schema_gate_status"] = previous_status
    report["status"] = style_gate["style_target_status"]
    report["style_gate"] = style_gate
    report["style_target"] = style_gate["style_target"]
    report["ready_for_cloth_seam_surface"] = False
    contract = report.setdefault("candidate_contract", {})
    contract.update({
        "style_target": style_gate["style_target"],
        "style_target_status": style_gate["style_target_status"],
        "debug_guides_hidden_in_beauty": style_gate["debug_guides_hidden_in_beauty"],
        "beauty_render_exists": style_gate["beauty_render_exists"],
        "guide_leak_into_beauty": style_gate["guide_leak_into_beauty"],
        "reads_as_hair": style_gate["reads_as_hair"],
        "candidate_beauty_manual_review_required": True,
        "visual_sanity_status": style_gate["style_target_status"],
        "replace_in_beauty_glb": False,
    })
    report.setdefault("quality", {})["style_gate"] = style_gate
    return report


def write_handoff(style_gate: dict[str, Any]) -> None:
    handoff = CHARACTER_PACKAGE / "semantic_layer_v9_candidate" / "CHATGPT_HANDOFF.md"
    lines = [
        "# COPY_TO_CHATGPT_HANDOFF",
        "",
        "项目：`jupiternaut/resonance-afterlight-yuna-3d`",
        "",
        "本轮目标：`separate_hair_debug_beauty_and_add_style_gate_v1`",
        "",
        "本轮结论：",
        f"- style_target_status: `{style_gate['style_target_status']}`",
        f"- debug_guides_hidden_in_beauty: `{style_gate['debug_guides_hidden_in_beauty']}`",
        f"- beauty_render_exists: `{style_gate['beauty_render_exists']}`",
        f"- guide_leak_into_beauty: `{style_gate['guide_leak_into_beauty']}`",
        f"- reads_as_hair: `{style_gate['reads_as_hair']}`",
        "- `replace_in_beauty_glb=false`",
        "- `ready_for_cloth_seam_surface=false`",
        "- `semantic_layer_v8` 未修改",
        "- 当前仍不是 final production hair",
        "",
        "生成/更新文件：",
        "- `CharacterPackage/style_targets/yuna_cinematic_sci_fi_heroine_v0.json`",
        "- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/debug_curve_overlay_front.png`",
        "- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/debug_curve_overlay_yaw30.png`",
        "- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/debug_schema_overlay.png`",
        "- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/candidate_beauty_front.png`",
        "- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/overlay_beauty_front.png`",
        "- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/yaw30_beauty.png`",
        "- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/side_beauty.png`",
        "- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/beauty_contact_sheet.png`",
        "- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_report.json`",
        "- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/validation_ci_report.json`",
        "",
        "当前阻塞：",
        "- `manual_style_review_curve_bundle_hair_candidate_v1`",
        "",
        "推荐下一条 Codex Goal：",
        "```text",
        "/goal Manual-review curve_bundle_candidate_v1 beauty outputs.",
        "Read the beauty/debug split outputs and decide whether the candidate is worth another style refinement pass.",
        "Keep semantic_layer_v8 unchanged, keep replace_in_beauty_glb=false, and do not proceed to cloth_seam_surface.",
        "```",
        "",
        "验证结果：待最终 Codex 回复填写。",
    ]
    handoff.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    write_json(STYLE_TARGET_PATH, style_target())
    validation_report = load_json(VALIDATION_REPORT)
    validation_ci_report = load_json(VALIDATION_CI_REPORT)
    debug_records = copy_outputs(DEBUG_OUTPUTS)
    beauty_records = copy_outputs(BEAUTY_OUTPUTS)
    contact_sheet = make_beauty_contact_sheet(beauty_records)
    style_gate = build_style_gate(
        validation_report=validation_report,
        validation_ci_report=validation_ci_report,
        debug_records=debug_records,
        beauty_records=beauty_records,
        contact_sheet=contact_sheet,
    )
    write_json(VALIDATION_REPORT, apply_style_gate_to_report(validation_report, style_gate))
    write_json(VALIDATION_CI_REPORT, apply_style_gate_to_ci_report(validation_ci_report, style_gate))
    write_handoff(style_gate)
    print(json.dumps({"status": style_gate["style_target_status"], "style_gate": style_gate}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
