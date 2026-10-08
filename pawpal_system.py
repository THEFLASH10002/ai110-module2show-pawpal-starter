"""PawPal+ core system: owners, pets, care tasks and the daily scheduler."""

from __future__ import annotations

from itertools import count

PRIORITY_RANKS = {"high": 3, "medium": 2, "low": 1}


def to_minutes(clock: str) -> int:
    """Convert an 'HH:MM' string into minutes since midnight."""
    hours, minutes = clock.split(":")
    return int(hours) * 60 + int(minutes)


def to_clock(minutes: int) -> str:
    """Convert minutes since midnight back into an 'HH:MM' string."""
    return f"{minutes // 60 % 24:02d}:{minutes % 60:02d}"


class Task:
    """A single care activity: what it is, how long it takes, how often, and whether it is done."""

    _ids = count(1)

    def __init__(
        self,
        title: str,
        duration_minutes: int,
        priority: str = "medium",
        frequency: str = "daily",
        preferred_time: str | None = None,
        task_id: str | None = None,
    ) -> None:
        """Create a care task, assigning it a unique id if one is not supplied."""
        if duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if priority not in PRIORITY_RANKS:
            raise ValueError(f"priority must be one of {sorted(PRIORITY_RANKS)}")
        self.task_id = task_id or f"t{next(Task._ids)}"
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.frequency = frequency
        self.preferred_time = preferred_time
        self.is_complete = False

    def mark_complete(self) -> None:
        """Mark this task as done for today."""
        self.is_complete = True

    def mark_incomplete(self) -> None:
        """Reset this task back to pending, for example at the start of a new day."""
        self.is_complete = False

    def priority_rank(self) -> int:
        """Return a sortable number so high priority sorts above low."""
        return PRIORITY_RANKS[self.priority]

    def fits_in(self, minutes_left: int) -> bool:
        """Return True if this task still fits in the time remaining."""
        return self.duration_minutes <= minutes_left

    def __repr__(self) -> str:
        """Return a readable debug representation."""
        state = "done" if self.is_complete else "pending"
        return f"<Task {self.title} {self.duration_minutes}min {self.priority} {state}>"


class Pet:
    """A pet and the care tasks it needs."""

    def __init__(self, name: str, species: str, breed: str = "") -> None:
        """Create a pet with an empty task list."""
        self.name = name
        self.species = species
        self.breed = breed
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        self.tasks.append(task)

    def find_task(self, task_id: str) -> Task | None:
        """Return the task with this id, or None if the pet does not have it."""
        return next((t for t in self.tasks if t.task_id == task_id), None)

    def edit_task(self, task_id: str, **changes) -> bool:
        """Update fields on one task by id, returning False if it is not found."""
        task = self.find_task(task_id)
        if task is None:
            return False
        for field, value in changes.items():
            if not hasattr(task, field):
                raise AttributeError(f"Task has no field {field!r}")
            setattr(task, field, value)
        return True

    def remove_task(self, task_id: str) -> bool:
        """Remove one task by id, returning False if it is not found."""
        task = self.find_task(task_id)
        if task is None:
            return False
        self.tasks.remove(task)
        return True

    def pending_tasks(self) -> list[Task]:
        """Return only the tasks that have not been completed yet."""
        return [t for t in self.tasks if not t.is_complete]

    def __repr__(self) -> str:
        """Return a readable debug representation."""
        return f"<Pet {self.name} ({self.species}) {len(self.tasks)} tasks>"


class Owner:
    """The person doing the caring, their pets, and the constraints they bring to the day."""

    def __init__(self, name: str, available_minutes: int = 120) -> None:
        """Create an owner with a daily time budget and no pets yet."""
        self.name = name
        self.available_minutes = available_minutes
        self.blocked_windows: list[tuple[str, str]] = []
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's care."""
        self.pets.append(pet)

    def set_availability(self, minutes: int) -> None:
        """Set how many minutes of care time the owner has today."""
        if minutes < 0:
            raise ValueError("available minutes cannot be negative")
        self.available_minutes = minutes

    def block_window(self, start_time: str, end_time: str) -> None:
        """Mark a period the owner is unavailable, for example 12:00 to 13:00."""
        if to_minutes(end_time) <= to_minutes(start_time):
            raise ValueError("blocked window must end after it starts")
        self.blocked_windows.append((start_time, end_time))

    def blocking_window(self, start_time: str, duration_minutes: int) -> tuple[str, str] | None:
        """Return the first blocked window a task of this length would run into, or None."""
        start = to_minutes(start_time)
        end = start + duration_minutes
        clashes = [
            (ws, we)
            for ws, we in self.blocked_windows
            if start < to_minutes(we) and end > to_minutes(ws)
        ]
        return min(clashes, key=lambda w: to_minutes(w[0])) if clashes else None

    def overlaps_blocked(self, start_time: str, duration_minutes: int) -> bool:
        """Return True if a task of this length would run into a blocked window."""
        return self.blocking_window(start_time, duration_minutes) is not None

    def all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every task across every pet, paired with the pet it belongs to."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def pending_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every not-yet-completed task across every pet, paired with its pet."""
        return [(pet, task) for pet, task in self.all_tasks() if not task.is_complete]

    def __repr__(self) -> str:
        """Return a readable debug representation."""
        return f"<Owner {self.name} {len(self.pets)} pets {self.available_minutes}min>"


class PlannedItem:
    """One task placed at one time for one pet, with the reason it landed there."""

    def __init__(
        self,
        task: Task,
        pet: Pet,
        start_time: str | None = None,
        reason: str = "",
    ) -> None:
        """Wrap a task with the pet it belongs to and where it sits in the day."""
        self.task = task
        self.pet = pet
        self.start_time = start_time
        self.reason = reason

    def end_time(self) -> str | None:
        """Return the clock time this item finishes, or None if it is unscheduled."""
        if self.start_time is None:
            return None
        return to_clock(to_minutes(self.start_time) + self.task.duration_minutes)

    def __repr__(self) -> str:
        """Return a readable debug representation."""
        return f"<PlannedItem {self.start_time} {self.pet.name}: {self.task.title}>"


class Scheduler:
    """Turns an owner's constraints and their pets' tasks into an explained daily plan."""

    def __init__(self, owner: Owner, day_ends: str = "21:00") -> None:
        """Create a scheduler for one owner, with a cutoff time for the day."""
        self.owner = owner
        self.day_ends = day_ends

    def collect_tasks(self) -> list[PlannedItem]:
        """Gather every pending task from every pet, still unscheduled."""
        return [PlannedItem(task, pet) for pet, task in self.owner.pending_tasks()]

    def sort_by_priority(self, items: list[PlannedItem]) -> list[PlannedItem]:
        """Order by priority first, then shortest task, so quick wins are not crowded out."""
        return sorted(
            items,
            key=lambda i: (-i.task.priority_rank(), i.task.duration_minutes, i.task.title),
        )

    def select_tasks(
        self, items: list[PlannedItem]
    ) -> tuple[list[PlannedItem], list[PlannedItem]]:
        """Split tasks into what fits in the owner's time budget and what does not."""
        budget = self.owner.available_minutes
        remaining = budget
        ranked = self.sort_by_priority(items)
        planned: list[PlannedItem] = []
        skipped: list[PlannedItem] = []
        for rank, item in enumerate(ranked, start=1):
            if item.task.fits_in(remaining):
                remaining -= item.task.duration_minutes
                item.reason = (
                    f"{item.task.priority} priority, picked {rank} of {len(ranked)} "
                    f"into the {budget} min budget"
                )
                planned.append(item)
            else:
                item.reason = (
                    f"needs {item.task.duration_minutes} min "
                    f"but only {remaining} min of the budget was left"
                )
                skipped.append(item)
        return planned, skipped

    def _order_for_clock(self, items: list[PlannedItem]) -> list[PlannedItem]:
        """Put tasks with a requested time in time order, then the rest by priority."""
        requested = [i for i in items if i.task.preferred_time]
        flexible = [i for i in items if not i.task.preferred_time]
        requested.sort(key=lambda i: to_minutes(i.task.preferred_time))
        return requested + self.sort_by_priority(flexible)

    def _first_free_slot(self, cursor: int, duration: int) -> int:
        """Push the clock forward past any blocked window this task would run into."""
        window = self.owner.blocking_window(to_clock(cursor), duration)
        while window is not None:
            cursor = to_minutes(window[1])
            window = self.owner.blocking_window(to_clock(cursor), duration)
        return cursor

    def assign_times(
        self, items: list[PlannedItem], start_time: str = "08:00"
    ) -> tuple[list[PlannedItem], list[PlannedItem]]:
        """Walk the clock forward stamping each task, deferring any that run past the day's end."""
        cursor = to_minutes(start_time)
        cutoff = to_minutes(self.day_ends)
        scheduled: list[PlannedItem] = []
        deferred: list[PlannedItem] = []
        for item in self._order_for_clock(items):
            if item.task.preferred_time:
                cursor = max(cursor, to_minutes(item.task.preferred_time))
            cursor = self._first_free_slot(cursor, item.task.duration_minutes)
            if cursor + item.task.duration_minutes > cutoff:
                item.start_time = None
                item.reason = f"no slot left before {self.day_ends}"
                deferred.append(item)
                continue
            item.start_time = to_clock(cursor)
            if item.task.preferred_time == item.start_time:
                item.reason = f"{item.reason}; placed at the requested time"
            cursor += item.task.duration_minutes
            scheduled.append(item)
        return scheduled, deferred

    def generate_plan(
        self, start_time: str = "08:00"
    ) -> tuple[list[PlannedItem], list[PlannedItem]]:
        """Run collect, select and assign in order, returning (planned, skipped)."""
        planned, skipped = self.select_tasks(self.collect_tasks())
        scheduled, deferred = self.assign_times(planned, start_time)
        return scheduled, skipped + deferred

    def explain_plan(self, planned: list[PlannedItem], skipped: list[PlannedItem]) -> str:
        """Describe what was scheduled, why it sits where it does, and what was dropped."""
        lines = [
            f"{self.owner.name} has {self.owner.available_minutes} minutes today "
            f"across {len(self.owner.pets)} pets.",
            "Tasks were ranked by priority, then by how short they are, "
            "so quick wins are not crowded out by one long low-priority job.",
        ]
        if self.owner.blocked_windows:
            windows = ", ".join(f"{s}-{e}" for s, e in self.owner.blocked_windows)
            lines.append(f"The plan works around these blocked times: {windows}.")
        for item in planned:
            lines.append(
                f"  {item.start_time} {item.pet.name}: {item.task.title} -> {item.reason}"
            )
        for item in skipped:
            lines.append(f"  dropped {item.pet.name}: {item.task.title} -> {item.reason}")
        return "\n".join(lines)
