# Meshy YUNA Multi-view Execution Log

Run: `meshy_yuna_multiview_20260522`

Time: 2026-05-22T11:50:42Z

Scope: this Meshy subagent writes only under `CharacterPackage/ai_3d_runs/meshy/`.

## Credential Check

- Environment key present: no
- Common local config key reference present: no
- Key value printed or stored: no
- Submission status: blocked on credentials

Accepted environment variable names:

- `MESHY_API_KEY`
- `MESHY_KEY`
- `MESHY_TOKEN`
- `MESHY_BEARER_TOKEN`
- `MESHY_AI_API_KEY`
- `MESHYAI_API_KEY`

## Official API Confirmation

Confirmed official Meshy endpoint:

- `POST https://api.meshy.ai/openapi/v1/multi-image-to-3d`
- `GET https://api.meshy.ai/openapi/v1/multi-image-to-3d/:id`

The official docs state that `image_urls` may be public URLs or base64 data URIs, and that multi-image tasks accept 1 to 4 images of the same object. The current payload uses three full-body YUNA views.

## Primary Upload Set

1. `front_rgba`: locked front identity reference.
2. `left_side`: side volume reference.
3. `back`: rear volume reference.

Excluded from this primary character task:

- Weapon orthographic sheet: should be a separate prop task.
- Expression sheet: should be used for manual blendshape sculpting.
- Combined 3-view sheet: retained for human review, not uploaded as an extra object view.

## Recommended Parameters

- `ai_model`: `meshy-6`
- `should_texture`: `true`
- `enable_pbr`: `true`
- `hd_texture`: `true`
- `should_remesh`: `true`
- `topology`: `quad`
- `target_polycount`: `80000`
- `save_pre_remeshed_model`: `true`
- `pose_mode`: `a-pose`
- `image_enhancement`: `false`
- `remove_lighting`: `true`
- `target_formats`: `glb`, `fbx`, `obj`

## Next Action

Set a Meshy API key in one of the accepted environment variables, then run:

```bash
cd /Users/gengrf/open-design/.od/projects/resonance-afterlight-20260521-692194ef/CharacterPackage/ai_3d_runs/meshy
MESHY_API_KEY=... python3 scripts/submit_meshy_multiview.py
python3 scripts/poll_meshy_task.py
```

Do not treat any local procedural blockout as a successful Meshy result. Success requires Meshy cloud output URLs and downloaded GLB/FBX/OBJ files.
