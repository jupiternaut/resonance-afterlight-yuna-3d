# Cloth Seam Surface v1 Manual Review

- Status: `manual_review_required`
- Candidate-only: yes
- Production-ready: no
- `replace_in_beauty_glb`: false for every variant
- Current blocker: hair route still blocks cloth integration
- Contact sheet: `CharacterPackage/semantic_layer_v9_cloth/variants/cloth_variants_contact_sheet.png`
- Recommended variant: `heroic`

## Variant Metrics

| Variant | Score | Purity | Leak | Drape span | Side readable | Front readable | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| minimal | 0.81828 | 1.0 | 0.0 | 1.05545 | 0.732199 | 0.88 | manual_review_required |
| heroic | 0.938742 | 1.0 | 0.0 | 1.26805 | 0.858971 | 0.96 | manual_review_required |
| technical | 0.874419 | 1.0 | 0.0 | 1.144 | 0.79168 | 0.92 | manual_review_required |

## Review Notes

- `minimal` is the conservative comparison target.
- `heroic` is the current scoring recommendation for manual art review.
- `technical` is useful for DCC seam and hard-edge interpretation, but it should not be treated as final art.

## Next Goal

Manual art review should choose one direction, then a DCC artist should rebuild selected cloth as real topology with UV, rigging, and deformation tests. Hair remains the integration blocker until its route is manually accepted.
