# Cloth Seam Surface v0 Handoff

## Git

- Branch: `feature/cloth-seam-surface-v0`
- Source/base commit: `41ce28d`
- Base branch: `origin/feature/authored-hair-ribbons-v0`

## Route Boundary

- Route: `semantic_layer_v9_cloth_seam_surface_v0`
- Output directory: `CharacterPackage/semantic_layer_v9_cloth/`
- Candidate-only: yes
- DCC handoff only: yes
- Production cloth topology: no
- `replace_in_beauty_glb`: false
- v8 beauty replacement: no
- Side/back constraints: soft constraints only
- Current blocker: hair route still blocks cloth integration
- Cloth integration status: blocked/pending, not unblocked by this route

## Target Parts

- `jacket_outer`
- `cape_left`
- `cape_right`
- `skirt_front`

## Generated Files

- `CharacterPackage/semantic_layer_v9_cloth/specs/yuna_semantic_layer_v9_cloth.json`
- `CharacterPackage/semantic_layer_v9_cloth/exports/yuna_semantic_layer_v9_cloth.obj`
- `CharacterPackage/semantic_layer_v9_cloth/exports/yuna_semantic_layer_v9_cloth.mtl`
- `CharacterPackage/semantic_layer_v9_cloth/exports/yuna_semantic_layer_v9_cloth.glb`
- `CharacterPackage/semantic_layer_v9_cloth/exports/yuna_semantic_layer_v9_cloth.blend`
- `CharacterPackage/semantic_layer_v9_cloth/validation_report.json`
- `CharacterPackage/semantic_layer_v9_cloth/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v9_cloth/validation_ci/yuna_semantic_layer_v9_cloth_validation_front.png`
- `CharacterPackage/semantic_layer_v9_cloth/validation_ci/yuna_semantic_layer_v9_cloth_validation_candidate_front.png`
- `CharacterPackage/semantic_layer_v9_cloth/validation_ci/yuna_semantic_layer_v9_cloth_validation_baseline_front.png`
- `CharacterPackage/semantic_layer_v9_cloth/validation_ci/yuna_semantic_layer_v9_cloth_validation_overlay_front.png`
- `CharacterPackage/semantic_layer_v9_cloth/validation_ci/yuna_semantic_layer_v9_cloth_validation_yaw15.png`
- `CharacterPackage/semantic_layer_v9_cloth/validation_ci/yuna_semantic_layer_v9_cloth_validation_yaw30.png`
- `CharacterPackage/semantic_layer_v9_cloth/validation_ci/yuna_semantic_layer_v9_cloth_validation_side.png`
- `CharacterPackage/semantic_layer_v9_cloth/validation_ci/yuna_semantic_layer_v9_cloth_validation_wire.png`
- `CharacterPackage/semantic_layer_v9_cloth/validation_ci/yuna_semantic_layer_v9_cloth_validation_exploded.png`
- `CharacterPackage/semantic_layer_v9_cloth/textures/jacket_outer.png`
- `CharacterPackage/semantic_layer_v9_cloth/textures/cape_left.png`
- `CharacterPackage/semantic_layer_v9_cloth/textures/cape_right.png`
- `CharacterPackage/semantic_layer_v9_cloth/textures/skirt_front.png`

## Validation Metrics

- Build status: `generated_with_warnings`
- Blender export: `ok`
- Validation CI status: `passed_with_warnings`
- Screenshot count: 9
- Missing screenshots: none
- Candidate mesh count: 12
- Candidate empty count: 21
- Cloth surface components: 4
- Vertices: 828
- UVs: 828
- Faces: 704
- Quad faces only: true
- GLB bytes: 6390076
- BLEND generated: true
- Seam metadata present:
  - shoulder anchors: true
  - cape roots: true
  - skirt waist seam: true
  - lower cloth edge: true

## Checks

- `python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v`: passed, 67 tests
- `python3 -m compileall CharacterPackage/tools`: passed
- `git diff --name-only -- CharacterPackage/semantic_layer_v8`: empty
- `git diff --name-only -- CharacterPackage/semantic_layer_v9_hair`: empty

## Blocker

This cloth route is independent and candidate-only. Hair remains blocked/pending, and the hair route still blocks cloth integration. This handoff does not modify the hair blocker and does not mark cloth as ready for integration.
