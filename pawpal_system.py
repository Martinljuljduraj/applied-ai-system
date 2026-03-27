from __future__ import annotations
from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Priority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class Frequency(Enum):
    ONCE = "Once"
    DAILY = "Daily"
    WEEKLY = "Weekly"


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet care activity."""
    id: int
    description: str
    duration_mins: int
    priority: Priority
    preferred_time: Optional[time] = None
    frequency: Frequency = Frequency.ONCE
    is_completed: bool = False
    last_completed_date: Optional[date] = None

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.is_completed = True
        self.last_completed_date = date.today()

    def is_due_today(self) -> bool:
        """Return True if this task should appear in today's schedule."""
        today = date.today()
        if self.frequency == Frequency.ONCE:
            return not self.is_completed
        if self.frequency == Frequency.DAILY:
            return True
        # WEEKLY
        return (
            self.last_completed_date is None
            or (today - self.last_completed_date).days >= 7
        )

    def clone_for_today(self) -> Task:
        """Return a fresh copy of this task for today (used for recurring tasks)."""
        return replace(self, id=self.id + 1000, is_completed=False)


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """A pet profile belonging to an owner."""
    id: int
    name: str
    species: str
    age: int
    breed: str = ""
    _tasks: list[Task] = field(default_factory=list, init=False, repr=False)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        self._tasks.append(task)

    def remove_task(self, task_id: int) -> None:
        """Remove a task by its id."""
        self._tasks = [t for t in self._tasks if t.id != task_id]

    def get_tasks(self) -> list[Task]:
        """Return all tasks assigned to this pet."""
        return self._tasks


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    """The pet owner, including their daily availability window."""
    id: int
    name: str
    email: str
    available_start: time = time(8, 0)   # default: 8:00 AM
    available_end: time = time(20, 0)    # default: 8:00 PM
    _pets: list[Pet] = field(default_factory=list, init=False, repr=False)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self._pets.append(pet)

    def remove_pet(self, pet_id: int) -> None:
        """Remove a pet by its id."""
        self._pets = [p for p in self._pets if p.id != pet_id]

    def get_pets(self) -> list[Pet]:
        """Return all pets owned by this owner."""
        return self._pets


# ---------------------------------------------------------------------------
# ScheduledBlock  (output of the Scheduler)
# ---------------------------------------------------------------------------

@dataclass
class ScheduledBlock:
    """One time-boxed slot in the generated daily plan."""
    pet_name: str
    task: Task
    start_time: time
    end_time: time
    reason: str = ""

    def to_display_row(self) -> dict:
        """Return a dict suitable for rendering in a Streamlit table."""
        return {
            "Pet": self.pet_name,
            "Task": self.task.description,
            "Start": self.start_time.strftime("%H:%M"),
            "End": self.end_time.strftime("%H:%M"),
            "Priority": self.task.priority.name,
            "Reason": self.reason,
        }


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Generates a conflict-free, priority-ordered daily care schedule
    for all pets belonging to an owner.
    """

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self._schedule: list[ScheduledBlock] = []
        self._total_due: int = 0

    def generate_schedule(self) -> list[ScheduledBlock]:
        """
        Build and return an ordered list of ScheduledBlocks that fit within
        the owner's available window.
        """
        self._schedule = []
        today = date.today()

        pending: list[tuple[str, Task]] = [
            (pet.name, task)
            for pet in self.owner.get_pets()
            for task in pet.get_tasks()
            if task.is_due_today()
        ]
        self._total_due = len(pending)

        current_start = self.owner.available_start
        for pet_name, task in self._sort_by_priority(pending):
            if not self._fits_in_window(task, current_start):
                continue
            end_dt = datetime.combine(today, current_start) + timedelta(minutes=task.duration_mins)
            end_time = end_dt.time()
            block = ScheduledBlock(
                pet_name=pet_name,
                task=task,
                start_time=current_start,
                end_time=end_time,
                reason=f"Priority: {task.priority.name}",
            )
            self._schedule.append(block)
            current_start = end_time

        return self._schedule

    def check_conflicts(self, task: Task) -> bool:
        """
        Return True if adding this task would overlap an already-scheduled block.
        """
        if not self._schedule:
            return False
        today = date.today()
        last_end = self._schedule[-1].end_time
        candidate_start_dt = datetime.combine(today, last_end)
        candidate_end_dt = candidate_start_dt + timedelta(minutes=task.duration_mins)
        for block in self._schedule:
            b_start = datetime.combine(today, block.start_time)
            b_end = datetime.combine(today, block.end_time)
            if candidate_start_dt < b_end and candidate_end_dt > b_start:
                return True
        return False

    def explain_plan(self) -> str:
        """
        Return a human-readable explanation of why tasks were ordered the way
        they were.
        """
        if self._total_due == 0:
            return "No tasks are due today."
        skipped = self._total_due - len(self._schedule)
        window = (
            f"{self.owner.available_start.strftime('%H:%M')}"
            f"–{self.owner.available_end.strftime('%H:%M')}"
        )
        lines = [
            f"Scheduled {len(self._schedule)} of {self._total_due} task(s)"
            f" across {len(self.owner.get_pets())} pet(s).",
            "Tasks were ordered by priority (HIGH → MEDIUM → LOW),"
            " then by preferred time, then shortest first.",
        ]
        if skipped > 0:
            lines.append(
                f"{skipped} task(s) were skipped — they did not fit"
                f" within the available window ({window})."
            )
        return " ".join(lines)

    # -- private helpers ----------------------------------------------------

    def _sort_by_priority(self, tasks: list[tuple[str, Task]]) -> list[tuple[str, Task]]:
        """
        Sort (pet_name, task) pairs: HIGH first, then MEDIUM, then LOW.
        Ties broken by preferred_time (earlier first), then duration (shorter first).
        """
        return sorted(
            tasks,
            key=lambda pair: (
                pair[1].priority.value,
                pair[1].preferred_time if pair[1].preferred_time is not None else time(23, 59),
                pair[1].duration_mins,
            ),
        )

    def _fits_in_window(self, task: Task, start: time) -> bool:
        """
        Return True if a task starting at `start` finishes before
        the owner's available_end.

        Uses datetime.combine to work around the limitation that Python's
        `time` type does not support direct arithmetic with `timedelta`.
        """
        today = date.today()
        start_dt = datetime.combine(today, start)
        end_dt = start_dt + timedelta(minutes=task.duration_mins)
        window_end_dt = datetime.combine(today, self.owner.available_end)
        return end_dt <= window_end_dt
