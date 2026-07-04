from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ActuatorPaths:
    repo_root: Path
    character_package: Path
    output_dir: Path
    spec_path: Path
    obj_path: Path
    glb_path: Path
    report_path: Path


@dataclass
class MeshData:
    vertices: list[tuple[float, float, float]]
    uvs: list[tuple[float, float]]
    faces: list[tuple[int, int, int, int]]
    face_materials: list[int]
    section_count: int
    thickness: float
    bevel: float

    def to_summary(self) -> dict[str, Any]:
        return {
            "vertices": len(self.vertices),
            "uvs": len(self.uvs),
            "faces": len(self.faces),
            "section_count": self.section_count,
            "thickness": self.thickness,
            "bevel": self.bevel,
            "material_face_counts": {
                "textured": sum(1 for item in self.face_materials if item == 0),
                "side": sum(1 for item in self.face_materials if item == 1),
            },
        }


@dataclass
class ActuatorResult:
    actuator: str
    status: str
    part_id: str
    decision_source: str
    generated_files: dict[str, str]
    mesh_summary: dict[str, Any]
    validation: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
