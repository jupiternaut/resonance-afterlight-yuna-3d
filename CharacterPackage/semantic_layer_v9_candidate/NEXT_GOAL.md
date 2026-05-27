# Next Goal: Manual Review Art-Directed Hair Ribbons v1

## Objective

Review `art_directed_hair_ribbons_v1` visually before any cloth actuator or v8
beauty replacement. The schema/non-degenerate gate has passed, but the route is
not accepted until manual visual review says the front/yaw/side screenshots are
hair-like enough for the next integration step.

## Current Checkpoint

`build_art_directed_hair_ribbons_v1` has generated an additive candidate under
`CharacterPackage/semantic_layer_v9_hair/art_directed_v1/`.

Key metrics:

- `status=art_directed_candidate_manual_review_required`
- `non_degenerate_hair_coverage_passed=true`
- `candidate_visible_area_ratio=0.007020` threshold `>=0.005`
- `soft_silhouette_coverage_ratio=0.341499` threshold `>=0.25`
- `candidate_core_coverage_ratio=0.341135` threshold `>=0.10`
- `candidate_soft_inside_ratio=0.822168` threshold `>=0.70`
- `forbidden_candidate_leak_ratio=0.020550` threshold `<0.10`
- `bangs_presence_ratio=0.214286` threshold `>=0.15`
- `side_hair_left_presence_ratio=0.493036` threshold `>=0.30`
- `side_hair_right_presence_ratio=0.911678` threshold `>=0.30`
- `back_hair_mass_presence_ratio=0.794342` threshold `>=0.35`
- `component_count=6` maximum `32`
- `scalp_anchor_continuity=0.214286` threshold `>=0.15`
- `ribbon_count=25`
- `depth_group_count=6`
- `art_directed_primitive_intent_count=25`
- `flow_continuity_passed=true`
- `replace_in_beauty_glb=false`
- `ready_for_cloth_seam_surface=false`

## Review Inputs

- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/target_schema_v1_eval/hair_target_schema_v1_report.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_front.png`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_yaw15.png`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_yaw30.png`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_side.png`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/target_schema_v1_eval/schema_debug_contact_sheet.png`

## Current Visual Verdict

- v1 is materially better than v0 underfilled/barcode-strip failure.
- yaw15/yaw30 show cleaner layered hair-card mass without the prior large
  side-profile volume rectangles.
- candidate-only front is still sparse at full-body framing and should not be
  called accepted production hair.

## Acceptance

- Human review accepts the front/yaw/side screenshots as a useful hair candidate.
- The report may remain `manual_review_required`; do not set accepted status
  unless the reviewer explicitly accepts it.
- `semantic_layer_v8` remains unchanged.
- `replace_in_beauty_glb=false` remains true until a separate replacement
  approval exists.
- `ready_for_cloth_seam_surface=false` remains true until hair quality is
  accepted.

## If Rejected

Refine v1, focusing on:

- side-profile shape so it reads as hair instead of blocky proxy volume;
- front scalp integration, especially the high bangs strip and face-adjacent
  vertical side faces;
- preserving schema pass metrics without returning to sparse/barcode strips.

## Non-Goals

- Do not implement `cloth_seam_surface`.
- Do not add physics.
- Do not replace v8 beauty.
- Do not call this final production topology.
