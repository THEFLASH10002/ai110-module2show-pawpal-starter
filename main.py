"""Terminal demo for PawPal+. Builds a sample household and exercises the scheduler."""

from pawpal_system import Owner, Pet, Scheduler, Task

LINE_WIDTH = 68


def heading(text: str) -> None:
    """Print a section heading so the demo output is scannable."""
    print()
    print("=" * LINE_WIDTH)
    print(text.center(LINE_WIDTH))
    print("=" * LINE_WIDTH)


def build_household() -> Owner:
    """Create a sample owner with two pets, deliberately adding tasks out of time order."""
    jordan = Owner("Jordan", available_minutes=100)
    jordan.block_window("12:00", "13:00")

    biscuit = Pet("Biscuit", "dog", "Golden Retriever")
    # Added evening first, then morning, to prove the sorting is doing the work.
    biscuit.add_task(Task("Evening enrichment", 20, "low", "daily", preferred_time="18:00"))
    biscuit.add_task(Task("Morning walk", 30, "high", "daily", preferred_time="07:30"))
    biscuit.add_task(Task("Full grooming", 45, "low", "weekly"))
    biscuit.add_task(Task("Breakfast", 10, "high", "daily", preferred_time="08:15"))

    mochi = Pet("Mochi", "cat", "Tabby")
    mochi.add_task(Task("Litter box", 10, "medium", "daily"))
    # Deliberately collides with Biscuit's breakfast at 08:15 to trigger a warning.
    mochi.add_task(Task("Thyroid medication", 5, "high", "daily", preferred_time="08:15"))
    mochi.add_task(Task("Nail trim", 15, "low", "once"))

    jordan.add_pet(biscuit)
    jordan.add_pet(mochi)
    return jordan


def show_sorting(scheduler: Scheduler) -> None:
    """Print every pending task in clock order, however it was entered."""
    heading("ALL TASKS, SORTED BY TIME")
    for item in scheduler.sort_by_time(scheduler.collect_tasks()):
        when = item.task.preferred_time or "flexible"
        print(f"  {when:<10} {item.pet.name:<9} {item.task.title:<22} [{item.task.priority}]")


def show_filtering(owner: Owner) -> None:
    """Print a couple of filtered views to show filter_tasks narrowing the list."""
    heading("FILTERING")

    print("  Mochi only:")
    for _, task in owner.filter_tasks(pet_name="Mochi"):
        print(f"    - {task.title}")

    print("  Still outstanding (any pet):")
    for pet, task in owner.filter_tasks(completed=False):
        print(f"    - {pet.name}: {task.title}")

    print("  High priority only:")
    for pet, task in owner.filter_tasks(priority="high"):
        print(f"    - {pet.name}: {task.title}")


def show_conflicts(scheduler: Scheduler) -> None:
    """Print any requested times that collide, as warnings rather than errors."""
    heading("CONFLICT CHECK")
    conflicts = scheduler.detect_conflicts()
    if not conflicts:
        print("  No clashes between requested times.")
    for warning in conflicts:
        print(f"  WARNING: {warning}")


def show_recurrence(owner: Owner) -> None:
    """Complete a repeating task and a one-off task to show what each leaves behind."""
    heading("RECURRING TASKS")
    biscuit = owner.pets[0]
    mochi = owner.pets[1]

    walk = next(t for t in biscuit.tasks if t.title == "Morning walk")
    print(f"  Completing {biscuit.name}'s '{walk.title}' (due {walk.due_date}, {walk.frequency})")
    follow_up = biscuit.complete_task(walk.task_id)
    print(f"  -> next instance queued for {follow_up.due_date}")

    trim = next(t for t in mochi.tasks if t.title == "Nail trim")
    print(f"  Completing {mochi.name}'s '{trim.title}' ({trim.frequency})")
    print(f"  -> {mochi.complete_task(trim.task_id)} queued, because it does not repeat")

    print("  Outstanding for Biscuit now:")
    for _, task in owner.filter_tasks(pet_name="Biscuit", completed=False):
        print(f"    - {task.title} (due {task.due_date})")


def print_schedule(owner: Owner, planned, skipped) -> None:
    """Print the plan as an aligned table rather than a raw list of objects."""
    heading(f"TODAY'S SCHEDULE for {owner.name}")
    if not planned:
        print("  Nothing scheduled today.")
    for item in planned:
        slot = f"{item.start_time}-{item.end_time()}"
        print(f"  {slot:<13} {item.pet.name:<9} {item.task.title:<22} [{item.task.priority}]")

    if skipped:
        print("-" * LINE_WIDTH)
        print("  NOT SCHEDULED TODAY")
        for item in skipped:
            print(f"  {'--':<13} {item.pet.name:<9} {item.task.title:<22} [{item.task.priority}]")
            print(f"  {'':<13} why: {item.reason}")


def main() -> None:
    """Run the whole demo: sorting, filtering, conflicts, recurrence and the final plan."""
    jordan = build_household()
    scheduler = Scheduler(jordan)

    show_sorting(scheduler)
    show_filtering(jordan)
    show_conflicts(scheduler)
    show_recurrence(jordan)

    planned, skipped = scheduler.generate_plan(start_time="07:00")
    print_schedule(jordan, planned, skipped)

    heading("WHY THIS PLAN")
    print(scheduler.explain_plan(planned, skipped))


if __name__ == "__main__":
    main()
