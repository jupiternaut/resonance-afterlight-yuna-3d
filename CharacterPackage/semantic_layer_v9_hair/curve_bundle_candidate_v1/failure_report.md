# Curve Bundle Hair Candidate v1 Failure Report

## Status

`curve_bundle_candidate_failed_visual_review`

The route generated actual candidate assets from
`CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1.json`, but the
candidate does not pass the target-schema alignment gate and must not unblock
`cloth_seam_surface`.

## Generated Artifacts

- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/exports/yuna_curve_bundle_hair_v1.obj`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/exports/yuna_curve_bundle_hair_v1.mtl`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/exports/yuna_curve_bundle_hair_v1.glb`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/exports/yuna_curve_bundle_hair_v1.blend`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/candidate_front.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/overlay_front.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/yaw30.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/side.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/wire.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/exploded.png`

## Key Metrics

From `validation_report.json`:

- `ribbon_count`: `46`
- `depth_group_count`: `7`
- `candidate_front_visible_hair_mass`: `true`
- `primary_group_presence_passed`: `true`
- `yaw30_hair_readability`: `true`
- `side_hair_readability`: `true`
- `forbidden_candidate_leak_ratio`: `0.330678`
- `candidate_soft_inside_ratio`: `0.484489`
- `candidate_core_coverage_ratio`: `0.367965`
- `candidate_visible_area_ratio`: `0.015166`
- `component_count`: `8`
- `scalp_anchor_continuity`: `1.0`

From `target_schema_v1_eval/hair_target_schema_v1_report.json`:

- `candidate_target_schema_status`: `failed_target_schema_alignment`
- `forbidden_candidate_leak_ratio`: `0.441191`
- `candidate_soft_inside_ratio`: `0.321086`
- `candidate_core_coverage_ratio`: `0.354627`
- `candidate_visible_area_ratio`: `0.017181`

## Failure Reason

The candidate is an actual mesh route, not another planning-only report, but it
still renders as fragmented ribbon geometry with target-schema leakage. It
preserves visible mass and primary group presence, yet it exceeds the forbidden
leak threshold and does not keep enough visible pixels inside the soft hair
silhouette.

## Boundary

- `CharacterPackage/semantic_layer_v8` remains immutable.
- `replace_in_beauty_glb=false`.
- This route is not final production hair.
- Do not proceed to `cloth_seam_surface`.

## Recommended Next Goal

`fix_curve_bundle_hair_candidate_v1_target_alignment`

Reduce forbidden leakage and improve soft-silhouette containment without
shrinking the candidate into an unreadable sparse artifact.
