# COPY_TO_CHATGPT_HANDOFF

项目：`jupiternaut/resonance-afterlight-yuna-3d`

分支：`feature/authored-hair-ribbons-v0`

提交：`以 feature/authored-hair-ribbons-v0 最新 HEAD 为准；final response 提供精确 hash`

本轮目标：构建 `art_directed_hair_ribbons_v1` overnight manual review pack。生成
`balanced`、`fuller`、`silhouette` 三套 hair candidate variants；不推进
`cloth_seam_surface`；不替换 v8 beauty。

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
    variant_design,
    strict_hair_core,
    soft_hair_silhouette,
    forbidden_nonhair_zone,
    front_identity,
    manual_visual_review
  )
)
```

## 当前路线状态

- route: `build_art_directed_hair_ribbons_v1_variants`
- status: `manual_review_pack_generated`
- generated variants: 3
- recommended first human review target: `fuller`
- `replace_in_beauty_glb=false` for all variants
- `ready_for_cloth_seam_surface=false`
- v8 unchanged: true
- manual visual review: required
- verdict: 三套候选已生成，但没有任何一套被标记 accepted 或 production-ready。`fuller` 只是优先人工复核对象。

## 生成/更新文件

代码与测试：

- `CharacterPackage/tools/semantic_actuators/art_directed_hair_ribbons_v1.py`
- `CharacterPackage/tools/build_art_directed_hair_ribbons_v1_variants.py`
- `CharacterPackage/tools/tests/test_art_directed_hair_ribbons_v1.py`

review pack：

- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1_variants/hair_variants_comparison_report.json`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1_variants/hair_variants_contact_sheet.png`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1_variants/manual_review_hair_v1.md`

per-variant directories：

- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1_variants/balanced/`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1_variants/fuller/`
- `CharacterPackage/semantic_layer_v9_hair/art_directed_v1_variants/silhouette/`

每个 variant 含：

- `specs/*.json`
- `exports/*.obj`
- `exports/*.mtl`
- `exports/*.glb`
- `exports/*.blend`
- `validation_report.json`
- `validation_ci/validation_ci_report.json`
- `validation_ci/*candidate_front.png`
- `validation_ci/*overlay_front.png`
- `validation_ci/*yaw15.png`
- `validation_ci/*yaw30.png`
- `validation_ci/*side.png`
- `validation_ci/*wire.png`
- `validation_ci/*exploded.png`
- `target_schema_v1_eval/hair_target_schema_v1_report.json`
- `target_schema_v1_eval/candidate_vs_schema_overlay.png`
- `target_schema_v1_eval/schema_debug_contact_sheet.png`

项目状态文档：

- `CharacterPackage/semantic_layer_v9_candidate/PROJECT_STATE.md`
- `CharacterPackage/semantic_layer_v9_candidate/NEXT_GOAL.md`
- `CharacterPackage/semantic_layer_v9_candidate/backlog_v10.md`
- `CharacterPackage/semantic_layer_v9_candidate/actuator_run_report.md`
- `CharacterPackage/semantic_layer_v9_candidate/goal_progress_hair_ribbons.md`
- `CharacterPackage/semantic_layer_v9_candidate/CHATGPT_HANDOFF.md`

## 关键指标

| Variant | Leak | Soft inside | Core | Visible area | Soft coverage | Front mass | Yaw30 | Side | Manual gate |
|---|---:|---:|---:|---:|---:|---|---|---|---|
| `balanced` | `0.071096` | `0.831454` | `0.608249` | `0.010395` | `0.511386` | true | true | true | pending review |
| `fuller` | `0.072702` | `0.833756` | `0.634326` | `0.010896` | `0.537518` | true | true | true | pending review |
| `silhouette` | `0.045859` | `0.854204` | `0.579953` | `0.009824` | `0.496502` | false | true | true | failed visible-mass gate |

Additional:

- `component_count`: balanced `15`, fuller `16`, silhouette `15`
- `replace_in_beauty_glb=false` for all variants
- `ready_for_cloth_seam_surface=false`
- no variant is accepted automatically

## 验证命令与结果

- `python3 CharacterPackage/tools/build_art_directed_hair_ribbons_v1_variants.py`
  - result: 3 variants generated; comparison report/contact sheet/manual review doc written.
- `python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v`
  - result: 63 tests passed.
- `python3 -m compileall CharacterPackage/tools`
  - result: passed.
- `git diff --name-only -- CharacterPackage/semantic_layer_v8`
  - result: empty.

## 视觉 / 人工复核判断

- `fuller` has the best numeric balance and is the recommended first human review target.
- This is not an acceptance decision.
- Contact sheet suggests candidate-only renders can still read sparse/fragmentary; human review must decide whether any variant is useful enough to polish.
- Do not proceed to `cloth_seam_surface`.
- Do not replace v8 beauty.
- Do not call any variant final production hair.

## 当前 blocker

```text
manual_review_hair_v1_variants
```

## 推荐下一条 Goal

```text
/goal Review the art_directed_hair_ribbons_v1 overnight variants.
Open CharacterPackage/semantic_layer_v9_hair/art_directed_v1_variants/hair_variants_contact_sheet.png
and inspect balanced, fuller, silhouette. Decide whether fuller is acceptable
as the next hair polish base, or reject all variants with visual reasons.
Do not proceed to cloth_seam_surface. Keep semantic_layer_v8 unchanged and
replace_in_beauty_glb=false.
```
