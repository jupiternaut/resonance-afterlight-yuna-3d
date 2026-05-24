# Resonance Afterlight CharacterPackage

This package starts the Unity-oriented 2D-to-3D production pipeline for sample character `YUNA`.

## Current Deliverables

- `refs/front_rgba/yuna_front_rgba.png`: validated transparent front cutout.
- `refs/front_raw/yuna_front_raw_green.png`: original green-screen source.
- `refs/ai_turnarounds/raw/`: generated green-screen side, back, face-expression and weapon reference sheets.
- `refs/ai_turnarounds/cutouts/`: transparent cutouts for the generated modeling references.
- `refs/dcc_reference/chatgpt_generated/`: higher-quality ChatGPT DCC reference set: 3-view, expression sheet, weapon sheet and material/texture board.
- `qa/turntable/yuna_dcc_reference_contact_sheet.png`: contact sheet for the ChatGPT DCC reference set.
- `meta/character_meta.json`: design lock, Unity target, known limits.
- `meta/missing_views.json`: original missing-view record retained for provenance.
- `refs/notes/ai_turnaround_prompts.md`: prompts for inferred side/back/face/weapon references.
- `qa/turntable/yuna_reference_views_contact.png`: contact sheet for front, side, back, face and weapon refs.
- `web/yuna_proxy_billboard.glb`: runtime GLB proxy asset.
- `unity/prefabs/yuna_proxy_billboard.glb`: same proxy copied into Unity-facing delivery path.
- `web/yuna_proxy_viewer.html`: local Three.js loader test for the proxy GLB.
- `qa/turntable/yuna_proxy_viewer.png`: screenshot proof that the GLB loads.
- `dcc/blender/yuna_dcc_blockout.blend`: Blender DCC scene with reference planes, proxy body, weapon, mantle and reference armature.
- `web/yuna_dcc_blockout.glb`: formal GLB export from the Blender DCC blockout.
- `rig/yuna_dcc_blockout.fbx`: formal FBX export from the Blender DCC blockout.
- `unity/prefabs/yuna_dcc_blockout.glb`: Unity-facing copy of the blockout GLB.
- `unity/prefabs/yuna_dcc_blockout.fbx`: Unity-facing copy of the blockout FBX.
- `web/yuna_dcc_blockout_viewer.html`: local Three.js loader test for the DCC blockout GLB.
- `qa/turntable/yuna_dcc_blockout_viewer.png`: screenshot proof that the DCC blockout GLB loads.
- `qa/dcc_scene_report.json`: Blender scene inventory for the blockout export.
- `unity/editor_tools/CharacterImportPostprocessor.cs`: import guardrails for Unity model/texture assets.
- `unity/editor_tools/LoadRuntimeGlb.cs`: glTFast runtime loading example.
- `tools/create_proxy_glb.py`: repeatable proxy GLB generator.
- `tools/build_yuna_blender_blockout.py`: repeatable Blender DCC blockout builder and FBX/GLB exporter.
- `dcc/blender/yuna_production_slice.blend`: automated production-slice Blender scene.
- `rig/yuna_production_lod0.fbx`, `rig/yuna_production_lod1.fbx`, `rig/yuna_production_lod2.fbx`: production-slice FBX exports.
- `web/yuna_production_lod0.glb`, `web/yuna_production_lod1.glb`, `web/yuna_production_lod2.glb`: production-slice GLB exports with skin and morph data.
- `web/yuna_production_lod0_preview_nomorph.glb`: no-morph preview GLB for the current Three.js r128 viewer.
- `web/yuna_production_viewer.html`: runtime preview for the production-slice GLB.
- `qa/turntable/yuna_production_viewer.png`: screenshot proof that the preview GLB loads in WebGL.
- `qa/yuna_production_slice_report.json`: production-slice QA inventory.
- `textures/export_unity_urp/`: URP texture set.
- `textures/export_gltf_web/`: glTF/Web texture set.
- `unity/editor_tools/YunaProductionValidator.cs`: Unity Editor validator for model, Avatar and texture import checks.
- `unity/ValidationProject/`: staged Unity validation project assets.
- `qa/unity/yuna_unity_static_preflight.json`: static Unity preflight; runtime Unity validation is blocked until Editor licensing is active.
- `docs/ai_3d_tool_selection.md`: image-to-3D tool decision for YUNA; Rodin first, Meshy as mandatory A/B candidate, Tripo as backup, TripoSR as local baseline.
- `ai_3d_runs/common/`: shared YUNA input package for Rodin vs Meshy A/B generation, including the contact sheet and manifest.
- `ai_3d_runs/rodin/`: Rodin Gen-2 request package, payload, submit script, status/download script and blocked-on-credentials log.
- `ai_3d_runs/meshy/`: Meshy 6 Multi-view request package, payload template, submit/poll scripts and blocked-on-credentials log.
- `ai_3d_runs/ab_status.json`: unified Rodin vs Meshy A/B run status report.
- `tools/build_yuna_production_slice.py`: repeatable production-slice builder.
- `tools/setup_unity_validation_project.py`: stages exported assets into the Unity validation project.
- `tools/prepare_ai_3d_ab_inputs.py`: repeatable shared input-pack generator for cloud image-to-3D A/B runs.
- `tools/score_ai_3d_ab_exports.py`: repeatable A/B export readiness/status report.
- `tools/qa_overlay.py`: front-view overlay/diff starter script.
- `tools/build_yuna_image_constructed_assets.py`: deterministic PNG alpha-to-relief-mesh builder that does not use Rodin/Meshy.
- `image_constructed/obj/yuna_image_constructed_front_relief.obj`: OBJ relief mesh carved from the locked YUNA front PNG alpha.
- `image_constructed/exports/yuna_image_constructed_front_relief.glb` and `.fbx`: GLB/FBX exports for the front relief asset.
- `image_constructed/obj/yuna_image_constructed_turnaround.obj`: OBJ three-view image-constructed reference asset.
- `image_constructed/exports/yuna_image_constructed_turnaround.glb` and `.fbx`: GLB/FBX exports for the front/side/back turnaround asset.
- `qa/turntable/yuna_image_constructed_front_relief_preview.png`: Blender screenshot of the image-constructed front relief asset.
- `qa/turntable/yuna_image_constructed_turnaround_preview.png`: Blender screenshot of the image-constructed three-view asset.
- `qa/yuna_image_constructed_report.json`: mesh counts, export paths and route boundary report.
- `tools/build_yuna_semantic_layer_v1.py`: deterministic semantic-layer v1 asset compiler using draft front-view masks, per-part mesh rules, Blender export and validation screenshots.
- `semantic_layer_v1/specs/yuna_semantic_layer_v1.json`: source-of-truth schema for the v1 semantic parts, mesh rules, depths, thicknesses, hooks and acceptance checks.
- `semantic_layer_v1/masks/front/`: auto-draft semantic masks for face, hair groups, torso, jacket, cape, legs, boots and weapon.
- `semantic_layer_v1/obj/parts/`: per-part OBJ exports for the v1 semantic mesh nodes.
- `semantic_layer_v1/exports/yuna_semantic_layer_v1.blend`: Blender handoff scene with render-shell parts plus proxy guides and animation hook empties.
- `semantic_layer_v1/exports/yuna_semantic_layer_v1.glb`, `.fbx` and `.obj`: semantic-layer v1 GLB/FBX/OBJ exports.
- `semantic_layer_v1/validation/`: mask contact sheet plus front, yaw15, yaw30, side and exploded validation renders.
- `semantic_layer_v1/validation_report.json`: v1 export inventory, GLB roundtrip result and next cleanup list.
- `tools/build_yuna_semantic_layer_v2.py`: semantic-layer v2 compiler with art-directed coarse masks, explicit warning/failure reporting and v2-named OBJ/MTL/spec outputs.
- `semantic_layer_v2/specs/yuna_semantic_layer_v2.json`: source-of-truth schema for the v2 semantic route.
- `semantic_layer_v2/exports/yuna_semantic_layer_v2.blend`, `.glb`, `.fbx` and `.obj`: semantic-layer v2 BLEND/GLB/FBX/OBJ exports.
- `semantic_layer_v2/validation/`: v2 mask contact sheet plus front, yaw15, yaw30, side and exploded validation renders.
- `semantic_layer_v2/validation_report.json`: v2 export inventory, GLB roundtrip result and quality warnings.
- `tools/build_yuna_semantic_layer_v3.py`: semantic-layer v3 compiler with expanded depth bands, side/back reference metadata and stricter pass/warning/fail gates.
- `semantic_layer_v3/specs/yuna_semantic_layer_v3.json`: source-of-truth schema for the v3 side/back-constrained route.
- `semantic_layer_v3/constraints/`: alpha constraint previews extracted from the AI-inferred side/back references.
- `semantic_layer_v3/exports/yuna_semantic_layer_v3.blend`, `.glb`, `.fbx` and `.obj`: semantic-layer v3 BLEND/GLB/FBX/OBJ exports.
- `semantic_layer_v3/validation/`: v3 mask contact sheet, side/back reference contact sheet, front, yaw15, yaw30, side and exploded validation renders.
- `semantic_layer_v3/validation_report.json`: v3 export inventory, side/back reference metrics, GLB roundtrip result and quality warnings.
- `tools/build_yuna_semantic_layer_v4.py`: semantic-layer v4 compiler that moves from thick cutout extrusion to typed part grammar: hair cards, cloth sheets, curved panels, face plate, weapon panel and DCC cage guides.
- `tools/inspect_yuna_v4_candidate.py`: read-only candidate inspector for checking BLEND/GLB/FBX/OBJ, validation PNGs and report JSON presence.
- `semantic_layer_v4/specs/yuna_semantic_layer_v4.json`: source-of-truth schema for the v4 part-grammar route.
- `semantic_layer_v4/exports/yuna_semantic_layer_v4.blend`, `.glb`, `.fbx` and `.obj`: semantic-layer v4 BLEND/GLB/FBX/OBJ exports.
- `semantic_layer_v4/exports/yuna_semantic_layer_v4_cage_debug.glb`: cage-debug GLB containing the render shell plus head, torso and leg DCC cage guides.
- `semantic_layer_v4/validation/`: v4 front, yaw15, yaw30, side cage, cage wire, exploded and reference validation renders.
- `semantic_layer_v4/validation_report.json`: v4 export inventory, GLB/cage-GLB/FBX/OBJ roundtrip results and quality warnings.
- `tools/build_yuna_semantic_layer_v5.py`: semantic-layer v5 compiler that adds leg continuity underlay volumes to test the broken-leg failure case.
- `semantic_layer_v5/exports/`: v5 BLEND/GLB/cage-debug GLB/FBX/OBJ exports and validation renders.
- `tools/build_yuna_semantic_layer_v6.py`: semantic-layer v6 compiler that adds continuous leg/boot topology proxies and knee/ankle hooks.
- `semantic_layer_v6/exports/`: v6 BLEND/GLB/cage-debug GLB/FBX/OBJ exports and validation renders.
- `tools/build_yuna_semantic_layer_v7.py`: semantic-layer v7 compiler that replaces the combined legs panel with split left/right visual leg panels.
- `semantic_layer_v7/exports/`: v7 BLEND/GLB/cage-debug GLB/FBX/OBJ exports and validation renders.
- `tools/build_yuna_semantic_layer_v8.py`: semantic-layer v8 compiler that keeps beauty leg panels in the main GLB and moves leg/boot volume guides to the cage-debug GLB.
- `semantic_layer_v8/exports/yuna_semantic_layer_v8.blend`, `.glb`, `.fbx` and `.obj`: current best visual-review export set for the semantic-layer route.
- `semantic_layer_v8/exports/yuna_semantic_layer_v8_cage_debug.glb`: debug GLB with DCC leg/boot guides, knee/ankle hooks and cage helpers.
- `semantic_layer_v8/validation/`: v8 front, yaw15, yaw30, side cage, cage wire, exploded and reference validation renders.
- `semantic_layer_v8/validation_report.json`: v8 export inventory, GLB/cage-GLB/FBX/OBJ roundtrip results and quality warnings.

## Important Limit

`yuna_dcc_blockout.blend`, `yuna_dcc_blockout.glb`, and `yuna_dcc_blockout.fbx` are DCC blockout/proxy assets. They are not final production game characters:

- proxy geometry only, not final anime character topology
- reference armature only, no weighted skinned mesh
- no facial blendshapes yet
- no production UV unwrap or PBR material pass
- no hair/mantle secondary-motion rig yet
- no LOD set yet
- no Unity prefab import validation yet

The current files bridge the 2D HTML/OpenDesign work into the formal DCC/Unity pipeline and are suitable for modeling alignment, pipeline validation, and early FBX/GLB handoff tests.

`yuna_production_slice.blend` is a stronger vertical slice than the blockout: it includes LOD0/1/2 mesh sets, UVs, PBR materials, armature modifiers, 23 humanoid-style bones and 12 facial shape keys. It is still automated geometry and must not be treated as final commercial character art.

`image_constructed/` is a separate non-cloud route. It builds 2.5D textured relief/reference meshes directly from PNG alpha masks and exports OBJ/FBX/GLB. It preserves the original 2D art much better than the procedural geometry dummy, but it is not a true volumetric, riggable character mesh.

`semantic_layer_v1/` is the first structured asset-compiler step after the raw alpha relief. It keeps major parts as independent mesh nodes (`face`, `bangs`, `back_hair`, side hair groups, torso, jacket, cape, skirt, legs, boots and weapon), adds draft depth/thickness/curvature rules, and exports a Blender handoff plus GLB/FBX/OBJ. Its masks are auto-draft and visibly imperfect; it is useful for testing the pipeline shape, not for final likeness or production topology.

`semantic_layer_v2/` improves the v1 front-view assembly with art-directed coarse masks and stricter quality reporting. It preserves 13 independent mesh nodes and 5 animation hook empties through GLB roundtrip, but the report intentionally marks it `generated_with_warnings`: side depth is still shallow, yaw views still show dark sidewall artifacts, and the mesh is too dense for runtime without decimation.

`semantic_layer_v3/` widens the part depth bands using AI-inferred side/back references as soft constraints and lowers mesh density compared with v2. It still preserves 13 independent mesh nodes and 5 hook empties through GLB roundtrip. The report remains `generated_with_warnings`: it passes the stricter hard gates for depth, GLB roundtrip and DCC face budget, but remains above runtime face budget and still needs hand-painted masks plus true part cages/cards/sheets.

`semantic_layer_v4/` is the first part-grammar pass after v3. It removes the main per-pixel sidewall extrusion path and replaces it with alpha render panels, split hair cards, cloth-like sheets, an independent weapon panel and DCC cage guides. It preserves 13 render-shell meshes and 5 hook empties in the main GLB, adds 4 cage meshes in the cage-debug GLB, and passes GLB, cage-GLB, FBX and OBJ roundtrip import checks. The report remains `generated_with_warnings`: it is a cleaner handoff baseline, not clean production topology; side view should be judged through the cage-debug view; the weapon still needs real orthographic hard-surface reconstruction.

`semantic_layer_v5/` and `semantic_layer_v6/` are leg-continuity experiments. v5 proves that adding rear continuity volumes can reduce broken-leg perception, but the visible underlay is too crude for beauty review. v6 adds more explicit leg/boot proxies and knee/ankle hooks, but the proxy volumes are visibly fake in front/yaw renders. Keep these as rejected intermediate references, not as current visual targets.

`semantic_layer_v7/` splits the leg visuals into left/right panels and separates debug loops from the main GLB, but the rear leg proxies are still visible enough to read as gray blocks. It is useful as a comparison point for the leg repair sequence.

`semantic_layer_v8/` is the current best semantic-layer visual-review pass. The main GLB keeps the beauty render shell, split leg visual panels, boots, hair cards, cape sheets, weapon panel and animation hook empties; the leg/boot volume guides are moved to `yuna_semantic_layer_v8_cage_debug.glb`. It is still a 2.5D DCC handoff asset: it does not have real skinned leg topology, final boot hard-surface geometry, production UVs, or weight-painted knee/ankle deformation.

## Required Next Production Steps

1. Replace automated forms with manually sculpted face, hair, outfit layers, mantle, boots and weapon.
2. Perform final retopology and hand-authored UV atlas work.
3. Bake normal/AO/curvature/position/thickness maps from the final high/low meshes.
4. Refine URP and GLB/Web material outputs against final UVs.
5. Clean up skin weights and validate Humanoid or Generic rig choice.
6. Sculpt production facial blendshapes from the expression sheet.
7. Add hair and mantle secondary-motion bones or cloth constraints.
8. Art-direct LOD0/LOD1/LOD2 instead of relying on automated simplification.
9. Activate Unity Editor license and run `YunaProductionValidator.Run` for Avatar/material/LOD QA.

## Local Environment Found

- Unity found at `/Applications/Unity/Hub/Editor/6000.4.5f1`.
- Blender found at `/opt/homebrew/bin/blender`.
- The DCC blockout `.blend`, `.glb`, and `.fbx` exports were generated locally.
- The production-slice `.blend`, LOD FBX/GLB exports, texture sets and WebGL preview were generated locally.
- Unity batchmode is currently blocked by missing Editor license; see `qa/unity/create_project.log`.
