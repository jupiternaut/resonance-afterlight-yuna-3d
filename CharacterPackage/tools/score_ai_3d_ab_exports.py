#!/usr/bin/env python3
"""Create a lightweight status report for Rodin/Meshy A/B exports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "ai_3d_runs"
TOOLS = ("rodin", "meshy")
EXPECTED_SUFFIXES = (".glb", ".fbx", ".obj", ".usdz", ".stl")

REQUEST_FILES = {
    "rodin": ("request_payload.json", "rodin_gen2_payload.json", "rodin_weapon_payload.json"),
    "meshy": ("request_payload.json", "payloads/meshy_multi_image_to_3d_payload.template.json"),
}

EXPORT_DIRS = {
    "rodin": ("exports", "results", "outputs"),
    "meshy": ("exports", "outputs", "results"),
}


def file_info(path: Path) -> dict:
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
    }


def scan_tool(tool: str) -> dict:
    root = RUN_ROOT / tool
    status_file = root / "status.json"
    tool_status = {}
    if status_file.exists():
        try:
            tool_status = json.loads(status_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            tool_status = {"status_parse_error": True}

    status = {
        "tool": tool,
        "root": str(root.relative_to(ROOT)),
        "request_present": any((root / path).exists() for path in REQUEST_FILES[tool]),
        "run_log_present": (root / "run_log.md").exists(),
        "execution_log_present": (root / "execution_log.md").exists(),
        "submitted_marker_present": (root / "submitted.json").exists() or bool(tool_status.get("submitted")),
        "blocked_on_credentials": bool(
            tool_status.get("blocked_on_credentials")
            or tool_status.get("submission", {}).get("blocked_on_credentials")
        ),
        "exports": [],
        "tool_status": tool_status,
        "state": "not_started",
    }

    for dirname in EXPORT_DIRS[tool]:
        exports_dir = root / dirname
        if not exports_dir.exists():
            continue
        for path in sorted(exports_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in EXPECTED_SUFFIXES:
                status["exports"].append(file_info(path))

    if status["exports"]:
        status["state"] = "exports_available"
    elif status["submitted_marker_present"]:
        status["state"] = "submitted_waiting_for_exports"
    elif status["blocked_on_credentials"] and status["request_present"]:
        status["state"] = "prepared_blocked_on_credentials"
    elif status["request_present"]:
        status["state"] = "prepared_blocked_or_pending_submission"

    return status


def main() -> None:
    report = {
        "character_id": "yuna-white-sword",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Rodin Gen-2 vs Meshy 6 Multi-view A/B export readiness report.",
        "tools": {tool: scan_tool(tool) for tool in TOOLS},
        "next_gate": "Import available GLB/FBX exports into Blender, render front orthographic preview, then compare against locked_front_rgba.",
    }

    out = RUN_ROOT / "ab_status.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(out), "states": {k: v["state"] for k, v in report["tools"].items()}}, indent=2))


if __name__ == "__main__":
    main()
