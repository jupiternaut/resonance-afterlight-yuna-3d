# YUNA Semantic v9 Actuator Run Report

## Summary

This run upgraded the read-only `semantic_layer_v9_candidate` into a small
checkpointed actuator loop. The executable actuators currently completed are:

- `weapon_hardsurface_ortho_v0`
- `boot_hardsurface_ortho_v0`
- `leg_quad_loop_retopo_proxy_v0`
- `authored_hair_ribbons_v0`

No `semantic_layer_v8` outputs were modified or replaced.

## Commands Run

```bash
python3 CharacterPackage/tools/semantic_state_filter_v0.py
python3 -m pytest CharacterPackage/tools/tests -q
python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v
python3 CharacterPackage/tools/build_yuna_semantic_layer_v9_weapon.py
python3 CharacterPackage/tools/build_yuna_semantic_layer_v9_boot.py
python3 CharacterPackage/tools/build_yuna_semantic_layer_v9_leg.py
python3 CharacterPackage/tools/build_yuna_semantic_layer_v9_hair.py
python3 CharacterPackage/tools/run_blender_semantic_validation.py --help
python3 CharacterPackage/tools/run_blender_semantic_validation.py
python3 CharacterPackage/tools/run_blender_semantic_validation.py \
  --candidate-glb CharacterPackage/semantic_layer_v9_boot/exports/yuna_semantic_layer_v9_boot.glb \
  --candidate-report CharacterPackage/semantic_layer_v9_boot/validation_report.json \
  --output-dir CharacterPackage/semantic_layer_v9_boot/validation_ci \
  --report CharacterPackage/semantic_layer_v9_boot/validation_ci/validation_ci_report.json
python3 CharacterPackage/tools/run_blender_semantic_validation.py \
  --candidate-glb CharacterPackage/semantic_layer_v9_leg/exports/yuna_semantic_layer_v9_leg.glb \
  --candidate-report CharacterPackage/semantic_layer_v9_leg/validation_report.json \
  --output-dir CharacterPackage/semantic_layer_v9_leg/validation_ci \
  --report CharacterPackage/semantic_layer_v9_leg/validation_ci/validation_ci_report.json
python3 CharacterPackage/tools/run_blender_semantic_validation.py \
  --candidate-glb CharacterPackage/semantic_layer_v9_hair/exports/yuna_semantic_layer_v9_hair.glb \
  --candidate-report CharacterPackage/semantic_layer_v9_hair/validation_report.json \
  --output-dir CharacterPackage/semantic_layer_v9_hair/validation_ci \
  --report CharacterPackage/semantic_layer_v9_hair/validation_ci/validation_ci_report.json
python3 -m compileall CharacterPackage/tools
git diff --name-only -- CharacterPackage/semantic_layer_v8
git diff --stat
```

`pytest` is not installed in the current Python environment, so the accepted
checkpoint test runner for this pass was `unittest`.

## Tests

- `python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v`
- Result: 43 tests passed.

Coverage added in this run:

- v9 candidate JSON contract.
- side/back soft-constraint contract.
- beauty/cage split contract.
- weapon/boots upgrade decision contract.
- debug-only guides cannot appear in beauty.
- weapon actuator mesh/OBJ/report contract.
- boot actuator mesh/OBJ/report contract.
- leg quad-loop retopo proxy mesh/OBJ/report contract.
- authored hair ribbon source/mesh/OBJ/report contract.
- authored hair ribbon mask/texture, alpha bbox, missing hook/depth rejection, Blender skip, and v8 unchanged contracts.
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

Boot actuator:

- `CharacterPackage/semantic_layer_v9_boot/specs/yuna_semantic_layer_v9_boot.json`
- `CharacterPackage/semantic_layer_v9_boot/exports/yuna_semantic_layer_v9_boot.obj`
- `CharacterPackage/semantic_layer_v9_boot/exports/yuna_semantic_layer_v9_boot.mtl`
- `CharacterPackage/semantic_layer_v9_boot/exports/yuna_semantic_layer_v9_boot.glb`
- `CharacterPackage/semantic_layer_v9_boot/exports/yuna_semantic_layer_v9_boot.blend`
- `CharacterPackage/semantic_layer_v9_boot/validation_report.json`

Boot Blender validation:

- `CharacterPackage/semantic_layer_v9_boot/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v9_boot/validation_ci/yuna_semantic_layer_v9_boot_validation_front.png`
- `CharacterPackage/semantic_layer_v9_boot/validation_ci/yuna_semantic_layer_v9_boot_validation_yaw15.png`
- `CharacterPackage/semantic_layer_v9_boot/validation_ci/yuna_semantic_layer_v9_boot_validation_yaw30.png`
- `CharacterPackage/semantic_layer_v9_boot/validation_ci/yuna_semantic_layer_v9_boot_validation_side.png`
- `CharacterPackage/semantic_layer_v9_boot/validation_ci/yuna_semantic_layer_v9_boot_validation_wire.png`
- `CharacterPackage/semantic_layer_v9_boot/validation_ci/yuna_semantic_layer_v9_boot_validation_exploded.png`

Leg retopo proxy actuator:

- `CharacterPackage/semantic_layer_v9_leg/specs/yuna_semantic_layer_v9_leg.json`
- `CharacterPackage/semantic_layer_v9_leg/exports/yuna_semantic_layer_v9_leg.obj`
- `CharacterPackage/semantic_layer_v9_leg/exports/yuna_semantic_layer_v9_leg.mtl`
- `CharacterPackage/semantic_layer_v9_leg/exports/yuna_semantic_layer_v9_leg.glb`
- `CharacterPackage/semantic_layer_v9_leg/exports/yuna_semantic_layer_v9_leg.blend`
- `CharacterPackage/semantic_layer_v9_leg/validation_report.json`

Leg Blender validation:

- `CharacterPackage/semantic_layer_v9_leg/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v9_leg/validation_ci/yuna_semantic_layer_v9_leg_validation_front.png`
- `CharacterPackage/semantic_layer_v9_leg/validation_ci/yuna_semantic_layer_v9_leg_validation_yaw15.png`
- `CharacterPackage/semantic_layer_v9_leg/validation_ci/yuna_semantic_layer_v9_leg_validation_yaw30.png`
- `CharacterPackage/semantic_layer_v9_leg/validation_ci/yuna_semantic_layer_v9_leg_validation_side.png`
- `CharacterPackage/semantic_layer_v9_leg/validation_ci/yuna_semantic_layer_v9_leg_validation_wire.png`
- `CharacterPackage/semantic_layer_v9_leg/validation_ci/yuna_semantic_layer_v9_leg_validation_exploded.png`

Authored hair ribbon actuator:

- `CharacterPackage/semantic_layer_v9_hair/specs/yuna_semantic_layer_v9_hair.json`
- `CharacterPackage/semantic_layer_v9_hair/exports/yuna_semantic_layer_v9_hair.obj`
- `CharacterPackage/semantic_layer_v9_hair/exports/yuna_semantic_layer_v9_hair.mtl`
- `CharacterPackage/semantic_layer_v9_hair/exports/yuna_semantic_layer_v9_hair.glb`
- `CharacterPackage/semantic_layer_v9_hair/exports/yuna_semantic_layer_v9_hair.blend`
- `CharacterPackage/semantic_layer_v9_hair/validation_report.json`

Hair Blender validation:

- `CharacterPackage/semantic_layer_v9_hair/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_front.png`
- `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_yaw15.png`
- `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_yaw30.png`
- `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_side.png`
- `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_wire.png`
- `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_exploded.png`

Executable plan:

- `CharacterPackage/semantic_layer_v9_candidate/specs/yuna_semantic_layer_v9_executable_plan.json`

Progress and backlog:

- `CharacterPackage/semantic_layer_v9_candidate/backlog_v10.md`
- `CharacterPackage/semantic_layer_v9_candidate/goal_progress_hair_ribbons.md`

## Result

The weapon candidate status is `generated_with_warnings`.

The weapon Blender validation status is `passed_with_warnings`.

The boot candidate status is `generated_with_warnings`.

The boot Blender validation status is `passed_with_warnings`.

The leg retopo proxy candidate status is `generated_with_warnings`.

The leg Blender validation status is `passed_with_warnings`.

The authored hair ribbon candidate status is `generated_with_warnings`.

The hair Blender validation status is `passed_with_warnings`.

The hair visual sanity status is `passed`.

After the coordinate-space debug pass and component-local rebuild, the authored
hair route no longer fails the coordinate alignment gate.

The v8 hair union projection is valid enough for the current render-space gate:
`hair_union_projection_valid=true` with
`hair_union_projection_overlap_ratio=0.612788`. The candidate geometry now
aligns to that projected hair union:
`candidate_geometry_alignment_valid=true`, `hair_mask_iou=0.121116`, and
`outside_hair_mask_ratio=0.05764`.

This means the previous coordinate/scale/origin blocker is fixed. The route
still remains a candidate only: `manual_visual_review=pending` and
`replace_in_beauty_glb=false`.

The alpha leak and artifact-generation parts of the route are fixed, but the
candidate is not integrated into v8 beauty. It requires manual visual review
before any later actuator is unblocked.

The candidate has:

- independent weapon mesh
- thickness
- bevel proxy
- front texture material
- side material
- `hand_R_socket` metadata
- OBJ and GLB exports
- screenshot validation evidence

The boot candidate has:

- independent boot component meshes
- thickness
- bevel proxy
- front texture material
- side material
- `foot_L_socket` and `foot_R_socket` metadata
- OBJ and GLB exports
- screenshot validation evidence

The leg candidate has:

- independent left/right leg proxy meshes
- 28 vertical loop rings and 12 radial segments
- quad faces only
- knee and ankle loop marker metadata
- UVs from the v8 leg texture
- OBJ and GLB exports
- screenshot validation evidence

The hair candidate has:

- 41 independent ribbon strip meshes
- four source hair groups: back hair, side hair left, side hair right, bangs
- four depth groups
- UVs from the v8 hair textures
- sanitized per-group alpha textures
- thin ribbon side material
- spring-hook metadata for each hair group
- OBJ and GLB exports
- screenshot validation evidence
- candidate-only, baseline-only, and overlay front screenshots
- visual sanity metrics: `black_alpha_leak_fixed=true`,
  `numeric_metrics_passed=true`, `black_alpha_leak_ratio=0.000625`,
  `candidate_black_pixel_ratio=0.000031`,
  `face_occlusion_ratio=0.040282`,
  `non_hair_occlusion_ratio=0.023251`,
  `hair_union_projection_valid=true`,
  `hair_union_projection_overlap_ratio=0.612788`,
  `candidate_geometry_alignment_valid=true`,
  `coordinate_mapping_status=passed`,
  `hair_mask_iou=0.121116`, `outside_hair_mask_ratio=0.05764`,
  `candidate_is_hair_only=true`,
  `baseline_framing_valid=true`,
  `overlay_alignment_valid=true`,
  `ready_for_cloth_seam_surface=false`
- coordinate-space debug evidence:
  `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_v8_hair_union_mask_projected_on_baseline.png`,
  `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_candidate_visible_mask.png`,
  `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_candidate_mask_vs_hair_union_overlay.png`,
  `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_candidate_bbox_vs_hair_union_bbox.png`,
  and `CharacterPackage/semantic_layer_v9_hair/validation_ci/coordinate_mapping_debug.json`

## Known Limits

- This is an alpha-profile hard-surface proxy, not final hand-modeled weapon art.
- The source weapon texture still contains some body/cloth residue from the v8 texture extraction.
- Boot v0 splits visible boot texture components but still includes leg/cloth texture residue from the v8 source texture.
- Boot v0 does not solve continuous leg, knee, ankle, or skinning topology.
- Leg v0 is a quad-loop retopo proxy, not final production leg topology.
- Knee and ankle markers are metadata only; no skinning or weight test has run yet.
- Hair v0 derives deterministic guide ribbons from v8 mask bounds and texture alpha; it is not final hand-authored strand grooming.
- Hair v0 is coordinate-aligned, but still awaits manual visual review before any integration decision.
- The validator projection is usable, and the candidate geometry now passes the current render-space hair mask gate.
- Hair side/back treatment remains a soft depth spread only, not locked multiview reconstruction.
- The earlier hair front-render black occlusion is preserved as a negative fixture and now fails visual sanity if it recurs.
- The candidate is not integrated into the v8 beauty GLB.
- `replace_in_beauty_glb` remains `false`.
- v8 remains the active visual-review baseline.

## Next Step

Next step: `manual_review_authored_hair_ribbons_v0_quality`.

Reason: `cloth_seam_surface` is intentionally paused. Hair generated artifacts,
fixed the black-alpha failure mode, and now passes the coordinate alignment
gate. Do not start another actuator until a human accepts the candidate-only,
baseline-only, overlay, yaw, and side screenshots as a usable hair candidate.
