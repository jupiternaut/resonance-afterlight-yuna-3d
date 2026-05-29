# Next Goal: Build Hair Ribbons From Primary Curve Bundle v1

## Objective

Use `CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1.json` to
build the next YUNA hair ribbon candidate. This is the first geometry pass after
explicit primary curves exist.

## Allowed Inputs

- `CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1.json`
- `CharacterPackage/external_hair_dataset/priors/external_hair_prior_schema_v1.json`
- `CharacterPackage/semantic_layer_v9_hair/hair_design_schema_v1.json`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/hair_target_schema_v1_report.json`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/group_masks/`

## Rules

- Keep `CharacterPackage/semantic_layer_v8` unchanged.
- Keep `replace_in_beauty_glb=false`.
- Do not replace v8 beauty.
- Do not proceed to `cloth_seam_surface`.
- Do not copy external geometry directly.
- Do not call the result final production hair.
- Keep manual visual review required.

## Required Evidence

- Candidate spec/report showing each ribbon came from a named primary curve,
  secondary strand, or flyaway strand.
- Validation screenshots or explicit skipped reports.
- Target-schema metrics for soft-inside, core coverage, forbidden leak,
  visible mass, group presence, yaw30 readability, and side readability.
- JSON report preserving `replace_in_beauty_glb=false` and
  `ready_for_cloth_seam_surface=false`.

## Verification

```bash
python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v
python3 -m compileall CharacterPackage/tools
git diff --name-only -- CharacterPackage/semantic_layer_v8
```
