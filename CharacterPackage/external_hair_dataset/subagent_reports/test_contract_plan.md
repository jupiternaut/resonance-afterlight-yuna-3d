# External Hair Dataset Test Contract Plan

Subagent E: Test Contract Planner

Scope: planning only. This report defines tests and blocked behavior for the
external hair dataset expansion and intake pipeline. It does not implement
tests, modify manifests or schemas, modify final reports, generate assets, or
touch `CharacterPackage/semantic_layer_v8`.

## Contract Assumptions

- External hair sources are `prior_only`. They may inform scalp anchors, curve
  families, width/taper profiles, depth groups, card topology patterns,
  benchmarks, and negative examples.
- External sources must never become direct YUNA geometry, direct texture
  transfer, final production topology, or a v8 beauty replacement.
- `replace_in_beauty_glb=false` is required for every manifest, report,
  derived prior, and probe output.
- `CharacterPackage/semantic_layer_v8` remains immutable. Any non-empty v8 diff
  blocks the pilot or intake run.
- The current hair route remains unresolved until target schema, visual sanity,
  and manual review are clean. `cloth_seam_surface` remains blocked.
- Missing license, provenance, size, import, render, or review evidence fails
  closed and must produce explicit blocked or skipped state.

## Planned Test Groups

### 1. Manifest And Schema Tests

Test intent:

- Parse `assets_manifest.schema.json` and `assets_manifest.json` as strict JSON.
- Validate the manifest against the schema when a JSON Schema validator is
  available; otherwise run equivalent structural assertions.
- Assert top-level constants:
  - `schema_version=external_hair_dataset_manifest_v0.1`
  - `dataset_id=external_hair_dataset_pilot_v0`
  - `project_guards.v8_immutable=true`
  - `project_guards.replace_in_beauty_glb=false`
  - `project_guards.external_asset_usage=prior_only`
  - `project_guards.large_binaries_committed=false`
  - `project_guards.cloth_seam_surface_blocked=true`
- Assert `sources` is non-empty and each `source_id` is unique,
  repo-stable, lowercase snake case, and referenced consistently by reports.
- Assert each source has source URL, source name, claimed license, license
  confidence, permission fields, recommendation, intake status, download
  status, validation status, notes, and prior-only guards.
- Assert `recommendation` uses the current closed enum:
  - `open_template_source`
  - `reference_report_only`
  - `local_study_only`
  - `do_not_use`
  - `pending`
- Assert `license_confidence` uses the current closed enum:
  - `high`
  - `medium-high`
  - `medium`
  - `medium-low`
  - `low`
  - `unknown`

Blocked behavior:

- Invalid JSON, schema mismatch, duplicate `source_id`, unknown enum value, or
  missing guard field blocks the pilot.
- A source without `external_asset_usage=prior_only` or
  `replace_in_beauty_glb=false` blocks the pilot.
- A manifest that implies production approval, direct asset replacement, or v8
  export writes blocks the pilot.

### 2. Report Tests

Test intent:

- Parse `external_hair_dataset_pilot_v0_report.json` and any future intake
  probe reports as strict JSON.
- Assert the pilot report records:
  - source count and recommendation counts;
  - downloaded binaries are false for the metadata pilot;
  - generated assets are false for the metadata pilot;
  - large binaries committed are false;
  - `external_asset_usage=prior_only`;
  - `replace_in_beauty_glb=false`;
  - `v8_expected_unchanged=true` or an equivalent clean v8 diff result;
  - `ready_for_cloth_seam_surface=false`;
  - `skipped_with_reason` for skipped download, import, render, or extraction.
- Assert probe reports record selected source IDs, per-source terminal status,
  guard values, whether third-party binaries were committed, whether YUNA hair
  was generated, and whether cloth remains blocked.
- Assert report references point to existing report files or to explicit
  skipped reasons, not silent omissions.

Blocked behavior:

- A report that marks the pilot or intake as production hair acceptance blocks
  the run.
- A report that claims pass while license, import, visual sanity, target schema,
  or manual review is pending blocks the run.
- A report that omits `skipped_with_reason` for missing evidence blocks the run.
- Any report setting `ready_for_cloth_seam_surface=true` from external dataset
  progress alone blocks the run.

### 3. No Unclear-License Binary Committed Tests

Test intent:

- Use tracked and staged file checks, not only filesystem scans, so scratch
  quarantine data can exist locally without becoming committed payload.
- Fail if third-party binary-like source payloads are tracked or staged under
  `CharacterPackage/external_hair_dataset/` without explicit manifest evidence
  that binary commit is allowed.
- Treat these extensions as source payload risk by default:
  `.blend`, `.fbx`, `.glb`, `.gltf`, `.obj`, `.zip`, `.rar`, `.7z`, `.psd`,
  `.tif`, `.tiff`, `.exr`, `.mp4`, `.mov`.
- Treat image files as allowed only when they are generated probe renders or
  explicitly allowed tiny fixtures with source/license evidence:
  `.png`, `.jpg`, `.jpeg`, `.webp`.
- For every committed or staged binary/render candidate, cross-check manifest
  fields:
  - `can_commit_binary_to_repo` is not pending, local-only, or uploader
    unverified for source payloads;
  - `can_commit_renders` allows committed renders;
  - `claimed_license` and `license_confidence` are explicit;
  - license snapshot or attribution evidence is referenced where needed.

Blocked behavior:

- Unknown, low, medium-low, uploader-unverified, incompatible, missing, or
  pending license plus any committed binary blocks the run.
- Bulk archives, full character rigs, or paid-pack-context files block the run
  unless a later explicit exception exists with license evidence and path scope.
- A generated render without a source report and license basis blocks the run.
- A source marked `pending`, `local_study_only`, or `do_not_use` cannot have
  committed source binaries or derived committed priors.

### 4. v8 Unchanged Tests

Test intent:

- Before and after every expansion, intake, probe, or extraction run, record the
  project-standard guard:

```bash
git diff --name-only -- CharacterPackage/semantic_layer_v8
```

- Assert no path is returned.
- Also inspect staged paths under `CharacterPackage/semantic_layer_v8` in the
  final harness.
- Assert external dataset tools do not write inside v8, do not overwrite v8
  reports, and do not replace the v8 beauty GLB.

Blocked behavior:

- Any modified, deleted, added, or staged file under
  `CharacterPackage/semantic_layer_v8` blocks the run.
- Any test fixture that requires v8 mutation is invalid.
- Any external dataset output path inside v8 blocks the run.

### 5. Source Expansion Acceptance Tests

Test intent:

- New sources may be accepted into the manifest only when they have stable
  provenance: source URL, source name, author or platform when available,
  claimed license, access date or snapshot plan, format/size notes, and source
  quality notes.
- New `open_template_source` entries require high or medium-high license
  confidence, explicit source evidence, targeted file scope, and no bulk-only
  access requirement.
- New `reference_report_only` entries require attribution and render/reference
  publication policy when applicable.
- New `local_study_only` entries must remain local/internal and cannot commit
  source payloads or derived assets.
- New `pending` entries must have a pending or blocked reason and cannot be
  selected for download/import/render until promoted by a separate review.
- Expansion must keep `project_guards` unchanged and must not reduce the
  existing conservative restrictions.
- Expansion must update source coverage counts and skipped/blocked source lists
  in reports when reports are regenerated by a future implementation.

Acceptance status:

- Accept as source metadata when provenance, license, recommendation, intake
  status, guards, and skip behavior are complete.
- Accept as probe candidate only when license, size, safety, and targeted-file
  gates pass.
- Accept as derived-prior candidate only when probe evidence exists and the
  output contains measurements or parameters, not copied mesh or texture data.

Blocked behavior:

- A source with missing provenance, unclear license, bulk-only payload, unsafe
  archive behavior, paid-pack ambiguity, proprietary plugin requirement, or
  JavaScript-only unverifiable license cannot become an `open_template_source`.
- A source cannot be promoted by filename/provider label alone.
- Expansion cannot make cloth ready or mark YUNA hair accepted.

### 6. Intake `skipped_with_reason` Behavior

Test intent:

- Every source and every required intake stage must end in a terminal status:
  metadata-only, license-blocked, download-skipped, import-skipped,
  render-skipped, classification-deferred, review-pack-ready, or blocked.
- Any skipped source, skipped stage, or missing required view/channel must carry
  `skipped_with_reason`.
- Skip reasons must be non-empty, machine-readable enough for tests, and tied
  to a stage such as `download`, `import`, `render.front`, `render.alpha`,
  `classification`, or `curve_extraction`.
- Recommended reason codes include:
  - `license_unknown_metadata_only`
  - `license_incompatible_metadata_only`
  - `large_binary_not_downloaded`
  - `remote_size_unknown_not_downloaded`
  - `source_requires_bulk_archive`
  - `unsafe_archive_paths`
  - `embedded_scripts_disabled`
  - `proprietary_plugin_required`
  - `blender_unavailable`
  - `unsupported_format_without_importer`
  - `import_failed`
  - `render_failed`
  - `render_timeout`
  - `missing_texture_paths`
  - `missing_alpha_data`
  - `classification_deferred_insufficient_evidence`
- Required render outputs are `front`, `yaw30`, `side`, `wire`, `alpha`,
  `depth`, and `normal`. Each must have either an artifact path or
  `skipped_with_reason`.

Blocked behavior:

- Silent omission of a required stage or view blocks intake.
- Empty placeholders such as `TODO`, `n/a`, `unknown`, or blank skip reasons
  block intake.
- Claiming visual readability, alpha sanity, depth quality, or normal quality
  without matching evidence blocks intake.
- Blender unavailable is not a total failure if metadata is recorded, but every
  render output must be explicitly skipped.

### 7. Current Hair And Cloth Blocked Behavior Tests

Test intent:

- Assert external dataset reports state the current hair route is still
  candidate/pending unless a separate hair review artifact accepts it.
- Assert dataset progress cannot change current YUNA hair status by itself.
- Assert `ready_for_cloth_seam_surface=false` and
  `cloth_seam_surface_blocked=true` remain present in manifest/report guards.
- Assert blocked reasons reference unresolved hair target schema, visual sanity,
  manual review, license uncertainty, or candidate-only status as applicable.
- Assert no test, report, or README text says external source progress has
  unblocked cloth.

Blocked behavior:

- Starting cloth from a metadata, source expansion, probe, or prior extraction
  success blocks the run.
- Treating numeric/probe success as visual hair acceptance blocks the run.
- Calling current hair, external hair, probe hair, or derived priors final
  production topology blocks the run.

### 8. Negative Cases For Candidate Sources And Assets

Candidate source negative cases that must fail or stay blocked:

- `claimed_license` missing, unclear, contradictory, uploader-unverified, or
  separated from a paid-pack context.
- Source page cannot be rechecked, requires account-only access without
  recorded terms, or hides license behind unavailable JavaScript.
- Source requires downloading a large bulk archive to inspect one hair asset.
- Source has no author/platform provenance or cannot provide an attribution
  path when attribution is required.
- Source is texture-only but is promoted as curve-template geometry.
- Source is a full character rig but is promoted as a small hair-only binary.

Candidate asset negative cases that must fail or stay blocked:

- Embedded scripts, drivers, unsafe archive paths, or proprietary plugin
  requirements.
- Broken archive, unsupported format without importer, import crash, missing
  geometry, or zero-size/empty scene.
- Missing alpha textures for hair cards while alpha/material claims are made.
- Opaque cards, cloth/cape/weapon fragments, face/body fused geometry, or
  disconnected strips misclassified as hair.
- Render evidence exists only for front view but report claims yaw/side/depth
  quality.
- Derived prior contains third-party vertices, UVs, groom curves, texture
  pixels, or full silhouettes rather than bounded measurements.
- Probe output is used as YUNA geometry, written to v8, or inserted into a
  beauty GLB.

Blocked behavior:

- Negative cases may be kept as `negative_fixture`, `local_study_only`,
  `reference_report_only`, `classification_deferred`, or blocked metadata.
- Negative cases cannot become `eligible_for_prior_use` without a later
  explicit review artifact that resolves the blocker.

## Acceptance Matrix

| Condition | Expected Status |
| --- | --- |
| Manifest or schema invalid JSON | blocked |
| Manifest does not satisfy schema/structural contract | blocked |
| Unknown recommendation or license-confidence enum | blocked |
| Missing prior-only or replacement guard | blocked |
| Report omits source counts, guard state, or skipped evidence | blocked |
| Unclear-license binary tracked or staged | blocked |
| Bulk external archive tracked or staged | blocked |
| Probe render committed without license/report basis | blocked |
| Required intake output missing without `skipped_with_reason` | blocked |
| Empty or placeholder skip reason | blocked |
| v8 diff or staged v8 path exists | blocked |
| External output path writes inside v8 | blocked |
| Source expansion promotes pending/local-only source to download | blocked |
| Probe success used as final hair acceptance | blocked |
| Cloth marked ready while hair unresolved | blocked |
| External asset described as direct YUNA replacement | blocked |
| Derived prior contains copied third-party geometry or texture pixels | blocked |

## Non-Goals

- Do not implement tests in this subtask.
- Do not modify `assets_manifest.schema.json`, `assets_manifest.json`, or final
  report files.
- Do not download, generate, transform, or commit assets.
- Do not modify `CharacterPackage/semantic_layer_v8`.
- Do not approve any external source as production YUNA hair.
