import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Owner, Pet, Scheduler, Task


def make_owner(minutes, *tasks):
    owner = Owner("Sam", minutes)
    pet = Pet("Rex", "dog")
    owner.add_pet(pet)
    for t in tasks:
        pet.add_task(t)
    return owner


def task(title, minutes, priority=1, required=False, completed=False):
    return Task(title, minutes, priority, "", required, completed)


def titles(tasks):
    return [t.title for t in tasks]


def plan_for(owner):
    return Scheduler(owner).generate_plan()


def test_everything_fits():
    plan = plan_for(make_owner(60, task("Walk", 30, 2), task("Feed", 10, 3, True)))
    assert titles(plan.scheduled) == ["Feed", "Walk"]
    assert plan.skipped == []
    assert plan.total_minutes == 40


def test_required_tasks_come_first_regardless_of_priority():
    plan = plan_for(make_owner(60, task("Play", 10, 3), task("Meds", 5, 1, True)))
    assert titles(plan.scheduled) == ["Meds", "Play"]


def test_higher_priority_first_then_shorter_first():
    plan = plan_for(
        make_owner(
            100,
            task("Low", 5, 1),
            task("HighLong", 20, 3),
            task("HighShort", 10, 3),
            task("Mid", 5, 2),
        )
    )
    assert titles(plan.scheduled) == ["HighShort", "HighLong", "Mid", "Low"]


def test_optional_task_that_does_not_fit_is_skipped_with_reason():
    plan = plan_for(make_owner(30, task("Walk", 20, 2), task("Groom", 25, 1)))
    assert titles(plan.scheduled) == ["Walk"]
    assert titles([s.task for s in plan.skipped]) == ["Groom"]
    assert "25" in plan.skipped[0].reason and "10" in plan.skipped[0].reason
    assert plan.missed_required == []


def test_required_task_that_does_not_fit_is_skipped_and_flagged():
    plan = plan_for(make_owner(30, task("Insulin", 40, 3, True), task("Walk", 20, 2)))
    assert titles(plan.scheduled) == ["Walk"]
    assert titles([s.task for s in plan.missed_required]) == ["Insulin"]
    assert plan.total_minutes == 20


def test_required_tasks_get_time_before_optional_ones():
    plan = plan_for(make_owner(30, task("Walk", 25, 3), task("Meds", 20, 1, True)))
    assert titles(plan.scheduled) == ["Meds"]
    assert titles([s.task for s in plan.skipped]) == ["Walk"]


def test_shorter_task_still_fits_after_a_longer_one_is_skipped():
    plan = plan_for(make_owner(30, task("Big", 40, 3), task("Small", 10, 1)))
    assert titles(plan.scheduled) == ["Small"]


def test_task_exactly_filling_remaining_time_fits():
    plan = plan_for(make_owner(30, task("A", 10, 2), task("B", 20, 1)))
    assert titles(plan.scheduled) == ["A", "B"]
    assert plan.total_minutes == 30


def test_completed_tasks_are_ignored():
    plan = plan_for(make_owner(60, task("Done", 10, 3, completed=True), task("Walk", 10)))
    assert titles(plan.scheduled) == ["Walk"]
    assert plan.skipped == []


def test_no_tasks_gives_empty_plan():
    plan = plan_for(Owner("Sam", 60))
    assert plan.scheduled == [] and plan.skipped == [] and plan.total_minutes == 0


def test_zero_available_minutes_skips_everything():
    plan = plan_for(make_owner(0, task("Walk", 10), task("Meds", 5, 1, True)))
    assert plan.scheduled == []
    assert titles([s.task for s in plan.missed_required]) == ["Meds"]


def test_tasks_from_multiple_pets_are_combined():
    owner = Owner("Sam", 60)
    dog, cat = Pet("Rex", "dog"), Pet("Mia", "cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(task("Walk", 20, 2))
    cat.add_task(task("Play", 10, 3))
    plan = plan_for(owner)
    assert titles(plan.scheduled) == ["Play", "Walk"]
    assert [t.pet_name for t in plan.scheduled] == ["Mia", "Rex"]


def test_explain_reports_problem_for_missed_required_task():
    owner = make_owner(30, task("Insulin", 40, 3, True), task("Walk", 20, 2))
    scheduler = Scheduler(owner)
    text = scheduler.explain(scheduler.generate_plan())
    assert "PROBLEM" in text
    assert "Insulin" in text
    assert "[REQUIRED]" in text


def test_explain_has_no_problem_section_when_all_required_fit():
    owner = make_owner(60, task("Meds", 5, 1, True), task("Walk", 20, 2))
    scheduler = Scheduler(owner)
    text = scheduler.explain(scheduler.generate_plan())
    assert "PROBLEM" not in text
    assert "20 of 60" not in text and "25 of 60" in text


def test_task_helpers():
    t = task("Walk", 10)
    t.mark_complete()
    assert t.completed

    pet = Pet("Rex", "dog")
    pet.add_task(t)
    assert t.pet_name == "Rex"
    pet.remove_task(t)
    assert pet.tasks == []
    pet.remove_task(t)  # removing a missing task is a no-op
