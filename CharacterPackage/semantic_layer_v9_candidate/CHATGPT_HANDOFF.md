COPY_TO_CHATGPT_HANDOFF
项目：jupiternaut/resonance-afterlight-yuna-3d
分支：feature/authored-hair-ribbons-v0
提交：本文件所在提交；最终 HEAD 请以 `git rev-parse --short HEAD` / GitHub 显示为准
本轮目标：把已下载的 Sketchfab `Gorgeous japanese Fight` 原始 GLB 和粉色头发提取资产上传到 GitHub，并保留授权/分析/截图证据。
本轮结论：已将原始 GLB、粉色头发提取 GLB/OBJ/BLEND、截图、分析报告和 CC BY 署名文件加入 `CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/`。这些文件是 external prior / local study 资产，不替换 YUNA v8，也不解除 cloth 阻塞。
公式阶段：
- theta_p_next = ProjectToConstraints_p((1-alpha)*theta_p + alpha*RobustFuse(front/side/back/validation/prior))
- 本轮只提交外部 prior 资产和证据，不改 YUNA mesh vertices。
核心状态：
- v8 unchanged: true
- replace_in_beauty_glb: false
- external_asset_usage: prior_only
- source_binary_committed: true, Git LFS
- generated_yuna_hair: false
- ready_for_cloth_seam_surface: false
- visual_sanity_status: not_applicable_external_prior_upload
- manual_review: still_required_for_current_hair_route
关键指标：
- original_source_glb: CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/source/gorgeous_japanese_fight.glb
- original_sha256: f57fadf8dbaad1c0bdda71c6354fca27264991cadfb7b9787be45a0c5463d9f1
- extracted_hair_glb: CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/extracted/pink_hair_segment_probe.glb
- extracted_hair_glb_sha256: 2db2dd8cee583a2cdeee3d4aa1c839d57f07f222028e7e5662e9cdffc86062fc
- original_polygons: 496472
- extracted_hair_probe_polygons: 142313
- claimed_license: CC BY 4.0
- attribution_required: true
生成/更新文件：
- .gitattributes
- CharacterPackage/external_hair_dataset/README.md
- CharacterPackage/external_hair_dataset/SOURCE_TRIAGE.md
- CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/README.md
- CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/ATTRIBUTION.md
- CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/source/gorgeous_japanese_fight.glb
- CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/source/metadata.json
- CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/source/source_page_snapshot.html
- CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/source/thumbnail.jpeg
- CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/extracted/pink_hair_segment_probe.glb
- CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/extracted/pink_hair_segment_probe.obj
- CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/extracted/pink_hair_segment_probe.mtl
- CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/extracted/pink_hair_segment_probe.blend
- CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/analysis/*
- CharacterPackage/semantic_layer_v9_candidate/PROJECT_STATE.md
- CharacterPackage/semantic_layer_v9_candidate/NEXT_GOAL.md
- CharacterPackage/semantic_layer_v9_candidate/CHATGPT_HANDOFF.md
验证命令：
- unittest: passed, 95 tests
- compileall: passed
- v8 diff: empty
当前阻塞：Sketchfab 资产只能作为发型体量/头皮锚点/发束走向 prior；当前 YUNA hair route 仍需人工视觉复核，`cloth_seam_surface` 继续阻塞。
推荐下一步 Codex goal：
/goal Build `sketchfab_hair_prior_schema_v0` from `CharacterPackage/external_hair_dataset/sketchfab_gorgeous_japanese_fight/`. Extract scalp anchor zones, crown/back mass, primary flow arcs, side strand arcs, width/taper hints, visible mass thresholds, and negative notes. Do not copy the high-poly shell into YUNA, do not replace v8 beauty, keep `replace_in_beauty_glb=false`, and keep cloth blocked.
