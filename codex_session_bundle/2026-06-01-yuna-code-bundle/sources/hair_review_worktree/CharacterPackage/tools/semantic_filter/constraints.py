from __future__ import annotations

from .state import ConstraintSet, FilterDecision, PartState


def project_to_constraints(
    state: PartState,
    decision: FilterDecision,
    constraints: ConstraintSet,
) -> FilterDecision:
    applied = list(decision.constraints_applied)

    if state.debug_only and constraints.must_not_leak_debug_to_beauty:
        decision.visible_in_beauty = False
        decision.visible_in_cage = True
        if "debug_guides_must_not_leak_to_beauty" not in applied:
            applied.append("debug_guides_must_not_leak_to_beauty")

    if constraints.keep_beauty_and_cage_separate:
        if "beauty_and_cage_exports_remain_separate" not in applied:
            applied.append("beauty_and_cage_exports_remain_separate")

    if constraints.side_back_are_soft:
        if "side_back_are_soft_constraints" not in applied:
            applied.append("side_back_are_soft_constraints")

    if constraints.must_keep_existing_beauty_until_replacement_validated:
        if "existing_beauty_mesh_kept_until_replacement_validated" not in applied:
            applied.append("existing_beauty_mesh_kept_until_replacement_validated")

    if constraints.preserve_front_identity:
        if "front_identity_preserved" not in applied:
            applied.append("front_identity_preserved")

    decision.constraints_applied = applied
    return decision

