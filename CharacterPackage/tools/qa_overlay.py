#!/usr/bin/env python3
"""Generate simple front-view alpha/RGB QA metrics for character renders."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops


def alpha_mask(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    return rgba.getchannel("A").point(lambda value: 255 if value > 0 else 0)


def compute_iou(a: Image.Image, b: Image.Image) -> float:
    data_a = list(alpha_mask(a).getdata())
    data_b = list(alpha_mask(b).getdata())
    inter = sum(1 for x, y in zip(data_a, data_b) if x and y)
    union = sum(1 for x, y in zip(data_a, data_b) if x or y)
    return inter / max(union, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", required=True, type=Path)
    parser.add_argument("--render", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    ref = Image.open(args.ref).convert("RGBA")
    render = Image.open(args.render).convert("RGBA").resize(ref.size, Image.Resampling.LANCZOS)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    overlay = Image.blend(ref.convert("RGB"), render.convert("RGB"), 0.5)
    diff = ImageChops.difference(ref.convert("RGB"), render.convert("RGB"))
    overlay.save(args.out_dir / "front_overlay.png")
    diff.save(args.out_dir / "front_diff.png")

    metrics = {
        "iou": compute_iou(ref, render),
        "ref_size": ref.size,
        "render_size": render.size,
        "note": "Use this only for front-view proxy/render comparison. Final DCC QA should add landmarks and color metrics."
    }
    (args.out_dir / "front_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
