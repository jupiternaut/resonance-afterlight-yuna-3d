# Next Goal: External Hair Intake Probe v1 Selected Sources

## Objective

Run a narrow intake probe for selected high-priority external hair prior sources.

## Allowed Sources

Start with one or two of:

- `vroid_hairsample_female_cc0`
- `vroid_hairsample_male_cc0`
- `blendswap_curly_hair`
- selected small files from `opengameart_hair_alphas_for_days`

## Rules

- Keep `CharacterPackage/semantic_layer_v8` unchanged.
- Keep `replace_in_beauty_glb=false`.
- Keep all external assets `prior_only`.
- Do not generate YUNA hair.
- Do not proceed to `cloth_seam_surface`.
- Do not commit unclear-license or large third-party binaries.
- Method references such as CHARM/DiffHairCard may inform schema language only.

## Required Evidence

- license snapshot;
- checksum and quarantine-only download metadata if any file is fetched;
- front/yaw30/side/wire/alpha/depth/normal render or explicit `skipped_with_reason`;
- prior report describing scalp anchors, curves, width/taper, depth groups, and failure/negative examples.

## Verification

```bash
python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v
python3 -m compileall CharacterPackage/tools
git diff --name-only -- CharacterPackage/semantic_layer_v8
```
