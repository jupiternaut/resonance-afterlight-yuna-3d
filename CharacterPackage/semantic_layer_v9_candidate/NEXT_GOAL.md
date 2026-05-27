# Next Goal: Manual Review Art-Directed Hair Ribbons v1 Quality

## Objective

Review `art_directed_hair_ribbons_v1` visually before any cloth actuator or v8
beauty replacement. The visible-mass/leak balance now passes the target-schema
numeric gates after applying the same render correction used by the generated
hair meshes.

## Current Checkpoint

`build_art_directed_hair_ribbons_v1` remains an additive candidate under
`CharacterPackage/semantic_layer_v9_hair/art_directed_v1/`.

Key metrics:

- `status=art_directed_candidate_manual_review_required`
- `candidate_target_schema_status=schema_gate_passed_manual_review_required`
- `non_degenerate_hair_coverage_passed=true`
- `candidate_front_visible_hair_mass=true`
- `candidate_visible_area_ratio=0.010395` threshold `>=0.010`
- `soft_silhouette_coverage_ratio=0.511386` threshold `>=0.25`
- `candidate_core_coverage_ratio=0.608249` threshold `>=0.10`
- `candidate_soft_inside_ratio=0.831454` threshold `>=0.70`
- `forbidden_candidate_leak_ratio=0.071096` threshold `<0.10`
- `primary_group_presence_passed=true`
- `yaw30_hair_readability=true`
- `side_hair_readability=true`
- `manual_visual_review_status=pending_user_review_visible_mass_refined`
- `bangs_presence_ratio=0.891591` threshold `>=0.15`
- `side_hair_left_presence_ratio=0.502321` threshold `>=0.30`
- `side_hair_right_presence_ratio=0.667259` threshold `>=0.30`
- `back_hair_mass_presence_ratio=0.474429` threshold `>=0.35`
- `component_count=15` maximum `32`
- `scalp_anchor_continuity=0.474429` threshold `>=0.15`
- `ribbon_count=27`
- `depth_group_count=6`
- `art_directed_primitive_intent_count=27`
- `flow_continuity_passed=true`
- `replace_in_beauty_glb=false`
- `ready_for_cloth_seam_surface=false`

## Review Inputs

- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/target_schema_v1_eval/hair_target_schema_v1_report.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_candidate_front.png`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_yaw15.png`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_yaw30.png`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/target_schema_v1_eval/schema_debug_contact_sheet.png`

## Current Visual Verdict

- The result is an improvement over the sparse v1 checkpoint.
- Candidate-only front now has more visible hair mass.
- Target-schema numeric gates pass.
- It still needs manual review because yaw/front may still read as separated
  plates rather than accepted scalp-anchored hair.

## Acceptance For Next Goal

- Human review accepts the front/yaw screenshots as a useful hair candidate.
- The report may remain `manual_review_required`; do not set accepted status
  unless the reviewer explicitly accepts it.
- Keep `replace_in_beauty_glb=false`.
- Keep `semantic_layer_v8` unchanged.
- Keep `ready_for_cloth_seam_surface=false` until hair quality is accepted.

## Non-Goals

- Do not implement `cloth_seam_surface`.
- Do not add physics.
- Do not replace v8 beauty.
- Do not call this final production topology.
