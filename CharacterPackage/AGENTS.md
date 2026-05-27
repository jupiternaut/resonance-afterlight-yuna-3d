# CharacterPackage/AGENTS.md

## Asset Rules

- `semantic_layer_v8` is the immutable baseline.
- New routes must be additive. Do not overwrite previous exports.
- Keep beauty assets separate from debug/cage/proxy assets.
- Candidate routes must write:
  - spec JSON;
  - `validation_report.json`;
  - `validation_ci_report.json` or an explicit skipped report;
  - an actuator run report or backlog update.

## Validation Priority

1. v8 unchanged.
2. Front identity preserved.
3. No debug/cage leakage into beauty exports.
4. Material and alpha sanity.
5. Mask/schema alignment.
6. DCC handoff usefulness.

## Current Block

`cloth_seam_surface` is blocked until the hair route has a clean target schema,
a visually acceptable candidate, and manual review acceptance. Do not advance
cloth work while hair remains failed or pending.
