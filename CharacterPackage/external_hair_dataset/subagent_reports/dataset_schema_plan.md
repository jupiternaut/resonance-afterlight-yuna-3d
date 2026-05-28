# External Hair Dataset Schema Plan

Subagent: B - Dataset Schema Planner

Scope: dataset scaffold and manifest schema plan for external hair references.
This report is planning material only. It does not create assets, does not
modify the current manifest/schema/final files, and does not alter
`CharacterPackage/semantic_layer_v8`.

Core rule: external hair references can become legal, visual, benchmark, or
parametric priors. They are not replacement YUNA hair, not production topology,
and not a path to changing `replace_in_beauty_glb=false`.

## Repo-Relative Directory Scaffold

Use a scaffold that separates source metadata, legal evidence, quarantined
downloads, inspected outputs, derived priors, and validation reports:

```text
CharacterPackage/external_hair_dataset/
  README.md
  SOURCE_TRIAGE.md
  assets_manifest.json
  assets_manifest.schema.json
  external_hair_dataset_pilot_v0_report.json

  subagent_reports/
    dataset_schema_plan.md
    source_scout_report.md
    intake_pipeline_plan.md
    hair_prior_plan.md
    test_contract_plan.md

  license_evidence/
    <asset_id>/
      source_terms_snapshot.txt
      license_text_snapshot.txt
      attribution.txt
      reviewer_notes.md

  manifests/
    dataset_manifest.json
    sources/
      <asset_id>.source.json
    intake/
      <asset_id>.intake.json
    priors/
      <asset_id>.prior_manifest.json

  sources/
    quarantine/
      <asset_id>/
        README.md
        .gitkeep
    external_only/
      <asset_id>/
        pointer.json
    approved_binary/
      <asset_id>/
        README.md

  probes/
    <asset_id>/
      source_probe_front.png
      source_probe_turntable_contact.png
      render_probe_report.json
      import_probe_report.json

  priors/
    <asset_id>/
      silhouette_prior.json
      flow_prior.json
      curve_template_prior.json
      quality_prior.json
      extraction_report.json

  reports/
    <asset_id>/
      license_audit_report.json
      file_inventory_report.json
      intake_validation_report.json
      skipped_with_reason.json
    dataset_validation_summary.json
```

Scaffold rules:

- Paths stored in manifests must be repo-relative.
- The top-level manifest stores source records and report references, not binary
  payloads.
- `sources/quarantine/` is a local review boundary, not approval for downstream
  YUNA use.
- `approved_binary/` is allowed only after explicit license/provenance review;
  the pilot default remains metadata and derived-prior oriented.
- `priors/` contains abstracted measurements or parameter hints, never direct
  YUNA replacement geometry.

## Manifest Source Fields

Each source record should be a single auditable object keyed by a stable
`source_id` / `asset_id`. Required groups:

### Identity

- `schema_version`
- `dataset_id`
- `source_id`
- `asset_id`
- `display_name`
- `source_url`
- `download_url`
- `source_platform`
- `author_name`
- `author_url`
- `publisher_name`
- `retrieved_at`
- `record_created_at`
- `record_updated_at`

### License

- `claimed_license`
- `license_spdx_id`
- `license_url`
- `license_text_snapshot_path`
- `source_terms_snapshot_path`
- `license_confidence`: `high`, `medium-high`, `medium`, `medium-low`, `low`,
  or `unknown`
- `license_review_status`: `pending`, `approved_for_prior_use`,
  `needs_human_legal_review`, `blocked`, or `rejected`
- `attribution_required`
- `attribution_text`
- `commercial_use_allowed`
- `redistribution_allowed`
- `derivatives_allowed`
- `render_publication_allowed`
- `binary_commit_allowed`
- `local_study_allowed`
- `license_restrictions`
- `license_reviewer`
- `license_reviewed_at`

### Provenance

- `original_filename`
- `original_file_hashes`
- `source_metadata_hash`
- `local_pointer_path`
- `archive_member_paths`
- `derived_from_asset_ids`
- `known_modifications`
- `normalization_steps`
- `import_tool`
- `import_tool_version`
- `provenance_confidence`: `high`, `medium`, `low`, or `unknown`
- `provenance_notes`

### Usage Role

- `external_asset_usage`: must be `prior_only`
- `allowed_usage_roles`: array of controlled roles
- `forbidden_usage_roles`: array of controlled roles
- `possible_usage_role`: short human summary
- `downstream_consumers_allowed`
- `downstream_consumers_forbidden`
- `replace_in_beauty_glb`: must be `false`
- `direct_yuna_geometry_replacement_allowed`: must be `false`

Recommended allowed role enum:

- `legal_audit_only`
- `visual_reference_only`
- `benchmark_render`
- `segmentation_fixture`
- `silhouette_prior`
- `flow_direction_prior`
- `curve_template_prior`
- `density_prior`
- `material_palette_reference`
- `negative_fixture`

Forbidden role enum:

- `replacement_candidate`
- `beauty_glb_source`
- `production_hair_asset`
- `texture_transfer_source`
- `direct_mesh_transfer_source`

### Representation Type

- `representation_type`: `hair_mesh`, `hair_cards`, `curve_groom`,
  `particle_hair`, `alpha_texture_set`, `image_reference`,
  `render_reference`, `rigged_character_package`, `tool_or_workflow`, or
  `mixed_package`
- `file_formats`
- `has_geometry`
- `has_textures`
- `has_rig`
- `has_animation`
- `has_blender_modifiers`
- `requires_external_plugins`
- `unit_scale_known`
- `coordinate_system_known`
- `hair_semantic_groups_observed`: examples include `bangs`,
  `side_hair_left`, `side_hair_right`, `back_hair`, `ponytail`, `braid`,
  `short_clump`, or `unknown`

### Quality

- `quality_review_status`: `not_reviewed`, `reviewed_reference_only`,
  `usable_as_prior`, `weak_prior`, `blocked`, or `rejected`
- `hair_relevance_score`: 0-5
- `license_safety_score`: 0-5
- `provenance_confidence_score`: 0-5
- `technical_import_score`: 0-5
- `visual_probe_score`: 0-5
- `yuna_prior_value_score`: 0-5
- `quality_flags`: controlled strings such as `long_hair`, `anime_style`,
  `cards_visible`, `curves_visible`, `dirty_mesh`, `unclear_scale`,
  `opaque_license`, `bulk_archive`, `plugin_dependency`
- `quality_notes`

## Asset Intake Fields

Downloaded or inspected assets need a separate intake record. This prevents a
source entry from being treated as approval to use a binary.

Required intake fields:

- `asset_id`
- `intake_id`
- `intake_status`: `proposed`, `source_identified`, `license_pending`,
  `license_blocked`, `downloaded_quarantine`, `hash_recorded`,
  `import_probe_pending`, `import_probe_complete`, `render_probe_pending`,
  `render_probe_complete`, `prior_extraction_pending`, `prior_extracted`,
  `eligible_for_prior_use`, `rejected`, or `retired`
- `intake_started_at`
- `intake_completed_at`
- `intake_operator`
- `download_status`: `not_downloaded`, `downloaded_to_quarantine`,
  `download_skipped`, or `download_blocked`
- `downloaded_at`
- `download_url_used`
- `local_quarantine_path`
- `local_external_only_path`
- `repo_committed_binary_paths`
- `file_count`
- `total_size_bytes`
- `sha256`
- `hash_manifest_path`
- `mime_types`
- `archive_inventory_path`
- `security_notes`
- `import_probe_status`
- `import_tool`
- `import_tool_version`
- `import_errors`
- `render_probe_status`
- `render_probe_paths`
- `render_probe_report_path`
- `extraction_status`
- `extraction_report_path`
- `derived_prior_paths`
- `skipped_with_reason`
- `manual_review_required`
- `reviewer_notes`

Eligibility rule: an intake can become `eligible_for_prior_use` only when legal
review, provenance review, file inventory, import/render probe, and derived
prior extraction all have explicit passing reports or explicit
`skipped_with_reason` records accepted by review.

## No-Binary Policy For Unclear Licenses

Default to no binary commit unless the source has explicit, archived, and
reviewed permission.

If `license_confidence` is `medium-low`, `low`, or `unknown`, or if
`license_review_status` is `pending`, `needs_human_legal_review`, `blocked`, or
`rejected`:

- do not commit source binaries;
- do not commit extracted source geometry;
- do not commit source textures;
- do not commit derivative curve templates that preserve source geometry too
  closely;
- do not publish source renders unless render publication is separately
  allowed;
- keep only pointer metadata, license notes, and a `skipped_with_reason` report;
- mark `allowed_usage_roles` as `legal_audit_only` or
  `visual_reference_only` at most.

For unclear licenses, a local-only download may exist only as a temporary
quarantine item for human review. The manifest must record it as
`downloaded_quarantine` or `download_blocked`, and downstream tools must treat
it as unavailable for prior extraction.

## External Assets Become Priors, Not Replacements

External assets may influence YUNA only through derived, reviewed prior data:

- silhouette envelopes;
- scalp anchor hypotheses;
- primary curve families;
- width and taper profiles;
- strand/card density ranges;
- depth-order hints;
- topology pattern notes;
- benchmark renders for extractor validation;
- negative examples that teach validators what to reject.

They must not be used as:

- direct mesh replacement for YUNA hair;
- source texture transfer;
- a beauty GLB input;
- proof that a YUNA candidate passed visual review;
- permission to modify `CharacterPackage/semantic_layer_v8`;
- permission to change `replace_in_beauty_glb=false`.

Derived prior records should include:

- `prior_id`
- `asset_id`
- `prior_kind`
- `source_record_path`
- `intake_record_path`
- `output_path`
- `extraction_method`
- `coordinate_space`: `source_asset_local`, `normalized_unit_head`,
  `yuna_reference_view_2d`, or `yuna_semantic_group_space`
- `scale_basis`
- `semantic_group_hypotheses`
- `confidence`
- `limitations`
- `contains_third_party_geometry`
- `contains_third_party_texture`
- `can_influence_yuna_theta_p`
- `allowed_downstream_consumers`
- `forbidden_downstream_consumers`

`can_influence_yuna_theta_p` should default to `false`. Set it to `true` only
after legal/provenance review and a validation report confirm that the prior is
abstract enough for YUNA schema work.

## Validation And Report Artifacts For Later Intake

Later intake should produce small, auditable artifacts before any prior is
allowed downstream:

- `license_evidence/<asset_id>/source_terms_snapshot.txt`
- `license_evidence/<asset_id>/license_text_snapshot.txt`
- `license_evidence/<asset_id>/attribution.txt`
- `reports/<asset_id>/license_audit_report.json`
- `reports/<asset_id>/file_inventory_report.json`
- `reports/<asset_id>/intake_validation_report.json`
- `reports/<asset_id>/skipped_with_reason.json` when any gate is skipped
- `probes/<asset_id>/import_probe_report.json`
- `probes/<asset_id>/render_probe_report.json`
- `probes/<asset_id>/source_probe_front.png` when render publication is allowed
- `priors/<asset_id>/extraction_report.json`
- `priors/<asset_id>/<prior_kind>.json`
- `reports/dataset_validation_summary.json`

Minimum dataset-level validation checks:

- all manifest paths are repo-relative;
- every source has license, provenance, usage role, representation type, and
  quality fields;
- unclear licenses have no committed binary paths;
- each committed binary path has matching license approval and SHA-256 hash;
- every prior references a reviewed source and reviewed intake record;
- every prior has `external_asset_usage=prior_only`;
- every YUNA guard keeps `replace_in_beauty_glb=false`;
- no validation step writes under `CharacterPackage/semantic_layer_v8`;
- skipped render/import/extraction work has explicit `skipped_with_reason`;
- dataset summary labels unresolved cases as `pending`, `blocked`, or
  `manual_review_required`, not passed.

Recommended final status labels:

- `metadata_only`
- `quarantine_only`
- `reference_only`
- `prior_extracted_pending_review`
- `eligible_for_prior_use`
- `blocked_license`
- `blocked_provenance`
- `blocked_quality`
- `manual_review_required`

## Acceptance Boundary

This scaffold is complete when it enables a later agent to:

- record legal/provenance evidence without downloading binaries;
- quarantine and inspect explicit assets without treating them as approved;
- generate small render/import/extraction reports when licenses allow;
- extract abstract priors that can be reviewed independently;
- prove that v8 remained unchanged;
- keep all external assets as prior sources rather than replacements.
