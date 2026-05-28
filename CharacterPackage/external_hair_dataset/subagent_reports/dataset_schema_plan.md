# External Hair Dataset Schema Plan

Subagent: B - Dataset Schema Planner

Scope: design the scaffold and manifest shape for an external hair reference
dataset. This is a planning report only. It does not define the final README,
manifest, JSON schema, or any asset payload.

Core boundary: external hair assets are prior sources only. They may inform
YUNA hair target schemas, flow priors, curve-template hypotheses, or benchmark
fixtures, but they must not directly replace YUNA hair geometry, textures, or
the v8 beauty GLB.

## Assumptions

- `CharacterPackage/semantic_layer_v8` remains the immutable visual-review and
  DCC baseline.
- `replace_in_beauty_glb` defaults to `false` and cannot be changed by an
  external dataset manifest.
- All intake decisions fail closed: missing license, missing provenance, or
  missing review evidence means the asset can only stay in audit/quarantine.
- External binaries, renders, and extracted priors need separate permission
  gates. A license that allows viewing does not automatically allow committing
  binaries, derived renders, or curve templates.
- Derived priors should be parameter data, reports, masks, or measurements, not
  copied mesh/texture payloads from third-party hair assets.

## Proposed Directory Structure

The scaffold should separate legal evidence, source inventory, quarantine
assets, derived priors, and review reports. Proposed future layout:

```text
CharacterPackage/external_hair_dataset/
  README.md                         # final human guide, not created by this task
  LICENSE_AUDIT.md                  # final license summary, not created by this task
  schemas/
    external_hair_manifest.schema.json
    derived_prior.schema.json
    intake_report.schema.json
  manifests/
    dataset_manifest.json
    assets/
      <asset_id>.manifest.json
  license_evidence/
    <asset_id>/
      source_terms_snapshot.txt
      attribution.txt
      reviewer_notes.md
  sources/
    quarantine/
      <asset_id>/                   # raw downloads before legal/technical gates
    approved_binary/
      <asset_id>/                   # only if can_commit_binary_to_repo.allowed=true
    external_only/
      <asset_id>/                   # local-only or pointer-only assets
  renders/
    <asset_id>/
      source_probe_front.png
      source_probe_turntable_contact.png
      render_probe_report.json
  derived_priors/
    <asset_id>/
      flow_prior.json
      silhouette_prior.json
      curve_template_prior.json
      extraction_report.json
  intake_reports/
    <asset_id>.intake_report.json
  subagent_reports/
    dataset_schema_plan.md
```

Recommended rule: the top-level manifest references assets by `asset_id` and
never inlines binary payloads. Raw or approved asset paths are optional and must
be absent when binaries cannot be committed.

## Manifest Required Fields

Each per-asset manifest should require:

- `manifest_version`: schema-compatible version string.
- `dataset_id`: stable dataset handle, for example
  `external_hair_dataset_pilot_v0`.
- `asset_id`: stable slug, never derived only from a filename.
- `asset_type`: controlled enum such as `hair_mesh`, `hair_cards`,
  `curve_groom`, `image_reference`, `render_reference`, or `mixed_package`.
- `display_name`: short human-readable name.
- `source`: structured source object.
- `license`: structured license object.
- `provenance`: structured provenance chain.
- `file_inventory`: hashes and paths for any files known to the repo.
- `intake_status`: current fail-closed state and reviewer notes.
- `allowed_usage_roles`: explicit role list; empty by default.
- `permission_gates`: structured gates for committing binaries, committing
  renders, and extracting curve templates.
- `derived_priors`: references to extracted prior files, if any.
- `yuna_integration_guard`: required guard object that keeps usage prior-only.
- `validation_evidence`: render, extraction, and review reports, or explicit
  skipped reasons.
- `audit`: reviewer, timestamp, and decision history.

Illustrative shape, not the final schema:

```json
{
  "manifest_version": "0.1-plan",
  "dataset_id": "external_hair_dataset_pilot_v0",
  "asset_id": "example_asset_slug",
  "asset_type": "hair_mesh",
  "display_name": "Example Hair Reference",
  "source": {},
  "license": {},
  "provenance": {},
  "file_inventory": [],
  "intake_status": {},
  "allowed_usage_roles": [],
  "permission_gates": {},
  "derived_priors": [],
  "yuna_integration_guard": {
    "replace_in_beauty_glb": false,
    "baseline_path": "CharacterPackage/semantic_layer_v8",
    "baseline_mutation_allowed": false,
    "direct_asset_replacement_allowed": false
  },
  "validation_evidence": {},
  "audit": {}
}
```

## Source, License, And Provenance Fields

`source` should answer where the asset came from and how it can be rechecked:

- `source_name`
- `source_platform`
- `source_url`
- `download_url`
- `author_name`
- `author_url`
- `publisher_name`
- `retrieved_at`
- `source_access_type`: `public`, `account_required`, `paid`,
  `private_permission`, or `unknown`
- `source_terms_snapshot_path`
- `source_metadata_hash`

`license` should express what is legally allowed, not what is technically
possible:

- `license_name`
- `license_spdx_id`: nullable when not SPDX compatible.
- `license_url`
- `license_text_snapshot_path`
- `attribution_required`
- `attribution_text`
- `commercial_use_allowed`
- `redistribution_allowed`
- `derivatives_allowed`
- `render_publication_allowed`
- `ml_training_allowed`: include because some datasets separate reference use
  from model/training use.
- `license_restrictions`
- `license_review_status`: `pending`, `approved`, `blocked`, or
  `needs_human_legal_review`
- `license_reviewer`
- `license_reviewed_at`

`provenance` should preserve the chain from source to local evidence:

- `original_filename`
- `original_file_hashes`: at minimum SHA-256 when a file exists.
- `local_pointer_path`: nullable when the asset is pointer-only.
- `import_tool`
- `import_tool_version`
- `normalization_steps`: array of reversible technical steps, not art edits.
- `derived_from_asset_ids`: for packages split into sub-assets.
- `human_notes`
- `known_modifications`
- `provenance_confidence`: `high`, `medium`, `low`, or `unknown`.

## Derived Prior Fields

Derived priors must be framed as constraints or measurements consumed by later
YUNA schema work, not as replacement asset payloads.

Required fields for each prior:

- `prior_id`
- `asset_id`
- `prior_kind`: `silhouette_prior`, `flow_direction_prior`,
  `curve_template_prior`, `density_prior`, `segmentation_fixture`,
  `benchmark_render`, or `material_palette_reference`.
- `source_files`: source inventory references, not copied file blobs.
- `output_path`: path under `derived_priors/<asset_id>/`.
- `extraction_method`
- `extraction_tool_version`
- `coordinate_space`: for example `source_asset_local`,
  `normalized_unit_head`, or `yuna_reference_view_2d`.
- `scale_basis`
- `semantic_groups`: for YUNA-compatible labels such as `bangs`,
  `side_hair_left`, `side_hair_right`, `back_hair`, while noting that labels are
  hypotheses.
- `confidence`
- `limitations`
- `allowed_downstream_consumers`: schema/report tools only by default.
- `forbidden_downstream_consumers`: beauty GLB builders and direct asset import
  steps.
- `contains_third_party_geometry`: boolean.
- `contains_third_party_texture`: boolean.
- `can_influence_yuna_theta_p`: boolean, default `false` until reviewed.

For curve templates specifically, store abstract curves and parameter ranges:

- control-point arrays in normalized coordinates;
- strand-flow direction vectors;
- width/taper ranges;
- grouping and depth-order hints;
- no source mesh vertices unless license and review explicitly allow that
  derived representation.

## Intake Status

Recommended status enum:

- `proposed`: source identified, no download or legal review.
- `source_identified`: source metadata recorded.
- `license_pending`: license evidence incomplete.
- `license_blocked`: license forbids required use.
- `downloaded_quarantine`: local file exists but cannot be consumed.
- `hash_recorded`: file inventory and hashes recorded.
- `render_probe_pending`: render proof not yet produced.
- `render_probe_complete`: render report exists.
- `curve_extraction_pending`: extraction allowed but not complete.
- `prior_extracted`: derived prior exists but is not approved for YUNA use.
- `eligible_for_prior_use`: legal, provenance, extraction, and review gates pass.
- `rejected`: do not use; keep only minimal audit record.
- `retired`: no longer part of active pilot.

Gate rule: only `eligible_for_prior_use` may feed later YUNA prior-fusion or
target-schema planning, and even then only through `derived_priors`, never by
importing the original asset into a YUNA export.

## Allowed Usage Roles

Allowed roles should be explicit and additive:

- `legal_audit_only`: keep source/license metadata only.
- `visual_reference_only`: humans may inspect screenshots/reference images.
- `benchmark_render`: used to compare extraction or render tooling.
- `segmentation_fixture`: used to test hair/non-hair segmentation behavior.
- `silhouette_prior`: informs high-level hair mass only.
- `flow_direction_prior`: informs strand direction or curve orientation.
- `curve_template_prior`: informs abstract curve hypotheses.
- `density_prior`: informs strand/card density ranges.
- `material_palette_reference`: informs rough color/value ranges only.
- `negative_fixture`: used as a known-bad or out-of-domain example.

No allowed role should mean direct import into YUNA beauty assets. A role named
`replacement_candidate`, `beauty_glb_source`, or `production_hair_asset` should
be invalid.

## Blocked Behavior

The scaffold should explicitly block:

- Replacing or overwriting anything under `CharacterPackage/semantic_layer_v8`.
- Setting `replace_in_beauty_glb=true` from any external dataset manifest.
- Importing third-party hair mesh, hair-card geometry, curves, textures, or
  materials directly into a YUNA beauty GLB.
- Copying source vertices, UVs, cards, groom curves, or texture pixels into
  YUNA candidate geometry unless a separate manual legal/art review approves a
  narrowly defined derived representation.
- Treating GLB load/export success as visual acceptance.
- Treating render probes as license approval.
- Treating license approval as art-direction approval.
- Publishing or committing binaries/renders when the corresponding permission
  gate is missing, pending, or false.
- Advancing cloth or other actuators based on external-hair scaffold progress.
- Calling any external or derived asset final production topology.

## Permission Gate Expression

Use explicit gate objects rather than loose booleans. The `allowed` value is the
machine-readable decision; `status`, `basis`, and evidence make the decision
auditable. Missing gates should be interpreted as `allowed=false`.

```json
{
  "permission_gates": {
    "can_commit_binary_to_repo": {
      "allowed": false,
      "status": "pending_review",
      "basis": "License and redistribution permission not verified.",
      "evidence": [],
      "allowed_paths": [],
      "reviewer": null,
      "checked_at": null
    },
    "can_commit_renders": {
      "allowed": false,
      "status": "pending_review",
      "basis": "Render publication permission not verified.",
      "evidence": [],
      "allowed_paths": [],
      "reviewer": null,
      "checked_at": null
    },
    "can_extract_curve_templates": {
      "allowed": false,
      "status": "pending_review",
      "basis": "Derivative-use permission not verified.",
      "evidence": [],
      "allowed_prior_kinds": [],
      "reviewer": null,
      "checked_at": null
    }
  }
}
```

Recommended `status` enum:

- `allowed`: evidence supports this action.
- `blocked_by_license`: license forbids it.
- `blocked_by_provenance`: source chain is unclear.
- `blocked_by_policy`: project rule forbids it even if technically possible.
- `pending_review`: no approval yet.
- `not_applicable`: action is irrelevant for this asset type.

Default decisions for initial intake:

- `can_commit_binary_to_repo.allowed=false`
- `can_commit_renders.allowed=false`
- `can_extract_curve_templates.allowed=false`

Each gate should list path scopes when allowed. Example: renders may be allowed
only under `CharacterPackage/external_hair_dataset/renders/<asset_id>/`, while
binaries remain pointer-only.

## Keeping `replace_in_beauty_glb=false` And v8 Unchanged

Every manifest should require this guard:

```json
{
  "yuna_integration_guard": {
    "replace_in_beauty_glb": false,
    "baseline_path": "CharacterPackage/semantic_layer_v8",
    "baseline_mutation_allowed": false,
    "direct_asset_replacement_allowed": false,
    "prior_only": true,
    "may_write_yuna_export_paths": false,
    "allowed_candidate_consumption": [
      "target_schema_planning",
      "manual_curve_review",
      "validation_fixture_comparison"
    ]
  }
}
```

Operational checks:

- Before and after any intake or extraction run, record the result of
  `git diff --name-only -- CharacterPackage/semantic_layer_v8`.
- Any non-empty v8 diff makes the intake report invalid until reverted by the
  owner of that change.
- External dataset tools may read v8 masks/specs for coordinate comparison, but
  they must not write to v8.
- Derived priors should feed only a later reviewed schema/manual-curve package,
  for example `primary_curve_bundle_v1`, and should keep status such as
  `manual_review_required` until a human accepts the visible result.
- No external manifest can mark a YUNA hair candidate as accepted. Acceptance
  must stay in the normal YUNA review artifacts, with visual sanity and manual
  review evidence.

## Recommended Top-Level Dataset Manifest Fields

The top-level dataset manifest can summarize the pilot without making
per-asset decisions implicit:

- `dataset_id`
- `manifest_version`
- `created_at`
- `updated_at`
- `purpose`: should state `prior_only`.
- `baseline_guard`: v8 immutable and `replace_in_beauty_glb=false`.
- `asset_manifest_paths`
- `global_default_permission_gates`: all false/pending.
- `allowed_usage_role_enum`
- `blocked_behavior`
- `review_policy`
- `v8_diff_check_policy`

The per-asset manifest remains authoritative for legal/provenance gates.

## Acceptance Criteria For This Scaffold

A future implementation of the scaffold should be considered acceptable only if:

- It can represent source, license, provenance, intake status, usage roles, and
  permission gates without ambiguity.
- It fails closed when legal or provenance fields are missing.
- It supports pointer-only assets where binaries cannot be committed.
- It separates external source assets from derived priors.
- It makes `replace_in_beauty_glb=false` required, not optional.
- It records that `CharacterPackage/semantic_layer_v8` stayed unchanged.
- It prevents external assets from becoming direct YUNA replacement geometry.
