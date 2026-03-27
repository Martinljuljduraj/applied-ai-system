from datetime import time
from pawpal_system import Owner, Pet, Task, Scheduler, Priority, Frequency


def main():
    # --- Setup ---
    owner = Owner(1, "Martin", "martin@pawpal.com",
                  available_start=time(8, 0),
                  available_end=time(10, 0))  # tight window to test skipping

    rex = Pet(1, "Rex", "Dog", 4, breed="Labrador")
    rex.add_task(Task(1, "Morning walk",    30, Priority.HIGH,   time(8, 0),  Frequency.DAILY))
    rex.add_task(Task(2, "Feeding",         10, Priority.MEDIUM, time(8, 30), Frequency.DAILY))
    rex.add_task(Task(3, "Bath time",       45, Priority.LOW,    frequency=Frequency.WEEKLY))
    rex.add_task(Task(4, "Vet appointment", 60, Priority.HIGH))   # ONCE, should be scheduled

    whiskers = Pet(2, "Whiskers", "Cat", 2)
    whiskers.add_task(Task(5, "Play session", 20, Priority.MEDIUM, time(9, 0), Frequency.DAILY))
    whiskers.add_task(Task(6, "Brush coat",   15, Priority.LOW,    frequency=Frequency.WEEKLY))

    owner.add_pet(rex)
    owner.add_pet(whiskers)

    # --- Generate schedule ---
    scheduler = Scheduler(owner)
    schedule = scheduler.generate_schedule()

    # --- Display ---
    print("=" * 55)
    print("  PawPal+ — Daily Schedule")
    print("=" * 55)

    if not schedule:
        print("  No tasks scheduled for today.")
    else:
        print(f"  {'Time':<15} {'Pet':<10} {'Task':<20} {'Priority'}")
        print("  " + "-" * 51)
        for block in schedule:
            row = block.to_display_row()
            time_range = f"{row['Start']} → {row['End']}"
            print(f"  {time_range:<15} {row['Pet']:<10} {row['Task']:<20} {row['Priority']}")

    print()
    print("  " + scheduler.explain_plan())

    # --- Verify conflict detection ---
    print()
    print("─" * 55)
    print("  Logic checks")
    print("─" * 55)
    long_task = Task(99, "Long grooming", 90, Priority.LOW)
    conflict = scheduler.check_conflicts(long_task)
    print(f"  Conflict check (90-min task):     {'CONFLICT' if conflict else 'OK — no conflict'}")

    # --- Verify mark_complete + is_due_today ---
    morning_walk = rex.get_tasks()[0]
    morning_walk.mark_complete()
    print(f"  Morning walk (DAILY) after done:  due = {morning_walk.is_due_today()}")

    once_task = Task(10, "One-off task", 15, Priority.HIGH)
    once_task.mark_complete()
    print(f"  One-off task (ONCE) after done:   due = {once_task.is_due_today()}")

    # --- Verify remove ---
    before = [t.description for t in rex.get_tasks()]
    rex.remove_task(2)
    after = [t.description for t in rex.get_tasks()]
    print(f"  Remove task 2 from Rex:")
    print(f"    before: {before}")
    print(f"    after:  {after}")

    print("─" * 55)


if __name__ == "__main__":
    main()
