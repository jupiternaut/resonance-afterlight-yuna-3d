#!/usr/bin/env python3
"""Prepare shared YUNA inputs for Rodin/Meshy image-to-3D A/B runs."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "ai_3d_runs" / "common" / "inputs"


SOURCES = {
    "locked_front_rgba": ROOT / "refs" / "front_rgba" / "yuna_front_rgba.png",
    "transparent_side_ref": ROOT / "refs" / "ai_turnarounds" / "cutouts" / "yuna_left_side.png",
    "transparent_back_ref": ROOT / "refs" / "ai_turnarounds" / "cutouts" / "yuna_back.png",
    "dcc_turnaround_3view": ROOT / "refs" / "dcc_reference" / "chatgpt_generated" / "yuna_dcc_turnaround_3view.png",
    "dcc_expression_sheet": ROOT / "refs" / "dcc_reference" / "chatgpt_generated" / "yuna_dcc_face_expression_sheet.png",
    "dcc_weapon_sheet": ROOT / "refs" / "dcc_reference" / "chatgpt_generated" / "yuna_dcc_weapon_orthographic_sheet.png",
    "dcc_material_reference": ROOT / "refs" / "dcc_reference" / "chatgpt_generated" / "yuna_dcc_material_texture_reference.png",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_image(src: Path, dst_name: str) -> dict:
    dst = INPUT_DIR / dst_name
    shutil.copy2(src, dst)
    with Image.open(dst) as image:
        width, height = image.size
    return {
        "path": str(dst.relative_to(ROOT)),
        "source": str(src.relative_to(ROOT)),
        "width": width,
        "height": height,
        "sha256": sha256(dst),
    }


def crop_turnaround(src: Path) -> dict:
    outputs = {}
    with Image.open(src) as image:
        width, height = image.size
        crops = {
            "dcc_front_crop": (0, 0, width // 3, height),
            "dcc_side_crop": (width // 3, 0, (2 * width) // 3, height),
            "dcc_back_crop": ((2 * width) // 3, 0, width, height),
        }
        for name, box in crops.items():
            out = INPUT_DIR / f"yuna_{name}.png"
            image.crop(box).save(out)
            with Image.open(out) as cropped:
                crop_width, crop_height = cropped.size
            outputs[name] = {
                "path": str(out.relative_to(ROOT)),
                "source": str(src.relative_to(ROOT)),
                "crop_box": list(box),
                "width": crop_width,
                "height": crop_height,
                "sha256": sha256(out),
            }
    return outputs


def make_contact_sheet(manifest: dict) -> dict:
    keys = [
        "locked_front_rgba",
        "dcc_front_crop",
        "dcc_side_crop",
        "dcc_back_crop",
        "dcc_expression_sheet",
        "dcc_weapon_sheet",
        "dcc_material_reference",
    ]
    thumb_w, thumb_h = 220, 220
    label_h = 28
    margin = 18
    cols = 4
    rows = 2
    sheet = Image.new("RGB", (cols * (thumb_w + margin) + margin, rows * (thumb_h + label_h + margin) + margin), "#101820")
    draw = ImageDraw.Draw(sheet)

    for index, key in enumerate(keys):
        item = manifest["inputs"][key]
        image_path = ROOT / item["path"]
        col = index % cols
        row = index // cols
        x = margin + col * (thumb_w + margin)
        y = margin + row * (thumb_h + label_h + margin)
        with Image.open(image_path) as image:
            image = image.convert("RGBA")
            image.thumbnail((thumb_w, thumb_h), Image.LANCZOS)
            plate = Image.new("RGBA", (thumb_w, thumb_h), "#e8edf2")
            px = (thumb_w - image.width) // 2
            py = (thumb_h - image.height) // 2
            plate.alpha_composite(image, (px, py))
            sheet.paste(plate.convert("RGB"), (x, y))
        draw.text((x, y + thumb_h + 8), key, fill="#dcecff")

    out = ROOT / "ai_3d_runs" / "common" / "yuna_ab_input_contact_sheet.png"
    sheet.save(out)
    return {
        "path": str(out.relative_to(ROOT)),
        "width": sheet.width,
        "height": sheet.height,
        "sha256": sha256(out),
    }


def main() -> None:
    INPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {
        "character_id": "yuna-white-sword",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Shared immutable input set for Rodin Gen-2 vs Meshy 6 Multi-view A/B generation.",
        "upload_order": [
            "locked_front_rgba",
            "dcc_front_crop",
            "dcc_side_crop",
            "dcc_back_crop",
            "dcc_expression_sheet",
            "dcc_weapon_sheet",
            "dcc_material_reference",
            "transparent_side_ref",
            "transparent_back_ref",
        ],
        "inputs": {},
    }

    for key, src in SOURCES.items():
        if not src.exists():
            raise FileNotFoundError(src)
        manifest["inputs"][key] = copy_image(src, f"yuna_{key}.png")

    manifest["inputs"].update(crop_turnaround(SOURCES["dcc_turnaround_3view"]))
    manifest["contact_sheet"] = make_contact_sheet(manifest)

    manifest_path = ROOT / "ai_3d_runs" / "common" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    upload_note = INPUT_DIR / "UPLOAD_ORDER.md"
    upload_note.write_text(
        "\n".join(
            [
                "# YUNA AI 3D Upload Order",
                "",
                "Use the same inputs for Rodin and Meshy. Do not mix in the older automated geometry screenshots.",
                "",
                "1. `yuna_locked_front_rgba.png`",
                "2. `yuna_dcc_front_crop.png`",
                "3. `yuna_dcc_side_crop.png`",
                "4. `yuna_dcc_back_crop.png`",
                "5. `yuna_dcc_expression_sheet.png`",
                "6. `yuna_dcc_weapon_sheet.png`",
                "7. `yuna_dcc_material_reference.png`",
                "",
                "If a tool limits image count, keep 1-4 first. Add weapon/material only if there is room.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(json.dumps({"manifest": str(manifest_path), "inputs": str(INPUT_DIR)}, indent=2))


if __name__ == "__main__":
    main()
