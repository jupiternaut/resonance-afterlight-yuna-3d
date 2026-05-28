# External Hair Asset Intake Pipeline Plan

Subagent: C - Intake Pipeline Planner  
Scope: plan only. No assets, manifests, schemas, README files, or
`semantic_layer_v8` changes are produced by this report.

## Boundary

- Treat every external hair asset as a candidate reference/input only.
- Keep `CharacterPackage/semantic_layer_v8` immutable.
- Keep `replace_in_beauty_glb=false` for every external asset.
- Do not download large binary payloads. Record source metadata and skip the
  payload when size is above the configured intake cap, when size is unknown on
  a remote source, or when the source requires a bulk/archive download.
- If the license is unknown, unclear, incompatible, or missing, record metadata
  only. Do not download, import, render, classify as usable, or derive assets
  from it.
- Do not run embedded scripts from `.blend` files or other asset containers.
- Do not call any imported asset final production topology.

## Pipeline Overview

1. Source registration
   - Record source URL or local path, provider, title, author if available,
     stated license, access date, declared file formats, declared file size,
     and preview links.
   - Gate before download:
     - license must be explicit and usable for review/research intake;
     - binary size must be within the configured intake cap;
     - source must not require downloading a large bundle to inspect one hair
       asset;
     - archive contents must be inspectable without unsafe path writes.
   - If any gate fails, stop at metadata and emit `skipped_with_reason`.

2. Import staging
   - Use an isolated candidate workspace outside `semantic_layer_v8`.
   - Store only small allowed source files and derived inspection records.
   - Preserve original filenames and source hashes when a download is allowed.
   - Never normalize, convert, or repair the asset as a persistent output during
     intake. Temporary conversions are allowed only inside the render process and
     must not become dataset assets.

3. Inspect
   - Read scene/object structure, modifiers, materials, texture references,
     alpha settings, geometry counts, curve/particle systems, and bounding boxes.
   - Inspect texture metadata and alpha channels when texture files are present.
   - Record missing texture paths instead of trying to replace them.
   - Flag suspicious content: executable scripts, broken archives, paid-only
     assets, unclear license, missing geometry, or files that require proprietary
     plugins.

4. Render
   - Produce a review pack only when license, size, import, and Blender gates
     pass.
   - Required outputs are `front`, `yaw30`, `side`, `wire`, `alpha`, `depth`,
     and `normal`.
   - Each required output must either exist or have an explicit
     `skipped_with_reason`.

5. Classify
   - Classify with evidence priority:
     structural scene data first, material/texture evidence second, render
     evidence third, filename/provider labels last.
   - Record a primary class plus secondary tags when the asset is mixed.
   - Leave ambiguous assets as `classification_deferred` rather than forcing a
     class.

## Asset Categories

| Category | Primary evidence | Intake notes | Common reject/defer reasons |
| --- | --- | --- | --- |
| `particle_hair` | Blender particle hair systems, groom systems, root/strand settings, child hairs, hair length controls, strand material slots | Inspect emitter object, particle settings, strand count, child count, render-as-path settings, root distribution, material bindings, and whether the groom can render headless | no Blender support, particle system hidden/disabled, requires proprietary groom plugin, no renderable strand material |
| `curve_hair` | Bezier/NURBS/poly curves, hair guide curves, bevel depth, taper/width profiles, curve collections | Inspect curve count, spline count, bevel/taper settings, root anchoring, strand grouping, material assignment, and whether curves have renderable thickness | curves have zero bevel/width, curves are guides only, unsupported curve type, missing material |
| `hair_cards` | Thin mesh cards/planes with alpha textures, UV atlases, alpha blend materials, double-sided card setup | Inspect card count, UV coverage, alpha texture paths, material alpha mode, normals, card orientation, atlas dimensions, and overdraw risk | missing alpha textures, opaque planes with no hair texture, alpha channel empty, broken UVs |
| `ribbon_surfaces` | Mesh strips or ribbon-like surfaces with geometric width/taper, usually broader than cards and not solely alpha-defined | Inspect strip count, edge flow, width/taper, connected components, material opacity, silhouette readability, and scalp/flow direction | ribbons are cloth/decoration rather than hair, disconnected fragments, no taper/flow evidence, excessive body/face coverage |
| `solid_sculpt_hair` | Sculpted hair masses, opaque mesh shells, chunky locks, high-volume connected components, baked normals | Inspect mesh volume, connected components, surface normals, sculpt lock boundaries, material separation, and whether it is hair-like from front/yaw/side | solid helmet-like mass, fused face/body geometry, no separate hair material, unusable topology for review |

Mixed assets should keep the strongest class as primary and record secondary
tags, for example `hair_cards` with `curve_hair_guides` or `solid_sculpt_hair`
with `ribbon_surface_bangs`.

## Required Views And Channels

All renders use a normalized object frame, transparent background where
possible, and consistent camera scale across the review pack.

| Output | Purpose | Planned behavior |
| --- | --- | --- |
| `front` | Front shaded view for identity and silhouette readability | Orthographic front camera, neutral material fallback only if original material cannot render but license/import gates pass |
| `yaw30` | Three-quarter volume check | Same camera scale, object or camera yawed 30 degrees, shaded render |
| `side` | Side volume and thickness check | Orthographic side camera, same scale, shaded render |
| `wire` | Geometry structure check | Wire overlay or wire-only render; for particles/curves, show renderable strand/curve paths when supported |
| `alpha` | Opacity and card/ribbon mask sanity | Render alpha pass or extracted material/texture alpha summary image; skip with reason when no alpha data exists |
| `depth` | Camera-space depth readability | Depth pass from the normalized front camera unless import format cannot provide renderable geometry |
| `normal` | Surface/strand orientation sanity | Normal pass from the normalized front camera; for particle/curve hair, use evaluated render geometry when available |

The render report should make no visual claim unless the corresponding image is
present. If an image is absent, the output entry must use `skipped_with_reason`
with the stage, reason code, and short detail.

## Blender Available Behavior

When Blender is available:

- Run Blender headless with auto-execution disabled.
- Use built-in importers and already-installed add-ons only.
- Import into an empty scene and never link to `semantic_layer_v8`.
- For `.blend` files, append/link data with scripts disabled; do not execute
  drivers or text blocks as trusted code.
- Evaluate particle and curve hair only for inspection/rendering. Any temporary
  mesh conversion is scratch-only and must be discarded after render.
- Render `front`, `yaw30`, `side`, `wire`, `alpha`, `depth`, and `normal` when
  the asset supports the required pass.
- Classify using imported object data plus render evidence.
- If one channel fails, keep successful channels and mark only the failed
  channel with `skipped_with_reason`.

## Blender Unavailable Behavior

When Blender is unavailable:

- Do not fail the whole source record.
- Perform metadata-only/static inspection where possible: source metadata,
  extension, file size, archive listing if already local and safe, texture file
  metadata, and declared provider tags.
- Mark every render output (`front`, `yaw30`, `side`, `wire`, `alpha`, `depth`,
  `normal`) as skipped with `reason_code=blender_unavailable`.
- Classification should be `classification_deferred` unless static evidence is
  strong enough to make a narrow metadata-only label.
- Do not claim visual readability, alpha sanity, depth quality, or normal
  quality without rendered evidence.

## `skipped_with_reason` Plan

Use `skipped_with_reason` whenever a source, stage, or required output cannot be
completed. The reason should be short and machine-readable, with a human detail
string.

Recommended reason codes:

- `license_unknown_metadata_only`
- `license_incompatible_metadata_only`
- `large_binary_not_downloaded`
- `remote_size_unknown_not_downloaded`
- `source_requires_bulk_archive`
- `blender_unavailable`
- `unsupported_format_without_importer`
- `import_failed`
- `render_failed`
- `render_timeout`
- `missing_texture_paths`
- `missing_alpha_data`
- `unsafe_archive_paths`
- `embedded_scripts_disabled`
- `proprietary_plugin_required`
- `classification_deferred_insufficient_evidence`

Example wording:

```text
skipped_with_reason:
  stage: render.alpha
  reason_code: missing_alpha_data
  detail: Asset imported successfully, but no material or texture alpha channel
    was present to render an alpha review output.
```

## Category-Specific Inspection Checklist

`particle_hair`

- Confirm emitter object, particle hair settings, visible viewport/render state,
  strand count, child hair settings, length, root distribution, material slots,
  and whether the system renders without scripts or paid plugins.
- Render pass risk: `wire`, `depth`, and `normal` may require evaluated render
  geometry. If evaluation is unavailable, skip those channels individually.

`curve_hair`

- Confirm curve object count, spline count, curve dimensions, bevel/width/taper,
  material slots, root/flow direction, and whether curves are guide-only or
  renderable.
- Render pass risk: zero-width guide curves should be classified as deferred or
  guide-only, not usable rendered hair.

`hair_cards`

- Confirm mesh card count, quad/triangle pattern, UVs, alpha atlas paths,
  material blend mode, double-sided settings, normals, and card grouping.
- Render pass risk: missing alpha textures should skip `alpha` and downgrade
  visual confidence even if shaded front/yaw/side renders exist.

`ribbon_surfaces`

- Confirm mesh strips, taper, width profile, connected components, flow
  direction, material opacity, and whether ribbons read as hair rather than
  cloth/cape/ornament.
- Render pass risk: wire and normal outputs are especially important because
  opaque ribbons can hide bad topology in shaded views.

`solid_sculpt_hair`

- Confirm separate hair mesh/material, connected sculpt locks, normals, vertex
  count, non-hair fused geometry, and whether the silhouette reads as hair from
  front/yaw30/side.
- Render pass risk: alpha may legitimately be skipped with
  `missing_alpha_data`; depth and normal should still be expected when geometry
  imports correctly.

## Classification Decision Rules

- Prefer `particle_hair` when a native hair particle/groom system is present and
  renderable.
- Prefer `curve_hair` when curves/splines are the actual renderable hair
  geometry.
- Prefer `hair_cards` when thin mesh planes plus alpha textures provide the
  hair silhouette.
- Prefer `ribbon_surfaces` when geometric strips/ribbons provide the hair mass
  and alpha is secondary or absent.
- Prefer `solid_sculpt_hair` when opaque sculpted mesh volumes provide the hair
  shape.
- If an asset contains multiple valid systems, record the dominant visible
  system as primary and the others as secondary tags.
- If evidence conflicts, defer classification and keep the asset out of any
  candidate route until manual review.

## Failure And Safety Gates

- Unknown license: metadata only, no download, no import, no render.
- Large binary: metadata only, no download. A small preview image may be
  referenced only if it is already exposed separately by the source page and
  license metadata is clear.
- Blender unavailable: metadata/static inspection only; all render outputs get
  `skipped_with_reason`.
- Unsupported format: record metadata and skip import/render unless an installed
  safe importer exists.
- Missing textures: import can continue for structure, but alpha/material claims
  must be downgraded or skipped.
- Paid/proprietary plugin dependency: metadata only or import-deferred; do not
  attempt replacement conversion.
- Any source that cannot produce the required view/channel evidence must remain
  a dataset intake record, not an accepted hair candidate.

## Verification Criteria For A Future Implementation

- Every source has a terminal intake state: metadata-only, import-deferred,
  render-skipped, classification-deferred, or review-pack-ready.
- Every required output view/channel has either an artifact path or
  `skipped_with_reason`.
- Every category listed in this plan is represented in the classifier decision
  rules.
- Unknown-license and large-binary cases stop before download/import/render.
- Blender unavailable cases still produce metadata records with explicit render
  skips.
- `git diff --name-only -- CharacterPackage/semantic_layer_v8` remains empty.
- No final README, manifest, schema, or generated asset is produced by intake
  planning.
