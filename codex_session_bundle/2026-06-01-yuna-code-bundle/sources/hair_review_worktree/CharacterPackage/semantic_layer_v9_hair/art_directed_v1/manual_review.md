# Manual Review: art_directed_hair_ribbons_v1

Status: `manual_review_required`

Route: `build_art_directed_hair_ribbons_v1`

Actuator: `art_directed_hair_ribbons_v1`

## Decision

The visible-mass refinement increases candidate-only front readability. The
target-schema pass now uses the same render correction as the generated hair
meshes, which brings the forbidden non-hair leak below threshold. Keep it as an
additive DCC handoff candidate until manual review accepts or rejects the
visual result.

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
- `soft_silhouette_coverage_ratio=0.511386`
- `candidate_core_coverage_ratio=0.608249`
- `candidate_soft_inside_ratio=0.831454`
- `forbidden_candidate_leak_ratio=0.071096`
- `bangs_presence_ratio=0.891591`
- `side_hair_left_presence_ratio=0.502321`
- `side_hair_right_presence_ratio=0.667259`
- `back_hair_mass_presence_ratio=0.474429`
- `component_count=15`
- `scalp_anchor_continuity=0.474429`
- `ribbon_count=27`
- `depth_group_count=6`
- `art_directed_primitive_intent_count=27`
- `flow_continuity_passed=true`
- `schema_render_correction_px={x:13.0,y:8.0}`
- `manual_visual_review_status=pending_user_review_visible_mass_refined`

## Visual Notes

- Candidate-only front now has more readable visible mass than the prior sparse
  pass, but it is still not a complete accepted hairstyle.
- Yaw30 remains readable as a candidate artifact, but it still breaks into
  separated plates rather than continuous scalp-anchored hair ribbons.
- The route is now ready for manual visual review, not cloth or replacement.

## Boundaries

- `replace_in_beauty_glb=false`
- `ready_for_cloth_seam_surface=false`
- `semantic_layer_v8` must remain unchanged.
- Do not proceed to `cloth_seam_surface` until manual review accepts this or a
  later hair candidate.

## Recommended Next

`manual_review_art_directed_hair_ribbons_v1_quality`

If rejected, refine authored curve placement and scalp integration while
preserving the target-schema gates. Do not proceed to cloth.
