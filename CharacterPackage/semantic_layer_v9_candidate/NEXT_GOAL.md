# Next Goal: Manual Review Authored Hair Ribbons v0 Quality

## Objective

Review the schema-gated authored hair ribbons candidate visually before any
cloth actuator or v8 beauty replacement. This goal must not create a cloth
actuator and must not replace v8 beauty.

## Current Checkpoint

A tightened schema-constrained rebuild has generated a candidate that passes the
target-schema numeric gates:

- `forbidden_candidate_leak_ratio=0.010006` (threshold `<0.10`)
- `candidate_core_coverage_ratio=0.187749` (threshold `>=0.10`)
- `candidate_soft_inside_ratio=0.916398` (threshold `>=0.70`)
- `candidate_target_schema_status=schema_gate_passed_manual_review_required`

The next pass should review screenshots and decide whether the candidate is
visually acceptable as a hair-only DCC candidate. Do not proceed to cloth.

## Inputs

- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/hair_target_schema_v1_report.json`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/strict_hair_core_mask.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/soft_hair_silhouette_mask.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/forbidden_nonhair_zone_mask.png`
- `CharacterPackage/semantic_layer_v9_hair/target_review/hair_target_review_report.json`
- `CharacterPackage/semantic_layer_v9_hair/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/validation_ci/validation_ci_report.json`
- v8 masks/textures referenced by the existing hair route
- `CharacterPackage/semantic_layer_v9_candidate/backlog_v10.md`

## Required Outputs

- A manual visual review report.
- A clear accept/reject decision for the hair route.
- If rejected, a specific next goal such as
  `build_art_directed_hair_ribbons_v1`.
- Updates to validation/backlog docs that keep the next blocker honest.

Suggested output location:

```text
CharacterPackage/semantic_layer_v9_hair/manual_review/
```

## Acceptance

- `semantic_layer_v8` diff is empty.
- Tests pass.
- Compile passes.
- Target-schema numeric gate remains passed.
- Candidate-only, baseline-only, overlay, yaw15, yaw30, side, wire, and exploded
  screenshots are reviewed.
- The report does not mark the route as accepted unless manual review accepts it.
- `ready_for_cloth_seam_surface=false` unless hair quality is accepted.

## Non-Goals

- Do not implement `cloth_seam_surface`.
- Do not add physics.
- Do not replace v8 beauty.
- Do not treat side/back references as locked geometry truth.
