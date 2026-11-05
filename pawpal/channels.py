"""Owner-facing I/O boundary plus a driver for blocking channels (CLI, scripted tests)."""

from dataclasses import dataclass
from datetime import date
from typing import Protocol, Sequence, Union

from pawpal.agent import Done, NeedConflictResolution, NeedContext, PlanAgent, ReviewPlan
from pawpal.models import AvailabilityWindow, Owner
from pawpal.plan import Conflict, DailyPlan, PlanChange, ResolutionOption


@dataclass(frozen=True)
class Approval:
    """The owner accepts the plan as shown."""


class OwnerChannel(Protocol):
    def ask_availability(self, plan_date: date) -> Sequence[AvailabilityWindow]: ...

    def ask_conflict(self, conflict: Conflict) -> ResolutionOption: ...

    def review(self, plan: DailyPlan) -> Union[Approval, PlanChange]: ...


def run_session(agent: PlanAgent, channel: OwnerChannel, owner: Owner, plan_date: date) -> DailyPlan:
    """Drive the agent to completion by relaying each turn to the owner."""
    turn = agent.start(owner, plan_date)
    while not isinstance(turn, Done):
        if isinstance(turn, NeedContext):
            turn = agent.provide_availability(channel.ask_availability(plan_date))
        elif isinstance(turn, NeedConflictResolution):
            turn = agent.resolve_conflict(channel.ask_conflict(turn.conflict))
        elif isinstance(turn, ReviewPlan):
            reply = channel.review(turn.plan)
            turn = agent.approve() if isinstance(reply, Approval) else agent.request_changes(reply)
    return turn.plan
