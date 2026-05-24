# Resonance Afterlight YUNA 2.5D-to-3D

This repository is a curated migration of the local OpenDesign project
`resonance-afterlight-20260521-692194ef`.

It preserves the runnable HTML prototype, generated visual assets, and the
current best YUNA `semantic_layer_v8` DCC handoff package.

## What This Is

- A local research/prototype package for anime RPG UI and 2.5D-to-3D character asset construction.
- A deterministic, inspectable alternative to black-box image-to-3D output.
- A handoff repo for further Blender/DCC cleanup, retopology, boot reconstruction, and Unity validation.

## What This Is Not

- Not a final production-ready rigged YUNA character.
- Not a commercial image-to-3D API wrapper.
- Not a full copy of OpenDesign runtime state.

## Main Entrypoints

- `index.html`: OpenDesign prototype entry.
- `asset-composite.html`: 2D composite prototype.
- `asset-composite-3d.html`: Three.js/WebGL scene prototype.
- `asset-composite-3d-roster.html`: Three.js roster scene prototype.
- `CharacterPackage/README.md`: detailed YUNA DCC/package inventory.
- `CharacterPackage/semantic_layer_v8/`: current best semantic-layer visual-review output.

## Current Best 3D Asset Route

Use `CharacterPackage/semantic_layer_v8/`:

- `exports/yuna_semantic_layer_v8.glb`: main beauty/review GLB.
- `exports/yuna_semantic_layer_v8_cage_debug.glb`: debug GLB with DCC guides.
- `exports/yuna_semantic_layer_v8.fbx`: FBX handoff export.
- `exports/yuna_semantic_layer_v8.obj`: OBJ static geometry export.
- `validation/`: front, yaw15, yaw30, side cage, wire, exploded, mask and constraint screenshots.
- `validation_report.json`: machine-readable export/roundtrip report.

The v8 route intentionally keeps the beauty GLB separate from the DCC debug cage.
The main GLB no longer exposes the gray leg/boot guide volumes that made the
legs look broken in earlier versions.

## Migration Scope

This repo includes:

- top-level HTML prototypes and visible assets
- screenshots for review
- YUNA references, docs, metadata and scripts
- `semantic_layer_v8` exports, textures, masks, reports and validation images
- small Unity-facing editor tools/prefab assets

This repo excludes:

- the `.od` runtime database and cache
- older `semantic_layer_v1` through `semantic_layer_v7` full output folders
- Unity generated `Library`, `Temp`, `Logs`, and user settings
- local tool caches and Python bytecode

See `MIGRATION_MANIFEST.md` for exact notes.

## Local Provenance

Migrated from:

`/Users/gengrf/open-design/.od/projects/resonance-afterlight-20260521-692194ef`

Generated on local macOS with Blender/OpenDesign tooling.
