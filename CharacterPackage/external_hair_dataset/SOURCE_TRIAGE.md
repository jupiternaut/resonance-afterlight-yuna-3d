# Source Triage: External Hair Dataset Pilot v0

Prepared from the five subagent reports under `subagent_reports/`.

No binaries were downloaded. No external source is approved as YUNA replacement
hair. Every row is `prior_only`, and the dataset-level replacement policy is
`replace_in_beauty_glb=false`. Recommendations are conservative and may be
downgraded after direct license capture or local intake.

| source_id | source_name | claimed_license | confidence | usage role | binary policy | renders | curve/templates | recommendation |
|---|---|---:|---:|---|---|---|---|---|
| `opengameart_ponytail_female` | OpenGameArt Ponytail hair style for female model | CC0 | high | ponytail/scalp anchor and low-poly clump prior | `yes_after_license_snapshot` | `yes` | `yes_from_mesh_centerlines` | `open_template_source` |
| `opengameart_long_male` | OpenGameArt Long hairstyle for male model | CC0 | high | long flat-hair silhouette and strip prior | `yes_after_license_snapshot` | `yes` | `yes_from_mesh_centerlines` | `open_template_source` |
| `opengameart_upcomb_male` | OpenGameArt Upcomb hair style for male model | CC0 | high | compact scalp-hugging short-hair topology | `yes_after_license_snapshot` | `yes` | `limited_short_hair` | `open_template_source` |
| `opengameart_hair_alphas_for_days` | OpenGameArt Hair Alphas For Days | CC0 | high | alpha/card material fixture source | `partial_selected_small_files_only` | `yes` | `no_texture_only` | `open_template_source` |
| `opengameart_vroid_cc0_samples` | OpenGameArt / VRoid Studio CC0 models and hair samples | CC0 for listed hair samples | high | anime/stylized hair topology and VRM import reference | `yes_selected_cc0_files_after_review` | `yes_selected_cc0_files` | `yes_after_import_verification` | `open_template_source` |
| `blendswap_hair_factory` | Blend Swap Hair Factory v1.0 | CC0 | high | low-poly hair workflow and card/tooling reference | `yes_after_license_snapshot_but_defer_large_file` | `yes` | `yes_workflow_reference` | `open_template_source` |
| `blendswap_curly_hair` | Blend Swap Curly Hair | CC0 | high | Bezier-curve curl template prior | `yes_after_license_snapshot` | `yes` | `yes_curve_templates` | `open_template_source` |
| `blendswap_braided_hair` | Blend Swap Braided Hair | CC0 | high | braid topology and interleaved strand prior | `yes_after_license_snapshot` | `yes` | `yes_from_mesh_or_modifiers` | `open_template_source` |
| `blendswap_dynamic_hairstyle_1` | Blend Swap Dynamic Hairstyle Model (1 / 10) | CC-0 claimed | medium | dynamic curve hair study | `pending_paid_pack_context` | `pending` | `pending` | `pending` |
| `open3dlab_hair_cards_to_curves` | Open3DLab Hair Cards to Curves Tool | CC0 claimed by uploader | medium-low | local conversion method study | `no_uploader_license_unverified` | `local_internal_only` | `local_study_only` | `local_study_only` |
| `blender_studio_sintel_rig` | Blender Studio Sintel character rig | CC-BY | medium-high | open-movie long hair and scalp organization reference | `yes_with_attribution_after_review` | `yes_with_attribution` | `yes_with_attribution_if_separable` | `reference_report_only` |
| `blender_studio_spring_rig` | Blender Studio Spring character rig | CC-BY | high | stylized open-movie hair mass and rig organization reference | `yes_with_attribution_after_review` | `yes_with_attribution` | `yes_with_attribution_if_separable` | `reference_report_only` |

## Current Intake Decision

The pilot remains metadata-only. First future intake should prefer small,
explicitly open sources:

1. `opengameart_ponytail_female`
2. `opengameart_long_male`
3. `blendswap_curly_hair`
4. selected files from `opengameart_hair_alphas_for_days`
5. selected CC0 VRoid hair samples after local import verification

Do not begin with full Blender Studio character rigs or bulk texture archives.

<!-- source_expansion_v1:start -->
## Source Expansion v1

Route: `external_hair_source_expansion_v1`.

This expansion records curated, source-checked candidates for future external hair priors. It does not download binaries, generate YUNA hair, or unblock cloth.

| source_id | representation | quality | yuna relevance | priority | recommendation | binary policy | reason |
|---|---|---:|---:|---|---|---|---|
| `vroid_hairsample_female_cc0` | vroid_vrm_hair_cards_or_meshes | 0.92 | 0.90 | high | open_template_source | `yes_selected_cc0_files_after_review` | Anime female hair template prior for bangs, side curtains, back mass, and scalp anchors. |
| `vroid_hairsample_male_cc0` | vroid_vrm_hair_cards_or_meshes | 0.86 | 0.72 | high | open_template_source | `yes_selected_cc0_files_after_review` | Anime hair card/clump topology prior and scalp anchor convention reference. |
| `opengameart_vroid_cc0_samples` | vroid_vrm_hair_cards_or_meshes | 0.84 | 0.88 | high | open_template_source | `yes_selected_cc0_files_after_review` | Umbrella source for VRoid CC0 anime/stylized hair sample intake. |
| `blendswap_curly_hair` | curve_hair | 0.78 | 0.58 | high | open_template_source | `yes_after_license_snapshot` | Bezier-curve curl and curve-width template prior. |
| `opengameart_hair_alphas_for_days` | hair_alpha_material_pack | 0.76 | 0.62 | high | open_template_source | `partial_selected_small_files_only` | Hair alpha/material fixture source for card transparency and strand texture tests. |
| `charm_anime_hair_method_reference` | method_reference_control_point_hair_cards | 0.90 | 0.88 | medium | reference_report_only | `no_method_reference_only` | Anime hair control-point schema and card-sequence planning reference. |
| `diffhaircard_method_reference` | method_reference_hair_card_extraction | 0.84 | 0.70 | low | reference_report_only | `no_method_reference_only` | Hair card clustering, texture/geometry optimization, and LoD planning reference. |
| `blender_studio_spring_rig` | open_movie_stylized_hair_reference | 0.83 | 0.72 | medium | reference_report_only | `yes_with_attribution_after_review` | Reference-only stylized hair mass and rig organization study. |
| `blender_studio_sintel_rig` | open_movie_character_hair_reference | 0.79 | 0.64 | medium | reference_report_only | `yes_with_attribution_after_review` | Reference-only long-hair organization and DCC rig/handoff study. |
| `blendswap_braided_hair` | ribbon_or_solid_braid_mesh | 0.66 | 0.36 | medium | open_template_source | `yes_after_license_snapshot` | Braid topology and repeated interleaved-strand prior. |
| `opengameart_ponytail_female` | solid_lowpoly_hair_mesh | 0.48 | 0.42 | low | open_template_source | `yes_after_license_snapshot` | Existing probe retained as a low-poly ponytail/back-mass prior, not a quality target. |
| `opengameart_long_male` | lowpoly_hair_cards_or_strips | 0.44 | 0.38 | low | open_template_source | `yes_after_license_snapshot` | Existing probe retained as a low/medium strip-hair and sheet-risk prior. |

High-priority next intake candidates:
- `vroid_hairsample_female_cc0`: VRoid Studio CC0 HairSample_Female (yes_selected_cc0_files_after_review)
- `vroid_hairsample_male_cc0`: VRoid Studio CC0 HairSample_Male (yes_selected_cc0_files_after_review)
- `opengameart_vroid_cc0_samples`: OpenGameArt / VRoid Studio CC0 models and hair samples (yes_selected_cc0_files_after_review)
- `blendswap_curly_hair`: Blend Swap Curly Hair (yes_after_license_snapshot)
- `opengameart_hair_alphas_for_days`: OpenGameArt Hair Alphas For Days (partial_selected_small_files_only)

The two existing probe sources remain retained but are explicitly low/medium prior quality, not quality targets.
<!-- source_expansion_v1:end -->
