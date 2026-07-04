#!/usr/bin/env python3
"""Stage YUNA production assets into a Unity validation project."""

from __future__ import annotations

from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "unity/ValidationProject"
ASSETS = PROJECT / "Assets/Characters/YUNA"


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> None:
    for name in ["yuna_production_lod0.fbx", "yuna_production_lod1.fbx", "yuna_production_lod2.fbx"]:
        copy_file(ROOT / "rig" / name, ASSETS / "Models" / name)

    for texture in (ROOT / "textures/export_unity_urp").glob("*.png"):
        copy_file(texture, ASSETS / "Textures" / texture.name)

    copy_file(ROOT / "unity/editor_tools/YunaProductionValidator.cs", PROJECT / "Assets/Editor/YunaProductionValidator.cs")
    copy_file(ROOT / "unity/editor_tools/CharacterImportPostprocessor.cs", PROJECT / "Assets/Editor/CharacterImportPostprocessor.cs")

    print(f"staged:{ASSETS}")


if __name__ == "__main__":
    main()
