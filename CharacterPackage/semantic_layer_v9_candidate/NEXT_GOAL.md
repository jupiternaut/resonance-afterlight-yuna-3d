# Next Goal: Manual Review Hair V1 Variants

## Objective

Review the overnight `art_directed_hair_ribbons_v1` variant pack before any
cloth actuator, physics pass, or v8 beauty replacement.

## Current Pack

Generated under:

```text
CharacterPackage/semantic_layer_v9_hair/art_directed_v1_variants/
```

Variants:

- `balanced`
- `fuller`
- `silhouette`

All variants are additive review candidates only:

- `replace_in_beauty_glb=false`
- `ready_for_cloth_seam_surface=false`
- no variant is accepted or production-ready

## Comparison Summary

| Variant | Leak | Soft inside | Core | Visible area | Front mass | Yaw30 | Side | Manual gate |
|---|---:|---:|---:|---:|---|---|---|---|
| `balanced` | `0.071096` | `0.831454` | `0.608249` | `0.010395` | true | true | true | pending review |
| `fuller` | `0.072702` | `0.833756` | `0.634326` | `0.010896` | true | true | true | pending review |
| `silhouette` | `0.045859` | `0.854204` | `0.579953` | `0.009824` | false | true | true | failed visible-mass gate |

Recommended first human review target: `fuller`.

This recommendation is not an acceptance decision. It only means `fuller`
currently has the strongest numeric balance for manual inspection.

## Review Inputs

- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1_variants/hair_variants_contact_sheet.png`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1_variants/hair_variants_comparison_report.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1_variants/manual_review_hair_v1.md`
- Per-variant `validation_ci/` screenshots:
  - candidate front
  - overlay front
  - yaw15
  - yaw30
  - side
  - wire
  - exploded

## Manual Review Questions

1. Does candidate-only front read as a coherent hairstyle without relying on the v8 overlay?
2. Does yaw30 still read as hair, not broken slice-wall fragments?
3. Does side view preserve enough hair volume without becoming a flat wall?
4. Does the chosen variant preserve YUNA front identity when overlaid?
5. Should the next pass polish the selected variant, or rebuild the generator again?

## Non-Goals

- Do not implement `cloth_seam_surface`.
- Do not replace v8 beauty.
- Do not set accepted status without explicit human review.
- Do not call any variant final production hair.

## Parallel Track: External Hair Dataset Pilot

The metadata-only external hair dataset pilot now exists under:

```text
CharacterPackage/external_hair_dataset/
```

This is not a substitute for manual review of the current hair variants. It is a
source/prior scaffold for later generator improvements.

Allowed follow-up only after the manual hair review state is explicit:

```text
/goal Review external_hair_intake_probe_v0 outputs and, if useful, extract
abstract priors only from the probe reports: scalp anchor hints, silhouette mass
statistics, curve/width/taper hypotheses, and negative examples. Keep v8
unchanged, do not commit source binaries, do not generate YUNA hair, and do not
proceed to cloth.
```

Still invalid:

```text
cloth_seam_surface
```
