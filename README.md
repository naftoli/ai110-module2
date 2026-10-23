# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
Plan for Alice: 65 of 120 available minutes used.

Scheduled (in order):
1. Walk Buddy (Buddy, 30 min): required task, scheduled first
2. Feed Whiskers (Whiskers, 15 min): required task, scheduled first
3. Play with Buddy (Buddy, 20 min): priority 1, fit in the remaining time
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
================================================ test session starts ================================================
platform darwin -- Python 3.13.3, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/naftolir/Sites/ai110-module2
plugins: anyio-4.15.1
collected 17 items

tests/test_pawpal.py ..                                                                                       [ 11%]
tests/test_scheduler.py ...............                                                                       [100%]

================================================ 17 passed in 0.02s =================================================
```

## 📐 Smarter Scheduling

So I actually updated the current generate_plan function to include the time element. I also added conflict detection logic in find_time_conflicts method. The recurring task recreation is in the method next_instance

| Feature           | Method(s)           | Notes                             |
| ----------------- | ------------------- | --------------------------------- |
| Task sorting      | task_sort_key       | e.g., by priority, duration       |
| Filtering         | task_sort_key       | e.g., skip tasks if time runs out |
| Conflict handling | find_time_conflicts | e.g., overlapping time slots      |
| Recurring tasks   | next_instance       | e.g., daily vs. weekly            |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. Create Owner (Update Default Owner)
2. Add Pets
3. Add Tasks for Pets
4. Each task includes the name, priority, required or not, time duration, date and time of task, the pet it's associated with, and whether it's a one time task or daily / weekly
5. Once all tasks have been entered, create and build your schedule

**Screenshot or video** _(optional)_: <!-- Insert a screenshot or link to a demo video here -->

## Testing Pawpal+

Ran python -m pytest

```
====================================================== test session starts ======================================================
platform darwin -- Python 3.13.3, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/naftolir/Sites/ai110-module2
plugins: anyio-4.15.1
collected 27 items

tests/test_pawpal.py ......                                                                                               [ 22%]
tests/test_scheduler.py .....................                                                                             [100%]

====================================================== 27 passed in 0.05s ======================================================
```

My confidence level: \*\*\*\*
