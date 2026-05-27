# Goal Progress: authored_hair_ribbons_v0

Status: generated as an independent candidate actuator, but rejected by manual visual review.

## Implemented

- Added `authored_hair_ribbons_v0` under `CharacterPackage/tools/semantic_actuators/`.
- Reads v8 hair masks/textures for `back_hair`, `side_hair_left`, `side_hair_right`, and `bangs`.
- Generates independent ribbon meshes preserving four hair groups and four depth groups.
- Constrains ribbon lanes to hair-mask evidence instead of broad bounding-box panels.
- Writes sanitized per-group alpha textures so transparent pixels do not render as black.
- Adds visual sanity gates for black alpha leakage, face/body over-occlusion, hair-mask alignment, and baseline/overlay framing validity.
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
- Negative fixture from the bad black-occlusion render: `CharacterPackage/semantic_layer_v9_hair/negative_fixtures/yuna_semantic_layer_v9_hair_validation_front_failed_visual_fixture.png`

## Current Result

- Hair candidate status: `failed_candidate_geometry_alignment`.
- Blender validation status: `failed_candidate_geometry_alignment`.
- Manual visual review: `failed`.
- Visual sanity status: `failed_candidate_geometry_alignment`.
- Black alpha leak fixed: `true`.
- Numeric metrics passed: `true`.
- Black alpha leak ratio: `0.001292`.
- Candidate black pixel ratio: `0.000065`.
- Face occlusion ratio: `0.0571`.
- Non-hair occlusion ratio: `0.083743`.
- Hair mask IoU: `0.0`.
- Outside hair mask ratio: `1.0`.
- Candidate is hair-only: `false`.
- Hair union projection valid: `true`.
- Hair union projection overlap ratio: `0.612788`.
- Candidate geometry alignment valid: `false`.
- Coordinate mapping status: `failed_candidate_geometry_alignment`.
- Alignment failure reason: `hair union projection is valid but candidate geometry does not align`.
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
- This route remains an experimental artifact / negative-plus case, not an accepted hair candidate.
- Coordinate-space debug indicates the validator projection is usable; the next repair should fix candidate geometry placement/scale/origin/depth rather than rewriting the mask projection gate first.

## Next

Next step: `fix_authored_hair_ribbons_v0_geometry_alignment`.

`cloth_seam_surface` remains paused. Do not replace v8 beauty hair in the meantime.
