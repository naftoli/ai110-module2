"""Storage boundary for tasks and approved plans."""

from datetime import date
from typing import Dict, Protocol, Tuple

from pawpal.models import Owner, Task
from pawpal.plan import DailyPlan


class TaskRepository(Protocol):
    def get_tasks_for_date(self, owner: Owner, plan_date: date) -> Tuple[Task, ...]: ...

    def save_approved_plan(self, plan: DailyPlan) -> None: ...


class InMemoryTaskRepository:
    """Reads tasks from the owner's pets and keeps approved plans in memory."""

    def __init__(self) -> None:
        self._saved: Dict[date, DailyPlan] = {}

    def get_tasks_for_date(self, owner: Owner, plan_date: date) -> Tuple[Task, ...]:
        return tuple(
            t for t in owner.get_all_tasks() if not t.completed and t.time.date() == plan_date
        )

    def save_approved_plan(self, plan: DailyPlan) -> None:
        self._saved[plan.plan_date] = plan

    def get_saved_plan(self, plan_date: date) -> DailyPlan:
        return self._saved[plan_date]
