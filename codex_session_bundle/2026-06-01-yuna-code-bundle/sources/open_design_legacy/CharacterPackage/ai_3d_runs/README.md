# YUNA Rodin vs Meshy A/B Run

Goal: run the same locked YUNA image set through Rodin Gen-2 and Meshy 6 Multi-view, then compare the exported 3D base meshes before any manual Blender cleanup.

## Shared Inputs

All tool runs must use files from:

`common/inputs/`

The upload order is documented in:

`common/inputs/UPLOAD_ORDER.md`

Do not use the previous automated geometry blockout screenshots as generation inputs.

## Tool Runs

- `rodin/`: Rodin Gen-2 request payload, logs, and exports.
- `meshy/`: Meshy 6 Multi-view request payload, logs, and exports.

Each tool folder should contain:

- `README.md`: tool-specific run instructions.
- `request_payload.json`: API/UI payload or parameter record.
- `run_log.md`: what was attempted and whether credentials were available.
- `submitted.json`: only when a cloud job was actually submitted.
- `exports/`: downloaded GLB/FBX/OBJ outputs.

## A/B Rule

The better result is not the prettier web preview. It is the base mesh that gives the best Blender/DCC handoff:

1. front silhouette against `yuna_locked_front_rgba.png`;
2. anime face identity;
3. hair separation;
4. translucent mantle separation;
5. weapon as a separate or separable mesh;
6. clean enough topology to repair;
7. usable UV/PBR texture output;
8. FBX/GLB imports without corruption.

Run status is summarized by:

`../tools/score_ai_3d_ab_exports.py`
