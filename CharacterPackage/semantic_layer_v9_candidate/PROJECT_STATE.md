# YUNA v9 Project State

## Current State

- `CharacterPackage/semantic_layer_v8` is the immutable visual-review / DCC
  baseline.
- v9 actuator routes exist for weapon, boots, legs, and authored hair ribbons.
- Weapon, boot, and leg routes are additive candidates/proxies; they do not
  replace v8 beauty.
- `authored_hair_ribbons_v0` generated assets and fixed the black-alpha leak,
  but the tightened schema pass correctly rejected it as underfilled/sparse.
- `art_directed_hair_ribbons_v1` now exists as an additive candidate under
  `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/`.
- Current v1 hair status:
  - current status: `art_directed_candidate_manual_review_required`
  - `non_degenerate_hair_coverage_passed=true`
  - current candidate is not accepted as replacement hair until manual review
  - `ready_for_cloth_seam_surface=false`
- `hair_target_schema_v1` now exists with `strict_hair_core`,
  `soft_hair_silhouette`, and `forbidden_nonhair_zone`.
- A tighter schema-constrained ribbon rebuild was generated. It passed
  leak/soft-inside/core thresholds but fails non-degenerate coverage:
  - baseline before rebuild:
    - `forbidden_candidate_leak_ratio=0.975006`
    - `candidate_core_coverage_ratio=0.041425`
    - `candidate_soft_inside_ratio=0.021113`
  - first schema-constrained rebuild:
    - `forbidden_candidate_leak_ratio=0.299879`
    - `candidate_core_coverage_ratio=0.196487`
    - `candidate_soft_inside_ratio=0.557359`
  - current tightened rebuild:
    - `forbidden_candidate_leak_ratio=0.010006`
    - `candidate_core_coverage_ratio=0.187749`
    - `candidate_soft_inside_ratio=0.916398`
    - `candidate_visible_area_ratio=0.003227`
    - `soft_silhouette_coverage_ratio=0.174971`
    - `bangs_presence_ratio=0.066363`
    - `side_hair_left_presence_ratio=0.259981`
    - `component_count=39`
- The art-directed v1 rebuild improves the non-degenerate metrics while
  keeping side-profile volume blocks out of the candidate beauty route:
  - `forbidden_candidate_leak_ratio=0.020550`
  - `candidate_core_coverage_ratio=0.341135`
  - `candidate_soft_inside_ratio=0.822168`
  - `candidate_visible_area_ratio=0.007020`
  - `soft_silhouette_coverage_ratio=0.341499`
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
- `cloth_seam_surface` remains blocked.

## Current Blocker

Manual-review the art-directed v1 hair candidate before any new actuator work.
The v1 metrics now pass the schema/non-degenerate gate, but the visual result is
still a DCC handoff candidate: yaw views have cleaner layered hair-card mass and
the previous blocky side-profile volumes no longer pollute the overlay, but
candidate-only front remains sparse at full-body framing. It is not accepted,
not integrated, and not ready for cloth.

## Formula Binding

The v9/v10 candidate loop is governed by the Bounded Semantic Geometry Filter:

```text
theta_p_next =
ProjectToConstraints_p(
  (1 - alpha) * theta_p
  + alpha * RobustFuse(
      front_obs_p,
      side_obs_p,
      back_obs_p,
      validation_obs_p,
      prior_p
    )
)
```

In this project, `theta_p` means part-generator parameters, target masks,
metadata, route status, and validation fields before it means raw vertices.
`ProjectToConstraints_p` must keep v8 immutable, preserve front identity, keep
side/back soft, preserve beauty/cage separation, keep
`replace_in_beauty_glb=false` by default, and reject candidates that fail visual
sanity or target-schema gates.

## Current Hair Formula Binding

For the hair route, do not treat one mask IoU as success. The current update
target is not:

```text
candidate ~= raw_hair_union
```

The current update target is:

```text
candidate_hair_next =
ProjectToConstraints_hair(
  RobustFuse(
    strict_hair_core,
    soft_hair_silhouette,
    forbidden_nonhair_zone,
    front_identity,
    manual_visual_review
  )
)
```

Current blocker:

- raw hair union is dirty;
- strict clean target is too narrow;
- refined component-prior target is still not final;
- `hair_target_schema_v1` is available;
- v0 candidate passed leak/soft-inside/core metrics but failed the
  non-degenerate coverage gate;
- `hair_design_schema_v1.json` is available to drive an art-directed rebuild;
- `art_directed_hair_ribbons_v1` has been generated and now requires manual
  visual review;
- `cloth_seam_surface` remains blocked.

Next valid task: `manual_review_art_directed_hair_ribbons_v1_quality`.

Invalid next task: `cloth_seam_surface`.

## Current Evidence

- `CharacterPackage/semantic_layer_v9_hair/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v9_hair/target_review/hair_target_review_report.json`
- `CharacterPackage/semantic_layer_v9_hair/target_review/hair_target_mask_refined_component_priors.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/hair_target_schema_v1_report.json`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/strict_hair_core_mask.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/soft_hair_silhouette_mask.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/forbidden_nonhair_zone_mask.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/candidate_vs_schema_overlay.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/schema_debug_contact_sheet.png`
- `CharacterPackage/semantic_layer_v9_hair/hair_design_schema_v1.json`
- `CharacterPackage/semantic_layer_v9_candidate/backlog_v10.md`
- `CharacterPackage/semantic_layer_v9_candidate/actuator_run_report.md`

## Do Not Do

- Do not proceed to `cloth_seam_surface`.
- Do not accept raw/refined union IoU as final proof of hair quality.
- Do not replace v8 beauty.
- Do not call hair v0 accepted until non-degenerate coverage and manual review
  pass.

## Required Verification

For implementation turns, run the narrowest relevant tests plus:

```bash
python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v
python3 -m compileall CharacterPackage/tools
git diff --name-only -- CharacterPackage/semantic_layer_v8
```
