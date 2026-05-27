# Next Goal: Build Art-Directed Hair Ribbons v1

## Objective

Rebuild the hair candidate from `hair_design_schema_v1.json` so it has
non-degenerate visible hair mass before any cloth actuator or v8 beauty
replacement. This goal must not create a cloth actuator and must not replace v8
beauty.

## Current Checkpoint

A tightened schema-constrained rebuild has generated a candidate that passes
leak/soft-inside/core metrics but fails the non-degenerate coverage gate:

- `forbidden_candidate_leak_ratio=0.010006` (threshold `<0.10`)
- `candidate_core_coverage_ratio=0.187749` (threshold `>=0.10`)
- `candidate_soft_inside_ratio=0.916398` (threshold `>=0.70`)
- `candidate_visible_area_ratio=0.003227` (threshold `>=0.005`)
- `soft_silhouette_coverage_ratio=0.174971` (threshold `>=0.25`)
- `bangs_presence_ratio=0.066363` (threshold `>=0.15`)
- `side_hair_left_presence_ratio=0.259981` (threshold `>=0.30`)
- `component_count=39` (maximum `32`)
- `candidate_target_schema_status=schema_gate_passed_manual_review_failed_underfilled`

The next pass should create an art-directed hair candidate with stronger bangs,
side-hair, back-mass, and scalp-anchor continuity. Do not proceed to cloth.

## Inputs

- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/hair_target_schema_v1_report.json`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/strict_hair_core_mask.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/soft_hair_silhouette_mask.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/forbidden_nonhair_zone_mask.png`
- `CharacterPackage/semantic_layer_v9_hair/target_review/hair_target_review_report.json`
- `CharacterPackage/semantic_layer_v9_hair/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v9_hair/hair_design_schema_v1.json`
- v8 masks/textures referenced by the existing hair route
- `CharacterPackage/semantic_layer_v9_candidate/backlog_v10.md`

## Required Outputs

- A rebuilt art-directed hair candidate evaluated against non-degenerate coverage.
- A JSON report explaining coverage pass/fail.
- Updated validation screenshots and schema overlays.
- Updates to validation/backlog docs that keep the next blocker honest.

Suggested output location:

```text
CharacterPackage/semantic_layer_v9_hair/
```

## Acceptance

- `semantic_layer_v8` diff is empty.
- Tests pass.
- Compile passes.
- Candidate remains additive and `replace_in_beauty_glb=false`.
- Candidate has non-degenerate visible hair mass:
  - enough candidate visible area;
  - enough soft silhouette coverage;
  - visible bangs, side hair left/right, and back hair mass;
  - acceptable component count;
  - scalp-anchor continuity above threshold.
- The report does not mark the route as accepted unless manual review accepts it.
- `ready_for_cloth_seam_surface=false` unless hair quality is accepted.

## Non-Goals

- Do not implement `cloth_seam_surface`.
- Do not add physics.
- Do not replace v8 beauty.
- Do not treat side/back references as locked geometry truth.
