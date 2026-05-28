# Hair Prior Plan: External Assets to YUNA Hair Priors

Status: planning report only.

This report defines how external hair assets may inform YUNA hair priors. It
does not import, generate, or approve any asset. It does not modify
`semantic_layer_v8`, does not write a final README, manifest, or schema, and
does not unblock `cloth_seam_surface`.

Hard boundary:

- External hair assets may contribute only parameters, curves, topology
  patterns, silhouette statistics, and negative/failure examples.
- External hair assets must not directly replace YUNA v8 beauty hair.
- External hair assets must not bypass manual visual review.
- `replace_in_beauty_glb=false` remains the default until an explicit separate
  review and integration pass accepts replacement.

## Current YUNA Constraints

The current hair route is governed by the project formula:

```text
theta_hair_next =
ProjectToConstraints_hair(
  RobustFuse(
    strict_hair_core,
    soft_hair_silhouette,
    forbidden_nonhair_zone,
    front_identity,
    manual_visual_review,
    prior_hair
  )
)
```

In this plan, `prior_hair` is not mesh geometry. It is a bounded set of
generator hints: anchor likelihoods, curve paths, width/taper profiles, depth
ordering, card topology patterns, silhouette mass distributions, and known bad
examples.

Relevant existing references:

- `CharacterPackage/semantic_layer_v9_hair/hair_design_schema_v1.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/manual_review.md`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1_variants/manual_review_hair_v1.md`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1_variants/hair_variants_comparison_report.json`
- `CharacterPackage/semantic_layer_v9_hair/negative_fixtures/yuna_semantic_layer_v9_hair_validation_front_failed_visual_fixture.png`

Current useful seed facts:

- Existing anchor names: `scalp_front_center`, `scalp_front_left`,
  `scalp_front_right`, `scalp_left_temple`, `scalp_right_temple`,
  `scalp_crown`, `scalp_back_left`, `scalp_back_right`.
- Existing depth groups: `back_mass`, `front_bangs`, `side_left_mid`,
  `side_right_mid`, `secondary_detail`, `flyaways`.
- Current review variants are additive candidates only. `balanced` and `fuller`
  pass numeric gates but remain `pending_user_review_visible_mass_refined`;
  `silhouette` is useful as a low-leak comparison but fails front visible mass.

## Conversion Pipeline

External hair assets should be handled as a read-only prior dataset:

1. Intake external assets into an isolated review area with source metadata.
2. Extract measurements, not production geometry: scalp root positions,
   strand/card centerlines, card widths, taper behavior, z-order/depth clusters,
   silhouette envelopes, and failure tags.
3. Normalize those measurements into YUNA's existing front identity frame and
   current hair target schema (`strict_hair_core`, `soft_hair_silhouette`,
   `forbidden_nonhair_zone`).
4. Convert normalized measurements into prior suggestions for the next hair
   generator pass.
5. Reject suggestions that violate v8 immutability, front identity, forbidden
   zones, alpha sanity, group presence, or scalp continuity.
6. Send any resulting YUNA candidate to manual visual review. Numeric fit and
   external asset similarity are not acceptance.

No step in this pipeline is allowed to paste external mesh cards, textures, or
full silhouettes onto YUNA.

## Scalp Anchors

External assets can improve anchor priors by showing common root placement
patterns for long anime/sci-fi hair, but the final anchors must remain YUNA
specific.

Allowed extraction:

- Anchor likelihood near front hairline, temples, crown, and rear scalp.
- Root spread statistics per group, such as bangs concentrated near
  `scalp_front_center` and side locks near `scalp_left_temple` /
  `scalp_right_temple`.
- Confidence weights for whether an external card is scalp-attached,
  secondary, flyaway, or detached/noise.

Required YUNA mapping:

- Bangs map only to `scalp_front_center`, `scalp_front_left`, and
  `scalp_front_right`.
- Left side hair maps to `scalp_left_temple` and `scalp_back_left` only when
  a continuous root path exists.
- Right side hair maps to `scalp_right_temple` and `scalp_back_right` only when
  a continuous root path exists.
- Back mass maps to `scalp_crown`, `scalp_back_left`, and
  `scalp_back_right`.

Rejection rules:

- Detached strips cannot become anchored strands.
- Lower fragments without a visible root path become negative examples.
- External scalp coordinates cannot override YUNA front identity or mask
  constraints.

## Primary Curves

External assets can contribute curve families, not finished curves. Each curve
prior should be stored conceptually as a normalized centerline with sampled
points along `t=0..1`, direction, curvature, and intended group.

Primary YUNA curve groups:

- `bangs_primary`: short front framing curves, scalp-rooted, readable over the
  forehead without broad face occlusion.
- `side_hair_left_primary`: longer left-side curves with shoulder-length flow,
  not horizontal slats.
- `side_hair_right_primary`: asymmetric right-side curves, kept away from
  weapon contamination.
- `back_hair_mass`: long rear volume curves from crown/back anchors, used to
  carry most silhouette mass.

External curve priors may suggest:

- Curve count per group.
- Knot spacing and smoothness.
- Directionality, such as inward face framing for bangs and downward flow for
  side/back hair.
- Split/merge patterns where a mass divides into secondary ribbons.

External curve priors must not suggest:

- Copying an external silhouette as a complete hairstyle.
- Replacing YUNA's current hair masks as ground truth.
- Curves that depend on body, cape, weapon, or face pixels to read as hair.

## Width Profiles

Width priors should be extracted as relative profiles, not absolute pasted card
sizes. The current YUNA variant pack uses scalp-anchored ribbon cards with
primary ribbon thickness around `0.044..0.047` and minimum ribbon thickness
around `0.018..0.020`, with wider primary masses and thinner secondary/flyaway
strands.

For each external candidate strand/card, extract:

- Normalized samples: root width, quarter width, mid width, three-quarter
  width, tip width.
- Width class: primary mass, side lock, bang, secondary detail, flyaway.
- Width symmetry/asymmetry around the centerline.
- Whether the card preserves a readable mass from candidate-only front view.

Useful YUNA priors:

- Back mass can use broader root/mid widths to avoid underfilled hair.
- Side hair can use medium widths with enough body to avoid shredded strips.
- Bangs can use narrower widths, but must still pass `bangs_presence_ratio`.
- Flyaways should remain thin and limited; they cannot carry the primary
  hairstyle by themselves.

Failure cues:

- Width profiles that collapse to needle-like shards.
- Width profiles that create opaque face blocks.
- Width distributions that pass leak metrics only by becoming too sparse.

## Taper Profiles

Current primitive intents often express shape through `width_profile` while
leaving `taper_profile` implicit. External assets should be used to make taper
behavior explicit for future generator passes.

Taper priors to extract:

- Root hold: how much width is retained near the scalp.
- Mid-body bulge: whether the strand expands for hair mass readability.
- Tip taper: how quickly the card narrows at the end.
- Edge feathering: whether alpha/geometry taper produces clean tips without
  black-alpha leakage.

Recommended YUNA taper families:

- `mass_ribbon_taper`: stable root, fuller midsection, controlled tip taper.
- `bang_taper`: medium root, slight mid narrowing, sharp but not needle-like
  tip.
- `side_lock_taper`: strong root/mid body, gradual tip taper.
- `flyaway_taper`: thin root and thin tip, short length, low silhouette weight.

Taper must be judged visually. A mathematically smooth taper still fails if it
reads as sparse fragments, shredded texture, or a flat wall from yaw/side views.

## Depth Groups

External assets can contribute z-order and layering patterns. They cannot
define YUNA's final depth ordering directly.

Required YUNA depth groups:

- `front_bangs`: in front of scalp/forehead, with strict face occlusion guard.
- `side_left_mid`: left side hair in the mid layer, visible from yaw/side.
- `side_right_mid`: right side hair in the mid layer, separated from weapon
  pixels.
- `back_mass`: rear volume behind front/side details.
- `secondary_detail`: support strands that enrich primary groups.
- `flyaways`: small distributed wisps, never the only visible hair mass.

External assets should provide:

- Relative layer order between bangs, side locks, and back mass.
- Occlusion patterns that keep the face readable.
- Yaw/side readability patterns where hair does not collapse into slice walls.

Depth priors fail if they:

- Put broad opaque cards across the eyes, nose, or mouth.
- Hide sparse fronts behind v8 overlay and only read in composite.
- Create disconnected plates with no scalp path.

## Hair Card Topology

External assets may contribute topology patterns for card construction, not
their actual card meshes.

Current YUNA-compatible topology direction:

- Use scalp-anchored spline ribbon cards.
- Keep primary groups independent by semantic role.
- Keep at least the existing six depth groups for review candidates.
- Use multiple sampled sections per card; the current variant pack records
  `section_count=25`.
- Current review variants use `ribbon_count=27` for `balanced`, `33` for
  `fuller`, and `27` for `silhouette`.
- Candidate cards must preserve UV/material sanity and alpha behavior.

External topology priors may suggest:

- Card count ranges per group.
- Whether wide mass should be one broad ribbon or several overlapping ribbons.
- Edge-loop density along length for smooth curvature.
- Split/merge arrangements for back mass and side locks.
- Two-sided review-card conventions if they improve yaw/side readability.

External topology priors must not:

- Paste external topology into YUNA exports.
- Merge hair, face, cape, body, boots, or weapon into one fused mesh.
- Reintroduce debug/cage geometry into beauty exports.
- Call candidate card topology production-ready retopology.

## Silhouette Mass

External assets are useful for silhouette mass statistics, especially to avoid
the current failure mode where a candidate passes leak/alignment gates by
becoming too thin or fragmented.

YUNA target schema should remain the governing envelope:

- `strict_hair_core`: reliable hair-only area.
- `soft_hair_silhouette`: allowed readable hair expansion.
- `forbidden_nonhair_zone`: body, face, weapon, cape, boot, and other
  non-hair contamination guard.

External silhouette priors may contribute:

- Desired mass balance between bangs, side hair, and back hair.
- Minimum readable front mass for candidate-only render.
- Yaw30 and side-view continuity expectations.
- Asymmetric silhouette hints, if they preserve YUNA front identity.

Current numeric context for future priors:

- `balanced`: visible area `0.010395`, soft coverage `0.511386`, core coverage
  `0.608249`, leak `0.071096`, pending manual review.
- `fuller`: visible area `0.010896`, soft coverage `0.537518`, core coverage
  `0.634326`, leak `0.072702`, pending manual review.
- `silhouette`: leak `0.045859`, but front mass failed, so low leak alone is
  not enough.

Silhouette mass acceptance must still be visual. A candidate that matches an
external silhouette but breaks YUNA identity, reads as a flat wall, or relies on
v8 overlay is rejected.

## Negative/Failure Examples

External assets should include negative examples as first-class prior data.
They are valuable because they define what the generator should avoid.

Existing YUNA failure examples to preserve:

- Dirty raw v8 hair union: body overlap is too high, so raw union cannot be
  treated as final hair truth.
- Strict clean target too narrow: it can reject useful visible mass and create
  underfilled candidates.
- Underfilled/schema-clipped v0: `candidate_visible_area_ratio=0.003227`,
  `soft_silhouette_coverage_ratio=0.174971`, `component_count=39`, and
  `scalp_anchor_continuity=0.066363`.
- Negative fixture:
  `CharacterPackage/semantic_layer_v9_hair/negative_fixtures/yuna_semantic_layer_v9_hair_validation_front_failed_visual_fixture.png`
- `silhouette` variant: lower leak but failed front visible mass, proving that
  leak reduction is not sufficient.

External negative tags to collect:

- Detached floating strips.
- Horizontal slat patterns.
- Broken slice-wall yaw silhouettes.
- Shredded body/cloth/weapon texture mistaken for hair.
- Black-alpha leakage or dark halos.
- Broad face occlusion.
- Sparse flyaways used as primary hair mass.
- Blocky side-volume panels that read as proxy geometry instead of hair.
- Cards with no scalp-root continuity.

Negative examples should be used to block future generator suggestions before
asset generation, and again during manual visual review after any candidate is
rendered.

## Manual Review Gate

Manual visual review is mandatory for every candidate influenced by external
hair priors.

Review questions:

1. Does candidate-only front read as coherent YUNA hair without relying on the
   v8 overlay?
2. Does yaw30 read as hair instead of broken card plates?
3. Does side view preserve hair volume without becoming a flat wall?
4. Does the candidate preserve YUNA front identity?
5. Does it avoid known negative examples, including dirty texture leakage,
   detached fragments, black-alpha artifacts, and face/body/weapon
   contamination?

No external prior score, topology match, or numeric schema pass can answer
these questions by itself.

## Recommended Use In Future Work

Use external hair assets only to update a future hair-prior packet or design
notes, then feed those hints into an additive generator route. The next route
must still report:

- Which external priors influenced scalp anchors.
- Which curve families were adopted or rejected.
- Width/taper profile changes.
- Depth group and card topology changes.
- Silhouette mass deltas against the YUNA target schema.
- Negative examples used as rejection checks.
- Manual visual review status.
- `replace_in_beauty_glb=false` unless a separate explicit integration review
  says otherwise.

This preserves the core constraint: external assets can teach the generator what
patterns are useful or harmful, but they cannot become YUNA hair by substitution.
