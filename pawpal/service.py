"""Orchestrates the scheduler and repository and enforces the human-approval rules."""

from dataclasses import replace
from datetime import date
from typing import Optional

from pawpal.models import Owner
from pawpal.plan import (
    ConflictResolution,
    DailyPlan,
    PlanChange,
    PlanningContext,
    PlanStatus,
    ScheduledTask,
    UnscheduledTask,
)
from pawpal.repository import TaskRepository
from pawpal.scheduler import Scheduler


class PlanningError(Exception):
    """Raised when an operation would break a planning rule."""


class PlanningService:
    def __init__(self, repository: TaskRepository, scheduler: Optional[Scheduler] = None) -> None:
        self._repository = repository
        self._scheduler = scheduler or Scheduler()

    def get_context(self, owner: Owner, plan_date: date) -> PlanningContext:
        return PlanningContext(
            plan_date=plan_date,
            tasks=self._repository.get_tasks_for_date(owner, plan_date),
            availability=tuple(owner.availability),
            preferences=owner.preferences,
        )

    def propose_plan(self, context: PlanningContext) -> DailyPlan:
        return self._finalize(self._scheduler.build_candidate(context), context)

    def apply_resolution(
        self, plan: DailyPlan, resolution: ConflictResolution, context: PlanningContext
    ) -> DailyPlan:
        """Apply the owner's chosen option for one open conflict."""
        conflict, option = resolution.conflict, resolution.option
        if conflict not in plan.open_conflicts:
            raise PlanningError("That conflict is not open on this plan.")
        if option not in conflict.options:
            raise PlanningError("That option was not offered for this conflict.")

        item = self._find_item(plan, conflict.tasks[option.task_index])
        if option.action == "skip":
            return self._finalize(self._without(plan, item, "left unscheduled by owner"), context)

        moved = self._scheduler.find_free_slot(plan, item, context)
        if moved is None:
            return self._finalize(self._without(plan, item, "no free slot was available to move it to"), context)
        return self._finalize(self._replacing(plan, item, moved), context)

    def revise_plan(self, plan: DailyPlan, context: PlanningContext, change: PlanChange) -> DailyPlan:
        """Apply an owner-requested edit; any conflicts it creates go back to the owner."""
        item = self._find_item(plan, change.task)
        if change.skip:
            revised = self._without(plan, item, "left unscheduled by owner")
        elif change.new_start is not None:
            duration = item.ends_at - item.starts_at
            revised = self._replacing(
                plan, item, ScheduledTask(item.task, change.new_start, change.new_start + duration)
            )
        else:
            raise PlanningError("A change must move the task or skip it.")
        return self._finalize(replace(revised, revision=plan.revision + 1), context)

    def approve(self, plan: DailyPlan) -> DailyPlan:
        if plan.open_conflicts:
            raise PlanningError("Resolve every open conflict before approving the plan.")
        return replace(plan, status=PlanStatus.APPROVED)

    def save_approved_plan(self, plan: DailyPlan) -> None:
        if plan.status is not PlanStatus.APPROVED:
            raise PlanningError("Only an approved plan can be saved.")
        self._repository.save_approved_plan(plan)

    def _finalize(self, plan: DailyPlan, context: PlanningContext) -> DailyPlan:
        plan = replace(plan, scheduled=tuple(sorted(plan.scheduled, key=lambda s: s.starts_at)))
        conflicts = tuple(self._scheduler.find_conflicts(plan, context))
        if conflicts:
            status = PlanStatus.NEEDS_OWNER_INPUT
        elif plan.revision > 0:
            status = PlanStatus.REVISED
        else:
            status = PlanStatus.PROPOSED
        return replace(plan, open_conflicts=conflicts, status=status)

    @staticmethod
    def _find_item(plan: DailyPlan, task) -> ScheduledTask:
        for item in plan.scheduled:
            if item.task is task:
                return item
        raise PlanningError(f"'{task.title}' is not scheduled in this plan.")

    @staticmethod
    def _without(plan: DailyPlan, item: ScheduledTask, reason: str) -> DailyPlan:
        return replace(
            plan,
            scheduled=tuple(s for s in plan.scheduled if s is not item),
            unscheduled=plan.unscheduled + (UnscheduledTask(item.task, reason),),
        )

    @staticmethod
    def _replacing(plan: DailyPlan, item: ScheduledTask, new_item: ScheduledTask) -> DailyPlan:
        return replace(
            plan, scheduled=tuple(new_item if s is item else s for s in plan.scheduled)
        )
