# Next Goal: Build Hair Target Schema v1

## Objective

Create an explicit hair target schema before regenerating or accepting authored
hair ribbons. This goal must not create a cloth actuator and must not replace
v8 beauty.

## Inputs

- `CharacterPackage/semantic_layer_v9_hair/target_review/hair_target_review_report.json`
- `CharacterPackage/semantic_layer_v9_hair/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/validation_ci/validation_ci_report.json`
- v8 masks/textures referenced by the existing hair route
- `CharacterPackage/semantic_layer_v9_candidate/backlog_v10.md`

## Required Outputs

- A machine-readable hair target schema with:
  - `strict_hair_core`
  - `soft_hair_silhouette`
  - `forbidden_nonhair_zone`
- Debug PNGs that show the schema over baseline/candidate renders.
- A JSON report explaining whether the current hair candidate passes or remains
  blocked under the new schema.
- Updates to validation/backlog docs that keep the next blocker honest.

Suggested output location:

```text
CharacterPackage/semantic_layer_v9_hair/target_schema_v1/
```

## Acceptance

- `semantic_layer_v8` diff is empty.
- Tests pass.
- Compile passes.
- The schema separates strict hair, soft hair silhouette, and forbidden nonhair
  zones.
- The report does not mark the route as accepted unless the candidate passes the
  clean schema and manual review accepts it.
- `ready_for_cloth_seam_surface=false` unless hair quality is accepted.

## Non-Goals

- Do not implement `cloth_seam_surface`.
- Do not add physics.
- Do not replace v8 beauty.
- Do not treat side/back references as locked geometry truth.
