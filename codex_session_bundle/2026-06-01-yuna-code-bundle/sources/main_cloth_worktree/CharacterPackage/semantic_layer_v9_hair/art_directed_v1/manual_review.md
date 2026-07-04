# Manual Review: art_directed_hair_ribbons_v1

Status: `failed_target_schema_alignment`

Route: `build_art_directed_hair_ribbons_v1`

Actuator: `art_directed_hair_ribbons_v1`

## Decision

The visible-mass refinement increases candidate-only front readability, but it
does not pass the schema boundary because the forbidden non-hair leak rose above
threshold. Keep it as an additive failed/needs-rework candidate.

## Evidence

- Main report:
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_report.json`
- CI report:
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/validation_ci_report.json`
- Schema eval:
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/target_schema_v1_eval/hair_target_schema_v1_report.json`
- Front:
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_front.png`
- Yaw15:
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_yaw15.png`
- Yaw30:
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_yaw30.png`
- Side:
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_side.png`

## Numeric Gate

- `non_degenerate_hair_coverage_passed=true`
- `candidate_front_visible_hair_mass=true`
- `candidate_visible_area_ratio=0.010395`
- `soft_silhouette_coverage_ratio=0.464084`
- `candidate_core_coverage_ratio=0.521867`
- `candidate_soft_inside_ratio=0.754547`
- `forbidden_candidate_leak_ratio=0.194649`
- `bangs_presence_ratio=0.371327`
- `side_hair_left_presence_ratio=0.443825`
- `side_hair_right_presence_ratio=0.792136`
- `back_hair_mass_presence_ratio=0.591295`
- `component_count=15`
- `scalp_anchor_continuity=0.371327`
- `ribbon_count=27`
- `depth_group_count=6`
- `art_directed_primitive_intent_count=27`
- `flow_continuity_passed=true`
- `manual_visual_review_status=blocked_by_target_schema_alignment`

## Visual Notes

- Candidate-only front now has more readable visible mass than the prior sparse
  pass, but it is still fragmented and not a complete accepted hairstyle.
- Yaw30 remains readable as a candidate artifact, but it still breaks into
  separated plates rather than continuous scalp-anchored hair ribbons.
- The route now exposes the tradeoff clearly: more visible hair mass increases
  forbidden-zone leakage under the current target schema.
- This is a useful negative-plus checkpoint, not an accepted hair candidate.

## Boundaries

- `replace_in_beauty_glb=false`
- `ready_for_cloth_seam_surface=false`
- `semantic_layer_v8` must remain unchanged.
- Do not proceed to `cloth_seam_surface` until manual review accepts this or a
  later hair candidate.

## Recommended Next

`fix_hair_ribbons_to_schema_v1_visible_mass_leak_balance`

Next work must preserve the new visible-mass/readability fields while reducing
`forbidden_candidate_leak_ratio` below threshold. Do not proceed to cloth.
