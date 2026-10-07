"""PawPal+ core system.

Class skeleton generated from diagrams/uml_draft.mmd, then revised after an
AI review flagged missing relationships and a few logic bottlenecks.
No scheduling logic yet.
"""

from __future__ import annotations


class CareTask:
    """One thing a pet needs: a walk, a meal, a dose of medication.

    Holds the definition of the task only. Where it lands in a day is a
    property of the plan, not of the task, so no scheduled time is stored here.
    """

    def __init__(
        self,
        title: str,
        duration_minutes: int,
        priority: str = "medium",
        is_recurring: bool = False,
        task_id: str | None = None,
    ) -> None:
        self.task_id = task_id or self._new_id()
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.is_recurring = is_recurring

    @staticmethod
    def _new_id() -> str:
        """Return a unique id so two tasks can share a title."""
        raise NotImplementedError

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

    def edit_task(self, task_id: str, **changes) -> bool:
        raise NotImplementedError

    def remove_task(self, task_id: str) -> bool:
        raise NotImplementedError


class Owner:
    """The person doing the caring, plus the constraints they bring."""

    def __init__(self, name: str, available_minutes: int = 120) -> None:
        self.name = name
        self.available_minutes = available_minutes
        self.blocked_windows: list[tuple[str, str]] = []
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        raise NotImplementedError

    def set_availability(self, minutes: int) -> None:
        raise NotImplementedError

    def block_window(self, start_time: str, end_time: str) -> None:
        """Mark a period the owner is unavailable, e.g. 12:00-13:00."""
        raise NotImplementedError

    def overlaps_blocked(self, start_time: str, duration_minutes: int) -> bool:
        """Return True if a task of this length would run into a blocked window."""
        raise NotImplementedError


class PlannedItem:
    """One task placed at one time, for one pet, with the reason it landed there."""

    def __init__(
        self,
        task: CareTask,
        pet: Pet,
        start_time: str | None = None,
        reason: str = "",
    ) -> None:
        self.task = task
        self.pet = pet
        self.start_time = start_time
        self.reason = reason

    def end_time(self) -> str:
        """Return the clock time this item finishes."""
        raise NotImplementedError


class Scheduler:
    """Turns an owner's constraints and their pets' tasks into a daily plan."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def collect_tasks(self) -> list[PlannedItem]:
        """Gather tasks from every pet the owner has, still unscheduled."""
        raise NotImplementedError

    def sort_by_priority(self, items: list[PlannedItem]) -> list[PlannedItem]:
        """Order by priority, then by shortest duration as the tie-breaker."""
        raise NotImplementedError

    def select_tasks(
        self, items: list[PlannedItem]
    ) -> tuple[list[PlannedItem], list[PlannedItem]]:
        """Split into what fits in the owner's available minutes and what does not."""
        raise NotImplementedError

    def assign_times(
        self, items: list[PlannedItem], start_time: str = "08:00"
    ) -> list[PlannedItem]:
        """Walk the clock forward, skipping blocked windows, stamping each item."""
        raise NotImplementedError

    def generate_plan(self, start_time: str = "08:00") -> tuple[list[PlannedItem], list[PlannedItem]]:
        """Run collect, sort, select and assign. Returns (planned, skipped)."""
        raise NotImplementedError

    def explain_plan(
        self, planned: list[PlannedItem], skipped: list[PlannedItem]
    ) -> str:
        """Explain what was scheduled, in what order, and what was dropped."""
        raise NotImplementedError
