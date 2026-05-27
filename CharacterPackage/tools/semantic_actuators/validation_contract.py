from __future__ import annotations

from pathlib import Path
from typing import Any


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
    }


def validate_weapon_candidate_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("part_id") != "weapon":
        errors.append("part_id must be weapon")
    if report.get("actuator") != "weapon_hardsurface_ortho_v0":
        errors.append("unexpected actuator")
    if report.get("status") not in {"generated_with_warnings", "failed", "failed_visual_sanity"}:
        errors.append("status must be generated_with_warnings, failed, or failed_visual_sanity")
    mesh = report.get("mesh_summary", {})
    if mesh.get("vertices", 0) <= 0:
        errors.append("mesh has no vertices")
    if mesh.get("faces", 0) <= 0:
        errors.append("mesh has no faces")
    validation = report.get("validation", {})
    if validation.get("independent_object") is not True:
        errors.append("weapon candidate must be independent")
    if validation.get("has_thickness") is not True:
        errors.append("weapon candidate must have thickness")
    if validation.get("has_bevel_proxy") is not True:
        errors.append("weapon candidate must have bevel proxy")
    if validation.get("has_hand_socket_metadata") is not True:
        errors.append("weapon candidate must include hand_R_socket metadata")
    return errors


def validate_boot_candidate_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("part_id") != "boots":
        errors.append("part_id must be boots")
    if report.get("actuator") != "boot_hardsurface_ortho_v0":
        errors.append("unexpected actuator")
    if report.get("status") not in {"generated_with_warnings", "failed"}:
        errors.append("status must be generated_with_warnings or failed")
    mesh = report.get("mesh_summary", {})
    if mesh.get("vertices", 0) <= 0:
        errors.append("mesh has no vertices")
    if mesh.get("faces", 0) <= 0:
        errors.append("mesh has no faces")
    if mesh.get("component_count", 0) < 2:
        errors.append("boot candidate should contain at least two visible components")
    validation = report.get("validation", {})
    if validation.get("independent_objects") is not True:
        errors.append("boot candidate must use independent objects")
    if validation.get("has_thickness") is not True:
        errors.append("boot candidate must have thickness")
    if validation.get("has_bevel_proxy") is not True:
        errors.append("boot candidate must have bevel proxy")
    if validation.get("has_foot_socket_metadata") is not True:
        errors.append("boot candidate must include foot socket metadata")
    return errors


def validate_leg_candidate_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("part_id") != "legs":
        errors.append("part_id must be legs")
    if report.get("actuator") != "leg_quad_loop_retopo_proxy_v0":
        errors.append("unexpected actuator")
    if report.get("status") not in {"generated_with_warnings", "failed"}:
        errors.append("status must be generated_with_warnings or failed")
    mesh = report.get("mesh_summary", {})
    if mesh.get("vertices", 0) <= 0:
        errors.append("mesh has no vertices")
    if mesh.get("faces", 0) <= 0:
        errors.append("mesh has no faces")
    if mesh.get("component_count", 0) != 2:
        errors.append("leg candidate should contain left and right components")
    if mesh.get("ring_count", 0) < 8:
        errors.append("leg candidate should contain enough vertical loop rings")
    if mesh.get("radial_segments", 0) < 8:
        errors.append("leg candidate should contain enough radial segments")
    if mesh.get("quad_faces_only") is not True:
        errors.append("leg candidate must use quad faces only")
    validation = report.get("validation", {})
    if validation.get("independent_objects") is not True:
        errors.append("leg candidate must use independent objects")
    if validation.get("has_quad_loop_topology") is not True:
        errors.append("leg candidate must expose quad-loop topology")
    if validation.get("has_knee_ankle_loop_metadata") is not True:
        errors.append("leg candidate must include knee/ankle loop metadata")
    if validation.get("replace_in_beauty_glb") is not False:
        errors.append("leg candidate must not replace v8 beauty mesh yet")
    return errors


def validate_hair_candidate_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("part_id") != "hair":
        errors.append("part_id must be hair")
    if report.get("actuator") != "authored_hair_ribbons_v0":
        errors.append("unexpected actuator")
    if report.get("status") not in {"generated_with_warnings", "failed", "failed_visual_sanity", "failed_hair_mask_alignment", "failed_validation_framing", "manual_review_failed"}:
        errors.append("status must be generated_with_warnings, failed, or a hair visual failure status")
    mesh = report.get("mesh_summary", {})
    if mesh.get("vertices", 0) <= 0:
        errors.append("mesh has no vertices")
    if mesh.get("faces", 0) <= 0:
        errors.append("mesh has no faces")
    if mesh.get("group_count", 0) < 4:
        errors.append("hair candidate should contain four source hair groups")
    if mesh.get("ribbon_count", 0) < 24:
        errors.append("hair candidate should contain enough ribbon strands")
    if mesh.get("depth_group_count", 0) < 3:
        errors.append("hair candidate should preserve at least three depth groups")
    validation = report.get("validation", {})
    if validation.get("independent_objects") is not True:
        errors.append("hair candidate must use independent objects")
    if validation.get("has_ribbon_meshes") is not True:
        errors.append("hair candidate must expose ribbon meshes")
    if validation.get("has_depth_groups") is not True:
        errors.append("hair candidate must expose multiple depth groups")
    if validation.get("has_spring_hook_metadata") is not True:
        errors.append("hair candidate must include spring hook metadata")
    if validation.get("side_back_are_soft_constraints") is not True:
        errors.append("hair candidate must keep side/back as soft constraints")
    if validation.get("replace_in_beauty_glb") is not False:
        errors.append("hair candidate must not replace v8 beauty mesh yet")
    required_sanity_fields = (
        "alpha_material_valid",
        "black_alpha_leak_ratio",
        "candidate_black_pixel_ratio",
        "face_occlusion_ratio",
        "non_hair_occlusion_ratio",
        "hair_mask_iou",
        "outside_hair_mask_ratio",
        "candidate_is_hair_only",
        "baseline_framing_valid",
        "overlay_alignment_valid",
        "visual_sanity_status",
        "visual_sanity_reason",
    )
    for field in required_sanity_fields:
        if field not in validation:
            errors.append(f"hair candidate missing visual sanity field: {field}")
    if validation.get("alpha_material_valid") is not True:
        errors.append("hair candidate must have valid alpha material")
    if validation.get("black_alpha_leak_ratio", 1.0) >= 0.02:
        errors.append("hair candidate black alpha leak ratio is too high")
    if validation.get("candidate_black_pixel_ratio", 1.0) >= 0.05:
        errors.append("hair candidate black pixel ratio is too high")
    if validation.get("face_occlusion_ratio", 1.0) >= 0.15:
        errors.append("hair candidate face occlusion ratio is too high")
    if validation.get("non_hair_occlusion_ratio", 1.0) >= 0.10:
        errors.append("hair candidate non-hair occlusion ratio is too high")
    visual_status = validation.get("visual_sanity_status")
    if visual_status not in {"passed", "passed_with_minor_warnings", "failed_visual_sanity", "failed_hair_mask_alignment", "failed_validation_framing", "manual_review_failed"}:
        errors.append("hair candidate visual_sanity_status is invalid")
    if visual_status in {"passed", "passed_with_minor_warnings"}:
        if validation.get("candidate_is_hair_only") is not True:
            errors.append("passing hair candidate must be constrained to the v8 hair mask union")
        if validation.get("baseline_framing_valid") is not True:
            errors.append("passing hair candidate requires valid baseline front framing")
        if validation.get("overlay_alignment_valid") is not True:
            errors.append("passing hair candidate requires valid overlay alignment")
    return errors
