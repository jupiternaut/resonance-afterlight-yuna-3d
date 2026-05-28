# External Hair Dataset Pilot Test Contract Plan

Subagent E: Test Contract Planner

Scope: planning only. This report defines the expected tests and blocked
behavior for an external hair dataset pilot. It does not implement tests, write
schemas, create manifests, generate assets, or modify `semantic_layer_v8`.

## Assumptions

- External hair dataset inputs are research priors only. They may inform target
  schemas, parameter choices, silhouette hypotheses, or review prompts, but must
  not become direct replacement geometry or direct texture payloads for YUNA.
- The v8 route remains the immutable visual-review and DCC baseline.
- The pilot must remain additive under `CharacterPackage/external_hair_dataset/`
  or future candidate-route directories. It must not overwrite existing exports.
- `cloth_seam_surface` remains blocked while hair route status is failed,
  pending, unreviewed, or license-blocked.
- No large external dataset binaries should be committed. The repo should store
  only small metadata, triage notes, reports, and skipped reports.

## Success Criteria

- Manifest JSON files parse as valid JSON and expose the minimum audit fields
  needed by the pilot.
- Source recommendations use a closed enum, so downstream automation cannot
  silently accept ambiguous labels.
- License confidence defaults conservative and blocks use when evidence is
  missing or unclear.
- Reports explicitly record `replace_in_beauty_glb=false`.
- Reports explicitly record that external assets are priors only.
- Any omitted visual/import validation has `skipped_with_reason`.
- v8 diff check is clean after pilot planning or execution.
- Cloth advancement is reported as blocked until hair has clean target schema,
  acceptable visual review, and license clearance.
- `SOURCE_TRIAGE`, pilot README, and pilot report files are testable as audit
  artifacts, without requiring checked-in external binaries.

## Planned Test Groups

### 1. Manifest JSON Validity

Planned test intent:

- Discover candidate manifest JSON files only inside the external hair dataset
  pilot path or explicit future candidate path.
- Parse each manifest with a strict JSON parser.
- Fail on invalid JSON, trailing comments, duplicate top-level keys if the test
  harness supports detection, or non-object top-level documents.
- Require stable audit fields such as `pilot_id`, `source_id`,
  `source_recommendation`, `license_confidence`, `license_status`,
  `asset_role`, `replace_in_beauty_glb`, and `external_asset_usage`.
- Require `generated_at` or equivalent timestamp only if existing repo patterns
  already use it; do not invent a broader manifest schema in this planning doc.

Blocked behavior:

- Invalid JSON blocks the pilot.
- Missing audit fields blocks the pilot.
- Manifest that names an external asset as direct YUNA replacement blocks the
  pilot.

### 2. Source Recommendation Enum

Planned test intent:

- Validate `source_recommendation` against a closed enum:
  - `use_as_prior`
  - `review_manually`
  - `skip_license_unclear`
  - `skip_quality_mismatch`
  - `blocked`
- Fail on free-form values such as `good`, `ok`, `approved`, or empty strings.
- Treat unknown future values as failing until the contract is intentionally
  updated.

Blocked behavior:

- Any source marked as direct production input blocks the pilot.
- Any source recommendation outside the enum blocks the pilot report.

### 3. License Confidence Conservatism

Planned test intent:

- Validate that license-related fields choose the most conservative state when
  evidence is incomplete.
- Expected confidence bands:
  - `confirmed_clear`
  - `likely_clear_pending_review`
  - `unknown`
  - `restricted`
  - `incompatible`
- Require `license_evidence` or `license_notes` for any state stronger than
  `unknown`.
- Require `blocked_or_pending_reason` when `license_confidence` is `unknown`,
  `restricted`, or `incompatible`.

Blocked behavior:

- `unknown`, `restricted`, or `incompatible` license confidence means the source
  cannot be used beyond human-readable triage notes.
- Missing evidence with `confirmed_clear` must fail.
- Unclear license must produce blocked or pending status, not pass.

### 4. No Large Binary Commit

Planned test intent:

- Scan the external hair dataset pilot path for binary-like extensions such as
  `.zip`, `.rar`, `.7z`, `.blend`, `.fbx`, `.glb`, `.gltf`, `.obj`, `.png`,
  `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.psd`, `.exr`, `.mp4`, and `.mov`.
- Fail if large files are staged or tracked under the pilot path unless they are
  tiny intentional fixtures already approved by the test contract.
- Set a conservative size threshold for pilot metadata review; suggested
  default is 1 MB per file and no external dataset payloads.
- Prefer testing against `git ls-files` and staged changes, not just filesystem
  presence, so local scratch data can exist outside commits.

Blocked behavior:

- Large dataset binaries in tracked or staged files block the pilot.
- Any committed third-party geometry or texture payload blocks the pilot unless
  a later explicit exception is created and reviewed.

### 5. `skipped_with_reason`

Planned test intent:

- Require skipped validation outputs to be explicit objects, not absent files or
  silent omissions.
- For every skipped screenshot, import check, roundtrip check, or visual claim,
  require `skipped_with_reason` with a non-empty reason.
- Require a clear status such as `skipped`, `blocked`, or `pending`, not
  `passed`.

Blocked behavior:

- A report claiming validation success without screenshots, import evidence, or
  `skipped_with_reason` blocks the pilot.
- Empty or placeholder skip reasons block the pilot.

### 6. v8 Diff Clean

Planned test intent:

- Run the project-standard v8 cleanliness check after any pilot script or report
  generation:

```bash
git diff --name-only -- CharacterPackage/semantic_layer_v8
```

- Assert no paths are returned.
- Also inspect staged paths if the final CI/test harness supports it.

Blocked behavior:

- Any diff under `CharacterPackage/semantic_layer_v8` blocks the pilot.
- Any test fixture that needs v8 mutation is invalid for this pilot.

### 7. `replace_in_beauty_glb=false`

Planned test intent:

- Require every pilot manifest and route report to include
  `replace_in_beauty_glb=false`.
- Fail if the field is missing, true, stringly typed as `"false"`, or buried in
  notes only.
- Require any future candidate beauty export to remain separate from the v8
  beauty GLB and from debug/cage outputs.

Blocked behavior:

- `replace_in_beauty_glb=true` blocks the pilot.
- Missing replacement policy blocks the pilot.
- Any attempt to overwrite v8 beauty exports blocks the pilot.

### 8. Cloth Blocked

Planned test intent:

- Require pilot reports to state that `cloth_seam_surface` remains blocked.
- Require the block reason to reference unresolved hair status, pending manual
  review, target-schema uncertainty, or license uncertainty as applicable.
- Fail if any report recommends starting cloth work while hair is pending,
  failed, license-blocked, or only numerically reviewed.

Blocked behavior:

- Cloth progression is blocked until hair route has clean target schema,
  visually acceptable candidate, manual acceptance, and clear license status.

### 9. External Assets Are Priors Only

Planned test intent:

- Require `external_asset_usage` or equivalent report language to be exactly
  `prior_only`.
- Require downstream reports to describe external data as reference priors,
  silhouette priors, topology inspiration, or annotation aids.
- Fail on terms that imply copying or direct inclusion, such as direct mesh
  transfer, texture transfer, production geometry, or beauty replacement.

Blocked behavior:

- External assets used as direct YUNA geometry, texture, or final topology block
  the pilot.
- Reports that omit the prior-only limitation block the pilot.

## SOURCE_TRIAGE Test Expectations

Planned artifact role:

- `SOURCE_TRIAGE` should be a human-readable audit table or structured note for
  each considered source. It should be testable without downloading the source.

Planned tests:

- File exists at the pilot-agreed path.
- Each source has a stable `source_id` matching any manifest/report references.
- Each source records recommendation enum, license confidence, evidence note,
  source quality note, and blocked/pending reason when applicable.
- No row may claim production approval.
- Unknown-license rows must be `skip_license_unclear`, `review_manually`, or
  `blocked`, not `use_as_prior`.
- The file must not contain local absolute paths as required input locations for
  other workers.

Blocked behavior:

- Missing triage for a referenced source blocks the pilot.
- Triage that upgrades unclear license to usable without evidence blocks the
  pilot.

## README Test Expectations

Planned artifact role:

- The pilot README should explain how to interpret the external dataset pilot
  without acting as a final production manifest.

Planned tests:

- File exists at the pilot-agreed path.
- States external sources are priors only.
- States no large external binaries are committed.
- States `replace_in_beauty_glb=false`.
- States v8 is immutable and must remain diff-clean.
- States cloth remains blocked while hair is unresolved.
- Includes validation commands or points to the test/report locations.
- Does not claim the pilot produces final production topology.
- Does not instruct users to overwrite v8 or import third-party assets directly
  into YUNA beauty exports.

Blocked behavior:

- README language that presents external data as production-ready replacement
  blocks the pilot.
- Missing blocked-license guidance blocks the pilot.

## Report Test Expectations

Planned artifact role:

- The pilot report should be the machine-checkable audit output for the external
  hair dataset decision.

Planned tests:

- Report parses as JSON if it is a JSON report, or contains a clearly testable
  status section if Markdown is intentionally used.
- Includes source coverage count and explicit list of skipped sources.
- Includes `replace_in_beauty_glb=false`.
- Includes `external_asset_usage=prior_only`.
- Includes `v8_diff_status=clean` or a command result that proves cleanliness.
- Includes `cloth_status=blocked`.
- Includes `license_status` and conservative blocked/pending behavior for every
  source with unclear license.
- Includes `visual_validation_status` as `skipped`, `blocked`, or `pending`
  unless screenshots/import evidence exist.
- Includes `skipped_with_reason` for each omitted validation artifact.

Blocked behavior:

- Report cannot mark the pilot passed when license, visual sanity, target schema,
  or manual review is pending.
- Report cannot use numeric or metadata checks alone as final hair acceptance.

## Suggested Acceptance Matrix

| Condition | Expected Status |
| --- | --- |
| Manifest invalid JSON | blocked |
| Unknown source recommendation enum | blocked |
| License unclear and no evidence | blocked or pending |
| License unclear but source used as direct asset | blocked |
| Large external binary staged/tracked | blocked |
| Missing validation with no `skipped_with_reason` | blocked |
| v8 diff not clean | blocked |
| `replace_in_beauty_glb` missing or true | blocked |
| Cloth requested while hair unresolved | blocked |
| External asset described as direct replacement | blocked |
| SOURCE_TRIAGE missing referenced source | blocked |
| README omits prior-only and license-blocked policy | blocked |
| Report claims pass with pending manual review | blocked |

## Non-Goals

- Do not implement the tests in this subtask.
- Do not define a final manifest schema.
- Do not write the final pilot README, manifest, or report.
- Do not download, generate, transform, or commit external assets.
- Do not modify `CharacterPackage/semantic_layer_v8`.
