import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler, DailyPlan

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_pet(name="Buddy", species="dog", age=3):
    return Pet(name=name, species=species, age=age)

def make_task(title="Walk", duration=20, priority="medium",
              scheduled_time="", recur_days=0):
    return Task(title=title, duration_minutes=duration, priority=priority,
                scheduled_time=scheduled_time, recur_days=recur_days)


# ===========================================================================
# 1. Task basics (existing tests, kept and expanded)
# ===========================================================================

def test_mark_complete_changes_status():
    """Happy path: mark_complete flips is_completed to True."""
    task = make_task()
    assert task.is_completed is False
    task.mark_complete()
    assert task.is_completed is True


def test_add_task_increases_pet_task_count():
    """Happy path: each add_task call grows the pet's task list by one."""
    pet = make_pet()
    assert len(pet.tasks) == 0
    pet.add_task(make_task("Playtime"))
    assert len(pet.tasks) == 1
    pet.add_task(make_task("Grooming"))
    assert len(pet.tasks) == 2


def test_add_task_tags_pet_name():
    """Pet.add_task should stamp the task's pet_name field."""
    pet = make_pet(name="Luna")
    task = make_task()
    pet.add_task(task)
    assert task.pet_name == "Luna"


# ===========================================================================
# 2. Sorting correctness
# ===========================================================================

def test_sort_by_time_chronological_order():
    """Tasks added in reverse time order must come out sorted chronologically."""
    pet = make_pet()
    pet.add_task(make_task("Evening walk",   scheduled_time="18:00"))
    pet.add_task(make_task("Lunch snack",    scheduled_time="12:00"))
    pet.add_task(make_task("Morning walk",   scheduled_time="07:00"))
    pet.add_task(make_task("Afternoon meds", scheduled_time="14:30"))

    scheduler = Scheduler(tasks=pet.tasks, available_minutes=120)
    sorted_tasks = scheduler.sort_by_time(pet.tasks)

    times = [t.scheduled_time for t in sorted_tasks]
    assert times == sorted(times), f"Expected sorted times, got: {times}"


def test_sort_by_time_no_time_sorts_last():
    """Tasks without a scheduled_time should appear at the end."""
    pet = make_pet()
    pet.add_task(make_task("Unnamed task",  scheduled_time=""))
    pet.add_task(make_task("Morning meds",  scheduled_time="08:00"))

    scheduler = Scheduler(tasks=pet.tasks, available_minutes=60)
    sorted_tasks = scheduler.sort_by_time(pet.tasks)

    assert sorted_tasks[0].title == "Morning meds"
    assert sorted_tasks[-1].scheduled_time == ""


def test_sort_by_duration_ascending():
    """sort_by_duration ascending=True should order shortest to longest."""
    tasks = [
        make_task("Long",   duration=45),
        make_task("Short",  duration=5),
        make_task("Medium", duration=20),
    ]
    scheduler = Scheduler(tasks=tasks, available_minutes=120)
    result = scheduler.sort_by_duration(tasks, ascending=True)
    durations = [t.duration_minutes for t in result]
    assert durations == sorted(durations)


# ===========================================================================
# 3. Recurrence logic
# ===========================================================================

def test_next_occurrence_advances_due_date_by_recur_days():
    """next_occurrence must set due_date = original due_date + recur_days."""
    today = date.today()
    task = Task(title="Daily walk", duration_minutes=30, priority="high",
                recur_days=1, due_date=today)
    nxt = task.next_occurrence()
    assert nxt.due_date == today + timedelta(days=1)
    assert nxt.is_completed is False


def test_next_occurrence_weekly():
    """Weekly task next occurrence should be 7 days ahead."""
    today = date.today()
    task = Task(title="Bath time", duration_minutes=20, priority="low",
                recur_days=7, due_date=today)
    nxt = task.next_occurrence()
    assert nxt.due_date == today + timedelta(days=7)


def test_next_occurrence_raises_for_non_recurring():
    """next_occurrence on a one-time task must raise ValueError."""
    import pytest
    task = make_task(recur_days=0)
    with pytest.raises(ValueError):
        task.next_occurrence()


def test_mark_task_complete_spawns_next_occurrence():
    """Completing a recurring task via Scheduler should add a new task to the pet."""
    pet = make_pet()
    task = Task(title="Morning walk", duration_minutes=30, priority="high",
                recur_days=1, due_date=date.today())
    pet.add_task(task)

    scheduler = Scheduler(tasks=pet.tasks, available_minutes=60)
    new_task = scheduler.mark_task_complete(task, pet)

    assert task.is_completed is True
    assert new_task is not None
    assert new_task.is_completed is False
    assert new_task.due_date == date.today() + timedelta(days=1)
    assert new_task in pet.tasks          # registered on the pet
    assert new_task in scheduler.tasks    # added to scheduler pool


def test_mark_task_complete_no_spawn_for_one_time():
    """Completing a non-recurring task should return None and not grow the task list."""
    pet = make_pet()
    task = make_task(recur_days=0)
    pet.add_task(task)

    scheduler = Scheduler(tasks=pet.tasks, available_minutes=60)
    original_count = len(pet.tasks)
    result = scheduler.mark_task_complete(task, pet)

    assert result is None
    assert len(pet.tasks) == original_count


# ===========================================================================
# 4. Conflict detection
# ===========================================================================

def test_time_conflict_detected_for_same_slot():
    """Two tasks at the same time should produce at least one conflict warning."""
    pet = make_pet()
    pet.add_task(make_task("Morning walk",  scheduled_time="07:00"))
    pet.add_task(make_task("Brush teeth",   scheduled_time="07:00"))

    scheduler = Scheduler(tasks=pet.tasks, available_minutes=120)
    warnings = scheduler.check_time_conflicts()

    assert len(warnings) == 1
    assert "07:00" in warnings[0]


def test_time_conflict_cross_pet():
    """Tasks from different pets at the same time should also be flagged."""
    buddy = make_pet("Buddy")
    luna  = make_pet("Luna", species="cat")
    buddy.add_task(make_task("Walk",    scheduled_time="07:00"))
    luna.add_task(make_task("Feeding",  scheduled_time="07:00"))

    all_tasks = buddy.tasks + luna.tasks
    scheduler = Scheduler(tasks=all_tasks, available_minutes=120)
    warnings = scheduler.check_time_conflicts()

    assert len(warnings) == 1
    assert "07:00" in warnings[0]


def test_no_conflict_when_times_differ():
    """Tasks at different times must produce zero conflict warnings."""
    pet = make_pet()
    pet.add_task(make_task("Morning walk",  scheduled_time="07:00"))
    pet.add_task(make_task("Evening walk",  scheduled_time="18:00"))

    scheduler = Scheduler(tasks=pet.tasks, available_minutes=120)
    assert scheduler.check_time_conflicts() == []


# ===========================================================================
# 5. Edge cases
# ===========================================================================

def test_pet_with_no_tasks_generates_empty_plan():
    """A scheduler with an empty task list should return a plan with no tasks."""
    scheduler = Scheduler(tasks=[], available_minutes=60)
    plan = scheduler.generate_plan()
    assert plan.tasks == []
    assert plan.total_duration == 0


def test_scheduler_skips_tasks_that_exceed_budget():
    """Tasks whose total duration exceeds available_minutes should be left out."""
    tasks = [
        make_task("Long task",  duration=90),   # won't fit in 60-min budget
        make_task("Short task", duration=10, priority="low"),
    ]
    # Make long task high priority so it's tried first
    tasks[0].priority = "high"
    scheduler = Scheduler(tasks=tasks, available_minutes=60)
    plan = scheduler.generate_plan()

    titles = [t.title for t in plan.tasks]
    assert "Long task" not in titles
    assert "Short task" in titles


def test_owner_get_pending_tasks_excludes_completed():
    """Owner.get_pending_tasks must not include tasks already marked done."""
    owner = Owner(name="Alex", available_minutes=60)
    pet = make_pet()
    t1 = make_task("Walk")
    t2 = make_task("Feed")
    t2.mark_complete()
    pet.add_task(t1)
    pet.add_task(t2)
    owner.add_pet(pet)

    pending = owner.get_pending_tasks()
    assert t1 in pending
    assert t2 not in pending


def test_filter_by_pet_returns_only_matching_tasks():
    """filter_by_pet should return tasks for the named pet only."""
    buddy = make_pet("Buddy")
    luna  = make_pet("Luna", species="cat")
    buddy.add_task(make_task("Buddy task"))
    luna.add_task(make_task("Luna task"))

    all_tasks = buddy.tasks + luna.tasks
    scheduler = Scheduler(tasks=all_tasks, available_minutes=120)

    buddy_only = scheduler.filter_by_pet("Buddy")
    assert all(t.pet_name == "Buddy" for t in buddy_only)
    assert len(buddy_only) == 1
