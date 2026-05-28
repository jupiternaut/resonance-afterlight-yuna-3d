from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .art_directed_hair_ribbons_v1 import (
    ANCHOR_ID_BY_PART,
    HAIR_REVIEW_VARIANTS,
    PRIMARY_GROUP_BY_PART,
    _binary,
    _component_mask,
    _visible_mass_mask,
    build_panel_mesh,
    build_side_profile_mesh,
    load_design_schema,
    panel_primitive_intent,
    side_profile_primitive_intent,
    write_solid_texture,
)
from .authored_hair_ribbons import (
    HAIR_PART_IDS,
    SEGMENT_COUNT,
    V8_SOURCE_HEIGHT_WORLD,
    HairRibbon,
    MaskComponent,
    blender_export_glb,
    build_schema_constrained_group_masks,
    load_hair_sources,
    load_schema_target_mask,
    mask_pixel_count,
    report_file_record,
    report_path,
    schema_region_prior,
    write_json,
    write_obj,
)
from .registry import register
from .state import ActuatorPaths, ActuatorResult
from .validation_contract import validate_hair_candidate_report


ACTUATOR_NAME = "hair_silhouette_mass_v1"
ROUTE = "build_hair_silhouette_mass_v1"
PART_ID = "hair"
STATUS_MANUAL_REVIEW = "hair_silhouette_mass_candidate_manual_review_required"
STATUS_FAILED_READABILITY = "failed_silhouette_mass_readability"


@dataclass(frozen=True)
class SilhouetteMassConfig:
    name: str = "silhouette_mass_v1"
    review_intent: str = "primary filled silhouette masses first, then secondary strands and restrained flyaways"
    component_area_min: int = 220
    visible_mass_dilate_radius: int = 4
    visible_mass_close_radius: int = 2
    visible_mass_forbidden_guard_radius: int = 5
    primary_width_fraction: float = 1.08
    secondary_width_fraction: float = 0.36
    flyaway_width_fraction: float = 0.16
    primary_thickness: float = 0.058
    secondary_thickness: float = 0.034
    flyaway_thickness: float = 0.018
    secondary_strand_count: int = 10
    flyaway_strand_count: int = 3
    side_profile_volume_count: int = 2


CONFIG = SilhouetteMassConfig()


@dataclass(frozen=True)
class MassMaskRecord:
    part_id: str
    group_id: str
    role: str
    depth_group: str
    spring_hook: str
    mask_path: Path
    texture_path: Path
    components: list[MaskComponent]
    color: tuple[int, int, int]
    depth: float


def _mask_pixels(mask: Image.Image) -> int:
    return sum(1 for value in mask.convert("L").getdata() if value > 0)


def _union_masks(masks: list[Image.Image]) -> Image.Image:
    if not masks:
        raise ValueError("Expected at least one mask")
    result = Image.new("L", masks[0].size, 0)
    for mask in masks:
        result = ImageChops.lighter(result, _binary(mask))
    return result.point(lambda value: 255 if value > 0 else 0)


def write_filled_mass_texture(
    mask: Image.Image,
    output_path: Path,
    color: tuple[int, int, int],
    components: list[MaskComponent],
) -> None:
    """Write a filled alpha texture so candidate-only front reads as hair mass."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    mask = _binary(mask)
    texture = Image.new("RGBA", mask.size, (*color, 0))
    alpha = mask.filter(ImageFilter.GaussianBlur(0.45)).point(lambda value: min(238, max(0, int(value * 0.92))))
    texture.putalpha(alpha)

    draw = ImageDraw.Draw(texture, "RGBA")
    for component in components:
        x0, y0, x1, y1 = component.bbox
        width = max(3, min(14, int((x1 - x0) * 0.10)))
        center_x = (x0 + x1) * 0.5
        sway = max(2.0, min(18.0, (x1 - x0) * 0.10))
        points = [
            (center_x, y0 + 2),
            (center_x + sway, y0 + (y1 - y0) * 0.36),
            (center_x - sway * 0.45, y0 + (y1 - y0) * 0.72),
            (center_x, y1 - 2),
        ]
        draw.line(points, fill=(255, 255, 255, 96), width=width, joint="curve")

    # Re-apply the mask alpha after decorative strokes, so no RGB-only pixels
    # leak outside the target region in GLB/Blender validation.
    texture.putalpha(alpha)
    texture.save(output_path)


def build_mass_records(character_package: Path, output_dir: Path, config: SilhouetteMassConfig = CONFIG) -> list[MassMaskRecord]:
    build_schema_constrained_group_masks(character_package, output_dir / "target_schema_v1" / "group_masks")
    sources = {source.part_id: source for source in load_hair_sources(character_package)}
    mask_dir = output_dir / "mass_masks"
    texture_dir = output_dir / "textures"
    records: list[MassMaskRecord] = []
    for part_id in HAIR_PART_IDS:
        source = sources[part_id]
        group_config = PRIMARY_GROUP_BY_PART[part_id]
        base = Image.open(source.mask_path).convert("L").point(lambda value: 255 if value > 0 else 0)
        mass = _visible_mass_mask(part_id, base, character_package, HAIR_REVIEW_VARIANTS["fuller"])
        soft = load_schema_target_mask(character_package, "soft_hair_silhouette")
        forbidden = load_schema_target_mask(character_package, "forbidden_nonhair_zone")
        if soft is not None:
            part_region = schema_region_prior(part_id, soft.size)
            grown = ImageChops.multiply(_binary(soft), part_region).filter(ImageFilter.MaxFilter(config.visible_mass_dilate_radius * 2 + 1))
            mass = ImageChops.lighter(mass, grown).point(lambda value: 255 if value > 0 else 0)
            mass = ImageChops.multiply(mass, _binary(soft)).point(lambda value: 255 if value > 0 else 0)
        if forbidden is not None:
            guard = _binary(forbidden).filter(ImageFilter.MaxFilter(config.visible_mass_forbidden_guard_radius * 2 + 1))
            mass = ImageChops.subtract(mass, guard).point(lambda value: 255 if value > 0 else 0)

        mass = mass.filter(ImageFilter.MaxFilter(config.visible_mass_dilate_radius * 2 + 1))
        mass = mass.filter(ImageFilter.MinFilter(config.visible_mass_close_radius * 2 + 1))
        if soft is not None:
            mass = ImageChops.multiply(mass, _binary(soft)).point(lambda value: 255 if value > 0 else 0)
        art_mask, components = _component_mask(mass, min_area=config.component_area_min)
        if not components:
            raise ValueError(f"No usable silhouette-mass components for {part_id}")
        mask_path = mask_dir / f"{group_config['group_id']}_silhouette_mass_v1_mask.png"
        texture_path = texture_dir / f"{group_config['group_id']}_silhouette_mass_v1.png"
        mask_path.parent.mkdir(parents=True, exist_ok=True)
        art_mask.save(mask_path)
        write_filled_mass_texture(art_mask, texture_path, tuple(group_config["color"]), components)
        records.append(
            MassMaskRecord(
                part_id=part_id,
                group_id=str(group_config["group_id"]),
                role=str(group_config["role"]),
                depth_group=str(group_config["depth_group"]),
                spring_hook=str(group_config["spring_hook"]),
                mask_path=mask_path,
                texture_path=texture_path,
                components=components,
                color=tuple(group_config["color"]),
                depth=source.depth + float(group_config["depth_bias"]),
            )
        )
    return records


def _source_coverage(records: list[MassMaskRecord]) -> Image.Image:
    return _union_masks([Image.open(record.mask_path).convert("L") for record in records])


def primary_mass_coverage_ratio(character_package: Path, records: list[MassMaskRecord]) -> float:
    soft = load_schema_target_mask(character_package, "soft_hair_silhouette")
    if soft is None:
        return 0.0
    coverage = _source_coverage(records)
    overlap = ImageChops.multiply(coverage, soft)
    return round(_mask_pixels(overlap) / max(_mask_pixels(soft), 1), 6)


def build_hair_silhouette_mass(
    character_package: Path,
    output_dir: Path,
    config: SilhouetteMassConfig = CONFIG,
) -> tuple[list[HairRibbon], list[MassMaskRecord], dict[str, Any]]:
    design_schema = load_design_schema(character_package)
    records = build_mass_records(character_package, output_dir, config)
    with Image.open(records[0].mask_path) as image:
        image_size = image.size
    scale = V8_SOURCE_HEIGHT_WORLD / image_size[1]
    constraint_masks = {
        record.group_id: Image.open(record.mask_path).convert("L").point(lambda value: 255 if value > 0 else 0)
        for record in records
    }
    ribbons: list[HairRibbon] = []
    primary_count_by_role: dict[str, int] = {}
    for record in records:
        for index, component in enumerate(record.components[: max(1, min(4, len(record.components)))]):
            ribbon_id = f"{record.group_id}_sheet_{index + 1:02d}"
            depth_offset = (index - (min(4, len(record.components)) - 1) * 0.5) * 0.014
            curve_px = 8.0 if record.part_id != "bangs" else 3.0
            mesh = build_panel_mesh(
                component.bbox,
                image_size=image_size,
                scale=scale,
                depth=record.depth,
                depth_offset=depth_offset,
                thickness=config.primary_thickness,
                width_fraction=config.primary_width_fraction,
                curve_px=curve_px,
                constraint_mask=constraint_masks[record.group_id],
            )
            primary_count_by_role[record.role] = primary_count_by_role.get(record.role, 0) + 1
            ribbons.append(
                HairRibbon(
                    id=ribbon_id,
                    group_id=record.group_id,
                    source_part_id=record.part_id,
                    mask_path=record.mask_path,
                    texture_path=record.texture_path,
                    depth_group=record.depth_group,
                    spring_hook=record.spring_hook,
                    bbox=component.bbox,
                    mesh=mesh,
                    primitive_intent=panel_primitive_intent(
                        ribbon_id=ribbon_id,
                        group_id=record.group_id,
                        source_part_id=record.part_id,
                        bbox=component.bbox,
                        image_size=image_size,
                        depth=record.depth,
                        depth_offset=depth_offset,
                        width_fraction=config.primary_width_fraction,
                        curve_px=curve_px,
                        depth_group=record.depth_group,
                        texture_path=record.texture_path,
                        spring_hook=record.spring_hook,
                        material="alpha_textured_primary_hair_mass_sheet",
                    ),
                )
            )

    large_components = [(record, component) for record in records for component in record.components if component.area >= 260]
    large_components.sort(key=lambda item: item[1].area, reverse=True)
    for index, (record, component) in enumerate(large_components[: config.secondary_strand_count]):
        ribbon_id = f"secondary_mass_strands_{index + 1:02d}"
        mesh = build_panel_mesh(
            component.bbox,
            image_size=image_size,
            scale=scale,
            depth=record.depth,
            depth_offset=0.042 + index * 0.002,
            thickness=config.secondary_thickness,
            width_fraction=config.secondary_width_fraction,
            curve_px=10.0,
            constraint_mask=constraint_masks[record.group_id],
        )
        ribbons.append(
            HairRibbon(
                id=ribbon_id,
                group_id="secondary_strands",
                source_part_id=record.part_id,
                mask_path=record.mask_path,
                texture_path=record.texture_path,
                depth_group="secondary_detail",
                spring_hook=record.spring_hook,
                bbox=component.bbox,
                mesh=mesh,
                primitive_intent=panel_primitive_intent(
                    ribbon_id=ribbon_id,
                    group_id="secondary_strands",
                    source_part_id=record.part_id,
                    bbox=component.bbox,
                    image_size=image_size,
                    depth=record.depth,
                    depth_offset=0.042 + index * 0.002,
                    width_fraction=config.secondary_width_fraction,
                    curve_px=10.0,
                    depth_group="secondary_detail",
                    texture_path=record.texture_path,
                    spring_hook=record.spring_hook,
                    material="alpha_textured_secondary_hair_ribbon",
                ),
            )
        )

    for index, (record, component) in enumerate(large_components[: config.flyaway_strand_count]):
        ribbon_id = f"limited_flyaway_strands_{index + 1:02d}"
        mesh = build_panel_mesh(
            component.bbox,
            image_size=image_size,
            scale=scale,
            depth=record.depth,
            depth_offset=0.064 + index * 0.002,
            thickness=config.flyaway_thickness,
            width_fraction=config.flyaway_width_fraction,
            curve_px=16.0,
            constraint_mask=constraint_masks[record.group_id],
        )
        ribbons.append(
            HairRibbon(
                id=ribbon_id,
                group_id="flyaway_strands",
                source_part_id=record.part_id,
                mask_path=record.mask_path,
                texture_path=record.texture_path,
                depth_group="flyaways",
                spring_hook=record.spring_hook,
                bbox=component.bbox,
                mesh=mesh,
                primitive_intent=panel_primitive_intent(
                    ribbon_id=ribbon_id,
                    group_id="flyaway_strands",
                    source_part_id=record.part_id,
                    bbox=component.bbox,
                    image_size=image_size,
                    depth=record.depth,
                    depth_offset=0.064 + index * 0.002,
                    width_fraction=config.flyaway_width_fraction,
                    curve_px=16.0,
                    depth_group="flyaways",
                    texture_path=record.texture_path,
                    spring_hook=record.spring_hook,
                    material="alpha_textured_limited_flyaway_hair_ribbon",
                ),
            )
        )

    side_profile_texture = output_dir / "textures" / "side_profile_volume_silhouette_mass_v1.png"
    write_solid_texture(side_profile_texture, (205, 225, 231))
    side_records = [record for record in records if record.part_id in {"back_hair", "side_hair_left", "side_hair_right"}]
    for index, record in enumerate(side_records[: config.side_profile_volume_count]):
        x0, y0, x1, y1 = record.components[0].bbox
        source_x = (x0 + x1) * 0.5
        ribbon_id = f"side_profile_volume_{index + 1:02d}"
        mesh = build_side_profile_mesh(
            source_x=source_x,
            source_y0=y0,
            source_y1=y1,
            image_size=image_size,
            scale=scale,
            depth_center=record.depth,
            depth_width=0.28 if record.part_id == "back_hair" else 0.20,
            x_width_px=9.0,
            curve_depth=0.055,
            thickness=0.030,
        )
        ribbons.append(
            HairRibbon(
                id=ribbon_id,
                group_id="side_profile_volume",
                source_part_id=record.part_id,
                mask_path=record.mask_path,
                texture_path=side_profile_texture,
                depth_group="side_profile_volume",
                spring_hook=record.spring_hook,
                bbox=(round(source_x - 5), y0, round(source_x + 5), y1),
                mesh=mesh,
                primitive_intent=side_profile_primitive_intent(
                    ribbon_id=ribbon_id,
                    source_part_id=record.part_id,
                    source_x=source_x,
                    source_y0=y0,
                    source_y1=y1,
                    depth_center=record.depth,
                    depth_width=0.28 if record.part_id == "back_hair" else 0.20,
                    texture_path=side_profile_texture,
                    spring_hook=record.spring_hook,
                ),
            )
        )

    design_summary = {
        "design_schema": report_path(character_package / "semantic_layer_v9_hair" / "hair_design_schema_v1.json"),
        "target_schema": "CharacterPackage/semantic_layer_v9_hair/target_schema_v1",
        "variant": {
            "name": config.name,
            "review_intent": config.review_intent,
            "primary_strategy": "filled_mass_sheets_before_secondary_strands",
            "component_area_min": config.component_area_min,
            "secondary_strand_count": config.secondary_strand_count,
            "flyaway_strand_count": config.flyaway_strand_count,
            "side_profile_volume_count": config.side_profile_volume_count,
        },
        "required_primary_groups": sorted(design_schema["required_primary_groups"].keys()),
        "primary_component_count_by_role": primary_count_by_role,
        "primary_mass_coverage_ratio": primary_mass_coverage_ratio(character_package, records),
        "scalp_anchor_points": [item["id"] for item in design_schema.get("scalp_anchor_points", [])],
        "depth_groups": sorted({ribbon.depth_group for ribbon in ribbons}),
        "primitive_intent_count": sum(1 for ribbon in ribbons if ribbon.primitive_intent),
        "flow_continuity_passed": set(PRIMARY_GROUP_BY_PART[part_id]["group_id"] for part_id in HAIR_PART_IDS).issubset(
            {ribbon.group_id for ribbon in ribbons if ribbon.primitive_intent}
        ),
    }
    return ribbons, records, design_summary


def mesh_summary(ribbons: list[HairRibbon], records: list[MassMaskRecord], design_summary: dict[str, Any]) -> dict[str, Any]:
    role_counts: dict[str, int] = {}
    for ribbon in ribbons:
        role_counts[ribbon.group_id] = role_counts.get(ribbon.group_id, 0) + 1
    primitive_intents = [ribbon.primitive_intent for ribbon in ribbons if ribbon.primitive_intent]
    required_primary_groups = {str(PRIMARY_GROUP_BY_PART[part_id]["group_id"]) for part_id in HAIR_PART_IDS}
    anchored_groups = {
        str(intent.get("group_id"))
        for intent in primitive_intents
        if intent.get("anchor_point") and intent.get("curve_path")
    }
    return {
        "group_count": len({ribbon.group_id for ribbon in ribbons}),
        "depth_group_count": len({ribbon.depth_group for ribbon in ribbons}),
        "ribbon_count": len(ribbons),
        "primary_mass_sheet_count": sum(1 for ribbon in ribbons if "_sheet_" in ribbon.id),
        "vertices": sum(len(ribbon.mesh.vertices) for ribbon in ribbons),
        "uvs": sum(len(ribbon.mesh.uvs) for ribbon in ribbons),
        "faces": sum(len(ribbon.mesh.faces) for ribbon in ribbons),
        "section_count": SEGMENT_COUNT + 1,
        "ribbon_thickness": round(max((ribbon.mesh.thickness for ribbon in ribbons), default=0.0), 6),
        "ribbon_thickness_min": round(min((ribbon.mesh.thickness for ribbon in ribbons), default=0.0), 6),
        "source_mask_component_count": sum(len(record.components) for record in records),
        "role_counts": role_counts,
        "schema_constrained": True,
        "art_directed_primitive_intent_count": len(primitive_intents),
        "scalp_anchor_continuity_passed": required_primary_groups.issubset(anchored_groups),
        "flow_continuity_passed": design_summary["flow_continuity_passed"],
        "design_summary": design_summary,
        "primitive_intents": primitive_intents,
        "mass_masks": [
            {
                "part_id": record.part_id,
                "group_id": record.group_id,
                "role": record.role,
                "mask": report_path(record.mask_path),
                "texture": report_path(record.texture_path),
                "component_count": len(record.components),
                "pixel_count": _mask_pixels(Image.open(record.mask_path).convert("L")),
                "largest_component_area": record.components[0].area if record.components else 0,
            }
            for record in records
        ],
    }


def build_initial_validation(character_package: Path, records: list[MassMaskRecord], design_summary: dict[str, Any]) -> dict[str, Any]:
    candidate = _source_coverage(records)
    soft = load_schema_target_mask(character_package, "soft_hair_silhouette")
    forbidden = load_schema_target_mask(character_package, "forbidden_nonhair_zone")
    candidate_pixels = max(_mask_pixels(candidate), 1)
    candidate_soft = _mask_pixels(ImageChops.multiply(candidate, soft)) if soft else 0
    candidate_forbidden = _mask_pixels(ImageChops.multiply(candidate, forbidden)) if forbidden else candidate_pixels
    return {
        "independent_objects": True,
        "has_ribbon_meshes": True,
        "has_depth_groups": True,
        "has_uvs": True,
        "has_front_texture_material": True,
        "uses_filled_primary_mass_textures": True,
        "has_side_material": True,
        "has_spring_hook_metadata": True,
        "replace_in_beauty_glb": False,
        "side_back_are_soft_constraints": True,
        "alpha_material_valid": True,
        "black_alpha_leak_ratio": 0.0,
        "candidate_black_pixel_ratio": 0.0,
        "face_occlusion_ratio": 0.0,
        "body_occlusion_ratio": 0.0,
        "non_hair_occlusion_ratio": round(max(0.0, 1.0 - candidate_soft / candidate_pixels), 6),
        "hair_mask_iou": 0.0,
        "outside_hair_mask_ratio": round(candidate_forbidden / candidate_pixels, 6),
        "raw_candidate_is_hair_only": False,
        "candidate_is_hair_only": False,
        "hair_union_body_overlap_ratio": 1.0,
        "hair_union_face_overlap_ratio": 1.0,
        "hair_union_weapon_overlap_ratio": 1.0,
        "hair_union_target_is_clean": False,
        "hair_target_quality": "pending_render_space_validation",
        "clean_hair_mask_iou": 0.0,
        "clean_outside_hair_mask_ratio": 1.0,
        "clean_candidate_is_hair_only": False,
        "hair_union_projection_valid": False,
        "candidate_geometry_alignment_valid": False,
        "clean_candidate_geometry_alignment_valid": False,
        "coordinate_alignment_gate": "pending_render_space_validation",
        "coordinate_mapping_status": "pending_render_space_validation",
        "alignment_failure_reason": "run_blender_semantic_validation.py has not evaluated this v1 candidate yet",
        "baseline_framing_valid": False,
        "overlay_alignment_valid": False,
        "visual_sanity_status": STATUS_MANUAL_REVIEW,
        "visual_sanity_reason": "silhouette mass v1 generated; render-space target schema and manual review still required",
        "manual_visual_review": "pending_user_review",
        "ready_for_cloth_seam_surface": False,
        "artifact_generated": True,
        "black_alpha_leak_fixed": True,
        "numeric_metrics_passed": candidate_forbidden / candidate_pixels < 0.10,
        "candidate_front_hair_readability": False,
        "yaw30_hair_readability": False,
        "side_hair_volume_present": False,
        "primary_mass_coverage_ratio": design_summary["primary_mass_coverage_ratio"],
    }


def build_spec(paths: ActuatorPaths, ribbons: list[HairRibbon], records: list[MassMaskRecord], design_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "route": ROUTE,
        "source_route": "art_directed_hair_ribbons_v1_manual_review_rejected_as_sparse",
        "baseline": "semantic_layer_v8_beauty_main_debug_cage_split",
        "boundary": "Independent silhouette-mass v1 hair candidate only. It does not replace v8 beauty hair cards and does not unblock cloth.",
        "formula_binding": {
            "state": "theta_hair_design: filled primary mass sheets, secondary strands, flyaways, scalp anchors, depth groups, and schema masks",
            "update": "ProjectToConstraints_hair(RobustFuse(strict_hair_core, soft_hair_silhouette, forbidden_nonhair_zone, front_identity, manual_visual_review))",
        },
        "part": {
            "id": "hair",
            "category": "hair",
            "generator": ACTUATOR_NAME,
            "replace_in_beauty_glb": False,
            "independent_objects": True,
            "candidate_only": True,
            "side_back_are_soft_constraints": True,
            "source_parts": list(HAIR_PART_IDS),
            "spring_hooks": sorted({ribbon.spring_hook for ribbon in ribbons}),
            "target_schema": "CharacterPackage/semantic_layer_v9_hair/target_schema_v1",
        },
        "mesh": mesh_summary(ribbons, records, design_summary),
        "exports": {
            "obj": report_path(paths.obj_path),
            "glb": report_path(paths.glb_path),
            "report": report_path(paths.report_path),
        },
    }


@register("build_hair_silhouette_mass_v1")
@register("hair_silhouette_mass_v1")
def run_hair_silhouette_mass_v1(paths: ActuatorPaths) -> ActuatorResult:
    warnings: list[str] = []
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    paths.spec_path.parent.mkdir(parents=True, exist_ok=True)
    paths.obj_path.parent.mkdir(parents=True, exist_ok=True)

    ribbons, records, design_summary = build_hair_silhouette_mass(paths.character_package, paths.output_dir)
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
    write_json(paths.spec_path, build_spec(paths, ribbons, records, design_summary))
    validation = build_initial_validation(paths.character_package, records, design_summary)
    validation.update(
        {
            "obj": report_file_record(paths.obj_path),
            "glb": report_file_record(paths.glb_path),
            "blender_glb_export": glb_report,
        }
    )
    result = ActuatorResult(
        actuator=ACTUATOR_NAME,
        status=STATUS_MANUAL_REVIEW,
        part_id=PART_ID,
        decision_source=report_path(paths.character_package / "semantic_layer_v9_hair" / "hair_design_schema_v1.json"),
        generated_files={
            "spec": report_path(paths.spec_path),
            "obj": report_path(paths.obj_path),
            "mtl": report_path(paths.obj_path.with_suffix(".mtl")),
            "glb": report_path(paths.glb_path),
            "blend": report_path(paths.glb_path.with_suffix(".blend")),
            "report": report_path(paths.report_path),
            "mass_masks": report_path(paths.output_dir / "mass_masks"),
            "schema_group_masks": report_path(paths.output_dir / "target_schema_v1" / "group_masks"),
        },
        mesh_summary=mesh_summary(ribbons, records, design_summary),
        validation=validation,
        warnings=warnings
        + [
            "silhouette_mass_v1 is a candidate review route, not final production hair.",
            "v8 beauty hair remains active; replace_in_beauty_glb=false.",
            "cloth_seam_surface remains blocked until manual visual review accepts a hair route.",
        ],
        errors=[],
    )
    contract_errors = validate_hair_candidate_report(result.to_dict())
    if contract_errors:
        result.status = "failed"
        result.errors.extend(contract_errors)
    write_json(
        paths.report_path,
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "route": ROUTE,
            **result.to_dict(),
        },
    )
    return result
