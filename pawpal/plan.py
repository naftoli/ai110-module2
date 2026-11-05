"""Immutable value objects describing a day's plan, its conflicts and the owner's choices."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional, Tuple

from pawpal.models import AvailabilityWindow, OwnerPreferences, Task


class PlanStatus(Enum):
    PROPOSED = "proposed"
    NEEDS_OWNER_INPUT = "needs_owner_input"
    REVISED = "revised"
    APPROVED = "approved"


@dataclass(frozen=True)
class ResolutionOption:
    action: str  # "shift" (move to the next free slot) or "skip" (leave unscheduled)
    task_index: int  # index into Conflict.tasks
    label: str


@dataclass(frozen=True)
class Conflict:
    kind: str  # "overlap" or "outside_availability"
    tasks: Tuple[Task, ...]
    options: Tuple[ResolutionOption, ...]
    description: str


@dataclass(frozen=True)
class ConflictResolution:
    conflict: Conflict
    option: ResolutionOption


@dataclass(frozen=True)
class ScheduledTask:
    task: Task
    starts_at: datetime
    ends_at: datetime


@dataclass(frozen=True)
class UnscheduledTask:
    task: Task
    reason: str


@dataclass(frozen=True)
class DailyPlan:
    plan_date: date
    scheduled: Tuple[ScheduledTask, ...] = ()
    unscheduled: Tuple[UnscheduledTask, ...] = ()
    open_conflicts: Tuple[Conflict, ...] = ()
    status: PlanStatus = PlanStatus.PROPOSED
    revision: int = 0


@dataclass(frozen=True)
class PlanChange:
    """An owner-requested edit: move a task to a new start time, or drop it from the plan."""

    task: Task
    new_start: Optional[datetime] = None
    skip: bool = False


@dataclass(frozen=True)
class PlanningContext:
    plan_date: date
    tasks: Tuple[Task, ...] = ()
    availability: Tuple[AvailabilityWindow, ...] = ()
    preferences: OwnerPreferences = field(default_factory=OwnerPreferences)


def format_plan(plan: DailyPlan) -> str:
    """Render a plan as plain text for the owner."""
    lines = [f"Plan for {plan.plan_date} [{plan.status.value}]"]
    if plan.scheduled:
        lines.append("")
        lines.append("Scheduled:")
        for item in plan.scheduled:
            t = item.task
            required = " [REQUIRED]" if t.is_required else ""
            lines.append(
                f"- {item.starts_at:%H:%M}-{item.ends_at:%H:%M} {t.title} ({t.pet_name}){required}"
            )
    if plan.unscheduled:
        lines.append("")
        lines.append("Not scheduled:")
        for item in plan.unscheduled:
            lines.append(f"- {item.task.title} ({item.task.pet_name}): {item.reason}")
    if plan.open_conflicts:
        lines.append("")
        lines.append("Open conflicts:")
        for conflict in plan.open_conflicts:
            lines.append(f"- {conflict.description}")
    return "\n".join(lines)
