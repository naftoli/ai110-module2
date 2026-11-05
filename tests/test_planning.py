import os
import sys
from datetime import date, datetime, timedelta

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal.agent import AgentStateError, Done, NeedConflictResolution, NeedContext, PlanAgent, ReviewPlan
from pawpal.channels import Approval, run_session
from pawpal.models import AvailabilityWindow, Owner, OwnerPreferences, Pet, Task
from pawpal.plan import PlanChange, PlanningContext, PlanStatus
from pawpal.repository import InMemoryTaskRepository
from pawpal.scheduler import Scheduler
from pawpal.service import PlanningError, PlanningService

DAY = date(2026, 10, 23)


def at(hour, minute=0):
    return datetime(2026, 10, 23, hour, minute)


def make_task(title, hour, minutes=30, minute=0, required=False, fixed=False, pet="Rex"):
    return Task(title, minutes, 2, pet, required, False, at(hour, minute), "once", None, fixed)


def window(start_hour, end_hour):
    return AvailabilityWindow(at(start_hour), at(end_hour))


def setup(*tasks, windows=(), break_minutes=0):
    owner = Owner("Sam", 120)
    pet = Pet("Rex", "dog")
    owner.add_pet(pet)
    for t in tasks:
        pet.add_task(t)
    owner.availability = list(windows)
    owner.preferences = OwnerPreferences(break_minutes)
    repo = InMemoryTaskRepository()
    return owner, repo, PlanningService(repo)


def titles(plan):
    return [s.task.title for s in plan.scheduled]


# Scheduler: pure detection, never resolves

def test_scheduler_places_tasks_at_requested_times_and_ignores_other_dates():
    other_day = Task("Later", 10, 2, "Rex", time=datetime(2026, 10, 24, 8, 0))
    context = PlanningContext(DAY, (make_task("Walk", 9), other_day, make_task("Feed", 8)))
    plan = Scheduler().build_candidate(context)
    assert titles(plan) == ["Feed", "Walk"]
    assert plan.scheduled[0].ends_at - plan.scheduled[0].starts_at == timedelta(minutes=30)


def test_scheduler_reports_overlap_but_does_not_move_anything():
    walk, groom = make_task("Walk", 8), make_task("Groom", 8, minute=15)
    context = PlanningContext(DAY, (walk, groom))
    scheduler = Scheduler()
    plan = scheduler.build_candidate(context)
    conflicts = scheduler.find_conflicts(plan, context)
    assert len(conflicts) == 1 and conflicts[0].kind == "overlap"
    assert {s.starts_at for s in plan.scheduled} == {at(8), at(8, 15)}


def test_back_to_back_tasks_do_not_conflict_without_a_break_but_do_with_one():
    walk, groom = make_task("Walk", 8), make_task("Groom", 8, minute=30)
    scheduler = Scheduler()
    plan = scheduler.build_candidate(PlanningContext(DAY, (walk, groom)))
    assert scheduler.find_conflicts(plan, PlanningContext(DAY, (walk, groom))) == []
    with_break = PlanningContext(DAY, (walk, groom), preferences=OwnerPreferences(15))
    assert len(scheduler.find_conflicts(plan, with_break)) == 1


def test_task_outside_availability_is_a_conflict():
    walk = make_task("Walk", 6)
    context = PlanningContext(DAY, (walk,), (window(8, 12),))
    scheduler = Scheduler()
    conflicts = scheduler.find_conflicts(scheduler.build_candidate(context), context)
    assert [c.kind for c in conflicts] == ["outside_availability"]


def test_fixed_time_task_is_not_offered_a_move():
    walk, vet = make_task("Walk", 8), make_task("Vet", 8, fixed=True)
    context = PlanningContext(DAY, (walk, vet))
    scheduler = Scheduler()
    (conflict,) = scheduler.find_conflicts(scheduler.build_candidate(context), context)
    actions = {(o.action, conflict.tasks[o.task_index].title) for o in conflict.options}
    assert ("shift", "Vet") not in actions and ("shift", "Walk") in actions


# Service: approval gates

def test_conflicting_plan_needs_owner_input_and_cannot_be_approved_or_saved():
    owner, repo, service = setup(make_task("Walk", 8), make_task("Groom", 8, minute=15), windows=[window(7, 12)])
    plan = service.propose_plan(service.get_context(owner, DAY))
    assert plan.status is PlanStatus.NEEDS_OWNER_INPUT
    with pytest.raises(PlanningError):
        service.approve(plan)
    with pytest.raises(PlanningError):
        service.save_approved_plan(plan)


def test_save_rejects_a_plan_that_is_not_approved():
    owner, repo, service = setup(make_task("Walk", 8), windows=[window(7, 12)])
    plan = service.propose_plan(service.get_context(owner, DAY))
    assert plan.status is PlanStatus.PROPOSED
    with pytest.raises(PlanningError):
        service.save_approved_plan(plan)
    service.save_approved_plan(service.approve(plan))
    assert repo.get_saved_plan(DAY).status is PlanStatus.APPROVED


def test_apply_resolution_rejects_unoffered_or_stale_choices():
    owner, repo, service = setup(make_task("Walk", 8), make_task("Groom", 8, minute=15), windows=[window(7, 12)])
    context = service.get_context(owner, DAY)
    plan = service.propose_plan(context)
    conflict = plan.open_conflicts[0]
    from pawpal.plan import ConflictResolution, ResolutionOption

    with pytest.raises(PlanningError):
        service.apply_resolution(plan, ConflictResolution(conflict, ResolutionOption("skip", 0, "made up")), context)
    resolved = service.apply_resolution(plan, ConflictResolution(conflict, conflict.options[0]), context)
    with pytest.raises(PlanningError):
        service.apply_resolution(resolved, ConflictResolution(conflict, conflict.options[0]), context)


def test_shift_moves_task_to_next_free_slot_and_clears_conflict():
    owner, repo, service = setup(make_task("Walk", 8), make_task("Groom", 8, minute=15), windows=[window(7, 12)])
    context = service.get_context(owner, DAY)
    plan = service.propose_plan(context)
    conflict = plan.open_conflicts[0]
    shift_groom = next(o for o in conflict.options if o.action == "shift" and conflict.tasks[o.task_index].title == "Groom")
    from pawpal.plan import ConflictResolution

    plan = service.apply_resolution(plan, ConflictResolution(conflict, shift_groom), context)
    assert plan.status is PlanStatus.PROPOSED and plan.open_conflicts == ()
    assert {s.task.title: s.starts_at for s in plan.scheduled} == {"Walk": at(8), "Groom": at(8, 30)}
    assert owner.get_all_tasks()[1].time == at(8, 15)  # stored task is untouched


def test_skip_moves_task_to_unscheduled_with_reason():
    owner, repo, service = setup(make_task("Walk", 8), make_task("Groom", 8, minute=15), windows=[window(7, 12)])
    context = service.get_context(owner, DAY)
    plan = service.propose_plan(context)
    conflict = plan.open_conflicts[0]
    skip = next(o for o in conflict.options if o.action == "skip")
    from pawpal.plan import ConflictResolution

    plan = service.apply_resolution(plan, ConflictResolution(conflict, skip), context)
    assert len(plan.scheduled) == 1 and plan.unscheduled[0].reason == "left unscheduled by owner"


def test_revision_that_creates_a_conflict_goes_back_to_the_owner():
    walk, groom = make_task("Walk", 8), make_task("Groom", 10)
    owner, repo, service = setup(walk, groom, windows=[window(7, 12)])
    context = service.get_context(owner, DAY)
    plan = service.propose_plan(context)
    revised = service.revise_plan(plan, context, PlanChange(groom, new_start=at(8, 10)))
    assert revised.status is PlanStatus.NEEDS_OWNER_INPUT and revised.revision == 1


# Agent: owner stays in the loop

class ScriptedChannel:
    def __init__(self, availability, conflict_choice, reviews):
        self.availability, self.conflict_choice, self.reviews = availability, conflict_choice, list(reviews)
        self.conflicts_asked = 0

    def ask_availability(self, plan_date):
        return self.availability

    def ask_conflict(self, conflict):
        self.conflicts_asked += 1
        return next(o for o in conflict.options if o.action == self.conflict_choice)

    def review(self, plan):
        return self.reviews.pop(0)


def test_agent_asks_for_availability_then_conflicts_then_approval_and_saves():
    owner, repo, service = setup(make_task("Walk", 8), make_task("Groom", 8, minute=15))
    channel = ScriptedChannel([window(7, 12)], "shift", [Approval()])
    plan = run_session(PlanAgent(service), channel, owner, DAY)
    assert channel.conflicts_asked == 1
    assert plan.status is PlanStatus.APPROVED
    assert repo.get_saved_plan(DAY) == plan


def test_agent_loops_on_requested_changes_until_approval():
    walk = make_task("Walk", 8)
    owner, repo, service = setup(walk, windows=[window(7, 12)])
    channel = ScriptedChannel([], "skip", [PlanChange(walk, new_start=at(9)), Approval()])
    plan = run_session(PlanAgent(service), channel, owner, DAY)
    assert plan.scheduled[0].starts_at == at(9) and plan.revision == 1


def test_agent_never_resolves_a_conflict_on_its_own():
    owner, repo, service = setup(make_task("Walk", 8), make_task("Groom", 8, minute=15), windows=[window(7, 12)])
    agent = PlanAgent(service)
    turn = agent.start(owner, DAY)
    assert isinstance(turn, NeedConflictResolution)
    assert len(agent.plan.scheduled) == 2
    with pytest.raises(AgentStateError):
        agent.approve()
    assert repo._saved == {}


def test_agent_asks_for_missing_availability_first():
    owner, repo, service = setup(make_task("Walk", 8))
    agent = PlanAgent(service)
    assert isinstance(agent.start(owner, DAY), NeedContext)
    assert isinstance(agent.provide_availability([window(7, 12)]), ReviewPlan)
    assert isinstance(agent.approve(), Done)
