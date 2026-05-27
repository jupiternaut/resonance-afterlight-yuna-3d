# YUNA v9 Project State

## Current State

- `CharacterPackage/semantic_layer_v8` is the immutable visual-review / DCC
  baseline.
- v9 actuator routes exist for weapon, boots, legs, and authored hair ribbons.
- Weapon, boot, and leg routes are additive candidates/proxies; they do not
  replace v8 beauty.
- `authored_hair_ribbons_v0` generated assets, fixed the black-alpha leak, and
  passes the leak/soft-inside/core numeric gate, but fails the non-degenerate
  hair coverage gate.
- Hair coordinate alignment is only a weak pass against the dirty v8 hair union,
  so the route still requires manual visual review before any integration.
- Clean/refined hair target status:
  - current status: `schema_gate_passed_manual_review_failed_underfilled`
  - current candidate is not accepted as hair-only
  - `ready_for_cloth_seam_surface=false`
- `hair_target_schema_v1` now exists with `strict_hair_core`,
  `soft_hair_silhouette`, and `forbidden_nonhair_zone`.
- A tighter schema-constrained ribbon rebuild has been generated. It passes
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
- `cloth_seam_surface` remains blocked.

## Current Blocker

Build an art-directed hair ribbon design before any new actuator work. The
leak/soft-inside/core metrics pass only because the candidate is too sparse and
fragmented. It is not accepted, not integrated, and not ready for cloth.

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
- current candidate passes leak/soft-inside/core metrics but fails the
  non-degenerate coverage gate;
- `hair_design_schema_v1.json` is available to drive an art-directed rebuild;
- `cloth_seam_surface` remains blocked.

Next valid task: `build_art_directed_hair_ribbons_v1`.

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
