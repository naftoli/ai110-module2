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


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def generate_plan(self) -> DailyPlan:
        """Required tasks first, then by priority (high to low), then shortest first.

        Required tasks are always scheduled, even if they exceed the time budget.
        Optional tasks are added only while they still fit.
        """
        pending = [t for t in self.owner.get_all_tasks() if not t.completed]
        ranked = sorted(
            pending,
            key=lambda t: (not t.is_required, -t.priority, t.duration_minutes),
        )

        plan = DailyPlan()
        remaining = self.owner.available_minutes
        for task in ranked:
            if task.is_required or task.duration_minutes <= remaining:
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
        if plan.total_minutes > budget:
            lines.append(
                f"Warning: required tasks exceed your available time by "
                f"{plan.total_minutes - budget} min."
            )

        if plan.scheduled:
            lines.append("")
            lines.append("Scheduled (in order):")
            for i, t in enumerate(plan.scheduled, 1):
                why = (
                    "required task, always scheduled first"
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
                lines.append(f"- {t.title} ({t.pet_name}): {s.reason}")
        return "\n".join(lines)
