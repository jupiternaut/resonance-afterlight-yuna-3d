#!/usr/bin/env python3
"""Read-only inspector for YUNA candidate asset directories.

The script checks whether a candidate directory has export assets, validation
PNGs, and a report JSON. It writes nothing; the JSON summary is printed to
stdout and the exit code reflects whether the required files were found.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATE = ROOT / "semantic_layer_v3"
REQUIRED_EXPORTS = ("glb", "fbx", "obj", "blend")
REPORT_NAMES = ("validation_report.json",)
IGNORED_DIRS = {"__pycache__", ".git", ".DS_Store"}
REPORT_EXPORT_KEYS = {"blend", "glb", "fbx", "obj", "validation_screenshots"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a YUNA candidate directory and print a short JSON summary.",
    )
    parser.add_argument(
        "candidate_dir",
        nargs="?",
        default=str(DEFAULT_CANDIDATE),
        help="Candidate directory to inspect. Defaults to semantic_layer_v3.",
    )
    parser.add_argument(
        "--max-files-per-kind",
        type=int,
        default=5,
        help="Maximum file entries to include for each file kind.",
    )
    return parser.parse_args()


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        try:
            return str(path.relative_to(ROOT))
        except ValueError:
            return str(path)


def file_entry(path: Path, root: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": rel(path, root),
        "bytes": stat.st_size,
    }


def iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
    return sorted(files)


def is_export_like(path: Path, candidate: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    return "exports" in parts or path.parent == candidate


def is_validation_png(path: Path, candidate: Path) -> bool:
    if path.suffix.lower() != ".png":
        return False
    parts = {part.lower() for part in path.relative_to(candidate).parts[:-1]}
    return "validation" in parts


def find_reports(files: list[Path], candidate: Path) -> list[Path]:
    exact = [path for path in files if path.name in REPORT_NAMES]
    fuzzy = [
        path
        for path in files
        if path.suffix.lower() == ".json" and "report" in path.stem.lower() and path not in exact
    ]
    return sorted(exact + fuzzy, key=lambda path: (len(path.relative_to(candidate).parts), rel(path, candidate)))


def flatten_strings(value: Any, prefix: str = "") -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(prefix, value)]
    if isinstance(value, dict):
        items: list[tuple[str, str]] = []
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            items.extend(flatten_strings(child, child_prefix))
        return items
    if isinstance(value, list):
        items = []
        for index, child in enumerate(value):
            child_prefix = f"{prefix}[{index}]"
            items.extend(flatten_strings(child, child_prefix))
        return items
    return []


def report_export_strings(data: dict[str, Any]) -> list[tuple[str, str]]:
    exports = data.get("exports")
    if not isinstance(exports, dict):
        return []

    items: list[tuple[str, str]] = []
    for key, value in exports.items():
        if key not in REPORT_EXPORT_KEYS:
            continue
        items.extend(flatten_strings(value, f"exports.{key}"))
    return items


def resolve_report_path(raw_path: str, candidate: Path, report_path: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path

    options = [
        report_path.parent / path,
        candidate / path,
        candidate.parent / path,
    ]
    if path.parts and path.parts[0] == candidate.name:
        options.append(candidate.parent / path)
        options.append(candidate / Path(*path.parts[1:]))

    for option in options:
        if option.exists():
            return option
    return options[0]


def summarize_report(report_path: Path, candidate: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "present": True,
        "path": rel(report_path, candidate),
        "parse_status": "ok",
    }
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        summary["parse_status"] = "json_error"
        summary["error"] = str(error)
        return summary

    if not isinstance(data, dict):
        summary["parse_status"] = "unexpected_root_type"
        summary["root_type"] = type(data).__name__
        return summary

    quality = data.get("quality") if isinstance(data.get("quality"), dict) else {}
    glb_roundtrip = data.get("glb_roundtrip") if isinstance(data.get("glb_roundtrip"), dict) else {}
    failures = quality.get("failures") if isinstance(quality.get("failures"), list) else []
    warnings = quality.get("warnings") if isinstance(quality.get("warnings"), list) else []

    summary.update(
        {
            "created_at": data.get("created_at"),
            "route": data.get("route"),
            "status": data.get("status"),
            "quality_status": quality.get("status"),
            "failure_count": len(failures),
            "warning_count": len(warnings),
            "glb_roundtrip_status": glb_roundtrip.get("status"),
            "mesh_count": glb_roundtrip.get("mesh_count"),
            "material_count": glb_roundtrip.get("material_count"),
        }
    )

    reported_assets = []
    for label, raw_path in report_export_strings(data):
        resolved = resolve_report_path(raw_path, candidate, report_path)
        reported_assets.append(
            {
                "label": label,
                "path": raw_path,
                "present": resolved.exists(),
            }
        )

    if reported_assets:
        missing = [asset for asset in reported_assets if not asset["present"]]
        summary["reported_assets"] = {
            "present_count": len(reported_assets) - len(missing),
            "missing_count": len(missing),
            "missing": missing[:10],
        }

    return summary


def summarize_candidate(candidate: Path, max_files_per_kind: int) -> dict[str, Any]:
    candidate = candidate.resolve()
    if not candidate.exists() or not candidate.is_dir():
        return {
            "candidate": str(candidate),
            "ok": False,
            "error": "candidate_dir_not_found",
        }

    files = iter_files(candidate)
    export_files = {
        suffix: [
            path
            for path in files
            if path.suffix.lower() == f".{suffix}" and is_export_like(path, candidate)
        ]
        for suffix in REQUIRED_EXPORTS
    }
    validation_pngs = [path for path in files if is_validation_png(path, candidate)]
    reports = find_reports(files, candidate)

    missing = [suffix for suffix, paths in export_files.items() if not paths]
    if not validation_pngs:
        missing.append("validation_png")
    if not reports:
        missing.append("report_json")

    report_summary: dict[str, Any]
    if reports:
        report_summary = summarize_report(reports[0], candidate)
        if report_summary.get("parse_status") != "ok":
            missing.append("valid_report_json")
    else:
        report_summary = {"present": False}

    return {
        "candidate": str(candidate),
        "ok": not missing,
        "missing": missing,
        "exports": {
            "required": list(REQUIRED_EXPORTS),
            "present": {suffix: bool(paths) for suffix, paths in export_files.items()},
            "counts": {suffix: len(paths) for suffix, paths in export_files.items()},
            "files": {
                suffix: [file_entry(path, candidate) for path in paths[:max_files_per_kind]]
                for suffix, paths in export_files.items()
            },
        },
        "validation_pngs": {
            "present": bool(validation_pngs),
            "count": len(validation_pngs),
            "files": [file_entry(path, candidate) for path in validation_pngs[:max_files_per_kind]],
        },
        "report_json": {
            **report_summary,
            "candidate_count": len(reports),
        },
    }


def main() -> int:
    args = parse_args()
    summary = summarize_candidate(Path(args.candidate_dir), max(1, args.max_files_per_kind))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
