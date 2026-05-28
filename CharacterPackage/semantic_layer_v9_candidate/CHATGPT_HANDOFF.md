COPY_TO_CHATGPT_HANDOFF
项目：jupiternaut/resonance-afterlight-yuna-3d
分支：feature/authored-hair-ribbons-v0
提交：本文件所在提交；最终 HEAD 请以 `git rev-parse --short HEAD` / GitHub 显示为准
本轮目标：实现 `external_hair_source_expansion_v1`，把外部 hair prior 来源从两个低/中质量 probe 扩展成可筛选的高质量候选来源集合。
本轮结论：已生成 source expansion v1。没有下载或提交第三方大二进制，没有生成 YUNA hair，没有替换 v8 beauty，cloth 仍阻塞。
公式阶段：
- theta_p_next = ProjectToConstraints_p((1-alpha)*theta_p + alpha*RobustFuse(front/side/back/validation/prior))
- 本轮只更新外部来源参数状态和 prior/source planning，不改 YUNA mesh vertices。
核心状态：
- v8 unchanged: true
- replace_in_beauty_glb: false
- external_asset_usage: prior_only
- large_binaries_committed: false
- generated_yuna_hair: false
- ready_for_cloth_seam_surface: false
- visual_sanity_status: not_applicable_external_source_expansion
- manual_review: still_required_for_current_hair_variants
关键指标：
- candidate_source_count: 12
- high_priority_source_count: 5
- high_priority_next_intake: vroid_hairsample_female_cc0, vroid_hairsample_male_cc0, opengameart_vroid_cc0_samples, blendswap_curly_hair, opengameart_hair_alphas_for_days
- method_reference_count: 2
- existing_probe_sources_retained: opengameart_ponytail_female, opengameart_long_male
生成/更新文件：
- CharacterPackage/tools/external_hair_source_expansion_v1.py
- CharacterPackage/tools/tests/test_external_hair_source_expansion_v1.py
- CharacterPackage/external_hair_dataset/assets_manifest.json
- CharacterPackage/external_hair_dataset/assets_manifest.schema.json
- CharacterPackage/external_hair_dataset/SOURCE_TRIAGE.md
- CharacterPackage/external_hair_dataset/README.md
- CharacterPackage/external_hair_dataset/reports/external_hair_source_expansion_v1_report.json
- CharacterPackage/semantic_layer_v9_candidate/PROJECT_STATE.md
- CharacterPackage/semantic_layer_v9_candidate/NEXT_GOAL.md
- CharacterPackage/semantic_layer_v9_candidate/CHATGPT_HANDOFF.md
验证命令：
- unittest: passed, 95 tests
- compileall: passed
- v8 diff: empty
当前阻塞：当前 hair variants 仍需人工视觉复核；external source expansion 只能给未来 intake/schema/planner 提供候选来源，不改变 hair route acceptance，也不解除 cloth 阻塞。
推荐下一步 Codex goal：
/goal Run `external_hair_intake_probe_v1_selected_sources` for one or two high-priority sources (`vroid_hairsample_female_cc0`, `vroid_hairsample_male_cc0`, or `blendswap_curly_hair`) with license snapshots and quarantine-only downloads. Do not generate YUNA hair, do not copy external shapes, keep v8 unchanged, and do not proceed to cloth.
