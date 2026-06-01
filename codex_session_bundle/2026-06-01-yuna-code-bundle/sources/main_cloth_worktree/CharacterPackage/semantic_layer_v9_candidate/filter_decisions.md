# Semantic State Filter v0 Decisions

This is a read-only planning pass. It does not modify v8 and does not generate new mesh exports.

| Part | Decision | Proposed generator | Confidence | Reason |
|---|---|---|---:|---|
| `back_hair` | `keep_for_visual_review_but_flag_strand_authoring` | `authored_hair_ribbons` | 0.82 | Hair cards work for visual review, but production needs authored strand/ribbon curves. |
| `bangs` | `keep_for_visual_review_but_flag_strand_authoring` | `authored_hair_ribbons` | 0.82 | Hair cards work for visual review, but production needs authored strand/ribbon curves. |
| `boot_L_hardsurface_proxy` | `keep_debug_only` | `boot_proxy` | 0.98 | This guide is useful for DCC planning but must not leak into the beauty GLB. |
| `boot_R_hardsurface_proxy` | `keep_debug_only` | `boot_proxy` | 0.98 | This guide is useful for DCC planning but must not leak into the beauty GLB. |
| `boots` | `upgrade_required` | `boot_hardsurface_ortho` | 0.88 | Boots are still visual-panel/proxy geometry; v9 should rebuild them as hard-surface forms with thickness and bevels. |
| `cage_head_ellipsoid` | `keep_for_visual_review` | `` | 0.75 | No high-priority v9 actuator is assigned for this part in v0. |
| `cage_leg_L_capsule_proxy` | `keep_for_visual_review` | `` | 0.75 | No high-priority v9 actuator is assigned for this part in v0. |
| `cage_leg_R_capsule_proxy` | `keep_for_visual_review` | `` | 0.75 | No high-priority v9 actuator is assigned for this part in v0. |
| `cage_torso_ellipsoid` | `keep_for_visual_review` | `` | 0.75 | No high-priority v9 actuator is assigned for this part in v0. |
| `cape_left` | `keep_for_visual_review_but_flag_cloth_seams` | `cloth_seam_surface` | 0.80 | Cloth sheets preserve the current silhouette, but seams and attachment points need authored cloth surfaces. |
| `cape_right` | `keep_for_visual_review_but_flag_cloth_seams` | `cloth_seam_surface` | 0.80 | Cloth sheets preserve the current silhouette, but seams and attachment points need authored cloth surfaces. |
| `face` | `keep_front_identity_locked` | `locked_face_plate` | 0.92 | The face is front-identity critical; do not replace it until a candidate preserves likeness in screenshots. |
| `jacket_outer` | `keep_for_visual_review` | `curved_panel` | 0.75 | No high-priority v9 actuator is assigned for this part in v0. |
| `leg_L_knee_loop_proxy` | `keep_debug_only` | `leg_proxy` | 0.98 | This guide is useful for DCC planning but must not leak into the beauty GLB. |
| `leg_L_retopo_proxy` | `keep_debug_only` | `leg_proxy` | 0.98 | This guide is useful for DCC planning but must not leak into the beauty GLB. |
| `leg_L_thigh_strap_proxy` | `keep_debug_only` | `leg_proxy` | 0.98 | This guide is useful for DCC planning but must not leak into the beauty GLB. |
| `leg_L_visual_panel` | `retopo_required` | `leg_quad_loop_retopo_proxy` | 0.90 | v8 uses split visual leg panels for beauty and cage guides for DCC; production knee/ankle topology is still missing. |
| `leg_R_knee_loop_proxy` | `keep_debug_only` | `leg_proxy` | 0.98 | This guide is useful for DCC planning but must not leak into the beauty GLB. |
| `leg_R_retopo_proxy` | `keep_debug_only` | `leg_proxy` | 0.98 | This guide is useful for DCC planning but must not leak into the beauty GLB. |
| `leg_R_thigh_strap_proxy` | `keep_debug_only` | `leg_proxy` | 0.98 | This guide is useful for DCC planning but must not leak into the beauty GLB. |
| `leg_R_visual_panel` | `retopo_required` | `leg_quad_loop_retopo_proxy` | 0.90 | v8 uses split visual leg panels for beauty and cage guides for DCC; production knee/ankle topology is still missing. |
| `legs` | `retopo_required` | `leg_quad_loop_retopo_proxy` | 0.90 | v8 uses split visual leg panels for beauty and cage guides for DCC; production knee/ankle topology is still missing. |
| `side_hair_left` | `keep_for_visual_review_but_flag_strand_authoring` | `authored_hair_ribbons` | 0.82 | Hair cards work for visual review, but production needs authored strand/ribbon curves. |
| `side_hair_right` | `keep_for_visual_review_but_flag_strand_authoring` | `authored_hair_ribbons` | 0.82 | Hair cards work for visual review, but production needs authored strand/ribbon curves. |
| `skirt_front` | `keep_for_visual_review_but_flag_cloth_seams` | `cloth_seam_surface` | 0.80 | Cloth sheets preserve the current silhouette, but seams and attachment points need authored cloth surfaces. |
| `torso_inner` | `keep_for_visual_review` | `curved_panel` | 0.75 | No high-priority v9 actuator is assigned for this part in v0. |
| `weapon` | `upgrade_required` | `weapon_hardsurface_ortho` | 0.95 | Current weapon is an independent textured panel; the next asset route requires orthographic hard-surface reconstruction. |

## Required Guarantees

- v8 remains untouched.
- Debug-only guides stay out of the beauty GLB.
- Side/back references remain soft constraints.
- Current beauty meshes stay until replacements are validated.
