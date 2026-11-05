"""The owner-facing agent: a state machine that asks the owner and never decides for them.

Each method returns the next Turn, which says what the owner must do next. Because the agent
never blocks waiting for input, it works the same in Streamlit (which reruns on each click) and
in scripted tests. For blocking channels use `pawpal.channels.run_session`.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional, Sequence, Tuple, Union

from pawpal.models import AvailabilityWindow, Owner
from pawpal.plan import Conflict, DailyPlan, PlanChange, PlanningContext, ResolutionOption, ConflictResolution
from pawpal.service import PlanningService


class AgentStateError(Exception):
    """Raised when the owner's reply does not fit the agent's current step."""


@dataclass(frozen=True)
class NeedContext:
    missing: Tuple[str, ...]


@dataclass(frozen=True)
class NeedConflictResolution:
    conflict: Conflict


@dataclass(frozen=True)
class ReviewPlan:
    plan: DailyPlan


@dataclass(frozen=True)
class Done:
    plan: DailyPlan


Turn = Union[NeedContext, NeedConflictResolution, ReviewPlan, Done]


class PlanAgent:
    def __init__(self, service: PlanningService) -> None:
        self._service = service
        self._owner: Optional[Owner] = None
        self._plan_date: Optional[date] = None
        self._context: Optional[PlanningContext] = None
        self._plan: Optional[DailyPlan] = None
        self._done = False

    @property
    def plan(self) -> Optional[DailyPlan]:
        return self._plan

    def start(self, owner: Owner, plan_date: date) -> Turn:
        self._owner, self._plan_date = owner, plan_date
        self._plan, self._done = None, False
        if not owner.availability:
            return NeedContext(("availability",))
        return self._propose()

    def provide_availability(self, windows: Sequence[AvailabilityWindow]) -> Turn:
        if self._owner is None or self._plan is not None:
            raise AgentStateError("Availability is only requested at the start of planning.")
        if not windows:
            return NeedContext(("availability",))
        self._owner.availability = list(windows)
        return self._propose()

    def resolve_conflict(self, option: ResolutionOption) -> Turn:
        plan = self._require_plan()
        if not plan.open_conflicts:
            raise AgentStateError("There is no open conflict to resolve.")
        resolution = ConflictResolution(plan.open_conflicts[0], option)
        self._plan = self._service.apply_resolution(plan, resolution, self._context)
        return self.current_turn()

    def request_changes(self, change: PlanChange) -> Turn:
        plan = self._require_plan()
        if plan.open_conflicts:
            raise AgentStateError("Resolve the open conflict before requesting other changes.")
        self._plan = self._service.revise_plan(plan, self._context, change)
        return self.current_turn()

    def approve(self) -> Turn:
        plan = self._require_plan()
        if plan.open_conflicts:
            raise AgentStateError("Resolve the open conflict before approving.")
        self._plan = self._service.approve(plan)
        self._service.save_approved_plan(self._plan)
        self._done = True
        return self.current_turn()

    def current_turn(self) -> Turn:
        plan = self._require_plan()
        if self._done:
            return Done(plan)
        if plan.open_conflicts:
            return NeedConflictResolution(plan.open_conflicts[0])
        return ReviewPlan(plan)

    def _propose(self) -> Turn:
        self._context = self._service.get_context(self._owner, self._plan_date)
        self._plan = self._service.propose_plan(self._context)
        return self.current_turn()

    def _require_plan(self) -> DailyPlan:
        if self._plan is None:
            raise AgentStateError("Planning has not started.")
        return self._plan
