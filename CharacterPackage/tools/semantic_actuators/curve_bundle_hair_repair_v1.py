from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageFilter

from .art_directed_hair_ribbons_v1 import build_panel_mesh
from .authored_hair_ribbons import (
    V8_SOURCE_HEIGHT_WORLD,
    HairRibbon,
    blender_export_glb,
    report_file_record,
    report_path,
    schema_region_prior,
    write_json,
    write_obj,
)
from .curve_bundle_hair_candidate_v1 import (
    ACTUATOR_NAME,
    PART_ID,
    PRIMARY_GROUPS,
    STATUS_FAILED_VISUAL,
    STATUS_MANUAL_REVIEW,
    TARGET_GROUP_MASKS,
    CurveRibbonRecord,
    _binary,
    _build_metrics,
    _build_spec,
    _build_validation,
    _component_primitive_intent,
    _mask_components,
    _mesh_summary,
    _target_mask,
    GROUP_CONFIG,
)
from .state import ActuatorPaths, ActuatorResult
from .validation_contract import validate_hair_candidate_report


REPAIR_ROUTE = "repair_curve_bundle_hair_candidate_v1_until_schema_gate"
REPAIR_ACTUATOR_NAME = "curve_bundle_hair_ribbons_v1"


@dataclass(frozen=True)
class RepairAttemptConfig:
    index: int
    name: str
    soft_dilate_radius: int = 0
    forbidden_guard_radius: int = 0
    component_min_area: int = 20
    component_limit: int = 6
    lanes_per_component: int = 2
    back_lanes_per_component: int = 3
    primary_width_fraction: float = 0.98
    secondary_enabled: bool = False
    side_profile_enabled: bool = False
    use_region_soft: bool = False


REPAIR_ATTEMPTS: tuple[RepairAttemptConfig, ...] = (
    RepairAttemptConfig(
        index=1,
        name="alpha_masked_group_components",
        component_min_area=20,
        component_limit=6,
        lanes_per_component=2,
        back_lanes_per_component=3,
        primary_width_fraction=0.98,
    ),
    RepairAttemptConfig(
        index=2,
        name="soft_expanded_group_components",
        soft_dilate_radius=3,
        component_min_area=20,
        component_limit=7,
        lanes_per_component=2,
        back_lanes_per_component=3,
        primary_width_fraction=1.02,
    ),
    RepairAttemptConfig(
        index=3,
        name="visible_mass_soft_expansion",
        soft_dilate_radius=5,
        forbidden_guard_radius=0,
        component_min_area=16,
        component_limit=8,
        lanes_per_component=2,
        back_lanes_per_component=3,
        primary_width_fraction=1.05,
    ),
    RepairAttemptConfig(
        index=4,
        name="dense_core_preserving_components",
        soft_dilate_radius=7,
        forbidden_guard_radius=1,
        component_min_area=12,
        component_limit=8,
        lanes_per_component=3,
        back_lanes_per_component=3,
        primary_width_fraction=1.08,
        use_region_soft=True,
    ),
    RepairAttemptConfig(
        index=5,
        name="full_soft_silhouette_components",
        soft_dilate_radius=10,
        forbidden_guard_radius=1,
        component_min_area=12,
        component_limit=8,
        lanes_per_component=2,
        back_lanes_per_component=3,
        primary_width_fraction=1.10,
        use_region_soft=True,
    ),
    RepairAttemptConfig(
        index=6,
        name="last_safe_soft_core_components",
        soft_dilate_radius=12,
        forbidden_guard_radius=2,
        component_min_area=8,
        component_limit=10,
        lanes_per_component=2,
        back_lanes_per_component=4,
        primary_width_fraction=1.04,
        use_region_soft=True,
    ),
)


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def _mask_pixels(mask: Image.Image) -> int:
    return sum(1 for value in mask.convert("L").getdata() if value > 0)


def _dilate(mask: Image.Image, radius: int) -> Image.Image:
    if radius <= 0:
        return _binary(mask)
    size = radius * 2 + 1
    return _binary(mask).filter(ImageFilter.MaxFilter(size)).point(lambda value: 255 if value > 0 else 0)


def _subtract(source: Image.Image, blocker: Image.Image) -> Image.Image:
    return ImageChops.subtract(_binary(source), _binary(blocker)).point(lambda value: 255 if value > 0 else 0)


def _write_masked_group_texture(path: Path, mask: Image.Image, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", mask.size, (*color, 255))
    image.putalpha(_binary(mask))
    image.save(path)


def _repaired_group_mask(character_package: Path, group_id: str, config: RepairAttemptConfig) -> Image.Image:
    group = _binary(_target_mask(character_package, "group_masks/" + TARGET_GROUP_MASKS[group_id]))
    soft = _binary(_target_mask(character_package, "soft_hair_silhouette_mask.png"))
    forbidden = _binary(_target_mask(character_package, "forbidden_nonhair_zone_mask.png"))
    if config.soft_dilate_radius:
        group = _dilate(group, config.soft_dilate_radius)
    if config.use_region_soft:
        source_part = str(GROUP_CONFIG[group_id]["source_part"])
        region_soft = ImageChops.multiply(soft, schema_region_prior(source_part, soft.size)).point(
            lambda value: 255 if value > 0 else 0
        )
        group = ImageChops.lighter(group, region_soft).point(lambda value: 255 if value > 0 else 0)
    allowed = ImageChops.multiply(group, soft).point(lambda value: 255 if value > 0 else 0)
    if config.forbidden_guard_radius:
        forbidden = _dilate(forbidden, config.forbidden_guard_radius)
    return _subtract(allowed, forbidden)


def _coverage_from_masks(masks: dict[str, Image.Image]) -> Image.Image:
    if not masks:
        raise ValueError("Expected at least one repaired group mask")
    image_size = next(iter(masks.values())).size
    coverage = Image.new("L", image_size, 0)
    for mask in masks.values():
        coverage = ImageChops.lighter(coverage, _binary(mask))
    return coverage.point(lambda value: 255 if value > 0 else 0)


def build_repaired_curve_bundle_hair(
    character_package: Path,
    output_dir: Path,
    config: RepairAttemptConfig,
) -> tuple[list[HairRibbon], list[CurveRibbonRecord], dict[str, Any]]:
    bundle_path = character_package / "semantic_layer_v9_hair" / "primary_curve_bundle_v1.json"
    bundle = _load_json(bundle_path)
    soft = _binary(_target_mask(character_package, "soft_hair_silhouette_mask.png"))
    image_size = soft.size
    scale = V8_SOURCE_HEIGHT_WORLD / image_size[1]
    exports_dir = output_dir / "exports"
    mask_dir = output_dir / "repair_masks"
    repaired_masks: dict[str, Image.Image] = {}
    ribbons: list[HairRibbon] = []
    records: list[CurveRibbonRecord] = []

    for group_id in PRIMARY_GROUPS:
        mask = _repaired_group_mask(character_package, group_id, config)
        if _mask_pixels(mask) <= 0:
            mask = _binary(_target_mask(character_package, "group_masks/" + TARGET_GROUP_MASKS[group_id]))
        mask_path = mask_dir / f"{group_id}_repair_attempt_{config.index:02d}_mask.png"
        texture_path = exports_dir / f"{group_id}_repair_attempt_{config.index:02d}.png"
        mask_path.parent.mkdir(parents=True, exist_ok=True)
        mask.save(mask_path)
        _write_masked_group_texture(texture_path, mask, tuple(GROUP_CONFIG[group_id]["color"]))
        repaired_masks[group_id] = mask

        components = _mask_components(mask, min_area=config.component_min_area)[: config.component_limit]
        if not components:
            components = _mask_components(mask, min_area=1)[:1]
        lane_count = config.back_lanes_per_component if group_id == "back_hair_mass" else config.lanes_per_component
        curve = bundle["primary_curves"][group_id]
        group_cfg = GROUP_CONFIG[group_id]
        for component_index, (bbox, _area) in enumerate(components):
            for lane in range(lane_count):
                ribbon_id = f"{group_id}_repair_{config.index:02d}_{component_index + 1:02d}_{lane + 1:02d}"
                depth_offset = (lane - (lane_count - 1) * 0.5) * 0.010
                mesh = build_panel_mesh(
                    bbox,
                    image_size=image_size,
                    scale=scale,
                    depth=float(group_cfg["depth_center"]),
                    depth_offset=depth_offset,
                    thickness=float(group_cfg["thickness"]),
                    width_fraction=config.primary_width_fraction if lane == 0 else config.primary_width_fraction * 0.62,
                    curve_px=(4.0 if group_id != "bangs_primary" else 2.0) * (1.0 + lane * 0.10),
                    constraint_mask=mask,
                )
                intent = _component_primitive_intent(
                    ribbon_id=ribbon_id,
                    curve=curve,
                    group_id=group_id,
                    bbox=bbox,
                    texture_path=texture_path,
                    spring_hook=str(group_cfg["spring_hook"]),
                    lane_index=lane,
                    lane_count=lane_count,
                )
                intent["primitive_type"] = "repaired_curve_bundle_alpha_masked_ribbon"
                intent["repair_attempt"] = config.index
                intent["repair_policy"] = {
                    "sampled_against": [
                        "soft_hair_silhouette",
                        "forbidden_nonhair_zone",
                        "strict_hair_core",
                    ],
                    "texture_alpha": "repaired group mask drives transparency",
                    "forbidden_leak_response": "clip mask before building ribbon panels",
                    "replace_in_beauty_glb": False,
                }
                polygon = [
                    (float(bbox[0]), float(bbox[1])),
                    (float(bbox[2]), float(bbox[1])),
                    (float(bbox[2]), float(bbox[3])),
                    (float(bbox[0]), float(bbox[3])),
                ]
                ribbons.append(
                    HairRibbon(
                        id=ribbon_id,
                        group_id=group_id,
                        source_part_id=str(group_cfg["source_part"]),
                        mask_path=mask_path,
                        texture_path=texture_path,
                        depth_group=str(group_cfg["depth_group"]),
                        spring_hook=str(group_cfg["spring_hook"]),
                        bbox=bbox,
                        mesh=mesh,
                        primitive_intent=intent,
                    )
                )
                records.append(
                    CurveRibbonRecord(
                        ribbon_id=ribbon_id,
                        group_id=group_id,
                        role="primary",
                        depth_group=str(group_cfg["depth_group"]),
                        spring_hook=str(group_cfg["spring_hook"]),
                        texture_path=texture_path,
                        bbox=bbox,
                        front_polygon_px=polygon,
                        primitive_intent=intent,
                    )
                )

    coverage = _coverage_from_masks(repaired_masks)
    coverage_dir = output_dir / "coverage_masks"
    coverage_dir.mkdir(parents=True, exist_ok=True)
    coverage.save(coverage_dir / f"curve_bundle_candidate_repair_attempt_{config.index:02d}_coverage_mask.png")
    metrics = _build_metrics(character_package, coverage, records)
    metrics["repair_attempt"] = config.index
    metrics["repair_attempt_name"] = config.name
    metrics["repair_policy"] = {
        "soft_dilate_radius": config.soft_dilate_radius,
        "forbidden_guard_radius": config.forbidden_guard_radius,
        "component_min_area": config.component_min_area,
        "component_limit": config.component_limit,
        "lanes_per_component": config.lanes_per_component,
        "back_lanes_per_component": config.back_lanes_per_component,
        "secondary_enabled": config.secondary_enabled,
        "side_profile_enabled": config.side_profile_enabled,
        "use_region_soft": config.use_region_soft,
    }
    design_summary = {
        "source_bundle": report_path(bundle_path),
        "hair_design_schema": report_path(character_package / "semantic_layer_v9_hair" / "hair_design_schema_v1.json"),
        "target_schema": report_path(character_package / "semantic_layer_v9_hair" / "target_schema_v1"),
        "repair_source_route": "curve_bundle_candidate_v1",
        "repair_attempt": config.index,
        "repair_attempt_name": config.name,
        "curve_group_count": len(PRIMARY_GROUPS),
        "secondary_strand_count": 0,
        "flyaway_strand_count": 0,
        "side_profile_support_count": 0,
        "render_size": list(image_size),
        "metrics": metrics,
        "status": metrics["status"],
        "manual_review_required": True,
        "replace_in_beauty_glb": False,
        "ready_for_cloth_seam_surface": False,
    }
    return ribbons, records, design_summary


def run_repaired_curve_bundle_hair_candidate_v1(
    paths: ActuatorPaths,
    config: RepairAttemptConfig,
) -> ActuatorResult:
    warnings = [
        "repair_curve_bundle_hair_candidate_v1 is candidate-only and not final production hair.",
        "v8 beauty hair remains active; replace_in_beauty_glb=false.",
        "cloth_seam_surface remains blocked until schema gates and manual visual review pass.",
    ]
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    paths.spec_path.parent.mkdir(parents=True, exist_ok=True)
    paths.obj_path.parent.mkdir(parents=True, exist_ok=True)
    ribbons, records, design_summary = build_repaired_curve_bundle_hair(paths.character_package, paths.output_dir, config)
    write_obj(paths.obj_path, ribbons)
    glb_report = blender_export_glb(
        paths.glb_path,
        ribbons,
        paths.repo_root,
        actuator_name=ACTUATOR_NAME,
        side_alpha=0.0,
    )
    if glb_report.get("status") != "ok":
        warnings.append("GLB export did not complete; see validation.blender_glb_export")
    spec = _build_spec(paths, ribbons, records, design_summary)
    spec["route"] = REPAIR_ROUTE
    spec["repair_attempt"] = config.index
    spec["repair_attempt_name"] = config.name
    write_json(paths.spec_path, spec)
    validation = _build_validation(paths, design_summary, glb_report)
    validation["repair_attempt"] = config.index
    validation["repair_attempt_name"] = config.name
    validation["repair_loop"] = True
    result = ActuatorResult(
        actuator=REPAIR_ACTUATOR_NAME,
        status=design_summary["status"],
        part_id=PART_ID,
        decision_source=report_path(paths.character_package / "semantic_layer_v9_hair" / "primary_curve_bundle_v1.json"),
        generated_files={
            "spec": report_path(paths.spec_path),
            "obj": report_path(paths.obj_path),
            "mtl": report_path(paths.obj_path.with_suffix(".mtl")),
            "glb": report_path(paths.glb_path),
            "blend": report_path(paths.glb_path.with_suffix(".blend")),
            "report": report_path(paths.report_path),
            "coverage_mask": report_path(
                paths.output_dir / "coverage_masks" / f"curve_bundle_candidate_repair_attempt_{config.index:02d}_coverage_mask.png"
            ),
        },
        mesh_summary=_mesh_summary(ribbons, records, design_summary),
        validation=validation,
        warnings=warnings,
        errors=[],
    )
    contract_errors = validate_hair_candidate_report(result.to_dict())
    if contract_errors:
        result.errors.extend(contract_errors)
        if result.status == STATUS_MANUAL_REVIEW:
            result.status = STATUS_FAILED_VISUAL
    write_json(
        paths.report_path,
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "route": REPAIR_ROUTE,
            **result.to_dict(),
        },
    )
    return result


def schema_score(metrics: dict[str, Any]) -> float:
    fragmentation_penalty = max(0, int(metrics.get("component_count", 0)) - 16) * 0.01
    return round(
        float(metrics.get("candidate_soft_inside_ratio", 0.0))
        + float(metrics.get("candidate_core_coverage_ratio", 0.0))
        + float(metrics.get("candidate_visible_area_ratio", 0.0))
        - float(metrics.get("forbidden_candidate_leak_ratio", 1.0))
        - fragmentation_penalty,
        6,
    )


def attempt_passes_schema_gate(metrics: dict[str, Any]) -> bool:
    return (
        float(metrics.get("forbidden_candidate_leak_ratio", 1.0)) < 0.10
        and float(metrics.get("candidate_soft_inside_ratio", 0.0)) >= 0.70
        and float(metrics.get("candidate_core_coverage_ratio", 0.0)) >= 0.10
        and bool(metrics.get("candidate_front_visible_hair_mass"))
        and bool(metrics.get("primary_group_presence_passed"))
    )


def repair_report_summary(
    *,
    attempts: list[dict[str, Any]],
    best_attempt: dict[str, Any] | None,
    passed: bool,
) -> dict[str, Any]:
    if best_attempt is None:
        status = "repair_failed_after_6_attempts"
    elif passed:
        status = "schema_gate_passed_manual_review_required"
    else:
        status = "repair_failed_after_6_attempts"
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": REPAIR_ROUTE,
        "status": status,
        "attempt_count": len(attempts),
        "passed_schema_gate": passed,
        "best_attempt_index": best_attempt.get("attempt_index") if best_attempt else None,
        "best_attempt_metrics": best_attempt.get("metrics") if best_attempt else {},
        "attempts": attempts,
        "replacement_policy": {
            "replace_in_beauty_glb": False,
            "semantic_layer_v8_modified": False,
            "ready_for_cloth_seam_surface": False,
        },
        "failure_recommendation": None
        if passed
        else "manual curve edits required: move leaking ribbons into soft silhouette, reduce horizontal bars, and author scalp-anchored primary curves.",
    }
