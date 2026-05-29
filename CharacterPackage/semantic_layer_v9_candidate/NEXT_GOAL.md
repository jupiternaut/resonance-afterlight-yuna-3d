# Next Goal: Manual Review Curve Bundle Hair Candidate v1

## Objective

Review the repaired curve-bundle candidate:

`CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/`

The repair loop passed the programmatic target-schema gate, but this is still a
candidate-only route. It must not replace v8 beauty hair or unblock
`cloth_seam_surface` until human visual review explicitly accepts it.

## Current Route

- Route: `repair_curve_bundle_hair_candidate_v1_until_schema_gate`
- Status: `schema_gate_passed_manual_review_required`
- Best attempt: `6`
- Boundary: independent candidate-only hair route.
- `replace_in_beauty_glb=false`
- `ready_for_cloth_seam_surface=false`

## Current Evidence

- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/repair_report.json`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/target_schema_v1_eval/hair_target_schema_v1_report.json`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/candidate_front.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/overlay_front.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/yaw30.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/side.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/wire.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/exploded.png`

## Key Metrics

- `forbidden_candidate_leak_ratio=0.084696`
- `candidate_soft_inside_ratio=0.832798`
- `candidate_core_coverage_ratio=0.645373`
- `candidate_visible_area_ratio=0.01118`
- `candidate_front_visible_hair_mass=true`
- `primary_group_presence_passed=true`
- `yaw30_hair_readability=true`
- `side_hair_readability=true`
- `manual_visual_review_status=pending_user_review_visible_mass_refined`

## Recommended Next Codex Goal

```text
/goal Manual-review curve_bundle_candidate_v1.

Read:
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/repair_report.json
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_report.json
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/target_schema_v1_eval/hair_target_schema_v1_report.json
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/candidate_front.png
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/overlay_front.png
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/yaw30.png
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/side.png

Goal:
Decide whether the repaired candidate is visually acceptable as a hair candidate
for the next integration planning step. Do not replace v8 beauty, do not proceed
to cloth, and do not call it final production hair.

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
