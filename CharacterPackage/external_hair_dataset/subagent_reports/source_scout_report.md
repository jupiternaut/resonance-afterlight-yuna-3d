# Source Scout Report: External Hair Asset Candidates

Prepared by: Subagent A, Source Scout
Date: 2026-05-28
Scope: source discovery and license triage only.

No binaries were downloaded. No external source is approved as replacement YUNA
hair. All entries are priors/references for legal review, benchmark design, or
possible curve/card-template extraction. `CharacterPackage/semantic_layer_v8`
was not modified.

## Candidate Sources

### 1. OpenGameArt: Ponytail hair style for female model

- source_url: https://opengameart.org/content/ponytail-hair-style-for-female-model
- source_name: Ponytail hair style for female model
- claimed_license: CC0
- license_confidence: high
- possible usage_role: Low-poly female ponytail mesh prior for scalp anchor placement, ponytail silhouette, and clump grouping.
- can_commit_binary_to_repo: yes_after_license_snapshot; source page exposes a small `.blend` and claims CC0.
- can_commit_renders: yes.
- can_extract_curve_templates: yes_from_mesh_centerlines; original asset is mesh, not native curves.
- recommendation: open_template_source
- license_reasoning: OpenGameArt page lists License(s): CC0 and the attached `.blend`; still capture the page/license text before intake.

### 2. OpenGameArt: Long hairstyle for male model

- source_url: https://opengameart.org/content/long-hairstyle-for-male-model
- source_name: Long hairstyle for male model
- claimed_license: CC0
- license_confidence: high
- possible usage_role: Broad long-hair sheet/strip topology prior for converting low-poly hair surfaces into guide curves.
- can_commit_binary_to_repo: yes_after_license_snapshot; source page exposes a small `.blend` and texture.
- can_commit_renders: yes.
- can_extract_curve_templates: yes_from_mesh_centerlines; useful for silhouette/strip flow, not production-ready curve grooming.
- recommendation: open_template_source
- license_reasoning: OpenGameArt page lists License(s): CC0 and describes the model as 253 triangles with a basic texture.

### 3. OpenGameArt: Upcomb hair style for male model

- source_url: https://opengameart.org/content/upcomb-hair-style-for-male-model
- source_name: Upcomb hair style for male model
- claimed_license: CC0
- license_confidence: high
- possible usage_role: Short scalp-hugging clump topology prior; useful for compact hair cap coverage and root-zone cleanup.
- can_commit_binary_to_repo: yes_after_license_snapshot; source page exposes a small `.blend` and placeholder texture.
- can_commit_renders: yes.
- can_extract_curve_templates: limited_short_hair_guides; weak match for YUNA long-flow hair but useful as a clean CC0 control.
- recommendation: open_template_source
- license_reasoning: OpenGameArt page lists License(s): CC0 and explicit file attachments.

### 4. OpenGameArt: Short punk hair style for female model

- source_url: https://opengameart.org/content/short-punk-hair-style-for-female-model
- source_name: Short punk hair style for female model
- claimed_license: CC0
- license_confidence: high
- possible usage_role: Female short-hair clump control sample; useful for checking scalp cap segmentation and non-long-hair false positives.
- can_commit_binary_to_repo: yes_after_license_snapshot; source page exposes a small `.blend`.
- can_commit_renders: yes.
- can_extract_curve_templates: limited_short_hair_guides.
- recommendation: open_template_source
- license_reasoning: OpenGameArt page lists License(s): CC0 and a `.blend` attachment; head mesh is described as included only for fit preview.

### 5. OpenGameArt: Side parting hairstyle for male model

- source_url: https://opengameart.org/content/side-parting-hairstyle-for-male-model
- source_name: Side parting hairstyle for male model
- claimed_license: CC0
- license_confidence: high
- possible usage_role: Simple asymmetric parting/topology prior for scalp direction fields and part-line masks.
- can_commit_binary_to_repo: yes_after_license_snapshot; source page exposes a small `.blend`.
- can_commit_renders: yes.
- can_extract_curve_templates: yes_from_mesh_centerlines; mainly a scalp-flow prior.
- recommendation: open_template_source
- license_reasoning: OpenGameArt page lists License(s): CC0 and explicit `.blend` attachment.

### 6. OpenGameArt: Hair Alphas For Days

- source_url: https://opengameart.org/content/hair-alphas-for-days
- source_name: Hair Alphas For Days
- claimed_license: CC0
- license_confidence: high
- possible usage_role: Hair-card opacity/alpha texture prior for material tests and card-render validation fixtures.
- can_commit_binary_to_repo: selected_files_only_after_license_snapshot; avoid committing the full large archive unless explicitly needed.
- can_commit_renders: yes.
- can_extract_curve_templates: no_texture_only; can support card material tests but does not provide geometry guides.
- recommendation: open_template_source
- license_reasoning: OpenGameArt page and per-file pages list CC0; page describes many transparent and black/white alpha PNGs for game hair texturing.

### 7. OpenGameArt: Toon/Low Poly Dread Ponytail

- source_url: https://opengameart.org/content/toonlow-poly-dread-ponytail
- source_name: Toon/Low Poly Dread Ponytail
- claimed_license: CC0
- license_confidence: high
- possible usage_role: Stylized dread/ponytail mass prior for grouped long forms and segment spacing.
- can_commit_binary_to_repo: defer; source page claims CC0, but the zip is about 20 MB, so do not commit during source-scouting.
- can_commit_renders: yes_after_license_snapshot.
- can_extract_curve_templates: yes_after_local_inspection; likely mesh-derived guides, not guaranteed native curves.
- recommendation: pending
- license_reasoning: OpenGameArt page states CC0 and says the asset was made from scratch in Blender; size makes it a second-pass intake candidate.

### 8. OpenGameArt / VRoid: VRoid Studio CC0 models and hair samples

- source_url: https://opengameart.org/content/vroid-studio-cc0-models
- source_name: VRoid Studio CC0 models
- claimed_license: CC0 for listed alpha/beta/sample models and hair samples; AvatarSample A-C excluded by the page as more restrictive.
- license_confidence: high_for_named_hair_samples
- possible usage_role: Anime/stylized hair topology and VRM import reference; useful for separated hair mass priors after import verification.
- can_commit_binary_to_repo: selected_hair_samples_only_after_license_snapshot; avoid bulk avatar zips by default.
- can_commit_renders: yes_for_explicit_cc0_samples.
- can_extract_curve_templates: yes_after_import_verification; preserve topology priors only, not avatar identity.
- recommendation: open_template_source
- license_reasoning: OpenGameArt page claims CC0 and points to VRoid's sample-model conditions; page explicitly distinguishes the CC0 sample set from more restrictive AvatarSample A-C.

### 9. Blend Swap: Hair Factory v1.0

- source_url: https://blendswap.com/blend/5913
- source_name: Hair Factory v1.0
- claimed_license: CC0
- license_confidence: high
- possible usage_role: Low-poly hair workflow/card-style reference; useful for understanding mesh hair authoring and extraction workflows.
- can_commit_binary_to_repo: defer_large_file; source page claims CC0 but lists about 15 MB, so prove intake value before committing.
- can_commit_renders: yes_after_license_snapshot.
- can_extract_curve_templates: yes_workflow_reference; likely mesh/card workflow rather than final YUNA-like long curves.
- recommendation: open_template_source
- license_reasoning: Blend Swap page lists License: CC0, Blender 2.6x, Blender Internal, and tags including hair/low poly.

### 10. Blend Swap: Curly Hair

- source_url: https://blendswap.com/blend/24481
- source_name: Curly Hair
- claimed_license: CC-0
- license_confidence: high
- possible usage_role: Native Bezier-curve curl template prior for curl radius, segmentation, and curve-to-card experiments.
- can_commit_binary_to_repo: yes_after_license_snapshot; page requires login for download, so capture source page before any intake.
- can_commit_renders: yes_after_license_snapshot.
- can_extract_curve_templates: yes_native_bezier_curves.
- recommendation: open_template_source
- license_reasoning: Blend Swap page lists License: CC-0 and description says the hair is made with Bezier Curves.

### 11. Blend Swap: Dynamic Hairstyle Model (1 / 10)

- source_url: https://www.blendswap.com/blend/22778
- source_name: Dynamic Hairstyle Model (1 / 10)
- claimed_license: CC-0
- license_confidence: medium
- possible usage_role: Curve-based long/dynamic hair study for strand grouping, soft-body weighting, and curve point-count priors.
- can_commit_binary_to_repo: pending; single free page claims CC-0, but description cross-links a paid full pack and comments suggest packaging ambiguity.
- can_commit_renders: pending.
- can_extract_curve_templates: pending_but_promising; page says the hair is made of curves with a maximum of 4 points per curve.
- recommendation: pending
- license_reasoning: Blend Swap page claims CC-0 for the listed single model, but the paid-pack context means direct reuse should wait for local file/license inspection.

### 12. Blender Studio: Rain character rig

- source_url: https://studio.blender.org/characters/rain/v3/
- source_name: Rain - Character Rig
- claimed_license: CC-BY
- license_confidence: high
- possible usage_role: Official Blender open-character reference for ponytail/short stylized hair organization, rig integration, and production-scale file structure.
- can_commit_binary_to_repo: not_for_pilot_full_rig; legally possible with attribution, but full character binaries are out of scope for source scout.
- can_commit_renders: yes_with_attribution.
- can_extract_curve_templates: yes_with_attribution_if_hair_is_separable; otherwise use as reference notes only.
- recommendation: reference_report_only
- license_reasoning: Blender Studio page lists License: CC-BY and gives a required Rain Rig credit string.

### 13. Blender Studio: Spring character rig

- source_url: https://studio.blender.org/characters/spring/v1/
- source_name: Spring - Character Rig
- claimed_license: CC-BY
- license_confidence: high
- possible usage_role: Official Blender open-movie reference for broad stylized hair mass, front identity preservation, and rig/hair organization.
- can_commit_binary_to_repo: not_for_pilot_full_rig; legally possible with attribution, but the full rig is not a small hair-template intake.
- can_commit_renders: yes_with_attribution.
- can_extract_curve_templates: yes_with_attribution_if_hair_is_separable.
- recommendation: reference_report_only
- license_reasoning: Blender Studio page lists License: CC-BY and states the rig is free to use with the specified credit.

### 14. Blender Studio: Sintel character rig

- source_url: https://studio.blender.org/characters/5d41a32b8307e9cd1023fa78/v2/
- source_name: Sintel - Character Rig
- claimed_license: CC-BY
- license_confidence: high
- possible usage_role: Official Blender open-movie long-hair reference for scalp anchoring, hair mass silhouette, and hero-character organization.
- can_commit_binary_to_repo: not_for_pilot_full_rig; use attribution-bound references before any extracted derivative.
- can_commit_renders: yes_with_attribution.
- can_extract_curve_templates: yes_with_attribution_if_hair_is_separable.
- recommendation: reference_report_only
- license_reasoning: Blender Studio page lists License: CC-BY for the Sintel rig; use attribution and avoid treating it as CC0.

### 15. Open3DLab: Hair Cards to Curves Tool

- source_url: https://open3dlab.com/project/97f61186-8e4f-4513-9986-7dc0d51b6983/
- source_name: Hair Cards to Curves Tool
- claimed_license: CC0 1.0 Public Domain dedication
- license_confidence: medium_low
- possible usage_role: Local conversion method study for turning game hair cards into Blender hair curves; tool reference, not a hairstyle source.
- can_commit_binary_to_repo: no_for_now; page states license info is uploader-selected and not verified by site moderators.
- can_commit_renders: local_internal_only_until_provenance_is_verified.
- can_extract_curve_templates: yes_for_method_study_only; do not commit extracted outputs based on this tool until provenance is resolved.
- recommendation: local_study_only
- license_reasoning: Page claims CC0 1.0, but also warns uploader license information is not moderator-verified and may have additional terms.

### 16. Daniel Bystedt: Blender geometry nodes - Hair cards from curves

- source_url: https://3dbystedt.gumroad.com/l/hairCardsFromCurves
- source_name: Blender geometry nodes - Hair cards from curves
- claimed_license: no_clear_reuse_license_found_on_listing
- license_confidence: low_for_repo_commit
- possible usage_role: Workflow reference for generating hair cards from curve inputs; useful as an external method reference only.
- can_commit_binary_to_repo: no.
- can_commit_renders: no_for_now; no explicit reusable asset/content license captured from listing.
- can_extract_curve_templates: no_for_repo; can study the public workflow concept but not import package contents into this dataset without a license file.
- recommendation: reference_report_only
- license_reasoning: Listing is free/pay-what-you-want and describes the tool, but the accessible listing text did not expose a CC0/CC-BY-style reuse license.

## Conservative Reject / Watch Notes

- Avoid ArtStation/marketplace "free hair cards" unless the listing exposes a
  clear open asset license. Free price is not equivalent to CC0 or CC-BY.
- Avoid Sketchfab hair-card assets in this first pass unless the page exposes
  license metadata without login/JavaScript ambiguity and the license allows
  derivative template extraction.
- Avoid CC-BY-NC, CC-BY-NC-SA, and ambiguous "personal use" assets for repo
  commit or curve-template extraction.

## Triage Summary

- Best first intake candidates: OpenGameArt ponytail, long hairstyle, side
  parting, upcomb, and short punk hair assets; Blend Swap Curly Hair is the best
  native-curve candidate if login/download inspection confirms the page license.
- Best material/card fixture: OpenGameArt Hair Alphas For Days, selected PNGs
  only.
- Best anime/stylized topology candidate: VRoid CC0 hair samples, after
  import/conversion verification and license snapshot capture.
- Best Blender open-project references: Rain, Spring, and Sintel, all
  attribution-bound and better suited to reference reports before binary intake.
- No source should replace YUNA hair directly. Use these sources only as priors,
  legal-audited templates, benchmarks, or extraction-method references.
