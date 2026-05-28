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
