from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


SCRIPT_NAME = "external_hair_prior_extraction_v0"
LIBRARY_VERSION = "external_hair_prior_library_v0.1"
REPORT_VERSION = "external_hair_prior_extraction_v0_report_v0.1"
SOURCE_IDS = ("opengameart_ponytail_female", "opengameart_long_male")


@dataclass(frozen=True)
class PriorExtractionPaths:
    repo_root: Path
    dataset_dir: Path
    probe_summary_path: Path
    priors_dir: Path
    reports_dir: Path
    prior_library_path: Path
    extraction_report_path: Path


def repo_root_from_file() -> Path:
    return Path(__file__).resolve().parents[2]


def default_paths(repo_root: Path) -> PriorExtractionPaths:
    dataset_dir = repo_root / "CharacterPackage" / "external_hair_dataset"
    return PriorExtractionPaths(
        repo_root=repo_root,
        dataset_dir=dataset_dir,
        probe_summary_path=dataset_dir / "probes" / "external_hair_intake_probe_v0_report.json",
        priors_dir=dataset_dir / "priors",
        reports_dir=dataset_dir / "reports",
        prior_library_path=dataset_dir / "priors" / "external_hair_prior_library_v0.json",
        extraction_report_path=dataset_dir / "reports" / "external_hair_prior_extraction_v0_report.json",
    )


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def rel(path: Path, repo_root: Path) -> str:
    return str(path.relative_to(repo_root))


def alpha_mask(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA").getchannel("A")


def count_nonzero(mask: Image.Image) -> int:
    return sum(1 for value in mask.getdata() if value > 0)


def normalized_bbox(mask: Image.Image) -> dict[str, Any]:
    width, height = mask.size
    bbox = mask.getbbox()
    if not bbox:
        return {
            "pixel_bbox": None,
            "normalized_bbox": None,
            "bbox_width_ratio": 0.0,
            "bbox_height_ratio": 0.0,
            "area_ratio": 0.0,
        }
    x0, y0, x1, y1 = bbox
    area = count_nonzero(mask)
    return {
        "pixel_bbox": [x0, y0, x1, y1],
        "normalized_bbox": [round(x0 / width, 6), round(y0 / height, 6), round(x1 / width, 6), round(y1 / height, 6)],
        "bbox_width_ratio": round((x1 - x0) / width, 6),
        "bbox_height_ratio": round((y1 - y0) / height, 6),
        "area_ratio": round(area / float(width * height), 6),
    }


def row_width(mask: Image.Image, y: int) -> int:
    width, _ = mask.size
    pixels = mask.load()
    xs = [x for x in range(width) if pixels[x, y] > 0]
    if not xs:
        return 0
    return max(xs) - min(xs) + 1


def width_samples(mask: Image.Image, sample_count: int = 7) -> list[dict[str, float]]:
    bbox = mask.getbbox()
    if not bbox:
        return []
    x0, y0, x1, y1 = bbox
    bbox_width = max(1, x1 - x0)
    samples: list[dict[str, float]] = []
    for index in range(sample_count):
        t = index / (sample_count - 1) if sample_count > 1 else 0
        y = int(round(y0 + t * max(0, y1 - y0 - 1)))
        samples.append({"t": round(t, 3), "width_ratio": round(row_width(mask, y) / bbox_width, 6)})
    return samples


def vertical_band_ratios(mask: Image.Image, band_count: int = 4) -> list[dict[str, float]]:
    bbox = mask.getbbox()
    if not bbox:
        return []
    x0, y0, x1, y1 = bbox
    total = max(1, count_nonzero(mask))
    pixels = mask.load()
    bands: list[dict[str, float]] = []
    for index in range(band_count):
        start = int(round(y0 + (y1 - y0) * index / band_count))
        end = int(round(y0 + (y1 - y0) * (index + 1) / band_count))
        band_area = 0
        for y in range(start, max(start + 1, end)):
            for x in range(x0, x1):
                if pixels[x, y] > 0:
                    band_area += 1
        bands.append({"band": index, "mass_ratio": round(band_area / total, 6)})
    return bands


def infer_taper(widths: list[dict[str, float]]) -> dict[str, Any]:
    if not widths:
        return {"family": "unknown", "root_width_ratio": 0.0, "mid_width_ratio": 0.0, "tip_width_ratio": 0.0}
    root = widths[0]["width_ratio"]
    mid = widths[len(widths) // 2]["width_ratio"]
    tip = widths[-1]["width_ratio"]
    if tip < root * 0.5 and mid >= root * 0.75:
        family = "stable_root_full_mid_tapered_tip"
    elif root > 0.8 and mid > 0.8 and tip > 0.6:
        family = "sheet_like_low_taper"
    else:
        family = "mixed_or_fragmented_taper"
    return {
        "family": family,
        "root_width_ratio": round(root, 6),
        "mid_width_ratio": round(mid, 6),
        "tip_width_ratio": round(tip, 6),
    }


def source_style_label(source_id: str) -> str:
    if source_id == "opengameart_ponytail_female":
        return "pony_tail_back_mass"
    if source_id == "opengameart_long_male":
        return "long_flat_curtain_sheet"
    return "generic_hair_reference"


def source_specific_hints(source_id: str, metrics: dict[str, Any]) -> dict[str, Any]:
    if source_id == "opengameart_ponytail_female":
        return {
            "scalp_anchor_hints": [
                {
                    "anchor": "scalp_crown",
                    "confidence": "medium",
                    "reason": "Front silhouette has compact crown mass and long descending tail.",
                },
                {
                    "anchor": "scalp_back_center",
                    "confidence": "medium",
                    "reason": "Side/yaw spread indicates rear-bundle depth useful for back_hair_mass priors.",
                },
            ],
            "primary_curve_hints": [
                {
                    "curve_family": "crown_to_low_back_vertical_bundle",
                    "semantic_group": "back_hair_mass",
                    "direction": "downward",
                    "copy_source_curve": False,
                    "use_as": "abstract flow and bundle-count prior only",
                }
            ],
            "suitability_for_yuna": {
                "score": 0.72,
                "useful_for": ["back_hair_mass", "scalp_crown_anchor", "long_bundle_depth"],
                "not_useful_for": ["bangs_primary", "side_hair_left_right_full_style"],
                "review_note": "Useful as a back-mass and ponytail/bundle prior, not as a direct YUNA silhouette.",
            },
        }
    if source_id == "opengameart_long_male":
        return {
            "scalp_anchor_hints": [
                {
                    "anchor": "scalp_crown",
                    "confidence": "medium",
                    "reason": "Broad top mass implies crown-to-curtain hair sheet organization.",
                },
                {
                    "anchor": "scalp_left_temple_and_right_temple",
                    "confidence": "low-medium",
                    "reason": "Front silhouette contains symmetrical side curtains that can inform side-lock coverage.",
                },
            ],
            "primary_curve_hints": [
                {
                    "curve_family": "crown_to_shoulder_curtain_sheet",
                    "semantic_group": "side_hair_left_right",
                    "direction": "downward_side_fall",
                    "copy_source_curve": False,
                    "use_as": "broad curtain mass prior only",
                }
            ],
            "suitability_for_yuna": {
                "score": 0.58,
                "useful_for": ["side_hair_mass", "soft_silhouette_fill", "sheet_width_negative_guard"],
                "not_useful_for": ["sci_fi_asymmetry", "cyan_accent_strands", "bangs_detail"],
                "review_note": "Useful for avoiding underfilled side hair, but unsafe if it becomes a flat wall.",
            },
        }
    return {"scalp_anchor_hints": [], "primary_curve_hints": [], "suitability_for_yuna": {"score": 0.0}}


def extract_source_prior(source_id: str, paths: PriorExtractionPaths) -> dict[str, Any]:
    probe_dir = paths.dataset_dir / "probes" / source_id
    report = read_json(probe_dir / "hair_reference_prior_report.json")
    front = alpha_mask(probe_dir / "front.png")
    yaw30 = alpha_mask(probe_dir / "yaw30.png")
    side = alpha_mask(probe_dir / "side.png")
    wire = alpha_mask(probe_dir / "wire.png")

    front_bbox = normalized_bbox(front)
    yaw_bbox = normalized_bbox(yaw30)
    side_bbox = normalized_bbox(side)
    wire_bbox = normalized_bbox(wire)
    widths = width_samples(front)
    taper = infer_taper(widths)
    bands = vertical_band_ratios(front)
    side_depth_ratio = round(side_bbox["bbox_width_ratio"] / max(0.0001, front_bbox["bbox_width_ratio"]), 6)
    yaw_spread_ratio = round(yaw_bbox["bbox_width_ratio"] / max(0.0001, front_bbox["bbox_width_ratio"]), 6)

    specific = source_specific_hints(source_id, {"front_bbox": front_bbox, "side_bbox": side_bbox})
    mesh_summary = report.get("blender_probe", {}).get("blender_summary", {})
    faces = mesh_summary.get("mesh_faces", 0)
    vertices = mesh_summary.get("mesh_vertices", 0)
    card_density = round(faces / max(1, front_bbox["area_ratio"] * 10000), 6) if front_bbox["area_ratio"] else 0.0

    return {
        "source_id": source_id,
        "source_name": report["source_name"],
        "source_url": report["source_url"],
        "representation_type": report.get("representation_classification", "classification_deferred"),
        "style_label": source_style_label(source_id),
        "source_probe_paths": {
            "front": rel(probe_dir / "front.png", paths.repo_root),
            "yaw30": rel(probe_dir / "yaw30.png", paths.repo_root),
            "side": rel(probe_dir / "side.png", paths.repo_root),
            "wire": rel(probe_dir / "wire.png", paths.repo_root),
            "alpha": rel(probe_dir / "alpha.png", paths.repo_root),
            "report": rel(probe_dir / "hair_reference_prior_report.json", paths.repo_root),
        },
        "image_metrics": {
            "front": front_bbox,
            "yaw30": yaw_bbox,
            "side": side_bbox,
            "wire": wire_bbox,
            "yaw_to_front_width_ratio": yaw_spread_ratio,
            "side_to_front_width_ratio": side_depth_ratio,
            "front_vertical_mass_bands": bands,
        },
        "scalp_anchor_hints": specific["scalp_anchor_hints"],
        "primary_curve_hints": specific["primary_curve_hints"],
        "width_profile_hints": {
            "samples_top_to_tip": widths,
            "recommended_use": "relative_width_profile_only",
            "do_not_use_as_exact_yuna_widths": True,
        },
        "taper_profile_hints": {
            **taper,
            "recommended_use": "choose taper family and avoid sparse needle fragments",
        },
        "depth_group_hints": {
            "suggested_depth_groups": ["front_or_crown_mass", "mid_side_or_tail", "rear_support_mass"],
            "side_to_front_width_ratio": side_depth_ratio,
            "yaw_to_front_width_ratio": yaw_spread_ratio,
            "side_back_are_soft_constraints": True,
        },
        "silhouette_mass_hints": {
            "front_area_ratio": front_bbox["area_ratio"],
            "front_bbox_height_ratio": front_bbox["bbox_height_ratio"],
            "front_bbox_width_ratio": front_bbox["bbox_width_ratio"],
            "vertical_mass_bands": bands,
            "recommended_use": "mass distribution and underfill/overfill guard only",
        },
        "card_topology_hints": {
            "mesh_vertices": vertices,
            "mesh_faces": faces,
            "has_alpha_material": bool(mesh_summary.get("has_alpha_material")),
            "card_density_hint": card_density,
            "topology_use": "infer card density and broad sheet risk; do not copy vertices/faces",
        },
        "suitability_for_yuna": specific["suitability_for_yuna"],
        "direct_copy_allowed": False,
        "do_not_copy_shape_directly": True,
        "contains_external_geometry": False,
        "contains_external_texture": False,
        "allowed_downstream_use": [
            "hair_design_schema_prior_notes",
            "curve_bundle_parameter_hints",
            "negative_fixture_reasoning",
        ],
        "forbidden_downstream_use": [
            "direct_yuna_geometry_import",
            "direct_texture_transfer",
            "v8_beauty_replacement",
            "cloth_unblock_signal",
        ],
    }


def build_combined_summary(source_priors: list[dict[str, Any]]) -> dict[str, Any]:
    useful = [
        "Use compact crown/back anchors from ponytail-like sources to strengthen back_hair_mass continuity.",
        "Use broad curtain-sheet references to prevent side hair underfill, but keep forbidden nonhair zones strict.",
        "Sample width/taper families as ratios, not copied card outlines.",
        "Use yaw30/side spread ratios as soft depth-group hints, never locked side/back truth.",
    ]
    unsafe = [
        "Do not copy the full ponytail or long flat curtain silhouette into YUNA.",
        "Do not convert broad sheet references into a flat hair wall.",
        "Do not treat low-poly source card topology as production-ready YUNA topology.",
        "Do not use external renders to override YUNA front identity or target-schema gates.",
    ]
    bundles = [
        {
            "bundle_id": "back_mass_crown_to_low_tail",
            "informed_by": ["opengameart_ponytail_female"],
            "anchors": ["scalp_crown", "scalp_back_center"],
            "intended_yuna_group": "back_hair_mass",
            "parameter_hint": "2-4 fuller downward mass ribbons plus secondary tapered strands",
        },
        {
            "bundle_id": "side_curtain_left_right_fill",
            "informed_by": ["opengameart_long_male"],
            "anchors": ["scalp_left_temple", "scalp_right_temple", "scalp_crown"],
            "intended_yuna_group": "side_hair_left_right",
            "parameter_hint": "medium-width side fall curves with stronger taper and anti-wall clipping",
        },
    ]
    return {
        "useful_prior_patterns": useful,
        "unsafe_or_style_mismatched_patterns": unsafe,
        "recommended_yuna_curve_bundle_hints": bundles,
        "next_goal_recommendation": (
            "Apply these priors to a schema/planner pass only: update hair design parameters or target notes, "
            "do not generate YUNA hair or proceed to cloth until manual review accepts the current hair route."
        ),
        "source_count": len(source_priors),
        "direct_copy_allowed": False,
        "ready_for_cloth_seam_surface": False,
    }


def build_prior_library(paths: PriorExtractionPaths) -> tuple[dict[str, Any], dict[str, Any]]:
    probe_summary = read_json(paths.probe_summary_path)
    source_priors = [extract_source_prior(source_id, paths) for source_id in SOURCE_IDS]
    combined = build_combined_summary(source_priors)
    library = {
        "library_version": LIBRARY_VERSION,
        "generated_at": now_iso(),
        "source_probe_report": rel(paths.probe_summary_path, paths.repo_root),
        "status": "prior_library_generated",
        "external_asset_usage": "prior_only",
        "replace_in_beauty_glb": False,
        "generated_yuna_hair": False,
        "cloth_seam_surface_blocked": True,
        "direct_copy_allowed": False,
        "sources": source_priors,
        "combined_prior_summary": combined,
    }
    report = {
        "report_version": REPORT_VERSION,
        "generated_at": library["generated_at"],
        "status": "prior_extraction_generated",
        "input_probe_status": probe_summary.get("status"),
        "input_source_ids": probe_summary.get("selected_source_ids", []),
        "output_prior_library": rel(paths.prior_library_path, paths.repo_root),
        "source_count": len(source_priors),
        "useful_prior_hint_count": sum(
            len(source["scalp_anchor_hints"])
            + len(source["primary_curve_hints"])
            + len(source["width_profile_hints"].get("samples_top_to_tip", []))
            for source in source_priors
        ),
        "guards": {
            "v8_immutable": True,
            "replace_in_beauty_glb": False,
            "external_asset_usage": "prior_only",
            "direct_copy_allowed": False,
            "generated_yuna_hair": False,
            "ready_for_cloth_seam_surface": False,
            "source_geometry_copied": False,
            "source_texture_copied": False,
        },
        "source_reports": [
            {
                "source_id": source["source_id"],
                "representation_type": source["representation_type"],
                "suitability_score": source["suitability_for_yuna"]["score"],
                "do_not_copy_shape_directly": source["do_not_copy_shape_directly"],
            }
            for source in source_priors
        ],
        "next_goal_recommendation": combined["next_goal_recommendation"],
    }
    return library, report


def run_extraction(paths: PriorExtractionPaths) -> dict[str, Any]:
    library, report = build_prior_library(paths)
    write_json(paths.prior_library_path, library)
    write_json(paths.extraction_report_path, report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract abstract external hair priors from probe outputs.")
    parser.add_argument("--repo-root", type=Path, default=repo_root_from_file())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = default_paths(args.repo_root.resolve())
    report = run_extraction(paths)
    print(json.dumps({"status": report["status"], "source_count": report["source_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
