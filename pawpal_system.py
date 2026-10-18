"""PawPal+ backend class stubs, generated from diagrams/uml.mmd."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: int  # 1 (low) to 3 (high)
    pet_name: str
    is_required: bool = False
    completed: bool = False

    def mark_complete(self) -> None:
        self.completed = True


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        if task in self.tasks:
            self.tasks.remove(task)


@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
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

    @property
    def missed_required(self) -> List[SkippedTask]:
        """Required tasks that could not be scheduled (a problem the owner must resolve)."""
        return [s for s in self.skipped if s.task.is_required]


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def generate_plan(self) -> DailyPlan:
        """Required tasks first, then by priority (high to low), then shortest first.

        Any task, required or not, is added only if it fits in the remaining time.
        A required task that does not fit is skipped and flagged in
        DailyPlan.missed_required so the owner can be told.
        """
        pending = [t for t in self.owner.get_all_tasks() if not t.completed]
        ranked = sorted(
            pending,
            key=lambda t: (not t.is_required, -t.priority, t.duration_minutes),
        )

        plan = DailyPlan()
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
        budget = self.owner.available_minutes
        lines = [
            f"Plan for {self.owner.name}: {plan.total_minutes} of {budget} "
            f"available minutes used."
        ]
        if plan.missed_required:
            lines.append("")
            lines.append("PROBLEM: not enough time for required tasks:")
            for s in plan.missed_required:
                t = s.task
                lines.append(
                    f"- {t.title} ({t.pet_name}, {t.duration_minutes} min): {s.reason}. "
                    f"Free up time or shorten other tasks."
                )

        if plan.scheduled:
            lines.append("")
            lines.append("Scheduled (in order):")
            for i, t in enumerate(plan.scheduled, 1):
                why = (
                    "required task, scheduled first"
                    if t.is_required
                    else f"priority {t.priority}, fit in the remaining time"
                )
                lines.append(
                    f"{i}. {t.title} ({t.pet_name}, {t.duration_minutes} min): {why}"
                )

        if plan.skipped:
            lines.append("")
            lines.append("Skipped:")
            for s in plan.skipped:
                t = s.task
                flag = " [REQUIRED]" if t.is_required else ""
                lines.append(f"- {t.title} ({t.pet_name}){flag}: {s.reason}")
        return "\n".join(lines)
