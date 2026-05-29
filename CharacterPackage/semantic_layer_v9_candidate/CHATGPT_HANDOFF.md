# COPY_TO_CHATGPT_HANDOFF

项目：`jupiternaut/resonance-afterlight-yuna-3d`

分支：`feature/authored-hair-ribbons-v0`

提交：本文件生成于提交前；本轮最终提交哈希以 Codex 最终回复和 GitHub 远端为准。

本轮目标：执行 `build_curve_bundle_hair_candidate_v1`，把 `primary_curve_bundle_v1.json` 从 planning-only 曲线包推进为一个真实的 hair candidate 资产，同时保持 v8 不变、不替换 beauty GLB、不推进 cloth。

公式阶段：
`theta_hair_next = ProjectToConstraints_hair(RobustFuse(primary_curve_bundle_v1, target_schema_v1, validation_obs, hair_priors))`

本轮结论：
- 已生成 `curve_bundle_candidate_v1` 的 OBJ/MTL/GLB/BLEND、spec、覆盖 mask、Blender 验证图和 target schema 复核报告。
- 候选资产状态：`curve_bundle_candidate_failed_visual_review`。
- `target_schema_status=failed_target_schema_alignment`。
- `replace_in_beauty_glb=false`。
- `ready_for_cloth_seam_surface=false`。
- `CharacterPackage/semantic_layer_v8` 未修改。
- 这不是最终生产头发，也不应自动替换 v8 beauty hair。

planning preview 图片确认存在：
- `CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1_front_overlay.png`
- `CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1_yaw30_plan.png`
- `CharacterPackage/semantic_layer_v9_hair/primary_curve_bundle_v1_contact_sheet.png`

生成/更新文件：
- `CharacterPackage/tools/build_curve_bundle_hair_candidate_v1.py`
- `CharacterPackage/tools/semantic_actuators/curve_bundle_hair_candidate_v1.py`
- `CharacterPackage/tools/semantic_actuators/validation_contract.py`
- `CharacterPackage/tools/tests/test_curve_bundle_hair_candidate_v1.py`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/specs/yuna_curve_bundle_hair_v1.json`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/exports/yuna_curve_bundle_hair_v1.obj`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/exports/yuna_curve_bundle_hair_v1.mtl`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/exports/yuna_curve_bundle_hair_v1.glb`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/exports/yuna_curve_bundle_hair_v1.blend`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/candidate_front.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/overlay_front.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/yaw30.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/side.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/wire.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/exploded.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/target_schema_v1_eval/hair_target_schema_v1_report.json`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/target_schema_v1_eval/candidate_vs_schema_overlay.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/failure_report.md`
- `CharacterPackage/semantic_layer_v9_candidate/PROJECT_STATE.md`
- `CharacterPackage/semantic_layer_v9_candidate/NEXT_GOAL.md`
- `CharacterPackage/semantic_layer_v9_candidate/backlog_v10.md`
- `CharacterPackage/semantic_layer_v9_candidate/CHATGPT_HANDOFF.md`

关键指标：
- `mesh_summary.ribbon_count=46`
- `mesh_summary.depth_group_count=7`
- `mesh_summary.vertices=4600`
- `mesh_summary.faces=4508`
- `candidate_front_visible_hair_mass=true`
- `primary_group_presence_passed=true`
- `yaw30_hair_readability=true`
- `side_hair_readability=true`
- `target_schema_v1_eval.forbidden_candidate_leak_ratio=0.441191`
- `target_schema_v1_eval.candidate_soft_inside_ratio=0.321086`
- `target_schema_v1_eval.candidate_core_coverage_ratio=0.354627`
- `target_schema_v1_eval.candidate_visible_area_ratio=0.017181`
- `target_schema_v1_eval.component_count=1`
- `manual_visual_review_status=blocked_by_target_schema_alignment`

验证命令：
- `python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v`
- `python3 -m compileall CharacterPackage/tools`
- `git diff --name-only -- CharacterPackage/semantic_layer_v8`

验证结果：
- unittest：通过，`Ran 114 tests ... OK`
- compileall：通过
- v8 diff：为空

视觉/人工复核结论：
- 当前候选有真实资产输出和截图证据，但 target schema alignment 未通过。
- forbidden leak 明显超阈值，soft inside 明显不足。
- 候选仍应视为失败样本和下一轮修复输入，不应推进下一 actuator。

当前阻塞：
- `curve_bundle_candidate_v1` 需要修 target alignment：降低 forbidden leak，同时提高 soft silhouette inside coverage。
- `cloth_seam_surface` 继续阻塞。

推荐下一条 Codex Goal：

```text
/goal Continue fix_curve_bundle_hair_candidate_v1_target_alignment.

Read:
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_report.json
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/target_schema_v1_eval/hair_target_schema_v1_report.json
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/candidate_front.png
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/overlay_front.png
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/yaw30.png

Goal:
Reduce forbidden_candidate_leak_ratio below threshold and improve candidate_soft_inside_ratio without shrinking away visible mass.

Do not modify semantic_layer_v8.
Keep replace_in_beauty_glb=false.
Do not proceed to cloth_seam_surface.
Do not call the result final production hair.
```
