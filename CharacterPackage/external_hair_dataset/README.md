# External Hair Dataset Pilot v0

This directory is a metadata-only pilot for external hair references that may
inform YUNA hair priors. It does not import, download, or approve any third
party asset as YUNA geometry.

## Boundary

- `CharacterPackage/semantic_layer_v8` remains the immutable baseline.
- `replace_in_beauty_glb=false` for every source and derived prior.
- External sources are `prior_only`: scalp anchors, curve families, width and
  taper profiles, depth grouping, topology patterns, silhouette mass, and
  negative examples.
- No external binary payloads are committed in this pilot.
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

This pilot is successful only if it stays metadata-only, keeps v8 unchanged, and
keeps cloth blocked.
