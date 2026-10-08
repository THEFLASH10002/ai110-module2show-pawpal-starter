"""Terminal demo for PawPal+. Builds a sample household and prints today's schedule."""

from pawpal_system import Owner, Pet, Scheduler, Task

LINE_WIDTH = 64


def build_household() -> Owner:
    """Create a sample owner with two pets and a realistic set of care tasks."""
    jordan = Owner("Jordan", available_minutes=100)
    jordan.block_window("12:00", "13:00")

    biscuit = Pet("Biscuit", "dog", "Golden Retriever")
    biscuit.add_task(Task("Morning walk", 30, "high", "daily", preferred_time="07:30"))
    biscuit.add_task(Task("Breakfast", 10, "high", "daily", preferred_time="08:15"))
    biscuit.add_task(Task("Evening enrichment", 20, "low", "daily", preferred_time="18:00"))
    biscuit.add_task(Task("Full grooming", 45, "low", "weekly"))

    mochi = Pet("Mochi", "cat", "Tabby")
    mochi.add_task(Task("Thyroid medication", 5, "high", "daily", preferred_time="09:00"))
    mochi.add_task(Task("Litter box", 10, "medium", "daily"))

    jordan.add_pet(biscuit)
    jordan.add_pet(mochi)
    return jordan


def print_schedule(owner: Owner, planned, skipped) -> None:
    """Print the plan as an aligned table rather than a raw list of objects."""
    print("=" * LINE_WIDTH)
    print(f"TODAY'S SCHEDULE for {owner.name}".center(LINE_WIDTH))
    print("=" * LINE_WIDTH)

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
    print("=" * LINE_WIDTH)


def main() -> None:
    """Build the sample household, generate a plan and print it with its reasoning."""
    jordan = build_household()
    scheduler = Scheduler(jordan)
    planned, skipped = scheduler.generate_plan(start_time="07:00")

    print_schedule(jordan, planned, skipped)
    print()
    print("WHY THIS PLAN")
    print(scheduler.explain_plan(planned, skipped))


if __name__ == "__main__":
    main()
