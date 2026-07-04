#!/usr/bin/env python3
"""Build the third executable v9 candidate: leg quad-loop retopo proxy."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from semantic_actuators.leg_quad_loop_retopo_proxy import run_leg_quad_loop_retopo_proxy
from semantic_actuators.state import ActuatorPaths


CHARACTER_PACKAGE = Path(__file__).resolve().parents[1]
REPO_ROOT = CHARACTER_PACKAGE.parent
OUT = CHARACTER_PACKAGE / "semantic_layer_v9_leg"
STEM = "yuna_semantic_layer_v9_leg"


def main() -> int:
    paths = ActuatorPaths(
        repo_root=REPO_ROOT,
        character_package=CHARACTER_PACKAGE,
        output_dir=OUT,
        spec_path=OUT / "specs" / f"{STEM}.json",
        obj_path=OUT / "exports" / f"{STEM}.obj",
        glb_path=OUT / "exports" / f"{STEM}.glb",
        report_path=OUT / "validation_report.json",
    )
    result = run_leg_quad_loop_retopo_proxy(paths)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.status != "failed" else 1


if __name__ == "__main__":
    sys.exit(main())
