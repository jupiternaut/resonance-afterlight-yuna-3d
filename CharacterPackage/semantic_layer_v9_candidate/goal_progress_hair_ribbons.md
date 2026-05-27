# Goal Progress: authored_hair_ribbons_v0 / art_directed_hair_ribbons_v1

## Current Result: art_directed_hair_ribbons_v1

Status: `art_directed_candidate_manual_review_required`.

The v1 route is now implemented as an additive art-directed candidate under
`CharacterPackage/semantic_layer_v9_hair/art_directed_v1/`. It uses
`hair_design_schema_v1.json`, the target schema v1 group masks, filtered
primary hair components, secondary strands, limited flyaways, and explicit
primitive intent metadata. It does not replace v8 beauty hair.

### Implemented in v1

- Added `art_directed_hair_ribbons_v1` under
  `CharacterPackage/tools/semantic_actuators/`.
- Added CLI builder:
  `CharacterPackage/tools/build_art_directed_hair_ribbons_v1.py`.
- Uses required primary groups:
  `bangs_primary`, `side_hair_left_primary`,
  `side_hair_right_primary`, and `back_hair_mass`.
- Adds `secondary_strands` and limited `flyaway_strands` to avoid the v0
  underfilled/barcode failure mode.
- Records explicit scalp-anchor, curve-path, width-profile, taper, depth-group,
  and material metadata for every generated primitive.
- Produces 6 depth groups and 25 independent ribbon objects.
- Keeps `replace_in_beauty_glb=false`.
- Keeps `ready_for_cloth_seam_surface=false`.

### v1 Evidence

- Spec:
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/specs/yuna_semantic_layer_v9_hair_art_directed_v1.json`
- OBJ/MTL:
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/exports/yuna_semantic_layer_v9_hair_art_directed_v1.obj`
- GLB:
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/exports/yuna_semantic_layer_v9_hair_art_directed_v1.glb`
- BLEND:
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/exports/yuna_semantic_layer_v9_hair_art_directed_v1.blend`
- Main report:
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_report.json`
- Blender validation report:
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/validation_ci_report.json`
- Schema eval report:
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/target_schema_v1_eval/hair_target_schema_v1_report.json`
- Screenshots:
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_front.png`,
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_yaw15.png`,
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_yaw30.png`,
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_side.png`
- Manual review note:
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/manual_review.md`

### v1 Metrics

- `non_degenerate_hair_coverage_passed=true`
- `candidate_visible_pixel_count=13479`
- `candidate_visible_area_ratio=0.007020` threshold `>=0.005`
- `soft_silhouette_coverage_ratio=0.341499` threshold `>=0.25`
- `candidate_core_coverage_ratio=0.341135` threshold `>=0.10`
- `candidate_soft_inside_ratio=0.822168` threshold `>=0.70`
- `forbidden_candidate_leak_ratio=0.020550` threshold `<0.10`
- `bangs_presence_ratio=0.214286` threshold `>=0.15`
- `side_hair_left_presence_ratio=0.493036` threshold `>=0.30`
- `side_hair_right_presence_ratio=0.911678` threshold `>=0.30`
- `back_hair_mass_presence_ratio=0.794342` threshold `>=0.35`
- `component_count=6` maximum `32`
- `scalp_anchor_continuity=0.214286` threshold `>=0.15`
- `ribbon_count=25`
- `depth_group_count=6`
- `art_directed_primitive_intent_count=25`
- `flow_continuity_passed=true`

### v1 Visual Sanity Verdict

The v1 candidate is no longer the v0-style underfilled/barcode-strip failure.
Yaw15 and yaw30 show cleaner layered hair-card mass, and the prior blocky
side-profile volumes no longer pollute the beauty overlay. However, this is
still a proxy/candidate: candidate-only front remains sparse at full-body
framing. Manual visual review is still required before any replacement or cloth
work.

### v1 Boundary

- v8 is not modified.
- v8 beauty GLB is not replaced.
- `cloth_seam_surface` remains blocked.
- This is a DCC handoff candidate, not final production hair.
- Recommended next: `manual_review_art_directed_hair_ribbons_v1_quality`.

Status: generated as an independent candidate actuator. The raw coordinate
alignment gate is a weak pass, but the cleaned hair-target gate fails, so this
candidate is not accepted.

## Implemented

- Added `authored_hair_ribbons_v0` under `CharacterPackage/tools/semantic_actuators/`.
- Reads v8 hair masks/textures for `back_hair`, `side_hair_left`, `side_hair_right`, and `bangs`.
- Generates independent ribbon meshes preserving four hair groups and four depth groups.
- Constrains ribbon lanes to hair-mask evidence instead of broad bounding-box panels.
- Writes sanitized per-group alpha textures so transparent pixels do not render as black.
- Adds visual sanity gates for black alpha leakage, face/body over-occlusion, hair-mask alignment, and baseline/overlay framing validity.
- Adds clean hair target diagnostics so the raw v8 hair union mask cannot hide
  body/weapon contamination.
- Writes UVs for every vertex, OBJ/MTL exports, candidate spec, and JSON validation report.
- Exports GLB/BLEND when Blender is available.
- Adds spring-hook metadata only; no physics, armature, or skin weights are generated.
- Keeps `replace_in_beauty_glb=false`; v8 beauty hair remains active.

## Evidence

- Candidate spec: `CharacterPackage/semantic_layer_v9_hair/specs/yuna_semantic_layer_v9_hair.json`
- OBJ: `CharacterPackage/semantic_layer_v9_hair/exports/yuna_semantic_layer_v9_hair.obj`
- MTL: `CharacterPackage/semantic_layer_v9_hair/exports/yuna_semantic_layer_v9_hair.mtl`
- GLB: `CharacterPackage/semantic_layer_v9_hair/exports/yuna_semantic_layer_v9_hair.glb`
- BLEND: `CharacterPackage/semantic_layer_v9_hair/exports/yuna_semantic_layer_v9_hair.blend`
- Sanitized textures: `CharacterPackage/semantic_layer_v9_hair/textures/*_sanitized.png`
- Report: `CharacterPackage/semantic_layer_v9_hair/validation_report.json`
- Blender validation: `CharacterPackage/semantic_layer_v9_hair/validation_ci/validation_ci_report.json`
- Candidate-only front screenshot: `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_candidate_front.png`
- Baseline-only front screenshot: `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_baseline_front.png`
- Overlay front screenshot: `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_overlay_front.png`
- Wire/exploded screenshots: `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_wire.png`, `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_exploded.png`
- Clean target mask: `CharacterPackage/semantic_layer_v9_hair/validation_ci/hair_target_mask_clean.png`
- Dirty target overlay: `CharacterPackage/semantic_layer_v9_hair/validation_ci/hair_target_mask_dirty_overlay.png`
- Clean target report: `CharacterPackage/semantic_layer_v9_hair/validation_ci/hair_target_cleaning_report.json`
- Target review report: `CharacterPackage/semantic_layer_v9_hair/target_review/hair_target_review_report.json`
- Refined component-prior target: `CharacterPackage/semantic_layer_v9_hair/target_review/hair_target_mask_refined_component_priors.png`
- Candidate vs refined target overlay: `CharacterPackage/semantic_layer_v9_hair/target_review/candidate_vs_refined_hair_target_overlay.png`
- Negative fixture from the bad black-occlusion render: `CharacterPackage/semantic_layer_v9_hair/negative_fixtures/yuna_semantic_layer_v9_hair_validation_front_failed_visual_fixture.png`

## Current Result

- Hair candidate status: `failed_clean_hair_mask_alignment`.
- Blender validation status: `failed_clean_hair_mask_alignment`.
- Manual visual review: `failed`.
- Visual sanity status: `failed_clean_hair_mask_alignment`.
- Black alpha leak fixed: `true`.
- Numeric metrics passed: `true`.
- Black alpha leak ratio: `0.000625`.
- Candidate black pixel ratio: `0.000031`.
- Face occlusion ratio: `0.040282`.
- Non-hair occlusion ratio: `0.023251`.
- Hair mask IoU: `0.121116`.
- Outside hair mask ratio: `0.05764`.
- Raw candidate is hair-only against the dirty union: `true`.
- Candidate is hair-only after clean target check: `false`.
- Coordinate alignment gate: `weak_pass`.
- Hair target quality: `dirty_or_overbroad`.
- Hair union target clean: `false`.
- Hair union body overlap ratio: `0.844485`.
- Hair union face overlap ratio: `0.044609`.
- Hair union weapon overlap ratio: `0.043164`.
- Clean hair mask IoU: `0.014959`.
- Clean outside hair mask ratio: `0.973581`.
- Clean candidate is hair-only: `false`.
- Refined component-prior target IoU: `0.120324`.
- Refined component-prior outside ratio: `0.474535`.
- Refined component-prior candidate inside target: `false`.
- Hair union projection valid: `true`.
- Hair union projection overlap ratio: `0.612788`.
- Candidate geometry alignment valid: `true`.
- Clean candidate geometry alignment valid: `false`.
- Coordinate mapping status: `failed_clean_hair_mask_alignment`.
- Alignment failure reason: `raw coordinate gate passes, but clean target alignment fails`.
- Baseline framing valid: `true`.
- Overlay alignment valid: `false`.
- Ready for cloth seam surface: `false`.
- Ribbon count: 41.
- Group count: 4.
- Depth group count: 4.
- UV count equals vertex count.

## Boundaries

- This is a hair ribbon candidate, not final production hair.
- Side/back references remain soft constraints.
- No v8 output is modified or replaced.
- No commercial image-to-3D API is used.
- The candidate is still a proxy/DCC handoff asset, not final groomed production hair.
- The previous black-occlusion render is preserved as a negative fixture; if that failure recurs, validation must report `failed_visual_sanity`.
- This route remains a candidate, not an accepted or integrated replacement.
- Coordinate-space debug indicates the validator projection is usable, but the
  current target mask is too dirty to treat `candidate_is_hair_only` as proven.

## Next

Next step: `fix_authored_hair_ribbons_v0_to_refined_target`.

`cloth_seam_surface` remains paused. Do not replace v8 beauty hair in the meantime.
