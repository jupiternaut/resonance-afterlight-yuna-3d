#!/usr/bin/env python3
"""Build semantic v9 cloth seam-surface v1 manual review pack."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from semantic_actuators.cloth_seam_surface import run_cloth_review_pack


CHARACTER_PACKAGE = Path(__file__).resolve().parents[1]
REPO_ROOT = CHARACTER_PACKAGE.parent


def main() -> int:
    comparison = run_cloth_review_pack(REPO_ROOT, CHARACTER_PACKAGE)
    print(json.dumps(comparison, ensure_ascii=False, indent=2))
    return 0 if comparison["status"] == "manual_review_required" else 1


if __name__ == "__main__":
    sys.exit(main())
