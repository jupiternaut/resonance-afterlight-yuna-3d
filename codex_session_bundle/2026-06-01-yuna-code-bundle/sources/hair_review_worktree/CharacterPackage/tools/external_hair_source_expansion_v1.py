from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_NAME = "external_hair_source_expansion_v1"
REPORT_VERSION = "external_hair_source_expansion_v1_report_v0.1"


@dataclass(frozen=True)
class SourceExpansionPaths:
    repo_root: Path
    dataset_dir: Path
    manifest_path: Path
    triage_path: Path
    readme_path: Path
    reports_dir: Path
    expansion_report_path: Path
    project_state_path: Path
    next_goal_path: Path
    chatgpt_handoff_path: Path


def repo_root_from_file() -> Path:
    return Path(__file__).resolve().parents[2]


def default_paths(repo_root: Path) -> SourceExpansionPaths:
    dataset_dir = repo_root / "CharacterPackage" / "external_hair_dataset"
    candidate_dir = repo_root / "CharacterPackage" / "semantic_layer_v9_candidate"
    return SourceExpansionPaths(
        repo_root=repo_root,
        dataset_dir=dataset_dir,
        manifest_path=dataset_dir / "assets_manifest.json",
        triage_path=dataset_dir / "SOURCE_TRIAGE.md",
        readme_path=dataset_dir / "README.md",
        reports_dir=dataset_dir / "reports",
        expansion_report_path=dataset_dir / "reports" / "external_hair_source_expansion_v1_report.json",
        project_state_path=candidate_dir / "PROJECT_STATE.md",
        next_goal_path=candidate_dir / "NEXT_GOAL.md",
        chatgpt_handoff_path=candidate_dir / "CHATGPT_HANDOFF.md",
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


def source_quality(
    *,
    usage_role: str,
    representation_type: str,
    quality_score: float,
    style_relevance_to_yuna: float,
    has_bangs: bool,
    has_side_hair: bool,
    has_back_hair_mass: bool,
    has_scalp_anchor_structure: bool,
    has_hair_cards_or_curves: bool,
    can_extract_curve_templates: str,
    source_class: str,
    prior_quality: str,
    next_intake_priority: str,
    high_priority_for_next_intake: bool,
    notes: list[str],
) -> dict[str, Any]:
    return {
        "usage_role": usage_role,
        "representation_type": representation_type,
        "quality_score": quality_score,
        "style_relevance_to_yuna": style_relevance_to_yuna,
        "has_bangs": has_bangs,
        "has_side_hair": has_side_hair,
        "has_back_hair_mass": has_back_hair_mass,
        "has_scalp_anchor_structure": has_scalp_anchor_structure,
        "has_hair_cards_or_curves": has_hair_cards_or_curves,
        "can_extract_curve_templates": can_extract_curve_templates,
        "source_class": source_class,
        "prior_quality": prior_quality,
        "next_intake_priority": next_intake_priority,
        "high_priority_for_next_intake": high_priority_for_next_intake,
        "notes": notes,
    }


def source_entry(
    *,
    source_id: str,
    source_url: str,
    source_name: str,
    claimed_license: str,
    license_confidence: str,
    possible_usage_role: str,
    can_commit_binary_to_repo: str,
    can_commit_renders: str,
    can_extract_curve_templates: str,
    recommendation: str,
    intake_status: str,
    validation_reason: str,
    notes: list[str],
    quality: dict[str, Any],
    verification_sources: list[str],
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "source_url": source_url,
        "source_name": source_name,
        "claimed_license": claimed_license,
        "license_confidence": license_confidence,
        "possible_usage_role": possible_usage_role,
        "can_commit_binary_to_repo": can_commit_binary_to_repo,
        "can_commit_renders": can_commit_renders,
        "can_extract_curve_templates": can_extract_curve_templates,
        "recommendation": recommendation,
        "intake_status": intake_status,
        "external_asset_usage": "prior_only",
        "replace_in_beauty_glb": False,
        "download_status": "not_downloaded",
        "validation_status": {"status": "skipped", "skipped_with_reason": validation_reason},
        "notes": notes,
        "source_quality_v1": quality,
        "verification_sources_v1": verification_sources,
    }


CURATED_SOURCE_UPDATES: dict[str, dict[str, Any]] = {
    "opengameart_ponytail_female": {
        "source_quality_v1": source_quality(
            usage_role="Existing probe retained as a low-poly ponytail/back-mass prior, not a quality target.",
            representation_type="solid_lowpoly_hair_mesh",
            quality_score=0.48,
            style_relevance_to_yuna=0.42,
            has_bangs=False,
            has_side_hair=False,
            has_back_hair_mass=True,
            has_scalp_anchor_structure=True,
            has_hair_cards_or_curves=False,
            can_extract_curve_templates="yes_from_mesh_centerlines",
            source_class="existing_probe_low_medium_prior",
            prior_quality="medium_low",
            next_intake_priority="low",
            high_priority_for_next_intake=False,
            notes=[
                "Useful as a back-bundle silhouette and scalp-anchor negative/contrast prior.",
                "Too low-poly/simple to be a premium YUNA hair target.",
            ],
        ),
        "verification_sources_v1": [
            "https://opengameart.org/content/ponytail-hair-style-for-female-model",
            "https://creativecommons.org/publicdomain/zero/1.0/",
        ],
    },
    "opengameart_long_male": {
        "source_quality_v1": source_quality(
            usage_role="Existing probe retained as a low/medium strip-hair and sheet-risk prior.",
            representation_type="lowpoly_hair_cards_or_strips",
            quality_score=0.44,
            style_relevance_to_yuna=0.38,
            has_bangs=False,
            has_side_hair=True,
            has_back_hair_mass=True,
            has_scalp_anchor_structure=True,
            has_hair_cards_or_curves=True,
            can_extract_curve_templates="yes_from_mesh_centerlines",
            source_class="existing_probe_low_medium_prior",
            prior_quality="medium_low",
            next_intake_priority="low",
            high_priority_for_next_intake=False,
            notes=[
                "Useful mainly as a failure-boundary example for broad flat strips.",
                "The source itself notes alpha texture trouble, so it should not guide material quality.",
            ],
        ),
        "verification_sources_v1": [
            "https://opengameart.org/content/long-hairstyle-for-male-model",
            "https://creativecommons.org/publicdomain/zero/1.0/",
        ],
    },
    "opengameart_hair_alphas_for_days": {
        "source_quality_v1": source_quality(
            usage_role="Hair alpha/material fixture source for card transparency and strand texture tests.",
            representation_type="hair_alpha_material_pack",
            quality_score=0.76,
            style_relevance_to_yuna=0.62,
            has_bangs=False,
            has_side_hair=False,
            has_back_hair_mass=False,
            has_scalp_anchor_structure=False,
            has_hair_cards_or_curves=False,
            can_extract_curve_templates="no_texture_only",
            source_class="open_material_prior",
            prior_quality="medium_high",
            next_intake_priority="high",
            high_priority_for_next_intake=True,
            notes=[
                "Strong alpha/material sanity source, but no geometry or scalp anchors.",
                "Future intake should select a few small PNGs only, not commit the full 138.5 MB archive.",
            ],
        ),
        "verification_sources_v1": [
            "https://opengameart.org/content/hair-alphas-for-days",
            "https://creativecommons.org/publicdomain/zero/1.0/",
        ],
    },
    "opengameart_vroid_cc0_samples": {
        "source_quality_v1": source_quality(
            usage_role="Umbrella source for VRoid CC0 anime/stylized hair sample intake.",
            representation_type="vroid_vrm_hair_cards_or_meshes",
            quality_score=0.84,
            style_relevance_to_yuna=0.88,
            has_bangs=True,
            has_side_hair=True,
            has_back_hair_mass=True,
            has_scalp_anchor_structure=True,
            has_hair_cards_or_curves=True,
            can_extract_curve_templates="yes_after_import_verification",
            source_class="open_anime_template_source",
            prior_quality="high",
            next_intake_priority="high",
            high_priority_for_next_intake=True,
            notes=[
                "Prefer explicit HairSample_Female and HairSample_Male files, not restricted AvatarSample A-C.",
                "VRM import verification is required before any committed render or derived prior.",
            ],
        ),
        "verification_sources_v1": [
            "https://opengameart.org/content/vroid-studio-cc0-models",
            "https://vroid.pixiv.help/hc/en-us/articles/4402614652569-Do-VRoid-Studio-s-sample-models-come-with-conditions-of-use",
        ],
    },
    "blendswap_curly_hair": {
        "source_quality_v1": source_quality(
            usage_role="Bezier-curve curl and curve-width template prior.",
            representation_type="curve_hair",
            quality_score=0.78,
            style_relevance_to_yuna=0.58,
            has_bangs=False,
            has_side_hair=True,
            has_back_hair_mass=True,
            has_scalp_anchor_structure=False,
            has_hair_cards_or_curves=True,
            can_extract_curve_templates="yes_curve_templates",
            source_class="open_curve_template_source",
            prior_quality="medium_high",
            next_intake_priority="high",
            high_priority_for_next_intake=True,
            notes=[
                "Small CC0 Bezier-curve source; good for curve extraction tests.",
                "Style is curly rather than YUNA-specific, so use as geometry parameter prior only.",
            ],
        ),
        "verification_sources_v1": [
            "https://blendswap.com/blend/24481",
            "https://creativecommons.org/publicdomain/zero/1.0/",
        ],
    },
    "blendswap_braided_hair": {
        "source_quality_v1": source_quality(
            usage_role="Braid topology and repeated interleaved-strand prior.",
            representation_type="ribbon_or_solid_braid_mesh",
            quality_score=0.66,
            style_relevance_to_yuna=0.36,
            has_bangs=False,
            has_side_hair=False,
            has_back_hair_mass=True,
            has_scalp_anchor_structure=False,
            has_hair_cards_or_curves=True,
            can_extract_curve_templates="yes_from_mesh_or_modifiers",
            source_class="open_topology_reference",
            prior_quality="medium",
            next_intake_priority="medium",
            high_priority_for_next_intake=False,
            notes=[
                "Useful for repeated strand topology and taper patterns.",
                "Not a close YUNA silhouette match.",
            ],
        ),
        "verification_sources_v1": [
            "https://blendswap.com/blend/18823",
            "https://creativecommons.org/publicdomain/zero/1.0/",
        ],
    },
    "blender_studio_sintel_rig": {
        "source_quality_v1": source_quality(
            usage_role="Reference-only long-hair organization and DCC rig/handoff study.",
            representation_type="open_movie_character_hair_reference",
            quality_score=0.79,
            style_relevance_to_yuna=0.64,
            has_bangs=True,
            has_side_hair=True,
            has_back_hair_mass=True,
            has_scalp_anchor_structure=True,
            has_hair_cards_or_curves=True,
            can_extract_curve_templates="yes_with_attribution_if_separable",
            source_class="cc_by_reference_report_only",
            prior_quality="medium_high",
            next_intake_priority="medium",
            high_priority_for_next_intake=False,
            notes=[
                "Good for DCC organization and long hair reference, but attribution and full-rig size make it non-first-intake.",
                "Keep as reference report only until attribution and file scope are explicit.",
            ],
        ),
        "verification_sources_v1": ["https://studio.blender.org/characters/5d41a32b8307e9cd1023fa78/v2/"],
    },
    "blender_studio_spring_rig": {
        "source_quality_v1": source_quality(
            usage_role="Reference-only stylized hair mass and rig organization study.",
            representation_type="open_movie_stylized_hair_reference",
            quality_score=0.83,
            style_relevance_to_yuna=0.72,
            has_bangs=True,
            has_side_hair=True,
            has_back_hair_mass=True,
            has_scalp_anchor_structure=True,
            has_hair_cards_or_curves=True,
            can_extract_curve_templates="yes_with_attribution_if_separable",
            source_class="cc_by_reference_report_only",
            prior_quality="medium_high",
            next_intake_priority="medium",
            high_priority_for_next_intake=False,
            notes=[
                "Useful visual/DCC reference for stylized silhouette mass.",
                "Do not use as direct template without attribution review and separability check.",
            ],
        ),
        "verification_sources_v1": ["https://studio.blender.org/characters/spring/v1/"],
    },
}


NEW_CURATED_SOURCES: list[dict[str, Any]] = [
    source_entry(
        source_id="vroid_hairsample_female_cc0",
        source_url="https://opengameart.org/content/vroid-studio-cc0-models",
        source_name="VRoid Studio CC0 HairSample_Female",
        claimed_license="CC0 for HairSample_Female per VRoid FAQ and OpenGameArt mirror",
        license_confidence="high",
        possible_usage_role="High-priority anime/stylized female hair sample for scalp anchors, bangs, side hair, and back mass priors.",
        can_commit_binary_to_repo="yes_selected_cc0_files_after_review",
        can_commit_renders="yes_selected_cc0_files",
        can_extract_curve_templates="yes_after_import_verification",
        recommendation="open_template_source",
        intake_status="source_identified_metadata_only",
        validation_reason="source_expansion_metadata_only_no_binary_download",
        notes=[
            "High-priority next intake candidate; isolate HairSample_Female zip only.",
            "Do not ingest restricted AvatarSample A-C; use official FAQ as license guard.",
        ],
        quality=source_quality(
            usage_role="Anime female hair template prior for bangs, side curtains, back mass, and scalp anchors.",
            representation_type="vroid_vrm_hair_cards_or_meshes",
            quality_score=0.92,
            style_relevance_to_yuna=0.9,
            has_bangs=True,
            has_side_hair=True,
            has_back_hair_mass=True,
            has_scalp_anchor_structure=True,
            has_hair_cards_or_curves=True,
            can_extract_curve_templates="yes_after_import_verification",
            source_class="open_anime_template_source",
            prior_quality="high",
            next_intake_priority="high",
            high_priority_for_next_intake=True,
            notes=[
                "Best first external prior candidate because it matches anime/stylized hair structure.",
                "Use abstract control curves and mass ratios only; no direct YUNA geometry transfer.",
            ],
        ),
        verification_sources=[
            "https://opengameart.org/content/vroid-studio-cc0-models",
            "https://vroid.pixiv.help/hc/en-us/articles/4402614652569-Do-VRoid-Studio-s-sample-models-come-with-conditions-of-use",
        ],
    ),
    source_entry(
        source_id="vroid_hairsample_male_cc0",
        source_url="https://opengameart.org/content/vroid-studio-cc0-models",
        source_name="VRoid Studio CC0 HairSample_Male",
        claimed_license="CC0 for HairSample_Male per VRoid FAQ and OpenGameArt mirror",
        license_confidence="high",
        possible_usage_role="High-priority anime/stylized male hair sample for short/medium clump topology and scalp anchor priors.",
        can_commit_binary_to_repo="yes_selected_cc0_files_after_review",
        can_commit_renders="yes_selected_cc0_files",
        can_extract_curve_templates="yes_after_import_verification",
        recommendation="open_template_source",
        intake_status="source_identified_metadata_only",
        validation_reason="source_expansion_metadata_only_no_binary_download",
        notes=[
            "Useful companion to HairSample_Female for anime card/mesh conventions.",
            "Use for topology/clump priors only, not as YUNA style target.",
        ],
        quality=source_quality(
            usage_role="Anime hair card/clump topology prior and scalp anchor convention reference.",
            representation_type="vroid_vrm_hair_cards_or_meshes",
            quality_score=0.86,
            style_relevance_to_yuna=0.72,
            has_bangs=True,
            has_side_hair=True,
            has_back_hair_mass=True,
            has_scalp_anchor_structure=True,
            has_hair_cards_or_curves=True,
            can_extract_curve_templates="yes_after_import_verification",
            source_class="open_anime_template_source",
            prior_quality="high",
            next_intake_priority="high",
            high_priority_for_next_intake=True,
            notes=[
                "Less directly YUNA-like than female sample but still valuable for anime topology grammar.",
                "Keep as selected-file intake only.",
            ],
        ),
        verification_sources=[
            "https://opengameart.org/content/vroid-studio-cc0-models",
            "https://vroid.pixiv.help/hc/en-us/articles/4402614652569-Do-VRoid-Studio-s-sample-models-come-with-conditions-of-use",
        ],
    ),
    source_entry(
        source_id="charm_anime_hair_method_reference",
        source_url="https://hyzcluster.github.io/charm/",
        source_name="CHARM anime hair card parameterization method reference",
        claimed_license="GPL-3.0 code; paper/project method reference; raw training models not redistributed",
        license_confidence="medium-high",
        possible_usage_role="Method reference for anime hair control points, card sequencing, and priors; not an asset source.",
        can_commit_binary_to_repo="no_method_reference_only",
        can_commit_renders="no_method_reference_only",
        can_extract_curve_templates="control_point_schema_reference",
        recommendation="reference_report_only",
        intake_status="method_reference_metadata_recorded",
        validation_reason="method_reference_only_no_asset_download",
        notes=[
            "Use as schema/planner literature reference only.",
            "Do not download datasets or model weights into this repo.",
        ],
        quality=source_quality(
            usage_role="Anime hair control-point schema and card-sequence planning reference.",
            representation_type="method_reference_control_point_hair_cards",
            quality_score=0.9,
            style_relevance_to_yuna=0.88,
            has_bangs=True,
            has_side_hair=True,
            has_back_hair_mass=True,
            has_scalp_anchor_structure=True,
            has_hair_cards_or_curves=True,
            can_extract_curve_templates="control_point_schema_reference",
            source_class="method_reference",
            prior_quality="high_method_reference",
            next_intake_priority="medium",
            high_priority_for_next_intake=False,
            notes=[
                "Relevant to future parameter-state updates, not direct geometry extraction.",
                "Dataset/raw models remain outside repo unless separately licensed and reviewed.",
            ],
        ),
        verification_sources=[
            "https://hyzcluster.github.io/charm/",
            "https://arxiv.org/abs/2509.21114",
            "https://github.com/hyz317/CHARM",
        ],
    ),
    source_entry(
        source_id="diffhaircard_method_reference",
        source_url="https://arxiv.org/abs/2505.18805",
        source_name="DiffHairCard / Auto Hair Card Extraction method reference",
        claimed_license="arXiv paper reference; no reusable asset binary license captured",
        license_confidence="unknown",
        possible_usage_role="Method reference for strand clustering into hair cards, texture sharing, LoD, and differentiable validation.",
        can_commit_binary_to_repo="no_method_reference_only",
        can_commit_renders="no_method_reference_only",
        can_extract_curve_templates="hair_card_clustering_method_reference",
        recommendation="reference_report_only",
        intake_status="method_reference_metadata_recorded",
        validation_reason="method_reference_only_no_asset_download",
        notes=[
            "Use as literature prior for card clustering and card-density validation.",
            "Do not treat paper figures or examples as reusable dataset assets.",
        ],
        quality=source_quality(
            usage_role="Hair card clustering, texture/geometry optimization, and LoD planning reference.",
            representation_type="method_reference_hair_card_extraction",
            quality_score=0.84,
            style_relevance_to_yuna=0.7,
            has_bangs=False,
            has_side_hair=True,
            has_back_hair_mass=True,
            has_scalp_anchor_structure=False,
            has_hair_cards_or_curves=True,
            can_extract_curve_templates="hair_card_clustering_method_reference",
            source_class="method_reference",
            prior_quality="medium_high_method_reference",
            next_intake_priority="low",
            high_priority_for_next_intake=False,
            notes=[
                "Good validation/planning reference for card count and LoD.",
                "Not anime-specific enough to drive YUNA shape alone.",
            ],
        ),
        verification_sources=["https://arxiv.org/abs/2505.18805"],
    ),
]


def merge_manifest(manifest: dict[str, Any], generated_at: str) -> dict[str, Any]:
    updated = dict(manifest)
    updated["generated_at"] = generated_at
    sources = [dict(source) for source in updated.get("sources", [])]
    by_id = {source["source_id"]: source for source in sources}

    for source_id, update in CURATED_SOURCE_UPDATES.items():
        if source_id in by_id:
            by_id[source_id].update(update)

    for source in NEW_CURATED_SOURCES:
        existing = by_id.get(source["source_id"])
        if existing:
            existing.update(source)
        else:
            sources.append(source)
            by_id[source["source_id"]] = source

    updated["sources"] = sources
    final_reports = updated.setdefault("pilot_outputs", {}).setdefault("final_reports", [])
    report_path = "CharacterPackage/external_hair_dataset/reports/external_hair_source_expansion_v1_report.json"
    if report_path not in final_reports:
        final_reports.append(report_path)
    tests = updated.setdefault("pilot_outputs", {}).setdefault("tests", [])
    test_path = "CharacterPackage/tools/tests/test_external_hair_source_expansion_v1.py"
    if test_path not in tests:
        tests.append(test_path)
    return updated


def candidate_record(source: dict[str, Any]) -> dict[str, Any]:
    quality = source["source_quality_v1"]
    return {
        "source_id": source["source_id"],
        "source_url": source["source_url"],
        "source_name": source["source_name"],
        "claimed_license": source["claimed_license"],
        "license_confidence": source["license_confidence"],
        "usage_role": quality["usage_role"],
        "possible_usage_role": source["possible_usage_role"],
        "representation_type": quality["representation_type"],
        "quality_score": quality["quality_score"],
        "style_relevance_to_yuna": quality["style_relevance_to_yuna"],
        "has_bangs": quality["has_bangs"],
        "has_side_hair": quality["has_side_hair"],
        "has_back_hair_mass": quality["has_back_hair_mass"],
        "has_scalp_anchor_structure": quality["has_scalp_anchor_structure"],
        "has_hair_cards_or_curves": quality["has_hair_cards_or_curves"],
        "can_extract_curve_templates": quality["can_extract_curve_templates"],
        "can_commit_binary_to_repo": source["can_commit_binary_to_repo"],
        "can_commit_renders": source["can_commit_renders"],
        "recommendation": source["recommendation"],
        "source_class": quality["source_class"],
        "prior_quality": quality["prior_quality"],
        "next_intake_priority": quality["next_intake_priority"],
        "high_priority_for_next_intake": quality["high_priority_for_next_intake"],
        "can_commit_binary": not source["can_commit_binary_to_repo"].startswith("no_"),
        "verification_sources": source.get("verification_sources_v1", []),
        "notes": quality["notes"],
    }


def build_report(manifest: dict[str, Any], generated_at: str, paths: SourceExpansionPaths) -> dict[str, Any]:
    candidates = [
        candidate_record(source)
        for source in manifest["sources"]
        if "source_quality_v1" in source
    ]
    candidates.sort(key=lambda item: (not item["high_priority_for_next_intake"], -item["quality_score"], item["source_id"]))
    high_priority = [item for item in candidates if item["high_priority_for_next_intake"]]
    existing_probe_sources = [
        item
        for item in candidates
        if item["source_id"] in {"opengameart_ponytail_female", "opengameart_long_male"}
    ]
    method_references = [item for item in candidates if item["source_class"] == "method_reference"]
    return {
        "report_version": REPORT_VERSION,
        "generated_at": generated_at,
        "status": "source_expansion_generated",
        "dataset_id": manifest["dataset_id"],
        "external_asset_usage": "prior_only",
        "replace_in_beauty_glb": False,
        "generated_yuna_hair": False,
        "cloth_seam_surface_blocked": True,
        "large_binaries_committed": False,
        "candidate_source_count": len(candidates),
        "high_priority_source_count": len(high_priority),
        "method_reference_count": len(method_references),
        "existing_probe_sources_retained": [item["source_id"] for item in existing_probe_sources],
        "current_probe_quality_boundary": {
            item["source_id"]: item["prior_quality"] for item in existing_probe_sources
        },
        "high_priority_next_intake": [
            {
                "source_id": item["source_id"],
                "source_name": item["source_name"],
                "why": item["usage_role"],
                "binary_policy": item["can_commit_binary_to_repo"],
            }
            for item in high_priority
        ],
        "candidate_sources": candidates,
        "blocked_behavior": [
            "No unclear-license source binary may be committed.",
            "Method references can update schemas and validation language only; they are not asset sources.",
            "External sources remain priors/references and cannot replace YUNA v8 beauty hair.",
            "cloth_seam_surface remains blocked by manual YUNA hair review.",
        ],
        "outputs": {
            "manifest": rel(paths.manifest_path, paths.repo_root),
            "triage": rel(paths.triage_path, paths.repo_root),
            "report": rel(paths.expansion_report_path, paths.repo_root),
        },
    }


def replace_section(text: str, marker: str, body: str) -> str:
    start = f"<!-- {marker}:start -->"
    end = f"<!-- {marker}:end -->"
    section = f"{start}\n{body.rstrip()}\n{end}"
    if start in text and end in text:
        before = text.split(start, 1)[0].rstrip()
        after = text.split(end, 1)[1].lstrip()
        return f"{before}\n\n{section}\n\n{after}".rstrip() + "\n"
    return text.rstrip() + "\n\n" + section + "\n"


def triage_expansion_section(report: dict[str, Any]) -> str:
    rows = [
        "| source_id | representation | quality | yuna relevance | priority | recommendation | binary policy | reason |",
        "|---|---|---:|---:|---|---|---|---|",
    ]
    for item in report["candidate_sources"]:
        rows.append(
            "| `{source_id}` | {representation_type} | {quality_score:.2f} | {style_relevance_to_yuna:.2f} | {next_intake_priority} | {recommendation} | `{can_commit_binary_to_repo}` | {usage_role} |".format(
                **item
            )
        )
    return "\n".join(
        [
            "## Source Expansion v1",
            "",
            "Route: `external_hair_source_expansion_v1`.",
            "",
            "This expansion records curated, source-checked candidates for future external hair priors. It does not download binaries, generate YUNA hair, or unblock cloth.",
            "",
            *rows,
            "",
            "High-priority next intake candidates:",
            *[
                f"- `{item['source_id']}`: {item['source_name']} ({item['binary_policy']})"
                for item in report["high_priority_next_intake"]
            ],
            "",
            "The two existing probe sources remain retained but are explicitly low/medium prior quality, not quality targets.",
        ]
    )


def readme_expansion_section(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "## Source Expansion v1",
            "",
            "`external_hair_source_expansion_v1` adds quality/style annotations and method-reference records without downloading third-party binaries.",
            "",
            f"- candidate sources: `{report['candidate_source_count']}`",
            f"- high-priority next intake sources: `{report['high_priority_source_count']}`",
            f"- method references: `{report['method_reference_count']}`",
            "- current probe sources are retained as low/medium priors, not accepted hair targets.",
            "- external assets remain `prior_only`; `replace_in_beauty_glb=false`; `cloth_seam_surface` remains blocked.",
            "",
            "Report:",
            "",
            "```text",
            "CharacterPackage/external_hair_dataset/reports/external_hair_source_expansion_v1_report.json",
            "```",
        ]
    )


def project_state_section(report: dict[str, Any]) -> str:
    high_priority = ", ".join(f"`{item['source_id']}`" for item in report["high_priority_next_intake"])
    return "\n".join(
        [
            "## External Hair Source Expansion v1",
            "",
            "- Route: `external_hair_source_expansion_v1`",
            "- Status: `source_expansion_generated`",
            f"- Candidate sources annotated: `{report['candidate_source_count']}`",
            f"- High-priority next intake sources: {high_priority}",
            "- Existing probe samples remain retained as low/medium prior quality, not quality targets.",
            "- Method references such as CHARM and DiffHairCard are `method_reference` / `reference_report_only`; they must not introduce binaries.",
            "- Boundary: no source binaries downloaded or committed; no YUNA hair generated; v8 remains immutable; `replace_in_beauty_glb=false`; `cloth_seam_surface` remains blocked.",
            "",
            "Next valid external-data task: `external_hair_intake_probe_v1_selected_sources` for selected VRoid HairSample and/or BlendSwap Curly Hair with license snapshots and quarantine-only downloads.",
            "",
            "Still invalid: `cloth_seam_surface`.",
        ]
    )


def next_goal_text() -> str:
    return """# Next Goal: External Hair Intake Probe v1 Selected Sources

## Objective

Run a narrow intake probe for selected high-priority external hair prior sources.

## Allowed Sources

Start with one or two of:

- `vroid_hairsample_female_cc0`
- `vroid_hairsample_male_cc0`
- `blendswap_curly_hair`
- selected small files from `opengameart_hair_alphas_for_days`

## Rules

- Keep `CharacterPackage/semantic_layer_v8` unchanged.
- Keep `replace_in_beauty_glb=false`.
- Keep all external assets `prior_only`.
- Do not generate YUNA hair.
- Do not proceed to `cloth_seam_surface`.
- Do not commit unclear-license or large third-party binaries.
- Method references such as CHARM/DiffHairCard may inform schema language only.

## Required Evidence

- license snapshot;
- checksum and quarantine-only download metadata if any file is fetched;
- front/yaw30/side/wire/alpha/depth/normal render or explicit `skipped_with_reason`;
- prior report describing scalp anchors, curves, width/taper, depth groups, and failure/negative examples.

## Verification

```bash
python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v
python3 -m compileall CharacterPackage/tools
git diff --name-only -- CharacterPackage/semantic_layer_v8
```
"""


def handoff_text(report: dict[str, Any]) -> str:
    high_priority = ", ".join(item["source_id"] for item in report["high_priority_next_intake"])
    return f"""COPY_TO_CHATGPT_HANDOFF
项目：jupiternaut/resonance-afterlight-yuna-3d
分支：feature/authored-hair-ribbons-v0
提交：本文件所在提交；最终 HEAD 请以 `git rev-parse --short HEAD` / GitHub 显示为准
本轮目标：实现 `external_hair_source_expansion_v1`，把外部 hair prior 来源从两个低/中质量 probe 扩展成可筛选的高质量候选来源集合。
本轮结论：已生成 source expansion v1。没有下载或提交第三方大二进制，没有生成 YUNA hair，没有替换 v8 beauty，cloth 仍阻塞。
公式阶段：
- theta_p_next = ProjectToConstraints_p((1-alpha)*theta_p + alpha*RobustFuse(front/side/back/validation/prior))
- 本轮只更新外部来源参数状态和 prior/source planning，不改 YUNA mesh vertices。
核心状态：
- v8 unchanged: true
- replace_in_beauty_glb: false
- external_asset_usage: prior_only
- large_binaries_committed: false
- generated_yuna_hair: false
- ready_for_cloth_seam_surface: false
- visual_sanity_status: not_applicable_external_source_expansion
- manual_review: still_required_for_current_hair_variants
关键指标：
- candidate_source_count: {report['candidate_source_count']}
- high_priority_source_count: {report['high_priority_source_count']}
- high_priority_next_intake: {high_priority}
- method_reference_count: {report['method_reference_count']}
- existing_probe_sources_retained: {', '.join(report['existing_probe_sources_retained'])}
生成/更新文件：
- CharacterPackage/tools/external_hair_source_expansion_v1.py
- CharacterPackage/tools/tests/test_external_hair_source_expansion_v1.py
- CharacterPackage/external_hair_dataset/assets_manifest.json
- CharacterPackage/external_hair_dataset/assets_manifest.schema.json
- CharacterPackage/external_hair_dataset/SOURCE_TRIAGE.md
- CharacterPackage/external_hair_dataset/README.md
- CharacterPackage/external_hair_dataset/reports/external_hair_source_expansion_v1_report.json
- CharacterPackage/semantic_layer_v9_candidate/PROJECT_STATE.md
- CharacterPackage/semantic_layer_v9_candidate/NEXT_GOAL.md
- CharacterPackage/semantic_layer_v9_candidate/CHATGPT_HANDOFF.md
验证命令：
- unittest: 待本轮最终运行记录
- compileall: 待本轮最终运行记录
- v8 diff: 待本轮最终运行记录
当前阻塞：当前 hair variants 仍需人工视觉复核；external source expansion 只能给未来 intake/schema/planner 提供候选来源，不改变 hair route acceptance，也不解除 cloth 阻塞。
推荐下一步 Codex goal：
/goal Run `external_hair_intake_probe_v1_selected_sources` for one or two high-priority sources (`vroid_hairsample_female_cc0`, `vroid_hairsample_male_cc0`, or `blendswap_curly_hair`) with license snapshots and quarantine-only downloads. Do not generate YUNA hair, do not copy external shapes, keep v8 unchanged, and do not proceed to cloth.
"""


def run(paths: SourceExpansionPaths) -> dict[str, Any]:
    generated_at = now_iso()
    manifest = read_json(paths.manifest_path)
    updated_manifest = merge_manifest(manifest, generated_at)
    report = build_report(updated_manifest, generated_at, paths)

    write_json(paths.manifest_path, updated_manifest)
    write_json(paths.expansion_report_path, report)

    triage = paths.triage_path.read_text(encoding="utf-8")
    paths.triage_path.write_text(
        replace_section(triage, "source_expansion_v1", triage_expansion_section(report)),
        encoding="utf-8",
    )

    readme = paths.readme_path.read_text(encoding="utf-8")
    paths.readme_path.write_text(
        replace_section(readme, "source_expansion_v1", readme_expansion_section(report)),
        encoding="utf-8",
    )

    project_state = paths.project_state_path.read_text(encoding="utf-8")
    paths.project_state_path.write_text(
        replace_section(project_state, "external_hair_source_expansion_v1", project_state_section(report)),
        encoding="utf-8",
    )

    paths.next_goal_path.write_text(next_goal_text(), encoding="utf-8")
    paths.chatgpt_handoff_path.write_text(handoff_text(report), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Expand curated external hair source metadata for YUNA priors.")
    parser.add_argument("--repo-root", type=Path, default=repo_root_from_file())
    args = parser.parse_args()
    paths = default_paths(args.repo_root.resolve())
    report = run(paths)
    print(f"{SCRIPT_NAME}: {report['status']} ({report['candidate_source_count']} candidates)")


if __name__ == "__main__":
    main()
