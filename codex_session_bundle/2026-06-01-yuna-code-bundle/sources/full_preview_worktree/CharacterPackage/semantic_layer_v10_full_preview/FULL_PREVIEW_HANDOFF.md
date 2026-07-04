# COPY_TO_CHATGPT_HANDOFF

项目：`jupiternaut/resonance-afterlight-yuna-3d`

分支：`feature/yuna-full-character-preview-v0`

源分支：`feature/authored-hair-ribbons-v0`

基线提交：`d933c6f`

本轮目标：实现 `yuna_full_character_preview_v0`，创建只用于整体轮廓审查的 v10 full-character preview 场景。该场景把 v8 baseline、未接受的 curve-bundle hair candidate、weapon、boots/legs body visual、debug cage 组装到同一个 Blender 审查文件中；cloth candidate 在当前源分支不可用，只记录 v8 cape/skirt/jacket panels 作为上下文。

公式阶段：
`PreviewScene = AssembleUnderConstraints(v8_baseline, candidate_hair, candidate_cloth, weapon, boots, debug_cage)`

本轮结论：
- route status: `preview_generated_manual_review_required`
- `preview_only=true`
- `replace_in_beauty_glb=false`
- `hair_accepted=false`
- `cloth_accepted=false`
- `ready_for_cloth_seam_surface=false`
- `manual_visual_review_required=true`
- `CharacterPackage/semantic_layer_v8` 未修改：`True`
- `CharacterPackage/semantic_layer_v9_hair` 未修改：`True`
- 这不是最终生产拓扑，也不是 beauty GLB 替换。

生成/更新文件：
- `CharacterPackage/semantic_layer_v10_full_preview/full_preview_asset_manifest.json`
- `CharacterPackage/semantic_layer_v10_full_preview/exports/yuna_full_character_preview_v0.blend`
- `CharacterPackage/semantic_layer_v10_full_preview/exports/yuna_full_character_preview_v0.glb`
- `CharacterPackage/semantic_layer_v10_full_preview/validation_report.json`
- `CharacterPackage/semantic_layer_v10_full_preview/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v10_full_preview/validation_ci/front_baseline.png`
- `CharacterPackage/semantic_layer_v10_full_preview/validation_ci/front_candidate_overlay.png`
- `CharacterPackage/semantic_layer_v10_full_preview/validation_ci/yaw15.png`
- `CharacterPackage/semantic_layer_v10_full_preview/validation_ci/yaw30.png`
- `CharacterPackage/semantic_layer_v10_full_preview/validation_ci/side.png`
- `CharacterPackage/semantic_layer_v10_full_preview/validation_ci/back.png`
- `CharacterPackage/semantic_layer_v10_full_preview/validation_ci/wire.png`
- `CharacterPackage/semantic_layer_v10_full_preview/validation_ci/exploded.png`
- `CharacterPackage/semantic_layer_v10_full_preview/validation_ci/contact_sheet.png`
- `CharacterPackage/semantic_layer_v10_full_preview/FULL_PREVIEW_HANDOFF.md`

缺失/不可用：
- cloth candidate: `semantic_layer_v9_cloth` 在当前源分支不存在；cloth 仍保持 blocked/unaccepted。
- missing screenshots: `[]`

审查清单：
- front identity readable?
- full silhouette coherent?
- candidate hair helps or hurts?
- cloth helps or hurts?
- weapon scale acceptable?
- boots/legs acceptable?
- top priority to fix?

验证命令：
- `python3 CharacterPackage/tools/build_yuna_full_character_preview_v0.py`
- `python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v`
- `python3 -m compileall CharacterPackage/tools`
- `git diff --name-only -- CharacterPackage/semantic_layer_v8`
- `git diff --name-only -- CharacterPackage/semantic_layer_v9_hair`

验证结果：
- build: `preview_generated_manual_review_required`
- unittest: `122 tests OK`
- compileall: `passed`
- v8 diff: `empty`
- v9_hair diff: `empty`

视觉/人工复核结论：
- 当前只生成 full-character preview 审查包；必须人工查看 screenshots/contact sheet 后再判断 hair/cloth/weapon/boots/body 哪个优先修。
- hair candidate 仍是 unaccepted。
- cloth candidate 不存在且未接受。

当前阻塞：
- `manual_visual_review_yuna_full_character_preview_v0`

推荐下一条 Codex Goal：

```text
/goal Manual-review yuna_full_character_preview_v0.

Read:
- CharacterPackage/semantic_layer_v10_full_preview/validation_report.json
- CharacterPackage/semantic_layer_v10_full_preview/full_preview_asset_manifest.json
- CharacterPackage/semantic_layer_v10_full_preview/validation_ci/contact_sheet.png
- CharacterPackage/semantic_layer_v10_full_preview/validation_ci/front_baseline.png
- CharacterPackage/semantic_layer_v10_full_preview/validation_ci/front_candidate_overlay.png
- CharacterPackage/semantic_layer_v10_full_preview/validation_ci/yaw30.png
- CharacterPackage/semantic_layer_v10_full_preview/validation_ci/side.png
- CharacterPackage/semantic_layer_v10_full_preview/validation_ci/back.png

Decide only review priority:
- front identity readable?
- full silhouette coherent?
- candidate hair helps or hurts?
- cloth helps or hurts?
- weapon scale acceptable?
- boots/legs acceptable?
- top priority to fix?

Keep semantic_layer_v8 unchanged.
Keep semantic_layer_v9_hair unchanged.
Keep replace_in_beauty_glb=false.
Keep preview_only=true.
Do not proceed to cloth_seam_surface.
Do not call this final production topology.
```
