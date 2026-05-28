# External Hair Dataset Pilot v0

This directory started as a metadata-only pilot for external hair references
that may inform YUNA hair priors. It now also contains a user-approved
Sketchfab local-study intake under `sketchfab_gorgeous_japanese_fight/`.

Downloaded or derived third-party assets remain `prior_only`. They do not
replace YUNA geometry.

## Boundary

- `CharacterPackage/semantic_layer_v8` remains the immutable baseline.
- `replace_in_beauty_glb=false` for every source and derived prior.
- External sources are `prior_only`: scalp anchors, curve families, width and
  taper profiles, depth grouping, topology patterns, silhouette mass, and
  negative examples.
- External binary payloads are committed only when explicitly requested by the
  user, license/provenance is recorded, and the files remain reference/prior
  assets.
- No source is accepted as production hair, replacement hair, or direct texture
  transfer.
- `cloth_seam_surface` remains blocked while the hair route is unresolved or
  pending manual visual review.

## Files

- `SOURCE_TRIAGE.md`: human-readable source/license triage.
- `assets_manifest.schema.json`: JSON schema for the pilot manifest.
- `assets_manifest.json`: machine-readable source manifest.
- `external_hair_dataset_pilot_v0_report.json`: pilot summary and validation
  status.
- `probes/`: minimal intake probes for selected sources. Probe reports and
  renders are prior/reference evidence only; raw third-party source binaries are
  not committed.
- `subagent_reports/`: parallel research reports used as input.
- `sketchfab_gorgeous_japanese_fight/`: user-approved CC BY 4.0 local-study
  intake with original GLB, extracted pink-hair probe, screenshots, and reports.

## Current Probe

`external_hair_intake_probe_v0` selected two high-confidence `open_template_source`
entries:

- `opengameart_ponytail_female`
- `opengameart_long_male`

Both were downloaded to temporary files only, rendered through Blender, and
recorded under `probes/<asset_id>/`. The committed artifacts are generated
probe renders and JSON reports, not source `.blend` payloads.

## Intake Policy

The first pilot records source metadata only. Future intake must pass these
gates before any download or derived prior extraction:

1. explicit source URL and author/platform provenance;
2. explicit license and conservative license confidence;
3. small targeted file, not a bulk archive;
4. no unsafe scripts or proprietary plugin requirement;
5. generated review evidence or `skipped_with_reason`;
6. v8 diff remains clean.

## Verification

Run:

```bash
python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v
python3 -m compileall CharacterPackage/tools
git diff --name-only -- CharacterPackage/semantic_layer_v8
```

This dataset is successful only if it keeps external assets prior-only, keeps v8
unchanged, and keeps cloth blocked until the hair route passes visual/manual
review.

<!-- source_expansion_v1:start -->
## Source Expansion v1

`external_hair_source_expansion_v1` adds quality/style annotations and method-reference records without downloading third-party binaries.

- candidate sources: `12`
- high-priority next intake sources: `5`
- method references: `2`
- current probe sources are retained as low/medium priors, not accepted hair targets.
- external assets remain `prior_only`; `replace_in_beauty_glb=false`; `cloth_seam_surface` remains blocked.

Report:

```text
CharacterPackage/external_hair_dataset/reports/external_hair_source_expansion_v1_report.json
```
<!-- source_expansion_v1:end -->
