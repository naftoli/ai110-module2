"""Original minutes-budget planner, kept unchanged so existing callers and tests keep working."""

from dataclasses import dataclass, field
from typing import List, Optional

from pawpal.models import Owner, Task


@dataclass
class SkippedTask:
    task: Task
    reason: str


@dataclass
class DailyPlan:
    scheduled: List[Task] = field(default_factory=list)
    skipped: List[SkippedTask] = field(default_factory=list)
    total_minutes: int = 0
    warnings: List[str] = field(default_factory=list)

    @property
    def missed_required(self) -> List[SkippedTask]:
        """Required tasks that could not be scheduled (a problem the owner must resolve)."""
        return [s for s in self.skipped if s.task.is_required]


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        """Create a scheduler for the given owner."""
        self.owner = owner

    def find_time_conflicts(self, tasks: Optional[List[Task]] = None) -> List[str]:
        """Return warnings for tasks that share the same datetime."""
        pending = tasks if tasks is not None else [t for t in self.owner.get_all_tasks() if not t.completed]
        by_time = {}
        for task in pending:
            by_time.setdefault(task.time, []).append(task)

        warnings = []
        for scheduled_time, items in sorted(by_time.items(), key=lambda pair: pair[0]):
            if len(items) > 1:
                names = ", ".join(f"{item.title} ({item.pet_name})" for item in items)
                warnings.append(f"WARNING: {names} all scheduled for {scheduled_time}.")
        return warnings

    def _task_sort_key(self, task: Task):
        """Return a consistent ordering key for scheduling decisions.

        Required tasks always come first, then higher priority, then earlier time,
        then shorter duration as a final tiebreaker.
        """
        return (not task.is_required, -task.priority, task.time, task.duration_minutes)

    def generate_plan(self) -> DailyPlan:
        """Required tasks first, then by priority, then by time, then by duration.

        Any task, required or not, is added only if it fits in the remaining time.
        A required task that does not fit is skipped and flagged in
        DailyPlan.missed_required so the owner can be told.
        """
        pending = [t for t in self.owner.get_all_tasks() if not t.completed]
        ranked = sorted(pending, key=self._task_sort_key)

        plan = DailyPlan(warnings=self.find_time_conflicts(pending))
        remaining = self.owner.available_minutes
        for task in ranked:
            if task.duration_minutes <= remaining:
                plan.scheduled.append(task)
                plan.total_minutes += task.duration_minutes
                remaining -= task.duration_minutes
            else:
                plan.skipped.append(
                    SkippedTask(
                        task,
                        f"needs {task.duration_minutes} min but only "
                        f"{max(remaining, 0)} min were left",
                    )
                )
        return plan

    def explain(self, plan: DailyPlan) -> str:
        """Return a human-readable explanation of the generated plan."""
        budget = self.owner.available_minutes
        lines = [
            f"Plan for {self.owner.name}: {plan.total_minutes} of {budget} "
            f"available minutes used."
        ]

        warnings = getattr(plan, "warnings", [])
        if warnings:
            lines.append("")
            lines.append("TIME CONFLICTS:")
            for warning in warnings:
                lines.append(f"- {warning}")

        if plan.missed_required:
            lines.append("")
            lines.append("PROBLEM: not enough time for required tasks:")
            for s in plan.missed_required:
                t = s.task
                lines.append(
                    f"- {t.title} ({t.pet_name}, {t.duration_minutes} min, {t.time}): {s.reason}. "
                    f"Free up time or shorten other tasks."
                )

        if plan.scheduled:
            lines.append("")
            lines.append("Scheduled (in order):")
            for i, t in enumerate(plan.scheduled, 1):
                why = (
                    "required task, scheduled first"
                    if t.is_required
                    else f"priority {t.priority}, time {t.time}, fit in the remaining time"
                )
                lines.append(
                    f"{i}. {t.title} ({t.pet_name}, {t.duration_minutes} min, {t.time}): {why}"
                )

        if plan.skipped:
            lines.append("")
            lines.append("Skipped:")
            for s in plan.skipped:
                t = s.task
                flag = " [REQUIRED]" if t.is_required else ""
                lines.append(f"- {t.title} ({t.pet_name}){flag} at {t.time}: {s.reason}")
        return "\n".join(lines)
