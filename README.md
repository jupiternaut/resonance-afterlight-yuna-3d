# Resonance Afterlight YUNA 2.5D-to-3D

## What it is

This repository is a curated Resonance Afterlight prototype and YUNA character handoff package.

It preserves static HTML UI prototypes, generated character cutouts, a Three.js roster/stage experiment, and the current best YUNA 2.5D-to-3D semantic-layer asset route.

## Current state

- Top-level experience: static HTML prototypes.
- WebGL stack: bundled Three.js r128 files under `assets/vendor/`.
- Character package: `CharacterPackage/`.
- Current best YUNA route: `CharacterPackage/semantic_layer_v8/`.
- v8 main beauty asset: `CharacterPackage/semantic_layer_v8/exports/yuna_semantic_layer_v8.glb`.
- v8 DCC guide asset: `CharacterPackage/semantic_layer_v8/exports/yuna_semantic_layer_v8_cage_debug.glb`.
- v8 handoff exports: GLB, cage-debug GLB, FBX, OBJ, BLEND, textures, masks, validation screenshots, and `validation_report.json`.

v8 is still the current-best visual-review baseline. It keeps the beauty GLB separate from the DCC cage/debug GLB so gray guide volumes do not leak into the review asset.

## v9 partial experiments

The repository also contains partial v9 experiments:

- `CharacterPackage/semantic_layer_v9_candidate/`
- `CharacterPackage/semantic_layer_v9_weapon/`
- `CharacterPackage/semantic_layer_v9_boot/`
- `CharacterPackage/semantic_layer_v9_leg/`

These are candidate actuator outputs, not a new full-character route. Their reports state `generated_with_warnings` or `passed_with_warnings`, and their validation boundary is candidate-only. They do not replace the v8 beauty GLB.

Use v9 as targeted evidence for weapon hard-surface reconstruction, boot hard-surface proxy work, and leg quad-loop retopo proxy exploration. Use v8 when Fable5 needs the current full YUNA visual-review package.

## Run it

Open the static prototypes directly:

```bash
open index.html
open asset-composite.html
open asset-composite-3d.html
open asset-composite-3d-roster.html
open reference-one-to-one.html
```

If a browser blocks local asset loading, serve the folder:

```bash
python3 -m http.server 8000
```

Then open `http://127.0.0.1:8000`.

## Project layout

```text
index.html                         Main Resonance Afterlight UI prototype
asset-composite.html               2D character composite prototype
asset-composite-3d.html            Three.js stage prototype
asset-composite-3d-roster.html     Three.js roster prototype
reference-one-to-one.html          Reference inspection page
assets/                            Generated UI and character cutout assets
screenshots/                       Review screenshots
CharacterPackage/                  YUNA DCC, semantic-layer, Unity, docs, and tool package
CharacterPackage/semantic_layer_v8/ Current best full semantic-layer handoff
CharacterPackage/semantic_layer_v9_*/ Partial v9 candidate experiments
MIGRATION_MANIFEST.md              Curated migration inventory
CODEX_TASK.md                      Project invariants and anti-patterns
```

## Assets

The repository includes visible prototype assets, YUNA references, v8 semantic-layer exports, v9 partial candidate exports, validation screenshots, and small Unity-facing editor/prefab files.

It does not include the original `.od` runtime database, cache, older full v1-v7 semantic-layer output folders, Unity generated folders, or local tool caches.

## Limitations

- YUNA is not a final production-ready rigged character.
- v8 is a 2.5D DCC handoff asset, not final skinned topology.
- v9 outputs are partial experiments and should not be treated as the current full-body package.
- Unity runtime validation remains dependent on local Unity licensing and setup.
- Commercial image-to-3D API runs are not included as completed runtime assets.

## Maintainer

Keep `README.md`, `MIGRATION_MANIFEST.md`, `CODEX_TASK.md`, and `CharacterPackage/README.md` aligned. Fable5 should read this repository as a curated prototype plus asset-handoff package, with v8 as the current-best full route and v9 as partial candidate evidence.
