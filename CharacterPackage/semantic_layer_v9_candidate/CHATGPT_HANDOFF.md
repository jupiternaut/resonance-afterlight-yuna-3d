# COPY_TO_CHATGPT_HANDOFF

项目：`jupiternaut/resonance-afterlight-yuna-3d`

分支：`feature/authored-hair-ribbons-v0`

提交：`以 feature/authored-hair-ribbons-v0 最新 HEAD 为准；final response 提供精确 hash`

本轮目标：继续 `fix_hair_ribbons_to_schema_v1_visible_mass_leak_balance`。不推进
`cloth_seam_surface`，不修改 `semantic_layer_v8`，不替换 v8 beauty GLB。

## 当前公式阶段

```text
theta_p_next =
ProjectToConstraints_p(
  (1 - alpha) * theta_p
  + alpha * RobustFuse(
      front_obs_p,
      side_obs_p,
      back_obs_p,
      validation_obs_p,
      prior_p
    )
)
```

Hair route 绑定：

```text
candidate_hair_next =
ProjectToConstraints_hair(
  RobustFuse(
    strict_hair_core,
    soft_hair_silhouette,
    forbidden_nonhair_zone,
    front_identity,
    manual_visual_review
  )
)
```

## 当前路线状态

- route: `build_art_directed_hair_ribbons_v1`
- status: `art_directed_candidate_manual_review_required`
- candidate target schema: `schema_gate_passed_manual_review_required`
- `replace_in_beauty_glb=false`
- `ready_for_cloth_seam_surface=false`
- v8 unchanged: true
- manual visual review: required
- verdict: target-schema 数字门禁通过，但还不能称为最终 hair candidate；下一步必须人工复核 candidate-only front/yaw 视觉质量。

## 本轮改动

- 修正 `build_hair_target_schema_v1` 的 render-space 评估：schema mask 现在使用与 art-directed hair mesh 生成一致的 render correction。
- 这是坐标一致性修复，不是放宽阈值，也不是 shrink-to-pass。
- 更新 target-schema eval 图、JSON report、validation report、PROJECT_STATE、NEXT_GOAL、backlog 和 goal progress。
- 更新 stale test：v0 默认候选仍然是 underfilled 负例，但失败原因现在是可见面积/soft 覆盖/碎片数量，而不是每个主发组都低于阈值。

## 生成/更新文件

代码与测试：

- `CharacterPackage/tools/build_hair_target_schema_v1.py`
- `CharacterPackage/tools/tests/test_hair_target_schema_v1.py`

候选评估与验证报告：

- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/target_schema_v1_eval/hair_target_schema_v1_report.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/target_schema_v1_eval/candidate_vs_schema_overlay.png`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/target_schema_v1_eval/schema_debug_contact_sheet.png`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/manual_review.md`

项目状态文档：

- `CharacterPackage/semantic_layer_v9_candidate/PROJECT_STATE.md`
- `CharacterPackage/semantic_layer_v9_candidate/NEXT_GOAL.md`
- `CharacterPackage/semantic_layer_v9_candidate/backlog_v10.md`
- `CharacterPackage/semantic_layer_v9_candidate/actuator_run_report.md`
- `CharacterPackage/semantic_layer_v9_candidate/goal_progress_hair_ribbons.md`
- `CharacterPackage/semantic_layer_v9_candidate/CHATGPT_HANDOFF.md`

## 关键指标

- `candidate_front_visible_hair_mass=true`
- `primary_group_presence_passed=true`
- `yaw30_hair_readability=true`
- `side_hair_readability=true`
- `candidate_visible_pixel_count=19959`
- `candidate_visible_area_ratio=0.010395`
- `soft_silhouette_coverage_ratio=0.511386`
- `candidate_core_coverage_ratio=0.608249`
- `candidate_soft_inside_ratio=0.831454`
- `forbidden_candidate_leak_ratio=0.071096`，阈值 `<0.10`
- `bangs_presence_ratio=0.891591`
- `side_hair_left_presence_ratio=0.502321`
- `side_hair_right_presence_ratio=0.667259`
- `back_hair_mass_presence_ratio=0.474429`
- `component_count=15`
- `scalp_anchor_continuity=0.474429`
- `schema_render_correction_px={"x":13.0,"y":8.0}`
- `manual_visual_review_status=pending_user_review_visible_mass_refined`

## 验证命令与结果

- `python3 CharacterPackage/tools/build_hair_target_schema_v1.py --output-dir CharacterPackage/semantic_layer_v9_hair/art_directed_v1/target_schema_v1_eval --candidate-front CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_candidate_front.png --candidate-route-label art_directed_hair_ribbons_v1 --validation-report CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_report.json --validation-ci-report CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/validation_ci_report.json`
  - result: target-schema status `schema_gate_passed_manual_review_required`; route status `art_directed_candidate_manual_review_required`.
- `python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v`
  - result: 61 tests passed.
- `python3 -m compileall CharacterPackage/tools`
  - result: passed.
- `git diff --name-only -- CharacterPackage/semantic_layer_v8`
  - result: empty.

## 视觉 / 人工复核判断

- 本轮解决的是 schema/candidate render-space 不一致导致的 forbidden leak 假高问题。
- leak 已低于阈值，且 visible mass、primary group、yaw30、side readability 均保持通过。
- 但当前仍是 candidate route，不是最终生产头发；不能替换 v8 beauty。
- 不应推进 `cloth_seam_surface`，直到人工复核确认 candidate-only front/yaw 的头发质量可接受。

## 当前 blocker

```text
manual_review_art_directed_hair_ribbons_v1_quality
```

需要人工看：

- candidate-only front 是否像完整发型，而不是碎片；
- yaw15/yaw30 是否仍像头发；
- side view 是否保持合理体量；
- 是否可以继续进入局部质量修正，或需要回到 generator 调整。

## 推荐下一条 Goal

```text
/goal 不要推进 cloth_seam_surface。执行 manual_review_art_directed_hair_ribbons_v1_quality：
检查 art_directed_v1 的 candidate-only front、yaw15、yaw30、side、schema_debug_contact_sheet。
如果人工视觉复核通过，只允许进入下一步 hair quality polish；如果失败，明确失败原因并继续修 hair。
保持 semantic_layer_v8 不变，replace_in_beauty_glb=false，不称为 final production hair。
```
