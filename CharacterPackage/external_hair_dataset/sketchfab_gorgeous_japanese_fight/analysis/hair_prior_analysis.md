# Sketchfab `Gorgeous japanese Fight` Hair Prior Analysis

Source:
`https://sketchfab.com/3d-models/gorgeous-japanese-fight-9cfcd8cf8302457a9d47e654b931ddec`

Local GLB:
`/Users/gengrf/Downloads/yuna_external_hair_sources/sketchfab_gorgeous_japanese_fight/gorgeous_japanese_fight.glb`

License shown on source page:
Creative Commons Attribution 4.0 (`CC BY 4.0`)

## Intake Summary

- File: GLB / glTF binary v2
- Size: 51,099,692 bytes
- SHA256: `f57fadf8dbaad1c0bdda71c6354fca27264991cadfb7b9787be45a0c5463d9f1`
- Mesh objects after import: 5
- Materials: 3
- Main textured material: `Material.001`
- Total vertices: 317,744
- Total polygons: 496,472
- Armature: none detected
- Animations: none detected
- Shape keys: none detected

## Visual Hair Quality

The hair is much closer to a usable anime-style reference than the earlier low-quality probe assets:

- clear short-bob silhouette;
- readable scalp/crown mass;
- side-swept bangs;
- front hair clumps with sculpted grooves;
- side/back hair shell with visible strand carving;
- a few loose outline strands and flyaways.

However, it is a short pink bob. It does not match YUNA's long flowing sci-fi heroine hair target directly.

## Separability Check

The model is not organized as a clean hair asset.

Findings:

- No object name contains `hair`, `bangs`, `scalp`, or similar semantic labels.
- No material name identifies hair.
- All visible character geometry uses the same main material `Material.001`.
- Object split is spatial/chunk-based rather than semantic.
- Hair geometry is spread across several objects:
  - `Object_4` includes face/front hair/upper torso pieces.
  - `Object_5` includes a large back-hair shell plus unrelated torn-cloth fragments.
  - `Object_6` and `Object_7` include some upper/head-zone hair-like components mixed with arms/body fragments.
- Connected component analysis finds many upper-head-zone candidate components, but these are heuristic only and include non-hair risks.

Verdict:
`reference_only / prior_source`, not `open_template_source`.

## Texture / UV Findings

- Main base color texture is `Image_0`, 4096x4096.
- The atlas is AI-style and densely packed.
- Hair, skin, cloth, and black clothing islands are mixed in one texture atlas.
- Hair cannot be reliably extracted only by material slot.
- Color/UV-based pink-hair extraction may be possible as a study pass, but it would be heuristic and should not be treated as clean source geometry.

## Usefulness For YUNA

Useful as prior for:

- crown volume;
- side-swept bang grouping;
- short sculpted lock topology;
- scalp anchor direction;
- strand groove density;
- side/back shell mass;
- "not too sparse" visible hair mass target.

Not useful as direct replacement because:

- not YUNA's long white/cyan hair style;
- no clean hair mesh separation;
- no cards/ribbons/curves authoring data;
- no rig, no hair bones, no blendshapes;
- high-poly sculpt chunks rather than DCC-ready ribbon hair;
- license requires attribution and binary commit policy still needs explicit review.

## Recommended Role In YUNA Pipeline

Recommended role:
`local_study_only_hair_prior`

Do not:

- commit the GLB binary to the repo by default;
- replace YUNA v8 hair;
- use it as production topology;
- treat it as a ready-made hair card source.

Do:

- use renders as visual reference;
- derive approximate scalp anchor map and primary flow directions manually;
- use it as a "visible mass" benchmark against sparse YUNA hair candidates;
- optionally run a separate color/UV segmentation experiment to extract rough pink hair components for study only.

## Generated Evidence

- `analysis/inventory_report.json`
- `analysis/connected_component_report.json`
- `analysis/review_front.png`
- `analysis/review_yaw30.png`
- `analysis/review_side.png`
- `analysis/object_breakdown/all_objects_color_coded_front.png`
- `analysis/sketchfab_gorgeous_japanese_fight_review_contact_sheet.jpg`
- `analysis/textures/Image_0.png`

## Bottom Line

This asset is visually valuable but structurally dirty.

It should raise the visual standard for YUNA hair candidates: current YUNA authored ribbons should not be sparse or fragmented compared with this model's readable crown/back/bangs mass.

But this Sketchfab GLB should remain a reference/prior source, not a direct extractable hair template.

## Pink Hair Segmentation Probe

Follow-up probe:
`analysis/pink_hair_segmentation_probe/`

This pass does not rely on object names or material names. It samples `Material.001`'s base-color atlas by UV, selects magenta/pink texture regions, constrains them to the source model's head-space, then filters connected components.

Output:

- `pink_hair_segment_probe.obj`
- `pink_hair_segment_probe.glb`
- `pink_hair_segment_probe.blend`
- `pink_hair_segmentation_report.json`
- `candidate_only_front.png`
- `candidate_only_yaw30.png`
- `candidate_only_side.png`
- `pink_hair_segmentation_contact_sheet.jpg`

Metrics:

- Source polygons: 496,472
- Kept hair-probe polygons: 142,313
- Kept face ratio: 0.2866485924684574
- Output vertices: 426,939
- Output polygons: 142,313
- Contributing source chunks:
  - `Object_4`: 46,284 faces
  - `Object_5`: 72,259 faces
  - `Object_6`: 17,386 faces
  - `Object_7`: 6,384 faces

Result:

The pink-color + UV + head-space probe successfully extracts a hair-like shell. It captures the short-bob crown, side arcs, back hair mass, and several loose strand silhouettes.

Limitations:

- It is still a color/space heuristic, not semantic authoring.
- Some darker strand grooves are missing because they fall outside the pink threshold.
- Some selected surfaces are high-poly sculpt chunks, not hair cards or animation-ready ribbons.
- The extracted probe is useful as a mass/flow prior, not as production hair topology.

Updated role:
`local_study_prior_with_extractable_hair_shell_probe`
