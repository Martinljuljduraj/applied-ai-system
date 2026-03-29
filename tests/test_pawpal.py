import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, time, timedelta
from pawpal_system import Owner, Pet, Task, Priority, Frequency, Scheduler, ScheduledBlock


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_owner_with_tasks(*tasks: Task) -> tuple[Owner, Scheduler]:
    """Create a single-pet owner pre-loaded with the given tasks."""
    owner = Owner(1, "Alex", "alex@example.com",
                  available_start=time(8, 0),
                  available_end=time(20, 0))
    pet = Pet(1, "Buddy", "Dog", 3)
    for t in tasks:
        pet.add_task(t)
    owner.add_pet(pet)
    return owner, Scheduler(owner)


# ---------------------------------------------------------------------------
# Sorting Correctness
# ---------------------------------------------------------------------------

def test_high_priority_scheduled_before_low():
    """HIGH-priority task must appear before LOW in the generated schedule."""
    low  = Task(1, "Trim nails", 20, Priority.LOW)
    high = Task(2, "Insulin shot", 5, Priority.HIGH)
    _, scheduler = _make_owner_with_tasks(low, high)

    blocks = scheduler.generate_schedule()

    priorities = [b.task.priority for b in blocks]
    assert priorities == [Priority.HIGH, Priority.LOW]


def test_all_three_priorities_ordered_correctly():
    """Schedule must come out HIGH → MEDIUM → LOW regardless of insertion order."""
    low    = Task(1, "Bath",        30, Priority.LOW)
    high   = Task(2, "Medication",  10, Priority.HIGH)
    medium = Task(3, "Walk",        20, Priority.MEDIUM)
    _, scheduler = _make_owner_with_tasks(low, high, medium)

    blocks = scheduler.generate_schedule()

    assert [b.task.priority for b in blocks] == [
        Priority.HIGH, Priority.MEDIUM, Priority.LOW
    ]


def test_equal_priority_shorter_task_scheduled_first():
    """Tie-break rule: among equal priorities, shorter duration comes first."""
    long_task  = Task(1, "Long walk",  60, Priority.MEDIUM)
    short_task = Task(2, "Quick feed", 10, Priority.MEDIUM)
    _, scheduler = _make_owner_with_tasks(long_task, short_task)

    blocks = scheduler.generate_schedule()

    assert blocks[0].task.id == short_task.id


def test_pet_with_no_tasks_produces_empty_schedule():
    """A pet with no tasks should yield an empty schedule without errors."""
    owner = Owner(1, "Alex", "alex@example.com")
    owner.add_pet(Pet(1, "Ghost", "Cat", 2))
    scheduler = Scheduler(owner)

    blocks = scheduler.generate_schedule()

    assert blocks == []


# ---------------------------------------------------------------------------
# Recurrence Logic
# ---------------------------------------------------------------------------

def test_complete_daily_task_adds_next_occurrence_to_pet():
    """Completing a DAILY task via the scheduler must register tomorrow's task."""
    task = Task(1, "Evening feed", 15, Priority.HIGH, frequency=Frequency.DAILY)
    _, scheduler = _make_owner_with_tasks(task)
    blocks = scheduler.generate_schedule()

    next_task = scheduler.complete_task(blocks[0])

    assert next_task is not None
    assert next_task.next_due_date == date.today() + timedelta(days=1)


def test_complete_daily_task_new_occurrence_not_completed():
    """The freshly queued task must start in an incomplete state."""
    task = Task(1, "Morning walk", 30, Priority.HIGH, frequency=Frequency.DAILY)
    _, scheduler = _make_owner_with_tasks(task)
    blocks = scheduler.generate_schedule()

    next_task = scheduler.complete_task(blocks[0])

    assert next_task.is_completed is False


def test_complete_once_task_returns_none():
    """ONCE tasks must not queue a follow-up; complete_task returns None."""
    task = Task(1, "Vet visit", 60, Priority.HIGH, frequency=Frequency.ONCE)
    _, scheduler = _make_owner_with_tasks(task)
    blocks = scheduler.generate_schedule()

    result = scheduler.complete_task(blocks[0])

    assert result is None


def test_daily_task_with_no_next_due_date_is_due_today():
    """A DAILY task that has never been run (next_due_date=None) is due immediately."""
    task = Task(1, "Feed", 10, Priority.HIGH, frequency=Frequency.DAILY,
                next_due_date=None)

    assert task.is_due_today() is True


# ---------------------------------------------------------------------------
# Conflict Detection
# ---------------------------------------------------------------------------

def test_clean_schedule_has_no_conflicts():
    """Sequential tasks generated by the scheduler must not conflict."""
    t1 = Task(1, "Walk",  30, Priority.HIGH)
    t2 = Task(2, "Feed",  15, Priority.MEDIUM)
    _, scheduler = _make_owner_with_tasks(t1, t2)
    scheduler.generate_schedule()

    assert scheduler.get_conflicts() == []


def test_overlapping_blocks_detected_as_conflict():
    """Manually injected overlapping blocks must be flagged by get_conflicts."""
    task_a = Task(1, "Walk",     60, Priority.HIGH)
    task_b = Task(2, "Grooming", 30, Priority.MEDIUM)
    _, scheduler = _make_owner_with_tasks(task_a, task_b)
    scheduler.generate_schedule()

    # Force an overlap: both blocks start at 08:00
    overlap_start = time(8, 0)
    overlap_end   = time(9, 0)
    scheduler._schedule = [
        ScheduledBlock("Buddy", task_a, overlap_start, overlap_end),
        ScheduledBlock("Buddy", task_b, overlap_start, time(8, 30)),
    ]

    conflicts = scheduler.get_conflicts()

    assert len(conflicts) == 1
    assert "Walk" in conflicts[0]
    assert "Grooming" in conflicts[0]


def test_back_to_back_tasks_are_not_conflicts():
    """Adjacent tasks (first ends exactly when second starts) must not conflict."""
    task_a = Task(1, "Walk",  30, Priority.HIGH)
    task_b = Task(2, "Feed",  15, Priority.MEDIUM)
    _, scheduler = _make_owner_with_tasks(task_a, task_b)
    scheduler.generate_schedule()

    # Place them end-to-end explicitly
    scheduler._schedule = [
        ScheduledBlock("Buddy", task_a, time(8, 0),  time(8, 30)),
        ScheduledBlock("Buddy", task_b, time(8, 30), time(8, 45)),
    ]

    assert scheduler.get_conflicts() == []


def test_single_block_schedule_has_no_conflicts():
    """A schedule with only one block can never conflict with itself."""
    task = Task(1, "Walk", 30, Priority.HIGH)
    _, scheduler = _make_owner_with_tasks(task)
    scheduler.generate_schedule()

    assert scheduler.get_conflicts() == []
