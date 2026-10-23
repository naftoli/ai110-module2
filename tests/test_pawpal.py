# create a test to Verify that calling mark_complete() actually changes the task's status
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pawpal_system


def test_mark_complete():
    task = pawpal_system.Task(title="Test Task", duration_minutes=10, priority=1, pet_name="Test Pet")
    assert not task.completed
    task.mark_complete()
    assert task.completed


# create a test to Verify that adding a task to a Pet increases that pet's task count.
def test_add_task_increases_task_count():
    pet = pawpal_system.Pet(name="Test Pet", species="Test Species")
    initial_task_count = len(pet.tasks)
    task = pawpal_system.Task(title="Test Task", duration_minutes=10, priority=1, pet_name="Test Pet")
    pet.add_task(task)
    assert len(pet.tasks) == initial_task_count + 1


def test_task_creation_supports_all_recurrence_types_and_normalizes_time():
    once_task = pawpal_system.Task("Feed", 10, 2, "Rex", False, False, "2026-10-23 08:00")
    daily_task = pawpal_system.Task("Walk", 20, 3, "Rex", True, False, "2026-10-23 07:00", "daily")
    weekly_task = pawpal_system.Task("Vet", 45, 1, "Mia", False, False, "2026-10-23 09:00", "weekly")
    invalid_task = pawpal_system.Task("Brush", 5, 2, "Mia", False, False, "09:30", "monthly")

    assert once_task.recurrence == "once"
    assert once_task.time == datetime(2026, 10, 23, 8, 0)
    assert daily_task.time == datetime(2026, 10, 23, 7, 0)
    assert daily_task.next_instance().time == datetime(2026, 10, 24, 7, 0)
    assert weekly_task.next_instance().time == datetime(2026, 10, 30, 9, 0)
    assert invalid_task.recurrence == "once"
    assert invalid_task.due_date == invalid_task.time


def test_owner_can_track_tasks_across_multiple_pets():
    owner = pawpal_system.Owner("Sam", 180)
    dog = pawpal_system.Pet("Rex", "dog")
    cat = pawpal_system.Pet("Mia", "cat")
    owner.add_pet(dog)
    owner.add_pet(cat)

    dog_task = pawpal_system.Task("Walk", 20, 2, "Rex", False, False, datetime(2026, 10, 23, 8, 0))
    cat_task = pawpal_system.Task("Play", 15, 3, "Mia", False, False, datetime(2026, 10, 23, 9, 0))
    required_task = pawpal_system.Task("Meds", 10, 1, "Mia", True, False, datetime(2026, 10, 23, 7, 0))

    dog.add_task(dog_task)
    cat.add_task(cat_task)
    cat.add_task(required_task)

    all_tasks = owner.get_all_tasks()
    assert {task.title for task in all_tasks} == {"Walk", "Play", "Meds"}
    assert {task.pet_name for task in all_tasks} == {"Rex", "Mia"}


def test_scheduler_prioritizes_required_tasks_and_handles_time_conflicts_for_multiple_pets():
    owner = pawpal_system.Owner("Sam", 120)
    dog = pawpal_system.Pet("Rex", "dog")
    cat = pawpal_system.Pet("Mia", "cat")
    owner.add_pet(dog)
    owner.add_pet(cat)

    dog.add_task(pawpal_system.Task("Walk", 20, 2, "Rex", False, False, datetime(2026, 10, 23, 10, 0)))
    cat.add_task(pawpal_system.Task("Groom", 15, 2, "Mia", False, False, datetime(2026, 10, 23, 10, 0)))
    dog.add_task(pawpal_system.Task("Meds", 10, 3, "Rex", True, False, datetime(2026, 10, 23, 9, 0)))
    cat.add_task(pawpal_system.Task("Feed", 25, 1, "Mia", False, False, datetime(2026, 10, 23, 11, 0)))

    plan = pawpal_system.Scheduler(owner).generate_plan()

    assert [task.title for task in plan.scheduled] == ["Meds", "Groom", "Walk", "Feed"]
    assert any("Walk" in warning and "Groom" in warning for warning in plan.warnings)


def test_scheduler_edge_cases_with_zero_time_and_completed_recurring_tasks():
    owner = pawpal_system.Owner("Sam", 0)
    pet = pawpal_system.Pet("Rex", "dog")
    owner.add_pet(pet)

    pet.add_task(pawpal_system.Task("Meds", 5, 3, "Rex", True, False, datetime(2026, 10, 23, 8, 0), "daily"))
    pet.add_task(pawpal_system.Task("Checkup", 10, 2, "Rex", False, False, datetime(2026, 10, 23, 8, 0)))

    plan = pawpal_system.Scheduler(owner).generate_plan()
    assert plan.scheduled == []
    assert [item.task.title for item in plan.missed_required] == ["Meds"]
    assert any("WARNING" in warning for warning in plan.warnings)

    pet2 = pawpal_system.Pet("Mia", "cat")
    task = pawpal_system.Task("Brush", 15, 2, "Mia", False, False, datetime(2026, 10, 23, 8, 0), "weekly")
    pet2.add_task(task)
    pet2.complete_task(task)
    assert len(pet2.tasks) == 2
    assert pet2.tasks[-1].time == datetime(2026, 10, 30, 8, 0)
    assert pet2.tasks[-1].recurrence == "weekly"
    assert pet2.tasks[-1].completed is False
