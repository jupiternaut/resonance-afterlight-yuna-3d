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
    if report.get("status") not in {"generated_with_warnings", "failed"}:
        errors.append("status must be generated_with_warnings or failed")
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
