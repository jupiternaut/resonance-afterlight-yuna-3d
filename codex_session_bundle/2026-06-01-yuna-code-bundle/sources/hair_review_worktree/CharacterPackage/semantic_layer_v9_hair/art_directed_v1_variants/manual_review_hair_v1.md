# Manual Review: Hair V1 Variants

This pack is for human visual review only. No variant replaces v8 beauty hair, no variant unblocks cloth, and no variant is production-ready hair.

Current caution: candidate-only renders may still read as sparse fragments. The recommendation below is only the first variant to inspect, not an acceptance decision.

Recommended first review target: `fuller`.

| Variant | Status | Manual gate | Leak | Soft inside | Core coverage | Visible area | Soft coverage | Front mass | Yaw30 | Side | Review note |
|---|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| balanced | schema_gate_passed_manual_review_required | pending_user_review_visible_mass_refined | 0.071096 | 0.831454 | 0.608249 | 0.010395 | 0.511386 | True | True | True | manual review required |
| fuller | schema_gate_passed_manual_review_required | pending_user_review_visible_mass_refined | 0.072702 | 0.833756 | 0.634326 | 0.010896 | 0.537518 | True | True | True | manual review required |
| silhouette | schema_gate_passed_manual_review_required | failed_visible_mass_readability_gate | 0.045859 | 0.854204 | 0.579953 | 0.009824 | 0.496502 | False | True | True | manual review required |

## Review Instructions

1. Start with `hair_variants_contact_sheet.png`.
2. Check candidate-only front first; it must read as hair without relying on v8 overlay.
3. Check yaw30 and side for broken slice-wall artifacts.
4. Reject any variant that looks like shredded body/cloth texture, even if numeric gates pass.
5. Keep `cloth_seam_surface` blocked until a human accepts a hair variant or requests another hair refinement pass.
