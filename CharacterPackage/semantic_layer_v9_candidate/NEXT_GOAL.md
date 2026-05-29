# Next Goal: Fix Curve Bundle Hair Candidate v1 Target Alignment

## Objective

Continue from the real asset route:

`CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/`

The candidate now generates OBJ/MTL/GLB/BLEND and validation screenshots, but it
fails target-schema alignment. The next goal is to reduce forbidden leakage and
improve soft-silhouette containment without shrinking the candidate into sparse,
unreadable strands.

## Current Route

- Route: `build_curve_bundle_hair_candidate_v1`
- Status: `curve_bundle_candidate_failed_visual_review`
- Boundary: independent candidate-only hair route.
- `replace_in_beauty_glb=false`
- `ready_for_cloth_seam_surface=false`

## Current Evidence

- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/exports/yuna_curve_bundle_hair_v1.obj`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/exports/yuna_curve_bundle_hair_v1.glb`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/exports/yuna_curve_bundle_hair_v1.blend`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/candidate_front.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/overlay_front.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/yaw30.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/side.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/failure_report.md`

## Key Metrics

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

## Recommended Next Codex Goal

```text
/goal Continue `fix_curve_bundle_hair_candidate_v1_target_alignment`.

Read:
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_report.json
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/target_schema_v1_eval/hair_target_schema_v1_report.json
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/candidate_front.png
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/overlay_front.png
- CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1.json
- CharacterPackage/semantic_layer_v9_hair/target_schema_v1/

Goal:
Reduce forbidden leakage and improve soft-silhouette containment while keeping
candidate-front hair mass, primary group presence, scalp-anchor metadata, and
flow continuity. Do not shrink-to-pass. Do not proceed to cloth. Keep v8
unchanged and replace_in_beauty_glb=false.

Run:
python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v
python3 -m compileall CharacterPackage/tools
git diff --name-only -- CharacterPackage/semantic_layer_v8
```

## Verification

```bash
python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v
python3 -m compileall CharacterPackage/tools
git diff --name-only -- CharacterPackage/semantic_layer_v8
```
