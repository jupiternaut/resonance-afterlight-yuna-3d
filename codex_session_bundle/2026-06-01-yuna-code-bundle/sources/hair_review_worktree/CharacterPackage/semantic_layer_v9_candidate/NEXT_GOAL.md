# Next Goal: Manual Style Review Curve Bundle Hair Candidate v1

## Objective

Review the separated beauty outputs for:

`CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/`

The schema gate passed, and debug/planning overlays are now separated from
beauty images. The style gate still marks the route as:

`style_gate_failed_manual_review_required`

This route must not replace v8 beauty hair or unblock `cloth_seam_surface`
until human visual review explicitly accepts a follow-up style refinement.

## Current Route

- Route: `separate_hair_debug_beauty_and_add_style_gate_v1`
- Style target: `CharacterPackage/style_targets/yuna_cinematic_sci_fi_heroine_v0.json`
- Status: `style_gate_failed_manual_review_required`
- `debug_guides_hidden_in_beauty=true`
- `beauty_render_exists=true`
- `guide_leak_into_beauty=false`
- `reads_as_hair=false`
- `replace_in_beauty_glb=false`
- `ready_for_cloth_seam_surface=false`

## Current Evidence

Debug/planning-only outputs:

- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/debug_curve_overlay_front.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/debug_curve_overlay_yaw30.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/debug_schema_overlay.png`

Beauty outputs:

- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/candidate_beauty_front.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/overlay_beauty_front.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/yaw30_beauty.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/side_beauty.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/beauty_contact_sheet.png`

Reports:

- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/validation_ci_report.json`

## Recommended Next Codex Goal

```text
/goal Manual-review curve_bundle_candidate_v1 beauty outputs.

Read:
- CharacterPackage/style_targets/yuna_cinematic_sci_fi_heroine_v0.json
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_report.json
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/validation_ci_report.json
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/candidate_beauty_front.png
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/overlay_beauty_front.png
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/yaw30_beauty.png
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/side_beauty.png
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/beauty_contact_sheet.png

Goal:
Decide whether this beauty candidate is worth another style refinement pass.
Do not replace v8 beauty, do not proceed to cloth, and do not call it final
production hair.

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
