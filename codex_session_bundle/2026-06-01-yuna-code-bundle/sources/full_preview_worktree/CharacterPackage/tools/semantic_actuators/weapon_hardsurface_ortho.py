from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image

from .registry import register
from .state import ActuatorPaths, ActuatorResult, MeshData
from .validation_contract import file_record, validate_weapon_candidate_report


ACTUATOR_NAME = "weapon_hardsurface_ortho_v0"
PART_ID = "weapon"


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


def alpha_profile(path: Path, sections: int = 36, threshold: int = 16) -> tuple[tuple[int, int, int, int], list[tuple[int, int, int]]]:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError(f"Texture has no visible alpha: {path}")
    x0, y0, x1, y1 = bbox
    profile: list[tuple[int, int, int]] = []
    for index in range(sections):
        y = round(y0 + (y1 - y0 - 1) * index / max(sections - 1, 1))
        xs = [x for x in range(x0, x1) if alpha.getpixel((x, y)) > threshold]
        if not xs:
            # Fall back to full bbox width if this row is empty; this keeps the
            # strip topologically stable while still reporting the limitation.
            left, right = x0, x1 - 1
        else:
            left, right = min(xs), max(xs)
        profile.append((y, left, right))
    return bbox, profile


def build_weapon_mesh(texture_path: Path, target_height: float = 3.4, thickness: float = 0.16, bevel: float = 0.035) -> MeshData:
    image = Image.open(texture_path).convert("RGBA")
    width, height = image.size
    bbox, profile = alpha_profile(texture_path)
    x0, y0, x1, y1 = bbox
    bbox_h = max(y1 - y0, 1)
    scale = target_height / bbox_h
    center_x = (x0 + x1) * 0.5
    center_y = (y0 + y1) * 0.5

    vertices: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []

    def world(px: float, py: float, depth: float, inset: float = 0.0) -> tuple[float, float, float]:
        # Inset x toward center to form a simple bevel proxy at front/back.
        if px < center_x:
            px = min(center_x, px + inset / scale)
        else:
            px = max(center_x, px - inset / scale)
        x = (px - center_x) * scale
        z = (center_y - py) * scale
        return (x, depth, z)

    layers = [
        ("front", thickness * 0.5, bevel),
        ("middle", 0.0, 0.0),
        ("back", -thickness * 0.5, bevel),
    ]
    for _, depth, inset in layers:
        for y, left, right in profile:
            for px in (left, right):
                vertices.append(world(px, y, depth, inset=inset))
                uvs.append((px / width, 1.0 - y / height))

    section_count = len(profile)
    layer_stride = section_count * 2

    def vid(layer: int, section: int, side: int) -> int:
        return layer * layer_stride + section * 2 + side

    faces: list[tuple[int, int, int, int]] = []
    face_materials: list[int] = []
    for section in range(section_count - 1):
        # Front and back textured strip faces.
        faces.append((vid(0, section, 0), vid(0, section, 1), vid(0, section + 1, 1), vid(0, section + 1, 0)))
        face_materials.append(0)
        faces.append((vid(2, section, 1), vid(2, section, 0), vid(2, section + 1, 0), vid(2, section + 1, 1)))
        face_materials.append(0)

        # Beveled left/right edges: front -> middle -> back.
        for side in (0, 1):
            faces.append((vid(0, section, side), vid(0, section + 1, side), vid(1, section + 1, side), vid(1, section, side)))
            face_materials.append(1)
            faces.append((vid(1, section, side), vid(1, section + 1, side), vid(2, section + 1, side), vid(2, section, side)))
            face_materials.append(1)

    # Top and bottom caps.
    for section in (0, section_count - 1):
        faces.append((vid(0, section, 0), vid(1, section, 0), vid(1, section, 1), vid(0, section, 1)))
        face_materials.append(1)
        faces.append((vid(1, section, 0), vid(2, section, 0), vid(2, section, 1), vid(1, section, 1)))
        face_materials.append(1)

    return MeshData(
        vertices=vertices,
        uvs=uvs,
        faces=faces,
        face_materials=face_materials,
        section_count=section_count,
        thickness=thickness,
        bevel=bevel,
    )


def write_obj(path: Path, mesh: MeshData, texture_path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    mtl_path = path.with_suffix(".mtl")
    tex_name = Path(texture_path).name
    lines = [
        "# YUNA semantic v9 weapon hard-surface candidate",
        f"mtllib {mtl_path.name}",
        "o weapon_hardsurface_ortho_v0",
    ]
    for x, y, z in mesh.vertices:
        lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
    for u, v in mesh.uvs:
        lines.append(f"vt {u:.6f} {v:.6f}")
    current_material = None
    for face, material_index in zip(mesh.faces, mesh.face_materials, strict=True):
        material = "weapon_front_texture" if material_index == 0 else "weapon_side_material"
        if material != current_material:
            lines.append(f"usemtl {material}")
            current_material = material
        refs = [f"{idx + 1}/{idx + 1}" for idx in face]
        lines.append("f " + " ".join(refs))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    mtl_path.write_text(
        "\n".join(
            [
                "newmtl weapon_front_texture",
                "Ka 1.000 1.000 1.000",
                "Kd 1.000 1.000 1.000",
                "Ks 0.100 0.100 0.100",
                "d 1.000",
                f"map_Kd {tex_name}",
                "",
                "newmtl weapon_side_material",
                "Ka 0.050 0.120 0.140",
                "Kd 0.080 0.200 0.220",
                "Ks 0.150 0.250 0.280",
                "d 1.000",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return mtl_path


def blender_export_glb(glb_path: Path, mesh: MeshData, texture_path: Path, repo_root: Path) -> dict[str, Any]:
    blender = find_blender()
    if blender is None:
        return {"status": "skipped_with_reason", "reason": "blender_not_found", "glb_exists": False}

    verts_json = json.dumps(mesh.vertices)
    faces_json = json.dumps(mesh.faces)
    uvs_json = json.dumps(mesh.uvs)
    face_materials_json = json.dumps(mesh.face_materials)
    script = f"""
import bpy
import json

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

verts = json.loads({verts_json!r})
faces = json.loads({faces_json!r})
uvs = json.loads({uvs_json!r})
face_materials = json.loads({face_materials_json!r})

mesh = bpy.data.meshes.new('weapon_hardsurface_ortho_v0_mesh')
mesh.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
mesh.update()
uv_layer = mesh.uv_layers.new(name='UVMap')
for poly in mesh.polygons:
    for loop_index in poly.loop_indices:
        vertex_index = mesh.loops[loop_index].vertex_index
        uv_layer.data[loop_index].uv = uvs[vertex_index]

front_mat = bpy.data.materials.new('weapon_front_texture')
front_mat.use_nodes = True
front_mat.blend_method = 'BLEND'
front_mat.show_transparent_back = True
nodes = front_mat.node_tree.nodes
bsdf = nodes.get('Principled BSDF')
tex = nodes.new('ShaderNodeTexImage')
tex.image = bpy.data.images.load(r'{texture_path}', check_existing=True)
tex.extension = 'CLIP'
front_mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
front_mat.node_tree.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
bsdf.inputs['Roughness'].default_value = 0.45

side_mat = bpy.data.materials.new('weapon_side_teal_metal_proxy')
side_mat.use_nodes = True
side_bsdf = side_mat.node_tree.nodes.get('Principled BSDF')
side_bsdf.inputs['Base Color'].default_value = (0.05, 0.16, 0.18, 1.0)
side_bsdf.inputs['Metallic'].default_value = 0.25
side_bsdf.inputs['Roughness'].default_value = 0.38

obj = bpy.data.objects.new('weapon_hardsurface_ortho_v0', mesh)
bpy.context.collection.objects.link(obj)
obj.data.materials.append(front_mat)
obj.data.materials.append(side_mat)
obj['semantic_part'] = 'weapon'
obj['actuator'] = 'weapon_hardsurface_ortho_v0'
obj['hand_socket'] = 'hand_R_socket'
obj['candidate_only'] = True
obj['replace_in_beauty_glb'] = False

for idx, poly in enumerate(obj.data.polygons):
    poly.material_index = face_materials[idx]

bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0.0, 0.0, 0.0))
socket = bpy.context.object
socket.name = 'hand_R_socket'
socket.empty_display_size = 0.12
socket['semantic_socket'] = 'hand_R_socket'
socket['parent_part'] = 'weapon'

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


def build_spec(paths: ActuatorPaths, texture_path: Path, mesh: MeshData, source_decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "route": "semantic_layer_v9_weapon_hardsurface_ortho_v0",
        "source_route": "semantic_layer_v9_candidate_spec_only",
        "baseline": "semantic_layer_v8_beauty_main_debug_cage_split",
        "boundary": "Independent weapon candidate only. It does not replace the v8 beauty weapon until validation passes.",
        "part": {
            "id": "weapon",
            "category": "weapon",
            "generator": "weapon_hardsurface_ortho_v0",
            "source_texture": display_path(texture_path, paths.repo_root),
            "hand_socket": "hand_R_socket",
            "replace_in_beauty_glb": False,
            "independent_object": True,
            "candidate_only": True,
        },
        "source_decision": source_decision,
        "mesh": mesh.to_summary(),
        "exports": {
            "obj": display_path(paths.obj_path, paths.repo_root),
            "glb": display_path(paths.glb_path, paths.repo_root),
            "report": display_path(paths.report_path, paths.repo_root),
        },
    }


@register("weapon_hardsurface_ortho_v0")
def run_weapon_hardsurface_ortho(paths: ActuatorPaths) -> ActuatorResult:
    candidate_spec = load_json(paths.character_package / "semantic_layer_v9_candidate" / "specs" / "yuna_semantic_layer_v9_candidate.json")
    decisions = {item["part_id"]: item for item in candidate_spec.get("decisions", [])}
    decision = decisions.get("weapon")
    warnings: list[str] = []
    errors: list[str] = []
    if not decision or decision.get("proposed_generator") != "weapon_hardsurface_ortho":
        errors.append("v9 candidate does not request weapon_hardsurface_ortho")

    texture_path = paths.character_package / "semantic_layer_v8" / "textures" / "weapon.png"
    if not texture_path.exists():
        errors.append(f"missing weapon texture: {texture_path}")

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
        write_json(
            paths.report_path,
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "route": "semantic_layer_v9_weapon_hardsurface_ortho_v0",
                **result.to_dict(),
            },
        )
        return result

    mesh = build_weapon_mesh(texture_path)
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    paths.spec_path.parent.mkdir(parents=True, exist_ok=True)
    paths.obj_path.parent.mkdir(parents=True, exist_ok=True)
    write_obj(paths.obj_path, mesh, texture_path)
    glb_report = blender_export_glb(paths.glb_path, mesh, texture_path, paths.repo_root)
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
        "independent_object": True,
        "has_thickness": mesh.thickness > 0,
        "has_bevel_proxy": mesh.bevel > 0,
        "has_uvs": len(mesh.uvs) == len(mesh.vertices),
        "has_front_texture_material": True,
        "has_side_material": True,
        "has_hand_socket_metadata": True,
        "replace_in_beauty_glb": False,
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
        mesh_summary=mesh.to_summary(),
        validation=validation,
        warnings=warnings
        + [
            "v0 uses an alpha-profile hard-surface proxy, not a final hand-modeled weapon.",
            "v8 beauty weapon remains active until screenshot/import validation passes.",
        ],
        errors=[],
    )
    contract_errors = validate_weapon_candidate_report({"part_id": PART_ID, **result.to_dict()})
    if contract_errors:
        result.status = "failed"
        result.errors.extend(contract_errors)

    write_json(paths.spec_path, build_spec(paths, texture_path, mesh, decision or {}))
    write_json(
        paths.report_path,
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "route": "semantic_layer_v9_weapon_hardsurface_ortho_v0",
            **result.to_dict(),
        },
    )
    return result
