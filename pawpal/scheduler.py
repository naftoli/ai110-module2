"""Pure, deterministic scheduling: places tasks, detects conflicts, never resolves them."""

from datetime import datetime, time, timedelta
from typing import List, Optional, Tuple

from pawpal.models import Task
from pawpal.plan import (
    Conflict,
    DailyPlan,
    PlanningContext,
    ResolutionOption,
    ScheduledTask,
)


def _clashes(a: ScheduledTask, b: ScheduledTask, gap: timedelta) -> bool:
    return a.starts_at < b.ends_at + gap and b.starts_at < a.ends_at + gap


def _within_availability(item: ScheduledTask, context: PlanningContext) -> bool:
    if not context.availability:
        return True
    return any(w.starts_at <= item.starts_at and item.ends_at <= w.ends_at for w in context.availability)


def _options_for(tasks: Tuple[Task, ...]) -> Tuple[ResolutionOption, ...]:
    options = []
    for index, task in enumerate(tasks):
        name = f"'{task.title}' ({task.pet_name})"
        if not task.fixed_time:
            options.append(ResolutionOption("shift", index, f"Move {name} to the next free slot"))
        options.append(ResolutionOption("skip", index, f"Leave {name} unscheduled"))
    return tuple(options)


class Scheduler:
    @staticmethod
    def sort_key(task: Task):
        """Required first, then higher priority, then earlier time, then shorter duration."""
        return (not task.is_required, -task.priority, task.time, task.duration_minutes)

    def build_candidate(self, context: PlanningContext) -> DailyPlan:
        """Place every pending task for the date at its requested time, without resolving clashes."""
        pending = [
            t for t in context.tasks if not t.completed and t.time.date() == context.plan_date
        ]
        scheduled = tuple(
            ScheduledTask(t, t.time, t.time + timedelta(minutes=t.duration_minutes))
            for t in sorted(pending, key=self.sort_key)
        )
        return DailyPlan(plan_date=context.plan_date, scheduled=scheduled)

    def find_conflicts(self, plan: DailyPlan, context: PlanningContext) -> List[Conflict]:
        """Report overlaps (including the owner's required break) and tasks outside availability."""
        gap = timedelta(minutes=context.preferences.break_minutes)
        items = sorted(plan.scheduled, key=lambda s: s.starts_at)
        conflicts = []
        for i, first in enumerate(items):
            for second in items[i + 1 :]:
                if _clashes(first, second, gap):
                    tasks = (first.task, second.task)
                    conflicts.append(
                        Conflict(
                            kind="overlap",
                            tasks=tasks,
                            options=_options_for(tasks),
                            description=(
                                f"'{first.task.title}' ({first.task.pet_name}, "
                                f"{first.starts_at:%H:%M}-{first.ends_at:%H:%M}) clashes with "
                                f"'{second.task.title}' ({second.task.pet_name}, "
                                f"{second.starts_at:%H:%M}-{second.ends_at:%H:%M})"
                                + (f" given the {context.preferences.break_minutes} min break" if gap else "")
                            ),
                        )
                    )
            if not _within_availability(first, context):
                tasks = (first.task,)
                conflicts.append(
                    Conflict(
                        kind="outside_availability",
                        tasks=tasks,
                        options=_options_for(tasks),
                        description=(
                            f"'{first.task.title}' ({first.task.pet_name}, "
                            f"{first.starts_at:%H:%M}-{first.ends_at:%H:%M}) is outside your available time"
                        ),
                    )
                )
        return conflicts

    def find_free_slot(
        self, plan: DailyPlan, item: ScheduledTask, context: PlanningContext
    ) -> Optional[ScheduledTask]:
        """Earliest placement for `item` at or after its current start that clashes with nothing."""
        gap = timedelta(minutes=context.preferences.break_minutes)
        duration = item.ends_at - item.starts_at
        others = [s for s in plan.scheduled if s is not item]
        day_end = datetime.combine(plan.plan_date, time.min) + timedelta(days=1)

        candidates = {o.ends_at + gap for o in others}
        candidates |= {w.starts_at for w in context.availability}
        for start in sorted(c for c in candidates if c > item.starts_at):
            moved = ScheduledTask(item.task, start, start + duration)
            if moved.ends_at > day_end:
                break
            if _within_availability(moved, context) and not any(_clashes(moved, o, gap) for o in others):
                return moved
        return None
