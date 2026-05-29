# YUNA v9 Project State

## Current State

- `CharacterPackage/semantic_layer_v8` is the immutable visual-review / DCC baseline.
- Current active hair work is planning-only:
  `CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1.json`.
- The curve bundle was rebuilt from:
  - `CharacterPackage/external_hair_dataset/priors/external_hair_prior_schema_v1.json`
  - `CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/benchmarks/constraint_benchmark_v0/external_hair_probe_constraint_benchmark_v0_report.json`
  - `CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/analysis/pink_hair_segmentation_probe/pink_hair_segmentation_report.json`
  - `CharacterPackage/semantic_layer_v9_hair/hair_design_schema_v1.json`
  - `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/hair_target_schema_v1_report.json`
- The positive pink hair probe is used only as a prior/benchmark source. It is
  not a shape source and its geometry, topology, UVs, transforms, and silhouette
  are not copied into YUNA.
- This turn did not generate a YUNA GLB/OBJ/BLEND route.
- `replace_in_beauty_glb=false`.
- `ready_for_cloth_seam_surface=false`.
- `manual_review_required=true`.
- `cloth_seam_surface` remains blocked.

## Curve Bundle Contents

The machine-readable curve bundle contains:

- `bangs_primary`
- `side_hair_left_primary`
- `side_hair_right_primary`
- `back_hair_mass`
- `secondary_strands`
- `flyaway_strands`

Each primary curve includes:

- `scalp_anchor`
- `curve_points`
- `width_profile`
- `taper_profile`
- `depth_group`
- `forbidden_zone_policy`
- `source_prior_reference`
- `confidence`
- `manual_review_required=true`

## Formula Binding

The v9/v10 candidate loop is governed by the Bounded Semantic Geometry Filter:

```text
theta_p_next =
ProjectToConstraints_p(
  (1 - alpha) * theta_p
  + alpha * RobustFuse(
      front_obs_p,
      side_obs_p,
      back_obs_p,
      validation_obs_p,
      prior_p
    )
)
```

For this stage, `theta_hair` means machine-readable curve parameters and
planning metadata, not generated mesh vertices.

## Current Evidence

- `CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1.json`
- `CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1_report.json`
- `CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1_front_overlay.png`
- `CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1_yaw30_plan.png`
- `CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1_contact_sheet.png`
- `CharacterPackage/external_hair_dataset/priors/external_hair_prior_schema_v1.json`
- `CharacterPackage/tools/build_primary_curve_bundle_v1.py`
- `CharacterPackage/tools/tests/test_primary_curve_bundle_v1.py`

## External Hair Source Expansion v1

- Route: `external_hair_source_expansion_v1`
- Status: `source_expansion_generated`
- Usage: external sources remain `prior_only`; they are not production-ready
  replacements and do not replace v8 beauty.
- Boundary: source expansion informs future priors and benchmarks only.
- `cloth_seam_surface` remains blocked while the hair planning/review route is
  unresolved.

## Current Blocker

Manual-review the curve bundle as a planning artifact before any mesh/GLB
generation. Do not proceed to `cloth_seam_surface`.

## Next Valid Task

`manual_review_primary_curve_bundle_v1_before_generation`

## Invalid Next Tasks

- `cloth_seam_surface`
- generating a YUNA GLB from the curve bundle without manual review
- replacing v8 beauty hair

## Required Verification

```bash
python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v
python3 -m compileall CharacterPackage/tools
git diff --name-only -- CharacterPackage/semantic_layer_v8
```
