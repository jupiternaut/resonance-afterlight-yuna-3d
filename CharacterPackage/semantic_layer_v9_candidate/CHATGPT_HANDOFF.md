# COPY_TO_CHATGPT_HANDOFF

项目：`jupiternaut/resonance-afterlight-yuna-3d`

分支：`feature/authored-hair-ribbons-v0`

当前提交：本文件会随本轮提交一起进入仓库，因此无法自指最终提交哈希；请以 Codex 最终回复中的 pushed HEAD 为准。

本轮目标：实现 `build_art_directed_hair_ribbons_v1`，从
`CharacterPackage/semantic_layer_v9_hair/hair_design_schema_v1.json` 生成一个
art-directed hair ribbon candidate。保持 v8 不变，不推进
`cloth_seam_surface`，不替换 v8 beauty GLB。

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

本轮没有优化 v8，也没有把 v1 写回 beauty GLB；只新增一个候选 route、
对应报告、验证截图和交接文档。

## 当前路线状态

- route: `build_art_directed_hair_ribbons_v1`
- actuator: `art_directed_hair_ribbons_v1`
- status: `art_directed_candidate_manual_review_required`
- `replace_in_beauty_glb=false`
- `ready_for_cloth_seam_surface=false`
- v8 unchanged: true
- manual visual review: required
- verdict: 候选已生成并通过 target-schema/non-degenerate 数值门禁，但不是 accepted/final hair。

## 生成/更新文件

代码：

- `CharacterPackage/tools/semantic_actuators/art_directed_hair_ribbons_v1.py`
- `CharacterPackage/tools/build_art_directed_hair_ribbons_v1.py`
- `CharacterPackage/tools/tests/test_art_directed_hair_ribbons_v1.py`
- `CharacterPackage/tools/semantic_actuators/authored_hair_ribbons.py`
- `CharacterPackage/tools/build_hair_target_schema_v1.py`
- `CharacterPackage/tools/semantic_actuators/validation_contract.py`
- `CharacterPackage/tools/run_blender_semantic_validation.py`

候选资产与报告：

- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/specs/yuna_semantic_layer_v9_hair_art_directed_v1.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/exports/yuna_semantic_layer_v9_hair_art_directed_v1.obj`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/exports/yuna_semantic_layer_v9_hair_art_directed_v1.mtl`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/exports/yuna_semantic_layer_v9_hair_art_directed_v1.glb`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/exports/yuna_semantic_layer_v9_hair_art_directed_v1.blend`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/target_schema_v1_eval/hair_target_schema_v1_report.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/manual_review.md`

项目状态文档：

- `CharacterPackage/semantic_layer_v9_candidate/goal_progress_hair_ribbons.md`
- `CharacterPackage/semantic_layer_v9_candidate/backlog_v10.md`
- `CharacterPackage/semantic_layer_v9_candidate/PROJECT_STATE.md`
- `CharacterPackage/semantic_layer_v9_candidate/NEXT_GOAL.md`
- `CharacterPackage/semantic_layer_v9_candidate/actuator_run_report.md`
- `CharacterPackage/semantic_layer_v9_candidate/CHATGPT_HANDOFF.md`

## 关键指标

- `non_degenerate_hair_coverage_passed=true`
- `candidate_visible_pixel_count=13479`
- `candidate_visible_area_ratio=0.007020`，阈值 `>=0.005`
- `soft_silhouette_coverage_ratio=0.341499`，阈值 `>=0.25`
- `candidate_core_coverage_ratio=0.341135`，阈值 `>=0.10`
- `candidate_soft_inside_ratio=0.822168`，阈值 `>=0.70`
- `forbidden_candidate_leak_ratio=0.020550`，阈值 `<0.10`
- `bangs_presence_ratio=0.214286`，阈值 `>=0.15`
- `side_hair_left_presence_ratio=0.493036`，阈值 `>=0.30`
- `side_hair_right_presence_ratio=0.911678`，阈值 `>=0.30`
- `back_hair_mass_presence_ratio=0.794342`，阈值 `>=0.35`
- `component_count=6`，最大值 `32`
- `scalp_anchor_continuity=0.214286`，阈值 `>=0.15`
- `ribbon_count=25`
- `group_count=6`
- `depth_group_count=6`
- `art_directed_primitive_intent_count=25`
- `flow_continuity_passed=true`
- primary groups: `bangs_primary`, `side_hair_left_primary`,
  `side_hair_right_primary`, `back_hair_mass`
- added groups: `secondary_strands`, `flyaway_strands`

## 验证命令与结果

- `python3 CharacterPackage/tools/build_art_directed_hair_ribbons_v1.py`
  - result: generated candidate, GLB/BLEND export ok via Blender; target schema eval status `art_directed_candidate_manual_review_required`.
- `python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v`
  - result: passed.
- `python3 -m compileall CharacterPackage/tools`
  - result: passed.
- `git diff --name-only -- CharacterPackage/semantic_layer_v8`
  - result: empty.

## 视觉 / 人工复核判断

- v1 明显优于 v0 的 underfilled/barcode-strip 失败状态。
- yaw15/yaw30 有更干净的层状 hair-card 体量。
- 之前造成脸/身体污染的 blocky side-profile volume 已从 beauty candidate 移除。
- candidate-only front 在全身 framing 下仍偏稀疏。
- 因此只能标记为 `art_directed_candidate_manual_review_required`，不能标记为 accepted/passed replacement。

## 当前 blocker

人工视觉复核尚未接受 `art_directed_hair_ribbons_v1`。在人工接受之前：

- 不推进 `cloth_seam_surface`
- 不替换 v8 beauty GLB
- 不称为最终生产头发

## 推荐下一条 Goal

```text
manual_review_art_directed_hair_ribbons_v1_quality
```

如果人工复核拒绝，下一步应 refine v1：重点处理 front scalp integration、
候选正面稀疏度和 authored curve placement，同时保持 schema/non-degenerate
指标不退回 v0 的 sparse/barcode 状态。
