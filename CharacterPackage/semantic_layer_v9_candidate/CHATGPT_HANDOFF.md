COPY_TO_CHATGPT_HANDOFF
项目：jupiternaut/resonance-afterlight-yuna-3d
分支：feature/authored-hair-ribbons-v0
提交：当前 HEAD 为 f17fc8c；本轮 primary-curve 文件尚未提交，最终提交号请以 GitHub / `git rev-parse --short HEAD` 为准
本轮目标：实现 `external_prior_to_yuna_primary_curve_bundle_v1`。基于 external pink hair benchmark、external prior library、`hair_design_schema_v1` 和 YUNA `target_schema_v1`，生成 YUNA 专用 primary curve bundle；不生成新 hair GLB。
本轮结论：已生成 planning-only primary curve bundle。四个主发组都有显式 scalp anchor、curve_points、width/taper/depth policy、soft silhouette region 和 forbidden-zone policy。该结果是下一轮 ribbon 生成器的输入，不是人工头发验收，也不是 v8 替换。

公式阶段：
- theta_hair_curves = ProjectToConstraints_hair(RobustFuse(external_prior, hair_design_schema_v1, target_schema_v1))
- 本轮只更新 part-parameter / curve-planning state，不优化 raw mesh vertices，不复制外部几何。

核心状态：
- v8 unchanged: true
- replace_in_beauty_glb: false
- generated_yuna_hair_glb: false
- direct_copy_allowed: false
- do_not_copy_shape_directly: true
- primary_curve_bundle_status: primary_curve_bundle_generated_planning_only
- manual_review_required: true
- ready_for_cloth_seam_surface: false

关键指标：
- primary_group_count: 4
- primary_groups: bangs_primary, side_hair_left_primary, side_hair_right_primary, back_hair_mass
- primary_curve_point_counts: 4 / 4 / 4 / 4
- secondary_strand_count: 4
- flyaway_strand_count: 4
- external_benchmark_status: constraint_benchmark_passed_for_external_probe
- positive_probe_status: passed
- negative_control_count: 5

生成/更新文件：
- CharacterPackage/tools/build_primary_curve_bundle_v1.py
- CharacterPackage/tools/tests/test_primary_curve_bundle_v1.py
- CharacterPackage/external_hair_dataset/priors/external_hair_prior_schema_v1.json
- CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1.json
- CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1_report.json
- CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1_front_overlay.png
- CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1_yaw30_plan.png
- CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1_contact_sheet.png
- CharacterPackage/semantic_layer_v9_candidate/PROJECT_STATE.md
- CharacterPackage/semantic_layer_v9_candidate/NEXT_GOAL.md
- CharacterPackage/semantic_layer_v9_candidate/CHATGPT_HANDOFF.md

验证命令：
- unittest: passed, 109 tests
- compileall: passed
- v8 diff: empty

当前阻塞：还没有新 YUNA hair geometry；当前输出只是下一轮 generator 的 primary curve 参数。`cloth_seam_surface` 继续阻塞。

推荐下一步 Codex goal：
/goal Build `build_hair_ribbons_from_primary_curve_bundle_v1`. Use `CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1.json` to generate a new additive hair candidate where every ribbon references a named primary curve, secondary strand, or flyaway. Keep `semantic_layer_v8` unchanged, keep `replace_in_beauty_glb=false`, do not copy external geometry, do not call it final production hair, and keep `cloth_seam_surface` blocked until manual visual review accepts the hair direction.
