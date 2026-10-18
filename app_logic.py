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
        raise NotImplementedError


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        raise NotImplementedError

    def remove_task(self, task: Task) -> None:
        raise NotImplementedError


@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        raise NotImplementedError

    def get_all_tasks(self) -> List[Task]:
        raise NotImplementedError


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
        raise NotImplementedError

    def explain(self, plan: DailyPlan) -> str:
        raise NotImplementedError
