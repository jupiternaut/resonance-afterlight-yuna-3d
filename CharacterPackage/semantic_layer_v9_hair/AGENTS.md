# semantic_layer_v9_hair/AGENTS.md

## Hair Route Rules

- Do not claim hair is accepted until manual review passes.
- `visual_sanity_status=passed` is not enough if the target mask is dirty,
  overbroad, or unreviewed.
- Keep `replace_in_beauty_glb=false` unless the user explicitly approves a
  replacement after review.
- Do not proceed to `cloth_seam_surface` while hair route status is failed or
  pending.

## Target Schema

Hair target work must distinguish:

- `strict_hair_core`: conservative pixels that are definitely hair.
- `soft_hair_silhouette`: broader silhouette allowed for wisps and translucent
  strands.
- `forbidden_nonhair_zone`: face, torso, weapon, legs, boots, and cloth regions
  where hair candidate coverage must be rejected or explicitly justified.

## Current Evidence

The generated `authored_hair_ribbons_v0` route fixed black alpha leakage and
basic coordinate framing, but it is still rejected as a clean hair candidate.
Raw, strict-clean, and refined target checks currently do not prove that the
candidate is hair-only. The next work is target-schema cleanup and then a
candidate rebuild against that schema, not cloth.
