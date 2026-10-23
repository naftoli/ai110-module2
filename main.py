import pawpal_system

# create owner
owner = pawpal_system.Owner(name="Alice", available_minutes=120)

# create pets
dog = pawpal_system.Pet(name="Buddy", species="Dog")
cat = pawpal_system.Pet(name="Whiskers", species="Cat")

# add pets to owner
owner.add_pet(dog)
owner.add_pet(cat)

# create tasks
walk_dog = pawpal_system.Task(title="Walk Buddy", duration_minutes=30, priority=3, pet_name="Buddy", is_required=True)
feed_cat = pawpal_system.Task(title="Feed Whiskers", duration_minutes=15, priority=2, pet_name="Whiskers", is_required=True)
play_with_dog = pawpal_system.Task(title="Play with Buddy", duration_minutes=20, priority=1, pet_name="Buddy")

# add tasks to pets
dog.add_task(walk_dog)
dog.add_task(play_with_dog)
cat.add_task(feed_cat)

scheduler = pawpal_system.Scheduler(owner)
plan = scheduler.generate_plan()
print(scheduler.explain(plan))