# YUNA 2D To 3D DCC Technical Route Research

This note summarizes the practical routes commonly shown in Bilibili tutorials and how they apply to YUNA.

## Routes Found

### 1. Traditional Game Character DCC Route

Typical route:

1. Concept art and orthographic references.
2. ZBrush or Blender sculpt for high-poly body, face, hair and clothing.
3. Blender, Maya or 3ds Max retopology.
4. UV unwrap and texture atlas planning.
5. Bake normal, AO, curvature and other supporting maps.
6. Substance Painter material and PBR texture pass.
7. Rigging, weight painting, facial blendshapes and secondary-motion setup.
8. LOD generation and cleanup.
9. FBX/GLB export and Unity validation.

This is the reliable path for a high-fidelity game character. Bilibili tutorials around Blender/ZBrush/Substance Painter describe this full production chain.

### 2. AI Image-To-3D Fast Prototype Route

Typical route:

1. Generate or prepare a clean T-pose/A-pose reference image.
2. Upload the image to Rodin, Meshy, Tripo, TripoSR or similar image-to-3D tools.
3. Download OBJ/FBX/GLB, sometimes with high-poly, low-poly or LOD choices.
4. Import into Blender.
5. Fix scale, orientation, topology, UVs and texture errors.
6. Use Mixamo or Blender rigging for quick animation.
7. Export to Unity for preview.

This route is fast and useful for blockout, toy-like characters, props, background assets and early look-dev. For YUNA, it can produce a reference mesh, not a final character.

### 3. AI-Assisted Texture / Retexture Route

Typical route:

1. Start from an existing mesh or AI-generated mesh.
2. Re-UV or create a cleaner duplicate mesh in Blender.
3. Bake old texture/detail to new UVs.
4. Paint or regenerate textures using Blender Texture Paint, Photoshop/Krita, Substance Painter or AI texturing tools.
5. Export PBR texture maps for Unity.

This is useful after a base mesh exists. It does not solve face likeness, topology or rig deformation by itself.

### 4. 2.5D / Grease Pencil Route

Typical route:

1. Use Blender Grease Pencil or flat geometry based on 2D art.
2. Add depth, camera parallax and stylized hand-drawn movement.
3. Keep the output close to a 2D/2.5D animated look.

This is useful for stylized animation or UI scenes, but not for a full 360-degree Unity action RPG character.

## Best Route For YUNA

Recommended hybrid route:

1. Use the locked 2D front image and the generated 3-view, expression, weapon and material sheets as reference.
2. Optionally run Meshy/Rodin/Tripo once to generate a disposable proxy mesh.
3. In Blender/ZBrush, manually sculpt the real face, body proportion, hair volume, coat, white stockings, boots, translucent mantle and weapon.
4. Retopologize manually, especially face loops, shoulders, elbows, hips, knees, mantle and hair attachment zones.
5. Build UV atlas and PBR texture sets.
6. Create humanoid skeleton, hair/mantle/weapon helper bones and facial blendshapes.
7. Export FBX for Unity and GLB for Web preview.
8. Validate with front-view overlay against the original 2D art, Unity Avatar, material import, LOD switching and animation deformation tests.

## Why The AI Route Alone Is Not Enough

YUNA has difficult features:

- anime face identity must match the 2D art closely;
- long layered hair with cyan gradient tips;
- semi-transparent mantle panels;
- dense gold trims, belts, ornaments and chains;
- white stockings and boot material contrast;
- precise weapon silhouette and glowing blade;
- facial expressions and game-ready deformation.

Current image-to-3D AI can guess a rough volume, but it commonly fails at clean topology, face likeness, hair layering, transparent fabric, precise ornaments, blendshapes and Unity-ready rig deformation.

## Acceptance Standard For Human DCC

- Front orthographic render aligns to the locked 2D reference silhouette and face.
- Model has clean topology and animation-safe loops around eyes, mouth, shoulders, elbows, hips and knees.
- UVs are non-overlapping except intentional mirrored parts.
- Texture set includes BaseColor, Normal, ORM or Metallic/Roughness, Emission and optional opacity mask.
- Rig imports into Unity without missing bones or broken materials.
- Face has at least Blink_L, Blink_R, Smile, Frown, Brow_Up, Brow_Down, Jaw_Open, Mouth_A/E/O/M/FV.
- Hair and mantle have secondary-motion bones or cloth-ready segmentation.
- LOD0/LOD1/LOD2 switch without holes, flipped normals or major silhouette breakage.

## Source Notes

- Bilibili traditional route examples mention Blender, ZBrush and Substance Painter character workflows.
- Bilibili AI route examples mention Rodin, Meshy, Tripo/TripoSR, Blender import, Mixamo binding, UV repair and texture repair.
- Unity AI generators currently help with sprites, textures, animations, sounds, materials and terrain layers, but they are not a complete 2D-to-final-character DCC replacement.
