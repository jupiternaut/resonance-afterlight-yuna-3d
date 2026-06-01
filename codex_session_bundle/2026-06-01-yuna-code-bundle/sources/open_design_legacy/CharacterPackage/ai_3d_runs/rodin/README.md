# Rodin Gen-2 Run Package For YUNA

Created: 2026-05-22T19:49:06+08:00

Scope: Rodin-only execution package for the YUNA image-to-3D A/B test. This directory is intentionally isolated from Meshy and shared scoring assets.

## Current Status

Status: `blocked_on_credentials`

I checked for Rodin/Hyper3D credentials in the active environment and common local config locations. No usable `RODIN_API_KEY` or `HYPER3D_API_KEY` was found. No key value was printed or written.

Because credentials are missing, no Rodin cloud task was submitted in this run.

## Official API Surface Confirmed

Rodin Gen-2 generation is an asynchronous multipart upload API:

- Generation endpoint: `POST https://api.hyper3d.com/api/v2/rodin`
- Auth: `Authorization: Bearer <token>`
- Request format: `multipart/form-data`
- Image-to-3D input: one or more images, up to 5 images
- Required Gen-2 field: `tier=Gen-2`
- Task tracking: response contains `uuid` and `jobs.subscription_key`
- Status endpoint: `POST https://api.hyper3d.com/api/v2/status`
- Download endpoint: `POST https://api.hyper3d.com/api/v2/download`

Sources:

- https://developer.hyper3d.ai/api-specification/rodin-generation-gen2
- https://developer.hyper3d.ai/api-specification/check-status
- https://developer.hyper3d.ai/api-specification/download-results

## Recommended Primary Character Run

Use `rodin_gen2_payload.json`.

Input order matters. The first image is used for material generation, so the locked front RGBA reference is first.

Recommended upload order:

1. `front_rgba/yuna_front_rgba.png` - locked visual identity and material reference
2. `ai_turnarounds/cutouts/yuna_left_side.png` - inferred side structure
3. `ai_turnarounds/cutouts/yuna_back.png` - inferred back structure
4. `dcc_reference/chatgpt_generated/yuna_dcc_material_texture_reference.png` - material and trim reference
5. `dcc_reference/chatgpt_generated/yuna_dcc_turnaround_3view.png` - consolidated 3-view reinforcement

Do not upload the expression sheet into the primary body run. It is useful for later blendshape targets, but it is not a clean single-object multi-view input and can confuse body reconstruction.

Do not upload the weapon ortho sheet into the primary body run unless Rodin under-generates the sword. The front image already contains the weapon; a separate weapon run is safer if the blade needs clean geometry.

## Recommended Parameters

Primary character base:

- `tier`: `Gen-2`
- `geometry_file_format`: `fbx`
- `material`: `All`
- `mesh_mode`: `Quad`
- `quality_override`: `150000`
- `TAPose`: `true`
- `use_original_alpha`: `true`
- `preview_render`: `true`
- `hd_texture`: `true`
- `addons`: `[]`

Rationale: FBX is better for Blender/Unity handoff; Quad plus high face count is the best starting point for DCC cleanup; `All` keeps both PBR and shaded material outputs for comparison.

## Optional Separate Weapon Run

Use `rodin_weapon_payload.json` only if the primary character result fuses or loses the sword. This should generate the energy blade as a separate prop model.

## How To Submit Later

From this directory:

```bash
export HYPER3D_API_KEY="your_token_here"
python3 submit_rodin_gen2.py --payload rodin_gen2_payload.json
```

The script also accepts `RODIN_API_KEY`. It never writes the token to disk.

After submission:

```bash
python3 rodin_status_download.py --submission results/rodin_submission_response.json
```

When status is `Done`, the same script writes a download URL manifest under `results/`.

## Success Boundary

A successful Rodin task is a cloud-generated DCC base mesh, not a final production character. It must still be checked against the YUNA 2D reference and then cleaned in Blender/ZBrush for face likeness, hair volume, mantle separation, UV/PBR, skinning, blendshapes, LOD, and Unity Avatar.

