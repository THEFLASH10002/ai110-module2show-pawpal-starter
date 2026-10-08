"""PawPal+ core system: owners, pets, care tasks and the daily scheduler."""

from __future__ import annotations

from datetime import date, timedelta
from itertools import combinations, count

PRIORITY_RANKS = {"high": 3, "medium": 2, "low": 1}

# How far ahead the next instance of a repeating task falls due.
FREQUENCY_DAYS = {"daily": 1, "weekly": 7}


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
        due_date: date | None = None,
    ) -> None:
        """Create a care task, assigning it a unique id and today's date if not supplied."""
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
        self.due_date = due_date or date.today()
        self.is_complete = False

    def next_due_date(self) -> date | None:
        """Return when this task falls due again, or None if it does not repeat."""
        step = FREQUENCY_DAYS.get(self.frequency)
        return self.due_date + timedelta(days=step) if step else None

    def next_occurrence(self) -> Task | None:
        """Return a fresh pending copy of this task due on its next date, or None if one-off."""
        next_date = self.next_due_date()
        if next_date is None:
            return None
        return Task(
            self.title,
            self.duration_minutes,
            self.priority,
            self.frequency,
            self.preferred_time,
            due_date=next_date,
        )

    def window(self) -> tuple[int, int] | None:
        """Return this task's requested start and end in minutes, or None if it has no set time."""
        if self.preferred_time is None:
            return None
        start = to_minutes(self.preferred_time)
        return start, start + self.duration_minutes

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

    def complete_task(self, task_id: str) -> Task | None:
        """Tick a task off and queue its next occurrence, returning that follow-up task.

        Returns None when the task is one-off or the id is unknown, so a caller can
        tell "nothing repeats" from "here is tomorrow's walk".
        """
        task = self.find_task(task_id)
        if task is None or task.is_complete:
            # Completing something already ticked off must not queue a second
            # follow-up, or a double click would leave two of tomorrow's walk.
            return None
        task.mark_complete()
        follow_up = task.next_occurrence()
        if follow_up is not None:
            self.add_task(follow_up)
        return follow_up

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

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
        priority: str | None = None,
        due_on: date | None = None,
    ) -> list[tuple[Pet, Task]]:
        """Return (pet, task) pairs narrowed by any combination of pet, status, priority and date.

        Every filter left as None is simply not applied, so filter_tasks() returns
        everything and filter_tasks(pet_name="Mochi", completed=False) returns just
        what Mochi still needs today.
        """
        pairs = self.all_tasks()
        if pet_name is not None:
            pairs = [(p, t) for p, t in pairs if p.name.lower() == pet_name.lower()]
        if completed is not None:
            pairs = [(p, t) for p, t in pairs if t.is_complete is completed]
        if priority is not None:
            pairs = [(p, t) for p, t in pairs if t.priority == priority]
        if due_on is not None:
            pairs = [(p, t) for p, t in pairs if t.due_date == due_on]
        return pairs

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

    def __init__(
        self, owner: Owner, day_ends: str = "21:00", today: date | None = None
    ) -> None:
        """Create a scheduler for one owner, with a cutoff time and the date being planned."""
        self.owner = owner
        self.day_ends = day_ends
        self.today = today or date.today()

    def collect_tasks(self) -> list[PlannedItem]:
        """Gather pending tasks that are actually due by today, still unscheduled.

        The due date check is what keeps a repeating task honest: completing today's
        walk queues tomorrow's, and without this filter that follow-up would turn
        straight around and appear in today's plan.
        """
        return [
            PlannedItem(task, pet)
            for pet, task in self.owner.pending_tasks()
            if task.due_date <= self.today
        ]

    @staticmethod
    def _clock_key(item: PlannedItem) -> tuple[bool, int]:
        """Return a sort key placing timed tasks in clock order and untimed ones last.

        'HH:MM' strings happen to sort correctly as text, but only while every value
        is zero padded and non-null. Converting to minutes makes that assumption
        explicit, and the leading bool pushes tasks with no time to the end instead
        of blowing up on None.
        """
        clock = item.start_time or item.task.preferred_time
        return (clock is None, to_minutes(clock) if clock else 0)

    def sort_by_time(self, items: list[PlannedItem]) -> list[PlannedItem]:
        """Order tasks by the clock, using the scheduled time if set and the requested one if not."""
        return sorted(items, key=self._clock_key)

    def detect_conflicts(self, items: list[PlannedItem] | None = None) -> list[str]:
        """Return a warning per pair of tasks whose requested times overlap, never raising.

        This looks at what the owner asked for, not at the finished plan, because
        assign_times already pushes clashing tasks apart. The warnings are how the
        owner finds out that something they pinned to 08:00 will not happen at 08:00.
        """
        if items is None:
            items = self.collect_tasks()
        timed = [i for i in items if i.task.window() is not None]
        warnings = []
        for first, second in combinations(self.sort_by_time(timed), 2):
            start_a, end_a = first.task.window()
            start_b, end_b = second.task.window()
            if start_a < end_b and start_b < end_a:
                warnings.append(
                    f"{first.pet.name}'s {first.task.title} "
                    f"({to_clock(start_a)}-{to_clock(end_a)}) overlaps "
                    f"{second.pet.name}'s {second.task.title} "
                    f"({to_clock(start_b)}-{to_clock(end_b)}); "
                    f"the later one will be pushed back."
                )
        return warnings

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
        return self.sort_by_time(requested) + self.sort_by_priority(flexible)

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
