# YUNA v9 Project State

## Current State

- `CharacterPackage/semantic_layer_v8` is the immutable visual-review / DCC
  baseline.
- v9 actuator routes exist for weapon, boots, legs, and authored hair ribbons.
- Weapon, boot, and leg routes are additive candidates/proxies; they do not
  replace v8 beauty.
- `authored_hair_ribbons_v0` generated assets and fixed the black-alpha leak,
  but it is rejected as a clean hair candidate.
- Hair coordinate alignment is only a weak pass against the dirty v8 hair union.
- Clean/refined hair target checks still fail:
  - current status: `failed_clean_hair_mask_alignment`
  - current candidate is not accepted as hair-only
  - `ready_for_cloth_seam_surface=false`
- `cloth_seam_surface` remains blocked.

## Current Blocker

Build `hair_target_schema_v1` before any new actuator work:

- `strict_hair_core`
- `soft_hair_silhouette`
- `forbidden_nonhair_zone`

The target schema must separate real hair evidence from body, face, weapon,
cloth, leg, boot, and cape contamination before authored ribbons are rebuilt or
accepted.

## Current Evidence

- `CharacterPackage/semantic_layer_v9_hair/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v9_hair/target_review/hair_target_review_report.json`
- `CharacterPackage/semantic_layer_v9_hair/target_review/hair_target_mask_refined_component_priors.png`
- `CharacterPackage/semantic_layer_v9_candidate/backlog_v10.md`
- `CharacterPackage/semantic_layer_v9_candidate/actuator_run_report.md`

## Do Not Do

- Do not proceed to `cloth_seam_surface`.
- Do not accept raw/refined union IoU as final proof of hair quality.
- Do not replace v8 beauty.
- Do not call hair v0 accepted until target-schema checks and manual review pass.

## Required Verification

For implementation turns, run the narrowest relevant tests plus:

```bash
python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v
python3 -m compileall CharacterPackage/tools
git diff --name-only -- CharacterPackage/semantic_layer_v8
```
