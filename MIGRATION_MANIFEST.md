# Migration Manifest

## Source

Original local OpenDesign project:

`/Users/gengrf/open-design/.od/projects/resonance-afterlight-20260521-692194ef`

Original project size was about 1.5GB. The migrated GitHub package is curated
to keep the current useful source, assets, reports and v8 exports without
committing abandoned runtime cache or older bulky experiment outputs.

## Included

- Top-level HTML prototypes:
  - `index.html`
  - `asset-composite.html`
  - `asset-composite-3d.html`
  - `asset-composite-3d-roster.html`
  - `reference-one-to-one.html`
- Top-level `assets/` and `screenshots/`.
- `CharacterPackage/README.md`.
- `CharacterPackage/docs/`, `meta/`, `refs/`, `tools/`.
- `CharacterPackage/semantic_layer_v8/` including:
  - BLEND/GLB/FBX/OBJ exports
  - textures
  - masks
  - constraints
  - spec JSON
  - validation PNGs
  - `validation_report.json`
- `CharacterPackage/unity/editor_tools/` and `CharacterPackage/unity/prefabs/`.

## Excluded

- `.od` database/runtime files.
- Older full semantic-layer output folders v1-v7.
- Unity generated runtime folders.
- `__pycache__`, `.DS_Store`, logs and local tool scratchpads.

## Current Best Asset

`CharacterPackage/semantic_layer_v8/exports/yuna_semantic_layer_v8.glb`

Status: `generated_with_warnings`.

Boundary: visual-review and DCC handoff asset, not final skinned production topology.

## Next Work

1. Hand/assisted retopology for continuous leg quad loops.
2. Proper hard-surface boot reconstruction.
3. Knee/ankle skinning and deformation test.
4. Replace weapon panel with orthographic hard-surface mesh.
5. Add Blender screenshot validation as a repeatable CI-style task.
