# YUNA Semantic v10 Backlog

## Recommended Order

1. `boot_hardsurface_ortho`
2. `leg_quad_loop_retopo_proxy`
3. `authored_hair_ribbons`
4. `fix_authored_hair_ribbons_v0_geometry_alignment`
5. `review_and_refine_hair_target_masks_v0`
6. `build_hair_target_schema_v1`
7. `fix_hair_ribbons_to_schema_v1`
8. `build_art_directed_hair_ribbons_v1`
9. `manual_review_art_directed_hair_ribbons_v1_quality`
10. `cloth_seam_surface`
11. `weapon_hardsurface_ortho_v1`

## 1. Boot Hard-Surface Ortho

Status: completed as `boot_hardsurface_ortho_v0`.

Goal:

- Generate independent boot candidates with thickness, bevel proxy, material separation, and validation screenshots.

Acceptance:

- Boots remain independent.
- Existing v8 boot beauty stays active until candidate validation passes.
- No leg/cage debug volumes leak into beauty.
- Screenshots: front, yaw15, yaw30, side, wire, exploded.

Remaining for v1:

- Remove leg/cloth texture residue from the boot source.
- Separate left/right boot intent more cleanly.
- Do not replace v8 beauty boots until integration validation passes.

## 2. Leg Quad-Loop Retopo Proxy

Status: completed as `leg_quad_loop_retopo_proxy_v0`.

Goal:

- Prepare a retopo proxy spec for continuous thigh/knee/shin/ankle loops.

Boundary:

- Do not attempt final production retopology automatically.
- Do not replace v8 leg visual panels in beauty until deformation tests exist.

Acceptance:

- Knee and ankle loop intent is machine-readable.
- Proxy remains debug/cage until validated.
- No gray volume guide leaks into beauty.

Remaining for v1:

- Add actual skinning/weight deformation tests for knee and ankle.
- Refine leg centerlines from hand-authored landmarks rather than alpha-only evidence.
- Keep v8 leg beauty panels active until deformation validation passes.

## 3. Authored Hair Ribbons

Status: generated as `authored_hair_ribbons_v0`, but rejected as a clean hair candidate.

Goal:

- Convert current hair cards into authored strand/ribbon candidate curves.
- Keep this as an independent candidate; do not replace v8 beauty hair.

Acceptance:

- At least three depth groups remain.
- Front identity and silhouette are preserved.
- Side/back remain soft constraints only.
- Black alpha leakage and candidate black-pixel ratios stay below visual sanity thresholds.
- Face/body over-occlusion stays below visual sanity thresholds.
- Candidate-only front render is constrained to a clean hair target, not only
  the overbroad v8 hair mask union.
- Baseline-only front render is full-frame and not boot-only.
- Overlay front render is a valid full baseline + aligned candidate review image.

Remaining for v1:

- Keep `replace_in_beauty_glb=false` until a reviewed integration pass accepts replacement.
- Replace alpha-derived guide lanes with hand-authored grooming curves.
- Add deformation/secondary-motion tests for the spring-hook metadata.
- Preserve the black-occlusion render as a negative fixture so similar failures become `failed_visual_sanity`.
- Coordinate alignment is a weak pass against the dirty v8 hair union; clean
  target validation currently fails.

## 4. Fix Authored Hair Ribbons v0 Geometry Alignment

Status: completed only for the dirty/overbroad render-space gate.

Goal:

- Separate raw coordinate alignment from clean hair-target acceptance.
- The coordinate-space diagnostic pass already showed the projected v8 hair union is usable:
  `hair_union_projection_valid=true` and `hair_union_projection_overlap_ratio=0.612788`.
- The component-local rebuild now passes candidate geometry alignment:
  `candidate_geometry_alignment_valid=true`, `hair_mask_iou=0.121116`,
  `outside_hair_mask_ratio=0.05764`.
- That pass is weak: the raw v8 hair union target is dirty/overbroad and
  overlaps body masks heavily.
- Clean target validation fails:
  `hair_union_target_is_clean=false`,
  `hair_union_body_overlap_ratio=0.844485`,
  `clean_hair_mask_iou=0.014959`,
  `clean_outside_hair_mask_ratio=0.973581`,
  `clean_candidate_is_hair_only=false`.

Acceptance:

- `validation_report.json` must not report `visual_sanity_status = passed`
  until the clean target gate passes.
- `validation_ci_report.json` includes candidate-only, baseline-only, overlay, wire, and exploded screenshots.
- `hair_union_projection_valid = true`.
- `candidate_geometry_alignment_valid = true`.
- `hair_mask_iou` and `outside_hair_mask_ratio` can only prove candidate
  alignment to the dirty v8 hair mask union.
- `clean_hair_mask_iou`, `clean_outside_hair_mask_ratio`, and
  `clean_candidate_is_hair_only` must pass before the candidate can be called
  hair-only.
- `baseline_framing_valid = true`.
- `overlay_alignment_valid = true` only after clean target validation.
- The candidate does not become a replacement for v8 beauty hair.
- If human review rejects the visual result again, keep the route as a failed/needs-rework candidate and do not proceed to cloth.

## 4b. Review and Refine Hair Target Masks v0

Status: required before manual hair quality review.

Goal:

- Confirm and clean the current v8 hair union target before using it as a
  quality gate for authored hair ribbons.

Acceptance:

- `hair_target_mask_clean.png` exists.
- `hair_target_mask_dirty_overlay.png` exists.
- `hair_target_cleaning_report.json` exists.
- `hair_union_target_is_clean=true` or the report explicitly keeps hair v0 as
  failed/needs-rework.
- `clean_hair_mask_iou` and `clean_outside_hair_mask_ratio` are the acceptance
  metrics for candidate hair-only status.
- `ready_for_cloth_seam_surface=false` until this gate passes.

Current evidence:

- `CharacterPackage/semantic_layer_v9_hair/target_review/hair_target_review_report.json`
- Refined component-prior target candidate IoU: `0.120324`.
- Refined component-prior outside ratio: `0.474535`.
- Current candidate is not inside the refined target.
- Recommended next: `fix_authored_hair_ribbons_v0_to_refined_target`.

## 4c. Build Hair Target Schema v1

Status: completed.

Goal:

- Build a three-layer target schema for future art-directed hair ribbons:
  `strict_hair_core`, `soft_hair_silhouette`, and
  `forbidden_nonhair_zone`.

Artifacts:

- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/strict_hair_core_mask.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/soft_hair_silhouette_mask.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/forbidden_nonhair_zone_mask.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/candidate_vs_schema_overlay.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/schema_debug_contact_sheet.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/hair_target_schema_v1_report.json`

Current result:

- `schema_ready_for_ribbon_rebuild=true`.
- `candidate_target_schema_status=failed_target_schema_alignment`.
- `core_body_overlap_ratio=0.0`.
- `soft_body_overlap_ratio=0.0`.
- `forbidden_candidate_leak_ratio=0.975006`.
- `candidate_core_coverage_ratio=0.041425`.
- `candidate_soft_inside_ratio=0.021113`.
- `ready_for_cloth_seam_surface=false`.

## 4d. Fix Hair Ribbons to Schema v1

Status: leak/alignment gate passed, but non-degenerate coverage failed.

Goal:

- Rebuild authored hair ribbons so candidate-visible render is constrained by
  `hair_target_schema_v1`, not raw/refined union alone.

Acceptance:

- `forbidden_candidate_leak_ratio` is below schema threshold.
- `candidate_soft_inside_ratio` is above schema threshold.
- `candidate_core_coverage_ratio` is high enough for manual review.
- Candidate still has four hair groups and at least three depth groups.
- No black alpha leakage regression.
- `replace_in_beauty_glb=false`.
- `ready_for_cloth_seam_surface=false` until manual review accepts screenshots.

Previous result:

- A schema-constrained rebuild now uses generated group masks under
  `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/group_masks/`.
- Four hair groups and four depth groups are preserved.
- `replace_in_beauty_glb=false`.
- Black alpha leakage remains under threshold.
- Metrics improved but did not pass:
  - `forbidden_candidate_leak_ratio`: `0.975006 -> 0.299879`
  - `candidate_core_coverage_ratio`: `0.041425 -> 0.196487`
  - `candidate_soft_inside_ratio`: `0.021113 -> 0.557359`
- `candidate_target_schema_status=failed_target_schema_alignment`.
- `ready_for_cloth_seam_surface=false`.

## 4e. Build Art-Directed Hair Ribbons v1

Status: completed as an additive candidate; manual visual review is required.

Goal:

- Replace the underfilled/schema-clipped v0-style candidate with an
  art-directed candidate driven by `hair_design_schema_v1.json`.
- Use named primary groups, secondary strands, limited flyaways, scalp-anchor
  continuity, and multiple depth groups.
- Keep the candidate independent and additive.

Current result:

- `route=build_art_directed_hair_ribbons_v1`
- `actuator=art_directed_hair_ribbons_v1`
- `status=art_directed_candidate_manual_review_required`
- `non_degenerate_hair_coverage_passed=true`
- `candidate_visible_area_ratio=0.007020`
- `soft_silhouette_coverage_ratio=0.341499`
- `candidate_core_coverage_ratio=0.341135`
- `candidate_soft_inside_ratio=0.822168`
- `forbidden_candidate_leak_ratio=0.020550`
- `bangs_presence_ratio=0.214286`
- `side_hair_left_presence_ratio=0.493036`
- `side_hair_right_presence_ratio=0.911678`
- `back_hair_mass_presence_ratio=0.794342`
- `component_count=6`
- `scalp_anchor_continuity=0.214286`
- `ribbon_count=25`
- `depth_group_count=6`
- `art_directed_primitive_intent_count=25`
- `flow_continuity_passed=true`
- `replace_in_beauty_glb=false`
- `ready_for_cloth_seam_surface=false`

Artifacts:

- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/target_schema_v1_eval/hair_target_schema_v1_report.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_front.png`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_yaw15.png`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_yaw30.png`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_side.png`

Visual review:

- Better than v0 underfilled/barcode strips.
- Yaw15/yaw30 show cleaner layered hair-card mass.
- The prior blocky side-profile volume rectangles were removed from the
  candidate beauty route.
- Candidate-only front is still sparse at full-body framing.
- Do not call this accepted production hair without human review.

Next:

- `manual_review_art_directed_hair_ribbons_v1_quality`
- If rejected, refine v1 front scalp integration and authored curve placement
  without reintroducing blocky side-profile volume panels.
- Do not proceed to `cloth_seam_surface` until manual review accepts hair.

Previous result:

- A tightened schema-constrained rebuild keeps the four hair groups and four
  depth groups while applying forbidden-zone guard and render-space correction.
- `forbidden_candidate_leak_ratio`: `0.975006 -> 0.299879 -> 0.010006`.
- `candidate_core_coverage_ratio`: `0.041425 -> 0.196487 -> 0.187749`.
- `candidate_soft_inside_ratio`: `0.021113 -> 0.557359 -> 0.916398`.
- `candidate_target_schema_status=schema_gate_passed_manual_review_required`.
- `replace_in_beauty_glb=false`.
- `ready_for_cloth_seam_surface=false`.

Current result:

- `candidate_target_schema_status=schema_gate_passed_manual_review_failed_underfilled`.
- The candidate passes leak/soft-inside/core metrics but is too sparse and fragmented:
  - `candidate_visible_area_ratio=0.003227` below threshold `0.005`.
  - `soft_silhouette_coverage_ratio=0.174971` below threshold `0.25`.
  - `bangs_presence_ratio=0.066363` below threshold `0.15`.
  - `side_hair_left_presence_ratio=0.259981` below threshold `0.30`.
  - `component_count=39` above maximum `32`.
  - `scalp_anchor_continuity=0.066363` below threshold `0.15`.
- `non_degenerate_hair_coverage_passed=false`.
- `hair_design_schema_v1.json` now defines the next art-directed hair rebuild contract.

Remaining:

- Build `build_art_directed_hair_ribbons_v1` from the design schema rather than
  continuing to shrink alpha-derived ribbons.

## 4e. Manual Review Authored Hair Ribbons v0 Quality

Status: blocked by underfilled/non-degenerate coverage failure.

Goal:

- Decide whether the coordinate-aligned hair candidate is visually acceptable as a hair-only DCC candidate.

Acceptance:

- Human review accepts candidate-only, baseline-only, overlay, yaw15, yaw30, side, wire, and exploded screenshots.
- `manual_visual_review` is updated from `pending` to `accepted`.
- `replace_in_beauty_glb` remains `false` until a separate integration pass is explicitly approved.
- If review rejects the visual result, keep this route as needs-rework and do not proceed to cloth.

## 4f. Hair Design Schema v1

Status: added.

Goal:

- Define an art-directed rebuild contract for non-degenerate hair coverage:
  bangs primary, side hair left/right, back hair mass, secondary strands,
  flyaways, scalp anchors, depth groups, face occlusion zones, and allowed
  silhouette expansion.

Artifact:

- `CharacterPackage/semantic_layer_v9_hair/hair_design_schema_v1.json`

Next:

- Implement `build_art_directed_hair_ribbons_v1` against this design schema.

## 5. Cloth Seam Surface

Status: paused until underfilled hair route is rebuilt and manual review accepts it.

Goal:

- Upgrade cape/skirt cloth sheets into seam-aware surfaces with attachment metadata.

Acceptance:

- Cape remains independent from torso.
- Cloth has visible front/yaw validation.
- Swing/attachment hooks are preserved.

## 6. Weapon Hard-Surface Ortho v1

Goal:

- Clean weapon source texture/mask residue and split weapon into blade/guard/handle subparts.

Acceptance:

- No body/cloth residue in the weapon texture.
- Subparts are independently named.
- GLB roundtrip preserves material slots and socket metadata.
