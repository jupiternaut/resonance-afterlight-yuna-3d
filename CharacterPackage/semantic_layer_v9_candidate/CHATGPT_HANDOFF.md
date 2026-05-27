# COPY_TO_CHATGPT_HANDOFF

项目：`jupiternaut/resonance-afterlight-yuna-3d`

分支：`feature/authored-hair-ribbons-v0`

提交：`31b76e7`

本轮目标：实现 `build_hair_target_schema_v1`，为未来 art-directed hair ribbons 建立三层目标 schema。

本轮结论：完成。已生成 `strict_hair_core`、`soft_hair_silhouette`、`forbidden_nonhair_zone` 三层 mask 和 schema 报告。当前 hair v0 不通过 schema gate，不应推进下一 actuator。

核心状态：

- v8 unchanged: true
- `replace_in_beauty_glb`: false
- formula stage: `theta_p_next = ProjectToConstraints_p((1-alpha)*theta_p + alpha*RobustFuse(...))`
- current route status: `failed_target_schema_alignment`
- visual_sanity_status: `failed_target_schema_alignment`
- manual_review: blocked / not accepted
- ready_for_cloth_seam_surface: false

关键指标：

- `strict_core_area=20309`
- `soft_silhouette_area=29823`
- `forbidden_zone_area=666429`
- `core_body_overlap_ratio=0.0`
- `soft_body_overlap_ratio=0.0`
- `forbidden_candidate_leak_ratio=0.975006`
- `candidate_core_coverage_ratio=0.041425`
- `candidate_soft_inside_ratio=0.021113`
- `schema_ready_for_ribbon_rebuild=true`

生成/更新文件：

- `CharacterPackage/tools/build_hair_target_schema_v1.py`
- `CharacterPackage/tools/tests/test_hair_target_schema_v1.py`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/strict_hair_core_mask.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/soft_hair_silhouette_mask.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/forbidden_nonhair_zone_mask.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/hair_target_schema_v1_report.json`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/candidate_vs_schema_overlay.png`
- `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/schema_debug_contact_sheet.png`
- `CharacterPackage/semantic_layer_v9_hair/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v9_candidate/PROJECT_STATE.md`
- `CharacterPackage/semantic_layer_v9_candidate/NEXT_GOAL.md`
- `CharacterPackage/semantic_layer_v9_candidate/backlog_v10.md`
- `CharacterPackage/semantic_layer_v9_candidate/actuator_run_report.md`

验证命令：

- `python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v`: 54 tests passed
- `python3 -m compileall CharacterPackage/tools`: passed
- `git diff --name-only -- CharacterPackage/semantic_layer_v8`: empty

视觉 / 人工复核判断：

- 当前 schema 质量可用于下一轮 ribbon rebuild。
- 当前 hair v0 candidate 大量漏入 forbidden zone，不能接受为 hair-only。
- 不能进入 `cloth_seam_surface`。

当前 blocker：

- 现有 hair ribbons 没有按 schema v1 约束生成。

推荐下一条 Codex Goal：

```text
/goal Implement `fix_hair_ribbons_to_schema_v1`.

Use `CharacterPackage/semantic_layer_v9_hair/target_schema_v1/` as the hard target schema.
Do not modify `CharacterPackage/semantic_layer_v8`.
Do not replace v8 beauty GLB.
Do not proceed to `cloth_seam_surface`.
Candidate must reduce forbidden-zone leakage, increase soft-silhouette inside ratio, preserve four hair groups and depth groups, regenerate reports/screenshots, and write `COPY_TO_CHATGPT_HANDOFF`.
```
