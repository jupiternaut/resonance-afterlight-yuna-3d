# YUNA Semantic v10 Backlog

## Recommended Order

1. `boot_hardsurface_ortho`
2. `leg_quad_loop_retopo_proxy`
3. `authored_hair_ribbons`
4. `cloth_seam_surface`
5. `weapon_hardsurface_ortho_v1`

## 1. Boot Hard-Surface Ortho

Goal:

- Generate independent boot candidates with thickness, bevel proxy, material separation, and validation screenshots.

Acceptance:

- Boots remain independent.
- Existing v8 boot beauty stays active until candidate validation passes.
- No leg/cage debug volumes leak into beauty.
- Screenshots: front, yaw15, yaw30, side, wire, exploded.

## 2. Leg Quad-Loop Retopo Proxy

Goal:

- Prepare a retopo proxy spec for continuous thigh/knee/shin/ankle loops.

Boundary:

- Do not attempt final production retopology automatically.
- Do not replace v8 leg visual panels in beauty until deformation tests exist.

Acceptance:

- Knee and ankle loop intent is machine-readable.
- Proxy remains debug/cage until validated.
- No gray volume guide leaks into beauty.

## 3. Authored Hair Ribbons

Goal:

- Convert current hair cards into authored strand/ribbon candidate curves.

Acceptance:

- At least three depth groups remain.
- Front identity and silhouette are preserved.
- Side/back remain soft constraints only.

## 4. Cloth Seam Surface

Goal:

- Upgrade cape/skirt cloth sheets into seam-aware surfaces with attachment metadata.

Acceptance:

- Cape remains independent from torso.
- Cloth has visible front/yaw validation.
- Swing/attachment hooks are preserved.

## 5. Weapon Hard-Surface Ortho v1

Goal:

- Clean weapon source texture/mask residue and split weapon into blade/guard/handle subparts.

Acceptance:

- No body/cloth residue in the weapon texture.
- Subparts are independently named.
- GLB roundtrip preserves material slots and socket metadata.
