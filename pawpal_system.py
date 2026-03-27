from __future__ import annotations
from dataclasses import dataclass, field
from datetime import time
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

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass

    def is_due_today(self) -> bool:
        """Return True if this task should appear in today's schedule."""
        pass

    def clone_for_today(self) -> Task:
        """Return a fresh copy of this task for today (used for recurring tasks)."""
        pass


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

    def add_task(self, _task: Task) -> None:
        """Attach a care task to this pet."""
        pass

    def remove_task(self, _task_id: int) -> None:
        """Remove a task by its id."""
        pass

    def get_tasks(self) -> list[Task]:
        """Return all tasks assigned to this pet."""
        pass


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
        pass

    def remove_pet(self, pet_id: int) -> None:
        """Remove a pet by its id."""
        pass

    def get_pets(self) -> list[Pet]:
        """Return all pets owned by this owner."""
        pass


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
        pass


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

    def generate_schedule(self) -> list[ScheduledBlock]:
        """
        Build and return an ordered list of ScheduledBlocks that fit within
        the owner's available window.
        """
        pass

    def check_conflicts(self, task: Task) -> bool:
        """
        Return True if adding this task would overlap an already-scheduled block.
        """
        pass

    def explain_plan(self) -> str:
        """
        Return a human-readable explanation of why tasks were ordered the way
        they were (can be AI-generated or rule-based text).
        """
        pass

    # -- private helpers ----------------------------------------------------

    def _sort_by_priority(self, tasks: list[tuple[str, Task]]) -> list[tuple[str, Task]]:
        """
        Sort (pet_name, task) pairs: HIGH first, then MEDIUM, then LOW.
        Ties broken by preferred_time (earlier first), then duration (shorter first).
        """
        pass

    def _fits_in_window(self, task: Task, start: time) -> bool:
        """
        Return True if a task starting at `start` finishes before
        the owner's available_end.
        """
        pass
