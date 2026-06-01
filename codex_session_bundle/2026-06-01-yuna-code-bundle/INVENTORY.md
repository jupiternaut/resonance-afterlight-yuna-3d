# Inventory

## Main Cloth Worktree

Source: `/Users/gengrf/resonance-afterlight-yuna-3d`

Branch: `feature/cloth-seam-surface-v0`

Commit: `5b80963`

Included areas:

- `CharacterPackage/tools/`
- `CharacterPackage/semantic_layer_v9_candidate/`
- `CharacterPackage/semantic_layer_v9_weapon/`
- `CharacterPackage/semantic_layer_v9_boot/`
- `CharacterPackage/semantic_layer_v9_leg/`
- `CharacterPackage/semantic_layer_v9_hair/`
- `CharacterPackage/semantic_layer_v9_cloth/`

Notable code families:

- `semantic_state_filter_v0`
- `semantic_filter`
- `semantic_actuators`
- weapon hard-surface actuator
- boot hard-surface actuator
- leg retopo proxy actuator
- authored/art-directed hair ribbon actuator work
- cloth seam surface actuator work
- Blender/semantic validation scripts

## Hair Review Worktree

Source: `/Users/gengrf/resonance-afterlight-yuna-3d-hair-review`

Branch: `feature/authored-hair-ribbons-v0`

Commit: `9b0db9d`

Included areas:

- `CharacterPackage/tools/`
- `CharacterPackage/semantic_layer_v9_candidate/`
- `CharacterPackage/semantic_layer_v9_hair/`

Notable code families:

- external hair intake/probe/prior scripts
- primary curve bundle scripts
- curve bundle candidate/repair scripts
- hair target schema/review scripts
- hair validation tests
- hair review reports and handoff markdown

## Full Preview Worktree

Source: `/Users/gengrf/resonance-afterlight-yuna-3d-preview`

Branch: `feature/yuna-full-character-preview-v0`

Commit: `d933c6f`

Included areas:

- `CharacterPackage/tools/`
- `CharacterPackage/semantic_layer_v10_full_preview/`

Notable code families:

- full character preview builder
- preview validation reports
- full preview handoff
- preview asset manifest

## OpenDesign Legacy

Source: `/Users/gengrf/open-design/.od/projects/resonance-afterlight-20260521-692194ef`

Included selected text/code files only:

- early HTML preview pages
- CharacterPackage markdown docs
- validation/report JSON
- Unity editor C# helpers

This legacy source is indexed, not fully migrated. Large assets, Unity generated folders, and generated model files are excluded.

## Exclusion Policy

This bundle is a code and report archive. It intentionally excludes generated 3D exports and image outputs. If binary deliverables are needed, create a separate GitHub Release asset rather than committing them to this branch.

