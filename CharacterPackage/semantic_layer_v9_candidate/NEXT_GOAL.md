# Next Goal: Sketchfab Hair Prior Schema Extraction v0

## Objective

Convert the committed Sketchfab `Gorgeous japanese Fight` original GLB and
pink-hair shell probe into a YUNA-safe prior schema.

## Allowed Inputs

- `CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/source/gorgeous_japanese_fight.glb`
- `CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/extracted/pink_hair_segment_probe.glb`
- analysis reports and screenshots under
  `CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/analysis/`

## Rules

- Keep `CharacterPackage/semantic_layer_v8` unchanged.
- Keep `replace_in_beauty_glb=false`.
- Keep all external assets `prior_only`.
- Do not generate YUNA hair.
- Do not proceed to `cloth_seam_surface`.
- Do not copy the high-poly shell directly into YUNA.
- Do not call the extracted probe production topology.
- Keep Sketchfab attribution intact.

## Required Evidence

- JSON prior schema describing:
  - scalp anchor zones;
  - crown/back mass;
  - primary flow arcs;
  - side strand arcs;
  - width/taper hints;
  - visible mass thresholds;
  - negative/failure notes.
- Review images or links to existing committed screenshots.
- Explicit note that the result is a prior schema only.

## Verification

```bash
python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v
python3 -m compileall CharacterPackage/tools
git diff --name-only -- CharacterPackage/semantic_layer_v8
```
