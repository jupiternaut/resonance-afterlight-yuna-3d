# Next Goal: Fix Hair Ribbons to Schema v1

## Objective

Rebuild or fix authored hair ribbons so the candidate is constrained to
`hair_target_schema_v1`. This goal must not create a cloth actuator and must not
replace v8 beauty.

## Current Checkpoint

A schema-constrained rebuild has been generated, but it still fails target
schema gates:

- `forbidden_candidate_leak_ratio=0.299879` (threshold `<=0.10`)
- `candidate_core_coverage_ratio=0.196487` (threshold `>=0.10`)
- `candidate_soft_inside_ratio=0.557359` (threshold `>=0.70`)

The next pass should continue reducing forbidden-zone leakage and improving
soft-silhouette containment, or move to `build_art_directed_hair_ribbons_v1`
with explicit hand-authored strand lanes. Do not proceed to cloth.

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

- A rebuilt or fixed hair ribbon candidate evaluated against schema v1.
- A JSON report explaining target-schema pass/fail.
- Debug PNGs that show candidate coverage against strict/soft/forbidden zones.
- Updates to validation/backlog docs that keep the next blocker honest.

Suggested output location:

```text
CharacterPackage/semantic_layer_v9_hair/
```

## Acceptance

- `semantic_layer_v8` diff is empty.
- Tests pass.
- Compile passes.
- Candidate leak into `forbidden_nonhair_zone` is below threshold.
- Candidate coverage is mostly inside `soft_hair_silhouette`.
- Candidate covers enough of `strict_hair_core` to justify manual review.
- The report does not mark the route as accepted unless the candidate passes the
  clean schema and manual review accepts it.
- `ready_for_cloth_seam_surface=false` unless hair quality is accepted.

## Non-Goals

- Do not implement `cloth_seam_surface`.
- Do not add physics.
- Do not replace v8 beauty.
- Do not treat side/back references as locked geometry truth.
