from datetime import time
from pawpal_system import Owner, Pet, Task, Scheduler, ScheduledBlock, Priority, Frequency


def print_blocks(blocks, label):
    print(f"\n  {label}")
    print("  " + "-" * 51)
    if not blocks:
        print("  (none)")
        return
    print(f"  {'Time':<15} {'Pet':<10} {'Task':<20} {'Priority'}")
    print("  " + "-" * 51)
    for block in blocks:
        row = block.to_display_row()
        time_range = f"{row['Start']} → {row['End']}"
        print(f"  {time_range:<15} {row['Pet']:<10} {row['Task']:<20} {row['Priority']}")


def main():
    # --- Setup ---
    owner = Owner(1, "Martin", "martin@pawpal.com",
                  available_start=time(8, 0),
                  available_end=time(20, 0))

    rex = Pet(1, "Rex", "Dog", 4, breed="Labrador")

    # Tasks added OUT OF ORDER (by time) to exercise sort_by_time()
    rex.add_task(Task(3, "Bath time",       45, Priority.LOW,    time(18, 0), Frequency.WEEKLY))
    rex.add_task(Task(4, "Vet appointment", 60, Priority.HIGH,   time(14, 0)))                   # ONCE
    rex.add_task(Task(1, "Morning walk",    30, Priority.HIGH,   time(8, 0),  Frequency.DAILY))
    rex.add_task(Task(2, "Feeding",         10, Priority.MEDIUM, time(8, 30), Frequency.DAILY))

    whiskers = Pet(2, "Whiskers", "Cat", 2)

    # Also out of order
    whiskers.add_task(Task(6, "Brush coat",   15, Priority.LOW,    time(17, 0), Frequency.WEEKLY))
    whiskers.add_task(Task(5, "Play session", 20, Priority.MEDIUM, time(9, 0),  Frequency.DAILY))

    owner.add_pet(rex)
    owner.add_pet(whiskers)

    # --- Generate schedule ---
    scheduler = Scheduler(owner)
    schedule = scheduler.generate_schedule()

    # --- Full schedule (sorted by priority, as generated) ---
    print("=" * 55)
    print("  PawPal+ — Daily Schedule (by priority)")
    print("=" * 55)
    print_blocks(schedule, "All scheduled tasks")
    print()
    print("  " + scheduler.explain_plan())

    # --- sort_by_time(): show all pending tasks in chronological order ---
    print("\n" + "=" * 55)
    print("  sort_by_time() — tasks in chronological order")
    print("=" * 55)
    all_pending = [
        (pet.name, task)
        for pet in owner.get_pets()
        for task in pet.get_tasks()
        if task.is_due_today()
    ]
    sorted_by_time = scheduler.sort_by_time(all_pending)
    print(f"  {'Time':<10} {'Pet':<10} {'Task':<25} {'Priority'}")
    print("  " + "-" * 51)
    for pet_name, task in sorted_by_time:
        pref = task.preferred_time.strftime("%H:%M") if task.preferred_time else "(none)"
        print(f"  {pref:<10} {pet_name:<10} {task.description:<25} {task.priority.name}")

    # --- filter_tasks(): filter by pet name ---
    print("\n" + "=" * 55)
    print("  filter_tasks(pet_name='Rex')")
    print("=" * 55)
    print_blocks(scheduler.filter_tasks(pet_name="Rex"), "Rex's blocks")

    # --- filter_tasks(): filter by completion status (pending) ---
    print("\n" + "=" * 55)
    print("  filter_tasks(completed=False) — pending tasks")
    print("=" * 55)
    print_blocks(scheduler.filter_tasks(completed=False), "Pending blocks")

    # Mark one task complete to make the next filter interesting
    for block in schedule:
        if block.task.description == "Morning walk":
            block.task.mark_complete()
            print(f"\n  [marked '{block.task.description}' complete]")
            break

    # --- filter_tasks(): combined — Rex's completed tasks ---
    print("\n" + "=" * 55)
    print("  filter_tasks(pet_name='Rex', completed=True)")
    print("=" * 55)
    print_blocks(scheduler.filter_tasks(pet_name="Rex", completed=True), "Rex's completed blocks")

    # --- Recurring task auto-creation via complete_task() ---
    print("\n" + "=" * 55)
    print("  complete_task() — auto-create next occurrence")
    print("=" * 55)
    # Find the Morning walk block (DAILY) and complete it through the scheduler
    for block in schedule:
        if block.task.description == "Morning walk":
            before_count = len(rex.get_tasks())
            next_task = scheduler.complete_task(block)
            after_count = len(rex.get_tasks())
            print(f"  Completed:  '{block.task.description}' ({block.task.frequency.value})")
            print(f"  Rex tasks before: {before_count}  →  after: {after_count}")
            if next_task:
                pref = next_task.preferred_time.strftime("%H:%M") if next_task.preferred_time else "(none)"
                print(f"  Next occurrence: id={next_task.id}, desc='{next_task.description}', "
                      f"preferred_time={pref}, completed={next_task.is_completed}")
            break

    # ONCE task should return None
    for block in schedule:
        if block.task.description == "Vet appointment":
            result = scheduler.complete_task(block)
            print(f"\n  Completed:  '{block.task.description}' (ONCE)")
            print(f"  Next occurrence: {result}  ← None expected for ONCE tasks")
            break

    # --- check_conflicts(): candidate task probe ---
    print("\n" + "=" * 55)
    print("  check_conflicts() — candidate probe")
    print("=" * 55)
    long_task = Task(99, "Long grooming", 90, Priority.LOW)
    conflict = scheduler.check_conflicts(long_task, start_time=time(9, 0))
    print(f"  90-min task at 09:00:  {'CONFLICT' if conflict else 'OK — no conflict'}")
    conflict2 = scheduler.check_conflicts(long_task, start_time=time(22, 0))
    print(f"  90-min task at 22:00:  {'CONFLICT' if conflict2 else 'OK — no conflict'}")

    # --- get_conflicts(): scan for overlaps already in the schedule ---
    print("\n" + "=" * 55)
    print("  get_conflicts() — overlap scan (no conflicts expected)")
    print("=" * 55)
    clean_warnings = scheduler.get_conflicts()
    if clean_warnings:
        for w in clean_warnings:
            print(f"  {w}")
    else:
        print("  No conflicts detected — schedule is clean.")

    # Inject two overlapping blocks directly to simulate the problem:
    #   Rex: "Bath time"     14:00 – 14:45
    #   Whiskers: "Play session"  14:15 – 14:35   ← overlaps Bath time
    print("\n" + "=" * 55)
    print("  get_conflicts() — two tasks forced to overlap")
    print("=" * 55)
    task_a = Task(201, "Bath time",    45, Priority.LOW,    time(14, 0))
    task_b = Task(202, "Play session", 20, Priority.MEDIUM, time(14, 15))
    scheduler._schedule.append(
        ScheduledBlock("Rex",      task_a, time(14, 0),  time(14, 45))
    )
    scheduler._schedule.append(
        ScheduledBlock("Whiskers", task_b, time(14, 15), time(14, 35))
    )
    overlap_warnings = scheduler.get_conflicts()
    if overlap_warnings:
        for w in overlap_warnings:
            print(f"  {w}")
    else:
        print("  No conflicts detected.")

    print("\n" + "=" * 55)


if __name__ == "__main__":
    main()
