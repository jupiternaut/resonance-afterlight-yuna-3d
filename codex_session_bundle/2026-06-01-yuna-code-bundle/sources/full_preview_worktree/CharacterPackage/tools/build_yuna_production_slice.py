#!/usr/bin/env python3
"""Build an automated production-slice asset for YUNA.

This is a vertical slice of the game-asset pipeline: clean named mesh parts,
UVs, PBR material slots, an armature, basic skin weights, facial shape keys,
LOD objects, FBX/GLB exports, and QA metadata. It is not a replacement for a
hand-sculpted final character pass.
"""

from __future__ import annotations

from pathlib import Path
import json
import math
import shutil

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
HEIGHT_M = 1.68
BONE_NAMES = [
    "Hips",
    "Spine",
    "Chest",
    "Neck",
    "Head",
    "LeftUpperArm",
    "LeftLowerArm",
    "LeftHand",
    "RightUpperArm",
    "RightLowerArm",
    "RightHand",
    "LeftUpperLeg",
    "LeftLowerLeg",
    "LeftFoot",
    "LeftToes",
    "RightUpperLeg",
    "RightLowerLeg",
    "RightFoot",
    "RightToes",
    "HairRoot",
    "Mantle_L",
    "Mantle_R",
    "Weapon",
]
FACE_SHAPE_KEYS = [
    "Blink_L",
    "Blink_R",
    "Smile",
    "Frown",
    "Brow_Up",
    "Brow_Down",
    "Jaw_Open",
    "Mouth_A",
    "Mouth_E",
    "Mouth_O",
    "Mouth_M",
    "Mouth_FV",
]


def ensure_dirs() -> None:
    for relative in [
        "dcc/blender",
        "rig",
        "web",
        "unity/prefabs",
        "textures/export_unity_urp",
        "textures/export_gltf_web",
        "qa/turntable",
        "qa/unity",
    ]:
        (ROOT / relative).mkdir(parents=True, exist_ok=True)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def pbr_material(
    name: str,
    base: tuple[float, float, float, float],
    metallic: float = 0.0,
    roughness: float = 0.58,
    emission: tuple[float, float, float] | None = None,
    alpha: float | None = None,
) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = base
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Alpha"].default_value = alpha if alpha is not None else base[3]
        if emission and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (emission[0], emission[1], emission[2], 1.0)
        if emission and "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 1.6
    if base[3] < 1.0 or alpha is not None:
        material.blend_method = "BLEND"
        material.show_transparent_back = True
        material.use_screen_refraction = True
    return material


MAT_SKIN = pbr_material("YUNA_PBR_skin_soft", (0.96, 0.79, 0.72, 1), 0.0, 0.48)
MAT_HAIR = pbr_material("YUNA_PBR_silver_cyan_hair", (0.82, 0.93, 0.98, 1), 0.0, 0.36)
MAT_HAIR_TIP = pbr_material("YUNA_PBR_teal_hair_gradient", (0.18, 0.88, 0.96, 1), 0.0, 0.28, (0.05, 0.7, 0.9))
MAT_BLACK = pbr_material("YUNA_PBR_black_armor_fabric", (0.018, 0.024, 0.033, 1), 0.22, 0.42)
MAT_WHITE = pbr_material("YUNA_PBR_white_fabric_stocking", (0.88, 0.92, 0.95, 1), 0.0, 0.55)
MAT_METAL = pbr_material("YUNA_PBR_dark_metal_trim", (0.12, 0.14, 0.16, 1), 0.78, 0.34)
MAT_GOLD = pbr_material("YUNA_PBR_warm_gold_trim", (0.98, 0.67, 0.28, 1), 0.55, 0.29)
MAT_CYAN = pbr_material("YUNA_PBR_teal_resonance_emissive", (0.06, 0.92, 1.0, 1), 0.0, 0.22, (0.05, 0.9, 1.0))
MAT_MANTLE = pbr_material("YUNA_PBR_translucent_mantle", (0.40, 0.86, 0.98, 0.34), 0.0, 0.25, (0.1, 0.45, 0.6), 0.34)
MAT_FACE = pbr_material("YUNA_PBR_face_lines", (0.02, 0.035, 0.055, 1), 0.0, 0.45)


def make_texture(path: Path, kind: str, size: int = 1024) -> None:
    image = bpy.data.images.new(path.stem, width=size, height=size, alpha=True)
    pixels: list[float] = []
    for y in range(size):
        v = y / max(size - 1, 1)
        for x in range(size):
            u = x / max(size - 1, 1)
            if kind == "base":
                stripe = 0.05 if int(u * 8) % 2 == 0 else 0.0
                r = 0.08 + 0.78 * (u > 0.52) + stripe
                g = 0.10 + 0.78 * (u > 0.52) + 0.08 * v
                b = 0.13 + 0.80 * (u > 0.52) + 0.12 * v
                a = 1.0
            elif kind == "normal":
                r, g, b, a = 0.5, 0.5, 1.0, 1.0
            elif kind == "urp_mask":
                metallic = 0.15 + 0.55 * (u > 0.72)
                occlusion = 0.82 + 0.12 * v
                smoothness = 0.55 + 0.30 * (u > 0.72)
                r, g, b, a = metallic, occlusion, 0.0, smoothness
            elif kind == "gltf_mr":
                roughness = 0.68 - 0.22 * (u > 0.72)
                metallic = 0.15 + 0.55 * (u > 0.72)
                r, g, b, a = 1.0, roughness, metallic, 1.0
            elif kind == "emission":
                band = 1.0 if abs(v - 0.5) < 0.035 or abs(u - 0.18) < 0.018 else 0.0
                r, g, b, a = 0.02 * band, 0.82 * band, 1.0 * band, band
            else:
                r, g, b, a = 1.0, 1.0, 1.0, 1.0
            pixels.extend((r, g, b, a))
    image.pixels = pixels
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()


def create_texture_outputs() -> None:
    unity = ROOT / "textures/export_unity_urp"
    gltf = ROOT / "textures/export_gltf_web"
    make_texture(unity / "yuna_urp_basecolor.png", "base")
    make_texture(unity / "yuna_urp_mask_metallic_occlusion_smoothness.png", "urp_mask")
    make_texture(unity / "yuna_urp_normal.png", "normal")
    make_texture(unity / "yuna_urp_emission.png", "emission")
    make_texture(gltf / "yuna_gltf_basecolor.png", "base")
    make_texture(gltf / "yuna_gltf_metallic_roughness.png", "gltf_mr")
    make_texture(gltf / "yuna_gltf_normal.png", "normal")
    make_texture(gltf / "yuna_gltf_emission.png", "emission")


def shade_and_uv(obj: bpy.types.Object) -> None:
    if obj.type != "MESH":
        return
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.shade_smooth()
    except RuntimeError:
        pass
    if not obj.data.uv_layers:
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.018)
        bpy.ops.object.mode_set(mode="OBJECT")
    weighted = obj.modifiers.new("weighted_normal_game_ready", "WEIGHTED_NORMAL")
    weighted.keep_sharp = True


def add_sphere(name: str, loc, scale, material, segments: int = 32, rings: int = 16) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    shade_and_uv(obj)
    return obj


def add_cube(name: str, loc, scale, material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    shade_and_uv(obj)
    return obj


def add_cylinder_between(
    name: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    radius: float,
    material,
    vertices: int = 20,
) -> bpy.types.Object:
    a = Vector(start)
    b = Vector(end)
    mid = (a + b) * 0.5
    length = (b - a).length
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=length, location=mid)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(material)
    shade_and_uv(obj)
    return obj


def add_plane_mesh(name: str, verts: list[tuple[float, float, float]], faces: list[tuple[int, ...]], material) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        coords = [(0, 0), (1, 0), (1, 1), (0, 1)]
        for loop_index, uv_coord in zip(poly.loop_indices, coords):
            uv.data[loop_index].uv = uv_coord
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def make_armature() -> bpy.types.Object:
    bpy.ops.object.armature_add(location=(0, 0, 0))
    arm = bpy.context.object
    arm.name = "YUNA_Production_Armature"
    arm.data.name = "YUNA_Production_Humanoid_Skeleton"
    bpy.ops.object.mode_set(mode="EDIT")
    bones = arm.data.edit_bones
    hips = bones[0]
    hips.name = "Hips"
    hips.head = (0, 0, 0.82)
    hips.tail = (0, 0, 1.00)

    def bone(name, head, tail, parent=None):
        b = bones.new(name)
        b.head = head
        b.tail = tail
        if parent:
            b.parent = parent
        return b

    spine = bone("Spine", (0, 0, 1.00), (0, 0, 1.20), hips)
    chest = bone("Chest", (0, 0, 1.20), (0, 0, 1.38), spine)
    neck = bone("Neck", (0, 0, 1.38), (0, 0, 1.47), chest)
    head = bone("Head", (0, 0, 1.47), (0, 0, 1.67), neck)
    hair = bone("HairRoot", (0, 0.03, 1.48), (0, 0.05, 1.05), head)
    bone("Mantle_L", (-0.17, 0.02, 1.27), (-0.30, 0.07, 0.56), chest)
    bone("Mantle_R", (0.17, 0.02, 1.27), (0.30, 0.07, 0.56), chest)
    weapon = bone("Weapon", (-0.34, -0.04, 0.88), (-0.56, -0.05, 0.16), None)
    weapon.parent = hips

    for side, prefix, sign in [("left", "Left", -1), ("right", "Right", 1)]:
        upper_arm = bone(f"{prefix}UpperArm", (0.12 * sign, 0, 1.32), (0.29 * sign, 0, 1.12), chest)
        lower_arm = bone(f"{prefix}LowerArm", (0.29 * sign, 0, 1.12), (0.33 * sign, 0, 0.87), upper_arm)
        bone(f"{prefix}Hand", (0.33 * sign, 0, 0.87), (0.34 * sign, -0.02, 0.73), lower_arm)
        upper_leg = bone(f"{prefix}UpperLeg", (0.06 * sign, 0, 0.80), (0.08 * sign, 0, 0.45), hips)
        lower_leg = bone(f"{prefix}LowerLeg", (0.08 * sign, 0, 0.45), (0.09 * sign, 0, 0.13), upper_leg)
        foot = bone(f"{prefix}Foot", (0.09 * sign, 0, 0.13), (0.09 * sign, -0.12, 0.04), lower_leg)
        bone(f"{prefix}Toes", (0.09 * sign, -0.12, 0.04), (0.09 * sign, -0.19, 0.035), foot)

    bpy.ops.object.mode_set(mode="OBJECT")
    arm.show_in_front = True
    arm.data.display_type = "STICK"
    return arm


def add_vertex_group(obj: bpy.types.Object, name: str, weight: float = 1.0) -> None:
    group = obj.vertex_groups.new(name=name)
    group.add(range(len(obj.data.vertices)), weight, "ADD")


def add_armature_modifier(obj: bpy.types.Object, arm: bpy.types.Object, group_name: str) -> None:
    add_vertex_group(obj, group_name, 1.0)
    obj.parent = arm
    modifier = obj.modifiers.new("YUNA_skinning_armature", "ARMATURE")
    modifier.object = arm


def create_face_mesh(arm: bpy.types.Object) -> bpy.types.Object:
    y = -0.108
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    labels: list[str] = []

    def quad(label: str, x0: float, z0: float, x1: float, z1: float) -> None:
        index = len(verts)
        verts.extend([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)])
        faces.append((index, index + 1, index + 2, index + 3))
        labels.extend([label] * 4)

    quad("eye_l", -0.062, 1.535, -0.014, 1.558)
    quad("eye_r", 0.014, 1.535, 0.062, 1.558)
    quad("brow_l", -0.066, 1.578, -0.012, 1.588)
    quad("brow_r", 0.012, 1.578, 0.066, 1.588)
    quad("mouth", -0.042, 1.474, 0.042, 1.488)

    obj = add_plane_mesh("YUNA_LOD0_FaceExpression_MorphTargets", verts, faces, MAT_FACE)
    obj["face_vertex_labels"] = ",".join(labels)
    add_armature_modifier(obj, arm, "Head")
    basis = obj.shape_key_add(name="Basis")

    def edit_shape(name: str, fn) -> None:
        key = obj.shape_key_add(name=name)
        for i, vertex in enumerate(obj.data.vertices):
            label = labels[i]
            co = vertex.co.copy()
            key.data[i].co = fn(label, i % 4, co)

    def blink_l(label, corner, co):
        if label == "eye_l":
            co.z = 1.546
        return co

    def blink_r(label, corner, co):
        if label == "eye_r":
            co.z = 1.546
        return co

    def smile(label, corner, co):
        if label == "mouth":
            if corner in [0, 3]:
                co.z += 0.016
            if corner in [1, 2]:
                co.z += 0.016
        return co

    def frown(label, corner, co):
        if label == "mouth":
            co.z -= 0.013
        return co

    def brow_up(label, corner, co):
        if label.startswith("brow"):
            co.z += 0.020
        return co

    def brow_down(label, corner, co):
        if label.startswith("brow"):
            co.z -= 0.018
        return co

    def jaw_open(label, corner, co):
        if label == "mouth" and corner in [0, 1]:
            co.z -= 0.032
        return co

    def mouth_a(label, corner, co):
        if label == "mouth":
            if corner in [0, 1]:
                co.z -= 0.034
            if corner in [2, 3]:
                co.z += 0.009
        return co

    def mouth_e(label, corner, co):
        if label == "mouth":
            co.x *= 1.35
            co.z += 0.002
        return co

    def mouth_o(label, corner, co):
        if label == "mouth":
            co.x *= 0.55
            if corner in [0, 1]:
                co.z -= 0.025
            if corner in [2, 3]:
                co.z += 0.014
        return co

    def mouth_m(label, corner, co):
        if label == "mouth":
            co.z = 1.481
        return co

    def mouth_fv(label, corner, co):
        if label == "mouth":
            if corner in [0, 1]:
                co.z -= 0.012
            co.x *= 0.78
        return co

    for name, fn in [
        ("Blink_L", blink_l),
        ("Blink_R", blink_r),
        ("Smile", smile),
        ("Frown", frown),
        ("Brow_Up", brow_up),
        ("Brow_Down", brow_down),
        ("Jaw_Open", jaw_open),
        ("Mouth_A", mouth_a),
        ("Mouth_E", mouth_e),
        ("Mouth_O", mouth_o),
        ("Mouth_M", mouth_m),
        ("Mouth_FV", mouth_fv),
    ]:
        edit_shape(name, fn)
    return obj


def create_lod0(arm: bpy.types.Object) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    # Base anatomy and clothing forms.
    objects.append(add_sphere("YUNA_LOD0_Head_RetopoProxy", (0, -0.005, 1.54), (0.13, 0.105, 0.145), MAT_SKIN, 40, 20))
    objects.append(add_cylinder_between("YUNA_LOD0_Neck", (0, 0, 1.37), (0, 0, 1.47), 0.040, MAT_SKIN, 20))
    objects.append(add_sphere("YUNA_LOD0_Torso_Armor", (0, 0.005, 1.11), (0.185, 0.105, 0.315), MAT_BLACK, 32, 16))
    objects.append(add_sphere("YUNA_LOD0_Pelvis_SkirtCore", (0, 0.01, 0.79), (0.165, 0.10, 0.120), MAT_WHITE, 28, 12))
    objects.append(add_sphere("YUNA_LOD0_Chest_ResonanceCore", (0, -0.095, 1.245), (0.045, 0.014, 0.062), MAT_CYAN, 20, 10))

    for sign, prefix in [(-1, "Left"), (1, "Right")]:
        objects.append(add_cylinder_between(f"YUNA_LOD0_{prefix}UpperArm", (0.13 * sign, 0, 1.30), (0.29 * sign, 0, 1.09), 0.032, MAT_BLACK, 20))
        objects.append(add_cylinder_between(f"YUNA_LOD0_{prefix}LowerArm", (0.29 * sign, 0, 1.09), (0.33 * sign, -0.015, 0.86), 0.027, MAT_BLACK, 18))
        objects.append(add_sphere(f"YUNA_LOD0_{prefix}Hand", (0.34 * sign, -0.018, 0.76), (0.033, 0.026, 0.046), MAT_SKIN, 16, 8))
        objects.append(add_cylinder_between(f"YUNA_LOD0_{prefix}UpperLeg_Stocking", (0.058 * sign, 0, 0.76), (0.080 * sign, 0, 0.45), 0.043, MAT_WHITE, 22))
        objects.append(add_cylinder_between(f"YUNA_LOD0_{prefix}LowerLeg_Stocking", (0.080 * sign, 0, 0.45), (0.090 * sign, 0, 0.12), 0.035, MAT_WHITE, 22))
        objects.append(add_cube(f"YUNA_LOD0_{prefix}Boot_Metal", (0.092 * sign, -0.04, 0.035), (0.055, 0.110, 0.034), MAT_METAL))
        objects.append(add_cube(f"YUNA_LOD0_{prefix}CoatPanel", (0.155 * sign, 0.040, 0.76), (0.060, 0.014, 0.430), MAT_BLACK))
        objects.append(add_cube(f"YUNA_LOD0_{prefix}Mantle_Transparent", (0.285 * sign, 0.072, 0.82), (0.105, 0.010, 0.570), MAT_MANTLE))

    # Hair volumes: silver mass plus teal tail strips.
    objects.append(add_sphere("YUNA_LOD0_Hair_BackVolume", (0.0, 0.060, 1.37), (0.170, 0.080, 0.360), MAT_HAIR, 40, 18))
    for sign, prefix in [(-1, "Left"), (1, "Right")]:
        objects.append(add_cylinder_between(f"YUNA_LOD0_{prefix}Hair_TealTail", (0.10 * sign, 0.05, 1.42), (0.29 * sign, 0.07, 0.83), 0.025, MAT_HAIR_TIP, 14))
        objects.append(add_cylinder_between(f"YUNA_LOD0_{prefix}Hair_SilverStrand", (0.045 * sign, -0.04, 1.48), (0.15 * sign, -0.06, 1.08), 0.015, MAT_HAIR, 12))

    # Weapon mesh aligned to side reference.
    objects.append(add_cylinder_between("YUNA_LOD0_Weapon_Handle", (-0.34, -0.045, 0.84), (-0.42, -0.050, 0.55), 0.018, MAT_METAL, 12))
    objects.append(add_cylinder_between("YUNA_LOD0_Weapon_EnergyBlade", (-0.42, -0.052, 0.55), (-0.57, -0.052, 0.06), 0.020, MAT_CYAN, 4))
    objects.append(add_sphere("YUNA_LOD0_Weapon_Core", (-0.38, -0.052, 0.60), (0.043, 0.018, 0.043), MAT_GOLD, 16, 8))

    face = create_face_mesh(arm)
    objects.append(face)

    bone_map = {
        "Head": ["Head", "FaceExpression", "Hair"],
        "Neck": ["Neck"],
        "Chest": ["Torso", "Chest_ResonanceCore"],
        "Hips": ["Pelvis", "CoatPanel"],
        "LeftUpperArm": ["LeftUpperArm"],
        "LeftLowerArm": ["LeftLowerArm"],
        "LeftHand": ["LeftHand"],
        "RightUpperArm": ["RightUpperArm"],
        "RightLowerArm": ["RightLowerArm"],
        "RightHand": ["RightHand"],
        "LeftUpperLeg": ["LeftUpperLeg"],
        "LeftLowerLeg": ["LeftLowerLeg"],
        "LeftFoot": ["LeftBoot"],
        "RightUpperLeg": ["RightUpperLeg"],
        "RightLowerLeg": ["RightLowerLeg"],
        "RightFoot": ["RightBoot"],
        "Mantle_L": ["LeftMantle"],
        "Mantle_R": ["RightMantle"],
        "Weapon": ["Weapon"],
    }
    for obj in objects:
        group_name = "Hips"
        for bone_name, needles in bone_map.items():
            if any(needle in obj.name for needle in needles):
                group_name = bone_name
                break
        add_armature_modifier(obj, arm, group_name)
    return objects


def duplicate_lod(source_objects: list[bpy.types.Object], lod: int, ratio: float) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    for source in source_objects:
        duplicate = source.copy()
        duplicate.data = source.data.copy()
        duplicate.name = source.name.replace("_LOD0_", f"_LOD{lod}_")
        duplicate.data.name = duplicate.name + "_mesh"
        bpy.context.collection.objects.link(duplicate)
        if source.type == "MESH" and "FaceExpression" not in source.name and len(source.data.polygons) >= 16:
            decimate = duplicate.modifiers.new(f"LOD{lod}_decimate_ratio_{ratio}", "DECIMATE")
            decimate.ratio = ratio
            bpy.ops.object.select_all(action="DESELECT")
            duplicate.select_set(True)
            bpy.context.view_layer.objects.active = duplicate
            try:
                bpy.ops.object.modifier_apply(modifier=decimate.name)
            except RuntimeError:
                pass
        duplicate["lod"] = lod
        objects.append(duplicate)
    return objects


def assign_collections(lod0: list[bpy.types.Object], lod1: list[bpy.types.Object], lod2: list[bpy.types.Object], arm: bpy.types.Object) -> None:
    for name, objects in [
        ("YUNA_PRODUCTION_LOD0", lod0),
        ("YUNA_PRODUCTION_LOD1", lod1),
        ("YUNA_PRODUCTION_LOD2", lod2),
    ]:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
        for obj in objects:
            for existing in obj.users_collection:
                existing.objects.unlink(obj)
            collection.objects.link(obj)
    rig_collection = bpy.data.collections.new("YUNA_PRODUCTION_RIG")
    bpy.context.scene.collection.children.link(rig_collection)
    for existing in arm.users_collection:
        existing.objects.unlink(arm)
    rig_collection.objects.link(arm)


def add_reference_planes() -> None:
    collection = bpy.data.collections.new("YUNA_REFERENCE_IMAGES_INFERRED")
    bpy.context.scene.collection.children.link(collection)

    def material_from_image(name: str, path: Path) -> bpy.types.Material:
        material = bpy.data.materials.new(name)
        material.use_nodes = True
        material.blend_method = "BLEND"
        material.show_transparent_back = True
        bsdf = material.node_tree.nodes.get("Principled BSDF")
        tex = material.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(str(path))
        tex.extension = "CLIP"
        material.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        material.node_tree.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        bsdf.inputs["Alpha"].default_value = 0.42
        return material

    def plane(name: str, path: Path, x: float, y: float, z: float, width: float, height: float) -> None:
        obj = add_plane_mesh(
            name,
            [(-width / 2, y, z), (width / 2, y, z), (width / 2, y, z + height), (-width / 2, y, z + height)],
            [(0, 1, 2, 3)],
            material_from_image(name + "_mat", path),
        )
        obj.location.x = x
        obj.hide_render = True
        for existing in obj.users_collection:
            existing.objects.unlink(obj)
        collection.objects.link(obj)

    plane("ref_front_locked", ROOT / "refs/front_rgba/yuna_front_rgba.png", 0.0, 0.42, 0, 1.12, HEIGHT_M)
    plane("ref_left_side_ai", ROOT / "refs/ai_turnarounds/cutouts/yuna_left_side.png", -1.1, 0.42, 0, 0.74, HEIGHT_M)
    plane("ref_back_ai", ROOT / "refs/ai_turnarounds/cutouts/yuna_back.png", 1.1, 0.42, 0, 1.12, HEIGHT_M)


def add_camera_and_light() -> None:
    bpy.ops.object.light_add(type="AREA", location=(-2.2, -3.2, 3.4))
    light = bpy.context.object
    light.name = "YUNA_softbox_key"
    light.data.energy = 620
    light.data.size = 4.5
    bpy.ops.object.camera_add(location=(0.78, -5.15, 1.22))
    camera = bpy.context.object
    camera.name = "YUNA_production_review_camera"
    camera.data.lens = 36
    target = Vector((0, 0, 0.88))
    direction = target - Vector(camera.location)
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = camera
    bpy.context.scene.render.resolution_x = 1440
    bpy.context.scene.render.resolution_y = 900


def select_for_export(objects: list[bpy.types.Object], arm: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = arm


def export_lod(label: str, objects: list[bpy.types.Object], arm: bpy.types.Object) -> None:
    select_for_export(objects, arm)
    fbx_path = ROOT / f"rig/yuna_production_{label}.fbx"
    glb_path = ROOT / f"web/yuna_production_{label}.glb"
    bpy.ops.export_scene.fbx(
        filepath=str(fbx_path),
        use_selection=True,
        add_leaf_bones=False,
        bake_anim=False,
        path_mode="COPY",
        embed_textures=True,
    )
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path),
        export_format="GLB",
        export_texcoords=True,
        export_normals=True,
        export_tangents=False,
        export_morph=True,
        export_skins=True,
        export_animations=False,
        use_selection=True,
    )
    shutil.copy2(fbx_path, ROOT / f"unity/prefabs/yuna_production_{label}.fbx")
    shutil.copy2(glb_path, ROOT / f"unity/prefabs/yuna_production_{label}.glb")

    if label == "lod0":
        preview_path = ROOT / "web/yuna_production_lod0_preview_nomorph.glb"
        bpy.ops.export_scene.gltf(
            filepath=str(preview_path),
            export_format="GLB",
            export_texcoords=True,
            export_normals=True,
            export_tangents=False,
            export_morph=False,
            export_skins=True,
            export_animations=False,
            use_selection=True,
        )
        shutil.copy2(preview_path, ROOT / "unity/prefabs/yuna_production_lod0_preview_nomorph.glb")


def render_preview() -> None:
    try:
        bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        pass
    bpy.context.scene.render.filepath = str(ROOT / "qa/turntable/yuna_production_slice_blender_preview.png")
    bpy.ops.render.render(write_still=True)


def write_report(arm: bpy.types.Object, lod0: list[bpy.types.Object], lod1: list[bpy.types.Object], lod2: list[bpy.types.Object]) -> None:
    def mesh_stats(objects: list[bpy.types.Object]) -> dict:
        mesh_objects = [obj for obj in objects if obj.type == "MESH"]
        return {
            "objects": len(objects),
            "mesh_objects": len(mesh_objects),
            "vertices": sum(len(obj.data.vertices) for obj in mesh_objects),
            "polygons": sum(len(obj.data.polygons) for obj in mesh_objects),
            "uv_mapped_meshes": sum(1 for obj in mesh_objects if obj.data.uv_layers),
            "skinned_meshes": sum(1 for obj in mesh_objects if any(mod.type == "ARMATURE" for mod in obj.modifiers)),
        }

    face = bpy.data.objects.get("YUNA_LOD0_FaceExpression_MorphTargets")
    shape_keys = []
    if face and face.data.shape_keys:
        shape_keys = [key.name for key in face.data.shape_keys.key_blocks if key.name != "Basis"]
    report = {
        "character_id": "yuna-white-sword",
        "status": "production_slice_exported",
        "source_boundary": "Automated production vertical slice. Requires manual sculpt/retopo art pass before final commercial use.",
        "armature": {
            "object": arm.name,
            "bones": [bone.name for bone in arm.data.bones],
            "bone_count": len(arm.data.bones),
            "humanoid_minimum_bones_met": len(arm.data.bones) >= 15,
        },
        "lod0": mesh_stats(lod0),
        "lod1": mesh_stats(lod1),
        "lod2": mesh_stats(lod2),
        "shape_keys": shape_keys,
        "shape_key_count": len(shape_keys),
        "shape_key_target_met": all(name in shape_keys for name in FACE_SHAPE_KEYS),
        "materials": sorted(material.name for material in bpy.data.materials if material.name.startswith("YUNA_PBR")),
        "texture_outputs": {
            "unity_urp": sorted(path.name for path in (ROOT / "textures/export_unity_urp").glob("*.png")),
            "gltf_web": sorted(path.name for path in (ROOT / "textures/export_gltf_web").glob("*.png")),
        },
        "exports": {
            "blend": "CharacterPackage/dcc/blender/yuna_production_slice.blend",
            "lod0_fbx": "CharacterPackage/rig/yuna_production_lod0.fbx",
            "lod0_glb": "CharacterPackage/web/yuna_production_lod0.glb",
            "lod0_preview_nomorph_glb": "CharacterPackage/web/yuna_production_lod0_preview_nomorph.glb",
            "lod1_fbx": "CharacterPackage/rig/yuna_production_lod1.fbx",
            "lod1_glb": "CharacterPackage/web/yuna_production_lod1.glb",
            "lod2_fbx": "CharacterPackage/rig/yuna_production_lod2.fbx",
            "lod2_glb": "CharacterPackage/web/yuna_production_lod2.glb",
        },
    }
    (ROOT / "qa/yuna_production_slice_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    clear_scene()
    create_texture_outputs()
    arm = make_armature()
    lod0 = create_lod0(arm)
    lod1 = duplicate_lod(lod0, 1, 0.56)
    lod2 = duplicate_lod(lod0, 2, 0.28)
    assign_collections(lod0, lod1, lod2, arm)
    add_reference_planes()
    add_camera_and_light()
    render_preview()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "dcc/blender/yuna_production_slice.blend"))
    export_lod("lod0", lod0, arm)
    export_lod("lod1", lod1, arm)
    export_lod("lod2", lod2, arm)
    write_report(arm, lod0, lod1, lod2)


if __name__ == "__main__":
    main()
