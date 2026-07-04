from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PartState:
    id: str
    category: str
    parent: str | None = None
    generator: str | None = None
    depth: float | None = None
    thickness: float | None = None
    curvature: str | None = None
    bbox: list[int] | None = None
    texture: str | None = None
    card_count: int | None = None
    visible_in_beauty: bool = False
    visible_in_cage: bool = False
    debug_only: bool = False
    source: str = "unknown"
    known_limits: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PartObservation:
    part_id: str
    source: str
    confidence: float
    bbox: list[int] | None = None
    coverage: float | None = None
    vertical_band_match: float | None = None
    roundtrip_present: bool | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PartPrior:
    category: str
    allowed_generators: list[str]
    preferred_next_generator: str | None
    thickness_bounds: tuple[float, float]
    depth_bounds: tuple[float, float]
    front_identity_locked: bool = True

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["thickness_bounds"] = list(self.thickness_bounds)
        data["depth_bounds"] = list(self.depth_bounds)
        return data


@dataclass
class ConstraintSet:
    preserve_front_identity: bool = True
    keep_major_parts_independent: bool = True
    keep_beauty_and_cage_separate: bool = True
    side_back_are_soft: bool = True
    must_not_leak_debug_to_beauty: bool = True
    must_keep_existing_beauty_until_replacement_validated: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FilterDecision:
    part_id: str
    decision: str
    confidence: float
    old_generator: str | None
    proposed_generator: str | None
    old_depth: float | None
    proposed_depth: float | None
    visible_in_beauty: bool
    visible_in_cage: bool
    debug_only: bool
    constraints_applied: list[str]
    reason: str
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FilterReport:
    route: str
    input_route: str | None
    formula: str
    applicability: dict[str, str]
    constraints: ConstraintSet
    global_decisions: list[dict[str, str]]
    part_states: list[PartState]
    observations: list[PartObservation]
    part_decisions: list[FilterDecision]
    output_paths: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "route": self.route,
            "input_route": self.input_route,
            "formula": self.formula,
            "applicability": self.applicability,
            "constraints": self.constraints.to_dict(),
            "global_decisions": self.global_decisions,
            "part_states": [part.to_dict() for part in self.part_states],
            "observations": [observation.to_dict() for observation in self.observations],
            "part_decisions": [decision.to_dict() for decision in self.part_decisions],
            "output_paths": self.output_paths,
        }

