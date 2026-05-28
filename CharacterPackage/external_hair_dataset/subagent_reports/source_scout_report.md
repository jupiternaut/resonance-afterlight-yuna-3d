# Source Scout Report: External Hair Asset Candidates

Prepared by: Subagent A, Source Scout
Date: 2026-05-28
Scope: Source discovery only. No assets were downloaded. No binaries were generated.

Hard boundary: `CharacterPackage/semantic_layer_v8` was not modified.

## Candidate Sources

### 1. OpenGameArt: Ponytail hair style for female model

- source_url: https://opengameart.org/content/ponytail-hair-style-for-female-model
- source_name: Ponytail hair style for female model
- claimed_license: CC0
- license_confidence: high
- possible usage_role: Low-poly female ponytail mesh template; useful for scalp anchor placement, ponytail silhouette, and low-poly clump grouping.
- can_commit_binary_to_repo: yes, legally likely safe if the source URL and CC0 license snapshot are recorded; file is small `.blend` only, but still prefer manifest entry before intake.
- can_commit_renders: yes.
- can_extract_curve_templates: yes, as derived centerlines from the ponytail mesh; original is mesh, not native curve hair.
- recommendation: open_template_source
- notes: Source page lists 867 triangles, unwrapped, no texture, and a `.blend` file.

### 2. OpenGameArt: Long hairstyle for male model

- source_url: https://opengameart.org/content/long-hairstyle-for-male-model
- source_name: Long hairstyle for male model
- claimed_license: CC0
- license_confidence: high
- possible usage_role: Simple long flat-hair silhouette and strip-like low-poly reference; useful for converting broad hair-sheet meshes into curve priors.
- can_commit_binary_to_repo: yes, legally likely safe if the source URL and CC0 license snapshot are recorded; files are small `.blend` and PNG.
- can_commit_renders: yes.
- can_extract_curve_templates: yes, from mesh/card centerlines; limited because the source is not authored as curve hair.
- recommendation: open_template_source
- notes: Source page lists 253 triangles, basic texture, `.blend`, and `hair.png`.

### 3. OpenGameArt: Upcomb hair style for male model

- source_url: https://opengameart.org/content/upcomb-hair-style-for-male-model
- source_name: Upcomb hair style for male model
- claimed_license: CC0
- license_confidence: high
- possible usage_role: Short-hair low-poly clump reference; useful as a compact scalp-hugging hairstyle topology sample.
- can_commit_binary_to_repo: yes, legally likely safe if the source URL and CC0 license snapshot are recorded; files are small `.blend` and PNG.
- can_commit_renders: yes.
- can_extract_curve_templates: yes, but value is limited to short-hair clump direction and scalp coverage, not long YUNA-like flow.
- recommendation: open_template_source
- notes: Source page lists 236 triangles and a placeholder texture.

### 4. OpenGameArt: Hair Alphas For Days

- source_url: https://opengameart.org/content/hair-alphas-for-days
- source_name: Hair Alphas For Days
- claimed_license: CC0
- license_confidence: high
- possible usage_role: Hair-card alpha/opacity texture reference for card material tests; useful for straight, wavy, curly, clump, and tuft masks.
- can_commit_binary_to_repo: partial; individual selected PNGs can likely be committed with license snapshot, but do not commit the 138.5 MB bulk zip unless the repo explicitly wants large texture payloads.
- can_commit_renders: yes.
- can_extract_curve_templates: no; texture-only source. Can support hair-card material tests, not curve extraction.
- recommendation: open_template_source
- notes: Source page lists 85 transparent and black/white alpha PNGs for game hair texturing.

### 5. OpenGameArt / VRoid: VRoid Studio CC0 models and hair samples

- source_url: https://opengameart.org/content/vroid-studio-cc0-models
- source_name: VRoid Studio CC0 models
- claimed_license: CC0, with official VRoid FAQ linked from the source page
- license_confidence: high for HairSample_Male, HairSample_Female, and listed CC0 beta/sample models; not high for AvatarSample_A/B/C because the source page explicitly excludes those as more restrictive.
- possible usage_role: Anime/stylized hair sample reference; useful for VRM/glTF-to-Blender import checks, hair-card topology study, and separated hair mass priors.
- can_commit_binary_to_repo: yes for the explicitly listed CC0 files if license snapshot is recorded, but intake should select only hair sample files or small extracted derivatives; avoid committing all 11-17 MB zips by default.
- can_commit_renders: yes for explicitly listed CC0 samples.
- can_extract_curve_templates: yes after local import/conversion verification; templates should preserve only hair topology/curve priors, not full avatar identity.
- recommendation: open_template_source
- notes: The linked official VRoid FAQ states some models are CC0 and specifically lists HairSample_Male and HairSample_Female under CC0 models.

### 6. Blend Swap: Hair Factory v1.0

- source_url: https://blendswap.com/blend/5913
- source_name: Hair Factory v1.0
- claimed_license: CC0
- license_confidence: high
- possible usage_role: Low-poly hair mesh workflow reference; useful for understanding particle-to-texture/low-poly hair-card style workflows.
- can_commit_binary_to_repo: yes if the source page/license snapshot is recorded, but the `.blend` is about 15 MB and should be committed only after intake value is proven.
- can_commit_renders: yes.
- can_extract_curve_templates: yes for derived mesh/card template study; source appears workflow/tool-like rather than a final hairstyle.
- recommendation: open_template_source
- notes: Blend Swap page lists Blender 2.6x, Blender Internal, 15 MB, tags `hair low Poly`, and CC0.

### 7. Blend Swap: Curly Hair

- source_url: https://blendswap.com/blend/24481
- source_name: Curly Hair
- claimed_license: CC0
- license_confidence: high
- possible usage_role: Native Bezier-curve curly hair reference; useful for curve segmentation, curl radius priors, and non-card curve extraction.
- can_commit_binary_to_repo: yes if the source page/license snapshot is recorded; file is small, about 830 KB.
- can_commit_renders: yes.
- can_extract_curve_templates: yes; this is one of the strongest curve-template candidates because the page says it is made with Bezier curves.
- recommendation: open_template_source
- notes: Strong candidate for curve-template extraction rather than just visual reference.

### 8. Blend Swap: Braided Hair

- source_url: https://blendswap.com/blend/18823
- source_name: Braided Hair
- claimed_license: CC0
- license_confidence: high
- possible usage_role: Braid topology and procedural/modifier stack reference; useful for strand grouping and repeated interleaved hair forms.
- can_commit_binary_to_repo: yes if the source page/license snapshot is recorded; file is about 6.51 MB.
- can_commit_renders: yes.
- can_extract_curve_templates: yes, but likely from mesh/modifier reconstruction rather than direct authored guide curves.
- recommendation: open_template_source
- notes: Page says it uses output from Hair Factory and a simple mesh with Array, Simple Deform, Subsurf, and Curve modifiers.

### 9. Blend Swap: Dynamic Hairstyle Model (1 / 10)

- source_url: https://blendswap.com/blend/22778
- source_name: Dynamic Hairstyle Model (1 / 10)
- claimed_license: CC-0
- license_confidence: medium
- possible usage_role: Curve-based dynamic hairstyle sample; useful for SoftBody/curve-weighted hair motion study and long strand grouping.
- can_commit_binary_to_repo: pending; source page shows CC-0 for the single sample, but the description cross-links a paid full pack, so capture the asset page and inspect the downloaded file before any commit.
- can_commit_renders: pending; likely yes if the single free sample license is confirmed, but keep conservative until intake.
- can_extract_curve_templates: pending; promising because the page says the hair is made of curves with a maximum of 4 points per curve.
- recommendation: pending
- notes: Treat as a candidate to revisit after local license/download inspection, not a first-pass safe source.

### 10. Open3DLab: Hair Cards to Curves Tool

- source_url: https://open3dlab.com/project/97f61186-8e4f-4513-9986-7dc0d51b6983/
- source_name: Hair Cards to Curves Tool
- claimed_license: CC0 1.0 Public Domain dedication
- license_confidence: medium-low
- possible usage_role: Local conversion workflow reference for turning hair cards into Blender hair curves; useful for evaluating extraction methods, not as a hairstyle asset.
- can_commit_binary_to_repo: no for now; the page itself says license information is uploader-selected and not verified by site moderators.
- can_commit_renders: local/internal only unless provenance is verified.
- can_extract_curve_templates: yes for local method study; do not commit extracted outputs based on this tool until provenance is resolved.
- recommendation: local_study_only
- notes: Useful small tool candidate, but the uploader-unverified license warning makes it unsuitable as a clean repo asset source on first pass.

### 11. Blender Studio: Sintel character rig

- source_url: https://studio.blender.org/characters/5d41a32b8307e9cd1023fa78/v2/
- source_name: Sintel - Character Rig
- claimed_license: CC-BY
- license_confidence: medium-high
- possible usage_role: Open-movie hero-character hair study; useful for long stylized hair mass, scalp anchoring, and production hair organization reference.
- can_commit_binary_to_repo: yes_with_attribution only after capturing the asset page/license text and including attribution; avoid committing large full-character binary unless the hair extraction is justified.
- can_commit_renders: yes_with_attribution.
- can_extract_curve_templates: yes_with_attribution if the downloaded rig exposes separable hair geometry/curves; derived templates must preserve attribution.
- recommendation: reference_report_only
- notes: Prefer as a Blender-open-project reference first, not a direct binary intake source.

### 12. Blender Studio: Spring character rig

- source_url: https://studio.blender.org/characters/spring/v1/
- source_name: Spring - Character Rig
- claimed_license: CC-BY
- license_confidence: high
- possible usage_role: Stylized open-movie hair and character silhouette study; useful for broad hair mass, front-view identity preservation, and production rig organization.
- can_commit_binary_to_repo: yes_with_attribution only after asset-page capture and attribution; not recommended to commit the full character binary for this pilot.
- can_commit_renders: yes_with_attribution.
- can_extract_curve_templates: yes_with_attribution if hair geometry is separable; otherwise use for reference notes only.
- recommendation: reference_report_only
- notes: Official Blender Studio page lists the rig as CC-BY; good source for study, lower priority for direct YUNA template extraction.

## Conservative Reject / Low-Priority Notes

- Daniel Bystedt `Hair Cards From Curves` Gumroad listing is relevant, but the listing found in this pass clearly shows free pricing and workflow description, not a clear reusable asset license. Keep as `pending` unless a license file is found in the download.
- ArtStation "free hair cards" listings are not first-pass candidates because common marketplace standard licenses are not equivalent to CC0/CC-BY open asset licenses.
- Sketchfab hair-card listings may be useful, but at least one page required JavaScript verification or did not expose the license in the accessible page text. Keep them out of the first intake until license capture is reliable.

## Triage Summary

- Best first intake candidates: OpenGameArt Micket ponytail, long hairstyle, upcomb hairstyle; Blend Swap Curly Hair; OpenGameArt Hair Alphas For Days selected PNGs.
- Best anime/stylized reference candidate: VRoid CC0 hair samples, but import/conversion needs a local verification step before extraction.
- Best Blender open-project references: Sintel and Spring rigs, both attribution-bound and better suited to reference reports before binary intake.
- Do not start by committing bulk zips or full character rigs. First intake should capture license pages, download only small targeted files, record checksums, and produce local renders/extraction proof.
- No candidate should be used to replace YUNA hair directly. These sources are for priors, benchmarks, and possible curve-template extraction only.
