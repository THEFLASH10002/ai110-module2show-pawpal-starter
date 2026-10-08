"""Tests for the PawPal+ core system."""

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
