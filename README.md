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

## Smarter Scheduling

Beyond the basic priority-and-time-budget plan, the scheduler includes four additional algorithms:

**Sort by scheduled time**
`Scheduler.sort_by_time(tasks)` orders any list of tasks chronologically using a lambda key on each task's `scheduled_time` string (`"HH:MM"`). Because ISO-formatted time strings compare lexicographically in the same order they compare chronologically, no date parsing is needed. Tasks without a time set sort to the end.

**Filter by pet or completion status**
`Scheduler.filter_by_pet(pet_name)` and `Scheduler.filter_by_status(completed)` return a filtered view of the task pool using a single list comprehension. These make it easy to display only one pet's workload or show only what still needs to be done.

**Recurring task auto-spawn**
Every `Task` carries a `recur_days` field (0 = one-time). When `Scheduler.mark_task_complete(task, pet)` is called on a recurring task, it calls `task.next_occurrence()` to create a fresh copy whose `due_date` is advanced by `timedelta(days=recur_days)`. The new task is registered on the pet and added back into the scheduler's pool automatically, so recurring care (daily walks, weekly litter changes) never falls off the list.

**Time-slot conflict detection**
`Scheduler.check_time_conflicts()` scans all pending tasks and groups them by `scheduled_time`. Any slot occupied by two or more tasks produces a plain-text warning (e.g., `[TIME CONFLICT] 07:00 has 3 overlapping tasks: ...`). The check returns a list of strings rather than raising an exception, so the app can display warnings without crashing. The same check runs automatically inside `generate_plan()` and appears in `DailyPlan.get_summary()`.
