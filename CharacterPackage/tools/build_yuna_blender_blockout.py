#!/usr/bin/env python3
"""Build a Blender DCC blockout for YUNA and export FBX/GLB.

Run with:
  blender --background --python CharacterPackage/tools/build_yuna_blender_blockout.py

This creates a modeling blockout with reference planes and proxy geometry.
It is not a final skinned production character.
"""

from __future__ import annotations

from pathlib import Path
import math

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
HEIGHT_M = 1.68


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def mat(name: str, color: tuple[float, float, float, float], alpha_blend: bool = False):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = 0.72
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Alpha"].default_value = color[3]
    if alpha_blend or color[3] < 1:
        material.blend_method = "BLEND"
        material.use_screen_refraction = True
        material.show_transparent_back = True
    return material


MAT_SKIN = mat("skin_soft_proxy", (0.94, 0.78, 0.70, 1.0))
MAT_WHITE = mat("white_fabric_stockings", (0.88, 0.92, 0.94, 1.0))
MAT_BLACK = mat("black_coat_armor", (0.02, 0.025, 0.035, 1.0))
MAT_CYAN = mat("teal_resonance_energy", (0.05, 0.85, 0.95, 1.0))
MAT_HAIR = mat("silver_cyan_hair", (0.78, 0.91, 0.96, 1.0))
MAT_GOLD = mat("warm_gold_trim", (0.95, 0.66, 0.25, 1.0))
MAT_MANTLE = mat("transparent_mantle_proxy", (0.25, 0.78, 0.92, 0.32), True)
MAT_REF = mat("reference_plane_dim", (1.0, 1.0, 1.0, 0.42), True)


def image_material(name: str, image_path: Path):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.blend_method = "BLEND"
    material.use_screen_refraction = True
    material.show_transparent_back = True

    nodes = material.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    image = bpy.data.images.load(str(image_path))
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.extension = "CLIP"
    material.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    material.node_tree.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = 0.78
    return material


def vertical_plane(name: str, image_path: Path, center: tuple[float, float, float], width: float, height: float, rotation_z: float = 0.0):
    mesh = bpy.data.meshes.new(name + "_mesh")
    verts = [(-width / 2, 0, 0), (width / 2, 0, 0), (width / 2, 0, height), (-width / 2, 0, height)]
    faces = [(0, 1, 2, 3)]
    uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for loop, uv in zip(mesh.polygons[0].loop_indices, uvs):
        uv_layer.data[loop].uv = uv

    obj = bpy.data.objects.new(name, mesh)
    obj.location = center
    obj.rotation_euler[2] = rotation_z
    obj.data.materials.append(image_material(name + "_mat", image_path))
    bpy.context.collection.objects.link(obj)
    return obj


def sphere(name: str, loc, scale, material, segments: int = 32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=16, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    return obj


def cube(name: str, loc, scale, material):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    return obj


def cyl(name: str, loc, radius: float, depth: float, material, rotation=(0, 0, 0), vertices: int = 18):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj


def cone(name: str, loc, radius1: float, radius2: float, depth: float, material, rotation=(0, 0, 0), vertices: int = 18):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj


def add_proxy_body() -> None:
    # Body proportions intentionally stay simple: a DCC blockout to align references.
    sphere("head_proxy", (0, 0, 1.52), (0.13, 0.105, 0.145), MAT_SKIN)
    cyl("neck_proxy", (0, 0, 1.36), 0.045, 0.12, MAT_SKIN)
    sphere("torso_proxy", (0, 0, 1.10), (0.19, 0.115, 0.34), MAT_BLACK)
    sphere("pelvis_proxy", (0, 0, 0.78), (0.17, 0.11, 0.13), MAT_WHITE)

    for side in [-1, 1]:
        cyl(f"upper_arm_{side}", (0.22 * side, 0, 1.15), 0.035, 0.36, MAT_BLACK, rotation=(math.radians(8), math.radians(18 * side), 0))
        cyl(f"forearm_{side}", (0.27 * side, 0, 0.91), 0.03, 0.34, MAT_BLACK, rotation=(math.radians(8), math.radians(8 * side), 0))
        sphere(f"hand_{side}", (0.30 * side, 0, 0.72), (0.035, 0.028, 0.05), MAT_SKIN, 16)
        cyl(f"thigh_{side}", (0.07 * side, 0, 0.50), 0.045, 0.48, MAT_WHITE)
        cyl(f"shin_{side}", (0.08 * side, 0, 0.21), 0.037, 0.42, MAT_WHITE)
        cube(f"boot_{side}", (0.09 * side, -0.015, 0.025), (0.06, 0.11, 0.035), MAT_BLACK)

    sphere("resonance_core_proxy", (0.0, -0.09, 1.23), (0.042, 0.012, 0.058), MAT_CYAN, 16)

    # Hair volume shells.
    sphere("hair_back_volume", (0.0, 0.055, 1.40), (0.18, 0.085, 0.34), MAT_HAIR)
    for side in [-1, 1]:
        cyl(f"cyan_hair_tail_{side}", (0.25 * side, 0.055, 1.06), 0.025, 0.68, MAT_CYAN, rotation=(math.radians(18), math.radians(16 * side), 0), vertices=12)

    # Coat and translucent mantle planes.
    for side in [-1, 1]:
        cube(f"coat_panel_{side}", (0.17 * side, 0.04, 0.72), (0.07, 0.018, 0.45), MAT_BLACK)
        cube(f"transparent_mantle_{side}", (0.28 * side, 0.075, 0.80), (0.10, 0.012, 0.56), MAT_MANTLE)

    # Weapon proxy along character left side.
    cyl("weapon_handle_proxy", (-0.36, -0.03, 0.74), 0.018, 0.34, MAT_BLACK, rotation=(0, math.radians(-18), 0), vertices=12)
    cone("weapon_blade_proxy", (-0.48, -0.05, 0.35), 0.045, 0.006, 0.85, MAT_CYAN, rotation=(0, math.radians(-18), 0), vertices=4)
    sphere("weapon_core_proxy", (-0.38, -0.045, 0.61), (0.045, 0.018, 0.045), MAT_GOLD, 12)


def add_armature() -> None:
    bpy.ops.object.armature_add(location=(0, 0, 0))
    arm = bpy.context.object
    arm.name = "YUNA_humanoid_reference_armature"
    bpy.ops.object.mode_set(mode="EDIT")
    bones = arm.data.edit_bones
    root = bones[0]
    root.name = "Hips"
    root.head = (0, 0, 0.78)
    root.tail = (0, 0, 1.02)

    def bone(name, head, tail, parent=None):
        b = bones.new(name)
        b.head = head
        b.tail = tail
        if parent:
            b.parent = parent
        return b

    spine = bone("Spine", (0, 0, 1.02), (0, 0, 1.30), root)
    chest = bone("Chest", (0, 0, 1.30), (0, 0, 1.42), spine)
    neck = bone("Neck", (0, 0, 1.42), (0, 0, 1.50), chest)
    bone("Head", (0, 0, 1.50), (0, 0, 1.68), neck)
    for side, label in [(-1, "L"), (1, "R")]:
        upper_arm = bone(f"{label}_UpperArm", (0.12 * side, 0, 1.32), (0.31 * side, 0, 1.08), chest)
        lower_arm = bone(f"{label}_LowerArm", (0.31 * side, 0, 1.08), (0.34 * side, 0, 0.84), upper_arm)
        bone(f"{label}_Hand", (0.34 * side, 0, 0.84), (0.35 * side, 0, 0.74), lower_arm)
        upper_leg = bone(f"{label}_UpperLeg", (0.06 * side, 0, 0.76), (0.08 * side, 0, 0.42), root)
        lower_leg = bone(f"{label}_LowerLeg", (0.08 * side, 0, 0.42), (0.09 * side, 0, 0.12), upper_leg)
        bone(f"{label}_Foot", (0.09 * side, 0, 0.12), (0.09 * side, -0.12, 0.02), lower_leg)

    bpy.ops.object.mode_set(mode="OBJECT")
    arm.data.display_type = "STICK"
    arm.show_in_front = True


def add_references() -> None:
    front = ROOT / "refs/front_rgba/yuna_front_rgba.png"
    side = ROOT / "refs/ai_turnarounds/cutouts/yuna_left_side.png"
    back = ROOT / "refs/ai_turnarounds/cutouts/yuna_back.png"
    face = ROOT / "refs/ai_turnarounds/cutouts/yuna_face_expression_sheet.png"
    weapon = ROOT / "refs/ai_turnarounds/cutouts/yuna_weapon_orthographic.png"

    vertical_plane("ref_front_rgba", front, (0, 0.34, 0), 1.12, HEIGHT_M)
    vertical_plane("ref_back_inferred", back, (1.15, 0.34, 0), 1.12, HEIGHT_M)
    vertical_plane("ref_left_side_inferred", side, (-1.15, 0.34, 0), 0.74, HEIGHT_M)
    vertical_plane("ref_face_sheet_inferred", face, (0, 1.02, 1.02), 0.92, 0.62)
    vertical_plane("ref_weapon_orthographic", weapon, (0, 1.02, 0.22), 1.05, 0.38)


def add_camera_and_lights() -> None:
    bpy.ops.object.light_add(type="AREA", location=(0, -3.5, 3.2))
    light = bpy.context.object
    light.name = "softbox_front"
    light.data.energy = 450
    light.data.size = 4

    bpy.ops.object.camera_add(location=(0, -4.3, 1.05), rotation=(math.radians(78), 0, 0))
    camera = bpy.context.object
    bpy.context.scene.camera = camera
    camera.name = "front_review_camera"
    camera.data.lens = 45


def add_floor() -> None:
    bpy.ops.mesh.primitive_grid_add if False else None
    # Simple floor grid via mesh lines is not necessary for export; add a thin base plane.
    cube("scale_floor_proxy_1m", (0, 0, -0.006), (0.5, 0.5, 0.002), mat("floor_dark_reference", (0.02, 0.04, 0.05, 0.36), True))


def export_outputs() -> None:
    blend_path = ROOT / "dcc/blender/yuna_dcc_blockout.blend"
    glb_path = ROOT / "web/yuna_dcc_blockout.glb"
    fbx_path = ROOT / "rig/yuna_dcc_blockout.fbx"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path),
        export_format="GLB",
        export_texcoords=True,
        export_normals=True,
        export_animations=True,
        use_visible=True,
    )
    bpy.ops.export_scene.fbx(
        filepath=str(fbx_path),
        use_selection=False,
        add_leaf_bones=False,
        bake_anim=False,
        path_mode="COPY",
        embed_textures=True,
    )


def main() -> None:
    clear_scene()
    add_references()
    add_proxy_body()
    add_armature()
    add_floor()
    add_camera_and_lights()
    export_outputs()


if __name__ == "__main__":
    main()
