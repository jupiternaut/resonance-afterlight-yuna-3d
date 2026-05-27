# COPY_TO_CHATGPT_HANDOFF

项目：`jupiternaut/resonance-afterlight-yuna-3d`

分支：`feature/authored-hair-ribbons-v0`

实现提交：`f618db1` (`Refine art-directed hair visible mass gates`)

本轮目标：执行 `refine_art_directed_hair_ribbons_v1_visible_mass`。不推进
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
- actuator: `art_directed_hair_ribbons_v1`
- status: `failed_target_schema_alignment`
- `replace_in_beauty_glb=false`
- `ready_for_cloth_seam_surface=false`
- v8 unchanged: true
- manual visual review: blocked by target-schema alignment
- verdict: 可见体量门禁改善并通过，但 forbidden-zone leak 过高，不能验收为 hair candidate。

## 生成/更新文件

代码：

- `CharacterPackage/tools/semantic_actuators/art_directed_hair_ribbons_v1.py`
- `CharacterPackage/tools/semantic_actuators/authored_hair_ribbons.py`
- `CharacterPackage/tools/build_hair_target_schema_v1.py`
- `CharacterPackage/tools/tests/test_art_directed_hair_ribbons_v1.py`
- `CharacterPackage/tools/tests/test_hair_target_schema_v1.py`

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
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_candidate_front.png`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/validation_ci/yuna_semantic_layer_v9_hair_art_directed_v1_validation_yaw30.png`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1/target_schema_v1_eval/schema_debug_contact_sheet.png`

项目状态文档：

- `CharacterPackage/semantic_layer_v9_candidate/PROJECT_STATE.md`
- `CharacterPackage/semantic_layer_v9_candidate/NEXT_GOAL.md`
- `CharacterPackage/semantic_layer_v9_candidate/backlog_v10.md`
- `CharacterPackage/semantic_layer_v9_candidate/actuator_run_report.md`
- `CharacterPackage/semantic_layer_v9_candidate/goal_progress_hair_ribbons.md`
- `CharacterPackage/semantic_layer_v9_candidate/CHATGPT_HANDOFF.md`

## 关键指标

- `candidate_front_visible_hair_mass=true`
- `candidate_visible_pixel_count=19959`
- `candidate_visible_area_ratio=0.010395`，阈值 `>=0.010`
- `soft_silhouette_coverage_ratio=0.464084`，阈值 `>=0.25`
- `candidate_core_coverage_ratio=0.521867`，阈值 `>=0.10`
- `candidate_soft_inside_ratio=0.754547`，阈值 `>=0.70`
- `forbidden_candidate_leak_ratio=0.194649`，阈值 `<0.10`
- `primary_group_presence_passed=true`
- `yaw30_hair_readability=true`
- `side_hair_readability=true`
- `manual_visual_review_status=blocked_by_target_schema_alignment`
- `bangs_presence_ratio=0.371327`
- `side_hair_left_presence_ratio=0.443825`
- `side_hair_right_presence_ratio=0.792136`
- `back_hair_mass_presence_ratio=0.591295`
- `component_count=15`
- `scalp_anchor_continuity=0.371327`
- `ribbon_count=27`
- `group_count=6`
- `depth_group_count=6`
- `art_directed_primitive_intent_count=27`
- `flow_continuity_passed=true`

## 验证命令与结果

- `python3 CharacterPackage/tools/build_art_directed_hair_ribbons_v1.py`
  - result: generated OBJ/MTL/GLB/BLEND/screenshots/reports; target-schema status `failed_target_schema_alignment`.
- `python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v`
  - result: 61 tests passed.
- `python3 -m compileall CharacterPackage/tools`
  - result: passed.
- `git diff --name-only -- CharacterPackage/semantic_layer_v8`
  - result: empty.
- `git diff --check`
  - result: passed.

## 视觉 / 人工复核判断

- candidate-only front 的可见发量比上一版更高，`candidate_front_visible_hair_mass=true`。
- yaw30 仍能显示候选发片，但仍像分离 plate，不是连续、可验收的头发。
- 因为 `forbidden_candidate_leak_ratio=0.194649` 超过阈值，当前状态必须保持失败/阻塞。
- 不应推进下一 actuator。

## 当前 blocker

需要在不回退可见体量的前提下降低 forbidden-zone leak：

```text
fix_hair_ribbons_to_schema_v1_visible_mass_leak_balance
```

在这之前：

- 不推进 `cloth_seam_surface`
- 不替换 v8 beauty GLB
- 不称为最终生产头发

## 推荐下一条 Goal

```text
/goal 不要推进 cloth_seam_surface。继续修 art_directed_hair_ribbons_v1：
执行 fix_hair_ribbons_to_schema_v1_visible_mass_leak_balance。
目标是在保持 candidate_front_visible_hair_mass=true、primary_group_presence_passed=true、
yaw30_hair_readability=true、side_hair_readability=true 的同时，把
forbidden_candidate_leak_ratio 降到阈值以下。保持 v8 不变，
replace_in_beauty_glb=false，运行 unittest、compileall、v8 diff check，
并更新 CHATGPT_HANDOFF。
```
