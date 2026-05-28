# Sketchfab Gorgeous Japanese Fight Hair Prior Intake

This directory stores a user-approved local-study intake of the Sketchfab model
`Gorgeous japanese Fight` and the derived pink-hair segmentation probe.

It is an external reference/prior source only. It must not replace
`CharacterPackage/semantic_layer_v8`, and it must not be treated as YUNA final
hair topology.

## Source

- Source URL: <https://sketchfab.com/3d-models/gorgeous-japanese-fight-9cfcd8cf8302457a9d47e654b931ddec>
- Source name: `Gorgeous japanese Fight`
- Author: `YØD (@YOD3DD)`
- Claimed license: Creative Commons Attribution 4.0
- License URL: <https://creativecommons.org/licenses/by/4.0/>
- Local role: `local_study_prior_with_extractable_hair_shell_probe`

## Files

Source snapshot and original download:

- `source/gorgeous_japanese_fight.glb`
- `source/metadata.json`
- `source/source_page_snapshot.html`
- `source/thumbnail.jpeg`

Derived hair probe:

- `extracted/pink_hair_segment_probe.glb`
- `extracted/pink_hair_segment_probe.obj`
- `extracted/pink_hair_segment_probe.mtl`
- `extracted/pink_hair_segment_probe.blend`

Analysis evidence:

- `analysis/hair_prior_analysis.md`
- `analysis/inventory_report.json`
- `analysis/connected_component_report.json`
- `analysis/sketchfab_gorgeous_japanese_fight_review_contact_sheet.jpg`
- `analysis/pink_hair_segmentation_probe/pink_hair_segmentation_report.json`
- `analysis/pink_hair_segmentation_probe/pink_hair_segmentation_contact_sheet.jpg`

## Boundaries

- `replace_in_beauty_glb=false`.
- `CharacterPackage/semantic_layer_v8` remains immutable.
- Do not advance `cloth_seam_surface` based on this source alone.
- Do not call the extracted shell production hair.
- Use this source to derive scalp anchors, visible mass, side/back shell
  silhouette, and flow priors.
- The original and derived large assets are tracked through Git LFS.

## Extraction Summary

The pink-hair probe samples the source model's base-color texture by UV,
selects magenta/pink regions, constrains them to the source head space, and
filters connected components.

Important metrics:

- Original model polygons: `496472`
- Extracted hair-probe polygons: `142313`
- Extracted GLB SHA256:
  `2db2dd8cee583a2cdeee3d4aa1c839d57f07f222028e7e5662e9cdffc86062fc`

The probe captures a readable short-bob hair shell, but it is still a heuristic
extract from a high-poly sculpt, not a clean hair-card or ribbon template.
