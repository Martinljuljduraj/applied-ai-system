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
    next_due_date: Optional[date] = None

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.is_completed = True
        self.last_completed_date = date.today()

    def is_due_today(self) -> bool:
        """Return True if this task should appear in today's schedule."""
        today = date.today()
        if self.frequency == Frequency.ONCE:
            return not self.is_completed
        # DAILY and WEEKLY: None means never completed → due immediately.
        if self.next_due_date is None:
            return True
        return self.next_due_date <= today

    def clone_for_today(self) -> Task:
        """Return a fresh copy of this task for today (used for recurring tasks)."""
        return replace(self, id=self.id + 1000, is_completed=False)

    def next_occurrence(self) -> Optional[Task]:
        """
        Return a new Task instance for the next scheduled occurrence, or None
        if this task does not recur (Frequency.ONCE).

        next_due_date is set using timedelta: +1 day for DAILY, +7 days for WEEKLY.
        """
        if self.frequency == Frequency.ONCE:
            return None
        delta = timedelta(days=1 if self.frequency == Frequency.DAILY else 7)
        return replace(
            self,
            id=self.id + 1,
            is_completed=False,
            last_completed_date=None,
            next_due_date=date.today() + delta,
        )


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

    def get_tasks_by_status(self, completed: bool) -> list[Task]:
        """Return tasks filtered by completion status."""
        return [t for t in self._tasks if t.is_completed == completed]


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

    def get_tasks_for_pet(self, pet_name: str) -> list[Task]:
        """Return all tasks for a pet with the given name (case-insensitive)."""
        for pet in self._pets:
            if pet.name.lower() == pet_name.lower():
                return pet.get_tasks()
        return []


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

    # Here we use a lambda function as a "key" to sort strings in "HH:MM" format.
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

        # Collect due tasks; clone recurring ones so originals are not mutated
        # when mark_complete() is called on the scheduled copy.
        pending: list[tuple[str, Task]] = []
        for pet in self.owner.get_pets():
            for task in pet.get_tasks():
                if task.is_due_today():
                    scheduled_task = (
                        task.clone_for_today()
                        if task.frequency != Frequency.ONCE
                        else task
                    )
                    pending.append((pet.name, scheduled_task))
        self._total_due = len(pending)

        current_start = self.owner.available_start
        for pet_name, task in self._sort_by_priority(pending):
            # Respect preferred_time as a soft constraint: delay start if the
            # slot is earlier than the owner's preferred time for this task.
            if task.preferred_time is not None and task.preferred_time > current_start:
                actual_start = task.preferred_time
            else:
                actual_start = current_start

            if not self._fits_in_window(task, actual_start):
                continue
            end_dt = datetime.combine(today, actual_start) + timedelta(minutes=task.duration_mins)
            end_time = end_dt.time()
            block = ScheduledBlock(
                pet_name=pet_name,
                task=task,
                start_time=actual_start,
                end_time=end_time,
                reason=f"Priority: {task.priority.name}",
            )
            self._schedule.append(block)
            current_start = end_time

        return self._schedule

    def check_conflicts(self, task: Task, start_time: Optional[time] = None) -> bool:
        """
        Return True if placing `task` at `start_time` overlaps any scheduled block.
        If `start_time` is None, checks starting immediately after the last block.
        Short-circuits on the first detected overlap.
        """
        if not self._schedule:
            return False
        today = date.today()
        if start_time is None:
            start_time = self._schedule[-1].end_time
        candidate_start = datetime.combine(today, start_time)
        candidate_end = candidate_start + timedelta(minutes=task.duration_mins)
        return any(
            candidate_start < datetime.combine(today, b.end_time)
            and candidate_end > datetime.combine(today, b.start_time)
            for b in self._schedule
        )

    def get_conflicts(self) -> list[str]:
        """
        Scan the current schedule for overlapping time blocks and return a
        warning message for each detected conflict.

        Algorithm: sort blocks by start_time, then walk the list once.
        Each block only needs to be compared against its immediate predecessor
        because sorted order guarantees no earlier block can overlap a later one
        without the adjacent pair also overlapping. This reduces comparisons
        from O(n²) to O(n log n) sort + O(n) scan, and eliminates all
        datetime.combine() calls since time objects support direct comparison.

        Works across pets (the owner has only one pair of hands) and within
        the same pet. Returns an empty list when no conflicts exist — never
        raises.

        Returns
        -------
        list[str]
            Human-readable warning strings, one per overlapping pair.
            Empty list means the schedule is clean.
        """
        warnings: list[str] = []
        sorted_blocks = sorted(self._schedule, key=lambda b: b.start_time)
        for i in range(1, len(sorted_blocks)):
            prev = sorted_blocks[i - 1]
            curr = sorted_blocks[i]
            if prev.end_time > curr.start_time:
                warnings.append(
                    f"WARNING: '{prev.task.description}' ({prev.pet_name}, "
                    f"{prev.start_time.strftime('%H:%M')}–{prev.end_time.strftime('%H:%M')}) "
                    f"overlaps '{curr.task.description}' ({curr.pet_name}, "
                    f"{curr.start_time.strftime('%H:%M')}–{curr.end_time.strftime('%H:%M')})"
                )
        return warnings

    def complete_task(self, block: ScheduledBlock) -> Optional[Task]:
        """
        Mark the task in `block` as complete. For DAILY and WEEKLY tasks,
        automatically create and register the next occurrence on the same pet.

        Returns the newly created Task if one was queued, otherwise None.
        """
        block.task.mark_complete()
        next_task = block.task.next_occurrence()
        if next_task is None:
            return None
        for pet in self.owner.get_pets():
            if pet.name == block.pet_name:
                pet.add_task(next_task)
                return next_task
        return None

    def filter_schedule_by_pet(self, pet_name: str) -> list[ScheduledBlock]:
        """Return only the scheduled blocks for a specific pet (case-insensitive)."""
        return [b for b in self._schedule if b.pet_name.lower() == pet_name.lower()]

    def filter_schedule_by_status(self, completed: bool) -> list[ScheduledBlock]:
        """Return blocks whose task matches the given completion status."""
        return [b for b in self._schedule if b.task.is_completed == completed]

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> list[ScheduledBlock]:
        """
        Filter the current schedule by pet name, completion status, or both.

        Parameters
        ----------
        pet_name  : if given, only blocks for this pet are returned (case-insensitive).
        completed : if given, only blocks whose task matches this status are returned.

        Passing neither argument returns the full schedule unchanged.
        """
        results = self._schedule
        if pet_name is not None:
            results = [b for b in results if b.pet_name.lower() == pet_name.lower()]
        if completed is not None:
            results = [b for b in results if b.task.is_completed == completed]
        return results

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

    def sort_by_time(self, tasks: list[tuple[str, Task]]) -> list[tuple[str, Task]]:
        """
        Sort (pet_name, task) pairs by preferred_time ascending.
        Tasks with no preferred_time are placed at the end.
        """
        return sorted(
            tasks,
            key=lambda pair: (
                pair[1].preferred_time is None,
                pair[1].preferred_time if pair[1].preferred_time is not None else time(23, 59),
            ),
        )

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
