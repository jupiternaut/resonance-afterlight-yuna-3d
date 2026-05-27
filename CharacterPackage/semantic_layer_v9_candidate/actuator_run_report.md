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
- Result: 47 tests passed.

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
- Blender semantic validation dirty target and clean hair target rejection contract.

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
- `CharacterPackage/semantic_layer_v9_hair/validation_ci/hair_target_mask_clean.png`
- `CharacterPackage/semantic_layer_v9_hair/validation_ci/hair_target_mask_dirty_overlay.png`
- `CharacterPackage/semantic_layer_v9_hair/validation_ci/hair_target_cleaning_report.json`
- `CharacterPackage/semantic_layer_v9_hair/target_review/hair_target_review_report.json`
- `CharacterPackage/semantic_layer_v9_hair/target_review/hair_target_mask_refined_component_priors.png`
- `CharacterPackage/semantic_layer_v9_hair/target_review/candidate_vs_refined_hair_target_overlay.png`

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

The authored hair ribbon candidate status is `failed_clean_hair_mask_alignment`.

The hair Blender validation status is `failed_clean_hair_mask_alignment`.

The hair visual sanity status is `failed_clean_hair_mask_alignment`.

After the coordinate-space debug pass and component-local rebuild, the authored
hair route no longer fails the raw coordinate alignment gate, but this is only
a weak pass.

The v8 hair union projection is valid enough for the current render-space gate:
`hair_union_projection_valid=true` with
`hair_union_projection_overlap_ratio=0.612788`. The candidate geometry now
aligns to that projected hair union:
`candidate_geometry_alignment_valid=true`, `hair_mask_iou=0.121116`, and
`outside_hair_mask_ratio=0.05764`.

However, the raw v8 hair union target is dirty/overbroad:
`hair_union_body_overlap_ratio=0.844485`,
`hair_union_face_overlap_ratio=0.044609`, and
`hair_union_weapon_overlap_ratio=0.043164`. Against the clean target, the same
candidate fails: `clean_hair_mask_iou=0.014959`,
`clean_outside_hair_mask_ratio=0.973581`, and
`clean_candidate_is_hair_only=false`.

This means the previous coordinate/scale/origin blocker is mostly fixed, but
the hair candidate is not accepted. The route remains a candidate only:
`manual_visual_review=failed`, `replace_in_beauty_glb=false`, and
`ready_for_cloth_seam_surface=false`.

The alpha leak and artifact-generation parts of the route are fixed, but the
candidate is not integrated into v8 beauty. It requires target-mask cleanup and
another hair quality pass before any later actuator is unblocked.

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
  `coordinate_alignment_gate=weak_pass`,
  `coordinate_mapping_status=failed_clean_hair_mask_alignment`,
  `hair_mask_iou=0.121116`, `outside_hair_mask_ratio=0.05764`,
  `raw_candidate_is_hair_only=true`,
  `candidate_is_hair_only=false`,
  `hair_target_quality=dirty_or_overbroad`,
  `hair_union_target_is_clean=false`,
  `hair_union_body_overlap_ratio=0.844485`,
  `clean_hair_mask_iou=0.014959`,
  `clean_outside_hair_mask_ratio=0.973581`,
  `clean_candidate_is_hair_only=false`,
  `baseline_framing_valid=true`,
  `overlay_alignment_valid=false`,
  `ready_for_cloth_seam_surface=false`
- coordinate-space debug evidence:
  `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_v8_hair_union_mask_projected_on_baseline.png`,
  `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_candidate_visible_mask.png`,
  `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_candidate_mask_vs_hair_union_overlay.png`,
  `CharacterPackage/semantic_layer_v9_hair/validation_ci/yuna_semantic_layer_v9_hair_validation_candidate_bbox_vs_hair_union_bbox.png`,
  and `CharacterPackage/semantic_layer_v9_hair/validation_ci/coordinate_mapping_debug.json`
- target review evidence:
  `CharacterPackage/semantic_layer_v9_hair/target_review/hair_target_review_report.json`,
  `CharacterPackage/semantic_layer_v9_hair/target_review/hair_target_mask_raw_union.png`,
  `CharacterPackage/semantic_layer_v9_hair/target_review/hair_target_mask_strict_clean.png`,
  `CharacterPackage/semantic_layer_v9_hair/target_review/hair_target_mask_refined_component_priors.png`,
  and `CharacterPackage/semantic_layer_v9_hair/target_review/candidate_vs_refined_hair_target_overlay.png`
- refined target metrics:
  `refined_component_priors.candidate_alignment.iou=0.120324`,
  `refined_component_priors.candidate_alignment.outside_ratio=0.474535`,
  `refined_component_priors.candidate_alignment.candidate_is_inside_target=false`
- target schema v1 evidence:
  `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/hair_target_schema_v1_report.json`,
  `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/strict_hair_core_mask.png`,
  `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/soft_hair_silhouette_mask.png`,
  `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/forbidden_nonhair_zone_mask.png`,
  `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/candidate_vs_schema_overlay.png`,
  and `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/schema_debug_contact_sheet.png`
- target schema v1 metrics:
  `candidate_target_schema_status=failed_target_schema_alignment`,
  `schema_ready_for_ribbon_rebuild=true`,
  `core_body_overlap_ratio=0.0`,
  `soft_body_overlap_ratio=0.0`,
  `forbidden_candidate_leak_ratio=0.975006`,
  `candidate_core_coverage_ratio=0.041425`,
  `candidate_soft_inside_ratio=0.021113`

## Known Limits

- This is an alpha-profile hard-surface proxy, not final hand-modeled weapon art.
- The source weapon texture still contains some body/cloth residue from the v8 texture extraction.
- Boot v0 splits visible boot texture components but still includes leg/cloth texture residue from the v8 source texture.
- Boot v0 does not solve continuous leg, knee, ankle, or skinning topology.
- Leg v0 is a quad-loop retopo proxy, not final production leg topology.
- Knee and ankle markers are metadata only; no skinning or weight test has run yet.
- Hair v0 derives deterministic guide ribbons from v8 mask bounds and texture alpha; it is not final hand-authored strand grooming.
- Hair v0 is weakly coordinate-aligned to the dirty hair union, but fails clean hair target validation.
- The validator projection is usable, but the current v8 hair union target is too contaminated to support a `candidate_is_hair_only=true` claim.
- The clean target artifacts are now the primary evidence for the next hair pass.
- Target review v0 generated a refined component-prior target, but the current
  candidate still fails against it.
- Target schema v1 now provides strict hair core, soft hair silhouette, and
  forbidden nonhair zone masks. The schema is ready for a ribbon rebuild, but
  the current candidate fails it because most visible candidate pixels leak into
  the forbidden zone.
- Hair side/back treatment remains a soft depth spread only, not locked multiview reconstruction.
- The earlier hair front-render black occlusion is preserved as a negative fixture and now fails visual sanity if it recurs.
- The candidate is not integrated into the v8 beauty GLB.
- `replace_in_beauty_glb` remains `false`.
- v8 remains the active visual-review baseline.

## Next Step

Next step: `fix_hair_ribbons_to_schema_v1` follow-up or
`build_art_directed_hair_ribbons_v1`.

Reason: `cloth_seam_surface` is intentionally paused. Hair generated artifacts
and fixed the black-alpha failure mode, but the current candidate still fails
against the schema v1 strict/soft/forbidden target. Do not start another
actuator until the hair ribbons pass target-schema checks and a follow-up hair
quality gate passes.

## Fix Hair Ribbons to Schema v1 Update

This pass rebuilt the authored hair ribbons using schema v1 group masks instead
of the dirty raw/refined union target. The generated route remains an
independent candidate and does not replace v8 beauty.

Generated/updated artifacts:

- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/group_masks/`
- `CharacterPackage/semantic_layer_v9_hair/specs/yuna_semantic_layer_v9_hair.json`
- `CharacterPackage/semantic_layer_v9_hair/exports/yuna_semantic_layer_v9_hair.obj`
- `CharacterPackage/semantic_layer_v9_hair/exports/yuna_semantic_layer_v9_hair.mtl`
- `CharacterPackage/semantic_layer_v9_hair/exports/yuna_semantic_layer_v9_hair.glb`
- `CharacterPackage/semantic_layer_v9_hair/exports/yuna_semantic_layer_v9_hair.blend`
- `CharacterPackage/semantic_layer_v9_hair/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/hair_target_schema_v1_report.json`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/candidate_vs_schema_overlay.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/schema_debug_contact_sheet.png`

Preserved constraints:

- v8 remains unchanged.
- `replace_in_beauty_glb=false`.
- side/back remain soft constraints.
- four hair groups are preserved.
- four depth groups are preserved.
- `ready_for_cloth_seam_surface=false`.

Metric movement:

- `forbidden_candidate_leak_ratio`: `0.975006 -> 0.299879`
- `candidate_core_coverage_ratio`: `0.041425 -> 0.196487`
- `candidate_soft_inside_ratio`: `0.021113 -> 0.557359`
- `candidate_visible_pixel_count`: `45611 -> 9057`

Verdict:

- `candidate_target_schema_status=failed_target_schema_alignment`.
- This is a measurable improvement, not an accepted hair candidate.
- Manual visual review remains blocked by target-schema failure.
- `cloth_seam_surface` remains blocked.
