# YUNA Semantic v9 Actuator Run Report

## Summary

This run upgraded the read-only `semantic_layer_v9_candidate` into a small
checkpointed actuator loop. The first executable actuator is
`weapon_hardsurface_ortho_v0` because the weapon is an independent prop and can
be validated without replacing the v8 beauty character.

No `semantic_layer_v8` outputs were modified or replaced.

## Commands Run

```bash
python3 CharacterPackage/tools/semantic_state_filter_v0.py
python3 -m pytest CharacterPackage/tools/tests -q
python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v
python3 CharacterPackage/tools/build_yuna_semantic_layer_v9_weapon.py
python3 CharacterPackage/tools/run_blender_semantic_validation.py --help
python3 CharacterPackage/tools/run_blender_semantic_validation.py
git diff --stat
```

`pytest` is not installed in the current Python environment, so the accepted
checkpoint test runner for this pass was `unittest`.

## Tests

- `python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v`
- Result: 20 tests passed.

Coverage added in this run:

- v9 candidate JSON contract.
- side/back soft-constraint contract.
- beauty/cage split contract.
- weapon/boots upgrade decision contract.
- debug-only guides cannot appear in beauty.
- weapon actuator mesh/OBJ/report contract.
- Blender semantic validation CLI/help/default input contract.

## Generated Files

Weapon actuator:

- `CharacterPackage/semantic_layer_v9_weapon/specs/yuna_semantic_layer_v9_weapon.json`
- `CharacterPackage/semantic_layer_v9_weapon/exports/yuna_semantic_layer_v9_weapon.obj`
- `CharacterPackage/semantic_layer_v9_weapon/exports/yuna_semantic_layer_v9_weapon.mtl`
- `CharacterPackage/semantic_layer_v9_weapon/exports/yuna_semantic_layer_v9_weapon.glb`
- `CharacterPackage/semantic_layer_v9_weapon/exports/yuna_semantic_layer_v9_weapon.blend`
- `CharacterPackage/semantic_layer_v9_weapon/validation_report.json`

Blender validation:

- `CharacterPackage/semantic_layer_v9_weapon/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v9_weapon/validation_ci/yuna_semantic_layer_v9_weapon_validation_front.png`
- `CharacterPackage/semantic_layer_v9_weapon/validation_ci/yuna_semantic_layer_v9_weapon_validation_yaw15.png`
- `CharacterPackage/semantic_layer_v9_weapon/validation_ci/yuna_semantic_layer_v9_weapon_validation_yaw30.png`
- `CharacterPackage/semantic_layer_v9_weapon/validation_ci/yuna_semantic_layer_v9_weapon_validation_side.png`
- `CharacterPackage/semantic_layer_v9_weapon/validation_ci/yuna_semantic_layer_v9_weapon_validation_wire.png`
- `CharacterPackage/semantic_layer_v9_weapon/validation_ci/yuna_semantic_layer_v9_weapon_validation_exploded.png`

Executable plan:

- `CharacterPackage/semantic_layer_v9_candidate/specs/yuna_semantic_layer_v9_executable_plan.json`

## Result

The weapon candidate status is `generated_with_warnings`.

The Blender validation status is `passed_with_warnings`.

The candidate has:

- independent weapon mesh
- thickness
- bevel proxy
- front texture material
- side material
- `hand_R_socket` metadata
- OBJ and GLB exports
- screenshot validation evidence

## Known Limits

- This is an alpha-profile hard-surface proxy, not final hand-modeled weapon art.
- The source weapon texture still contains some body/cloth residue from the v8 texture extraction.
- The candidate is not integrated into the v8 beauty GLB.
- `replace_in_beauty_glb` remains `false`.
- v8 remains the active visual-review baseline.

## Next Recommended Actuator

Next actuator: `boot_hardsurface_ortho`.

Reason: boots are a high-value hard-surface cleanup target and are less risky
than continuous leg retopology. Full leg quad-loop retopo remains out of scope
for this pass.
