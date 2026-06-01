# Cloth Seam Surface Handoff

## Git

- Branch: `feature/cloth-seam-surface-v0`
- Current HEAD at handoff time: `5b80963`
- Source/base commit: `41ce28d`
- Base branch: `origin/feature/authored-hair-ribbons-v0`

## Route Boundary

- Base route: `semantic_layer_v9_cloth_seam_surface_v0`
- Review-pack route: `cloth_seam_surface_v1_review_pack`
- Output directory: `CharacterPackage/semantic_layer_v9_cloth/`
- Candidate-only: yes
- DCC handoff only: yes
- Production cloth topology: no
- `replace_in_beauty_glb`: false
- v8 beauty replacement: no
- Side/back constraints: soft constraints only
- Current blocker: hair route still blocks cloth integration
- Cloth integration status: blocked/pending, not unblocked by this route

## Target Parts

- `jacket_outer`
- `cape_left`
- `cape_right`
- `skirt_front`

## Generated Base Files

- `CharacterPackage/semantic_layer_v9_cloth/specs/yuna_semantic_layer_v9_cloth.json`
- `CharacterPackage/semantic_layer_v9_cloth/exports/yuna_semantic_layer_v9_cloth.obj`
- `CharacterPackage/semantic_layer_v9_cloth/exports/yuna_semantic_layer_v9_cloth.mtl`
- `CharacterPackage/semantic_layer_v9_cloth/exports/yuna_semantic_layer_v9_cloth.glb`
- `CharacterPackage/semantic_layer_v9_cloth/exports/yuna_semantic_layer_v9_cloth.blend`
- `CharacterPackage/semantic_layer_v9_cloth/validation_report.json`
- `CharacterPackage/semantic_layer_v9_cloth/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v9_cloth/validation_ci/cloth_target_mask_union.png`
- `CharacterPackage/semantic_layer_v9_cloth/validation_ci/cloth_forbidden_noncloth_zone.png`
- `CharacterPackage/semantic_layer_v9_cloth/validation_ci/cloth_candidate_vs_target_overlay.png`
- `CharacterPackage/semantic_layer_v9_cloth/validation_ci/cloth_purity_report.json`
- `CharacterPackage/semantic_layer_v9_cloth/validation_ci/cloth_side_volume_debug.png`
- `CharacterPackage/semantic_layer_v9_cloth/validation_ci/cloth_depth_span_report.json`

## Generated Review Pack

- Comparison report: `CharacterPackage/semantic_layer_v9_cloth/variants/cloth_variants_comparison_report.json`
- Contact sheet: `CharacterPackage/semantic_layer_v9_cloth/variants/cloth_variants_contact_sheet.png`
- Iteration log: `CharacterPackage/semantic_layer_v9_cloth/variants/cloth_iteration_log.md`
- Manual review doc: `CharacterPackage/semantic_layer_v9_cloth/variants/manual_review_cloth_v1.md`
- Variant folders: `minimal/`, `heroic/`, `technical/`

Each variant folder contains:

- `specs/yuna_semantic_layer_v9_cloth_<variant>.json`
- `exports/yuna_semantic_layer_v9_cloth_<variant>.obj`
- `exports/yuna_semantic_layer_v9_cloth_<variant>.mtl`
- `exports/yuna_semantic_layer_v9_cloth_<variant>.glb`
- `exports/yuna_semantic_layer_v9_cloth_<variant>.blend`
- `validation_report.json`
- `validation_ci/validation_ci_report.json`
- `validation_ci/cloth_target_mask_union.png`
- `validation_ci/cloth_forbidden_noncloth_zone.png`
- `validation_ci/cloth_candidate_vs_target_overlay.png`
- `validation_ci/cloth_purity_report.json`
- `validation_ci/cloth_side_volume_debug.png`
- `validation_ci/cloth_depth_span_report.json`
- Screenshots: `candidate_front`, `overlay_front`, `yaw15`, `yaw30`, `side`, `wire`, `exploded`

## Review Pack Metrics

Overall status: `manual_review_required`

Recommended variant for manual review: `heroic`

| Variant | Score | Purity | Leak | Side volume | Edge thickness | Curvature | Drape span | Front readable | Yaw30 readable | Side readable |
| --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| minimal | 0.81828 | 1.0 | 0.0 | true | true | 0.138019 | 1.05545 | 0.88 | 0.68492 | 0.732199 |
| heroic | 0.938742 | 1.0 | 0.0 | true | true | 0.308569 | 1.26805 | 0.96 | 0.943997 | 0.858971 |
| technical | 0.874419 | 1.0 | 0.0 | true | true | 0.211425 | 1.144 | 0.92 | 0.801996 | 0.79168 |

Shared metrics:

- `cloth_body_attachment_valid`: true
- `seam_count`: 8
- `anchor_count`: 21
- `material_alpha_stability`: 1.0
- `cloth_dcc_handoff_status`: `manual_review_required_candidate_only_hair_blocked`
- `replace_in_beauty_glb`: false
- `ready_for_cloth_integration`: false

## Iteration Rounds

1. `minimal`: conservative comparison target; preserves v0 front read with the smallest side-volume push.
2. `heroic`: strongest side-volume and silhouette score; recommended for manual art review.
3. `technical`: seam-guide-heavy DCC interpretation; useful for construction review, not final art.

## Checks

- `python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v`: passed, 69 tests
- `python3 -m compileall CharacterPackage/tools`: passed
- `git diff --name-only -- CharacterPackage/semantic_layer_v8`: empty
- `git diff --name-only -- CharacterPackage/semantic_layer_v9_hair`: empty
- `git diff --check`: passed

## Blocker

This cloth route is independent and candidate-only. Hair remains blocked/pending, and the hair route still blocks cloth integration. This handoff does not modify the hair blocker and does not mark cloth as ready for integration.

## Exact Next Goal

Run human art review on `minimal`, `heroic`, and `technical`; choose one visual direction; then have DCC rebuild the selected direction as real cloth topology with UVs, rigging, deformation checks, and side/back production review. Do not integrate cloth until the hair route is accepted.
