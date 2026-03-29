import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta
from pawpal_system import Pet, Task, Priority, Frequency


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


def test_daily_next_occurrence_not_due_today():
    task = Task(1, "Feed", 10, Priority.HIGH, frequency=Frequency.DAILY)
    task.mark_complete()
    assert task.next_occurrence().is_due_today() is False


def test_daily_next_due_date_is_tomorrow():
    task = Task(1, "Feed", 10, Priority.HIGH, frequency=Frequency.DAILY)
    task.mark_complete()
    assert task.next_occurrence().next_due_date == date.today() + timedelta(days=1)


def test_weekly_next_due_date_is_seven_days():
    task = Task(2, "Groom", 45, Priority.MEDIUM, frequency=Frequency.WEEKLY)
    task.mark_complete()
    next_task = task.next_occurrence()
    assert next_task.next_due_date == date.today() + timedelta(days=7)
    assert next_task.is_due_today() is False
