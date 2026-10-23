# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

Task Class
Attributes: title, duration_minutes, priority (1–3), pet_name, is_required (meds, feeding), completed
Methods: mark_complete()

Pet Class
Attributes: name, species, tasks: list[Task]
Methods: add_task(), remove_task()

Owner Class
Attributes: name, available_minutes, pets: list[Pet]
Methods: add_pet(), get_all_tasks()

Scheduler Class
Attributes: owner
Methods:
generate_plan() -> DailyPlan, which sorts required tasks first, then by priority, then fits them into available_minutes
explain(plan) -> str, which gives a reason for each task included or skipped

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

One change was to add another class called SkippedTask b/c it has more than one attribute and was originally going to be a tuple but is easier to change/extend if needed by having it as a class.

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

First checks whether it's required or not, then checks the priority, then the time (11am, 2pm), and then finally
if it fits into the amount of time the owner has.

The time aspect was something I added b/c I noticed that when giving it 2 tasks, for example to eat lunch and take an afternoon walk, and it was obvious that the eating lunch should be first. However, since there was no time associated with the scheduler, since the afternoon walk was entered first, it was shown first.

That's when it became obvious that we need to also have a time element and I used AI to help me flesh out how it would work and add it to the code.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

One big trade off is the ability to fit in the maximum number of tasks in the available time. Instead, we are adding tasks based on a strict set of rules, which works fine for the pet system but may not be as good in other situations.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

So I asked the agent to help me identify the classes with their attributes and methods needed for this project.

Here's what I put in:
I would like to create an app that does the following:
A busy pet owner needs help staying consistent with pet care. They want an assistant that can:
Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
Consider constraints (time available, priority, owner preferences)
Produce a daily plan and explain why it chose that plan

It first provided a pretty sophisticated outline of the classes, attributes, and methods needed for the project. I asked it to simplify it which it did.

The original plan was as follows:
Suggested design
Seven classes, split into data (what exists) and logic (how the plan is made).

Data classes
Owner

Attributes: name, available_minutes_per_day, available_windows (e.g. 7–9am, 6–9pm), preferences (a Preferences object), pets: list[Pet]
Methods: add_pet(), remove_pet(), get_all_tasks(), total_available_time()
Pet

Attributes: name, species, age, special_needs, tasks: list[Task]
Methods: add_task(), remove_task(), get_tasks_due(date)
Task

Attributes:
title
category (walk, feeding, meds, enrichment, grooming)
duration_minutes
priority (1–5, or low/med/high)
pet
frequency (daily, twice daily, weekly)
preferred_time / time_window (optional, e.g. "morning")
is_required (meds are non-negotiable, enrichment is flexible)
completed, last_completed
Methods: mark_complete(), is_due(date), fits_in(window)
Preferences (the owner's soft constraints)

Attributes: preferred_walk_times, category_weights (e.g. "I care more about walks than grooming"), avoid_times, max_tasks_per_day
Methods: score_task(task), which returns how well a task matches the owner's preferences
Logic classes
Scheduler (the planner, which holds the algorithm)

Attributes: owner, strategy (e.g. priority-first)
Methods:
generate_plan(date) -> DailyPlan
\_collect_due_tasks()
\_rank_tasks(), which sorts by required first, then priority, then preference score
\_fit_to_time(), which greedily packs tasks into the available time and drops the rest
\_detect_conflicts()
DailyPlan (the output)

Attributes: date, scheduled: list[ScheduledItem], skipped: list[(Task, reason)], total_minutes_used
Methods: add_item(), explain() -> str, summary(), to_table()
ScheduledItem

Attributes: task, start_time, end_time, reason (e.g. "Scheduled first: required medication, due daily")
Methods: overlaps(other)
Why this split works
Explanation is built in. Every placement or skip records a reason as it happens, so DailyPlan.explain() just assembles the stored reasons instead of guessing afterward.
Hard and soft constraints are separate. is_required and time windows are hard rules. Preferences only influences ranking. Required tasks always get scheduled first.
Scheduler is separate from the data classes. You can swap the strategy (priority-first, shortest-first, and so on) without touching Task or Pet.
Multiple pets are easy. Owner holds the shared time budget, and tasks stay attached to their Pet.

Then I asked for a simplified design and got this:
Simplified design: 4 classes
Task

Attributes: title, duration_minutes, priority (1–3), pet_name, is_required (meds, feeding), completed
Methods: mark_complete()
Pet

Attributes: name, species, tasks: list[Task]
Methods: add_task(), remove_task()
Owner

Attributes: name, available_minutes, pets: list[Pet]
Methods: add_pet(), get_all_tasks()
Scheduler

Attributes: owner
Methods:
generate_plan() -> DailyPlan, which sorts required tasks first, then by priority, then fits them into available_minutes
explain(plan) -> str, which gives a reason for each task included or skipped
DailyPlan could be a plain dataclass or just a return value, such as scheduled: list[Task] and skipped: list[(Task, reason)].

I preferred the simplified plan b/c it's easier to work with and less prone to errors.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

So at first the scheduler decided that all required tasks are added whether or not there is enough time for it. I changed that so that even a required task is not added if there's not enough time. The Owner then gets notified about that.
I read the code and confirmed that the AI created the first version and then changed to my recommended version. Then I ran tests on my version.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I tested to make sure the the scheduler worked correctly and correctly chose the tasks based on our rules.
The scheduler is really the main crux of the program and therefore it needed to be tested the most.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I created extensive tests to test the scheduler using AI. here's the output from AI:
✅ Added comprehensive task and scheduler tests
I expanded the test coverage to check:

creation and normalization of all task types
recurring task behavior for once/daily/weekly tasks
invalid recurrence fallback
owner + multi-pet task aggregation
required-vs-optional scheduling
duplicate-time conflict warnings
zero-budget and other edge cases
repeated rescheduling for completed recurring tasks
The tests are in test_pawpal.py, and the existing scheduler coverage remains in test_scheduler.py.

Verification
I ran the full suite:

Command: pytest -q
Result: 26 passed in 0.02s
This is fresh verification that the task model and scheduler behavior are covered and passing.

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
  How the scheduler was iteratively created

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
  More thought into how to create a scheduler with different days and having the UI show it in a better way.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
  The most important thing now - with using AI - is to figure out the correct rules and constraints that the project needs, as well as using AI to help collaborate on system design and algorithmic efficiency.
