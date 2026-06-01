# YUNA Meshy 6 Multi-view Run

This folder contains the Meshy side of the Rodin vs Meshy A/B task.

Current status: blocked on credentials. No Meshy task has been submitted.

## Files

- `input_manifest.json`: YUNA source image list, dimensions, hashes, and upload order.
- `payloads/meshy_multi_image_to_3d_payload.template.json`: Meshy request body with data URI placeholders.
- `scripts/submit_meshy_multiview.py`: builds data URIs from local PNGs and submits the Meshy task.
- `scripts/poll_meshy_task.py`: polls the task and downloads GLB/FBX/OBJ outputs when ready.
- `responses/`: reserved for API responses.
- `outputs/`: reserved for downloaded Meshy model files.
- `execution_log.md`: run log.
- `status.json`: machine-readable run status.

## Why Only Three Images

Meshy Multi-Image to 3D expects 1 to 4 images of the same object, ideally different views. The primary YUNA run uses front, side and back full-body references.

The weapon sheet is excluded because it is a separate object and may be fused into the character body. Run it later as a dedicated prop task.

The expression sheet is excluded because it is for manual face blendshape sculpting, not base-body reconstruction.

## Submit

Provide a Meshy API key through an environment variable, then run:

```bash
cd /Users/gengrf/open-design/.od/projects/resonance-afterlight-20260521-692194ef/CharacterPackage/ai_3d_runs/meshy
MESHY_API_KEY=... python3 scripts/submit_meshy_multiview.py
```

The script does not print or store the key. It writes a redacted request preview to `payloads/last_request_redacted.json` and the task response to `responses/create_task_response.json`.

## Poll And Download

```bash
python3 scripts/poll_meshy_task.py
```

Or provide a task id explicitly:

```bash
python3 scripts/poll_meshy_task.py <task_id>
```

Successful outputs are downloaded to `outputs/`.

## Acceptance Boundary

This run is successful only when Meshy returns cloud-generated 3D assets. A local procedural dummy, proxy, or blockout is not a successful result.
