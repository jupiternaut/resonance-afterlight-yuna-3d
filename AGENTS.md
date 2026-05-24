# AGENTS.md

## Project

This repository contains the Resonance Afterlight YUNA 2.5D-to-3D research and
DCC handoff package. The current immutable baseline is
`CharacterPackage/semantic_layer_v8`.

## Layout

- `CharacterPackage/semantic_layer_v8/`: current visual-review/DCC baseline.
- `CharacterPackage/semantic_layer_v9_candidate/`: read-only v9 planning output.
- `CharacterPackage/tools/semantic_filter/`: semantic state filter v0.
- `CharacterPackage/tools/semantic_actuators/`: v9 actuator implementations.
- `CharacterPackage/tools/tests/`: Python tests for contracts and actuators.

## Commands

Run the read-only v9 candidate filter:

```bash
python3 CharacterPackage/tools/semantic_state_filter_v0.py
```

Run tests without extra dependencies:

```bash
python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v
```

If `pytest` is installed, this should also work:

```bash
python3 -m pytest CharacterPackage/tools/tests -q
```

Run v8 screenshot validation:

```bash
python3 CharacterPackage/tools/run_semantic_layer_validation_ci.py
```

Run the first v9 actuator:

```bash
python3 CharacterPackage/tools/build_yuna_semantic_layer_v9_weapon.py
```

Run v9 candidate validation:

```bash
python3 CharacterPackage/tools/run_blender_semantic_validation.py
```

## Hard Invariants

1. Do not modify or delete `semantic_layer_v8` outputs.
2. Do not reintroduce debug/cage guide volumes into the beauty GLB.
3. Do not call commercial image-to-3D APIs.
4. Do not treat side/back references as locked geometry truth.
5. Preserve front-view identity as the highest-priority constraint.
6. Every generated route must write a JSON report.
7. Every visual claim must have screenshot or import/roundtrip evidence.
8. If Blender is unavailable, write an explicit skipped/failed report with a reason.
9. Existing v8 beauty meshes remain until a candidate replacement passes validation.
10. Do not attempt full production retopology in this repo pass.

## Anti-Patterns

- Mutating v8 while testing a v9 candidate.
- Replacing the beauty GLB without a validation report.
- Treating GLB export success as production topology readiness.
- Letting debug-only guides leak into a beauty/candidate beauty export.
- Collapsing face, hair, cape, body, boots, and weapon into one fused mesh.
- Using side/back AI references as hard geometric truth.

## Done Criteria

- Tests pass with the narrowest relevant command.
- Generated assets have JSON reports.
- Validation screenshots or explicit skipped reports exist.
- v8 remains reproducible and unmodified.
- Diffs remain scoped to the current phase.
