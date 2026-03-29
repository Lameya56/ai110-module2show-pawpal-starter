import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet


def test_mark_complete_changes_status():
    task = Task(title="Feed fish", duration_minutes=5, priority="low")
    assert task.is_completed is False
    task.mark_complete()
    assert task.is_completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="cat", age=2)
    assert len(pet.tasks) == 0
    pet.add_task(Task(title="Playtime", duration_minutes=10, priority="medium"))
    assert len(pet.tasks) == 1
    pet.add_task(Task(title="Grooming", duration_minutes=15, priority="low"))
    assert len(pet.tasks) == 2
