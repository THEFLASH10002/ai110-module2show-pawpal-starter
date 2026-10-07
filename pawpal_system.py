"""PawPal+ core system.

Class skeleton generated from diagrams/uml_draft.mmd. No scheduling logic yet.
"""

from __future__ import annotations


class CareTask:
    """One thing a pet needs: a walk, a meal, a dose of medication."""

    def __init__(
        self,
        title: str,
        duration_minutes: int,
        priority: str = "medium",
        is_recurring: bool = False,
    ) -> None:
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.is_recurring = is_recurring
        self.scheduled_time: str | None = None

    def priority_rank(self) -> int:
        """Return a sortable number so high priority comes first."""
        raise NotImplementedError

    def fits_in(self, minutes_left: int) -> bool:
        """Return True if this task still fits in the time remaining."""
        raise NotImplementedError


class Pet:
    """A pet and the care tasks it needs."""

    def __init__(self, name: str, species: str, breed: str = "") -> None:
        self.name = name
        self.species = species
        self.breed = breed
        self.tasks: list[CareTask] = []

    def add_task(self, task: CareTask) -> None:
        raise NotImplementedError

    def edit_task(self, title: str, **changes) -> bool:
        raise NotImplementedError

    def remove_task(self, title: str) -> bool:
        raise NotImplementedError


class Owner:
    """The person doing the caring, plus the constraints they bring."""

    def __init__(self, name: str, available_minutes: int = 120) -> None:
        self.name = name
        self.available_minutes = available_minutes
        self.blocked_times: list[str] = []
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        raise NotImplementedError

    def set_availability(self, minutes: int) -> None:
        raise NotImplementedError

    def is_time_blocked(self, start_time: str) -> bool:
        raise NotImplementedError


class Scheduler:
    """Turns an owner's constraints and a pet's tasks into a daily plan."""

    def __init__(self, owner: Owner, pet: Pet) -> None:
        self.owner = owner
        self.pet = pet
        self.planned: list[CareTask] = []
        self.skipped: list[CareTask] = []

    def sort_by_priority(self, tasks: list[CareTask]) -> list[CareTask]:
        raise NotImplementedError

    def generate_plan(self, start_time: str = "08:00") -> list[CareTask]:
        """Select, order and time-stamp the tasks that fit."""
        raise NotImplementedError

    def explain_plan(self) -> str:
        """Explain what was scheduled, in what order, and what was dropped."""
        raise NotImplementedError
