# Next Goal: Fix Hair Ribbons Visible-Mass / Leak Balance

## Objective

Continue `art_directed_hair_ribbons_v1` without advancing cloth. The latest
visible-mass refinement made candidate-only front/yaw30 easier to see, but it
does not pass target-schema alignment because forbidden-zone leakage is too
high.

## Current Checkpoint

`build_art_directed_hair_ribbons_v1` has regenerated the additive candidate
under `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/`.

Key metrics:

- `status=failed_target_schema_alignment`
- `non_degenerate_hair_coverage_passed=true`
- `candidate_front_visible_hair_mass=true`
- `candidate_visible_area_ratio=0.010395` threshold `>=0.010`
- `soft_silhouette_coverage_ratio=0.464084` threshold `>=0.25`
- `candidate_core_coverage_ratio=0.521867` threshold `>=0.10`
- `candidate_soft_inside_ratio=0.754547` threshold `>=0.70`
- `forbidden_candidate_leak_ratio=0.194649` threshold `<0.10`
- `primary_group_presence_passed=true`
- `yaw30_hair_readability=true`
- `side_hair_readability=true`
- `manual_visual_review_status=blocked_by_target_schema_alignment`
- `bangs_presence_ratio=0.371327` threshold `>=0.15`
- `side_hair_left_presence_ratio=0.443825` threshold `>=0.30`
- `side_hair_right_presence_ratio=0.792136` threshold `>=0.30`
- `back_hair_mass_presence_ratio=0.591295` threshold `>=0.35`
- `component_count=15` maximum `32`
- `scalp_anchor_continuity=0.371327` threshold `>=0.15`
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
- It still reads as disconnected plates, especially in yaw30.
- It cannot be accepted as a hair candidate while
  `forbidden_candidate_leak_ratio` is above threshold.

## Acceptance For Next Goal

- Reduce `forbidden_candidate_leak_ratio` below threshold without dropping:
  - `candidate_front_visible_hair_mass=true`
  - `primary_group_presence_passed=true`
  - `yaw30_hair_readability=true`
  - `side_hair_readability=true`
- Keep `replace_in_beauty_glb=false`.
- Keep `semantic_layer_v8` unchanged.
- Keep `ready_for_cloth_seam_surface=false`.
- Do not call this final production hair.

## Non-Goals

- Do not implement `cloth_seam_surface`.
- Do not add physics.
- Do not replace v8 beauty.
- Do not call numeric pass an accepted visual pass.
