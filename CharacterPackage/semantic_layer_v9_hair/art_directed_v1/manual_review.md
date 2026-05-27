# Manual Review: art_directed_hair_ribbons_v1

Status: `manual_review_required`

Route: `build_art_directed_hair_ribbons_v1`

Actuator: `art_directed_hair_ribbons_v1`

## Decision

The candidate passes the schema/non-degenerate numeric gate, but it is not an
accepted replacement for v8 hair. Keep it as an additive DCC handoff candidate.

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
- `candidate_visible_area_ratio=0.007020`
- `soft_silhouette_coverage_ratio=0.341499`
- `candidate_core_coverage_ratio=0.341135`
- `candidate_soft_inside_ratio=0.822168`
- `forbidden_candidate_leak_ratio=0.020550`
- `bangs_presence_ratio=0.214286`
- `side_hair_left_presence_ratio=0.493036`
- `side_hair_right_presence_ratio=0.911678`
- `back_hair_mass_presence_ratio=0.794342`
- `component_count=6`
- `scalp_anchor_continuity=0.214286`
- `ribbon_count=25`
- `depth_group_count=6`
- `art_directed_primitive_intent_count=25`
- `flow_continuity_passed=true`

## Visual Notes

- The v1 candidate is no longer the v0 underfilled/barcode-strip result.
- Yaw15 and yaw30 show a cleaner layered hair-card mass than v0.
- The previous side-profile volume blocks were removed from the beauty
  candidate, so the overlay no longer has large side-volume rectangles on the
  face/body.
- Candidate-only front remains sparse at full-body framing and should still be
  treated as an additive DCC handoff candidate, not accepted production hair.

## Boundaries

- `replace_in_beauty_glb=false`
- `ready_for_cloth_seam_surface=false`
- `semantic_layer_v8` must remain unchanged.
- Do not proceed to `cloth_seam_surface` until manual review accepts this or a
  later hair candidate.

## Recommended Next

`manual_review_art_directed_hair_ribbons_v1_quality`

If rejected, refine side-profile shape and front scalp integration without
regressing to sparse/barcode strips.
