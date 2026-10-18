# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

<!-- Describe the goal you asked the agent to accomplish -->

So I asked the agent to help me identify the classes with their attributes and methods needed for this project.

Here's what I put in:
I would like to create an app that does the following:
A busy pet owner needs help staying consistent with pet care. They want an assistant that can:
Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
Consider constraints (time available, priority, owner preferences)
Produce a daily plan and explain why it chose that plan

**What did the agent do?**

<!-- List the steps the agent took (files edited, commands run, etc.) -->

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

**What did you have to verify or fix manually?**

<!-- Describe anything the agent got wrong or that required human review -->

So I didn't like the original version b/c it was too complex for what I believe is needed. It's always better to keep things as simple as necessary with additional complexity if and when needed.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

|                       | Option A | Option B |
| --------------------- | -------- | -------- |
| **Model / tool used** |          |          |
| **Prompt**            |          |          |
| **Response summary**  |          |          |
| **What was useful**   |          |          |
| **Problems noticed**  |          |          |
| **Decision**          |          |          |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->
