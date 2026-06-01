from __future__ import annotations

from .constraints import project_to_constraints
from .state import ConstraintSet, FilterDecision, PartObservation, PartPrior, PartState


def prior_for_part(state: PartState) -> PartPrior:
    category = state.category
    if category == "weapon" or state.id == "weapon":
        return PartPrior(
            category=category,
            allowed_generators=["weapon_panel", "weapon_hardsurface_ortho"],
            preferred_next_generator="weapon_hardsurface_ortho",
            thickness_bounds=(0.01, 0.18),
            depth_bounds=(-1.0, 1.2),
        )
    if state.id == "boots" or "boot" in state.id:
        return PartPrior(
            category=category,
            allowed_generators=["curved_panel", "boot_hardsurface_ortho"],
            preferred_next_generator="boot_hardsurface_ortho",
            thickness_bounds=(0.01, 0.16),
            depth_bounds=(-1.0, 1.2),
        )
    if state.id == "legs" or state.id.startswith("leg_"):
        return PartPrior(
            category=category,
            allowed_generators=["curved_panel", "leg_quad_loop_retopo_proxy"],
            preferred_next_generator="leg_quad_loop_retopo_proxy",
            thickness_bounds=(0.01, 0.14),
            depth_bounds=(-1.0, 1.2),
        )
    if category == "hair":
        return PartPrior(
            category=category,
            allowed_generators=["hair_cards", "authored_hair_ribbons"],
            preferred_next_generator="authored_hair_ribbons",
            thickness_bounds=(0.001, 0.03),
            depth_bounds=(-1.0, 1.2),
        )
    if category == "cloth":
        return PartPrior(
            category=category,
            allowed_generators=["cloth_sheet", "cloth_seam_surface"],
            preferred_next_generator="cloth_seam_surface",
            thickness_bounds=(0.001, 0.05),
            depth_bounds=(-1.0, 1.2),
        )
    if category == "face":
        return PartPrior(
            category=category,
            allowed_generators=["face_plate", "locked_face_plate"],
            preferred_next_generator="locked_face_plate",
            thickness_bounds=(0.001, 0.03),
            depth_bounds=(-1.0, 1.2),
            front_identity_locked=True,
        )
    return PartPrior(
        category=category,
        allowed_generators=[state.generator or "unknown"],
        preferred_next_generator=state.generator,
        thickness_bounds=(0.001, 0.20),
        depth_bounds=(-1.0, 1.2),
    )


def robust_fuse_part(
    state: PartState,
    observations: list[PartObservation],
    prior: PartPrior,
    alpha: float = 0.65,
) -> FilterDecision:
    del observations, alpha  # v0 is deterministic and rule-based.
    constraints = ["semantic_part_independence"]

    if state.debug_only:
        return FilterDecision(
            part_id=state.id,
            decision="keep_debug_only",
            confidence=0.98,
            old_generator=state.generator,
            proposed_generator=state.generator or prior.preferred_next_generator,
            old_depth=state.depth,
            proposed_depth=state.depth,
            visible_in_beauty=False,
            visible_in_cage=True,
            debug_only=True,
            constraints_applied=constraints,
            reason="This guide is useful for DCC planning but must not leak into the beauty GLB.",
            next_action="Keep as cage/debug reference until a validated replacement mesh exists.",
        )

    if state.category == "weapon" or state.id == "weapon":
        return FilterDecision(
            part_id=state.id,
            decision="upgrade_required",
            confidence=0.95,
            old_generator=state.generator,
            proposed_generator="weapon_hardsurface_ortho",
            old_depth=state.depth,
            proposed_depth=state.depth,
            visible_in_beauty=state.visible_in_beauty,
            visible_in_cage=state.visible_in_cage,
            debug_only=False,
            constraints_applied=constraints + ["weapon_must_remain_independent"],
            reason="Current weapon is an independent textured panel; the next asset route requires orthographic hard-surface reconstruction.",
            next_action="Build a separate beveled hard-surface weapon mesh from the orthographic sheet.",
        )

    if state.id == "legs" or state.id.startswith("leg_L_visual") or state.id.startswith("leg_R_visual"):
        return FilterDecision(
            part_id=state.id,
            decision="retopo_required",
            confidence=0.90,
            old_generator=state.generator,
            proposed_generator="leg_quad_loop_retopo_proxy",
            old_depth=state.depth,
            proposed_depth=state.depth,
            visible_in_beauty=state.visible_in_beauty,
            visible_in_cage=state.visible_in_cage,
            debug_only=state.debug_only,
            constraints_applied=constraints + ["leg_topology_missing"],
            reason="v8 uses split visual leg panels for beauty and cage guides for DCC; production knee/ankle topology is still missing.",
            next_action="Retopologize continuous thigh/knee/shin/ankle quad loops before skinning tests.",
        )

    if state.id == "boots" or "boot" in state.id:
        return FilterDecision(
            part_id=state.id,
            decision="upgrade_required",
            confidence=0.88,
            old_generator=state.generator,
            proposed_generator="boot_hardsurface_ortho",
            old_depth=state.depth,
            proposed_depth=state.depth,
            visible_in_beauty=state.visible_in_beauty,
            visible_in_cage=state.visible_in_cage,
            debug_only=state.debug_only,
            constraints_applied=constraints + ["boot_must_remain_independent"],
            reason="Boots are still visual-panel/proxy geometry; v9 should rebuild them as hard-surface forms with thickness and bevels.",
            next_action="Create boot hard-surface mesh from silhouette and validate against front/yaw screenshots.",
        )

    if state.category == "hair" and state.generator == "hair_cards":
        return FilterDecision(
            part_id=state.id,
            decision="keep_for_visual_review_but_flag_strand_authoring",
            confidence=0.82,
            old_generator=state.generator,
            proposed_generator="authored_hair_ribbons",
            old_depth=state.depth,
            proposed_depth=state.depth,
            visible_in_beauty=state.visible_in_beauty,
            visible_in_cage=state.visible_in_cage,
            debug_only=False,
            constraints_applied=constraints + ["front_hair_identity_preserved"],
            reason="Hair cards work for visual review, but production needs authored strand/ribbon curves.",
            next_action="Keep current beauty hair until authored hair ribbons pass front/yaw validation.",
        )

    if state.category == "cloth" and state.generator == "cloth_sheet":
        return FilterDecision(
            part_id=state.id,
            decision="keep_for_visual_review_but_flag_cloth_seams",
            confidence=0.80,
            old_generator=state.generator,
            proposed_generator="cloth_seam_surface",
            old_depth=state.depth,
            proposed_depth=state.depth,
            visible_in_beauty=state.visible_in_beauty,
            visible_in_cage=state.visible_in_cage,
            debug_only=False,
            constraints_applied=constraints + ["cloth_must_remain_layered"],
            reason="Cloth sheets preserve the current silhouette, but seams and attachment points need authored cloth surfaces.",
            next_action="Keep current cape/skirt sheets until seam-aware cloth surfaces validate.",
        )

    if state.category == "face" or state.generator == "face_plate":
        return FilterDecision(
            part_id=state.id,
            decision="keep_front_identity_locked",
            confidence=0.92,
            old_generator=state.generator,
            proposed_generator="locked_face_plate",
            old_depth=state.depth,
            proposed_depth=state.depth,
            visible_in_beauty=state.visible_in_beauty,
            visible_in_cage=state.visible_in_cage,
            debug_only=False,
            constraints_applied=constraints + ["face_identity_locked"],
            reason="The face is front-identity critical; do not replace it until a candidate preserves likeness in screenshots.",
            next_action="Keep face plate locked and defer face topology until a dedicated face pass.",
        )

    return FilterDecision(
        part_id=state.id,
        decision="keep_for_visual_review",
        confidence=0.75,
        old_generator=state.generator,
        proposed_generator=prior.preferred_next_generator,
        old_depth=state.depth,
        proposed_depth=state.depth,
        visible_in_beauty=state.visible_in_beauty,
        visible_in_cage=state.visible_in_cage,
        debug_only=state.debug_only,
        constraints_applied=constraints,
        reason="No high-priority v9 actuator is assigned for this part in v0.",
        next_action="Keep current v8 beauty mesh until a targeted generator is selected.",
    )


def filter_part(
    state: PartState,
    observations: list[PartObservation],
    constraints: ConstraintSet,
    alpha: float = 0.65,
) -> FilterDecision:
    prior = prior_for_part(state)
    decision = robust_fuse_part(state, observations, prior, alpha)
    return project_to_constraints(state, decision, constraints)

