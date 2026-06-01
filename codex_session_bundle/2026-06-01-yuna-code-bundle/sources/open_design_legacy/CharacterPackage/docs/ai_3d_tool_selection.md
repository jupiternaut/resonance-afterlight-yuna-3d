# AI Image-To-3D Tool Selection For YUNA

Updated: 2026-05-22

Scope: choose the best image-to-3D route for turning the locked YUNA 2D reference pack into a DCC/Unity-ready base mesh. This is a tool-selection decision, not a claim that AI output can replace final human character art.

## Decision

Use **Rodin Gen-2** as the first high-quality generation attempt for YUNA.

Use **Meshy 6 Multi-view** as the comparison run. For this character, it should be treated as a serious A/B candidate, not only a fallback, because Meshy has more visibly inspectable public anime/stylized character examples.

Use **Tripo 3.1 / Tripo P1** for quick comparison, prop generation, or a backup API route.

Do not use **TripoSR** as the main quality route. Use it only as a local/free baseline.

## Why Rodin First

YUNA is not a simple prop. The difficult parts are face identity, long layered hair, translucent mantle, gold trims, white stockings, boots, weapon silhouette, and full-body readability.

Rodin Gen-2 is the strongest fit for a DCC base mesh because it explicitly supports:

- text/image-to-3D;
- up to 5 input images;
- quad-dominant and raw mesh modes;
- PBR and shaded materials;
- configurable polygon count;
- T/A pose control;
- output to GLB, FBX, OBJ, USDZ and STL.

That makes it more suitable as a base for Blender/ZBrush cleanup than a fast single-image reconstructor.

## Online Reference Check

The practical comparison is:

- **Rodin**: strongest production-facing parameter set. Hyper3D's official page positions Rodin around text/image input, clean topology, UVs, PBR materials, and GLB/FBX/OBJ/USD export. The Gen-2 API also exposes up to 5 input images, `PBR` material output, `Quad` mesh mode, configurable face counts, `TAPose`, and GLB/FBX/OBJ/STL/USDZ output. This is the best fit for a DCC base mesh.
- **Meshy**: strongest visible anime/stylized public proof. Meshy has public character model pages such as `Anime Character Standing`, and its Meshy 6 Multi-view docs explicitly recommend front/side/back-style references for character work. It exports GLB/FBX/OBJ/STL and related formats. This is the best direct visual benchmark.
- **Tripo**: strong general production API. Its docs cover image/text/multiview model generation, conversion, quad remeshing, texture size/format controls, FBX presets, rigging, retargeting and animation-oriented export options. It is attractive for batch pipelines, but I would not choose it first for YUNA's high-fidelity anime face/hair target.
- **TripoSR**: best local/open-source baseline. Stability AI describes it as under-0.5-second single-image reconstruction and MIT-licensed, but that speed/open-source advantage is not the same as hero-character quality.

Sources checked:

- Hyper3D/Rodin official page: https://hyper3d.io/
- Hyper3D Rodin Gen-2 API docs: https://developer.hyper3d.ai/api-specification/rodin-generation-gen2
- Meshy public anime character example: https://www.meshy.ai/3d-models/Anime-Character-Standing-v2-019b808b-42ee-76d3-bbc2-8a94211df5da
- Meshy Multi-view docs: https://help.meshy.ai/en/articles/12634481-how-to-use-multi-view
- Meshy Multi-Image to 3D API docs: https://docs.meshy.ai/en/api/multi-image-to-3d
- Tripo conversion/export docs: https://docs.tripo3d.ai/export/conversion.html
- Tripo API pricing/task list: https://docs.tripo3d.ai/get-started/pricing.html
- Stability AI TripoSR announcement: https://stability.ai/news/triposr-3d-generation

## Tool Ranking For This Project

| Rank | Tool | Best Use | Why | Risk |
|---|---|---|---|---|
| 1 | Rodin Gen-2 | Highest-quality DCC base mesh attempt | Better fit for quad/PBR/configurable output and multi-image character generation | Less anime-specific public finished examples; still needs manual DCC cleanup |
| 2 | Meshy 6 Multi-view | Fast anime/stylized model candidate and auto-rig preview | Public anime model library, multi-view workflow, GLB/FBX export, auto-rig/animation tooling | Character output can still become figurine-like or simplified |
| 3 | Tripo 3.1 / Multi-view | Fast multi-view model and plugin/API workflow | Good multi-image support, fast generation, post-processing and plugins | More suitable for broad assets; character likeness still uncertain |
| 4 | TripoSR | Local/open-source baseline | MIT-licensed, under-0.5s single-image reconstruction | Not enough quality for YUNA final or even strong DCC base |

## Actual Recommendation

If only one paid tool can be used, run **Rodin Gen-2 first**.

If two runs are possible, run **Rodin Gen-2 + Meshy 6 Multi-view** with identical YUNA inputs and compare the exported FBX/GLB in Blender. This is the most useful bakeoff:

- Rodin answers: "Can we get a cleaner DCC mesh with PBR, quads, pose control and higher production leverage?"
- Meshy answers: "Can we get closer anime/stylized character appeal from an inspectable online tool?"

Do not spend the first serious budget on TripoSR. It is useful for privacy/offline tests and technical baseline comparison, but it is not the route for the YUNA hero character.

## Recommended YUNA Test Plan

1. Split the ChatGPT-generated 3-view sheet into clean front, side and back images if the tool accepts separate views better than a combined sheet.
2. Run Rodin Gen-2 first:
   - input images: front RGBA, side, back, optional face crop, optional weapon ortho;
   - first image should be the locked front material reference;
   - request T-pose or A-pose;
   - use Quad mesh mode and PBR material;
   - export FBX for Blender/Unity and GLB for web preview.
3. Run Meshy 6 Multi-view with the same view set:
   - use front/side/back/three-quarter or front/side/back/weapon depending on upload constraints;
   - export GLB and FBX;
   - do not judge only by web preview lighting.
4. Import into Blender and check:
   - front silhouette against locked 2D art;
   - face likeness;
   - hair volume;
   - mantle separation;
   - weapon thickness;
   - topology around face/shoulders/hips/knees;
   - UV and texture channels.
5. Keep Tripo as a quick third run only if Rodin or Meshy fails badly.
6. Pick the better base mesh for manual DCC cleanup.

## Acceptance Gate

Accept an AI-generated base only if:

- front silhouette is close enough to the 2D reference for manual correction;
- face does not look like a different person;
- back and side volume are usable;
- hair and mantle are separated enough to edit;
- weapon is a separate or easily separable mesh;
- export includes usable FBX or GLB;
- Blender import has no unrecoverable mesh corruption.

Reject it if:

- face becomes generic;
- hair melts into cloak;
- transparent mantle becomes solid blob;
- white stockings/boots merge incorrectly;
- weapon is fused into the body;
- topology is too damaged for cleanup.

## Final Note

Even the best AI output should be treated as a starting mesh, not final character art. The final YUNA still needs manual sculpting, retopology, UV cleanup, material repainting, skin weights, blendshapes and Unity Avatar validation.
