from __future__ import annotations

import json
import math
import shutil
import subprocess
import tempfile
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image

from .registry import register
from .state import ActuatorPaths, ActuatorResult, MeshData
from .validation_contract import file_record, validate_leg_candidate_report


ACTUATOR_NAME = "leg_quad_loop_retopo_proxy_v0"
PART_ID = "legs"
RING_COUNT = 28
RADIAL_SEGMENTS = 12


@dataclass
class LegComponent:
    id: str
    side: str
    texture_path: Path
    bbox: tuple[int, int, int, int]
    mesh: MeshData
    loop_rings: dict[str, int]
    loop_world_z: dict[str, float]


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def find_blender() -> str | None:
    blender = shutil.which("blender")
    if blender:
        return blender
    app_path = Path("/Applications/Blender.app/Contents/MacOS/Blender")
    if app_path.exists():
        return str(app_path)
    return None


def alpha_bbox(path: Path) -> tuple[int, int, int, int]:
    image = Image.open(path).convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError(f"Texture has no visible alpha: {path}")
    return bbox


def alpha_components(path: Path, threshold: int = 16, min_area: int = 5000) -> list[tuple[int, tuple[int, int, int, int]]]:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError(f"Texture has no visible alpha: {path}")
    x0, y0, x1, y1 = bbox
    seen: set[tuple[int, int]] = set()
    components: list[tuple[int, tuple[int, int, int, int]]] = []
    for y in range(y0, y1):
        for x in range(x0, x1):
            if alpha.getpixel((x, y)) <= threshold or (x, y) in seen:
                continue
            queue: deque[tuple[int, int]] = deque([(x, y)])
            seen.add((x, y))
            xs: list[int] = []
            ys: list[int] = []
            while queue:
                cx, cy = queue.popleft()
                xs.append(cx)
                ys.append(cy)
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if nx < x0 or nx >= x1 or ny < y0 or ny >= y1 or (nx, ny) in seen:
                        continue
                    if alpha.getpixel((nx, ny)) > threshold:
                        seen.add((nx, ny))
                        queue.append((nx, ny))
            area = len(xs)
            if area >= min_area:
                components.append((area, (min(xs), min(ys), max(xs) + 1, max(ys) + 1)))
    return sorted(components, key=lambda item: item[1][0])


def alpha_profile_for_bbox(
    path: Path,
    bbox: tuple[int, int, int, int],
    *,
    rings: int = RING_COUNT,
    threshold: int = 16,
) -> list[tuple[int, int, int]]:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    x0, y0, x1, y1 = bbox
    profile: list[tuple[int, int, int]] = []
    for index in range(rings):
        y = round(y0 + (y1 - y0 - 1) * index / max(rings - 1, 1))
        xs = [x for x in range(x0, x1) if alpha.getpixel((x, y)) > threshold]
        if not xs:
            left, right = x0, x1 - 1
        else:
            left, right = min(xs), max(xs)
        profile.append((y, left, right))
    return profile


def build_leg_mesh(
    texture_path: Path,
    *,
    bbox: tuple[int, int, int, int] | None = None,
    target_height: float = 1.72,
    depth_ratio: float = 0.42,
) -> tuple[MeshData, tuple[int, int, int, int], dict[str, int], dict[str, float]]:
    image = Image.open(texture_path).convert("RGBA")
    width, height = image.size
    bbox = bbox or alpha_bbox(texture_path)
    x0, y0, x1, y1 = bbox
    bbox_h = max(y1 - y0, 1)
    scale = target_height / bbox_h
    image_center_x = width * 0.5
    center_y = (y0 + y1) * 0.5
    profile = alpha_profile_for_bbox(texture_path, bbox)

    vertices: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    ring_z: list[float] = []
    for y, left, right in profile:
        center_px = (left + right) * 0.5
        alpha_radius = (right - left) * 0.5 * scale
        # The source leg masks still include some skirt/cloth overlap. For a
        # retopo proxy, alpha gives the centerline and rough height, but the
        # loop radius must stay within plausible leg bounds.
        radius_x = max(0.045, min(alpha_radius, 0.115))
        radius_depth = max(0.035, min(radius_x * depth_ratio, 0.060))
        z = (center_y - y) * scale
        ring_z.append(z)
        for segment in range(RADIAL_SEGMENTS):
            theta = math.tau * segment / RADIAL_SEGMENTS
            px = center_px + math.cos(theta) * radius_x / scale
            x = (center_px - image_center_x) * scale + math.cos(theta) * radius_x
            depth = math.sin(theta) * radius_depth
            vertices.append((x, depth, z))
            uvs.append((max(0.0, min(1.0, px / width)), 1.0 - y / height))

    def vid(ring: int, segment: int) -> int:
        return ring * RADIAL_SEGMENTS + segment % RADIAL_SEGMENTS

    faces: list[tuple[int, int, int, int]] = []
    face_materials: list[int] = []
    for ring in range(RING_COUNT - 1):
        for segment in range(RADIAL_SEGMENTS):
            faces.append((vid(ring, segment), vid(ring, segment + 1), vid(ring + 1, segment + 1), vid(ring + 1, segment)))
            mid_theta = math.tau * (segment + 0.5) / RADIAL_SEGMENTS
            face_materials.append(0 if math.sin(mid_theta) >= -0.15 else 1)

    loop_rings = {
        "hip": 2,
        "knee": round((RING_COUNT - 1) * 0.48),
        "ankle": round((RING_COUNT - 1) * 0.88),
        "foot_socket": RING_COUNT - 2,
    }
    loop_world_z = {name: ring_z[index] for name, index in loop_rings.items()}
    return (
        MeshData(
            vertices=vertices,
            uvs=uvs,
            faces=faces,
            face_materials=face_materials,
            section_count=RING_COUNT,
            thickness=max((max(x for x, _, _ in vertices) - min(x for x, _, _ in vertices)), 0.0),
            bevel=0.0,
        ),
        bbox,
        loop_rings,
        loop_world_z,
    )


def build_leg_components(character_package: Path) -> list[LegComponent]:
    texture_path = character_package / "semantic_layer_v8" / "textures" / "legs.png"
    if not texture_path.exists():
        raise ValueError(f"Missing leg texture: {texture_path}")
    raw_components = alpha_components(texture_path)
    if len(raw_components) < 2:
        raise ValueError("Leg texture should contain at least two visible leg components")
    components: list[LegComponent] = []
    for component_id, side, (_, bbox) in zip(
        ("leg_L_retopo_proxy_candidate", "leg_R_retopo_proxy_candidate"),
        ("L", "R"),
        raw_components[:2],
        strict=True,
    ):
        mesh, bbox, loop_rings, loop_world_z = build_leg_mesh(texture_path, bbox=bbox)
        components.append(
            LegComponent(
                id=component_id,
                side=side,
                texture_path=texture_path,
                bbox=bbox,
                mesh=mesh,
                loop_rings=loop_rings,
                loop_world_z=loop_world_z,
            )
        )
    return components


def combined_summary(components: list[LegComponent]) -> dict[str, Any]:
    return {
        "component_count": len(components),
        "vertices": sum(len(component.mesh.vertices) for component in components),
        "uvs": sum(len(component.mesh.uvs) for component in components),
        "faces": sum(len(component.mesh.faces) for component in components),
        "ring_count": RING_COUNT,
        "radial_segments": RADIAL_SEGMENTS,
        "quad_faces_only": True,
        "components": [
            {
                "id": component.id,
                "side": component.side,
                "bbox": list(component.bbox),
                "loop_rings": component.loop_rings,
                "loop_world_z": component.loop_world_z,
                "texture": str(component.texture_path),
                **component.mesh.to_summary(),
            }
            for component in components
        ],
    }


def write_obj(path: Path, components: list[LegComponent]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    mtl_path = path.with_suffix(".mtl")
    lines = ["# YUNA semantic v9 leg quad-loop retopo proxy candidate", f"mtllib {mtl_path.name}"]
    vertex_offset = 0
    for component in components:
        lines.append(f"o {component.id}")
        for x, y, z in component.mesh.vertices:
            lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
        for u, v in component.mesh.uvs:
            lines.append(f"vt {u:.6f} {v:.6f}")
        current_material = None
        for face, material_index in zip(component.mesh.faces, component.mesh.face_materials, strict=True):
            material = f"leg_{component.side}_front_texture" if material_index == 0 else "leg_retopo_side_material"
            if material != current_material:
                lines.append(f"usemtl {material}")
                current_material = material
            refs = [f"{idx + 1 + vertex_offset}/{idx + 1 + vertex_offset}" for idx in face]
            lines.append("f " + " ".join(refs))
        vertex_offset += len(component.mesh.vertices)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    material_lines = []
    for component in components:
        material_lines.extend(
            [
                f"newmtl leg_{component.side}_front_texture",
                "Ka 1.000 1.000 1.000",
                "Kd 1.000 1.000 1.000",
                "Ks 0.050 0.050 0.050",
                "d 1.000",
                f"map_Kd {component.texture_path.name}",
                "",
            ]
        )
    material_lines.extend(
        [
            "newmtl leg_retopo_side_material",
            "Ka 0.080 0.072 0.078",
            "Kd 0.120 0.110 0.118",
            "Ks 0.050 0.050 0.060",
            "d 1.000",
        ]
    )
    mtl_path.write_text("\n".join(material_lines) + "\n", encoding="utf-8")
    return mtl_path


def blender_export_glb(glb_path: Path, components: list[LegComponent], repo_root: Path) -> dict[str, Any]:
    blender = find_blender()
    if blender is None:
        return {"status": "skipped_with_reason", "reason": "blender_not_found", "glb_exists": False}
    payload = [
        {
            "id": component.id,
            "side": component.side,
            "texture_path": str(component.texture_path),
            "vertices": component.mesh.vertices,
            "faces": component.mesh.faces,
            "uvs": component.mesh.uvs,
            "face_materials": component.mesh.face_materials,
            "loop_world_z": component.loop_world_z,
        }
        for component in components
    ]
    payload_json = json.dumps(payload)
    script = f"""
import bpy
import json

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

COMPONENTS = json.loads({payload_json!r})

side_mat = bpy.data.materials.new('leg_retopo_side_material')
side_mat.use_nodes = True
side_bsdf = side_mat.node_tree.nodes.get('Principled BSDF')
side_bsdf.inputs['Base Color'].default_value = (0.12, 0.11, 0.118, 1.0)
side_bsdf.inputs['Roughness'].default_value = 0.62

for item in COMPONENTS:
    front_mat = bpy.data.materials.new('leg_' + item['side'] + '_front_texture')
    front_mat.use_nodes = True
    front_mat.blend_method = 'BLEND'
    front_mat.show_transparent_back = True
    nodes = front_mat.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(item['texture_path'], check_existing=True)
    tex.extension = 'CLIP'
    front_mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    front_mat.node_tree.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    bsdf.inputs['Roughness'].default_value = 0.55

    mesh = bpy.data.meshes.new(item['id'] + '_mesh')
    mesh.from_pydata([tuple(v) for v in item['vertices']], [], [tuple(f) for f in item['faces']])
    mesh.update()
    uv_layer = mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = item['uvs'][vertex_index]
    obj = bpy.data.objects.new(item['id'], mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(front_mat)
    obj.data.materials.append(side_mat)
    obj['semantic_part'] = 'legs'
    obj['actuator'] = 'leg_quad_loop_retopo_proxy_v0'
    obj['candidate_only'] = True
    obj['replace_in_beauty_glb'] = False
    obj['quad_loop_proxy'] = True
    obj['side'] = item['side']
    for idx, poly in enumerate(obj.data.polygons):
        poly.material_index = item['face_materials'][idx]

    x_offset = -0.24 if item['side'] == 'L' else 0.24
    for loop_name in ['knee', 'ankle']:
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(x_offset, 0.0, item['loop_world_z'][loop_name]))
        marker = bpy.context.object
        marker.name = 'leg_' + item['side'] + '_' + loop_name + '_loop'
        marker.empty_display_size = 0.08
        marker['semantic_loop'] = loop_name
        marker['semantic_part'] = 'legs'
        marker['actuator'] = 'leg_quad_loop_retopo_proxy_v0'

bpy.ops.wm.save_as_mainfile(filepath=r'{glb_path.with_suffix('.blend')}')
bpy.ops.export_scene.gltf(
    filepath=r'{glb_path}',
    export_format='GLB',
    export_texcoords=True,
    export_normals=True,
    export_materials='EXPORT'
)
"""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(script)
        tmp_path = tmp.name
    result = subprocess.run(
        [blender, "--background", "--python", tmp_path],
        cwd=str(repo_root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {
        "status": "ok" if result.returncode == 0 and glb_path.exists() else "failed",
        "blender": blender,
        "exit_code": result.returncode,
        "glb_exists": glb_path.exists(),
        "glb_bytes": glb_path.stat().st_size if glb_path.exists() else 0,
        "blend_exists": glb_path.with_suffix(".blend").exists(),
        "blend_path": display_path(glb_path.with_suffix(".blend"), repo_root),
        "log_tail": result.stdout.splitlines()[-80:],
    }


def build_spec(paths: ActuatorPaths, components: list[LegComponent], source_decisions: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "route": "semantic_layer_v9_leg_quad_loop_retopo_proxy_v0",
        "source_route": "semantic_layer_v9_candidate_spec_only",
        "baseline": "semantic_layer_v8_beauty_main_debug_cage_split",
        "boundary": "Continuous leg quad-loop proxy only. It does not replace v8 beauty leg panels until deformation validation passes.",
        "part": {
            "id": "legs",
            "category": "body",
            "generator": "leg_quad_loop_retopo_proxy_v0",
            "replace_in_beauty_glb": False,
            "independent_objects": True,
            "candidate_only": True,
            "loop_markers": ["leg_L_knee_loop", "leg_L_ankle_loop", "leg_R_knee_loop", "leg_R_ankle_loop"],
        },
        "source_decisions": source_decisions,
        "mesh": combined_summary(components),
        "exports": {
            "obj": display_path(paths.obj_path, paths.repo_root),
            "glb": display_path(paths.glb_path, paths.repo_root),
            "report": display_path(paths.report_path, paths.repo_root),
        },
    }


@register("leg_quad_loop_retopo_proxy_v0")
def run_leg_quad_loop_retopo_proxy(paths: ActuatorPaths) -> ActuatorResult:
    candidate_spec = load_json(paths.character_package / "semantic_layer_v9_candidate" / "specs" / "yuna_semantic_layer_v9_candidate.json")
    decisions = {item["part_id"]: item for item in candidate_spec.get("decisions", [])}
    source_decisions = [decisions[item] for item in ("legs", "leg_L_visual_panel", "leg_R_visual_panel") if item in decisions]
    warnings: list[str] = []
    errors: list[str] = []
    if not source_decisions:
        errors.append("v9 candidate does not request leg_quad_loop_retopo_proxy")
    if any(item.get("proposed_generator") != "leg_quad_loop_retopo_proxy" for item in source_decisions):
        errors.append("v9 candidate has inconsistent leg retopo proposals")

    if errors:
        result = ActuatorResult(
            actuator=ACTUATOR_NAME,
            status="failed",
            part_id=PART_ID,
            decision_source=display_path(paths.character_package / "semantic_layer_v9_candidate" / "specs" / "yuna_semantic_layer_v9_candidate.json", paths.repo_root),
            generated_files={},
            mesh_summary={},
            validation={},
            warnings=warnings,
            errors=errors,
        )
        write_json(paths.report_path, {"created_at": datetime.now(timezone.utc).isoformat(), "route": "semantic_layer_v9_leg_quad_loop_retopo_proxy_v0", **result.to_dict()})
        return result

    components = build_leg_components(paths.character_package)
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    paths.spec_path.parent.mkdir(parents=True, exist_ok=True)
    paths.obj_path.parent.mkdir(parents=True, exist_ok=True)
    write_obj(paths.obj_path, components)
    glb_report = blender_export_glb(paths.glb_path, components, paths.repo_root)
    if glb_report.get("status") != "ok":
        warnings.append("GLB export did not complete; see validation.blender_glb_export")

    generated_files = {
        "spec": display_path(paths.spec_path, paths.repo_root),
        "obj": display_path(paths.obj_path, paths.repo_root),
        "mtl": display_path(paths.obj_path.with_suffix(".mtl"), paths.repo_root),
        "glb": display_path(paths.glb_path, paths.repo_root),
        "blend": display_path(paths.glb_path.with_suffix(".blend"), paths.repo_root),
        "report": display_path(paths.report_path, paths.repo_root),
    }
    validation = {
        "independent_objects": True,
        "has_quad_loop_topology": all(len(component.mesh.faces) == (RING_COUNT - 1) * RADIAL_SEGMENTS for component in components),
        "quad_faces_only": True,
        "has_knee_ankle_loop_metadata": True,
        "has_uvs": all(len(component.mesh.uvs) == len(component.mesh.vertices) for component in components),
        "replace_in_beauty_glb": False,
        "deformation_test_status": "not_run_requires_skinning_stage",
        "obj": file_record(paths.obj_path),
        "glb": file_record(paths.glb_path),
        "blender_glb_export": glb_report,
    }
    result = ActuatorResult(
        actuator=ACTUATOR_NAME,
        status="generated_with_warnings",
        part_id=PART_ID,
        decision_source=display_path(paths.character_package / "semantic_layer_v9_candidate" / "filter_report.json", paths.repo_root),
        generated_files=generated_files,
        mesh_summary=combined_summary(components),
        validation=validation,
        warnings=warnings
        + [
            "v0 creates a quad-loop retopo proxy, not final production leg topology.",
            "knee/ankle loops are marker metadata only; skinning and weight tests are not run in this actuator.",
            "v8 beauty leg panels remain active until deformation validation passes.",
        ],
        errors=[],
    )
    contract_errors = validate_leg_candidate_report({"part_id": PART_ID, **result.to_dict()})
    if contract_errors:
        result.status = "failed"
        result.errors.extend(contract_errors)

    write_json(paths.spec_path, build_spec(paths, components, source_decisions))
    write_json(paths.report_path, {"created_at": datetime.now(timezone.utc).isoformat(), "route": "semantic_layer_v9_leg_quad_loop_retopo_proxy_v0", **result.to_dict()})
    return result
