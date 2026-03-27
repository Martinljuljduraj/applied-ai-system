import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Pet, Task, Priority


def test_mark_complete_changes_status():
    task = Task(1, "Morning walk", 30, Priority.HIGH)
    assert task.is_completed is False

    task.mark_complete()

    assert task.is_completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(1, "Rex", "Dog", 4)
    assert len(pet.get_tasks()) == 0

    pet.add_task(Task(1, "Feeding", 10, Priority.MEDIUM))
    pet.add_task(Task(2, "Walk", 30, Priority.HIGH))

    assert len(pet.get_tasks()) == 2
