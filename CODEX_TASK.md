# Codex Task Context

## Project

Resonance Afterlight YUNA 2.5D-to-3D migration repo.

## Invariants

1. Do not treat this as final production-ready character art.
2. Do not use commercial image-to-3D APIs in this repo unless explicitly added as a separate experiment.
3. Preserve front-view identity as the highest-priority visual constraint.
4. Major semantic parts should remain independent where possible.
5. Every generated asset route should write a JSON report.
6. Every visual claim should be backed by validation screenshots or import/roundtrip checks.
7. Beauty exports and DCC debug/cage exports should remain separate.

## Current Milestone

The migrated current-best route is `semantic_layer_v8`.

Important files:

- `CharacterPackage/tools/build_yuna_semantic_layer_v8.py`
- `CharacterPackage/semantic_layer_v8/validation_report.json`
- `CharacterPackage/semantic_layer_v8/exports/yuna_semantic_layer_v8.glb`
- `CharacterPackage/semantic_layer_v8/exports/yuna_semantic_layer_v8_cage_debug.glb`

## Anti-Patterns

- Reintroducing gray DCC guide volumes into the beauty GLB.
- Calling 2.5D panels a final rigged mesh.
- Collapsing hair/cape/weapon/body into one fused mesh.
- Pushing generated Unity runtime cache.
