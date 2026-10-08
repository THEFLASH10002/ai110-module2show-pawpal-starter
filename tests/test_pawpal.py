"""Tests for the PawPal+ core system."""

from datetime import date

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


@pytest.fixture
def pet() -> Pet:
    """Return a pet with no tasks attached."""
    return Pet("Biscuit", "dog", "Golden Retriever")


@pytest.fixture
def owner(pet: Pet) -> Owner:
    """Return an owner with one pet and a two hour budget."""
    jordan = Owner("Jordan", available_minutes=120)
    jordan.add_pet(pet)
    return jordan


def test_mark_complete_changes_status():
    """A new task starts pending and mark_complete flips it to done."""
    task = Task("Morning walk", 30, "high")
    assert task.is_complete is False

    task.mark_complete()

    assert task.is_complete is True


def test_adding_task_increases_pet_task_count(pet: Pet):
    """Adding a task to a pet grows that pet's task list by one."""
    before = len(pet.tasks)

    pet.add_task(Task("Breakfast", 10, "high"))

    assert len(pet.tasks) == before + 1


def test_owner_collects_tasks_across_all_pets(owner: Owner, pet: Pet):
    """all_tasks reaches into every pet, not just the first one."""
    pet.add_task(Task("Morning walk", 30, "high"))
    mochi = Pet("Mochi", "cat")
    mochi.add_task(Task("Thyroid medication", 5, "high"))
    owner.add_pet(mochi)

    pairs = owner.all_tasks()

    assert len(pairs) == 2
    assert {p.name for p, _ in pairs} == {"Biscuit", "Mochi"}


def test_high_priority_is_scheduled_before_low(owner: Owner, pet: Pet):
    """A high priority task is placed earlier in the day than a low priority one."""
    pet.add_task(Task("Evening enrichment", 20, "low"))
    pet.add_task(Task("Thyroid medication", 5, "high"))

    planned, _ = Scheduler(owner).generate_plan(start_time="08:00")

    assert [i.task.title for i in planned] == ["Thyroid medication", "Evening enrichment"]


def test_task_is_skipped_when_budget_runs_out(owner: Owner, pet: Pet):
    """A task that does not fit the owner's remaining minutes is skipped with a reason."""
    owner.set_availability(30)
    pet.add_task(Task("Morning walk", 30, "high"))
    pet.add_task(Task("Full grooming", 45, "low"))

    planned, skipped = Scheduler(owner).generate_plan(start_time="08:00")

    assert [i.task.title for i in planned] == ["Morning walk"]
    assert [i.task.title for i in skipped] == ["Full grooming"]
    assert "45 min" in skipped[0].reason


def test_completed_tasks_are_left_out_of_the_plan(owner: Owner, pet: Pet):
    """Once a task is marked complete it no longer appears in a generated plan."""
    walk = Task("Morning walk", 30, "high")
    pet.add_task(walk)
    walk.mark_complete()

    planned, skipped = Scheduler(owner).generate_plan(start_time="08:00")

    assert planned == []
    assert skipped == []


def test_scheduler_works_around_a_blocked_window(owner: Owner, pet: Pet):
    """A task that would run into a blocked window is pushed to after that window."""
    owner.block_window("12:00", "13:00")
    pet.add_task(Task("Morning walk", 30, "high", preferred_time="11:45"))

    planned, _ = Scheduler(owner).generate_plan(start_time="08:00")

    assert planned[0].start_time == "13:00"
    assert planned[0].end_time() == "13:30"


def test_planning_twice_does_not_mutate_the_pets_tasks(owner: Owner, pet: Pet):
    """Generating a plan leaves the pet's own task objects untouched, so re-runs are clean."""
    pet.add_task(Task("Morning walk", 30, "high"))
    scheduler = Scheduler(owner)

    scheduler.generate_plan(start_time="08:00")
    owner.set_availability(10)
    planned, skipped = scheduler.generate_plan(start_time="08:00")

    assert planned == []
    assert [i.task.title for i in skipped] == ["Morning walk"]
    assert not hasattr(pet.tasks[0], "start_time")


def test_sort_by_time_orders_tasks_entered_out_of_order(owner: Owner, pet: Pet):
    """Tasks added back to front come out in clock order, with untimed ones last."""
    pet.add_task(Task("Evening enrichment", 20, "low", preferred_time="18:00"))
    pet.add_task(Task("Litter box", 10, "medium"))
    pet.add_task(Task("Morning walk", 30, "high", preferred_time="07:30"))

    scheduler = Scheduler(owner)
    ordered = scheduler.sort_by_time(scheduler.collect_tasks())

    assert [i.task.title for i in ordered] == [
        "Morning walk",
        "Evening enrichment",
        "Litter box",
    ]


def test_filter_tasks_narrows_by_pet_and_status(owner: Owner, pet: Pet):
    """filter_tasks applies only the filters it is given, and combines them."""
    walk = Task("Morning walk", 30, "high")
    pet.add_task(walk)
    mochi = Pet("Mochi", "cat")
    mochi.add_task(Task("Thyroid medication", 5, "high"))
    owner.add_pet(mochi)
    walk.mark_complete()

    assert len(owner.filter_tasks()) == 2
    assert [t.title for _, t in owner.filter_tasks(pet_name="Mochi")] == ["Thyroid medication"]
    assert [t.title for _, t in owner.filter_tasks(completed=True)] == ["Morning walk"]
    assert owner.filter_tasks(pet_name="Mochi", completed=True) == []


def test_completing_a_daily_task_queues_it_for_tomorrow(pet: Pet):
    """Completing a daily task leaves it done and adds a fresh one due the next day."""
    walk = Task("Morning walk", 30, "high", "daily", due_date=date(2026, 10, 7))
    pet.add_task(walk)

    follow_up = pet.complete_task(walk.task_id)

    assert walk.is_complete is True
    assert follow_up.due_date == date(2026, 10, 8)
    assert follow_up.is_complete is False
    assert len(pet.tasks) == 2


def test_completing_a_weekly_task_queues_it_seven_days_out(pet: Pet):
    """A weekly task comes back a week later, not the next day."""
    grooming = Task("Full grooming", 45, "low", "weekly", due_date=date(2026, 10, 7))
    pet.add_task(grooming)

    assert pet.complete_task(grooming.task_id).due_date == date(2026, 10, 14)


def test_completing_a_one_off_task_queues_nothing(pet: Pet):
    """A task with frequency 'once' does not come back."""
    trim = Task("Nail trim", 15, "low", "once")
    pet.add_task(trim)

    assert pet.complete_task(trim.task_id) is None
    assert len(pet.tasks) == 1


def test_tomorrows_task_is_not_planned_today(owner: Owner, pet: Pet):
    """A follow-up queued for tomorrow stays out of today's plan."""
    walk = Task("Morning walk", 30, "high", "daily", due_date=date(2026, 10, 7))
    pet.add_task(walk)
    pet.complete_task(walk.task_id)

    planned, skipped = Scheduler(owner, today=date(2026, 10, 7)).generate_plan()

    assert planned == []
    assert skipped == []


def test_detect_conflicts_warns_on_overlapping_requested_times(owner: Owner, pet: Pet):
    """Two tasks asking for the same slot produce a warning string, not an exception."""
    pet.add_task(Task("Breakfast", 10, "high", preferred_time="08:15"))
    mochi = Pet("Mochi", "cat")
    mochi.add_task(Task("Thyroid medication", 5, "high", preferred_time="08:15"))
    owner.add_pet(mochi)

    warnings = Scheduler(owner).detect_conflicts()

    assert len(warnings) == 1
    assert "Breakfast" in warnings[0] and "Thyroid medication" in warnings[0]


def test_detect_conflicts_is_quiet_when_times_only_touch(owner: Owner, pet: Pet):
    """A task ending exactly when the next starts is not a conflict."""
    pet.add_task(Task("Breakfast", 10, "high", preferred_time="08:00"))
    pet.add_task(Task("Morning walk", 30, "high", preferred_time="08:10"))

    assert Scheduler(owner).detect_conflicts() == []
