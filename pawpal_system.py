"""PawPal+ backend class stubs, generated from diagrams/uml.mmd."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Union


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: int  # 1 (low) to 3 (high)
    pet_name: str
    is_required: bool = False
    completed: bool = False
    time: Union[str, datetime] = "00:00"
    recurrence: str = "once"
    due_date: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Normalize recurrence and ensure each task has a real datetime value."""
        if self.recurrence not in {"once", "daily", "weekly"}:
            self.recurrence = "once"
        if isinstance(self.time, str):
            for fmt in ("%Y-%m-%d %H:%M", "%H:%M"):
                try:
                    self.time = datetime.strptime(self.time, fmt)
                    break
                except ValueError:
                    continue
            else:
                self.time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if self.due_date is None:
            self.due_date = self.time
        elif isinstance(self.due_date, str):
            for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    self.due_date = datetime.strptime(self.due_date, fmt)
                    break
                except ValueError:
                    continue

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.completed = True

    def next_instance(self) -> Optional["Task"]:
        """Create the next recurring instance for the task using a real datetime offset."""
        if self.recurrence not in {"daily", "weekly"}:
            return None
        delta_days = 1 if self.recurrence == "daily" else 7
        next_time = self.time + timedelta(days=delta_days)
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            pet_name=self.pet_name,
            is_required=self.is_required,
            completed=False,
            time=next_time,
            recurrence=self.recurrence,
            due_date=next_time,
        )


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet and assign it to the pet."""
        task.pet_name = self.name
        if task.due_date is None:
            task.due_date = task.time
        self.tasks.append(task)

    def complete_task(self, task: Task) -> Optional[Task]:
        """Mark a task complete and recreate it for the next recurring cycle if needed."""
        if task not in self.tasks:
            return None
        task.mark_complete()
        next_task = task.next_instance()
        if next_task is not None:
            self.tasks.append(next_task)
            return next_task
        return None

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet if it exists."""
        if task in self.tasks:
            self.tasks.remove(task)


@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's list of pets."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Return all tasks owned by this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


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
