# Codex Session Code Bundle: YUNA 2.5D-to-3D

Date: 2026-06-01

This bundle collects the code, tests, specs, JSON reports, and handoff notes written across multiple local Codex worktrees for the YUNA 2.5D-to-3D asset pipeline.

It is an archive/package branch, not a replacement for the active candidate branches.

## Sources

| Bundle folder | Local source | Branch | Source state |
|---|---|---|---|
| `sources/main_cloth_worktree` | `/Users/gengrf/resonance-afterlight-yuna-3d` | `feature/cloth-seam-surface-v0` at `5b80963` | dirty local worktree included as copied text files |
| `sources/hair_review_worktree` | `/Users/gengrf/resonance-afterlight-yuna-3d-hair-review` | `feature/authored-hair-ribbons-v0` at `9b0db9d` | clean worktree |
| `sources/full_preview_worktree` | `/Users/gengrf/resonance-afterlight-yuna-3d-preview` | `feature/yuna-full-character-preview-v0` at `d933c6f` | dirty local worktree included as copied text files |
| `sources/open_design_legacy` | `/Users/gengrf/open-design/.od/projects/resonance-afterlight-20260521-692194ef` | non-git runtime project | selected early HTML/Unity/docs/report text files only |

## What Is Included

- Python build scripts and actuator/filter modules.
- Python tests from the active worktrees.
- Candidate specs, reports, handoff notes, backlog, and project-state markdown.
- Validation JSON reports.
- Early OpenDesign HTML and Unity editor helper code.

## What Is Not Included

Generated binary/heavy assets are intentionally omitted from this branch:

- `.blend`
- `.glb`
- `.fbx`
- `.obj`
- `.mtl`
- `.png`
- Unity generated runtime folders

The goal is to preserve the code and machine-readable reasoning trail without bloating the GitHub repository with generated assets.

## Counts

- Total files: 462
- Python: 206
- JSON: 204
- Markdown: 39
- C#: 5
- HTML: 8

## Guardrails

- `semantic_layer_v8` remains the immutable visual-review/DCC baseline.
- Candidate routes must not replace the v8 beauty GLB until manual visual review accepts them.
- Side/back references remain soft constraints, not locked geometry truth.
- This bundle does not claim any route is final production topology.

