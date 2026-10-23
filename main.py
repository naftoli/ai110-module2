from datetime import datetime

import pawpal_system

# Create owner and pets
owner = pawpal_system.Owner(name="Alice", available_minutes=120)
dog = pawpal_system.Pet(name="Buddy", species="Dog")
cat = pawpal_system.Pet(name="Whiskers", species="Cat")
owner.add_pet(dog)
owner.add_pet(cat)

shared_time = datetime(2026, 10, 23, 8, 0)

# IMPORTANT: add the later-time task first to show insertion order does NOT matter.
# The scheduler sorts by: required -> priority -> time -> duration.
evening_walk = pawpal_system.Task(
    title="Evening walk",
    duration_minutes=30,
    priority=2,
    pet_name="Buddy",
    is_required=True,
    time=datetime(2026, 10, 23, 18, 0),
)
morning_walk = pawpal_system.Task(
    title="Morning walk",
    duration_minutes=30,
    priority=2,
    pet_name="Buddy",
    is_required=True,
    time=datetime(2026, 10, 23, 8, 0),
)
feed_cat = pawpal_system.Task(
    title="Feed Whiskers",
    duration_minutes=15,
    priority=2,
    pet_name="Whiskers",
    is_required=True,
    time=datetime(2026, 10, 23, 9, 0),
)
play_with_dog = pawpal_system.Task(
    title="Play with Buddy",
    duration_minutes=20,
    priority=1,
    pet_name="Buddy",
    time=datetime(2026, 10, 23, 11, 0),
)
# Add a second task at the exact same date/time to demonstrate the warning.
brush_whiskers = pawpal_system.Task(
    title="Brush Whiskers",
    duration_minutes=10,
    priority=1,
    pet_name="Whiskers",
    time=shared_time,
)

# Add tasks in intentionally "wrong" order
# Later time is added first, but scheduler should still order them by time.
dog.add_task(evening_walk)
dog.add_task(morning_walk)
dog.add_task(play_with_dog)
cat.add_task(feed_cat)
cat.add_task(brush_whiskers)

scheduler = pawpal_system.Scheduler(owner)
plan = scheduler.generate_plan()
print("Tasks added in this order: Evening walk, Morning walk, Play, Feed, Brush Whiskers")
print("Sorted plan result:")
print(scheduler.explain(plan))