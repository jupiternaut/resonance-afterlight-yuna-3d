# YUNA v9 Project State

## Current State

- `CharacterPackage/semantic_layer_v8` is the immutable visual-review / DCC baseline.
- Current active hair work generated an actual curve-bundle candidate route:
  `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/`.
- The curve bundle was rebuilt from:
  - `CharacterPackage/external_hair_dataset/priors/external_hair_prior_schema_v1.json`
  - `CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/benchmarks/constraint_benchmark_v0/external_hair_probe_constraint_benchmark_v0_report.json`
  - `CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/analysis/pink_hair_segmentation_probe/pink_hair_segmentation_report.json`
  - `CharacterPackage/semantic_layer_v9_hair/hair_design_schema_v1.json`
  - `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/hair_target_schema_v1_report.json`
- The positive pink hair probe is used only as a prior/benchmark source. It is
  not a shape source and its geometry, topology, UVs, transforms, and silhouette
  are not copied into YUNA.
- The curve-bundle route generated OBJ/MTL/GLB/BLEND plus validation screenshots.
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
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/exports/yuna_curve_bundle_hair_v1.obj`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/exports/yuna_curve_bundle_hair_v1.glb`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/exports/yuna_curve_bundle_hair_v1.blend`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/candidate_front.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/overlay_front.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/yaw30.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/side.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/failure_report.md`
- `CharacterPackage/external_hair_dataset/priors/external_hair_prior_schema_v1.json`
- `CharacterPackage/tools/build_primary_curve_bundle_v1.py`
- `CharacterPackage/tools/build_curve_bundle_hair_candidate_v1.py`
- `CharacterPackage/tools/tests/test_primary_curve_bundle_v1.py`
- `CharacterPackage/tools/tests/test_curve_bundle_hair_candidate_v1.py`

## Curve Bundle Candidate v1 Result

- Route: `build_curve_bundle_hair_candidate_v1`
- Status: `curve_bundle_candidate_failed_visual_review`
- `ribbon_count=46`
- `depth_group_count=7`
- `candidate_front_visible_hair_mass=true`
- `primary_group_presence_passed=true`
- `yaw30_hair_readability=true`
- `side_hair_readability=true`
- `forbidden_candidate_leak_ratio=0.330678` in `validation_report.json`
- `forbidden_candidate_leak_ratio=0.441191` in target-schema render evaluation
- `candidate_soft_inside_ratio=0.484489` in `validation_report.json`
- `candidate_soft_inside_ratio=0.321086` in target-schema render evaluation
- `candidate_target_schema_status=failed_target_schema_alignment`
- `replace_in_beauty_glb=false`
- `ready_for_cloth_seam_surface=false`

## External Hair Source Expansion v1

- Route: `external_hair_source_expansion_v1`
- Status: `source_expansion_generated`
- Usage: external sources remain `prior_only`; they are not production-ready
  replacements and do not replace v8 beauty.
- Boundary: source expansion informs future priors and benchmarks only.
- `cloth_seam_surface` remains blocked while the hair planning/review route is
  unresolved.

## Current Blocker

The curve bundle has now produced a real candidate asset, but target-schema
alignment failed. Do not proceed to `cloth_seam_surface`.

## Next Valid Task

`fix_curve_bundle_hair_candidate_v1_target_alignment`

## Invalid Next Tasks

- `cloth_seam_surface`
- replacing v8 beauty hair
- calling `curve_bundle_candidate_v1` accepted or production hair

## Required Verification

```bash
python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v
python3 -m compileall CharacterPackage/tools
git diff --name-only -- CharacterPackage/semantic_layer_v8
```
