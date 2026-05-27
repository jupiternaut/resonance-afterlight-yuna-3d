# AGENTS.md

## Project

This repository is a deterministic 2.5D-to-3D DCC handoff research project for
YUNA. It produces auditable candidate assets, validation screenshots, and JSON
reports. It is not a commercial image-to-3D wrapper and candidate assets are not
final production topology.

## Current Baseline

`CharacterPackage/semantic_layer_v8` is the immutable visual-review / DCC
baseline. Do not modify, delete, overwrite, or replace v8 outputs unless the
user explicitly asks for that operation.

## Current Rule

Candidate routes are experimental. They must not replace the v8 beauty GLB until
manual visual review explicitly accepts the replacement. Keep
`replace_in_beauty_glb=false` by default.

## Core Research Formula

Candidate evolution should follow the Bounded Semantic Geometry Filter:

```text
theta_p_next =
ProjectToConstraints_p(
  (1 - alpha) * theta_p
  + alpha * RobustFuse(
      front_obs_p,
      side_obs_p,
      back_obs_p,
      validation_obs_p,
      prior_p
    )
)
```

Where:

- `theta_p` is the current parameter state of part `p`, not raw mesh vertices.
- `RobustFuse` combines front/side/back/validation evidence with part priors.
- `ProjectToConstraints_p` enforces hard project constraints:
  - v8 immutable baseline;
  - front identity priority;
  - side/back are soft constraints;
  - beauty/cage separation;
  - `replace_in_beauty_glb=false` by default;
  - visual sanity gates;
  - target-schema gates;
  - DCC handoff honesty.

Do not optimize raw vertices first. Update part parameters, target schemas,
reports, and candidate routes before changing geometry.

## Layout

- `CharacterPackage/semantic_layer_v8/`: immutable visual-review/DCC baseline.
- `CharacterPackage/semantic_layer_v9_candidate/`: v9 plans, reports, backlog,
  and project-state cards.
- `CharacterPackage/semantic_layer_v9_hair/`: current failed/pending authored
  hair ribbon candidate route.
- `CharacterPackage/tools/semantic_filter/`: semantic state filter v0.
- `CharacterPackage/tools/semantic_actuators/`: v9 actuator implementations.
- `CharacterPackage/tools/tests/`: contract and actuator tests.

## Commands

Run tests:

```bash
python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v
```

Compile tool scripts:

```bash
python3 -m compileall CharacterPackage/tools
```

Confirm v8 is unchanged:

```bash
git diff --name-only -- CharacterPackage/semantic_layer_v8
```

Run the read-only v9 state filter:

```bash
python3 CharacterPackage/tools/semantic_state_filter_v0.py
```

Run hair target review:

```bash
python3 CharacterPackage/tools/review_hair_target_masks_v0.py
```

## Hard Invariants

- Do not use commercial image-to-3D APIs.
- Do not treat side/back references as locked geometry truth; they are soft
  constraints.
- Preserve front-view identity above numeric metrics.
- Every generated route must write a JSON report.
- Every visual claim requires screenshots, roundtrip/import evidence, or an
  explicit `skipped_with_reason` report.
- `replace_in_beauty_glb` must remain `false` unless manual review explicitly
  accepts replacement.
- Do not advance to the next actuator when the current actuator has failed or
  pending visual sanity.
- Do not call candidate/proxy assets final production topology.
- Do not reintroduce debug/cage guide volumes into the beauty GLB.

## Hair Gate

- Numeric metrics alone are insufficient for hair acceptance.
- A hair candidate must look hair-like, not like shredded body/cloth/weapon
  texture.
- Raw v8 union hair masks may be dirty and cannot be treated as final hair
  truth.
- Hair target work should separate:
  - `strict_hair_core`
  - `soft_hair_silhouette`
  - `forbidden_nonhair_zone`
- If target masks are dirty, fix the target schema before regenerating ribbons
  or proceeding to cloth.

## ChatGPT Handoff

At the end of any long-running Goal, Codex must write a Chinese handoff summary
for ChatGPT. Write it to:

```text
CharacterPackage/semantic_layer_v9_candidate/CHATGPT_HANDOFF.md
```

Also include the same block in the final response under:

```text
COPY_TO_CHATGPT_HANDOFF
```

The handoff must use repo-relative paths only. Do not use local absolute paths
such as `/Users/...`.

The handoff must include:

- branch and commit hash;
- current formula stage, including `theta_p_next = ProjectToConstraints(...)`;
- current route status;
- whether v8 remained unchanged;
- whether `replace_in_beauty_glb` is still `false`;
- changed/generated files;
- key metrics;
- validation commands and results;
- v8 diff status;
- visual sanity/manual review verdict;
- current blocker;
- exact recommended next Goal.

Do not claim a route is passed if it is only numeric-pass,
manual-review-pending, or blocked by target-schema/visual sanity.

## Anti-Patterns

- Mutating v8 while testing any v9/v10 candidate.
- Treating GLB export success as visual or production-topology success.
- Marking `visual_sanity_status=passed` when manual review or target-schema
  checks are still failed/pending.
- Letting debug-only guides leak into a beauty/candidate beauty export.
- Collapsing face, hair, cape, body, boots, and weapon into one fused mesh.
- Proceeding to `cloth_seam_surface` while the hair route is failed/pending.

## Definition of Done

A candidate route is done only when:

- tests pass;
- compile passes;
- v8 diff is clean;
- JSON report exists;
- screenshots or skipped report exist;
- visual sanity status is honest;
- backlog is updated with the correct next blocker.
