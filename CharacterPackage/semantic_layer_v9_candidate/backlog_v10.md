# YUNA Semantic v10 Backlog

## Recommended Order

1. `boot_hardsurface_ortho`
2. `leg_quad_loop_retopo_proxy`
3. `authored_hair_ribbons`
4. `fix_authored_hair_ribbons_v0_alignment`
5. `cloth_seam_surface`
6. `weapon_hardsurface_ortho_v1`

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

Status: generated as `authored_hair_ribbons_v0`, but rejected as a hair candidate.

Goal:

- Convert current hair cards into authored strand/ribbon candidate curves.
- Keep this as an independent candidate; do not replace v8 beauty hair.

Acceptance:

- At least three depth groups remain.
- Front identity and silhouette are preserved.
- Side/back remain soft constraints only.
- Black alpha leakage and candidate black-pixel ratios stay below visual sanity thresholds.
- Face/body over-occlusion stays below visual sanity thresholds.
- Candidate-only front render is constrained to the v8 hair mask union.
- Baseline-only front render is full-frame and not boot-only.
- Overlay front render is a valid full baseline + aligned candidate review image.

Remaining for v1:

- Keep `replace_in_beauty_glb=false` until a reviewed integration pass accepts replacement.
- Replace alpha-derived guide lanes with hand-authored grooming curves.
- Add deformation/secondary-motion tests for the spring-hook metadata.
- Preserve the black-occlusion render as a negative fixture so similar failures become `failed_visual_sanity`.
- Fix current `failed_hair_mask_alignment` result before starting the cloth actuator.

## 4. Fix Authored Hair Ribbons v0 Alignment

Status: required before `cloth_seam_surface`.

Goal:

- Turn `authored_hair_ribbons_v0` from a generated artifact into a valid hair-only candidate.

Acceptance:

- `validation_report.json` reports `visual_sanity_status = passed` or `passed_with_minor_warnings`.
- `validation_ci_report.json` includes candidate-only, baseline-only, overlay, wire, and exploded screenshots.
- `hair_mask_iou` and `outside_hair_mask_ratio` prove candidate render is aligned to the v8 hair mask union.
- `candidate_is_hair_only = true`.
- `baseline_framing_valid = true`.
- `overlay_alignment_valid = true`.
- The candidate does not become a replacement for v8 beauty hair.
- If human review rejects the visual result again, keep the route as a failed/needs-rework candidate and do not proceed to cloth.

## 5. Cloth Seam Surface

Status: paused until manual hair review completes.

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
