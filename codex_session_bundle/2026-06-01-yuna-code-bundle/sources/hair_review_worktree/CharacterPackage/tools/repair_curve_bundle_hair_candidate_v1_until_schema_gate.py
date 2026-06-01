#!/usr/bin/env python3
"""Repair curve-bundle hair candidate until target-schema gates pass or attempts are exhausted."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from semantic_actuators.authored_hair_ribbons import write_json
from semantic_actuators.curve_bundle_hair_repair_v1 import (
    REPAIR_ATTEMPTS,
    REPAIR_ROUTE,
    RepairAttemptConfig,
    attempt_passes_schema_gate,
    repair_report_summary,
    run_repaired_curve_bundle_hair_candidate_v1,
    schema_score,
)
from semantic_actuators.state import ActuatorPaths


CHARACTER_PACKAGE = Path(__file__).resolve().parents[1]
REPO_ROOT = CHARACTER_PACKAGE.parent
OUT = CHARACTER_PACKAGE / "semantic_layer_v9_hair" / "curve_bundle_candidate_v1"
ATTEMPTS_DIR = OUT / "repair_attempts"
FINAL_STEM = "yuna_curve_bundle_hair_v1"
REPAIR_REPORT = OUT / "repair_report.json"
VALIDATION_DIR = OUT / "validation_ci"
VALIDATION_CI_REPORT = VALIDATION_DIR / "validation_ci_report.json"
TARGET_SCHEMA_EVAL_DIR = OUT / "target_schema_v1_eval"

SCREENSHOT_ALIASES = {
    "candidate_front": "candidate_front.png",
    "overlay_front": "overlay_front.png",
    "yaw30": "yaw30.png",
    "side": "side.png",
    "wire": "wire.png",
    "exploded": "exploded.png",
}


def run_step(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        args,
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {
        "args": args,
        "exit_code": result.returncode,
        "log_tail": result.stdout.splitlines()[-80:],
    }


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def display(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def build_paths(output_dir: Path, stem: str) -> ActuatorPaths:
    return ActuatorPaths(
        repo_root=REPO_ROOT,
        character_package=CHARACTER_PACKAGE,
        output_dir=output_dir,
        spec_path=output_dir / "specs" / f"{stem}.json",
        obj_path=output_dir / "exports" / f"{stem}.obj",
        glb_path=output_dir / "exports" / f"{stem}.glb",
        report_path=output_dir / "validation_report.json",
    )


def alias_screenshots(paths: ActuatorPaths, validation_dir: Path) -> dict[str, dict[str, Any]]:
    aliases: dict[str, dict[str, Any]] = {}
    for key, alias_name in SCREENSHOT_ALIASES.items():
        source = validation_dir / f"{paths.glb_path.stem}_validation_{key}.png"
        target = validation_dir / alias_name
        if source.exists():
            shutil.copyfile(source, target)
        aliases[key] = {
            "source": display(source) if source.exists() else str(source),
            "path": display(target),
            "exists": target.exists(),
            "bytes": target.stat().st_size if target.exists() else 0,
        }
    return aliases


def run_validation_and_schema(paths: ActuatorPaths, validation_dir: Path, target_eval_dir: Path) -> dict[str, Any]:
    validation_dir.mkdir(parents=True, exist_ok=True)
    ci_report = validation_dir / "validation_ci_report.json"
    if not paths.glb_path.exists():
        write_json(
            ci_report,
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "route": "blender_semantic_validation_v0",
                "status": "skipped_with_reason",
                "reason": "candidate_glb_missing",
                "ready_for_cloth_seam_surface": False,
            },
        )
        return {
            "blender_validation": {"skipped_with_reason": "candidate_glb_missing", "exit_code": 0},
            "target_schema_eval": {"skipped_with_reason": "candidate_front_missing", "exit_code": 0},
            "schema_metrics": {},
        }
    validation_step = run_step(
        [
            sys.executable,
            str(CHARACTER_PACKAGE / "tools" / "run_blender_semantic_validation.py"),
            "--candidate-glb",
            str(paths.glb_path),
            "--candidate-report",
            str(paths.report_path),
            "--output-dir",
            str(validation_dir),
            "--report",
            str(ci_report),
        ]
    )
    ci_data = load_json(ci_report)
    ci_data["screenshot_aliases"] = alias_screenshots(paths, validation_dir)
    ci_data["ready_for_cloth_seam_surface"] = False
    write_json(ci_report, ci_data)
    candidate_front = validation_dir / f"{paths.glb_path.stem}_validation_candidate_front.png"
    if candidate_front.exists():
        schema_step = run_step(
            [
                sys.executable,
                str(CHARACTER_PACKAGE / "tools" / "build_hair_target_schema_v1.py"),
                "--output-dir",
                str(target_eval_dir),
                "--candidate-front",
                str(candidate_front),
                "--candidate-route-label",
                REPAIR_ROUTE,
                "--validation-report",
                str(paths.report_path),
                "--validation-ci-report",
                str(ci_report),
            ]
        )
    else:
        schema_step = {
            "args": [],
            "exit_code": 0,
            "skipped_with_reason": "candidate_front_render_missing",
        }
    schema_metrics = load_json(target_eval_dir / "hair_target_schema_v1_report.json")
    return {
        "blender_validation": validation_step,
        "target_schema_eval": schema_step,
        "schema_metrics": schema_metrics,
    }


def attempt_summary(
    *,
    config: RepairAttemptConfig,
    paths: ActuatorPaths,
    validation_result: dict[str, Any],
) -> dict[str, Any]:
    schema_metrics = validation_result.get("schema_metrics", {})
    metrics = {
        "forbidden_candidate_leak_ratio": schema_metrics.get("forbidden_candidate_leak_ratio"),
        "candidate_soft_inside_ratio": schema_metrics.get("candidate_soft_inside_ratio"),
        "candidate_core_coverage_ratio": schema_metrics.get("candidate_core_coverage_ratio"),
        "candidate_visible_area_ratio": schema_metrics.get("candidate_visible_area_ratio"),
        "soft_silhouette_coverage_ratio": schema_metrics.get("soft_silhouette_coverage_ratio"),
        "component_count": schema_metrics.get("component_count"),
        "candidate_front_visible_hair_mass": schema_metrics.get("candidate_front_visible_hair_mass"),
        "primary_group_presence_passed": schema_metrics.get("primary_group_presence_passed"),
        "yaw30_hair_readability": schema_metrics.get("yaw30_hair_readability"),
        "side_hair_readability": schema_metrics.get("side_hair_readability"),
        "candidate_target_schema_status": schema_metrics.get("candidate_target_schema_status"),
        "manual_visual_review_status": schema_metrics.get("manual_visual_review_status"),
    }
    score = schema_score(schema_metrics)
    return {
        "attempt_index": config.index,
        "attempt_name": config.name,
        "paths": {
            "output_dir": display(paths.output_dir),
            "obj": display(paths.obj_path),
            "glb": display(paths.glb_path),
            "report": display(paths.report_path),
        },
        "metrics": metrics,
        "score": score,
        "passes_schema_gate": attempt_passes_schema_gate(schema_metrics),
        "blender_exit_code": validation_result.get("blender_validation", {}).get("exit_code"),
        "target_schema_exit_code": validation_result.get("target_schema_eval", {}).get("exit_code"),
    }


def write_result_markdown(path: Path, repair_report: dict[str, Any]) -> None:
    best = repair_report.get("best_attempt_metrics") or {}
    passed = repair_report.get("passed_schema_gate") is True
    title = "Curve bundle hair repair result"
    status = repair_report["status"]
    lines = [
        f"# {title}",
        "",
        f"Status: `{status}`",
        "",
        "- v8 remains untouched.",
        "- `replace_in_beauty_glb=false`.",
        "- `ready_for_cloth_seam_surface=false`.",
        "- This is not final production hair.",
        "",
        "## Best Attempt Metrics",
        "",
        f"- forbidden_candidate_leak_ratio: `{best.get('forbidden_candidate_leak_ratio')}`",
        f"- candidate_soft_inside_ratio: `{best.get('candidate_soft_inside_ratio')}`",
        f"- candidate_core_coverage_ratio: `{best.get('candidate_core_coverage_ratio')}`",
        f"- candidate_visible_area_ratio: `{best.get('candidate_visible_area_ratio')}`",
        f"- primary_group_presence_passed: `{best.get('primary_group_presence_passed')}`",
        f"- candidate_front_visible_hair_mass: `{best.get('candidate_front_visible_hair_mass')}`",
        "",
    ]
    if passed:
        lines.extend(
            [
                "## Verdict",
                "",
                "The schema gate passed programmatically, but manual visual review is still required before any replacement or cloth work.",
            ]
        )
    else:
        lines.extend(
            [
                "## Failure",
                "",
                "`repair_failed_after_6_attempts`: the best candidate did not satisfy forbidden leak and soft-inside gates together.",
                "",
                "Recommended next step: manual curve edits against the target schema masks.",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def finalize_canonical_reports(repair_report: dict[str, Any]) -> None:
    status = repair_report["status"]
    for path in (OUT / "validation_report.json", VALIDATION_CI_REPORT):
        report = load_json(path)
        if not report:
            continue
        report["status"] = status
        report["repair_loop"] = {
            "route": REPAIR_ROUTE,
            "status": status,
            "attempt_count": repair_report["attempt_count"],
            "best_attempt_index": repair_report["best_attempt_index"],
            "best_attempt_metrics": repair_report["best_attempt_metrics"],
            "passed_schema_gate": repair_report["passed_schema_gate"],
        }
        report["ready_for_cloth_seam_surface"] = False
        validation = report.setdefault("validation", {})
        validation["visual_sanity_status"] = status
        validation["manual_visual_review_status"] = (
            "pending_user_review_schema_gate_passed"
            if repair_report["passed_schema_gate"]
            else "blocked_by_target_schema_alignment"
        )
        validation["ready_for_cloth_seam_surface"] = False
        validation["replace_in_beauty_glb"] = False
        if "candidate_contract" in report:
            report["candidate_contract"]["visual_sanity_status"] = status
            report["candidate_contract"]["manual_visual_review_status"] = validation["manual_visual_review_status"]
        write_json(path, report)


def write_chatgpt_handoff(repair_report: dict[str, Any]) -> None:
    best = repair_report.get("best_attempt_metrics") or {}
    passed = repair_report.get("passed_schema_gate") is True
    next_goal = "manual_visual_review_curve_bundle_hair_candidate_v1" if passed else "manual_curve_edit_curve_bundle_hair_candidate_v1"
    handoff = f"""# COPY_TO_CHATGPT_HANDOFF

项目：`jupiternaut/resonance-afterlight-yuna-3d`

分支：`feature/authored-hair-ribbons-v0`

提交：本文件生成于提交前；最终提交哈希以 Codex 最终回复或 GitHub 远端为准。

本轮目标：执行 `repair_curve_bundle_hair_candidate_v1_until_schema_gate`，最多 6 次修复 `curve_bundle_candidate_v1`，降低 forbidden leak 并提高 soft-inside，同时保持 v8 不变、不替换 beauty、不推进 cloth。

公式阶段：
`theta_hair_next = ProjectToConstraints_hair((1-alpha)*theta_hair + alpha*RobustFuse(repair_attempts, target_schema_v1, validation_obs, priors))`

本轮结论：
- repair status: `{repair_report['status']}`
- passed_schema_gate: `{repair_report['passed_schema_gate']}`
- best_attempt_index: `{repair_report['best_attempt_index']}`
- `replace_in_beauty_glb=false`
- `ready_for_cloth_seam_surface=false`
- `CharacterPackage/semantic_layer_v8` 未修改
- 这不是最终生产头发

关键指标：
- forbidden_candidate_leak_ratio: `{best.get('forbidden_candidate_leak_ratio')}`
- candidate_soft_inside_ratio: `{best.get('candidate_soft_inside_ratio')}`
- candidate_core_coverage_ratio: `{best.get('candidate_core_coverage_ratio')}`
- candidate_visible_area_ratio: `{best.get('candidate_visible_area_ratio')}`
- primary_group_presence_passed: `{best.get('primary_group_presence_passed')}`
- candidate_front_visible_hair_mass: `{best.get('candidate_front_visible_hair_mass')}`

生成/更新文件：
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/repair_report.json`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/repair_attempts/`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_report.json`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/validation_ci_report.json`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/candidate_front.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/overlay_front.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/yaw30.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/side.png`
- `CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/target_schema_v1_eval/hair_target_schema_v1_report.json`
- `CharacterPackage/semantic_layer_v9_candidate/CHATGPT_HANDOFF.md`

验证命令：
- `python3 -m unittest discover -s CharacterPackage/tools/tests -p 'test_*.py' -v`
- `python3 -m compileall CharacterPackage/tools`
- `git diff --name-only -- CharacterPackage/semantic_layer_v8`

验证结果：待最终 Codex 回复填写。

视觉/人工复核结论：
- {'schema gate 已通过，但仍需要人工视觉复核；不应自动替换 v8 beauty，也不应直接推进 cloth。' if passed else '6 次修复后仍未过 schema gate；应保留失败状态并进行人工曲线编辑，不应推进 cloth。'}

当前阻塞：
- `{next_goal}`

推荐下一条 Codex Goal：

```text
/goal Continue {next_goal}.

Read:
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/repair_report.json
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_report.json
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/target_schema_v1_eval/hair_target_schema_v1_report.json
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/candidate_front.png
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/overlay_front.png
- CharacterPackage/semantic_layer_v9_hair/curve_bundle_candidate_v1/validation_ci/yaw30.png

Keep semantic_layer_v8 unchanged.
Keep replace_in_beauty_glb=false.
Do not proceed to cloth_seam_surface.
Do not call result production hair.
```
"""
    (CHARACTER_PACKAGE / "semantic_layer_v9_candidate" / "CHATGPT_HANDOFF.md").write_text(handoff, encoding="utf-8")


def main() -> int:
    if ATTEMPTS_DIR.exists():
        shutil.rmtree(ATTEMPTS_DIR)
    attempts: list[dict[str, Any]] = []
    best_attempt: dict[str, Any] | None = None
    best_config: RepairAttemptConfig | None = None
    passed = False
    for config in REPAIR_ATTEMPTS:
        attempt_dir = ATTEMPTS_DIR / f"attempt_{config.index:02d}_{config.name}"
        stem = f"{FINAL_STEM}_repair_attempt_{config.index:02d}"
        paths = build_paths(attempt_dir, stem)
        run_repaired_curve_bundle_hair_candidate_v1(paths, config)
        validation_result = run_validation_and_schema(
            paths,
            attempt_dir / "validation_ci",
            attempt_dir / "target_schema_v1_eval",
        )
        summary = attempt_summary(config=config, paths=paths, validation_result=validation_result)
        attempts.append(summary)
        if best_attempt is None or summary["score"] > best_attempt["score"]:
            best_attempt = summary
            best_config = config
        if summary["passes_schema_gate"]:
            passed = True
            best_attempt = summary
            best_config = config
            break

    if best_config is None:
        raise RuntimeError("Repair loop did not produce any attempts")

    final_paths = build_paths(OUT, FINAL_STEM)
    run_repaired_curve_bundle_hair_candidate_v1(final_paths, best_config)
    final_validation = run_validation_and_schema(final_paths, VALIDATION_DIR, TARGET_SCHEMA_EVAL_DIR)
    final_summary = attempt_summary(config=best_config, paths=final_paths, validation_result=final_validation)
    passed = attempt_passes_schema_gate(final_validation.get("schema_metrics", {}))
    if best_attempt is None or final_summary["score"] >= best_attempt["score"]:
        best_attempt = final_summary

    repair_report = repair_report_summary(attempts=attempts, best_attempt=best_attempt, passed=passed)
    write_json(REPAIR_REPORT, repair_report)
    finalize_canonical_reports(repair_report)
    if passed:
        write_result_markdown(OUT / "repair_success_report.md", repair_report)
        write_result_markdown(OUT / "failure_report.md", repair_report)
    else:
        write_result_markdown(OUT / "failure_report.md", repair_report)
    write_chatgpt_handoff(repair_report)
    print(json.dumps(repair_report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
