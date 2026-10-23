# create a test to Verify that calling mark_complete() actually changes the task's status
import os
import sys

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
