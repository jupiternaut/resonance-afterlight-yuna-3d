# Hair Prior Plan: External Assets As YUNA Priors

Subagent D: Hair Prior Planner

Status: planning report only. This file explains how external hair assets can
become bounded priors for YUNA hair planning. It does not generate assets,
modify `semantic_layer_v8`, edit manifest/schema/final files, approve a
candidate, replace v8 beauty hair, or unblock `cloth_seam_surface`.

## Hard Boundary

- External assets are evidence sources, not replacement hair.
- External meshes, cards, curves, textures, UVs, materials, and full silhouettes
  must not be copied into YUNA exports.
- External priors may influence only parameter choices, target notes, future
  schema planning, review prompts, and negative tests.
- `replace_in_beauty_glb=false` remains mandatory unless a separate explicit
  manual integration review changes it.
- `ready_for_cloth_seam_surface=false` remains mandatory while YUNA hair is
  pending, failed, unreviewed, or license/provenance blocked.

Current external prior evidence is limited to small probe reports and generated
review images for:

- `opengameart_ponytail_female`: useful as a crown/back-mass and long-bundle
  depth prior.
- `opengameart_long_male`: useful as a side-hair fill and flat-sheet negative
  guard.

Both are `prior_only`. Neither source is suitable as direct YUNA geometry,
texture, silhouette, or production topology.

## Binding To Current YUNA Hair Route

External priors are introduced only as `prior_hair` inside the existing bounded
hair update, not as raw geometry:

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

`prior_hair` is a structured packet of hints:

- scalp anchor likelihoods;
- primary curve families;
- width profiles;
- taper profiles;
- depth group ordering;
- hair-card topology patterns;
- silhouette mass distributions;
- negative/failure examples.

It is not a source asset, source mesh, source texture, or direct source curve.

Current YUNA target schema remains the authority:

- `strict_hair_core`: conservative hair-only region.
- `soft_hair_silhouette`: allowed hair expansion and wisps.
- `forbidden_nonhair_zone`: face, torso, weapon, legs, boots, cloth, and other
  non-hair areas where candidate coverage must be rejected or explicitly
  justified.

Current required YUNA primary groups remain:

- `bangs_primary`
- `side_hair_left_primary`
- `side_hair_right_primary`
- `back_hair_mass`

Current manual gates remain:

- candidate-only front must read as coherent YUNA hair without relying on the
  v8 overlay;
- yaw30 must read as hair, not broken plates;
- side view must preserve volume without becoming a flat wall;
- front identity must remain intact;
- known failures such as shredded body/cloth/weapon texture, detached strips,
  black-alpha artifacts, and broad face occlusion must be rejected.

Numeric target-schema success is not acceptance. The current `balanced` and
`fuller` variants still require manual review; the `silhouette` variant shows
that low leak can still fail visible front mass.

## Prior Record Shape

Every external-derived prior should be recorded as a measurement or hypothesis:

```text
prior_id
source_id
prior_kind
representation_class
coordinate_space
yuna_group_mapping
confidence
source_evidence_paths
allowed_downstream_consumers
forbidden_downstream_consumers
limitations
negative_tags
```

Allowed consumers:

- target-schema notes;
- design-parameter planning;
- curve-bundle planning;
- review rubrics;
- negative fixture reasoning.

Forbidden consumers:

- v8 beauty replacement;
- direct GLB/OBJ/BLEND import into YUNA;
- texture transfer;
- manifest/schema/final auto-approval;
- cloth unblock signals.

## Conversion Flow

1. Confirm source provenance, license, size, and intake status.
2. Inspect only permitted evidence: probe renders, wire view, alpha view, object
   summary, and prior extraction report.
3. Extract normalized measurements, not source geometry.
4. Map measurements to YUNA groups and target-schema layers.
5. Project suggestions through YUNA constraints: v8 immutable, front identity,
   forbidden zones, alpha/material sanity, scalp continuity, and manual review.
6. Emit parameter suggestions only. Any future candidate generation is a
   separate additive route with its own report and review pack.

No step may paste an external hairstyle onto YUNA.

## Scalp Anchors

YUNA-compatible anchor vocabulary:

- `scalp_front_center`
- `scalp_front_left`
- `scalp_front_right`
- `scalp_left_temple`
- `scalp_right_temple`
- `scalp_crown`
- `scalp_back_left`
- `scalp_back_right`

Allowed external contribution:

- root placement likelihood near crown, temples, and front hairline;
- root spread ranges per group;
- confidence that a visible card/strand is scalp-attached;
- continuity warnings when mass appears detached from the scalp.

Current source mapping:

- `opengameart_ponytail_female` can inform `scalp_crown` and rear mass
  continuity. Its `scalp_back_center` hint must be translated into YUNA's
  existing `scalp_back_left` / `scalp_back_right` vocabulary or kept as a note;
  it must not silently add a new schema anchor.
- `opengameart_long_male` can weakly inform `scalp_left_temple`,
  `scalp_right_temple`, and `scalp_crown` because it presents broad side
  curtain mass.
- Neither current source is strong evidence for YUNA-specific bangs anchors.
  Bangs must remain governed by YUNA's front identity, existing front anchors,
  and manual review.

Rejection rules:

- Detached lower fragments are not anchors.
- External coordinates cannot override YUNA front identity.
- Source root placement cannot justify coverage inside
  `forbidden_nonhair_zone`.
- A future candidate must still satisfy scalp-anchor continuity; the current
  non-degenerate gate expects continuity at or above `0.15`.

## Primary Curves

Primary curves should be represented as abstract normalized centerlines:

- sampled `t=0..1` points;
- intended YUNA group;
- anchor id;
- direction vector;
- curvature and smoothness class;
- confidence and limitations;
- explicit `copy_source_curve=false`.

YUNA primary curve groups:

- `bangs_primary`: front framing, anchored to front hairline, with strict face
  occlusion guard.
- `side_hair_left_primary`: shoulder-length left flow, avoiding torso leakage
  and horizontal slats.
- `side_hair_right_primary`: asymmetric right flow, avoiding weapon leakage.
- `back_hair_mass`: main long rear volume from crown/back anchors.

Useful current external curve hints:

- `back_mass_crown_to_low_tail`: from `opengameart_ponytail_female`; use as an
  abstract suggestion for two to four fuller downward mass ribbons plus
  secondary tapered strands.
- `side_curtain_left_right_fill`: from `opengameart_long_male`; use as a
  medium-width side-fall coverage hint with anti-wall clipping.

Current gap:

- No current source provides a strong YUNA-like `bangs_primary` prior. Bangs
  should use the current YUNA target schema, current anchors, and negative
  examples until a vetted bangs-specific source is added.

Curve priors fail when they:

- copy an external style as a complete hairstyle;
- depend on body, cape, face, or weapon pixels to read as hair;
- create disconnected plates without a visible root path;
- reduce leak by becoming too sparse to read as hair.

## Width Profiles

Width profiles are relative ratios, not pasted card sizes.

Required extracted fields:

- `t=0.0` root width ratio;
- `t=0.25` or nearest quarter width ratio;
- `t=0.5` mid width ratio;
- `t=0.75` or nearest three-quarter width ratio;
- `t=1.0` tip width ratio;
- width class: primary mass, side lock, bang, secondary strand, or flyaway;
- limitations and source confidence.

Current probe hints:

- `opengameart_ponytail_female` has a compact root, broad upper/mid mass, and
  narrow tip behavior. Use this to strengthen `back_hair_mass` readability,
  not to create a ponytail replacement.
- `opengameart_long_male` has broader curtain-like width through most of its
  length, then a sharp tip. Use this to avoid side-hair underfill, but also as
  a negative guard against flat side walls.

YUNA use:

- Back mass can be wider at root/mid sections to avoid underfilled candidates.
- Side hair can use medium widths with enough body to avoid shredded strips.
- Bangs may be narrower, but must still pass presence and face-readability
  review.
- Flyaways must stay thin and low-weight; they cannot carry the primary
  hairstyle.

Failure rules:

- needle-like shards fail even if leak is low;
- broad opaque face blocks fail;
- width choices that pass metrics only by shrinking visible mass fail;
- exact external card outlines are forbidden.

## Taper Profiles

Taper is a generator hint and review feature, not a source shape transfer.

Required extracted fields:

- root hold;
- mid-body fullness;
- tip taper rate;
- edge feathering or alpha behavior;
- visual failure tags.

Recommended YUNA taper families:

- `mass_ribbon_taper`: stable root, full midsection, controlled tip taper.
- `side_lock_taper`: strong root/mid body, gradual tip taper, anti-wall guard.
- `bang_taper`: medium root, controlled narrowing, no needle shards.
- `flyaway_taper`: thin and short, used only as detail.

Current source guidance:

- `opengameart_long_male` supports a `stable_root_full_mid_tapered_tip` family
  for side-fill planning, but its flat curtain silhouette is a risk.
- `opengameart_ponytail_female` is more mixed and should be used as a back-mass
  bundle/taper caution rather than a clean YUNA taper template.

Taper must be judged visually. A smooth taper still fails if the candidate reads
as sparse fragments, flat walls, dark halos, or pasted source style.

## Depth Groups

External assets may inform relative layer ordering only. Side/back views are
soft constraints and cannot override front identity.

Current YUNA depth vocabulary in generated specs includes:

- `front_bangs`
- `side_left_mid`
- `side_right_mid`
- `back_mass`
- `secondary_detail`
- `flyaways`

The `silhouette_mass_v1` route also introduced `side_profile_volume` as a review
depth aid. That kind of extra group must remain candidate-route-specific unless
a later schema review accepts it.

External depth hints:

- `opengameart_ponytail_female`: side/front spread suggests rear bundle depth
  useful for `back_hair_mass`.
- `opengameart_long_male`: similar front/yaw/side width suggests broad side
  sheets; useful for fill, risky for flat-wall artifacts.

Depth priors should suggest:

- ordering between bangs, side locks, secondary detail, flyaways, and back mass;
- yaw30/side readability expectations;
- where to split broad masses into layered ribbons.

Depth priors fail when they:

- place broad opaque cards across the eyes, nose, or mouth;
- hide sparse front mass behind v8 overlay;
- create disconnected plates with no scalp path;
- convert side-fill references into flat side walls.

## Hair Card Topology

External topology is pattern evidence only.

Current probe classes:

- both current sources classify as `hair_cards` with medium confidence;
- `opengameart_ponytail_female` reports 367 mesh vertices and 345 faces;
- `opengameart_long_male` reports 136 mesh vertices and 154 faces;
- both have alpha-material evidence.

Allowed topology priors:

- card density range;
- broad sheet risk;
- split-versus-overlap pattern;
- card orientation patterns;
- overdraw and alpha sanity examples;
- possible need for multiple overlapping ribbons instead of one broad wall.

Current YUNA-compatible topology direction:

- use scalp-anchored spline ribbon cards;
- keep semantic groups separate;
- keep beauty, debug, and cage outputs separated;
- maintain sampled sections along length; current review specs use
  `section_count=25`;
- current review variants use separate primary, secondary, and flyaway ribbons
  and remain candidate-only.

Forbidden topology use:

- copying source vertices, faces, UVs, or card meshes;
- calling low-poly source card topology production-ready YUNA topology;
- merging hair, face, cape, body, boots, or weapon into one fused mesh;
- reintroducing debug/cage geometry into beauty exports.

## Silhouette Mass

External silhouette mass is useful for underfill and overfill guards, not for
style transfer.

Current YUNA failure context:

- The target-schema report showed an underfilled candidate with
  `candidate_visible_area_ratio=0.003227`,
  `soft_silhouette_coverage_ratio=0.174971`, `component_count=39`, and
  `scalp_anchor_continuity=0.066363`.
- Current `balanced` and `fuller` variants improved numeric coverage and are
  recommended for manual review, but are not accepted.
- Current `silhouette` variant reduced leak but failed front visible mass,
  proving that low leak alone is not enough.

Current external mass hints:

- `opengameart_ponytail_female`: front area ratio around `0.141730`, compact
  crown/back volume, side/front width ratio around `1.492753`; useful for
  back-mass continuity and side-depth awareness.
- `opengameart_long_male`: front area ratio around `0.265557`, broader curtain
  width, side/front width ratio around `1.089287`; useful for preventing
  underfill, risky for flat-sheet overfill.

YUNA use:

- Convert mass hints into minimum/maximum readable mass notes per YUNA group.
- Compare future candidate-only front, yaw30, and side renders against these
  notes.
- Clip every suggestion through `forbidden_nonhair_zone`.
- Preserve asymmetry and front identity rather than importing external balance.

Silhouette priors fail when:

- they make YUNA look like the source asset;
- they create a helmet, curtain wall, or pasted ponytail;
- they fill forbidden body/weapon/face zones;
- they pass only because the v8 overlay makes them appear coherent.

## Negative And Failure Examples

Negative examples are first-class priors. They tell the planner what to reject
before any generation and what manual review must check after any candidate
render exists.

Existing YUNA negatives:

- dirty raw v8 union masks that include non-hair contamination;
- strict clean masks that can become too narrow and underfill hair;
- underfilled/schema-clipped candidates;
- excessive disconnected components;
- failed visual fixture:
  `CharacterPackage/semantic_layer_v9_hair/negative_fixtures/yuna_semantic_layer_v9_hair_validation_front_failed_visual_fixture.png`;
- low-leak but underfilled `silhouette` variant;
- numeric-pass but manual-review-pending `balanced` and `fuller` variants.

External negative tags to collect:

- detached floating strips;
- horizontal slat patterns;
- broad flat curtain walls;
- copied ponytail silhouette;
- broken slice-wall yaw silhouettes;
- black-alpha leakage or dark halos;
- missing or dirty alpha;
- source cards with no scalp-root continuity;
- broad face occlusion;
- body/cloth/weapon texture mistaken for hair;
- sparse flyaways used as primary mass;
- style mismatch with YUNA's premium cinematic sci-fi heroine direction;
- unclear license or provenance.

Negative priors block downstream suggestions when they match a future candidate
or when source evidence is not legally/technically safe for prior use.

## Relation To Target Schema And Manual Gates

External priors can propose changes to future parameter notes, but they do not
change the current target schema in this task.

Mapping to target schema:

- `strict_hair_core` filters priors down to reliable hair-only support.
- `soft_hair_silhouette` bounds allowable expansion for mass, wisps, and
  translucent strands.
- `forbidden_nonhair_zone` rejects any prior that would place hair on face,
  body, cloth, boots, weapon, or other non-hair areas.
- `front_identity` outranks side/back source evidence.
- `manual_visual_review` is the final gate for readability.

A future candidate influenced by external priors must report:

- which source ids informed it;
- which scalp anchor hints were adopted or rejected;
- which primary curve families were adopted or rejected;
- width and taper profile deltas;
- depth group and topology deltas;
- silhouette mass deltas against the YUNA target schema;
- negative examples checked;
- manual visual review status;
- `replace_in_beauty_glb=false`;
- `ready_for_cloth_seam_surface=false` unless a separate manual acceptance and
  integration review explicitly changes it.

Manual review must still answer:

- Does candidate-only front read as coherent YUNA hair?
- Does yaw30 read as hair rather than plates?
- Does side view preserve volume without becoming a flat wall?
- Is YUNA's face/front identity preserved?
- Are forbidden zones, alpha/material behavior, and negative examples clean?

If any answer is no or pending, the result is `manual_review_required` or
`not_accepted`, not accepted hair.

## Recommended Next Use

Use this plan to author a future prior packet or schema-planning note, not a
hair asset. The next valid external-prior step should be a report-only or
schema-planner pass that summarizes adopted/rejected prior hints. Any later
geometry generation must be a separate additive YUNA candidate route with its
own JSON report, screenshots, and manual review pack.

This preserves the intended boundary: external hair assets can teach the
planner which patterns are useful or harmful, but they cannot become YUNA hair
by substitution.
